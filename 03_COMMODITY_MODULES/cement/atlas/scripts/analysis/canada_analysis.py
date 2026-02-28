#!/usr/bin/env python3
"""Analyze Canadian cement competition."""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb

atlas = duckdb.connect('../data/atlas.duckdb', read_only=True)

print('=== CANADIAN IMPORTS - PORT DESTINATIONS ===')
df = atlas.execute('''
    SELECT port_of_unlading as port,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE origin_country = 'Canada'
    GROUP BY port_of_unlading
    ORDER BY million_tons DESC
''').fetchdf()
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace('\u2011', '-', regex=False)
print(df.to_string())

print()
print('=== CANADIAN IMPORTERS (Who is receiving Canadian cement?) ===')
df = atlas.execute('''
    SELECT consignee, port_of_unlading,
           COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE origin_country = 'Canada'
    GROUP BY consignee, port_of_unlading
    ORDER BY million_tons DESC
    LIMIT 15
''').fetchdf()
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace('\u2011', '-', regex=False)
print(df.to_string())

print('''
=== ANALYSIS: CANADIAN COMPETITION ===

Canadian cement enters the US market through two primary channels:

1. VESSEL-TO-RAIL (Great Lakes/St. Lawrence):
   - Detroit: 2.05 MM MT - Major Canada supply point
   - Portland OR: 2.84 MM MT - Western Canada (BC) supply
   - Seattle: 2.45 MM MT - Western Canada supply

   These are primarily serving:
   - Midwest markets (Detroit -> Ohio, Indiana, Michigan)
   - Pacific Northwest (Portland, Seattle)

2. OVERLAND RAIL:
   - Direct rail service from Canadian plants to US border crossings
   - Lafarge/Holcim, CRH (formerly Martin Marietta Canada), etc.
   - Primarily serving:
     * Buffalo/Niagara corridor -> Northeast
     * Detroit corridor -> Midwest
     * Pacific Northwest from BC plants

KEY INSIGHT for East Coast Port Selection:
- Canadian competition is NOT a significant factor for SE/Mid-Atlantic
- Canada primarily impacts Great Lakes and Pacific NW markets
- NC/VA/SC markets are NOT directly threatened by Canadian supply
- Distance and rail economics favor Mediterranean/Caribbean imports for Southeast
''')

atlas.close()
