"""
Database query functions for USACE dashboard.
All queries use the vessel_analytics_view for fast, code-translated results.
Updated for DuckDB compatibility.
"""
import pandas as pd


def build_where_clause(filters):
    """
    Build WHERE clause from filters.

    Args:
        filters: Dict with keys: operators, vessel_types, districts, series, fleet_year, year_range

    Returns:
        tuple: (where_clause_string, params_dict)
    """
    conditions = ["1=1"]  # Always true base condition
    params = []

    # Fleet year filter (which year's data to show)
    if filters.get('fleet_year'):
        conditions.append("fleet_year = ?")
        params.append(filters['fleet_year'])

    if filters.get('operators'):
        placeholders = ','.join(['?' for _ in filters['operators']])
        conditions.append(f"COALESCE(operator_name_std, operator_name) IN ({placeholders})")
        params.extend(filters['operators'])

    if filters.get('vessel_types'):
        placeholders = ','.join(['?' for _ in filters['vessel_types']])
        conditions.append(f"vtcc_vessel_type IN ({placeholders})")
        params.extend(filters['vessel_types'])

    if filters.get('districts'):
        placeholders = ','.join(['?' for _ in filters['districts']])
        conditions.append(f"district_name IN ({placeholders})")
        params.extend(filters['districts'])

    if filters.get('series'):
        placeholders = ','.join(['?' for _ in filters['series']])
        conditions.append(f"series_name IN ({placeholders})")
        params.extend(filters['series'])

    if filters.get('year_range'):
        year_min, year_max = filters['year_range']
        conditions.append("year_vessel BETWEEN ? AND ?")
        params.extend([year_min, year_max])

    where_clause = " AND ".join(conditions)
    return where_clause, params


def get_fleet_summary(db, filters):
    """Get high-level fleet statistics."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            COUNT(*) as total_vessels,
            COUNT(DISTINCT ts_oper) as total_operators,
            AVG(vessel_age) as avg_age,
            SUM(nrt) as total_nrt
        FROM vessel_analytics_view
        WHERE {where_clause}
    """

    result = db.conn.execute(query, params).fetchone()
    return {
        'total_vessels': result[0] or 0,
        'total_operators': result[1] or 0,
        'avg_age': result[2] or 0,
        'total_nrt': result[3] or 0
    }


def get_vessel_type_distribution(db, filters):
    """Get vessel count by type."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT vtcc_vessel_type, COUNT(*) as count
        FROM vessel_analytics_view
        WHERE {where_clause} AND vtcc_vessel_type IS NOT NULL
        GROUP BY vtcc_vessel_type
        ORDER BY count DESC
    """

    return db.conn.execute(query, params).df()


def get_age_distribution(db, filters):
    """Get vessel count by age category."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT age_category, COUNT(*) as count
        FROM vessel_analytics_view
        WHERE {where_clause}
        GROUP BY age_category
        ORDER BY
            CASE age_category
                WHEN 'Modern' THEN 1
                WHEN 'Mature' THEN 2
                ELSE 3
            END
    """

    return db.conn.execute(query, params).df()


def get_top_operators(db, filters, limit=15):
    """Get top operators by fleet size."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            COALESCE(operator_name_std, operator_name) as operator_name,
            COUNT(*) as vessel_count,
            AVG(nrt) as avg_nrt
        FROM vessel_analytics_view
        WHERE {where_clause} AND COALESCE(operator_name_std, operator_name) IS NOT NULL
        GROUP BY COALESCE(operator_name_std, operator_name)
        ORDER BY vessel_count DESC
        LIMIT {limit}
    """

    return db.conn.execute(query, params).df()


def get_operator_list(db):
    """Get list of all operators."""
    query = """
        SELECT DISTINCT COALESCE(operator_name_std, operator_name) as operator_name
        FROM vessel_analytics_view
        WHERE COALESCE(operator_name_std, operator_name) IS NOT NULL
        ORDER BY operator_name
    """
    return db.conn.execute(query).fetchall()


def get_vessel_types(db):
    """Get list of all vessel types."""
    query = """
        SELECT DISTINCT vtcc_vessel_type
        FROM vessel_analytics_view
        WHERE vtcc_vessel_type IS NOT NULL
        ORDER BY vtcc_vessel_type
    """
    return db.conn.execute(query).fetchall()


def get_districts(db):
    """Get list of all districts."""
    query = """
        SELECT DISTINCT district_name
        FROM vessel_analytics_view
        WHERE district_name IS NOT NULL
        ORDER BY district_name
    """
    return db.conn.execute(query).fetchall()


def get_series(db):
    """Get list of all series/regions."""
    query = """
        SELECT DISTINCT series_name
        FROM vessel_analytics_view
        WHERE series_name IS NOT NULL
        ORDER BY series_name
    """
    return db.conn.execute(query).fetchall()


def get_operator_details(db, operator_search):
    """Get operator details by name search."""
    query = """
        SELECT
            ts_oper,
            COALESCE(operator_name_std, operator_name) as operator_name,
            operator_city,
            operator_state,
            phone,
            district_name,
            service_name,
            principal_commodity,
            COUNT(*) as vessel_count
        FROM vessel_analytics_view
        WHERE COALESCE(operator_name_std, operator_name) LIKE ?
        GROUP BY ts_oper, COALESCE(operator_name_std, operator_name), operator_city, operator_state,
                 phone, district_name, service_name, principal_commodity
        LIMIT 1
    """
    return db.conn.execute(query, [f'%{operator_search}%']).df()


def get_operator_fleet_composition(db, ts_oper):
    """Get operator's fleet composition by vessel type."""
    # Convert numpy types to native Python int
    ts_oper = int(ts_oper)
    query = """
        SELECT
            characteristic_desc,
            COUNT(*) as count
        FROM vessel_analytics_view
        WHERE ts_oper = ?
        GROUP BY characteristic_desc
        ORDER BY count DESC
    """
    return db.conn.execute(query, [ts_oper]).df()


def get_operator_vessels(db, ts_oper):
    """Get list of vessels for an operator."""
    # Convert numpy types to native Python int
    ts_oper = int(ts_oper)
    query = """
        SELECT
            vessel_name,
            characteristic_desc,
            nrt,
            year_vessel,
            vessel_state
        FROM vessel_analytics_view
        WHERE ts_oper = ?
        ORDER BY vessel_name
    """
    return db.conn.execute(query, [ts_oper]).df()


def get_vessel_type_stats(db, filters):
    """Get statistics by vessel type."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            vtcc_vessel_type,
            COUNT(*) as vessel_count,
            AVG(nrt) as avg_nrt,
            AVG(year_vessel) as avg_year
        FROM vessel_analytics_view
        WHERE {where_clause} AND vtcc_vessel_type IS NOT NULL
        GROUP BY vtcc_vessel_type
        ORDER BY vessel_count DESC
    """

    return db.conn.execute(query, params).df()


def get_district_distribution(db, filters):
    """Get vessel distribution by district."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            district_name,
            COUNT(*) as vessel_count
        FROM vessel_analytics_view
        WHERE {where_clause} AND district_name IS NOT NULL
        GROUP BY district_name
        ORDER BY vessel_count DESC
    """

    return db.conn.execute(query, params).df()


def get_series_distribution(db, filters):
    """Get vessel distribution by series/region."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            series_name,
            COUNT(*) as vessel_count
        FROM vessel_analytics_view
        WHERE {where_clause} AND series_name IS NOT NULL
        GROUP BY series_name
        ORDER BY vessel_count DESC
    """

    return db.conn.execute(query, params).df()


def get_equipment_summary(db, filters):
    """Get equipment summary."""
    where_clause, params = build_where_clause(filters)

    query = f"""
        SELECT
            equip1_category as category,
            equip1_name as equipment_name,
            COUNT(*) as vessel_count
        FROM vessel_analytics_view
        WHERE {where_clause} AND equip1_name IS NOT NULL
        GROUP BY equip1_category, equip1_name
        ORDER BY vessel_count DESC
    """

    return db.conn.execute(query, params).df()


def search_vessels(db, vessel_name='', cg_number='', filters=None):
    """Search for vessels by name or CG number."""
    if filters is None:
        filters = {}

    where_clause, params = build_where_clause(filters)

    # Add search conditions
    conditions = [where_clause]
    if vessel_name:
        conditions.append("vessel_name LIKE ?")
        params.append(f'%{vessel_name}%')

    if cg_number:
        conditions.append("cg_number LIKE ?")
        params.append(f'%{cg_number}%')

    final_where = " AND ".join(conditions)

    query = f"""
        SELECT
            vessel_id,
            vessel_name,
            cg_number,
            vtcc_vessel_type,
            COALESCE(operator_name_std, operator_name) as operator_name,
            nrt,
            year_vessel,
            vessel_state
        FROM vessel_analytics_view
        WHERE {final_where}
        ORDER BY vessel_name
        LIMIT 100
    """

    return db.conn.execute(query, params).df()
