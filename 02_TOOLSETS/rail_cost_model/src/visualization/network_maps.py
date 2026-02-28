"""
Network Visualization Module
Creates interactive maps of rail network and flows
"""

import folium
from folium import plugins
import geopandas as gpd
import pandas as pd
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


def create_network_map(
    lines_gdf: gpd.GeoDataFrame,
    nodes_gdf: Optional[gpd.GeoDataFrame] = None,
    yards_gdf: Optional[gpd.GeoDataFrame] = None,
    center: tuple = (39.8283, -98.5795),  # Center of US
    zoom: int = 4
) -> folium.Map:
    """Create interactive Folium map of rail network."""
    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='cartodbpositron'
    )
    
    # Add rail lines
    logger.info("Adding rail lines to map...")
    
    # Color by owner (simplified)
    owner_colors = {
        'BNSF': '#FF6600',
        'UP': '#FFD700', 
        'NS': '#000000',
        'CSX': '#0000FF',
        'CN': '#FF0000',
        'CP': '#008000',
        'KCS': '#800080',
    }
    
    for idx, row in lines_gdf.iterrows():
        if row.geometry is None:
            continue
            
        owner = row.get('RROWNER1', 'OTHER')
        color = owner_colors.get(owner, '#808080')
        
        # Convert to coordinates
        if row.geometry.geom_type == 'LineString':
            coords = [[lat, lon] for lon, lat in row.geometry.coords]
        elif row.geometry.geom_type == 'MultiLineString':
            coords = [[lat, lon] for line in row.geometry.geoms for lon, lat in line.coords]
        else:
            continue
        
        folium.PolyLine(
            coords,
            weight=2,
            color=color,
            opacity=0.7,
            popup=f"Owner: {owner}"
        ).add_to(m)
    
    # Add yards if provided
    if yards_gdf is not None:
        logger.info("Adding rail yards to map...")
        yard_group = folium.FeatureGroup(name='Rail Yards')
        
        for idx, row in yards_gdf.iterrows():
            if row.geometry is None:
                continue
            
            centroid = row.geometry.centroid
            
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=5,
                color='red',
                fill=True,
                popup=row.get('YARDNAME', 'Unknown Yard')
            ).add_to(yard_group)
        
        yard_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m


def highlight_route(
    m: folium.Map,
    graph,
    path: List[int],
    color: str = 'red',
    weight: int = 5
) -> folium.Map:
    """Highlight a specific route on an existing map."""
    coords = []
    
    for node_id in path:
        node_data = graph.nodes[node_id]
        coords.append([node_data['lat'], node_data['lon']])
    
    folium.PolyLine(
        coords,
        weight=weight,
        color=color,
        opacity=0.9,
        popup='Selected Route'
    ).add_to(m)
    
    # Add markers for origin/destination
    folium.Marker(
        coords[0],
        icon=folium.Icon(color='green'),
        popup='Origin'
    ).add_to(m)
    
    folium.Marker(
        coords[-1],
        icon=folium.Icon(color='red'),
        popup='Destination'
    ).add_to(m)
    
    return m
