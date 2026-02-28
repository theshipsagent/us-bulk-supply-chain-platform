#!/usr/bin/env python3
"""Check NC port activity and comparable ports."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb

atlas = duckdb.connect('../data/atlas.duckdb', read_only=True)

print('=== NC PORT ACTIVITY ===')
df = atlas.execute('''
    SELECT port_of_unlading as port, COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%North Carolina%'
       OR port_of_unlading LIKE '%Wilmington%'
       OR port_of_unlading LIKE '%Morehead%'
    GROUP BY port_of_unlading
''').fetchdf()
if len(df) == 0:
    print('  No cement imports recorded at NC ports in data')
else:
    print(df.to_string())

print()
print('=== NORFOLK/VIRGINIA DETAIL ===')
df = atlas.execute('''
    SELECT origin_country, consignee, COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%Virginia%'
       OR port_of_unlading LIKE '%Norfolk%'
    GROUP BY origin_country, consignee
    ORDER BY million_tons DESC
''').fetchdf()
# Clean non-ASCII characters
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace('\u2011', '-', regex=False)
print(df.to_string())

print()
print('=== PHILADELPHIA/CAMDEN AREA ===')
df = atlas.execute('''
    SELECT port_of_unlading, origin_country, consignee, COUNT(*) as shipments,
           ROUND(SUM(weight_tons)/1000000, 3) as million_tons
    FROM trade_imports
    WHERE port_of_unlading LIKE '%Camden%'
       OR port_of_unlading LIKE '%Philadelphia%'
       OR port_of_unlading LIKE '%Pennsylvania%'
    GROUP BY port_of_unlading, origin_country, consignee
    ORDER BY million_tons DESC
''').fetchdf()
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace('\u2011', '-', regex=False)
print(df.to_string())

print()
print('=== ALL PORTS WITH NO CEMENT CURRENTLY ===')
# List of potential expansion ports
expansion_ports = [
    'Wilmington', 'Morehead', 'Charleston', 'Savannah', 'Jacksonville',
    'Mobile', 'Pascagoula', 'Gulfport', 'Beaumont', 'Freeport',
    'Baltimore', 'Boston'
]
for port in expansion_ports:
    df = atlas.execute(f'''
        SELECT COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 3) as million_tons
        FROM trade_imports
        WHERE port_of_unlading LIKE '%{port}%'
    ''').fetchdf()
    shipments = df['shipments'].iloc[0]
    tons = df['million_tons'].iloc[0] or 0
    if shipments > 0:
        print(f'  {port}: {shipments} shipments, {tons:.2f} MM MT')
    else:
        print(f'  {port}: NO CURRENT IMPORTS')

atlas.close()
