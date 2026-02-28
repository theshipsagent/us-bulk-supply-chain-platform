#!/usr/bin/env python3
"""Pass 2: Refine remaining CEMENT_MANUFACTURER facilities + flag distribution across all segments."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb

DB_PATH = 'atlas/data/atlas.duckdb'
con = duckdb.connect(DB_PATH)

print("=" * 70)
print("STORAGE/TERMINAL CLASSIFICATION - PASS 2")
print("=" * 70)

# === 1: Known cement companies with multiple EPA entries that are likely plants ===
# Major cement producers - if they appear in CEMENT_MANUFACTURER, likely a real plant or grinding station
cement_producers_plants = [
    "CEMEX", "CalPortland", "Holcim Group", "Heidelberg Materials",
    "Buzzi Unicem", "CRH plc", "Eagle Materials", "GCC",
    "Argos USA", "Mitsubishi Cement", "National Cement", "Kosmos Cement",
    "Summit Materials", "St Marys Cement", "Suwannee American Cement",
]

print("\n--- Reclassifying known cement producers as CEMENT_PLANT ---")
for producer in cement_producers_plants:
    safe_p = producer.replace("'", "''")
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND corporate_parent = '{safe_p}'
    """).fetchone()[0]
    if cnt > 0:
        # Check names for signs of non-plant (quarry, batch, ready mix)
        plants = con.execute(f"""
            SELECT registry_id, fac_name FROM epa_cement_consumers
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND corporate_parent = '{safe_p}'
        """).fetchall()
        for rid, fname in plants:
            fn_upper = fname.upper()
            if any(kw in fn_upper for kw in ['READY MIX', 'READY M', 'REDI-MIX', 'BATCH PLANT',
                                               'QUARRY', 'AGGREGATE', 'ASPHALT', 'SAND']):
                con.execute(f"""
                    UPDATE epa_cement_consumers SET facility_subtype = 'MISCLASSIFIED_READYMIX'
                    WHERE registry_id = '{rid}'
                """)
            elif any(kw in fn_upper for kw in ['PACKAGING', 'PACKAG']):
                con.execute(f"""
                    UPDATE epa_cement_consumers SET facility_subtype = 'CEMENT_PACKAGING'
                    WHERE registry_id = '{rid}'
                """)
            elif any(kw in fn_upper for kw in ['DISTRIBUTOR', 'DISTRIBUT']):
                con.execute(f"""
                    UPDATE epa_cement_consumers SET facility_subtype = 'CEMENT_DISTRIBUTION'
                    WHERE registry_id = '{rid}'
                """)
            else:
                con.execute(f"""
                    UPDATE epa_cement_consumers SET facility_subtype = 'CEMENT_PLANT'
                    WHERE registry_id = '{rid}'
                """)
        print(f"  {producer}: {cnt} facilities classified")

# === 2: Name-based cement plant identification ===
# Facilities with "CEMENT" + location words = likely plants or grinding stations
print("\n--- Name-based cement plant/grinding identification ---")
cement_plant_names = [
    "CEMENT PLANT", "CEMENT CO", "CEMENT COMPANY", "CEMENT CORP",
    "PORTLAND CEMENT", "CEMENT LLC", "CEMENT INC", "CEMENT MANUFACTURING",
]
for pattern in cement_plant_names:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{pattern}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'CEMENT_PLANT'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{pattern}%'
        """)
        print(f"  '{pattern}': {cnt} -> CEMENT_PLANT")

# === 3: Obvious misclassifications (not cement at all) ===
print("\n--- Flagging non-cement facilities ---")
non_cement_keywords = [
    "TIRE", "LIBRARY", "SALVAGE", "METALS", "ELECTRONICS", "BATTERY",
    "RECYCLING", "PIPELINE", "GAS PROCESSING", "LUMBER", "SAWMILL",
    "STORAGE RENTALS", "AUTO PARTS", "FUEL STORAGE", "REFINING",
    "HIGHWAY DEPT", "DEPT OF TRANSPORTATION", "WELL SVC", "OIL",
    "EXIDE", "SCHUYLKILL", "SIERRA PACIFIC", "DUCOMMUN",
]
for kw in non_cement_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'NON_CEMENT_MISCLASS'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> NON_CEMENT_MISCLASS")

# === 4: Ready-mix/concrete plants misclassified as CEMENT_MANUFACTURER ===
print("\n--- Flagging misclassified ready-mix ---")
rmx_keywords = [
    "READY MIX", "READY M", "REDI MIX", "REDI-MIX", "READYMIX",
    "BATCH PLANT", "CONCRETE SUPPLY", "CONCRETE PLANT",
    "CONCRETE BATCHING", "PORTABLE PLANT", "PORTABLE #",
    "A CONCRETE", " RMC", "PLANT #",
]
for kw in rmx_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'MISCLASSIFIED_READYMIX'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> MISCLASSIFIED_READYMIX")

# === 5: Specialty/chemical cement (not portland cement plants) ===
print("\n--- Flagging specialty cement/chemical ---")
specialty_keywords = [
    "ARDEX", "BASF", "CONPROCO", "SAUEREISEN", "DEGUSSA",
    "POZZOLANIC", "MINERAL RESOURCE", "PROMETHEUS",
    "CAVITATION", "QUIKRETE", "CUSTOM BUILDING",
    "STUCCO", "KRETE INDUSTRIES",
]
for kw in specialty_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'SPECIALTY_CEMENT'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> SPECIALTY_CEMENT")

# === 6: Distributors across all segments ===
print("\n--- Flagging distributors ---")
dist_keywords = [
    "DISTRIBUTOR", "DISTRIBUT",
    "CONRAD YELVINGTON",  # Known cement distributor
]
for kw in dist_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'CEMENT_DISTRIBUTION'
            WHERE facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> CEMENT_DISTRIBUTION")

# === 7: SCM (supplementary cementitious materials) handling ===
print("\n--- Flagging SCM/fly ash facilities ---")
scm_keywords = ["FLY ASH", "SLAG", "GRINDING", "MILL ", "BLENDING"]
for kw in scm_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'GRINDING_SCM'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> GRINDING_SCM")

# === 8: Precast/block plants miscoded as 327310 ===
print("\n--- Flagging precast/block ---")
precast_keywords = ["PRECAST", "PRESTRESS", "BLOCK PLANT", "BLOCK-"]
for kw in precast_keywords:
    cnt = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        AND UPPER(fac_name) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET facility_subtype = 'MISCLASSIFIED_PRECAST'
            WHERE segment = 'CEMENT_MANUFACTURER'
            AND facility_subtype = 'OPERATING_FACILITY'
            AND UPPER(fac_name) LIKE '%{kw}%'
        """)
        print(f"  '{kw}': {cnt} -> MISCLASSIFIED_PRECAST")

# === FINAL RESULTS ===
print(f"\n{'=' * 70}")
print("FINAL FACILITY SUBTYPE DISTRIBUTION (ALL 15,782)")
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

print(f"\n{'=' * 70}")
print("CEMENT_MANUFACTURER SEGMENT BREAKDOWN (468 facilities)")
print(f"{'=' * 70}")
r_mfr = con.execute("""
    SELECT facility_subtype, COUNT(*) c
    FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    GROUP BY facility_subtype
    ORDER BY c DESC
""").fetchall()
mfr_total = 0
for subtype, c in r_mfr:
    print(f"  {subtype:<30} {c:>6}")
    mfr_total += c
print(f"  {'TOTAL':<30} {mfr_total:>6}")

# Show remaining unclassified
remaining = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
    AND facility_subtype = 'OPERATING_FACILITY'
""").fetchone()[0]
print(f"\n  Still unclassified: {remaining}")

if remaining > 0:
    print(f"\n--- Remaining unclassified CEMENT_MANUFACTURER ---")
    r_rem = con.execute("""
        SELECT fac_name, fac_state, corporate_parent
        FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        AND facility_subtype = 'OPERATING_FACILITY'
        ORDER BY fac_name
    """).fetchall()
    for name, st, cp in r_rem:
        print(f"  {name[:50]:<52} {st}  {(cp or '')[:25]}")

# === Cross-segment summary ===
print(f"\n{'=' * 70}")
print("STORAGE/TERMINAL/DISTRIBUTION FACILITIES (all segments)")
print(f"{'=' * 70}")
r_stor = con.execute("""
    SELECT facility_subtype, segment, COUNT(*) c
    FROM epa_cement_consumers
    WHERE facility_subtype IN ('CEMENT_TERMINAL', 'CEMENT_DISTRIBUTION', 'BULK_STORAGE',
                               'WAREHOUSE', 'OILFIELD_CEMENT', 'SCM_HANDLING', 'GRINDING_SCM')
    GROUP BY facility_subtype, segment
    ORDER BY facility_subtype, c DESC
""").fetchall()
for subtype, segment, c in r_stor:
    print(f"  {subtype:<25} {segment:<25} {c:>5}")

# Total storage-type
stor_total = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE facility_subtype IN ('CEMENT_TERMINAL', 'CEMENT_DISTRIBUTION', 'BULK_STORAGE',
                               'WAREHOUSE', 'OILFIELD_CEMENT', 'SCM_HANDLING', 'GRINDING_SCM')
""").fetchone()[0]
print(f"\n  Total storage/terminal/distribution: {stor_total}")

# === Cross-reference: Rail CEMENT_DISTRIBUTION sites ===
print(f"\n{'=' * 70}")
print("RAIL CEMENT_DISTRIBUTION SITES (294 from us_cement_facilities)")
print(f"{'=' * 70}")
r_rail = con.execute("""
    SELECT company, COUNT(*) c, COUNT(DISTINCT state) states
    FROM us_cement_facilities
    WHERE facility_type = 'CEMENT_DISTRIBUTION'
    GROUP BY company ORDER BY c DESC LIMIT 20
""").fetchall()
print(f"  {'Company':<45} Sites  States")
print(f"  {'-'*60}")
for co, c, s in r_rail:
    print(f"  {str(co)[:43]:<45} {c:>4}   {s:>3}")
print(f"\n  NOTE: These 294 rail distribution sites are NOT in epa_cement_consumers")
print(f"  They represent dedicated cement silos/terminals on railroad networks")

con.close()
print("\nDone.")
