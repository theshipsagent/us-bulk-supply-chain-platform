"""
Information API endpoints for database statistics and metadata.
"""

from fastapi import APIRouter, HTTPException
import logging
from sqlalchemy import text

from src.config.database import get_db_session, get_table_counts

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/info/stats")
async def get_database_stats():
    """
    Get database statistics.

    Returns record counts for all major tables.
    """
    try:
        counts = get_table_counts()

        return {
            "database": "barge_db",
            "tables": counts,
            "total_records": sum(counts.values())
        }

    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/info/rivers")
async def get_rivers():
    """
    Get list of all rivers in the system.

    Returns unique river names with waterway link counts.
    """
    try:
        with get_db_session() as db:
            query = text("""
                SELECT
                    rivername,
                    COUNT(*) as link_count,
                    SUM(length_miles) as total_miles
                FROM waterway_links
                WHERE rivername IS NOT NULL
                GROUP BY rivername
                ORDER BY total_miles DESC
            """)

            result = db.execute(query)
            rows = result.fetchall()

            rivers = []
            for row in rows:
                rivers.append({
                    "river_name": row[0],
                    "link_count": row[1],
                    "total_miles": float(row[2]) if row[2] else 0
                })

            return {
                "count": len(rivers),
                "rivers": rivers
            }

    except Exception as e:
        logger.error(f"Rivers query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch rivers")


@router.get("/info/states")
async def get_states():
    """
    Get list of states with waterway coverage.

    Returns states with counts of waterways, docks, and locks.
    """
    try:
        with get_db_session() as db:
            query = text("""
                SELECT
                    w.state,
                    COUNT(DISTINCT w.objectid) as waterway_count,
                    COUNT(DISTINCT d.objectid) as dock_count,
                    COUNT(DISTINCT l.objectid) as lock_count
                FROM waterway_links w
                LEFT JOIN docks d ON w.state = d.state
                LEFT JOIN locks l ON w.state = l.state
                WHERE w.state IS NOT NULL
                GROUP BY w.state
                ORDER BY w.state
            """)

            result = db.execute(query)
            rows = result.fetchall()

            states = []
            for row in rows:
                states.append({
                    "state": row[0],
                    "waterways": row[1],
                    "docks": row[2],
                    "locks": row[3]
                })

            return {
                "count": len(states),
                "states": states
            }

    except Exception as e:
        logger.error(f"States query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch states")


@router.get("/info/tonnage")
async def get_tonnage_summary():
    """
    Get cargo tonnage summary.

    Returns total tonnage by commodity type.
    """
    try:
        with get_db_session() as db:
            query = text("""
                SELECT
                    SUM(totalup) as total_upstream,
                    SUM(totaldown) as total_downstream,
                    SUM(coalup + coaldown) as total_coal,
                    SUM(petrolup + petrodown) as total_petroleum,
                    SUM(chemup + chemdown) as total_chemicals,
                    SUM(farmup + farmdown) as total_farm,
                    SUM(manuup + manudown) as total_manufactured
                FROM link_tonnages
            """)

            result = db.execute(query)
            row = result.fetchone()

            return {
                "total_upstream_tons": row[0] if row[0] else 0,
                "total_downstream_tons": row[1] if row[1] else 0,
                "total_tons": (row[0] if row[0] else 0) + (row[1] if row[1] else 0),
                "by_commodity": {
                    "coal_tons": row[2] if row[2] else 0,
                    "petroleum_tons": row[3] if row[3] else 0,
                    "chemicals_tons": row[4] if row[4] else 0,
                    "farm_products_tons": row[5] if row[5] else 0,
                    "manufactured_goods_tons": row[6] if row[6] else 0
                }
            }

    except Exception as e:
        logger.error(f"Tonnage query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch tonnage data")


@router.get("/info/vessel-types")
async def get_vessel_types():
    """
    Get vessel type distribution.

    Returns counts of vessels by type.
    """
    try:
        with get_db_session() as db:
            query = text("""
                SELECT
                    vessel_type,
                    COUNT(*) as vessel_count,
                    AVG(dwt) as avg_dwt,
                    AVG(beam) as avg_beam_m,
                    AVG(depth_m) as avg_draft_m
                FROM vessels
                WHERE vessel_type IS NOT NULL
                GROUP BY vessel_type
                ORDER BY vessel_count DESC
                LIMIT 20
            """)

            result = db.execute(query)
            rows = result.fetchall()

            types = []
            for row in rows:
                types.append({
                    "type": row[0],
                    "count": row[1],
                    "avg_dwt": round(row[2], 2) if row[2] else None,
                    "avg_beam_m": round(row[3], 2) if row[3] else None,
                    "avg_draft_m": round(row[4], 2) if row[4] else None
                })

            return {
                "count": len(types),
                "vessel_types": types
            }

    except Exception as e:
        logger.error(f"Vessel types query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch vessel types")
