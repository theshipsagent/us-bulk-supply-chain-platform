"""Cargo HS6 Classification — API Module

Source: data/cargo_hs6_dictionary.json (built by build_cargo_dict.py)
HS6 codes are 6-digit strings (e.g. "270900").

Usage:
    from census_trade.config.cargo_codes import load_cargo_reference, get_cargo, get_group
    ref = load_cargo_reference()  # dict keyed by HS6 code
"""

import json
import os

# ============================================================
# CARGO GROUPS (top-level classification)
# ============================================================

CARGO_GROUPS = [
    'Dry Bulk',
    'Liquid Gas',
    'Liquid Bulk',
    'Containerized',
    'Dry',
]

# ============================================================
# LOADER
# ============================================================

_cache = {}


def load_cargo_reference(base_path: str = None) -> dict:
    """Load the cargo HS6 dictionary into a dict keyed by HS6 code.

    Each value has: description, group, commodity, cargo, cargo_detail,
    export_ves_mt, import_ves_mt, total_mt, mapping_source.

    Returns:
        dict: {hs6_code: {description, group, commodity, cargo, cargo_detail,
               export_ves_mt, import_ves_mt, total_mt, mapping_source}}
    """
    if 'ref' in _cache:
        return _cache['ref']

    if base_path is None:
        base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    fpath = os.path.join(base_path, 'cargo_hs6_dictionary.json')
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    _cache['ref'] = data['hs6_lookup']
    return _cache['ref']


# ============================================================
# HELPERS
# ============================================================

def get_cargo(hs6_code: str, base_path: str = None) -> dict:
    """Look up cargo classification for an HS6 code.

    Returns:
        dict with keys: group, commodity, cargo, cargo_detail
        Returns {'group': 'Unmapped', ...} if not found.
    """
    ref = load_cargo_reference(base_path)
    entry = ref.get(str(hs6_code).zfill(6))
    if entry:
        return {
            'group': entry['group'],
            'commodity': entry['commodity'],
            'cargo': entry['cargo'],
            'cargo_detail': entry['cargo_detail'],
        }
    return {
        'group': 'Unmapped',
        'commodity': 'Unmapped',
        'cargo': 'Unmapped',
        'cargo_detail': 'Unmapped',
    }


def get_group(hs6_code: str, base_path: str = None) -> str:
    """Get just the group name for an HS6 code."""
    return get_cargo(hs6_code, base_path)['group']
