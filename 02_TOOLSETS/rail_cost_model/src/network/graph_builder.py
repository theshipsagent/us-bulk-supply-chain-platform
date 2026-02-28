"""
Rail Network Graph Builder
Constructs NetworkX graph from NARN geospatial data

Graph structure:
- Nodes: Rail junctions, terminals, interchange points
- Edges: Track segments with attributes (distance, owner, track class)

Key attributes for routing/costing:
- Edge: miles, owner, track_class, signals, max_speed
- Node: node_type, yard_indicator, interchange_indicator
"""

import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RailNetworkGraph:
    """Build and manage rail network graph."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed multigraph for parallel tracks
        self.node_gdf = None
        self.edge_gdf = None
        
    def build_from_narn(
        self, 
        lines_gdf: gpd.GeoDataFrame, 
        nodes_gdf: gpd.GeoDataFrame,
        yards_gdf: Optional[gpd.GeoDataFrame] = None
    ) -> nx.MultiDiGraph:
        """
        Build NetworkX graph from NARN line and node data.
        
        Process:
        1. Index nodes by geometry for fast lookup
        2. For each line segment, identify start/end nodes
        3. Create edge with attributes
        4. Validate topology
        """
        logger.info("Building rail network graph...")
        
        # Ensure consistent CRS
        target_crs = "EPSG:4326"
        lines_gdf = lines_gdf.to_crs(target_crs)
        nodes_gdf = nodes_gdf.to_crs(target_crs)
        
        # Store for reference
        self.edge_gdf = lines_gdf.copy()
        self.node_gdf = nodes_gdf.copy()
        
        # Create spatial index for nodes
        logger.info("  Building spatial index for nodes...")
        node_sindex = nodes_gdf.sindex
        
        # Add nodes to graph
        logger.info(f"  Adding {len(nodes_gdf)} nodes...")
        for idx, row in nodes_gdf.iterrows():
            node_id = row.get('FRANODEID', idx)
            self.graph.add_node(
                node_id,
                geometry=row.geometry,
                lon=row.geometry.x,
                lat=row.geometry.y,
                **{k: v for k, v in row.items() if k != 'geometry'}
            )
        
        # Add edges from line segments
        logger.info(f"  Processing {len(lines_gdf)} line segments...")
        edges_added = 0
        edges_failed = 0
        
        for idx, row in lines_gdf.iterrows():
            try:
                # Get start and end points of line
                line = row.geometry
                start_point = Point(line.coords[0])
                end_point = Point(line.coords[-1])
                
                # Find nearest nodes
                start_node = self._find_nearest_node(start_point, nodes_gdf, node_sindex)
                end_node = self._find_nearest_node(end_point, nodes_gdf, node_sindex)
                
                if start_node is not None and end_node is not None:
                    # Calculate length in miles
                    length_miles = self._calculate_length_miles(line)
                    
                    # Extract edge attributes
                    edge_attrs = {
                        'geometry': line,
                        'miles': length_miles,
                        'owner': row.get('RROWNER1', 'UNKNOWN'),
                        'track_class': row.get('TRKCLASS', None),
                        'signals': row.get('SIGNALS', None),
                        'stracnet': row.get('STRACNET', None),
                        'link_id': row.get('OBJECTID', idx)
                    }
                    
                    # Add edge (both directions for undirected routing)
                    self.graph.add_edge(start_node, end_node, **edge_attrs)
                    edges_added += 1
                else:
                    edges_failed += 1
                    
            except Exception as e:
                logger.debug(f"  Error processing line {idx}: {e}")
                edges_failed += 1
        
        logger.info(f"  Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        logger.info(f"  Edges added: {edges_added}, failed: {edges_failed}")
        
        # Add yard information if available
        if yards_gdf is not None:
            self._add_yard_attributes(yards_gdf)
        
        return self.graph

    def _find_nearest_node(
        self, 
        point: Point, 
        nodes_gdf: gpd.GeoDataFrame, 
        sindex,
        tolerance: float = 0.001  # ~100m at mid-latitudes
    ) -> Optional[int]:
        """Find nearest node within tolerance."""
        # Query spatial index
        bounds = (
            point.x - tolerance,
            point.y - tolerance,
            point.x + tolerance,
            point.y + tolerance
        )
        candidates = list(sindex.intersection(bounds))
        
        if not candidates:
            return None
        
        # Find closest
        min_dist = float('inf')
        nearest = None
        
        for idx in candidates:
            node_point = nodes_gdf.iloc[idx].geometry
            dist = point.distance(node_point)
            if dist < min_dist:
                min_dist = dist
                nearest = nodes_gdf.iloc[idx].get('FRANODEID', idx)
        
        return nearest
    
    def _calculate_length_miles(self, line: LineString) -> float:
        """Calculate line length in miles using haversine formula."""
        coords = list(line.coords)
        total_miles = 0
        
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]
            
            # Haversine formula
            R = 3959  # Earth radius in miles
            lat1, lat2 = np.radians(lat1), np.radians(lat2)
            dlat = lat2 - lat1
            dlon = np.radians(lon2 - lon1)
            
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            total_miles += R * c
        
        return total_miles
    
    def _add_yard_attributes(self, yards_gdf: gpd.GeoDataFrame):
        """Add yard/terminal attributes to nearest nodes."""
        logger.info("  Adding yard attributes to nodes...")
        
        for idx, yard in yards_gdf.iterrows():
            # Find nearest node
            yard_point = yard.geometry.centroid if yard.geometry.geom_type != 'Point' else yard.geometry
            
            min_dist = float('inf')
            nearest_node = None
            
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                node_point = Point(node_data['lon'], node_data['lat'])
                dist = yard_point.distance(node_point)
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = node_id
            
            if nearest_node and min_dist < 0.01:  # ~1km tolerance
                self.graph.nodes[nearest_node]['is_yard'] = True
                self.graph.nodes[nearest_node]['yard_name'] = yard.get('YARDNAME', 'Unknown')
                self.graph.nodes[nearest_node]['yard_type'] = yard.get('YARDTYPE', 'Unknown')
    
    def get_network_stats(self) -> Dict:
        """Return network statistics."""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'connected_components': nx.number_weakly_connected_components(self.graph),
            'density': nx.density(self.graph),
            'total_miles': sum(d.get('miles', 0) for u, v, d in self.graph.edges(data=True))
        }
    
    def find_shortest_path(
        self, 
        origin_node: int, 
        dest_node: int, 
        weight: str = 'miles'
    ) -> Tuple[list, float]:
        """Find shortest path between two nodes."""
        try:
            path = nx.shortest_path(self.graph, origin_node, dest_node, weight=weight)
            length = nx.shortest_path_length(self.graph, origin_node, dest_node, weight=weight)
            return path, length
        except nx.NetworkXNoPath:
            logger.warning(f"No path found between {origin_node} and {dest_node}")
            return [], float('inf')
    
    def save_graph(self, filepath: Path):
        """Save graph to file."""
        nx.write_gpickle(self.graph, filepath)
        logger.info(f"Graph saved to {filepath}")
    
    def load_graph(self, filepath: Path):
        """Load graph from file."""
        self.graph = nx.read_gpickle(filepath)
        logger.info(f"Graph loaded from {filepath}")
