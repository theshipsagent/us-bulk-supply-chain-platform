#!/usr/bin/env python3
"""
Facility Master Builder — Slag / GGBFS
========================================
Creates a consolidated facility master table from FRS data
with entity resolution results merged in.
"""

import duckdb
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class FacilityMasterBuilder:
    """Builds slag facility master table from FRS + entity resolution."""

    def __init__(self, atlas_db_path: str):
        self.atlas_db_path = atlas_db_path

    def check_source_tables(self) -> Dict[str, bool]:
        """Check which source tables are available."""
        con = duckdb.connect(self.atlas_db_path, read_only=True)
        try:
            tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
            return {
                'frs_facilities': 'frs_facilities' in tables,
                'frs_facilities_resolved': 'frs_facilities_resolved' in tables,
            }
        finally:
            con.close()

    def build_master(self) -> None:
        """Build master facilities table from available source data."""
        con = duckdb.connect(self.atlas_db_path)
        try:
            tables = self.check_source_tables()

            if not tables['frs_facilities']:
                raise ValueError("frs_facilities table not found. Run 'refresh epa' first.")

            source_table = 'frs_facilities_resolved' if tables['frs_facilities_resolved'] else 'frs_facilities'
            logger.info(f"Building master table from {source_table}...")

            con.execute(f"""
            CREATE OR REPLACE TABLE master_facilities AS
            SELECT
                registry_id, facility_name, street_address, city, state, zip,
                county, latitude, longitude, naics_codes, naics_category,
                {'resolved_company,' if tables['frs_facilities_resolved'] else 'NULL as resolved_company,'}
                {'match_score,' if tables['frs_facilities_resolved'] else 'NULL as match_score,'}
                load_timestamp, 'EPA_FRS' as data_source
            FROM {source_table}
            """)

            row_count = con.execute("SELECT COUNT(*) FROM master_facilities").fetchone()[0]
            logger.info(f"Master facilities table built: {row_count:,} records")
        finally:
            con.close()

    def get_master_stats(self) -> Dict:
        """Get summary statistics from master table."""
        con = duckdb.connect(self.atlas_db_path, read_only=True)
        try:
            stats = {}
            stats['total_facilities'] = con.execute("SELECT COUNT(*) FROM master_facilities").fetchone()[0]
            stats['total_states'] = con.execute(
                "SELECT COUNT(DISTINCT state) FROM master_facilities WHERE state IS NOT NULL"
            ).fetchone()[0]
            stats['geocoded'] = con.execute(
                "SELECT COUNT(*) FROM master_facilities WHERE latitude IS NOT NULL"
            ).fetchone()[0]

            try:
                stats['resolved_companies'] = con.execute(
                    "SELECT COUNT(DISTINCT resolved_company) FROM master_facilities WHERE resolved_company IS NOT NULL"
                ).fetchone()[0]
            except Exception:
                stats['resolved_companies'] = 0

            cat_df = con.execute("""
                SELECT naics_category, COUNT(*) as count
                FROM master_facilities GROUP BY naics_category ORDER BY count DESC
            """).fetchdf()
            stats['by_category'] = cat_df.to_dict('records')

            return stats
        except Exception:
            return {}
        finally:
            con.close()


def build_facility_master(atlas_db_path: str) -> None:
    """Convenience function to build master facilities table."""
    builder = FacilityMasterBuilder(atlas_db_path)
    builder.build_master()
