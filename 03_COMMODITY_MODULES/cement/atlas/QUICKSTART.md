# ATLAS Quick Start Guide

Get up and running with ATLAS in 5 minutes.

## Prerequisites

- Python 3.9+
- EPA FRS database at `../../task_epa_frs/data/frs.duckdb`

## Installation

1. **Install dependencies**:
```bash
cd atlas
pip install -r requirements.txt
```

2. **Verify installation**:
```bash
python verify_installation.py
```

You should see all checks pass with "61,017" facilities loaded.

## Basic Usage

### View Database Statistics
```bash
python cli.py stats
```

**Output**:
```
Total Facilities:          61,017
States Covered:            57
```

### Query Facilities by State
```bash
python cli.py query --state TX --limit 10
```

**Output**: Table of 10 Texas cement facilities

### Query by NAICS Code
```bash
python cli.py query --naics 327310  # Cement manufacturing
```

**Output**: Count of cement manufacturing facilities

### State Breakdown
```bash
python cli.py stats --by-state
```

**Output**: Facility counts by state

### Export to CSV
```bash
python cli.py query --state CA --output california_facilities.csv
```

## Common Queries

### Find All Ready-Mix Concrete Plants
```bash
python cli.py query --naics 327320
```

### Find All Highway Construction Projects
```bash
python cli.py query --naics 237310
```

### Get Top 20 States by Facility Count
```bash
python cli.py stats --by-state | head -25
```

### Search for Specific Company (once entity resolution is enabled)
```bash
python cli.py query --company "CEMEX"
```

## Refresh Data

To reload data from EPA FRS:
```bash
python cli.py refresh
```

This will:
1. Connect to EPA FRS database (read-only)
2. Extract cement-relevant facilities (40+ NAICS codes)
3. Load ~61,000 facilities into ATLAS

**Time**: ~20 seconds

## Configuration

Edit `config/settings.yaml` to change:
- EPA FRS database path
- ATLAS database path
- Fuzzy matching thresholds

Edit `config/naics_cement.yaml` to add/remove NAICS codes.

Edit `config/target_companies.yaml` to add company fuzzy match patterns.

## Troubleshooting

### "Database not found"
Check `config/settings.yaml` and ensure EPA FRS path is correct:
```yaml
data:
  epa_frs:
    path: "../../task_epa_frs/data/frs.duckdb"
```

### "No module named 'duckdb'"
Install dependencies:
```bash
pip install -r requirements.txt
```

### Unicode errors on Windows
Fixed in Phase 0. If you see checkmarks (✓) errors, the CLI has been updated to use `[OK]` instead.

## Next Steps

1. **Explore data**: Run various queries to understand the dataset
2. **Customize**: Add your own NAICS codes or company patterns
3. **Export**: Generate CSV reports for analysis
4. **Integrate**: Use as data source for market reports

## Help

For command help:
```bash
python cli.py --help
python cli.py query --help
python cli.py stats --help
```

## Example Workflow

```bash
# 1. Check what you have
python cli.py stats

# 2. Find California cement manufacturers
python cli.py query --state CA --naics 327310

# 3. Export ready-mix plants in Texas
python cli.py query --state TX --naics 327320 --output tx_readymix.csv

# 4. View state-by-state breakdown
python cli.py stats --by-state | head -30

# 5. Get detailed info about a specific state
python cli.py info --state CA
```

## Documentation

- **Full README**: See `README.md`
- **Implementation Details**: See `PHASE0_COMPLETE.md`
- **Architecture**: See `../ATLAS_PHASE0_SUMMARY.md`

---

**Ready to go!** Start querying cement market data.
