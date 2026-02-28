# Data Loaders

This directory contains scripts to load all datasets from CSV files into the PostgreSQL database.

## Overview

Five data loaders load 95,480 total records into the database:

| Loader | Records | Description |
|--------|---------|-------------|
| `load_waterways.py` | 6,860 | Waterway network graph (ANODE→BNODE routing) |
| `load_locks.py` | 80 | Lock facilities with dimensional constraints |
| `load_docks.py` | 29,645 | Navigation facilities and docks |
| `load_tonnages.py` | 6,860 | Cargo volumes by commodity type |
| `load_vessels.py` | 52,035 | Vessel registry with beam/draft specifications |

## Prerequisites

1. **PostgreSQL 15+ with PostGIS** installed and running
2. **Database created:**
   ```bash
   createdb barge_db
   psql -d barge_db -c "CREATE EXTENSION postgis;"
   psql -d barge_db -c "CREATE EXTENSION postgis_topology;"
   ```
3. **Schema loaded:**
   ```bash
   psql -d barge_db -f src/db/schema.sql
   ```
4. **Python dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Environment configured:**
   ```bash
   cp .env.example .env
   # Edit .env with your database password
   ```

## Usage

### Option 1: Load All Data (Recommended)

Run the master loader to load all datasets in the correct order:

```bash
python src/data_loaders/load_all.py
```

This will:
- Verify database connection and PostGIS
- Load all 5 datasets in dependency order
- Verify expected row counts
- Report success/failure status

Expected output:
```
✓ ALL DATA LOADED SUCCESSFULLY!
  Phase 1 (Data Loading) is now complete.
  Next: Implement routing engine (Phase 2)
```

### Option 2: Load Individual Datasets

You can run each loader individually:

```bash
# Must be run first (builds routing graph)
python src/data_loaders/load_waterways.py

# Can run in any order
python src/data_loaders/load_locks.py
python src/data_loaders/load_docks.py
python src/data_loaders/load_vessels.py

# Must run AFTER waterways (depends on LINKNUM foreign key)
python src/data_loaders/load_tonnages.py
```

## Dependencies

**Load Order Matters:**
- `load_tonnages.py` requires `load_waterways.py` to be completed first (LINKNUM foreign key)
- All others can run in any order

## Features

### Common Features (All Loaders)
- ✅ UTF-8 BOM handling (`encoding='utf-8-sig'`)
- ✅ Null value handling with type conversion
- ✅ Progress bars (tqdm) for batch operations
- ✅ Batch inserts (1000 records per batch) for performance
- ✅ Table truncation before loading (fresh load each time)
- ✅ Transaction management with commit/rollback
- ✅ Summary statistics after loading
- ✅ Error handling with detailed messages

### Waterways Loader Special Features
- Builds NetworkX DiGraph for routing engine
- Saves graph to `models/waterway_graph.pkl` for fast loading
- Graph structure: ANODE → BNODE edges with attributes (linknum, length, rivername)

## Verification

After loading, verify the data:

```bash
# Check table counts
python src/config/database.py

# Expected output:
# Table row counts:
#   waterway_links: 6,860
#   locks: 80
#   docks: 29,645
#   link_tonnages: 6,860
#   vessels: 52,035
#   computed_routes: 0
```

Or use SQL:
```bash
psql -d barge_db -c "SELECT COUNT(*) FROM waterway_links;"
psql -d barge_db -c "SELECT COUNT(*) FROM locks;"
psql -d barge_db -c "SELECT COUNT(*) FROM docks;"
psql -d barge_db -c "SELECT COUNT(*) FROM link_tonnages;"
psql -d barge_db -c "SELECT COUNT(*) FROM vessels;"
```

## Data Quality Checks

```sql
-- Check for nulls in critical fields
SELECT COUNT(*) FROM waterway_links WHERE linknum IS NULL;  -- Should be 0
SELECT COUNT(*) FROM locks WHERE width IS NULL;  -- May have nulls
SELECT COUNT(*) FROM docks WHERE latitude IS NULL;  -- May have nulls
SELECT COUNT(*) FROM vessels WHERE beam IS NULL;  -- May have nulls

-- Check graph connectivity
SELECT COUNT(DISTINCT anode) as unique_anodes FROM waterway_links;
SELECT COUNT(DISTINCT bnode) as unique_bnodes FROM waterway_links;

-- Check tonnage coverage
SELECT COUNT(*) FROM link_tonnages lt
LEFT JOIN waterway_links wl ON lt.linknum = wl.linknum
WHERE wl.linknum IS NULL;  -- Should be 0 (all tonnages have matching waterways)

-- Check dock linkage
SELECT COUNT(*) FROM docks WHERE tows_link_num IS NOT NULL;
```

## Troubleshooting

### "Database connection failed"
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env` file
- Verify username/password are correct

### "PostGIS extension not found"
```bash
psql -d barge_db -c "CREATE EXTENSION postgis;"
psql -d barge_db -c "CREATE EXTENSION postgis_topology;"
```

### "CSV file not found"
- Verify data files exist in `data/` directory
- Check paths in `src/config/settings.py` DATA_FILES dict

### "UnicodeDecodeError"
- All loaders use `encoding='utf-8-sig'` to handle BOM
- If error persists, check CSV file encoding

### "Foreign key constraint violation" (tonnages)
- Ensure `load_waterways.py` completed successfully before `load_tonnages.py`
- Check that waterway_links table is populated

### "Out of memory"
- Reduce batch_size in loader (default 1000)
- For docks and vessels (large datasets), try batch_size=500

## Performance

Typical loading times on standard hardware:

| Loader | Records | Time | Rate |
|--------|---------|------|------|
| Waterways | 6,860 | ~15s | ~450/s |
| Locks | 80 | ~1s | ~80/s |
| Docks | 29,645 | ~45s | ~660/s |
| Tonnages | 6,860 | ~12s | ~570/s |
| Vessels | 52,035 | ~90s | ~580/s |
| **Total** | **95,480** | **~3 min** | **~530/s** |

## Next Steps

After all data is loaded:

1. **Verify graph cache:** Check that `models/waterway_graph.pkl` exists
2. **Test routing:** Implement routing engine in `src/engines/routing_engine.py`
3. **Implement cost engine:** Create `src/engines/cost_engine.py`
4. **Build dashboard:** Start on `dashboard/app.py`

## Implementation Notes

### CSV Column Mapping

Each loader maps CSV columns (UPPERCASE) to database columns (lowercase):
- Waterways: `LINKNUM` → `linknum`, `ANODE` → `anode`, etc.
- Locks: `PMSNAME` → `pmsname`, `WIDTH` → `width`, etc.
- Docks: `NAV_UNIT_NAME` → `nav_unit_name`, etc.
- Tonnages: `TOTALUP` → `totalup`, `COALDOWN` → `coaldown`, etc.
- Vessels: `IMO` → `imo`, `Beam` → `beam`, etc.

### Type Conversions

The `clean_value()` function in each loader:
- Handles `pd.isna()` for null detection
- Converts strings to int/float with error handling
- Returns `None` for nulls (or `0` for tonnages)
- Strips whitespace from strings

### Batch Processing

Large datasets (docks, vessels) use batch inserts:
```python
batch_size = 1000
for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    # Process and insert batch
```

This prevents memory issues and provides progress feedback via tqdm.

## Contributing

When adding new loaders:
1. Follow the existing pattern (see `load_waterways.py` as template)
2. Include `clean_value()` function for type safety
3. Use batch processing for >1000 records
4. Add progress bars with tqdm
5. Include summary statistics
6. Document in this README
7. Add to `load_all.py` in correct dependency order
