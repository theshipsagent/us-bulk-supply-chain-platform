"""
Vessel Name Normalizer — Shared utility for matching vessel names across datasets.

MRTIS uses mixed case with various punctuation (e.g., "African Lorikeet"),
while FGIS uses uppercase (e.g., "AFRICAN LORIKEET"). This module provides
normalization functions to enable reliable matching.

Reusable across MRTIS, FGIS, and manifest projects.
"""

import re


def normalize_vessel_name(name: str) -> str:
    """Normalize a vessel name for display/comparison.

    Steps: strip, uppercase, remove punctuation (dots, hyphens, slashes),
    collapse whitespace to single spaces.

    Returns empty string for None/empty input.
    """
    if not name or not isinstance(name, str):
        return ""
    name = name.strip().upper()
    # Remove dots, hyphens, slashes, and other common punctuation
    name = re.sub(r'[.\-/\'\"()]+', ' ', name)
    # Collapse multiple spaces to one
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def build_name_key(name: str) -> str:
    """Build a fully collapsed key (no spaces) for dictionary lookup.

    Applies normalize_vessel_name then removes all remaining spaces.
    E.g., "African Lorikeet" -> "AFRICANLORIKEET"
    """
    return normalize_vessel_name(name).replace(' ', '')
