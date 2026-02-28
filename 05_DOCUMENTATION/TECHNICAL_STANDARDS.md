# Technical Standards — US Bulk Supply Chain Reporting Platform

**Last Updated:** 2026-02-24
**Reference:** See CLAUDE.md for summary

---

## Code Style

### Python Standards

**Version:** Python 3.11+

**Style Guidelines:**
- Type hints on all function signatures
- Docstrings for all public functions (Google style)
- Black formatter (line length 100)
- isort for import sorting
- pylint/flake8 for linting

**Example:**
```python
from typing import List, Optional
import pandas as pd

def calculate_barge_cost(
    origin: str,
    destination: str,
    commodity: str,
    tonnage: float,
    date: Optional[str] = None
) -> dict:
    """
    Calculate barge freight cost for a given route and commodity.

    Args:
        origin: Origin port/terminal name
        destination: Destination port/terminal name
        commodity: Commodity type (e.g., 'cement', 'grain')
        tonnage: Cargo tonnage (short tons)
        date: Optional date for rate lookup (defaults to latest)

    Returns:
        dict: Cost breakdown with total, components, and route details
    """
    # Implementation
    pass
```

### CLI Standards

**Framework:** Click (preferred over argparse)

**Command Structure:**
```python
import click

@click.group()
def cli():
    """US Bulk Supply Chain Reporting Platform CLI"""
    pass

@cli.group()
def data():
    """Data operations (download, ingest, status)"""
    pass

@data.command()
@click.option('--source', required=True, help='Data source name')
def download(source: str):
    """Download data from specified source"""
    click.echo(f"Downloading {source}...")
```

**Command Naming:**
- Use kebab-case for multi-word commands (`barge-cost`, not `bargeCost`)
- Verb-first for actions (`download`, `ingest`, `generate`)
- Noun-first for queries (`list`, `status`, `show`)

---

## Database Standards

### DuckDB (Primary Analytics Database)

**When to use DuckDB:**
- Analytical queries on large datasets (>1M rows)
- Geospatial analysis with spatial extension
- Cross-source data joins
- Report generation queries

**Schema Naming:**
- Use snake_case for table and column names
- Prefix source tables with source abbreviation (e.g., `epa_frs_facilities`, `usace_mrtis_voyages`)
- Use `_staging` suffix for intermediate tables
- Use `_final` suffix for production-ready tables

**Example:**
```sql
CREATE TABLE epa_frs_facilities (
    registry_id VARCHAR PRIMARY KEY,
    facility_name VARCHAR,
    naics_code VARCHAR,
    latitude DOUBLE,
    longitude DOUBLE,
    state_code VARCHAR(2),
    last_updated DATE
);

CREATE INDEX idx_naics ON epa_frs_facilities(naics_code);
CREATE INDEX idx_state ON epa_frs_facilities(state_code);
```

### File-Based Formats

**Parquet (preferred for intermediate data):**
- Use for large analytical datasets (>100K rows)
- Preserves schema and data types
- Efficient compression

**CSV (use for small reference data):**
- Use for human-readable reference tables (<10K rows)
- Always include header row
- UTF-8 encoding
- Escape quotes with double quotes

**JSON (use for configuration and structured metadata):**
- Configuration files
- API responses
- Hierarchical reference data
- NAICS/HTS code mappings

---

## Data Standards

### Geographic Data

**Coordinate System:**
- **Default:** WGS84 (EPSG:4326) for all lat/lon coordinates
- **Projected:** Use UTM zones for distance calculations
- Always specify CRS in GeoJSON/shapefile metadata

**Units:**
- **Distance (inland):** Statute miles
- **Distance (coastal/ocean):** Nautical miles
- Always specify units in column names or metadata (e.g., `distance_nm`, `distance_mi`)

**Precision:**
- Latitude/Longitude: 6 decimal places (≈0.1 meter precision)
- Example: `29.951065, -90.071533`

### Monetary Data

**Currency:**
- All monetary values in USD
- Always note the year for inflation adjustment (e.g., `USD 2024`)
- Use column suffix to indicate year (e.g., `freight_cost_usd_2024`)

**Precision:**
- Whole dollars for values >$1,000
- Cents for values <$1,000
- Avoid floating point rounding errors (use Decimal type when needed)

### Tonnage Data

**Units:**
- **Default:** Short tons (US, 2,000 lbs) — the industry standard for US domestic
- **Metric:** Metric tons (1,000 kg) — clearly label as `_mt` suffix
- Always specify in column names (e.g., `cargo_tonnage_short`, `capacity_mt`)

**Conversions:**
- 1 short ton = 2,000 lbs = 0.907 metric tons
- 1 metric ton = 2,204.62 lbs = 1.102 short tons

### Date/Time Data

**Format:** ISO 8601 (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)

**Examples:**
- Date only: `2024-03-15`
- Date + time: `2024-03-15 14:30:00`
- With timezone: `2024-03-15T14:30:00-05:00` (Central Time)

**Column Naming:**
- Use `_date` suffix for dates without time (e.g., `arrival_date`)
- Use `_datetime` or `_timestamp` for full timestamps (e.g., `arrival_datetime`)

---

## File Naming Standards

### General Rules
- **Snake_case** for all files and folders
- **No spaces** in any path
- Use lowercase for all file/folder names
- Use hyphens only in kebab-case CLI commands, not in file names

### Data Files

**Raw data files:**
```
{source}_{dataset}_{date}.{ext}

Examples:
usace_lock_performance_2024.csv
epa_frs_national_2024-02-01.csv
panjiva_cement_imports_2023Q4.parquet
```

**Processed data files:**
```
{source}_{dataset}_{processing_stage}.{ext}

Examples:
mrtis_voyages_cleaned.parquet
scrs_facilities_geocoded.csv
stb_contracts_parsed.parquet
```

### Script Files

**Prefix with action verb:**
```
{action}_{target}.py

Examples:
download_frs.py
ingest_panjiva.py
build_waterway_graph.py
analyze_cement_flow.py
generate_port_report.py
```

**Test files:**
```
test_{module}.py

Examples:
test_routing_engine.py
test_cost_calculator.py
test_facility_search.py
```

### Documentation Files

**Uppercase for top-level:**
- `README.md` (every folder)
- `METHODOLOGY.md` (every toolset)
- `CHANGELOG.md` (project root)

**Lowercase for detailed docs:**
- `architecture.md`
- `api_catalog.md`
- `data_dictionary.md`

---

## Documentation Standards

### README Files

Every folder must have a `README.md` with:

1. **Title and Purpose** (1 paragraph)
2. **Contents** (what's in this folder)
3. **Usage** (how to use scripts/data)
4. **Dependencies** (if any)
5. **Last Updated** (date)

**Example:**
```markdown
# EPA FRS Facility Registry

Contains EPA Facility Registry System (FRS) data and ETL scripts.

## Contents
- `data/frs.duckdb` — DuckDB database with 4M+ facilities
- `src/etl/download.py` — Download national/state CSV files
- `src/etl/ingest.py` — CSV → DuckDB ingestion

## Usage
```bash
python src/etl/download.py --state LA
python src/etl/ingest.py --input data/raw/
```

## Last Updated
2024-03-15
```

### METHODOLOGY Files

Every toolset must have a `METHODOLOGY.md` with:

1. **Overview** (1-2 paragraphs on what the toolset does)
2. **Data Sources** (all inputs with URLs and access dates)
3. **Algorithms** (routing, cost calculation, classification logic)
4. **Validation** (how results are validated)
5. **Limitations** (known limitations and assumptions)
6. **References** (academic papers, industry standards, government docs)

**Example Structure:**
```markdown
# Barge Cost Model Methodology

## Overview
This toolset calculates inland waterway barge freight costs...

## Data Sources
- **USDA Grain Transportation Report (GTR)**
  - URL: https://www.ams.usda.gov/services/transportation-analysis/gtr
  - Access: Weekly, most recent 2024-02-20
  - Coverage: Barge rates 2006-present

## Algorithms
### Routing Engine
Uses NetworkX Dijkstra shortest path...

### Cost Calculation
Total cost = Linehaul + Lock delays + Fleeting + Switching
- Linehaul: $/ton-mile × distance × tonnage
- Lock delays: Probabilistic based on LPMS data
...

## Validation
Compared against published tariffs from...

## Limitations
- Does not account for low water surcharges
- Assumes standard barge configurations
...

## References
1. USDA AMS (2023). *Grain Transportation Report*
2. USACE (2022). *Lock Performance Monitoring System*
```

### Data Source README Template

Every data source folder needs:

```markdown
# {Data Source Name}

## Source
- **Organization:** {EPA, USACE, STB, etc.}
- **URL:** {direct download or query URL}
- **API Documentation:** {if applicable}

## Access
- **Method:** {Download, API, Web Query}
- **Refresh Cadence:** {Daily, Weekly, Monthly, Annual}
- **Last Downloaded:** {YYYY-MM-DD}

## Schema
| Column | Type | Description | Example |
|---|---|---|---|
| registry_id | VARCHAR | Unique facility ID | 110000123456 |
| facility_name | VARCHAR | Facility name | ACME Cement Plant |
| latitude | DOUBLE | Latitude (WGS84) | 29.951065 |

## Usage
```bash
python download_{source}.py
```

## Notes
- {Any special handling, data quality issues, etc.}
```

---

## Code Organization

### Project Structure

```
{toolset_name}/
├── README.md                  ← Usage guide
├── METHODOLOGY.md             ← White paper
├── requirements.txt           ← Python dependencies
├── setup.py                   ← Package installation (if needed)
│
├── src/                       ← Source code
│   ├── __init__.py
│   ├── {module1}.py
│   ├── {module2}.py
│   └── cli.py                 ← CLI entry point
│
├── data/                      ← Local data (gitignored if large)
│   ├── raw/
│   ├── processed/
│   └── reference/
│
├── tests/                     ← Unit tests
│   ├── __init__.py
│   ├── test_{module1}.py
│   └── test_{module2}.py
│
├── notebooks/                 ← Jupyter notebooks (exploratory analysis)
│   └── {analysis_name}.ipynb
│
└── results/                   ← Output files (gitignored)
    └── {timestamp}/
```

### Import Organization (Python)

Use `isort` with the following order:

1. Standard library
2. Third-party packages
3. Local project imports

```python
# Standard library
import os
from typing import List, Optional

# Third-party
import click
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Local
from src.routing_engine import RouteCalculator
from src.cost_engine import CostCalculator
```

---

## Git Standards

### Commit Messages

**Format:**
```
{type}: {short description}

{optional longer description}

{optional footer}
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

**Examples:**
```
feat: Add barge cost forecasting with VAR/SpVAR models

Implements vector autoregression and spatial VAR models for
barge freight rate forecasting based on USDA GTR data.

Closes #42
```

```
fix: Correct geocoding precision for SCRS facilities

Changed geocoding precision from 4 to 6 decimal places
to match EPSG:4326 standard.
```

### Branch Naming

```
{type}/{ticket-number}-{short-description}

Examples:
feature/123-add-cement-module
bugfix/456-fix-route-calculation
docs/789-update-methodology
```

---

## Quality Standards

### Code Quality

**Linting:**
- Run `pylint` and `flake8` before committing
- Target score: >8.0 for pylint
- Maximum line length: 100 characters

**Type Checking:**
- Use `mypy` for static type checking
- All public functions must have type hints

**Testing:**
- Unit tests for all public functions
- Target coverage: >80%
- Use `pytest` framework

### Data Quality

**Validation Checks:**
- Check for null values in required fields
- Validate data types (e.g., lat/lon are numeric)
- Range checks (e.g., tonnage > 0)
- Referential integrity (foreign keys exist)

**Example:**
```python
def validate_facility_data(df: pd.DataFrame) -> List[str]:
    """Validate facility data quality"""
    issues = []

    # Check required fields
    required = ['registry_id', 'facility_name', 'latitude', 'longitude']
    for col in required:
        if df[col].isnull().any():
            issues.append(f"Null values in {col}")

    # Range checks
    if (df['latitude'] < -90).any() or (df['latitude'] > 90).any():
        issues.append("Latitude out of range")

    return issues
```

---

## Performance Standards

### Query Performance

**DuckDB Queries:**
- Target: <5 seconds for analytical queries
- Use `EXPLAIN` to check query plans
- Create indexes on commonly filtered columns

**API Response Times:**
- Simple queries: <500ms
- Complex calculations: <2 seconds
- Use caching for repeated queries

### Data Processing

**Batch Processing:**
- Process data in chunks for large files (>1GB)
- Use multiprocessing for CPU-bound tasks
- Use async I/O for I/O-bound tasks

**Example:**
```python
import duckdb
from pathlib import Path

def process_large_csv(csv_path: Path, chunk_size: int = 100000):
    """Process large CSV in chunks using DuckDB"""
    con = duckdb.connect()

    # Use DuckDB's streaming CSV reader
    query = f"""
    SELECT * FROM read_csv_auto('{csv_path}')
    WHERE tonnage > 0
    """

    for chunk in con.execute(query).fetch_df_chunk(chunk_size):
        # Process chunk
        yield chunk
```

---

## Security Standards

### Credentials Management

**Never commit:**
- API keys
- Passwords
- Database connection strings with credentials

**Use environment variables:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from .env file (gitignored)
load_dotenv()

API_KEY = os.getenv('EPA_API_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')
```

### Data Privacy

**PII Handling:**
- Do not store personally identifiable information unless required
- Anonymize data when possible
- Follow client confidentiality rules (see CLAUDE.md)

**Client Confidentiality:**
- Never mention specific client names in general platform documentation
- Client-specific data only in dedicated client deliverable folders
- Replace "OceanDatum.ai" with "William S. Davis III" in all docs

---

## Deployment Standards

### Dependencies

**requirements.txt:**
```
# Core
click>=8.1
pyyaml>=6.0
tqdm>=4.66
requests>=2.31

# Data Processing
duckdb>=1.1
pandas>=2.1
pyarrow>=14.0
openpyxl>=3.1

# Geospatial
geopandas>=0.14
folium>=0.15
shapely>=2.0

# Network Analysis
networkx>=3.2

# Visualization
matplotlib>=3.8
plotly>=5.18
```

**Version Pinning:**
- Use `>=` for minor versions
- Pin major versions to avoid breaking changes
- Test before upgrading major versions

### Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

---

## Reference

For detailed examples, see:
- `02_TOOLSETS/barge_cost_model/` — Production-ready toolset
- `02_TOOLSETS/vessel_intelligence/` — Large-scale data processing
- `02_TOOLSETS/facility_registry/` — DuckDB + geospatial analysis
