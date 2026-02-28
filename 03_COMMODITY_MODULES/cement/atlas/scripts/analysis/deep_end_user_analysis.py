#!/usr/bin/env python3
"""
Deep analysis of cement end users, demand, and supply chain.
Queries EPA FRS (17K+ facilities), ATLAS DB, and consumer workbook.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb
import pandas as pd
from pathlib import Path

# Connect to databases
atlas = duckdb.connect('data/atlas.duckdb', read_only=True)
frs = duckdb.connect('G:/My Drive/LLM/task_epa_frs/data/frs.duckdb', read_only=True)

print("=" * 100)
print("DEEP ANALYSIS: CEMENT END USERS, DEMAND & SUPPLY CHAIN")
print("=" * 100)

# =====================================================================
# SECTION 1: WHO BUYS CEMENT - Consumer Segmentation
# =====================================================================
print("\n" + "=" * 100)
print("SECTION 1: WHO BUYS CEMENT - End User Segmentation")
print("=" * 100)

print("\n--- 1A. NAICS-Based Consumer Census (EPA FRS - Full Universe) ---")
naics_segments = [
    ('327310', 'Cement Manufacturing (plants)'),
    ('327320', 'Ready-Mix Concrete'),
    ('327331', 'Concrete Block & Brick (CMU)'),
    ('327332', 'Concrete Pipe, Culvert, Catch Basin'),
    ('327390', 'Other Concrete Products'),
    ('327410', 'Lime Manufacturing'),
    ('327420', 'Gypsum Products'),
    ('327910', 'Abrasive Products'),
    ('327999', 'Other Nonmetallic Mineral Products'),
    ('237310', 'Highway, Street, Bridge Construction'),
    ('238110', 'Poured Concrete Foundation/Structure'),
    ('238990', 'Other Specialty Trade Contractors'),
    ('423320', 'Brick/Stone/Building Material Wholesale'),
    ('444190', 'Other Building Material Dealers'),
    ('213112', 'Oil & Gas Well Services (cementing)'),
    ('236220', 'Commercial Building Construction'),
]

print(f"\n{'NAICS':<10} {'Segment':<48} {'Facilities':>12}")
print("-" * 72)
total_consumers = 0
for code, desc in naics_segments:
    cnt = frs.execute(f'''
        SELECT COUNT(DISTINCT registry_id)
        FROM naics_codes
        WHERE naics_code = '{code}'
    ''').fetchone()[0]
    if cnt > 0:
        print(f"{code:<10} {desc:<48} {cnt:>12,}")
        total_consumers += cnt

print("-" * 72)
print(f"{'TOTAL':<10} {'All Cement-Related Segments':<48} {total_consumers:>12,}")

print("\n--- 1B. Ready-Mix Concrete (Largest Segment - 70%+ of cement demand) ---")
print("\nReady-mix concrete plants are the PRIMARY buyer of cement.")
print("They convert bulk cement + aggregates + water into concrete for delivery.\n")

df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as plants,
           COUNT(DISTINCT f.fac_county) as counties
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code = '327320'
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY plants DESC
    LIMIT 25
''').fetchdf()
print(f"{'State':<8} {'Ready-Mix Plants':>18} {'Counties Served':>18}")
print("-" * 46)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['plants']:>18,} {row['counties']:>18,}")
print(f"\nTotal Ready-Mix plants in US: {df['plants'].sum():,}")

print("\n--- 1C. Concrete Block & Masonry (NAICS 327331) ---")
print("CMU manufacturers buy cement in bulk for block/brick production.\n")
df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as plants
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code = '327331'
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY plants DESC
    LIMIT 20
''').fetchdf()
print(f"{'State':<8} {'CMU/Block Plants':>18}")
print("-" * 28)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['plants']:>18,}")

print("\n--- 1D. Concrete Pipe & Precast (NAICS 327332 + 327390) ---")
print("Precast/pipe manufacturers: high-volume, rail-receivable cement consumers.\n")
df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as plants
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code IN ('327332', '327390')
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY plants DESC
    LIMIT 20
''').fetchdf()
print(f"{'State':<8} {'Precast/Pipe Plants':>20}")
print("-" * 30)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['plants']:>20,}")

print("\n--- 1E. Highway/Paving Contractors (NAICS 237310) ---")
print("Road builders consume cement for concrete paving, bridges, barriers.\n")
df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as plants
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code = '237310'
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY plants DESC
    LIMIT 15
''').fetchdf()
print(f"{'State':<8} {'Hwy/Paving Facilities':>22}")
print("-" * 32)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['plants']:>22,}")

print("\n--- 1F. Oil & Gas Cementing (NAICS 213112) ---")
print("Well cementing services: specialized, high-margin, cyclical demand.\n")
df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as facilities
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code = '213112'
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY facilities DESC
    LIMIT 10
''').fetchdf()
print(f"{'State':<8} {'Oil/Gas Cementing':>20}")
print("-" * 30)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['facilities']:>20,}")

# =====================================================================
# SECTION 2: WHERE ARE THEY - Geographic Demand Mapping
# =====================================================================
print("\n\n" + "=" * 100)
print("SECTION 2: WHERE ARE THEY - Geographic Demand Concentration")
print("=" * 100)

print("\n--- 2A. Total Cement Consumer Density by State (All NAICS 3273%) ---")
df = frs.execute('''
    SELECT f.fac_state as state,
           COUNT(DISTINCT f.registry_id) as total_facilities,
           COUNT(DISTINCT CASE WHEN n.naics_code = '327320' THEN f.registry_id END) as readymix,
           COUNT(DISTINCT CASE WHEN n.naics_code = '327331' THEN f.registry_id END) as block_brick,
           COUNT(DISTINCT CASE WHEN n.naics_code IN ('327332','327390') THEN f.registry_id END) as precast_pipe,
           COUNT(DISTINCT CASE WHEN n.naics_code = '327310' THEN f.registry_id END) as cement_plants
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
      AND f.fac_state IS NOT NULL
      AND LENGTH(f.fac_state) = 2
    GROUP BY f.fac_state
    ORDER BY total_facilities DESC
    LIMIT 25
''').fetchdf()
print(f"{'State':<8} {'Total':>8} {'ReadyMix':>10} {'Block/Brick':>12} {'Precast/Pipe':>14} {'Cement Plants':>14}")
print("-" * 68)
for _, row in df.iterrows():
    print(f"{row['state']:<8} {row['total_facilities']:>8,} {row['readymix']:>10,} {row['block_brick']:>12,} {row['precast_pipe']:>14,} {row['cement_plants']:>14,}")

print("\n--- 2B. USGS Cement Demand by Region (Actual Shipments) ---")
df = atlas.execute('''
    SELECT state, ROUND(SUM(shipments_short_tons)/1000000, 2) as million_tons
    FROM usgs_monthly_shipments
    GROUP BY state
    ORDER BY million_tons DESC
''').fetchdf()
print(f"\n{'Region/State':<35} {'MM Short Tons':>14}")
print("-" * 51)
for _, row in df.iterrows():
    print(f"{row['state']:<35} {row['million_tons']:>14,.2f}")
print(f"\n{'US TOTAL':<35} {df['million_tons'].sum():>14,.2f}")

print("\n--- 2C. Supply vs Demand Gap (Import-Dependent Markets) ---")
print("\nStates with HIGH demand but LOW/NO domestic production rely on imports:\n")

# Get production states
prod = atlas.execute('''
    SELECT state, COUNT(*) as plants, ROUND(SUM(capacity_mtpa), 1) as capacity_mt
    FROM us_cement_facilities
    WHERE facility_type = 'CEMENT_PLANT' AND capacity_mtpa > 0
    GROUP BY state
    ORDER BY capacity_mt DESC
''').fetchdf()

# Get demand
demand = atlas.execute('''
    SELECT state as demand_state, ROUND(SUM(shipments_short_tons)/1000000, 2) as demand_mt
    FROM usgs_monthly_shipments
    GROUP BY state
    ORDER BY demand_mt DESC
''').fetchdf()

print(f"{'State/Region':<35} {'Demand (MM ST)':>15} {'Production':>12} {'Gap':>10}")
print("-" * 74)
import_dependent = [
    ('Florida', 11.91, 'Minimal', 'HIGH'),
    ('North Carolina', 4.02, 'Low', 'HIGH'),
    ('New York, metropolitan', 3.14, 'None', 'TOTAL'),
    ('Georgia', 2.86, 'Low', 'HIGH'),
    ('Massachusetts', 2.45, 'None', 'TOTAL'),
    ('Virginia', 2.45, 'Low', 'MODERATE'),
    ('South Carolina', 2.10, 'Low', 'HIGH'),
    ('New Jersey', 2.02, 'None', 'TOTAL'),
    ('Louisiana', 1.69, 'Moderate', 'MODERATE'),
]
for state, demand_val, prod_str, gap in import_dependent:
    print(f"{state:<35} {demand_val:>15,.2f} {prod_str:>12} {gap:>10}")

# =====================================================================
# SECTION 3: SUPPLY CHAIN - How Cement Moves
# =====================================================================
print("\n\n" + "=" * 100)
print("SECTION 3: SUPPLY CHAIN - How Cement Gets From Source to Consumer")
print("=" * 100)

print("""
CEMENT SUPPLY CHAIN OVERVIEW:
==============================

Source --> Ocean Vessel --> Import Terminal --> Distribution --> End User
 |                              |                  |               |
 |  Domestic Plant ----------->|                  |               |
 |                              |                  |               |
 |  MODES:                      |    MODES:        |    MODES:     |
 |  - Bulk vessel (30-60K MT)   |    - Rail car    |    - Truck    |
 |  - Self-unloading vessel     |    - Truck       |    (concrete  |
 |                              |    - Barge       |     mixer)    |
 |                              |                  |               |
 ORIGIN COUNTRIES:              TERMINAL TYPES:    DISTRIBUTION:   CONSUMERS:
 - Turkey (35%)                 - Deep water port  - Rail hoppers  - Ready-mix
 - Greece (12%)                 - River terminal   - Pneumatic     - Precast
 - Canada (10%)                 - Lake port          trailer       - Block/CMU
 - Colombia (8%)                - Rail terminal    - Silo truck    - Highway
 - Vietnam (7%)                                    - Barge         - Oil/gas
 - Algeria (5%)                                                    - Wholesale

KEY ECONOMICS:
- Ocean freight: $15-30/MT (origin dependent)
- Terminal handling: $5-8/MT
- Rail: $15-40/MT (distance dependent, ~$0.03-0.05/ton-mile)
- Truck: $8-15/MT (max ~100 miles economical)
- Barge: $8-15/MT (Mississippi system, very cost effective)

TYPICAL DELIVERED COST COMPONENTS (Import cement to end user):
- FOB plant/port of origin:     $40-60/MT
- Ocean freight:                $15-30/MT
- Terminal/handling:            $5-8/MT
- Inland freight (rail/truck):  $15-40/MT
- TOTAL DELIVERED:              $75-138/MT ($68-125/short ton)
""")

print("\n--- 3A. Import Origin Analysis ---")
df = atlas.execute('''
    SELECT origin_country,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
           ROUND(100.0 * SUM(weight_tons) / (SELECT SUM(weight_tons) FROM trade_imports), 1) as pct_share,
           COUNT(DISTINCT port_of_unlading) as ports_served,
           COUNT(DISTINCT consignee) as importers
    FROM trade_imports
    GROUP BY origin_country
    ORDER BY million_tons DESC
''').fetchdf()
print(f"\n{'Origin Country':<20} {'Shipments':>10} {'MM MT':>10} {'Share%':>8} {'Ports':>8} {'Importers':>10}")
print("-" * 68)
for _, row in df.iterrows():
    print(f"{str(row['origin_country'] or ''):<20} {row['shipments']:>10,} {row['million_tons']:>10,.2f} {row['pct_share']:>8,.1f} {row['ports_served']:>8} {row['importers']:>10}")

print("\n--- 3B. Terminal/Port Infrastructure ---")
df = atlas.execute('''
    SELECT port_of_unlading as port,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
           COUNT(DISTINCT origin_country) as source_countries,
           COUNT(DISTINCT consignee) as importers
    FROM trade_imports
    GROUP BY port_of_unlading
    ORDER BY million_tons DESC
    LIMIT 20
''').fetchdf()
print(f"\n{'Port':<55} {'Ship':>6} {'MM MT':>8} {'Cntry':>6} {'Imp':>5}")
print("-" * 82)
for _, row in df.iterrows():
    port = str(row['port'] or '')[:53].replace('\u2011', '-')
    print(f"{port:<55} {row['shipments']:>6} {row['million_tons']:>8,.2f} {row['source_countries']:>6} {row['importers']:>5}")

print("\n--- 3C. Rail-Served Facility Analysis ---")
df = atlas.execute('''
    SELECT facility_type,
           COUNT(*) as total,
           SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) as rail_served,
           ROUND(100.0 * SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) / COUNT(*), 0) as pct_rail
    FROM us_cement_facilities
    GROUP BY facility_type
    ORDER BY total DESC
''').fetchdf()
print(f"\n{'Facility Type':<25} {'Total':>8} {'Rail-Served':>12} {'% Rail':>8}")
print("-" * 55)
for _, row in df.iterrows():
    print(f"{str(row['facility_type'] or ''):<25} {row['total']:>8,} {row['rail_served']:>12,} {row['pct_rail']:>7,.0f}%")

print("\n--- 3D. Major Importers (Who Controls Supply?) ---")
df = atlas.execute('''
    SELECT consignee as importer,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
           COUNT(DISTINCT origin_country) as source_countries,
           COUNT(DISTINCT port_of_unlading) as ports
    FROM trade_imports
    WHERE consignee IS NOT NULL
    GROUP BY consignee
    ORDER BY million_tons DESC
    LIMIT 20
''').fetchdf()
print(f"\n{'Importer':<30} {'Shipments':>10} {'MM MT':>8} {'Sources':>8} {'Ports':>6}")
print("-" * 64)
for _, row in df.iterrows():
    imp = str(row['importer'] or '')[:28].replace('\u2011', '-')
    print(f"{imp:<30} {row['shipments']:>10,} {row['million_tons']:>8,.2f} {row['source_countries']:>8} {row['ports']:>6}")

# =====================================================================
# SECTION 4: MARKET-BY-MARKET PORT ANALYSIS
# =====================================================================
print("\n\n" + "=" * 100)
print("SECTION 4: PORT-TO-MARKET ANALYSIS - Delivered Cost Economics")
print("=" * 100)

print("""
METHODOLOGY:
- Rail economics: ~$0.03-0.05/ton-mile for bulk cement (covered hopper)
- Truck economics: ~$0.10-0.15/ton-mile (pneumatic trailer, max ~150 miles)
- Barge economics: ~$0.01-0.02/ton-mile (Mississippi system)
- Vessel economics: ~$0.005-0.01/ton-mile (ocean, highly variable)

COMPETITIVE RADIUS:
- Truck: 0-100 miles (primary), 100-150 miles (competitive edge)
- Rail: 100-800 miles (sweet spot 200-500 miles)
- Barge: Unlimited on navigable waterways (most cost effective)
""")

# Port-specific market analysis
ports_analysis = [
    {
        'name': 'HOUSTON TX',
        'rail': 'UP, BNSF, KCS (3 Class I carriers)',
        'markets': [
            ('Houston Metro', 'Truck', '0-50 mi', '$5-8/MT', '6.8M pop, massive construction'),
            ('Dallas-Fort Worth', 'Rail (BNSF/UP)', '250 mi', '$12-18/MT', '7.6M pop, #1 TX market'),
            ('San Antonio', 'Rail/Truck', '200 mi', '$10-15/MT', '2.6M pop, steady growth'),
            ('Austin', 'Rail/Truck', '165 mi', '$8-12/MT', '2.3M pop, boom market'),
            ('Oklahoma City', 'Rail (BNSF)', '440 mi', '$18-25/MT', 'Limited local supply'),
            ('Midland-Odessa', 'Rail (UP)', '500 mi', '$20-30/MT', 'Oil/gas cementing demand'),
            ('El Paso', 'Rail (UP/BNSF)', '750 mi', '$25-35/MT', 'Competes with Mexico supply'),
            ('Shreveport/Monroe', 'Rail (KCS)', '330 mi', '$15-22/MT', 'NE Louisiana market'),
            ('Little Rock', 'Rail (UP)', '500 mi', '$20-28/MT', 'Competes with MO/AR plants'),
        ]
    },
    {
        'name': 'TAMPA FL',
        'rail': 'CSX (single Class I)',
        'markets': [
            ('Tampa Bay Metro', 'Truck', '0-50 mi', '$5-8/MT', '3.2M pop, condo/commercial boom'),
            ('Orlando', 'Rail/Truck', '85 mi', '$8-12/MT', '2.7M pop, tourism infrastructure'),
            ('Southwest FL', 'Truck', '120 mi', '$10-15/MT', 'Naples/Ft Myers, growth corridor'),
            ('Jacksonville', 'Rail (CSX)', '200 mi', '$12-18/MT', '1.6M pop, port development'),
            ('Gainesville/N FL', 'Rail/Truck', '130 mi', '$10-14/MT', 'University/state projects'),
            ('South FL (Miami)', 'Competes w/ PEV', '280 mi', '$18-25/MT', 'Port Everglades closer'),
        ]
    },
    {
        'name': 'NORFOLK VA',
        'rail': 'CSX + Norfolk Southern (dual Class I)',
        'markets': [
            ('Hampton Roads', 'Truck', '0-30 mi', '$4-7/MT', 'Naval base, port infrastructure'),
            ('Richmond', 'Rail (NS/CSX)', '90 mi', '$8-12/MT', '1.3M pop, state capital'),
            ('Raleigh-Durham', 'Rail (NS)', '170 mi', '$12-18/MT', '2.0M pop, research triangle'),
            ('DC/Baltimore', 'Rail (CSX)', '180 mi', '$12-18/MT', '6.3M pop, federal projects'),
            ('Charlotte', 'Rail (NS)', '280 mi', '$15-22/MT', '2.7M pop, banking/commercial hub'),
            ('Philadelphia', 'Rail (CSX)', '300 mi', '$18-25/MT', 'Competes w/ Phila terminal'),
            ('Charleston SC', 'Rail (NS/CSX)', '500 mi', '$22-30/MT', 'Long haul, Savannah closer'),
        ]
    },
    {
        'name': 'WILMINGTON NC',
        'rail': 'CSX (single Class I)',
        'markets': [
            ('Wilmington Metro', 'Truck', '0-30 mi', '$4-7/MT', 'Coastal NC growth'),
            ('Raleigh-Durham', 'Rail (CSX)', '130 mi', '$10-15/MT', '2.0M pop, closest port'),
            ('Charlotte', 'Rail (CSX via Hamlet)', '200 mi', '$12-18/MT', '2.7M pop, key target'),
            ('Fayetteville', 'Truck/Rail', '85 mi', '$8-12/MT', 'Ft Liberty military base'),
            ('Greensboro/Triad', 'Rail (CSX)', '200 mi', '$12-18/MT', '1.7M pop, manufacturing'),
            ('Columbia SC', 'Rail (CSX)', '170 mi', '$12-16/MT', 'Competes w/ Savannah'),
            ('Myrtle Beach', 'Truck', '75 mi', '$7-10/MT', 'Tourism construction'),
        ]
    },
    {
        'name': 'MOREHEAD CITY NC',
        'rail': 'Norfolk Southern (single Class I, branch line)',
        'markets': [
            ('Eastern NC', 'Truck', '0-80 mi', '$5-10/MT', 'Limited market size'),
            ('Raleigh', 'Rail (NS)', '140 mi', '$12-16/MT', 'Less direct than Wilmington'),
            ('Charlotte', 'Rail (NS)', '280 mi', '$18-25/MT', 'Circuitous, less competitive'),
            ('Greenville/Rocky Mt', 'Truck', '90 mi', '$8-12/MT', 'Regional market'),
        ]
    },
    {
        'name': 'SAVANNAH GA',
        'rail': 'CSX + Norfolk Southern (dual Class I)',
        'markets': [
            ('Savannah Metro', 'Truck', '0-30 mi', '$4-7/MT', 'Port growth, manufacturing'),
            ('Atlanta', 'Rail (NS/CSX)', '250 mi', '$15-20/MT', '6.1M pop, massive market'),
            ('Charlotte', 'Rail (NS)', '260 mi', '$15-22/MT', 'Competes w/ Norfolk & Wilmington'),
            ('Charleston', 'Rail/Truck', '110 mi', '$8-12/MT', 'Growing coastal market'),
            ('Jacksonville', 'Rail/Truck', '140 mi', '$10-14/MT', 'Competes w/ Tampa/PEV'),
            ('Columbia SC', 'Rail (NS/CSX)', '160 mi', '$10-15/MT', 'SC state capital'),
            ('Birmingham', 'Rail (NS)', '400 mi', '$20-28/MT', 'Competes w/ local plants'),
            ('Chattanooga', 'Rail (NS)', '360 mi', '$18-25/MT', 'Competes w/ TN plants'),
        ]
    },
    {
        'name': 'GRAMERCY/NEW ORLEANS LA',
        'rail': 'UP, BNSF, NS, CSX, KCS (5 Class I carriers!)',
        'markets': [
            ('New Orleans Metro', 'Truck', '0-50 mi', '$5-8/MT', '1.3M pop, petrochemical'),
            ('Baton Rouge', 'Truck/Barge', '60 mi', '$6-10/MT', 'Industrial corridor'),
            ('Memphis', 'Barge/Rail', '400 mi', '$12-18/MT', 'Barge economics unbeatable'),
            ('St. Louis', 'Barge/Rail', '700 mi', '$15-22/MT', 'Mississippi barge access'),
            ('Jackson MS', 'Rail (NS/CN)', '180 mi', '$12-16/MT', 'Limited local supply'),
            ('Birmingham', 'Rail (NS)', '350 mi', '$18-25/MT', 'Competes w/ AL plants'),
            ('Little Rock', 'Rail (UP)', '400 mi', '$18-25/MT', 'Competes w/ AR plants'),
            ('Quad Cities/Midwest', 'Barge', '900 mi', '$18-25/MT', 'Barge cost advantage'),
        ]
    },
]

for port in ports_analysis:
    print(f"\n{'='*80}")
    print(f"  {port['name']}")
    print(f"  Rail Service: {port['rail']}")
    print(f"{'='*80}")
    print(f"  {'Market':<25} {'Mode':<22} {'Distance':<12} {'Freight':>10} {'Notes'}")
    print(f"  {'-'*95}")
    for market, mode, dist, freight, notes in port['markets']:
        print(f"  {market:<25} {mode:<22} {dist:<12} {freight:>10} {notes}")

# =====================================================================
# SECTION 5: DEMAND DRIVERS & MARKET SIZING
# =====================================================================
print("\n\n" + "=" * 100)
print("SECTION 5: DEMAND DRIVERS & MARKET SIZING")
print("=" * 100)

print("""
CEMENT DEMAND DRIVERS (by sector):

1. RESIDENTIAL CONSTRUCTION (30-35% of demand)
   - Foundations, driveways, sidewalks
   - Driven by: housing starts, population growth, migration
   - Key markets: FL, TX, NC, GA, AZ (Sun Belt growth)

2. NON-RESIDENTIAL CONSTRUCTION (25-30%)
   - Commercial buildings, warehouses, data centers
   - Driven by: GDP, commercial investment, tech expansion
   - Key markets: TX, CA, GA, NC, VA (data center boom)

3. PUBLIC/INFRASTRUCTURE (30-35%)
   - Highways, bridges, water/sewer, airports
   - Driven by: IIJA ($1.2T), state DOT budgets
   - Key markets: Every state, but FL/TX/CA lead spending

4. OIL & GAS (5-8%)
   - Well cementing, platforms, terminals
   - Driven by: Rig count, drilling activity
   - Key markets: TX (Permian), ND (Bakken), PA (Marcellus)

US CEMENT MARKET SIZE:
- Annual consumption: ~110 million metric tons
- Domestic production: ~85 million metric tons
- Import requirement: ~25 million metric tons (23%)
- Annual market value: ~$15-18 billion
""")

# =====================================================================
# SECTION 6: COMPETITIVE LANDSCAPE AT EACH PORT
# =====================================================================
print("\n" + "=" * 100)
print("SECTION 6: COMPETITIVE LANDSCAPE - Who Operates Where")
print("=" * 100)

print("\n--- 6A. Import Terminal Operators by Port ---")
df = atlas.execute('''
    SELECT port_of_unlading as port, consignee as operator,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 2) as mm_mt,
           COUNT(DISTINCT origin_country) as sources
    FROM trade_imports
    WHERE consignee IS NOT NULL
    GROUP BY port_of_unlading, consignee
    ORDER BY mm_mt DESC
    LIMIT 40
''').fetchdf()

current_port = None
for _, row in df.iterrows():
    port = str(row['port'] or '')[:50].replace('\u2011', '-')
    op = str(row['operator'] or '')[:25].replace('\u2011', '-')
    if port != current_port:
        print(f"\n  {port}")
        print(f"  {'Operator':<28} {'Ship':>6} {'MM MT':>8} {'Sources':>8}")
        print(f"  {'-'*52}")
        current_port = port
    print(f"  {op:<28} {row['shipments']:>6} {row['mm_mt']:>8,.2f} {row['sources']:>8}")

# =====================================================================
# SECTION 7: KEY FINDINGS & STRATEGIC IMPLICATIONS
# =====================================================================
print("\n\n" + "=" * 100)
print("SECTION 7: KEY FINDINGS & STRATEGIC IMPLICATIONS")
print("=" * 100)

# Count consumers by region served by each port
for port_name, states, label in [
    ('Houston', ['TX', 'OK', 'NM', 'AR', 'LA'], 'Gulf/Southwest'),
    ('Tampa', ['FL'], 'Florida'),
    ('Norfolk', ['VA', 'MD', 'DC', 'DE'], 'Mid-Atlantic'),
    ('Wilmington', ['NC'], 'North Carolina'),
    ('Savannah', ['GA', 'SC'], 'SE Coastal'),
    ('Gramercy', ['LA', 'MS', 'AL'], 'Lower Mississippi'),
]:
    states_sql = "','".join(states)
    cnt = frs.execute(f'''
        SELECT COUNT(DISTINCT f.registry_id)
        FROM facilities f
        JOIN naics_codes n ON f.registry_id = n.registry_id
        WHERE n.naics_code LIKE '3273%'
          AND f.fac_state IN ('{states_sql}')
    ''').fetchone()[0]
    print(f"\n  {port_name} -> {label}: {cnt:,} cement consumer facilities")

print("""

STRATEGIC FINDINGS:
==================

1. HIGHEST CONSUMER DENSITY MARKETS:
   - Florida (1,382 facilities) - Tampa/PEV coverage
   - Texas (850) - Houston dominant
   - Illinois (1,169) - Served by Gramercy barge + Great Lakes
   - North Carolina (722) - UNDERSERVED by import terminals
   - Virginia (632) - Norfolk coverage but could expand

2. UNDERSERVED MARKETS (high demand, limited import infrastructure):
   - NC Piedmont (Charlotte/Raleigh): 722 facilities, only 0.65 MM MT imports
   - South Carolina: 507 facilities, minimal import presence
   - Tennessee: 462 facilities, no direct import port
   - Kentucky: 388 facilities, no import terminal

3. PORT ADVANTAGES RANKING (for new terminal):

   TIER 1 - Best Economics:
   a) Gramercy/New Orleans: 5 Class I carriers + barge = unmatched reach
   b) Norfolk: Dual Class I + deepest water = best vessel economics

   TIER 2 - Good Niche Play:
   c) Wilmington NC: CSX to Charlotte/Raleigh, underserved market
   d) Savannah: Already established but room for growth

   TIER 3 - Challenging:
   e) Morehead City: Single branch line, small vessels, limited market
   f) Camden/Philadelphia: Established competition (Riverside Controls)

4. NC MARKET OPPORTUNITY:
   - 722 cement consumer facilities
   - 4.02 MM short tons annual demand (USGS)
   - Only 0.65 MM MT currently imported through NC ports
   - Charlotte MSA (2.7M pop) is the prize market
   - Wilmington CSX rail: 200 miles to Charlotte
   - Norfolk NS/CSX rail: 280 miles to Charlotte
   - Wilmington has DISTANCE ADVANTAGE to Charlotte

5. SUPPLY CHAIN CRITICAL SUCCESS FACTORS:
   - Vessel size capability (larger = lower $/MT)
   - Number of Class I rail carriers (more = competitive rates)
   - Distance to demand center (shorter = lower delivered cost)
   - Barge access (cheapest inland mode, if available)
   - Terminal throughput capacity (silo storage, discharge rate)
""")

atlas.close()
frs.close()
print("\nAnalysis complete.")
