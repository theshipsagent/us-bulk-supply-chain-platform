"""
Search API endpoints for finding docks, locks, vessels, and waterways.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from sqlalchemy import text, or_, and_

from src.config.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/docks")
async def search_docks(
    name: Optional[str] = Query(None, description="Dock name (partial match)"),
    state: Optional[str] = Query(None, description="State code"),
    port: Optional[str] = Query(None, description="Port name"),
    fac_type: Optional[str] = Query(None, description="Facility type"),
    min_depth: Optional[float] = Query(None, description="Minimum depth (feet)"),
    limit: int = Query(50, ge=1, le=500, description="Max results")
):
    """
    Search for navigation facilities (docks).

    Search by name, location, facility type, or depth requirements.
    """
    try:
        with get_db_session() as db:
            # Build WHERE clause
            conditions = []
            params = {}

            if name:
                conditions.append("nav_unit_name ILIKE :name")
                params["name"] = f"%{name}%"

            if state:
                conditions.append("state = :state")
                params["state"] = state.upper()

            if port:
                conditions.append("port_name ILIKE :port")
                params["port"] = f"%{port}%"

            if fac_type:
                conditions.append("fac_type = :fac_type")
                params["fac_type"] = fac_type

            if min_depth is not None:
                conditions.append("depth_min >= :min_depth")
                params["min_depth"] = min_depth

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    objectid, nav_unit_name, fac_type, state, city_or_town,
                    port_name, depth_min, depth_max, latitude, longitude,
                    tows_link_num, tows_mile
                FROM docks
                WHERE {where_clause}
                ORDER BY nav_unit_name
                LIMIT :limit
            """)

            params["limit"] = limit
            result = db.execute(query, params)
            rows = result.fetchall()

            docks = []
            for row in rows:
                docks.append({
                    "objectid": row[0],
                    "name": row[1],
                    "facility_type": row[2],
                    "state": row[3],
                    "city": row[4],
                    "port": row[5],
                    "depth_min_ft": row[6],
                    "depth_max_ft": row[7],
                    "latitude": row[8],
                    "longitude": row[9],
                    "tows_link_num": row[10],
                    "tows_mile": row[11]
                })

            return {
                "count": len(docks),
                "results": docks
            }

    except Exception as e:
        logger.error(f"Dock search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Dock search failed")


@router.get("/search/locks")
async def search_locks(
    name: Optional[str] = Query(None, description="Lock name (partial match)"),
    river: Optional[str] = Query(None, description="River name"),
    state: Optional[str] = Query(None, description="State code"),
    min_width: Optional[float] = Query(None, description="Minimum chamber width (feet)"),
    min_length: Optional[float] = Query(None, description="Minimum chamber length (feet)"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """
    Search for locks.

    Search by name, location, or dimensional requirements.
    """
    try:
        with get_db_session() as db:
            conditions = []
            params = {}

            if name:
                conditions.append("pmsname ILIKE :name")
                params["name"] = f"%{name}%"

            if river:
                conditions.append("river ILIKE :river")
                params["river"] = f"%{river}%"

            if state:
                conditions.append("state = :state")
                params["state"] = state.upper()

            if min_width is not None:
                conditions.append("width >= :min_width")
                params["min_width"] = min_width

            if min_length is not None:
                conditions.append("length >= :min_length")
                params["min_length"] = min_length

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    objectid, pmsname, river, rivermi, state,
                    width, length, lift, status, x, y
                FROM locks
                WHERE {where_clause}
                ORDER BY river, rivermi
                LIMIT :limit
            """)

            params["limit"] = limit
            result = db.execute(query, params)
            rows = result.fetchall()

            locks = []
            for row in rows:
                locks.append({
                    "objectid": row[0],
                    "name": row[1],
                    "river": row[2],
                    "river_mile": row[3],
                    "state": row[4],
                    "width_ft": row[5],
                    "length_ft": row[6],
                    "lift_ft": row[7],
                    "status": row[8],
                    "longitude": row[9],
                    "latitude": row[10]
                })

            return {
                "count": len(locks),
                "results": locks
            }

    except Exception as e:
        logger.error(f"Lock search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lock search failed")


@router.get("/search/vessels")
async def search_vessels(
    name: Optional[str] = Query(None, description="Vessel name (partial match)"),
    imo: Optional[str] = Query(None, description="IMO number"),
    vessel_type: Optional[str] = Query(None, description="Vessel type"),
    max_beam: Optional[float] = Query(None, description="Maximum beam (meters)"),
    max_draft: Optional[float] = Query(None, description="Maximum draft (meters)"),
    limit: int = Query(50, ge=1, le=500, description="Max results")
):
    """
    Search vessel registry.

    Find vessels by name, IMO, type, or dimensions.
    """
    try:
        with get_db_session() as db:
            conditions = []
            params = {}

            if name:
                conditions.append("vessel_name ILIKE :name")
                params["name"] = f"%{name}%"

            if imo:
                conditions.append("imo = :imo")
                params["imo"] = imo

            if vessel_type:
                conditions.append("vessel_type ILIKE :vessel_type")
                params["vessel_type"] = f"%{vessel_type}%"

            if max_beam is not None:
                conditions.append("beam <= :max_beam")
                params["max_beam"] = max_beam

            if max_draft is not None:
                conditions.append("depth_m <= :max_draft")
                params["max_draft"] = max_draft

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    imo, vessel_name, vessel_type, design, dwt,
                    loa, beam, depth_m, gt
                FROM vessels
                WHERE {where_clause}
                ORDER BY vessel_name
                LIMIT :limit
            """)

            params["limit"] = limit
            result = db.execute(query, params)
            rows = result.fetchall()

            vessels = []
            for row in rows:
                vessels.append({
                    "imo": row[0],
                    "name": row[1],
                    "type": row[2],
                    "design": row[3],
                    "dwt": row[4],
                    "loa_m": row[5],
                    "beam_m": row[6],
                    "draft_m": row[7],
                    "gt": row[8]
                })

            return {
                "count": len(vessels),
                "results": vessels
            }

    except Exception as e:
        logger.error(f"Vessel search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Vessel search failed")


@router.get("/search/waterways")
async def search_waterways(
    river_name: Optional[str] = Query(None, description="River name (partial match)"),
    state: Optional[str] = Query(None, description="State code"),
    waterway_code: Optional[str] = Query(None, description="Waterway code"),
    limit: int = Query(100, ge=1, le=500, description="Max results")
):
    """
    Search waterway links.

    Find waterway segments by river, state, or waterway code.
    """
    try:
        with get_db_session() as db:
            conditions = []
            params = {}

            if river_name:
                conditions.append("rivername ILIKE :river_name")
                params["river_name"] = f"%{river_name}%"

            if state:
                conditions.append("state = :state")
                params["state"] = state.upper()

            if waterway_code:
                conditions.append("waterway = :waterway_code")
                params["waterway_code"] = waterway_code

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    objectid, linknum, linkname, rivername,
                    anode, bnode, length_miles, state, waterway
                FROM waterway_links
                WHERE {where_clause}
                ORDER BY rivername, linknum
                LIMIT :limit
            """)

            params["limit"] = limit
            result = db.execute(query, params)
            rows = result.fetchall()

            waterways = []
            for row in rows:
                waterways.append({
                    "objectid": row[0],
                    "linknum": row[1],
                    "link_name": row[2],
                    "river_name": row[3],
                    "anode": row[4],
                    "bnode": row[5],
                    "length_miles": row[6],
                    "state": row[7],
                    "waterway_code": row[8]
                })

            return {
                "count": len(waterways),
                "results": waterways
            }

    except Exception as e:
        logger.error(f"Waterway search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Waterway search failed")
