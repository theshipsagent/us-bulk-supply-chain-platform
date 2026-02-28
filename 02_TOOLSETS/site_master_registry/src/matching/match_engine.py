"""Orchestrates matching strategies 1–4 in priority order.

For each commodity seed site, finds the best FRS match:
  1. Manual overrides (highest priority)
  2. Name + State + NAICS
  3. Spatial + Fuzzy name
  4. Parent company bridge (boost only)

Optimized: bulk-preloads FRS data by state before per-site matching.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..connectors.base_connector import SourceRecord
from ..connectors.epa_frs_connector import EpaFrsConnector
from .name_matcher import name_similarity, naics_overlap, parent_company_match
from .spatial_matcher import spatial_distance
from .composite_scorer import MatchScore, compute_score

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Best match for a seed site."""
    seed: SourceRecord
    frs_candidate: Optional[SourceRecord]
    score: Optional[MatchScore]
    is_manual_override: bool = False


class MatchEngine:
    """Runs all matching strategies for a set of seed records against FRS."""

    def __init__(
        self,
        frs_connector: EpaFrsConnector,
        overrides_path: Optional[str] = None,
        weights: Optional[dict] = None,
        parent_boost: float = 0.10,
        search_radius_km: float = 5.0,
    ):
        self.frs = frs_connector
        self.overrides = self._load_overrides(overrides_path)
        self.weights = weights
        self.parent_boost = parent_boost
        self.search_radius_km = search_radius_km

    @staticmethod
    def _load_overrides(path: Optional[str]) -> dict:
        if not path:
            return {}
        p = Path(path)
        if not p.exists():
            return {}
        with open(p) as f:
            data = json.load(f)
        return data.get("overrides", {})

    def match_seed_to_frs(self, seed: SourceRecord) -> MatchResult:
        """Find the best FRS match for a single seed site (cache must be loaded)."""
        # --- Strategy 1: Manual override ---
        override_key = f"{seed.source_system}:{seed.source_record_id}"
        if override_key in self.overrides:
            frs_id = self.overrides[override_key]
            frs_records = self.frs.get_candidates_for_site(seed.state)
            for frs_rec in frs_records:
                if frs_rec.source_record_id == str(frs_id):
                    return MatchResult(
                        seed=seed,
                        frs_candidate=frs_rec,
                        score=MatchScore(
                            confidence=1.0, level="HIGH",
                            name_similarity=1.0, distance_meters=None,
                            naics_overlap=True, parent_match=True,
                            method="manual_override",
                        ),
                        is_manual_override=True,
                    )

        # --- Strategy 2+3: Spatial proximity candidates from cache ---
        frs_candidates = self.frs.get_candidates_for_site(
            state=seed.state,
            lat=seed.latitude,
            lon=seed.longitude,
            radius_km=self.search_radius_km,
        )

        if not frs_candidates:
            # Widen to full state (no spatial filter)
            frs_candidates = self.frs.get_candidates_for_site(state=seed.state)

        if not frs_candidates:
            return MatchResult(seed=seed, frs_candidate=None, score=None)

        # --- Score all candidates ---
        best_match: Optional[SourceRecord] = None
        best_score: Optional[MatchScore] = None

        for frs_rec in frs_candidates:
            nsim = name_similarity(seed.name, frs_rec.name)
            dist_m = spatial_distance(
                seed.latitude, seed.longitude,
                frs_rec.latitude, frs_rec.longitude,
            )
            naics_match = naics_overlap(seed.naics_codes, frs_rec.naics_codes)
            parent_match = parent_company_match(seed.parent_company, frs_rec.name)

            score = compute_score(
                name_sim=nsim,
                distance_m=dist_m,
                naics_match=naics_match,
                parent_match=parent_match,
                weights=self.weights,
                parent_boost=self.parent_boost,
            )

            if best_score is None or score.confidence > best_score.confidence:
                best_score = score
                best_match = frs_rec

        return MatchResult(seed=seed, frs_candidate=best_match, score=best_score)

    def match_all(self, seeds: list[SourceRecord]) -> list[MatchResult]:
        """Match all seed records against FRS.

        Bulk-preloads FRS data for all needed states first, then matches locally.
        """
        # Collect all unique states and NAICS prefixes
        states = {s.state.upper() for s in seeds if s.state}
        naics_prefixes = set()
        for s in seeds:
            for code in s.naics_codes.split(","):
                code = code.strip()[:4]
                if code:
                    naics_prefixes.add(code)

        # Single bulk FRS query
        self.frs.preload_states(states, sorted(naics_prefixes) or None)

        # Match each seed against cached FRS records
        results = []
        for i, seed in enumerate(seeds, 1):
            result = self.match_seed_to_frs(seed)
            if result.score:
                level = result.score.level
                conf = f"({result.score.confidence:.2f})"
            else:
                level = "NO_MATCH"
                conf = ""
            if i % 25 == 0 or i == len(seeds):
                logger.info(f"  Matched {i}/{len(seeds)} sites...")
            results.append(result)

        return results
