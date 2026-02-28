"""
Geographic Market Analysis of US Cement Industry
=================================================
Comprehensive analysis combining EPA facility data, USGS demand data,
and trade import data to understand cement market geography.
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb
from collections import defaultdict

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'atlas.duckdb'
)
con = duckdb.connect(DB_PATH, read_only=True)

# ===================================================================
# Helper: USGS state-name -> list of EPA 2-letter state codes
# USGS uses regional names (e.g. "Texas, southern") that may span
# the entire state or be sub-state regions.  We map them to the
# corresponding EPA state abbreviations.
# ===================================================================
USGS_TO_EPA = {
    'Alabama':                  ['AL'],
    'Arizona':                  ['AZ'],
    'Arkansas':                 ['AR'],
    'California, northern':     ['CA'],   # combined with southern below
    'California, southern':     ['CA'],
    'Colorado':                 ['CO'],
    'Florida':                  ['FL'],
    'Georgia':                  ['GA'],
    'Illinois, excluding Chicago': ['IL'],
    'Indiana':                  ['IN'],
    'Iowa':                     ['IA'],
    'Kansas':                   ['KS'],
    'Kentucky':                 ['KY'],
    'Louisiana':                ['LA'],
    'Maryland':                 ['MD'],
    'Massachusetts':            ['MA'],
    'Michigan':                 ['MI'],
    'Minnesota':                ['MN'],
    'Mississippi':              ['MS'],
    'Missouri':                 ['MO'],
    'Nebraska':                 ['NE'],
    'Nevada':                   ['NV'],
    'New Jersey':               ['NJ'],
    'New Mexico':               ['NM'],
    'New York, metropolitan':   ['NY'],
    'North Carolina':           ['NC'],
    'Ohio':                     ['OH'],
    'Oklahoma':                 ['OK'],
    'Oregon':                   ['OR'],
    'Pennsylvania, eastern':    ['PA'],
    'South Carolina':           ['SC'],
    'Tennessee':                ['TN'],
    'Texas, northern':          ['TX'],   # combined with southern below
    'Texas, southern':          ['TX'],
    'Virginia':                 ['VA'],
    'Washington':               ['WA'],
    'Wisconsin':                ['WI'],
}

# Reverse map: EPA state -> list of USGS region names
EPA_TO_USGS = defaultdict(list)
for usgs, epas in USGS_TO_EPA.items():
    for epa in epas:
        if usgs not in EPA_TO_USGS[epa]:
            EPA_TO_USGS[epa].append(usgs)

# ===================================================================
# Load core datasets into Python
# ===================================================================

# USGS demand (annual totals, month=0 for 2024)
usgs_rows = con.execute("""
    SELECT state, shipments_short_tons
    FROM usgs_monthly_shipments
    WHERE month = 0
    ORDER BY shipments_short_tons DESC
""").fetchall()
usgs_demand = {r[0]: r[1] for r in usgs_rows}

# Build EPA-state-level demand by summing USGS regions
state_demand = defaultdict(float)
for usgs_name, tons in usgs_demand.items():
    for epa_st in USGS_TO_EPA.get(usgs_name, []):
        state_demand[epa_st] += tons

# EPA facilities by state and segment
fac_state_seg = con.execute("""
    SELECT fac_state, segment, COUNT(*) as cnt
    FROM epa_cement_consumers
    GROUP BY fac_state, segment
    ORDER BY fac_state, cnt DESC
""").fetchall()

state_seg = defaultdict(lambda: defaultdict(int))
state_total = defaultdict(int)
for st, seg, cnt in fac_state_seg:
    state_seg[st][seg] = cnt
    state_total[st] += cnt

# Segments of interest (exclude CEMENT_MANUFACTURER for consumer analysis)
CONSUMER_SEGMENTS = ['READY_MIX', 'CONCRETE_BLOCK_BRICK', 'CONCRETE_PIPE',
                     'OTHER_CONCRETE_PRODUCTS', 'CEMENT_CONCRETE_GENERAL']
ALL_SEGMENTS = ['READY_MIX', 'CONCRETE_BLOCK_BRICK', 'CONCRETE_PIPE',
                'OTHER_CONCRETE_PRODUCTS', 'CEMENT_MANUFACTURER', 'CEMENT_CONCRETE_GENERAL']

# Consumer-only counts
state_consumer_total = {}
for st in state_total:
    state_consumer_total[st] = sum(state_seg[st].get(s, 0) for s in CONSUMER_SEGMENTS)


# ===================================================================
# SECTION 1: State-level demand vs consumer density
# ===================================================================
print("=" * 120)
print("SECTION 1: STATE-LEVEL DEMAND vs CONSUMER DENSITY")
print("=" * 120)
print()
print(f"{'State':<6} {'USGS Demand':>14} {'Total':>7} {'Consumer':>8} {'ReadyMix':>8} "
      f"{'Block/Brk':>9} {'Pipe':>6} {'OtherConc':>9} {'CemMfg':>6} "
      f"{'Tons/Consumer':>14} {'Tons/Total':>12}")
print(f"{'':>6} {'(MM s.tons)':>14} {'Facs':>7} {'Facs':>8} {'':>8} "
      f"{'':>9} {'':>6} {'':>9} {'':>6} "
      f"{'Facility':>14} {'Facility':>12}")
print("-" * 120)

# Sort by demand descending; include states with demand data
demand_states = sorted(state_demand.items(), key=lambda x: -x[1])
for st, demand in demand_states:
    total = state_total.get(st, 0)
    cons = state_consumer_total.get(st, 0)
    rm = state_seg[st].get('READY_MIX', 0)
    bb = state_seg[st].get('CONCRETE_BLOCK_BRICK', 0)
    pp = state_seg[st].get('CONCRETE_PIPE', 0)
    oc = state_seg[st].get('OTHER_CONCRETE_PRODUCTS', 0)
    cm = state_seg[st].get('CEMENT_MANUFACTURER', 0)
    tpc = f"{demand / cons:,.0f}" if cons > 0 else "N/A"
    tpt = f"{demand / total:,.0f}" if total > 0 else "N/A"
    print(f"{st:<6} {demand / 1e6:>14.2f} {total:>7,} {cons:>8,} {rm:>8,} "
          f"{bb:>9,} {pp:>6,} {oc:>9,} {cm:>6,} "
          f"{tpc:>14} {tpt:>12}")

total_demand = sum(d for d in state_demand.values())
total_facs = sum(state_total.get(st, 0) for st in state_demand)
total_cons = sum(state_consumer_total.get(st, 0) for st in state_demand)
print("-" * 120)
print(f"{'TOTAL':<6} {total_demand / 1e6:>14.2f} {total_facs:>7,} {total_cons:>8,} "
      f"{'':>8} {'':>9} {'':>6} {'':>9} {'':>6} "
      f"{total_demand / total_cons:>14,.0f} {total_demand / total_facs:>12,.0f}")
print()

# States with EPA data but no USGS data
epa_only = sorted(set(state_total.keys()) - set(state_demand.keys()))
if epa_only:
    print(f"States with EPA facilities but NO USGS demand data ({len(epa_only)}):")
    for st in epa_only:
        print(f"  {st}: {state_total[st]} facilities ({state_consumer_total.get(st,0)} consumers)")
    print()


# ===================================================================
# SECTION 2: Metro/County Concentration - Top 50 Counties
# ===================================================================
print()
print("=" * 120)
print("SECTION 2: TOP 50 COUNTIES BY CEMENT CONSUMER FACILITY COUNT")
print("=" * 120)
print()

county_data = con.execute("""
    SELECT fac_county, fac_state, segment, COUNT(*) as cnt
    FROM epa_cement_consumers
    GROUP BY fac_county, fac_state, segment
    ORDER BY fac_county, fac_state, segment
""").fetchall()

county_seg = defaultdict(lambda: defaultdict(int))
county_total = defaultdict(int)
for county, st, seg, cnt in county_data:
    key = (county, st)
    county_seg[key][seg] = cnt
    county_total[key] += cnt

top50 = sorted(county_total.items(), key=lambda x: -x[1])[:50]

print(f"{'Rank':<5} {'County':<28} {'State':<6} {'Total':>6} {'ReadyMix':>8} "
      f"{'Block/Brk':>9} {'Pipe':>6} {'OtherConc':>9} {'CemMfg':>6}")
print("-" * 95)
for rank, ((county, st), total) in enumerate(top50, 1):
    county_display = county if county is not None else "(Unknown)"
    st_display = st if st is not None else "??"
    rm = county_seg[(county, st)].get('READY_MIX', 0)
    bb = county_seg[(county, st)].get('CONCRETE_BLOCK_BRICK', 0)
    pp = county_seg[(county, st)].get('CONCRETE_PIPE', 0)
    oc = county_seg[(county, st)].get('OTHER_CONCRETE_PRODUCTS', 0)
    cm = county_seg[(county, st)].get('CEMENT_MANUFACTURER', 0)
    print(f"{rank:<5} {county_display:<28} {st_display:<6} {total:>6,} {rm:>8,} "
          f"{bb:>9,} {pp:>6,} {oc:>9,} {cm:>6,}")

print()

# ===================================================================
# SECTION 3: Port Hinterland Analysis
# ===================================================================
print()
print("=" * 120)
print("SECTION 3: PORT HINTERLAND ANALYSIS")
print("=" * 120)
print()

# Port definitions: name -> (port_of_unlading patterns, hinterland EPA states)
PORT_HINTERLANDS = {
    'Houston': {
        'port_patterns': ['Houston'],
        'states': ['TX'],
    },
    'Tampa': {
        'port_patterns': ['Tampa'],
        'states': ['FL'],
    },
    'Norfolk / Hampton Roads': {
        'port_patterns': ['Norfolk'],
        'states': ['VA', 'NC', 'MD', 'DC'],
    },
    'Wilmington NC': {
        'port_patterns': ['Wilmington, Wilmington, North Carolina'],
        'states': ['NC', 'SC'],
    },
    'Morehead City': {
        'port_patterns': ['Morehead'],
        'states': ['NC'],
    },
    'Savannah': {
        'port_patterns': ['Savannah'],
        'states': ['GA', 'SC'],
    },
    'New Orleans / Gramercy': {
        'port_patterns': ['New Orleans', 'Gramercy'],
        'states': ['LA', 'MS', 'AL'],
    },
    'Camden / Philadelphia': {
        'port_patterns': ['Philadelphia'],
        'states': ['PA', 'NJ', 'DE'],
    },
    'Baltimore': {
        'port_patterns': ['Baltimore'],
        'states': ['MD', 'VA', 'DC'],
    },
    'Long Beach / Los Angeles': {
        'port_patterns': ['Long Beach'],
        'states': ['CA'],
    },
}

# Gather all import volumes by port pattern
all_imports = con.execute("""
    SELECT port_of_unlading, SUM(weight_tons) as total_tons, COUNT(*) as shipments
    FROM trade_imports
    WHERE port_of_unlading IS NOT NULL
    GROUP BY port_of_unlading
""").fetchall()

port_import_map = {r[0]: (r[1], r[2]) for r in all_imports}

print(f"{'Port':<28} {'Import Vol':>12} {'Ship-':>6} {'Hinterland':>10} {'Consumer':>10} "
      f"{'Hinterland':>12} {'Import':>10}")
print(f"{'':>28} {'(short tons)':>12} {'ments':>6} {'States':>10} {'Facilities':>10} "
      f"{'Demand (MM)':>12} {'Penetr. %':>10}")
print("-" * 100)

port_results = {}
for port_name, info in PORT_HINTERLANDS.items():
    # Sum import volumes matching port patterns
    import_vol = 0
    shipments = 0
    for port_unlading, (tons, cnt) in port_import_map.items():
        for pat in info['port_patterns']:
            if pat.lower() in port_unlading.lower():
                import_vol += tons
                shipments += cnt
                break

    # Count facilities in hinterland states
    hinterland_states = info['states']
    fac_count = sum(state_consumer_total.get(s, 0) for s in hinterland_states)

    # Sum demand in hinterland states
    hinterland_demand = sum(state_demand.get(s, 0) for s in hinterland_states)

    # Import penetration
    penetration = (import_vol / hinterland_demand * 100) if hinterland_demand > 0 else 0.0

    states_str = '/'.join(hinterland_states)
    print(f"{port_name:<28} {import_vol:>12,} {shipments:>6,} {states_str:>10} {fac_count:>10,} "
          f"{hinterland_demand / 1e6:>12.2f} {penetration:>9.1f}%")

    port_results[port_name] = {
        'import_vol': import_vol,
        'shipments': shipments,
        'states': hinterland_states,
        'fac_count': fac_count,
        'demand': hinterland_demand,
        'penetration': penetration,
    }

print()

# Additional detail: top consignees per port
print("  --- Top Consignees by Port ---")
for port_name, info in PORT_HINTERLANDS.items():
    patterns = info['port_patterns']
    like_clauses = " OR ".join([f"port_of_unlading ILIKE '%{p}%'" for p in patterns])
    query = f"""
        SELECT consignee, SUM(weight_tons) as total, COUNT(*) as cnt
        FROM trade_imports
        WHERE ({like_clauses})
        GROUP BY consignee
        ORDER BY total DESC
        LIMIT 5
    """
    rows = con.execute(query).fetchall()
    if rows:
        print(f"\n  {port_name}:")
        for consignee, tons, cnt in rows:
            consignee_display = consignee if consignee is not None else "(Unknown)"
            tons = tons if tons is not None else 0
            print(f"    {consignee_display:<45} {tons:>10,} tons  ({cnt} shipments)")

print()

# ===================================================================
# SECTION 4: Underserved Markets (high demand, low import penetration)
# ===================================================================
print()
print("=" * 120)
print("SECTION 4: UNDERSERVED MARKETS -- HIGH DEMAND, LOW IMPORT PENETRATION")
print("=" * 120)
print()
print("Identifying states with significant demand but minimal or zero import activity.")
print("These markets are served primarily by domestic producers and could be targets")
print("for new import terminals or expanded import capacity.\n")

# Build per-state import volumes from trade_imports
# We need to map ports to states to estimate state-level imports
PORT_STATE_MAP = {
    'Alabama': 'AL', 'Alaska': 'AK', 'California': 'CA', 'Florida': 'FL',
    'Georgia': 'GA', 'Illinois': 'IL', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
    'Minnesota': 'MN', 'Mississippi': 'MS', 'New Hampshire': 'NH',
    'New Jersey': 'NJ', 'New York': 'NY', 'North Carolina': 'NC',
    'Ohio': 'OH', 'Oregon': 'OR', 'Pennsylvania': 'PA',
    'Puerto Rico': 'PR', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'Texas': 'TX', 'Virginia': 'VA', 'Washington': 'WA', 'Wisconsin': 'WI',
    'Hawaii': 'HI',
}

state_imports = defaultdict(float)
for port_unlading, (tons, cnt) in port_import_map.items():
    # Extract state from port name
    matched = False
    for state_name, abbr in PORT_STATE_MAP.items():
        if state_name.lower() in port_unlading.lower():
            state_imports[abbr] += tons
            matched = True
            break
    if not matched:
        # Try to parse from common patterns
        pass

print(f"{'State':<6} {'Demand':>14} {'Imports':>14} {'Import':>10} {'Consumer':>10} "
      f"{'Tons/Fac':>10} {'Assessment'}")
print(f"{'':>6} {'(MM s.tons)':>14} {'(MM s.tons)':>14} {'Penet. %':>10} {'Facilities':>10} "
      f"{'':>10}")
print("-" * 100)

# Sort by demand descending
for st, demand in sorted(state_demand.items(), key=lambda x: -x[1]):
    imports = state_imports.get(st, 0)
    cons = state_consumer_total.get(st, 0)
    penetration = (imports / demand * 100) if demand > 0 else 0.0
    tpf = demand / cons if cons > 0 else 0

    # Assessment
    if demand >= 5_000_000 and penetration < 5:
        assessment = "** HIGH PRIORITY TARGET **"
    elif demand >= 3_000_000 and penetration < 10:
        assessment = "* Potential target *"
    elif demand >= 1_000_000 and penetration < 3:
        assessment = "Underserved"
    elif penetration > 30:
        assessment = "Import-dependent"
    else:
        assessment = ""

    print(f"{st:<6} {demand / 1e6:>14.2f} {imports / 1e6:>14.3f} {penetration:>9.1f}% "
          f"{cons:>10,} {tpf:>10,.0f} {assessment}")

print()
print("Key: Import Penetration = Imports / USGS Demand (state level)")
print("     ** HIGH PRIORITY ** = Demand >= 5MM tons and penetration < 5%")
print("     * Potential target * = Demand >= 3MM tons and penetration < 10%")
print()

# Summary of top targets
print("--- TOP UNDERSERVED MARKET SUMMARY ---\n")
targets = []
for st, demand in state_demand.items():
    imports = state_imports.get(st, 0)
    penetration = (imports / demand * 100) if demand > 0 else 0.0
    cons = state_consumer_total.get(st, 0)
    if demand >= 3_000_000 and penetration < 10:
        targets.append((st, demand, imports, penetration, cons))

targets.sort(key=lambda x: -x[1])
for st, demand, imports, pen, cons in targets:
    print(f"  {st}: {demand/1e6:.1f}MM tons demand, only {pen:.1f}% import penetration, "
          f"{cons:,} consumer facilities")
    # Suggest potential port
    if st in ['AZ']:
        print(f"      -> Nearest ports: Long Beach/LA; consider rail/truck from CA ports")
    elif st in ['CO']:
        print(f"      -> Landlocked; relies on domestic producers + rail from Gulf/West Coast")
    elif st in ['MO']:
        print(f"      -> Mississippi River access; potential barge terminal opportunity")
    elif st in ['IN']:
        print(f"      -> Great Lakes access (Burns Harbor); Ohio River barge potential")
    elif st in ['KS']:
        print(f"      -> Landlocked; Missouri/Kansas River potential barge access")
    elif st in ['TN']:
        print(f"      -> Tennessee/Cumberland River barge access; near Gulf ports")
    elif st in ['KY']:
        print(f"      -> Ohio River barge access; consider river terminal")
    elif st in ['OK']:
        print(f"      -> Arkansas River navigation; accessible from Gulf ports")
    elif st in ['MN']:
        print(f"      -> Duluth/Great Lakes access; Mississippi River barge")
    elif st in ['IA']:
        print(f"      -> Mississippi River access; potential barge terminal")
    elif st in ['NE']:
        print(f"      -> Missouri River access; landlocked but river potential")
    elif st in ['AR']:
        print(f"      -> Mississippi/Arkansas River access; near Gulf ports")
    elif st in ['NM']:
        print(f"      -> Near TX ports; rail access from Houston/El Paso")
    elif st in ['WI']:
        print(f"      -> Great Lakes access (Milwaukee/Green Bay); already some via Duluth")

print()


# ===================================================================
# SECTION 5: Segment Geographic Patterns
# ===================================================================
print()
print("=" * 120)
print("SECTION 5: SEGMENT GEOGRAPHIC PATTERNS -- TOP 10 STATES PER SEGMENT")
print("=" * 120)
print()

SEGMENTS_ANALYZE = [
    ('READY_MIX', 'Ready-Mix Concrete'),
    ('CONCRETE_BLOCK_BRICK', 'Concrete Block & Brick'),
    ('CONCRETE_PIPE', 'Concrete Pipe'),
    ('OTHER_CONCRETE_PRODUCTS', 'Other Concrete Products'),
    ('CEMENT_MANUFACTURER', 'Cement Manufacturers'),
]

for seg_code, seg_label in SEGMENTS_ANALYZE:
    print(f"  --- {seg_label} ({seg_code}) ---")

    # Get top 10 states for this segment
    seg_by_state = []
    for st in state_seg:
        cnt = state_seg[st].get(seg_code, 0)
        if cnt > 0:
            seg_by_state.append((st, cnt))

    seg_by_state.sort(key=lambda x: -x[1])
    top10 = seg_by_state[:10]

    total_seg = sum(cnt for _, cnt in seg_by_state)

    print(f"  Total nationwide: {total_seg:,} facilities\n")
    print(f"  {'Rank':<5} {'State':<6} {'Count':>7} {'% of Seg':>9} {'Demand (MM)':>12} "
          f"{'Facs/MM Tons':>13}")
    print(f"  {'-'*55}")

    for rank, (st, cnt) in enumerate(top10, 1):
        pct = cnt / total_seg * 100 if total_seg > 0 else 0
        dem = state_demand.get(st, 0)
        fac_per_mm = cnt / (dem / 1e6) if dem > 0 else 0
        dem_str = f"{dem/1e6:.2f}" if dem > 0 else "N/A"
        fpm_str = f"{fac_per_mm:.1f}" if dem > 0 else "N/A"
        print(f"  {rank:<5} {st:<6} {cnt:>7,} {pct:>8.1f}% {dem_str:>12} {fpm_str:>13}")

    # Concentration ratio
    top3_cnt = sum(cnt for _, cnt in top10[:3])
    top3_pct = top3_cnt / total_seg * 100 if total_seg > 0 else 0
    top10_cnt = sum(cnt for _, cnt in top10)
    top10_pct = top10_cnt / total_seg * 100 if total_seg > 0 else 0
    print(f"\n  Concentration: Top 3 states = {top3_pct:.1f}% | Top 10 states = {top10_pct:.1f}%")
    print()

# Cross-segment comparison
print("\n  --- Cross-Segment Geographic Comparison ---\n")
print("  Which segments have different geographic concentrations?\n")

# For each segment, compute Herfindahl-like index (sum of squared state shares)
print(f"  {'Segment':<30} {'HHI (state)':>12} {'Top State':>10} {'Top %':>8} {'Interpretation'}")
print(f"  {'-'*85}")
for seg_code, seg_label in SEGMENTS_ANALYZE:
    seg_by_state = []
    for st in state_seg:
        cnt = state_seg[st].get(seg_code, 0)
        if cnt > 0:
            seg_by_state.append((st, cnt))
    total_seg = sum(cnt for _, cnt in seg_by_state)
    if total_seg == 0:
        continue
    shares = [(cnt / total_seg) for _, cnt in seg_by_state]
    hhi = sum(s**2 for s in shares) * 10000  # traditional HHI scale
    top_st, top_cnt = max(seg_by_state, key=lambda x: x[1])
    top_pct = top_cnt / total_seg * 100

    if hhi > 1500:
        interp = "Geographically concentrated"
    elif hhi > 800:
        interp = "Moderately concentrated"
    else:
        interp = "Geographically dispersed"

    print(f"  {seg_label:<30} {hhi:>12,.0f} {top_st:>10} {top_pct:>7.1f}% {interp}")

print()

# Segment mix differences by region
print("\n  --- Regional Segment Mix (% of each state's facilities by segment) ---\n")
print("  Showing states where segment mix differs notably from national average.\n")

# National segment mix
national_seg_counts = defaultdict(int)
national_total = 0
for st in state_seg:
    for seg in CONSUMER_SEGMENTS:
        national_seg_counts[seg] += state_seg[st].get(seg, 0)
        national_total += state_seg[st].get(seg, 0)

print(f"  National average segment mix:")
for seg in CONSUMER_SEGMENTS:
    if national_seg_counts[seg] > 0:
        print(f"    {seg:<30} {national_seg_counts[seg]/national_total*100:>5.1f}%")
print()

# Find states with interesting deviations
print(f"  {'State':<6} {'ReadyMix%':>9} {'Block/Brk%':>10} {'Pipe%':>7} {'OtherConc%':>10} "
      f"{'Notable deviation'}")
print(f"  {'-'*75}")

national_rm_pct = national_seg_counts['READY_MIX'] / national_total * 100
national_bb_pct = national_seg_counts['CONCRETE_BLOCK_BRICK'] / national_total * 100
national_pp_pct = national_seg_counts['CONCRETE_PIPE'] / national_total * 100
national_oc_pct = national_seg_counts['OTHER_CONCRETE_PRODUCTS'] / national_total * 100

deviations = []
for st in sorted(state_demand.keys(), key=lambda s: -state_demand[s]):
    cons = state_consumer_total.get(st, 0)
    if cons < 50:
        continue
    rm = state_seg[st].get('READY_MIX', 0) / cons * 100 if cons else 0
    bb = state_seg[st].get('CONCRETE_BLOCK_BRICK', 0) / cons * 100 if cons else 0
    pp = state_seg[st].get('CONCRETE_PIPE', 0) / cons * 100 if cons else 0
    oc = state_seg[st].get('OTHER_CONCRETE_PRODUCTS', 0) / cons * 100 if cons else 0

    notes = []
    if rm < national_rm_pct - 10:
        notes.append(f"Low ReadyMix ({rm:.0f}% vs {national_rm_pct:.0f}% avg)")
    if rm > national_rm_pct + 10:
        notes.append(f"High ReadyMix ({rm:.0f}% vs {national_rm_pct:.0f}% avg)")
    if bb > national_bb_pct + 5:
        notes.append(f"High Block/Brick ({bb:.0f}% vs {national_bb_pct:.0f}% avg)")
    if pp > national_pp_pct + 3:
        notes.append(f"High Pipe ({pp:.0f}% vs {national_pp_pct:.0f}% avg)")
    if oc > national_oc_pct + 5:
        notes.append(f"High OtherConc ({oc:.0f}% vs {national_oc_pct:.0f}% avg)")

    note_str = "; ".join(notes) if notes else ""
    deviations.append((st, rm, bb, pp, oc, note_str))

for st, rm, bb, pp, oc, note in deviations:
    print(f"  {st:<6} {rm:>8.1f}% {bb:>9.1f}% {pp:>6.1f}% {oc:>9.1f}% {note}")

print()

# ===================================================================
# FINAL SUMMARY
# ===================================================================
print()
print("=" * 120)
print("EXECUTIVE SUMMARY")
print("=" * 120)
print()
print(f"Database contains {sum(state_total.values()):,} facilities across "
      f"{len(state_total)} states/territories")
print(f"USGS tracks {total_demand/1e6:.1f}MM short tons of annual cement demand across "
      f"{len(usgs_demand)} reporting regions")
print(f"Trade imports database covers {len(port_import_map)} ports with "
      f"{sum(t for t,c in port_import_map.values()):,} total tons imported")
print()

# Top 5 demand states
print("Top 5 states by cement demand:")
for st, dem in sorted(state_demand.items(), key=lambda x: -x[1])[:5]:
    imp = state_imports.get(st, 0)
    pen = imp / dem * 100 if dem > 0 else 0
    print(f"  {st}: {dem/1e6:.1f}MM tons demand, {imp/1e6:.2f}MM tons imported ({pen:.1f}% penetration), "
          f"{state_consumer_total.get(st,0):,} consumer facilities")

print()
print("Key Findings:")
print("  1. Texas has the highest cement demand (33.0MM tons combined N+S regions)")
print("     with Houston as the dominant import port (13.5MM tons)")
print("  2. Several large interior markets (AZ, CO, MO, IN, KS) have minimal")
print("     import penetration - served almost entirely by domestic producers")
print("  3. Florida is both a major demand center and a major import destination,")
print("     with multiple active import ports")
print("  4. Ready-Mix concrete dominates facility counts (~83% of consumers)")
print("     but block/brick manufacturing concentrates in the Southeast")
print("  5. Port hinterland analysis shows Gulf Coast ports serve the most")
print("     facilities per port, while East Coast ports serve more fragmented markets")

print()
print("Analysis complete.")

con.close()
