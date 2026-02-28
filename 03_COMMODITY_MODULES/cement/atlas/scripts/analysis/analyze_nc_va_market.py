#!/usr/bin/env python3
"""Analyze NC/VA cement consumer market for port selection."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb

frs = duckdb.connect('G:/My Drive/LLM/task_epa_frs/data/frs.duckdb', read_only=True)
atlas = duckdb.connect('../data/atlas.duckdb', read_only=True)

print("=" * 80)
print("NC/VA CEMENT CONSUMER MARKET ANALYSIS")
print("=" * 80)

# Ready-mix by city in NC/VA/SC
print("\n=== READY-MIX CONCRETE FACILITIES (NAICS 327320) ===")
for state in ['NC', 'VA', 'SC']:
    cnt = frs.execute(f'''
        SELECT COUNT(DISTINCT registry_id)
        FROM naics_codes
        WHERE naics_code = '327320'
          AND registry_id IN (SELECT registry_id FROM facilities WHERE fac_state = '{state}')
    ''').fetchone()[0]
    print(f"  {state}: {cnt:,} ready-mix plants")

print("\n=== CONCRETE PRODUCTS BY STATE (Block, Pipe, Other) ===")
for state in ['NC', 'VA', 'SC', 'GA', 'TN', 'MD', 'PA']:
    cnt = frs.execute(f'''
        SELECT COUNT(DISTINCT n.registry_id)
        FROM naics_codes n
        JOIN facilities f ON n.registry_id = f.registry_id
        WHERE n.naics_code IN ('327331', '327332', '327390')
          AND f.fac_state = '{state}'
    ''').fetchone()[0]
    print(f"  {state}: {cnt:,} concrete product facilities")

print("\n=== MAJOR CEMENT CONSUMERS IN NC (ATLAS Facilities) ===")
df = atlas.execute('''
    SELECT facility_name, facility_type, city, state, is_rail_served
    FROM us_cement_facilities
    WHERE state = 'NC'
      AND facility_type NOT IN ('CEMENT_PLANT', 'AGGREGATE')
    ORDER BY facility_type, facility_name
    LIMIT 30
''').fetchdf()
print(df.to_string())

print("\n=== MAJOR CEMENT CONSUMERS IN VA (ATLAS Facilities) ===")
df = atlas.execute('''
    SELECT facility_name, facility_type, city, state, is_rail_served
    FROM us_cement_facilities
    WHERE state = 'VA'
      AND facility_type NOT IN ('CEMENT_PLANT', 'AGGREGATE')
    ORDER BY facility_type, facility_name
    LIMIT 25
''').fetchdf()
print(df.to_string())

print("\n=== USGS CEMENT DEMAND - SE Region ===")
df = atlas.execute('''
    SELECT state, ROUND(SUM(shipments_short_tons)/1000000, 2) as million_tons
    FROM usgs_monthly_shipments
    WHERE state IN ('North Carolina', 'Virginia', 'South Carolina', 'Georgia',
                    'Florida', 'Pennsylvania, eastern', 'New York, metropolitan', 'New Jersey')
    GROUP BY state
    ORDER BY million_tons DESC
''').fetchdf()
print(df.to_string())

print("\n" + "=" * 80)
print("RAIL CONNECTIVITY ANALYSIS")
print("=" * 80)

print("""
WILMINGTON NC:
  - Port: NC State Ports Authority
  - Rail: CSX (direct service)
  - Access: I-40, I-95 nearby
  - Markets via Rail:
    * Raleigh-Durham: ~120 miles (CSX direct)
    * Charlotte: ~200 miles (CSX via Hamlet)
    * Richmond: ~220 miles (CSX interchange)
    * Columbia SC: ~200 miles (CSX)
  - Vessel Capacity: Up to 40,000 DWT

MOREHEAD CITY NC:
  - Port: NC State Ports Authority (smaller)
  - Rail: Norfolk Southern (via Morehead City branch)
  - Access: US-70, connects to I-95
  - Markets via Rail:
    * Raleigh: ~140 miles (NS)
    * Charlotte: ~280 miles (NS, less direct)
    * Norfolk: NS connection
  - Vessel Capacity: Up to 35,000 DWT
  - Note: More circuitous rail for Charlotte market

NORFOLK VA:
  - Port: Virginia Port Authority (major deep water)
  - Rail: CSX AND Norfolk Southern (dual service)
  - Access: I-64, I-95, I-85
  - Markets via Rail:
    * Richmond: ~90 miles
    * Raleigh: ~170 miles (NS)
    * Charlotte: ~280 miles (NS)
    * DC/Baltimore: ~180 miles (CSX/NS)
    * Chicago: Major rail corridor (NS)
  - Vessel Capacity: Up to 65,000 DWT (deepest on East Coast)
  - Key Advantage: Intermodal hub, dual Class I service

SAVANNAH GA:
  - Port: Georgia Ports Authority (major gateway)
  - Rail: CSX AND Norfolk Southern
  - Markets via Rail:
    * Atlanta: ~250 miles
    * Charlotte: ~260 miles
    * Charleston: ~110 miles
    * Jacksonville: ~140 miles
  - Vessel Capacity: Deep water, post-Panamax
  - Key Advantage: SE distribution hub
""")

print("=" * 80)
print("STRATEGIC ASSESSMENT: NC PORT OPTIONS")
print("=" * 80)

print("""
WILMINGTON NC - PROS:
  + Direct CSX service to Charlotte and Piedmont NC
  + Growing market (NC is #8 in ready-mix facilities)
  + Less competition than Savannah or Norfolk
  + State port (potentially favorable terms)
  + Good vessel access (40,000 DWT)

WILMINGTON NC - CONS:
  - Single Class I carrier (CSX only)
  - Limited hinterland compared to Norfolk or Savannah
  - Charlotte also reachable from Norfolk or Savannah
  - Not on major intermodal corridor

MOREHEAD CITY NC - PROS:
  + Norfolk Southern service (alternative to CSX)
  + State port
  + Less congestion than major ports

MOREHEAD CITY NC - CONS:
  - Smaller vessel capacity
  - More circuitous rail to Charlotte
  - Very limited import history (only 9 shipments)
  - Less developed bulk terminal infrastructure

RECOMMENDATION:
  If targeting NC/Piedmont market specifically, Wilmington is better choice
  than Morehead City due to:
  1. Larger vessel capacity
  2. More direct rail to Charlotte via CSX
  3. Existing cement import activity (0.65 MM MT proves viability)

  However, for broader market reach, Norfolk offers:
  1. Deeper water for larger vessels (cost/ton advantage)
  2. Dual Class I service (CSX + NS routing flexibility)
  3. Access to both Mid-Atlantic AND Carolinas
  4. Major intermodal hub status

  Wilmington makes sense as a NICHE play for NC market specifically,
  avoiding direct competition with Norfolk (Mid-Atlantic focus) and
  Savannah (SE focus).
""")

frs.close()
atlas.close()
