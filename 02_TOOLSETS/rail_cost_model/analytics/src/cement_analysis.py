"""Cement (STCC 32411) Analysis"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import query
import pandas as pd

pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 30)

print('=' * 80)
print('CEMENT ANALYSIS - STCC 32411 (Hydraulic Cement)')
print('=' * 80)

# Overall cement stats
print('\n=== OVERALL CEMENT STATISTICS ===')
result = query("""
    SELECT
        COUNT(*) as sample_records,
        CAST(SUM(exp_carloads) AS BIGINT) as total_carloads,
        CAST(SUM(exp_tons) AS BIGINT) as total_tons,
        CAST(SUM(exp_freight_rev) AS BIGINT) as total_revenue,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 2) as avg_rev_per_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 4) as avg_rev_per_ton,
        ROUND(AVG(short_line_miles), 0) as avg_miles
    FROM fact_waybill
    WHERE stcc = '32411'
""")
print(result.to_string(index=False))

# Revenue per ton analysis
print('\n=== PRICE DISTRIBUTION (Revenue per Ton) ===')
result = query("""
    WITH priced AS (
        SELECT *,
            exp_freight_rev/NULLIF(exp_tons,0) as rev_per_ton
        FROM fact_waybill
        WHERE stcc = '32411' AND exp_tons > 0
    )
    SELECT
        CASE
            WHEN rev_per_ton < 20 THEN '1. Under $20/ton'
            WHEN rev_per_ton < 30 THEN '2. $20-30/ton'
            WHEN rev_per_ton < 40 THEN '3. $30-40/ton'
            WHEN rev_per_ton < 50 THEN '4. $40-50/ton'
            WHEN rev_per_ton < 75 THEN '5. $50-75/ton'
            ELSE '6. Over $75/ton'
        END as price_range,
        COUNT(*) as shipments,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        ROUND(AVG(short_line_miles), 0) as avg_miles
    FROM priced
    GROUP BY 1
    ORDER BY 1
""")
print(result.to_string(index=False))

# Revenue per car analysis
print('\n=== PRICE DISTRIBUTION (Revenue per Carload) ===')
result = query("""
    WITH priced AS (
        SELECT *,
            exp_freight_rev/NULLIF(exp_carloads,0) as rev_per_car
        FROM fact_waybill
        WHERE stcc = '32411' AND exp_carloads > 0
    )
    SELECT
        CASE
            WHEN rev_per_car < 2000 THEN '1. Under $2,000'
            WHEN rev_per_car < 3000 THEN '2. $2,000-3,000'
            WHEN rev_per_car < 4000 THEN '3. $3,000-4,000'
            WHEN rev_per_car < 5000 THEN '4. $4,000-5,000'
            WHEN rev_per_car < 6000 THEN '5. $5,000-6,000'
            ELSE '6. Over $6,000'
        END as price_range,
        COUNT(*) as shipments,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        ROUND(AVG(short_line_miles), 0) as avg_miles
    FROM priced
    GROUP BY 1
    ORDER BY 1
""")
print(result.to_string(index=False))

# Top O-D pairs
print('\n=== TOP 20 CEMENT ROUTES BY VOLUME ===')
result = query("""
    SELECT
        w.origin_bea,
        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
        w.term_bea,
        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        CAST(SUM(w.exp_freight_rev) AS BIGINT) as revenue,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as rev_per_car,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_tons), 2) as rev_per_ton,
        ROUND(AVG(w.short_line_miles), 0) as avg_miles
    FROM fact_waybill w
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2, 3, 4
    ORDER BY carloads DESC
    LIMIT 20
""")
print(result.to_string(index=False))

# Top origin regions
print('\n=== TOP CEMENT ORIGIN REGIONS ===')
result = query("""
    SELECT
        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
        COALESCE(o.region, 'Unknown') as region,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
    FROM fact_waybill w
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 15
""")
print(result.to_string(index=False))

# Top destination regions
print('\n=== TOP CEMENT DESTINATION REGIONS ===')
result = query("""
    SELECT
        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
        COALESCE(d.region, 'Unknown') as region,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
    FROM fact_waybill w
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 15
""")
print(result.to_string(index=False))

# Quarterly seasonality
print('\n=== CEMENT SEASONALITY (by Quarter) ===')
result = query("""
    SELECT
        EXTRACT(QUARTER FROM waybill_date) as quarter,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(exp_tons) AS BIGINT) as tons,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 0) as avg_rev_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as avg_rev_ton
    FROM fact_waybill
    WHERE stcc = '32411'
    GROUP BY 1
    ORDER BY 1
""")
print(result.to_string(index=False))

# Distance-based pricing
print('\n=== CEMENT PRICING BY DISTANCE ===')
result = query("""
    SELECT
        CASE
            WHEN short_line_miles < 200 THEN '< 200 miles'
            WHEN short_line_miles < 400 THEN '200-400 miles'
            WHEN short_line_miles < 600 THEN '400-600 miles'
            WHEN short_line_miles < 800 THEN '600-800 miles'
            ELSE '> 800 miles'
        END as distance_band,
        COUNT(*) as shipments,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 0) as rev_per_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as rev_per_ton,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads) / AVG(short_line_miles), 3) as rev_per_car_mile
    FROM fact_waybill
    WHERE stcc = '32411' AND short_line_miles > 0
    GROUP BY 1
    ORDER BY MIN(short_line_miles)
""")
print(result.to_string(index=False))

print('\n' + '=' * 80)
print('Analysis complete!')
