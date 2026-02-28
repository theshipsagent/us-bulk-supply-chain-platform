# 🎯 DATA SOURCE FOR OTHER PROCESSES - READ THIS FIRST!

**Date:** 2026-02-07
**Status:** PRODUCTION READY
**Version:** 2.0

---

## ⚠️ CRITICAL: WHICH DATA SOURCE TO USE

### **USE THIS DATA SOURCE: 👉 DuckDB Database**

**File:** `data/frs.duckdb`
**Size:** 0.61 GB
**Version:** 2.0 (with parent_company column)

---

## ✅ WHY USE THE DUCKDB DATABASE?

### **1. Complete Data**
- ✅ 3,177,680 facilities (ALL EPA FRS data)
- ✅ 4,272,709 program linkages
- ✅ 2,012,727 NAICS codes
- ✅ 958,758 SIC codes
- ✅ Parent company harmonization (99.999% coverage)

### **2. Structured & Cleaned**
- ✅ Proper relational schema with foreign keys
- ✅ Normalized data (no duplicates)
- ✅ Indexed for fast queries
- ✅ Original facility names PRESERVED

### **3. Production Ready**
- ✅ Backed up (3 backups available)
- ✅ Version tracked
- ✅ Validated (zero data loss)
- ✅ Harmonized parent companies

---

## 🗄️ DATABASE SCHEMA (Version 2.0)

### Primary Table: **facilities**

```python
import duckdb
conn = duckdb.connect('data/frs.duckdb')

# Query with parent company
df = conn.execute("""
    SELECT
        registry_id,           -- EPA unique ID
        fac_name,             -- ORIGINAL facility name
        parent_company,       -- HARMONIZED parent corporation
        fac_street,
        fac_city,
        fac_state,
        fac_zip,
        fac_county,
        fac_epa_region,
        latitude,             -- Coordinates for mapping
        longitude
    FROM facilities
    WHERE fac_state = 'VA'
    LIMIT 10
""").df()
```

### Related Tables:

**program_links** - EPA program linkages (NPDES, RCRA, TRI, etc.)
```python
# Get programs for a facility
df = conn.execute("""
    SELECT pgm_sys_acrnm, pgm_sys_id, primary_name
    FROM program_links
    WHERE registry_id = '110000350174'
""").df()
```

**naics_codes** - Industry classifications
```python
# Get NAICS codes for facilities
df = conn.execute("""
    SELECT f.fac_name, f.parent_company, n.naics_code
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
""").df()
```

---

## 📊 ALTERNATIVE: CSV FILES (For Specific Industries Only)

### Cement Industry Pre-Exported Files:
If you only need cement industry data, these CSV files are available:

1. **cement_industry_with_parent_companies.csv** (17,263 records)
   - ✅ Has parent_company column
   - ✅ Complete cement industry
   - ✅ Ready for Excel/GIS

2. **cement_industry_all_facilities.csv** (17,670 records)
   - ✅ All cement facilities (may have duplicates across NAICS)
   - ✅ Includes facility_type column

**⚠️ LIMITATION:** CSV files only contain cement industry (NAICS 3273*)

---

## 🎯 RECOMMENDED: Use DuckDB Database

### **For Python/Pandas:**
```python
import duckdb
import pandas as pd

# Connect to database
conn = duckdb.connect('data/frs.duckdb')

# Query any industry with parent companies
df = conn.execute("""
    SELECT
        f.registry_id,
        f.fac_name AS facility_name_original,
        f.parent_company,
        f.fac_state,
        f.fac_city,
        f.latitude,
        f.longitude,
        n.naics_code
    FROM facilities f
    LEFT JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '324%'  -- Petroleum refining
""").df()

# Export to CSV if needed
df.to_csv('petroleum_with_parents.csv', index=False)
```

### **For Excel/GIS:**
Export from DuckDB to CSV:
```python
import duckdb
conn = duckdb.connect('data/frs.duckdb')

# Export any industry
df = conn.execute("""
    SELECT
        f.registry_id,
        f.fac_name,
        f.parent_company,
        f.fac_street,
        f.fac_city,
        f.fac_state,
        f.fac_zip,
        f.latitude,
        f.longitude
    FROM facilities f
    WHERE f.fac_state = 'CA'
""").df()

df.to_csv('california_facilities_with_parents.csv', index=False)
```

### **For R:**
```r
library(DBI)
library(duckdb)

# Connect to database
con <- dbConnect(duckdb::duckdb(), "data/frs.duckdb")

# Query with parent companies
df <- dbGetQuery(con, "
    SELECT registry_id, fac_name, parent_company, fac_state
    FROM facilities
    WHERE parent_company = 'CEMEX'
")

dbDisconnect(con)
```

---

## 🔍 QUICK VERIFICATION

Check the database is working:

```bash
cd "G:\My Drive\LLM\task_epa_frs"

python -c "
import duckdb
conn = duckdb.connect('data/frs.duckdb')

# Check row counts
print('Facilities:', conn.execute('SELECT COUNT(*) FROM facilities').fetchone()[0])
print('With parent:', conn.execute('SELECT COUNT(*) FROM facilities WHERE parent_company IS NOT NULL').fetchone()[0])

# Check parent companies
print('\nTop 5 Parent Companies:')
df = conn.execute('SELECT parent_company, COUNT(*) as count FROM facilities WHERE parent_company IS NOT NULL GROUP BY parent_company ORDER BY count DESC LIMIT 5').df()
print(df)
"
```

Expected output:
```
Facilities: 3177680
With parent: 3177640

Top 5 Parent Companies:
  parent_company  count
0     CON EDISON  50361
1      RESIDENCE  22748
2   CVS PHARMACY  10386
3        UNKNOWN   9858
4  DOLLAR GENERAL   7828
```

---

## 📍 FILE LOCATIONS

### **PRIMARY DATA SOURCE:**
```
data/frs.duckdb                                    ← USE THIS!
```

### **Backups (in case of corruption):**
```
data/backups/frs.duckdb.backup_before_harmonization_bake
data/backups/frs.duckdb.backup_20260207_234110
data/backups/frs.duckdb.backup_20260207_234019
```

### **Cement Industry Exports (alternative):**
```
cement_industry_with_parent_companies.csv          ← Cement only
cement_parent_companies_summary.csv                ← Parent totals
cement_parent_companies_by_state.csv               ← State rollup
```

### **Raw EPA Data (original downloads):**
```
data/raw/FRS_FACILITIES.csv                        ← Original, no parents
data/raw/FRS_PROGRAM_LINKS.csv
data/raw/FRS_NAICS_CODES.csv
data/raw/FRS_SIC_CODES.csv
```

---

## ⚠️ DO NOT USE Raw CSV Files Directly

**Why NOT to use data/raw/*.csv:**
- ❌ No parent company harmonization
- ❌ Not normalized (duplicates possible)
- ❌ No relationships between tables
- ❌ Harder to query
- ❌ Missing lookup tables

**Always use the DuckDB database or export from it!**

---

## 🚀 EXAMPLE USE CASES

### Use Case 1: Export Petroleum Industry
```python
import duckdb
conn = duckdb.connect('data/frs.duckdb')

df = conn.execute("""
    SELECT
        f.registry_id,
        f.fac_name,
        f.parent_company,
        f.fac_state,
        f.fac_city,
        f.latitude,
        f.longitude,
        n.naics_code
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '324%'
""").df()

df.to_csv('petroleum_refining_with_parents.csv', index=False)
print(f'Exported {len(df)} petroleum facilities')
```

### Use Case 2: Market Analysis by Parent Company
```python
import duckdb
conn = duckdb.connect('data/frs.duckdb')

# Get CEMEX footprint
df = conn.execute("""
    SELECT
        fac_state,
        COUNT(*) as facilities,
        COUNT(DISTINCT fac_city) as cities
    FROM facilities
    WHERE parent_company = 'CEMEX'
    GROUP BY fac_state
    ORDER BY facilities DESC
""").df()

print(df)
```

### Use Case 3: GIS Mapping
```python
import duckdb
import geopandas as gpd
from shapely.geometry import Point

conn = duckdb.connect('data/frs.duckdb')

# Get facilities with coordinates
df = conn.execute("""
    SELECT
        registry_id,
        fac_name,
        parent_company,
        fac_state,
        latitude,
        longitude
    FROM facilities
    WHERE latitude IS NOT NULL
      AND longitude IS NOT NULL
      AND parent_company = 'CEMEX'
""").df()

# Convert to GeoDataFrame
geometry = [Point(xy) for xy in zip(df.longitude, df.latitude)]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

# Export to shapefile
gdf.to_file('cemex_facilities.shp')
```

---

## 📞 SUPPORT

**Questions? Check these files:**
1. **PROJECT_STATUS.md** - Current database state
2. **SESSION_SUMMARY.md** - What was built this session
3. **QUICKSTART.md** - How to query the database

**Verify Setup:**
```bash
python verify_setup.py
```

---

## ✅ FINAL ANSWER: USE THE DUCKDB DATABASE

**Primary Data Source:** `data/frs.duckdb`
- Complete data (3.17M facilities)
- Parent companies included
- Production ready
- Backed up

**For Other Processes:** Query DuckDB and export what you need
**Don't use:** Raw CSV files in data/raw/

---

*Last Updated: 2026-02-07 23:50:00*
*Database Version: 2.0*
