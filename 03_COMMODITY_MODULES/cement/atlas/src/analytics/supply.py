#!/usr/bin/env python3
"""
Supply Analytics Module
========================
Query and analytics functions for cement facilities.

Functions:
    - count_by_state: Count facilities by state
    - count_by_naics: Count facilities by NAICS code
    - count_by_company: Count facilities by resolved company
    - get_facility_details: Get detailed information for specific facilities
    - get_state_summary: Get comprehensive state-level summary
"""

import duckdb
import pandas as pd
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class SupplyAnalytics:
    """Handles analytics and queries for cement facility supply data."""

    def __init__(self, atlas_db_path: str):
        """
        Initialize Supply Analytics.

        Args:
            atlas_db_path: Path to ATLAS DuckDB database
        """
        self.atlas_db_path = atlas_db_path

    def _connect(self) -> duckdb.DuckDBPyConnection:
        """Create database connection."""
        return duckdb.connect(self.atlas_db_path, read_only=True)

    def count_by_state(self, state: Optional[str] = None) -> pd.DataFrame:
        """
        Count facilities by state.

        Args:
            state: Optional state code to filter (e.g., 'CA', 'TX')

        Returns:
            DataFrame with state counts
        """
        con = self._connect()
        try:
            where_clause = f"WHERE state = '{state}'" if state else ""
            query = f"""
            SELECT
                state,
                COUNT(*) as facility_count,
                COUNT(DISTINCT registry_id) as unique_facilities
            FROM frs_facilities
            {where_clause}
            GROUP BY state
            ORDER BY facility_count DESC
            """
            df = con.execute(query).fetchdf()
            logger.info(f"Retrieved facility counts for {len(df)} states")
            return df
        finally:
            con.close()

    def count_by_naics(self, naics_prefix: Optional[str] = None) -> pd.DataFrame:
        """
        Count facilities by NAICS code.

        Args:
            naics_prefix: Optional NAICS prefix to filter (e.g., '3273', '327310')

        Returns:
            DataFrame with NAICS code counts
        """
        con = self._connect()
        try:
            # Parse individual NAICS codes from semicolon-separated field
            query = """
            WITH naics_split AS (
                SELECT
                    registry_id,
                    facility_name,
                    state,
                    TRIM(UNNEST(string_split(naics_codes, ';'))) as naics_code
                FROM frs_facilities
                WHERE naics_codes IS NOT NULL
            )
            """

            if naics_prefix:
                query += f"""
                SELECT
                    naics_code,
                    COUNT(*) as facility_count
                FROM naics_split
                WHERE naics_code LIKE '{naics_prefix}%'
                GROUP BY naics_code
                ORDER BY facility_count DESC
                """
            else:
                query += """
                SELECT
                    naics_code,
                    COUNT(*) as facility_count
                FROM naics_split
                GROUP BY naics_code
                ORDER BY facility_count DESC
                """

            df = con.execute(query).fetchdf()
            logger.info(f"Retrieved facility counts for {len(df)} NAICS codes")
            return df
        finally:
            con.close()

    def count_by_company(self) -> pd.DataFrame:
        """
        Count facilities by resolved company name.

        Returns:
            DataFrame with company counts
        """
        con = self._connect()
        try:
            query = """
            SELECT
                resolved_company,
                COUNT(*) as facility_count,
                COUNT(DISTINCT state) as state_count,
                AVG(match_score) as avg_match_score
            FROM frs_facilities
            WHERE resolved_company IS NOT NULL
            GROUP BY resolved_company
            ORDER BY facility_count DESC
            """
            df = con.execute(query).fetchdf()
            logger.info(f"Retrieved facility counts for {len(df)} companies")
            return df
        except Exception as e:
            # If resolved_company column doesn't exist yet
            logger.warning(f"Could not query by company: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def get_facility_details(
        self,
        registry_id: Optional[str] = None,
        state: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get detailed facility information with optional filters.

        Args:
            registry_id: Optional specific registry ID to query
            state: Optional state code filter
            company: Optional resolved company name filter
            limit: Maximum number of records to return

        Returns:
            DataFrame with facility details
        """
        con = self._connect()
        try:
            where_clauses = []
            if registry_id:
                where_clauses.append(f"registry_id = '{registry_id}'")
            if state:
                where_clauses.append(f"state = '{state}'")
            if company:
                where_clauses.append(f"resolved_company LIKE '%{company}%'")

            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            query = f"""
            SELECT
                registry_id,
                facility_name,
                street_address,
                city,
                state,
                zip,
                county,
                latitude,
                longitude,
                naics_codes,
                resolved_company,
                match_score,
                load_timestamp
            FROM frs_facilities
            {where_clause}
            ORDER BY state, facility_name
            LIMIT {limit}
            """
            df = con.execute(query).fetchdf()
            logger.info(f"Retrieved {len(df)} facility detail records")
            return df
        except Exception as e:
            # Handle case where resolved_company doesn't exist yet
            logger.warning(f"Error in facility details query: {e}")
            query = f"""
            SELECT
                registry_id,
                facility_name,
                street_address,
                city,
                state,
                zip,
                county,
                latitude,
                longitude,
                naics_codes,
                load_timestamp
            FROM frs_facilities
            {where_clause}
            ORDER BY state, facility_name
            LIMIT {limit}
            """
            df = con.execute(query).fetchdf()
            return df
        finally:
            con.close()

    def get_state_summary(self, state: str) -> Dict:
        """
        Get comprehensive summary for a specific state.

        Args:
            state: State code (e.g., 'CA', 'TX')

        Returns:
            Dictionary with state summary statistics
        """
        con = self._connect()
        try:
            # Total facilities
            total_query = f"""
            SELECT COUNT(*) as total
            FROM frs_facilities
            WHERE state = '{state}'
            """
            total = con.execute(total_query).fetchone()[0]

            # Top NAICS codes
            naics_query = f"""
            WITH naics_split AS (
                SELECT
                    TRIM(UNNEST(string_split(naics_codes, ';'))) as naics_code
                FROM frs_facilities
                WHERE state = '{state}' AND naics_codes IS NOT NULL
            )
            SELECT
                naics_code,
                COUNT(*) as count
            FROM naics_split
            GROUP BY naics_code
            ORDER BY count DESC
            LIMIT 10
            """
            top_naics = con.execute(naics_query).fetchdf()

            # Top companies (if available)
            try:
                company_query = f"""
                SELECT
                    resolved_company,
                    COUNT(*) as count
                FROM frs_facilities
                WHERE state = '{state}' AND resolved_company IS NOT NULL
                GROUP BY resolved_company
                ORDER BY count DESC
                LIMIT 10
                """
                top_companies = con.execute(company_query).fetchdf()
            except:
                top_companies = pd.DataFrame()

            # City distribution
            city_query = f"""
            SELECT
                city,
                COUNT(*) as count
            FROM frs_facilities
            WHERE state = '{state}' AND city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 10
            """
            top_cities = con.execute(city_query).fetchdf()

            summary = {
                'state': state,
                'total_facilities': total,
                'top_naics_codes': top_naics.to_dict('records'),
                'top_companies': top_companies.to_dict('records') if not top_companies.empty else [],
                'top_cities': top_cities.to_dict('records')
            }

            logger.info(f"Generated state summary for {state}: {total} facilities")
            return summary

        finally:
            con.close()

    def get_database_stats(self) -> Dict:
        """
        Get overall database statistics.

        Returns:
            Dictionary with database-level statistics
        """
        con = self._connect()
        try:
            stats = {}

            # Total facilities
            stats['total_facilities'] = con.execute(
                "SELECT COUNT(*) FROM frs_facilities"
            ).fetchone()[0]

            # Total states
            stats['total_states'] = con.execute(
                "SELECT COUNT(DISTINCT state) FROM frs_facilities WHERE state IS NOT NULL"
            ).fetchone()[0]

            # Facilities with coordinates
            stats['facilities_with_coords'] = con.execute(
                "SELECT COUNT(*) FROM frs_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
            ).fetchone()[0]

            # Try to get company resolution stats
            try:
                stats['facilities_with_company'] = con.execute(
                    "SELECT COUNT(*) FROM frs_facilities WHERE resolved_company IS NOT NULL"
                ).fetchone()[0]

                stats['unique_companies'] = con.execute(
                    "SELECT COUNT(DISTINCT resolved_company) FROM frs_facilities WHERE resolved_company IS NOT NULL"
                ).fetchone()[0]
            except:
                stats['facilities_with_company'] = 0
                stats['unique_companies'] = 0

            # Last load timestamp
            try:
                last_load = con.execute(
                    "SELECT MAX(load_timestamp) FROM frs_facilities"
                ).fetchone()[0]
                stats['last_load_timestamp'] = str(last_load) if last_load else None
            except:
                stats['last_load_timestamp'] = None

            logger.info(f"Database stats: {stats['total_facilities']} facilities across {stats['total_states']} states")
            return stats

        finally:
            con.close()


# Convenience functions for direct usage
def query_facilities_by_state(atlas_db_path: str, state: Optional[str] = None) -> pd.DataFrame:
    """
    Query facilities by state.

    Args:
        atlas_db_path: Path to ATLAS database
        state: Optional state code filter

    Returns:
        DataFrame with state counts
    """
    analytics = SupplyAnalytics(atlas_db_path)
    return analytics.count_by_state(state)


def query_facilities_by_naics(atlas_db_path: str, naics_prefix: Optional[str] = None) -> pd.DataFrame:
    """
    Query facilities by NAICS code.

    Args:
        atlas_db_path: Path to ATLAS database
        naics_prefix: Optional NAICS prefix filter

    Returns:
        DataFrame with NAICS code counts
    """
    analytics = SupplyAnalytics(atlas_db_path)
    return analytics.count_by_naics(naics_prefix)


def get_facility_info(
    atlas_db_path: str,
    registry_id: Optional[str] = None,
    state: Optional[str] = None,
    company: Optional[str] = None
) -> pd.DataFrame:
    """
    Get detailed facility information.

    Args:
        atlas_db_path: Path to ATLAS database
        registry_id: Optional registry ID filter
        state: Optional state filter
        company: Optional company filter

    Returns:
        DataFrame with facility details
    """
    analytics = SupplyAnalytics(atlas_db_path)
    return analytics.get_facility_details(registry_id, state, company)
