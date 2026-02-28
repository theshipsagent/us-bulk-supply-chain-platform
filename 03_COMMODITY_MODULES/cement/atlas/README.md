# ATLAS - U.S. Cement Market Intelligence System

**A**nalytical **T**ool for **L**ogistics, **A**ssets, **T**rade & **S**upply

A hybrid intelligence platform for analyzing U.S. cement markets, combining structured data (EPA, USGS, trade statistics) with AI-powered analysis.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from src.utils.db import init_atlas_db; init_atlas_db()"

# Load EPA FRS data
python cli.py refresh

# Query facilities
python cli.py query --state TX
python cli.py query --naics 3273

# View statistics
python cli.py stats
python cli.py stats --by-state
```

## Features

### Phase 0 (Current)
- **EPA FRS Integration**: 5,000-15,000 cement-relevant facilities with addresses and coordinates
- **NAICS-based Filtering**: 40+ cement industry NAICS codes from manufacturing to distribution
- **Entity Resolution**: Fuzzy matching against 150+ target companies
- **CLI Query Interface**: Filter by state, NAICS, company name
- **Analytics**: Facility counts, distributions, summaries

### Future Phases
- USGS cement production data integration
- EPA GHGRP emissions tracking
- Import/export trade statistics
- Market share analysis
- AI-powered report generation

## Project Structure

```
atlas/
├── config/                    # Configuration files
│   ├── settings.yaml         # Main settings (paths, thresholds)
│   ├── naics_cement.yaml     # Cement industry NAICS codes
│   └── target_companies.yaml # Company fuzzy match patterns
├── data/                      # Data files (gitignored)
│   ├── raw/                  # Downloaded source data
│   ├── processed/            # Parquet intermediates
│   ├── work_product_archive/ # Previous work preserved
│   └── atlas.duckdb         # Master analytical database
├── src/                       # Source code
│   ├── etl/                  # Data extraction & loading
│   │   └── epa_frs.py       # EPA FRS loader
│   ├── harmonize/            # Entity resolution
│   │   └── entity_resolver.py
│   ├── analytics/            # Query & analysis
│   │   └── supply.py        # Supply-side analytics
│   └── utils/                # Utilities
│       └── db.py            # Database connections
├── cli.py                    # Command-line interface
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Data Sources

### EPA FRS (Facility Registry Service)
- **Location**: `../task_epa_frs/data/frs.duckdb` (read-only)
- **Size**: 623 MB
- **Tables**: facilities, naics_codes, parent_company_lookup, program_links
- **Coverage**: ~1.2M U.S. facilities with environmental permits/reporting
- **Used for**: Identifying cement manufacturing and consumption facilities

## Database Schema

### `atlas.duckdb`

**facilities** - Core facility information
- `registry_id` (PK): EPA Registry ID
- `facility_name`: Facility name
- `street_address`, `city`, `state`, `zip`, `county`: Address
- `latitude`, `longitude`: Geocoordinates
- `created_at`, `updated_at`: Timestamps

**facility_naics** - NAICS codes per facility
- `registry_id`, `naics_code` (PK): Composite key
- `naics_description`: NAICS description
- `naics_category`: Category from config (Precast, Highway/Paving, etc.)

**parent_companies** - Company name resolution
- `raw_name` (PK): Original facility name
- `resolved_parent`: Canonical parent company name
- `match_score`: Fuzzy match confidence (0-100)
- `method`: Resolution method (fuzzy, exact, manual)

**facility_companies** - Facility-to-company links
- `registry_id`, `raw_name` (PK): Composite key
- `resolved_parent`: Parent company
- `match_score`: Match confidence

## CLI Commands

### refresh
Refresh data from EPA FRS database:
```bash
python cli.py refresh
python cli.py refresh --resolve-entities  # Include fuzzy matching
```

### query
Query facilities with filters:
```bash
python cli.py query --state CA --limit 20
python cli.py query --naics 327310  # Cement manufacturing
python cli.py query --company "CEMEX"
python cli.py query --state TX --output texas_facilities.csv
```

### stats
View statistics:
```bash
python cli.py stats               # Overall stats
python cli.py stats --by-state    # State breakdown
python cli.py stats --by-naics    # NAICS breakdown
python cli.py stats --by-company  # Company breakdown
```

### info
Get detailed information:
```bash
python cli.py info 110000123456   # Facility details by Registry ID
python cli.py info --state CA     # State summary
```

## Configuration

### settings.yaml
Main configuration file:
- Data source paths
- Database locations
- Fuzzy matching thresholds
- Output paths

### naics_cement.yaml
Cement industry NAICS codes organized by category:
- Primary Production (327310)
- Distribution (327320)
- Precast Products (327331, 327332, 327390)
- Highway/Paving (324121, 237310)
- Building Materials (423320, 423390, 444190)
- Oil & Gas (213112)

### target_companies.yaml
Company name patterns for fuzzy matching, organized by industry segment:
- precast_prestressed: Oldcastle, CRH, Forterra, etc.
- concrete_masonry: Basalite, QUIKRETE, etc.
- highway_paving: Kiewit, Granite Construction, etc.
- oil_gas_cementing: Halliburton, SLB, Baker Hughes
- cement_producers: CEMEX, Holcim, Heidelberg Materials

## Work Product Archive

Previous work preserved in `data/work_product_archive/`:
- `enrich_cement_facilities_from_frs.py`: Original standalone script (logic migrated to ATLAS)
- `US_Cement_Consumers_Facility_Database.xlsx`: Manual reference data (companies extracted to config)

## Development

### Adding New Data Sources
1. Create ETL module in `src/etl/`
2. Define schema in `src/utils/db.py:init_atlas_db()`
3. Add load function
4. Add CLI command in `cli.py`

### Adding Analytics
1. Add query functions to `src/analytics/`
2. Add CLI command or enhance existing commands

### Entity Resolution
1. Add company patterns to `config/target_companies.yaml`
2. Run `python cli.py refresh --resolve-entities`

## License

Internal research project

## Contact

Created: 2026-02-09
Phase: 0 (Foundation)
