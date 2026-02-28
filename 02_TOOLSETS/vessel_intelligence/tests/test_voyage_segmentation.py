#!/usr/bin/env python3
"""
Test suite for Phase 2 voyage segmentation functionality.

Tests:
1. Discharge terminal detection
2. Inbound/outbound segment splitting
3. Draft calculation and cargo status
4. Efficiency metrics calculation
5. Edge cases (no terminal, incomplete voyages)
"""

import sys
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.insert(0, '.')

from src.models.event import Event
from src.models.voyage import Voyage
from src.models.voyage_segment import VoyageSegment
from src.processing.voyage_segmenter import VoyageSegmenter
from src.processing.efficiency_calculator import EfficiencyCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_event(
    imo: str,
    vessel_name: str,
    action: str,
    timestamp: datetime,
    zone: str,
    zone_type: str,
    draft: float = None
) -> Event:
    """Create a test event."""
    return Event(
        imo=imo,
        vessel_name=vessel_name,
        action=action,
        timestamp=timestamp,
        zone=zone,
        zone_type=zone_type,
        agent="Test Agent",
        vessel_type="Bulk Carrier",
        draft=draft,
        mile="0",
        raw_time=timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        source_file="test.csv",
        facility=f"Test {zone}",
        vessel_types="Bulk - Only",
        activity="Load or Discharge",
        cargoes="Dry Bulk"
    )


def create_complete_voyage_with_terminal() -> Voyage:
    """
    Create a complete voyage with terminal stop for testing.

    Timeline:
    - Cross In (draft 35 ft)
    - Arrive Anchor
    - Depart Anchor
    - Arrive Terminal (draft 36 ft) <- Discharge terminal
    - Depart Terminal (draft 40 ft) <- Loaded cargo
    - Cross Out (draft 40 ft)
    """
    base_time = datetime(2026, 1, 1, 10, 0, 0)

    events = [
        create_test_event("1234567", "Test Vessel", "Enter", base_time, "Southwest Pass", "CROSS_IN", draft=35.0),
        create_test_event("1234567", "Test Vessel", "Arrive", base_time + timedelta(hours=2), "12 Mile Anch", "ANCHORAGE"),
        create_test_event("1234567", "Test Vessel", "Depart", base_time + timedelta(hours=6), "12 Mile Anch", "ANCHORAGE"),
        create_test_event("1234567", "Test Vessel", "Arrive", base_time + timedelta(hours=8), "Test Terminal", "TERMINAL", draft=36.0),
        create_test_event("1234567", "Test Vessel", "Depart", base_time + timedelta(hours=20), "Test Terminal", "TERMINAL", draft=40.0),
        create_test_event("1234567", "Test Vessel", "Exit", base_time + timedelta(hours=24), "Southwest Pass", "CROSS_OUT", draft=40.0),
    ]

    voyage = Voyage(
        voyage_id="1234567_20260101_100000",
        imo="1234567",
        vessel_name="Test Vessel",
        cross_in_event=events[0],
        cross_out_event=events[5],
        events=events,
        is_complete=True
    )

    voyage.total_port_time_hours = 24.0

    return voyage


def create_voyage_no_terminal() -> Voyage:
    """Create a voyage with no terminal stops (anchor only)."""
    base_time = datetime(2026, 1, 1, 10, 0, 0)

    events = [
        create_test_event("1234567", "Test Vessel", "Enter", base_time, "Southwest Pass", "CROSS_IN", draft=35.0),
        create_test_event("1234567", "Test Vessel", "Arrive", base_time + timedelta(hours=2), "12 Mile Anch", "ANCHORAGE"),
        create_test_event("1234567", "Test Vessel", "Depart", base_time + timedelta(hours=10), "12 Mile Anch", "ANCHORAGE"),
        create_test_event("1234567", "Test Vessel", "Exit", base_time + timedelta(hours=12), "Southwest Pass", "CROSS_OUT", draft=35.5),
    ]

    voyage = Voyage(
        voyage_id="1234567_20260101_100000",
        imo="1234567",
        vessel_name="Test Vessel",
        cross_in_event=events[0],
        cross_out_event=events[3],
        events=events,
        is_complete=True
    )

    voyage.total_port_time_hours = 12.0

    return voyage


def create_incomplete_voyage() -> Voyage:
    """Create an incomplete voyage (no Cross Out)."""
    base_time = datetime(2026, 1, 1, 10, 0, 0)

    events = [
        create_test_event("1234567", "Test Vessel", "Enter", base_time, "Southwest Pass", "CROSS_IN", draft=35.0),
        create_test_event("1234567", "Test Vessel", "Arrive", base_time + timedelta(hours=8), "Test Terminal", "TERMINAL", draft=36.0),
        create_test_event("1234567", "Test Vessel", "Depart", base_time + timedelta(hours=20), "Test Terminal", "TERMINAL", draft=40.0),
    ]

    voyage = Voyage(
        voyage_id="1234567_20260101_100000",
        imo="1234567",
        vessel_name="Test Vessel",
        cross_in_event=events[0],
        cross_out_event=None,
        events=events,
        is_complete=False
    )

    return voyage


def test_discharge_terminal_detection():
    """Test that first terminal is correctly identified as discharge terminal."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Discharge Terminal Detection")
    logger.info("="*70)

    voyage = create_complete_voyage_with_terminal()
    segmenter = VoyageSegmenter()

    segment = segmenter._segment_voyage(voyage)

    logger.info(f"✓ Voyage created with {len(voyage.events)} events")
    logger.info(f"  Terminal events: {sum(1 for e in voyage.events if e.is_terminal_arrive())}")

    assert segment.has_discharge_terminal, "Segment should have discharge terminal"
    assert segment.discharge_terminal_zone == "Test Terminal", "Wrong discharge terminal detected"
    assert segment.discharge_terminal_facility == "Test Test Terminal", "Wrong facility name"

    logger.info(f"✓ Discharge terminal detected: {segment.discharge_terminal_zone}")
    logger.info(f"  Facility: {segment.discharge_terminal_facility}")

    logger.info("\n✅ TEST 1 PASSED: Discharge terminal detection working correctly\n")
    return True


def test_segment_time_calculation():
    """Test inbound and outbound time calculations."""
    logger.info("="*70)
    logger.info("TEST 2: Segment Time Calculations")
    logger.info("="*70)

    voyage = create_complete_voyage_with_terminal()
    segmenter = VoyageSegmenter()

    segment = segmenter._segment_voyage(voyage)

    logger.info("✓ Segment created")
    logger.info(f"  Inbound duration: {segment.inbound_duration_hours:.2f} hours")
    logger.info(f"  Port duration: {segment.port_duration_hours:.2f} hours")
    logger.info(f"  Outbound duration: {segment.outbound_duration_hours:.2f} hours")
    logger.info(f"  Total port time: {segment.total_port_time_hours:.2f} hours")

    # Verify times
    assert segment.inbound_duration_hours == 8.0, f"Inbound should be 8 hours, got {segment.inbound_duration_hours}"
    assert segment.port_duration_hours == 12.0, f"Port should be 12 hours, got {segment.port_duration_hours}"
    assert segment.outbound_duration_hours == 4.0, f"Outbound should be 4 hours, got {segment.outbound_duration_hours}"

    logger.info("\n✓ All durations calculated correctly")
    logger.info("\n✅ TEST 2 PASSED: Segment time calculations working correctly\n")
    return True


def test_draft_calculation():
    """Test draft delta and cargo status determination."""
    logger.info("="*70)
    logger.info("TEST 3: Draft Calculation and Cargo Status")
    logger.info("="*70)

    voyage = create_complete_voyage_with_terminal()
    segmenter = VoyageSegmenter(draft_threshold=1.5)

    segment = segmenter._segment_voyage(voyage)

    logger.info("✓ Draft analysis performed")
    logger.info(f"  Inbound draft (at terminal): {segment.first_terminal_arrival_draft:.1f} ft")
    logger.info(f"  Outbound draft (at terminal): {segment.first_terminal_departure_draft:.1f} ft")
    logger.info(f"  Draft delta: {segment.draft_delta_ft:+.1f} ft")
    logger.info(f"  Cargo status: {segment.cargo_status}")

    # Verify draft analysis (36 ft inbound, 40 ft outbound = +4 ft delta = Laden Outbound)
    assert segment.draft_delta_ft == 4.0, f"Draft delta should be +4.0, got {segment.draft_delta_ft}"
    assert segment.cargo_status == "Laden Outbound", f"Should be Laden Outbound, got {segment.cargo_status}"

    logger.info("\n✓ Draft analysis correct: +4 ft = Laden Outbound")
    logger.info("\n✅ TEST 3 PASSED: Draft calculation working correctly\n")
    return True


def test_no_terminal_case():
    """Test handling of voyages with no terminal stops."""
    logger.info("="*70)
    logger.info("TEST 4: No Terminal Case (Anchor Only)")
    logger.info("="*70)

    voyage = create_voyage_no_terminal()
    segmenter = VoyageSegmenter()

    segment = segmenter._segment_voyage(voyage)

    logger.info("✓ Voyage with no terminal stops processed")
    logger.info(f"  Has discharge terminal: {segment.has_discharge_terminal}")
    logger.info(f"  Inbound duration: {segment.inbound_duration_hours:.2f} hours")
    logger.info(f"  Port duration: {segment.port_duration_hours}")
    logger.info(f"  Outbound duration: {segment.outbound_duration_hours}")
    logger.info(f"  Quality notes: {segment.quality_notes}")

    assert not segment.has_discharge_terminal, "Should not have discharge terminal"
    assert segment.inbound_duration_hours == 12.0, "Full voyage should be inbound"
    assert segment.port_duration_hours is None, "Port duration should be None"
    assert segment.outbound_duration_hours is None, "Outbound duration should be None"
    assert "No terminal" in segment.quality_notes, "Should have quality note about no terminal"

    logger.info("\n✓ No terminal case handled correctly")
    logger.info("\n✅ TEST 4 PASSED: No terminal case working correctly\n")
    return True


def test_incomplete_voyage():
    """Test handling of incomplete voyages (no Cross Out)."""
    logger.info("="*70)
    logger.info("TEST 5: Incomplete Voyage (No Cross Out)")
    logger.info("="*70)

    voyage = create_incomplete_voyage()
    segmenter = VoyageSegmenter()

    segment = segmenter._segment_voyage(voyage)

    logger.info("✓ Incomplete voyage processed")
    logger.info(f"  Has discharge terminal: {segment.has_discharge_terminal}")
    logger.info(f"  Is complete: {segment.is_complete}")
    logger.info(f"  Inbound duration: {segment.inbound_duration_hours:.2f} hours")
    logger.info(f"  Outbound duration: {segment.outbound_duration_hours}")
    logger.info(f"  Quality notes: {segment.quality_notes}")

    assert segment.has_discharge_terminal, "Should have terminal"
    assert not segment.is_complete, "Segment should be marked incomplete"
    assert segment.cross_out_time is None, "Should not have Cross Out"
    assert segment.outbound_duration_hours is None, "Outbound should be None"
    assert "Cross Out" in segment.quality_notes, "Should note missing Cross Out"

    logger.info("\n✓ Incomplete voyage handled correctly")
    logger.info("\n✅ TEST 5 PASSED: Incomplete voyage handling working correctly\n")
    return True


def test_efficiency_calculation():
    """Test efficiency metrics calculation."""
    logger.info("="*70)
    logger.info("TEST 6: Efficiency Metrics Calculation")
    logger.info("="*70)

    voyage = create_complete_voyage_with_terminal()
    segmenter = VoyageSegmenter()
    segment = segmenter._segment_voyage(voyage)

    # Calculate efficiency
    calculator = EfficiencyCalculator()
    segments = calculator.calculate_efficiency([segment])

    logger.info("✓ Efficiency metrics calculated")
    logger.info(f"  Vessel utilization: {segments[0].vessel_utilization_pct:.1f}%")
    logger.info(f"  Port idle time: {segments[0].port_idle_time_hours:.2f} hours")

    # Port duration = 12 hours, Total = 24 hours -> Utilization = 50%
    assert segments[0].vessel_utilization_pct == 50.0, "Utilization should be 50%"
    assert segments[0].port_idle_time_hours == 12.0, "Port idle should be 12 hours"

    logger.info("\n✓ Efficiency calculations correct")
    logger.info("\n✅ TEST 6 PASSED: Efficiency metrics working correctly\n")
    return True


def test_aggregate_metrics():
    """Test aggregate metrics calculation across multiple voyages."""
    logger.info("="*70)
    logger.info("TEST 7: Aggregate Metrics Calculation")
    logger.info("="*70)

    # Create multiple voyages for same vessel
    voyage1 = create_complete_voyage_with_terminal()
    voyage2 = create_complete_voyage_with_terminal()

    segmenter = VoyageSegmenter()
    segment1 = segmenter._segment_voyage(voyage1)
    segment2 = segmenter._segment_voyage(voyage2)

    calculator = EfficiencyCalculator()
    segments = calculator.calculate_efficiency([segment1, segment2])
    aggregates = calculator.calculate_aggregate_metrics(segments)

    logger.info("✓ Aggregate metrics calculated for 2 voyages")
    logger.info(f"  Vessels analyzed: {len(aggregates)}")
    logger.info(f"  Total voyages (IMO 1234567): {aggregates['1234567']['total_voyages']}")
    logger.info(f"  Avg inbound duration: {aggregates['1234567']['avg_inbound_duration_hours']:.2f} hours")
    logger.info(f"  Avg port duration: {aggregates['1234567']['avg_port_duration_hours']:.2f} hours")
    logger.info(f"  Most frequent terminal: {aggregates['1234567']['most_frequent_discharge_terminal']}")

    assert len(aggregates) == 1, "Should have 1 vessel"
    assert aggregates['1234567']['total_voyages'] == 2, "Should have 2 voyages"
    assert aggregates['1234567']['avg_inbound_duration_hours'] == 8.0, "Avg inbound should be 8"

    logger.info("\n✓ Aggregate metrics correct")
    logger.info("\n✅ TEST 7 PASSED: Aggregate metrics working correctly\n")
    return True


def test_segment_validation():
    """Test segment validation methods."""
    logger.info("="*70)
    logger.info("TEST 8: Segment Validation Methods")
    logger.info("="*70)

    voyage = create_complete_voyage_with_terminal()
    segmenter = VoyageSegmenter()
    segment = segmenter._segment_voyage(voyage)

    # Calculate efficiency to populate utilization_pct
    calculator = EfficiencyCalculator()
    calculator.calculate_efficiency([segment])

    logger.info("✓ Testing segment validation methods")
    logger.info(f"  Is complete: {segment.is_complete}")
    logger.info(f"  Validate times: {segment.validate_segment_times()}")
    logger.info(f"  Cargo status: {segment.get_cargo_status_description()}")
    logger.info(f"  Utilization %: {segment.vessel_utilization_pct}")
    logger.info(f"  Utilization grade: {segment.get_utilization_grade()}")

    assert segment.is_complete, "Segment should be complete"
    assert segment.validate_segment_times(), "Times should validate"
    assert segment.get_utilization_grade() == "C", "50% utilization should be grade C"

    logger.info("\n✓ All validation methods working")
    logger.info("\n✅ TEST 8 PASSED: Segment validation working correctly\n")
    return True


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║                                                                    ║")
    logger.info("║         PHASE 2 VOYAGE SEGMENTATION TEST SUITE                    ║")
    logger.info("║                                                                    ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")

    tests = [
        ("Discharge Terminal Detection", test_discharge_terminal_detection),
        ("Segment Time Calculations", test_segment_time_calculation),
        ("Draft Calculation", test_draft_calculation),
        ("No Terminal Case", test_no_terminal_case),
        ("Incomplete Voyage", test_incomplete_voyage),
        ("Efficiency Metrics", test_efficiency_calculation),
        ("Aggregate Metrics", test_aggregate_metrics),
        ("Segment Validation", test_segment_validation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            logger.error(f"❌ TEST FAILED: {name}")
            logger.error(f"   Error: {e}")
            failed += 1
        except Exception as e:
            logger.error(f"❌ TEST ERROR: {name}")
            logger.exception(e)
            failed += 1

    # Summary
    logger.info("="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    for name, _ in tests:
        logger.info(f"✅ PASS - {name}")
    logger.info("="*70)
    logger.info(f"Results: {passed}/{len(tests)} tests passed")
    logger.info("="*70)

    if failed == 0:
        logger.info("\n🎉 All tests passed! Phase 2 segmentation is working correctly.")
        return 0
    else:
        logger.error(f"\n❌ {failed} test(s) failed.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
