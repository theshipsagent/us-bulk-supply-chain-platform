"""
Phase 3: Enrich state profiles with DuckDB waybill data.
Queries commodity, O-D pair, car type, and volume data per state.
"""

import logging
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import STATES_46, DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)


def _safe_query(con, sql, params=None):
    """Execute query and return list of dicts. Returns empty list on error."""
    try:
        if params:
            result = con.execute(sql, params)
        else:
            result = con.execute(sql)
        cols = [desc[0] for desc in result.description]
        rows = result.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        log.warning("  Query failed: %s", str(e)[:80])
        return []


def enrich_from_waybill(con, state_abbr):
    """
    Query waybill data to get freight metrics for a state.
    Returns dict with commodity, O-D, car type, and volume data.
    """
    like_pattern = f"%{state_abbr}%"

    # Top commodities by state (origin)
    top_commodities = _safe_query(con, """
        SELECT s.stcc_group AS commodity,
               COALESCE(SUM(f.exp_tons), 0) AS tons,
               COALESCE(SUM(f.exp_carloads), 0) AS carloads
        FROM fact_waybill f
        JOIN dim_stcc s ON f.stcc_2digit = s.stcc_2digit
        JOIN dim_bea b ON f.origin_bea = b.bea_code
        WHERE b.states LIKE ?
        GROUP BY s.stcc_group
        ORDER BY tons DESC
        LIMIT 10
    """, [like_pattern])

    # Top O-D pairs involving the state
    top_od_pairs = _safe_query(con, """
        SELECT b1.bea_name AS origin,
               b2.bea_name AS destination,
               COALESCE(SUM(f.exp_tons), 0) AS tons,
               COALESCE(SUM(f.exp_carloads), 0) AS carloads
        FROM fact_waybill f
        JOIN dim_bea b1 ON f.origin_bea = b1.bea_code
        JOIN dim_bea b2 ON f.term_bea = b2.bea_code
        WHERE b1.states LIKE ? OR b2.states LIKE ?
        GROUP BY b1.bea_name, b2.bea_name
        ORDER BY tons DESC
        LIMIT 10
    """, [like_pattern, like_pattern])

    # Car type mix for state
    car_types = _safe_query(con, """
        SELECT ct.description AS car_type,
               COALESCE(SUM(f.exp_carloads), 0) AS carloads
        FROM fact_waybill f
        JOIN dim_car_type ct ON CAST(f.stb_car_type AS VARCHAR) = ct.stb_car_type
        JOIN dim_bea b ON f.origin_bea = b.bea_code
        WHERE b.states LIKE ?
        GROUP BY ct.description
        ORDER BY carloads DESC
        LIMIT 5
    """, [like_pattern])

    # Total volume summary
    volume_rows = _safe_query(con, """
        SELECT COALESCE(SUM(f.exp_carloads), 0) AS total_carloads,
               COALESCE(SUM(f.exp_tons), 0) AS total_tons,
               COALESCE(SUM(f.exp_freight_rev), 0) AS total_revenue
        FROM fact_waybill f
        JOIN dim_bea b ON f.origin_bea = b.bea_code
        WHERE b.states LIKE ?
    """, [like_pattern])

    total_volume = volume_rows[0] if volume_rows else {
        "total_carloads": 0, "total_tons": 0, "total_revenue": 0
    }

    return {
        "waybill_top_commodities": top_commodities,
        "waybill_top_od_pairs": top_od_pairs,
        "waybill_car_types": car_types,
        "waybill_total_volume": total_volume,
    }


def enrich_all_states():
    """
    Enrich all 46 states with waybill data.
    Returns dict: {state_abbr: waybill_enrichment_dict}
    """
    if not DB_PATH.exists():
        log.warning("DuckDB not found at %s - skipping waybill enrichment", DB_PATH)
        return {abbr: _empty_enrichment() for abbr in STATES_46}

    con = duckdb.connect(str(DB_PATH), read_only=True)

    # Verify fact_waybill exists
    try:
        con.execute("SELECT 1 FROM fact_waybill LIMIT 1")
    except Exception:
        log.warning("fact_waybill table not found - skipping waybill enrichment")
        con.close()
        return {abbr: _empty_enrichment() for abbr in STATES_46}

    enrichments = {}
    total = len(STATES_46)

    for i, (abbr, name) in enumerate(sorted(STATES_46.items()), 1):
        log.info("[%d/%d] Enriching %s (%s) from waybill...", i, total, name, abbr)
        enrichments[abbr] = enrich_from_waybill(con, abbr)

        vol = enrichments[abbr]["waybill_total_volume"]
        log.info("  -> %s tons, %s carloads",
                 f"{vol['total_tons']:,.0f}" if vol["total_tons"] else "0",
                 f"{vol['total_carloads']:,.0f}" if vol["total_carloads"] else "0")

    con.close()
    return enrichments


def _empty_enrichment():
    return {
        "waybill_top_commodities": [],
        "waybill_top_od_pairs": [],
        "waybill_car_types": [],
        "waybill_total_volume": {"total_carloads": 0, "total_tons": 0, "total_revenue": 0},
    }
