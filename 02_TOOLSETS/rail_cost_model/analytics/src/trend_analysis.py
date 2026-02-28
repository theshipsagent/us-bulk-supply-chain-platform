"""
Trend Analysis Module for Rail Analytics

Provides views and functions for analyzing multi-year trends in:
- Commodity volumes and revenue
- Pricing trends (revenue per ton, per car)
- Route shifts
- Modal competition
- Seasonal patterns
"""

from .database import get_connection, query
import pandas as pd


def create_trend_views(conn):
    """Create analytical views for trend analysis."""

    # Annual commodity summary
    conn.execute("""
        CREATE OR REPLACE VIEW v_annual_commodity_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            stcc_2digit,
            s.stcc_group as commodity_group,
            COUNT(*) as sample_count,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue,
            ROUND(SUM(exp_freight_rev) / NULLIF(SUM(exp_tons), 0), 2) as rev_per_ton,
            ROUND(SUM(exp_freight_rev) / NULLIF(SUM(exp_carloads), 0), 2) as rev_per_car,
            ROUND(SUM(exp_tons) / NULLIF(SUM(exp_carloads), 0), 1) as tons_per_car
        FROM fact_waybill w
        LEFT JOIN dim_stcc s ON w.stcc = s.stcc_code
        WHERE waybill_date IS NOT NULL
        GROUP BY 1, 2, 3
        ORDER BY 1, carloads DESC
    """)

    # Quarterly trends
    conn.execute("""
        CREATE OR REPLACE VIEW v_quarterly_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            EXTRACT(QUARTER FROM waybill_date) as quarter,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue,
            ROUND(SUM(exp_freight_rev) / NULLIF(SUM(exp_tons), 0), 2) as rev_per_ton,
            COUNT(DISTINCT stcc_2digit) as commodity_count,
            COUNT(DISTINCT origin_bea || '-' || term_bea) as lane_count
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    # Year-over-year growth by commodity
    conn.execute("""
        CREATE OR REPLACE VIEW v_yoy_commodity_growth AS
        WITH annual AS (
            SELECT
                EXTRACT(YEAR FROM waybill_date) as year,
                stcc_2digit,
                SUM(exp_carloads) as carloads,
                SUM(exp_tons) as tons,
                SUM(exp_freight_rev) as revenue
            FROM fact_waybill
            WHERE waybill_date IS NOT NULL
            GROUP BY 1, 2
        )
        SELECT
            a.year,
            a.stcc_2digit,
            s.stcc_group as commodity_group,
            CAST(a.carloads AS BIGINT) as carloads,
            CAST(a.tons AS BIGINT) as tons,
            ROUND(a.revenue, 0) as revenue,
            -- Year-over-year changes
            ROUND((a.carloads - LAG(a.carloads) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year))
                / NULLIF(LAG(a.carloads) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year), 0) * 100, 1)
                as carload_yoy_pct,
            ROUND((a.tons - LAG(a.tons) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year))
                / NULLIF(LAG(a.tons) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year), 0) * 100, 1)
                as tons_yoy_pct,
            ROUND((a.revenue - LAG(a.revenue) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year))
                / NULLIF(LAG(a.revenue) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year), 0) * 100, 1)
                as revenue_yoy_pct
        FROM annual a
        LEFT JOIN dim_stcc s ON a.stcc_2digit = LEFT(s.stcc_code, 2)
        ORDER BY a.stcc_2digit, a.year
    """)

    # Route trends (O-D pairs over time)
    conn.execute("""
        CREATE OR REPLACE VIEW v_route_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            origin_bea,
            COALESCE(o.bea_name, 'Unknown') as origin_name,
            term_bea,
            COALESCE(d.bea_name, 'Unknown') as dest_name,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        WHERE waybill_date IS NOT NULL
          AND origin_bea != '000' AND term_bea != '000'
        GROUP BY 1, 2, 3, 4, 5
        HAVING SUM(exp_carloads) > 100
    """)

    # Pricing trends by commodity
    conn.execute("""
        CREATE OR REPLACE VIEW v_pricing_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            stcc_2digit,
            s.stcc_group as commodity_group,
            ROUND(AVG(exp_freight_rev / NULLIF(exp_tons, 0)), 2) as avg_rev_per_ton,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY exp_freight_rev / NULLIF(exp_tons, 0)), 2)
                as p25_rev_per_ton,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY exp_freight_rev / NULLIF(exp_tons, 0)), 2)
                as median_rev_per_ton,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY exp_freight_rev / NULLIF(exp_tons, 0)), 2)
                as p75_rev_per_ton,
            ROUND(AVG(exp_freight_rev / NULLIF(exp_carloads, 0)), 2) as avg_rev_per_car,
            COUNT(*) as sample_count
        FROM fact_waybill w
        LEFT JOIN dim_stcc s ON w.stcc = s.stcc_code
        WHERE waybill_date IS NOT NULL
          AND exp_tons > 0 AND exp_freight_rev > 0
        GROUP BY 1, 2, 3
    """)

    # Cement-specific trends
    conn.execute("""
        CREATE OR REPLACE VIEW v_cement_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            EXTRACT(QUARTER FROM waybill_date) as quarter,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue,
            ROUND(AVG(exp_freight_rev / NULLIF(exp_tons, 0)), 2) as avg_rev_per_ton,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
                (ORDER BY exp_freight_rev / NULLIF(exp_tons, 0)), 2) as median_rev_per_ton,
            COUNT(*) as sample_count
        FROM fact_waybill
        WHERE stcc LIKE '324%'
          AND waybill_date IS NOT NULL
          AND exp_tons > 0
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    # Coal trends (declining industry)
    conn.execute("""
        CREATE OR REPLACE VIEW v_coal_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue,
            ROUND(AVG(exp_freight_rev / NULLIF(exp_tons, 0)), 2) as avg_rev_per_ton,
            COUNT(DISTINCT origin_bea || '-' || term_bea) as active_lanes
        FROM fact_waybill
        WHERE stcc LIKE '11%'
          AND waybill_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)

    # Intermodal trends
    conn.execute("""
        CREATE OR REPLACE VIEW v_intermodal_trends AS
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            CASE WHEN all_rail_intermodal = 1 THEN 'All Rail'
                 WHEN all_rail_intermodal = 2 THEN 'Intermodal'
                 ELSE 'Unknown'
            END as service_type,
            CAST(SUM(exp_carloads) AS BIGINT) as carloads,
            CAST(SUM(exp_tons) AS BIGINT) as tons,
            ROUND(SUM(exp_freight_rev), 0) as revenue
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    print("Created trend analysis views:")
    print("  - v_annual_commodity_trends")
    print("  - v_quarterly_trends")
    print("  - v_yoy_commodity_growth")
    print("  - v_route_trends")
    print("  - v_pricing_trends")
    print("  - v_cement_trends")
    print("  - v_coal_trends")
    print("  - v_intermodal_trends")


def get_trend_summary():
    """Get summary of trend data available."""
    result = {}

    # Year range
    years = query("""
        SELECT
            MIN(EXTRACT(YEAR FROM waybill_date)) as min_year,
            MAX(EXTRACT(YEAR FROM waybill_date)) as max_year,
            COUNT(DISTINCT EXTRACT(YEAR FROM waybill_date)) as num_years
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
    """)
    result['year_range'] = f"{int(years['min_year'].iloc[0])}-{int(years['max_year'].iloc[0])}"
    result['num_years'] = int(years['num_years'].iloc[0])

    # Records by year
    by_year = query("""
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            COUNT(*) as records,
            SUM(exp_carloads) as carloads
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)
    result['by_year'] = by_year

    return result


def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
    """Calculate Compound Annual Growth Rate."""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def get_commodity_cagrs():
    """Calculate CAGR for each commodity category."""
    data = query("""
        SELECT
            stcc_2digit,
            MIN(EXTRACT(YEAR FROM waybill_date)) as start_year,
            MAX(EXTRACT(YEAR FROM waybill_date)) as end_year,
            SUM(CASE WHEN EXTRACT(YEAR FROM waybill_date) =
                (SELECT MIN(EXTRACT(YEAR FROM waybill_date)) FROM fact_waybill)
                THEN exp_tons ELSE 0 END) as start_tons,
            SUM(CASE WHEN EXTRACT(YEAR FROM waybill_date) =
                (SELECT MAX(EXTRACT(YEAR FROM waybill_date)) FROM fact_waybill)
                THEN exp_tons ELSE 0 END) as end_tons,
            SUM(CASE WHEN EXTRACT(YEAR FROM waybill_date) =
                (SELECT MIN(EXTRACT(YEAR FROM waybill_date)) FROM fact_waybill)
                THEN exp_freight_rev ELSE 0 END) as start_rev,
            SUM(CASE WHEN EXTRACT(YEAR FROM waybill_date) =
                (SELECT MAX(EXTRACT(YEAR FROM waybill_date)) FROM fact_waybill)
                THEN exp_freight_rev ELSE 0 END) as end_rev
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
        GROUP BY stcc_2digit
        HAVING start_tons > 0 AND end_tons > 0
    """)

    results = []
    for _, row in data.iterrows():
        years = row['end_year'] - row['start_year']
        if years > 0:
            tons_cagr = calculate_cagr(row['start_tons'], row['end_tons'], years)
            rev_cagr = calculate_cagr(row['start_rev'], row['end_rev'], years)
            results.append({
                'stcc_2digit': row['stcc_2digit'],
                'start_year': int(row['start_year']),
                'end_year': int(row['end_year']),
                'tons_cagr': round(tons_cagr, 1),
                'revenue_cagr': round(rev_cagr, 1),
            })

    return pd.DataFrame(results)


def init_trends(conn=None):
    """Initialize trend analysis (create views)."""
    if conn is None:
        conn = get_connection()
    create_trend_views(conn)


if __name__ == "__main__":
    conn = get_connection()
    create_trend_views(conn)

    print("\n" + "=" * 60)
    print("TREND ANALYSIS SUMMARY")
    print("=" * 60)

    summary = get_trend_summary()
    print(f"\nData Range: {summary['year_range']} ({summary['num_years']} years)")

    print("\nRecords by Year:")
    print(summary['by_year'].to_string(index=False))
