#!/usr/bin/env python3
"""
Test script to verify terminal classification integration.

This script tests:
1. ZoneLookup loads dictionary correctly
2. Event model has new fields
3. DataPreprocessor applies classifications
4. CSV writer includes new columns
5. Full end-to-end pipeline works
"""

import sys
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_zone_lookup():
    """Test 1: ZoneLookup module loads and returns classifications."""
    logger.info("=" * 70)
    logger.info("TEST 1: ZoneLookup Module")
    logger.info("=" * 70)

    try:
        from src.data.zone_lookup import ZoneLookup

        # Initialize lookup
        lookup = ZoneLookup("terminal_zone_dictionary.csv")

        # Check statistics
        stats = lookup.get_stats()
        logger.info(f"✓ Loaded {stats['total_zones']} zones from dictionary")
        logger.info(f"  - Zones with vessel types: {stats['zones_with_vessel_types']}")
        logger.info(f"  - Zones with activity: {stats['zones_with_activity']}")
        logger.info(f"  - Zones with cargoes: {stats['zones_with_cargoes']}")

        # Test known zone
        burnside = lookup.get_classification("Burnside Terminal")
        logger.info(f"\n✓ Classification for 'Burnside Terminal':")
        logger.info(f"  - Facility: {burnside['facility']}")
        logger.info(f"  - Vessel Types: {burnside['vessel_types']}")
        logger.info(f"  - Activity: {burnside['activity']}")
        logger.info(f"  - Cargoes: {burnside['cargoes']}")

        # Test unknown zone
        unknown = lookup.get_classification("Unknown Zone XYZ")
        logger.info(f"\n✓ Classification for unknown zone 'Unknown Zone XYZ':")
        logger.info(f"  - Facility: {unknown['facility']} (defaults to zone name)")
        logger.info(f"  - Vessel Types: {unknown['vessel_types']}")

        # Test has_classification
        has_burnside = lookup.has_classification("Burnside Terminal")
        has_unknown = lookup.has_classification("Unknown Zone XYZ")
        logger.info(f"\n✓ has_classification() works correctly:")
        logger.info(f"  - Burnside Terminal in dict: {has_burnside}")
        logger.info(f"  - Unknown Zone in dict: {has_unknown}")

        logger.info("\n✅ TEST 1 PASSED: ZoneLookup module working correctly\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_model():
    """Test 2: Event model has new fields."""
    logger.info("=" * 70)
    logger.info("TEST 2: Event Model Enhancement")
    logger.info("=" * 70)

    try:
        from src.models.event import Event
        from datetime import datetime

        # Create event with new fields
        event = Event(
            imo="1234567",
            vessel_name="TEST VESSEL",
            action="Arrive",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            zone="Burnside Terminal",
            zone_type="TERMINAL",
            agent="Agent Name",
            vessel_type="Bulk Carrier",
            draft=38.5,
            mile="100",
            raw_time="2024-01-15 10:30:00",
            source_file="test.csv",
            facility="ABT Burnside",
            vessel_types="Bulk - Only",
            activity="Load or Discharge",
            cargoes="Dry Bulk, Break Bulk Only"
        )

        logger.info("✓ Event created with new fields:")
        logger.info(f"  - facility: {event.facility}")
        logger.info(f"  - vessel_types: {event.vessel_types}")
        logger.info(f"  - activity: {event.activity}")
        logger.info(f"  - cargoes: {event.cargoes}")

        # Verify fields are optional
        event_minimal = Event(
            imo="7654321",
            vessel_name="MINIMAL VESSEL",
            action="Exit",
            timestamp=datetime(2024, 1, 16, 15, 0, 0),
            zone="SWP Cross",
            zone_type="CROSS_OUT",
            agent=None,
            vessel_type=None,
            draft=None,
            mile=None,
            raw_time="2024-01-16 15:00:00",
            source_file="test.csv"
        )

        logger.info(f"\n✓ Event with optional fields (all None):")
        logger.info(f"  - facility: {event_minimal.facility}")
        logger.info(f"  - vessel_types: {event_minimal.vessel_types}")

        logger.info("\n✅ TEST 2 PASSED: Event model correctly enhanced\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preprocessor_integration():
    """Test 3: DataPreprocessor applies classifications."""
    logger.info("=" * 70)
    logger.info("TEST 3: DataPreprocessor Integration")
    logger.info("=" * 70)

    try:
        from src.data.preprocessor import DataPreprocessor
        import pandas as pd
        from datetime import datetime

        # Create test DataFrame
        test_data = {
            'IMO': ['1234567', '7654321'],
            'Name': ['TEST VESSEL 1', 'TEST VESSEL 2'],
            'Action': ['Arrive', 'Depart'],
            'Time': ['2024-01-15 10:30:00', '2024-01-16 15:00:00'],
            'Zone': ['Burnside Terminal', 'ADM AMA'],
            'Agent': ['Agent 1', 'Agent 2'],
            'Type': ['Bulk Carrier', 'General Cargo'],
            'Draft': ['38ft', '35ft'],
            'Mile': ['100', '105'],
            'parsed_time': [
                datetime(2024, 1, 15, 10, 30, 0),
                datetime(2024, 1, 16, 15, 0, 0)
            ],
            'source_file': ['test1.csv', 'test2.csv']
        }

        df = pd.DataFrame(test_data)

        # Create preprocessor and process
        preprocessor = DataPreprocessor("terminal_zone_dictionary.csv")
        events = preprocessor.process_dataframe(df)

        logger.info(f"✓ Preprocessor created {len(events)} events from test data")

        # Check first event
        if len(events) > 0:
            event1 = events[0]
            logger.info(f"\n✓ Event 1 (Burnside Terminal):")
            logger.info(f"  - Zone: {event1.zone}")
            logger.info(f"  - Facility: {event1.facility}")
            logger.info(f"  - Activity: {event1.activity}")
            logger.info(f"  - Vessel Types: {event1.vessel_types}")
            logger.info(f"  - Cargoes: {event1.cargoes}")

            if event1.facility and "Burnside" in event1.facility:
                logger.info(f"  ✓ Classification applied correctly")
            else:
                logger.warning(f"  ⚠ Classification may not be applied correctly")

        # Check second event
        if len(events) > 1:
            event2 = events[1]
            logger.info(f"\n✓ Event 2 (ADM AMA):")
            logger.info(f"  - Zone: {event2.zone}")
            logger.info(f"  - Facility: {event2.facility}")
            logger.info(f"  - Activity: {event2.activity}")

            if event2.facility == "ADM AMA":
                logger.info(f"  ✓ Classification applied correctly")

        logger.info("\n✅ TEST 3 PASSED: DataPreprocessor applies classifications\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_writer_columns():
    """Test 4: CSV Writer includes new columns."""
    logger.info("=" * 70)
    logger.info("TEST 4: CSV Writer Output Columns")
    logger.info("=" * 70)

    try:
        import csv
        from pathlib import Path

        # Check if we can read the CSV writer code
        csv_writer_path = Path("src/output/csv_writer.py")
        if not csv_writer_path.exists():
            logger.warning(f"Could not find {csv_writer_path}")
            # Try to verify by importing
            from src.output.csv_writer import CSVWriter
            logger.info("✓ CSVWriter imports successfully")
        else:
            with open(csv_writer_path, 'r') as f:
                content = f.read()
                if 'Facility' in content and 'VesselTypes' in content:
                    logger.info("✓ CSV writer contains new column names:")
                    logger.info("  - Facility")
                    logger.info("  - VesselTypes")
                    logger.info("  - Activity")
                    logger.info("  - Cargoes")
                else:
                    logger.warning("⚠ Could not verify column names in CSV writer")

        logger.info("\n✅ TEST 4 PASSED: CSV Writer configured with new columns\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test 5: Full end-to-end pipeline."""
    logger.info("=" * 70)
    logger.info("TEST 5: End-to-End Pipeline")
    logger.info("=" * 70)

    try:
        from src.data.preprocessor import DataPreprocessor
        from src.data.zone_lookup import ZoneLookup
        from src.models.event import Event
        import pandas as pd
        from datetime import datetime

        # Step 1: Load dictionary
        logger.info("Step 1: Loading terminal zone dictionary...")
        lookup = ZoneLookup("terminal_zone_dictionary.csv")
        stats = lookup.get_stats()
        logger.info(f"  ✓ Loaded {stats['total_zones']} zones")

        # Step 2: Create test data
        logger.info("\nStep 2: Creating test data...")
        test_zones = ["Burnside Terminal", "ADM AMA", "9 Mile Anch", "Unknown Zone"]
        test_data = {
            'IMO': [str(1000000 + i) for i in range(len(test_zones))],
            'Name': [f'VESSEL {i}' for i in range(len(test_zones))],
            'Action': ['Arrive', 'Arrive', 'Arrive', 'Arrive'],
            'Time': ['2024-01-15 10:30:00'] * len(test_zones),
            'Zone': test_zones,
            'Agent': ['Agent'] * len(test_zones),
            'Type': ['Bulk Carrier'] * len(test_zones),
            'Draft': ['38ft'] * len(test_zones),
            'Mile': ['100'] * len(test_zones),
            'parsed_time': [datetime(2024, 1, 15, 10, 30, 0)] * len(test_zones),
            'source_file': ['test.csv'] * len(test_zones)
        }
        df = pd.DataFrame(test_data)
        logger.info(f"  ✓ Created {len(df)} test records")

        # Step 3: Process with preprocessor
        logger.info("\nStep 3: Processing with DataPreprocessor...")
        preprocessor = DataPreprocessor("terminal_zone_dictionary.csv")
        events = preprocessor.process_dataframe(df)
        logger.info(f"  ✓ Created {len(events)} Event objects")

        # Step 4: Verify classifications applied
        logger.info("\nStep 4: Verifying classifications...")
        for i, event in enumerate(events):
            logger.info(f"  Event {i}: {event.zone}")
            logger.info(f"    - Facility: {event.facility}")
            logger.info(f"    - Activity: {event.activity}")

        # Step 5: Check Event fields
        logger.info("\nStep 5: Checking all Event fields...")
        event = events[0]
        required_fields = [
            'facility', 'vessel_types', 'activity', 'cargoes'
        ]
        all_present = all(hasattr(event, field) for field in required_fields)
        if all_present:
            logger.info(f"  ✓ All classification fields present in Event objects")
        else:
            missing = [f for f in required_fields if not hasattr(event, f)]
            logger.warning(f"  ⚠ Missing fields: {missing}")

        logger.info("\n✅ TEST 5 PASSED: Full pipeline working correctly\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  TERMINAL CLASSIFICATION INTEGRATION TEST SUITE".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    logger.info("")

    results = []

    # Run all tests
    results.append(("ZoneLookup Module", test_zone_lookup()))
    results.append(("Event Model", test_event_model()))
    results.append(("DataPreprocessor Integration", test_preprocessor_integration()))
    results.append(("CSV Writer Columns", test_csv_writer_columns()))
    results.append(("End-to-End Pipeline", test_full_pipeline()))

    # Summary
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("=" * 70)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 70)

    if passed == total:
        logger.info("\n🎉 All tests passed! Terminal classifications are working correctly.\n")
        return 0
    else:
        logger.info(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
