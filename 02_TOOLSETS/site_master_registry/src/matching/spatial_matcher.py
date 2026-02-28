"""Spatial matching via Haversine distance.

Thin wrapper around the geospatial_engine's haversine function,
adapted for the matching engine's needs (meters, km, bounding box).
"""

from __future__ import annotations

import math
from typing import Optional

EARTH_RADIUS_KM = 6_371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers."""
    lat1, lon1, lat2, lon2 = (math.radians(x) for x in (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    return haversine_km(lat1, lon1, lat2, lon2) * 1000.0


def spatial_distance(
    lat1: Optional[float], lon1: Optional[float],
    lat2: Optional[float], lon2: Optional[float],
) -> Optional[float]:
    """Distance in meters, or None if either coordinate is missing."""
    if any(v is None for v in (lat1, lon1, lat2, lon2)):
        return None
    return haversine_meters(lat1, lon1, lat2, lon2)


def within_radius_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    radius_km: float,
) -> bool:
    """Quick check if two points are within a radius."""
    return haversine_km(lat1, lon1, lat2, lon2) <= radius_km
