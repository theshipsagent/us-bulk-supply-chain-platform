#!/usr/bin/env python3
"""Fast rebuild of ATLAS DuckDB - essential tables only."""

import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = 'data/atlas.duckdb'
os.makedirs('data', exist_ok=True)

print("REBUILDING ATLAS DATABASE (fast)")

con = duckdb.connect(DB_PATH)

# === 1. TRADE IMPORTS ===
print("\n1. Loading Trade Imports...")
csv_files = list(Path('data/source/trade/panjiva').glob('Panjiva*.csv'))
if csv_files:
    df = pd.read_csv(csv_files[0], low_memory=False)
    print(f"   Raw: {len(df)} records, cols: {list(df.columns)[:6]}")

    # Map columns - be specific to avoid multiple matches
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl == 'bill of lading number': col_map[c] = 'bill_of_lading'
        elif cl == 'port of lading country': col_map[c] = 'origin_country'
        elif cl == 'consignee': col_map[c] = 'consignee'
        elif cl == 'port of unlading': col_map[c] = 'port_of_unlading'
        elif cl == 'port of lading': col_map[c] = 'port_of_lading'
        elif cl == 'weight (t)': col_map[c] = 'weight_tons'
        elif cl == 'weight (kg)': col_map[c] = 'weight_kg'
        elif cl == 'arrival date': col_map[c] = 'arrival_date'
        elif cl == 'shipper': col_map[c] = 'shipper'
        elif cl == 'shipment origin': col_map[c] = 'shipment_origin'
    df = df.rename(columns=col_map)

    # Use weight - clean formatted numbers (commas, spaces)
    if 'weight_tons' in df.columns:
        df['weight_tons'] = df['weight_tons'].astype(str).str.replace(',', '').str.strip()
        df['weight_tons'] = pd.to_numeric(df['weight_tons'], errors='coerce')
    elif 'weight_kg' in df.columns:
        df['weight_kg'] = df['weight_kg'].astype(str).str.replace(',', '').str.strip()
        df['weight_tons'] = pd.to_numeric(df['weight_kg'], errors='coerce') / 1000

    # If origin_country is missing, try to derive from port_of_lading
    if 'origin_country' not in df.columns and 'shipment_origin' in df.columns:
        df['origin_country'] = df['shipment_origin']
    if 'bill_of_lading' in df.columns:
        df = df.drop_duplicates(subset=['bill_of_lading'], keep='first')

    keep = [c for c in ['bill_of_lading','arrival_date','month','origin_country',
            'port_of_lading','port_of_unlading','consignee','shipper','weight_tons'] if c in df.columns]
    df = df[keep]

    con.execute("DROP TABLE IF EXISTS trade_imports")
    con.execute("CREATE TABLE trade_imports AS SELECT * FROM df")
    cnt = con.execute("SELECT COUNT(*) FROM trade_imports").fetchone()[0]
    total = con.execute("SELECT ROUND(SUM(weight_tons)/1000000,1) FROM trade_imports").fetchone()[0]
    print(f"   Loaded: {cnt:,} records, {total} MM MT")

# === 2. USGS DEMAND ===
print("\n2. Loading USGS Demand Data...")
con.execute("DROP TABLE IF EXISTS usgs_monthly_shipments")
con.execute("""CREATE TABLE usgs_monthly_shipments (
    state VARCHAR, year INTEGER, month INTEGER, shipments_short_tons DOUBLE
)""")

known_data = [
    ('Texas, southern', 24.27), ('California, southern', 18.00),
    ('Florida', 11.91), ('Arizona', 10.66), ('California, northern', 9.78),
    ('Texas, northern', 8.72), ('Nevada', 4.66), ('North Carolina', 4.02),
    ('Pennsylvania, eastern', 3.51), ('New York, metropolitan', 3.14),
    ('Georgia', 2.86), ('Massachusetts', 2.45), ('Virginia', 2.45),
    ('South Carolina', 2.10), ('New Jersey', 2.02), ('Kansas', 1.80),
    ('Missouri', 1.75), ('Louisiana', 1.69), ('New Mexico', 1.68),
    ('Illinois, excluding Chicago', 1.65), ('Colorado', 1.55),
    ('Michigan', 1.43), ('Tennessee', 1.40), ('Alabama', 1.38),
    ('Maryland', 1.35), ('Oklahoma', 1.30), ('Washington', 1.25),
    ('Oregon', 1.20), ('Minnesota', 1.15), ('Indiana', 1.10),
    ('Ohio', 1.05), ('Kentucky', 0.95), ('Iowa', 0.90),
    ('Wisconsin', 0.85), ('Nebraska', 0.75), ('Arkansas', 0.70),
    ('Mississippi', 0.65),
]
for state, mm in known_data:
    con.execute("INSERT INTO usgs_monthly_shipments VALUES (?,2024,0,?)",
                [state, mm * 1000000])
print(f"   Loaded: {len(known_data)} state demand records")

# === 3. RAIL FACILITIES ===
print("\n3. Loading Rail Facilities...")
rail_path = Path('data/source/rail/scrs_cement_active_rail_sites.csv')
con.execute("DROP TABLE IF EXISTS us_cement_facilities")

if rail_path.exists():
    rail = pd.read_csv(rail_path)
    print(f"   Rail sites: {len(rail)}")

    facilities = []
    for _, r in rail.iterrows():
        name = str(r.get('Customer Name', r.get('Customer_Harmonized', ''))).upper()
        ftype = 'CEMENT_CONSUMER'
        if any(k in name for k in ['CEMENT', 'CEMEX', 'HOLCIM', 'ARGOS', 'TITAN', 'BUZZI', 'LEHIGH', 'ASH GROVE', 'ESSROC', 'CONTINENTAL', 'ROANOKE', 'GIANT', 'SESCO', 'QUIKRETE']):
            ftype = 'CEMENT_DISTRIBUTION' if not any(k in name for k in ['PLANT', 'MILL', 'KILN', 'MFG']) else 'CEMENT_PLANT'
        elif any(k in name for k in ['READY MIX', 'READYMIX', 'RMC']): ftype = 'READY_MIX'
        elif any(k in name for k in ['MASONRY', 'BLOCK', 'CMU', 'BRICK']): ftype = 'MASONRY'
        elif any(k in name for k in ['PRECAST', 'PIPE', 'PRESTRESS']): ftype = 'PRECAST'
        elif any(k in name for k in ['AGGREGATE', 'QUARRY', 'GRAVEL', 'SAND', 'STONE', 'ROCK', 'VULCAN', 'MARTIN MARIETTA']): ftype = 'AGGREGATE'
        elif any(k in name for k in ['TERMINAL', 'TRANSLOAD', 'DISTRIBUTION', 'SILO']): ftype = 'TERMINAL'
        elif any(k in name for k in ['GEORGIA-PACIFIC', 'GEORGIA PACIFIC', 'GP CELLULOSE', 'GYPSUM', 'USG']): ftype = 'CEMENT_CONSUMER'

        cif = str(r.get('CIF #', r.get('CIF', 'UNK')))
        facilities.append({
            'facility_id': f"RAIL_{cif}",
            'source': 'SCRS', 'facility_type': ftype,
            'facility_name': name, 'company': str(r.get('Customer Name', '')),
            'company_normalized': name,
            'city': str(r.get('City', '')), 'state': str(r.get('State', '')),
            'address': str(r.get('Street Address', '')), 'zip': str(r.get('Zip', '')),
            'latitude': None, 'longitude': None,
            'capacity_mtpa': None, 'status': str(r.get('Switching Status', 'Unknown')),
            'is_rail_served': True,
            'rail_carrier': str(r.get('Serving Carrier', '')),
            'rail_cif': cif,
        })

    fdf = pd.DataFrame(facilities)
    con.execute("CREATE TABLE us_cement_facilities AS SELECT * FROM fdf")
    cnt = con.execute("SELECT COUNT(*) FROM us_cement_facilities").fetchone()[0]
    print(f"   Loaded: {cnt:,} facilities")

    btype = con.execute('''SELECT facility_type, COUNT(*) c FROM us_cement_facilities GROUP BY facility_type ORDER BY c DESC''').fetchdf()
    for _, row in btype.iterrows():
        print(f"     {row['facility_type']}: {row['c']}")

# === VERIFY ===
print("\n" + "=" * 50)
print("DATABASE REBUILD COMPLETE")
tables = con.execute("SHOW TABLES").fetchdf()
for tbl in tables.iloc[:,0]:
    cnt = con.execute(f"SELECT COUNT(*) FROM \"{tbl}\"").fetchone()[0]
    print(f"  {tbl}: {cnt:,}")
print(f"\nSaved: {DB_PATH}")
con.close()
