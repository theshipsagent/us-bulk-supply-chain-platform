"""
Network Topology Analysis
Validates and analyzes rail network connectivity
"""

import networkx as nx
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def analyze_connectivity(graph: nx.MultiDiGraph) -> Dict:
    """Analyze network connectivity."""
    logger.info("Analyzing network connectivity...")
    
    # Find connected components
    weak_components = list(nx.weakly_connected_components(graph))
    strong_components = list(nx.strongly_connected_components(graph))
    
    # Get largest component
    largest_weak = max(weak_components, key=len)
    
    analysis = {
        'total_nodes': graph.number_of_nodes(),
        'total_edges': graph.number_of_edges(),
        'weak_components': len(weak_components),
        'strong_components': len(strong_components),
        'largest_component_size': len(largest_weak),
        'largest_component_pct': len(largest_weak) / graph.number_of_nodes() * 100
    }
    
    logger.info(f"  {analysis['weak_components']} weakly connected components")
    logger.info(f"  Largest component: {analysis['largest_component_pct']:.1f}% of nodes")
    
    return analysis


def find_isolated_nodes(graph: nx.MultiDiGraph) -> List:
    """Find nodes with no connections."""
    isolated = [node for node in graph.nodes() if graph.degree(node) == 0]
    logger.info(f"Found {len(isolated)} isolated nodes")
    return isolated


def validate_network(graph: nx.MultiDiGraph) -> bool:
    """Validate network structure."""
    logger.info("Validating network...")
    
    # Check for isolated nodes
    isolated = find_isolated_nodes(graph)
    if len(isolated) > 0:
        logger.warning(f"  {len(isolated)} isolated nodes found")
    
    # Check connectivity
    connectivity = analyze_connectivity(graph)
    
    if connectivity['largest_component_pct'] < 90:
        logger.warning(f"  Largest component only {connectivity['largest_component_pct']:.1f}% of network")
    
    logger.info("Validation complete")
    return True
