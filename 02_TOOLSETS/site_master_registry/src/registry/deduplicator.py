"""Deduplicator — merges master_sites that represent the same physical site.

Two sites are considered duplicates when:
  1. Within 200m of each other, AND
  2. Same parent company (normalized brand match)

The survivor is the site with the most source_links (or the earlier UID
alphabetically as tiebreaker). The loser's source_links are reassigned
to the survivor, and the loser row is deleted.
"""

from __future__ import annotations

import logging
from typing import Optional

import duckdb

from ..matching.name_matcher import extract_core_brand
from ..matching.spatial_matcher import haversine_meters

logger = logging.getLogger(__name__)

# Maximum distance in meters to consider two sites as duplicates
DEDUP_RADIUS_M = 200.0


def deduplicate_sites(
    conn: duckdb.DuckDBPyConnection,
    radius_m: float = DEDUP_RADIUS_M,
) -> dict:
    """Find and merge duplicate master_sites.

    Returns summary dict with merge count and details.
    """
    # Load all sites with coordinates
    rows = conn.execute("""
        SELECT facility_uid, canonical_name, city, state,
               latitude, longitude, parent_company, source_count
        FROM master_sites
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY state, city, canonical_name
    """).fetchall()

    sites = []
    for r in rows:
        sites.append({
            "uid": r[0],
            "name": r[1],
            "city": r[2],
            "state": r[3],
            "lat": r[4],
            "lon": r[5],
            "parent": r[6] or "",
            "source_count": r[7] or 1,
            "brand": extract_core_brand(r[6] or r[1]),
        })

    logger.info(f"Deduplicating {len(sites)} sites (radius={radius_m}m)...")

    # Group by state for efficiency
    by_state: dict[str, list[dict]] = {}
    for s in sites:
        by_state.setdefault(s["state"], []).append(s)

    merges: list[tuple[str, str]] = []  # (survivor_uid, loser_uid)
    merged_uids: set[str] = set()  # track already-merged to avoid chains

    for state, state_sites in sorted(by_state.items()):
        n = len(state_sites)
        for i in range(n):
            if state_sites[i]["uid"] in merged_uids:
                continue
            for j in range(i + 1, n):
                if state_sites[j]["uid"] in merged_uids:
                    continue

                a = state_sites[i]
                b = state_sites[j]

                # Quick lat check before expensive haversine
                if abs(a["lat"] - b["lat"]) > 0.003:  # ~333m
                    continue
                if abs(a["lon"] - b["lon"]) > 0.003:
                    continue

                dist = haversine_meters(a["lat"], a["lon"], b["lat"], b["lon"])
                if dist > radius_m:
                    continue

                # Check parent company brand match
                if not _brands_match(a["brand"], b["brand"]):
                    continue

                # Pick survivor: more source_links wins, then alphabetical UID
                if a["source_count"] >= b["source_count"]:
                    survivor, loser = a, b
                else:
                    survivor, loser = b, a

                merges.append((survivor["uid"], loser["uid"]))
                merged_uids.add(loser["uid"])
                logger.debug(
                    f"  Merge: {loser['name']} → {survivor['name']} "
                    f"({dist:.0f}m, brand={survivor['brand']})"
                )

    # Execute merges
    for survivor_uid, loser_uid in merges:
        _execute_merge(conn, survivor_uid, loser_uid)

    logger.info(f"Deduplicated: {len(merges)} merges applied")

    return {
        "sites_before": len(sites),
        "merges": len(merges),
        "sites_after": len(sites) - len(merges),
    }


def _brands_match(brand_a: str, brand_b: str) -> bool:
    """Check if two brand names match (case-insensitive)."""
    if not brand_a or not brand_b:
        return False
    return brand_a.upper() == brand_b.upper()


def _execute_merge(
    conn: duckdb.DuckDBPyConnection,
    survivor_uid: str,
    loser_uid: str,
):
    """Reassign loser's links to survivor, then delete loser."""
    # Move source_links
    conn.execute("""
        UPDATE source_links
        SET facility_uid = ?
        WHERE facility_uid = ?
    """, [survivor_uid, loser_uid])

    # Move match_candidates
    conn.execute("""
        UPDATE match_candidates
        SET facility_uid = ?
        WHERE facility_uid = ?
    """, [survivor_uid, loser_uid])

    # Update survivor's source_count
    new_count = conn.execute("""
        SELECT COUNT(*) FROM source_links WHERE facility_uid = ?
    """, [survivor_uid]).fetchone()[0]
    conn.execute("""
        UPDATE master_sites
        SET source_count = ?, updated_at = CURRENT_TIMESTAMP
        WHERE facility_uid = ?
    """, [new_count, survivor_uid])

    # Delete loser
    conn.execute("DELETE FROM master_sites WHERE facility_uid = ?", [loser_uid])
