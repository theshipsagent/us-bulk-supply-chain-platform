"""
Data validation utilities for the Interactive Barge Dashboard.

Provides data quality checks, constraint validation, and integrity verification.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, List, Dict
from sqlalchemy import text
import logging

from src.config.database import get_db_session
from src.config.settings import ROUTING_CONSTRAINTS

logger = logging.getLogger(__name__)


class DatabaseValidator:
    """Validates database data quality and integrity."""

    def __init__(self):
        """Initialize database validator."""
        self.validation_results = []

    def check_table_counts(self) -> Dict[str, int]:
        """
        Verify all tables have expected row counts.

        Returns:
            Dictionary of table names to row counts
        """
        expected_counts = {
            'waterway_links': 6860,
            'locks': 80,
            'docks': 29645,
            'link_tonnages': 6860,
            'vessels': 52035,
        }

        actual_counts = {}
        with get_db_session() as db:
            for table in expected_counts.keys():
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                actual_counts[table] = count

                expected = expected_counts[table]
                if count == expected:
                    logger.info(f"✓ {table}: {count:,} (matches expected)")
                    self.validation_results.append(('PASS', table, 'row_count', f"{count:,}"))
                else:
                    logger.warning(f"✗ {table}: {count:,} (expected {expected:,})")
                    self.validation_results.append(('FAIL', table, 'row_count', f"{count:,} != {expected:,}"))

        return actual_counts

    def check_null_values(self) -> Dict[str, List[str]]:
        """
        Check for unexpected null values in critical fields.

        Returns:
            Dictionary of tables with null issues
        """
        critical_fields = {
            'waterway_links': ['linknum', 'anode', 'bnode'],
            'locks': ['objectid', 'pmsname'],
            'docks': ['objectid'],
            'link_tonnages': ['linknum'],
            'vessels': ['imo'],
        }

        issues = {}
        with get_db_session() as db:
            for table, fields in critical_fields.items():
                table_issues = []

                for field in fields:
                    result = db.execute(text(
                        f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL"
                    ))
                    null_count = result.fetchone()[0]

                    if null_count > 0:
                        table_issues.append(f"{field}: {null_count} nulls")
                        logger.warning(f"✗ {table}.{field}: {null_count} null values")
                        self.validation_results.append(('FAIL', table, f'{field}_nulls', null_count))
                    else:
                        self.validation_results.append(('PASS', table, f'{field}_nulls', 0))

                if table_issues:
                    issues[table] = table_issues

        return issues

    def check_foreign_key_integrity(self) -> List[str]:
        """
        Verify foreign key relationships.

        Returns:
            List of integrity issues found
        """
        issues = []

        with get_db_session() as db:
            # Check tonnages → waterway_links
            result = db.execute(text("""
                SELECT COUNT(*)
                FROM link_tonnages lt
                LEFT JOIN waterway_links wl ON lt.linknum = wl.linknum
                WHERE wl.linknum IS NULL
            """))
            orphaned_tonnages = result.fetchone()[0]

            if orphaned_tonnages > 0:
                msg = f"Found {orphaned_tonnages} tonnage records with no matching waterway link"
                issues.append(msg)
                logger.error(f"✗ {msg}")
                self.validation_results.append(('FAIL', 'link_tonnages', 'foreign_key', orphaned_tonnages))
            else:
                logger.info("✓ All tonnage records have matching waterway links")
                self.validation_results.append(('PASS', 'link_tonnages', 'foreign_key', 0))

        return issues

    def check_graph_connectivity(self) -> Dict[str, int]:
        """
        Check waterway network graph properties.

        Returns:
            Dictionary with connectivity statistics
        """
        stats = {}

        with get_db_session() as db:
            # Count unique nodes
            result = db.execute(text("""
                SELECT COUNT(DISTINCT anode) FROM waterway_links
            """))
            unique_anodes = result.fetchone()[0]

            result = db.execute(text("""
                SELECT COUNT(DISTINCT bnode) FROM waterway_links
            """))
            unique_bnodes = result.fetchone()[0]

            # Check for isolated nodes (nodes that appear only once)
            result = db.execute(text("""
                WITH all_nodes AS (
                    SELECT anode as node FROM waterway_links
                    UNION ALL
                    SELECT bnode as node FROM waterway_links
                )
                SELECT node, COUNT(*) as occurrences
                FROM all_nodes
                GROUP BY node
                HAVING COUNT(*) = 1
            """))
            isolated_nodes = len(result.fetchall())

            stats = {
                'unique_anodes': unique_anodes,
                'unique_bnodes': unique_bnodes,
                'isolated_nodes': isolated_nodes,
            }

            logger.info(f"Graph stats: {unique_anodes} start nodes, {unique_bnodes} end nodes, {isolated_nodes} isolated")

            if isolated_nodes > 0:
                self.validation_results.append(('WARNING', 'waterway_links', 'isolated_nodes', isolated_nodes))
            else:
                self.validation_results.append(('PASS', 'waterway_links', 'isolated_nodes', 0))

        return stats

    def check_constraint_violations(self) -> List[str]:
        """
        Check for constraint violations (beam, draft, depth).

        Returns:
            List of constraint issues
        """
        issues = []

        with get_db_session() as db:
            # Check vessels with impossible dimensions
            result = db.execute(text("""
                SELECT COUNT(*)
                FROM vessels
                WHERE beam <= 0 OR depth_m <= 0 OR loa <= 0
            """))
            invalid_vessels = result.fetchone()[0]

            if invalid_vessels > 0:
                msg = f"Found {invalid_vessels} vessels with invalid dimensions (<=0)"
                issues.append(msg)
                logger.warning(f"⚠ {msg}")
                self.validation_results.append(('WARNING', 'vessels', 'invalid_dimensions', invalid_vessels))

            # Check locks with missing dimensions
            result = db.execute(text("""
                SELECT COUNT(*)
                FROM locks
                WHERE width IS NULL OR length IS NULL
            """))
            locks_missing_dims = result.fetchone()[0]

            if locks_missing_dims > 0:
                msg = f"Found {locks_missing_dims} locks missing width/length data"
                issues.append(msg)
                logger.warning(f"⚠ {msg}")
                self.validation_results.append(('WARNING', 'locks', 'missing_dimensions', locks_missing_dims))

        return issues

    def check_statistical_outliers(self) -> Dict[str, List]:
        """
        Detect statistical outliers in numeric fields.

        Returns:
            Dictionary of fields with outliers
        """
        outliers = {}

        with get_db_session() as db:
            # Check waterway link lengths
            result = db.execute(text("""
                SELECT AVG(length_miles), STDDEV(length_miles), MAX(length_miles)
                FROM waterway_links
                WHERE length_miles IS NOT NULL
            """))
            avg, stddev, max_length = result.fetchone()

            if max_length and avg and stddev:
                if max_length > (avg + 3 * stddev):
                    outliers['waterway_link_length'] = [
                        f"Max length {max_length:.1f} miles exceeds 3σ (avg={avg:.1f}, σ={stddev:.1f})"
                    ]
                    logger.warning(f"⚠ Outlier detected in waterway lengths: {max_length:.1f} miles")

            # Check vessel dimensions
            result = db.execute(text("""
                SELECT MAX(beam), MAX(loa), MAX(depth_m)
                FROM vessels
                WHERE beam IS NOT NULL AND loa IS NOT NULL
            """))
            max_beam, max_loa, max_draft = result.fetchone()

            vessel_outliers = []
            if max_beam and max_beam > 50:  # Unusually wide (>50m)
                vessel_outliers.append(f"Max beam {max_beam:.1f}m (very wide)")
            if max_loa and max_loa > 400:  # Very long (>400m)
                vessel_outliers.append(f"Max length {max_loa:.1f}m (very long)")
            if max_draft and max_draft > 15:  # Deep draft (>15m)
                vessel_outliers.append(f"Max draft {max_draft:.1f}m (very deep)")

            if vessel_outliers:
                outliers['vessel_dimensions'] = vessel_outliers

        return outliers

    def run_all_checks(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all critical checks pass, False otherwise
        """
        print("=" * 80)
        print("DATABASE VALIDATION")
        print("=" * 80)

        # Clear previous results
        self.validation_results = []

        # Run checks
        print("\n[1/6] Checking table row counts...")
        self.check_table_counts()

        print("\n[2/6] Checking for null values in critical fields...")
        null_issues = self.check_null_values()

        print("\n[3/6] Checking foreign key integrity...")
        fk_issues = self.check_foreign_key_integrity()

        print("\n[4/6] Checking graph connectivity...")
        self.check_graph_connectivity()

        print("\n[5/6] Checking constraint violations...")
        constraint_issues = self.check_constraint_violations()

        print("\n[6/6] Checking for statistical outliers...")
        outliers = self.check_statistical_outliers()

        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.validation_results if r[0] == 'PASS')
        failed = sum(1 for r in self.validation_results if r[0] == 'FAIL')
        warnings = sum(1 for r in self.validation_results if r[0] == 'WARNING')

        print(f"\nTotal Checks: {len(self.validation_results)}")
        print(f"  ✓ Passed:   {passed}")
        print(f"  ✗ Failed:   {failed}")
        print(f"  ⚠ Warnings: {warnings}")

        if failed == 0:
            print("\n✓ All critical validation checks passed!")
            print("=" * 80)
            return True
        else:
            print("\n✗ Some validation checks failed. Review errors above.")
            print("=" * 80)
            return False


# Convenience function
def validate_database() -> bool:
    """
    Quick database validation.

    Returns:
        True if validation passes, False otherwise
    """
    validator = DatabaseValidator()
    return validator.run_all_checks()


if __name__ == "__main__":
    """Test validator."""
    import logging
    logging.basicConfig(level=logging.INFO)

    success = validate_database()
    sys.exit(0 if success else 1)
