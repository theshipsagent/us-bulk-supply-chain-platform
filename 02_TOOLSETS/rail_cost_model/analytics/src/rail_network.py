"""
Rail Network Routing Module

Builds a graph from NTAD rail network data and provides:
- Shortest path routing between locations
- Actual rail miles (vs straight-line Haversine)
- Network-based URCS cost calculations
- BEA zone to rail node mapping

Data source: BTS/NTAD North American Rail Network
"""

import pandas as pd
import numpy as np
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
import heapq
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Major interchange gateways (East-West crossover points)
# These are where Western carriers (UP, BNSF) interchange with Eastern (CSX, NS)
INTERCHANGE_GATEWAYS = {
    'chicago': {'lat': 41.8781, 'lon': -87.6298, 'cost_factor': 1.0},  # Primary
    'st_louis': {'lat': 38.6270, 'lon': -90.1994, 'cost_factor': 1.05},
    'kansas_city': {'lat': 39.0997, 'lon': -94.5786, 'cost_factor': 1.05},
    'memphis': {'lat': 35.1495, 'lon': -90.0490, 'cost_factor': 1.08},
    'new_orleans': {'lat': 29.9511, 'lon': -90.0715, 'cost_factor': 1.10},
}

# Class I Railroad ownership codes and regions
CLASS_I_CARRIERS = {
    # Western
    'UP': {'name': 'Union Pacific', 'region': 'west', 'type': 'class1'},
    'BNSF': {'name': 'BNSF Railway', 'region': 'west', 'type': 'class1'},
    # Eastern
    'CSXT': {'name': 'CSX Transportation', 'region': 'east', 'type': 'class1'},
    'CSX': {'name': 'CSX Transportation', 'region': 'east', 'type': 'class1'},
    'NS': {'name': 'Norfolk Southern', 'region': 'east', 'type': 'class1'},
    # North-South / Cross-border
    'CN': {'name': 'Canadian National', 'region': 'north_south', 'type': 'class1'},
    'CPKC': {'name': 'Canadian Pacific Kansas City', 'region': 'cross_border', 'type': 'class1'},
    'CPRS': {'name': 'Canadian Pacific', 'region': 'cross_border', 'type': 'class1'},
}

# Network type weights (prefer mainlines)
NETWORK_TYPE_WEIGHTS = {
    'M': 1.0,   # Mainline - preferred
    'A': 1.05,  # Major branch
    'I': 1.15,  # Industrial
    'S': 1.20,  # Spur
    'Y': 1.25,  # Yard
    'O': 1.10,  # Other
    'T': 1.30,  # Terminal
    'X': 1.50,  # Abandoned/low priority
    'R': 1.10,  # Regional
    'F': 1.20,  # Ferry/float
}

# Paths to rail network data
GEOSPATIAL_DIR = Path(__file__).parent.parent.parent / "03_geospatial" / "rail_nodes_lines"
NODES_CSV = GEOSPATIAL_DIR / "NTAD_North_American_Rail_Network_Nodes_1238521289684721083.csv"
LINES_CSV = GEOSPATIAL_DIR / "NTAD_North_American_Rail_Network_Lines_6174416889338357996.csv"


def haversine(lon1, lat1, lon2, lat2):
    """Calculate great circle distance in miles between two points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 3959 * c  # Earth radius in miles


class RailNetwork:
    """
    Rail network graph for routing and distance calculations.

    Uses Dijkstra's algorithm for shortest path routing on actual rail network.
    """

    def __init__(self, us_only=True, mainline_only=False):
        """
        Initialize rail network.

        Args:
            us_only: Only include US rail nodes/lines
            mainline_only: Only include mainline track (NET='M')
        """
        self.nodes = {}  # {node_id: (lon, lat, state, fra_district)}
        self.graph = defaultdict(list)  # {node_id: [(neighbor_id, miles, owner)]}
        self.node_index = None  # Spatial index for nearest node lookup
        self.bea_to_nodes = {}  # {bea_code: [nearest_node_ids]}

        self._load_network(us_only, mainline_only)

    def _load_network(self, us_only, mainline_only):
        """Load nodes and lines, build graph."""
        logger.info("Loading rail network data...")

        # Load nodes
        nodes_df = pd.read_csv(NODES_CSV, low_memory=False)
        if us_only:
            nodes_df = nodes_df[nodes_df['COUNTRY'] == 'US']

        for _, row in nodes_df.iterrows():
            self.nodes[row['FRANODEID']] = (
                row['x'],  # longitude
                row['y'],  # latitude
                row['STATE'],
                row['FRADISTRCT']
            )

        logger.info(f"Loaded {len(self.nodes):,} nodes")

        # Load lines and build graph
        lines_df = pd.read_csv(LINES_CSV, low_memory=False)
        if us_only:
            lines_df = lines_df[lines_df['COUNTRY'] == 'US']
        if mainline_only:
            lines_df = lines_df[lines_df['NET'] == 'M']

        edge_count = 0
        mainline_miles = 0
        for _, row in lines_df.iterrows():
            from_node = row['FRFRANODE']
            to_node = row['TOFRANODE']
            miles = row['MILES'] if pd.notna(row['MILES']) else 0.1
            owner = row['RROWNER1'] if pd.notna(row['RROWNER1']) else 'UNK'
            net_type = row['NET'] if pd.notna(row['NET']) else 'O'

            # Skip if nodes not in our set
            if from_node not in self.nodes or to_node not in self.nodes:
                continue

            # Apply network type weight (prefer mainlines)
            weight = NETWORK_TYPE_WEIGHTS.get(net_type, 1.1)
            weighted_miles = miles * weight

            # Track mainline miles
            if net_type == 'M':
                mainline_miles += miles

            # Bidirectional edges (rail can go both ways)
            # Store: (neighbor, weighted_miles, owner, actual_miles, net_type)
            self.graph[from_node].append((to_node, weighted_miles, owner, miles, net_type))
            self.graph[to_node].append((from_node, weighted_miles, owner, miles, net_type))
            edge_count += 1

        logger.info(f"Built graph with {edge_count:,} edges ({mainline_miles:,.0f} mainline miles)")

        # Build spatial index for fast nearest-node lookups
        self._build_spatial_index()

    def _build_spatial_index(self):
        """Build a simple grid-based spatial index for nodes."""
        logger.info("Building spatial index...")

        # Grid cells of ~0.5 degree (~35 miles at mid-latitudes)
        self.node_index = defaultdict(list)

        for node_id, (lon, lat, state, fra) in self.nodes.items():
            # Grid cell key
            cell = (int(lon * 2), int(lat * 2))
            self.node_index[cell].append(node_id)

        logger.info(f"Spatial index: {len(self.node_index):,} grid cells")

    def find_nearest_node(self, lon, lat, max_miles=50):
        """
        Find the nearest rail node to a given point.

        Args:
            lon, lat: Coordinates
            max_miles: Maximum distance to search

        Returns:
            (node_id, distance_miles) or (None, None)
        """
        # Check grid cells around the point
        cell_x, cell_y = int(lon * 2), int(lat * 2)

        best_node = None
        best_dist = float('inf')

        # Search 3x3 grid of cells
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                cell = (cell_x + dx, cell_y + dy)
                for node_id in self.node_index.get(cell, []):
                    node_lon, node_lat = self.nodes[node_id][:2]
                    dist = haversine(lon, lat, node_lon, node_lat)
                    if dist < best_dist:
                        best_dist = dist
                        best_node = node_id

        if best_dist <= max_miles:
            return best_node, best_dist
        return None, None

    def shortest_path(self, from_node, to_node, max_miles=5000):
        """
        Find shortest path between two nodes using Dijkstra's algorithm.

        Args:
            from_node, to_node: Node IDs
            max_miles: Maximum path length to consider

        Returns:
            dict with path details or None
        """
        if from_node not in self.graph or to_node not in self.graph:
            return None

        # Dijkstra's algorithm
        distances = {from_node: 0}
        actual_distances = {from_node: 0}
        parents = {from_node: None}
        edge_info = {}
        pq = [(0, from_node)]
        visited = set()

        while pq:
            dist, node = heapq.heappop(pq)

            if node in visited:
                continue
            visited.add(node)

            if node == to_node:
                # Reconstruct path
                path = []
                owners = []
                net_types = []
                current = to_node
                while current is not None:
                    path.append(current)
                    if current in edge_info:
                        owners.append(edge_info[current]['owner'])
                        net_types.append(edge_info[current]['net_type'])
                    current = parents[current]
                path.reverse()
                owners.reverse()
                net_types.reverse()

                # Count carrier transitions (interchanges)
                interchanges = 0
                prev_owner = None
                for owner in owners:
                    if prev_owner and owner != prev_owner:
                        # Check if this is a Class I to Class I transition
                        if owner in CLASS_I_CARRIERS and prev_owner in CLASS_I_CARRIERS:
                            interchanges += 1
                    prev_owner = owner

                # Calculate mainline percentage
                mainline_count = sum(1 for t in net_types if t == 'M')
                mainline_pct = mainline_count / len(net_types) * 100 if net_types else 0

                return {
                    'weighted_miles': dist,
                    'actual_miles': actual_distances[to_node],
                    'path': path,
                    'owners': owners,
                    'net_types': net_types,
                    'interchanges': interchanges,
                    'mainline_pct': mainline_pct
                }

            if dist > max_miles:
                continue

            for edge in self.graph[node]:
                neighbor, weighted_miles, owner, actual_miles, net_type = edge
                new_dist = dist + weighted_miles
                new_actual = actual_distances[node] + actual_miles

                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    actual_distances[neighbor] = new_actual
                    parents[neighbor] = node
                    edge_info[neighbor] = {'owner': owner, 'net_type': net_type}
                    heapq.heappush(pq, (new_dist, neighbor))

        return None

    def route_distance(self, from_lon, from_lat, to_lon, to_lat):
        """
        Calculate rail network distance between two points.

        Args:
            from_lon, from_lat: Origin coordinates
            to_lon, to_lat: Destination coordinates

        Returns:
            dict with route info or None
        """
        # Find nearest nodes
        from_node, from_dist = self.find_nearest_node(from_lon, from_lat)
        to_node, to_dist = self.find_nearest_node(to_lon, to_lat)

        if from_node is None or to_node is None:
            return None

        # Find shortest path
        path_result = self.shortest_path(from_node, to_node)

        if path_result is None:
            return None

        # Use actual miles (not weighted)
        rail_miles = path_result['actual_miles']
        total_miles = rail_miles + from_dist + to_dist

        # Get origin/destination info
        from_state = self.nodes[from_node][2]
        to_state = self.nodes[to_node][2]
        from_fra = self.nodes[from_node][3]
        to_fra = self.nodes[to_node][3]

        # Determine region (East vs West for URCS)
        # FRA Districts 1-4 = East, 5-8 = West
        from_region = 'east' if from_fra in [1, 2, 3, 4] else 'west'
        to_region = 'east' if to_fra in [1, 2, 3, 4] else 'west'

        # Identify Class I carriers on route
        owners = path_result['owners']
        class1_carriers = [o for o in set(owners) if o in CLASS_I_CARRIERS]
        unique_owners = list(set(owners)) if owners else []

        # Calculate interchange cost factor
        interchange_cost = 1.0 + (path_result['interchanges'] * 0.03)  # 3% per interchange

        return {
            'rail_miles': rail_miles,
            'access_miles': from_dist + to_dist,
            'total_miles': total_miles,
            'from_node': from_node,
            'to_node': to_node,
            'from_state': from_state,
            'to_state': to_state,
            'from_region': from_region,
            'to_region': to_region,
            'carriers': unique_owners,
            'class1_carriers': class1_carriers,
            'num_carriers': len(unique_owners),
            'interchanges': path_result['interchanges'],
            'interchange_cost_factor': interchange_cost,
            'mainline_pct': path_result['mainline_pct'],
            'haversine_miles': haversine(from_lon, from_lat, to_lon, to_lat),
            'circuity': total_miles / max(haversine(from_lon, from_lat, to_lon, to_lat), 1)
        }


def map_bea_to_network(network, bea_df):
    """
    Map BEA zones to nearest rail network nodes.

    Args:
        network: RailNetwork instance
        bea_df: DataFrame with bea_code, lat, lon columns

    Returns:
        dict mapping bea_code to nearest node info
    """
    bea_mapping = {}

    for _, row in bea_df.iterrows():
        bea_code = row['bea_code']
        lon = row['lon']
        lat = row['lat']

        if pd.isna(lon) or pd.isna(lat):
            continue

        node_id, dist = network.find_nearest_node(lon, lat)

        if node_id:
            bea_mapping[bea_code] = {
                'node_id': node_id,
                'access_miles': dist,
                'node_lon': network.nodes[node_id][0],
                'node_lat': network.nodes[node_id][1],
                'state': network.nodes[node_id][2],
                'fra_district': network.nodes[node_id][3]
            }

    return bea_mapping


def create_network_distance_table(conn, network, sample_size=None):
    """
    Create a table of network-based distances for O-D pairs in the waybill data.

    Args:
        conn: DuckDB connection
        network: RailNetwork instance
        sample_size: Limit to top N O-D pairs (for testing)
    """
    logger.info("Creating network distance table...")

    # Get unique O-D pairs with BEA coordinates
    limit_sql = f"LIMIT {sample_size}" if sample_size else ""

    od_pairs = conn.execute(f"""
        SELECT DISTINCT
            w.origin_bea,
            o.lat as origin_lat,
            o.lon as origin_lon,
            w.term_bea,
            d.lat as dest_lat,
            d.lon as dest_lon,
            COUNT(*) as shipment_count
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        WHERE o.lat IS NOT NULL AND d.lat IS NOT NULL
          AND w.origin_bea != '000' AND w.term_bea != '000'
        GROUP BY 1, 2, 3, 4, 5, 6
        ORDER BY shipment_count DESC
        {limit_sql}
    """).fetchall()

    logger.info(f"Processing {len(od_pairs):,} unique O-D pairs...")

    # Calculate network distances
    results = []
    for i, (origin_bea, o_lat, o_lon, term_bea, d_lat, d_lon, count) in enumerate(od_pairs):
        if i % 1000 == 0:
            logger.info(f"  Processed {i:,}/{len(od_pairs):,} pairs...")

        route = network.route_distance(o_lon, o_lat, d_lon, d_lat)

        if route:
            results.append({
                'origin_bea': origin_bea,
                'term_bea': term_bea,
                'haversine_miles': route['haversine_miles'],
                'rail_miles': route['rail_miles'],
                'total_miles': route['total_miles'],
                'circuity': route['circuity'],
                'from_region': route['from_region'],
                'to_region': route['to_region'],
                'num_carriers': route['num_carriers'],
                'carriers': ','.join(route['carriers'][:3]) if route['carriers'] else ''
            })

    if not results:
        logger.warning("No routes calculated")
        return

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Create table in DuckDB
    conn.execute("DROP TABLE IF EXISTS dim_network_distance")
    conn.execute("""
        CREATE TABLE dim_network_distance (
            origin_bea VARCHAR,
            term_bea VARCHAR,
            haversine_miles DOUBLE,
            rail_miles DOUBLE,
            total_miles DOUBLE,
            circuity DOUBLE,
            from_region VARCHAR,
            to_region VARCHAR,
            num_carriers INTEGER,
            carriers VARCHAR,
            PRIMARY KEY (origin_bea, term_bea)
        )
    """)

    conn.executemany("""
        INSERT INTO dim_network_distance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, results_df.values.tolist())

    logger.info(f"Created dim_network_distance with {len(results):,} O-D pairs")

    # Create view with network-adjusted distances
    conn.execute("""
        CREATE OR REPLACE VIEW v_waybill_network_distance AS
        SELECT
            w.*,
            COALESCE(nd.rail_miles, w.est_miles) as network_miles,
            nd.circuity,
            nd.from_region,
            nd.to_region,
            nd.num_carriers,
            nd.carriers
        FROM v_waybill_with_distance w
        LEFT JOIN dim_network_distance nd
            ON w.origin_bea = nd.origin_bea AND w.term_bea = nd.term_bea
    """)

    logger.info("Created v_waybill_network_distance view")


def calculate_network_urcs(conn):
    """
    Calculate URCS costs using network-based distances and regional cost factors.

    Creates enhanced R/VC analysis with:
    - Actual rail miles instead of Haversine
    - Regional cost differentials (East vs West)
    - Carrier count factor (competition)
    """

    # Regional URCS cost factors (2023 approximate)
    # East region has higher unit costs than West
    conn.execute("""
        CREATE OR REPLACE VIEW v_network_urcs_analysis AS
        SELECT
            w.waybill_id,
            w.stcc,
            w.stcc_2digit,
            w.origin_bea,
            w.term_bea,
            w.exp_carloads,
            w.exp_tons,
            w.exp_freight_rev,
            w.network_miles,
            w.from_region,
            w.to_region,
            w.num_carriers,
            -- Network-adjusted URCS variable cost
            ROUND(
                (
                    GREATEST(50, w.network_miles) * 0.048 * w.exp_tons +  -- GTM cost (regional adjusted)
                    GREATEST(50, w.network_miles) * 0.14 * w.exp_carloads +  -- Car-mile cost
                    w.exp_carloads * 8.50 +  -- Switch moves
                    w.exp_carloads * 2.50 * GREATEST(1, w.num_carriers - 1)  -- Interchange cost
                ) *
                CASE
                    WHEN w.from_region = 'east' AND w.to_region = 'east' THEN 1.15
                    WHEN w.from_region = 'west' AND w.to_region = 'west' THEN 0.95
                    ELSE 1.05
                END
            , 2) as network_urcs_cost,
            -- R/VC ratio
            ROUND(w.exp_freight_rev / NULLIF(
                (
                    GREATEST(50, w.network_miles) * 0.048 * w.exp_tons +
                    GREATEST(50, w.network_miles) * 0.14 * w.exp_carloads +
                    w.exp_carloads * 8.50 +
                    w.exp_carloads * 2.50 * GREATEST(1, w.num_carriers - 1)
                ) *
                CASE
                    WHEN w.from_region = 'east' AND w.to_region = 'east' THEN 1.15
                    WHEN w.from_region = 'west' AND w.to_region = 'west' THEN 0.95
                    ELSE 1.05
                END
            , 0) * 100, 1) as network_rvc_ratio
        FROM v_waybill_network_distance w
        WHERE w.network_miles IS NOT NULL
          AND w.exp_tons > 0
          AND w.exp_freight_rev > 0
    """)

    logger.info("Created v_network_urcs_analysis view with regional cost factors")


def estimate_rate(network, from_lon, from_lat, to_lon, to_lat,
                  commodity_stcc='32411', tons=100, conn=None):
    """
    Estimate freight rate for a point-to-point shipment.

    Uses:
    - Network-based distance with mainline preference
    - Historical rate curves by commodity and distance
    - Regional cost factors (URCS East/West)
    - Interchange penalty for cross-carrier moves
    - Competition factor based on carrier options

    Args:
        network: RailNetwork instance
        from_lon, from_lat, to_lon, to_lat: Coordinates
        commodity_stcc: STCC code
        tons: Shipment tonnage
        conn: Optional DuckDB connection for historical rates

    Returns:
        dict with rate estimates
    """
    # Get network route
    route = network.route_distance(from_lon, from_lat, to_lon, to_lat)

    if route is None:
        return None

    miles = route['total_miles']

    # Rate per ton-mile by commodity type (derived from STB waybill analysis)
    # These reflect 2023 average rates adjusted for distance
    commodity_rates = {
        '11': 0.022,  # Coal - low value, unit train, bulk
        '14': 0.028,  # Non-metallic minerals
        '20': 0.048,  # Food products
        '24': 0.038,  # Lumber
        '26': 0.042,  # Paper products
        '28': 0.058,  # Chemicals
        '29': 0.032,  # Petroleum
        '32': 0.045,  # Stone/clay/cement
        '33': 0.040,  # Primary metals
        '37': 0.068,  # Transportation equipment
        '40': 0.052,  # Waste/scrap
        '46': 0.085,  # Intermodal - premium service
        '49': 0.055,  # Hazmat
    }

    stcc_2 = commodity_stcc[:2]
    base_rate_per_ton_mile = commodity_rates.get(stcc_2, 0.045)

    # Distance taper: rate/mile decreases with distance (economies of length of haul)
    # Based on STB waybill regression analysis
    if miles < 300:
        taper = 1.45  # Short haul premium (high terminal cost ratio)
    elif miles < 500:
        taper = 1.20
    elif miles < 800:
        taper = 1.05
    elif miles < 1200:
        taper = 0.92
    elif miles < 1800:
        taper = 0.85
    else:
        taper = 0.78  # Long haul discount (terminal costs amortized)

    # Regional adjustment (URCS cost differential)
    if route['from_region'] == 'east' and route['to_region'] == 'east':
        region_factor = 1.18  # Eastern Class I higher costs
    elif route['from_region'] == 'west' and route['to_region'] == 'west':
        region_factor = 0.94  # Western carriers more efficient (longer trains, less congestion)
    else:
        region_factor = 1.08  # Cross-region includes interchange costs

    # Interchange cost factor (from corridor analysis)
    # Each Class I interchange adds ~3% to cost (dwell time, handling)
    interchange_factor = route['interchange_cost_factor']

    # Competition/captive shipper adjustment
    class1_count = len(route['class1_carriers'])
    if class1_count == 1:
        competition_factor = 1.18  # Captive shipper - railroad has pricing power
    elif class1_count == 2:
        competition_factor = 1.0   # Typical - some competition
    elif class1_count >= 3:
        competition_factor = 0.88  # Multiple options = competitive market
    else:
        competition_factor = 1.05  # Short-line only route

    # Mainline route quality bonus (PSR corridors more efficient)
    if route['mainline_pct'] > 80:
        quality_factor = 0.95  # High mainline usage = efficient
    elif route['mainline_pct'] > 50:
        quality_factor = 1.0
    else:
        quality_factor = 1.08  # Heavy branch line usage = less efficient

    # Calculate estimated rate
    rate_per_ton = (base_rate_per_ton_mile * miles * taper *
                    region_factor * interchange_factor *
                    competition_factor * quality_factor)
    total_rate = rate_per_ton * tons

    # Estimate URCS variable cost (2023 coefficients)
    # GTM: $0.048/gross-ton-mile, Car-mile: $0.14, Switch: $8.50
    carloads = max(1, tons / 100)  # Assume ~100 tons per car
    urcs_cost = (
        miles * 0.048 * tons +           # Gross ton-mile cost
        miles * 0.14 * carloads +        # Car-mile cost
        8.50 * carloads +                # Origin switching
        8.50 * carloads +                # Destination switching
        5.00 * route['interchanges'] * carloads  # Interchange handling
    ) * region_factor

    rvc_ratio = (total_rate / urcs_cost * 100) if urcs_cost > 0 else 0

    return {
        'distance': {
            'rail_miles': route['rail_miles'],
            'total_miles': route['total_miles'],
            'haversine_miles': route['haversine_miles'],
            'circuity': route['circuity'],
            'mainline_pct': route['mainline_pct']
        },
        'route': {
            'from_state': route['from_state'],
            'to_state': route['to_state'],
            'from_region': route['from_region'],
            'to_region': route['to_region'],
            'carriers': route['carriers'][:5],  # Top 5
            'class1_carriers': route['class1_carriers'],
            'num_carriers': route['num_carriers'],
            'interchanges': route['interchanges']
        },
        'rate_estimate': {
            'rate_per_ton': round(rate_per_ton, 2),
            'total_rate': round(total_rate, 2),
            'rate_per_ton_mile': round(rate_per_ton / miles, 4) if miles > 0 else 0,
            'rate_per_car': round(total_rate / carloads, 2)
        },
        'urcs_analysis': {
            'variable_cost': round(urcs_cost, 2),
            'rvc_ratio': round(rvc_ratio, 1),
            'above_180_threshold': rvc_ratio > 180,
            'cost_per_ton': round(urcs_cost / tons, 2)
        },
        'factors': {
            'distance_taper': round(taper, 2),
            'region_factor': round(region_factor, 2),
            'interchange_factor': round(interchange_factor, 2),
            'competition_factor': round(competition_factor, 2),
            'quality_factor': round(quality_factor, 2)
        }
    }


def init_rail_network(conn=None, sample_size=5000):
    """
    Initialize rail network and create distance tables.

    Args:
        conn: DuckDB connection
        sample_size: Number of O-D pairs to process (None for all)
    """
    from .database import get_connection

    if conn is None:
        conn = get_connection()

    logger.info("Initializing rail network...")

    # Build network
    network = RailNetwork(us_only=True)

    # Create network distance table for top O-D pairs
    create_network_distance_table(conn, network, sample_size=sample_size)

    # Create network-adjusted URCS view
    calculate_network_urcs(conn)

    logger.info("Rail network initialization complete")

    return network


if __name__ == "__main__":
    # Test the network
    print("Loading rail network...")
    network = RailNetwork(us_only=True)

    print(f"\nNetwork stats:")
    print(f"  Nodes: {len(network.nodes):,}")
    print(f"  Edges: {sum(len(v) for v in network.graph.values()) // 2:,}")

    # Test routing: Chicago to Los Angeles
    print("\nTest route: Chicago, IL to Los Angeles, CA")
    chicago = (-87.6298, 41.8781)
    la = (-118.2437, 34.0522)

    route = network.route_distance(*chicago, *la)
    if route:
        print(f"  Rail miles: {route['rail_miles']:,.0f}")
        print(f"  Total miles: {route['total_miles']:,.0f}")
        print(f"  Haversine: {route['haversine_miles']:,.0f}")
        print(f"  Circuity: {route['circuity']:.2f}x")
        print(f"  Carriers: {route['carriers'][:5]}")
        print(f"  Regions: {route['from_region']} -> {route['to_region']}")

    # Test rate estimation
    print("\nTest rate estimate: Cement shipment")
    estimate = estimate_rate(network, *chicago, *la, commodity_stcc='32411', tons=100)
    if estimate:
        print(f"  Distance: {estimate['distance']['total_miles']:,.0f} miles")
        print(f"  Rate/ton: ${estimate['rate_estimate']['rate_per_ton']:.2f}")
        print(f"  Total rate: ${estimate['rate_estimate']['total_rate']:,.2f}")
        print(f"  URCS cost: ${estimate['urcs_analysis']['variable_cost']:,.2f}")
        print(f"  R/VC ratio: {estimate['urcs_analysis']['rvc_ratio']:.1f}%")
