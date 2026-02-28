# USACE Vessel Characteristics Database & Dashboard

Complete database and dashboard system for analyzing 45,937 US Army Corps of Engineers vessel characteristics.

## 🚢 Overview

This system provides:
- **PostgreSQL database** with normalized schema and code translations
- **ETL pipeline** to load 9 Excel files (3,511 operators + 45,937 vessels)
- **Streamlit dashboard** for interactive analytics
- **Materialized view** for instant queries with all codes pre-translated

## 📊 Features

### Database
- **Lookup tables** for all USACE codes (VTCC, ICST, Districts, Series, Service, etc.)
- **Normalized schema** with proper foreign keys
- **Materialized view** (`vessel_analytics_view`) with all codes translated
- **Indexes** optimized for dashboard queries

### Dashboard Analytics
- Fleet overview with KPIs and charts
- Operator analysis with contact info and fleet composition
- Vessel type distribution and statistics
- Geographic analysis by Corps district and region
- Equipment inventory tracking
- Advanced search and CSV export

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ (running locally or on network)
- 45,937 USACE vessel records in Excel format

### Step 1: Install PostgreSQL
Download and install from: https://www.postgresql.org/download/

**Windows:**
```bash
# Use the PostgreSQL installer
# Default port: 5432
# Remember your postgres user password!
```

### Step 2: Setup Python Environment
```bash
cd "G:\My Drive\LLM\project_us_flag"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install sqlalchemy psycopg2-binary pandas openpyxl pyyaml streamlit plotly
```

### Step 4: Configure Database Credentials
```bash
# Copy template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
notepad .env
```

Example `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=usace_vessels
DB_USER=postgres
DB_PASSWORD=YourPasswordHere
```

### Step 5: Create PostgreSQL Database
```sql
-- Connect to PostgreSQL (using pgAdmin or psql)
CREATE DATABASE usace_vessels;
```

## 🚀 Usage

### Initialize Database (Run Once)
```bash
python scripts/usace/init_database.py
```

This will:
1. Create all tables (operators, vessels, lookup tables)
2. Populate lookup tables with code translations
3. Create materialized view and indexes

### Run ETL Pipeline
```bash
python scripts/usace/run_etl.py
```

This will:
1. Load 9 Excel files from `data/raw/usace/`
2. Insert 3,511 operators into database
3. Insert 45,937 vessels into database
4. Refresh materialized view
5. Generate summary statistics

Expected output:
```
USACE VESSEL ETL PIPELINE
=================================================================
1. Connecting to database...
✓ Connected to database

2. Loading Excel files...
✓ Loaded 3,511 operators and 45,937 vessels

3. Validating data integrity...
✓ Validation complete

4. Loading operators into database...
✓ Loaded 3,511 operators

5. Loading vessels into database...
  Loaded 5,000 / 45,937 vessels...
  Loaded 10,000 / 45,937 vessels...
  ...
✓ Loaded 45,937 vessels

6. Refreshing materialized view...
✓ Materialized view refreshed

7. Generating statistics...

Database Statistics:
  Total Operators: 3,511
  Total Vessels: 45,937

✓ ETL PIPELINE COMPLETE!
  Time elapsed: 120.5 seconds
```

### Launch Dashboard
```bash
streamlit run src/usace_db/dashboard/app.py
```

Dashboard will open at: http://localhost:8501

## 📁 Project Structure

```
project_us_flag/
├── data/
│   └── raw/
│       └── usace/                        # Raw Excel files
│           ├── 2023 TS OP TS23OP.xlsx   # 3,511 operators
│           ├── 2023 TS VS TS23VS.xlsx   # 45,937 vessels
│           ├── 2023 Self Propelled Vessels selfpr23.xlsx
│           ├── 2023 Deck Barges deck23.xlsx
│           ├── 2023 Dry Covered Barge drycv23.xlsx
│           ├── 2023 Dry Open Barge dryop23.xlsx
│           ├── 2023 Tank Barges tankb23.xlsx
│           ├── 2023 Toe Boats towb23.xlsx
│           ├── 2023 Other Dry Barges otdbrg23.xlsx
│           └── Data Dictionary.pdf
│
├── src/
│   └── usace_db/
│       ├── config/
│       │   ├── code_mappings.yaml      # Code translations
│       │   └── database.yaml          # Configuration
│       ├── database/
│       │   ├── connection.py          # DB connection manager
│       │   └── schema.sql             # PostgreSQL schema
│       ├── etl/
│       │   ├── excel_loader.py        # Load Excel files
│       │   ├── code_loader.py         # Populate lookup tables
│       │   └── data_loader.py         # Load vessels/operators
│       └── dashboard/
│           ├── app.py                 # Streamlit dashboard
│           └── queries.py             # Database queries
│
├── scripts/
│   └── usace/
│       ├── init_database.py           # Initialize database
│       └── run_etl.py                 # Run ETL pipeline
│
├── .env.example                        # Database credentials template
├── .env                                # Your credentials (DO NOT commit)
└── USACE_README.md                    # This file
```

## 📊 Database Schema

### Core Tables
- **operators** (3,511 rows) - Operator master table with contact info
- **vessels** (45,937 rows) - Vessel master table with physical characteristics

### Lookup Tables (Code Translations)
- **lookup_vtcc** - Vessel Type, Construction & Characteristics (79 codes)
- **lookup_icst** - International Classification of Ships (18 codes)
- **lookup_district** - Corps of Engineers Districts (44 districts)
- **lookup_series** - Geographic regions (3: Great Lakes, Mississippi, Coastal)
- **lookup_service** - Service types (3: ICC-regulated, ICC-exempt, Private)
- **lookup_capacity_ref** - Cargo capacity types (6 types)
- **lookup_equipment** - Equipment types (cranes, pumps, etc.)

### Materialized View
- **vessel_analytics_view** - Denormalized view with ALL codes translated
  - Join of vessels + operators + all lookup tables
  - Optimized with 11 indexes for fast filtering
  - Refresh after ETL: `REFRESH MATERIALIZED VIEW vessel_analytics_view`

## 🔍 Example Queries

### Get all vessels with translated codes
```sql
SELECT * FROM vessel_analytics_view LIMIT 100;
```

### Top operators by fleet size
```sql
SELECT
    operator_name,
    operator_city || ', ' || operator_state AS location,
    COUNT(*) AS vessel_count,
    AVG(nrt) AS avg_nrt
FROM vessel_analytics_view
GROUP BY operator_name, operator_city, operator_state
ORDER BY vessel_count DESC
LIMIT 20;
```

### Fleet by district
```sql
SELECT
    district_name,
    COUNT(*) AS vessels,
    SUM(CASE WHEN is_self_propelled THEN 1 ELSE 0 END) AS self_propelled,
    SUM(CASE WHEN is_barge THEN 1 ELSE 0 END) AS barges
FROM vessel_analytics_view
GROUP BY district_name
ORDER BY vessels DESC;
```

### Equipment inventory by operator
```sql
SELECT
    operator_name,
    equip1_name,
    COUNT(*) AS vessel_count
FROM vessel_analytics_view
WHERE equip1_name IS NOT NULL
GROUP BY operator_name, equip1_name
ORDER BY vessel_count DESC
LIMIT 50;
```

## 🔧 Maintenance

### Refresh Materialized View
After data updates:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY vessel_analytics_view;
```

Or use Python function:
```python
from usace_db.database.connection import DatabaseConnection
db = DatabaseConnection()
db.connect()
db.engine.execute("SELECT refresh_vessel_analytics()")
```

### Backup Database
```bash
pg_dump -U postgres usace_vessels > usace_vessels_backup.sql
```

### Restore Database
```bash
psql -U postgres usace_vessels < usace_vessels_backup.sql
```

## 📈 Performance

- **Database size:** ~350 MB (45,937 vessels + indexes)
- **ETL runtime:** ~2 minutes for full load
- **Dashboard load time:** < 2 seconds (with cached queries)
- **Query response:** < 500ms for filtered analytics

## 🐛 Troubleshooting

### "Database connection failed"
- Check PostgreSQL is running: `pg_ctl status`
- Verify credentials in `.env` file
- Test connection: `psql -U postgres -d usace_vessels -c "SELECT 1"`

### "Failed to load Excel files"
- Verify files exist in `data/raw/usace/`
- Check file permissions (read access required)
- Ensure openpyxl installed: `pip install openpyxl`

### "Streamlit dashboard won't start"
- Check port 8501 is available
- Verify Streamlit installed: `pip install streamlit`
- Try different port: `streamlit run app.py --server.port 8502`

### "Materialized view is slow"
- Refresh the view: `REFRESH MATERIALIZED VIEW vessel_analytics_view`
- Check indexes: `\d+ vessel_analytics_view` in psql
- Vacuum analyze: `VACUUM ANALYZE vessel_analytics_view`

## 📚 Data Sources

- **Source:** USACE Waterborne Commerce Statistics Center (WCSC)
- **URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Vessel-Characteristics/
- **Data Year:** 2023
- **Coverage:** All vessels >1,000 GT operating on US inland waterways

## 🤝 Contact

For questions about the USACE vessel database:
- **Owner:** William S. Davis III
- **Email:** [Your email]
- **Location:** Chesapeake, VA

## 📝 License

Proprietary - Internal use only.

---

**Built with:** Python 3.11 | PostgreSQL 15 | Streamlit 1.31 | SQLAlchemy 2.0
