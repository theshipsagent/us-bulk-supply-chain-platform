# Maritime Voyage Analysis System - Quick Start Guide

## Installation

```bash
# Install required dependency
pip install pandas

# No additional setup needed!
```

## Basic Usage

### Analyze All Data
```bash
python voyage_analyzer.py -i 00_source_files/ -o results/
```

**Expected Output:**
```
================================================================================
MARITIME VOYAGE ANALYSIS SYSTEM
================================================================================
[Stage 1/6] Loading CSV data...
Loaded 304765 records

[Stage 2/6] Preprocessing data and creating events...
Created 304765 event objects

[Stage 3/6] Detecting voyage boundaries...
Detected 41156 voyages

[Stage 4/6] Calculating voyage metrics...
Calculated metrics for 41156 voyages

[Stage 5/6] Analyzing data quality...
Quality analysis complete: 3658 issues found

[Stage 6/6] Generating output files...

================================================================================
PROCESSING COMPLETE
================================================================================
Input files:         36
Total events:        304765
Total voyages:       41156
Complete voyages:    40491
Completeness rate:   98.4%
Quality issues:      3658

Output files:
  - results\voyage_summary.csv
  - results\event_log.csv
  - results\quality_report.txt
================================================================================
```

## Common Use Cases

### 1. Analyze Specific Vessel
```bash
python voyage_analyzer.py -i 00_source_files/ -o vessel_report/ -v "Aquadonna"
```

**What it does:**
- Filters all data for vessels matching "Aquadonna" (partial match)
- Finds voyages for that vessel only
- Generates focused reports

### 2. Analyze Date Range
```bash
python voyage_analyzer.py -i 00_source_files/ -o monthly_report/ -s 2025-01-01 -e 2025-01-31
```

**What it does:**
- Analyzes only events in January 2025
- Useful for monthly reports
- Filters by event timestamp

### 3. Combine Filters
```bash
python voyage_analyzer.py -i 00_source_files/ -o combined/ -v "Carnival" -s 2024-01-01 -e 2024-12-31
```

**What it does:**
- Finds all Carnival ships in 2024
- Generates annual report for that vessel group

### 4. Debug Mode
```bash
python voyage_analyzer.py -i 00_source_files/ -o debug_results/ --verbose
```

**What it does:**
- Shows detailed processing steps
- Displays warnings for each orphaned event
- Helpful for troubleshooting data issues

## Understanding the Outputs

### voyage_summary.csv
One row per voyage with summary metrics.

**Key Columns:**
- `TotalPortTimeHours`: How long the voyage took (Cross In to Cross Out)
- `TransitTimeHours`: Time spent moving
- `AnchorTimeHours`: Time spent at anchorage
- `TerminalTimeHours`: Time spent at terminals
- `IsComplete`: "Yes" if voyage has both Cross In and Cross Out

**Example Row:**
```
VoyageID: 1013676_20250111_002600
Vessel: Aquadonna (IMO: 1013676)
Total Port Time: 132.00 hours (5.5 days)
Transit Time: 31.20 hours
Anchor Time: 63.95 hours (at Grandview Upr Anch)
Terminal Time: 36.85 hours (at Convent Marine Terminal)
```

### event_log.csv
Detailed event-by-event timeline for each voyage.

**Use Cases:**
- Trace exactly what happened during a voyage
- See time between each event
- Verify calculations
- Audit vessel movements

**Example Events:**
```
2025-01-11 00:26 - VOYAGE_START (Enter SWP Cross)
2025-01-11 16:28 - ANCHOR_ARRIVE (Grandview Upr Anch) [16.03 hrs in transit]
2025-01-14 08:25 - ANCHOR_DEPART (Grandview Upr Anch) [63.95 hrs at anchor]
2025-01-14 09:59 - TERMINAL_ARRIVE (Convent Marine Terminal) [1.57 hrs in transit]
2025-01-15 22:50 - TERMINAL_DEPART (Convent Marine Terminal) [36.85 hrs at terminal]
2025-01-16 12:26 - VOYAGE_END (Exit SWP Cross) [13.60 hrs in transit]
```

### quality_report.txt
Human-readable report on data quality.

**Contains:**
- Summary statistics
- Issue breakdown by type
- Top problematic vessels
- Detailed issue list
- Recommendations

**Common Issues:**
- `MISSING_CROSS_OUT`: Voyage didn't exit (vessel still in port or data incomplete)
- `ORPHANED_ARRIVAL`: Arrival event without matching departure
- `ORPHANED_DEPARTURE`: Departure without prior arrival

## Interpreting Results

### Complete Voyage (Ideal Case)
```
VoyageID: 1013676_20250111_002600
IsComplete: Yes
Total Port Time: 132.00 hours
Transit + Anchor + Terminal = 31.20 + 63.95 + 36.85 = 132.00 ✓
Quality Flags: (none)
```

### Incomplete Voyage
```
VoyageID: 303174162_20181102_205800
IsComplete: No
Total Port Time: (empty - cannot calculate)
Quality Flags: MISSING_CROSS_OUT
```
**Reason:** Vessel entered but never exited (still in port or data gap)

### Voyage with Issues
```
VoyageID: 8512956_20181219_175100
IsComplete: No
Transit Time: 18.75 hours
Anchor Time: 219.87 hours (unusual - very long)
Quality Flags: MISSING_CROSS_OUT,ORPHANED_ARRIVAL
```
**Reason:** Missing exit event and arrival without departure

## Tips & Tricks

### Finding Specific Voyages
```bash
# Find all voyages for a vessel by IMO
python voyage_analyzer.py -i 00_source_files/ -o results/ -v "9138850"

# Find all voyages in Q1 2025
python voyage_analyzer.py -i 00_source_files/ -o q1_2025/ -s 2025-01-01 -e 2025-03-31
```

### Working with Output Files

**Excel/Spreadsheet:**
1. Open voyage_summary.csv in Excel
2. Sort by TotalPortTimeHours (descending) to find longest voyages
3. Filter IsComplete = "Yes" for reliable metrics
4. Filter QualityFlags = (empty) for cleanest data

**Python Analysis:**
```python
import pandas as pd

# Load results
df = pd.read_csv('results/voyage_summary.csv')

# Find average port time for complete voyages
complete = df[df['IsComplete'] == 'Yes']
avg_port_time = complete['TotalPortTimeHours'].mean()
print(f"Average port time: {avg_port_time:.2f} hours")

# Find vessels with longest anchor times
top_anchored = df.nlargest(10, 'AnchorTimeHours')
print(top_anchored[['VesselName', 'AnchorTimeHours']])
```

## Troubleshooting

### "File not found" Error
```
ERROR - File not found: Input path does not exist: 00_source_files/
```
**Solution:** Check the path is correct. Use absolute path if needed:
```bash
python voyage_analyzer.py -i "G:\My Drive\LLM\project_mrtis\00_source_files" -o results/
```

### "No CSV files found" Error
```
ERROR - No CSV files found in: data/
```
**Solution:** Make sure the directory contains .csv files

### Low Completeness Rate
```
Completeness rate: 45.0%
```
**Possible Causes:**
- Data covers ongoing voyages (vessels still in port)
- Data collection incomplete
- Filtered to a date range that cuts off voyages

**Check:** Look at quality_report.txt for issue breakdown

### High Issue Count
```
Quality issues: 15000
```
**Check quality_report.txt:**
- If mostly ORPHANED_ARRIVAL: Missing departure events in source data
- If mostly MISSING_CROSS_OUT: Vessels still in port or incomplete data collection

## Performance Notes

- **Small datasets** (<1000 events): < 1 second
- **Medium datasets** (10K-50K events): 5-10 seconds
- **Large datasets** (300K+ events): 10-15 seconds

**Memory:** Handles 300K+ events with minimal memory usage

## Getting Help

1. Check README.md for detailed documentation
2. Review VERIFICATION.md for example outputs
3. Run with --verbose flag to see detailed processing
4. Check quality_report.txt for data-specific issues

## Next Steps

After analyzing your data:
1. Review quality_report.txt to understand data completeness
2. Open voyage_summary.csv to see voyage-level metrics
3. Use event_log.csv to drill into specific voyages
4. Filter results by vessel or date range for focused analysis
5. Import CSVs into your preferred analytics tool (Excel, Python, R, Tableau, etc.)

---

**Need more help?** Check README.md for complete documentation.
