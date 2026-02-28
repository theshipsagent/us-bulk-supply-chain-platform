# Migration Checklist — Consolidating Scattered Projects

**Status**: 🟡 In Progress
**Last Updated**: 2026-02-23

---

## Universal Modules Migration

### Priority 1: epa_facility (task_epa_frs → 02_TOOLSETS/epa_facility/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/task_epa_frs/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/epa_facility/`

**Files to Migrate**:
- [ ] `cli.py` → `cli.py` (Click CLI interface)
- [ ] `data/frs.duckdb` → `data/frs.duckdb` (4M+ facilities database)
- [ ] Cement analysis CSVs → Archive or `data/examples/`
- [ ] `ENTITY_HARMONIZATION_GUIDE.md` → Update `METHODOLOGY.md`
- [ ] ETL scripts → `src/etl/`
- [ ] Query/analysis scripts → `src/analyze/`

**Actions**:
1. Copy entire `task_epa_frs/` to `06_ARCHIVE/task_epa_frs_ORIGINAL/`
2. Restructure into new module format
3. Update import paths in CLI
4. Wire into master CLI
5. Test: `report-platform facility search --naics 327310 --state LA`

**Estimated Effort**: 2-3 hours

---

### Priority 2: ocean_vessel (project_manifest + project_manifest_v2 → 02_TOOLSETS/ocean_vessel/)

**Status**: ⬜ Not Started

**Sources**:
- `G:/My Drive/LLM/project_manifest/` (original)
- `G:/My Drive/LLM/project_manifest_v2/` (improved engine)

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/ocean_vessel/`

**Universal Module Files** (move to ocean_vessel):
- [ ] `cargo_flow_analyzer.py` → `src/cargo_flow_analyzer.py`
- [ ] `cargo_matcher.py` → `src/cargo_matcher.py`
- [ ] `DICTIONARIES/` → `data/dictionaries/`
- [ ] `project_manifest_v2/engine/` → `src/engine/`
- [ ] `project_manifest_v2/processors/` → `src/processors/`
- [ ] `project_manifest_v2/METHODOLOGY.md` → `METHODOLOGY.md`

**Commodity-Specific Files** (move to commodity modules):
- [ ] `analyze_grain_flow.py` → `03_COMMODITY_MODULES/grain/supply_chain_models/`
- [ ] `analyze_steel_products_flow.py` → `03_COMMODITY_MODULES/steel_metals/supply_chain_models/`
- [ ] `analyze_pig_iron_flow.py` → `03_COMMODITY_MODULES/steel_metals/supply_chain_models/`
- [ ] `analyze_cement_flow.py` → `03_COMMODITY_MODULES/cement/supply_chain_models/`
- [ ] `analyze_aggregates_flow.py` → `03_COMMODITY_MODULES/aggregates/supply_chain_models/`
- [ ] `analyze_crude_oil_flow.py` → `03_COMMODITY_MODULES/oil_gas/supply_chain_models/`
- [ ] `analyze_fertilizer_flow.py` → `03_COMMODITY_MODULES/fertilizers/supply_chain_models/`
- [ ] `CHEMICALS_DECLINE_ROOT_CAUSE.md` → `03_COMMODITY_MODULES/chemicals/market_intelligence/`

**Actions**:
1. Archive originals to `06_ARCHIVE/`
2. Merge v2 improvements into unified ocean_vessel module
3. Extract commodity-specific logic into commodity modules
4. Refactor to call universal module with commodity parameters
5. Update all import paths

**Estimated Effort**: 6-8 hours

---

### Priority 3: barge_river (project_barge → 02_TOOLSETS/barge_river/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_barge/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/barge_river/`

**Files to Migrate**:
- [ ] `costing_tool/` → `src/` (restructure)
- [ ] Barge cost calculator → `src/rate_engine.py`
- [ ] `dashboard/` → Consider separate dashboard project or `src/visualize/`
- [ ] Build summaries → Update `METHODOLOGY.md`
- [ ] Screenshots → `data/examples/` or archive

**Actions**:
1. Archive to `06_ARCHIVE/project_barge_ORIGINAL/`
2. Extract core cost calculation logic
3. Integrate USDA GTR data
4. Build rate engine API
5. Create CLI commands

**Estimated Effort**: 4-5 hours

---

### Priority 4: rail (project_rail → 02_TOOLSETS/rail/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_rail/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/rail/`

**Files to Migrate**:
- [ ] `00_raw_sources/` → `data/ntad_rail_network/`
- [ ] `01_geospatial/` and `03_geospatial/` → `data/geospatial/`
- [ ] `02_STB/` → `data/stb_data/`
- [ ] Network analysis scripts → `src/network_builder.py`
- [ ] Class I rail knowledge → `METHODOLOGY.md`
- [ ] `CLAUDE.md` → Merge into module README

**Actions**:
1. Archive to `06_ARCHIVE/project_rail_ORIGINAL/`
2. Consolidate NTAD/NARN data
3. Build NetworkX graph construction
4. Integrate STB URCS factors
5. Create routing engine

**Estimated Effort**: 5-6 hours

---

### Priority 5: geospatial (sources_data_maps → 02_TOOLSETS/geospatial/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/sources_data_maps/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/geospatial/`

**Files to Migrate**:
- [ ] `01_geospatial/` → `data/base_layers/`
- [ ] Map building scripts → `src/map_builder.py`
- [ ] Commodity cluster analysis → Move to commodity modules (calls geospatial)
- [ ] Infrastructure deck builder → `src/infrastructure_deck.py`
- [ ] Facility/navigation analysis → `src/spatial_joins.py`

**Actions**:
1. Archive to `06_ARCHIVE/sources_data_maps_ORIGINAL/`
2. Consolidate GIS utilities
3. Separate commodity-specific analysis (move to commodity modules)
4. Create unified map builder API

**Estimated Effort**: 4-5 hours

---

### Priority 6: policy_analysis (project_us_flag → 02_TOOLSETS/policy_analysis/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_us_flag/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/policy_analysis/`

**Files to Migrate**:
- [ ] `main.py` → `src/section_301_model.py`
- [ ] `data/` → `data/` (US flag fleet data)
- [ ] `CLAUDE.md` → Merge into README
- [ ] Research docs → `METHODOLOGY.md`
- [ ] Analysis notebooks → `data/examples/`

**Actions**:
1. Archive to `06_ARCHIVE/project_us_flag_ORIGINAL/`
2. Restructure Section 301 fee calculator
3. Add Jones Act analysis tools
4. Document policy impacts

**Estimated Effort**: 3-4 hours

---

### Priority 7: pipeline (project_pipelines → 02_TOOLSETS/pipeline/)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_pipelines/`

**Target**: `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/pipeline/`

**Files to Migrate**:
- [ ] `01_research/` → `data/` or `METHODOLOGY.md`
- [ ] `02_analysis/` → `src/` (restructure)
- [ ] `03_maps/` → `data/geospatial/` or examples
- [ ] Louisiana pipeline analysis → Example use case in documentation

**Actions**:
1. Archive to `06_ARCHIVE/project_pipelines_ORIGINAL/`
2. Extract general pipeline analysis code
3. Make Louisiana study an example (not hard-coded)
4. Build network graph utilities

**Estimated Effort**: 3-4 hours

---

## Commodity Modules Migration

### Priority 1: Cement (Consolidate within project_master_reporting)

**Status**: ⬜ Not Started

**Sources**:
- `G:/My Drive/LLM/project_master_reporting/aggregate/`
- `G:/My Drive/LLM/project_master_reporting/natural_pozzolan/`
- `G:/My Drive/LLM/project_master_reporting/slag/`
- `G:/My Drive/LLM/project_cement/`
- `G:/My Drive/LLM/project_cement_markets/`
- `G:/My Drive/LLM/project_flyash/`
- `G:/My Drive/LLM/project_sesco/flyash/`
- `task_epa_frs/` cement analysis outputs

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/cement/`

**Actions**:
1. Create comprehensive naics_hts_codes.json:
   - NAICS: 327310 (cement mfg), 327320 (ready-mix), 327331 (block/brick), etc.
   - HTS: 2523.21 (white cement), 2523.29 (other Portland), 2618.00 (slag)

2. Consolidate market intelligence:
   - Tampa Bay cement study → `market_intelligence/florida_market/`
   - SESCO competitive analysis → `market_intelligence/sesco_position/`
   - SCM market ($28B global) → `market_intelligence/scm_markets/`

3. Organize by SCM type:
   - Fly ash content → `market_intelligence/scm_markets/fly_ash/`
   - Slag content → `market_intelligence/scm_markets/slag/`
   - Natural pozzolans → `market_intelligence/scm_markets/natural_pozzolans/`
   - Aggregates → `market_intelligence/scm_markets/aggregates/`

4. Move cement flow analysis from manifest project
5. Document all cement data sources
6. Create example report using universal modules

**Estimated Effort**: 6-8 hours

---

### Priority 2: Grain (New module, consolidate scattered work)

**Status**: ⬜ Not Started

**Sources**:
- `project_manifest/analyze_grain_flow.py`
- `project_master_reporting/01_DATA_SOURCES/federal_waterway/usace_entrance_clearance/02_SCRIPTS/aggregate_fgis_grain_data.py`
- `project_master_reporting/01_DATA_SOURCES/federal_waterway/usace_entrance_clearance/02_SCRIPTS/match_grain_to_clearances.py`
- `project_mrtis/` FGIS grain data

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/grain/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 111150 (corn), 111140 (wheat), 111110 (soybeans), 424510 (wholesalers)
   - HTS: 1001 (wheat), 1005 (corn), 1201 (soybeans)

2. Organize market intelligence:
   - Production regions (Corn Belt, wheat plains)
   - Export terminals (Cargill, ADM, Bunge at Gulf/PNW)
   - Barge routes (Mississippi River grain movements)

3. Move grain-specific analysis scripts
4. Extract universal vessel/barge logic → call modules
5. Document grain data sources (USDA NASS, WASDE, GTR, FGIS)

**Estimated Effort**: 4-5 hours

---

### Priority 3: Steel/Metals (New module, consolidate scattered work)

**Status**: ⬜ Not Started

**Sources**:
- `project_manifest/analyze_pig_iron_flow.py`
- `project_manifest/analyze_steel_products_flow.py`
- `project_gazala_steel/` (if any content)

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/steel_metals/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 331110 (iron/steel), 331313 (alumina), 331410 (copper)
   - HTS: 72xx (steel), 76xx (aluminum), 74xx (copper)

2. Organize by metal type:
   - `market_intelligence/steel/`
   - `market_intelligence/aluminum/`
   - `market_intelligence/copper/`
   - `market_intelligence/pig_iron/`

3. Move steel/pig iron flow analysis
4. Document Great Lakes ore movements
5. Document USGS minerals data sources

**Estimated Effort**: 3-4 hours

---

### Priority 4: Coal (New module, build from knowledge)

**Status**: ⬜ Not Started

**Source**: Industry knowledge (no existing project)

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/coal/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 212100 (coal mining), 221112 (fossil fuel power), 331110 (steel mills)
   - HTS: 2701.11 (anthracite), 2701.12 (bituminous), 2701.19 (other)

2. Document market intelligence:
   - Powder River Basin (PRB) production
   - Appalachian region
   - Export terminals (Hampton Roads, Mobile, NOLA)

3. Create key routes:
   - PRB → power plants (rail unit trains)
   - Appalachia → export (Ohio/Mon river barge)

4. Document EIA coal data sources

**Estimated Effort**: 2-3 hours

---

### Priority 5: Oil & Gas (New module, partial existing work)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_oil_gas/` (minimal content - RBN scraping)

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/oil_gas/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 211120 (crude), 324110 (refining), 325110 (petrochemicals)
   - HTS: 2709 (crude), 27xx (petroleum products)

2. Organize by product type:
   - Crude oil
   - Refined products
   - LNG
   - Petrochemicals

3. Document EIA data sources

**Estimated Effort**: 2-3 hours

---

### Priority 6: Fertilizers (New module, partial existing work)

**Status**: ⬜ Not Started

**Source**: `G:/My Drive/LLM/project_fertilizer/` (appears mostly empty)

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/fertilizers/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 325311 (nitrogenous), 325312 (phosphatic)
   - HTS: 31xx (fertilizers)

2. Organize by type:
   - Nitrogen (ammonia, urea, UAN)
   - Phosphate (DAP, MAP)
   - Potash

3. Move fertilizer flow analysis from manifest project
4. Document USDA, IFA data sources

**Estimated Effort**: 2-3 hours

---

### Priority 7: Chemicals (New module, partial existing work)

**Status**: ⬜ Not Started

**Source**: `project_manifest/CHEMICALS_DECLINE_ROOT_CAUSE.md`

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/chemicals/`

**Actions**:
1. Create naics_hts_codes.json:
   - NAICS: 325xxx (chemical manufacturing)
   - HTS: 28xx, 29xx, 38xx

2. Move chemical decline analysis
3. Document ICIS data sources

**Estimated Effort**: 2-3 hours

---

### Priority 8: Aggregates (New module)

**Status**: ⬜ Not Started

**Source**: `project_manifest/analyze_aggregates_flow.py`

**Target**: `G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES/aggregates/`

**Actions**:
1. Create naics_hts_codes.json
2. Move aggregates flow analysis
3. Document USGS minerals data

**Estimated Effort**: 2-3 hours

---

## Regional Studies Migration

### Port Nickle / Port Sulphur

**Status**: ⬜ Not Started

**Sources**:
- `G:/My Drive/LLM/project_port_nickle/`
- `G:/My Drive/LLM/project_port_sulphur/`

**Target**: `G:/My Drive/LLM/project_master_reporting/01_DATA_SOURCES/regional_studies/plaquemines_parish/`

**Actions**:
1. Archive complete projects
2. Extract reusable economic impact methodology → `02_TOOLSETS/economic/`
3. Keep Port Nickle study as regional case study
4. Reference in documentation

**Estimated Effort**: 2-3 hours

---

## Master CLI Expansion

**Status**: ⬜ Not Started

**Target**: `G:/My Drive/LLM/project_master_reporting/src/report_platform/cli.py`

**Actions**:
1. Create command groups:
   - `barge` (barge-river module commands)
   - `rail` (rail module commands)
   - `facility` (epa_facility module commands)
   - `vessel` (ocean_vessel module commands)
   - `commodity` (commodity operations)

2. Wire module APIs to CLI commands
3. Add help documentation
4. Test all commands

**Estimated Effort**: 4-5 hours

---

## Estimated Total Effort

**Universal Modules**: 25-32 hours
**Commodity Modules**: 20-26 hours
**Documentation & CLI**: 6-8 hours

**Grand Total**: 51-66 hours (~1.5-2 weeks full-time)

---

## Progress Tracking

**Phase 1 Foundation**: ✅ COMPLETE
- ✅ Directory scaffolding created
- ✅ Core documentation written
- ⬜ Master CLI expanded

**Phase 2 Universal Modules**: ⬜ NOT STARTED
**Phase 3 Commodity Modules**: ⬜ NOT STARTED
**Phase 4 Validation**: ⬜ NOT STARTED

---

## Next Immediate Action

**Recommended**: Start with `epa_facility` migration (quickest win, already well-built)

Then: `ocean_vessel` consolidation (most commodity-specific extraction needed)
