# Phase 2: Voyage Segmentation & Efficiency Analysis - User Guide

**Version:** 2.0.0
**Status:** Production Ready
**Date:** 2026-01-30

---

## Overview

Phase 2 extends the Maritime Voyage Analysis System to segment voyages into **inbound** and **outbound** portions, enabling detailed efficiency analysis and draft-based cargo tracking.

### What's New in Phase 2

- **Voyage Segmentation:** Automatically split voyages at the discharge terminal (first terminal arrival)
- **Inbound/Outbound Analysis:** Separate metrics for each voyage segment
- **Draft Comparison:** Identify loaded vs. ballast conditions using draft changes
- **Efficiency Metrics:** Vessel utilization, port idle time, and aggregate statistics
- **New Outputs:** `voyage_segments.csv` and `efficiency_metrics.csv`

---

## Quick Start

### Basic Phase 2 Run

```bash
python voyage_analyzer.py -i 00_source_files -o results_phase2 --phase 2
```

**This generates:**
- All Phase 1 outputs (voyage_summary.csv, event_log.csv, quality_report.txt)
- **NEW:** voyage_segments.csv (427 segments in test run)
- **NEW:** efficiency_metrics.csv (406 vessels aggregated)

### Custom Draft Threshold

```bash
python voyage_analyzer.py -i 00_source_files -o results_phase2 --phase 2 --draft-threshold 2.0
```

**Draft threshold** (default 1.5 ft): Minimum draft change to classify cargo status
- draft_delta > threshold → "Laden Outbound" (picked up cargo)
- draft_delta < -threshold → "Laden Inbound" (delivered cargo)
- |draft_delta| ≤ threshold → "Ballast"

---

## How It Works

### Segmentation Algorithm

**1. Identify Discharge Terminal**
- Find **first terminal arrival** in voyage sequence
- This is the primary cargo exchange point

**2. Split Voyage**
- **Inbound Segment:** Cross In → First Terminal Arrival
- **Outbound Segment:** First Terminal Departure → Cross Out

**3. Extract Metrics**
- Durations (inbound, port, outbound)
- Drafts at key transition points
- Transit and anchor times for each segment

### Example Timeline

```
Cross In (35.0 ft)
    ↓ [Inbound: 10 hours]
First Terminal Arrival (36.0 ft) ← Discharge Terminal
    ↓ [Port Duration: 46 hours]
First Terminal Departure (40.0 ft)
    ↓ [Outbound: 9 hours]
Cross Out (40.0 ft)

Analysis:
- Draft Delta: 40.0 - 36.0 = +4.0 ft
- Cargo Status: "Laden Outbound" (loaded cargo at terminal)
- Vessel Utilization: 46 / 65 = 70.8%
```

---

## Output Files

### 1. voyage_segments.csv

**Purpose:** One row per voyage with inbound/outbound breakdown

**Key Columns:**
- **VoyageID, SegmentID, IMO, VesselName**
- **Inbound Segment:**
  - CrossInTime, CrossInDraft
  - FirstTerminalArrivalTime, FirstTerminalArrivalDraft
  - InboundDurationHours, InboundTransitHours, InboundAnchorHours
- **Discharge Terminal:**
  - DischargeTerminalZone, DischargeTerminalFacility
- **Outbound Segment:**
  - FirstTerminalDepartureTime, FirstTerminalDepartureDraft
  - CrossOutTime, CrossOutDraft
  - OutboundDurationHours, OutboundTransitHours, OutboundAnchorHours
- **Port Operations:**
  - PortDurationHours (time at discharge terminal)
  - TotalPortTimeHours (Cross In to Cross Out)
- **Draft Analysis:**
  - DraftDeltaFt (outbound - inbound)
  - EstimatedCargoTonnes (if TPC available)
  - CargoStatus ("Laden Inbound", "Laden Outbound", "Ballast", "Unknown")
- **Efficiency:**
  - VesselUtilizationPct (port time / total time * 100)
- **Quality:**
  - HasDischargeTerminal, IsComplete, QualityNotes

**Example Row:**
```csv
VoyageID,SegmentID,IMO,VesselName,...
1024429_20260118_110500,1024429_20260118_110500_SEGMENT,1024429,Ssi Formidable II,
  2026-01-18 11:05:00,29.0,                    # Cross In
  2026-01-18 21:28:00,29.0,                    # Terminal Arrival
  Nashville Ave A,Nashville Ave,              # Discharge Terminal
  10.38,0.00,0.00,                            # Inbound (duration, transit, anchor)
  2026-01-20 20:09:00,29.0,                    # Terminal Departure
  2026-01-21 05:01:00,27.0,                    # Cross Out
  8.87,0.00,0.00,                             # Outbound (duration, transit, anchor)
  46.68,65.93,                                # Port duration, Total port time
  0.00,,Ballast,                              # Draft delta, Cargo estimate, Status
  70.8,Yes,Yes,                               # Utilization, Has terminal, Complete
```

---

### 2. efficiency_metrics.csv

**Purpose:** Aggregated statistics per vessel (all voyages combined)

**Columns:**
- **IMO, VesselName**
- **TotalVoyages, CompleteVoyages**
- **AvgInboundDurationHours** (average time Cross In → Terminal)
- **AvgOutboundDurationHours** (average time Terminal → Cross Out)
- **AvgPortDurationHours** (average time at discharge terminal)
- **AvgVesselUtilizationPct** (average % of time at terminal vs total)
- **MostFrequentDischargeTerminal** (terminal used most often)
- **TotalCargoEstimateTonnes** (sum of all cargo estimates)
- **AvgCargoPerVoyageTonnes** (average cargo per voyage)

**Example Row:**
```csv
IMO,VesselName,TotalVoyages,CompleteVoyages,...
9995478,Narrator,1,1,
  11.62,                  # Avg inbound
  10.50,                  # Avg outbound
  30.10,                  # Avg port duration
  57.6,                   # Avg utilization %
  Valero St Charles,,     # Most frequent terminal
```

---

## Interpreting Results

### Cargo Status Classification

| Draft Delta | Cargo Status | Meaning |
|------------|--------------|---------|
| > +1.5 ft | Laden Outbound | Vessel loaded cargo at terminal |
| < -1.5 ft | Laden Inbound | Vessel delivered cargo at terminal |
| -1.5 to +1.5 ft | Ballast | No significant cargo change |

**Change threshold** with `--draft-threshold <feet>`

### Vessel Utilization Grades

| Utilization % | Grade | Interpretation |
|--------------|-------|----------------|
| ≥80% | A | Excellent - minimal waiting time |
| 60-79% | B | Good - some anchorage/transit |
| 40-59% | C | Fair - significant waiting |
| 20-39% | D | Poor - excessive delays |
| <20% | F | Very poor - mostly waiting |

**Higher utilization** = More time at terminal (productive)
**Lower utilization** = More time anchored/transiting (inefficient)

---

## Use Cases

### 1. Identify Inefficient Voyages

```bash
# Find voyages with low utilization (lots of waiting)
awk -F',' '$26 < 40 && $27 == "Yes"' voyage_segments.csv | less
```

Column 26 = VesselUtilizationPct
Column 27 = HasDischargeTerminal

### 2. Compare Inbound vs Outbound Times

```bash
# Check if outbound consistently takes longer (congestion indicator)
cut -d',' -f1,4,11,18 voyage_segments.csv | less
```

Fields: VoyageID, VesselName, InboundDuration, OutboundDuration

### 3. Find Laden vs Ballast Patterns

```bash
# Count cargo statuses
cut -d',' -f25 voyage_segments.csv | sort | uniq -c
```

### 4. Terminal Performance Analysis

```bash
# Average port duration by terminal
cut -d',' -f10,21 voyage_segments.csv | sort | uniq
```

Fields: DischargeTerminalFacility, PortDurationHours

### 5. Vessel Comparison

Open `efficiency_metrics.csv` and sort by:
- **AvgInboundDurationHours** - Which vessels reach terminals fastest?
- **AvgVesselUtilizationPct** - Which vessels have best efficiency?
- **TotalVoyages** - Which vessels are most active?

---

## Edge Cases & Quality Notes

### Voyages Without Terminals

**Behavior:** Treated as inbound segment only (full voyage)

**Example:**
```csv
...,No terminal stops detected - full voyage treated as inbound
```

**Use:** These are typically anchorage-only visits (shifting, awaiting orders, etc.)

### Incomplete Voyages

**Missing Cross Out:**
- Outbound segment = None
- Vessel still in port or data gap

**Quality Notes:**
```
Missing Cross Out event; Missing terminal departure
```

### Multiple Terminals

**Current Implementation:** Only first terminal used as discharge point

**Future Enhancement:** Track all terminal stops and segment between each

---

## Performance Notes

### Processing Speed

**Test Results (2026 Jan data):**
- Events: 3,416
- Voyages: 427
- Segments: 427
- Processing time: **~20 seconds**

**Full Dataset (296K events):**
- Expected Phase 2 overhead: +15-20% (adds ~30 seconds to 2-minute total)

### Memory Usage

- Minimal increase (~50 MB for segment objects)
- No significant change from Phase 1

---

## Troubleshooting

### Issue: Low Cargo Estimate Coverage

**Symptom:** Most segments have blank EstimatedCargoTonnes

**Cause:** TPC (Tonnes Per Centimeter) not available in ships register for many vessels

**Solution:** TPC is specialized data - not all vessels have it. Draft delta and cargo status are still valid.

### Issue: Unexpected Cargo Status

**Symptom:** Vessel shows "Laden Outbound" but you expected "Laden Inbound"

**Cause:** Draft measurements may be reversed, or vessel loaded at discharge terminal

**Solution:**
1. Check draft data quality in event_log.csv
2. Verify discharge terminal is correct (first terminal)
3. Adjust `--draft-threshold` if needed

### Issue: Segments Without Terminal

**Symptom:** Many segments marked "No terminal stops detected"

**Cause:** Voyages that only visited anchorages (no terminal stops)

**Solution:** This is normal for:
- Vessels awaiting berth assignment
- Ship-to-ship transfers
- Crew changes
- Weather delays

---

## CLI Reference

### Phase 2 Specific Flags

```bash
--phase [1|2]
  Default: 1
  Options:
    1 = Phase 1 only (voyage analysis)
    2 = Phase 1 + Phase 2 (segmentation & efficiency)

--draft-threshold <float>
  Default: 1.5
  Unit: Feet
  Purpose: Threshold for cargo status classification
  Example: --draft-threshold 2.0 (stricter classification)
```

### Complete Examples

```bash
# Basic Phase 2
python voyage_analyzer.py -i 00_source_files -o results_p2 --phase 2

# Phase 2 with vessel filter
python voyage_analyzer.py -i 00_source_files -o results_p2 --phase 2 -v "Carnival"

# Phase 2 with date range
python voyage_analyzer.py -i 00_source_files -o results_p2 --phase 2 -s 2026-01-01 -e 2026-01-31

# Phase 2 with custom threshold
python voyage_analyzer.py -i 00_source_files -o results_p2 --phase 2 --draft-threshold 2.0

# Verbose output
python voyage_analyzer.py -i 00_source_files -o results_p2 --phase 2 --verbose
```

---

## Integration with Phase 1

### Phase 1 Outputs (Always Generated)

1. **voyage_summary.csv** - High-level voyage KPIs
2. **event_log.csv** - Detailed event timeline
3. **quality_report.txt** - Data quality issues

### Phase 2 Outputs (Only with --phase 2)

4. **voyage_segments.csv** - Inbound/outbound breakdown
5. **efficiency_metrics.csv** - Aggregate vessel statistics

**All files share common identifiers:**
- VoyageID format: `{IMO}_{CrossIn_Timestamp}`
- IMO and VesselName consistent across all files

**Cross-reference example:**
```bash
# Get voyage details from Phase 1
grep "1024429_20260118_110500" voyage_summary.csv

# Get segment details from Phase 2
grep "1024429_20260118_110500" voyage_segments.csv

# Get all events for this voyage
grep "1024429_20260118_110500" event_log.csv
```

---

## Next Steps

### Explore Your Data

1. **Run Phase 2 on full dataset:**
   ```bash
   python voyage_analyzer.py -i 00_source_files -o results_phase2_full --phase 2
   ```

2. **Open voyage_segments.csv** in Excel/Google Sheets:
   - Sort by VesselUtilizationPct (find inefficient voyages)
   - Filter by CargoStatus (identify laden vs ballast patterns)
   - Group by DischargeTerminalFacility (terminal performance)

3. **Open efficiency_metrics.csv:**
   - Sort by AvgVesselUtilizationPct (find most efficient vessels)
   - Compare AvgInboundDurationHours vs AvgOutboundDurationHours
   - Identify vessels with most voyages (TotalVoyages)

### Custom Analysis

Phase 2 outputs are CSV format - use any tool:
- **Python:** pandas, matplotlib for visualization
- **R:** ggplot2 for statistical analysis
- **Excel:** Pivot tables, charts, conditional formatting
- **Tableau/Power BI:** Interactive dashboards

---

## Support & Documentation

### Related Guides

- **README.md** - System overview and installation
- **QUICK_START.md** - 5-minute getting started guide
- **PHASE_2_DESIGN.md** - Technical architecture and design decisions
- **BUILD_DOCUMENTATION.md** - Development history and technical details

### Testing

Phase 2 has comprehensive test coverage:
```bash
python test_voyage_segmentation.py
```

**8 tests verify:**
- Discharge terminal detection
- Segment time calculations
- Draft analysis
- Efficiency metrics
- Edge cases (no terminal, incomplete voyages)

---

## Appendix: Column Reference

### voyage_segments.csv (29 columns)

| # | Column Name | Type | Description |
|---|------------|------|-------------|
| 1 | VoyageID | String | Unique voyage identifier |
| 2 | SegmentID | String | Unique segment identifier |
| 3 | IMO | String | Vessel IMO number |
| 4 | VesselName | String | Vessel name |
| 5 | CrossInTime | DateTime | Voyage start time |
| 6 | CrossInDraft | Float | Draft at Cross In (feet) |
| 7 | FirstTerminalArrivalTime | DateTime | First terminal arrival |
| 8 | FirstTerminalArrivalDraft | Float | Draft at terminal arrival (feet) |
| 9 | DischargeTerminalZone | String | Terminal zone name |
| 10 | DischargeTerminalFacility | String | Terminal facility name |
| 11 | InboundDurationHours | Float | Inbound segment duration |
| 12 | InboundTransitHours | Float | Inbound transit time |
| 13 | InboundAnchorHours | Float | Inbound anchor time |
| 14 | FirstTerminalDepartureTime | DateTime | First terminal departure |
| 15 | FirstTerminalDepartureDraft | Float | Draft at terminal departure (feet) |
| 16 | CrossOutTime | DateTime | Voyage end time |
| 17 | CrossOutDraft | Float | Draft at Cross Out (feet) |
| 18 | OutboundDurationHours | Float | Outbound segment duration |
| 19 | OutboundTransitHours | Float | Outbound transit time |
| 20 | OutboundAnchorHours | Float | Outbound anchor time |
| 21 | PortDurationHours | Float | Time at discharge terminal |
| 22 | TotalPortTimeHours | Float | Total port time (Cross In to Cross Out) |
| 23 | DraftDeltaFt | Float | Draft change (outbound - inbound) |
| 24 | EstimatedCargoTonnes | Float | Estimated cargo using TPC |
| 25 | CargoStatus | String | Laden Inbound/Outbound/Ballast/Unknown |
| 26 | VesselUtilizationPct | Float | Port time / total time * 100 |
| 27 | HasDischargeTerminal | Boolean | Yes/No |
| 28 | IsComplete | Boolean | Yes/No |
| 29 | QualityNotes | String | Quality issues if any |

### efficiency_metrics.csv (11 columns)

| # | Column Name | Type | Description |
|---|------------|------|-------------|
| 1 | IMO | String | Vessel IMO number |
| 2 | VesselName | String | Vessel name |
| 3 | TotalVoyages | Integer | Total voyages in dataset |
| 4 | CompleteVoyages | Integer | Complete voyages only |
| 5 | AvgInboundDurationHours | Float | Average inbound time |
| 6 | AvgOutboundDurationHours | Float | Average outbound time |
| 7 | AvgPortDurationHours | Float | Average port time |
| 8 | AvgVesselUtilizationPct | Float | Average utilization % |
| 9 | MostFrequentDischargeTerminal | String | Most common terminal |
| 10 | TotalCargoEstimateTonnes | Float | Sum of all cargo estimates |
| 11 | AvgCargoPerVoyageTonnes | Float | Average cargo per voyage |

---

**Phase 2 Status:** ✅ Production Ready
**Last Updated:** 2026-01-30
**All tests passing:** 8/8 ✓
