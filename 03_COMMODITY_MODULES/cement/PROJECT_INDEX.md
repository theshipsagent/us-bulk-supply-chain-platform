# ATLAS - US Cement Market Intelligence System
## Project Directory Index

**Last Updated:** February 2026
**Project Root:** `G:\My Drive\LLM\project_cement_markets`

---

## Directory Structure

```
project_cement_markets/
|
|-- ATLAS_ARCHITECTURE.md          System design blueprint
|-- ATLAS_PHASE0_SUMMARY.md        Phase 0 completion report
|-- PROJECT_INDEX.md               This file
|
|-- atlas/                         MAIN SYSTEM (one-stop-shop)
|   |-- cli.py                     Master CLI interface
|   |-- extract_report_data.py     Report data extraction pipeline
|   |-- generate_market_report.py  PDF report generator
|   |-- verify_installation.py     Installation verification
|   |-- requirements.txt           Python dependencies
|   |
|   |-- config/                    Configuration
|   |   |-- settings.yaml          System settings
|   |   |-- naics_cement.yaml      40+ cement NAICS codes
|   |   |-- target_companies.yaml  150+ company match patterns
|   |
|   |-- data/                      ALL DATA
|   |   |-- atlas.duckdb           Master analytical database
|   |   |
|   |   |-- source/                Raw data sources
|   |   |   |-- usgs/              USGS mineral statistics (MIS + MYB)
|   |   |   |-- trade/panjiva/     Panjiva import/export trade data
|   |   |   |-- rail/              Railroad cement site data (SCRS)
|   |   |   |-- reports/           Market reports, Cement Weekly
|   |   |   |-- industry_tracker/  GEM Tracker, Schedule K, Ownership
|   |   |
|   |   |-- geospatial/            GeoJSON mapping files
|   |   |   |-- facilities/        Cement plants, ready-mix, terminals
|   |   |   |-- trade_flows/       Import origins, shipping routes
|   |   |   |-- transport/         Rail networks, marine highways
|   |   |   |-- demand/            State/county demand maps
|   |   |
|   |   |-- reference/             Knowledge base
|   |   |   |-- research/          Market research documents
|   |   |   |-- reports/           Generated & archived reports
|   |   |   |   |-- tampa_study/   Original Tampa Bay study archive
|   |   |   |-- rag_documents/     40+ cement industry PDFs
|   |   |   |-- processed_docs/    RAG chunks and analytics
|   |   |
|   |   |-- processed/             Clean Parquet intermediates
|   |   |-- work_product_archive/  Previous work preservation
|   |   |-- archive/               Older file versions
|   |
|   |-- output/                    Generated outputs
|   |   |-- report_data.json       Extracted report data
|   |   |-- US_Cement_Market_Intelligence_Report.pdf
|   |
|   |-- scripts/                   Utility & analysis scripts
|   |   |-- analysis/              Port market, NC/VA, Canada analysis
|   |   |-- utility/               Cleanup, reorganization scripts
|   |   |-- upload_to_arcgis.py    ArcGIS data upload
|   |
|   |-- src/                       Source code modules
|       |-- etl/                   Extract-Transform-Load pipelines
|       |-- harmonize/             Entity resolution (fuzzy matching)
|       |-- analytics/             Supply-side analytics
|       |-- utils/                 Database utilities
|
|-- archive/                       ARCHIVED OLD PROJECTS
|   |-- tampa_study_original/      Full copy of old project_cement
|   |-- read_cement/               Early analysis scripts & data
```

---

## Database Tables (atlas.duckdb)

| Table | Records | Description |
|-------|---------|-------------|
| us_cement_facilities | 1,203 | Integrated US facilities (plants, terminals, consumers) |
| trade_imports | 3,420 | Panjiva import shipments (Jun 2022 - Jun 2025) |
| usgs_monthly_shipments | ~200 | USGS cement shipments by state/month |
| gem_plants | ~100 | GEM cement plant tracker |
| frs_facilities | 61,017 | EPA Facility Registry (cement-related) |

---

## Key Data Assets

### Trade Intelligence
- **66.8 million MT** of imports tracked across 25 origin countries
- **54 US ports** with import activity
- **Export data** available for outbound analysis

### Facility Database
- **100 cement plants** with capacity data
- **222 distribution/terminal sites** with rail service flags
- **88% of plants** confirmed as rail-served
- **382 geocoded rail sites** with coordinates

### Geospatial
- **21 GeoJSON files** covering facilities, trade flows, transport, demand
- Ready for ArcGIS, Leaflet, or Mapbox visualization

### Research Library
- **40+ industry PDFs** (operations handbooks, market studies)
- **5 research documents** (freight analysis, customer prospects, etc.)
- **Tampa Bay study archive** (13 reports, maps, executive summaries)

---

## Quick Start

```bash
cd atlas
pip install -r requirements.txt
python cli.py stats          # Database overview
python cli.py rail --plants  # Rail-served cement plants
python cli.py market --imports  # Import market analysis
python extract_report_data.py   # Extract data for reports
python generate_market_report.py  # Generate PDF report
```

---

## External Data Dependencies

| Source | Location | Purpose |
|--------|----------|---------|
| EPA FRS | `G:\My Drive\LLM\task_epa_frs\data\frs.duckdb` | 17,286 cement consumer facilities |
| Rail SCRS | `G:\My Drive\LLM\project_rail\` | Railroad-served site data |
