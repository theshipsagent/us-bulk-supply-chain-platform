"""Spatial join and proximity operations.

Provides point-in-polygon, radius search, nearest-neighbour,
and buffer operations used across toolsets. Works with both
raw lat/lon data and GeoPandas GeoDataFrames.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, MultiPolygon
    from shapely.ops import nearest_points
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


EARTH_RADIUS_MILES = 3_958.8
EARTH_RADIUS_KM = 6_371.0


def haversine(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    unit: str = "miles",
) -> float:
    """Great-circle distance between two points.

    Parameters
    ----------
    lat1, lon1, lat2, lon2 : float
        Coordinates in decimal degrees.
    unit : str
        ``"miles"`` or ``"km"``.
    """
    r = EARTH_RADIUS_MILES if unit == "miles" else EARTH_RADIUS_KM
    lat1, lon1, lat2, lon2 = (math.radians(x) for x in (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def radius_search(
    center_lat: float,
    center_lon: float,
    points: list[dict[str, Any]],
    radius_miles: float,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
) -> list[dict[str, Any]]:
    """Find all points within a radius of a center point.

    Each point dict must have lat/lon keys. Returns matching points
    with ``distance_miles`` added.
    """
    results = []
    for pt in points:
        lat = pt.get(lat_key)
        lon = pt.get(lon_key)
        if lat is None or lon is None:
            continue
        dist = haversine(center_lat, center_lon, float(lat), float(lon))
        if dist <= radius_miles:
            pt_copy = dict(pt)
            pt_copy["distance_miles"] = round(dist, 2)
            results.append(pt_copy)
    results.sort(key=lambda x: x["distance_miles"])
    return results


def nearest_neighbours(
    target_lat: float,
    target_lon: float,
    points: list[dict[str, Any]],
    k: int = 5,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
) -> list[dict[str, Any]]:
    """Find k nearest points to a target location."""
    scored = []
    for pt in points:
        lat = pt.get(lat_key)
        lon = pt.get(lon_key)
        if lat is None or lon is None:
            continue
        dist = haversine(target_lat, target_lon, float(lat), float(lon))
        pt_copy = dict(pt)
        pt_copy["distance_miles"] = round(dist, 2)
        scored.append(pt_copy)
    scored.sort(key=lambda x: x["distance_miles"])
    return scored[:k]


def bounding_box(
    center_lat: float,
    center_lon: float,
    radius_miles: float,
) -> tuple[float, float, float, float]:
    """Return (min_lat, min_lon, max_lat, max_lon) for a radius.

    Useful for pre-filtering large datasets before exact distance calc.
    """
    lat_delta = radius_miles / 69.0  # ~69 miles per degree latitude
    lon_delta = radius_miles / (69.0 * math.cos(math.radians(center_lat)))
    return (
        center_lat - lat_delta,
        center_lon - lon_delta,
        center_lat + lat_delta,
        center_lon + lon_delta,
    )


# ---------------------------------------------------------------------------
# GeoPandas operations (require geopandas + shapely)
# ---------------------------------------------------------------------------

def points_to_geodf(
    points: list[dict[str, Any]],
    lat_key: str = "latitude",
    lon_key: str = "longitude",
    crs: str = "EPSG:4326",
) -> "gpd.GeoDataFrame":
    """Convert a list of point dicts to a GeoDataFrame."""
    if not HAS_GEO:
        raise ImportError("geopandas is required: pip install geopandas")
    df = pd.DataFrame(points)
    geometry = [
        Point(float(row[lon_key]), float(row[lat_key]))
        for _, row in df.iterrows()
        if row.get(lat_key) is not None and row.get(lon_key) is not None
    ]
    return gpd.GeoDataFrame(df, geometry=geometry, crs=crs)


def spatial_join_points_to_polygons(
    points_gdf: "gpd.GeoDataFrame",
    polygons_gdf: "gpd.GeoDataFrame",
    how: str = "left",
    predicate: str = "within",
) -> "gpd.GeoDataFrame":
    """Perform a spatial join of points to polygons.

    Common use: assign facilities to states/counties/regions.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    return gpd.sjoin(points_gdf, polygons_gdf, how=how, predicate=predicate)


def buffer_points(
    gdf: "gpd.GeoDataFrame",
    radius_miles: float,
    crs_projected: str = "EPSG:3857",
) -> "gpd.GeoDataFrame":
    """Create buffer polygons around points.

    Projects to Web Mercator for buffering, then back to WGS84.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    original_crs = gdf.crs
    projected = gdf.to_crs(crs_projected)
    radius_meters = radius_miles * 1_609.34
    projected["geometry"] = projected.geometry.buffer(radius_meters)
    return projected.to_crs(original_crs)


def calculate_density(
    points_gdf: "gpd.GeoDataFrame",
    polygons_gdf: "gpd.GeoDataFrame",
    polygon_id_col: str = "id",
) -> "gpd.GeoDataFrame":
    """Count points per polygon and compute density.

    Returns the polygon GeoDataFrame with ``point_count`` and
    ``density_per_sq_mile`` columns added.
    """
    if not HAS_GEO:
        raise ImportError("geopandas is required")
    joined = gpd.sjoin(points_gdf, polygons_gdf, how="right", predicate="within")
    counts = joined.groupby(polygon_id_col).size().reset_index(name="point_count")
    result = polygons_gdf.merge(counts, on=polygon_id_col, how="left")
    result["point_count"] = result["point_count"].fillna(0).astype(int)

    # Area in square miles (project to equal-area CRS)
    projected = result.to_crs("EPSG:5070")  # NAD83 / Conus Albers
    result["area_sq_miles"] = projected.geometry.area / (1_609.34 ** 2)
    result["density_per_sq_mile"] = result["point_count"] / result["area_sq_miles"].replace(0, float("nan"))

    return result
