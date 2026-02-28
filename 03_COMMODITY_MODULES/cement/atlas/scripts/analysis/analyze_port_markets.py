#!/usr/bin/env python3
"""Analyze port-to-market economics for cement import terminals."""

import duckdb

# Connect to databases
atlas = duckdb.connect('../data/atlas.duckdb', read_only=True)
frs = duckdb.connect('G:/My Drive/LLM/task_epa_frs/data/frs.duckdb', read_only=True)

print("=" * 80)
print("PORT-TO-MARKET ANALYSIS: WHERE ARE CEMENT CONSUMERS?")
print("=" * 80)

# Define market regions by state
southeast_coastal = ['FL', 'GA', 'SC', 'NC']
mid_atlantic = ['VA', 'MD', 'DE', 'PA', 'NJ', 'NY']
gulf_states = ['TX', 'LA', 'AL', 'MS']
midwest = ['IL', 'MO', 'KS', 'IA', 'NE', 'MN', 'WI', 'IN', 'OH', 'MI']

print("\n=== CEMENT CONSUMER FACILITIES BY REGION (EPA FRS - NAICS 3273%) ===")
regions = {
    'Southeast Coastal (FL/GA/SC/NC)': southeast_coastal,
    'Mid-Atlantic (VA/MD/DE/PA/NJ/NY)': mid_atlantic,
    'Gulf States (TX/LA/AL/MS)': gulf_states,
    'Midwest (IL/MO/KS/IA/NE/MN/WI/IN/OH/MI)': midwest,
}

for region_name, states in regions.items():
    states_sql = "','".join(states)
    cnt = frs.execute(f'''
        SELECT COUNT(DISTINCT f.registry_id)
        FROM facilities f
        JOIN naics_codes n ON f.registry_id = n.registry_id
        WHERE n.naics_code LIKE '3273%'
          AND f.fac_state IN ('{states_sql}')
    ''').fetchone()[0]
    print(f"  {region_name}: {cnt:,} facilities")

print("\n=== READY-MIX CONCRETE PLANTS BY STATE (Largest Consumer Segment) ===")
df = frs.execute('''
    SELECT f.fac_state as state, COUNT(DISTINCT f.registry_id) as facilities
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code = '327320'
    GROUP BY f.fac_state
    ORDER BY facilities DESC
    LIMIT 20
''').fetchdf()
print(df.to_string())

print("\n=== CURRENT IMPORT FLOWS BY PORT (ATLAS Trade Data) ===")
df = atlas.execute('''
    SELECT port_of_unlading as port,
           ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
           COUNT(DISTINCT consignee) as importers
    FROM trade_imports
    GROUP BY port_of_unlading
    ORDER BY million_tons DESC
    LIMIT 15
''').fetchdf()
print(df.to_string())

print("\n=== NC AREA IMPORTS (Current Activity) ===")
df = atlas.execute('''
    SELECT port_of_unlading as port, origin_country, consignee,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%North Carolina%'
       OR port_of_unlading LIKE '%Wilmington%'
       OR port_of_unlading LIKE '%Morehead%'
    GROUP BY port_of_unlading, origin_country, consignee
    ORDER BY million_tons DESC
''').fetchdf()
if len(df) > 0:
    print(df.to_string())
else:
    print("  No cement imports recorded to NC ports in data period")

print("\n=== VIRGINIA/NORFOLK IMPORTS (Comparison) ===")
df = atlas.execute('''
    SELECT port_of_unlading as port, origin_country, consignee,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%Virginia%'
       OR port_of_unlading LIKE '%Norfolk%'
    GROUP BY port_of_unlading, origin_country, consignee
    ORDER BY million_tons DESC
''').fetchdf()
print(df.to_string())

print("\n=== SAVANNAH IMPORTS (Comparison - SE Gateway) ===")
df = atlas.execute('''
    SELECT origin_country, consignee,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%Savannah%'
       OR port_of_unlading LIKE '%Georgia%'
    GROUP BY origin_country, consignee
    ORDER BY million_tons DESC
''').fetchdf()
print(df.to_string())

print("\n=== CEMENT DEMAND (USGS Shipments) - Key Markets ===")
df = atlas.execute('''
    SELECT state, ROUND(SUM(shipments_short_tons)/1000000, 2) as million_short_tons
    FROM usgs_monthly_shipments
    GROUP BY state
    ORDER BY million_short_tons DESC
''').fetchdf()
print(df.to_string())

print("\n" + "=" * 80)
print("PORT MARKET ANALYSIS SUMMARY")
print("=" * 80)

# NC market analysis
nc_facilities = frs.execute('''
    SELECT COUNT(DISTINCT f.registry_id)
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
      AND f.fac_state = 'NC'
''').fetchone()[0]

sc_facilities = frs.execute('''
    SELECT COUNT(DISTINCT f.registry_id)
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
      AND f.fac_state = 'SC'
''').fetchone()[0]

va_facilities = frs.execute('''
    SELECT COUNT(DISTINCT f.registry_id)
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
      AND f.fac_state = 'VA'
''').fetchone()[0]

print(f"""
NORTH CAROLINA PORT OPTIONS (Wilmington vs Morehead City):

1. LOCAL MARKET SIZE:
   - NC cement consumers: {nc_facilities:,} facilities
   - SC cement consumers: {sc_facilities:,} facilities
   - VA cement consumers: {va_facilities:,} facilities

2. WILMINGTON NC:
   - Deepwater port with good vessel access
   - CSX rail service
   - Primary markets: Raleigh-Durham, Charlotte, Piedmont NC
   - Secondary markets: Columbia SC, coastal NC
   - Competition: Savannah (southbound), Norfolk (northbound)

3. MOREHEAD CITY NC:
   - State-owned port (NC Ports)
   - Norfolk Southern rail connection
   - Smaller vessel capacity than Wilmington
   - Markets: Eastern NC, potentially VA border
   - More limited hinterland than Wilmington

4. KEY CONSIDERATION - RAIL ECONOMICS:
   - Wilmington: CSX provides access to Charlotte, Piedmont, and connections west
   - Morehead City: NS provides access to Raleigh, but more circuitous to Charlotte
   - Neither matches Norfolk's rail hub status for Mid-Atlantic reach
   - Neither matches Savannah's rail economics for Deep South reach
""")

atlas.close()
frs.close()
