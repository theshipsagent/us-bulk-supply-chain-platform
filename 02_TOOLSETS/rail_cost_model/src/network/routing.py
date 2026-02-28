"""
Network Routing Functions
Shortest path and flow assignment algorithms
"""

import networkx as nx
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def shortest_path_distance(
    graph: nx.MultiDiGraph,
    origin: int,
    destination: int,
    weight: str = 'miles'
) -> Tuple[List, float]:
    """Find shortest path by specified weight."""
    try:
        path = nx.shortest_path(graph, origin, destination, weight=weight)
        length = nx.shortest_path_length(graph, origin, destination, weight=weight)
        return path, length
    except nx.NetworkXNoPath:
        logger.warning(f"No path found from {origin} to {destination}")
        return [], float('inf')
    except nx.NodeNotFound as e:
        logger.error(f"Node not found: {e}")
        return [], float('inf')


def k_shortest_paths(
    graph: nx.MultiDiGraph,
    origin: int,
    destination: int,
    k: int = 3,
    weight: str = 'miles'
) -> List[Tuple[List, float]]:
    """Find k shortest paths."""
    try:
        paths = []
        for path in nx.shortest_simple_paths(graph, origin, destination, weight=weight):
            length = sum(
                graph[path[i]][path[i+1]][0].get(weight, 0)
                for i in range(len(path)-1)
            )
            paths.append((path, length))
            if len(paths) >= k:
                break
        return paths
    except nx.NetworkXNoPath:
        logger.warning(f"No paths found from {origin} to {destination}")
        return []


def find_nearest_node_to_point(
    graph: nx.MultiDiGraph,
    lon: float,
    lat: float,
    max_candidates: int = 10
) -> Optional[int]:
    """Find nearest graph node to a lat/lon point."""
    min_dist = float('inf')
    nearest = None
    
    # Simple linear search (could use spatial index for large graphs)
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        node_lon = node_data.get('lon')
        node_lat = node_data.get('lat')
        
        if node_lon is None or node_lat is None:
            continue
        
        # Euclidean distance (approximate)
        dist = ((lon - node_lon)**2 + (lat - node_lat)**2)**0.5
        
        if dist < min_dist:
            min_dist = dist
            nearest = node_id
    
    return nearest
