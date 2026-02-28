"""Deterministic UUID v5 generation for master site identifiers.

Each facility_uid is a UUID v5 derived from a namespace + canonical key,
so the same physical site always gets the same UID regardless of when
or how many times the build runs.

Canonical key format: "{state}:{city_norm}:{name_norm}"
"""

from __future__ import annotations

import re
import uuid


# Platform-wide namespace UUID (generated once, never changes)
_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "us-bulk-supply-chain.platform")


def _normalize_for_uid(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    t = text.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def generate_facility_uid(name: str, state: str, city: str = "") -> str:
    """Generate a deterministic UUID v5 for a physical site.

    Parameters
    ----------
    name : str
        Canonical facility name.
    state : str
        2-letter state code.
    city : str
        City name (optional but improves uniqueness).

    Returns
    -------
    str
        UUID v5 as a 36-char string (e.g., 'a1b2c3d4-...')
    """
    state_norm = state.upper().strip()
    city_norm = _normalize_for_uid(city)
    name_norm = _normalize_for_uid(name)

    canonical_key = f"{state_norm}:{city_norm}:{name_norm}"
    return str(uuid.uuid5(_NAMESPACE, canonical_key))
