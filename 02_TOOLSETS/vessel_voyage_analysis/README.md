# Maritime Voyage Analysis System

A Python CLI tool for analyzing maritime vessel voyages through the Southwest Pass (SWP), calculating key performance indicators (KPIs) including transit time, anchor time, terminal time, and total port time. **Phase 2 adds voyage segmentation and efficiency analysis.**

## Overview

This system processes maritime event records from CSV files and:
- **Phase 1:** Detects complete voyages from Cross In (entering SWP) to Cross Out (exiting SWP)
- **Phase 1:** Calculates voyage metrics: total port time, transit time, anchor time, terminal time
- **Phase 2:** Segments voyages into inbound/outbound at discharge terminal
- **Phase 2:** Analyzes draft changes to identify loaded vs. ballast conditions
- **Phase 2:** Calculates vessel utilization and efficiency metrics
- Identifies data quality issues: missing events, orphaned arrivals/departures
- Generates detailed CSV outputs and human-readable quality reports

## Dataset

The system has been tested with:
- **304,765 maritime events** (2018-2026)
- **41,156 detected voyages**
- **98.4% completeness rate**

## Installation

### Requirements
- Python 3.8 or higher
- pandas library

### Setup
```bash
# Install dependencies
pip install pandas

# No additional installation needed - the system is ready to use
```

## Usage

### Basic Usage

Process all CSV files in a directory:
```bash
python voyage_analyzer.py -i 00_source_files/ -o results/
```

### Filtering Options

Filter by vessel (partial name or IMO match):
```bash
python voyage_analyzer.py -i 00_source_files/ -o results/ -v "Aquadonna"
python voyage_analyzer.py -i 00_source_files/ -o results/ -v "9012345"
```

Filter by date range:
```bash
python voyage_analyzer.py -i 00_source_files/ -o results/ -s 2025-01-01 -e 2025-12-31
```

Enable verbose logging:
```bash
python voyage_analyzer.py -i 00_source_files/ -o results/ --verbose
```

### Phase 2: Voyage Segmentation (NEW)

Run Phase 2 to segment voyages and calculate efficiency metrics:
```bash
python voyage_analyzer.py -i 00_source_files/ -o results_phase2/ --phase 2
```

**What Phase 2 Does:**
- Splits voyages at the **discharge terminal** (first terminal arrival)
- **Inbound segment:** Cross In → Terminal Arrival
- **Outbound segment:** Terminal Departure → Cross Out
- Compares drafts to determine cargo status (Laden/Ballast)
- Calculates vessel utilization (% of time at terminal vs anchored/transiting)
- Generates aggregate efficiency metrics per vessel

**Custom draft threshold:**
```bash
python voyage_analyzer.py -i 00_source_files/ -o results_phase2/ --phase 2 --draft-threshold 2.0
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-i, --input` | Input CSV file or directory (required) |
| `-o, --output` | Output directory for results (required) |
| `-v, --vessel` | Filter by vessel name or IMO (partial match) |
| `-s, --start-date` | Start date filter (YYYY-MM-DD) |
| `-e, --end-date` | End date filter (YYYY-MM-DD) |
| `--phase` | Analysis phase: 1 (default) or 2 (segmentation) |
| `--draft-threshold` | Draft threshold in feet for cargo classification (default: 1.5) |
| `--verbose` | Enable detailed logging |

## Input Data Format

The system expects CSV files with these columns:
- **IMO**: Vessel IMO number
- **Name**: Vessel name
- **Action**: Event type (Enter, Exit, Arrive, Depart)
- **Time**: Timestamp (MM/DD/YYYY HH:MM format)
- **Zone**: Location/zone name
- **Agent**: Shipping agent
- **Type**: Vessel type (Tank, Bulk, Cont, etc.)
- **Draft**: Vessel draft (e.g., "38ft")
- **Mile**: Mile marker

## Output Files

### Phase 1 Outputs (Always Generated)

The system generates three output files in Phase 1:

### 1. voyage_summary.csv
Summary of all detected voyages with calculated metrics.

**Columns:**
- VoyageID: Unique identifier ({IMO}_{CrossInTimestamp})
- IMO: Vessel IMO number
- VesselName: Vessel name
- CrossInTime: Voyage start time
- CrossOutTime: Voyage end time
- TotalPortTimeHours: Total time in port (Cross Out - Cross In)
- TransitTimeHours: Time moving between locations
- AnchorTimeHours: Total time at anchorage
- TerminalTimeHours: Total time at terminals
- NumAnchorStops: Number of anchorage stops
- NumTerminalStops: Number of terminal stops
- IsComplete: Whether voyage has Cross Out event
- QualityFlags: Comma-separated quality issues

**Example:**
```csv
VoyageID,IMO,VesselName,CrossInTime,CrossOutTime,TotalPortTimeHours,TransitTimeHours,AnchorTimeHours,TerminalTimeHours,NumAnchorStops,NumTerminalStops,IsComplete,QualityFlags
1013676_20250111_002600,1013676,Aquadonna,2025-01-11 00:26:00,2025-01-16 12:26:00,132.00,31.20,63.95,36.85,1,1,Yes,
```

### 2. event_log.csv
Detailed log of all events in chronological order.

**Columns:**
- VoyageID: Associated voyage identifier
- IMO: Vessel IMO number
- VesselName: Vessel name
- EventType: Classified event type (VOYAGE_START, ANCHOR_ARRIVE, etc.)
- EventTime: Event timestamp
- Zone: Location/zone name
- ZoneType: Zone classification (CROSS_IN, CROSS_OUT, ANCHORAGE, TERMINAL)
- Action: Raw action (Enter, Exit, Arrive, Depart)
- DurationToNextEventHours: Time until next event
- NextEventType: Type of next event
- Draft: Vessel draft (feet)
- VesselType: Vessel classification

**Example:**
```csv
VoyageID,IMO,VesselName,EventType,EventTime,Zone,ZoneType,Action,DurationToNextEventHours,NextEventType,Draft,VesselType
1013676_20250111_002600,1013676,Aquadonna,VOYAGE_START,2025-01-11 00:26:00,SWP Cross,CROSS_IN,Enter,16.03,Arrive ANCHORAGE,22.0,Bulk
1013676_20250111_002600,1013676,Aquadonna,ANCHOR_ARRIVE,2025-01-11 16:28:00,Grandview Upr Anch,ANCHORAGE,Arrive,63.95,Depart ANCHORAGE,22.0,
```

### 3. quality_report.txt
Human-readable quality analysis report.

**Contents:**
- Summary statistics (total voyages, completeness rate, issues)
- Issues by type (MISSING_CROSS_OUT, ORPHANED_ARRIVAL, etc.)
- Issues by severity (ERROR, WARNING, INFO)
- Top problematic vessels
- Detailed issue list with descriptions
- Recommendations for data quality improvements

---

### Phase 2 Outputs (Only with --phase 2)

When running with `--phase 2`, two additional files are generated:

### 4. voyage_segments.csv (Phase 2)
Inbound/outbound breakdown of each voyage.

**Key Columns:**
- **Inbound Segment:** CrossInTime, CrossInDraft, FirstTerminalArrivalTime, FirstTerminalArrivalDraft, InboundDurationHours
- **Discharge Terminal:** DischargeTerminalZone, DischargeTerminalFacility
- **Outbound Segment:** FirstTerminalDepartureTime, FirstTerminalDepartureDraft, CrossOutTime, CrossOutDraft, OutboundDurationHours
- **Port Operations:** PortDurationHours (time at terminal), TotalPortTimeHours
- **Draft Analysis:** DraftDeltaFt (outbound - inbound), CargoStatus (Laden/Ballast), EstimatedCargoTonnes
- **Efficiency:** VesselUtilizationPct (% time at terminal vs total port time)
- **Quality:** HasDischargeTerminal, IsComplete, QualityNotes

**Example Row:**
```csv
VoyageID,SegmentID,IMO,VesselName,CrossInTime,CrossInDraft,...
1024429_20260118_110500,1024429_..._SEGMENT,1024429,Ssi Formidable II,
  2026-01-18 11:05:00,29.0,                    # Cross In
  2026-01-18 21:28:00,29.0,                    # Terminal Arrival
  Nashville Ave A,Nashville Ave,              # Discharge Terminal
  10.38,46.68,8.87,                           # Inbound, Port, Outbound durations
  65.93,0.00,Ballast,70.8,Yes,Yes            # Total, Draft delta, Status, Utilization
```

### 5. efficiency_metrics.csv (Phase 2)
Aggregated statistics per vessel (all voyages combined).

**Columns:**
- IMO, VesselName
- TotalVoyages, CompleteVoyages
- AvgInboundDurationHours, AvgOutboundDurationHours, AvgPortDurationHours
- AvgVesselUtilizationPct
- MostFrequentDischargeTerminal
- TotalCargoEstimateTonnes, AvgCargoPerVoyageTonnes

**Use Cases:**
- Compare vessel efficiency (utilization %)
- Identify vessels with longest inbound/outbound times
- Find most common terminals per vessel
- Track cargo patterns over multiple voyages

---

## How It Works

### Processing Pipeline

The system runs through 6 stages:

1. **Data Loading**: Load and consolidate CSV files, apply filters, remove duplicates
2. **Preprocessing**: Parse timestamps and drafts, classify zones, create Event objects
3. **Voyage Detection**: Identify voyage boundaries (Cross In → Cross Out)
4. **Time Calculation**: Calculate all voyage metrics (transit, anchor, terminal times)
5. **Quality Analysis**: Detect and categorize data quality issues
6. **Output Generation**: Write CSV files and quality report

### Zone Classification

Events are classified into zone types:
- **CROSS_IN**: Enter SWP Cross
- **CROSS_OUT**: Exit SWP Cross
- **ANCHORAGE**: Anchorage zones (e.g., "9 Mile Anch", "SWP Anch")
- **TERMINAL**: Terminal/buoy zones (e.g., "Shell Norco", "136 Buoys")

### Time Calculations

**Transit Time**: Time spent moving between locations
- Cross In → First Arrive
- Each Depart → Next Arrive
- Last Depart → Cross Out

**Anchor Time**: Sum of all (Arrive Anchorage → Depart Anchorage) durations

**Terminal Time**: Sum of all (Arrive Terminal → Depart Terminal) durations

**Total Port Time**: Cross Out - Cross In (only for complete voyages)

### Quality Issues Detected

| Issue Type | Severity | Description |
|------------|----------|-------------|
| MISSING_CROSS_OUT | WARNING | Voyage missing Cross Out event |
| MISSING_CROSS_IN | WARNING | Events without Cross In |
| ORPHANED_ARRIVAL | WARNING | Arrival without matching departure |
| ORPHANED_DEPARTURE | WARNING | Departure without matching arrival |
| OUT_OF_SEQUENCE | ERROR | Events in wrong chronological order |
| NEGATIVE_DURATION | ERROR | Negative time duration calculated |
| TIME_GAP | WARNING | Gap > 24 hours between events |

## Project Structure

```
project_mrtis/
├── src/
│   ├── models/
│   │   ├── event.py           # Event data model
│   │   ├── voyage.py          # Voyage data model
│   │   └── quality_issue.py   # Quality issue tracking
│   ├── data/
│   │   ├── loader.py          # CSV loading and consolidation
│   │   ├── preprocessor.py    # Data cleaning and Event creation
│   │   └── zone_classifier.py # Zone type classification
│   ├── processing/
│   │   ├── voyage_detector.py # Voyage boundary detection
│   │   ├── time_calculator.py # Time interval calculations
│   │   └── quality_analyzer.py# Data quality validation
│   └── output/
│       ├── csv_writer.py      # CSV output generation
│       └── report_writer.py   # Human-readable reports
├── 00_source_files/           # Input CSV files
├── voyage_analyzer.py         # Main CLI entry point
└── README.md                  # This file
```

## Examples

### Example 1: Analyze all data
```bash
python voyage_analyzer.py -i 00_source_files/ -o results_all/
```

**Output:**
```
Input files:         36
Total events:        304,765
Total voyages:       41,156
Complete voyages:    40,491
Completeness rate:   98.4%
Quality issues:      3,658
```

### Example 2: Analyze specific vessel
```bash
python voyage_analyzer.py -i 00_source_files/ -o results_aquadonna/ -v "Aquadonna"
```

**Output:**
```
Total events:        6
Total voyages:       1
Complete voyages:    1
Completeness rate:   100.0%
Quality issues:      0
```

### Example 3: Analyze date range
```bash
python voyage_analyzer.py -i 00_source_files/ -o results_2025/ -s 2025-01-01 -e 2025-12-31
```

## Performance

- Processes **~300K events** in under 10 seconds
- Memory efficient streaming of CSV files
- Handles large datasets (multiple years) without issue
- Parallel-capable architecture for future scaling

## Validation

The system has been validated with:
- Manual spot-checks of voyage calculations
- Verification of time arithmetic (transit + anchor + terminal ≈ total)
- Edge case testing (missing events, orphaned records, incomplete voyages)
- Full dataset processing (2018-2026)

## Data Quality Statistics

Based on full dataset (2018-2026):
- **98.4% voyage completeness** (40,491 of 41,156 voyages have Cross Out)
- **3,658 quality issues** detected (~0.012 issues per event)
- **Most common issues**: Orphaned arrivals (2,993), Missing Cross Out (665)

## Documentation

### Quick Start Guides
- **QUICK_START.md** - 5-minute getting started guide
- **QUICK_START_SHIP_CHARACTERISTICS.md** - Ship register integration guide

### Phase 2 Documentation
- **PHASE_2_GUIDE.md** - Complete Phase 2 user guide (voyage segmentation & efficiency analysis)
- **PHASE_2_DESIGN.md** - Technical architecture and design decisions

### Feature Guides
- **TERMINAL_CLASSIFICATION_GUIDE.md** - Terminal classification system (detailed)
- **TERMINAL_CLASSIFICATIONS_README.md** - Terminal classifications (overview)
- **SHIP_REGISTER_INTEGRATION_GUIDE.md** - Ship characteristics integration
- **DATA_DICTIONARY_AND_EXCLUSIONS.md** - Zone & vessel analysis

### Technical Documentation
- **BUILD_DOCUMENTATION.md** - Build history and system architecture
- **VERIFICATION.md** - Test results and validation
- **SESSION_HANDOFF.md** - System state and operational details

## Testing

Run the test suites to verify system functionality:

```bash
# Phase 1 tests
python test_terminal_classifications.py
python test_ship_register_integration.py

# Phase 2 tests
python test_voyage_segmentation.py
```

All tests should show: **ALL TESTS PASSING**

## License

Internal use for maritime operations analysis.

## Contact

For questions or issues, contact the maritime operations team.
