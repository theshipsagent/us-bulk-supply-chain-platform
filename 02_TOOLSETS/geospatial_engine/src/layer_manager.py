"""GIS layer manager — loading, caching, and transformation.

Handles loading of common geospatial data formats (Shapefile, GeoJSON,
GeoPackage, Parquet) and provides a unified interface for accessing
reference layers used across the platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import geopandas as gpd
    HAS_GEO = True
except ImportError:
    HAS_GEO = False


@dataclass
class LayerInfo:
    """Metadata for a loaded GIS layer."""
    name: str
    source_path: str
    crs: str
    feature_count: int
    geometry_type: str
    columns: list[str] = field(default_factory=list)
    bounds: tuple[float, float, float, float] | None = None


class LayerManager:
    """Manages loading and caching of GIS layers.

    Usage::

        lm = LayerManager(base_path="01_DATA_SOURCES/geospatial")
        states = lm.load("base_layers/us_states.shp", name="us_states")
        waterways = lm.load("waterway_layers/rivers.geojson", name="rivers")
        print(lm.list_layers())
    """

    def __init__(self, base_path: str | Path | None = None) -> None:
        self._base = Path(base_path) if base_path else None
        self._cache: dict[str, "gpd.GeoDataFrame"] = {}
        self._info: dict[str, LayerInfo] = {}

    def load(
        self,
        path: str | Path,
        name: str | None = None,
        target_crs: str = "EPSG:4326",
        columns: list[str] | None = None,
    ) -> "gpd.GeoDataFrame":
        """Load a geospatial file into a GeoDataFrame.

        Parameters
        ----------
        path : str or Path
            Relative (to base_path) or absolute path.
        name : str
            Cache key. If None, uses the filename stem.
        target_crs : str
            Reproject to this CRS after loading.
        columns : list[str], optional
            Only read these columns (plus geometry).
        """
        if not HAS_GEO:
            raise ImportError("geopandas is required: pip install geopandas")

        resolved = self._resolve(path)
        layer_name = name or resolved.stem

        if layer_name in self._cache:
            return self._cache[layer_name]

        gdf = gpd.read_file(str(resolved), columns=columns)

        if gdf.crs and str(gdf.crs) != target_crs:
            gdf = gdf.to_crs(target_crs)

        self._cache[layer_name] = gdf
        self._info[layer_name] = LayerInfo(
            name=layer_name,
            source_path=str(resolved),
            crs=str(gdf.crs),
            feature_count=len(gdf),
            geometry_type=gdf.geom_type.iloc[0] if len(gdf) > 0 else "unknown",
            columns=list(gdf.columns),
            bounds=tuple(gdf.total_bounds) if len(gdf) > 0 else None,
        )

        return gdf

    def load_parquet(
        self,
        path: str | Path,
        name: str | None = None,
        target_crs: str = "EPSG:4326",
    ) -> "gpd.GeoDataFrame":
        """Load a GeoParquet file."""
        if not HAS_GEO:
            raise ImportError("geopandas is required")

        resolved = self._resolve(path)
        layer_name = name or resolved.stem

        if layer_name in self._cache:
            return self._cache[layer_name]

        gdf = gpd.read_parquet(str(resolved))
        if gdf.crs and str(gdf.crs) != target_crs:
            gdf = gdf.to_crs(target_crs)

        self._cache[layer_name] = gdf
        self._info[layer_name] = LayerInfo(
            name=layer_name,
            source_path=str(resolved),
            crs=str(gdf.crs),
            feature_count=len(gdf),
            geometry_type=gdf.geom_type.iloc[0] if len(gdf) > 0 else "unknown",
            columns=list(gdf.columns),
            bounds=tuple(gdf.total_bounds) if len(gdf) > 0 else None,
        )

        return gdf

    def get(self, name: str) -> "gpd.GeoDataFrame":
        """Retrieve a cached layer by name."""
        if name not in self._cache:
            raise KeyError(f"Layer '{name}' not loaded. Available: {list(self._cache.keys())}")
        return self._cache[name]

    def info(self, name: str) -> LayerInfo:
        """Get metadata for a loaded layer."""
        if name not in self._info:
            raise KeyError(f"Layer '{name}' not loaded.")
        return self._info[name]

    def list_layers(self) -> list[LayerInfo]:
        """List all loaded layers."""
        return list(self._info.values())

    def drop(self, name: str) -> None:
        """Remove a layer from cache."""
        self._cache.pop(name, None)
        self._info.pop(name, None)

    def _resolve(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        if self._base:
            return self._base / p
        return p
