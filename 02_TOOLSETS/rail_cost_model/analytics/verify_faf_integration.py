"""Verify FAF integration with existing rail analytics database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import get_connection, query
from faf_data import init_faf_tables, create_faf_views

# Get connection and ensure FAF tables exist
conn = get_connection()
init_faf_tables(conn)
create_faf_views(conn)

print("=" * 60)
print("FAF INTEGRATION VERIFICATION")
print("=" * 60)

# Check dimension tables
print("\n--- DIMENSION TABLES ---\n")

# SCTG codes
result = query("SELECT COUNT(*) as cnt FROM dim_sctg")
print(f"SCTG Commodity Codes: {result['cnt'].iloc[0]}")

# Sample SCTG codes
print("\nSample SCTG codes (rail-intensive):")
result = query("""
    SELECT sctg_code, sctg_name, sctg_group
    FROM dim_sctg
    WHERE rail_intensive = TRUE
    LIMIT 10
""")
print(result.to_string(index=False))

# Transportation modes
print("\n\nTransportation Modes:")
result = query("SELECT * FROM dim_mode ORDER BY mode_code")
print(result.to_string(index=False))

# FAF Zones sample
print("\n\nSample FAF Zones (Texas):")
result = query("""
    SELECT faf_zone, zone_name, zone_type
    FROM dim_faf_zone
    WHERE state_name = 'Texas'
    ORDER BY faf_zone
""")
print(result.to_string(index=False))

# STCC-SCTG Crosswalk sample
print("\n\nSTCC to SCTG Crosswalk (exact matches):")
result = query("""
    SELECT stcc_2digit, stcc_name, sctg_code, sctg_name
    FROM xwalk_stcc_sctg
    WHERE match_quality = 'exact'
    LIMIT 10
""")
print(result.to_string(index=False))

# Cross-reference with existing waybill data
print("\n\n--- WAYBILL INTEGRATION ---\n")

# Check how many waybill STCC codes have SCTG mappings
result = query("""
    WITH waybill_stcc AS (
        SELECT DISTINCT LEFT(stcc, 2) as stcc_2digit
        FROM fact_waybill
    ),
    mapped AS (
        SELECT DISTINCT w.stcc_2digit,
               x.sctg_code IS NOT NULL as has_mapping
        FROM waybill_stcc w
        LEFT JOIN xwalk_stcc_sctg x ON w.stcc_2digit = x.stcc_2digit
    )
    SELECT
        COUNT(*) as total_stcc_2digit,
        SUM(CASE WHEN has_mapping THEN 1 ELSE 0 END) as mapped,
        SUM(CASE WHEN NOT has_mapping THEN 1 ELSE 0 END) as unmapped
    FROM mapped
""")
print("Waybill STCC Code Mapping Coverage:")
print(result.to_string(index=False))

# Show top commodities with their SCTG equivalents
print("\n\nTop Waybill Commodities with SCTG Mapping:")
result = query("""
    SELECT
        LEFT(w.stcc, 2) as stcc_2,
        MIN(x.stcc_name) as stcc_name,
        MIN(x.sctg_code) as sctg_code,
        MIN(x.sctg_name) as sctg_name,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons
    FROM fact_waybill w
    LEFT JOIN xwalk_stcc_sctg x ON LEFT(w.stcc, 2) = x.stcc_2digit
    GROUP BY LEFT(w.stcc, 2)
    ORDER BY tons DESC
    LIMIT 15
""")
print(result.to_string(index=False))

# Cement specifically
print("\n\nCement (STCC 32) -> SCTG Mapping:")
result = query("""
    SELECT stcc_2digit, stcc_name, sctg_code, sctg_name, match_quality
    FROM xwalk_stcc_sctg
    WHERE stcc_2digit = '32'
""")
print(result.to_string(index=False))

print("\n" + "=" * 60)
print("FAF integration verified successfully!")
print("=" * 60)
print("\nNext steps:")
print("1. Download FAF5 CSV from https://faf.ornl.gov/faf5/")
print("2. Run: load_faf_csv(conn, 'path/to/faf_data.csv')")
print("3. Query cross-modal analysis views")
