"""Query API for the Site Master Registry.

Provides search, filter, and summary functions against site_master.duckdb.
Used by the CLI, report extractor, and map builder.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import duckdb

logger = logging.getLogger(__name__)


class SiteRegistryQuery:
    """Read-only query interface to site_master.duckdb."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def _get_conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Site master DB not found: {self.db_path}")
            self._conn = duckdb.connect(str(self.db_path), read_only=True)
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ----- Search -----

    def search(
        self,
        name: Optional[str] = None,
        state: Optional[str] = None,
        sector: Optional[str] = None,
        rail_served: Optional[bool] = None,
        water_access: Optional[bool] = None,
        min_sources: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search master_sites with flexible filters."""
        conditions = []
        params: list = []

        if name:
            conditions.append("canonical_name ILIKE ?")
            params.append(f"%{name}%")
        if state:
            conditions.append("state = ?")
            params.append(state.upper())
        if sector:
            conditions.append("commodity_sectors ILIKE ?")
            params.append(f"%{sector}%")
        if rail_served is not None:
            conditions.append("rail_served = ?")
            params.append(rail_served)
        if water_access is not None:
            conditions.append("water_access = ?")
            params.append(water_access)
        if min_sources > 0:
            conditions.append("source_count >= ?")
            params.append(min_sources)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT facility_uid, canonical_name, city, state, county,
                   latitude, longitude, parent_company, facility_types,
                   naics_codes, commodity_sectors,
                   rail_served, barge_access, water_access, port_adjacent,
                   capacity_kt_year, source_count, confidence_score
            FROM master_sites
            WHERE {where}
            ORDER BY source_count DESC, canonical_name
            LIMIT ?
        """
        params.append(limit)

        rows = self._get_conn().execute(query, params).fetchall()
        cols = [
            "facility_uid", "canonical_name", "city", "state", "county",
            "latitude", "longitude", "parent_company", "facility_types",
            "naics_codes", "commodity_sectors",
            "rail_served", "barge_access", "water_access", "port_adjacent",
            "capacity_kt_year", "source_count", "confidence_score",
        ]
        return [dict(zip(cols, row)) for row in rows]

    def get_site(self, facility_uid: str) -> Optional[dict[str, Any]]:
        """Get a single site by UID."""
        results = self._get_conn().execute(
            "SELECT * FROM master_sites WHERE facility_uid = ?", [facility_uid]
        ).fetchall()
        if not results:
            return None
        cols = [desc[0] for desc in self._get_conn().description]
        return dict(zip(cols, results[0]))

    def get_source_links(self, facility_uid: str) -> list[dict[str, Any]]:
        """Get all source links for a site."""
        rows = self._get_conn().execute("""
            SELECT source_system, source_record_id, match_method,
                   match_confidence, distance_meters, name_similarity
            FROM source_links
            WHERE facility_uid = ?
            ORDER BY source_system
        """, [facility_uid]).fetchall()
        cols = ["source_system", "source_record_id", "match_method",
                "match_confidence", "distance_meters", "name_similarity"]
        return [dict(zip(cols, row)) for row in rows]

    # ----- Summaries -----

    def summary(self) -> dict[str, Any]:
        """High-level registry summary."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM master_sites").fetchone()[0]
        rail = conn.execute("SELECT COUNT(*) FROM master_sites WHERE rail_served = TRUE").fetchone()[0]
        water = conn.execute("SELECT COUNT(*) FROM master_sites WHERE water_access = TRUE").fetchone()[0]
        multimodal = conn.execute(
            "SELECT COUNT(*) FROM master_sites WHERE rail_served = TRUE AND water_access = TRUE"
        ).fetchone()[0]
        links = conn.execute("SELECT COUNT(*) FROM source_links").fetchone()[0]
        states = conn.execute("SELECT COUNT(DISTINCT state) FROM master_sites").fetchone()[0]

        sectors = {}
        rows = conn.execute("""
            SELECT commodity_sectors, COUNT(*) as cnt
            FROM master_sites
            GROUP BY commodity_sectors
            ORDER BY cnt DESC
        """).fetchall()
        for r in rows:
            sectors[r[0] or "unclassified"] = r[1]

        return {
            "total_sites": total,
            "total_links": links,
            "states": states,
            "rail_served": rail,
            "water_access": water,
            "multimodal": multimodal,
            "sectors": sectors,
        }

    def sector_summary(self, sector: str) -> dict[str, Any]:
        """Summary stats for a specific commodity sector."""
        conn = self._get_conn()
        where = "commodity_sectors ILIKE ?"
        param = f"%{sector}%"

        total = conn.execute(f"SELECT COUNT(*) FROM master_sites WHERE {where}", [param]).fetchone()[0]
        rail = conn.execute(
            f"SELECT COUNT(*) FROM master_sites WHERE {where} AND rail_served = TRUE", [param]
        ).fetchone()[0]
        water = conn.execute(
            f"SELECT COUNT(*) FROM master_sites WHERE {where} AND water_access = TRUE", [param]
        ).fetchone()[0]

        top_states = conn.execute(f"""
            SELECT state, COUNT(*) as cnt FROM master_sites
            WHERE {where}
            GROUP BY state ORDER BY cnt DESC LIMIT 10
        """, [param]).fetchall()

        return {
            "sector": sector,
            "total_sites": total,
            "rail_served": rail,
            "water_access": water,
            "top_states": [{"state": r[0], "count": r[1]} for r in top_states],
        }

    def all_sites_for_map(
        self,
        sectors: Optional[list[str]] = None,
        min_sources: int = 0,
    ) -> list[dict[str, Any]]:
        """Get all sites with coordinates for map rendering."""
        conditions = ["latitude IS NOT NULL", "longitude IS NOT NULL"]
        params: list = []

        if sectors:
            placeholders = ",".join(["?"] * len(sectors))
            conditions.append(f"commodity_sectors IN ({placeholders})")
            params.extend(sectors)
        if min_sources > 0:
            conditions.append("source_count >= ?")
            params.append(min_sources)

        where = " AND ".join(conditions)
        geo_cols = self._geo_columns()
        geo_select = (", " + ", ".join(geo_cols)) if geo_cols else ""
        rows = self._get_conn().execute(f"""
            SELECT facility_uid, canonical_name, city, state,
                   latitude, longitude, commodity_sectors,
                   rail_served, water_access, source_count,
                   parent_company{geo_select}
            FROM master_sites
            WHERE {where}
            ORDER BY commodity_sectors, state, canonical_name
        """, params).fetchall()

        cols = ["facility_uid", "canonical_name", "city", "state",
                "latitude", "longitude", "commodity_sectors",
                "rail_served", "water_access", "source_count",
                "parent_company"] + geo_cols
        return [dict(zip(cols, row)) for row in rows]

    def all_sites_for_dashboard(
        self,
        sectors: Optional[list[str]] = None,
        min_sources: int = 0,
    ) -> list[dict[str, Any]]:
        """Get all sites with extended fields for the interactive dashboard."""
        conditions = ["latitude IS NOT NULL", "longitude IS NOT NULL"]
        params: list = []

        if sectors:
            placeholders = ",".join(["?"] * len(sectors))
            conditions.append(f"commodity_sectors IN ({placeholders})")
            params.extend(sectors)
        if min_sources > 0:
            conditions.append("source_count >= ?")
            params.append(min_sources)

        where = " AND ".join(conditions)
        geo_cols = self._geo_columns()
        geo_select = (", " + ", ".join(geo_cols)) if geo_cols else ""
        rows = self._get_conn().execute(f"""
            SELECT facility_uid, canonical_name, city, state, county,
                   latitude, longitude, parent_company, facility_types,
                   naics_codes, commodity_sectors,
                   rail_served, barge_access, water_access, port_adjacent,
                   capacity_kt_year, source_count, confidence_score{geo_select}
            FROM master_sites
            WHERE {where}
            ORDER BY commodity_sectors, state, canonical_name
        """, params).fetchall()

        cols = [
            "facility_uid", "canonical_name", "city", "state", "county",
            "latitude", "longitude", "parent_company", "facility_types",
            "naics_codes", "commodity_sectors",
            "rail_served", "barge_access", "water_access", "port_adjacent",
            "capacity_kt_year", "source_count", "confidence_score",
        ] + geo_cols
        return [dict(zip(cols, row)) for row in rows]

    def _geo_columns(self) -> list[str]:
        """Return list of geographic identity columns present in the table."""
        all_geo = [
            "latitude_dms", "longitude_dms", "fips_state_code",
            "fips_county_code", "census_region", "census_division",
            "bea_region", "epa_region", "congressional_district",
            "market_region", "nearest_port_code",
            "nearest_port_name", "nearest_port_consolidated",
            "nearest_port_coast", "nearest_port_region",
        ]
        existing = {
            row[0]
            for row in self._get_conn().execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'master_sites'"
            ).fetchall()
        }
        return [c for c in all_geo if c in existing]

    def distinct_values(self, column: str) -> list[str]:
        """Return sorted unique non-null values for a column (for dropdown filters)."""
        safe_cols = {
            "state", "commodity_sectors", "county", "parent_company",
            "facility_types", "naics_codes",
        }
        if column not in safe_cols:
            raise ValueError(f"Column '{column}' not allowed; pick from {safe_cols}")
        rows = self._get_conn().execute(f"""
            SELECT DISTINCT {column}
            FROM master_sites
            WHERE {column} IS NOT NULL AND {column} != ''
            ORDER BY {column}
        """).fetchall()
        return [r[0] for r in rows]
