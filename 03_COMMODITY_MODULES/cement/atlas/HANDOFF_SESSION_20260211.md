# ATLAS Session Handoff - 2026-02-11
## Cement Market Intelligence Platform - Foundation Build

---

## SESSION SCOPE

Built the analytical foundation for US cement market facility intelligence. This session focused on cleaning, classifying, resolving ownership, estimating consumption, and cross-referencing rail data for 15,782 EPA-registered cement/concrete facilities. All work is modular and designed to feed into a consolidated toolset.

---

## WHAT WAS BUILT

### 1. Master Database
**Location:** `atlas/data/atlas.duckdb`

**Tables created/populated this session:**

| Table | Rows | Purpose |
|---|---|---|
| `epa_cement_consumers` | 15,782 | Core facility table - cleaned, classified, ownership-resolved, consumption-estimated |
| `scrs_stations` | 40,180 | Full STB Station Cross Reference System (all industries, all states) |
| `scrs_epa_crosswalk` | 1,238 | Mapping table linking cement-relevant SCRS rail records to EPA facilities |
| `gis_cement_facilities` | 13,960 | GIS-ready export with lat/lon, consumption estimates, size classes, log weights |
| `gem_plants` | 100 | Global Energy Monitor verified cement plants (US only) |
| `trade_imports` | 3,420 | Cement import records |
| `us_cement_facilities` | 1,153 | Rail-served cement facilities with CIF codes |
| `usgs_monthly_shipments` | 37 | USGS cement shipment data by state/region |

### 2. Key Columns Added to `epa_cement_consumers`

| Column | Type | Description |
|---|---|---|
| `corporate_parent` | VARCHAR | Resolved parent company (41.4% coverage via 2-pass entity resolution) |
| `parent_type` | VARCHAR | INTEGRATED_PRODUCER, MAJOR_READYMIX, REGIONAL_READYMIX, PRECAST_NATIONAL, BLOCK_MASONRY, PIPE_PRODUCTS |
| `facility_subtype` | VARCHAR | CEMENT_PLANT, CEMENT_TERMINAL, MISCLASSIFIED_READYMIX, NON_CEMENT_MISCLASS, SPECIALTY_CEMENT, OILFIELD_CEMENT, GRINDING_SCM, etc. |
| `est_cement_low_mt` | INTEGER | Low consumption estimate (metric tons/yr) |
| `est_cement_median_mt` | INTEGER | Median consumption estimate - USE THIS for weighting |
| `est_cement_high_mt` | INTEGER | High consumption estimate |
| `est_method` | VARCHAR | GEM_CAPACITY (154 plants) or MODEL_ESTIMATE (remainder) |
| `est_notes` | VARCHAR | Calculation basis for each facility |

### 3. Scripts Created

| Script | Purpose |
|---|---|
| `atlas/scripts/analysis/entity_resolution.py` | Pass 1: 162 keyword patterns mapping facilities to 60+ corporate groups |
| `atlas/scripts/analysis/entity_resolution_pass2.py` | Pass 2: Decoded truncated EPA parent_company values + regional firms |
| `atlas/scripts/analysis/geographic_market_analysis.py` | State demand, county concentration, port hinterlands, supply gaps |
| `atlas/scripts/analysis/cross_reference_analysis.py` | Import consignees, rail sites, GEM plants cross-matching |
| `atlas/scripts/analysis/classify_storage_terminals.py` | Pass 1: Terminal/silo/storage classification + GEM plant matching |
| `atlas/scripts/analysis/classify_storage_terminals_pass2.py` | Pass 2: Refined 468 CEMENT_MANUFACTURER into plants/terminals/misclassified |
| `atlas/scripts/analysis/scrs_epa_matching.py` | SCRS-to-EPA crosswalk builder (4-strategy matching: CIF, name, address, company) |
| `atlas/scripts/analysis/estimate_consumption.py` | Consumption estimation model with GIS export |

### 4. Data Exports
- `atlas/data/processed/gis_cement_facilities.csv` - 13,960 facilities, GIS-ready
- `atlas/data/raw/scrs_harmonized.csv` - Copy of SCRS source data (40,180 records)

---

## DATA ARCHITECTURE NOTES FOR TOOLSET INTEGRATION

### Source Data Flow
```
EPA FRS (623 MB, read-only)          -->  epa_cement_consumers (15,782)
  G:/My Drive/LLM/task_epa_frs/          Filtered to NAICS 3273xx only
  data/frs.duckdb                         Dropped 3241xx petroleum/asphalt

SCRS Rail Directory (40,180)         -->  scrs_stations + scrs_epa_crosswalk
  G:/My Drive/LLM/project_rail/           748 matched to EPA (60.4%)
  00_raw_sources/SCRS/                    490 unmatched (mostly aggregates)

GEM Cement Tracker (100 plants)      -->  gem_plants
                                          98 with capacity data
                                          154 EPA facilities geo-matched
```

### Cross-Project Data Sources (NOT YET INTEGRATED)
```
project_rail/rail_analytics/
  rail_analytics.duckdb (313 MB)      STB Waybill: ~76M tons cement by BEA region
                                      STCC 32411, exp_tons, exp_carloads, exp_freight_rev
                                      Years: 2018-2023
                                      Pre-aggregated: cement_origins.csv, cement_destinations.csv,
                                                      cement_od_flows.csv

project_manifest/_archive/
  maritime_cargo.duckdb               Panjiva imports: ~63M tons by port/shipper
  industry_tracker/01_CEMENT/         cement_by_loading_port.csv (130 rows)
                                      cement_by_shipper.csv (245 rows)
                                      cement_trade_lanes.csv (232 rows)
                                      cement_facilities_geo_v1.0.0.csv (with lat/lon)

project_barge/
  Link_Tonnages CSV                   CRMAT aggregated only - cement NOT broken out
                                      Facility infrastructure data, no volumes
```

### Key Relationships for Toolset
```
epa_cement_consumers.registry_id  <-->  scrs_epa_crosswalk.epa_registry_id
scrs_epa_crosswalk.scrs_cif       <-->  scrs_stations."CIF #"
us_cement_facilities.rail_cif     <-->  scrs_stations."CIF #"
gem_plants (lat/lon proximity)    <-->  epa_cement_consumers (lat/lon)
trade_imports (consignee/port)    <-->  epa_cement_consumers (name/city)
```

---

## CONSUMPTION MODEL SPECIFICATION

### Calibration Result
- Model median total: 119.6M MT vs USGS actual: 125.3M MT = **95.4%**
- Gap = contractor direct purchases + model uses medians not means

### Rate Table (metric tons Portland cement per year)

| Segment | Facility Subtype | Low | Median | High | Source |
|---|---|---|---|---|---|
| READY_MIX | OPERATING_FACILITY | 3,000 | 8,200 | 18,000 | NRMCA 45K cy/yr median, 540 lbs/cy |
| CONCRETE_BLOCK_BRICK | OPERATING_FACILITY | 5,000 | 10,000 | 25,000 | 10M blocks/yr, 4.2 lbs/block, 45% SCM |
| CONCRETE_PIPE | OPERATING_FACILITY | 2,000 | 4,500 | 8,000 | 25K cy/yr, 750 lbs/cy high-strength |
| OTHER_CONCRETE_PRODUCTS | OPERATING_FACILITY | 1,000 | 3,000 | 8,000 | Heterogeneous catch-all |
| CEMENT_MANUFACTURER | CEMENT_PLANT | 500,000 | 870,000 | 2,100,000 | USGS 99 plants, 72% utilization |
| CEMENT_MANUFACTURER | CEMENT_TERMINAL | 50,000 | 150,000 | 400,000 | 7K MT storage x 22 turns (throughput) |
| CEMENT_MANUFACTURER | GRINDING_SCM | 50,000 | 200,000 | 500,000 | Grinding station throughput |

154 cement plants use GEM-specific capacity (not model median).

Full rate table with all segment/subtype combinations in `estimate_consumption.py`.

Reference document: `atlas/data/reference/research/cement_consumption_by_facility_type.md`

---

## ENTITY RESOLUTION STATE

| Metric | Value |
|---|---|
| Total facilities | 15,782 |
| Resolved to corporate parent | 6,539 (41.4%) |
| Unresolved | 9,243 (58.6%) |
| CEMENT_MANUFACTURER resolved | 99.6% |
| READY_MIX resolved | ~35% |
| Unresolved = structural | 5,997 single-facility independents |

Key M&A corrections applied:
- Ready Mix USA -> CEMEX (acquired 2007 via Rinker)
- Concrete Supply Co -> Thomas Concrete Group (acquired ~2013)
- Cemstone -> Knife River Corp (acquired 2023)
- CalMat -> Vulcan Materials (acquired)
- Ash Grove -> CRH plc (acquired)
- Lafarge/Holcim -> Holcim Group (merged)
- Lehigh/Essroc -> Heidelberg Materials (rebranded)

---

## KNOWN ISSUES & TECHNICAL NOTES

1. **DuckDB `changes()` doesn't exist** - All update counting uses count-before/count-after pattern
2. **DuckDB subquery correlation** - `EXISTS (SELECT 1 FROM other_table t WHERE t.col = main.col)` fails with table alias scoping issues; use Python-side joins or materialized conditions instead
3. **GEM capacity field** - Contains `>0` string values that break CAST; filter with Python, not SQL
4. **SCRS column names have spaces** - Must use double-quote syntax: `"Customer Name"`, `"CIF #"`
5. **Duplicate EPA facilities** - Some plants appear 2-3x with different registry_ids (different EPA programs); 15,782 is after primary dedup but some remain
6. **File lock on atlas.duckdb** - Only one write connection at a time; parallel scripts must run sequentially
7. **Windows encoding** - All scripts need `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')`

---

## NEXT STEPS FOR TOOLSET BUILD

### Immediate (Module 1: Facility Intelligence)
- [ ] Consolidate entity resolution patterns into a YAML config (currently hardcoded in .py)
- [ ] Build CLI commands: `atlas query --state NC --segment READY_MIX`
- [ ] Add remaining 102 unclassified CEMENT_MANUFACTURER facilities (manual review)
- [ ] GeoJSON export for web mapping (script stub exists, needs completion)

### Near-Term (Module 2: Volume Intelligence)
- [ ] Integrate STB waybill data from project_rail (rail tonnage by BEA region -> facility allocation)
- [ ] Integrate Panjiva import data from project_manifest (port volumes -> terminal matching)
- [ ] Build supply-demand balance by state/region using all three sources
- [ ] Replace model estimates with actual observed volumes where rail/import data exists

### Future (Module 3: Unified Data Lake)
- [ ] Bring project_rail, project_manifest, project_barge into single repository
- [ ] Cross-modal volume reconciliation (rail + import + truck + barge = total)
- [ ] Time-series analysis (waybill 2018-2023 trends)
- [ ] Competitive intelligence layer (market share by geography)

---

## FILE LOCATIONS SUMMARY

```
G:/My Drive/LLM/project_cement_markets/
  atlas/
    data/
      atlas.duckdb                    <-- MASTER DATABASE (all tables)
      raw/
        scrs_harmonized.csv           <-- SCRS source copy (40,180 records)
      processed/
        gis_cement_facilities.csv     <-- GIS EXPORT (13,960 w/ lat/lon + estimates)
      reference/research/
        cement_consumption_by_facility_type.md  <-- Research document
    scripts/analysis/
        entity_resolution.py          <-- Pass 1 ownership mapping
        entity_resolution_pass2.py    <-- Pass 2 ownership mapping
        geographic_market_analysis.py  <-- State/county/port analysis
        cross_reference_analysis.py   <-- Import/rail/GEM cross-ref
        classify_storage_terminals.py  <-- Terminal/silo classification pass 1
        classify_storage_terminals_pass2.py  <-- Classification pass 2
        scrs_epa_matching.py          <-- SCRS-EPA crosswalk builder
        estimate_consumption.py       <-- Consumption model + GIS export

EXTERNAL (read-only sources, do not modify):
  G:/My Drive/LLM/task_epa_frs/data/frs.duckdb          <-- EPA FRS (623 MB)
  G:/My Drive/LLM/project_rail/rail_analytics/data/      <-- STB waybill (313 MB)
  G:/My Drive/LLM/project_rail/00_raw_sources/SCRS/      <-- SCRS originals
  G:/My Drive/LLM/project_manifest/_archive/             <-- Panjiva imports
  G:/My Drive/LLM/project_barge/data/                    <-- Barge/waterway
```

---

*Session: 2026-02-11 | Model: Claude Opus 4.6 | Platform: Windows 11*
