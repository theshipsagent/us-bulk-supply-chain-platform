"""Connector for EPA FRS (Facility Registry Service) via DuckDB.

Optimized for Google Drive: loads all needed FRS records in a single
bulk query per state-set, then serves candidates from an in-memory cache.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Optional

import duckdb

from .base_connector import BaseConnector, SourceRecord

logger = logging.getLogger(__name__)


class EpaFrsConnector(BaseConnector):
    """Query EPA FRS DuckDB for facility candidates.

    Call preload_states() once with the set of states you need, then
    use get_candidates_for_site() which reads from in-memory cache.
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        # Cache: state -> list[SourceRecord]
        self._cache: dict[str, list[SourceRecord]] = {}

    def source_system_name(self) -> str:
        return "epa_frs"

    def _get_conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"FRS database not found: {self.db_path}")
            self._conn = duckdb.connect(str(self.db_path), read_only=True)
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
        self._cache.clear()

    def fetch_records(self, **filters) -> list[SourceRecord]:
        """Fetch FRS records. Prefer preload_states() + get_candidates_for_site()."""
        state = filters.get("state")
        if state and state.upper() in self._cache:
            return self._cache[state.upper()]
        return self._query_state(state)

    def preload_states(self, states: set[str], naics_prefixes: list[str] | None = None):
        """Bulk-load all FRS facility records for the given states.

        One big query instead of per-site queries. Stores results
        in memory for fast lookups.
        """
        conn = self._get_conn()

        states_upper = sorted({s.upper() for s in states})
        placeholders = ",".join(["?"] * len(states_upper))

        # Build NAICS filter
        naics_clause = ""
        if naics_prefixes:
            like_parts = " OR ".join(f"n.naics_code LIKE '{p}%'" for p in naics_prefixes)
            naics_clause = f"""
                AND f.registry_id IN (
                    SELECT DISTINCT registry_id FROM naics_codes n
                    WHERE {like_parts}
                )
            """

        query = f"""
            SELECT
                f.registry_id,
                f.fac_name,
                f.fac_city,
                f.fac_state,
                f.fac_county,
                f.latitude,
                f.longitude,
                (
                    SELECT STRING_AGG(DISTINCT n.naics_code, ',')
                    FROM naics_codes n
                    WHERE n.registry_id = f.registry_id
                ) as naics_codes,
                (
                    SELECT STRING_AGG(DISTINCT s.sic_code, ',')
                    FROM sic_codes s
                    WHERE s.registry_id = f.registry_id
                ) as sic_codes
            FROM facilities f
            WHERE f.fac_state IN ({placeholders})
              AND f.latitude IS NOT NULL
              AND f.longitude IS NOT NULL
            {naics_clause}
            ORDER BY f.fac_state, f.fac_name
        """

        logger.info(f"[epa_frs] Bulk loading FRS for {len(states_upper)} states...")
        rows = conn.execute(query, states_upper).fetchall()
        logger.info(f"[epa_frs] Loaded {len(rows)} FRS records")

        # Index by state
        by_state: dict[str, list[SourceRecord]] = defaultdict(list)
        for row in rows:
            rec = SourceRecord(
                source_system="epa_frs",
                source_record_id=str(row[0]),
                name=row[1] or "",
                city=row[2] or "",
                state=row[3] or "",
                county=row[4] or "",
                latitude=row[5],
                longitude=row[6],
                naics_codes=row[7] or "",
                sic_codes=row[8] or "",
            )
            by_state[rec.state].append(rec)

        self._cache.update(by_state)
        for st in states_upper:
            if st not in self._cache:
                self._cache[st] = []
            logger.info(f"  {st}: {len(self._cache[st])} FRS records cached")

    def get_candidates_for_site(
        self,
        state: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: float = 5.0,
    ) -> list[SourceRecord]:
        """Return FRS candidates from cache, optionally filtered by proximity."""
        state_upper = state.upper()
        candidates = self._cache.get(state_upper, [])

        if lat is None or lon is None:
            return candidates

        # Filter by bounding box for efficiency
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
        min_lat, max_lat = lat - lat_delta, lat + lat_delta
        min_lon, max_lon = lon - lon_delta, lon + lon_delta

        return [
            r for r in candidates
            if r.latitude is not None
            and r.longitude is not None
            and min_lat <= r.latitude <= max_lat
            and min_lon <= r.longitude <= max_lon
        ]

    # Legacy interface
    def fetch_candidates_for_site(
        self,
        name: str,
        state: str,
        lat: Optional[float],
        lon: Optional[float],
        naics_prefixes: list[str],
        radius_km: float = 5.0,
    ) -> list[SourceRecord]:
        """Convenience wrapper — uses cache if available, else queries."""
        if state.upper() in self._cache:
            return self.get_candidates_for_site(state, lat, lon, radius_km)
        # Fallback: load this state on demand
        self.preload_states({state}, naics_prefixes or None)
        return self.get_candidates_for_site(state, lat, lon, radius_km)

    def _query_state(self, state: Optional[str]) -> list[SourceRecord]:
        """Direct query for a single state (no cache)."""
        if state:
            self.preload_states({state})
            return self._cache.get(state.upper(), [])
        return []
