"""Composite confidence scoring for facility matches.

Combines name similarity, spatial proximity, NAICS overlap, and
parent company signals into a single 0.0–1.0 confidence score
with a categorical level (HIGH / MEDIUM / LOW).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchScore:
    """Result of scoring a candidate match."""
    confidence: float           # 0.0 – 1.0
    level: str                  # 'HIGH', 'MEDIUM', 'LOW'
    name_similarity: float      # 0.0 – 1.0
    distance_meters: Optional[float]
    naics_overlap: bool
    parent_match: bool
    method: str                 # how the match was found


# Default thresholds (can be overridden from settings.yaml)
DEFAULT_WEIGHTS = {
    "name": 0.45,
    "spatial": 0.35,
    "naics": 0.15,
    "parent": 0.05,
}

HIGH_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 0.50


def _spatial_score(distance_m: Optional[float], radius_m: float = 25000.0) -> float:
    """Convert distance in meters to a 0–1 score (closer = higher).

    Default radius is 25km — industrial sites span several km and FRS
    geocodes often differ from curated CSV geocodes by 5-20km.
    """
    if distance_m is None:
        return 0.0
    if distance_m <= 0:
        return 1.0
    if distance_m >= radius_m:
        return 0.0
    # Linear decay
    return 1.0 - (distance_m / radius_m)


def compute_score(
    name_sim: float,
    distance_m: Optional[float],
    naics_match: bool,
    parent_match: bool,
    weights: Optional[dict] = None,
    parent_boost: float = 0.10,
) -> MatchScore:
    """Compute weighted composite confidence score.

    Parameters
    ----------
    name_sim : float
        Name similarity 0.0–1.0.
    distance_m : float or None
        Spatial distance in meters (None if coords unavailable).
    naics_match : bool
        Whether NAICS codes overlap at 4-digit level.
    parent_match : bool
        Whether parent company names match.
    weights : dict, optional
        Override default component weights.
    parent_boost : float
        Extra confidence added when parent companies match.
    """
    w = weights or DEFAULT_WEIGHTS

    spatial = _spatial_score(distance_m)
    naics_val = 1.0 if naics_match else 0.0

    # Base weighted score
    score = (
        w["name"] * name_sim
        + w["spatial"] * spatial
        + w["naics"] * naics_val
        + w["parent"] * (1.0 if parent_match else 0.0)
    )

    # Parent company boost (confirmation signal)
    if parent_match:
        score = min(1.0, score + parent_boost)

    # Strong-name override: very high name similarity in same state = HIGH
    # regardless of distance (FRS geocodes differ from curated data)
    if name_sim >= 0.90:
        score = max(score, 0.80)

    # Determine level
    if score >= HIGH_THRESHOLD:
        level = "HIGH"
    elif score >= MEDIUM_THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Determine method label
    if name_sim >= 0.90:
        method = "name_strong"
    elif distance_m is not None and distance_m < 500 and name_sim > 0.8:
        method = "spatial_name_strong"
    elif name_sim >= 0.85 and naics_match:
        method = "name_state_naics"
    elif distance_m is not None and distance_m < 5000:
        method = "spatial_fuzzy"
    else:
        method = "fuzzy_composite"

    return MatchScore(
        confidence=round(score, 4),
        level=level,
        name_similarity=round(name_sim, 4),
        distance_meters=round(distance_m, 1) if distance_m is not None else None,
        naics_overlap=naics_match,
        parent_match=parent_match,
        method=method,
    )
