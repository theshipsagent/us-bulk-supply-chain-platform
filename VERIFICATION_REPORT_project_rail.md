# VERIFICATION REPORT: project_rail → Master Reporting Platform
# Migration Status Assessment

**Report Date:** February 23, 2026
**Original Location:** `G:\My Drive\LLM\project_rail`
**Target Locations:**
- `G:\My Drive\LLM\project_master_reporting\01_DATA_SOURCES\federal_rail\`
- `G:\My Drive\LLM\project_master_reporting\02_TOOLSETS\rail_cost_model\`
**Assessor:** Claude Code (Sonnet 4.5)
**CLAUDE.md Reference:** Section "Phase 0: Physical Reorganization" — Rail Infrastructure Analysis

---

## EXECUTIVE SUMMARY

**Migration Status:** ⚠️ **21.4% COMPLETE** (by size) / **17.3% COMPLETE** (by file count) — SUBSTANTIAL CONTENT UNMIGRATED

**Original Project Size:**
- **Files:** 4,095 files
- **Size:** 18 GB (confirmed)
- **Last Modified:** February 23, 2026 (ACTIVE PROJECT)

**Migrated Content:**
- **Files:** 707 files (17.3% of original file count)
- **Size:** 3.86 GB (21.4% of original size)
- **Locations:** Split between federal_rail data sources (555 files, 160 MB) and rail_cost_model toolset (152 files, 3.7 GB)

**Missing Content:**
- **Files:** 3,388 files (82.7% unmigrated)
- **Size:** 14.14 GB (78.6% unmigrated)
- **Critical Components:** Railroad knowledge bank (166 files), STB rate database (748 files, 113 MB), SESCO proprietary rail analysis (1,907 files), State Customs Records (541 files), geospatial layers (90 files), New Orleans rail gateway study (34 files)

**Key Finding:** This is an **active research project** modified TODAY (Feb 23, 2026) with substantial recent work including a comprehensive railroad knowledge bank covering all 6 Class I carriers plus 71 short line operators (164 files created in latest session). The project contains multiple distinct workstreams that should be evaluated individually for migration priority.

---

## PROJECT OVERVIEW

### Purpose and Scope

Project_rail is a **comprehensive rail freight cost modeling and intelligence platform** that integrates:

1. **Rail Cost Modeling:** NetworkX-based graph analysis using NTAD rail network topology with STB URCS (Uniform Rail Costing System) variable cost calculations
2. **Railroad Intelligence:** Class I carrier + short line operator knowledge banks with commodity specializations, facility locations, interchange points, and route corridors
3. **Rate Analysis:** STB contract database scraping and parsing (10,340 Union Pacific contracts documented)
4. **Industry Data Integration:** State Customs Records System (SCRS) consolidation, EPA FRS facility matching, FAF5 freight flow analysis
5. **Regional Studies:** New Orleans rail gateway analysis, maritime terminal rail connections, captive shipper studies
6. **Commodity Focus:** Construction materials (cement, aggregates, steel, lumber), agriculture (grain, salt), chemicals, energy, forestry, metals

### Strategic Context

From `project_rail/README.md`:

> "This is **data archaeology meets supply chain intelligence**. Government datasets trace lineage to 19th/20th century pen-and-pencil logic, fragmented across multiple agencies (STB, EPA, BTS, USACE, Customs). **Core principle:** Extract 25% signal from 75% noise by understanding the linear intent behind government data collection."

The project serves both:
- **SESCO Cement:** Rail freight cost analysis for cement/SCM distribution (Houston terminal focus)
- **OceanDatum.ai:** Broader bulk commodity supply chain intelligence platform

### Recent Activity (Feb 2026)

**Session Handoff 2026-02-23** documents major recent work:
- **Class I Railroad Knowledge Bank:** 94 files covering BNSF, UP, CSX, NS, CN, CPKC (13,703 lines)
- **Short Line Knowledge Banks:** Watco (43 files, 38 railroads), Genesee & Wyoming (26 files, 25 detailed profiles)
- **Total Knowledge Bank:** 164 files, 19,224 lines, ~13,500 route miles documented
- **Construction Materials Intelligence:** 15+ cement facilities per major carrier, NS aggregates leader (67 quarries), steel transportation networks
- **Commits:** Two commits on Feb 23 (`70aa1a5`, `5025520`)

This represents **active, high-value research** completed through autonomous background agents with ~270 tool calls and ~312,000 tokens processed.

---

## DIRECTORY STRUCTURE COMPARISON

### Original Project Structure (project_rail/)

```
project_rail/ (4,095 files, ~18 GB)
│
├── .git/                                 ← Git repository (active development)
├── .claude/                              ← Claude Code project files
├── .playwright-mcp/                      ← Playwright automation
│
├── 00_raw_sources/                       ← 541 files (SCRS data)
│   └── SCRS/                             ← State Customs Records System (50 CSV files)
│       ├── AL_SCRSSummary_files/         ← Alabama rail-served facilities
│       ├── DE_SCRSSummary_files/         ← Delaware facilities
│       ├── FL_SCRSSummary_files/         ← Florida facilities
│       ├── GA_SCRSSummary_files/         ← Georgia facilities
│       ├── LA_SCRSSummary_files/         ← Louisiana facilities (critical for Lower Miss)
│       ├── MD_SCRSSummary_files/         ← Maryland facilities
│       ├── MS_SCRSSummary_files/         ← Mississippi facilities
│       └── NC_SCRSSummary_files/         ← North Carolina facilities
│
├── 01_processed/                         ← Harmonized SCRS datasets
│   ├── scrs_consolidated_master.csv      ← 39,936 records consolidated
│   ├── scrs_bulk_commodities_only.csv    ← 8,555 bulk commodity facilities
│   └── scrs_parent_company_lookup.csv    ← 42 major parent companies
│
├── 02_STB/                               ← Empty directory
│
├── 01_geospatial/                        ← 90 files (rail network geospatial data)
├── 02_integrated/                        ← Cross-dataset linkages
├── 03_geospatial/                        ← Additional GIS layers
│
├── rail_cost_model/                      ← Rail cost modeling project (original)
│   ├── README.md                         ← NetworkX graph builder documentation
│   ├── requirements.txt                  ← Python dependencies
│   ├── config/config.yaml                ← Data source URLs, parameters
│   ├── data/                             ← Raw/processed/reference data
│   │   ├── raw/ntad/                     ← NARN shapefiles (North American Rail Network)
│   │   ├── raw/stb/                      ← URCS workbooks, waybill data
│   │   ├── raw/faf/                      ← FAF5 freight analysis databases
│   │   └── processed/                    ← Rail network graph (NetworkX pickle)
│   ├── notebooks/                        ← Jupyter analysis notebooks
│   ├── src/                              ← Python modules
│   │   ├── data_ingestion/               ← NTAD, STB, FAF loaders
│   │   ├── network/                      ← Graph construction and routing
│   │   ├── costing/                      ← URCS cost models
│   │   ├── analysis/                     ← Flow and corridor analysis
│   │   └── visualization/                ← Folium map generation
│   ├── outputs/                          ← Generated maps, reports, exports
│   └── tests/                            ← Unit tests
│
├── knowledge_bank/                       ← 166 files (CREATED FEB 23, 2026)
│   ├── BNSF/                             ← 19 files (14 commodities + 5 supporting)
│   │   ├── network_overview.md           ← 32,500 route miles, 28 states
│   │   ├── routes_corridors.md           ← Transcontinental routes, strategic corridors
│   │   ├── facilities.md                 ← Intermodal terminals, classification yards
│   │   ├── interchanges.md               ← Junction points with other carriers
│   │   ├── ports_international.md        ← Pacific ports, Canadian/Mexican connections
│   │   └── commodities/                  ← 14 commodity-specific files
│   │       ├── cement.md                 ← Cement production & distribution
│   │       ├── aggregates.md             ← Construction aggregates
│   │       ├── steel.md                  ← Steel mills & processors
│   │       └── [11 more commodity files]
│   │
│   ├── UP/                               ← 16 files (Union Pacific)
│   ├── CSX/                              ← 16 files (CSX Transportation)
│   ├── NS/                               ← 12 files (Norfolk Southern)
│   │   └── commodities/aggregates.md     ← **67 quarries + 30 distribution yards**
│   ├── CN/                               ← 12 files (Canadian National)
│   ├── CPKC/                             ← 13 files (Canadian Pacific Kansas City)
│   │
│   ├── notes/                            ← 4 cross-carrier files
│   │   ├── interchange_matrix.md         ← Class I junction mapping
│   │   ├── commodity_coverage.md         ← Commodity specialization by carrier
│   │   ├── construction_materials.md     ← Cement/aggregates/steel/lumber analysis
│   │   └── data_gaps.md                  ← Known limitations
│   │
│   ├── shortlines/                       ← Short line railroad knowledge banks
│   │   ├── Watco/                        ← 43 files (38 railroads profiled)
│   │   │   ├── railroads/                ← 38 individual railroad profiles
│   │   │   ├── watco_master.csv          ← Structured data table
│   │   │   ├── watco_summary.html        ← Interactive report
│   │   │   ├── README.md                 ← Documentation
│   │   │   └── RAILROAD_INDEX.md         ← Quick reference
│   │   │
│   │   └── GW/                           ← 26 files (Genesee & Wyoming)
│   │       ├── railroads/                ← 25 detailed profiles (~9,000 route miles)
│   │       ├── gw_master.csv             ← 33 railroads catalogued
│   │       ├── gw_summary.html           ← Interactive report
│   │       ├── README.md                 ← Documentation
│   │       ├── INDEX.md                  ← Navigation by region/commodity
│   │       └── HANDOFF_NOTES.md          ← Project notes
│   │
│   ├── summary_report.html               ← Class I overview (interactive)
│   └── README.md                         ← Knowledge bank documentation
│
├── read_rail/                            ← 1,907 files (reference library)
│   ├── 2023-STB-Waybill-Reference-Guide.pdf  ← 4.1 MB (official STB guide)
│   ├── Papers/                           ← Academic papers, industry reports
│   ├── Rail/                             ← Rail industry documentation
│   ├── RailGIS/                          ← GIS-specific documentation
│   ├── STB/                              ← STB documentation and tools
│   │   └── stb_build_1/                  ← STB data processing pipeline
│   │       ├── Input/                    ← Raw STB data
│   │       ├── Output/                   ← Processed results
│   │       ├── Papers/                   ← Research papers
│   │       └── Scripts/                  ← Processing scripts
│   └── SESCO_RAIL/                       ← SESCO-specific rail analysis
│       ├── waybills/                     ← SESCO waybill records
│       ├── trinity/                      ← Trinity Rail car data
│       ├── invoices/                     ← SESCO rail invoices
│       └── statements/                   ← SESCO carrier statements
│
├── rate_files/                           ← 748 files (STB rate database)
│   ├── stb_contracts.db                  ← 113 MB DuckDB (10,340 UP contracts)
│   ├── scrape_stb_up.py                  ← 26 KB scraper (Union Pacific)
│   ├── parse_acs_pdf.py                  ← 28 KB PDF parser (ACS tariffs)
│   ├── up_urls_discovered.json           ← 66 KB URL catalog
│   ├── downloads/                        ← Downloaded rate files
│   ├── cement/                           ← Cement-specific rate analysis
│   └── .claude/                          ← Claude Code project files
│
├── nola_rail/                            ← 34 files (New Orleans rail gateway)
│   ├── New Orleans Maritime Terminal Rail Connections - Detailed Report.pdf  ← 3.8 MB
│   ├── New Orleans Maritime Terminal Rail Connections - Concise Reference.pdf  ← 796 KB
│   ├── nola-rail-detailed-report.html    ← 54 KB interactive report
│   ├── nola-freight-movement-guide.html  ← 33 KB freight guide
│   └── nola-gateway-flowchart-color.svg  ← 17 KB visual flowchart
│
├── data/                                 ← 55 files (various analysis data)
├── freight_report/                       ← Freight analysis reports
├── rail_analytics/                       ← Analytics dashboards
├── rail_analyticssrc/                    ← Analytics source code (alternate structure)
├── rail_analyticsdata/                   ← Analytics data (alternate structure)
├── rail_analyticsdashboards/             ← Analytics dashboards (alternate structure)
├── logs/                                 ← Processing logs
├── _archive/                             ← Archived materials
├── _user_notes/                          ← User notes and documentation
│
├── CLAUDE.md                             ← Project specification (3.9 KB)
├── README.md                             ← Project overview (9.9 KB, comprehensive)
├── DATA_GOVERNANCE_FRAMEWORK.md          ← 17.3 KB data methodology
├── FAF_MULTIMODAL_FREIGHT_INTEGRATION_PLAN.md  ← 19.5 KB integration plan
├── RAIL_ANALYTICS_PLATFORM_PLAN.md       ← 35 KB platform architecture
├── SESSION_SUMMARY_2026-01-24.md         ← Session handoff notes
├── HANDOFF_SESSION_*.md                  ← 5 handoff files (Feb 13-23)
│
├── class1_rail_knowledge_bank_prompt.md  ← 19.4 KB (knowledge bank specs)
├── class1_rail_scope_summary.html        ← 26.6 KB (scope summary)
├── class1_railroad_corridors.pdf         ← 152 KB (corridor reference)
├── cement_rail.pdf                       ← 734 KB (cement rail analysis)
│
└── Various analysis outputs              ← PNG images, reports, CSVs
    ├── report_*.png                      ← Report visualizations
    ├── *_section.png                     ← Report section graphics
    └── *.html                            ← Interactive reports
```

### Migrated Structure (project_master_reporting/)

```
project_master_reporting/
│
├── 01_DATA_SOURCES/federal_rail/        ← 555 files, 160 MB (PARTIAL)
│   ├── stb_economic_data/                ← 555 files (ALL MIGRATED HERE)
│   │   └── [555 STB economic files]
│   ├── ntad_rail_network/                ← EMPTY (0 files)
│   └── fra_safety_data/                  ← EMPTY (0 files)
│
└── 02_TOOLSETS/rail_cost_model/          ← 152 files, 3.7 GB (PARTIAL)
    ├── README.md                         ← 6.2 KB (migrated)
    ├── METHODOLOGY.md                    ← 8.5 KB (new documentation)
    ├── requirements.txt                  ← Migrated
    ├── config/                           ← Configuration files
    ├── data/                             ← 55 files (subset of original)
    │   ├── raw/                          ← Raw data files
    │   ├── processed/                    ← Processed data
    │   └── reference/                    ← Reference tables
    ├── analytics/                        ← 48 files (analytics modules)
    ├── freight_report/                   ← 11 files (report generation)
    ├── notebooks/                        ← Jupyter notebooks
    ├── outputs/                          ← Generated outputs
    ├── src/                              ← Source code
    └── tests/                            ← Unit tests
```

---

## MIGRATION COMPLETENESS ANALYSIS

### What Was Migrated (707 files, 3.9 GB)

#### 1. STB Economic Data (555 files, 160 MB)
**Location:** `01_DATA_SOURCES/federal_rail/stb_economic_data/`
**Status:** ✅ Complete migration of STB data files
**Contents:** 555 files from original project (likely URCS tables, waybill data, STB reference files)

#### 2. Rail Cost Model Core (152 files, 3.7 GB)
**Location:** `02_TOOLSETS/rail_cost_model/`
**Status:** ✅ Core modeling framework migrated
**Contents:**
- **data/**: 55 files (NTAD, STB, FAF data subsets)
- **analytics/**: 48 files (analysis modules)
- **freight_report/**: 11 files (report generation system)
- **src/**: Source code modules (network, costing, analysis, visualization)
- **config/**: Configuration files
- **notebooks/**: Jupyter notebooks for exploration
- **Documentation:** README.md, METHODOLOGY.md, requirements.txt

**Key Capabilities Migrated:**
- NetworkX graph construction from NTAD rail network
- URCS variable cost calculator
- Route optimization and cost estimation
- Folium interactive map generation
- FAF5 freight flow integration framework

### What Was NOT Migrated (3,388 files, ~14 GB)

#### CRITICAL UNMIGRATED CONTENT

##### 1. Railroad Knowledge Bank (166 files)
**Location:** `project_rail/knowledge_bank/` → **NO TARGET IN CLAUDE.MD**
**Status:** ❌ **NOT MIGRATED** — HIGHEST PRIORITY MISSING CONTENT
**Created:** February 23, 2026 (TODAY)
**Size:** ~5-10 MB (markdown + CSV + HTML)

**Contents:**
- **Class I Carriers:** 94 files covering BNSF, UP, CSX, NS, CN, CPKC
  - Network overviews (route miles, territories, states served)
  - Routes & corridors (transcontinental routes, strategic corridors)
  - Facilities (intermodal terminals, classification yards, transload)
  - Interchanges (junction points between carriers)
  - Ports & international connections
  - Commodity specializations (14 commodities per carrier)
  - Construction materials deep-dive (cement, aggregates, steel, lumber)

- **Short Line Operators:** 70 files covering 71 railroads
  - **Watco Companies:** 43 files, 38 railroads, 4,500+ route miles, 22 states
  - **Genesee & Wyoming:** 26 files, 33 railroads catalogued, ~9,000 route miles

- **Cross-Carrier Analysis:** 4 files
  - Interchange matrix (Class I junction mapping)
  - Commodity coverage comparison
  - Construction materials market intelligence
  - Data gaps documentation

- **Structured Data:**
  - `watco_master.csv` — 38 railroads with Class I connections
  - `gw_master.csv` — 33 railroads with Class I connections
  - `summary_report.html` — Interactive Class I overview
  - `watco_summary.html` — Interactive Watco overview
  - `gw_summary.html` — Interactive G&W overview

**Business Value:**
- **Construction Materials Intelligence:** 15+ cement facilities per carrier, NS aggregates leader (67 quarries)
- **Captive Shipper Analysis:** Single-carrier access identification, routing alternatives
- **Freight Flow Matching:** Cross-reference with FAF, Waybill, SCRS data
- **Routing Optimization:** Class I interchanges, short line connections, port access routes

**Why Not Migrated:**
- CLAUDE.md does not specify a target location for railroad intelligence knowledge banks
- Content created TODAY in active session, not yet integrated into master platform specification

##### 2. STB Rate Database & Scraping Tools (748 files, 113 MB DuckDB)
**Location:** `project_rail/rate_files/` → **NO TARGET IN CLAUDE.MD**
**Status:** ❌ **NOT MIGRATED** — CRITICAL COMMERCIAL INTELLIGENCE

**Contents:**
- **stb_contracts.db** — 113 MB DuckDB database
  - 10,340 Union Pacific contracts scraped and parsed
  - Contract identifiers, parties, commodities, origins, destinations
  - Rate structures, tariff references, effective dates

- **Scraping & Parsing Tools:**
  - `scrape_stb_up.py` (26 KB) — Union Pacific STB scraper
  - `parse_acs_pdf.py` (28 KB) — ACS tariff PDF parser
  - `up_urls_discovered.json` (66 KB) — 10,340 URL catalog
  - `parsing_analysis.md` — Parser methodology

- **Downloaded Rate Files:**
  - `downloads/` — Actual STB filing PDFs
  - `cement/` — Cement-specific rate analysis
  - ACS-UP-4Q-11-29-2021.pdf (444 KB) — Sample ACS tariff
  - Parsed JSON and CSV outputs

**Business Value:**
- **Rate Benchmarking:** Compare published rates to SESCO rail costs
- **Competitive Intelligence:** Identify cement/SCM rate patterns
- **Route Costing Validation:** Validate URCS model outputs against actual tariffs
- **Market Analysis:** UP rate structures for construction materials

**Why Not Migrated:**
- CLAUDE.md does not specify where commercial rate intelligence should reside
- May be considered proprietary/sensitive data requiring special handling
- Could integrate into `02_TOOLSETS/rail_cost_model/data/reference/` or new `02_TOOLSETS/rail_rate_intelligence/`

##### 3. SESCO Rail Analysis (1,907 files in read_rail/)
**Location:** `project_rail/read_rail/SESCO_RAIL/` → **NO TARGET IN CLAUDE.MD**
**Status:** ❌ **NOT MIGRATED** — PROPRIETARY CLIENT DATA

**Contents:**
- **waybills/** — SESCO waybill records (actual shipment data)
- **trinity/** — Trinity Rail car data (SESCO fleet/car hire)
- **invoices/** — SESCO rail invoices (carrier billing records)
  - `duplicates/` — Duplicate invoice detection
- **statements/** — SESCO carrier statements (monthly accounting)

**Business Value:**
- **Actual Cost Validation:** Real SESCO rail costs vs. model predictions
- **Route Analysis:** Actual SESCO origin-destination patterns
- **Cost Benchmarking:** Carrier-specific pricing for cement
- **Invoice Reconciliation:** Duplicate detection, billing verification

**Why Not Migrated:**
- **Proprietary data** — SESCO Cement confidential business records
- Should likely be kept in separate project_rail directory with access controls
- Potentially integrate aggregated/anonymized data into cement module without exposing raw records

##### 4. State Customs Records System (541 files)
**Location:** `project_rail/00_raw_sources/SCRS/` → **NO TARGET IN CLAUDE.MD**
**Status:** ❌ **NOT MIGRATED** — VALUABLE FACILITY DATA

**Contents:**
- 50 CSV files from 8 states (AL, DE, FL, GA, LA, MD, MS, NC)
- Each state has multiple file chunks from web scraping
- HTML files accompanying each CSV (web page source)

**Processed Outputs (also unmigrated):**
- **scrs_consolidated_master.csv** — 39,936 records
- **scrs_bulk_commodities_only.csv** — 8,555 bulk commodity facilities classified
- **scrs_parent_company_lookup.csv** — 42 major parent companies identified
  - Top companies: ADM (239), International Paper (232), Cargill (216), Martin Marietta (87), CEMEX (61), Nucor (59)

**Business Value:**
- **Rail-Served Facilities:** Identifies which facilities have rail access
- **Commodity Classification:** Bulk commodity focus (cement, aggregates, steel, grain, forestry, chemicals)
- **Parent Company Analysis:** Corporate ownership patterns
- **Cross-Dataset Matching:** Can be matched to EPA FRS, rail network proximity analysis

**Why Not Migrated:**
- CLAUDE.md does not specify where SCRS data should reside
- Could integrate into `01_DATA_SOURCES/federal_rail/` or new category
- Processed files should feed into `02_TOOLSETS/facility_registry/` for cross-matching with EPA FRS

##### 5. Rail Network Geospatial Data (90 files)
**Location:** `project_rail/01_geospatial/` → **PARTIAL TARGET EXISTS**
**Status:** ⚠️ **NOT MIGRATED** — GIS layers for rail network
**Target:** `01_DATA_SOURCES/geospatial/rail_layers/` (per CLAUDE.md spec)

**Expected Contents:**
- Rail network shapefiles/GeoJSON
- Rail yard locations
- Intermodal terminal locations
- Classification facility points
- NTAD/NARN processed layers

**Why Not Migrated:**
- Files exist but not moved to target location
- Should be integrated with other geospatial layers in master platform
- Critical for rail_cost_model routing visualization

##### 6. New Orleans Rail Gateway Study (34 files)
**Location:** `project_rail/nola_rail/` → **REGIONAL STUDY TARGET EXISTS**
**Status:** ⚠️ **NOT MIGRATED** — Regional analysis
**Target:** Could integrate into `01_DATA_SOURCES/regional_studies/lower_miss_river/` or separate `houston_galveston/`

**Contents:**
- **Detailed Report:** 3.8 MB PDF — comprehensive NOLA rail gateway analysis
- **Concise Reference:** 796 KB PDF — executive summary
- **Interactive Reports:** HTML versions with search/filtering
- **Freight Guide:** HTML guide to NOLA freight movements
- **Visual Flowchart:** SVG diagram of NOLA rail gateway structure

**Business Value:**
- **Port-Rail Integration:** Critical for Lower Mississippi River port analysis
- **Class I Connections:** UP, NS, CPKC, BNSF operations at NOLA
- **Maritime Terminal Access:** Rail serving Gulf ports
- **SESCO Relevance:** Houston terminal has similar dynamics

**Why Not Migrated:**
- Regional study fits CLAUDE.md structure but not yet moved
- Should complement Lower Mississippi River analysis in regional_studies

##### 7. Reference Library (1,907 files in read_rail/)
**Location:** `project_rail/read_rail/` → **NO TARGET IN CLAUDE.MD**
**Status:** ❌ **NOT MIGRATED** — Extensive research library

**Contents:**
- **STB Documentation:**
  - 2023-STB-Waybill-Reference-Guide.pdf (4.1 MB) — Official STB guide
  - STB methodology papers, waybill documentation
  - stb_build_1/ — STB data processing pipeline (complete system)

- **Academic Papers:**
  - Cost Models and Cost Factors of Road Freight Transportation.pdf (1.5 MB)
  - Various industry research papers
  - Railroad economics and operations research

- **Industry Documentation:**
  - AAR-RIO-JULY-3-2025-FINAL.pdf (362 KB) — AAR Railroad Index Overview
  - AAR-Staggers-Act-Fact-Sheet.pdf (306 KB) — Staggers Act economics
  - BNSF-5-Geography-Groups.pdf (990 KB) — BNSF service regions
  - BNSF-8005-Switch-Book.pdf (793 KB) — BNSF switching guide

- **Rail Terminology:**
  - APTA-Compendium-of-Definitions-Acronyms-for-Rail-Systems.pdf (1.7 MB)

**Business Value:**
- **Research Foundation:** Supports methodology development for white papers
- **Industry Standards:** AAR, STB, APTA standards and definitions
- **Validation:** Academic research validates cost model approaches

**Why Not Migrated:**
- Could integrate into `05_DOCUMENTATION/` or create new research library location
- Some content already embedded in migrated code documentation

##### 8. Other Unmigrated Components

**Analytics Platforms (duplicate structures):**
- `rail_analyticssrc/` — Alternate analytics source code
- `rail_analyticsdata/` — Alternate analytics data
- `rail_analyticsdashboards/` — Alternate dashboards

**Processing Outputs:**
- `01_processed/` — SCRS consolidated datasets
- `02_integrated/` — Cross-dataset linkages
- `03_geospatial/` — Additional GIS layers

**Project Documentation:**
- `DATA_GOVERNANCE_FRAMEWORK.md` (17.3 KB) — Core methodology
- `FAF_MULTIMODAL_FREIGHT_INTEGRATION_PLAN.md` (19.5 KB) — Integration plan
- `RAIL_ANALYTICS_PLATFORM_PLAN.md` (35 KB) — Platform architecture
- `SESSION_SUMMARY_2026-01-24.md` — Previous session handoff
- 5 HANDOFF_SESSION files (Feb 13-23) — Recent session notes

**Visualization Outputs:**
- report_*.png — Report visualizations
- *_section.png — Report section graphics
- Various HTML reports and interactive visualizations

---

## ALIGNMENT WITH CLAUDE.MD SPECIFICATION

### Target Locations per CLAUDE.md

| CLAUDE.md Section | Current Migration Status | Missing Content |
|---|---|---|
| **01_DATA_SOURCES/federal_rail/** | ⚠️ Partial (555 files in stb_economic_data) | NTAD rail network (0 files), FRA safety data (0 files), SCRS data (541 files unmigrated) |
| **01_DATA_SOURCES/geospatial/rail_layers/** | ❌ Empty | 90 files in project_rail/01_geospatial/ |
| **02_TOOLSETS/rail_cost_model/** | ✅ Core framework migrated (152 files) | Reference library (1,907 files), rate database (748 files), SESCO proprietary data |
| **01_DATA_SOURCES/regional_studies/lower_miss_river/** | ⚠️ Exists but NOLA study not integrated | New Orleans rail gateway (34 files) |
| **03_COMMODITY_MODULES/cement/supply_chain_models/rail_routes/** | ❌ Not yet populated | Cement-specific rail analysis from project_rail |

### Missing Specification Gaps

CLAUDE.md does **not** specify target locations for:

1. **Railroad Knowledge Banks** (knowledge_bank/ — 166 files)
   - **Proposed Location:** Create new `02_TOOLSETS/rail_intelligence/` or `05_DOCUMENTATION/rail_knowledge_bank/`
   - **Justification:** This is operational intelligence, not raw data. It's a toolset for freight flow analysis, captive shipper studies, and routing optimization.

2. **STB Rate Database** (rate_files/ — 748 files, 113 MB DuckDB)
   - **Proposed Location:** `02_TOOLSETS/rail_cost_model/data/reference/stb_rates/` or new `02_TOOLSETS/rail_rate_intelligence/`
   - **Justification:** Commercial rate intelligence complements cost modeling, validates URCS calculations.

3. **SESCO Proprietary Data** (SESCO_RAIL/ within read_rail/)
   - **Proposed Location:** Keep in separate project_rail with access controls, or create `03_COMMODITY_MODULES/cement/proprietary/sesco_rail/` with restricted access
   - **Justification:** Confidential client data should not be in general platform.

4. **SCRS Consolidated Data** (processed SCRS files)
   - **Proposed Location:** `01_DATA_SOURCES/federal_rail/scrs_facility_data/` or integrate into `02_TOOLSETS/facility_registry/`
   - **Justification:** Rail-served facility data complements EPA FRS, supports commodity-specific facility analysis.

5. **Reference Library** (read_rail/ research papers)
   - **Proposed Location:** `05_DOCUMENTATION/research_library/rail/`
   - **Justification:** Supports white paper methodology, industry standards documentation.

---

## DATA QUALITY AND INTEGRATION STATUS

### Data Sources Summary

| Data Source | Original Location | Migrated? | Target Integration Point |
|---|---|---|---|
| **NTAD Rail Network** (NARN) | rail_cost_model/data/raw/ntad/ | ✅ Partial | 01_DATA_SOURCES/federal_rail/ntad_rail_network/ (empty) |
| **STB Economic Data** (URCS, Waybill) | Various | ✅ Complete | 01_DATA_SOURCES/federal_rail/stb_economic_data/ (555 files) |
| **STB Rate Database** (10,340 contracts) | rate_files/stb_contracts.db | ❌ Not migrated | No target specified |
| **SCRS Facility Data** (39,936 records) | 00_raw_sources/SCRS/ + 01_processed/ | ❌ Not migrated | Could feed facility_registry |
| **Railroad Knowledge Bank** (164 files) | knowledge_bank/ | ❌ Not migrated | No target specified |
| **SESCO Rail Data** (waybills, invoices) | read_rail/SESCO_RAIL/ | ❌ Not migrated | Proprietary, separate handling |
| **NOLA Rail Study** (34 files) | nola_rail/ | ❌ Not migrated | Regional studies integration |
| **Rail GIS Layers** (90 files) | 01_geospatial/ | ❌ Not migrated | 01_DATA_SOURCES/geospatial/rail_layers/ |

### Cross-Platform Integration Points

#### With EPA FRS Facility Registry
**Status:** Ready for integration, not yet executed
**Approach:**
1. SCRS provides rail-served facility lists (8,555 bulk commodity facilities)
2. EPA FRS provides facility locations, NAICS codes, parent companies
3. **Cross-Match Strategy:**
   - Spatial matching (coordinates within tolerance)
   - NAICS code validation (327310 cement, 331110 steel, etc.)
   - Fuzzy name matching (rapidfuzz) for facility identification
   - Parent company reconciliation
4. **Output:** Master facility database with rail access + environmental compliance + ownership

**Integration Code:**
From `project_rail/README.md` lines 141-148:
```
Cross-Dataset Reconciliation:
- SCRS ↔ EPA FRS: Spatial + NAICS + name matching
- EPA FRS ↔ NTAD: Facility → rail/port proximity
- SCRS + FRS ↔ Rail Cost Model: Facility → network routing
```

**Current Status:** Planned but not implemented

#### With Cement Commodity Module
**Status:** Direct application ready
**Integration Points:**
1. **Rail-Served Cement Plants:** SCRS + EPA FRS matching for NAICS 327310
2. **Cement Distribution Routes:** Rail cost model can calculate Houston terminal → upriver cement markets
3. **Import Terminal Rail Access:** Knowledge bank documents UP/BNSF/NS cement terminal rail serving
4. **SCM Sources:** Fly ash (coal plants with rail), slag (steel mills with rail), pozzolans (mining rail access)

**Cement-Specific Deliverables from Knowledge Bank:**
- BNSF cement facilities documented
- NS cement facilities documented
- UP cement facilities documented
- All Class I carriers: 15+ cement facilities per carrier

**Application:** Supports `03_COMMODITY_MODULES/cement/supply_chain_models/rail_routes/`

#### With Barge Cost Model
**Status:** Complementary modal analysis
**Integration:**
- Rail vs. barge cost comparison (Houston → Memphis cement)
- Intermodal transfer points (barge terminals with rail access)
- NOLA rail gateway study complements NOLA barge operations

---

## TECHNICAL ARCHITECTURE

### Technology Stack

**Python Environment:**
```
Core Libraries:
- pandas, numpy (data processing)
- geopandas, shapely, fiona (geospatial)
- networkx (network graph analysis)
- folium, matplotlib, plotly (visualization)

Databases:
- DuckDB (stb_contracts.db — 113 MB, 10,340 contracts)
- NetworkX pickle (.gpickle) — Rail network graph

Data Formats:
- Raw: CSV, Excel, shapefile, GDB
- Processed: CSV, parquet (fast reads)
- Geospatial: GeoPackage (.gpkg), GeoJSON
- Network: NetworkX pickle
```

**Git Repository:**
- Active development (commits Feb 13-23)
- `.gitignore` excludes large data files
- Recent commits: Class I knowledge bank, short line knowledge banks

**Dependencies (requirements.txt):**
```
click>=8.1
pyyaml>=6.0
tqdm>=4.66
requests>=2.31
duckdb>=1.1
pandas>=2.1
pyarrow>=14.0
geopandas>=0.14
folium>=0.15
shapely>=2.0
networkx>=3.2
matplotlib>=3.8
plotly>=5.18
```

### Data Processing Pipelines

#### SCRS Consolidation Pipeline
**Status:** Complete in original project, not migrated
**Process:**
1. Download 50 state CSV files from SCRS system
2. Consolidate to single master file (39,936 records)
3. Classify bulk commodities by NAICS code (8,555 facilities)
4. Parent company matching (42 major companies identified)
5. Duplicate detection (24,166 suspected duplicates flagged)

**Output Files:**
- `scrs_consolidated_master.csv`
- `scrs_bulk_commodities_only.csv`
- `scrs_parent_company_lookup.csv`
- `scrs_processing_log.txt`

#### STB Rate Scraping Pipeline
**Status:** Complete in original project, not migrated
**Components:**
1. **scrape_stb_up.py** — Union Pacific STB website scraper
   - Discovered 10,340 contract URLs
   - Downloaded PDF filings
   - Stored URLs in `up_urls_discovered.json`

2. **parse_acs_pdf.py** — ACS tariff PDF parser
   - Extracts tables from PDF rate files
   - Outputs to JSON and CSV
   - Example: ACS-UP-4Q-11-29-2021 parsed successfully

3. **stb_contracts.db** — DuckDB database
   - 113 MB structured database
   - 10,340 Union Pacific contracts indexed
   - Queryable by commodity, origin, destination, party

#### Rail Network Graph Builder
**Status:** Migrated to rail_cost_model
**Process:**
1. Download NTAD/NARN data (rail lines, nodes, yards)
2. Build NetworkX MultiDiGraph
3. Assign edge attributes (distance, owner, track class)
4. Integrate URCS unit costs
5. Calculate shortest path routes with cost estimation
6. Generate Folium interactive maps

**Output:**
- `rail_network.gpickle` — NetworkX graph
- `network_map.html` — Interactive visualization

---

## BUSINESS VALUE ASSESSMENT

### High-Priority Content for Migration

#### 1. Railroad Knowledge Bank (166 files)
**Priority:** 🔴 **CRITICAL — HIGHEST VALUE**
**Business Impact:**
- **Construction Materials Market Intelligence:** Cement, aggregates, steel, lumber facility locations and rail connections for all 6 Class I carriers
- **Captive Shipper Analysis:** Identify facilities with single-carrier access, routing alternatives
- **SESCO Competitive Intelligence:** Cement import terminals (UP, BNSF, NS documented), rail-served cement plants
- **Freight Flow Optimization:** Class I interchange matrix, short line connections, port access routes
- **OceanDatum.ai Service Offering:** Professional railroad intelligence product ready for client delivery

**Unique Value:**
- Created TODAY with ~312,000 tokens of research
- Organized by carrier, commodity, facility type
- Structured data (CSV tables) + narrative documentation (markdown) + interactive reports (HTML)
- 71 short line operators profiled (~13,500 route miles)

**Recommendation:** **IMMEDIATE MIGRATION**
**Proposed Location:** `02_TOOLSETS/rail_intelligence/knowledge_bank/`

#### 2. STB Rate Database (748 files, 113 MB DuckDB)
**Priority:** 🔴 **CRITICAL — COMMERCIAL INTELLIGENCE**
**Business Impact:**
- **Rate Benchmarking:** Validate SESCO rail costs against 10,340 published UP contracts
- **Cost Model Validation:** Compare URCS model outputs to actual tariff rates
- **Cement-Specific Intelligence:** Identify cement/SCM rate patterns, origin-destination pricing
- **Competitive Analysis:** Understand Union Pacific pricing strategies for bulk commodities

**Recommendation:** **IMMEDIATE MIGRATION**
**Proposed Location:** `02_TOOLSETS/rail_cost_model/data/reference/stb_rates/`

#### 3. SCRS Facility Data (541 files + 3 processed CSVs)
**Priority:** 🟡 **HIGH — FACILITY INTELLIGENCE**
**Business Impact:**
- **Rail-Served Facility Mapping:** 8,555 bulk commodity facilities with rail access documented
- **EPA FRS Cross-Matching:** Enables spatial matching of SCRS facilities to EPA FRS environmental compliance data
- **Commodity Analysis:** Identifies cement plants (NAICS 327310), aggregates operations, steel mills, etc.
- **Parent Company Intelligence:** 42 major companies catalogued (ADM, International Paper, Cargill, Martin Marietta, CEMEX, Nucor)

**Recommendation:** **HIGH PRIORITY MIGRATION**
**Proposed Location:** `01_DATA_SOURCES/federal_rail/scrs_facility_data/` + integrate into `02_TOOLSETS/facility_registry/`

#### 4. NOLA Rail Gateway Study (34 files)
**Priority:** 🟡 **HIGH — REGIONAL ANALYSIS**
**Business Impact:**
- **Port-Rail Integration:** Critical for Lower Mississippi River port analysis
- **Class I Gateway Analysis:** UP, NS, CPKC, BNSF operations at New Orleans
- **Maritime Terminal Rail Access:** Supports cement import terminal analysis
- **Houston Terminal Comparison:** SESCO Houston terminal has similar Class I dynamics

**Recommendation:** **HIGH PRIORITY MIGRATION**
**Proposed Location:** `01_DATA_SOURCES/regional_studies/lower_miss_river/nola_rail_gateway/`

### Medium-Priority Content

#### 5. Rail Network GIS Layers (90 files)
**Priority:** 🟢 **MEDIUM — GEOSPATIAL INTEGRATION**
**Recommendation:** Migrate to `01_DATA_SOURCES/geospatial/rail_layers/`

#### 6. Reference Library (1,907 files)
**Priority:** 🟢 **MEDIUM — RESEARCH SUPPORT**
**Recommendation:** Selective migration of key documents to `05_DOCUMENTATION/research_library/rail/`

### Low-Priority / Special Handling Content

#### 7. SESCO Proprietary Data (SESCO_RAIL/ within read_rail/)
**Priority:** ⚫ **SPECIAL HANDLING — CONFIDENTIAL**
**Recommendation:** **DO NOT MIGRATE to master platform**
**Rationale:**
- Proprietary client data (waybills, invoices, carrier statements)
- Confidential business records requiring access controls
- Should remain in separate project_rail directory
- If needed for cement module, use aggregated/anonymized data only

#### 8. Development Artifacts
**Priority:** ⚫ **LOW — ARCHIVE ONLY**
**Contents:** Logs, temporary files, duplicate directory structures (rail_analyticssrc, etc.)
**Recommendation:** Archive in `06_ARCHIVE/project_rail_ORIGINAL/`, do not migrate

---

## RECOMMENDATIONS

### Immediate Actions (Next Session)

#### 1. Migrate Railroad Knowledge Bank
**Priority:** 🔴 **CRITICAL**
**Action Steps:**
1. Create new directory: `02_TOOLSETS/rail_intelligence/`
2. Move entire `knowledge_bank/` directory (166 files)
3. Update CLAUDE.md to include rail_intelligence toolset specification
4. Test interactive HTML reports (summary_report.html, watco_summary.html, gw_summary.html)
5. Verify CSV tables load correctly (watco_master.csv, gw_master.csv)

**Integration Requirements:**
- Link to cement module: `03_COMMODITY_MODULES/cement/supply_chain_models/rail_routes/`
- Cross-reference with facility_registry for rail-served cement plants
- Support captive shipper analysis in port economic impact studies

**Estimated Time:** 30 minutes

#### 2. Migrate STB Rate Database
**Priority:** 🔴 **CRITICAL**
**Action Steps:**
1. Create directory: `02_TOOLSETS/rail_cost_model/data/reference/stb_rates/`
2. Copy `rate_files/stb_contracts.db` (113 MB DuckDB)
3. Copy scraping tools: `scrape_stb_up.py`, `parse_acs_pdf.py`
4. Copy reference files: `up_urls_discovered.json`
5. Document usage in rail_cost_model METHODOLOGY.md

**Integration Requirements:**
- Update rail_cost_model to query stb_contracts.db for rate validation
- Create cost model validation notebook comparing URCS outputs to actual rates
- Document cement-specific rate patterns

**Estimated Time:** 20 minutes

#### 3. Migrate SCRS Facility Data
**Priority:** 🟡 **HIGH**
**Action Steps:**
1. Create directory: `01_DATA_SOURCES/federal_rail/scrs_facility_data/`
2. Move `00_raw_sources/SCRS/` (541 files)
3. Move `01_processed/scrs_*.csv` (3 consolidated files)
4. Create README documenting SCRS methodology
5. Integrate with facility_registry tool for EPA FRS cross-matching

**Integration Requirements:**
- Update facility_registry to ingest SCRS data
- Create spatial matching script (SCRS coordinates → EPA FRS coordinates)
- NAICS code validation across datasets
- Parent company reconciliation

**Estimated Time:** 45 minutes

#### 4. Migrate NOLA Rail Gateway Study
**Priority:** 🟡 **HIGH**
**Action Steps:**
1. Create directory: `01_DATA_SOURCES/regional_studies/lower_miss_river/nola_rail_gateway/`
2. Move `nola_rail/` contents (34 files)
3. Link to Lower Mississippi River regional study
4. Cross-reference with USACE port data

**Estimated Time:** 15 minutes

### Phase 2 Actions (Subsequent Sessions)

#### 5. Migrate Rail Network GIS Layers
**Priority:** 🟢 **MEDIUM**
**Action:** Move `01_geospatial/` to `01_DATA_SOURCES/geospatial/rail_layers/` (90 files)
**Estimated Time:** 20 minutes

#### 6. Selective Reference Library Migration
**Priority:** 🟢 **MEDIUM**
**Action:**
- Identify key documents (STB Waybill Reference Guide, AAR standards, methodology papers)
- Move to `05_DOCUMENTATION/research_library/rail/`
- Leave bulk of read_rail/ in archive

**Estimated Time:** 30 minutes

#### 7. Update CLAUDE.md Specification
**Priority:** 🟡 **HIGH**
**Action:**
- Add rail_intelligence toolset specification
- Add stb_rates reference data specification
- Add scrs_facility_data specification
- Clarify SESCO proprietary data handling
- Update Phase 0 classification guide

**Estimated Time:** 45 minutes

### Long-Term Strategic Recommendations

#### 1. Consolidate Project Structure
**Issue:** project_rail has multiple overlapping directory structures (rail_analytics, rail_analyticssrc, rail_analyticsdata, rail_analyticsdashboards)
**Recommendation:** Consolidate into single analytics structure in migrated rail_cost_model

#### 2. SESCO Data Governance
**Issue:** Proprietary SESCO data (waybills, invoices, statements) mixed with public research
**Recommendation:**
- Keep SESCO_RAIL in separate access-controlled directory
- Create aggregated/anonymized summary data for cement module
- Document data lineage and confidentiality requirements

#### 3. Knowledge Bank Maintenance
**Issue:** Railroad knowledge bank created TODAY will require updates as railroads change
**Recommendation:**
- Establish quarterly update schedule
- Automate scraping where possible (carrier websites, STB filings)
- Version control with git tags (e.g., v2026.02, v2026.05)

#### 4. SCRS-EPA FRS Integration Priority
**Issue:** Two major facility databases (SCRS, EPA FRS) not yet cross-matched
**Recommendation:**
- High-value integration for cement commodity module
- Identifies rail-served cement plants with environmental compliance data
- Supports facility proximity analysis (rail + port + waterway access)

#### 5. Rate Database Expansion
**Issue:** STB rate database currently only covers Union Pacific
**Recommendation:**
- Extend scraping to BNSF, NS, CSX (if data available)
- Integrate cement-specific rates from rate_files/cement/
- Build rate benchmarking dashboard for SESCO cost validation

---

## RISK ASSESSMENT

### Data Loss Risk
**Status:** 🟢 **LOW RISK**
**Reason:** Original project_rail remains intact, no files deleted, migration is copy operation
**Mitigation:** Archive complete original to `06_ARCHIVE/project_rail_ORIGINAL/` after migration

### Data Currency Risk
**Status:** 🟡 **MEDIUM RISK**
**Reason:** Project modified TODAY (Feb 23, 2026) with active development
**Mitigation:**
- Coordinate migration with user to avoid conflicts
- Use git to track changes during migration
- Verify no background agents are working on project_rail during migration

### Proprietary Data Exposure Risk
**Status:** 🟡 **MEDIUM RISK**
**Reason:** SESCO proprietary data (waybills, invoices) mixed with public research
**Mitigation:**
- **DO NOT MIGRATE SESCO_RAIL/** to master platform
- Document which data is proprietary vs. public
- Establish access controls for confidential data

### Integration Complexity Risk
**Status:** 🟡 **MEDIUM RISK**
**Reason:** Multiple cross-dataset integration points (SCRS ↔ EPA FRS, rate database ↔ cost model, knowledge bank ↔ routing)
**Mitigation:**
- Migrate data sources first, integration logic second
- Document integration requirements in each toolset METHODOLOGY.md
- Test integration points incrementally

### Specification Ambiguity Risk
**Status:** 🟡 **MEDIUM RISK**
**Reason:** CLAUDE.md does not specify targets for knowledge bank, rate database, SCRS data
**Mitigation:**
- Update CLAUDE.md with new specifications before migration
- Get user confirmation on proposed locations
- Document rationale for location decisions

---

## VERIFICATION CHECKLIST

### Pre-Migration Verification
- [x] Original project size documented (4,095 files, ~18 GB)
- [x] Current migration status documented (707 files, 17.3%)
- [x] Missing content catalogued (3,388 files, 82.7%)
- [x] Business value assessed for each component
- [x] Migration priorities established
- [x] Risk assessment completed
- [ ] CLAUDE.md updated with new specifications
- [ ] User approval on migration plan

### Post-Migration Verification (To Be Completed)
- [ ] File counts match (compare original vs. migrated)
- [ ] File sizes match (verify no data loss)
- [ ] DuckDB databases functional (stb_contracts.db queryable)
- [ ] CSV tables readable (SCRS, knowledge bank CSVs)
- [ ] HTML reports functional (knowledge bank interactive reports)
- [ ] Python scripts executable (update import paths)
- [ ] Git repository functional (verify commits preserved)
- [ ] Documentation links updated (README cross-references)
- [ ] Integration tests passed (SCRS ↔ EPA FRS, rate DB ↔ cost model)

---

## CONCLUSION

### Summary Assessment

Project_rail is a **highly valuable, actively developed** rail intelligence and cost modeling platform with **only 21.4% content migrated by size (17.3% by file count)**. The unmigrated 78.6% (14.14 GB) includes:

1. **Railroad Knowledge Bank (166 files)** — Created TODAY, highest business value, immediate migration priority
2. **STB Rate Database (748 files, 113 MB)** — Commercial intelligence, critical for cost validation
3. **SCRS Facility Data (541 files)** — Rail-served facility mapping, EPA FRS integration ready
4. **SESCO Proprietary Data** — Confidential, should NOT migrate to master platform
5. **Reference Library (1,907 files)** — Research foundation, selective migration

### Critical Dependencies

The master reporting platform **cannot fully function** without:
- **Railroad knowledge bank** → Cement module rail distribution analysis incomplete
- **Rate database** → Rail cost model cannot validate against actual tariffs
- **SCRS facility data** → Facility registry cross-matching incomplete
- **NOLA rail study** → Lower Mississippi River regional study missing rail component

### Next Steps

**Immediate (This Session):**
1. Update CLAUDE.md with new specifications (rail_intelligence, stb_rates, scrs_facility_data)
2. Get user approval on migration plan and proposed locations
3. Begin migration of highest-priority components (knowledge bank, rate database)

**Near-Term (Next 1-2 Sessions):**
1. Complete SCRS facility data migration
2. Integrate NOLA rail gateway study
3. Migrate rail network GIS layers
4. Test cross-platform integrations (facility_registry, cement module)

**Long-Term (Ongoing):**
1. Maintain railroad knowledge bank (quarterly updates)
2. Expand rate database (additional carriers)
3. Implement SCRS-EPA FRS cross-matching
4. Build integrated freight flow analysis dashboard

### User Decision Required

**Question for William:**

The railroad knowledge bank (166 files, created TODAY) is the highest-value unmigrated content but CLAUDE.md doesn't specify where it should go.

**Proposed location:** `02_TOOLSETS/rail_intelligence/`
**Rationale:** This is operational intelligence (not raw data), serves as a toolset for freight flow analysis, captive shipper studies, and routing optimization.

**Alternative:** `05_DOCUMENTATION/rail_knowledge_bank/` (if considered reference material rather than analytical tool)

**Your preference?** This decision will determine how the knowledge bank integrates with the cement module and other commodity verticals.

---

**Report completed:** February 23, 2026
**Next action:** Await user approval on migration plan and CLAUDE.md updates before proceeding with file moves.
