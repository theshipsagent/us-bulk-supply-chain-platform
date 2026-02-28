# MIGRATION PLAN — Existing Projects to Unified Architecture
**Date**: 2026-02-23
**Status**: INVENTORY & MAPPING
**Purpose**: Map existing Google Drive projects to new architecture; enable parallel work during transition

---

## EXECUTIVE SUMMARY

**Current State**: 12+ separate project folders on Google Drive, each with 2+ years of work
**Target State**: Unified `project_master_reporting/` architecture with Knowledge Bank
**Strategy**: Build new structure in parallel; migrate content incrementally; keep old folders working

---

## GUIDING PRINCIPLES

### Principle 1: **Non-Disruptive Migration**
- ✅ You can continue working in old folders during migration
- ✅ Old folders remain functional until explicitly migrated
- ✅ No "big bang" cutover - incremental migration by project

### Principle 2: **Read-Only Archive**
- ✅ Old folders copied (not moved) to `06_ARCHIVE/` for historical reference
- ✅ Active work migrated to new structure
- ✅ Archive is permanent snapshot of original state

### Principle 3: **Content Categorization**
Every file in old folders categorized as one of:
- **Data** → `01_DATA_SOURCES/` or `02_TOOLSETS/{toolset}/data/`
- **Code** → `02_TOOLSETS/{toolset}/src/`
- **Research/Writing** → `04_REPORTS/` or `03_COMMODITY_MODULES/{commodity}/`
- **Documentation** → `05_DOCUMENTATION/`
- **Configuration** → Root or relevant module

---

## INVENTORY: EXISTING GOOGLE DRIVE PROJECTS

### Overview Table

| Project Folder | Size Est. | Key Contents | Migration Status | Target Location(s) |
|----------------|-----------|--------------|------------------|-------------------|
| **project_Miss_river/** | Medium | Lower Miss River chapters, navigation data, hydrology, Port Sulphur study | 🟡 Partial | `01_DATA_SOURCES/regional_studies/lower_miss_river/`, `04_REPORTS/` |
| **project_barge/** | Large | GTR rates, lock data, barge fleet, USDA data, forecasting models | 🟢 Active | `02_TOOLSETS/barge_cost_model/` (exists), migrate to `barge_river/` later |
| **project_cement_markets/** | Large | Cement analysis, SCM data, tariffs, SESCO intel | 🟢 Active | `03_COMMODITY_MODULES/cement/` (exists) |
| **project_rail/** | Large | NTAD shapefiles, STB URCS, NetworkX routing, rail cost model | 🟢 Active | `02_TOOLSETS/rail_cost_model/` (exists), migrate to `rail/` later |
| **project_pipelines/** | Small | Pipeline route data, terminal locations | 🔴 Not Started | `01_DATA_SOURCES/geospatial/pipeline_layers/` |
| **project_us_flag/** | Medium | Section 301, Jones Act, US flag fleet, legal analysis | 🟢 Active | `02_TOOLSETS/policy_analysis/` (exists) |
| **project_manifest/** | Large | Panjiva 800K records, data dictionary, column lineage, vessel tracking | 🟢 Active | `02_TOOLSETS/vessel_intelligence/` (exists) |
| **task_epa_frs/** | Large | DuckDB (732MB), Python ETL, NAICS lookups, facility queries | 🟢 Active | `02_TOOLSETS/facility_registry/` (exists) |
| **task_usace_entrance_clearance/** | Medium | USACE vessel entrance/clearance records | 🔴 Not Started | `01_DATA_SOURCES/federal_waterway/usace_entrance_clearance/` |
| **project_mrtis/** | Medium | MRTIS waterborne commerce exports | 🔴 Not Started | `01_DATA_SOURCES/federal_waterway/mrtis/` |
| **project_port_nickle/** | Medium | Plaquemines Parish 11-chapter study, Port Sulphur economics | 🔴 Not Started | `01_DATA_SOURCES/regional_studies/plaquemines_parish/`, `04_REPORTS/` |
| **sources_data_maps/** | Large | GIS layers, shapefiles, base maps, ArcGIS data | 🔴 Not Started | `01_DATA_SOURCES/geospatial/` (distribute to sublayers) |
| **project_master_reporting/** | Growing | NEW unified platform (current work location) | 🟢 Active | — (this IS the target) |

**Legend**:
- 🟢 **Active**: Already migrated or actively being worked in new structure
- 🟡 **Partial**: Some content migrated, some still in old folder
- 🔴 **Not Started**: Old folder untouched, content not yet migrated

---

## DETAILED PROJECT INVENTORY

### 1. **project_Miss_river/** → Multiple Destinations

**Contents**:
- Chapter drafts on Lower Mississippi River system (hydrology, navigation, port facilities)
- River mile marker data
- Navigation charts and USACE data
- Port Sulphur infrastructure research
- Hydrological data (flows, stages, gauge readings)

**Migration Map**:
```
project_Miss_river/
├── chapters/                          → 04_REPORTS/us_bulk_supply_chain/01_mississippi_river_system.md
├── data/
│   ├── river_miles/                   → 07_KNOWLEDGE_BANK/reference_data/river_mile_markers.yaml
│   ├── navigation_charts/             → 01_DATA_SOURCES/federal_waterway/usace_hydro_navigation/
│   ├── hydrology/                     → 01_DATA_SOURCES/federal_waterway/hydrology/
│   └── port_sulphur_study/            → 01_DATA_SOURCES/regional_studies/lower_miss_river/port_sulphur/
├── research/                          → 05_DOCUMENTATION/research_notes/
└── maps/                              → 01_DATA_SOURCES/geospatial/waterway_layers/
```

**Current Status**: 🟡 Partial
- Chapter content not yet migrated
- Data still in original folder
- Can continue working here until ready to migrate

**Dependencies**: None - standalone research

---

### 2. **project_barge/** → `02_TOOLSETS/barge_cost_model/` (ALREADY EXISTS)

**Contents**:
- USDA GTR rate data (historical + current)
- Lock performance data (LPMS)
- Barge fleet statistics
- Freight rate analysis scripts
- Forecasting models (VAR, Prophet)

**Migration Map**:
```
project_barge/
├── data/
│   ├── usda_gtr/                      → 02_TOOLSETS/barge_cost_model/data/gtr_rate_tables/
│   ├── lock_performance/              → 02_TOOLSETS/barge_cost_model/data/lock_delays/
│   └── fleet_stats/                   → 02_TOOLSETS/barge_cost_model/data/fleet_utilization/
├── scripts/
│   ├── rate_analysis.py               → 02_TOOLSETS/barge_cost_model/src/rate_engine.py
│   ├── transit_calculator.py          → 02_TOOLSETS/barge_cost_model/src/transit_calculator.py
│   └── forecasting/                   → 02_TOOLSETS/barge_cost_model/forecasting/
└── research/                          → 02_TOOLSETS/barge_cost_model/METHODOLOGY.md
```

**Current Status**: 🟢 Active
- **Already migrated** to `02_TOOLSETS/barge_cost_model/`
- Toolset exists and working
- Old folder can be archived

**Future Step**: When ready, rename `barge_cost_model/` → `barge_river/` per new architecture

---

### 3. **project_cement_markets/** → `03_COMMODITY_MODULES/cement/` (ALREADY EXISTS)

**Contents**:
- Cement market analysis
- SCM market data (slag, fly ash, pozzolans)
- Tariff analysis
- SESCO competitive intelligence
- Import/export trade flows

**Migration Map**:
```
project_cement_markets/
├── market_analysis/                   → 03_COMMODITY_MODULES/cement/market_intelligence/
├── scm_data/                          → 03_COMMODITY_MODULES/cement/market_intelligence/scm_markets/
├── tariffs/                           → 03_COMMODITY_MODULES/cement/market_intelligence/trade_flows/tariff_structure.json
├── sesco/                             → 07_KNOWLEDGE_BANK/client_intelligence/sesco/
└── trade_flows/                       → 03_COMMODITY_MODULES/cement/market_intelligence/trade_flows/
```

**Current Status**: 🟢 Active
- **Already migrated** to `03_COMMODITY_MODULES/cement/`
- Four SCM dossiers completed (slag, fly ash, aggregates, natural pozzolans)
- Old folder can be archived

---

### 4. **project_rail/** → `02_TOOLSETS/rail_cost_model/` (ALREADY EXISTS)

**Contents**:
- NTAD/NARN rail network shapefiles
- STB URCS cost tables
- NetworkX routing scripts
- Rail cost modeling code

**Migration Map**:
```
project_rail/
├── data/
│   ├── ntad_shapefiles/               → 02_TOOLSETS/rail_cost_model/data/ntad_network/
│   ├── urcs_tables/                   → 02_TOOLSETS/rail_cost_model/data/urcs_cost_tables/
│   └── splc_codes/                    → 07_KNOWLEDGE_BANK/reference_data/splc_codes.yaml
├── scripts/
│   ├── network_builder.py             → 02_TOOLSETS/rail_cost_model/src/network_builder.py
│   ├── route_engine.py                → 02_TOOLSETS/rail_cost_model/src/route_engine.py
│   └── urcs_costing.py                → 02_TOOLSETS/rail_cost_model/src/urcs_costing.py
└── research/                          → 02_TOOLSETS/rail_cost_model/METHODOLOGY.md
```

**Current Status**: 🟢 Active
- **Already migrated** to `02_TOOLSETS/rail_cost_model/`
- Toolset exists and working
- Old folder can be archived

**Future Step**: When ready, rename `rail_cost_model/` → `rail/` per new architecture

---

### 5. **project_pipelines/** → `01_DATA_SOURCES/geospatial/pipeline_layers/`

**Contents**:
- Pipeline route shapefiles
- Terminal location data
- Pipeline capacity/throughput data

**Migration Map**:
```
project_pipelines/
├── routes/                            → 01_DATA_SOURCES/geospatial/pipeline_layers/routes/
├── terminals/                         → 01_DATA_SOURCES/geospatial/pipeline_layers/terminals/
└── capacity_data/                     → 01_DATA_SOURCES/geospatial/pipeline_layers/capacity/
```

**Current Status**: 🔴 Not Started
- Content still in original folder
- **YOU CAN CONTINUE WORKING HERE** until ready to migrate
- No rush - pipelines not critical path

---

### 6. **project_us_flag/** → `02_TOOLSETS/policy_analysis/` (ALREADY EXISTS)

**Contents**:
- Section 301 Chinese shipping fee analysis
- Jones Act cabotage law research
- US flag fleet data (MARAD)
- Maritime policy white papers

**Migration Map**:
```
project_us_flag/
├── section_301/                       → 02_TOOLSETS/policy_analysis/src/section_301_model.py
│                                      → 02_TOOLSETS/policy_analysis/data/section_301_fee_schedule.json
├── jones_act/                         → 02_TOOLSETS/policy_analysis/src/jones_act_analyzer.py
│                                      → 07_KNOWLEDGE_BANK/market_intelligence_commons/policy_briefs/jones_act_analysis.md
├── us_flag_fleet/                     → 01_DATA_SOURCES/federal_vessel/marad_fleet/
└── research/                          → 02_TOOLSETS/policy_analysis/research/
```

**Current Status**: 🟢 Active
- **Already migrated** to `02_TOOLSETS/policy_analysis/`
- Toolset exists and working
- Old folder can be archived

---

### 7. **project_manifest/** → `02_TOOLSETS/vessel_intelligence/` (ALREADY EXISTS)

**Contents**:
- Panjiva import records (800K+ records, 4.5 GB)
- Master data dictionary (column lineage, grid references)
- Vessel tracking analysis
- HTS code lookups

**Migration Map**:
```
project_manifest/
├── panjiva_data/                      → 01_DATA_SOURCES/federal_trade/panjiva_imports/
├── data_dictionary/
│   ├── master_data_dictionary.csv     → 05_DOCUMENTATION/data_dictionary/MASTER_DATA_DICTIONARY.csv
│   ├── grid_reference_lookup.csv      → 05_DOCUMENTATION/data_dictionary/GRID_REFERENCE_LOOKUP.csv
│   └── transformation_rules.csv       → 05_DOCUMENTATION/data_dictionary/TRANSFORMATION_RULES.csv
├── scripts/
│   ├── manifest_processor.py          → 02_TOOLSETS/vessel_intelligence/src/manifest_processor.py
│   ├── voyage_tracker.py              → 02_TOOLSETS/vessel_intelligence/src/voyage_tracker.py
│   └── entity_resolver.py             → 02_TOOLSETS/vessel_intelligence/src/entity_resolver.py
└── hts_codes/                         → 02_TOOLSETS/vessel_intelligence/data/hs_codes/
                                       → 07_KNOWLEDGE_BANK/reference_data/hts_master.yaml (consolidated)
```

**Current Status**: 🟢 Active
- **Already migrated** to `02_TOOLSETS/vessel_intelligence/`
- Data dictionary migrated to `05_DOCUMENTATION/data_dictionary/`
- Old folder can be archived

**Future Step**: When ready, rename `vessel_intelligence/` → `ocean_vessel/` per new architecture

---

### 8. **task_epa_frs/** → `02_TOOLSETS/facility_registry/` (ALREADY EXISTS)

**Contents**:
- EPA FRS national database (DuckDB, 732 MB, 4M+ facilities)
- Python ETL scripts (download, ingest, query)
- NAICS lookups
- Entity resolution patterns (company name fuzzy matching)

**Migration Map**:
```
task_epa_frs/
├── data/
│   ├── frs.duckdb                     → 02_TOOLSETS/facility_registry/data/frs.duckdb
│   └── state_downloads/               → 01_DATA_SOURCES/federal_environmental/epa_frs/
├── scripts/
│   ├── etl/
│   │   ├── download.py                → 02_TOOLSETS/facility_registry/src/etl/download.py
│   │   └── ingest.py                  → 02_TOOLSETS/facility_registry/src/etl/ingest.py
│   ├── analyze/
│   │   ├── query_engine.py            → 02_TOOLSETS/facility_registry/src/analyze/query_engine.py
│   │   └── entity_resolver.py         → 02_TOOLSETS/facility_registry/src/analyze/entity_resolver.py
│   └── visualize/
│       └── facility_maps.py           → 02_TOOLSETS/facility_registry/src/visualize/facility_maps.py
├── config/
│   └── parent_mapping.json            → 07_KNOWLEDGE_BANK/competitive_intelligence/company_master.yaml (consolidated)
└── cli.py                             → 02_TOOLSETS/facility_registry/cli.py
```

**Current Status**: 🟢 Active
- **Already migrated** to `02_TOOLSETS/facility_registry/`
- DuckDB working
- Old folder can be archived

**Future Step**:
- When ready, rename `facility_registry/` → `epa_facility/` per new architecture
- Feed into Master Facility Register as primary seed data

---

### 9. **task_usace_entrance_clearance/** → `01_DATA_SOURCES/federal_waterway/`

**Contents**:
- USACE vessel entrance/clearance records
- Vessel call data (by port, date, vessel characteristics)

**Migration Map**:
```
task_usace_entrance_clearance/
├── data/                              → 01_DATA_SOURCES/federal_waterway/usace_entrance_clearance/
└── scripts/                           → 02_TOOLSETS/ocean_vessel/src/ (vessel call analysis)
```

**Current Status**: 🔴 Not Started
- Content still in original folder
- **YOU CAN CONTINUE WORKING HERE** until ready to migrate

---

### 10. **project_mrtis/** → `01_DATA_SOURCES/federal_waterway/mrtis/`

**Contents**:
- USACE Marine Transportation Information System exports
- Waterborne commerce statistics
- Tonnage by commodity, by waterway segment, by port

**Migration Map**:
```
project_mrtis/
├── data/                              → 01_DATA_SOURCES/federal_waterway/mrtis/
└── analysis/                          → 02_TOOLSETS/barge_river/src/ (commodity flow analysis)
```

**Current Status**: 🔴 Not Started
- Content still in original folder
- **YOU CAN CONTINUE WORKING HERE** until ready to migrate

---

### 11. **project_port_nickle/** → Multiple Destinations

**Contents**:
- Plaquemines Parish 11-chapter research report
- Port Sulphur economic analysis
- Port development feasibility study

**Migration Map**:
```
project_port_nickle/
├── report_chapters/                   → 04_REPORTS/regional_studies/plaquemines_parish/
├── economic_analysis/                 → 01_DATA_SOURCES/regional_studies/plaquemines_parish/
├── data/                              → 01_DATA_SOURCES/regional_studies/plaquemines_parish/data/
└── methodology/                       → 02_TOOLSETS/port_development/ (extract reusable patterns)
```

**Current Status**: 🔴 Not Started
- Content still in original folder
- **YOU CAN CONTINUE WORKING HERE** until ready to migrate
- Port development patterns can seed new `port_development/` toolset

---

### 12. **sources_data_maps/** → `01_DATA_SOURCES/geospatial/` (LARGE, COMPLEX)

**Contents**:
- GIS layers (shapefiles, GeoJSON)
- Base maps (state boundaries, counties, metro areas)
- Waterway centerlines, lock locations
- Rail network layers
- Port boundary layers
- ArcGIS project files

**Migration Map** (distribute by layer type):
```
sources_data_maps/
├── base_layers/                       → 01_DATA_SOURCES/geospatial/base_layers/
├── waterway_layers/                   → 01_DATA_SOURCES/geospatial/waterway_layers/
├── rail_layers/                       → 01_DATA_SOURCES/geospatial/rail_layers/
├── pipeline_layers/                   → 01_DATA_SOURCES/geospatial/pipeline_layers/
├── port_layers/                       → 01_DATA_SOURCES/geospatial/port_layers/
└── facility_layers/                   → 01_DATA_SOURCES/geospatial/facility_layers/
```

**Current Status**: 🔴 Not Started
- Content still in original folder
- **YOU CAN CONTINUE WORKING HERE** until ready to migrate
- Large data volume - migrate in phases by layer type

---

## MIGRATION STRATEGY

### Phase 1: **Already Done** ✅
The following projects are already migrated and working:
- ✅ `project_barge/` → `02_TOOLSETS/barge_cost_model/`
- ✅ `project_rail/` → `02_TOOLSETS/rail_cost_model/`
- ✅ `project_cement_markets/` → `03_COMMODITY_MODULES/cement/`
- ✅ `project_us_flag/` → `02_TOOLSETS/policy_analysis/`
- ✅ `project_manifest/` → `02_TOOLSETS/vessel_intelligence/`
- ✅ `task_epa_frs/` → `02_TOOLSETS/facility_registry/`

### Phase 2: **Build Infrastructure** (Do Next)
Before migrating remaining projects, build the new architecture:
1. Create `07_KNOWLEDGE_BANK/` structure
2. Build Master Facility Register
3. Create `data_sources_catalog.yaml`
4. Centralize NAICS/HTS codes → Knowledge Bank

### Phase 3: **Migrate Data-Heavy Projects** (When Infrastructure Ready)
- `sources_data_maps/` → `01_DATA_SOURCES/geospatial/` (large, many files)
- `project_mrtis/` → `01_DATA_SOURCES/federal_waterway/mrtis/`
- `task_usace_entrance_clearance/` → `01_DATA_SOURCES/federal_waterway/`

### Phase 4: **Migrate Research Projects** (Low Priority)
- `project_Miss_river/` → `04_REPORTS/` + `01_DATA_SOURCES/regional_studies/`
- `project_port_nickle/` → `04_REPORTS/` + `01_DATA_SOURCES/regional_studies/`
- `project_pipelines/` → `01_DATA_SOURCES/geospatial/pipeline_layers/`

### Phase 5: **Archive Old Folders**
Once content is fully migrated and validated:
1. Copy (not move) old folder to `06_ARCHIVE/[project_name]_ORIGINAL/`
2. Add README to archive explaining what was migrated where
3. Keep archive read-only for historical reference
4. Optionally delete original Google Drive folder (but archive is permanent backup)

---

## PARALLEL WORK STRATEGY

### **YES, You Can Continue Working in Old Folders!**

**Safe to keep working in**:
- ✅ `project_pipelines/` - not yet migrated
- ✅ `task_usace_entrance_clearance/` - not yet migrated
- ✅ `project_mrtis/` - not yet migrated
- ✅ `project_port_nickle/` - not yet migrated
- ✅ `sources_data_maps/` - not yet migrated
- ✅ `project_Miss_river/` - partially migrated, can still work on chapters

**Transition to new structure** (already migrated, use new location):
- 🔄 `project_barge/` → work in `02_TOOLSETS/barge_cost_model/` instead
- 🔄 `project_rail/` → work in `02_TOOLSETS/rail_cost_model/` instead
- 🔄 `project_cement_markets/` → work in `03_COMMODITY_MODULES/cement/` instead
- 🔄 `task_epa_frs/` → work in `02_TOOLSETS/facility_registry/` instead

### **Migration Workflow for Active Projects**

When you're ready to migrate a project:

1. **Copy (don't move)** entire folder to `06_ARCHIVE/[project_name]_ORIGINAL/`
2. **Categorize** files (data, code, research, docs)
3. **Move** files to new locations per migration map above
4. **Update** any hardcoded paths in scripts
5. **Test** that everything still works in new location
6. **Document** migration in `06_ARCHIVE/[project_name]_ORIGINAL/MIGRATION_LOG.md`
7. **Continue working** in new location
8. **Optionally delete** original Google Drive folder (archive is backup)

---

## NEXT STEPS

### Immediate (This Session):
1. ✅ Review this migration plan
2. ✅ Confirm you can keep working in old folders during transition
3. ✅ Decide: Build Knowledge Bank infrastructure first, or migrate data-heavy projects first?

### Short-Term (Next 1-2 Weeks):
1. Build `07_KNOWLEDGE_BANK/` structure
2. Create `01_DATA_SOURCES/data_sources_catalog.yaml`
3. Migrate one small project as pilot (e.g., `project_pipelines/`)
4. Validate migration workflow

### Medium-Term (Next Month):
1. Migrate data-heavy projects (`sources_data_maps/`, `project_mrtis/`)
2. Feed EPA FRS + Panjiva into Master Facility Register
3. Migrate research projects (`project_Miss_river/`, `project_port_nickle/`)
4. Archive old folders

---

## MIGRATION DECISION MATRIX

| Project | Size | Complexity | Priority | Can Wait? | Work in Old Folder? |
|---------|------|------------|----------|-----------|---------------------|
| project_Miss_river | Medium | Low | Medium | ✅ Yes | ✅ Yes |
| project_barge | — | — | — | Already migrated | Use new location |
| project_cement_markets | — | — | — | Already migrated | Use new location |
| project_rail | — | — | — | Already migrated | Use new location |
| project_pipelines | Small | Low | Low | ✅ Yes | ✅ Yes |
| project_us_flag | — | — | — | Already migrated | Use new location |
| project_manifest | — | — | — | Already migrated | Use new location |
| task_epa_frs | — | — | — | Already migrated | Use new location |
| task_usace_entrance_clearance | Medium | Low | Medium | ✅ Yes | ✅ Yes |
| project_mrtis | Medium | Low | Medium | ✅ Yes | ✅ Yes |
| project_port_nickle | Medium | Low | Low | ✅ Yes | ✅ Yes |
| sources_data_maps | Large | High | High | ⚠️ Migrate Soon | ✅ Yes for now |

---

## QUESTIONS FOR WILLIAM

1. **Which projects are you actively working in?** (So we prioritize those last)
2. **Are any old projects completely dormant?** (Can archive immediately)
3. **Data-heavy migration timing**: Should we migrate `sources_data_maps/` soon, or wait until Knowledge Bank is built?
4. **Acceptable parallel work period**: How long do you want to work in old folders before forcing migration? (1 month? 3 months? No rush?)

---

**Status**: READY FOR REVIEW
**Decision Needed**: Prioritize infrastructure build vs. data migration
**Author**: Claude Sonnet 4.5
**Date**: 2026-02-23
