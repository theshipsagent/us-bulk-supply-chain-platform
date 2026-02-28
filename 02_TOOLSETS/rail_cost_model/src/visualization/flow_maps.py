"""
Commodity Flow Visualization
"""

import folium
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def create_flow_map(
    flows_df: pd.DataFrame,
    center: tuple = (39.8283, -98.5795),
    zoom: int = 4
) -> folium.Map:
    """Create map showing commodity flows with line thickness by volume."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='cartodbpositron'
    )
    
    # flows_df should have: origin_lat, origin_lon, dest_lat, dest_lon, tons
    max_tons = flows_df['tons'].max() if 'tons' in flows_df.columns else 1
    
    for idx, row in flows_df.iterrows():
        weight = 1 + (row.get('tons', 0) / max_tons) * 10
        
        folium.PolyLine(
            [
                [row['origin_lat'], row['origin_lon']],
                [row['dest_lat'], row['dest_lon']]
            ],
            weight=weight,
            color='blue',
            opacity=0.5,
            popup=f"Tons: {row.get('tons', 0):,.0f}"
        ).add_to(m)
    
    return m
