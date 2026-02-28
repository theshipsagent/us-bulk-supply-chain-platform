# 📈 USACE Historical Data Analysis Guide

Complete guide for downloading, loading, and analyzing historical vessel data to track trends over time.

## 🎯 What You'll Get

With historical data loaded, you can analyze:
- **Year-over-year fleet growth** - Track total vessel and operator counts
- **Operator expansion/contraction** - See which companies are growing or shrinking
- **Vessel type trends** - Identify shifts in fleet composition
- **Geographic changes** - Track regional vessel distribution over time
- **Equipment adoption** - Monitor new equipment uptake
- **Fleet age evolution** - Watch fleet modernization trends
- **Market share dynamics** - Analyze competitive positioning

---

## 📥 Step 1: Download Historical Data

### Manual Download (Recommended)

The USACE library sites block automated scraping, so download manually:

1. **Visit:** https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/WCSC-Vessel-Characteristics/

2. **For each year (2020-2023), download 9 files:**
   - TS Operator File (TS{YY}OP.xlsx)
   - TS Vessel File (TS{YY}VS.xlsx)
   - Self-Propelled Vessels (selfpr{YY}.xlsx)
   - Deck Barges (deck{YY}.xlsx)
   - Dry Covered Barges (drycv{YY}.xlsx)
   - Dry Open Barges (dryop{YY}.xlsx)
   - Tank Barges (tankb{YY}.xlsx)
   - Tow Boats (towb{YY}.xlsx)
   - Other Dry Barges (otdbrg{YY}.xlsx)

3. **Organize by year:**
```
project_us_flag/
└── data/
    └── raw/
        └── usace/
            ├── 2020/
            │   ├── 2020 TS OP TS20OP.xlsx
            │   ├── 2020 TS VS TS20VS.xlsx
            │   └── ... (7 more files)
            ├── 2021/
            │   └── ... (9 files)
            ├── 2022/
            │   └── ... (9 files)
            └── 2023/
                └── ... (9 files) ← Already have this
```

---

## 🔧 Step 2: Load Historical Data

### Load Multiple Years
```bash
cd "G:\My Drive\LLM\project_us_flag"

# Load specific years
python scripts/usace/load_historical_data.py --years 2020,2021,2022,2023

# Or load all years found
python scripts/usace/load_historical_data.py --all
```

### What Happens
1. ✅ Reads Excel files for each year
2. ✅ Loads operators and vessels into database
3. ✅ Sets `fleet_year` field for tracking
4. ✅ Refreshes materialized view
5. ✅ Generates summary statistics

### Expected Output
```
HISTORICAL USACE VESSEL DATA LOADER
====================================================================
Loading years: [2020, 2021, 2022, 2023]

✓ Connected to database
✓ Historical schema extensions applied

====================================================================
Loading 2020 data...
====================================================================
✓ Loaded 3,421 operators and 43,892 vessels
✓ 2020 data loaded successfully

====================================================================
Loading 2021 data...
====================================================================
✓ Loaded 3,456 operators and 44,523 vessels
✓ 2021 data loaded successfully

...

Data by Year:
  2020: 43,892 vessels
  2021: 44,523 vessels
  2022: 45,201 vessels
  2023: 45,937 vessels

HISTORICAL DATA LOAD COMPLETE!
  Successful: 4 years
  Time elapsed: 320.5 seconds
```

---

## 📊 Step 3: Analyze Historical Trends

### Option A: Dashboard (Visual)

Launch the dashboard:
```bash
streamlit run src/usace_db/dashboard/app.py
```

Navigate to **"📈 Historical Trends"** tab to see:

1. **Fleet Size Trend**
   - Line charts showing vessel and operator counts over time
   - Automatic growth rate calculations

2. **Year Comparison**
   - Side-by-side comparison of any two years
   - Metrics: Total vessels, operators, avg NRT, total NRT
   - Percent change calculations

3. **Fleet Age Distribution**
   - Stacked area chart showing age composition
   - Categories: Modern (0-10 yrs), Mature (11-20), Aging (21-30), Legacy (30+)

4. **Top Growing Operators**
   - Bar chart of operators with highest growth rates
   - Shows percent change year-over-year

5. **Vessel Type Trends**
   - Interactive line charts for each vessel type
   - Track shifts in fleet composition

### Option B: SQL Queries (Data Analysis)

#### Fleet Growth Trend
```sql
SELECT * FROM v_fleet_size_by_year;
```

Output:
```
fleet_year | vessel_count | operator_count | avg_nrt | total_nrt | avg_age
-----------+--------------+----------------+---------+-----------+---------
2020       | 43,892       | 3,421          | 2,145   | 94,168,540| 28.3
2021       | 44,523       | 3,456          | 2,162   | 96,282,726| 28.1
2022       | 45,201       | 3,489          | 2,178   | 98,427,678| 27.9
2023       | 45,937       | 3,511          | 2,195   | 100,832,315| 27.5
```

#### Compare Two Years
```sql
SELECT * FROM compare_years(2022, 2023);
```

Output:
```
metric              | year1_value | year2_value | change | percent_change
--------------------+-------------+-------------+--------+---------------
Total Vessels       | 45,201      | 45,937      | 736    | 1.63
Total Operators     | 3,489       | 3,511       | 22     | 0.63
Average NRT         | 2,178.45    | 2,195.32    | 16.87  | 0.77
Total NRT           | 98,427,678  | 100,832,315 | 2,404,637 | 2.44
```

#### Top Growing Operators
```sql
SELECT operator_name, vessel_count, prev_year_count, percent_change
FROM v_operator_trends
WHERE fleet_year = 2023 AND percent_change IS NOT NULL
ORDER BY percent_change DESC
LIMIT 20;
```

#### Vessel Type Trends
```sql
SELECT fleet_year, vessel_type, vessel_count
FROM v_vessel_type_trends
WHERE vessel_type = 'Self-Propelled, Dry Cargo'
ORDER BY fleet_year;
```

#### New vs Retired Vessels
```sql
SELECT * FROM v_vessel_lifecycle ORDER BY fleet_year;
```

#### District Trends
```sql
SELECT district_name, fleet_year, vessel_count
FROM v_district_trends
WHERE district_name = 'Norfolk District'
ORDER BY fleet_year;
```

#### Operator-Specific Trend
```sql
SELECT *
FROM v_operator_trends
WHERE operator_name ILIKE '%ACBL%'  -- American Commercial Barge Line
ORDER BY fleet_year;
```

#### Market Share Trends
```python
# In Python/pandas
import historical_queries
market_share = historical_queries.get_market_share_trends(db, top_n=10)
```

---

## 📈 Use Cases

### 1. Market Analysis
**Question:** Which operators are gaining market share?

```sql
SELECT operator_name, fleet_year, market_share_pct
FROM (
    -- Get market share query from dashboard
) AS market_data
WHERE operator_name IN ('TOP_OPERATOR_1', 'TOP_OPERATOR_2')
ORDER BY fleet_year;
```

### 2. Fleet Modernization
**Question:** Is the fleet getting younger or older?

```sql
SELECT * FROM v_fleet_age_trends ORDER BY fleet_year;
```

**Dashboard:** View stacked area chart in Historical Trends tab.

### 3. Regional Shifts
**Question:** Are vessels moving between regions?

```sql
SELECT series_name, fleet_year, COUNT(*) as vessels
FROM vessel_analytics_view
WHERE fleet_year BETWEEN 2020 AND 2023
GROUP BY series_name, fleet_year
ORDER BY fleet_year, series_name;
```

### 4. Equipment Adoption
**Question:** How fast are operators adopting new equipment?

```sql
SELECT * FROM v_equipment_trends
WHERE equipment_name = 'Crane'
ORDER BY fleet_year;
```

### 5. Competitive Intelligence
**Question:** How does my growth compare to competitors?

```python
# Dashboard: Operators tab → Search your company → View growth trend
# Or SQL:
SELECT * FROM v_operator_trends
WHERE operator_name IN ('YOUR_COMPANY', 'COMPETITOR_A', 'COMPETITOR_B')
ORDER BY fleet_year, operator_name;
```

---

## 🛠️ Advanced Analysis

### Export Historical Data
```sql
-- Export fleet trend to CSV
COPY (SELECT * FROM v_fleet_size_by_year) TO '/tmp/fleet_trend.csv' CSV HEADER;
```

### Custom Dashboards
Use the `historical_queries.py` functions in Jupyter notebooks:

```python
import sys
sys.path.append('src')

from usace_db.database.connection import DatabaseConnection
from usace_db.dashboard import historical_queries

db = DatabaseConnection()
db.connect()

# Get fleet size trend
trend = historical_queries.get_fleet_size_trend(db)

# Plot with matplotlib
import matplotlib.pyplot as plt
plt.plot(trend['fleet_year'], trend['vessel_count'])
plt.title('Fleet Size Trend')
plt.show()
```

### Forecasting
With multiple years of data, you can build predictive models:

```python
import pandas as pd
from sklearn.linear_model import LinearRegression

# Load historical data
trend = historical_queries.get_fleet_size_trend(db)

# Simple linear regression
X = trend[['fleet_year']]
y = trend['vessel_count']
model = LinearRegression().fit(X, y)

# Predict 2024
prediction_2024 = model.predict([[2024]])
print(f"Predicted vessels in 2024: {prediction_2024[0]:,.0f}")
```

---

## 🔍 Troubleshooting

### No historical data showing?
1. **Check data loaded:**
   ```sql
   SELECT fleet_year, COUNT(*) FROM vessels GROUP BY fleet_year;
   ```
2. **Verify schema extensions applied:**
   ```sql
   SELECT * FROM get_available_years();
   ```
3. **Re-apply schema if needed:**
   ```bash
   python scripts/usace/init_database.py
   ```

### Duplicate data?
If you accidentally loaded the same year twice:
```sql
-- Check for duplicates
SELECT vessel_id, fleet_year, COUNT(*)
FROM vessels
GROUP BY vessel_id, fleet_year
HAVING COUNT(*) > 1;

-- Remove duplicates (keep first occurrence)
DELETE FROM vessels a USING vessels b
WHERE a.vessel_id = b.vessel_id
  AND a.fleet_year = b.fleet_year
  AND a.created_at > b.created_at;
```

### Slow queries?
Refresh materialized view:
```sql
REFRESH MATERIALIZED VIEW vessel_analytics_view;
VACUUM ANALYZE vessels;
VACUUM ANALYZE operators;
```

---

## 📚 Database Schema

### Historical Views Added
- `v_fleet_size_by_year` - Aggregate fleet stats by year
- `v_vessel_type_trends` - Vessel type distribution over time
- `v_operator_trends` - Operator growth/decline with YoY change
- `v_district_trends` - Geographic distribution changes
- `v_equipment_trends` - Equipment adoption patterns
- `v_vessel_lifecycle` - New additions and retirements
- `v_fleet_age_trends` - Age composition over time

### Helper Functions
- `get_available_years()` - List years with data
- `compare_years(year1, year2)` - Side-by-side comparison

---

## 🎯 Best Practices

1. **Load data chronologically** - Start with oldest year first
2. **Verify each year** - Check vessel counts match source files
3. **Backup before loading** - `pg_dump usace_vessels > backup.sql`
4. **Document gaps** - Note any missing years in your analysis
5. **Refresh views** - After loading new years, refresh materialized view

---

## 📊 Sample Historical Analysis Report

```sql
-- Executive Summary: 4-Year Fleet Analysis (2020-2023)

-- 1. Overall Growth
SELECT
    MIN(fleet_year) as start_year,
    MAX(fleet_year) as end_year,
    MAX(vessel_count) - MIN(vessel_count) as vessel_growth,
    ROUND((MAX(vessel_count) - MIN(vessel_count))::NUMERIC / MIN(vessel_count) * 100, 1) as growth_pct
FROM v_fleet_size_by_year;

-- 2. Top 10 Fastest Growing Operators
SELECT operator_name, vessel_count, prev_year_count, percent_change
FROM v_operator_trends
WHERE fleet_year = 2023 AND percent_change > 10
ORDER BY percent_change DESC
LIMIT 10;

-- 3. Fleet Modernization Progress
SELECT
    fleet_year,
    SUM(CASE WHEN age_bracket = 'Modern (0-10 yrs)' THEN vessel_count ELSE 0 END) as modern,
    SUM(vessel_count) as total,
    ROUND(SUM(CASE WHEN age_bracket = 'Modern (0-10 yrs)' THEN vessel_count ELSE 0 END)::NUMERIC /
          SUM(vessel_count) * 100, 1) as modern_pct
FROM v_fleet_age_trends
GROUP BY fleet_year
ORDER BY fleet_year;

-- 4. Regional Distribution Changes
SELECT series_name, fleet_year, vessel_count
FROM v_district_trends
GROUP BY series_name, fleet_year
ORDER BY fleet_year, series_name;
```

---

**🎉 With historical data loaded, you can now analyze trends, forecast growth, and track competitive dynamics in the US inland waterway fleet!**

See `USACE_README.md` for database setup and `USACE_QUICKSTART.md` for initial data loading.
