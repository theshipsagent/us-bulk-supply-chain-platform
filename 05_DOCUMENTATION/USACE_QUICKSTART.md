# 🚀 USACE Database Quick Start Guide

## Prerequisites
- Python 3.8+ installed
- PostgreSQL 12+ installed and running
- USACE data files in `data/raw/usace/`

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd "G:\My Drive\LLM\project_us_flag"

# Install required packages
pip install sqlalchemy psycopg2-binary pandas openpyxl pyyaml streamlit plotly
```

### 2. Configure Database
```bash
# Copy environment template
copy .env.example .env

# Edit .env and set your PostgreSQL password
notepad .env
```

Set these values in `.env`:
```
DB_PASSWORD=your_postgres_password_here
```

### 3. Create PostgreSQL Database
Open **pgAdmin** or **psql** and run:
```sql
CREATE DATABASE usace_vessels;
```

### 4. Initialize Database
```bash
python scripts/usace/init_database.py
```

Expected output:
```
✓ Connected to database
✓ Schema created successfully
✓ All lookup tables populated successfully
✓ DATABASE INITIALIZATION COMPLETE!
```

### 5. Load Data
```bash
python scripts/usace/run_etl.py
```

This loads 45,937 vessels (takes ~2 minutes):
```
✓ Loaded 3,511 operators
✓ Loaded 45,937 vessels
✓ ETL PIPELINE COMPLETE!
```

### 6. Launch Dashboard
```bash
streamlit run src/usace_db/dashboard/app.py
```

Dashboard opens at: **http://localhost:8501**

## 🎯 Dashboard Features

### Fleet Overview Tab
- Total vessel count, operators, avg age, total NRT
- Vessel type pie chart
- Fleet age distribution (Modern/Mature/Legacy)
- Top 15 operators by fleet size

### Operators Tab
- Search operators by name
- View contact info (phone, address, district)
- See fleet composition by vessel type
- List all vessels for an operator

### Vessel Types Tab
- Statistics by vessel type
- Average NRT and age by type
- Self-propelled vs barges breakdown

### Geography Tab
- Vessels by Corps of Engineers district
- Regional distribution (Great Lakes, Mississippi, Coastal)

### Equipment Tab
- Equipment inventory by category
- Vessels with cranes, pumps, conveyors, etc.

### Search & Export Tab
- Search by vessel name or Coast Guard number
- Export filtered results to CSV

## 📊 Sample Queries

Once loaded, try these queries in PostgreSQL:

### All vessels with translated codes:
```sql
SELECT * FROM vessel_analytics_view LIMIT 100;
```

### Top 20 operators:
```sql
SELECT operator_name, COUNT(*) as vessels
FROM vessel_analytics_view
GROUP BY operator_name
ORDER BY vessels DESC
LIMIT 20;
```

### Norfolk district vessels:
```sql
SELECT *
FROM vessel_analytics_view
WHERE district_name = 'Norfolk District';
```

## 🔧 Troubleshooting

### Can't connect to database?
1. Check PostgreSQL is running
2. Verify password in `.env` file
3. Test: `psql -U postgres -c "SELECT 1"`

### Excel files not loading?
1. Check files exist: `dir "data\raw\usace\*.xlsx"`
2. Verify permissions (should be readable)

### Dashboard won't start?
1. Check Streamlit installed: `pip show streamlit`
2. Try different port: `streamlit run app.py --server.port 8502`

## 📁 Key Files

| File | Purpose |
|------|---------|
| `scripts/usace/init_database.py` | Initialize database schema |
| `scripts/usace/run_etl.py` | Load vessel data |
| `src/usace_db/dashboard/app.py` | Launch dashboard |
| `.env` | Database credentials |
| `USACE_README.md` | Full documentation |

## ✅ Success Checklist

- [ ] PostgreSQL installed and running
- [ ] Python packages installed
- [ ] `.env` file configured
- [ ] Database `usace_vessels` created
- [ ] Initialization script ran successfully
- [ ] ETL script loaded 45,937 vessels
- [ ] Dashboard accessible at localhost:8501
- [ ] Can search and filter vessels
- [ ] Can export results to CSV

**🎉 You're ready! Start exploring 45,937 USACE vessels!**

---

**Need help?** See `USACE_README.md` for detailed documentation.
