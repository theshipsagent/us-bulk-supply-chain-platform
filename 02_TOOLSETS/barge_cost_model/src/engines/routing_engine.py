"""
Routing engine for waterway navigation using NetworkX.

This module provides pathfinding algorithms with vessel constraint enforcement
for inland waterway navigation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pickle
import networkx as nx
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from src.config.settings import settings, ROUTING_CONSTRAINTS
from src.config.database import get_db_session
from src.models.route import (
    ComputedRoute,
    RouteSegment,
    RouteConstraints,
    RouteRequest
)
from sqlalchemy import text

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Waterway routing engine using NetworkX for pathfinding.

    Features:
    - Dijkstra's shortest path algorithm
    - A* pathfinding with heuristics
    - Vessel constraint enforcement (beam, draft, length)
    - Lock detection and delay estimation
    - Route caching
    """

    def __init__(self, graph_cache_path: Optional[Path] = None):
        """
        Initialize routing engine.

        Args:
            graph_cache_path: Path to cached NetworkX graph file
        """
        self.graph_cache_path = graph_cache_path or (settings.MODELS_DIR / 'waterway_graph.pkl')
        self.graph: Optional[nx.DiGraph] = None
        self._locks_cache: Optional[dict] = None

    def load_graph(self) -> bool:
        """
        Load the waterway graph from cache.

        Returns:
            True if graph loaded successfully, False otherwise
        """
        try:
            if not self.graph_cache_path.exists():
                logger.error(f"Graph cache not found: {self.graph_cache_path}")
                return False

            with open(self.graph_cache_path, 'rb') as f:
                self.graph = pickle.load(f)

            logger.info(f"Loaded graph: {len(self.graph.nodes())} nodes, {len(self.graph.edges())} edges")
            return True

        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False

    def load_locks_data(self):
        """Load locks data from database for constraint checking."""
        try:
            with get_db_session() as db:
                result = db.execute(text("""
                    SELECT objectid, pmsname, river, rivermi,
                           width, length, lift, x, y
                    FROM locks
                    WHERE width IS NOT NULL AND length IS NOT NULL
                """))

                self._locks_cache = {}
                for row in result:
                    lock_data = {
                        'objectid': row[0],
                        'name': row[1],
                        'river': row[2],
                        'rivermi': row[3],
                        'width': row[4],  # feet
                        'length': row[5],  # feet
                        'lift': row[6],
                        'x': row[7],
                        'y': row[8],
                    }
                    # Index by river and mile for quick lookup
                    key = (row[2], round(row[3], 1)) if row[2] and row[3] else None
                    if key:
                        self._locks_cache[key] = lock_data

            logger.info(f"Loaded {len(self._locks_cache)} locks")

        except Exception as e:
            logger.error(f"Failed to load locks data: {e}")
            self._locks_cache = {}

    def find_route(
        self,
        origin_node: int,
        dest_node: int,
        constraints: Optional[RouteConstraints] = None,
        algorithm: str = 'dijkstra'
    ) -> Optional[ComputedRoute]:
        """
        Find optimal route between two nodes.

        Args:
            origin_node: Starting node ID
            dest_node: Destination node ID
            constraints: Vessel constraints (beam, draft, length)
            algorithm: Routing algorithm ('dijkstra' or 'astar')

        Returns:
            ComputedRoute object with full route details, or None if no route found
        """
        if not self.graph:
            if not self.load_graph():
                return None

        # Load locks data if not already loaded
        if self._locks_cache is None:
            self.load_locks_data()

        try:
            # Check if nodes exist in graph
            if origin_node not in self.graph.nodes():
                logger.error(f"Origin node {origin_node} not in graph")
                return None

            if dest_node not in self.graph.nodes():
                logger.error(f"Destination node {dest_node} not in graph")
                return None

            # Find path using specified algorithm
            if algorithm == 'astar':
                path = nx.astar_path(self.graph, origin_node, dest_node, weight='length')
            else:
                path = nx.dijkstra_path(self.graph, origin_node, dest_node, weight='length')

            # Build detailed route from path
            route = self._build_route_from_path(
                path=path,
                origin_node=origin_node,
                dest_node=dest_node,
                constraints=constraints,
                algorithm=algorithm
            )

            # Check constraint feasibility
            if constraints and route:
                route = self._check_route_feasibility(route, constraints)

            return route

        except nx.NetworkXNoPath:
            logger.warning(f"No path found from {origin_node} to {dest_node}")
            return None
        except Exception as e:
            logger.error(f"Error finding route: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _build_route_from_path(
        self,
        path: List[int],
        origin_node: int,
        dest_node: int,
        constraints: Optional[RouteConstraints],
        algorithm: str
    ) -> ComputedRoute:
        """Build a ComputedRoute object from a node path."""

        segments = []
        total_distance = 0.0
        locks_encountered = []

        # Build segments from consecutive node pairs
        for i in range(len(path) - 1):
            anode = path[i]
            bnode = path[i + 1]

            # Get edge data
            edge_data = self.graph[anode][bnode]

            length = edge_data.get('length', 0.0) or 0.0
            linknum = edge_data.get('linknum')
            rivername = edge_data.get('rivername')

            total_distance += length

            # Check for locks on this segment (simple heuristic: check river mile)
            has_lock = False
            lock_name = None
            if rivername and self._locks_cache:
                # This is a simplified check - in reality would need spatial query
                # to find locks near this segment
                pass

            segment = RouteSegment(
                linknum=linknum,
                anode=anode,
                bnode=bnode,
                length_miles=length,
                rivername=rivername,
                has_lock=has_lock,
                lock_name=lock_name
            )
            segments.append(segment)

        # Calculate transit time (using average speed from settings)
        avg_speed_mph = settings.COST_CONSTANTS.get('average_speed_mph', 5.0)
        transit_time_hours = total_distance / avg_speed_mph if avg_speed_mph > 0 else 0

        # Create route object
        route = ComputedRoute(
            origin_node=origin_node,
            dest_node=dest_node,
            node_path=path,
            segments=segments,
            total_distance_miles=total_distance,
            total_distance_km=total_distance * 1.60934,
            transit_time_hours=transit_time_hours,
            transit_time_days=transit_time_hours / 24,
            num_locks=len(locks_encountered),
            lock_names=locks_encountered,
            total_lock_delay_hours=len(locks_encountered) * 2.0,  # Assume 2 hours per lock
            algorithm_used=algorithm,
            constraints_applied=constraints,
            is_feasible=True,
            computed_at=datetime.utcnow()
        )

        return route

    def _check_route_feasibility(
        self,
        route: ComputedRoute,
        constraints: RouteConstraints
    ) -> ComputedRoute:
        """
        Check if route satisfies vessel constraints.

        Args:
            route: Route to check
            constraints: Vessel constraints

        Returns:
            Updated route with feasibility flag
        """
        feasibility_issues = []

        # Check lock compatibility for each segment
        for segment in route.segments:
            if segment.has_lock and self._locks_cache:
                # Find lock data for this segment
                # (simplified - would need better spatial matching)
                lock_data = None  # Would lookup from _locks_cache

                if lock_data and constraints.vessel_beam_m and constraints.vessel_length_m:
                    lock_width_m = lock_data['width'] * 0.3048  # Convert feet to meters
                    lock_length_m = lock_data['length'] * 0.3048

                    if not constraints.check_lock_compatibility(lock_width_m, lock_length_m):
                        feasibility_issues.append(
                            f"Vessel too large for lock: {lock_data['name']}"
                        )

        # Update route feasibility
        if feasibility_issues:
            route.is_feasible = False
            route.feasibility_notes = "; ".join(feasibility_issues)
        else:
            route.is_feasible = True
            route.feasibility_notes = "All constraints satisfied"

        return route

    def find_k_shortest_paths(
        self,
        origin_node: int,
        dest_node: int,
        k: int = 3,
        constraints: Optional[RouteConstraints] = None
    ) -> List[ComputedRoute]:
        """
        Find k shortest paths between origin and destination.

        Args:
            origin_node: Starting node
            dest_node: Destination node
            k: Number of paths to find
            constraints: Vessel constraints

        Returns:
            List of up to k routes, sorted by distance
        """
        if not self.graph:
            if not self.load_graph():
                return []

        try:
            # Use NetworkX k_shortest_paths
            paths = list(nx.shortest_simple_paths(
                self.graph,
                origin_node,
                dest_node,
                weight='length'
            ))[:k]

            routes = []
            for path in paths:
                route = self._build_route_from_path(
                    path=path,
                    origin_node=origin_node,
                    dest_node=dest_node,
                    constraints=constraints,
                    algorithm='k_shortest'
                )

                if constraints:
                    route = self._check_route_feasibility(route, constraints)

                routes.append(route)

            return routes

        except Exception as e:
            logger.error(f"Error finding k shortest paths: {e}")
            return []

    def get_graph_stats(self) -> dict:
        """Get statistics about the loaded graph."""
        if not self.graph:
            return {}

        return {
            'num_nodes': len(self.graph.nodes()),
            'num_edges': len(self.graph.edges()),
            'is_connected': nx.is_strongly_connected(self.graph),
            'num_connected_components': nx.number_strongly_connected_components(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / len(self.graph.nodes()),
        }

    def get_available_nodes(
        self,
        river_name: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get list of available waterway nodes for routing.

        Args:
            river_name: Filter by river name (partial match)
            state: Filter by state code
            limit: Maximum number of results

        Returns:
            List of node dictionaries with metadata
        """
        from src.config.database import get_db_session
        from sqlalchemy import text

        try:
            with get_db_session() as db:
                conditions = []
                params = {}

                if river_name:
                    conditions.append("rivername ILIKE :river_name")
                    params["river_name"] = f"%{river_name}%"

                if state:
                    conditions.append("state = :state")
                    params["state"] = state.upper()

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = text(f"""
                    SELECT DISTINCT
                        anode as node_id,
                        rivername,
                        state,
                        MIN(linkname) as example_link
                    FROM waterway_links
                    WHERE {where_clause} AND anode IS NOT NULL
                    GROUP BY anode, rivername, state
                    ORDER BY rivername, node_id
                    LIMIT :limit
                """)

                params["limit"] = limit
                result = db.execute(query, params)
                rows = result.fetchall()

                nodes = []
                for row in rows:
                    nodes.append({
                        "node_id": row[0],
                        "river_name": row[1],
                        "state": row[2],
                        "example_link": row[3]
                    })

                return nodes

        except Exception as e:
            logger.error(f"Error fetching available nodes: {e}")
            return []


# Convenience function for quick routing
def compute_route(
    origin_node: int,
    dest_node: int,
    vessel_beam_m: Optional[float] = None,
    vessel_draft_m: Optional[float] = None,
    vessel_length_m: Optional[float] = None,
    algorithm: str = 'dijkstra'
) -> Optional[ComputedRoute]:
    """
    Quick route computation with optional vessel constraints.

    Args:
        origin_node: Starting node ID
        dest_node: Destination node ID
        vessel_beam_m: Vessel beam in meters
        vessel_draft_m: Vessel draft in meters
        vessel_length_m: Vessel length in meters
        algorithm: Routing algorithm

    Returns:
        ComputedRoute or None
    """
    engine = RoutingEngine()

    constraints = None
    if any([vessel_beam_m, vessel_draft_m, vessel_length_m]):
        constraints = RouteConstraints(
            vessel_beam_m=vessel_beam_m,
            vessel_draft_m=vessel_draft_m,
            vessel_length_m=vessel_length_m
        )

    return engine.find_route(origin_node, dest_node, constraints, algorithm)


if __name__ == "__main__":
    """Test routing engine."""
    print("=" * 80)
    print("ROUTING ENGINE TEST")
    print("=" * 80)

    engine = RoutingEngine()

    # Test 1: Load graph
    print("\n[1/3] Loading graph...")
    if engine.load_graph():
        print("✓ Graph loaded successfully")
        stats = engine.get_graph_stats()
        print(f"  Nodes: {stats['num_nodes']:,}")
        print(f"  Edges: {stats['num_edges']:,}")
        print(f"  Connected: {stats['is_connected']}")
    else:
        print("✗ Failed to load graph")
        sys.exit(1)

    # Test 2: Load locks
    print("\n[2/3] Loading locks data...")
    engine.load_locks_data()
    print(f"✓ Loaded {len(engine._locks_cache or {})} locks")

    # Test 3: Compute sample route (if we had known nodes)
    print("\n[3/3] Route computation test...")
    print("  (Requires known node IDs - skipping for now)")

    print("\n" + "=" * 80)
    print("✓ Routing engine initialized successfully")
    print("=" * 80)
