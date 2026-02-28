#!/usr/bin/env python3
"""Test ship register integration with sample data."""

import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.ship_register_lookup import ShipRegisterLookup
from src.data.preprocessor import DataPreprocessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_ship_register_lookup():
    """Test ShipRegisterLookup module."""
    logger.info("=" * 70)
    logger.info("TESTING SHIP REGISTER LOOKUP MODULE")
    logger.info("=" * 70)

    # Initialize lookup
    lookup = ShipRegisterLookup("ships_register_dictionary.csv")

    # Get stats
    stats = lookup.get_lookup_stats()
    logger.info(f"\nRegister Statistics:")
    logger.info(f"  Total Unique IMOs: {stats['total_unique_imos']}")
    logger.info(f"  Total Unique Names: {stats['total_unique_names']}")
    logger.info(f"  Lookup Initialized: {stats['lookup_initialized']}")

    # Test cases
    test_cases = [
        {
            'name': 'Exact IMO Match (SUMURUN)',
            'imo': '1004156',
            'vessel_name': 'SUMURUN'
        },
        {
            'name': 'Padded IMO (LEVERAGE)',
            'imo': '0001007823',
            'vessel_name': 'LEVERAGE'
        },
        {
            'name': 'Name Match Only',
            'imo': '9999999',
            'vessel_name': 'AMADEA'
        },
        {
            'name': 'No Match',
            'imo': '1234567',
            'vessel_name': 'NONEXISTENT SHIP'
        }
    ]

    logger.info(f"\n{'Test Case':<40} | {'Match Method':<12} | {'Ship Type':<15} | {'DWT':<10} | {'Draft':<8}")
    logger.info("-" * 100)

    for test in test_cases:
        characteristics = lookup.get_ship_characteristics(test['imo'], test['vessel_name'])
        match_method = characteristics['match_method'] or 'NONE'
        ship_type = characteristics['ship_type'] or '-'
        dwt = f"{characteristics['dwt']:.0f}" if characteristics['dwt'] else '-'
        draft = f"{characteristics['draft_m']:.2f}" if characteristics['draft_m'] else '-'

        logger.info(
            f"{test['name']:<40} | {match_method:<12} | {ship_type:<15} | {dwt:<10} | {draft:<8}"
        )


def test_preprocessor_integration():
    """Test DataPreprocessor integration with ship register."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING DATAPREPROCESSOR INTEGRATION")
    logger.info("=" * 70)

    # Initialize preprocessor
    preprocessor = DataPreprocessor(
        dict_path="terminal_zone_dictionary.csv",
        ship_register_path="ships_register_dictionary.csv"
    )

    logger.info("\nPreprocessor initialized successfully")
    logger.info("  Zone Classifier: Ready")
    logger.info("  Zone Lookup: Ready")
    logger.info("  Ship Register Lookup: Ready")

    # Get stats
    stats = preprocessor.get_stats()
    logger.info(f"\nPreprocessor Statistics:")
    logger.info(f"  Events Created: {stats['events_created']}")
    logger.info(f"  Parse Errors: {stats['parse_errors']}")
    logger.info(f"  Ship Register:")
    logger.info(f"    Total Unique IMOs: {stats['register_stats']['total_unique_imos']}")
    logger.info(f"    Total Unique Names: {stats['register_stats']['total_unique_names']}")


def test_imo_cleaning():
    """Test IMO cleaning logic."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING IMO CLEANING")
    logger.info("=" * 70)

    lookup = ShipRegisterLookup("ships_register_dictionary.csv")

    test_imos = [
        '1004156',
        '1004156.0',
        '0001004156',
        '4156',
        '  1004156  ',
        None,
        '',
        'invalid'
    ]

    logger.info(f"\n{'Input':<20} | {'Cleaned IMO':<12} | {'Result'}")
    logger.info("-" * 50)

    for imo in test_imos:
        cleaned = lookup._clean_imo_for_lookup(imo)
        result = f"Valid (7-digit)" if cleaned else "Invalid"
        logger.info(f"{str(imo):<20} | {str(cleaned):<12} | {result}")


def test_matching_strategies():
    """Test different matching strategies."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING MATCHING STRATEGIES")
    logger.info("=" * 70)

    lookup = ShipRegisterLookup("ships_register_dictionary.csv")

    scenarios = [
        {
            'name': 'Strategy 1: IMO Primary (Best Case)',
            'imo': '1004156',
            'vessel_name': 'UNKNOWN'
        },
        {
            'name': 'Strategy 2: Name Fallback (IMO Missing)',
            'imo': '9999999',
            'vessel_name': 'AMADEA'
        },
        {
            'name': 'Strategy 3: Both Available (Uses IMO)',
            'imo': '1004156',
            'vessel_name': 'AMADEA'
        },
        {
            'name': 'Strategy 4: Case Insensitive Name',
            'imo': '9999999',
            'vessel_name': 'amadea'
        }
    ]

    for scenario in scenarios:
        logger.info(f"\n{scenario['name']}")
        logger.info(f"  Input IMO: {scenario['imo']}")
        logger.info(f"  Input Name: {scenario['vessel_name']}")

        result = lookup.get_ship_characteristics(scenario['imo'], scenario['vessel_name'])

        logger.info(f"  Match Method: {result['match_method'] or 'NONE'}")
        if result['match_method']:
            logger.info(f"    Matched Name: {result['vessel_name_matched']}")
            logger.info(f"    Ship Type: {result['ship_type'] or 'N/A'}")
            logger.info(f"    DWT: {result['dwt'] or 'N/A'}")
            logger.info(f"    Draft: {result['draft_m'] or 'N/A'} m")
            logger.info(f"    TPC: {result['tpc'] or 'N/A'}")


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 70)
    logger.info("SHIP REGISTER INTEGRATION TEST SUITE")
    logger.info("=" * 70)

    try:
        test_ship_register_lookup()
        test_imo_cleaning()
        test_matching_strategies()
        test_preprocessor_integration()

        logger.info("\n" + "=" * 70)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error(f"\nTEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
