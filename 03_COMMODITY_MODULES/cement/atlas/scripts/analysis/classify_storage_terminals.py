#!/usr/bin/env python3
"""Classify cement storage/terminal/distribution facilities in epa_cement_consumers."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb

DB_PATH = 'atlas/data/atlas.duckdb'
con = duckdb.connect(DB_PATH)

print("=" * 70)
print("CEMENT STORAGE / TERMINAL CLASSIFICATION")
print("=" * 70)

# === Step 1: Add facility_subtype column if not exists ===
cols = [r[0] for r in con.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name='epa_cement_consumers'"
).fetchall()]

if 'facility_subtype' not in cols:
    con.execute("ALTER TABLE epa_cement_consumers ADD COLUMN facility_subtype VARCHAR DEFAULT 'OPERATING_FACILITY'")
    print("Added facility_subtype column")
else:
    # Reset to default
    con.execute("UPDATE epa_cement_consumers SET facility_subtype = 'OPERATING_FACILITY'")
    print("Reset facility_subtype column")

# === Step 2: Classify CEMENT_MANUFACTURER segment ===
# These are the 468 facilities with NAICS 327310 (Cement Manufacturing)
# But only ~100 are actual cement plants (per GEM cross-reference)
# Many are distribution terminals owned by cement companies

# 2a: Flag obvious terminals/distribution by name keywords
terminal_keywords = [
    ("TERMINAL", "CEMENT_TERMINAL"),
    ("DISTRIBUTION", "CEMENT_TERMINAL"),
    ("TRANSLOAD", "CEMENT_TERMINAL"),
    ("BULK CEMENT", "CEMENT_TERMINAL"),
    ("CEMENT SILO", "CEMENT_TERMINAL"),
    ("CEMENT STORAGE", "CEMENT_TERMINAL"),
]

print("\n--- Classifying CEMENT_MANUFACTURER terminals by name ---")
for keyword, subtype in terminal_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{keyword}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = '{subtype}'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{keyword}%'
        """)
        print(f"  '{keyword}' -> {subtype}: {cnt} facilities")

# 2b: Flag oilfield cement handling (Halliburton, Baker Hughes, Schlumberger)
oilfield_companies = ["HALLIBURTON", "BAKER HUGHES", "SCHLUMBERGER", "BJ SERVICES"]
for co in oilfield_companies:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{co}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'OILFIELD_CEMENT'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{co}%'
        """)
        print(f"  Oilfield '{co}': {cnt} facilities")

# 2c: Flag ash/fly ash handling (Headwaters, Boral Material Technologies)
ash_companies = ["HEADWATERS", "BORAL MATERIAL", "FLY ASH", "SEPARATION TECHNOLOGIES"]
for co in ash_companies:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{co}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'SCM_HANDLING'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{co}%'
        """)
        print(f"  SCM/Ash '{co}': {cnt} facilities")

# === Step 3: Classify across ALL segments ===
# Facilities with storage/terminal indicators in any segment

print("\n--- Classifying storage/terminal across all segments ---")
all_segment_keywords = [
    ("CEMENT TERMINAL", "CEMENT_TERMINAL"),
    ("CEMENT DEPOT", "CEMENT_TERMINAL"),
    ("BULK PLANT", "BULK_STORAGE"),
    ("BULK STORAGE", "BULK_STORAGE"),
    ("SILO", "BULK_STORAGE"),
    ("WAREHOUSE", "WAREHOUSE"),
]

for keyword, subtype in all_segment_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{keyword}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = '{subtype}'
            WHERE facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{keyword}%'
        """)
        print(f"  '{keyword}' -> {subtype}: {cnt} facilities")

# === Step 4: Known cement plant identification ===
# Cross-ref with GEM plants to mark confirmed actual cement plants
# GEM has 100 verified operational plants
print("\n--- Marking confirmed cement plants via GEM cross-reference ---")

# Use lat/lon proximity (within ~5km = 0.05 degrees) to match GEM plants
# GEM stores coords as "lat, lon" string - parse them
gem_raw = con.execute("""
    SELECT "Coordinates" FROM gem_plants
    WHERE "Coordinates" IS NOT NULL AND "Coordinates" != ''
""").fetchall()
gem_coords = []
for (coord_str,) in gem_raw:
    parts = coord_str.split(',')
    if len(parts) == 2:
        try:
            gem_coords.append((float(parts[0].strip()), float(parts[1].strip())))
        except ValueError:
            pass

# Build a WHERE clause matching any GEM plant within 0.05 degrees
geo_conditions = " OR ".join([
    f"(ABS(latitude - {lat}) < 0.05 AND ABS(longitude - {lon}) < 0.05)"
    for lat, lon in gem_coords
])

cnt_gem = con.execute(f"""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    AND facility_subtype = 'OPERATING_FACILITY'
    AND ({geo_conditions})
""").fetchone()[0]

con.execute(f"""
    UPDATE epa_cement_consumers
    SET facility_subtype = 'CEMENT_PLANT'
    WHERE segment = 'CEMENT_MANUFACTURER'
    AND facility_subtype = 'OPERATING_FACILITY'
    AND ({geo_conditions})
""")
print(f"  GEM-matched cement plants: {cnt_gem}")

# === Step 5: Remaining CEMENT_MANUFACTURER that are unclassified ===
# These have NAICS 327310 but didn't match GEM or terminal keywords
# Likely a mix of: grinding stations, import terminals, small/closed plants,
# or regional operations not in GEM
remaining_mfr = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    AND facility_subtype = 'OPERATING_FACILITY'
""").fetchone()[0]
print(f"\n  Remaining unclassified CEMENT_MANUFACTURER: {remaining_mfr}")

# Show them for review
print("\n--- Unclassified CEMENT_MANUFACTURER facilities ---")
r_unc = con.execute("""
    SELECT fac_name, fac_state, fac_city, corporate_parent
    FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    AND facility_subtype = 'OPERATING_FACILITY'
    ORDER BY corporate_parent NULLS LAST, fac_state
""").fetchall()
for name, st, city, cp in r_unc:
    print(f"  {name[:48]:<50} {st}  {(city or '')[:15]:<17} {(cp or '')[:25]}")

# === RESULTS ===
print(f"\n{'=' * 70}")
print("FACILITY SUBTYPE DISTRIBUTION")
print(f"{'=' * 70}")

r_dist = con.execute("""
    SELECT facility_subtype, segment, COUNT(*) c
    FROM epa_cement_consumers
    GROUP BY facility_subtype, segment
    ORDER BY facility_subtype, c DESC
""").fetchall()

current_subtype = None
for subtype, segment, c in r_dist:
    if subtype != current_subtype:
        if current_subtype is not None:
            print()
        current_subtype = subtype
        print(f"\n  {subtype}:")
    print(f"    {segment:<30} {c:>6}")

# Summary totals
print(f"\n{'=' * 70}")
print("SUMMARY BY SUBTYPE")
print(f"{'=' * 70}")
r_sum = con.execute("""
    SELECT facility_subtype, COUNT(*) c
    FROM epa_cement_consumers
    GROUP BY facility_subtype
    ORDER BY c DESC
""").fetchall()
total = 0
for subtype, c in r_sum:
    print(f"  {subtype:<30} {c:>6}")
    total += c
print(f"  {'TOTAL':<30} {total:>6}")

# CEMENT_MANUFACTURER breakdown
print(f"\n{'=' * 70}")
print("CEMENT_MANUFACTURER SEGMENT BREAKDOWN")
print(f"{'=' * 70}")
r_mfr = con.execute("""
    SELECT facility_subtype, COUNT(*) c
    FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    GROUP BY facility_subtype
    ORDER BY c DESC
""").fetchall()
for subtype, c in r_mfr:
    print(f"  {subtype:<30} {c:>6}")

con.close()
print("\nDone.")
