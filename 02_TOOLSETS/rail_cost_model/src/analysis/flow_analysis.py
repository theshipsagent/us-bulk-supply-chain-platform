"""
Commodity Flow Analysis
Analyzes freight flows on the rail network
"""

import pandas as pd
import networkx as nx
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def aggregate_flows_by_corridor(flows_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate flows by origin-destination corridor."""
    logger.info("Aggregating flows by corridor...")
    
    required_cols = ['origin', 'destination', 'tons']
    if not all(col in flows_df.columns for col in required_cols):
        logger.error(f"Missing required columns. Need: {required_cols}")
        return pd.DataFrame()
    
    corridor_flows = flows_df.groupby(['origin', 'destination']).agg({
        'tons': 'sum',
        'value': 'sum' if 'value' in flows_df.columns else 'count'
    }).reset_index()
    
    logger.info(f"  {len(corridor_flows)} unique corridors")
    
    return corridor_flows


def identify_top_corridors(flows_df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Identify top N corridors by tonnage."""
    if 'tons' not in flows_df.columns:
        logger.error("'tons' column not found in flows DataFrame")
        return pd.DataFrame()
    
    top = flows_df.nlargest(n, 'tons')
    total_tonnage = flows_df['tons'].sum()
    
    if total_tonnage > 0:
        pct = top['tons'].sum() / total_tonnage * 100
        logger.info(f"Top {n} corridors represent {pct:.1f}% of total tonnage")
    
    return top


def analyze_commodity_mix(flows_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze commodity distribution in flows."""
    if 'commodity' not in flows_df.columns and 'sctg' not in flows_df.columns:
        logger.warning("No commodity column found")
        return pd.DataFrame()
    
    commodity_col = 'commodity' if 'commodity' in flows_df.columns else 'sctg'
    
    commodity_summary = flows_df.groupby(commodity_col).agg({
        'tons': 'sum',
        'value': 'sum' if 'value' in flows_df.columns else 'count'
    }).reset_index()
    
    commodity_summary = commodity_summary.sort_values('tons', ascending=False)
    
    logger.info(f"  {len(commodity_summary)} unique commodities")
    
    return commodity_summary
