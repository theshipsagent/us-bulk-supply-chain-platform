"""
Cross-Reference Analysis: Linking US Cement Industry Datasets
=============================================================
Connects trade_imports, us_cement_facilities, gem_plants, epa_cement_consumers,
and usgs_monthly_shipments to build a unified view of the US cement supply chain.
"""

import sys
import io
import os
import re
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb
from rapidfuzz import fuzz, process

# ──────────────────────────────────────────────────────────────────────────────
# Database connection
# ──────────────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'atlas.duckdb')
con = duckdb.connect(DB_PATH, read_only=True)

# ──────────────────────────────────────────────────────────────────────────────
# Helper: US state name -> abbreviation
# ──────────────────────────────────────────────────────────────────────────────
STATE_ABBREV = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
    'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
    'Pennsylvania': 'PA', 'Puerto Rico': 'PR', 'Rhode Island': 'RI',
    'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
    'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA',
    'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI',
    'Wyoming': 'WY',
}
STATE_NAME_FROM_ABBREV = {v: k for k, v in STATE_ABBREV.items()}

def normalize(s):
    """Lowercase, strip punctuation, collapse whitespace."""
    if s is None:
        return ''
    s = s.upper().strip()
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_state_from_port(port_str):
    """Extract 2-letter state abbreviation from port_of_unlading string."""
    if port_str is None:
        return None
    for state_name, abbrev in STATE_ABBREV.items():
        if state_name.lower() in port_str.lower():
            return abbrev
    return None


# ======================================================================
# SECTION 1: Import Consignees -> EPA Facilities (Fuzzy Match)
# ======================================================================
print("=" * 90)
print("SECTION 1: IMPORT CONSIGNEES -> EPA FACILITY MATCHING")
print("=" * 90)

# Get top consignees by volume
consignees = con.execute("""
    SELECT consignee, SUM(weight_tons) as total_tons, COUNT(*) as shipments
    FROM trade_imports
    WHERE consignee IS NOT NULL
    GROUP BY consignee
    ORDER BY total_tons DESC
""").fetchall()

# Get all EPA facility names with details
epa_facs = con.execute("""
    SELECT DISTINCT fac_name, fac_city, fac_state, segment, parent_company
    FROM epa_cement_consumers
""").fetchall()

epa_names = [normalize(r[0]) for r in epa_facs]
epa_lookup = {}
for i, r in enumerate(epa_facs):
    key = normalize(r[0])
    if key not in epa_lookup:
        epa_lookup[key] = []
    epa_lookup[key].append(r)

# Also build a parent_company lookup
epa_by_parent = defaultdict(list)
for r in epa_facs:
    if r[4]:
        epa_by_parent[normalize(r[4])].append(r)

# Fuzzy match consignees against EPA facility names and parent companies
print(f"\nMatching {len(consignees)} import consignees against {len(epa_facs)} EPA facilities...")
print(f"{'Consignee':<35s} {'Import Tons':>12s} {'Ships':>5s} | {'Match Type':<12s} {'EPA Name / Parent':<45s} {'Seg':<25s} {'Score':>5s}")
print("-" * 150)

consignee_matches = []
unique_epa_names_list = list(set(epa_names))
unique_parents_list = list(set(normalize(k) for k in epa_by_parent.keys()))

for consignee_name, total_tons, shipments in consignees:
    norm_consignee = normalize(consignee_name)

    best_match = None
    best_score = 0
    match_type = None

    # Strategy 1: Fuzzy match against facility names
    result = process.extractOne(norm_consignee, unique_epa_names_list, scorer=fuzz.token_set_ratio, score_cutoff=70)
    if result:
        matched_name, score, _ = result
        if score > best_score:
            best_score = score
            best_match = matched_name
            match_type = 'fac_name'

    # Strategy 2: Fuzzy match against parent companies
    result2 = process.extractOne(norm_consignee, unique_parents_list, scorer=fuzz.token_set_ratio, score_cutoff=75)
    if result2:
        matched_parent, score2, _ = result2
        if score2 > best_score:
            best_score = score2
            best_match = matched_parent
            match_type = 'parent_co'

    # Strategy 3: Exact substring containment
    for parent_norm, facs in epa_by_parent.items():
        if len(norm_consignee) >= 4 and (norm_consignee in parent_norm or parent_norm in norm_consignee):
            if len(parent_norm) >= 4:
                score3 = 95
                if score3 > best_score:
                    best_score = score3
                    best_match = parent_norm
                    match_type = 'substring'

    if best_match and best_score >= 70:
        if match_type == 'fac_name':
            details = epa_lookup.get(best_match, [])
        elif match_type in ('parent_co', 'substring'):
            details = epa_by_parent.get(best_match, [])
        else:
            details = []

        segments = set(d[3] for d in details if d[3])
        seg_str = ', '.join(sorted(segments)) if segments else '?'
        display_match = best_match[:45]
        consignee_matches.append((consignee_name, total_tons, shipments, best_match, match_type, best_score, segments, details))
        print(f"{consignee_name:<35s} {total_tons:>12,d} {shipments:>5d} | {match_type:<12s} {display_match:<45s} {seg_str:<25s} {best_score:>5.0f}")
    else:
        consignee_matches.append((consignee_name, total_tons, shipments, None, None, 0, set(), []))
        print(f"{consignee_name:<35s} {total_tons:>12,d} {shipments:>5d} | {'NO MATCH':<12s} {'--':<45s} {'--':<25s} {'--':>5s}")

matched_consignees = [c for c in consignee_matches if c[3] is not None]
matched_volume = sum(c[1] for c in matched_consignees)
total_volume = sum(c[1] for c in consignee_matches)
print(f"\nSummary: {len(matched_consignees)}/{len(consignee_matches)} consignees matched to EPA facilities")
print(f"  Matched volume: {matched_volume:,.0f} tons ({matched_volume/total_volume*100:.1f}% of total)")
print(f"  Unmatched volume: {total_volume - matched_volume:,.0f} tons ({(total_volume - matched_volume)/total_volume*100:.1f}%)")

# Segment breakdown of matched importers
print("\nSegment breakdown of matched import consignees:")
seg_vol = defaultdict(lambda: [0, 0])
for c in matched_consignees:
    for seg in c[6]:
        seg_vol[seg][0] += c[1]
        seg_vol[seg][1] += 1
for seg, (vol, cnt) in sorted(seg_vol.items(), key=lambda x: -x[1][0]):
    print(f"  {seg:<30s} {cnt:>3d} consignees  {vol:>14,.0f} tons")


# ======================================================================
# SECTION 2: Rail-Served Sites -> EPA Facilities
# ======================================================================
print("\n" + "=" * 90)
print("SECTION 2: RAIL-SERVED SITES -> EPA FACILITY MATCHING")
print("=" * 90)

rail_sites = con.execute("""
    SELECT facility_name, company, city, state, facility_type, rail_carrier, is_rail_served
    FROM us_cement_facilities
    WHERE is_rail_served = true
""").fetchall()

epa_all = con.execute("""
    SELECT fac_name, fac_city, fac_state, segment, parent_company, registry_id
    FROM epa_cement_consumers
""").fetchall()

# Build EPA index by state+city
epa_by_state_city = defaultdict(list)
for r in epa_all:
    key = (r[2], normalize(r[1]))  # (state, normalized_city)
    epa_by_state_city[key].append(r)

# Build EPA index by state only for company matching
epa_by_state = defaultdict(list)
for r in epa_all:
    epa_by_state[r[2]].append(r)

print(f"\nCross-referencing {len(rail_sites)} rail-served sites against {len(epa_all)} EPA facilities...")

rail_matched = 0
rail_unmatched = 0
rail_match_details = []
rail_seg_counts = defaultdict(int)
rail_type_seg = defaultdict(lambda: defaultdict(int))

for fname, company, city, state, ftype, carrier, _ in rail_sites:
    norm_city = normalize(city) if city else ''
    norm_name = normalize(fname) if fname else ''
    norm_company = normalize(company) if company else ''

    matched = False
    matched_epa = None

    # Strategy 1: Same state + same city + fuzzy name match
    candidates = epa_by_state_city.get((state, norm_city), [])
    if candidates:
        cand_names = [normalize(c[0]) for c in candidates]
        # Try matching against facility name
        result = process.extractOne(norm_name, cand_names, scorer=fuzz.token_set_ratio, score_cutoff=65)
        if result:
            matched = True
            idx = cand_names.index(result[0])
            matched_epa = candidates[idx]
        else:
            # Try matching company name against EPA parent
            for c in candidates:
                parent_norm = normalize(c[4]) if c[4] else ''
                if parent_norm and (fuzz.token_set_ratio(norm_company, parent_norm) >= 70 or
                                    fuzz.token_set_ratio(norm_name, parent_norm) >= 70):
                    matched = True
                    matched_epa = c
                    break

    # Strategy 2: Same state + fuzzy name/company match (broader)
    if not matched:
        state_cands = epa_by_state.get(state, [])
        if state_cands:
            cand_names2 = [normalize(c[0]) for c in state_cands]
            result2 = process.extractOne(norm_name, cand_names2, scorer=fuzz.token_set_ratio, score_cutoff=80)
            if result2:
                matched = True
                idx2 = cand_names2.index(result2[0])
                matched_epa = state_cands[idx2]

    if matched and matched_epa:
        rail_matched += 1
        seg = matched_epa[3]
        rail_seg_counts[seg] += 1
        rail_type_seg[ftype][seg] += 1
        rail_match_details.append((fname, company, city, state, ftype, carrier, matched_epa))
    else:
        rail_unmatched += 1

print(f"\nResults:")
print(f"  Rail-served sites matched to EPA:   {rail_matched:>6,d} ({rail_matched/len(rail_sites)*100:.1f}%)")
print(f"  Rail-served sites NOT in EPA:       {rail_unmatched:>6,d} ({rail_unmatched/len(rail_sites)*100:.1f}%)")

print(f"\nEPA segment distribution of matched rail-served sites:")
for seg, cnt in sorted(rail_seg_counts.items(), key=lambda x: -x[1]):
    print(f"  {seg:<30s} {cnt:>5d} sites ({cnt/rail_matched*100:.1f}%)")

print(f"\nRail facility type -> EPA segment cross-tab:")
print(f"  {'Rail Facility Type':<25s}", end="")
all_segs = sorted(set(s for d in rail_type_seg.values() for s in d.keys()))
for seg in all_segs:
    short = seg[:15]
    print(f" {short:>15s}", end="")
print(f" {'TOTAL':>8s}")
print("  " + "-" * (25 + 16 * len(all_segs) + 8))
for ftype in sorted(rail_type_seg.keys()):
    total_ft = sum(rail_type_seg[ftype].values())
    print(f"  {ftype:<25s}", end="")
    for seg in all_segs:
        print(f" {rail_type_seg[ftype].get(seg, 0):>15d}", end="")
    print(f" {total_ft:>8d}")

# Show some example matches
print(f"\nSample rail-served site matches (first 15):")
print(f"  {'Rail Site':<35s} {'City':<15s} {'ST':<4s} {'Rail Type':<20s} -> {'EPA Facility':<40s} {'EPA Segment':<25s}")
print("  " + "-" * 150)
for det in rail_match_details[:15]:
    fname, company, city, state, ftype, carrier, epa = det
    print(f"  {(fname or '')[:35]:<35s} {(city or '')[:15]:<15s} {state:<4s} {ftype:<20s} -> {epa[0][:40]:<40s} {epa[3]:<25s}")


# ======================================================================
# SECTION 3: GEM Plants -> EPA Facilities
# ======================================================================
print("\n" + "=" * 90)
print("SECTION 3: GEM PLANTS -> EPA CEMENT MANUFACTURERS MATCHING")
print("=" * 90)

gem_plants = con.execute("""
    SELECT "GEM Asset name (English)", "Municipality", "Subnational unit",
           "Owner name (English)", "Parent",
           "Cement Capacity (millions metric tonnes per annum)",
           "Operating status"
    FROM gem_plants
""").fetchall()

epa_mfrs = con.execute("""
    SELECT fac_name, fac_city, fac_state, segment, parent_company, registry_id
    FROM epa_cement_consumers
    WHERE segment = 'CEMENT_MANUFACTURER'
""").fetchall()

# Build EPA manufacturer index by state
epa_mfr_by_state = defaultdict(list)
for r in epa_mfrs:
    epa_mfr_by_state[r[2]].append(r)

print(f"\nMatching {len(gem_plants)} GEM plants against {len(epa_mfrs)} EPA CEMENT_MANUFACTURER facilities...")
print(f"\n{'GEM Plant':<40s} {'City':<18s} {'State':<6s} {'Cap(Mt)':<8s} {'Status':<12s} | {'EPA Match':<45s} {'Score':>5s}")
print("-" * 145)

gem_matched = 0
gem_unmatched = 0
gem_match_details = []
gem_unmatched_list = []

for gem_name, municipality, state_full, owner, parent, capacity, status in gem_plants:
    state_abbrev = STATE_ABBREV.get(state_full, '')
    norm_gem = normalize(gem_name)
    norm_municipality = normalize(municipality) if municipality else ''
    # Clean owner: remove percentage brackets
    owner_clean = re.sub(r'\[.*?\]', '', owner).strip() if owner else ''
    parent_clean = re.sub(r'\[.*?\]', '', parent).strip() if parent else ''
    norm_owner = normalize(owner_clean)
    norm_parent = normalize(parent_clean)

    candidates = epa_mfr_by_state.get(state_abbrev, [])
    best_match = None
    best_score = 0

    if candidates:
        cand_names = [normalize(c[0]) for c in candidates]

        # Strategy 1: Match GEM plant name against EPA facility name
        result = process.extractOne(norm_gem, cand_names, scorer=fuzz.token_set_ratio, score_cutoff=55)
        if result:
            matched_n, score, _ = result
            if score > best_score:
                best_score = score
                idx = cand_names.index(matched_n)
                best_match = candidates[idx]

        # Strategy 2: Match owner/parent against EPA parent_company or facility name
        for c in candidates:
            epa_parent_norm = normalize(c[4]) if c[4] else ''
            epa_name_norm = normalize(c[0])
            epa_city_norm = normalize(c[1]) if c[1] else ''

            # Check city match + owner/parent match
            city_match = (norm_municipality and epa_city_norm and
                          fuzz.ratio(norm_municipality, epa_city_norm) >= 80)

            owner_score = max(
                fuzz.token_set_ratio(norm_owner, epa_name_norm),
                fuzz.token_set_ratio(norm_owner, epa_parent_norm) if epa_parent_norm else 0,
                fuzz.token_set_ratio(norm_parent, epa_name_norm),
                fuzz.token_set_ratio(norm_parent, epa_parent_norm) if epa_parent_norm else 0,
            )

            combined = 0
            if city_match and owner_score >= 50:
                combined = 90
            elif city_match:
                combined = 75
            elif owner_score >= 80:
                combined = owner_score

            if combined > best_score:
                best_score = combined
                best_match = c

    cap_str = str(capacity) if capacity else '?'
    if best_match and best_score >= 55:
        gem_matched += 1
        gem_match_details.append((gem_name, municipality, state_abbrev, capacity, status, best_match, best_score))
        print(f"{gem_name[:40]:<40s} {(municipality or '')[:18]:<18s} {state_abbrev:<6s} {cap_str:<8s} {(status or '')[:12]:<12s} | {best_match[0][:45]:<45s} {best_score:>5.0f}")
    else:
        gem_unmatched += 1
        gem_unmatched_list.append((gem_name, municipality, state_abbrev, capacity, status))
        print(f"{gem_name[:40]:<40s} {(municipality or '')[:18]:<18s} {state_abbrev:<6s} {cap_str:<8s} {(status or '')[:12]:<12s} | {'** NO MATCH **':<45s} {'--':>5s}")

print(f"\nSummary:")
print(f"  GEM plants matched to EPA:    {gem_matched:>4d} / {len(gem_plants)} ({gem_matched/len(gem_plants)*100:.1f}%)")
print(f"  GEM plants NOT in EPA:        {gem_unmatched:>4d} / {len(gem_plants)} ({gem_unmatched/len(gem_plants)*100:.1f}%)")

operating = [g for g in gem_plants if g[6] == 'operating']
matched_operating = [g for g in gem_match_details if g[4] == 'operating']
print(f"  Operating GEM plants matched: {len(matched_operating):>4d} / {len(operating)} ({len(matched_operating)/len(operating)*100:.1f}%)")

if gem_unmatched_list:
    print(f"\nUnmatched GEM plants (no EPA CEMENT_MANUFACTURER found in same state):")
    for name, muni, st, cap, status in gem_unmatched_list:
        print(f"  {name:<40s}  {(muni or ''):<18s}  {st:<4s}  cap={cap}  status={status}")


# ======================================================================
# SECTION 4: STATE-LEVEL SUPPLY CHAIN MAP
# ======================================================================
print("\n" + "=" * 90)
print("SECTION 4: STATE-LEVEL SUPPLY CHAIN MAP")
print("=" * 90)

# 4a: Domestic production capacity from GEM (operating plants)
gem_state_cap = {}
for row in con.execute("""
    SELECT "Subnational unit",
           COUNT(*) as plants,
           SUM(TRY_CAST("Cement Capacity (millions metric tonnes per annum)" AS DOUBLE)) as total_cap_mt
    FROM gem_plants
    WHERE "Operating status" = 'operating'
    GROUP BY "Subnational unit"
""").fetchall():
    st = STATE_ABBREV.get(row[0], row[0])
    # Convert millions metric tonnes to short tons (1 metric ton = 1.10231 short tons)
    cap_short_tons = (row[2] or 0) * 1_000_000 * 1.10231
    gem_state_cap[st] = {'plants': row[1], 'capacity_mt': row[2] or 0, 'capacity_short_tons': cap_short_tons}

# 4b: USGS demand by state (need to map USGS regions to states)
usgs_data = con.execute("SELECT state, shipments_short_tons FROM usgs_monthly_shipments").fetchall()

# Map USGS regions to state abbreviations
USGS_REGION_MAP = {
    'Texas, southern': 'TX',
    'Texas, northern': 'TX',
    'California, southern': 'CA',
    'California, northern': 'CA',
    'Florida': 'FL',
    'Arizona': 'AZ',
    'Nevada': 'NV',
    'North Carolina': 'NC',
    'Pennsylvania, eastern': 'PA',
    'New York, metropolitan': 'NY',
    'Georgia': 'GA',
    'Massachusetts': 'MA',
    'Virginia': 'VA',
    'South Carolina': 'SC',
    'New Jersey': 'NJ',
    'Kansas': 'KS',
    'Missouri': 'MO',
    'Louisiana': 'LA',
    'New Mexico': 'NM',
    'Illinois, excluding Chicago': 'IL',
    'Colorado': 'CO',
    'Michigan': 'MI',
    'Tennessee': 'TN',
    'Alabama': 'AL',
    'Maryland': 'MD',
    'Oklahoma': 'OK',
    'Washington': 'WA',
    'Oregon': 'OR',
    'Minnesota': 'MN',
    'Indiana': 'IN',
    'Ohio': 'OH',
    'Kentucky': 'KY',
    'Iowa': 'IA',
    'Wisconsin': 'WI',
    'Nebraska': 'NE',
    'Arkansas': 'AR',
    'Mississippi': 'MS',
}

usgs_by_state = defaultdict(float)
for region, tons in usgs_data:
    st = USGS_REGION_MAP.get(region)
    if st:
        usgs_by_state[st] += tons

# 4c: Import volume by port hinterland (map port -> state)
port_state_data = con.execute("""
    SELECT port_of_unlading, SUM(weight_tons) as vol
    FROM trade_imports
    WHERE port_of_unlading IS NOT NULL
    GROUP BY port_of_unlading
""").fetchall()

imports_by_state = defaultdict(float)
for port, vol in port_state_data:
    st = extract_state_from_port(port)
    if st:
        imports_by_state[st] += vol

# 4d: Consumer counts by state and segment
consumer_counts = con.execute("""
    SELECT fac_state, segment, COUNT(*) as cnt
    FROM epa_cement_consumers
    GROUP BY fac_state, segment
""").fetchall()

consumers_by_state = defaultdict(lambda: defaultdict(int))
for st, seg, cnt in consumer_counts:
    consumers_by_state[st][seg] = cnt

# Build consolidated state table
all_states = sorted(set(
    list(gem_state_cap.keys()) +
    list(usgs_by_state.keys()) +
    list(imports_by_state.keys()) +
    list(consumers_by_state.keys())
))

print(f"\n{'State':<6s} {'GEM Plants':>10s} {'Capacity(Mt)':>13s} {'Cap(ShortT)':>14s} {'USGS Demand':>14s} "
      f"{'Imports':>12s} {'ReadyMix':>9s} {'Block/Brk':>10s} {'ConcPipe':>9s} {'Other':>8s} {'Mfr':>5s} {'Supply Gap':>14s}")
print("-" * 140)

state_rows = []
for st in all_states:
    gem = gem_state_cap.get(st, {'plants': 0, 'capacity_mt': 0, 'capacity_short_tons': 0})
    demand = usgs_by_state.get(st, 0)
    imports = imports_by_state.get(st, 0)
    cdata = consumers_by_state.get(st, {})
    rmx = cdata.get('READY_MIX', 0)
    blk = cdata.get('CONCRETE_BLOCK_BRICK', 0)
    pipe = cdata.get('CONCRETE_PIPE', 0)
    other = cdata.get('OTHER_CONCRETE_PRODUCTS', 0)
    mfr = cdata.get('CEMENT_MANUFACTURER', 0)

    supply_gap = demand - gem['capacity_short_tons'] - imports if demand > 0 else None

    state_rows.append((st, gem['plants'], gem['capacity_mt'], gem['capacity_short_tons'],
                        demand, imports, rmx, blk, pipe, other, mfr, supply_gap))

    gap_str = f"{supply_gap:>14,.0f}" if supply_gap is not None else f"{'n/a':>14s}"
    demand_str = f"{demand:>14,.0f}" if demand > 0 else f"{'n/a':>14s}"

    print(f"{st:<6s} {gem['plants']:>10d} {gem['capacity_mt']:>13.2f} {gem['capacity_short_tons']:>14,.0f} "
          f"{demand_str} {imports:>12,.0f} {rmx:>9d} {blk:>10d} {pipe:>9d} {other:>8d} {mfr:>5d} {gap_str}")

# Summary
total_cap = sum(r[3] for r in state_rows)
total_demand = sum(r[4] for r in state_rows)
total_imports = sum(r[5] for r in state_rows)
total_gap = total_demand - total_cap - total_imports

print(f"\n{'TOTAL':<6s} {sum(r[1] for r in state_rows):>10d} "
      f"{sum(r[2] for r in state_rows):>13.2f} {total_cap:>14,.0f} "
      f"{total_demand:>14,.0f} {total_imports:>12,.0f} "
      f"{sum(r[6] for r in state_rows):>9d} {sum(r[7] for r in state_rows):>10d} "
      f"{sum(r[8] for r in state_rows):>9d} {sum(r[9] for r in state_rows):>8d} "
      f"{sum(r[10] for r in state_rows):>5d} {total_gap:>14,.0f}")

print(f"\nNational Supply-Demand Summary:")
print(f"  Total domestic GEM capacity:  {total_cap:>14,.0f} short tons/year")
print(f"  Total USGS demand (reported): {total_demand:>14,.0f} short tons/year")
print(f"  Total imports (trade data):   {total_imports:>14,.0f} short tons/year")
print(f"  Apparent supply gap:          {total_gap:>14,.0f} short tons/year")
print(f"  Import share of demand:       {total_imports/total_demand*100:>13.1f}%")

# Top 10 states by supply gap
print(f"\nTop 10 states by SUPPLY DEFICIT (demand exceeds domestic capacity + imports):")
deficit_states = [(r[0], r[11]) for r in state_rows if r[11] is not None and r[11] > 0]
deficit_states.sort(key=lambda x: -x[1])
for st, gap in deficit_states[:10]:
    gem = gem_state_cap.get(st, {'capacity_short_tons': 0})
    print(f"  {st}: gap = {gap:>12,.0f} tons  (capacity={gem['capacity_short_tons']:>12,.0f}, "
          f"demand={usgs_by_state.get(st, 0):>12,.0f}, imports={imports_by_state.get(st, 0):>10,.0f})")

print(f"\nTop 10 states by SUPPLY SURPLUS (domestic capacity exceeds demand):")
surplus_states = [(r[0], r[11]) for r in state_rows if r[11] is not None and r[11] < 0]
surplus_states.sort(key=lambda x: x[1])
for st, gap in surplus_states[:10]:
    gem = gem_state_cap.get(st, {'capacity_short_tons': 0})
    print(f"  {st}: surplus = {-gap:>12,.0f} tons  (capacity={gem['capacity_short_tons']:>12,.0f}, "
          f"demand={usgs_by_state.get(st, 0):>12,.0f}, imports={imports_by_state.get(st, 0):>10,.0f})")


# ======================================================================
# SECTION 5: TOP 20 IMPORT CONSIGNEES DEEP DIVE
# ======================================================================
print("\n" + "=" * 90)
print("SECTION 5: TOP 20 IMPORT CONSIGNEES - DEEP DIVE")
print("=" * 90)

# Get full details per consignee
top_consignees = con.execute("""
    SELECT consignee, SUM(weight_tons) as total_tons, COUNT(*) as shipments
    FROM trade_imports
    WHERE consignee IS NOT NULL
    GROUP BY consignee
    ORDER BY total_tons DESC
    LIMIT 20
""").fetchall()

# Rail-served facility lookup by company name
rail_by_company = defaultdict(list)
for row in con.execute("SELECT facility_name, company, city, state, facility_type, rail_carrier FROM us_cement_facilities WHERE is_rail_served = true").fetchall():
    rail_by_company[normalize(row[1])].append(row)
    rail_by_company[normalize(row[0])].append(row)

for consignee, total_tons, shipments in top_consignees:
    print(f"\n{'=' * 80}")
    print(f"  CONSIGNEE: {consignee}")
    print(f"  Total Import Volume: {total_tons:>12,d} tons  ({shipments} shipments)")
    print(f"{'=' * 80}")

    # Ports
    ports = con.execute("""
        SELECT port_of_unlading, SUM(weight_tons) as vol, COUNT(*) as ships
        FROM trade_imports
        WHERE consignee = ?
        GROUP BY port_of_unlading
        ORDER BY vol DESC
    """, [consignee]).fetchall()
    print(f"\n  Ports of Entry:")
    for port, vol, ships in ports:
        port_str = (port or 'Unknown')[:60]
        print(f"    {port_str:<62s} {vol:>10,d} tons  ({ships} ships)")

    # Origin countries
    origins = con.execute("""
        SELECT origin_country, SUM(weight_tons) as vol, COUNT(*) as ships
        FROM trade_imports
        WHERE consignee = ?
        GROUP BY origin_country
        ORDER BY vol DESC
    """, [consignee]).fetchall()
    print(f"\n  Origin Countries:")
    for country, vol, ships in origins:
        print(f"    {(country or 'Unknown'):<30s} {vol:>10,d} tons  ({ships} ships)")

    # EPA match
    norm_c = normalize(consignee)
    epa_matches_found = []

    # Check parent_company match
    for parent_norm, facs in epa_by_parent.items():
        score = fuzz.token_set_ratio(norm_c, parent_norm)
        if score >= 75 or (len(norm_c) >= 4 and (norm_c in parent_norm or parent_norm in norm_c)):
            for f in facs:
                epa_matches_found.append((f, max(score, 80)))

    # Also check direct facility name match
    result = process.extract(norm_c, unique_epa_names_list, scorer=fuzz.token_set_ratio, score_cutoff=75, limit=5)
    for matched_name, score, _ in (result or []):
        for f in epa_lookup.get(matched_name, []):
            epa_matches_found.append((f, score))

    # Deduplicate by registry_id equivalent (fac_name + state)
    seen = set()
    unique_epa = []
    for f, score in epa_matches_found:
        key = (f[0], f[2])
        if key not in seen:
            seen.add(key)
            unique_epa.append((f, score))

    if unique_epa:
        seg_summary = defaultdict(int)
        state_summary = defaultdict(int)
        for f, _ in unique_epa:
            seg_summary[f[3]] += 1
            state_summary[f[2]] += 1

        print(f"\n  EPA Facility Matches: {len(unique_epa)} facilities found")
        print(f"    Segments: ", end="")
        print(", ".join(f"{seg}({cnt})" for seg, cnt in sorted(seg_summary.items(), key=lambda x: -x[1])))
        print(f"    States:   ", end="")
        top_states = sorted(state_summary.items(), key=lambda x: -x[1])[:10]
        print(", ".join(f"{st}({cnt})" for st, cnt in top_states))
        if len(unique_epa) <= 10:
            for f, score in unique_epa:
                print(f"      - {f[0][:50]:<50s} {f[1]:<15s} {f[2]:<4s} {f[3]:<25s} (score={score:.0f})")
    else:
        print(f"\n  EPA Facility Matches: NONE FOUND")

    # Rail-served match
    rail_matches = []
    for rail_norm, rail_facs in rail_by_company.items():
        score = fuzz.token_set_ratio(norm_c, rail_norm)
        if score >= 75 or (len(norm_c) >= 4 and (norm_c in rail_norm or rail_norm in norm_c)):
            for rf in rail_facs:
                rail_matches.append((rf, score))

    # Deduplicate
    seen_rail = set()
    unique_rail = []
    for rf, score in rail_matches:
        key = (rf[0], rf[3])  # name + state
        if key not in seen_rail:
            seen_rail.add(key)
            unique_rail.append((rf, score))

    if unique_rail:
        print(f"\n  Rail-Served Sites: {len(unique_rail)} matches")
        for rf, score in unique_rail[:8]:
            print(f"    - {rf[0][:40]:<40s} {rf[2]:<15s} {rf[3]:<4s} type={rf[4]:<20s} carrier={rf[5]}")
        if len(unique_rail) > 8:
            print(f"    ... and {len(unique_rail) - 8} more")
    else:
        print(f"\n  Rail-Served Sites: NONE FOUND")


# ======================================================================
# FINAL SUMMARY
# ======================================================================
print("\n" + "=" * 90)
print("EXECUTIVE SUMMARY")
print("=" * 90)

print(f"""
DATASET CROSS-REFERENCE RESULTS:

1. IMPORT CONSIGNEES -> EPA FACILITIES
   - {len(matched_consignees)} of {len(consignee_matches)} consignees (by name) matched to EPA facility records
   - Matched consignees account for {matched_volume:,.0f} tons ({matched_volume/total_volume*100:.1f}%) of import volume
   - Major importers like Heidelberg, CEMEX, Holcim, Argos are well-represented in EPA
   - Many consignees operate across multiple segments (manufacturing, distribution, ready-mix)

2. RAIL-SERVED SITES -> EPA FACILITIES
   - {rail_matched} of {len(rail_sites)} rail-served sites ({rail_matched/len(rail_sites)*100:.1f}%) matched to EPA records
   - Most matched rail sites are in READY_MIX ({rail_seg_counts.get('READY_MIX', 0)}) and
     OTHER_CONCRETE_PRODUCTS ({rail_seg_counts.get('OTHER_CONCRETE_PRODUCTS', 0)}) segments
   - Rail serves the full supply chain: manufacturers, distributors, and end consumers

3. GEM PLANTS -> EPA CEMENT MANUFACTURERS
   - {gem_matched} of {len(gem_plants)} GEM plants ({gem_matched/len(gem_plants)*100:.1f}%) matched to EPA CEMENT_MANUFACTURER entries
   - {len(matched_operating)} of {len(operating)} operating GEM plants ({len(matched_operating)/len(operating)*100:.1f}%) found in EPA
   - EPA has {len(epa_mfrs)} CEMENT_MANUFACTURER entries (includes terminals and distributors too)

4. NATIONAL SUPPLY-DEMAND BALANCE
   - Domestic capacity (GEM):     {total_cap:>14,.0f} short tons/year
   - Reported demand (USGS):      {total_demand:>14,.0f} short tons/year
   - Import volume (trade data):  {total_imports:>14,.0f} short tons/year
   - Import share of demand:      {total_imports/total_demand*100:.1f}%
   - Note: USGS data covers only {len(usgs_by_state)} reporting states/regions

5. KEY FINDINGS
   - The US cement market is heavily consolidated: top 10 importers control
     {sum(c[1] for c in consignee_matches[:10]):,.0f} tons ({sum(c[1] for c in consignee_matches[:10])/total_volume*100:.1f}%) of imports
   - Major multinationals (Heidelberg, CEMEX, Holcim, Titan) are both domestic
     producers and importers, operating integrated supply chains
   - Texas, Florida, and California are the largest demand centers and import hubs
   - The USGS data is partial (annual estimate for select states) making exact
     gap calculation approximate
""")

con.close()
print("Analysis complete.")
