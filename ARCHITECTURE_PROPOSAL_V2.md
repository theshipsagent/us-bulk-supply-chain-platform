# ARCHITECTURE PROPOSAL V2 — US Bulk Supply Chain Reporting Platform
**Date**: 2026-02-23
**Status**: DRAFT FOR REVIEW
**Purpose**: Comprehensive architecture incorporating Knowledge Bank, Master Facility Register, and data sources organization

---

## EXECUTIVE SUMMARY

This proposal integrates the original CLAUDE.md architecture with new components identified through architectural review:

**NEW COMPONENTS:**
1. **07_KNOWLEDGE_BANK/** - Centralized reference data, competitive intelligence, facility registry
2. **Master Facility Register** - Unified facility profiles linking fragmented data sources
3. **Centralized Data Sources Catalog** - Registry of all data sources with distributed storage

**KEY ARCHITECTURAL DECISIONS:**
- Data sources: **Centralized catalog + distributed storage** (see Section 3)
- Reference data: **Centralized in Knowledge Bank**, consumed by modules
- Facility intelligence: **Master Facility Register** as single source of truth
- Client intelligence: **Segmented by client** for multi-client OceanDatum.ai scaling

---

## TABLE OF CONTENTS

1. [Directory Structure Overview](#1-directory-structure-overview)
2. [Layer-by-Layer Breakdown](#2-layer-by-layer-breakdown)
3. [Data Sources Organization Strategy](#3-data-sources-organization-strategy)
4. [Knowledge Bank Detailed Design](#4-knowledge-bank-detailed-design)
5. [Module Interaction Patterns](#5-module-interaction-patterns)
6. [Data Flow Architecture](#6-data-flow-architecture)
7. [Implementation Roadmap](#7-implementation-roadmap)

---

## 1. DIRECTORY STRUCTURE OVERVIEW

```
project_master_reporting/
│
├── config.yaml                        ← Global configuration (paths, API keys, client settings)
├── requirements.txt                   ← Python dependencies
├── pyproject.toml                     ← Package metadata
├── CLAUDE.md                          ← Project specification (original)
├── ARCHITECTURE_PROPOSAL_V2.md        ← THIS FILE
├── README.md                          ← Project quickstart
│
├── 01_DATA_SOURCES/                   ← Raw data ingestion layer (distributed storage)
│   ├── README.md                      ← Master data sources catalog (THE REGISTRY)
│   ├── data_sources_catalog.yaml      ← Centralized metadata for ALL sources
│   │
│   ├── federal_waterway/              ← USACE data (distributed by category)
│   │   ├── README.md
│   │   ├── wcsc_waterborne_commerce/
│   │   ├── mrtis/
│   │   ├── ndc_lock_performance/
│   │   └── usace_entrance_clearance/
│   │
│   ├── federal_rail/                  ← STB, DOT, FRA data
│   ├── federal_environmental/         ← EPA data
│   ├── federal_trade/                 ← Census, USITC, Panjiva
│   ├── federal_vessel/                ← MARAD, USCG
│   ├── market_data/                   ← USDA, USGS, EIA, PCA
│   ├── geospatial/                    ← GIS layers
│   └── regional_studies/              ← Location-specific research
│
├── 02_TOOLSETS/                       ← Commodity-agnostic analysis engines
│   ├── README.md                      ← Toolset catalog
│   │
│   ├── barge_river/                   ← Inland waterway freight analysis
│   │   ├── README.md
│   │   ├── METHODOLOGY.md
│   │   ├── api_reference.md
│   │   ├── src/
│   │   ├── data/                      ← TOOLSET-SPECIFIC reference data
│   │   │   ├── gtr_rate_tables/       ← USDA GTR historical rates
│   │   │   ├── lock_delay_models/     ← Lock delay probability distributions
│   │   │   └── waterway_network/      ← River network graph (NetworkX)
│   │   └── tests/
│   │
│   ├── rail/                          ← Railroad freight analysis
│   │   ├── src/
│   │   ├── data/                      ← TOOLSET-SPECIFIC reference data
│   │   │   ├── ntad_network/          ← NARN rail network shapefiles
│   │   │   ├── urcs_cost_tables/      ← STB URCS factors
│   │   │   └── splc_lookup/           ← Standard Point Location Codes
│   │   └── tests/
│   │
│   ├── ocean_vessel/                  ← Ocean freight & vessel tracking
│   │   ├── src/
│   │   ├── data/                      ← TOOLSET-SPECIFIC reference data
│   │   │   ├── hts_codes/             ← HTS 2-digit, 4-digit, 6-digit lookups
│   │   │   ├── vessel_characteristics/ ← Lloyd's vessel registry
│   │   │   └── port_pair_distances/   ← Sea route distance matrix
│   │   └── tests/
│   │
│   ├── port_cost_model/               ← Port/terminal cost estimation
│   │   ├── src/
│   │   ├── data/                      ← TOOLSET-SPECIFIC reference data
│   │   │   ├── port_tariffs/          ← Port authority tariff schedules
│   │   │   ├── pilotage_zones/        ← Mississippi River pilotage associations
│   │   │   └── stevedoring_rates/     ← Cargo handling benchmarks
│   │   └── tests/
│   │
│   ├── epa_facility/                  ← EPA FRS geospatial analysis
│   │   ├── src/
│   │   ├── data/
│   │   │   └── frs.duckdb             ← EPA FRS national database (4M+ facilities)
│   │   └── tests/
│   │
│   ├── geospatial/                    ← GIS and mapping utilities
│   ├── policy_analysis/               ← Maritime policy, tariffs, Jones Act
│   ├── economic/                      ← Port economic impact (RIMS II)
│   ├── port_development/              ← NEW: Port feasibility analysis
│   ├── scenario_planning/             ← NEW: What-if modeling engine
│   ├── forecasting/                   ← NEW: Time-series forecasting
│   ├── market_monitor/                ← NEW: Continuous data monitoring & alerts
│   └── historical/                    ← Historical data analysis
│
├── 03_COMMODITY_MODULES/              ← Pluggable commodity verticals
│   ├── README.md                      ← Commodity catalog
│   ├── HANDOFF.md                     ← Integration status
│   │
│   ├── cement_scm_family/             ← RESTRUCTURED: SCM family parent
│   │   ├── README.md                  ← SCM market overview
│   │   ├── scm_master_outlook.md      ← Combined supply/demand analysis
│   │   │
│   │   ├── portland_cement/           ← Primary commodity
│   │   │   ├── README.md
│   │   │   ├── config.yaml
│   │   │   ├── naics_hts_codes.json   → References Knowledge Bank naics_master
│   │   │   ├── market_intelligence/
│   │   │   │   ├── supply_landscape/
│   │   │   │   ├── demand_analysis/
│   │   │   │   ├── trade_flows/
│   │   │   │   └── scm_markets/
│   │   │   ├── supply_chain_models/   ← Cement-specific routes
│   │   │   ├── reports/
│   │   │   └── data_sources.json      ← Commodity-specific source list
│   │   │
│   │   ├── slag_ggbfs/                ← SCM sub-module
│   │   │   ├── market_intelligence/
│   │   │   │   └── dossier/
│   │   │   │       ├── SLAG_COMPREHENSIVE_DOSSIER.html
│   │   │   │       └── SLAG_COMPREHENSIVE_DOSSIER.pdf
│   │   │   └── data_sources.json
│   │   │
│   │   ├── fly_ash/                   ← SCM sub-module
│   │   │   ├── market_intelligence/
│   │   │   │   └── dossier/
│   │   │   └── data_sources.json
│   │   │
│   │   ├── natural_pozzolans/         ← SCM sub-module
│   │   └── aggregates/                ← Related (limestone feeds cement)
│   │
│   ├── grain/                         ← Future commodity
│   │   ├── README.md
│   │   ├── config.yaml
│   │   ├── naics_hts_codes.json
│   │   ├── data_sources.json          ← COMMODITY-SPECIFIC sources
│   │   ├── market_intelligence/
│   │   ├── supply_chain_models/
│   │   └── reports/
│   │
│   ├── coal/                          ← Future commodity
│   ├── steel_metals/
│   ├── fertilizers/
│   ├── oil_gas/
│   ├── chemicals/
│   └── petcoke/
│
├── 04_REPORTS/                        ← Generated reports and publications
│   ├── README.md
│   ├── templates/                     ← Reusable report templates
│   ├── us_bulk_supply_chain/          ← Master report (commodity-agnostic)
│   └── commodity_reports/             ← Commodity-specific reports
│
├── 05_DOCUMENTATION/                  ← Project-wide documentation
│   ├── architecture.md                ← System architecture (this evolves into summary)
│   ├── data_dictionary/
│   ├── api_catalog.md
│   ├── methodology_index.md
│   ├── MASTER_FACILITY_REGISTER_CONCEPT.md
│   └── changelog.md
│
├── 06_ARCHIVE/                        ← Original folder contents (read-only)
│
├── 07_KNOWLEDGE_BANK/                 ← NEW: Cross-cutting intelligence layer
│   ├── README.md                      ← Knowledge Bank overview
│   │
│   ├── master_facility_register/      ← CORE: Unified facility intelligence
│   │   ├── README.md
│   │   ├── METHODOLOGY.md
│   │   ├── facility_master.duckdb     ← Central facility database
│   │   │
│   │   ├── src/                       ← Entity resolution & profile generation
│   │   │   ├── entity_resolution.py
│   │   │   ├── geospatial_fusion.py
│   │   │   ├── cross_reference_builder.py
│   │   │   ├── attribute_enrichment.py
│   │   │   └── facility_profile_generator.py
│   │   │
│   │   ├── crosswalks/                ← ID mapping tables
│   │   │   ├── epa_frs_to_master.csv
│   │   │   ├── rail_scrs_to_master.csv
│   │   │   ├── port_unloc_to_master.csv
│   │   │   ├── panjiva_consignee_to_master.csv
│   │   │   ├── eia_generator_to_master.csv
│   │   │   └── bls_establishment_to_master.csv
│   │   │
│   │   ├── geometries/                ← Facility boundary polygons
│   │   │   ├── facility_boundaries.geojson
│   │   │   ├── rail_infrastructure.geojson
│   │   │   ├── waterfront_infrastructure.geojson
│   │   │   └── emission_points.geojson
│   │   │
│   │   └── profiles/                  ← Generated facility intelligence cards
│   │       ├── [facility_master_id].json
│   │       └── [facility_master_id].html
│   │
│   ├── reference_data/                ← Centralized taxonomies & lookups
│   │   ├── README.md                  ← Reference data catalog
│   │   ├── naics_master.yaml          ← Complete NAICS taxonomy
│   │   ├── hts_master.yaml            ← Complete HTS code taxonomy
│   │   ├── stcc_codes.yaml            ← Rail commodity codes
│   │   ├── port_codes.yaml            ← UNLOC codes, port directory
│   │   ├── river_mile_markers.yaml    ← Waterway mile marker system
│   │   ├── lock_directory.yaml        ← All 192 USACE locks
│   │   ├── economic_indicators.yaml   ← Construction spending, GDP, inflation
│   │   ├── carbon_emissions.yaml      ← Embodied carbon factors
│   │   └── commodity_adjustments.yaml ← Commodity-specific handling factors
│   │
│   ├── competitive_intelligence/      ← Company-level intelligence
│   │   ├── README.md
│   │   ├── company_master.yaml        ← 500+ companies, harmonized names
│   │   ├── ownership_trees/           ← Corporate hierarchies
│   │   │   ├── holcim_group.json
│   │   │   ├── crh_plc.json
│   │   │   ├── heidelberg_materials.json
│   │   │   └── martin_marietta.json
│   │   │
│   │   ├── facility_portfolios/       ← Company facility inventories
│   │   │   ├── holcim_facilities.geojson
│   │   │   └── crh_facilities.geojson
│   │   │
│   │   ├── ma_tracker/                ← M&A timeline
│   │   │   ├── 2024_transactions.json
│   │   │   ├── 2025_transactions.json
│   │   │   └── historical_index.json
│   │   │
│   │   └── market_share/              ← Market concentration analysis
│   │       ├── cement_market_share_by_region.json
│   │       └── aggregates_market_share_by_msa.json
│   │
│   ├── analytical_patterns/           ← Reusable analytical frameworks
│   │   ├── supply_demand_analysis/
│   │   │   ├── template.md
│   │   │   ├── calculation_methodology.py
│   │   │   └── visualization_templates/
│   │   │
│   │   ├── trade_flow_analysis/
│   │   │   ├── import_analysis_template.md
│   │   │   ├── landed_cost_calculator.py
│   │   │   └── origin_country_profiles/
│   │   │
│   │   ├── transport_cost_modeling/
│   │   │   ├── multimodal_comparison.py
│   │   │   ├── sensitivity_analysis.py
│   │   │   └── route_optimization.py
│   │   │
│   │   └── carbon_footprint/
│   │       ├── lifecycle_analysis_template.md
│   │       ├── carbon_calculator.py
│   │       └── regulatory_compliance/
│   │
│   ├── market_intelligence_commons/   ← Cross-commodity market research
│   │   ├── policy_briefs/
│   │   │   ├── iija_infrastructure_spending.md
│   │   │   ├── section_301_chinese_shipping.md
│   │   │   ├── jones_act_analysis.md
│   │   │   ├── buy_clean_policies.md
│   │   │   └── tariff_outlook_2026.md
│   │   │
│   │   ├── economic_reports/
│   │   │   ├── construction_outlook_2026.md
│   │   │   ├── data_center_boom_infrastructure.md
│   │   │   └── manufacturing_reshoring_trends.md
│   │   │
│   │   ├── technology_trends/
│   │   │   ├── carbon_capture_storage.md
│   │   │   ├── alternative_fuels_industrial.md
│   │   │   └── automation_logistics.md
│   │   │
│   │   └── regulatory_landscape/
│   │       ├── epa_emissions_regulations.md
│   │       ├── water_infrastructure_funding.md
│   │       └── maritime_workforce_crisis.md
│   │
│   └── client_intelligence/           ← Client-specific context
│       ├── sesco/
│       │   ├── strategic_context.md
│       │   ├── terminal_portfolio.json
│       │   ├── import_partners.json
│       │   ├── competitive_positioning.md
│       │   └── scm_strategy_options.md
│       │
│       └── [future_clients]/          ← Scalable for multi-client
│
└── src/report_platform/               ← Unified CLI and platform core
    ├── __init__.py
    ├── __main__.py
    ├── cli.py                         ← Master CLI
    ├── config.py
    ├── database.py
    ├── data_tracker.py
    └── knowledge_bank/                ← Knowledge Bank API
        ├── __init__.py
        ├── facility_registry.py       ← MFR query API
        ├── reference_data.py          ← NAICS/HTS/port lookups
        ├── competitive_intel.py       ← Company/market share queries
        └── client_context.py          ← Client-specific filtering
```

---

## 2. LAYER-BY-LAYER BREAKDOWN

### **Layer 0: Configuration & Documentation**
- **Purpose**: Project metadata, global settings, architectural documentation
- **Key files**: `config.yaml`, `CLAUDE.md`, `README.md`, `05_DOCUMENTATION/`

### **Layer 1: Data Sources (01_DATA_SOURCES/)**
- **Purpose**: Raw data ingestion, organized by source type
- **Pattern**: Distributed storage + centralized catalog
- **Key decision**: Sources stored where logically grouped, cataloged centrally

### **Layer 2: Toolsets (02_TOOLSETS/)**
- **Purpose**: Commodity-agnostic analytical engines
- **Pattern**: Each toolset has `src/`, `data/`, `tests/`, `METHODOLOGY.md`
- **Key decision**: Toolset-specific reference data lives in `toolset/data/`

### **Layer 3: Commodity Modules (03_COMMODITY_MODULES/)**
- **Purpose**: Market intelligence verticals
- **Pattern**: Each module has `market_intelligence/`, `supply_chain_models/`, `reports/`
- **Key decision**: Commodity modules CALL toolsets, don't duplicate analysis code

### **Layer 4: Reports (04_REPORTS/)**
- **Purpose**: Generated output documents
- **Pattern**: Templates + generated reports (markdown, DOCX, PDF)

### **Layer 5: Documentation (05_DOCUMENTATION/)**
- **Purpose**: Project-wide technical documentation
- **Pattern**: Architecture, data dictionaries, API catalogs, methodology index

### **Layer 6: Archive (06_ARCHIVE/)**
- **Purpose**: Historical preservation of original project folders
- **Pattern**: Read-only, organized by original project name

### **Layer 7: Knowledge Bank (07_KNOWLEDGE_BANK/)** ← NEW
- **Purpose**: Cross-cutting intelligence layer
- **Pattern**: Centralized reference data, facility registry, competitive intel
- **Key decision**: Single source of truth for shared knowledge

### **Layer 8: Platform Core (src/report_platform/)**
- **Purpose**: Unified CLI, database connections, APIs
- **Pattern**: Python package, installable via pip

---

## 3. DATA SOURCES ORGANIZATION STRATEGY

### THE PROBLEM

**Question**: Should data sources be:
- A) Centralized in `01_DATA_SOURCES/` only?
- B) Distributed within each module/toolset?
- C) Both (centralized catalog + distributed storage)?

### THE ANSWER: **HYBRID APPROACH (Option C)**

#### **Principle 1: Centralized Catalog + Distributed Storage**

**Centralized Catalog**: `01_DATA_SOURCES/data_sources_catalog.yaml`
- Master registry of EVERY data source used in the platform
- Metadata: URL, format, refresh cadence, file size, access method
- Pointers to where the data actually lives

**Distributed Storage**: Data files live where they're primarily used
- Federal data → `01_DATA_SOURCES/` (shared across all modules)
- Toolset-specific data → `02_TOOLSETS/{toolset}/data/`
- Commodity-specific data → `03_COMMODITY_MODULES/{commodity}/` (optional, or reference federal sources)

#### **Principle 2: Data Source Types**

##### **Type A: Universal Federal Data** → `01_DATA_SOURCES/`
**Characteristics**:
- Used by multiple commodities
- Large files (100+ MB)
- Infrequently updated (annual, quarterly)
- Authoritative government sources

**Examples**:
- EPA FRS national database (732 MB) → `01_DATA_SOURCES/federal_environmental/epa_frs/`
- USACE waterborne commerce (MRTIS) → `01_DATA_SOURCES/federal_waterway/mrtis/`
- Panjiva import manifests (800K+ records) → `01_DATA_SOURCES/federal_trade/panjiva_imports/`
- NTAD rail network shapefiles → `01_DATA_SOURCES/federal_rail/ntad_rail_network/`

**Why here**: Avoid duplication; single download serves all modules

##### **Type B: Toolset-Specific Reference Data** → `02_TOOLSETS/{toolset}/data/`
**Characteristics**:
- Only used by one toolset
- Small-to-medium files (< 50 MB)
- Preprocessed or derived data
- Toolset methodology depends on it

**Examples**:
- USDA GTR rate tables → `02_TOOLSETS/barge_river/data/gtr_rate_tables/`
- STB URCS cost factors → `02_TOOLSETS/rail/data/urcs_cost_tables/`
- Port tariff schedules → `02_TOOLSETS/port_cost_model/data/port_tariffs/`
- HTS code lookups → `02_TOOLSETS/ocean_vessel/data/hts_codes/`

**Why here**: Keeps toolset self-contained; data travels with the analytical engine

##### **Type C: Commodity-Specific Market Data** → `03_COMMODITY_MODULES/{commodity}/`
**Characteristics**:
- Only relevant to one commodity
- Market intelligence (not infrastructure data)
- Often manually curated or purchased
- Proprietary or industry-specific sources

**Examples**:
- Portland Cement Association (PCA) reports → `cement_scm_family/portland_cement/market_intelligence/`
- USGS Mineral Commodity Summaries (cement-specific extract) → `cement_scm_family/`
- SESCO competitive intelligence → `cement_scm_family/market_intelligence/supply_landscape/sesco_competitive.json`

**Why here**: Commodity modules own their market intelligence; doesn't clutter federal data layer

##### **Type D: Knowledge Bank Reference Data** → `07_KNOWLEDGE_BANK/reference_data/`
**Characteristics**:
- Cross-cutting taxonomies and lookups
- Small files (< 10 MB)
- Used by multiple toolsets AND commodity modules
- High-value, manually curated

**Examples**:
- NAICS master taxonomy → `07_KNOWLEDGE_BANK/reference_data/naics_master.yaml`
- HTS master taxonomy → `07_KNOWLEDGE_BANK/reference_data/hts_master.yaml`
- Port directory (all US ports) → `07_KNOWLEDGE_BANK/reference_data/port_codes.yaml`
- Company master list → `07_KNOWLEDGE_BANK/competitive_intelligence/company_master.yaml`

**Why here**: Single source of truth; eliminates duplication across modules

#### **Principle 3: Master Data Sources Catalog**

**File**: `01_DATA_SOURCES/data_sources_catalog.yaml`

**Purpose**: Every data source used anywhere in the platform is registered here

**Schema**:
```yaml
sources:
  epa_frs_national:
    name: "EPA Facility Registry Service - National Dataset"
    category: "federal_environmental"
    url: "https://www.epa.gov/frs/epa-state-combined-csv-download-files"
    format: "csv_zip"
    size_mb: 732
    refresh_cadence: "quarterly"
    last_download: "2026-01-15"
    storage_location: "01_DATA_SOURCES/federal_environmental/epa_frs/NATIONAL_COMBINED.csv"
    used_by:
      - "02_TOOLSETS/epa_facility/"
      - "07_KNOWLEDGE_BANK/master_facility_register/"
      - "03_COMMODITY_MODULES/cement_scm_family/portland_cement/"
      - "03_COMMODITY_MODULES/steel_metals/"
    schema_reference: "05_DOCUMENTATION/data_dictionary/epa_frs_schema.md"
    notes: "Primary facility geospatial database; 4M+ facilities nationwide"

  usda_gtr_barge_rates:
    name: "USDA Grain Transportation Report - Barge Rates"
    category: "market_data"
    url: "https://www.ams.usda.gov/services/transportation-analysis/gtr"
    format: "excel"
    size_mb: 12
    refresh_cadence: "weekly"
    last_download: "2026-02-20"
    storage_location: "02_TOOLSETS/barge_river/data/gtr_rate_tables/gtr_2026.xlsx"
    used_by:
      - "02_TOOLSETS/barge_river/"
    schema_reference: "02_TOOLSETS/barge_river/METHODOLOGY.md"
    notes: "Primary source for barge freight rate benchmarking"

  panjiva_import_manifests:
    name: "Panjiva (S&P Global) - US Import Manifests"
    category: "federal_trade"
    url: "https://panjiva.com (subscription)"
    format: "csv"
    size_mb: 4500
    record_count: 800000
    refresh_cadence: "manual"
    last_download: "2025-12-01"
    storage_location: "01_DATA_SOURCES/federal_trade/panjiva_imports/panjiva_2020_2025.csv"
    used_by:
      - "02_TOOLSETS/ocean_vessel/"
      - "07_KNOWLEDGE_BANK/master_facility_register/"
      - "03_COMMODITY_MODULES/cement_scm_family/"
      - "03_COMMODITY_MODULES/steel_metals/"
    schema_reference: "05_DOCUMENTATION/data_dictionary/panjiva_manifest_schema.md"
    notes: "800K+ import records; primary source for trade flow analysis"

  naics_taxonomy:
    name: "NAICS Code Master Taxonomy"
    category: "reference_data"
    url: "https://www.census.gov/naics/"
    format: "yaml"
    size_mb: 0.5
    refresh_cadence: "every 5 years (next: 2027)"
    last_updated: "2026-02-23"
    storage_location: "07_KNOWLEDGE_BANK/reference_data/naics_master.yaml"
    used_by:
      - "ALL toolsets"
      - "ALL commodity modules"
    schema_reference: "07_KNOWLEDGE_BANK/reference_data/README.md"
    notes: "Centralized NAICS taxonomy; eliminates duplication across modules"
```

#### **Principle 4: Data Source README Files**

Every data storage location has a `README.md` explaining:
1. **What**: Description of the data source
2. **Why**: Why this data is stored here (vs. elsewhere)
3. **Schema**: Link to data dictionary or schema documentation
4. **Refresh**: How to update/refresh the data
5. **Dependencies**: What modules depend on this data

**Example**: `01_DATA_SOURCES/federal_environmental/epa_frs/README.md`
```markdown
# EPA Facility Registry Service (FRS) - National Dataset

## What
EPA's authoritative registry of 4M+ facilities nationwide. Includes lat/lon, NAICS codes,
parent company linkages, environmental permits.

## Why Stored Here
- Used by multiple commodity modules (cement, steel, coal, chemicals)
- Large file (732 MB uncompressed)
- Quarterly refresh from EPA
- Authoritative geospatial baseline for facility analysis

## Schema
See: `05_DOCUMENTATION/data_dictionary/epa_frs_schema.md`

## How to Refresh
```bash
cd 01_DATA_SOURCES/federal_environmental/epa_frs
python download_frs.py --state ALL --output NATIONAL_COMBINED.csv
```

## Used By
- `02_TOOLSETS/epa_facility/` - Facility search and geospatial analysis
- `07_KNOWLEDGE_BANK/master_facility_register/` - Entity resolution seed
- All commodity modules for facility mapping

## Last Updated
2026-01-15 (Q4 2025 release)
```

---

## 4. KNOWLEDGE BANK DETAILED DESIGN

### 4.1 Master Facility Register

**Purpose**: Single source of truth for all industrial facility intelligence

**Core Database**: `07_KNOWLEDGE_BANK/master_facility_register/facility_master.duckdb`

**Tables**:
1. `facilities` - Master facility inventory (one row per facility)
2. `facility_external_ids` - Cross-reference table linking external IDs
3. `facility_attributes` - All attributes from all sources (key-value store)
4. `facility_infrastructure` - Rail, port, road, pipeline connections
5. `facility_ownership` - Historical ownership and M&A timeline

**API**:
```python
from report_platform.knowledge_bank import facility_registry

# Get complete facility profile
profile = facility_registry.get_facility(
    name="ArcelorMittal Burns Harbor",
    state="IN"
)

# Search facilities by criteria
results = facility_registry.search(
    naics_codes=[331110],  # Steel mills
    state="IN",
    has_rail=True,
    has_port=True
)

# Get all facilities for a parent company
company_facilities = facility_registry.get_company_portfolio(
    parent_company="Holcim Group"
)
```

### 4.2 Reference Data Library

**Purpose**: Centralized taxonomies and lookups

**Key Files**:
- `naics_master.yaml` - Complete NAICS taxonomy with commodity mappings
- `hts_master.yaml` - Complete HTS code taxonomy with tariff rates
- `port_codes.yaml` - All US ports with UNLOC, lat/lon, contact info
- `lock_directory.yaml` - All 192 USACE locks with specifications

**API**:
```python
from report_platform.knowledge_bank import reference_data

# Get NAICS codes for a commodity
cement_naics = reference_data.get_naics(commodities=["cement"])
# Returns: ["327310", "327320", "327331", ...]

# Get HTS codes for a commodity
cement_hts = reference_data.get_hts(commodities=["cement"])
# Returns: ["2523.10", "2523.21", "2523.29", ...]

# Get port information
port = reference_data.get_port(unloc="USNOL")  # New Orleans
# Returns: {name, lat, lon, max_draft, pilotage_authority, ...}
```

### 4.3 Competitive Intelligence

**Purpose**: Company profiles, ownership trees, market share analysis

**Structure**:
- `company_master.yaml` - Harmonized company names, aliases, parent relationships
- `ownership_trees/` - Corporate hierarchies (JSON files per parent company)
- `facility_portfolios/` - GeoJSON files showing all facilities per company
- `ma_tracker/` - M&A transaction timeline

**API**:
```python
from report_platform.knowledge_bank import competitive_intel

# Resolve company name
company = competitive_intel.resolve_company("Lafarge Holcim")
# Returns: canonical_id="HOLCIM_GROUP", canonical_name="Holcim Group"

# Get company profile
profile = competitive_intel.get_company_profile("HOLCIM_GROUP")
# Returns: parent, subsidiaries, facility_count, commodities, market_cap, ...

# Get market share
market_share = competitive_intel.get_market_share(
    commodity="cement",
    geography="US",
    year=2024
)
# Returns: {company: percentage, ...} ranked by share
```

### 4.4 Client Intelligence

**Purpose**: Client-specific context for segmented reporting

**Structure**:
- `client_intelligence/sesco/` - SESCO-specific strategy, terminals, partners
- `client_intelligence/[future_clients]/` - Scalable for multi-client consultancy

**API**:
```python
from report_platform.knowledge_bank import client_context

# Get client strategic context
context = client_context.get_client_context("sesco")
# Returns: {ceo_priorities, terminal_portfolio, import_partners, competitive_positioning}

# Generate client-filtered report
from report_platform.reporting import ReportBuilder

report = ReportBuilder(commodity="cement", client="sesco")
report.generate_competitive_analysis()  # Shows SESCO vs. competitors
# Filters out SESCO confidential data if client=None (public report)
```

---

## 5. MODULE INTERACTION PATTERNS

### Pattern 1: Commodity Module Calls Toolset

**Scenario**: Cement module needs barge cost estimate

```python
# In 03_COMMODITY_MODULES/cement_scm_family/portland_cement/supply_chain_models/lower_miss_barge.py

from report_platform.toolsets import barge_river

# Cement module provides origin/destination/commodity
cost = barge_river.calculate_cost(
    origin="Houston, TX",
    destination="Memphis, TN",
    commodity="cement",  # ← Triggers cement-specific adjustments
    tonnage=22500
)

# Toolset returns cost breakdown
# Toolset applies commodity-specific factors from Knowledge Bank:
#   - Discharge rate: 300 MT/hr (cement) vs. 500 MT/hr (grain)
#   - Storage: covered silo required (cement) vs. open (aggregates)
```

### Pattern 2: Toolset Queries Knowledge Bank

**Scenario**: Rail toolset needs NAICS codes for facility matching

```python
# In 02_TOOLSETS/rail/src/route_engine.py

from report_platform.knowledge_bank import reference_data

# Toolset queries Knowledge Bank for NAICS taxonomy
cement_facilities = reference_data.get_facilities(
    naics_codes=reference_data.get_naics(commodities=["cement"]),
    has_rail=True
)

# Knowledge Bank returns facility list from Master Facility Register
# Rail toolset uses facility lat/lon to find nearest NARN rail nodes
```

### Pattern 3: Master Facility Register Aggregates Multi-Source Data

**Scenario**: Build facility profile for "ArcelorMittal Burns Harbor"

```python
# In 07_KNOWLEDGE_BANK/master_facility_register/src/facility_profile_generator.py

from report_platform.knowledge_bank import facility_registry

# Step 1: Entity resolution (fuzzy match across sources)
frs_match = epa_frs.search(name="ArcelorMittal Burns Harbor", state="IN")
rail_match = rail_scrs.search(name="Burns Harbor", buffer_miles=1, center=frs_match.lat_lon)
port_match = usace_port.search(name="Port of Indiana", port_code="USBUR")
panjiva_match = panjiva.consignee_search(name="ARCELORMITTAL", city="Portage")

# Step 2: Create master facility
facility_id = "MFR_00012345"
facility_registry.create_facility(
    facility_master_id=facility_id,
    canonical_name="ArcelorMittal Burns Harbor",
    lat=frs_match.lat,
    lon=frs_match.lon
)

# Step 3: Link external IDs
facility_registry.add_external_id(facility_id, "epa_frs", frs_match.registry_id)
facility_registry.add_external_id(facility_id, "rail_scrs", rail_match.scrs_code)
facility_registry.add_external_id(facility_id, "port_unloc", "USBUR")

# Step 4: Aggregate attributes
facility_registry.add_attribute(facility_id, "environmental", "air_permit", frs_match.air_permit)
facility_registry.add_attribute(facility_id, "rail", "serving_railroads", rail_match.carriers)
facility_registry.add_attribute(facility_id, "port", "berth_count", port_match.berth_count)

# Step 5: Generate unified profile
profile = facility_registry.generate_profile(facility_id)
# Returns: JSON + HTML facility intelligence card
```

---

## 6. DATA FLOW ARCHITECTURE

### Flow 1: Report Generation

```
USER REQUEST: "Generate cement market report for SESCO"
    ↓
CLI: report-platform report generate --commodity cement --client sesco
    ↓
ReportBuilder (src/report_platform/reporting.py)
    ├─→ Load client context from Knowledge Bank
    │   └─→ 07_KNOWLEDGE_BANK/client_intelligence/sesco/
    │
    ├─→ Query Master Facility Register for cement facilities
    │   └─→ 07_KNOWLEDGE_BANK/master_facility_register/facility_master.duckdb
    │
    ├─→ Call barge_river toolset for transport costs
    │   └─→ 02_TOOLSETS/barge_river/src/rate_engine.py
    │       └─→ References USDA GTR data: 02_TOOLSETS/barge_river/data/gtr_rate_tables/
    │
    ├─→ Call ocean_vessel toolset for import analysis
    │   └─→ 02_TOOLSETS/ocean_vessel/src/manifest_processor.py
    │       └─→ Queries Panjiva data: 01_DATA_SOURCES/federal_trade/panjiva_imports/
    │
    ├─→ Load commodity market intelligence
    │   └─→ 03_COMMODITY_MODULES/cement_scm_family/portland_cement/market_intelligence/
    │
    └─→ Apply report template
        └─→ 04_REPORTS/templates/market_report.md
    ↓
OUTPUT: 04_REPORTS/commodity_reports/cement_sesco_2026.docx
```

### Flow 2: Facility Intelligence Query

```
USER REQUEST: "Show me everything about ArcelorMittal Burns Harbor"
    ↓
CLI: report-platform facility-search --name "ArcelorMittal Burns Harbor" --state IN
    ↓
Knowledge Bank API (src/report_platform/knowledge_bank/facility_registry.py)
    ├─→ Query Master Facility Register
    │   └─→ 07_KNOWLEDGE_BANK/master_facility_register/facility_master.duckdb
    │       └─→ Returns facility_master_id="MFR_00012345"
    │
    ├─→ Retrieve external IDs
    │   └─→ EPA FRS: FIN000004359
    │   └─→ Rail SCRS: 045802
    │   └─→ Port UNLOC: USBUR
    │   └─→ EIA Plant: 50000
    │
    ├─→ Aggregate attributes from sources
    │   ├─→ Environmental: Query EPA FRS (01_DATA_SOURCES/federal_environmental/epa_frs/)
    │   ├─→ Rail: Query Rail SCRS (02_TOOLSETS/rail/data/splc_lookup/)
    │   ├─→ Port: Query USACE (01_DATA_SOURCES/federal_waterway/usace_entrance_clearance/)
    │   └─→ Trade: Query Panjiva (01_DATA_SOURCES/federal_trade/panjiva_imports/)
    │
    ├─→ Retrieve geospatial boundaries
    │   └─→ 07_KNOWLEDGE_BANK/master_facility_register/geometries/facility_boundaries.geojson
    │
    └─→ Generate facility profile
        └─→ 07_KNOWLEDGE_BANK/master_facility_register/profiles/MFR_00012345.json
    ↓
OUTPUT: Facility Intelligence Card (HTML + JSON)
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 0: Finalize Architecture (THIS DOCUMENT)
- [ ] Review this proposal with William
- [ ] Finalize data sources organization strategy
- [ ] Approve Knowledge Bank structure
- [ ] Decide implementation priorities

### Phase 1: Knowledge Bank Foundation (2-4 hours)
- [ ] Create `07_KNOWLEDGE_BANK/` directory structure
- [ ] Build `data_sources_catalog.yaml` (centralized registry)
- [ ] Consolidate NAICS codes → `naics_master.yaml`
- [ ] Consolidate HTS codes → `hts_master.yaml`
- [ ] Create `company_master.yaml` from existing ATLAS configs

### Phase 2: Master Facility Register POC (3-4 hours)
- [ ] Create DuckDB schema (`facility_master.duckdb`)
- [ ] Load EPA FRS for cement (NAICS 327310) and steel (331110)
- [ ] Fuzzy match to Rail SCRS data (1-mile buffer + name matching)
- [ ] Fuzzy match to Panjiva consignees (name + location)
- [ ] Generate 25 facility profiles (JSON + HTML)
- [ ] Validate entity resolution accuracy

### Phase 3: Knowledge Bank API (2-3 hours)
- [ ] Build `src/report_platform/knowledge_bank/` package
- [ ] Implement `facility_registry.py` API
- [ ] Implement `reference_data.py` API
- [ ] Implement `competitive_intel.py` API
- [ ] Integrate with CLI: `report-platform facility-search`

### Phase 4: Data Sources Catalog (1-2 hours)
- [ ] Create `01_DATA_SOURCES/data_sources_catalog.yaml`
- [ ] Document all existing data sources
- [ ] Create README files for each data storage location
- [ ] Update `05_DOCUMENTATION/` with data flow diagrams

### Phase 5: Toolset Enhancement (4-6 hours)
- [ ] Update toolsets to query Knowledge Bank for reference data
- [ ] Add commodity-specific adjustment factors
- [ ] Build port development module
- [ ] Build scenario planning engine

### Phase 6: Commodity Module Integration (2-3 hours)
- [ ] Update existing modules to reference Knowledge Bank
- [ ] Remove duplicate NAICS/HTS files (replaced by Knowledge Bank)
- [ ] Add `data_sources.json` to each commodity module
- [ ] Restructure SCM family (cement/slag/fly ash/pozzolans)

---

## ARCHITECTURAL DECISIONS LOG

### Decision 1: Data Sources Organization
**Decision**: Hybrid approach - centralized catalog + distributed storage
**Rationale**: Balances discoverability (one catalog) with logical grouping (storage near use)
**Trade-offs**: Slight complexity vs. full centralization, but much better than pure distribution

### Decision 2: Knowledge Bank as Layer 7
**Decision**: Add Knowledge Bank as new top-level directory (not within toolsets or data sources)
**Rationale**: Cross-cutting concerns deserve dedicated layer; signals architectural importance
**Trade-offs**: Adds directory depth, but clarifies separation of concerns

### Decision 3: Master Facility Register in Knowledge Bank
**Decision**: MFR lives in Knowledge Bank, not as a toolset
**Rationale**: MFR is reference data infrastructure, not an analytical engine
**Trade-offs**: Could argue it's a toolset, but Knowledge Bank emphasizes its foundational role

### Decision 4: NAICS/HTS Centralization
**Decision**: Single `naics_master.yaml` and `hts_master.yaml` in Knowledge Bank
**Rationale**: Eliminates duplication, enables commodity cross-mapping
**Trade-offs**: Commodity modules lose self-contained NAICS files, but gain consistency

### Decision 5: SCM Family Restructure
**Decision**: Group cement/slag/fly ash/pozzolans/aggregates under `cement_scm_family/`
**Rationale**: Reflects real-world market relationships (all serve concrete industry)
**Trade-offs**: Aggregates could be standalone, but limestone-cement linkage justifies inclusion

### Decision 6: Client Intelligence Segmentation
**Decision**: Separate client directories under `client_intelligence/`
**Rationale**: Enables multi-client OceanDatum.ai scaling, prevents data leakage
**Trade-offs**: Adds complexity if only one client (SESCO), but future-proofs architecture

---

## REVIEW QUESTIONS FOR WILLIAM

1. **Data Sources Strategy**: Do you approve the hybrid approach (centralized catalog + distributed storage)? Any changes needed?

2. **Knowledge Bank Scope**: Is the Knowledge Bank scope appropriate, or should it be narrower/broader?

3. **Master Facility Register Priority**: Should MFR be the first implementation priority, or something else?

4. **SCM Family Restructure**: Do you want cement/slag/fly ash/pozzolans grouped, or keep them as separate top-level commodities?

5. **Implementation Pace**: Should I proceed with Phase 1-3 (Knowledge Bank + MFR POC) while you're away, or wait for your review?

6. **Commodity Module Population**: Should I prioritize populating new commodity modules (coal, grain, steel), or finish infrastructure first?

---

**Status**: AWAITING REVIEW
**Next Step**: William approval → Begin Phase 1 implementation
**Author**: Claude Sonnet 4.5
**Date**: 2026-02-23
