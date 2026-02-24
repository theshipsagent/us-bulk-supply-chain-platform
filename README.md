# US Bulk Supply Chain Reporting Platform

**Unified analytics and intelligence platform for US inland waterway, port, rail, and vessel operations with pluggable commodity modules**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/theshipsagent/us-bulk-supply-chain-platform)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

---

## Overview

The **US Bulk Supply Chain Reporting Platform** is a comprehensive data integration and analysis system for understanding commodity flows through US transportation infrastructure. It combines federal data sources (USACE, STB, EPA, USDA) with proprietary market intelligence to model supply chain economics across multiple transport modes.

### Purpose

- **Unified Infrastructure Analysis**: Single platform for waterway, rail, port, and vessel intelligence
- **Commodity-Specific Insights**: Pluggable modules for cement, steel, aluminum, copper, forestry, and more
- **Economic Modeling**: Freight cost calculation, route optimization, and port economic impact analysis
- **Market Intelligence**: Facility mapping, trade flow analysis, and competitive landscape assessment

---

## Key Features

### 🚢 **8 Operational Toolsets**

| Toolset | Description | Status |
|---------|-------------|--------|
| **vessel_intelligence** | Panjiva import manifest processing, 8-phase commodity classification | ✅ Operational |
| **vessel_voyage_analysis** | Maritime voyage tracking (Phase 1+2), port time analytics | ✅ Operational |
| **rail_intelligence** | STB waybill analysis, SCRS facility mapping, rail knowledge bank | ✅ Operational |
| **rail_cost_model** | NTAD/NARN network routing, URCS cost modeling | ✅ Operational |
| **barge_cost_model** | USDA GTR-based freight rates, lock delay modeling | ✅ Operational |
| **facility_registry** | EPA FRS geospatial analysis (4M+ facilities, DuckDB) | ✅ Operational |
| **port_cost_model** | Pilotage, towage, stevedoring cost estimation | ✅ Operational |
| **policy_analysis** | Section 301, Jones Act, tariff impact modeling | ✅ Operational |

### 🏭 **5 Commodity Modules**

| Module | Facilities Mapped | Data Sources | Status |
|--------|------------------|--------------|--------|
| **Cement/SCMs** | 68 plants/terminals | USGS, PCA, EPA FRS, Panjiva | ✅ Complete |
| **Steel** | 68 production + 53 end users | AIST, EPA, STB | ✅ Complete |
| **Aluminum** | 68 facilities | USGS, trade data | ✅ Complete |
| **Copper** | 43 facilities | USGS, industry data | ✅ Complete |
| **Forestry** | TBD | Planned | 🚧 Planned |

### 📊 **Integrated Data Sources**

#### Federal Waterway
- USACE Waterborne Commerce Statistics (WCSC/MRTIS)
- USACE Lock Performance (NDC/LPMS)
- USACE Vessel Entrance/Clearance Records
- FGIS Grain Inspection Records (438 MB, CY1983–present)

#### Federal Rail
- STB Economic Data (waybill, URCS cost tables)
- NTAD Rail Network (NARN lines/nodes)
- SCRS Facility Data (39,936 rail-served facilities)
- STB Rate Database (10,340 contracts)

#### Federal Environmental
- EPA Facility Registry (FRS) — 4M+ facilities, DuckDB
- NAICS/SIC classification lookups

#### Trade & Vessel
- Panjiva Import Manifests (800K+ records)
- Ships Register (52,034 vessels with characteristics)
- MARAD US Flag Fleet Registry

#### Market Data
- USDA Grain Transportation Report (barge rate benchmarks)
- USGS Mineral Commodity Summaries
- Portland Cement Association data
- EIA energy data (fuel costs)

---

## Project Structure

```
project_master_reporting/
├── 01_DATA_SOURCES/          # Raw data ingestion layer
│   ├── federal_waterway/     # USACE, FGIS
│   ├── federal_rail/         # STB, NTAD, SCRS
│   ├── federal_environmental/ # EPA FRS, NAICS
│   ├── federal_trade/        # Panjiva, Census
│   ├── federal_vessel/       # MARAD, USCG, ship register
│   ├── market_data/          # USDA, USGS, PCA, EIA
│   ├── geospatial/           # GIS layers and base maps
│   └── regional_studies/     # Location-specific research
│
├── 02_TOOLSETS/              # Reusable analysis engines
│   ├── vessel_intelligence/  # Import manifest processing
│   ├── vessel_voyage_analysis/ # Maritime voyage tracking
│   ├── rail_intelligence/    # Rail knowledge bank
│   ├── rail_cost_model/      # Rail routing & costing
│   ├── barge_cost_model/     # Waterway freight economics
│   ├── facility_registry/    # EPA FRS geospatial analysis
│   ├── port_cost_model/      # Port cost estimation
│   └── policy_analysis/      # Regulatory impact modeling
│
├── 03_COMMODITY_MODULES/     # Pluggable commodity verticals
│   ├── cement/               # Portland cement, white cement, SCMs
│   ├── steel_metals/         # Steel production & end users
│   ├── aluminum/             # Primary/secondary aluminum
│   ├── copper/               # Copper cathode, wire rod, brass
│   └── forestry/             # Wood products (planned)
│
├── 04_REPORTS/               # Generated reports & publications
├── 05_DOCUMENTATION/         # Project-wide documentation
├── 06_ARCHIVE/               # Original project folders (reference)
└── 07_KNOWLEDGE_BANK/        # Curated research & intelligence
```

---

## Installation

### Requirements

- **Python**: 3.11+
- **Database**: DuckDB (embedded)
- **GIS Libraries**: GDAL/OGR (for geospatial operations)

### Setup

```bash
# Clone repository
git clone https://github.com/theshipsagent/us-bulk-supply-chain-platform.git
cd us-bulk-supply-chain-platform

# Install Python dependencies
pip install -r requirements.txt

# Verify toolset installations
python -m report_platform --version
```

### Configuration

Edit `config.yaml` to configure:
- Data source URLs and refresh schedules
- Database paths
- API credentials (if using external services)
- Active commodity modules

---

## Quick Start

### Master CLI

The platform provides a unified CLI (`report-platform`) for all operations:

```bash
# Data operations
report-platform data download --source epa_frs
report-platform data status

# Toolset operations
report-platform barge-cost --origin "Houston" --destination "Memphis" --commodity cement
report-platform rail-cost --origin "Baton Rouge" --destination "Chicago"
report-platform facility-search --state LA --naics 327310 --radius 50

# Vessel intelligence
report-platform vessel classify --input panjiva_imports.csv
report-platform voyage analyze --port "New Orleans" --year 2025

# Report generation
report-platform report generate --report us_bulk_supply_chain --format docx
```

### Example: Cement Supply Chain Analysis

```python
from report_platform.toolsets.facility_registry import search_facilities
from report_platform.toolsets.barge_cost import calculate_route_cost

# Find cement terminals in Louisiana
terminals = search_facilities(
    state='LA',
    naics_prefix='327310',
    facility_type='terminal'
)

# Calculate barge freight cost
cost = calculate_route_cost(
    origin='Houston',
    destination='Memphis',
    commodity='cement',
    tons=3000
)
```

---

## Toolsets

### 🚢 Vessel Intelligence

**8-Phase Classification System** for Panjiva import manifests:
1. Load & Validate → 2. Normalize → 3. Pre-classify → 4. Commodity Detection
5. Consignee Analysis → 6. Final Classification → 7. Confidence Scoring → 8. Reporting

**Outputs**: Classified CSV, confidence reports, consignee profiles

[📖 Documentation](02_TOOLSETS/vessel_intelligence/README.md)

### ⚓ Vessel Voyage Analysis

**Phase 1**: Voyage detection (Cross In → Cross Out), time calculations
**Phase 2**: Inbound/outbound segmentation, draft analysis, efficiency metrics

**Key Metrics**: Port time, anchor time, terminal time, vessel utilization %

[📖 Documentation](02_TOOLSETS/vessel_voyage_analysis/README.md)

### 🚂 Rail Intelligence & Cost Modeling

- **Knowledge Bank**: STB waybill analysis, SCRS facility mapping (39,936 facilities)
- **Network Routing**: NTAD/NARN graph construction, shortest-path optimization
- **Cost Modeling**: URCS variable cost integration, tariff rate lookups

[📖 Documentation](02_TOOLSETS/rail_cost_model/README.md)

### 🚛 Barge Cost Model

- **Rate Engine**: USDA GTR-based benchmarks, seasonal adjustment
- **Lock Delays**: Probabilistic delay modeling (LPMS data integration)
- **Route Optimization**: Origin-destination transit time & cost

[📖 Documentation](02_TOOLSETS/barge_cost_model/README.md)

### 🏭 Facility Registry (EPA FRS)

- **Database**: 4M+ facilities, DuckDB backend
- **Geospatial**: Proximity analysis, clustering, facility density mapping
- **Entity Resolution**: Parent company harmonization (rapidfuzz)

[📖 Documentation](02_TOOLSETS/facility_registry/README.md)

---

## Commodity Modules

### Cement & Cementitious Materials

**Scope**: Portland cement, white cement, slag cement, fly ash, natural pozzolans, calcined clay

**Facilities**:
- 68 cement plants/import terminals (USGS, PCA)
- 17,671 cement industry facilities (EPA FRS NAICS 327310-327390)
- Parent company consolidation → 9,114 unique entities

**Analysis**:
- Import origins & tariff impacts (Turkey 10%, Vietnam 46%)
- SCM supply mapping (coal plants → fly ash, steel mills → slag)
- Barge/rail distribution modeling

[📖 Module Documentation](03_COMMODITY_MODULES/cement/README.md)

### Steel, Aluminum, Copper

**Steel**: 68 production facilities (AIST), 53 major end users
**Aluminum**: 68 facilities (primary smelters, secondary refineries, rolling mills)
**Copper**: 43 facilities (smelters, refineries, wire rod mills, brass mills)

[📖 Module Documentation](03_COMMODITY_MODULES/)

---

## Autonomous Migration (2026-02-23)

This platform consolidates **4 major projects** migrated autonomously:

| Project | Size | Files | Status |
|---------|------|-------|--------|
| `project_manifest` (vessel_intelligence) | 6.2 GB | 800K+ records | ✅ Complete |
| `task_rail_intelligence` (rail_intelligence) | 4.8 GB | 39,936 facilities | ✅ Complete |
| `project_mrtis` (vessel_voyage_analysis) | 862 MB | ~400 files | ✅ Complete |
| `project_barge` (barge_cost_model) | 2.1 GB | ~500 files | ✅ Complete |

**Migration Statistics**:
- **~14 GB** data migrated
- **~4,500 files** reorganized
- **9 background tasks** + **1 agent** (100% success rate)
- **23/23 tests passing** (vessel voyage analysis)

[📖 Migration Report](AUTONOMOUS_SESSION_COMPLETE_2026-02-23.md)

---

## Documentation

### User Guides
- [CLAUDE.md](CLAUDE.md) — Master project specification
- [Installation Guide](05_DOCUMENTATION/installation.md)
- [Quick Start Guides](02_TOOLSETS/) — Per-toolset documentation

### Technical Documentation
- [Architecture Overview](05_DOCUMENTATION/architecture.md)
- [Data Dictionary](05_DOCUMENTATION/data_dictionary/)
- [API Catalog](05_DOCUMENTATION/api_catalog.md)
- [Methodology Index](05_DOCUMENTATION/methodology_index.md)

### Reports
- US Bulk Supply Chain Report (planned)
- Cement & Cementitious Materials Report (in progress)
- White Papers: Barge Cost Model, Rail Cost Model, Port Economic Impact

---

## Use Cases

### Maritime Operations
- **Vessel voyage reconstruction** from USACE entrance/clearance records
- **Port time analysis** (anchor time, terminal time, efficiency metrics)
- **Import manifest classification** for trade flow analysis

### Supply Chain Economics
- **Multi-modal freight cost comparison** (barge vs rail vs truck)
- **Route optimization** using NTAD rail network + USACE waterway data
- **Port economic impact modeling** (RIMS II multipliers)

### Market Intelligence
- **Facility proximity analysis** (EPA FRS + commodity-specific databases)
- **Competitive landscape mapping** (parent company consolidation)
- **Tariff impact assessment** (Section 301, HTS-specific rates)

### Regulatory Analysis
- **Jones Act compliance** (US flag fleet requirements)
- **Section 232 implications** (steel/aluminum/copper national security)
- **Environmental compliance** (EPA ECHO integration)

---

## Contributing

This is a proprietary platform developed for **SESCO Cement Corporation** and **OceanDatum.ai** maritime consultancy.

For questions or collaboration inquiries:
- **Developer**: Claude (Anthropic)
- **Project Lead**: William Davis
- **Organization**: OceanDatum.ai

---

## Development Roadmap

### Phase 0: ✅ Platform Foundation (Complete)
- Unified directory structure
- Master CLI framework
- Data source integration
- Core toolset migration

### Phase 1: 🚧 Core Platform Report (In Progress)
- US Bulk Supply Chain Report (10 chapters)
- Data source documentation
- Methodology white papers

### Phase 2: 🚧 Commodity Module Expansion (In Progress)
- Cement module completion
- Steel/aluminum/copper integration
- Grain module (planned)
- Fertilizer module (planned)

### Phase 3: 📅 Advanced Analytics (Planned)
- Real-time data pipelines
- Predictive freight cost modeling
- Interactive dashboards (Streamlit/Plotly)
- API endpoints for external integration

---

## License

**Proprietary** — Internal use for SESCO Cement Corporation and OceanDatum.ai clients.

---

## Acknowledgments

### Data Sources
- **USACE**: Waterborne commerce statistics, lock performance data
- **Surface Transportation Board**: Economic data, waybill samples
- **EPA**: Facility Registry System
- **USDA**: Grain Transportation Report
- **USGS**: Mineral Commodity Summaries
- **S&P Global Panjiva**: Import manifest records

### Technology Stack
- **Python**: pandas, geopandas, networkx, duckdb
- **GIS**: GDAL/OGR, Folium, Shapely
- **Database**: DuckDB (embedded analytics)
- **CLI**: Click framework
- **AI Assistant**: Claude (Anthropic)

---

**Built with [Claude Code](https://claude.com/claude-code) • Last Updated: 2026-02-23**
