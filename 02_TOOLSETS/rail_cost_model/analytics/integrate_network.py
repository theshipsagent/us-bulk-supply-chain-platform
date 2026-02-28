"""
Rail Network Database Integration

Integrates the NTAD rail network routing with the DuckDB waybill database:
1. Creates v_waybill_with_distance (Haversine-based estimates)
2. Builds dim_network_distance with actual rail routing for top O-D pairs
3. Creates v_waybill_network_distance and v_network_urcs_analysis views

Run from project root:
    python rail_analytics/integrate_network.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_connection
from src.rail_network import RailNetwork, create_network_distance_table, calculate_network_urcs
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_prerequisite_views(conn):
    """Create views that need to exist before network integration."""

    logger.info("Creating prerequisite views...")

    # First, ensure we have the distance estimation view with Haversine
    conn.execute("""
        CREATE OR REPLACE VIEW v_waybill_with_distance AS
        SELECT
            w.*,
            o.lat as origin_lat,
            o.lon as origin_lon,
            o.bea_name as origin_name,
            o.region as origin_region,
            d.lat as dest_lat,
            d.lon as dest_lon,
            d.bea_name as dest_name,
            d.region as dest_region,
            -- Haversine distance formula (straight-line miles)
            CASE
                WHEN o.lat IS NOT NULL AND d.lat IS NOT NULL THEN
                    3959 * 2 * ASIN(SQRT(
                        POWER(SIN(RADIANS(d.lat - o.lat) / 2), 2) +
                        COS(RADIANS(o.lat)) * COS(RADIANS(d.lat)) *
                        POWER(SIN(RADIANS(d.lon - o.lon) / 2), 2)
                    ))
                ELSE NULL
            END as haversine_miles,
            -- Estimated rail miles (apply circuity factor of ~1.20)
            CASE
                WHEN o.lat IS NOT NULL AND d.lat IS NOT NULL THEN
                    3959 * 2 * ASIN(SQRT(
                        POWER(SIN(RADIANS(d.lat - o.lat) / 2), 2) +
                        COS(RADIANS(o.lat)) * COS(RADIANS(d.lat)) *
                        POWER(SIN(RADIANS(d.lon - o.lon) / 2), 2)
                    )) * 1.20
                ELSE NULL
            END as est_miles
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    """)

    logger.info("Created v_waybill_with_distance view")

    # Verify the view works
    count = conn.execute("""
        SELECT COUNT(*)
        FROM v_waybill_with_distance
        WHERE est_miles IS NOT NULL
    """).fetchone()[0]
    logger.info(f"  -> {count:,} records have distance estimates")


def get_od_pair_count(conn):
    """Get count of unique O-D pairs with valid coordinates."""
    result = conn.execute("""
        SELECT COUNT(DISTINCT origin_bea || '-' || term_bea) as od_count
        FROM v_waybill_with_distance
        WHERE origin_lat IS NOT NULL AND dest_lat IS NOT NULL
          AND origin_bea != '000' AND term_bea != '000'
    """).fetchone()[0]
    return result


def integrate_network(sample_size=3000):
    """
    Full network integration pipeline.

    Args:
        sample_size: Number of top O-D pairs to route (by shipment count)
                    Use None for all pairs (very slow)
    """
    logger.info("=" * 60)
    logger.info("Rail Network Database Integration")
    logger.info("=" * 60)

    conn = get_connection()

    try:
        # Step 1: Create prerequisite views
        create_prerequisite_views(conn)

        # Step 2: Check O-D pair count
        od_count = get_od_pair_count(conn)
        logger.info(f"\nTotal unique O-D pairs with coordinates: {od_count:,}")

        if sample_size:
            logger.info(f"Processing top {sample_size:,} O-D pairs by volume")
        else:
            logger.info(f"Processing ALL {od_count:,} O-D pairs (this will take a while)")

        # Step 3: Load the rail network
        logger.info("\nStep 1: Loading rail network from NTAD data...")
        network = RailNetwork(us_only=True)
        logger.info(f"  Nodes: {len(network.nodes):,}")
        logger.info(f"  Edges: {sum(len(v) for v in network.graph.values()) // 2:,}")

        # Step 4: Create network distance table
        logger.info("\nStep 2: Calculating network routes for O-D pairs...")
        create_network_distance_table(conn, network, sample_size=sample_size)

        # Verify the table
        route_count = conn.execute("SELECT COUNT(*) FROM dim_network_distance").fetchone()[0]
        logger.info(f"  Created dim_network_distance with {route_count:,} routes")

        # Step 5: Create network-enhanced views
        logger.info("\nStep 3: Creating network-enhanced analytical views...")
        calculate_network_urcs(conn)

        # Step 6: Show sample results
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION COMPLETE - Sample Results")
        logger.info("=" * 60)

        # Sample network distances
        sample = conn.execute("""
            SELECT
                nd.origin_bea,
                o.bea_name as origin,
                nd.term_bea,
                d.bea_name as destination,
                ROUND(nd.haversine_miles, 0) as straight_line_mi,
                ROUND(nd.rail_miles, 0) as rail_mi,
                ROUND(nd.circuity, 2) as circuity,
                nd.num_carriers,
                nd.carriers
            FROM dim_network_distance nd
            LEFT JOIN dim_bea o ON nd.origin_bea = o.bea_code
            LEFT JOIN dim_bea d ON nd.term_bea = d.bea_code
            ORDER BY nd.rail_miles DESC
            LIMIT 10
        """).fetchdf()

        print("\nTop 10 Longest Rail Routes:")
        print(sample.to_string(index=False))

        # Show circuity distribution
        circuity = conn.execute("""
            SELECT
                CASE
                    WHEN circuity < 1.1 THEN '< 1.10x (direct)'
                    WHEN circuity < 1.2 THEN '1.10-1.20x'
                    WHEN circuity < 1.3 THEN '1.20-1.30x'
                    WHEN circuity < 1.4 THEN '1.30-1.40x'
                    ELSE '> 1.40x (indirect)'
                END as circuity_band,
                COUNT(*) as routes,
                ROUND(AVG(rail_miles), 0) as avg_rail_miles
            FROM dim_network_distance
            GROUP BY 1
            ORDER BY 1
        """).fetchdf()

        print("\nCircuity Distribution:")
        print(circuity.to_string(index=False))

        # Regional URCS comparison
        urcs = conn.execute("""
            SELECT
                from_region || ' -> ' || to_region as route_type,
                COUNT(*) as routes,
                ROUND(AVG(rail_miles), 0) as avg_miles,
                ROUND(AVG(circuity), 2) as avg_circuity
            FROM dim_network_distance
            WHERE from_region IS NOT NULL
            GROUP BY 1
            ORDER BY routes DESC
        """).fetchdf()

        print("\nRoutes by Region:")
        print(urcs.to_string(index=False))

        logger.info("\n" + "=" * 60)
        logger.info("Views available for analysis:")
        logger.info("  - v_waybill_with_distance: All waybills with Haversine distance")
        logger.info("  - dim_network_distance: Network-routed O-D pairs")
        logger.info("  - v_waybill_network_distance: Waybills with network miles")
        logger.info("  - v_network_urcs_analysis: URCS cost analysis with regional factors")
        logger.info("=" * 60)

    finally:
        conn.close()


def test_routing(origin_bea='051', dest_bea='034'):
    """
    Test routing between two BEA zones.

    Args:
        origin_bea: Origin BEA code (default: Houston '051')
        dest_bea: Destination BEA code (default: Atlanta '034')
    """
    conn = get_connection()

    # Get coordinates
    result = conn.execute(f"""
        SELECT bea_code, bea_name, lat, lon
        FROM dim_bea
        WHERE bea_code IN ('{origin_bea}', '{dest_bea}')
    """).fetchdf()

    if len(result) < 2:
        print("Could not find both BEA zones")
        return

    origin = result[result['bea_code'] == origin_bea].iloc[0]
    dest = result[result['bea_code'] == dest_bea].iloc[0]

    print(f"\nTest Route: {origin['bea_name']} -> {dest['bea_name']}")
    print("=" * 50)

    # Load network and route
    network = RailNetwork(us_only=True)
    route = network.route_distance(origin['lon'], origin['lat'], dest['lon'], dest['lat'])

    if route:
        print(f"Haversine (straight): {route['haversine_miles']:.0f} miles")
        print(f"Rail network:         {route['rail_miles']:.0f} miles")
        print(f"Circuity factor:      {route['circuity']:.2f}x")
        print(f"Carriers:             {', '.join(route['carriers'][:5])}")
        print(f"Interchanges:         {route['interchanges']}")
        print(f"Mainline %:           {route['mainline_pct']:.0f}%")
        print(f"Region flow:          {route['from_region']} -> {route['to_region']}")
    else:
        print("No route found!")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Integrate rail network with database')
    parser.add_argument('--sample', type=int, default=3000,
                       help='Number of O-D pairs to process (default: 3000, use 0 for all)')
    parser.add_argument('--test', action='store_true',
                       help='Run test routing instead of full integration')
    parser.add_argument('--origin', default='051', help='Origin BEA for test (default: Houston)')
    parser.add_argument('--dest', default='034', help='Dest BEA for test (default: Atlanta)')

    args = parser.parse_args()

    if args.test:
        test_routing(args.origin, args.dest)
    else:
        sample = args.sample if args.sample > 0 else None
        integrate_network(sample_size=sample)
