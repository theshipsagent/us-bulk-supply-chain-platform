"""
Historical comparison queries for dashboard.
Updated for DuckDB compatibility.
"""
import pandas as pd


def get_available_years(db):
    """Get list of years with data."""
    query = """
        SELECT
            fleet_year,
            COUNT(*) as vessel_count,
            COUNT(DISTINCT ts_oper) as operator_count
        FROM vessels
        WHERE fleet_year IS NOT NULL
        GROUP BY fleet_year
        ORDER BY fleet_year
    """
    return db.conn.execute(query).df()


def get_fleet_size_trend(db):
    """Get fleet size trend over time."""
    query = """
        SELECT
            fleet_year,
            COUNT(*) as vessel_count,
            COUNT(DISTINCT ts_oper) as operator_count,
            AVG(nrt) as avg_nrt,
            SUM(nrt) as total_nrt
        FROM vessel_analytics_view
        WHERE fleet_year IS NOT NULL
        GROUP BY fleet_year
        ORDER BY fleet_year
    """
    return db.conn.execute(query).df()


def get_vessel_type_trends(db, vessel_type=None):
    """Get vessel type trends over time."""
    if vessel_type:
        query = """
            SELECT
                fleet_year,
                vtcc_vessel_type as vessel_type,
                COUNT(*) as vessel_count,
                AVG(nrt) as avg_nrt
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND vtcc_vessel_type = ?
            GROUP BY fleet_year, vtcc_vessel_type
            ORDER BY fleet_year
        """
        params = [vessel_type]
    else:
        query = """
            SELECT
                fleet_year,
                vtcc_vessel_type as vessel_type,
                COUNT(*) as vessel_count,
                AVG(nrt) as avg_nrt
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND vtcc_vessel_type IS NOT NULL
            GROUP BY fleet_year, vtcc_vessel_type
            ORDER BY fleet_year, vessel_count DESC
        """
        params = []

    return db.conn.execute(query, params).df()


def get_operator_trends(db, ts_oper):
    """Get specific operator's growth trend."""
    # Convert numpy types to native Python int
    ts_oper = int(ts_oper)
    query = """
        SELECT
            v.fleet_year,
            COALESCE(o.operator_name_std, o.operator_name) as operator_name,
            COUNT(v.vessel_id) as vessel_count,
            AVG(v.nrt) as avg_nrt
        FROM vessels v
        LEFT JOIN operators o ON v.ts_oper = o.ts_oper
        WHERE v.ts_oper = ?
        GROUP BY v.fleet_year, COALESCE(o.operator_name_std, o.operator_name)
        ORDER BY v.fleet_year
    """
    return db.conn.execute(query, [ts_oper]).df()


def get_top_growing_operators(db, year, limit=20):
    """Get operators with highest growth in specified year."""
    query = """
        WITH current_year AS (
            SELECT
                ts_oper,
                COALESCE(operator_name_std, operator_name) as operator_name,
                COUNT(*) as current_count
            FROM vessel_analytics_view
            WHERE fleet_year = ?
              AND COALESCE(operator_name_std, operator_name) IS NOT NULL
            GROUP BY ts_oper, COALESCE(operator_name_std, operator_name)
        ),
        previous_year AS (
            SELECT
                ts_oper,
                COUNT(*) as previous_count
            FROM vessel_analytics_view
            WHERE fleet_year = ? - 1
            GROUP BY ts_oper
        )
        SELECT
            cy.operator_name,
            cy.current_count as vessel_count,
            COALESCE(py.previous_count, 0) as previous_count,
            cy.current_count - COALESCE(py.previous_count, 0) as vessel_change,
            ROUND(
                (cy.current_count - COALESCE(py.previous_count, 0))::DECIMAL /
                NULLIF(py.previous_count, 0) * 100, 1
            ) as percent_change
        FROM current_year cy
        LEFT JOIN previous_year py ON cy.ts_oper = py.ts_oper
        WHERE py.previous_count > 0
        ORDER BY percent_change DESC
        LIMIT ?
    """
    return db.conn.execute(query, [year, year, limit]).df()


def get_top_declining_operators(db, year, limit=20):
    """Get operators with largest decline in specified year."""
    query = """
        WITH current_year AS (
            SELECT
                ts_oper,
                operator_name,
                COUNT(*) as current_count
            FROM vessel_analytics_view
            WHERE fleet_year = ?
              AND operator_name IS NOT NULL
            GROUP BY ts_oper, operator_name
        ),
        previous_year AS (
            SELECT
                ts_oper,
                COUNT(*) as previous_count
            FROM vessel_analytics_view
            WHERE fleet_year = ? - 1
            GROUP BY ts_oper
        )
        SELECT
            cy.operator_name,
            cy.current_count as vessel_count,
            py.previous_count,
            cy.current_count - py.previous_count as vessel_change,
            ROUND(
                (cy.current_count - py.previous_count)::DECIMAL /
                py.previous_count * 100, 1
            ) as percent_change
        FROM current_year cy
        LEFT JOIN previous_year py ON cy.ts_oper = py.ts_oper
        WHERE py.previous_count > 0
        ORDER BY percent_change ASC
        LIMIT ?
    """
    return db.conn.execute(query, [year, year, limit]).df()


def get_district_trends(db, district_name=None):
    """Get district vessel trends over time."""
    if district_name:
        query = """
            SELECT
                fleet_year,
                district_name,
                COUNT(*) as vessel_count
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND district_name = ?
            GROUP BY fleet_year, district_name
            ORDER BY fleet_year
        """
        params = [district_name]
    else:
        query = """
            SELECT
                fleet_year,
                district_name,
                COUNT(*) as vessel_count
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND district_name IS NOT NULL
            GROUP BY fleet_year, district_name
            ORDER BY fleet_year, vessel_count DESC
        """
        params = []

    return db.conn.execute(query, params).df()


def get_equipment_trends(db, equipment_name=None):
    """Get equipment adoption trends."""
    if equipment_name:
        query = """
            SELECT
                fleet_year,
                equip1_name as equipment_name,
                COUNT(*) as vessel_count
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND equip1_name = ?
            GROUP BY fleet_year, equip1_name
            ORDER BY fleet_year
        """
        params = [equipment_name]
    else:
        query = """
            SELECT
                fleet_year,
                equip1_name as equipment_name,
                COUNT(*) as vessel_count
            FROM vessel_analytics_view
            WHERE fleet_year IS NOT NULL
              AND equip1_name IS NOT NULL
            GROUP BY fleet_year, equip1_name
            ORDER BY fleet_year, vessel_count DESC
        """
        params = []

    return db.conn.execute(query, params).df()


def get_fleet_age_trends(db):
    """Get fleet age distribution trends."""
    query = """
        SELECT
            fleet_year,
            CASE
                WHEN vessel_age BETWEEN 0 AND 10 THEN 'Modern (0-10 yrs)'
                WHEN vessel_age BETWEEN 11 AND 20 THEN 'Mature (11-20 yrs)'
                WHEN vessel_age BETWEEN 21 AND 30 THEN 'Aging (21-30 yrs)'
                ELSE 'Legacy (30+ yrs)'
            END as age_bracket,
            COUNT(*) as vessel_count
        FROM vessel_analytics_view
        WHERE fleet_year IS NOT NULL
          AND vessel_age IS NOT NULL
        GROUP BY fleet_year, age_bracket
        ORDER BY fleet_year, age_bracket
    """
    return db.conn.execute(query).df()


def get_vessel_lifecycle(db):
    """Get new/retired vessels by year."""
    query = """
        WITH vessel_years AS (
            SELECT vessel_id, MIN(fleet_year) as first_year, MAX(fleet_year) as last_year
            FROM vessels
            WHERE fleet_year IS NOT NULL
            GROUP BY vessel_id
        )
        SELECT
            fleet_year,
            COUNT(CASE WHEN first_year = fleet_year THEN 1 END) as new_vessels,
            COUNT(CASE WHEN last_year = fleet_year THEN 1 END) as retired_vessels
        FROM vessel_years
        CROSS JOIN (SELECT DISTINCT fleet_year FROM vessels WHERE fleet_year IS NOT NULL) years
        WHERE fleet_year BETWEEN first_year AND last_year
        GROUP BY fleet_year
        ORDER BY fleet_year
    """
    return db.conn.execute(query).df()


def compare_two_years(db, year1, year2):
    """Compare statistics between two years."""
    query = """
        WITH y1_stats AS (
            SELECT
                COUNT(*) as vessel_count,
                COUNT(DISTINCT ts_oper) as operator_count,
                AVG(nrt) as avg_nrt,
                AVG(vessel_age) as avg_age
            FROM vessel_analytics_view
            WHERE fleet_year = ?
        ),
        y2_stats AS (
            SELECT
                COUNT(*) as vessel_count,
                COUNT(DISTINCT ts_oper) as operator_count,
                AVG(nrt) as avg_nrt,
                AVG(vessel_age) as avg_age
            FROM vessel_analytics_view
            WHERE fleet_year = ?
        )
        SELECT
            ? as year1,
            ? as year2,
            y1.vessel_count as year1_vessels,
            y2.vessel_count as year2_vessels,
            y2.vessel_count - y1.vessel_count as vessel_change,
            ROUND((y2.vessel_count - y1.vessel_count)::DECIMAL / y1.vessel_count * 100, 1) as vessel_pct_change,
            y1.operator_count as year1_operators,
            y2.operator_count as year2_operators,
            y2.operator_count - y1.operator_count as operator_change,
            ROUND(y1.avg_nrt, 0) as year1_avg_nrt,
            ROUND(y2.avg_nrt, 0) as year2_avg_nrt,
            ROUND(y1.avg_age, 1) as year1_avg_age,
            ROUND(y2.avg_age, 1) as year2_avg_age
        FROM y1_stats y1, y2_stats y2
    """
    return db.conn.execute(query, [year1, year2, year1, year2]).df()


def get_operator_year_comparison(db, operator_name, year1, year2):
    """Compare operator's fleet between two years."""
    query = """
        WITH y1 AS (
            SELECT COUNT(*) as count, AVG(nrt) as avg_nrt
            FROM vessel_analytics_view
            WHERE operator_name = ? AND fleet_year = ?
        ),
        y2 AS (
            SELECT COUNT(*) as count, AVG(nrt) as avg_nrt
            FROM vessel_analytics_view
            WHERE operator_name = ? AND fleet_year = ?
        )
        SELECT
            ? as year1,
            ? as year2,
            y1.count as year1_vessels,
            y2.count as year2_vessels,
            (y2.count - y1.count) as vessel_change,
            ROUND((y2.count - y1.count)::DECIMAL / NULLIF(y1.count, 0) * 100, 1) as percent_change,
            ROUND(y1.avg_nrt, 0) as year1_avg_nrt,
            ROUND(y2.avg_nrt, 0) as year2_avg_nrt
        FROM y1, y2
    """
    return db.conn.execute(query, [
        operator_name, year1,
        operator_name, year2,
        year1, year2
    ]).df()


def get_market_share_trends(db, top_n=10):
    """Get market share trends for top N operators."""
    query = """
        WITH operator_yearly_totals AS (
            SELECT
                ts_oper,
                COALESCE(operator_name_std, operator_name) as operator_name,
                fleet_year,
                COUNT(*) as vessel_count
            FROM vessel_analytics_view
            WHERE COALESCE(operator_name_std, operator_name) IS NOT NULL AND fleet_year IS NOT NULL
            GROUP BY ts_oper, COALESCE(operator_name_std, operator_name), fleet_year
        ),
        yearly_totals AS (
            SELECT
                fleet_year,
                SUM(vessel_count) as total_vessels
            FROM operator_yearly_totals
            GROUP BY fleet_year
        ),
        top_operators AS (
            SELECT ts_oper
            FROM operator_yearly_totals
            WHERE fleet_year = (SELECT MAX(fleet_year) FROM operator_yearly_totals)
            ORDER BY vessel_count DESC
            LIMIT ?
        )
        SELECT
            oyt.operator_name,
            oyt.fleet_year,
            oyt.vessel_count,
            yt.total_vessels,
            ROUND((oyt.vessel_count::DECIMAL / yt.total_vessels * 100), 2) as market_share_pct
        FROM operator_yearly_totals oyt
        JOIN yearly_totals yt ON oyt.fleet_year = yt.fleet_year
        WHERE oyt.ts_oper IN (SELECT ts_oper FROM top_operators)
        ORDER BY oyt.fleet_year, oyt.vessel_count DESC
    """
    return db.conn.execute(query, [top_n]).df()
