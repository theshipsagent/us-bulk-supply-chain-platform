# Directory Structure — US Bulk Supply Chain Reporting Platform

**Last Updated:** 2026-02-24
**Reference:** See CLAUDE.md for high-level structure

This document provides the complete directory tree with descriptions, file counts, and sizes.

---

## Complete Directory Tree

```
G:\My Drive\LLM\project_master_reporting\
│
├── CLAUDE.md                          ← Project directives (condensed, ~250 lines)
├── README.md                          ← Project overview, quickstart, architecture diagram
├── config.yaml                        ← Global configuration (API endpoints, paths, credentials)
├── requirements.txt                   ← Python dependencies (consolidated)
├── package.json                       ← Node.js dependencies (for visualization)
│
├── 01_DATA_SOURCES/                   ← Raw data ingestion layer
│   ├── README.md                      ← Data catalog: every source, URL, format, refresh cadence
│   │
│   ├── federal_waterway/              ← USACE waterborne commerce & navigation
│   │   ├── wcsc_waterborne_commerce/  ← Waterborne Commerce Statistics Center data
│   │   ├── mrtis/                     ← Marine Transportation Information System ✅
│   │   │   ├── source_files/          ← 36 CSV files (Zone Reports 2018-2026, 318K records)
│   │   │   ├── results_clean/         ← Processed voyage data (41,156 voyages)
│   │   │   └── VERIFICATION_REPORT.md ← 86% migration complete
│   │   ├── fgis_grain_inspection/     ← USDA FGIS grain inspection system ✅
│   │   │   └── fgis/                  ← 438 MB grain database
│   │   │       ├── fgis_export_grain.duckdb  ← 101 MB grain database
│   │   │       ├── grain_report.csv          ← 32 MB grain analysis output
│   │   │       ├── raw_data/                 ← ~300 MB CY1983-present
│   │   │       ├── build_database.py         ← ETL from CSV to DuckDB
│   │   │       ├── build_grain_report.py     ← Grain reporting pipeline
│   │   │       └── grain_matcher.py          ← Match grain to vessel voyages
│   │   ├── ndc_lock_performance/      ← Navigation Data Center lock stats (LPMS)
│   │   ├── usace_entrance_clearance/  ← Vessel entrance/clearance records ✅
│   │   │   └── VERIFICATION_REPORT.md ← 93% migration complete
│   │   └── usace_hydro_navigation/    ← Hydrographic surveys, navigation charts, mile markers
│   │
│   ├── federal_rail/                  ← Surface Transportation Board & DOT
│   │   ├── stb_economic_data/         ← STB carload waybill, URCS cost tables
│   │   ├── ntad_rail_network/         ← NARN lines and nodes (ArcGIS shapefiles/GeoJSON)
│   │   ├── scrs_facility_data/        ← State Customs Records rail-served facilities ✅
│   │   │   ├── raw/                   ← 541 files from 8 states (AL, DE, FL, GA, LA, MD, MS, NC)
│   │   │   └── processed/
│   │   │       ├── scrs_consolidated_master.csv    ← 39,936 rail-served facilities
│   │   │       ├── scrs_bulk_commodities_only.csv  ← 8,555 bulk facilities
│   │   │       └── scrs_parent_company_lookup.csv  ← 42 companies
│   │   └── fra_safety_data/           ← FRA crossing and safety databases
│   │
│   ├── federal_environmental/         ← EPA data
│   │   ├── epa_frs/                   ← Facility Registry System (national CSV, DuckDB)
│   │   ├── epa_echo/                  ← ECHO compliance data
│   │   └── naics_sic_lookups/         ← Industry classification reference tables
│   │
│   ├── federal_trade/                 ← Trade and customs data
│   │   ├── panjiva_imports/           ← Panjiva/S&P Global import records (800K+ records)
│   │   ├── census_trade/              ← Census Bureau trade statistics
│   │   ├── usitc_tariff/             ← USITC tariff schedule, HTS codes
│   │   └── cbp_entry_data/           ← CBP entry summary data (if available)
│   │
│   ├── federal_vessel/                ← Vessel and fleet data
│   │   ├── marad_fleet/              ← MARAD US flag fleet registry
│   │   ├── uscg_psix/               ← USCG Port State Info Exchange
│   │   ├── ships_register/           ← Commercial vessel registry ✅
│   │   │   └── ships_register_012926_1530/
│   │   │       └── 01_ships_register.csv  ← 52,034 vessels with DWT, TPC, draft, type
│   │   └── wcsc_vessel_chars/        ← USACE vessel characteristics database
│   │
│   ├── market_data/                   ← Industry and market intelligence
│   │   ├── usda_gtr/                 ← Grain Transportation Report (barge rate benchmarks)
│   │   ├── usgs_minerals/            ← USGS Mineral Commodity Summaries (cement, aggregates)
│   │   ├── pca_cement/               ← Portland Cement Association data
│   │   └── eia_energy/               ← EIA energy data (fuel costs for transport modeling)
│   │
│   ├── geospatial/                    ← GIS and mapping source data
│   │   ├── base_layers/              ← State boundaries, counties, metro areas
│   │   ├── waterway_layers/          ← River centerlines, mile markers, lock locations
│   │   ├── rail_layers/              ← Rail network, yard locations, intermodal terminals ✅
│   │   │   ├── bulk_facilities_interactive.html  ← Interactive facility maps
│   │   │   ├── create_bulk_facilities_visualizations.py
│   │   │   ├── create_qgis_project.py           ← QGIS project automation
│   │   │   ├── geocode_scrs_census.py           ← Geocoding tool for SCRS
│   │   │   ├── geocoding_checkpoint_*.csv       ← 39,936 facilities geocoded
│   │   │   └── EXECUTIVE_SUMMARY.md             ← GIS analysis documentation
│   │   │       # Coverage: 112 files, 976 MB geospatial data
│   │   ├── pipeline_layers/          ← Pipeline routes and terminals
│   │   ├── port_layers/              ← Port boundaries, terminal locations, berths
│   │   └── facility_layers/          ← EPA FRS facility points, industrial sites
│   │
│   └── regional_studies/              ← Location-specific research
│       ├── lower_miss_river/          ← Baton Rouge to Gulf passes
│       ├── plaquemines_parish/        ← Port Sulphur study
│       └── houston_galveston/         ← Houston Ship Channel context
│
├── 02_TOOLSETS/                       ← Reusable analysis engines (commodity-agnostic)
│   ├── README.md                      ← Toolset catalog, usage examples
│   │
│   ├── barge_cost_model/              ← Inland waterway freight cost calculator ✅ OPERATIONAL
│   │   ├── src/
│   │   │   ├── engines/
│   │   │   │   ├── routing_engine.py  ← NetworkX graph routing (Dijkstra, A*)
│   │   │   │   └── cost_engine.py     ← Multi-component cost calculator
│   │   │   ├── models/                ← Data models (route, waterway, vessel, cargo)
│   │   │   ├── data_loaders/          ← ETL pipelines (waterways, locks, docks, vessels)
│   │   │   ├── api/                   ← FastAPI REST endpoints (4 routers)
│   │   │   ├── dashboard/             ← Streamlit UI (3 pages)
│   │   │   ├── config/                ← Settings & database config
│   │   │   └── utils/                 ← Logging & validation
│   │   ├── data/
│   │   │   └── waterway_graph.pkl     ← NetworkX graph cache (6,860 nodes)
│   │   ├── cargo_flow/                ← Cargo flow analyzer
│   │   ├── enterprise/                ← API authentication
│   │   ├── forecasting/               ← VAR/SpVAR rate forecasting (5 scripts)
│   │   ├── tests/                     ← test_engines.py, test_loaders.py
│   │   ├── README.md                  ← 1,337-line comprehensive guide
│   │   ├── METHODOLOGY.md             ← 223-line white paper (USDA GTR, VAR/SpVAR)
│   │   └── MIGRATION_SUMMARY.md       ← 425-line migration log
│   │
│   ├── rail_cost_model/               ← Railroad freight cost calculator ✅ OPERATIONAL
│   │   ├── src/
│   │   │   ├── network_builder.py     ← NTAD/NARN graph construction (NetworkX)
│   │   │   ├── route_engine.py        ← Shortest path / cost-optimized routing
│   │   │   ├── urcs_costing.py        ← URCS variable cost calculator
│   │   │   ├── class_i_tariffs.py     ← Published tariff rate lookups
│   │   │   └── intermodal_transfer.py ← Rail-to-barge, rail-to-truck transfer costs
│   │   ├── data/
│   │   │   └── reference/
│   │   │       └── stb_rates/         ← STB rate database (747 files, 862 MB)
│   │   │           ├── stb_contracts.db    ← DuckDB with 10,340 UP contracts
│   │   │           ├── scrape_stb_up.py    ← STB scraper tool
│   │   │           └── parse_acs_pdf.py    ← PDF parser
│   │   ├── tests/
│   │   └── METHODOLOGY.md
│   │
│   ├── port_cost_model/               ← Port/terminal cost estimator ⏳ PARTIAL
│   │   ├── src/
│   │   │   ├── port_tariff_engine.py  ← Port authority tariff calculators
│   │   │   ├── pilotage_calculator.py ← Mississippi River pilotage
│   │   │   ├── towage_calculator.py   ← Tug/towage rate estimation
│   │   │   ├── stevedoring_model.py   ← Cargo handling cost estimation
│   │   │   └── proforma_generator.py  ← Full proforma port cost estimate builder
│   │   ├── data/                      ← Tariff PDFs, rate cards, fee schedules
│   │   └── METHODOLOGY.md
│   │
│   ├── port_economic_impact/          ← Regional economic impact modeling ⏳ PLANNED
│   │   ├── src/
│   │   │   ├── multiplier_engine.py   ← RIMS II / IMPLAN multiplier application
│   │   │   ├── employment_model.py    ← Direct/indirect/induced employment
│   │   │   ├── revenue_model.py       ← Tax revenue and fiscal impact
│   │   │   └── scenario_builder.py    ← What-if scenario comparison tool
│   │   └── METHODOLOGY.md
│   │
│   ├── vessel_intelligence/           ← Maritime cargo classification ✅ OPERATIONAL
│   │   ├── src/
│   │   │   ├── pipeline/              ← 8-phase classification pipeline
│   │   │   │   ├── phase_00_preprocessing.py
│   │   │   │   ├── phase_01_white_noise.py
│   │   │   │   ├── phase_02_carrier_exclusions.py
│   │   │   │   ├── phase_03_carrier_classification.py
│   │   │   │   ├── phase_04_main_classification.py  ← 5,000+ keyword rules
│   │   │   │   ├── phase_05_hs4_alignment.py
│   │   │   │   ├── phase_06_catchall.py
│   │   │   │   └── phase_07_enrichment.py
│   │   │   ├── analysis/              ← Commodity flow analyzers (14 scripts)
│   │   │   └── manifest_processor.py
│   │   ├── data/
│   │   │   ├── cargo_classification.csv        ← 5,000+ keywords
│   │   │   ├── ships_register.csv              ← 5.4 MB vessel registry
│   │   │   └── master_data_dictionary.csv
│   │   └── METHODOLOGY.md             ← 13,000-word classification white paper
│   │
│   ├── rail_intelligence/             ← Railroad knowledge bank ✅ OPERATIONAL
│   │   ├── knowledge_bank/
│   │   │   ├── BNSF/                  ← Burlington Northern Santa Fe
│   │   │   ├── UP/                    ← Union Pacific
│   │   │   ├── CSX/                   ← CSX Transportation
│   │   │   ├── NS/                    ← Norfolk Southern
│   │   │   ├── CN/                    ← Canadian National
│   │   │   ├── CPKC/                  ← Canadian Pacific Kansas City
│   │   │   ├── shortlines/
│   │   │   │   ├── Watco/             ← 38 railroads
│   │   │   │   └── GW/                ← 33 railroads
│   │   │   ├── summary_report.html
│   │   │   ├── watco_master.csv
│   │   │   └── gw_master.csv
│   │   └── README.md
│   │
│   ├── vessel_voyage_analysis/        ← Maritime voyage analysis ✅ OPERATIONAL
│   │   ├── src/
│   │   │   ├── models/                ← Event, Voyage, VoyageSegment, QualityIssue
│   │   │   ├── data/                  ← Loaders, preprocessors, lookups
│   │   │   ├── processing/            ← Voyage detector, segmenter, quality analyzer
│   │   │   └── output/                ← CSV writer, report writer
│   │   ├── voyage_analyzer.py         ← Main CLI
│   │   ├── terminal_zone_dictionary.csv  ← 217 zones
│   │   ├── ships_register_dictionary.csv ← 52K vessels
│   │   ├── results_phase2_full/       ← 95 MB production output
│   │   └── README.md + 30 markdown docs
│   │
│   ├── facility_registry/             ← EPA FRS geospatial analysis ✅ OPERATIONAL
│   │   ├── src/
│   │   │   ├── etl/                   ← Download, ingest to DuckDB
│   │   │   ├── analyze/               ← Query engine, entity resolver, spatial analysis
│   │   │   └── visualize/             ← Folium interactive maps
│   │   ├── data/
│   │   │   ├── frs.duckdb            ← 4M+ facilities
│   │   │   └── parent_mapping.json
│   │   ├── cli.py
│   │   └── METHODOLOGY.md
│   │
│   ├── geospatial_engine/             ← Shared GIS utilities ⏳ PLANNED
│   │   ├── src/
│   │   │   ├── map_builder.py
│   │   │   ├── layer_manager.py
│   │   │   ├── spatial_joins.py
│   │   │   └── export_utils.py
│   │   └── data/
│   │       └── projections.json
│   │
│   └── policy_analysis/               ← Maritime policy & regulatory tools ⏳ PARTIAL
│       ├── src/
│       │   ├── section_301_model.py   ← Chinese shipping fee impact
│       │   ├── jones_act_analyzer.py  ← Cabotage/US flag fleet
│       │   ├── tariff_impact.py
│       │   └── regulatory_tracker.py
│       ├── data/
│       │   ├── section_301_fee_schedule.json
│       │   └── hts_cement_tariff_rates.json
│       └── research/
│
├── 03_COMMODITY_MODULES/              ← Pluggable commodity verticals
│   ├── README.md
│   │
│   ├── cement/                        ← MODULE 1 ✅ ACTIVE
│   │   ├── README.md
│   │   ├── config.yaml
│   │   ├── naics_codes.json
│   │   ├── market_intelligence/
│   │   │   ├── supply_landscape/      ← Plants, terminals, capacity
│   │   │   ├── demand_analysis/       ← Consumption patterns
│   │   │   ├── trade_flows/           ← Import/export analysis
│   │   │   └── scm_markets/           ← Fly ash, slag, pozzolans
│   │   ├── supply_chain_models/
│   │   │   ├── barge_routes/
│   │   │   ├── rail_routes/
│   │   │   └── terminal_operations/
│   │   └── reports/
│   │       ├── templates/
│   │       ├── drafts/
│   │       └── published/
│   │
│   ├── steel/                         ← MODULE 2 ✅ NEW
│   │   ├── README.md
│   │   └── market_intelligence/supply_landscape/
│   │       ├── aist_steel_plants.geojson  ← 68 facilities
│   │       └── aist_steel_plants.csv
│   │
│   ├── aluminum/                      ← MODULE 3 ✅ NEW
│   │   ├── README.md
│   │   └── market_intelligence/supply_landscape/
│   │       └── us_aluminum_facilities.geojson
│   │
│   ├── copper/                        ← MODULE 4 ✅ NEW
│   │   ├── README.md
│   │   └── market_intelligence/supply_landscape/
│   │       ├── us_copper_facilities.geojson  ← 43 facilities
│   │       └── us_copper_facilities.csv
│   │
│   └── forestry/                      ← MODULE 5 ✅ NEW
│       ├── README.md
│       └── market_intelligence/supply_landscape/
│           └── us_forest_products_facilities.geojson
│
├── 04_REPORTS/                        ← Master report generation pipeline
│   ├── README.md
│   ├── templates/
│   │   ├── executive_briefing.md
│   │   ├── market_report.md
│   │   ├── technical_methodology.md
│   │   └── data_appendix.md
│   │
│   ├── us_bulk_supply_chain/          ← MASTER REPORT (commodity-agnostic)
│   │   ├── 00_executive_summary.md
│   │   ├── 01_mississippi_river_system.md
│   │   ├── 02_inland_waterway_infrastructure.md
│   │   ├── 03_barge_industry_economics.md
│   │   ├── 04_port_system_lower_miss.md
│   │   ├── 05_rail_network_integration.md
│   │   ├── 06_pipeline_infrastructure.md
│   │   ├── 07_vessel_trade_flows.md
│   │   ├── 08_regulatory_environment.md
│   │   ├── 09_economic_impact.md
│   │   ├── 10_data_sources_methodology.md
│   │   └── annexes/
│   │
│   └── cement_commodity_report/       ← COMMODITY DRILLDOWN
│       ├── 00_executive_summary.md
│       ├── 01_us_cement_market_overview.md
│       ├── 02_import_dynamics.md
│       ├── 03_scm_supplementary_materials.md
│       ├── 04_supply_chain_logistics.md
│       ├── 05_lower_miss_river_cement.md
│       ├── 06_competitive_landscape.md
│       ├── 07_pricing_cost_analysis.md
│       ├── 08_demand_drivers_outlook.md
│       ├── 09_sesco_market_position.md      ← CLIENT-SPECIFIC (isolated)
│       └── 10_methodology_sources.md
│
├── 05_DOCUMENTATION/                  ← Project-wide documentation
│   ├── DIRECTORY_STRUCTURE.md         ← THIS FILE
│   ├── MIGRATION_STATUS.md            ← Detailed project migration tracking
│   ├── IMPLEMENTATION_GUIDE.md        ← Phase-by-phase build instructions
│   ├── TECHNICAL_STANDARDS.md         ← Code style, data standards
│   ├── DATA_SOURCES.md                ← Complete data source catalog
│   ├── NAICS_HTS_CODES.md             ← Commodity classification codes
│   ├── architecture.md                ← System architecture diagrams
│   ├── data_dictionary/
│   │   ├── MASTER_DATA_DICTIONARY.csv
│   │   ├── GRID_REFERENCE_LOOKUP.csv
│   │   └── TRANSFORMATION_RULES.csv
│   ├── api_catalog.md
│   ├── methodology_index.md
│   └── changelog.md
│
└── 06_ARCHIVE/                        ← Original folder contents (read-only)
    ├── README.md                      ← Migration log: what moved where
    ├── project_Miss_river_ORIGINAL/
    ├── project_barge_ORIGINAL/
    ├── project_cement_markets_ORIGINAL/
    ├── project_rail_ORIGINAL/
    ├── project_pipelines_ORIGINAL/
    ├── project_us_flag_ORIGINAL/
    ├── project_manifest_ORIGINAL/
    ├── task_epa_frs_ORIGINAL/
    ├── task_usace_entrance_clearance_ORIGINAL/
    ├── project_mrtis_ORIGINAL/
    ├── project_port_nickle_ORIGINAL/
    └── sources_data_maps_ORIGINAL/
```

---

## File Count & Size Summary (by category)

| Category | Description | Est. Size | Est. Files |
|---|---|---:|---:|
| **01_DATA_SOURCES/** | Raw data ingestion | ~15 GB | ~5,000 |
| **02_TOOLSETS/** | Analysis engines | ~8 GB | ~1,500 |
| **03_COMMODITY_MODULES/** | Commodity verticals | ~500 MB | ~200 |
| **04_REPORTS/** | Generated reports | ~50 MB | ~100 |
| **05_DOCUMENTATION/** | Platform docs | ~10 MB | ~50 |
| **06_ARCHIVE/** | Original projects | ~20 GB | ~8,000 |
| **Total** | | **~43 GB** | **~15,000** |

---

## Navigation Tips

- **Quick start:** Read CLAUDE.md → README.md → This file
- **Data source details:** See `01_DATA_SOURCES/{category}/README.md`
- **Toolset usage:** See `02_TOOLSETS/{toolset}/README.md`
- **Methodology details:** See `02_TOOLSETS/{toolset}/METHODOLOGY.md`
- **Commodity module setup:** See `03_COMMODITY_MODULES/README.md`
- **Migration tracking:** See `MIGRATION_STATUS.md`
