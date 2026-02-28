-- ============================================================
-- HISTORICAL DATA EXTENSIONS
-- Add support for multi-year vessel tracking and comparisons
-- ============================================================

-- Add year-specific indexes for time-series queries
CREATE INDEX IF NOT EXISTS idx_vessels_fleet_year ON vessels(fleet_year);
CREATE INDEX IF NOT EXISTS idx_operators_fleet_year ON operators(fleet_year);

-- ============================================================
-- HISTORICAL COMPARISON VIEWS
-- ============================================================

-- View: Fleet Size by Year
CREATE OR REPLACE VIEW v_fleet_size_by_year AS
SELECT
    fleet_year,
    COUNT(DISTINCT vessel_id) as vessel_count,
    COUNT(DISTINCT ts_oper) as operator_count,
    AVG(nrt) as avg_nrt,
    SUM(nrt) as total_nrt,
    AVG(EXTRACT(YEAR FROM CURRENT_DATE) - year_vessel) as avg_age
FROM vessels
WHERE fleet_year IS NOT NULL
GROUP BY fleet_year
ORDER BY fleet_year;

COMMENT ON VIEW v_fleet_size_by_year IS 'Year-over-year fleet size trends';

-- View: Vessel Type Trends
CREATE OR REPLACE VIEW v_vessel_type_trends AS
SELECT
    v.fleet_year,
    vtcc.vessel_type,
    COUNT(*) as vessel_count,
    AVG(v.nrt) as avg_nrt
FROM vessels v
LEFT JOIN lookup_vtcc vtcc ON v.vtcc_code = vtcc.vtcc_code
WHERE v.fleet_year IS NOT NULL AND vtcc.vessel_type IS NOT NULL
GROUP BY v.fleet_year, vtcc.vessel_type
ORDER BY v.fleet_year, vessel_count DESC;

COMMENT ON VIEW v_vessel_type_trends IS 'Vessel type distribution over time';

-- View: Operator Growth/Decline
CREATE OR REPLACE VIEW v_operator_trends AS
WITH yearly_counts AS (
    SELECT
        ts_oper,
        fleet_year,
        COUNT(*) as vessel_count
    FROM vessels
    WHERE ts_oper IS NOT NULL AND fleet_year IS NOT NULL
    GROUP BY ts_oper, fleet_year
),
operator_info AS (
    SELECT DISTINCT ON (ts_oper)
        ts_oper,
        operator_name,
        operator_city,
        operator_state
    FROM operators
    WHERE operator_name IS NOT NULL
)
SELECT
    yc.ts_oper,
    oi.operator_name,
    oi.operator_city,
    oi.operator_state,
    yc.fleet_year,
    yc.vessel_count,
    LAG(yc.vessel_count) OVER (PARTITION BY yc.ts_oper ORDER BY yc.fleet_year) as prev_year_count,
    yc.vessel_count - LAG(yc.vessel_count) OVER (PARTITION BY yc.ts_oper ORDER BY yc.fleet_year) as year_over_year_change,
    CASE
        WHEN LAG(yc.vessel_count) OVER (PARTITION BY yc.ts_oper ORDER BY yc.fleet_year) IS NOT NULL
        THEN ROUND(((yc.vessel_count - LAG(yc.vessel_count) OVER (PARTITION BY yc.ts_oper ORDER BY yc.fleet_year))::NUMERIC /
                    LAG(yc.vessel_count) OVER (PARTITION BY yc.ts_oper ORDER BY yc.fleet_year) * 100), 1)
        ELSE NULL
    END as percent_change
FROM yearly_counts yc
LEFT JOIN operator_info oi ON yc.ts_oper = oi.ts_oper
ORDER BY yc.ts_oper, yc.fleet_year;

COMMENT ON VIEW v_operator_trends IS 'Operator fleet size changes year-over-year';

-- View: District Trends
CREATE OR REPLACE VIEW v_district_trends AS
SELECT
    o.dist_code,
    d.district_name,
    v.fleet_year,
    COUNT(DISTINCT v.vessel_id) as vessel_count,
    COUNT(DISTINCT v.ts_oper) as operator_count
FROM vessels v
LEFT JOIN operators o ON v.ts_oper = o.ts_oper
LEFT JOIN lookup_district d ON o.dist_code = d.dist_code
WHERE v.fleet_year IS NOT NULL AND d.district_name IS NOT NULL
GROUP BY o.dist_code, d.district_name, v.fleet_year
ORDER BY v.fleet_year, vessel_count DESC;

COMMENT ON VIEW v_district_trends IS 'Vessel distribution by district over time';

-- View: Equipment Adoption Trends
CREATE OR REPLACE VIEW v_equipment_trends AS
SELECT
    v.fleet_year,
    eq.equipment_name,
    eq.category,
    COUNT(DISTINCT v.vessel_id) as vessel_count
FROM vessels v
LEFT JOIN lookup_equipment eq ON v.equip1 = eq.equipment_code OR v.equip2 = eq.equipment_code
WHERE v.fleet_year IS NOT NULL AND eq.equipment_name IS NOT NULL
GROUP BY v.fleet_year, eq.equipment_name, eq.category
ORDER BY v.fleet_year, vessel_count DESC;

COMMENT ON VIEW v_equipment_trends IS 'Equipment usage trends over time';

-- View: New vs Retired Vessels
CREATE OR REPLACE VIEW v_vessel_lifecycle AS
WITH vessel_years AS (
    SELECT
        vessel_id,
        MIN(fleet_year) as first_year,
        MAX(fleet_year) as last_year,
        COUNT(DISTINCT fleet_year) as years_present
    FROM vessels
    WHERE fleet_year IS NOT NULL
    GROUP BY vessel_id
)
SELECT
    fleet_year,
    COUNT(CASE WHEN first_year = fleet_year THEN 1 END) as new_vessels,
    COUNT(CASE WHEN last_year = fleet_year AND fleet_year < (SELECT MAX(fleet_year) FROM vessels) THEN 1 END) as retired_vessels,
    COUNT(*) as total_tracked
FROM vessels v
JOIN vessel_years vy ON v.vessel_id = vy.vessel_id
WHERE v.fleet_year IS NOT NULL
GROUP BY fleet_year
ORDER BY fleet_year;

COMMENT ON VIEW v_vessel_lifecycle IS 'New vessel additions and retirements by year';

-- View: Fleet Age Distribution by Year
CREATE OR REPLACE VIEW v_fleet_age_trends AS
SELECT
    fleet_year,
    CASE
        WHEN (fleet_year - year_vessel) <= 10 THEN 'Modern (0-10 yrs)'
        WHEN (fleet_year - year_vessel) <= 20 THEN 'Mature (11-20 yrs)'
        WHEN (fleet_year - year_vessel) <= 30 THEN 'Aging (21-30 yrs)'
        ELSE 'Legacy (30+ yrs)'
    END as age_bracket,
    COUNT(*) as vessel_count,
    AVG(nrt) as avg_nrt
FROM vessels
WHERE fleet_year IS NOT NULL AND year_vessel IS NOT NULL
GROUP BY fleet_year, age_bracket
ORDER BY fleet_year, age_bracket;

COMMENT ON VIEW v_fleet_age_trends IS 'Fleet age distribution trends over time';

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Function: Get years available in database
CREATE OR REPLACE FUNCTION get_available_years()
RETURNS TABLE(fleet_year INTEGER, vessel_count BIGINT, operator_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.fleet_year,
        COUNT(DISTINCT v.vessel_id) as vessel_count,
        COUNT(DISTINCT v.ts_oper) as operator_count
    FROM vessels v
    WHERE v.fleet_year IS NOT NULL
    GROUP BY v.fleet_year
    ORDER BY v.fleet_year DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_available_years IS 'List all years with data in the database';

-- Function: Compare two years
CREATE OR REPLACE FUNCTION compare_years(year1 INTEGER, year2 INTEGER)
RETURNS TABLE(
    metric TEXT,
    year1_value NUMERIC,
    year2_value NUMERIC,
    change NUMERIC,
    percent_change NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH year1_stats AS (
        SELECT
            COUNT(DISTINCT vessel_id) as vessels,
            COUNT(DISTINCT ts_oper) as operators,
            AVG(nrt) as avg_nrt,
            SUM(nrt) as total_nrt
        FROM vessels
        WHERE fleet_year = year1
    ),
    year2_stats AS (
        SELECT
            COUNT(DISTINCT vessel_id) as vessels,
            COUNT(DISTINCT ts_oper) as operators,
            AVG(nrt) as avg_nrt,
            SUM(nrt) as total_nrt
        FROM vessels
        WHERE fleet_year = year2
    )
    SELECT 'Total Vessels'::TEXT, y1.vessels::NUMERIC, y2.vessels::NUMERIC,
           (y2.vessels - y1.vessels)::NUMERIC,
           ROUND((y2.vessels - y1.vessels)::NUMERIC / y1.vessels * 100, 2)
    FROM year1_stats y1, year2_stats y2
    UNION ALL
    SELECT 'Total Operators'::TEXT, y1.operators::NUMERIC, y2.operators::NUMERIC,
           (y2.operators - y1.operators)::NUMERIC,
           ROUND((y2.operators - y1.operators)::NUMERIC / y1.operators * 100, 2)
    FROM year1_stats y1, year2_stats y2
    UNION ALL
    SELECT 'Average NRT'::TEXT, ROUND(y1.avg_nrt, 2), ROUND(y2.avg_nrt, 2),
           ROUND(y2.avg_nrt - y1.avg_nrt, 2),
           ROUND((y2.avg_nrt - y1.avg_nrt) / y1.avg_nrt * 100, 2)
    FROM year1_stats y1, year2_stats y2
    UNION ALL
    SELECT 'Total NRT'::TEXT, ROUND(y1.total_nrt, 0), ROUND(y2.total_nrt, 0),
           ROUND(y2.total_nrt - y1.total_nrt, 0),
           ROUND((y2.total_nrt - y1.total_nrt) / y1.total_nrt * 100, 2)
    FROM year1_stats y1, year2_stats y2;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compare_years IS 'Compare fleet statistics between two years';

-- ============================================================
-- EXAMPLE HISTORICAL QUERIES
-- ============================================================

-- Example 1: Fleet growth trend
-- SELECT * FROM v_fleet_size_by_year;

-- Example 2: Top growing operators
-- SELECT *
-- FROM v_operator_trends
-- WHERE fleet_year = 2023 AND percent_change IS NOT NULL
-- ORDER BY percent_change DESC
-- LIMIT 20;

-- Example 3: Compare 2022 vs 2023
-- SELECT * FROM compare_years(2022, 2023);

-- Example 4: Vessel type changes
-- SELECT vessel_type, fleet_year, vessel_count
-- FROM v_vessel_type_trends
-- WHERE vessel_type = 'Self-Propelled, Dry Cargo'
-- ORDER BY fleet_year;

-- ============================================================
-- SCHEMA EXTENSION COMPLETE
-- ============================================================
