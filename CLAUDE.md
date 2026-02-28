# CLAUDE.md — US Bulk Supply Chain Reporting Platform
**Project Root:** `G:\My Drive\LLM\project_master_reporting`
**Owner:** William S. Davis III (30+ yrs maritime/supply chain consulting)
**Version:** 1.0.0 | Last Updated: 2026-02-24

---

## EXECUTIVE BRIEFING

You are building a **unified reporting and analysis platform** for US bulk commodity supply chain intelligence:

1. **Core Platform (commodity-agnostic):** US inland waterway, port, rail, pipeline infrastructure — the backbone for ANY commodity
2. **Commodity Modules (pluggable):** Starting with cement/cementitious materials, designed so grain, fertilizer, metals, etc. bolt on using same toolsets

**Your Role:** Full implementation autonomy. William has deep domain expertise but depends entirely on you for technical execution. **Do not ask confirmation on technical choices** — make expert judgment calls. Only pause for strategic forks or material scope changes.

---

## WORKING STYLE

- **Voice typing:** Parse for intent, not literal text
- **High-level first, then deep detail:** He thinks conceptually, then pivots to technical specifics
- **Comprehensive execution:** Minimize confirmation loops, maximize forward progress
- **Error handling:** He pastes full tracebacks — fix efficiently without re-explaining context
- **Grid reference system:** Use Column-Letter + Row-Number (e.g., "AZ-100") for data dictionary references

---

## CLIENT CONFIDENTIALITY — CRITICAL

**This platform is William S. Davis III's proprietary intellectual property.**

**BLOCKING REQUIREMENT:**
- **DO NOT mention specific client names** (e.g., "SESCO Cement") in git docs, README files, or general platform documentation
- Client-specific work appears ONLY in dedicated deliverable folders (e.g., `03_COMMODITY_MODULES/cement/reports/client_name/`)
- In all platform docs, toolset docs, methodology files: refer to clients generically or use William's name as author/owner
- Replace "OceanDatum.ai" references with "William S. Davis III" throughout platform

---

## CROSS-PROJECT BOUNDARY — DO NOT TOUCH

**The OceanDatum.ai website is a SEPARATE project.**

- Website repo: `theshipsagent.github.io/` (sibling directory under `G:\My Drive\LLM\`)
- **NEVER read, modify, or commit files** in `theshipsagent.github.io/` from this environment
- **NEVER modify** any `.html`, `.css`, `.js` files related to the OceanDatum.ai website
- Website work happens in its own dedicated Claude session with its own CLAUDE.md
- If William asks about website pages from this session, remind him it's handled separately

---

## PROJECT STRUCTURE (High-Level)

```
project_master_reporting/
├── CLAUDE.md                          ← THIS FILE (condensed directives)
├── README.md                          ← Project overview, quickstart
├── config.yaml                        ← Global configuration
├── requirements.txt                   ← Python dependencies
│
├── 01_DATA_SOURCES/                   ← Raw data ingestion (see DIRECTORY_STRUCTURE.md)
│   ├── federal_waterway/              ← USACE MRTIS ✅, FGIS grain ✅, entrance/clearance ✅
│   ├── federal_rail/                  ← STB rates ✅, SCRS facilities ✅, NTAD network
│   ├── federal_environmental/         ← EPA FRS ✅
│   ├── federal_trade/                 ← Panjiva ✅, Census trade
│   ├── federal_vessel/                ← Ship register ✅ (52K vessels), MARAD fleet
│   ├── market_data/                   ← USDA GTR, USGS minerals, PCA cement
│   ├── geospatial/                    ← Rail layers ✅ (976 MB, 112 files), waterway, port
│   └── regional_studies/              ← Lower Miss River, Plaquemines Parish
│
├── 02_TOOLSETS/                       ← Commodity-agnostic analysis engines
│   ├── barge_cost_model/              ✅ OPERATIONAL (6,860 nodes, API, forecasting)
│   ├── rail_cost_model/               ✅ OPERATIONAL (STB 10,340 contracts, 39,936 facilities)
│   ├── vessel_intelligence/           ✅ OPERATIONAL (8-phase, 854K records, 100% coverage)
│   ├── rail_intelligence/             ✅ OPERATIONAL (6 Class I + 71 short lines)
│   ├── vessel_voyage_analysis/        ✅ OPERATIONAL (Phase 1+2, FGIS grain, 41K voyages)
│   ├── facility_registry/             ✅ OPERATIONAL (EPA FRS 4M+ facilities, DuckDB)
│   ├── port_cost_model/               ⏳ PARTIAL (pilotage calculator exists)
│   ├── geospatial_engine/             ⏳ PLANNED (shared GIS utilities)
│   └── policy_analysis/               ⏳ PARTIAL (Section 301 data exists)
│
├── 03_COMMODITY_MODULES/              ← Pluggable commodity verticals
│   ├── cement/                        ✅ ACTIVE (market intel, SCM, supply chain models)
│   ├── steel/                         ✅ NEW (AIST 68 facilities)
│   ├── aluminum/                      ✅ NEW (smelters, mills, extrusion)
│   ├── copper/                        ✅ NEW (43 facilities)
│   └── forestry/                      ✅ NEW (sawmills, pulp/paper)
│
├── 04_REPORTS/                        ← Master report generation pipeline
│   ├── templates/                     ← Reusable report templates
│   ├── us_bulk_supply_chain/          ← Master report (10 chapters, commodity-agnostic)
│   └── cement_commodity_report/       ← Cement drilldown (references core report)
│
├── 05_DOCUMENTATION/                  ← Detailed reference docs (NEW)
│   ├── DIRECTORY_STRUCTURE.md         ← Full directory tree with descriptions
│   ├── MIGRATION_STATUS.md            ← Detailed project migration tracking
│   ├── IMPLEMENTATION_GUIDE.md        ← Phase-by-phase build instructions
│   ├── TECHNICAL_STANDARDS.md         ← Code style, data standards, file naming
│   ├── DATA_SOURCES.md                ← Complete data source catalog (config.yaml detail)
│   ├── NAICS_HTS_CODES.md             ← Commodity-relevant classification codes
│   ├── architecture.md                ← System architecture diagrams
│   ├── data_dictionary/               ← Master data dictionary with grid references
│   ├── api_catalog.md                 ← All API endpoints
│   └── methodology_index.md           ← Links to all toolset METHODOLOGY.md files
│
└── 06_ARCHIVE/                        ← Original project folders (read-only reference)
```

**Detailed structure:** See `05_DOCUMENTATION/DIRECTORY_STRUCTURE.md`
**Migration status:** See `05_DOCUMENTATION/MIGRATION_STATUS.md` (8 of 12 projects complete, 67%)

---

## MASTER CLI ENTRY POINT

Unified CLI at project root (`report-platform` command):

```bash
# Data operations
report-platform data download --source epa_frs
report-platform data ingest --source panjiva
report-platform data status                    # Show freshness of all sources

# Toolset operations
report-platform barge-cost --origin "Houston" --destination "Memphis" --commodity cement
report-platform rail-cost --origin "Baton Rouge" --destination "Chicago" --naics 327310
report-platform facility-search --state LA --naics 327310 --radius 50

# Report generation
report-platform report generate --report us_bulk_supply_chain --format docx
report-platform commodity list
report-platform commodity init --name grain    # Scaffold new module
```

---

## TECHNICAL STANDARDS (Summary)

**Full standards:** See `05_DOCUMENTATION/TECHNICAL_STANDARDS.md`

**Code:**
- Python 3.11+, type hints, Click CLI
- DuckDB primary analytics database
- Parquet for intermediate data, JSON for config

**Data:**
- Coordinates: WGS84 (EPSG:4326)
- Money: USD with year noted
- Tonnage: Short tons (US) unless stated metric
- Dates: ISO 8601 (YYYY-MM-DD)

**File Naming:**
- Snake_case, no spaces
- Prefix data files with source (e.g., `usace_lock_performance_2024.csv`)
- Prefix scripts with action verb (e.g., `download_frs.py`)

**Documentation:**
- Every toolset: `METHODOLOGY.md`
- Every data source folder: `README.md` (source URL, schema, refresh cadence)
- Master data dictionary: Grid reference system (Column-Letter + Row-Number)
- All reports: Cite sources with URL and access date

---

## CURRENT PRIORITIES (2026-02-24)

### Platform Status
- **Toolsets operational:** 6 of 8 (75%)
- **Projects migrated:** 8 of 12 (67%)
- **Commodity modules:** 5 active
- **Production-ready:** Yes

### Next Work (in priority order)

**1. Remaining Project Migrations:**
- `project_us_flag` (~50% complete) → `02_TOOLSETS/policy_analysis/` + `01_DATA_SOURCES/federal_vessel/`
- `project_port_nickle` (0% complete) → `01_DATA_SOURCES/regional_studies/plaquemines_parish/` + `04_REPORTS/`
- `sources_data_maps` (~40% complete) → `01_DATA_SOURCES/geospatial/` (consolidate remaining GIS layers)
- `project_pipelines` (~30% complete) → Assess if needed, may deprecate

**2. Platform Enhancements:**
- Master CLI integration (`report-platform` commands for all toolsets)
- End-to-end cement module integration test (use ALL toolsets for single analysis)
- Census Bureau trade statistics collection
- Port cost model completion (stevedoring, tariffs, proforma generator)

**3. Report Generation:**
- US Bulk Supply Chain Report (10 chapters) — leverage existing toolset outputs
- Cement Commodity Report (10 chapters) — integrate vessel_intelligence + rail/barge models

---

## COMMODITY MODULE TEMPLATE

When adding new commodity (grain, fertilizer, metals, etc.):

```
03_COMMODITY_MODULES/{commodity_name}/
├── README.md
├── config.yaml                        ← Commodity-specific config
├── naics_hts_codes.json              ← Relevant classification codes
├── market_intelligence/
│   ├── supply_landscape/             ← Production facilities, capacity
│   ├── demand_analysis/              ← Consumption patterns
│   ├── trade_flows/                  ← Import/export analysis
│   └── pricing/                      ← Market pricing data
├── supply_chain_models/
│   ├── barge_routes/                 ← Commodity-specific barge routing
│   ├── rail_routes/                  ← Commodity-specific rail routing
│   └── terminal_operations/          ← Commodity-specific handling
└── reports/
    ├── templates/
    ├── drafts/
    └── published/
```

**Use core toolsets:**
- `facility_registry` for production/consumption facility mapping
- `vessel_intelligence` for trade flow classification
- `barge_cost_model` / `rail_cost_model` for distribution economics
- `port_cost_model` for terminal cost estimation

---

## INTEGRATION ARCHITECTURE

**Cross-Toolset Integration (already working):**
- `vessel_intelligence` ↔ `cement` module (import manifest classification)
- `rail_intelligence` ↔ `rail_cost_model` (knowledge bank + rate benchmarking)
- `vessel_voyage_analysis` ↔ `facility_registry` (terminal-to-facility linking)
- `barge_cost_model` ↔ all commodity modules (inland distribution routing)

**Knowledge Banks:**
- Specialized knowledge banks live WITH their toolset (e.g., `rail_intelligence/knowledge_bank/`)
- NOT in a centralized 07_KNOWLEDGE_BANK/ folder

---

## KEY REFERENCES

| Document | Purpose |
|---|---|
| `05_DOCUMENTATION/DIRECTORY_STRUCTURE.md` | Full directory tree with file counts/sizes |
| `05_DOCUMENTATION/MIGRATION_STATUS.md` | Detailed project migration tracking |
| `05_DOCUMENTATION/IMPLEMENTATION_GUIDE.md` | Phase-by-phase build sequence |
| `05_DOCUMENTATION/TECHNICAL_STANDARDS.md` | Code style, data formats, file naming |
| `05_DOCUMENTATION/DATA_SOURCES.md` | Complete data source catalog |
| `05_DOCUMENTATION/NAICS_HTS_CODES.md` | Commodity classification codes |

**For autonomous sessions:** Read `MIGRATION_STATUS.md` first to see what's complete vs. in-progress.

---

## CRITICAL CONTEXT

This platform consolidates ~2 years of incremental research across 12 separate workstreams. William has deep maritime/commodity domain expertise — when he describes business logic, he's usually right. Translate his intent into working code without second-guessing domain knowledge.

**End goal:** Publishing-quality reporting platform owned by William S. Davis III for maritime and bulk commodity supply chain consulting, with commodity modules that spin up for any client in different verticals.
