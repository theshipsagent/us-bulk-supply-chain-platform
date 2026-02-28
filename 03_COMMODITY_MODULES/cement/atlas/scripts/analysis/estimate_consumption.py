#!/usr/bin/env python3
"""Estimate annual cement consumption for each EPA facility.

Model based on:
- USGS MCS 2025 (110M MT shipped, segment splits)
- NRMCA plant statistics (~5,500 plants, ~370M cy/yr)
- PCA cement content per cubic yard (500-600 lbs)
- GEM Cement Tracker (individual plant capacities)
- Tampa Cement Market Study (per-plant ranges by type)
- First-principles engineering calculations

Calibrated against USGS 2024 total: ~125.3 million metric tonnes
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb
import pandas as pd

DB_PATH = 'atlas/data/atlas.duckdb'
con = duckdb.connect(DB_PATH)

print("=" * 70)
print("CEMENT CONSUMPTION ESTIMATION MODEL")
print("=" * 70)

# =========================================================================
# CONSUMPTION LOOKUP BY SEGMENT + FACILITY_SUBTYPE
# =========================================================================
# Format: (segment, facility_subtype) -> (low, median, high) in metric tons/yr
# We use MEDIAN as the default estimate

CONSUMPTION_ESTIMATES = {
    # --- READY_MIX (12,680 facilities) ---
    # NRMCA: median plant ~45,000 cy/yr, ~520-550 lbs cement/cy after SCM
    # Median = 8,200 MT Portland cement/yr
    ('READY_MIX', 'OPERATING_FACILITY'):    (3000, 8200, 18000),
    ('READY_MIX', 'BULK_STORAGE'):          (0, 0, 0),        # storage only, not consumer
    ('READY_MIX', 'CEMENT_TERMINAL'):       (50000, 150000, 400000),  # throughput
    ('READY_MIX', 'CEMENT_DISTRIBUTION'):   (20000, 80000, 200000),
    ('READY_MIX', 'WAREHOUSE'):             (500, 1500, 3000),

    # --- CONCRETE_BLOCK_BRICK (997 facilities) ---
    # Median plant: 10M blocks/yr, 4.2 lbs cement/block, 40-50% SCM
    # = ~10,000 MT Portland cement/yr
    ('CONCRETE_BLOCK_BRICK', 'OPERATING_FACILITY'): (5000, 10000, 25000),
    ('CONCRETE_BLOCK_BRICK', 'WAREHOUSE'):          (0, 0, 0),

    # --- CONCRETE_PIPE (386 facilities) ---
    # High-strength concrete, 700-800 lbs cement/cy, ~25,000 cy/yr median
    ('CONCRETE_PIPE', 'OPERATING_FACILITY'):        (2000, 4500, 8000),
    ('CONCRETE_PIPE', 'CEMENT_DISTRIBUTION'):       (2000, 4500, 8000),

    # --- OTHER_CONCRETE_PRODUCTS (1,248 facilities) ---
    # Heterogeneous: pavers, stucco, dry-mix, roof tile, specialty
    ('OTHER_CONCRETE_PRODUCTS', 'OPERATING_FACILITY'):  (1000, 3000, 8000),
    ('OTHER_CONCRETE_PRODUCTS', 'BULK_STORAGE'):        (0, 0, 0),
    ('OTHER_CONCRETE_PRODUCTS', 'WAREHOUSE'):           (0, 0, 0),

    # --- CEMENT_MANUFACTURER (468 facilities) ---
    # Broken into subtypes by our classification
    ('CEMENT_MANUFACTURER', 'CEMENT_PLANT'):            (500000, 870000, 2100000),  # PRODUCTION
    ('CEMENT_MANUFACTURER', 'CEMENT_TERMINAL'):         (50000, 150000, 400000),    # throughput
    ('CEMENT_MANUFACTURER', 'CEMENT_DISTRIBUTION'):     (20000, 80000, 200000),
    ('CEMENT_MANUFACTURER', 'CEMENT_PACKAGING'):        (10000, 30000, 80000),
    ('CEMENT_MANUFACTURER', 'OILFIELD_CEMENT'):         (5000, 15000, 40000),
    ('CEMENT_MANUFACTURER', 'SCM_HANDLING'):            (10000, 30000, 80000),
    ('CEMENT_MANUFACTURER', 'GRINDING_SCM'):            (50000, 200000, 500000),    # grinding stations
    ('CEMENT_MANUFACTURER', 'SPECIALTY_CEMENT'):        (2000, 8000, 20000),
    ('CEMENT_MANUFACTURER', 'MISCLASSIFIED_READYMIX'):  (3000, 8200, 18000),        # same as ready-mix
    ('CEMENT_MANUFACTURER', 'MISCLASSIFIED_PRECAST'):   (3000, 8000, 15000),
    ('CEMENT_MANUFACTURER', 'NON_CEMENT_MISCLASS'):     (0, 0, 0),                  # not cement at all
    ('CEMENT_MANUFACTURER', 'OPERATING_FACILITY'):      (1000, 5000, 15000),        # unclassified mix

    # --- CEMENT_CONCRETE_GENERAL (3 facilities) ---
    ('CEMENT_CONCRETE_GENERAL', 'OPERATING_FACILITY'):  (1000, 5000, 15000),
    ('CEMENT_CONCRETE_GENERAL', 'CEMENT_TERMINAL'):     (50000, 150000, 400000),
}

# Default fallback
DEFAULT_ESTIMATE = (1000, 3000, 8000)

# =========================================================================
# LOAD DATA
# =========================================================================
print("\nLoading facilities...")
df = con.execute("""
    SELECT registry_id, fac_name, fac_city, fac_state, fac_zip,
           latitude, longitude, segment, facility_subtype,
           corporate_parent, parent_type
    FROM epa_cement_consumers
""").fetchdf()
print(f"  Loaded {len(df):,} facilities")

# Load GEM plant capacities for precise cement plant estimates
print("Loading GEM plant capacities...")
gem = con.execute("""
    SELECT "GEM Asset name (English)" as plant_name,
           "Cement Capacity (millions metric tonnes per annum)" as cap_str,
           "Subnational unit" as state,
           "Coordinates" as coords
    FROM gem_plants
""").fetchall()

gem_caps = {}  # state -> [(plant_name, capacity_mtpa)]
for plant, cap_str, state, coords in gem:
    if not cap_str or str(cap_str).strip() == '':
        continue
    cap_s = str(cap_str).strip()
    if cap_s.startswith('>'):
        cap_s = cap_s[1:]
    try:
        cap = float(cap_s)
        if state not in gem_caps:
            gem_caps[state] = []
        # Parse coordinates
        lat, lon = None, None
        if coords:
            parts = str(coords).split(',')
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                except:
                    pass
        gem_caps[state].append((plant, cap, lat, lon))
    except:
        pass

print(f"  GEM plants with capacity: {sum(len(v) for v in gem_caps.values())}")

# =========================================================================
# APPLY ESTIMATES
# =========================================================================
print("\nApplying consumption estimates...")

estimates_low = []
estimates_med = []
estimates_high = []
estimate_methods = []
estimate_notes = []

for idx, row in df.iterrows():
    seg = row['segment']
    subtype = row['facility_subtype']
    key = (seg, subtype)

    # Special handling for CEMENT_PLANT: use GEM capacity if available
    if subtype == 'CEMENT_PLANT' and pd.notna(row['latitude']) and pd.notna(row['fac_state']):
        # Try to match to GEM by lat/lon proximity
        matched_gem = None
        fac_lat = row['latitude']
        fac_lon = row['longitude']

        # Check all states (GEM uses full state names)
        for st, plants in gem_caps.items():
            for pname, cap, glat, glon in plants:
                if glat is not None and glon is not None:
                    if abs(fac_lat - glat) < 0.05 and abs(fac_lon - glon) < 0.05:
                        matched_gem = (pname, cap)
                        break
            if matched_gem:
                break

        if matched_gem:
            # Use GEM capacity * 72% utilization for production estimate
            cap_mt = matched_gem[1] * 1_000_000
            prod_mt = cap_mt * 0.72
            estimates_low.append(int(cap_mt * 0.50))   # low utilization
            estimates_med.append(int(prod_mt))          # 72% utilization
            estimates_high.append(int(cap_mt * 0.90))   # high utilization
            estimate_methods.append('GEM_CAPACITY')
            estimate_notes.append(f"GEM: {matched_gem[0]}, {matched_gem[1]:.2f} mtpa")
            continue

    # Standard lookup
    low, med, high = CONSUMPTION_ESTIMATES.get(key, DEFAULT_ESTIMATE)
    estimates_low.append(low)
    estimates_med.append(med)
    estimates_high.append(high)
    estimate_methods.append('MODEL_ESTIMATE')
    estimate_notes.append(f"Based on {seg}/{subtype} median")

df['est_cement_low_mt'] = estimates_low
df['est_cement_median_mt'] = estimates_med
df['est_cement_high_mt'] = estimates_high
df['est_method'] = estimate_methods
df['est_notes'] = estimate_notes

# =========================================================================
# CALIBRATION CHECK
# =========================================================================
print("\n" + "=" * 70)
print("CALIBRATION CHECK vs USGS")
print("=" * 70)

# Total consumption (excluding production plants and terminals - those are supply side)
consumption_segments = ['READY_MIX', 'CONCRETE_BLOCK_BRICK', 'CONCRETE_PIPE',
                        'OTHER_CONCRETE_PRODUCTS', 'CEMENT_CONCRETE_GENERAL']
consumption_subtypes_exclude = ['CEMENT_TERMINAL', 'CEMENT_DISTRIBUTION',
                                 'BULK_STORAGE', 'WAREHOUSE', 'NON_CEMENT_MISCLASS']

mask_consumer = (df['segment'].isin(consumption_segments)) & \
                (~df['facility_subtype'].isin(consumption_subtypes_exclude))

total_consumer_median = df.loc[mask_consumer, 'est_cement_median_mt'].sum()
total_consumer_low = df.loc[mask_consumer, 'est_cement_low_mt'].sum()
total_consumer_high = df.loc[mask_consumer, 'est_cement_high_mt'].sum()

# Also add misclassified ready-mix/precast from CEMENT_MANUFACTURER
mask_misclass = df['facility_subtype'].isin(['MISCLASSIFIED_READYMIX', 'MISCLASSIFIED_PRECAST'])
total_consumer_median += df.loc[mask_misclass, 'est_cement_median_mt'].sum()

# USGS reference: ~110M short tons shipped = ~99.8M metric tonnes consumption
# (production + imports - exports = consumption)
usgs_consumption_mt = 125_300_000  # metric tonnes

print(f"\nUSGS total US cement consumption:    {usgs_consumption_mt/1e6:.1f}M MT")
print(f"\nOur model (consumer facilities only):")
print(f"  Low estimate:    {total_consumer_low/1e6:.1f}M MT")
print(f"  Median estimate: {total_consumer_median/1e6:.1f}M MT")
print(f"  High estimate:   {total_consumer_high/1e6:.1f}M MT")

# Note: Our dataset only covers EPA-registered facilities.
# Missing: contractor direct purchases (~9%), some smaller operations
# The model intentionally uses the MEDIAN per facility (not the mean)
# which will undercount because of right-skew in plant sizes.
# This is expected and appropriate for GIS weighting.

print(f"\nModel/USGS ratio (median): {total_consumer_median/usgs_consumption_mt:.1%}")
print(f"  (Expected <100% - model uses median, missing contractors/direct)")

# =========================================================================
# SEGMENT BREAKDOWN
# =========================================================================
print(f"\n{'=' * 70}")
print("CONSUMPTION BY SEGMENT (median estimates)")
print(f"{'=' * 70}")

for seg in ['READY_MIX', 'CONCRETE_BLOCK_BRICK', 'CONCRETE_PIPE',
            'OTHER_CONCRETE_PRODUCTS', 'CEMENT_MANUFACTURER', 'CEMENT_CONCRETE_GENERAL']:
    mask_seg = df['segment'] == seg
    subtypes = df.loc[mask_seg].groupby('facility_subtype').agg(
        count=('est_cement_median_mt', 'count'),
        total_mt=('est_cement_median_mt', 'sum')
    ).sort_values('total_mt', ascending=False)

    total_seg = subtypes['total_mt'].sum()
    total_cnt = subtypes['count'].sum()
    print(f"\n  {seg} ({total_cnt:,} fac, {total_seg/1e6:.2f}M MT):")
    for st, row in subtypes.iterrows():
        print(f"    {st:<30} {row['count']:>5} fac  {row['total_mt']/1e6:>8.2f}M MT")

# =========================================================================
# PRODUCTION (SUPPLY SIDE) CHECK
# =========================================================================
print(f"\n{'=' * 70}")
print("PRODUCTION SIDE (cement plants)")
print(f"{'=' * 70}")

mask_plant = df['facility_subtype'] == 'CEMENT_PLANT'
gem_matched = df.loc[mask_plant & (df['est_method'] == 'GEM_CAPACITY')]
model_est = df.loc[mask_plant & (df['est_method'] == 'MODEL_ESTIMATE')]

print(f"  Total CEMENT_PLANT facilities: {mask_plant.sum()}")
print(f"  GEM-matched (precise capacity): {len(gem_matched)}")
print(f"  Model-estimated: {len(model_est)}")
print(f"  GEM total production: {gem_matched['est_cement_median_mt'].sum()/1e6:.1f}M MT")
print(f"  Model total production: {model_est['est_cement_median_mt'].sum()/1e6:.1f}M MT")
print(f"  Combined: {df.loc[mask_plant, 'est_cement_median_mt'].sum()/1e6:.1f}M MT")
print(f"  USGS actual production: ~86M MT (2024)")

# =========================================================================
# SAVE TO DATABASE
# =========================================================================
print(f"\n{'=' * 70}")
print("SAVING TO DATABASE")
print(f"{'=' * 70}")

# Add columns to epa_cement_consumers
for col in ['est_cement_low_mt', 'est_cement_median_mt', 'est_cement_high_mt',
            'est_method', 'est_notes']:
    try:
        con.execute(f"ALTER TABLE epa_cement_consumers ADD COLUMN {col} VARCHAR")
    except:
        pass  # column exists

# Update in batches
print("  Updating estimates...")
for idx, row in df.iterrows():
    rid = row['registry_id']
    con.execute(f"""
        UPDATE epa_cement_consumers
        SET est_cement_low_mt = {row['est_cement_low_mt']},
            est_cement_median_mt = {row['est_cement_median_mt']},
            est_cement_high_mt = {row['est_cement_high_mt']},
            est_method = '{row['est_method']}',
            est_notes = '{str(row['est_notes']).replace("'", "''")}'
        WHERE registry_id = '{rid}'
    """)

# Verify
cnt = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE est_cement_median_mt IS NOT NULL
""").fetchone()[0]
print(f"  Updated: {cnt:,} facilities")

# =========================================================================
# CREATE GIS-READY EXPORT TABLE
# =========================================================================
print(f"\n{'=' * 70}")
print("CREATING GIS-READY EXPORT")
print(f"{'=' * 70}")

con.execute("DROP TABLE IF EXISTS gis_cement_facilities")
con.execute("""
    CREATE TABLE gis_cement_facilities AS
    SELECT
        registry_id,
        fac_name,
        fac_street,
        fac_city,
        fac_state,
        fac_zip,
        fac_county,
        latitude,
        longitude,
        segment,
        facility_subtype,
        corporate_parent,
        parent_type,
        CAST(est_cement_low_mt AS INTEGER) as est_cement_low_mt,
        CAST(est_cement_median_mt AS INTEGER) as est_cement_median_mt,
        CAST(est_cement_high_mt AS INTEGER) as est_cement_high_mt,
        est_method,
        est_notes,
        -- GIS weighting fields
        CASE
            WHEN CAST(est_cement_median_mt AS INTEGER) >= 500000 THEN 'MEGA'
            WHEN CAST(est_cement_median_mt AS INTEGER) >= 100000 THEN 'LARGE'
            WHEN CAST(est_cement_median_mt AS INTEGER) >= 10000 THEN 'MEDIUM'
            WHEN CAST(est_cement_median_mt AS INTEGER) >= 1000 THEN 'SMALL'
            WHEN CAST(est_cement_median_mt AS INTEGER) > 0 THEN 'MICRO'
            ELSE 'ZERO'
        END as size_class,
        -- Log-scale for proportional symbol mapping
        CASE
            WHEN CAST(est_cement_median_mt AS INTEGER) > 0
            THEN ROUND(LN(CAST(est_cement_median_mt AS DOUBLE)), 2)
            ELSE 0
        END as log_volume,
        -- Normalized weight (0-100 scale for heatmaps)
        CASE
            WHEN CAST(est_cement_median_mt AS INTEGER) > 0
            THEN ROUND(100.0 * LN(CAST(est_cement_median_mt AS DOUBLE)) / LN(2100000.0), 1)
            ELSE 0
        END as weight_normalized
    FROM epa_cement_consumers
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
""")

gis_cnt = con.execute("SELECT COUNT(*) FROM gis_cement_facilities").fetchone()[0]
print(f"  GIS table created: {gis_cnt:,} facilities with coordinates")

# Size class distribution
print("\n  Size class distribution:")
r = con.execute("""
    SELECT size_class, COUNT(*) c,
           ROUND(SUM(est_cement_median_mt)/1e6, 1) as total_mt_m
    FROM gis_cement_facilities
    GROUP BY size_class
    ORDER BY CASE size_class
        WHEN 'MEGA' THEN 1 WHEN 'LARGE' THEN 2 WHEN 'MEDIUM' THEN 3
        WHEN 'SMALL' THEN 4 WHEN 'MICRO' THEN 5 ELSE 6 END
""").fetchall()
for sc, c, t in r:
    print(f"    {sc:<10} {c:>6} facilities  {t:>8.1f}M MT")

# Export to CSV for GIS tools
con.execute("""
    COPY gis_cement_facilities TO 'atlas/data/processed/gis_cement_facilities.csv'
    (HEADER, DELIMITER ',')
""")
print(f"\n  CSV exported: atlas/data/processed/gis_cement_facilities.csv")

# Also export GeoJSON for direct mapping
con.execute("""
    COPY (
        SELECT *,
            '{{\"type\":\"Feature\",\"geometry\":{{\"type\":\"Point\",\"coordinates\":[' ||
            CAST(longitude AS VARCHAR) || ',' || CAST(latitude AS VARCHAR) ||
            ']}},\"properties\":{{' ||
            '\"name\":\"' || REPLACE(fac_name, '"', '\\"') || '\",' ||
            '\"city\":\"' || COALESCE(fac_city,'') || '\",' ||
            '\"state\":\"' || COALESCE(fac_state,'') || '\",' ||
            '\"segment\":\"' || COALESCE(segment,'') || '\",' ||
            '\"subtype\":\"' || COALESCE(facility_subtype,'') || '\",' ||
            '\"parent\":\"' || COALESCE(REPLACE(corporate_parent, '"', '\\"'),'') || '\",' ||
            '\"est_mt\":' || CAST(est_cement_median_mt AS VARCHAR) || ',' ||
            '\"size_class\":\"' || size_class || '\"' ||
            '}}}}'
            as geojson_feature
        FROM gis_cement_facilities
        LIMIT 0
    ) TO 'atlas/data/processed/gis_features_header.csv' (HEADER)
""")

# Top 20 facilities by estimated consumption
print(f"\n{'=' * 70}")
print("TOP 25 FACILITIES BY ESTIMATED CEMENT VOLUME")
print(f"{'=' * 70}")
r2 = con.execute("""
    SELECT fac_name, fac_state, segment, facility_subtype,
           est_cement_median_mt, est_method, corporate_parent
    FROM gis_cement_facilities
    ORDER BY est_cement_median_mt DESC
    LIMIT 25
""").fetchall()
print(f"{'Facility':<45} {'ST':<4} {'Type':<18} {'MT/yr':>10} {'Method':<15} {'Parent'}")
print("-" * 120)
for name, st, seg, sub, mt, meth, parent in r2:
    print(f"  {str(name)[:43]:<43} {st:<4} {sub[:16]:<18} {mt:>10,} {meth:<15} {(parent or '')[:20]}")

con.close()
print(f"\n{'=' * 70}")
print("DONE. Estimates saved to epa_cement_consumers + gis_cement_facilities table")
print("=" * 70)
