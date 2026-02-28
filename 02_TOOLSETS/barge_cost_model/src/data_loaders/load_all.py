"""
Master data loader - runs all data loaders in the correct sequence.
This ensures dependencies are handled properly (e.g., tonnages depends on waterways).
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.database import verify_db_connection, verify_postgis, get_table_counts
from src.data_loaders.load_waterways import load_waterway_networks
from src.data_loaders.load_locks import load_locks
from src.data_loaders.load_docks import load_docks
from src.data_loaders.load_tonnages import load_tonnages
from src.data_loaders.load_vessels import load_vessels


def load_all_data():
    """
    Load all datasets in the correct order.

    Order is important:
    1. waterways - no dependencies
    2. locks - no dependencies
    3. docks - no dependencies
    4. tonnages - depends on waterways (LINKNUM foreign key)
    5. vessels - no dependencies
    """

    print("\n" + "=" * 80)
    print("MASTER DATA LOADER - Loading All Datasets")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Pre-flight checks
    print("\n[PRE-FLIGHT CHECKS]")
    print("-" * 80)

    if not verify_db_connection():
        print("✗ Database connection failed!")
        print("  Please ensure PostgreSQL is running and DATABASE_URL is correct in .env")
        return False
    print("✓ Database connection verified")

    if not verify_postgis():
        print("⚠ PostGIS extension not found (running without spatial features)")
        print("  All data will load correctly, but spatial queries will be disabled")
    else:
        print("✓ PostGIS extension verified")

    print("-" * 80)

    # Track progress
    start_time = datetime.now()
    loaders = [
        ("Waterway Networks", load_waterway_networks, 6860),
        ("Locks", load_locks, 80),
        ("Docks", load_docks, 29645),
        ("Link Tonnages", load_tonnages, 6860),
        ("Vessels", load_vessels, 52035),
    ]

    results = []

    # Run each loader
    for i, (name, loader_func, expected_count) in enumerate(loaders, 1):
        print(f"\n[{i}/{len(loaders)}] Loading {name}...")
        print("-" * 80)

        try:
            loader_start = datetime.now()
            loader_func()
            loader_end = datetime.now()
            duration = (loader_end - loader_start).total_seconds()

            results.append({
                'name': name,
                'status': 'SUCCESS',
                'duration': duration,
                'expected': expected_count
            })

            print(f"✓ {name} loaded successfully in {duration:.1f}s")

        except Exception as e:
            print(f"✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                'name': name,
                'status': 'FAILED',
                'duration': 0,
                'error': str(e),
                'expected': expected_count
            })

            # Continue with remaining loaders
            print(f"\n⚠ Continuing with remaining loaders...")

    # Final verification
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)

    try:
        counts = get_table_counts()

        print("\nTable row counts:")
        for table, count in counts.items():
            print(f"  {table:20s}: {count:>10,}")

        # Verify expected counts
        print("\nExpected vs Actual:")
        verification = {
            'waterway_links': 6860,
            'locks': 80,
            'docks': 29645,
            'link_tonnages': 6860,
            'vessels': 52035,
        }

        all_match = True
        for table, expected in verification.items():
            actual = counts.get(table, 0)
            match = "✓" if actual == expected else "✗"
            print(f"  {match} {table:20s}: {actual:>10,} / {expected:>10,}")
            if actual != expected:
                all_match = False

        total_expected = sum(verification.values())
        total_actual = sum(counts.get(t, 0) for t in verification.keys())

        print(f"\n  Total Records: {total_actual:,} / {total_expected:,}")

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        all_match = False

    # Summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"End Time:     {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:     {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    print(f"Loaders Run:  {len(results)}")

    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed_count = len(results) - success_count

    print(f"Successful:   {success_count}")
    print(f"Failed:       {failed_count}")

    if all_match and failed_count == 0:
        print("\n✓ ALL DATA LOADED SUCCESSFULLY!")
        print("  Phase 1 (Data Loading) is now complete.")
        print("  Next: Implement routing engine (Phase 2)")
    else:
        print("\n✗ Some issues occurred during data loading.")
        print("  Please review the errors above and re-run failed loaders.")

    print("=" * 80)

    return all_match and failed_count == 0


if __name__ == "__main__":
    try:
        success = load_all_data()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nData loading interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
