# Phase 2: Voyage Segmentation - Design Document

**Version:** 2.0.0
**Status:** Design Complete - Ready for Implementation
**Date:** 2026-01-30

---

## Overview

Phase 2 extends the Maritime Voyage Analysis System to split voyages into **inbound** and **outbound** segments, enabling detailed efficiency analysis and draft-based cargo tracking.

### Key Concept

**Segmentation Point:** First Terminal Arrival (discharge terminal)
- **Inbound Voyage:** Cross In → First Terminal Arrival
- **Outbound Voyage:** First Terminal Departure → Cross Out

---

## Architecture Design

### 1. New Data Model: VoyageSegment

**File:** `src/models/voyage_segment.py`

```python
@dataclass
class VoyageSegment:
    """Represents inbound and outbound segments of a voyage."""

    # Identifiers
    voyage_id: str              # Reference to parent Voyage
    imo: str
    vessel_name: str
    segment_id: str            # {voyage_id}_SEGMENT

    # Inbound Segment
    cross_in_time: datetime
    cross_in_draft: Optional[float]
    first_terminal_arrival_time: Optional[datetime]
    first_terminal_arrival_draft: Optional[float]
    discharge_terminal_zone: Optional[str]
    discharge_terminal_facility: Optional[str]
    inbound_duration_hours: Optional[float]
    inbound_transit_hours: float = 0.0
    inbound_anchor_hours: float = 0.0

    # Outbound Segment
    first_terminal_departure_time: Optional[datetime]
    first_terminal_departure_draft: Optional[float]
    cross_out_time: Optional[datetime]
    cross_out_draft: Optional[float]
    outbound_duration_hours: Optional[float]
    outbound_transit_hours: float = 0.0
    outbound_anchor_hours: float = 0.0

    # Port Operations
    port_duration_hours: Optional[float]  # Time at discharge terminal
    total_port_time_hours: Optional[float]  # Cross In to Cross Out

    # Draft Analysis
    draft_delta_ft: Optional[float]  # Outbound - Inbound
    estimated_cargo_tonnes: Optional[float]  # Using TPC if available
    cargo_status: Optional[str]  # "Laden Inbound", "Ballast Inbound", "Unknown"

    # Efficiency Metrics
    inbound_efficiency: Optional[float]  # Hours per mile (if available)
    outbound_efficiency: Optional[float]
    port_idle_time_hours: Optional[float]
    vessel_utilization_pct: Optional[float]  # Terminal time / Total time

    # Quality
    has_discharge_terminal: bool = False
    is_complete: bool = False
    quality_notes: Optional[str] = None
```

**Design Rationale:**
- Extends Voyage concept without modifying existing Voyage model
- Stores all inbound/outbound metrics in one place
- Includes draft-based cargo analysis
- Backward compatible with Phase 1

---

### 2. New Processing Module: VoyageSegmenter

**File:** `src/processing/voyage_segmenter.py`

**Purpose:** Split voyages at discharge terminal and calculate segment metrics

**Algorithm:**
```
For each complete Voyage:
    1. Find first terminal arrival event
       - Filter voyage.events for is_terminal_arrive() == True
       - Take first chronologically

    2. If no terminal found:
       - Mark has_discharge_terminal = False
       - Set all outbound metrics to None
       - Set inbound metrics = full voyage metrics
       - Add quality note: "No terminal stops detected"

    3. If terminal found (discharge terminal):
       a. Extract inbound segment:
          - Start: cross_in_event
          - End: first terminal arrival event
          - Draft: event.draft at both points
          - Calculate: inbound_duration, transit, anchor times

       b. Extract outbound segment:
          - Start: first terminal departure event
          - End: cross_out_event (if exists)
          - Draft: event.draft at both points
          - Calculate: outbound_duration, transit, anchor times

       c. Calculate port metrics:
          - port_duration = terminal_depart_time - terminal_arrive_time
          - total_port_time = cross_out_time - cross_in_time

       d. Calculate draft analysis:
          - draft_delta = outbound_draft - inbound_draft
          - If draft_delta > 1.5 ft: cargo_status = "Laden Outbound"
          - If draft_delta < -1.5 ft: cargo_status = "Laden Inbound"
          - Else: cargo_status = "Ballast" or "Unknown"
          - If TPC available: estimated_cargo = draft_delta_m * TPC

    4. Mark as complete if all segments have valid times
```

**Edge Cases:**
- **No terminal stops:** Full voyage treated as inbound segment
- **Multiple terminal stops:** Only first terminal used (per spec)
- **Missing Cross Out:** Outbound segment incomplete
- **Missing draft data:** Draft analysis = None

---

### 3. New Processing Module: EfficiencyCalculator

**File:** `src/processing/efficiency_calculator.py`

**Purpose:** Calculate efficiency and utilization metrics

**Metrics:**

1. **Inbound Transit Efficiency** (if mile data available)
   - Formula: `inbound_transit_hours / total_miles`
   - Unit: Hours per mile
   - Lower is better

2. **Outbound Transit Efficiency** (if mile data available)
   - Formula: `outbound_transit_hours / total_miles`
   - Unit: Hours per mile
   - Lower is better

3. **Port Idle Time**
   - Formula: `port_duration_hours - (loading/unloading activity)`
   - Approximation: Use full port_duration (activity time not tracked)
   - Unit: Hours

4. **Vessel Utilization**
   - Formula: `port_duration_hours / total_port_time_hours * 100`
   - Unit: Percentage
   - Higher is better (more time at terminal vs anchored/transiting)

5. **Aggregate Statistics** (across multiple segments)
   - Average inbound/outbound times by vessel
   - Average by terminal facility
   - Trend analysis (if date ranges span months)

---

### 4. Output Extensions

#### New Output File: `voyage_segments.csv`

**Columns:**
```
VoyageID
SegmentID
IMO
VesselName
CrossInTime
CrossInDraft
FirstTerminalArrivalTime
FirstTerminalArrivalDraft
DischargeTerminalZone
DischargeTerminalFacility
InboundDurationHours
InboundTransitHours
InboundAnchorHours
FirstTerminalDepartureTime
FirstTerminalDepartureDraft
CrossOutTime
CrossOutDraft
OutboundDurationHours
OutboundTransitHours
OutboundAnchorHours
PortDurationHours
TotalPortTimeHours
DraftDeltaFt
EstimatedCargoTonnes
CargoStatus
InboundEfficiency
OutboundEfficiency
PortIdleTimeHours
VesselUtilizationPct
HasDischargeTerminal
IsComplete
QualityNotes
```

#### New Output File: `efficiency_metrics.csv`

**Aggregated Metrics:**
```
VesselName
IMO
TotalVoyages
AvgInboundDurationHours
AvgOutboundDurationHours
AvgPortDurationHours
AvgInboundEfficiency
AvgOutboundEfficiency
AvgVesselUtilizationPct
MostFrequentDischargeTerminal
TotalCargoEstimateTonnes (sum of all voyages)
```

---

### 5. CLI Integration

**Updated CLI:** `voyage_analyzer.py`

**New Flags:**
```bash
--phase [1|2]                      # Default: 1 (backward compatible)
--discharge-terminal-mode [auto]   # Future: allow manual specification
--draft-threshold <float>          # Default: 1.5 (feet)
--segment-output <dir>             # Where to write segment files
```

**Examples:**
```bash
# Run Phase 2 (generates all Phase 1 + Phase 2 outputs)
python voyage_analyzer.py -i 00_source_files -o results_phase2 --phase 2

# Run with custom draft threshold
python voyage_analyzer.py -i 00_source_files -o results_phase2 --phase 2 --draft-threshold 2.0

# Run Phase 1 only (default, backward compatible)
python voyage_analyzer.py -i 00_source_files -o results
```

**Output Behavior:**
- **Phase 1:** Generates voyage_summary.csv, event_log.csv, quality_report.txt (current)
- **Phase 2:** Generates ALL Phase 1 files + voyage_segments.csv + efficiency_metrics.csv

---

### 6. Data Flow

```
Phase 1 Pipeline (Existing):
  DataLoader → DataPreprocessor → VoyageDetector → TimeCalculator → QualityAnalyzer → CSVWriter

Phase 2 Pipeline (Extended):
  [Phase 1 Pipeline] → VoyageSegmenter → EfficiencyCalculator → SegmentCSVWriter

  VoyageSegmenter:
    Input: List[Voyage] (from Phase 1)
    Process: Split at first terminal, extract drafts
    Output: List[VoyageSegment]

  EfficiencyCalculator:
    Input: List[VoyageSegment]
    Process: Calculate metrics, aggregate stats
    Output: Enhanced List[VoyageSegment] + AggregateMetrics

  SegmentCSVWriter:
    Input: List[VoyageSegment] + AggregateMetrics
    Output: voyage_segments.csv + efficiency_metrics.csv
```

---

## Implementation Plan

### Task Breakdown (10 Tasks)

1. ✅ **Design Phase 2 architecture** (this document)
2. Implement VoyageSegment model
3. Implement VoyageSegmenter logic
4. Implement EfficiencyCalculator
5. Add voyage_segments.csv writer
6. Add efficiency_metrics.csv writer
7. Integrate Phase 2 into CLI
8. Create test suite
9. Run end-to-end test with real data
10. Create documentation

---

## Testing Strategy

### Unit Tests

**File:** `test_voyage_segmentation.py`

**Test Cases:**
1. **Test: Detect discharge terminal**
   - Input: Voyage with 3 terminal stops
   - Expected: First terminal identified as discharge

2. **Test: Segment times calculation**
   - Input: Voyage with known timestamps
   - Expected: Correct inbound/outbound durations

3. **Test: Draft delta calculation**
   - Input: Segment with inbound=35ft, outbound=40ft
   - Expected: draft_delta=+5ft, cargo_status="Laden Outbound"

4. **Test: No terminal case**
   - Input: Voyage with only anchorages
   - Expected: has_discharge_terminal=False, inbound=full voyage

5. **Test: Incomplete voyage**
   - Input: Voyage with Cross In but no Cross Out
   - Expected: Outbound metrics = None, is_complete=False

6. **Test: Efficiency metrics**
   - Input: VoyageSegment with valid times
   - Expected: All efficiency metrics calculated

7. **Test: Cargo estimation with TPC**
   - Input: Segment with draft_delta and TPC
   - Expected: Estimated cargo in tonnes

8. **Test: Aggregate statistics**
   - Input: 10 segments for same vessel
   - Expected: Correct averages in efficiency_metrics

### Integration Tests

- Run on 2026 data subset (fast)
- Verify both CSV outputs generated
- Check column counts and data types
- Validate segment durations sum correctly

### End-to-End Test

- Run on full dataset (296K events)
- Compare Phase 1 vs Phase 2 voyage counts (should match)
- Verify no data loss
- Check performance impact

---

## Quality Assurance

### Data Validation

1. **Segment times must sum correctly:**
   - `total_port_time ≈ inbound_duration + port_duration + outbound_duration`

2. **Draft values must be realistic:**
   - 0 < draft < 100 ft (sanity check)

3. **Efficiency metrics must be positive:**
   - All efficiency values ≥ 0

4. **Completeness tracking:**
   - is_complete flag must match data availability

### Error Handling

- Missing draft data → Set draft metrics to None, continue processing
- No terminal stops → Mark has_discharge_terminal=False, use full voyage as inbound
- Missing Cross Out → Mark incomplete, set outbound=None
- Invalid timestamps → Add quality note, mark incomplete

---

## Performance Considerations

### Expected Impact

- Phase 2 adds ~10-15% processing time (segmentation + efficiency calc)
- Memory impact minimal (segment objects smaller than voyage objects)
- I/O impact: 2 additional CSV writes (~30 seconds total)

### Optimization Opportunities

- Segment calculation can be parallelized (future)
- Draft extraction happens once during segmentation
- Efficiency metrics calculated in batch

---

## Backward Compatibility

### Preserved Behavior

- Phase 1 outputs unchanged when `--phase 1` (default)
- All existing models, files, dictionaries untouched
- Existing tests continue to pass
- Documentation remains valid for Phase 1

### Migration Path

- Users can run Phase 2 without code changes
- Simply add `--phase 2` flag
- Phase 1 outputs still generated (backward compatible)

---

## Success Criteria

✅ All 10 tasks completed
✅ All tests passing (unit, integration, end-to-end)
✅ Documentation complete
✅ Performance acceptable (<3 min total)
✅ No Phase 1 regressions
✅ voyage_segments.csv has expected columns
✅ efficiency_metrics.csv has aggregate stats
✅ Draft analysis working correctly
✅ Efficiency metrics calculated
✅ Real data validation successful

---

## Future Enhancements (Post-Phase 2)

### Potential Phase 3 Features

1. **Multi-terminal voyages:**
   - Track all terminal stops, not just first
   - Segment between each terminal pair

2. **Manual discharge terminal specification:**
   - Allow user to override auto-detection
   - Useful for complex voyages

3. **Seasonal trend analysis:**
   - Compare Q1 vs Q2 vs Q3 vs Q4
   - Identify congestion patterns

4. **Agent classification integration:**
   - Apply agent roll-ups (from agent_dictionary.csv)
   - Agent efficiency comparisons

5. **Advanced cargo estimation:**
   - Use TPC for all vessels with register data
   - Validate against actual cargo manifests

6. **Web dashboard:**
   - Visualize inbound/outbound trends
   - Interactive segment explorer

---

**Design Status:** ✅ COMPLETE - Ready for Implementation
**Next Step:** Begin Task #2 - Implement VoyageSegment Model
