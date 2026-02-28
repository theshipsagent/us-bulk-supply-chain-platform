"""GIS export utilities — GeoJSON, Shapefile, KML, CSV.

Provides standardised export functions for geospatial data generated
by the platform's analysis engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import geopandas as gpd
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def export_geojson(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
    properties: list[str] | None = None,
) -> Path:
    """Export GeoDataFrame to GeoJSON file.

    Parameters
    ----------
    gdf : GeoDataFrame
        Source data.
    output_path : str or Path
        Output file path.
    properties : list[str], optional
        Limit exported properties to these columns.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    subset = gdf[properties + ["geometry"]] if properties else gdf
    subset.to_file(str(path), driver="GeoJSON")
    return path


def export_shapefile(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
) -> Path:
    """Export GeoDataFrame to ESRI Shapefile."""
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(path), driver="ESRI Shapefile")
    return path


def export_geopackage(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
    layer_name: str = "data",
) -> Path:
    """Export GeoDataFrame to GeoPackage (.gpkg)."""
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(path), driver="GPKG", layer=layer_name)
    return path


def export_geoparquet(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
) -> Path:
    """Export GeoDataFrame to GeoParquet."""
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(str(path))
    return path


def export_csv(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
    include_wkt: bool = False,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> Path:
    """Export GeoDataFrame to CSV with lat/lon columns.

    Parameters
    ----------
    include_wkt : bool
        If True, include a WKT geometry column.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df = gdf.copy()
    if gdf.geometry.name in df.columns:
        df[lon_col] = df.geometry.x
        df[lat_col] = df.geometry.y
        if include_wkt:
            df["geometry_wkt"] = df.geometry.to_wkt()
        df = df.drop(columns=[gdf.geometry.name])

    df.to_csv(str(path), index=False)
    return path


def export_kml(
    gdf: "gpd.GeoDataFrame",
    output_path: str | Path,
    name_col: str | None = None,
    description_col: str | None = None,
) -> Path:
    """Export GeoDataFrame to KML (Google Earth format).

    Requires fiona with KML driver support.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure WGS84 for KML
    export_gdf = gdf.to_crs("EPSG:4326") if gdf.crs and str(gdf.crs) != "EPSG:4326" else gdf

    # KML needs Name and Description fields
    if name_col and name_col in export_gdf.columns:
        export_gdf = export_gdf.rename(columns={name_col: "Name"})
    if description_col and description_col in export_gdf.columns:
        export_gdf = export_gdf.rename(columns={description_col: "Description"})

    export_gdf.to_file(str(path), driver="KML")
    return path
