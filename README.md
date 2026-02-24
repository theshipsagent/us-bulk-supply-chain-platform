# US Bulk Supply Chain Reporting Platform

Unified reporting and analysis platform for US bulk commodity supply chain intelligence.

## Architecture

```
project_master_reporting/
├── 01_DATA_SOURCES/     Raw data ingestion layer (federal, market, geospatial)
├── 02_TOOLSETS/          Reusable analysis engines (commodity-agnostic)
├── 03_COMMODITY_MODULES/ Pluggable commodity verticals (cement first)
├── 04_REPORTS/           Master report generation pipeline
├── 05_DOCUMENTATION/     Project-wide documentation
└── 06_ARCHIVE/           Original folder contents (read-only reference)
```

## Two-Tier Design

1. **Core Platform (commodity-agnostic):** US inland waterway, port, rail, pipeline, and vessel infrastructure
2. **Commodity Modules (pluggable):** Starting with cement/cementitious materials

## Quickstart

```bash
pip install -r requirements.txt
python -m report_platform --help
```

## Data Sources

See `01_DATA_SOURCES/README.md` for the complete data catalog.

## Toolsets

See `02_TOOLSETS/README.md` for available analysis engines.
