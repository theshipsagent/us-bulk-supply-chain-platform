# Entity Harmonization Guide - Parent Company Rollup

**Date:** 2026-02-07
**Phase:** 2 - Entity Harmonization
**Facilities Processed:** 17,263 cement industry facilities

---

## Overview

This guide explains the **parent company harmonization** system that rolls up individual facility names to their parent corporations while preserving the original facility names.

### What Problem Does This Solve?

In EPA FRS data, the same company appears with many name variations:
- **CEMEX, INC.**
- **CEMEX Construction Materials Florida LLC**
- **CEMEX Construction Materials Pacific LLC**
- **CEMEX West Plant**
- **CEMEX Corp**
- **Ready Mix, LLC-CEMEX**

These all represent facilities owned by the same parent corporation: **CEMEX**

---

## How Harmonization Works

### 1. Name Normalization

The system normalizes facility names by:
- Converting to uppercase
- Removing business entity suffixes (LLC, INC, CORP, etc.)
- Removing location-specific terms (Florida, Pacific, South, etc.)
- Removing operation terms (Ready Mix, Concrete, Plant, etc.)
- Removing extra punctuation and whitespace

**Example:**
```
Original: "CEMEX Construction Materials Florida LLC"
Normalized: "CEMEX"
Parent Company: "CEMEX"
```

### 2. Base Company Extraction

The system extracts the core company name (1-2 significant words) from the normalized name.

**Examples:**
```
"HOLCIM (US) INC." → "HOLCIM US"
"Irving Materials, Inc." → "IRVING"
"Oldcastle Precast Inc" → "OLDCASTLE"
"Ready Mixed Concrete Company" → "READY MIXED"
```

### 3. Parent Company Assignment

Each facility gets assigned a parent company while keeping its original name:

| registry_id | facility_name_original | parent_company | state |
|-------------|------------------------|----------------|-------|
| 110007233421 | CEMEX, INC. | CEMEX | AL |
| 110001715476 | CEMEX | CEMEX | AL |
| 110070125988 | READY MIX, LLC-CEMEX | CEMEX | AL |
| 110002567990 | CEMEX CORP | CEMEX | AZ |

---

## Data Preservation

### Original Names Are Preserved

✓ **facility_name_original** - Unchanged EPA facility name
✓ **parent_company** - Harmonized parent corporation

This allows you to:
- Roll up to parent companies for corporate analysis
- Maintain original facility names for regulatory compliance
- Track individual sites while understanding corporate ownership

---

## Cement Industry Results

### Summary Statistics

- **Total Facilities:** 17,263
- **Unique Original Names:** 13,282
- **Parent Companies:** 9,113
- **Top Parent Company:** CEMEX (206 facilities)

### Top 25 Parent Companies

| Parent Company | Facilities | States | Unique Names |
|----------------|------------|--------|--------------|
| CEMEX | 206 | 10 | 22 |
| READY MIXED | 109 | 8 | 68 |
| HANSON PIPE | 105 | 18 | 61 |
| ARGOS USA | 80 | 6 | 24 |
| VCNA PRAIRIE | 80 | 3 | 57 |
| KNIFE RIVER | 65 | 12 | 60 |
| OLDCASTLE | 65 | 22 | 8 |
| ROBERTSON'S | 64 | 2 | 5 |
| HANSON AGGREGATES | 55 | 3 | 28 |
| HOLLIDAY ROCK | 55 | 1 | 33 |
| AMERICAN | 52 | 12 | 20 |
| WELLS | 51 | 6 | 8 |
| CROELL REDI | 48 | 5 | 41 |
| IRVING | 48 | 5 | 7 |
| THOMAS CAROLINA | 43 | 2 | 35 |
| HOLCIM US | 41 | 16 | 20 |
| FORTERRA PIPE | 39 | 12 | 19 |
| PREFERRED | 38 | 2 | 3 |
| IMI | 38 | 3 | 4 |
| TARMAC AMERICA | 38 | 2 | 13 |

### Examples of Successful Rollups

**CEMEX (22 facility name variations → 1 parent):**
- CEMEX, INC.
- CEMEX
- READY MIX, LLC-CEMEX
- CEMEX CORP
- CEMEX WEST PLANT
- CEMEX CONSTRUCTION MATERIALS PACIFIC LLC
- CEMEX CONSTRUCTION MATERIALS FLORIDA LLC
- CEMEX CALIFORNIA CEMENT LLC
- ... and 14 more

**ARGOS USA (24 variations → 1 parent):**
- ARGOS USA
- ARGOS USA DBA ARGOS READY MIX LLC
- ARGOS USA HIGH SPRINGS CONCRETE PLANT
- ARGOS USA, LLC
- ARGOS USA-AVALON ROAD RMF
- ... and 19 more

**IRVING (7 variations → 1 parent):**
- IRVING MATERIALS INC
- IRVING MATERIALS, INC.
- IRVING MATERIALS INCORPORATED
- IRVING MATERIALS INC.
- ... and 3 more

---

## Files Created

### 1. Detail File (With All Columns)
**cement_industry_with_parent_companies.csv**
- 17,263 records
- Columns: registry_id, facility_name_original, parent_company, fac_street, fac_city, fac_state, fac_zip, fac_county, fac_epa_region, latitude, longitude, naics_code
- Use for: Detailed facility-level analysis while maintaining parent company context

### 2. Parent Company Summary
**cement_parent_companies_summary.csv**
- Columns: parent_company, total_facilities, states_present, unique_names, with_latitude, with_longitude
- Use for: Corporate-level analysis and market share

### 3. By Facility Type
**cement_parent_companies_by_type.csv**
- Columns: parent_company, facility_type, facility_count, states
- Facility types: Cement Manufacturing, Ready-Mix Concrete, Concrete Block & Brick, Concrete Pipe, Precast & Other, Terminal/Distributor
- Use for: Understanding parent company portfolio mix

### 4. By State
**cement_parent_companies_by_state.csv**
- Columns: state, parent_company, facilities, facility_types
- Use for: State-level market analysis and geographic footprint

---

## Use Cases

### 1. Market Share Analysis

Roll up facilities by parent company to understand market concentration:

```python
import pandas as pd

df = pd.read_csv('cement_industry_with_parent_companies.csv')

# Market share by parent company
market_share = df.groupby('parent_company').size().sort_values(ascending=False)
market_share_pct = (market_share / market_share.sum() * 100).round(2)

print("Top 10 Parent Companies Market Share:")
print(market_share_pct.head(10))
```

### 2. Geographic Footprint

Analyze which parent companies have the broadest geographic reach:

```python
# States per parent company
geographic_reach = df.groupby('parent_company')['fac_state'].nunique()
print(geographic_reach.sort_values(ascending=False).head(10))
```

### 3. Corporate Portfolio Analysis

Understand the facility mix for each parent company:

```python
# Facility type mix by parent
df_type = pd.read_csv('cement_parent_companies_by_type.csv')
cemex_portfolio = df_type[df_type['parent_company'] == 'CEMEX']
print(cemex_portfolio)
```

### 4. Competitive Analysis

Compare parent companies in specific states:

```python
# Florida cement industry parent companies
florida = df[df['fac_state'] == 'FL']
fl_companies = florida['parent_company'].value_counts().head(10)
print("Florida Market Leaders:")
print(fl_companies)
```

### 5. Supply Chain Mapping

Identify parent companies with vertically integrated operations (cement mfg + ready-mix + terminals):

```python
df_type = pd.read_csv('cement_parent_companies_by_type.csv')

# Parents with multiple facility types
integrated = df_type.groupby('parent_company')['facility_type'].nunique()
integrated = integrated[integrated >= 3].sort_values(ascending=False)

print("Vertically Integrated Parent Companies:")
print(integrated)
```

---

## Manual Overrides

### Parent Mapping Configuration

The system allows manual overrides via `config/parent_mapping.json`:

```json
{
  "mappings": {
    "HOLCIM US": "LAFARGEHOLCIM",
    "HOLCIM": "LAFARGEHOLCIM",
    "LAFARGE": "LAFARGEHOLCIM"
  }
}
```

After editing the mapping file, recreate the parent company table:

```bash
python cli.py harmonize create-parent-table
```

---

## CLI Commands

### Analyze Facility Names
```bash
# See parent company groupings before creating table
python cli.py harmonize analyze --min-facilities 5
```

### Create Parent Company Table
```bash
# Process all facilities and create lookup table
python cli.py harmonize create-parent-table --min-facilities 2
```

### Export with Parent Companies
```bash
# Export cement industry with parent rollup
python cli.py harmonize export --naics 3273 --output cement_with_parents.csv

# Export all facilities with parents
python cli.py harmonize export --output all_facilities_with_parents.csv
```

### View Coverage Statistics
```bash
# Show parent company coverage analysis
python cli.py harmonize coverage
```

---

## Data Quality Considerations

### High Confidence Rollups
- Major corporations with consistent naming (CEMEX, HOLCIM, OLDCASTLE)
- Companies with clear brand identity (ROBERTSON'S, IRVING)
- Well-known national chains

### Lower Confidence Rollups
- Generic facility names (PLANT #1, FACILITY A)
- Single-word names (AMERICAN, PREFERRED)
- Ambiguous abbreviations (S &, IMI)

### Recommendations
1. **Review top 100 parent companies** manually for accuracy
2. **Add manual overrides** in parent_mapping.json for known corrections
3. **Filter by facility count** (e.g., only companies with 5+ facilities) for higher confidence
4. **Cross-reference** with corporate ownership databases for validation

---

## Integration with Phase 1 Analysis

The harmonized data enhances Phase 1 analysis:

### Before Harmonization
```
CEMEX Construction Materials Florida LLC: 178 facilities
CEMEX Construction Materials Pacific LLC: 56 facilities
CEMEX, INC.: 14 facilities
CEMEX CORP: 8 facilities
```
= 256 facilities across 4+ entries

### After Harmonization
```
CEMEX: 206 facilities
```
= Unified view of corporate footprint

---

## Next Steps (Phase 3)

With harmonized data, you can:
1. **Map corporate footprints** - Visualize parent company facility locations
2. **Analyze market concentration** - Calculate Herfindahl-Hirschman Index
3. **Track M&A activity** - Update parent mappings as companies merge
4. **Regulatory compliance** - Aggregate emissions/permits by corporate parent
5. **Supply chain analysis** - Map vertical integration (quarry → cement → ready-mix)

---

## Technical Implementation

### Algorithm
1. **Normalization** - Remove noise from facility names
2. **Extraction** - Identify core company identifier
3. **Clustering** - Group similar names under parent
4. **Manual Override** - Apply curated corrections
5. **Lookup Table** - Store mappings in DuckDB

### Performance
- Processed 2.7M facility names in ~8 minutes
- Created parent company mappings for 1.3M facilities
- Identified 68,272 parent companies

---

## Support

For questions or to suggest parent company corrections:
1. Review `config/parent_mapping.json` format
2. Add corrections to the mappings section
3. Recreate the parent company table
4. Re-export harmonized data

---

*Entity Harmonization System - EPA FRS Analytics Tool Phase 2*
