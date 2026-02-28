"""
NTAD Rail Network Data Loader
Downloads and processes North American Rail Network (NARN) data from BTS/FRA

Key datasets:
- Rail Lines: Track segments with ownership, track class, signals
- Rail Nodes: Junctions, terminals, connection points
- Rail Yards: Classification yards, intermodal facilities
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import requests
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class NTADLoader:
    """Load and process NTAD rail network data."""
    
    def __init__(self, config: dict, data_dir: Path):
        self.config = config
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw" / "ntad"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_from_arcgis(self, url: str, layer_name: str) -> gpd.GeoDataFrame:
        """
        Fetch data from ArcGIS REST API.
        Handles pagination for large datasets.
        """
        # Query to get all features (may need pagination)
        query_url = f"{url}/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true"
        }
        
        logger.info(f"Fetching {layer_name} from ArcGIS...")
        
        # For large datasets, implement pagination
        all_features = []
        offset = 0
        batch_size = 2000
        
        while True:
            params["resultOffset"] = offset
            params["resultRecordCount"] = batch_size
            
            response = requests.get(query_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            features = data.get("features", [])
            
            if not features:
                break
                
            all_features.extend(features)
            logger.info(f"  Retrieved {len(all_features)} features...")
            
            if len(features) < batch_size:
                break
            offset += batch_size
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")
        logger.info(f"  Total: {len(gdf)} features loaded")
        
        return gdf
    
    def load_rail_lines(self, force_refresh: bool = False) -> gpd.GeoDataFrame:
        """Load rail lines (edges of the network graph)."""
        cache_path = self.raw_dir / "rail_lines.parquet"
        
        if cache_path.exists() and not force_refresh:
            logger.info("Loading rail lines from cache...")
            return gpd.read_parquet(cache_path)
        
        url = self.config["data_sources"]["ntad"]["rail_lines"]
        gdf = self.fetch_from_arcgis(url, "Rail Lines")
        
        # Save to parquet for faster subsequent loads
        gdf.to_parquet(cache_path)
        
        return gdf
    
    def load_rail_nodes(self, force_refresh: bool = False) -> gpd.GeoDataFrame:
        """Load rail nodes (vertices of the network graph)."""
        cache_path = self.raw_dir / "rail_nodes.parquet"
        
        if cache_path.exists() and not force_refresh:
            logger.info("Loading rail nodes from cache...")
            return gpd.read_parquet(cache_path)
        
        url = self.config["data_sources"]["ntad"]["rail_nodes"]
        gdf = self.fetch_from_arcgis(url, "Rail Nodes")
        
        gdf.to_parquet(cache_path)
        
        return gdf
    
    def load_rail_yards(self, force_refresh: bool = False) -> gpd.GeoDataFrame:
        """Load rail yards (classification/switching facilities)."""
        cache_path = self.raw_dir / "rail_yards.parquet"
        
        if cache_path.exists() and not force_refresh:
            logger.info("Loading rail yards from cache...")
            return gpd.read_parquet(cache_path)
        
        url = self.config["data_sources"]["ntad"]["rail_yards"]
        gdf = self.fetch_from_arcgis(url, "Rail Yards")
        
        gdf.to_parquet(cache_path)
        
        return gdf
    
    def load_all(self, force_refresh: bool = False) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Load all NTAD rail datasets."""
        lines = self.load_rail_lines(force_refresh)
        nodes = self.load_rail_nodes(force_refresh)
        yards = self.load_rail_yards(force_refresh)
        
        return lines, nodes, yards
    
    def summarize(self, gdf: gpd.GeoDataFrame, name: str) -> dict:
        """Generate summary statistics for a dataset."""
        summary = {
            "name": name,
            "record_count": len(gdf),
            "columns": list(gdf.columns),
            "crs": str(gdf.crs),
            "bounds": gdf.total_bounds.tolist(),
            "geometry_types": gdf.geometry.geom_type.value_counts().to_dict()
        }
        return summary
