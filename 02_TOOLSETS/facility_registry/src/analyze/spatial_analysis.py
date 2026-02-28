"""Spatial analysis for EPA FRS facilities.

Provides radius search, density analysis, clustering, and
proximity calculations using the facility registry DuckDB database.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


def _get_db_path() -> Path:
    """Resolve the FRS database path."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "frs.duckdb"


def _connect(read_only: bool = True) -> "duckdb.DuckDBPyConnection":
    if not HAS_DUCKDB:
        raise ImportError("duckdb is required: pip install duckdb")
    return duckdb.connect(str(_get_db_path()), read_only=read_only)


def radius_search(
    center_lat: float,
    center_lon: float,
    radius_miles: float,
    naics_filter: str | None = None,
    state_filter: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Search facilities within a radius of a point.

    Uses Haversine formula in SQL for efficient radius filtering
    with optional NAICS and state constraints.

    Parameters
    ----------
    center_lat, center_lon : float
        Center point coordinates.
    radius_miles : float
        Search radius in statute miles.
    naics_filter : str, optional
        NAICS code prefix to filter (e.g., "3273" for cement).
    state_filter : str, optional
        Two-letter state code.
    limit : int
        Maximum results to return.
    """
    # Bounding box pre-filter for performance
    lat_delta = radius_miles / 69.0
    lon_delta = radius_miles / (69.0 * math.cos(math.radians(center_lat)))

    con = _connect()

    sql = """
    WITH candidates AS (
        SELECT
            f.registry_id,
            f.fac_name,
            f.fac_city,
            f.fac_state,
            f.fac_county,
            f.latitude,
            f.longitude,
            -- Haversine distance in miles
            3958.8 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(f.latitude - ?) / 2), 2)
                + COS(RADIANS(?)) * COS(RADIANS(f.latitude))
                * POWER(SIN(RADIANS(f.longitude - ?) / 2), 2)
            )) AS distance_miles
        FROM facilities f
        WHERE f.latitude IS NOT NULL
          AND f.longitude IS NOT NULL
          AND f.latitude BETWEEN ? AND ?
          AND f.longitude BETWEEN ? AND ?
    """

    params: list[Any] = [
        center_lat, center_lat, center_lon,
        center_lat - lat_delta, center_lat + lat_delta,
        center_lon - lon_delta, center_lon + lon_delta,
    ]

    if state_filter:
        sql += " AND f.fac_state = ?"
        params.append(state_filter.upper())

    sql += """
    )
    SELECT c.*
    FROM candidates c
    """

    if naics_filter:
        sql += """
        INNER JOIN naics_codes n ON c.registry_id = n.registry_id
        WHERE n.naics_code LIKE ?
          AND c.distance_miles <= ?
        """
        params.extend([f"{naics_filter}%", radius_miles])
    else:
        sql += " WHERE c.distance_miles <= ?"
        params.append(radius_miles)

    sql += f" ORDER BY c.distance_miles LIMIT {limit}"

    rows = con.execute(sql, params).fetchall()
    columns = [desc[0] for desc in con.description]
    con.close()

    return [dict(zip(columns, row)) for row in rows]


def state_density(
    naics_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Count facilities per state, optionally filtered by NAICS.

    Returns list of {state, count} dicts sorted by count descending.
    """
    con = _connect()

    if naics_filter:
        sql = """
        SELECT f.fac_state AS state, COUNT(DISTINCT f.registry_id) AS facility_count
        FROM facilities f
        INNER JOIN naics_codes n ON f.registry_id = n.registry_id
        WHERE n.naics_code LIKE ?
          AND f.fac_state IS NOT NULL
        GROUP BY f.fac_state
        ORDER BY facility_count DESC
        """
        rows = con.execute(sql, [f"{naics_filter}%"]).fetchall()
    else:
        sql = """
        SELECT fac_state AS state, COUNT(*) AS facility_count
        FROM facilities
        WHERE fac_state IS NOT NULL
        GROUP BY fac_state
        ORDER BY facility_count DESC
        """
        rows = con.execute(sql).fetchall()

    con.close()
    columns = ["state", "facility_count"]
    return [dict(zip(columns, row)) for row in rows]


def nearest_facilities(
    target_lat: float,
    target_lon: float,
    k: int = 10,
    naics_filter: str | None = None,
    state_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Find the k nearest facilities to a target point."""
    # Use a generous initial radius, then trim
    results = radius_search(
        center_lat=target_lat,
        center_lon=target_lon,
        radius_miles=200,
        naics_filter=naics_filter,
        state_filter=state_filter,
        limit=k,
    )
    if len(results) < k:
        # Expand radius
        results = radius_search(
            center_lat=target_lat,
            center_lon=target_lon,
            radius_miles=500,
            naics_filter=naics_filter,
            state_filter=state_filter,
            limit=k,
        )
    return results[:k]


def cluster_facilities(
    state: str,
    naics_filter: str,
    grid_size_degrees: float = 0.5,
) -> list[dict[str, Any]]:
    """Grid-based spatial clustering of facilities.

    Divides the state into grid cells and counts facilities per cell.
    Useful for identifying concentration zones.
    """
    con = _connect()

    sql = """
    SELECT
        FLOOR(f.latitude / ?) * ? AS grid_lat,
        FLOOR(f.longitude / ?) * ? AS grid_lon,
        COUNT(DISTINCT f.registry_id) AS facility_count,
        MIN(f.latitude) AS min_lat,
        MAX(f.latitude) AS max_lat,
        MIN(f.longitude) AS min_lon,
        MAX(f.longitude) AS max_lon
    FROM facilities f
    INNER JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE f.fac_state = ?
      AND n.naics_code LIKE ?
      AND f.latitude IS NOT NULL
      AND f.longitude IS NOT NULL
    GROUP BY grid_lat, grid_lon
    HAVING COUNT(DISTINCT f.registry_id) > 0
    ORDER BY facility_count DESC
    """

    params = [
        grid_size_degrees, grid_size_degrees,
        grid_size_degrees, grid_size_degrees,
        state.upper(),
        f"{naics_filter}%",
    ]

    rows = con.execute(sql, params).fetchall()
    columns = [desc[0] for desc in con.description]
    con.close()

    return [dict(zip(columns, row)) for row in rows]


def competitor_proximity(
    facility_lat: float,
    facility_lon: float,
    naics_code: str,
    radius_miles: float = 100,
) -> dict[str, Any]:
    """Analyse competitive landscape around a facility location.

    Returns counts and distances to competitors within the radius.
    """
    competitors = radius_search(
        center_lat=facility_lat,
        center_lon=facility_lon,
        radius_miles=radius_miles,
        naics_filter=naics_code,
        limit=100,
    )

    if not competitors:
        return {
            "center": {"lat": facility_lat, "lon": facility_lon},
            "naics": naics_code,
            "radius_miles": radius_miles,
            "competitor_count": 0,
            "nearest_distance_miles": None,
            "avg_distance_miles": None,
            "competitors": [],
        }

    distances = [c["distance_miles"] for c in competitors if c["distance_miles"] > 0]

    return {
        "center": {"lat": facility_lat, "lon": facility_lon},
        "naics": naics_code,
        "radius_miles": radius_miles,
        "competitor_count": len(competitors),
        "nearest_distance_miles": min(distances) if distances else None,
        "avg_distance_miles": round(sum(distances) / len(distances), 1) if distances else None,
        "competitors": competitors[:20],  # top 20 nearest
    }
