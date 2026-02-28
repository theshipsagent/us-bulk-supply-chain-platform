"""Name matching using entity_resolver normalization + rapidfuzz scoring.

Wraps the existing entity_resolver.normalize_org_name() and adds
rapidfuzz.fuzz.token_sort_ratio for fuzzy comparison.
"""

from __future__ import annotations

import re
from typing import Optional

from rapidfuzz import fuzz


# --- Name normalization (adapted from facility_registry entity_resolver) ---

_BUSINESS_SUFFIXES = [
    r'\bINCORPORATED\b', r'\bINC\.?\b', r'\bCORPORATION\b', r'\bCORP\.?\b',
    r'\bCOMPANY\b', r'\bCO\.?\b', r'\bLIMITED\b', r'\bLTD\.?\b',
    r'\bL\.?L\.?C\.?\b', r'\bLLC\b', r'\bL\.?P\.?\b', r'\bLLP\b',
    r'\bPLLC\b', r'\bP\.?C\.?\b',
    r'\bLIMITED LIABILITY COMPANY\b', r'\bLIMITED PARTNERSHIP\b',
]

_OPERATION_TERMS = [
    r'\bPLANT\b', r'\bFACILITY\b', r'\bDIVISION\b', r'\bOPERATIONS\b',
    r'\bMANUFACTURING\b', r'\bINDUSTRIES\b', r'\bPRODUCTS\b',
    r'\bMATERIALS\b', r'\bCONSTRUCTION MATERIALS\b',
    r'\bMILL\b', r'\bMINE\b', r'\bREFINERY\b', r'\bSMELTER\b',
    r'\bTERMINAL\b', r'\bWAREHOUSE\b', r'\bDISTRIBUTION CENTER\b',
]

# Location qualifiers that FRS appends but commodity CSVs don't
_LOCATION_QUALIFIERS = [
    r'\b(?:FLORIDA|CALIFORNIA|TEXAS|PACIFIC|ILLINOIS|OHIO|MICHIGAN|'
    r'VIRGINIA|GEORGIA|ALABAMA|LOUISIANA|INDIANA|MISSISSIPPI|'
    r'TENNESSEE|KENTUCKY|ARKANSAS|SOUTH|NORTH|EAST|WEST|MIDWEST)\b',
]


def normalize_name(name: str) -> str:
    """Normalize a facility name for matching.

    Strips business suffixes, operation terms, and location qualifiers.
    Returns uppercase, single-spaced string.
    """
    if not name:
        return ""

    text = str(name).upper().strip()

    for pat in _BUSINESS_SUFFIXES + _OPERATION_TERMS + _LOCATION_QUALIFIERS:
        text = re.sub(pat, "", text)

    # Collapse punctuation and whitespace
    text = re.sub(r'[,.\-\(\)/&]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_core_brand(name: str) -> str:
    """Extract 1-2 core brand words from a facility name.

    More aggressive than normalize_name — strips filler to get 'NUCOR',
    'ALCOA', 'US STEEL', etc.
    """
    normalized = normalize_name(name)
    if not normalized:
        return str(name).upper().strip()

    filler = {'THE', 'A', 'AN', 'OF', 'AND', 'OR', 'IN', 'ON', 'AT', 'TO',
              'FOR', 'BY', 'WITH', 'FROM', 'AS', 'GROUP', 'COMPANIES', 'HOLDINGS',
              'INTERNATIONAL', 'NATIONAL', 'AMERICAN', 'US', 'USA'}

    words = [w for w in normalized.split() if w not in filler]
    if len(words) >= 2:
        return " ".join(words[:2])
    elif words:
        return words[0]
    return normalized.split()[0] if normalized else ""


def name_similarity(name_a: str, name_b: str) -> float:
    """Compute normalized similarity between two facility names.

    Returns 0.0–1.0 using token_sort_ratio on normalized names.
    """
    norm_a = normalize_name(name_a)
    norm_b = normalize_name(name_b)
    if not norm_a or not norm_b:
        return 0.0
    return fuzz.token_sort_ratio(norm_a, norm_b) / 100.0


def parent_company_match(parent_a: str, parent_b: str) -> bool:
    """Check if two parent company names match (brand-level)."""
    if not parent_a or not parent_b:
        return False
    brand_a = extract_core_brand(parent_a)
    brand_b = extract_core_brand(parent_b)
    if not brand_a or not brand_b:
        return False
    return fuzz.token_sort_ratio(brand_a, brand_b) >= 80


def naics_overlap(codes_a: str, codes_b: str, prefix_len: int = 4) -> bool:
    """Check if two NAICS code sets share a common prefix.

    Compares at `prefix_len` digits (default 4 = industry group).
    """
    if not codes_a or not codes_b:
        return False

    set_a = {c.strip()[:prefix_len] for c in codes_a.split(",") if c.strip()}
    set_b = {c.strip()[:prefix_len] for c in codes_b.split(",") if c.strip()}
    return bool(set_a & set_b)
