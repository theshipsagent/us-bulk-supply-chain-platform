"""Registry builder — orchestrates the full build pipeline.

Phase 1: Seed commodity CSVs → master_sites → match to FRS → source_links
Phase 2: FRS Industrial Expansion — add unlinked FRS facilities by NAICS anchor codes
Phase 3: SCRS Rail + BTS Navigation enrichment — rail_served / water_access flags
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import yaml

from ..schema import init_database
from ..connectors.base_connector import SourceRecord
from ..connectors.commodity_csv_connector import CommodityCsvConnector
from ..connectors.epa_frs_connector import EpaFrsConnector
from ..matching.match_engine import MatchEngine, MatchResult
from .uid_generator import generate_facility_uid

logger = logging.getLogger(__name__)


class RegistryBuilder:
    """Builds and populates site_master.duckdb."""

    def __init__(self, project_root: str, frs_db_override: Optional[str] = None):
        self.root = Path(project_root)
        self.config = self._load_config()
        self.db_path = str(self.root / self.config["database"]["path"])
        self.frs_db_override = frs_db_override  # e.g. /tmp/frs_local.duckdb
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def _load_config(self) -> dict:
        config_path = self.root / "02_TOOLSETS" / "site_master_registry" / "config" / "settings.yaml"
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _init_db(self) -> duckdb.DuckDBPyConnection:
        if self.conn is None:
            self.conn = init_database(self.db_path)
        return self.conn

    def _start_run(self, phase: str) -> int:
        conn = self._init_db()
        run_id = conn.execute("SELECT nextval('seq_run_id')").fetchone()[0]
        conn.execute(
            "INSERT INTO build_log (run_id, phase) VALUES (?, ?)",
            [run_id, phase],
        )
        return run_id

    def _finish_run(self, run_id: int, sites_created: int, sites_updated: int,
                    links_created: int, candidates_queued: int, notes: str = ""):
        conn = self._init_db()
        conn.execute(
            """UPDATE build_log
               SET finished_at = CURRENT_TIMESTAMP,
                   sites_created = ?, sites_updated = ?,
                   links_created = ?, candidates_queued = ?,
                   notes = ?
               WHERE run_id = ?""",
            [sites_created, sites_updated, links_created, candidates_queued, notes, run_id],
        )

    # ----- Phase 1: Seed + FRS Match -----

    def build_phase_1(self) -> dict:
        """Seed 179 commodity sites → match to FRS → write to DB.

        Returns summary dict with counts and confidence distribution.
        """
        conn = self._init_db()
        run_id = self._start_run("phase_1_seed_frs")

        # 1. Load all commodity CSV seeds
        seeds = self._load_commodity_seeds()
        logger.info(f"Loaded {len(seeds)} commodity seed records")

        # 2. Init FRS connector (use local copy if provided for perf)
        frs_db = self.frs_db_override or str(self.root / self.config["sources"]["epa_frs"]["db_path"])
        frs_connector = EpaFrsConnector(frs_db)

        # 3. Init match engine
        overrides_path = str(
            self.root / "02_TOOLSETS" / "site_master_registry" / "config" / "manual_overrides.json"
        )
        match_cfg = self.config.get("matching", {})
        weights = {
            "name": match_cfg.get("weight_name", 0.45),
            "spatial": match_cfg.get("weight_spatial", 0.35),
            "naics": match_cfg.get("weight_naics", 0.15),
            "parent": match_cfg.get("weight_parent", 0.05),
        }
        engine = MatchEngine(
            frs_connector=frs_connector,
            overrides_path=overrides_path,
            weights=weights,
            parent_boost=match_cfg.get("parent_company_boost", 0.10),
            search_radius_km=match_cfg.get("spatial_radius_km", 5.0),
        )

        # 4. Match all seeds to FRS
        results = engine.match_all(seeds)
        frs_connector.close()

        # 5. Write to DB
        sites_created = 0
        links_created = 0
        candidates_queued = 0
        confidence_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "NO_MATCH": 0}

        for mr in results:
            uid = generate_facility_uid(mr.seed.name, mr.seed.state, mr.seed.city)

            # Insert master site
            self._upsert_master_site(conn, uid, mr.seed)
            sites_created += 1

            # Insert seed source link
            self._insert_source_link(
                conn, uid, mr.seed, match_method="seed",
                match_confidence=1.0, distance_m=None, name_sim=1.0,
            )
            links_created += 1

            # Insert FRS link if matched
            if mr.frs_candidate and mr.score:
                level = mr.score.level
                confidence_dist[level] += 1

                if level in ("HIGH", "MEDIUM"):
                    self._insert_source_link(
                        conn, uid, mr.frs_candidate,
                        match_method=mr.score.method,
                        match_confidence=mr.score.confidence,
                        distance_m=mr.score.distance_meters,
                        name_sim=mr.score.name_similarity,
                    )
                    links_created += 1
                    self._enrich_from_frs(conn, uid, mr.frs_candidate)
                else:
                    # LOW confidence → queue for review
                    self._insert_candidate(conn, uid, mr.seed, mr.frs_candidate, mr.score)
                    candidates_queued += 1
            else:
                confidence_dist["NO_MATCH"] += 1

        # 6. Update source_count on master_sites
        conn.execute("""
            UPDATE master_sites
            SET source_count = (
                SELECT COUNT(*) FROM source_links sl
                WHERE sl.facility_uid = master_sites.facility_uid
            ),
            updated_at = CURRENT_TIMESTAMP
        """)

        self._finish_run(
            run_id, sites_created, 0, links_created, candidates_queued,
            f"Seeds: {len(seeds)}, FRS matches: {confidence_dist}",
        )

        summary = {
            "phase": "phase_1_seed_frs",
            "run_id": run_id,
            "seeds_loaded": len(seeds),
            "sites_created": sites_created,
            "frs_links_created": links_created - sites_created,  # subtract seed self-links
            "candidates_queued": candidates_queued,
            "confidence_distribution": confidence_dist,
        }

        self._print_phase1_summary(summary)
        return summary

    def _load_commodity_seeds(self) -> list[SourceRecord]:
        """Load all commodity CSV connectors and combine records."""
        all_records: list[SourceRecord] = []
        for source_key in ["steel", "aluminum", "copper"]:
            cfg = self.config["sources"].get(source_key)
            if not cfg:
                continue
            csv_path = str(self.root / cfg["csv_path"])
            connector = CommodityCsvConnector(
                csv_path=csv_path,
                commodity_sector=cfg["commodity_sector"],
                naics_prefixes=cfg.get("naics_prefixes", []),
            )
            records = connector.fetch_records()
            all_records.extend(records)
        return all_records

    def _upsert_master_site(self, conn: duckdb.DuckDBPyConnection,
                            uid: str, seed: SourceRecord):
        """Insert or update a master_site row from a seed record."""
        existing = conn.execute(
            "SELECT facility_uid FROM master_sites WHERE facility_uid = ?", [uid]
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE master_sites SET
                    updated_at = CURRENT_TIMESTAMP
                WHERE facility_uid = ?
            """, [uid])
            return

        conn.execute("""
            INSERT INTO master_sites (
                facility_uid, canonical_name, city, state, latitude, longitude,
                parent_company, facility_types, naics_codes, commodity_sectors,
                rail_served, barge_access, water_access, port_adjacent,
                capacity_kt_year, confidence_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            uid, seed.name, seed.city, seed.state,
            seed.latitude, seed.longitude,
            seed.parent_company, seed.facility_types,
            seed.naics_codes, seed.commodity_sector,
            seed.rail_served, seed.barge_access,
            seed.water_access, seed.port_adjacent,
            seed.capacity_kt_year, 1.0, seed.status,
        ])

    def _insert_source_link(self, conn: duckdb.DuckDBPyConnection,
                            uid: str, record: SourceRecord,
                            match_method: str, match_confidence: float,
                            distance_m: Optional[float], name_sim: float):
        """Insert a source_link row."""
        link_id = conn.execute("SELECT nextval('seq_link_id')").fetchone()[0]
        attrs_json = json.dumps(record.raw_attributes) if record.raw_attributes else "{}"
        conn.execute("""
            INSERT INTO source_links (
                link_id, facility_uid, source_system, source_record_id,
                match_method, match_confidence, distance_meters,
                name_similarity, source_attributes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            link_id, uid, record.source_system, record.source_record_id,
            match_method, match_confidence, distance_m, name_sim, attrs_json,
        ])

    def _insert_candidate(self, conn: duckdb.DuckDBPyConnection,
                          uid: str, seed: SourceRecord,
                          frs: SourceRecord, score):
        """Insert a match_candidate for review."""
        cid = conn.execute("SELECT nextval('seq_candidate_id')").fetchone()[0]
        conn.execute("""
            INSERT INTO match_candidates (
                candidate_id, facility_uid, source_system, source_record_id,
                source_name, source_lat, source_lon,
                candidate_frs_id, candidate_frs_name,
                candidate_lat, candidate_lon,
                distance_meters, name_similarity, confidence_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            cid, uid, seed.source_system, seed.source_record_id,
            seed.name, seed.latitude, seed.longitude,
            frs.source_record_id, frs.name,
            frs.latitude, frs.longitude,
            score.distance_meters, score.name_similarity, score.level,
        ])

    def _enrich_from_frs(self, conn: duckdb.DuckDBPyConnection,
                         uid: str, frs: SourceRecord):
        """Add FRS-sourced data (county, NAICS, SIC) to master site."""
        updates = []
        params = []

        if frs.county:
            updates.append("county = ?")
            params.append(frs.county)

        if frs.naics_codes:
            # Merge NAICS codes
            existing = conn.execute(
                "SELECT naics_codes FROM master_sites WHERE facility_uid = ?", [uid]
            ).fetchone()
            existing_codes = set((existing[0] or "").split(",")) if existing else set()
            new_codes = set(frs.naics_codes.split(","))
            merged = ",".join(sorted(existing_codes | new_codes - {""}))
            if merged:
                updates.append("naics_codes = ?")
                params.append(merged)

        if frs.sic_codes:
            updates.append("sic_codes = ?")
            params.append(frs.sic_codes)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            sql = f"UPDATE master_sites SET {', '.join(updates)} WHERE facility_uid = ?"
            params.append(uid)
            conn.execute(sql, params)

    # ----- Phase 2: FRS Industrial Expansion -----

    def build_phase_2(self, max_tier: int = 1) -> dict:
        """Expand registry with unlinked FRS facilities by NAICS anchor codes.

        Queries FRS nationally for industrial NAICS codes, skips any
        registry_ids already linked in Phase 1, creates new master_sites,
        then deduplicates within 200m + same parent.

        Parameters
        ----------
        max_tier : int
            Include NAICS codes up to this tier (1 = strategic only,
            2 = includes foundries, ready-mix, aggregates).
        """
        from .deduplicator import deduplicate_sites

        conn = self._init_db()
        run_id = self._start_run("phase_2_frs_expansion")

        # 1. Load anchor NAICS codes filtered by tier
        anchor_config = self._load_naics_anchors()
        naics_prefixes = []
        sector_map: dict[str, str] = {}  # naics_prefix -> sector
        for code, info in anchor_config.items():
            if info.get("tier", 1) <= max_tier:
                naics_prefixes.append(code)
                sector_map[code] = info["sector"]

        logger.info(f"Phase 2: Using {len(naics_prefixes)} NAICS anchor codes (tier ≤ {max_tier})")

        # 2. Bulk-load FRS nationally
        frs_db = self.frs_db_override or str(self.root / self.config["sources"]["epa_frs"]["db_path"])
        frs_connector = EpaFrsConnector(frs_db)
        frs_connector.preload_all_by_naics(naics_prefixes)
        all_frs = frs_connector.get_all_cached()
        frs_connector.close()

        logger.info(f"Phase 2: {len(all_frs)} FRS records loaded nationally")

        # 3. Get already-linked FRS registry_ids
        linked_ids = set()
        rows = conn.execute("""
            SELECT source_record_id FROM source_links
            WHERE source_system = 'epa_frs'
        """).fetchall()
        for r in rows:
            linked_ids.add(r[0])
        logger.info(f"Phase 2: {len(linked_ids)} FRS records already linked from Phase 1")

        # 4. Filter to unlinked FRS records
        unlinked = [r for r in all_frs if r.source_record_id not in linked_ids]
        logger.info(f"Phase 2: {len(unlinked)} unlinked FRS records to process")

        # 5. Create master sites from unlinked FRS records
        sites_created = 0
        links_created = 0
        sector_counts: dict[str, int] = {}

        for frs_rec in unlinked:
            # Determine commodity sector from NAICS codes
            sector = self._resolve_sector(frs_rec.naics_codes, sector_map, naics_prefixes)

            uid = generate_facility_uid(frs_rec.name, frs_rec.state, frs_rec.city)

            # Check if UID already exists (possible if name+state+city collide)
            existing = conn.execute(
                "SELECT facility_uid FROM master_sites WHERE facility_uid = ?", [uid]
            ).fetchone()

            if existing:
                # Just add the source link
                self._insert_source_link(
                    conn, uid, frs_rec,
                    match_method="frs_expansion",
                    match_confidence=1.0,
                    distance_m=None,
                    name_sim=1.0,
                )
                links_created += 1
                continue

            # Create new master site from FRS
            frs_rec.commodity_sector = sector
            conn.execute("""
                INSERT INTO master_sites (
                    facility_uid, canonical_name, city, state, county,
                    latitude, longitude,
                    naics_codes, sic_codes, commodity_sectors,
                    confidence_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                uid, frs_rec.name, frs_rec.city, frs_rec.state, frs_rec.county,
                frs_rec.latitude, frs_rec.longitude,
                frs_rec.naics_codes, frs_rec.sic_codes, sector,
                0.8,  # FRS-sourced = 0.8 confidence (not curated like Phase 1)
                "active",
            ])
            sites_created += 1
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

            # Source link
            self._insert_source_link(
                conn, uid, frs_rec,
                match_method="frs_expansion",
                match_confidence=1.0,
                distance_m=None,
                name_sim=1.0,
            )
            links_created += 1

        # 6. Update source_count
        conn.execute("""
            UPDATE master_sites
            SET source_count = (
                SELECT COUNT(*) FROM source_links sl
                WHERE sl.facility_uid = master_sites.facility_uid
            ),
            updated_at = CURRENT_TIMESTAMP
        """)

        # 7. Deduplicate
        logger.info("Phase 2: Running deduplication...")
        dedup_result = deduplicate_sites(conn)

        # 8. Final counts
        total_sites = conn.execute("SELECT COUNT(*) FROM master_sites").fetchone()[0]

        self._finish_run(
            run_id, sites_created, 0, links_created, 0,
            f"FRS expansion: {len(unlinked)} unlinked → {sites_created} new sites, "
            f"{dedup_result['merges']} dedup merges, {total_sites} total",
        )

        summary = {
            "phase": "phase_2_frs_expansion",
            "run_id": run_id,
            "frs_loaded": len(all_frs),
            "already_linked": len(linked_ids),
            "unlinked_processed": len(unlinked),
            "sites_created": sites_created,
            "uid_collisions": len(unlinked) - sites_created - (links_created - sites_created) if links_created > sites_created else 0,
            "links_created": links_created,
            "dedup_merges": dedup_result["merges"],
            "total_sites": total_sites,
            "sector_distribution": sector_counts,
        }

        self._print_phase2_summary(summary)
        return summary

    def _load_naics_anchors(self) -> dict:
        """Load NAICS anchor codes from config."""
        config_path = (
            self.root / "02_TOOLSETS" / "site_master_registry" / "config" / "naics_anchor_codes.yaml"
        )
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return data.get("anchor_codes", {})

    @staticmethod
    def _resolve_sector(
        naics_codes: str,
        sector_map: dict[str, str],
        naics_prefixes: list[str],
    ) -> str:
        """Determine the best commodity sector from a facility's NAICS codes."""
        if not naics_codes:
            return "industrial"

        codes = [c.strip() for c in naics_codes.split(",") if c.strip()]

        # Find the most specific anchor match
        for prefix in sorted(naics_prefixes, key=len, reverse=True):
            for code in codes:
                if code.startswith(prefix):
                    return sector_map.get(prefix, "industrial")

        return "industrial"

    @staticmethod
    def _print_phase2_summary(summary: dict):
        print("\n" + "=" * 70)
        print("  SITE MASTER REGISTRY — Phase 2 Build Summary")
        print("=" * 70)
        print(f"  FRS records loaded:      {summary['frs_loaded']:,}")
        print(f"  Already linked (Ph1):    {summary['already_linked']}")
        print(f"  Unlinked processed:      {summary['unlinked_processed']:,}")
        print(f"  New sites created:       {summary['sites_created']:,}")
        print(f"  Dedup merges:            {summary['dedup_merges']}")
        print(f"  TOTAL master sites:      {summary['total_sites']:,}")
        print("-" * 70)
        print("  Sites by sector:")
        for sector, count in sorted(
            summary["sector_distribution"].items(), key=lambda x: -x[1]
        ):
            print(f"    {sector:25s}: {count:,}")
        print("=" * 70 + "\n")

    # ----- Phase 3: SCRS Rail + BTS Navigation Enrichment -----

    def build_phase_3(self) -> dict:
        """Enrich master sites with rail-served and water-access attributes.

        1. Match SCRS rail records to master sites by name+city+state
        2. Match BTS navigation records to master sites by spatial proximity
        3. Set rail_served / water_access / barge_access flags
        """
        from ..connectors.scrs_connector import ScrsConnector
        from ..connectors.bts_navigation_connector import BtsNavigationConnector
        from ..matching.name_matcher import name_similarity
        from ..matching.spatial_matcher import haversine_meters

        conn = self._init_db()
        run_id = self._start_run("phase_3_rail_navigation")

        # Load all master sites into memory for matching
        site_rows = conn.execute("""
            SELECT facility_uid, canonical_name, city, state,
                   latitude, longitude
            FROM master_sites
        """).fetchall()
        sites = []
        for r in site_rows:
            sites.append({
                "uid": r[0], "name": r[1], "city": r[2] or "",
                "state": r[3], "lat": r[4], "lon": r[5],
            })
        logger.info(f"Phase 3: {len(sites)} master sites loaded for matching")

        # Index sites by state for fast lookup
        sites_by_state: dict[str, list[dict]] = {}
        for s in sites:
            sites_by_state.setdefault(s["state"], []).append(s)

        # ---- SCRS Rail Matching ----
        scrs_path = str(self.root / "01_DATA_SOURCES" / "federal_rail"
                        / "stb_economic_data" / "integrated" / "scrs_integration_ready.csv")
        scrs_conn = ScrsConnector(scrs_path)
        scrs_records = scrs_conn.fetch_records()

        rail_matches = 0
        rail_links = 0
        matched_uids_rail: set[str] = set()

        for scrs_rec in scrs_records:
            state_sites = sites_by_state.get(scrs_rec.state, [])
            if not state_sites:
                continue

            # Find best name match in same state+city first, then state
            best_uid = None
            best_sim = 0.0

            # City-level match first (faster, more precise)
            city_upper = scrs_rec.city.upper()
            for site in state_sites:
                if site["city"].upper() != city_upper:
                    continue
                sim = name_similarity(scrs_rec.name, site["name"])
                if sim > best_sim:
                    best_sim = sim
                    best_uid = site["uid"]

            # If no city match, try state-wide with higher threshold
            if best_sim < 0.70:
                for site in state_sites:
                    sim = name_similarity(scrs_rec.name, site["name"])
                    if sim > best_sim:
                        best_sim = sim
                        best_uid = site["uid"]

            if best_uid and best_sim >= 0.60:
                matched_uids_rail.add(best_uid)

                # Add source link (skip if already linked to same source)
                existing = conn.execute("""
                    SELECT 1 FROM source_links
                    WHERE facility_uid = ? AND source_system = 'scrs_rail'
                      AND source_record_id = ?
                """, [best_uid, scrs_rec.source_record_id]).fetchone()

                if not existing:
                    self._insert_source_link(
                        conn, best_uid, scrs_rec,
                        match_method="name_city_state",
                        match_confidence=best_sim,
                        distance_m=None,
                        name_sim=best_sim,
                    )
                    rail_links += 1
                    rail_matches += 1

        # Set rail_served=True on matched sites
        if matched_uids_rail:
            placeholders = ",".join(["?"] * len(matched_uids_rail))
            conn.execute(f"""
                UPDATE master_sites
                SET rail_served = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE facility_uid IN ({placeholders})
            """, list(matched_uids_rail))

        logger.info(f"Phase 3 SCRS: {rail_matches} rail links created, "
                     f"{len(matched_uids_rail)} sites flagged rail_served")

        # ---- BTS Navigation Matching ----
        bts_path = str(self.root / "01_DATA_SOURCES" / "geospatial"
                       / "base_layers" / "05_bts_navigation_fac"
                       / "Docks_8605051818000540974.csv")
        bts_conn = BtsNavigationConnector(bts_path)
        bts_records = bts_conn.fetch_records()

        nav_matches = 0
        nav_links = 0
        matched_uids_water: set[str] = set()
        match_radius_m = 2500.0  # 2.5 km

        # Only match BTS records to sites that have coordinates
        sites_with_coords = [s for s in sites if s["lat"] is not None and s["lon"] is not None]

        # Index sites with coords by state for efficiency
        coord_sites_by_state: dict[str, list[dict]] = {}
        for s in sites_with_coords:
            coord_sites_by_state.setdefault(s["state"], []).append(s)

        for bts_rec in bts_records:
            if bts_rec.latitude is None or bts_rec.longitude is None:
                continue

            state_sites = coord_sites_by_state.get(bts_rec.state, [])
            if not state_sites:
                continue

            # Find nearest master site within radius
            best_uid = None
            best_dist = match_radius_m + 1

            for site in state_sites:
                # Quick lat check
                if abs(site["lat"] - bts_rec.latitude) > 0.025:  # ~2.8km
                    continue
                if abs(site["lon"] - bts_rec.longitude) > 0.035:
                    continue

                dist = haversine_meters(
                    site["lat"], site["lon"],
                    bts_rec.latitude, bts_rec.longitude,
                )
                if dist < best_dist:
                    best_dist = dist
                    best_uid = site["uid"]

            if best_uid and best_dist <= match_radius_m:
                matched_uids_water.add(best_uid)

                # Add source link (one per BTS record, skip dupes)
                existing = conn.execute("""
                    SELECT 1 FROM source_links
                    WHERE facility_uid = ? AND source_system = 'bts_navigation'
                      AND source_record_id = ?
                """, [best_uid, bts_rec.source_record_id]).fetchone()

                if not existing:
                    self._insert_source_link(
                        conn, best_uid, bts_rec,
                        match_method="spatial_proximity",
                        match_confidence=max(0.5, 1.0 - best_dist / match_radius_m),
                        distance_m=best_dist,
                        name_sim=0.0,
                    )
                    nav_links += 1
                    nav_matches += 1

        # Set water_access=True on matched sites
        if matched_uids_water:
            placeholders = ",".join(["?"] * len(matched_uids_water))
            conn.execute(f"""
                UPDATE master_sites
                SET water_access = TRUE, barge_access = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE facility_uid IN ({placeholders})
            """, list(matched_uids_water))

        logger.info(f"Phase 3 BTS: {nav_matches} nav links created, "
                     f"{len(matched_uids_water)} sites flagged water_access")

        # Update source_count
        conn.execute("""
            UPDATE master_sites
            SET source_count = (
                SELECT COUNT(*) FROM source_links sl
                WHERE sl.facility_uid = master_sites.facility_uid
            ),
            updated_at = CURRENT_TIMESTAMP
        """)

        total_sites = conn.execute("SELECT COUNT(*) FROM master_sites").fetchone()[0]
        total_rail = conn.execute("SELECT COUNT(*) FROM master_sites WHERE rail_served = TRUE").fetchone()[0]
        total_water = conn.execute("SELECT COUNT(*) FROM master_sites WHERE water_access = TRUE").fetchone()[0]

        self._finish_run(
            run_id, 0, len(matched_uids_rail) + len(matched_uids_water),
            rail_links + nav_links, 0,
            f"SCRS: {rail_matches} links → {len(matched_uids_rail)} rail_served. "
            f"BTS: {nav_matches} links → {len(matched_uids_water)} water_access.",
        )

        summary = {
            "phase": "phase_3_rail_navigation",
            "run_id": run_id,
            "scrs_records": len(scrs_records),
            "scrs_matches": rail_matches,
            "sites_rail_served": len(matched_uids_rail),
            "bts_records": len(bts_records),
            "bts_matches": nav_matches,
            "sites_water_access": len(matched_uids_water),
            "total_links_created": rail_links + nav_links,
            "total_sites": total_sites,
            "total_rail_served": total_rail,
            "total_water_access": total_water,
        }

        self._print_phase3_summary(summary)
        return summary

    @staticmethod
    def _print_phase3_summary(summary: dict):
        print("\n" + "=" * 70)
        print("  SITE MASTER REGISTRY — Phase 3 Build Summary")
        print("=" * 70)
        print(f"  SCRS rail records:       {summary['scrs_records']:,}")
        print(f"  SCRS matches:            {summary['scrs_matches']:,}")
        print(f"  Sites → rail_served:     {summary['sites_rail_served']:,}")
        print("-" * 70)
        print(f"  BTS nav records:         {summary['bts_records']:,}")
        print(f"  BTS matches:             {summary['bts_matches']:,}")
        print(f"  Sites → water_access:    {summary['sites_water_access']:,}")
        print("-" * 70)
        print(f"  Total links created:     {summary['total_links_created']:,}")
        print(f"  TOTAL master sites:      {summary['total_sites']:,}")
        print(f"  With rail_served:        {summary['total_rail_served']:,} "
              f"({100*summary['total_rail_served']/summary['total_sites']:.1f}%)")
        print(f"  With water_access:       {summary['total_water_access']:,} "
              f"({100*summary['total_water_access']/summary['total_sites']:.1f}%)")
        print("=" * 70 + "\n")

    @staticmethod
    def _print_phase1_summary(summary: dict):
        dist = summary["confidence_distribution"]
        total = summary["seeds_loaded"]
        high = dist.get("HIGH", 0)
        med = dist.get("MEDIUM", 0)
        low = dist.get("LOW", 0)
        none = dist.get("NO_MATCH", 0)

        print("\n" + "=" * 70)
        print("  SITE MASTER REGISTRY — Phase 1 Build Summary")
        print("=" * 70)
        print(f"  Seeds loaded:        {total}")
        print(f"  Master sites:        {summary['sites_created']}")
        print(f"  FRS links (HIGH):    {high}  ({100*high/total:.0f}%)")
        print(f"  Review queue (MED):  {med}  ({100*med/total:.0f}%)")
        print(f"  Low confidence:      {low}  ({100*low/total:.0f}%)")
        print(f"  No FRS match:        {none}  ({100*none/total:.0f}%)")
        print(f"  Candidates queued:   {summary['candidates_queued']}")
        print("=" * 70)
        print(f"  FRS match rate:      {100*(high+med+low)/total:.1f}%")
        print(f"  HIGH confidence:     {100*high/total:.1f}%")
        print("=" * 70 + "\n")
