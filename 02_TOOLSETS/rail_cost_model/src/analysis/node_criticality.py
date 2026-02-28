"""
Node Criticality Analysis
Identifies critical junctions and yards in the network
"""

import networkx as nx
import pandas as pd
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def calculate_betweenness_centrality(
    graph: nx.MultiDiGraph,
    k: int = 1000,
    weight: str = 'miles'
) -> Dict:
    """
    Calculate betweenness centrality for nodes.
    
    Args:
        graph: NetworkX graph
        k: Number of nodes to sample for approximation
        weight: Edge attribute to use as weight
        
    Returns:
        Dictionary mapping node_id to betweenness centrality value
    """
    logger.info("Calculating betweenness centrality...")
    logger.info(f"  Using sample of {k} nodes for approximation")
    
    # For large graphs, use k-node sample
    try:
        bc = nx.betweenness_centrality(graph, k=k, weight=weight)
        logger.info("  Betweenness centrality calculated")
        logger.info(f"  Max centrality: {max(bc.values()):.6f}")
        return bc
    except Exception as e:
        logger.error(f"Error calculating betweenness: {e}")
        return {}


def identify_critical_yards(
    graph: nx.MultiDiGraph,
    centrality: Dict[int, float]
) -> List[Dict]:
    """
    Identify critical yard nodes.
    
    Args:
        graph: NetworkX graph
        centrality: Betweenness centrality scores
        
    Returns:
        List of critical yards with metrics
    """
    logger.info("Identifying critical yards...")
    
    critical_yards = []
    
    for node_id, bc_value in centrality.items():
        node_data = graph.nodes.get(node_id, {})
        
        if node_data.get('is_yard', False):
            critical_yards.append({
                'node_id': node_id,
                'yard_name': node_data.get('yard_name', 'Unknown'),
                'yard_type': node_data.get('yard_type', 'Unknown'),
                'betweenness': bc_value,
                'degree': graph.degree(node_id),
                'lat': node_data.get('lat'),
                'lon': node_data.get('lon')
            })
    
    # Sort by betweenness
    critical_yards.sort(key=lambda x: x['betweenness'], reverse=True)
    
    logger.info(f"  Identified {len(critical_yards)} yard nodes")
    
    return critical_yards[:20]  # Top 20


def identify_critical_junctions(
    graph: nx.MultiDiGraph,
    centrality: Dict[int, float],
    min_degree: int = 3
) -> List[Dict]:
    """
    Identify critical junction nodes (high degree, high betweenness).
    
    Args:
        graph: NetworkX graph
        centrality: Betweenness centrality scores
        min_degree: Minimum node degree to consider
        
    Returns:
        List of critical junctions
    """
    logger.info("Identifying critical junctions...")
    
    junctions = []
    
    for node_id, bc_value in centrality.items():
        degree = graph.degree(node_id)
        
        if degree >= min_degree:
            node_data = graph.nodes.get(node_id, {})
            
            junctions.append({
                'node_id': node_id,
                'betweenness': bc_value,
                'degree': degree,
                'lat': node_data.get('lat'),
                'lon': node_data.get('lon')
            })
    
    # Sort by betweenness
    junctions.sort(key=lambda x: x['betweenness'], reverse=True)
    
    logger.info(f"  Identified {len(junctions)} high-degree junctions")
    
    return junctions[:30]  # Top 30


def calculate_node_importance_scores(
    graph: nx.MultiDiGraph
) -> pd.DataFrame:
    """
    Calculate multiple importance metrics for all nodes.
    
    Returns:
        DataFrame with node_id and various centrality measures
    """
    logger.info("Calculating node importance scores...")
    
    # Degree centrality (fast)
    logger.info("  Computing degree centrality...")
    degree_cent = nx.degree_centrality(graph)
    
    # Betweenness (approximate)
    logger.info("  Computing betweenness centrality (sample)...")
    betweenness = nx.betweenness_centrality(graph, k=1000)
    
    # Combine into DataFrame
    scores = pd.DataFrame({
        'node_id': list(degree_cent.keys()),
        'degree_centrality': list(degree_cent.values()),
        'betweenness_centrality': [betweenness.get(n, 0) for n in degree_cent.keys()]
    })
    
    # Add lat/lon if available
    scores['lat'] = scores['node_id'].apply(lambda n: graph.nodes.get(n, {}).get('lat'))
    scores['lon'] = scores['node_id'].apply(lambda n: graph.nodes.get(n, {}).get('lon'))
    
    logger.info(f"  Calculated scores for {len(scores)} nodes")
    
    return scores
