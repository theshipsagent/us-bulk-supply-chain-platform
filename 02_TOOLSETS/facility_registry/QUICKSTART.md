# EPA FRS Analytics Tool - Quick Start Guide

## Setup Complete! ✓

Your EPA FRS Analytics Tool is fully configured and ready to use.

## Verification

Run the verification script to confirm everything is working:

```bash
python verify_setup.py
```

## Getting Started (3 Easy Steps)

### Step 1: Download Data

Start with the ECHO simplified files (recommended for initial testing - smaller and faster):

```bash
python cli.py download echo
```

This will download 4 CSV files (~200MB total) to `data/raw/`:
- FRS_FACILITIES.CSV
- FRS_PROGRAM_LINKS.CSV
- FRS_NAICS_CODES.CSV
- FRS_SIC_CODES.CSV

**Alternative**: For the full national dataset (~732MB):
```bash
python cli.py download national
```

### Step 2: Load Data into DuckDB

```bash
python cli.py ingest echo
```

This will:
- Create the DuckDB database at `data/frs.duckdb`
- Load all CSV files into optimized tables
- Create NAICS and SIC lookup tables
- Print a summary with row counts and distributions

### Step 3: Query and Analyze

**Search facilities in Virginia:**
```bash
python cli.py query facilities --state VA
```

**Search chemical manufacturing facilities (NAICS 325):**
```bash
python cli.py query facilities --naics 325 --limit 50
```

**Search by name:**
```bash
python cli.py query facilities --name "waste management" --limit 20
```

**Combine multiple filters:**
```bash
python cli.py query facilities --state VA --naics 325 --city Richmond
```

**Get summary statistics:**
```bash
python cli.py stats summary
```

**View NAICS distribution:**
```bash
python cli.py stats naics-distribution --top 20
```

**Facility count by state:**
```bash
python cli.py stats by-state
```

## Example Workflow

Here's a complete example workflow to find chemical facilities in Virginia:

```bash
# 1. Download data (if not already done)
python cli.py download echo

# 2. Load into database
python cli.py ingest echo

# 3. Get Virginia chemical facilities
python cli.py query facilities --state VA --naics 325

# 4. Get statistics for Virginia
python cli.py stats summary --state VA

# 5. See NAICS distribution in Virginia
python cli.py stats naics-distribution --state VA --top 10

# 6. Look up a specific facility (use a registry_id from previous results)
python cli.py query programs 110000350174
python cli.py query naics 110000350174
```

## Understanding the Output

### Facilities Query Output
Shows a table with:
- `registry_id`: Unique facility identifier (use this for detailed lookups)
- `primary_name`: Facility name
- `location_address`: Street address
- `city_name`, `state_code`, `postal_code`: Location
- `county_name`, `epa_region_code`: Geographic identifiers

### Summary Statistics
Shows:
- Total facility count
- Number of unique states/EPA regions
- Number of unique EPA programs
- Number of unique NAICS codes

### NAICS Distribution
Shows:
- NAICS code or sector
- Description (industry category)
- Facility count (unique facilities)
- Total records (including duplicates across programs)

## CSV Export

To export results to CSV instead of viewing in terminal:

```bash
python cli.py query facilities --state VA --format csv > va_facilities.csv
python cli.py stats by-state --format csv > state_counts.csv
python cli.py stats naics-distribution --format csv > naics_dist.csv
```

## Common NAICS Codes

Use these prefixes to filter by industry:

- `21` - Mining, Quarrying, Oil and Gas
- `22` - Utilities
- `31`, `32`, `33` - Manufacturing
- `324` - Petroleum and Coal Products
- `325` - Chemical Manufacturing
- `562` - Waste Management and Remediation

## Database Location

Your DuckDB database is stored at:
```
data/frs.duckdb
```

You can query it directly with DuckDB CLI or any DuckDB client:
```bash
duckdb data/frs.duckdb
```

## Next Steps

After getting familiar with the basics:

1. **Explore Program Links**: Use `query programs <registry_id>` to see all EPA programs a facility is linked to

2. **Geographic Analysis**: Use state filters and EPA region statistics to understand geographic distribution

3. **Industry Analysis**: Use NAICS filters to analyze specific industries

4. **Data Quality**: Run `python cli.py stats null-rates` to see data completeness

## Troubleshooting

**Download fails:**
- Check internet connection
- Try with `--force` flag to re-download
- Check EPA website status

**Ingest fails:**
- Make sure you ran the download command first
- Check that CSV files exist in `data/raw/`
- Try with `--force` to recreate tables

**No results in queries:**
- Check that you've run the ingest command
- Verify filters (state codes must be uppercase, e.g., 'VA' not 'va')
- Check the database has data: `python cli.py stats summary`

**Module import errors:**
- Install dependencies: `pip install -r requirements.txt`
- Run verification: `python verify_setup.py`

## Help

Get help for any command:
```bash
python cli.py --help
python cli.py download --help
python cli.py query facilities --help
python cli.py stats --help
```

## What's Next?

This is Phase 1 of the tool. Future phases will add:
- **Phase 2**: Entity harmonization (roll up subsidiaries to parent corporations)
- **Phase 3**: Geospatial analysis and interactive maps
- **Future**: Advanced analytics, compliance comparison, data exports

Happy analyzing!
