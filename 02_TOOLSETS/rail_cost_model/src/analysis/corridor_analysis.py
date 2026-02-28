"""
Rail Corridor Analysis
Identifies high-cost and high-volume corridors
"""

import pandas as pd
import networkx as nx
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def identify_bottleneck_segments(
    graph: nx.MultiDiGraph,
    flow_assignments: Dict[Tuple[int, int], Dict]
) -> List[Dict]:
    """
    Identify network segments with high flow volume.
    
    Args:
        graph: NetworkX graph
        flow_assignments: Dict mapping (u,v) edges to flow data
        
    Returns:
        List of bottleneck segments sorted by tonnage
    """
    logger.info("Identifying bottleneck segments...")
    
    segment_flows = {}
    
    for (u, v), flow_data in flow_assignments.items():
        key = (u, v)
        if key not in segment_flows:
            # Get edge attributes
            edge_data = list(graph.get_edge_data(u, v).values())[0] if graph.has_edge(u, v) else {}
            
            segment_flows[key] = {
                'origin_node': u,
                'destination_node': v,
                'total_tons': 0,
                'num_flows': 0,
                'miles': edge_data.get('miles', 0),
                'owner': edge_data.get('owner', 'UNKNOWN')
            }
        
        segment_flows[key]['total_tons'] += flow_data.get('tons', 0)
        segment_flows[key]['num_flows'] += 1
    
    # Convert to list and sort
    bottlenecks = sorted(
        segment_flows.values(),
        key=lambda x: x['total_tons'],
        reverse=True
    )
    
    logger.info(f"  Analyzed {len(bottlenecks)} unique segments")
    if bottlenecks:
        logger.info(f"  Top segment: {bottlenecks[0]['total_tons']:,.0f} tons")
    
    return bottlenecks[:20]  # Top 20


def calculate_corridor_costs(
    graph: nx.MultiDiGraph,
    corridors_df: pd.DataFrame,
    cost_calculator
) -> pd.DataFrame:
    """
    Calculate costs for each corridor.
    
    Args:
        graph: NetworkX graph
        corridors_df: DataFrame with origin, destination, tons
        cost_calculator: RouteCostCalculator instance
        
    Returns:
        DataFrame with cost estimates
    """
    logger.info("Calculating corridor costs...")
    
    costs = []
    
    for idx, row in corridors_df.iterrows():
        # This would need actual origin/destination node mapping
        # For now, use simplified cost estimate
        
        tons = row.get('tons', 0)
        
        # Estimate: assume 500 mile average corridor
        est_miles = 500
        est_cars = max(1, tons / 100)  # 100 tons per car
        
        cost_result = cost_calculator.calculate_route_cost(
            route_miles=est_miles,
            commodity_tons=tons,
            num_cars=int(est_cars),
            num_interchanges=1
        )
        
        cost_info = {
            'corridor': f"{row.get('origin', '?')}-{row.get('destination', '?')}",
            'tons': tons,
            'estimated_miles': est_miles,
            'estimated_cost': cost_result['total_variable_cost'],
            'cost_per_ton': cost_result['cost_per_ton']
        }
        costs.append(cost_info)
    
    result = pd.DataFrame(costs)
    logger.info(f"  Calculated costs for {len(result)} corridors")
    
    return result


def rank_corridors_by_cost_efficiency(
    corridors_with_costs: pd.DataFrame
) -> pd.DataFrame:
    """Rank corridors by cost per ton-mile."""
    if 'cost_per_ton' not in corridors_with_costs.columns:
        logger.error("Missing cost_per_ton column")
        return corridors_with_costs
    
    # Calculate cost per ton-mile
    corridors_with_costs['cost_per_ton_mile'] = (
        corridors_with_costs['cost_per_ton'] / 
        corridors_with_costs.get('estimated_miles', 1)
    )
    
    # Sort by efficiency (lower cost/ton-mile is better)
    ranked = corridors_with_costs.sort_values('cost_per_ton_mile')
    
    logger.info("Corridor ranking complete")
    
    return ranked
