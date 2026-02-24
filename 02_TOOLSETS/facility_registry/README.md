# EPA FRS Analytics Tool

A Python CLI tool for managing, extracting, comparing, analyzing, and harmonizing EPA Facility Registry Service (FRS) data. Handles 4M+ facility records with geospatial coordinates, NAICS/SIC industry codes, program linkages across 25+ EPA systems, and organization/ownership data.

## Features

- **Data Download**: Download EPA FRS data from multiple sources (ECHO simplified files, National Combined, or state-specific)
- **Database Management**: DuckDB-based analytical database with columnar storage
- **Flexible Querying**: Search facilities by state, NAICS code, name pattern, city
- **Statistical Analysis**: Comprehensive summaries, distributions, and data quality checks
- **Geospatial Ready**: DuckDB spatial extension integrated for future spatial analytics
- **Entity Resolution**: Framework for parent corporation rollup (Phase 2)

## Technical Stack

- **Database**: DuckDB with spatial extension
- **Language**: Python 3.11+
- **CLI Framework**: Click
- **Data Processing**: Pandas, PyArrow
- **Geospatial**: GeoPandas (Phase 3), Folium (Phase 3)
- **Entity Matching**: rapidfuzz (Phase 2)

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Download ECHO FRS Files (Recommended for initial testing)

```bash
python cli.py download echo
```

This downloads 4 simplified CSV files (~200MB total):
- FRS_FACILITIES.CSV
- FRS_PROGRAM_LINKS.CSV
- FRS_NAICS_CODES.CSV
- FRS_SIC_CODES.CSV

### 2. Ingest Data into DuckDB

```bash
python cli.py ingest echo
```

This loads the CSV files into DuckDB tables and creates NAICS/SIC lookup tables.

### 3. Query Facilities

Search facilities in Virginia:
```bash
python cli.py query facilities --state VA
```

Search chemical manufacturing facilities (NAICS 325):
```bash
python cli.py query facilities --naics 325
```

Search by name pattern:
```bash
python cli.py query facilities --name "waste management"
```

Combine filters:
```bash
python cli.py query facilities --state VA --naics 325 --city Richmond
```

### 4. Get Statistics

Summary statistics:
```bash
python cli.py stats summary
```

State-specific summary:
```bash
python cli.py stats summary --state VA
```

NAICS distribution:
```bash
python cli.py stats naics-distribution --top 20
```

Facility counts by state:
```bash
python cli.py stats by-state
```

Program system summary:
```bash
python cli.py stats programs
```

## CLI Command Reference

### Download Commands

```bash
# Download ECHO simplified files
python cli.py download echo [--force]

# Download National Combined ZIP (~732MB)
python cli.py download national [--force]

# Download individual state data
python cli.py download state <STATE_ABBR> [--force]
```

### Ingest Commands

```bash
# Ingest ECHO files into DuckDB
python cli.py ingest echo [--force]
```

### Query Commands

```bash
# Query facilities
python cli.py query facilities [--state STATE] [--naics PREFIX] [--name PATTERN] [--city CITY] [--limit N] [--format table|csv]

# Get program links for a facility
python cli.py query programs <REGISTRY_ID> [--format table|csv]

# Get NAICS codes for a facility
python cli.py query naics <REGISTRY_ID> [--format table|csv]
```

### Statistics Commands

```bash
# Summary statistics
python cli.py stats summary [--state STATE] [--naics-prefix PREFIX]

# NAICS distribution
python cli.py stats naics-distribution [--state STATE] [--top N] [--digits 2|3|4|6] [--format table|csv]

# Facility count by state
python cli.py stats by-state [--format table|csv]

# Facility count by EPA region
python cli.py stats by-epa-region [--format table|csv]

# Program system summary
python cli.py stats programs [--format table|csv]

# Null rate analysis
python cli.py stats null-rates
```

## Project Structure

```
epa-frs-tool/
├── config/
│   ├── settings.yaml              # Configuration settings
│   ├── naics_sectors.yaml         # NAICS sector groupings
│   └── parent_mapping.json        # Entity rollup mappings (Phase 2)
├── data/
│   ├── raw/                       # Downloaded CSV/ZIP files
│   ├── processed/                 # Intermediate Parquet files
│   └── frs.duckdb                 # Analytical database
├── src/
│   ├── etl/
│   │   ├── download.py            # Data download functions
│   │   └── ingest.py              # CSV to DuckDB loader
│   ├── analyze/
│   │   ├── query_engine.py        # Query functions
│   │   └── stats.py               # Statistical analysis
│   ├── harmonize/                 # Phase 2: Entity resolution
│   ├── geo/                       # Phase 3: Geospatial analysis
│   └── export/                    # Phase 3: Export and reporting
├── cli.py                         # CLI entry point
├── requirements.txt
└── README.md
```

## Database Schema

### Tables

- **facilities**: Core facility information (registry_id, name, address, state, etc.)
- **program_links**: Program system linkages (EPA programs linked to facilities)
- **naics_codes**: NAICS industry codes for facilities
- **sic_codes**: SIC industry codes for facilities
- **naics_lookup**: NAICS sector descriptions
- **sic_lookup**: SIC major group descriptions

### Key Fields

- `registry_id`: Universal join key across all tables (primary key for facilities)
- `pgm_sys_acrnm`: Program system acronym (e.g., NPDES, RCRA, TRI)
- `naics_code`: 6-digit NAICS code
- `sic_code`: 4-digit SIC code
- `state_code`: Two-letter state abbreviation
- `epa_region_code`: EPA region number

## Data Sources

### ECHO FRS Download (Current Implementation)
- **URL**: https://echo.epa.gov/tools/data-downloads
- **Files**: 4 simplified CSV files
- **Best for**: Initial testing, faster downloads

### EPA FRS National Combined (Future)
- **URL**: https://www.epa.gov/frs/epa-state-combined-csv-download-files
- **Size**: ~732MB compressed
- **Best for**: Complete national dataset with all fields

### FRS REST API (Future)
- **Base URL**: https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities
- **Best for**: Targeted queries, refresh specific facilities

## Development Roadmap

### Phase 1: Core ETL + Database + Basic Queries ✓
- [x] Project scaffolding
- [x] Download module (ECHO files)
- [x] Ingest module (DuckDB loader)
- [x] CLI interface with Click
- [x] Basic query engine
- [x] Statistical summaries

### Phase 2: Entity Harmonization (Next)
- [ ] Organization name normalization
- [ ] Fuzzy matching with rapidfuzz
- [ ] Parent corporation rollup
- [ ] Manual mapping override system

### Phase 3: Geospatial + Advanced Analytics (Future)
- [ ] Facility density maps
- [ ] Proximity analysis
- [ ] Sector clustering visualization
- [ ] Cross-program compliance comparison
- [ ] Interactive Folium maps

## Configuration

Edit `config/settings.yaml` to customize:
- Database path
- Data directories
- Download URLs
- API endpoints
- Processing parameters

## Logging

The tool uses Python's logging module. Logs include:
- Download progress
- Ingest statistics
- Query execution
- Error messages

## Error Handling

- Download failures: Automatic cleanup of partial downloads
- Missing files: Clear error messages
- Schema mismatches: Validation and logging
- Query errors: Informative error messages with suggestions

## Contributing

This is a Phase 1 implementation. Future enhancements:
- Additional data source support
- Enhanced entity resolution
- Geospatial analysis capabilities
- Export and reporting features
- Data quality validation

## License

This tool is for analytical purposes with EPA public data.

## Support

For issues or questions:
- Check the CLI help: `python cli.py --help`
- Check command-specific help: `python cli.py <command> --help`

## Data Attribution

Data sourced from:
- EPA Facility Registry Service (FRS)
- EPA Enforcement and Compliance History Online (ECHO)
