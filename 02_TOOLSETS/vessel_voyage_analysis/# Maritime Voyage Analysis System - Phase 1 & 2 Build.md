# Maritime Voyage Analysis System - Phase 1 & 2 Build

## Project Overview
Build a Python CLI tool that processes maritime vessel event data to analyze port calls, calculate voyage metrics, and segment inbound/outbound voyage patterns. The tool ingests raw event records (Cross In/Out, anchorages, terminals) and produces structured voyage analysis with KPI metrics.

---

## Phase 1: Voyage Data Processing & KPI Calculation

### Input Data Structure
- **Columns (static across all datasets):** IMO, Name, Action, Time, Zone, Agent, Type, Draft, Mile
- **Key Actions:** Cross In, Cross Out, Arrive Anchor, Depart Anchor, Arrive Terminal, Depart Terminal
- **Data Format:** CSV or delimited text file

### Data Model & Definitions

**Voyage:** Complete port call from Cross In (SWP) to Cross Out (SWP)
- A vessel cannot have two concurrent calls between Cross In and Cross Out
- Multiple terminals and anchorages can occur within one voyage
- Missing sequential events should be flagged but not break the voyage chain

**Events (sequential):**
1. Cross In (SWP) - Voyage begins
2. Arrive Anchor/Terminal (multiple possible)
3. Depart Anchor/Terminal (paired with arrival)
4. Cross Out (SWP) - Voyage ends

**Time Calculations:**
- Transit time: time between Cross In and first Anchor/Terminal arrival (and between subsequent departures and arrivals)
- Anchor time: elapsed time between Arrive Anchor and Depart Anchor
- Terminal time: elapsed time between Arrive Terminal and Depart Terminal
- Total port time: Cross In to Cross Out

### Phase 1 Deliverables

**Output 1: Voyage Summary Table**
- Vessel Name, IMO, Voyage ID (Cross In datetime)
- Cross In Time, Cross Out Time
- Total Port Time (hours)
- Total Transit Time (hours)
- Total Anchor Time (hours)
- Total Terminal Time (hours)
- Number of Anchor Stops, Number of Terminal Stops

**Output 2: Detailed Event Log**
- Vessel, Event Type, Event Time, Duration Until Next Event, Location/Zone
- Group by Voyage

**Output 3: Data Quality Report**
- Missing events (gaps between departures and next arrivals)
- Orphaned events (arrivals without departures)
- Timeline anomalies (out-of-sequence timestamps)

### Implementation Requirements
- Parse CSV with flexible delimiters (comma, tab, pipe)
- Handle datetime formats (detect and standardize)
- Group events by vessel and voyage (Cross In → Cross Out boundaries)
- Calculate all time intervals in hours (or hours:minutes)
- Export to CSV and human-readable report format
- CLI arguments: input file path, output directory, optional vessel filter, date range filter

---

## Phase 2: Voyage Segmentation & Inbound/Outbound Analysis

### Voyage Splitting Logic

**Inbound Voyage:** Cross In → First Terminal Arrival (discharge terminal)
- Accumulate all anchor/transit time before discharge terminal
- Record draft at first terminal arrival

**Outbound Voyage:** Depart Discharge Terminal → Cross Out
- Starts immediately after first terminal departure
- Accumulate all anchor/transit time after discharge terminal
- Record draft at departure

**Transition Point:** Discharge terminal (first terminal in sequence where cargo is exchanged)
- If draft changes significantly between inbound and outbound, flag as validation

### Phase 2 Deliverables

**Output 1: Voyage Segment Table**
- Vessel, IMO, Voyage ID
- Inbound: Cross In Time, Terminal Arrival Time, Inbound Duration (hours), Inbound Draft
- Outbound: Terminal Departure Time, Cross Out Time, Outbound Duration (hours), Outbound Draft
- Port Duration (time between inbound arrival and outbound departure at discharge terminal)

**Output 2: Voyage Efficiency Metrics**
- Inbound transit efficiency (hours to discharge terminal)
- Port idle time (time at discharge terminal between arrival and departure)
- Outbound transit efficiency (hours from discharge terminal to Cross Out)
- Draft delta (inbound vs outbound) as cargo indicator

**Output 3: Aggregate Trend Analysis**
- Average inbound/outbound times by vessel
- Seasonal patterns (if data spans multiple months/years)
- Port congestion indicators (growing idle time trends)
- Vessel utilization score

### Implementation Requirements
- Auto-detect discharge terminal (first terminal arrival in voyage sequence)
- Allow manual override for discharge terminal identification
- Flag ambiguous cases (multiple terminals, no clear discharge)
- Calculate draft change between inbound/outbound
- Generate summary and detailed voyage segment reports
- Export comparative analysis (vessel performance over time)
- CLI options: voyage filter, date range, segment analysis mode, draft threshold

---

## CLI Interface Design

### Phase 1 Commands
```
python voyage_analyzer.py --input <file.csv> --output <dir> --phase 1
python voyage_analyzer.py --input <file.csv> --output <dir> --vessel "M/V Claude" --phase 1
python voyage_analyzer.py --input <file.csv> --output <dir> --start-date 2026-01-01 --end-date 2026-03-31 --phase 1
```

### Phase 2 Commands
```
python voyage_analyzer.py --input <file.csv> --output <dir> --phase 2
python voyage_analyzer.py --input <file.csv> --output <dir> --phase 2 --discharge-terminal-mode auto
python voyage_analyzer.py --input <file.csv> --output <dir> --phase 2 --draft-threshold 1.5
```

### Output Files
- `voyage_summary.csv` - KPI metrics per voyage
- `event_log.csv` - Detailed timeline
- `quality_report.txt` - Data gaps and anomalies
- `voyage_segments.csv` - Inbound/outbound breakdown (Phase 2)
- `efficiency_metrics.csv` - Performance analysis (Phase 2)
- `analysis_report.txt` - Human-readable summary

---

## Technical Stack
- **Language:** Python 3.8+
- **Libraries:** pandas, datetime, argparse, csv
- **Error Handling:** Graceful parsing failures, detailed logging
- **Testing Data:** Use the M/V Claude example (01/01/2026 - 01/07/2026 voyage)

---

## Development Notes
- Build Phase 1 core logic first (event grouping, time calculations)
- Phase 2 leverages Phase 1 output (voyage boundaries already established)
- Prioritize data validation and gap reporting
- Make discharge terminal detection flexible (auto vs. manual modes)
- Assume data may have missing events—handle gracefully with flagging
- Focus on CSV I/O and tabular reporting

---

## Success Criteria
✅ Phase 1: Correctly parses all vessel events, groups by voyage, calculates 4 KPI metrics accurately
✅ Phase 2: Segments voyages at discharge terminal, calculates inbound/outbound metrics, identifies efficiency trends
✅ Handles missing data without crashing
✅ CLI is intuitive and accepts multiple filter/mode options
✅ Output reports are clear and actionable for maritime operations analysis