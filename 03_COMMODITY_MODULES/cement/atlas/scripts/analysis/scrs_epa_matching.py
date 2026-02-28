"""
SCRS-EPA Crosswalk Builder
===========================
Creates a mapping table (scrs_epa_crosswalk) that links SCRS rail-served facility
records to EPA FRS cement/concrete facility records.

Matching strategies:
  A) CIF Match via us_cement_facilities bridge table
  B) City + State + Fuzzy Name match
  C) State + Address match
  D) Company + State match (weaker, for large companies only)

All cement-relevant SCRS records are included, even if unmatched.
"""

import sys
import io
import re
import duckdb
import pandas as pd
from collections import defaultdict

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'G:/My Drive/LLM/project_cement_markets/atlas/data/atlas.duckdb'

# ---------------------------------------------------------------------------
# 1. KEYWORD LISTS FOR SCRS FILTERING
# ---------------------------------------------------------------------------

# Generic cement/concrete keywords (match anywhere in Customer Name)
GENERIC_KEYWORDS = [
    'CEMENT', 'CONCRETE', 'READY MIX', 'READYMIX', 'REDI-MIX', 'REDI MIX',
    'PRECAST', 'PRESTRESS', 'MASONRY', 'QUIKRETE',
]

# Company names that are unambiguous - match anywhere in name
COMPANY_KEYWORDS_BROAD = [
    'HOLCIM', 'CEMEX', 'ARGOS', 'BUZZI', 'LEHIGH', 'LAFARGE',
    'ASH GROVE', 'HEIDELBERG', 'CALPORTLAND', 'CRH', 'OLDCASTLE',
    'MARTIN MARIETTA', 'FORTERRA', 'KNIFE RIVER',
    'SUWANNEE', 'NATIONAL CEMENT', 'ESSROC', 'LONE STAR',
    'GCC', 'KOSMOS', 'MONARCH', 'CONTINENTAL CEMENT', 'GIANT CEMENT',
    'MITSUBISHI CEMENT', 'DRAKE CEMENT', 'NEVADA CEMENT', 'MOUNTAIN CEMENT',
    'RIVER CEMENT', 'TEXAS LEHIGH', 'CAROLINA CEMENT', 'ROANOKE CEMENT',
    'SIGNAL MOUNTAIN', 'PHOENIX CEMENT', 'SUMMIT MATERIALS', 'ST MARYS',
    'AMRIZE',
]

# BLOCK keyword - needs to be in a cement/masonry context
# We'll use it but also include the Cementitious category as a catch-all
BLOCK_KEYWORD = 'BLOCK'

# Companies that need more specific matching to avoid false positives:
#   EAGLE -> must contain EAGLE MATERIALS or EAGLE CEMENT
#   TITAN -> must contain TITAN AMERICA or TITAN FLORIDA or TITAN CEMENT
#   VULCAN -> must contain VULCAN MATERIALS or VULCAN CONSTRUCTION or VULCAN LIME
#   KEYSTONE -> must contain KEYSTONE CEMENT
COMPANY_KEYWORDS_SPECIFIC = {
    'EAGLE MATERIALS': True, 'EAGLE CEMENT': True,
    'TITAN AMERICA': True, 'TITAN FLORIDA': True, 'TITAN CEMENT': True,
    'VULCAN MATERIALS': True, 'VULCAN CONSTRUCTION': True, 'VULCAN LIME': True,
    'KEYSTONE CEMENT': True,
}


def is_cement_relevant(name_upper):
    """Check if an SCRS customer name is cement/concrete relevant."""
    if not name_upper:
        return False
    for kw in GENERIC_KEYWORDS:
        if kw in name_upper:
            return True
    for kw in COMPANY_KEYWORDS_BROAD:
        if kw in name_upper:
            return True
    for kw in COMPANY_KEYWORDS_SPECIFIC:
        if kw in name_upper:
            return True
    # BLOCK - include if it appears to be a concrete block company
    if BLOCK_KEYWORD in name_upper:
        # Exclude obvious non-cement uses
        non_cement_block = ['BLOCK DRUG', 'BLOCK DISTRIBUTING', 'BLOCK SUPERMARKET',
                            'BLOCK BUSTER', 'BLOCKBUSTER', 'BLOCK CHAIN', 'BLOCKCHAIN',
                            'H&R BLOCK', 'HR BLOCK']
        if not any(ncb in name_upper for ncb in non_cement_block):
            return True
    return False


# ---------------------------------------------------------------------------
# 2. NAME NORMALIZATION AND MATCHING UTILITIES
# ---------------------------------------------------------------------------

# Words to strip for comparison
STOPWORDS = {
    'INC', 'LLC', 'LTD', 'LP', 'CO', 'CORP', 'COMPANY', 'CORPORATION',
    'INDUSTRIES', 'PRODUCTS', 'MATERIALS', 'GROUP', 'HOLDINGS',
    'OF', 'THE', 'AND', 'DBA', 'USA', 'US', 'NA', 'NORTH', 'AMERICA',
    'CONSTRUCTION', 'BUILDING', 'SUPPLY', 'SERVICES', 'ENTERPRISES',
    'INTERNATIONAL', 'NATIONAL',
}

# Abbreviation expansions
ABBREVIATIONS = {
    'RDY': 'READY',
    'MX': 'MIX',
    'CONC': 'CONCRETE',
    'CONSTR': 'CONSTRUCTION',
    'MTL': 'MATERIALS',
    'MTLS': 'MATERIALS',
    'MATL': 'MATERIALS',
    'MATLS': 'MATERIALS',
    'FLA': 'FLORIDA',
    'FL': 'FLORIDA',
    'TX': 'TEXAS',
    'BROS': 'BROTHERS',
}


def normalize_name(name):
    """Normalize a company/facility name for comparison."""
    if not name:
        return ''
    name = name.upper().strip()
    # Remove punctuation
    name = re.sub(r'[^A-Z0-9\s]', ' ', name)
    # Expand abbreviations
    words = name.split()
    words = [ABBREVIATIONS.get(w, w) for w in words]
    # Remove stopwords
    words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return ' '.join(words)


def extract_name_tokens(name):
    """Extract significant tokens from a normalized name."""
    norm = normalize_name(name)
    return set(norm.split())


def name_similarity(name1, name2):
    """Compute token-based Jaccard-like similarity between two names."""
    tokens1 = extract_name_tokens(name1)
    tokens2 = extract_name_tokens(name2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    if not union:
        return 0.0
    return len(intersection) / len(union)


def key_token_overlap(name1, name2):
    """Check if key distinguishing tokens overlap between names.
    Returns (score, matched_tokens).
    """
    tokens1 = extract_name_tokens(name1)
    tokens2 = extract_name_tokens(name2)
    if not tokens1 or not tokens2:
        return 0.0, set()
    # Key tokens are those that aren't generic location/type words
    generic_tokens = {
        'CEMENT', 'CONCRETE', 'READY', 'MIX', 'PRECAST', 'MASONRY', 'BLOCK',
        'PLANT', 'FACILITY', 'SITE', 'TERMINAL', 'DISTRIBUTION',
    }
    key1 = tokens1 - generic_tokens
    key2 = tokens2 - generic_tokens
    if not key1 or not key2:
        # Fall back to full token overlap
        intersection = tokens1 & tokens2
        return len(intersection) / max(len(tokens1), len(tokens2)), intersection
    intersection = key1 & key2
    return len(intersection) / max(len(key1), len(key2)), intersection


def normalize_address(addr):
    """Normalize a street address for comparison."""
    if not addr:
        return ''
    addr = addr.upper().strip()
    # Common abbreviations
    addr = re.sub(r'\bSTREET\b', 'ST', addr)
    addr = re.sub(r'\bAVENUE\b', 'AVE', addr)
    addr = re.sub(r'\bBOULEVARD\b', 'BLVD', addr)
    addr = re.sub(r'\bDRIVE\b', 'DR', addr)
    addr = re.sub(r'\bROAD\b', 'RD', addr)
    addr = re.sub(r'\bLANE\b', 'LN', addr)
    addr = re.sub(r'\bHIGHWAY\b', 'HWY', addr)
    addr = re.sub(r'\bPARKWAY\b', 'PKWY', addr)
    addr = re.sub(r'\bCOURT\b', 'CT', addr)
    addr = re.sub(r'\bPLACE\b', 'PL', addr)
    addr = re.sub(r'\bCIRCLE\b', 'CIR', addr)
    addr = re.sub(r'[^A-Z0-9\s]', ' ', addr)
    addr = re.sub(r'\s+', ' ', addr).strip()
    return addr


def extract_street_number(addr):
    """Extract the leading street number from an address."""
    if not addr:
        return None
    m = re.match(r'^(\d+)', addr.strip())
    return m.group(1) if m else None


def address_similarity(addr1, addr2):
    """Compare two addresses. Returns a score 0-1."""
    n1 = normalize_address(addr1)
    n2 = normalize_address(addr2)
    if not n1 or not n2:
        return 0.0
    # Check street number match
    num1 = extract_street_number(n1)
    num2 = extract_street_number(n2)
    if num1 and num2 and num1 == num2:
        # Same street number - check street name tokens
        tokens1 = set(n1.split())
        tokens2 = set(n2.split())
        overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
        return 0.5 + 0.5 * overlap  # 0.5 base for matching number
    # Token overlap without number match
    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    if not tokens1 or not tokens2:
        return 0.0
    overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
    return 0.3 * overlap


# ---------------------------------------------------------------------------
# CORPORATE PARENT MAPPING (SCRS name -> EPA corporate_parent)
# ---------------------------------------------------------------------------

CORPORATE_PARENT_MAP = {
    'CEMEX': 'CEMEX',
    'HOLCIM': 'Holcim Group',
    'LAFARGE': 'Holcim Group',
    'LEHIGH': 'Heidelberg Materials',
    'HEIDELBERG': 'Heidelberg Materials',
    'ESSROC': 'Heidelberg Materials',
    'ARGOS': 'Argos USA',
    'BUZZI': 'Buzzi Unicem',
    'ASH GROVE': 'Ash Grove',
    'CALPORTLAND': 'CalPortland',
    'CRH': 'CRH plc',
    'OLDCASTLE': 'CRH plc',
    'EAGLE MATERIALS': 'Eagle Materials',
    'MARTIN MARIETTA': 'Martin Marietta',
    'VULCAN': 'Vulcan Materials',
    'FORTERRA': 'Forterra',
    'KNIFE RIVER': 'Knife River (MDU)',
    'TITAN': 'Titan America',
    'QUIKRETE': 'QUIKRETE Holdings',
    'GCC': 'GCC',
    'NATIONAL CEMENT': 'National Cement',
    'LONE STAR': 'Lone Star',
    'SUMMIT MATERIALS': 'Summit Materials',
    'CONTINENTAL CEMENT': 'Continental Cement',
    'GIANT CEMENT': 'Giant Cement',
    'ST MARYS': "St. Mary's Cement",
    'AMRIZE': 'Amrize',
    'SUWANNEE': 'Suwannee',
    'KEYSTONE CEMENT': 'Keystone Cement',
    'KOSMOS': 'Kosmos',
    'MONARCH': 'Monarch Cement',
    'MITSUBISHI CEMENT': 'Mitsubishi Cement',
    'DRAKE CEMENT': 'Drake Cement',
    'NEVADA CEMENT': 'Nevada Cement',
    'MOUNTAIN CEMENT': 'Mountain Cement',
    'RIVER CEMENT': 'River Cement',
    'TEXAS LEHIGH': 'Heidelberg Materials',
    'CAROLINA CEMENT': 'Carolina Cement',
    'ROANOKE CEMENT': 'Roanoke Cement',
    'SIGNAL MOUNTAIN': 'Signal Mountain',
    'PHOENIX CEMENT': 'Phoenix Cement',
}


def get_corporate_parent_from_scrs(name):
    """Map an SCRS customer name to a known corporate parent."""
    if not name:
        return None
    name_upper = name.upper()
    for keyword, parent in CORPORATE_PARENT_MAP.items():
        if keyword in name_upper:
            return parent
    return None


# ---------------------------------------------------------------------------
# 3. MAIN MATCHING LOGIC
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("SCRS-EPA CROSSWALK BUILDER")
    print("=" * 70)

    con = duckdb.connect(DB_PATH)

    # ------------------------------------------------------------------
    # Step 1: Load SCRS cement-relevant records
    # ------------------------------------------------------------------
    print("\n[1] Loading SCRS stations...")
    scrs_all = con.execute("""
        SELECT
            "CIF #" as cif,
            "Customer Name" as customer_name,
            "Street Address" as address,
            City as city,
            State as state,
            Zip as zip,
            "Station Name" as station_name,
            "Serving Carrier" as carrier,
            "Switching Status" as switching,
            Category as category
        FROM scrs_stations
    """).fetchdf()
    print(f"  Total SCRS records: {len(scrs_all):,}")

    # Filter to cement-relevant
    # Include: keyword match OR Cementitious category
    mask = scrs_all['customer_name'].apply(
        lambda x: is_cement_relevant(str(x).upper()) if pd.notna(x) else False
    )
    mask_category = scrs_all['category'] == 'Cementitious'
    scrs_cement = scrs_all[mask | mask_category].copy()
    scrs_cement = scrs_cement.reset_index(drop=True)
    print(f"  Cement-relevant SCRS records: {len(scrs_cement):,}")
    print(f"    - By keyword match: {mask.sum():,}")
    print(f"    - By Cementitious category: {mask_category.sum():,}")
    print(f"    - Overlap: {(mask & mask_category).sum():,}")

    # ------------------------------------------------------------------
    # Step 2: Load EPA facilities
    # ------------------------------------------------------------------
    print("\n[2] Loading EPA cement consumers...")
    epa = con.execute("""
        SELECT
            registry_id,
            fac_name,
            fac_street,
            fac_city,
            fac_state,
            fac_zip,
            latitude,
            longitude,
            segment,
            corporate_parent,
            parent_type,
            facility_subtype
        FROM epa_cement_consumers
    """).fetchdf()
    print(f"  Total EPA records: {len(epa):,}")

    # ------------------------------------------------------------------
    # Step 3: Load us_cement_facilities (for CIF bridge)
    # ------------------------------------------------------------------
    print("\n[3] Loading us_cement_facilities (CIF bridge)...")
    ucf = con.execute("""
        SELECT
            facility_name,
            company_normalized,
            city,
            state,
            rail_cif
        FROM us_cement_facilities
        WHERE rail_cif IS NOT NULL AND rail_cif != ''
    """).fetchdf()
    print(f"  Facilities with CIF: {len(ucf):,}")

    # ------------------------------------------------------------------
    # Build indexes for efficient matching
    # ------------------------------------------------------------------
    print("\n[4] Building match indexes...")

    # EPA index by (state, city_upper) for fast lookup
    epa_by_state_city = defaultdict(list)
    epa_by_state = defaultdict(list)
    for idx, row in epa.iterrows():
        state = str(row['fac_state']).upper().strip() if pd.notna(row['fac_state']) else ''
        city = str(row['fac_city']).upper().strip() if pd.notna(row['fac_city']) else ''
        if state:
            epa_by_state_city[(state, city)].append(idx)
            epa_by_state[state].append(idx)

    # UCF index by CIF
    ucf_by_cif = {}
    for idx, row in ucf.iterrows():
        cif = str(row['rail_cif']).strip()
        ucf_by_cif[cif] = idx

    print(f"  EPA state+city index: {len(epa_by_state_city):,} keys")
    print(f"  UCF CIF index: {len(ucf_by_cif):,} keys")

    # ------------------------------------------------------------------
    # Step 5: Execute matching strategies
    # ------------------------------------------------------------------
    print("\n[5] Executing matching strategies...")

    # Results: list of dicts for crosswalk rows
    results = []
    matched_scrs_indices = set()  # Track which SCRS records got matched

    # For deduplication: track (cif, epa_registry_id) pairs already matched
    matched_pairs = set()

    def add_match(scrs_idx, epa_idx, method, confidence, notes=''):
        """Add a match to results, avoiding duplicates."""
        s = scrs_cement.iloc[scrs_idx]
        cif = str(s['cif']) if pd.notna(s['cif']) else None

        if epa_idx is not None:
            e = epa.iloc[epa_idx]
            reg_id = str(e['registry_id']) if pd.notna(e['registry_id']) else None
            pair_key = (cif, reg_id)
            if pair_key in matched_pairs:
                return False
            matched_pairs.add(pair_key)

            results.append({
                'scrs_cif': cif,
                'scrs_customer': s['customer_name'],
                'scrs_address': s['address'],
                'scrs_city': s['city'],
                'scrs_state': s['state'],
                'scrs_zip': s['zip'],
                'scrs_station': s['station_name'],
                'scrs_carrier': s['carrier'],
                'scrs_switching': s['switching'],
                'epa_registry_id': reg_id,
                'epa_fac_name': e['fac_name'],
                'epa_city': e['fac_city'],
                'epa_state': e['fac_state'],
                'epa_segment': e['segment'],
                'epa_corporate_parent': e['corporate_parent'],
                'epa_parent_type': e['parent_type'],
                'epa_facility_subtype': e['facility_subtype'],
                'epa_latitude': e['latitude'] if pd.notna(e['latitude']) else None,
                'epa_longitude': e['longitude'] if pd.notna(e['longitude']) else None,
                'match_method': method,
                'match_confidence': confidence,
                'match_notes': notes,
            })
        else:
            results.append({
                'scrs_cif': cif,
                'scrs_customer': s['customer_name'],
                'scrs_address': s['address'],
                'scrs_city': s['city'],
                'scrs_state': s['state'],
                'scrs_zip': s['zip'],
                'scrs_station': s['station_name'],
                'scrs_carrier': s['carrier'],
                'scrs_switching': s['switching'],
                'epa_registry_id': None,
                'epa_fac_name': None,
                'epa_city': None,
                'epa_state': None,
                'epa_segment': None,
                'epa_corporate_parent': None,
                'epa_parent_type': None,
                'epa_facility_subtype': None,
                'epa_latitude': None,
                'epa_longitude': None,
                'match_method': 'UNMATCHED',
                'match_confidence': None,
                'match_notes': notes,
            })

        matched_scrs_indices.add(scrs_idx)
        return True

    # ---- Strategy A: CIF Match via us_cement_facilities ----
    print("\n  Strategy A: CIF Match via us_cement_facilities...")
    cif_matches = 0
    for scrs_idx, s_row in scrs_cement.iterrows():
        cif = str(s_row['cif']).strip() if pd.notna(s_row['cif']) else ''
        if not cif or cif not in ucf_by_cif:
            continue

        ucf_row = ucf.iloc[ucf_by_cif[cif]]
        ucf_city = str(ucf_row['city']).upper().strip() if pd.notna(ucf_row['city']) else ''
        ucf_state = str(ucf_row['state']).upper().strip() if pd.notna(ucf_row['state']) else ''
        ucf_company = str(ucf_row['company_normalized']).upper().strip() if pd.notna(ucf_row['company_normalized']) else ''

        # Try to find matching EPA record via city+state+name
        best_epa_idx = None
        best_score = 0.0

        candidates = epa_by_state_city.get((ucf_state, ucf_city), [])
        for epa_idx in candidates:
            e_row = epa.iloc[epa_idx]
            epa_name = str(e_row['fac_name']) if pd.notna(e_row['fac_name']) else ''

            # Compare UCF company to EPA name
            score = name_similarity(ucf_company, epa_name)
            key_score, _ = key_token_overlap(ucf_company, epa_name)

            # Also check corporate parent
            scrs_parent = get_corporate_parent_from_scrs(ucf_company)
            epa_parent = str(e_row['corporate_parent']) if pd.notna(e_row['corporate_parent']) else ''

            parent_match = False
            if scrs_parent and epa_parent:
                parent_match = (scrs_parent.upper() in epa_parent.upper() or
                                epa_parent.upper() in scrs_parent.upper())

            combined = max(score, key_score)
            if parent_match:
                combined = max(combined, 0.6)

            if combined > best_score:
                best_score = combined
                best_epa_idx = epa_idx

        if best_epa_idx is not None and best_score >= 0.15:
            e_row = epa.iloc[best_epa_idx]
            notes = f"CIF {cif} -> UCF '{ucf_row['company_normalized']}' -> EPA '{e_row['fac_name']}' (score={best_score:.2f})"
            if add_match(scrs_idx, best_epa_idx, 'CIF', 'HIGH', notes):
                cif_matches += 1
        elif best_epa_idx is None:
            # CIF found in UCF but no EPA match in same city - try broader state match
            candidates_state = epa_by_state.get(ucf_state, [])
            for epa_idx in candidates_state:
                e_row = epa.iloc[epa_idx]
                epa_name = str(e_row['fac_name']) if pd.notna(e_row['fac_name']) else ''
                epa_city = str(e_row['fac_city']).upper().strip() if pd.notna(e_row['fac_city']) else ''

                scrs_parent = get_corporate_parent_from_scrs(ucf_company)
                epa_parent = str(e_row['corporate_parent']) if pd.notna(e_row['corporate_parent']) else ''

                # Need both name match and address/close city
                score = name_similarity(ucf_company, epa_name)
                key_score, _ = key_token_overlap(ucf_company, epa_name)
                combined = max(score, key_score)

                parent_match = False
                if scrs_parent and epa_parent:
                    parent_match = (scrs_parent.upper() in epa_parent.upper() or
                                    epa_parent.upper() in scrs_parent.upper())
                if parent_match:
                    combined = max(combined, 0.5)

                if combined > best_score:
                    best_score = combined
                    best_epa_idx = epa_idx

            if best_epa_idx is not None and best_score >= 0.4:
                e_row = epa.iloc[best_epa_idx]
                notes = f"CIF {cif} -> UCF '{ucf_row['company_normalized']}' state match -> EPA '{e_row['fac_name']}' (score={best_score:.2f})"
                if add_match(scrs_idx, best_epa_idx, 'CIF', 'MEDIUM', notes):
                    cif_matches += 1

    print(f"    CIF matches: {cif_matches}")

    # ---- Strategy B: City + State + Fuzzy Name Match ----
    print("\n  Strategy B: City + State + Fuzzy Name Match...")
    csn_matches = 0
    for scrs_idx, s_row in scrs_cement.iterrows():
        if scrs_idx in matched_scrs_indices:
            continue

        s_state = str(s_row['state']).upper().strip() if pd.notna(s_row['state']) else ''
        s_city = str(s_row['city']).upper().strip() if pd.notna(s_row['city']) else ''
        s_name = str(s_row['customer_name']) if pd.notna(s_row['customer_name']) else ''

        if not s_state or not s_city:
            continue

        candidates = epa_by_state_city.get((s_state, s_city), [])
        if not candidates:
            continue

        best_epa_idx = None
        best_score = 0.0
        best_notes = ''

        for epa_idx in candidates:
            e_row = epa.iloc[epa_idx]
            epa_name = str(e_row['fac_name']) if pd.notna(e_row['fac_name']) else ''

            # Token-based name similarity
            score = name_similarity(s_name, epa_name)
            key_score, matched_tokens = key_token_overlap(s_name, epa_name)

            # Corporate parent matching boost
            scrs_parent = get_corporate_parent_from_scrs(s_name)
            epa_parent = str(e_row['corporate_parent']) if pd.notna(e_row['corporate_parent']) else ''

            parent_match = False
            if scrs_parent and epa_parent:
                parent_match = (scrs_parent.upper() in epa_parent.upper() or
                                epa_parent.upper() in scrs_parent.upper())

            combined = max(score, key_score)
            if parent_match:
                combined = max(combined, 0.55)

            if combined > best_score:
                best_score = combined
                best_epa_idx = epa_idx
                best_notes = f"Name sim={score:.2f}, key_overlap={key_score:.2f}, parent_match={parent_match}, tokens={matched_tokens}"

        if best_epa_idx is not None and best_score >= 0.25:
            confidence = 'HIGH' if best_score >= 0.5 else 'MEDIUM'
            e_row = epa.iloc[best_epa_idx]
            notes = f"City+State+Name: SCRS '{s_name}' -> EPA '{e_row['fac_name']}'. {best_notes}"
            if add_match(scrs_idx, best_epa_idx, 'CITY_STATE_NAME', confidence, notes):
                csn_matches += 1

    print(f"    City+State+Name matches: {csn_matches}")

    # ---- Strategy C: State + Address Match ----
    print("\n  Strategy C: State + Address Match...")
    addr_matches = 0
    for scrs_idx, s_row in scrs_cement.iterrows():
        if scrs_idx in matched_scrs_indices:
            continue

        s_state = str(s_row['state']).upper().strip() if pd.notna(s_row['state']) else ''
        s_addr = str(s_row['address']) if pd.notna(s_row['address']) else ''
        s_name = str(s_row['customer_name']) if pd.notna(s_row['customer_name']) else ''
        s_city = str(s_row['city']).upper().strip() if pd.notna(s_row['city']) else ''

        if not s_state or not s_addr:
            continue

        s_street_num = extract_street_number(s_addr)
        if not s_street_num:
            continue

        # Search EPA in same state (try same city first, then nearby)
        candidates = epa_by_state_city.get((s_state, s_city), [])
        # Also check state-level if no city match
        if not candidates:
            candidates = epa_by_state.get(s_state, [])

        best_epa_idx = None
        best_score = 0.0
        best_notes = ''

        for epa_idx in candidates:
            e_row = epa.iloc[epa_idx]
            epa_addr = str(e_row['fac_street']) if pd.notna(e_row['fac_street']) else ''
            epa_name = str(e_row['fac_name']) if pd.notna(e_row['fac_name']) else ''
            epa_city = str(e_row['fac_city']).upper().strip() if pd.notna(e_row['fac_city']) else ''

            addr_score = address_similarity(s_addr, epa_addr)
            name_score = name_similarity(s_name, epa_name)

            # Require strong address match
            if addr_score < 0.5:
                continue

            # Bonus for city match
            city_bonus = 0.1 if s_city == epa_city else 0.0

            combined = addr_score + 0.3 * name_score + city_bonus

            if combined > best_score:
                best_score = combined
                best_epa_idx = epa_idx
                best_notes = f"addr_score={addr_score:.2f}, name_score={name_score:.2f}, city_match={s_city == epa_city}"

        if best_epa_idx is not None and best_score >= 0.6:
            confidence = 'HIGH' if best_score >= 0.8 else 'MEDIUM'
            e_row = epa.iloc[best_epa_idx]
            notes = f"Address: SCRS '{s_addr}' -> EPA '{e_row['fac_street']}'. {best_notes}"
            if add_match(scrs_idx, best_epa_idx, 'ADDRESS', confidence, notes):
                addr_matches += 1

    print(f"    Address matches: {addr_matches}")

    # ---- Strategy D: Company + State (large companies only) ----
    print("\n  Strategy D: Company + State (large companies only)...")
    cs_matches = 0

    for scrs_idx, s_row in scrs_cement.iterrows():
        if scrs_idx in matched_scrs_indices:
            continue

        s_state = str(s_row['state']).upper().strip() if pd.notna(s_row['state']) else ''
        s_name = str(s_row['customer_name']) if pd.notna(s_row['customer_name']) else ''

        if not s_state:
            continue

        # Only for known large companies
        scrs_parent = get_corporate_parent_from_scrs(s_name)
        if not scrs_parent:
            continue

        candidates = epa_by_state.get(s_state, [])
        if not candidates:
            continue

        best_epa_idx = None
        best_score = 0.0
        best_notes = ''

        for epa_idx in candidates:
            e_row = epa.iloc[epa_idx]
            epa_parent = str(e_row['corporate_parent']) if pd.notna(e_row['corporate_parent']) else ''
            epa_name = str(e_row['fac_name']) if pd.notna(e_row['fac_name']) else ''

            # Must match corporate parent
            parent_match = False
            if epa_parent:
                parent_match = (scrs_parent.upper() in epa_parent.upper() or
                                epa_parent.upper() in scrs_parent.upper())

            if not parent_match:
                continue

            # Score by name similarity
            score = name_similarity(s_name, epa_name)
            key_score, matched_tokens = key_token_overlap(s_name, epa_name)
            combined = max(score, key_score)

            # Check city proximity for better scoring
            s_city = str(s_row['city']).upper().strip() if pd.notna(s_row['city']) else ''
            epa_city = str(e_row['fac_city']).upper().strip() if pd.notna(e_row['fac_city']) else ''
            if s_city == epa_city:
                combined += 0.3  # boost for city match (shouldn't happen since B would have caught it, but just in case)

            if combined > best_score:
                best_score = combined
                best_epa_idx = epa_idx
                best_notes = f"Parent: {scrs_parent} -> {epa_parent}, name_sim={combined:.2f}, tokens={matched_tokens}"

        if best_epa_idx is not None and best_score >= 0.15:
            e_row = epa.iloc[best_epa_idx]
            notes = f"Company+State: SCRS '{s_name}' ({s_state}) -> EPA '{e_row['fac_name']}'. {best_notes}"
            if add_match(scrs_idx, best_epa_idx, 'COMPANY_STATE', 'LOW', notes):
                cs_matches += 1

    print(f"    Company+State matches: {cs_matches}")

    # ---- Add unmatched SCRS records ----
    print("\n  Adding unmatched SCRS records...")
    unmatched = 0
    for scrs_idx, s_row in scrs_cement.iterrows():
        if scrs_idx not in matched_scrs_indices:
            add_match(scrs_idx, None, 'UNMATCHED', None, 'No EPA match found')
            unmatched += 1

    print(f"    Unmatched records: {unmatched}")

    # ------------------------------------------------------------------
    # Step 6: Create crosswalk table
    # ------------------------------------------------------------------
    print(f"\n[6] Creating crosswalk table ({len(results):,} rows)...")

    results_df = pd.DataFrame(results)
    results_df.insert(0, 'match_id', range(1, len(results_df) + 1))

    # Drop existing table if present
    con.execute("DROP TABLE IF EXISTS scrs_epa_crosswalk")

    # Register dataframe and create table
    con.execute("CREATE TABLE scrs_epa_crosswalk AS SELECT * FROM results_df")

    # Verify
    count = con.execute("SELECT COUNT(*) FROM scrs_epa_crosswalk").fetchone()[0]
    print(f"  Table created with {count:,} rows")

    # ------------------------------------------------------------------
    # Step 7: Print summary statistics
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    total = con.execute("SELECT COUNT(*) FROM scrs_epa_crosswalk").fetchone()[0]
    matched = con.execute("SELECT COUNT(*) FROM scrs_epa_crosswalk WHERE match_method != 'UNMATCHED'").fetchone()[0]
    unmatched_count = con.execute("SELECT COUNT(*) FROM scrs_epa_crosswalk WHERE match_method = 'UNMATCHED'").fetchone()[0]

    print(f"\nTotal SCRS cement records in crosswalk: {total:,}")
    print(f"  Matched to EPA:   {matched:,} ({100*matched/total:.1f}%)")
    print(f"  Unmatched:        {unmatched_count:,} ({100*unmatched_count/total:.1f}%)")

    print("\n--- Matches by Method ---")
    r = con.execute("""
        SELECT match_method, match_confidence, COUNT(*) as cnt
        FROM scrs_epa_crosswalk
        GROUP BY match_method, match_confidence
        ORDER BY match_method, match_confidence
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Matched Records by EPA Segment ---")
    r = con.execute("""
        SELECT epa_segment, COUNT(*) as cnt
        FROM scrs_epa_crosswalk
        WHERE match_method != 'UNMATCHED'
        GROUP BY epa_segment
        ORDER BY cnt DESC
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Top 20 Companies by Match Count ---")
    r = con.execute("""
        SELECT scrs_customer, COUNT(*) as total_records,
               SUM(CASE WHEN match_method != 'UNMATCHED' THEN 1 ELSE 0 END) as matched,
               SUM(CASE WHEN match_method = 'UNMATCHED' THEN 1 ELSE 0 END) as unmatched
        FROM scrs_epa_crosswalk
        GROUP BY scrs_customer
        ORDER BY total_records DESC
        LIMIT 20
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Match Method Distribution ---")
    r = con.execute("""
        SELECT match_method, COUNT(*) as cnt,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM scrs_epa_crosswalk
        GROUP BY match_method
        ORDER BY cnt DESC
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Top Corporate Parents (matched) ---")
    r = con.execute("""
        SELECT epa_corporate_parent, COUNT(*) as cnt
        FROM scrs_epa_crosswalk
        WHERE epa_corporate_parent IS NOT NULL
        GROUP BY epa_corporate_parent
        ORDER BY cnt DESC
        LIMIT 15
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Sample Matches (first 10) ---")
    r = con.execute("""
        SELECT match_id, scrs_customer, scrs_city, scrs_state,
               epa_fac_name, epa_city, epa_segment,
               match_method, match_confidence
        FROM scrs_epa_crosswalk
        WHERE match_method != 'UNMATCHED'
        LIMIT 10
    """).fetchdf()
    print(r.to_string(index=False))

    print("\n--- Sample Unmatched (first 10) ---")
    r = con.execute("""
        SELECT match_id, scrs_customer, scrs_city, scrs_state, scrs_carrier
        FROM scrs_epa_crosswalk
        WHERE match_method = 'UNMATCHED'
        LIMIT 10
    """).fetchdf()
    print(r.to_string(index=False))

    # Verify table schema
    print("\n--- Crosswalk Table Schema ---")
    r = con.execute("DESCRIBE scrs_epa_crosswalk").fetchdf()
    print(r.to_string(index=False))

    con.close()
    print("\n" + "=" * 70)
    print("DONE. Crosswalk table 'scrs_epa_crosswalk' created in atlas.duckdb")
    print("=" * 70)


if __name__ == '__main__':
    main()
