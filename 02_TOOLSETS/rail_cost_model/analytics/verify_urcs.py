"""Verify URCS cost model integration and run R/VC analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import get_connection, query
from urcs_model import (
    init_urcs_tables, create_urcs_views,
    calculate_urcs_cost, calculate_rvc_ratio,
    ShipmentCharacteristics, get_stb_jurisdiction_threshold
)

# Initialize database connection and URCS tables
conn = get_connection()
init_urcs_tables(conn)
create_urcs_views(conn)

print("=" * 70)
print("URCS RATE BENCHMARKING ANALYSIS")
print("=" * 70)

# Check unit costs loaded
print("\n--- URCS Unit Costs (2023, System Average) ---\n")
result = query("""
    SELECT * FROM dim_urcs_unit_costs
    WHERE year = 2023 AND region = 'system'
""")
for col in result.columns:
    print(f"  {col}: {result[col].iloc[0]}")

# R/VC Distribution by Commodity
print("\n\n--- R/VC RATIO BY COMMODITY (Top 15) ---\n")
result = query("""
    SELECT
        stcc_2digit,
        commodity,
        shipments,
        avg_rvc,
        median_rvc,
        p25_rvc,
        p75_rvc,
        above_threshold,
        pct_above_threshold
    FROM v_rvc_by_commodity
    WHERE shipments > 100
    ORDER BY avg_rvc DESC
    LIMIT 15
""")
print(result.to_string(index=False))

# R/VC by Distance Band
print("\n\n--- R/VC RATIO BY DISTANCE BAND ---\n")
result = query("""
    SELECT * FROM v_rvc_by_distance
    ORDER BY distance_band
""")
print(result.to_string(index=False))

# Cement-specific R/VC analysis
print("\n\n--- CEMENT (STCC 32411) R/VC ANALYSIS ---\n")
result = query("""
    SELECT
        COUNT(*) as shipments,
        ROUND(AVG(rvc_ratio), 1) as avg_rvc,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
        ROUND(MIN(rvc_ratio), 1) as min_rvc,
        ROUND(MAX(rvc_ratio), 1) as max_rvc,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold,
        ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above,
        ROUND(AVG(revenue), 2) as avg_revenue,
        ROUND(AVG(est_variable_cost), 2) as avg_var_cost
    FROM v_rvc_analysis
    WHERE stcc LIKE '324%'
      AND rvc_ratio > 0 AND rvc_ratio < 1000
""")
print(result.to_string(index=False))

# R/VC distribution for cement by distance
print("\n\nCement R/VC by Distance:")
result = query("""
    SELECT
        CASE
            WHEN miles < 250 THEN '1. Short (<250 mi)'
            WHEN miles < 500 THEN '2. Medium (250-500 mi)'
            WHEN miles < 1000 THEN '3. Long (500-1000 mi)'
            ELSE '4. Very Long (>1000 mi)'
        END as distance_band,
        COUNT(*) as shipments,
        ROUND(AVG(rvc_ratio), 1) as avg_rvc,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
        ROUND(AVG(revenue / tons), 2) as avg_rev_per_ton,
        ROUND(AVG(est_variable_cost / tons), 2) as avg_cost_per_ton,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold
    FROM v_rvc_analysis
    WHERE stcc LIKE '324%'
      AND rvc_ratio > 0 AND rvc_ratio < 1000
    GROUP BY 1
    ORDER BY 1
""")
print(result.to_string(index=False))

# Shipments above STB threshold
print("\n\n--- SHIPMENTS ABOVE STB 180% THRESHOLD ---\n")
result = query("""
    SELECT
        LEFT(stcc, 2) as stcc_2,
        commodity,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as count_above,
        COUNT(*) as total,
        ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above,
        ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN revenue ELSE 0 END), 0) as revenue_above
    FROM v_rvc_analysis
    WHERE rvc_ratio > 0 AND rvc_ratio < 1000
    GROUP BY LEFT(stcc, 2), commodity
    HAVING SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) > 50
    ORDER BY count_above DESC
    LIMIT 15
""")
print(result.to_string(index=False))

# Revenue vs. Variable Cost scatter data (for potential visualization)
print("\n\n--- SAMPLE SHIPMENTS FOR SCATTER PLOT ---\n")
result = query("""
    SELECT
        stcc,
        commodity,
        miles,
        tons,
        ROUND(revenue, 2) as revenue,
        ROUND(est_variable_cost, 2) as var_cost,
        ROUND(rvc_ratio, 1) as rvc_ratio
    FROM v_rvc_analysis
    WHERE stcc LIKE '324%'  -- Cement
      AND rvc_ratio > 0 AND rvc_ratio < 500
    ORDER BY RANDOM()
    LIMIT 10
""")
print(result.to_string(index=False))

# Summary statistics
print("\n\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

result = query("""
    SELECT
        COUNT(*) as total_shipments,
        ROUND(AVG(rvc_ratio), 1) as overall_avg_rvc,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as overall_median_rvc,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as total_above_threshold,
        ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above_threshold,
        ROUND(SUM(revenue), 0) as total_revenue,
        ROUND(SUM(est_variable_cost), 0) as total_var_cost,
        ROUND(SUM(revenue) / SUM(est_variable_cost) * 100, 1) as aggregate_rvc
    FROM v_rvc_analysis
    WHERE rvc_ratio > 0 AND rvc_ratio < 1000
""")
print(f"\nTotal Shipments Analyzed: {result['total_shipments'].iloc[0]:,}")
print(f"Overall Average R/VC: {result['overall_avg_rvc'].iloc[0]}%")
print(f"Overall Median R/VC: {result['overall_median_rvc'].iloc[0]}%")
print(f"Shipments Above 180% Threshold: {result['total_above_threshold'].iloc[0]:,} ({result['pct_above_threshold'].iloc[0]}%)")
print(f"Aggregate R/VC (Total Rev / Total Cost): {result['aggregate_rvc'].iloc[0]}%")
print(f"\nSTB Jurisdiction Threshold: {get_stb_jurisdiction_threshold()}%")
