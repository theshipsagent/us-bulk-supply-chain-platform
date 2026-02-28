#!/usr/bin/env python3
"""
Supply Analytics Module — Slag / GGBFS
========================================
Query and analytics for slag facilities (steel mills, slag processors,
cement/concrete end users).

Key feature: distinguishes BF-BOF mills (GGBFS source) from EAF (no GGBFS).
"""

import duckdb
import pandas as pd
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SupplyAnalytics:
    """Handles analytics and queries for slag/GGBFS facility supply data."""

    def __init__(self, atlas_db_path: str):
        self.atlas_db_path = atlas_db_path

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.atlas_db_path, read_only=True)

    def count_by_state(self, state: Optional[str] = None) -> pd.DataFrame:
        """Count facilities by state."""
        con = self._connect()
        try:
            where_clause = f"WHERE state = '{state}'" if state else ""
            query = f"""
            SELECT state, COUNT(*) as facility_count,
                   COUNT(DISTINCT registry_id) as unique_facilities
            FROM frs_facilities {where_clause}
            GROUP BY state ORDER BY facility_count DESC
            """
            return con.execute(query).fetchdf()
        finally:
            con.close()

    def count_by_naics(self, naics_prefix: Optional[str] = None) -> pd.DataFrame:
        """Count facilities by NAICS code."""
        con = self._connect()
        try:
            query = """
            WITH naics_split AS (
                SELECT registry_id, facility_name, state,
                       TRIM(UNNEST(string_split(naics_codes, ';'))) as naics_code
                FROM frs_facilities WHERE naics_codes IS NOT NULL
            )
            """
            if naics_prefix:
                query += f"""
                SELECT naics_code, COUNT(*) as facility_count
                FROM naics_split WHERE naics_code LIKE '{naics_prefix}%'
                GROUP BY naics_code ORDER BY facility_count DESC
                """
            else:
                query += """
                SELECT naics_code, COUNT(*) as facility_count
                FROM naics_split GROUP BY naics_code ORDER BY facility_count DESC
                """
            return con.execute(query).fetchdf()
        finally:
            con.close()

    def count_by_category(self) -> pd.DataFrame:
        """Count facilities by NAICS category (BF-BOF, EAF, etc.)."""
        con = self._connect()
        try:
            return con.execute("""
            SELECT naics_category, COUNT(*) as facility_count,
                   COUNT(DISTINCT state) as state_count
            FROM frs_facilities GROUP BY naics_category ORDER BY facility_count DESC
            """).fetchdf()
        finally:
            con.close()

    def count_by_company(self) -> pd.DataFrame:
        """Count facilities by resolved company name."""
        con = self._connect()
        try:
            query = """
            SELECT resolved_company, COUNT(*) as facility_count,
                   COUNT(DISTINCT state) as state_count,
                   AVG(match_score) as avg_match_score
            FROM frs_facilities WHERE resolved_company IS NOT NULL
            GROUP BY resolved_company ORDER BY facility_count DESC
            """
            return con.execute(query).fetchdf()
        except Exception:
            try:
                return con.execute(query.replace('frs_facilities', 'frs_facilities_resolved')).fetchdf()
            except Exception as e:
                logger.warning(f"Could not query by company: {e}")
                return pd.DataFrame()
        finally:
            con.close()

    def get_steel_mills(self, mill_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get steel mills, optionally filtered by type.

        Args:
            mill_type: 'bf-bof' for integrated mills (GGBFS source),
                      'eaf' for electric arc furnace (no GGBFS),
                      None for all steel mills
        """
        con = self._connect()
        try:
            where = "WHERE naics_category LIKE 'Steel Production%'"
            if mill_type == 'bf-bof':
                where = "WHERE naics_category = 'Steel Production (BF-BOF)'"
            elif mill_type == 'eaf':
                where = "WHERE naics_category = 'Steel Production (EAF)'"

            try:
                query = f"""
                SELECT registry_id, facility_name, city, state, county,
                       latitude, longitude, naics_codes, naics_category,
                       resolved_company, match_score
                FROM frs_facilities {where}
                ORDER BY state, facility_name
                """
                return con.execute(query).fetchdf()
            except Exception:
                query = f"""
                SELECT registry_id, facility_name, city, state, county,
                       latitude, longitude, naics_codes, naics_category
                FROM frs_facilities {where}
                ORDER BY state, facility_name
                """
                return con.execute(query).fetchdf()
        finally:
            con.close()

    def get_facility_details(
        self,
        registry_id: Optional[str] = None,
        state: Optional[str] = None,
        company: Optional[str] = None,
        naics: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get detailed facility information with optional filters."""
        con = self._connect()
        try:
            where_clauses = []
            if registry_id:
                where_clauses.append(f"registry_id = '{registry_id}'")
            if state:
                where_clauses.append(f"state = '{state}'")
            if naics:
                where_clauses.append(f"naics_codes LIKE '%{naics}%'")
            if category:
                where_clauses.append(f"naics_category = '{category}'")

            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            try:
                if company:
                    where_clauses.append(f"resolved_company LIKE '%{company}%'")
                    where_clause = "WHERE " + " AND ".join(where_clauses)

                query = f"""
                SELECT registry_id, facility_name, street_address, city, state, zip,
                       county, latitude, longitude, naics_codes, naics_category,
                       resolved_company, match_score, load_timestamp
                FROM frs_facilities {where_clause}
                ORDER BY state, facility_name LIMIT {limit}
                """
                return con.execute(query).fetchdf()
            except Exception:
                query = f"""
                SELECT registry_id, facility_name, street_address, city, state, zip,
                       county, latitude, longitude, naics_codes, naics_category, load_timestamp
                FROM frs_facilities {where_clause}
                ORDER BY state, facility_name LIMIT {limit}
                """
                return con.execute(query).fetchdf()
        finally:
            con.close()

    def get_state_summary(self, state: str) -> Dict:
        """Get comprehensive summary for a specific state."""
        con = self._connect()
        try:
            total = con.execute(
                f"SELECT COUNT(*) FROM frs_facilities WHERE state = '{state}'"
            ).fetchone()[0]

            top_naics = con.execute(f"""
            WITH naics_split AS (
                SELECT TRIM(UNNEST(string_split(naics_codes, ';'))) as naics_code
                FROM frs_facilities WHERE state = '{state}' AND naics_codes IS NOT NULL
            )
            SELECT naics_code, COUNT(*) as count FROM naics_split
            GROUP BY naics_code ORDER BY count DESC LIMIT 10
            """).fetchdf()

            categories = con.execute(f"""
            SELECT naics_category, COUNT(*) as count FROM frs_facilities
            WHERE state = '{state}' GROUP BY naics_category ORDER BY count DESC
            """).fetchdf()

            try:
                top_companies = con.execute(f"""
                SELECT resolved_company, COUNT(*) as count FROM frs_facilities
                WHERE state = '{state}' AND resolved_company IS NOT NULL
                GROUP BY resolved_company ORDER BY count DESC LIMIT 10
                """).fetchdf()
            except Exception:
                top_companies = pd.DataFrame()

            top_cities = con.execute(f"""
            SELECT city, COUNT(*) as count FROM frs_facilities
            WHERE state = '{state}' AND city IS NOT NULL
            GROUP BY city ORDER BY count DESC LIMIT 10
            """).fetchdf()

            return {
                'state': state,
                'total_facilities': total,
                'top_naics_codes': top_naics.to_dict('records'),
                'categories': categories.to_dict('records'),
                'top_companies': top_companies.to_dict('records') if not top_companies.empty else [],
                'top_cities': top_cities.to_dict('records')
            }
        finally:
            con.close()

    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        con = self._connect()
        try:
            stats = {}
            stats['total_facilities'] = con.execute("SELECT COUNT(*) FROM frs_facilities").fetchone()[0]
            stats['total_states'] = con.execute(
                "SELECT COUNT(DISTINCT state) FROM frs_facilities WHERE state IS NOT NULL"
            ).fetchone()[0]
            stats['facilities_with_coords'] = con.execute(
                "SELECT COUNT(*) FROM frs_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
            ).fetchone()[0]

            try:
                cat_df = con.execute("""
                    SELECT naics_category, COUNT(*) as count
                    FROM frs_facilities GROUP BY naics_category ORDER BY count DESC
                """).fetchdf()
                stats['by_category'] = cat_df.to_dict('records')
            except Exception:
                stats['by_category'] = []

            try:
                stats['facilities_with_company'] = con.execute(
                    "SELECT COUNT(*) FROM frs_facilities WHERE resolved_company IS NOT NULL"
                ).fetchone()[0]
                stats['unique_companies'] = con.execute(
                    "SELECT COUNT(DISTINCT resolved_company) FROM frs_facilities WHERE resolved_company IS NOT NULL"
                ).fetchone()[0]
            except Exception:
                stats['facilities_with_company'] = 0
                stats['unique_companies'] = 0

            try:
                last_load = con.execute("SELECT MAX(load_timestamp) FROM frs_facilities").fetchone()[0]
                stats['last_load_timestamp'] = str(last_load) if last_load else None
            except Exception:
                stats['last_load_timestamp'] = None

            return stats
        finally:
            con.close()

    def production_summary(self) -> Dict:
        """Generate top-line production metrics with dossier reference data."""
        stats = self.get_database_stats()

        stats['reference'] = {
            'total_slag_production_mt': 18_000_000,
            'ggbfs_supply_mt': 4_000_000,
            'ggbfs_imports_mt': 2_000_000,
            'ggbfs_market_value_usd': 600_000_000,
            'sca_shipments_2023_mt': 4_400_000,
            'sca_shipments_2024_mt': 3_700_000,
            'source': 'USGS MCS 2025, SCA, industry estimates',
            'year': 2024,
            'unit': 'metric_tons',
        }

        return stats


# Convenience functions
def query_facilities_by_state(atlas_db_path: str, state: Optional[str] = None) -> pd.DataFrame:
    return SupplyAnalytics(atlas_db_path).count_by_state(state)


def query_facilities_by_naics(atlas_db_path: str, naics_prefix: Optional[str] = None) -> pd.DataFrame:
    return SupplyAnalytics(atlas_db_path).count_by_naics(naics_prefix)


def get_facility_info(atlas_db_path: str, registry_id: Optional[str] = None,
                      state: Optional[str] = None, company: Optional[str] = None) -> pd.DataFrame:
    return SupplyAnalytics(atlas_db_path).get_facility_details(
        registry_id=registry_id, state=state, company=company
    )
