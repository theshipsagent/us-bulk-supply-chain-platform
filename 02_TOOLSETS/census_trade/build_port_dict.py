"""Build US Port Dictionary from Census trade data + authoritative reference.

Source of truth: data/reference/port_reference.csv (unified port reference)
Trade volumes: Census PORTHS6 trade data files (Sep-Nov 2025)
"""
import csv
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Load the single source of truth ──
port_ref = {}
with open('data/reference/port_reference.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        port_ref[row['port_code']] = row

print(f"Port reference: {len(port_ref)} port codes")

# ── 2. District lookup ──
districts = {}
with open('data/extracted/EXDB2501/DISTRICT.TXT', 'r') as f:
    for line in f:
        code = line[0:2].strip()
        name = line[9:59].strip()
        districts[code] = name

# ── 3. Parse trade volumes by port ──
import_port_stats = {}
export_port_stats = {}

for month_dir in ['PORTHS6MM2509', 'PORTHS6MM2510', 'PORTHS6MM2511']:
    fpath = f'data/extracted/{month_dir}/{month_dir}.TXT'
    print(f"Parsing {month_dir}...", flush=True)
    with open(fpath, 'r') as f:
        for line in f:
            if len(line) < 125:
                continue
            port = line[10:14].strip()
            try:
                val_mo = int(line[20:35].strip() or '0')
                ves_val = int(line[65:80].strip() or '0')
                ves_swt = int(line[80:95].strip() or '0')
            except ValueError:
                continue
            if port not in import_port_stats:
                import_port_stats[port] = {'value_usd': 0, 'ves_value_usd': 0, 'ves_weight_kg': 0, 'records': 0}
            import_port_stats[port]['value_usd'] += val_mo
            import_port_stats[port]['ves_value_usd'] += ves_val
            import_port_stats[port]['ves_weight_kg'] += ves_swt
            import_port_stats[port]['records'] += 1

for month_dir in ['PORTHS6XM2509', 'PORTHS6XM2510', 'PORTHS6XM2511']:
    fpath = f'data/extracted/{month_dir}/{month_dir}.TXT'
    print(f"Parsing {month_dir}...", flush=True)
    with open(fpath, 'r') as f:
        for line in f:
            if len(line) < 125:
                continue
            port = line[10:14].strip()
            try:
                val_mo = int(line[20:35].strip() or '0')
                ves_val = int(line[65:80].strip() or '0')
                ves_swt = int(line[80:95].strip() or '0')
            except ValueError:
                continue
            if port not in export_port_stats:
                export_port_stats[port] = {'value_usd': 0, 'ves_value_usd': 0, 'ves_weight_kg': 0, 'records': 0}
            export_port_stats[port]['value_usd'] += val_mo
            export_port_stats[port]['ves_value_usd'] += ves_val
            export_port_stats[port]['ves_weight_kg'] += ves_swt
            export_port_stats[port]['records'] += 1

# ── 4. Build the port dictionary ──
all_ports = sorted(set(list(import_port_stats.keys()) + list(export_port_stats.keys())))

port_lookup = {}
for port_code in all_ports:
    dist = port_code[:2]

    # Get everything from the unified port reference
    if port_code in port_ref:
        ref = port_ref[port_code]
        port_name = ref['sked_d_name'] or ref['cbp_appendix_e_name'] or f"PORT {port_code}"
        consol = ref['port_consolidated']
        coast = ref['port_coast']
        region = ref['port_region']
        port_type = ref['port_type']
    else:
        port_name = f"PORT {port_code}"
        consol = f"District {dist}"
        coast = "Unknown"
        region = "Unknown"
        port_type = "unknown"

    imp = import_port_stats.get(port_code, {'value_usd': 0, 'ves_value_usd': 0, 'ves_weight_kg': 0, 'records': 0})
    exp = export_port_stats.get(port_code, {'value_usd': 0, 'ves_value_usd': 0, 'ves_weight_kg': 0, 'records': 0})

    port_lookup[port_code] = {
        'port_name': port_name,
        'district_code': dist,
        'district_name': districts.get(dist, 'UNKNOWN'),
        'port_type': port_type,
        'port_consolidated': consol,
        'port_coast': coast,
        'port_region': region,
        'import_value_usd': imp['value_usd'],
        'import_ves_value_usd': imp['ves_value_usd'],
        'import_ves_weight_kg': imp['ves_weight_kg'],
        'import_records': imp['records'],
        'export_value_usd': exp['value_usd'],
        'export_ves_value_usd': exp['ves_value_usd'],
        'export_ves_weight_kg': exp['ves_weight_kg'],
        'export_records': exp['records'],
        'total_value_usd': imp['value_usd'] + exp['value_usd'],
        'total_ves_weight_kg': imp['ves_weight_kg'] + exp['ves_weight_kg'],
    }

# ── 5. Build consolidated rollups ──
consol_rollup = {}
for pc, info in port_lookup.items():
    key = info['port_consolidated']
    if key not in consol_rollup:
        consol_rollup[key] = {
            'coast': info['port_coast'],
            'region': info['port_region'],
            'port_codes': [],
            'total_value_usd': 0,
            'import_value_usd': 0,
            'export_value_usd': 0,
            'total_ves_weight_kg': 0,
        }
    consol_rollup[key]['port_codes'].append(pc)
    consol_rollup[key]['total_value_usd'] += info['total_value_usd']
    consol_rollup[key]['import_value_usd'] += info['import_value_usd']
    consol_rollup[key]['export_value_usd'] += info['export_value_usd']
    consol_rollup[key]['total_ves_weight_kg'] += info['total_ves_weight_kg']

consol_rollup = dict(sorted(consol_rollup.items(), key=lambda x: x[1]['total_value_usd'], reverse=True))

# ── 6. Build coast/region hierarchy ──
hierarchy = {}
for consol, info in consol_rollup.items():
    coast = info['coast']
    region = info['region']
    if coast not in hierarchy:
        hierarchy[coast] = {}
    if region not in hierarchy[coast]:
        hierarchy[coast][region] = []
    hierarchy[coast][region].append(consol)

# ── 7. Write master dictionary ──
master = {
    '_metadata': {
        'source_files': [
            'Census PORTHS6MM2509-2511 (imports)',
            'Census PORTHS6XM2509-2511 (exports)',
            'data/reference/port_reference.csv (unified port reference)',
        ],
        'created': '2026-02-15',
        'period': 'Sep-Nov 2025',
        'total_port_codes': len(port_lookup),
        'consolidated_ports': len(consol_rollup),
        'coasts': list(hierarchy.keys()),
        'units': {'value': 'USD', 'weight': 'kilograms'},
        'notes': 'Port codes follow Census Schedule D (district 2-digit + port 2-digit). '
                 'All lookups from data/reference/port_reference.csv.',
    },
    'hierarchy': hierarchy,
    'consolidated_rollup': consol_rollup,
    'port_lookup': port_lookup,
    'district_lookup': districts,
}

with open('data/port_dictionary.json', 'w') as f:
    json.dump(master, f, indent=2, default=str)

fsize = os.path.getsize('data/port_dictionary.json')
print(f"\nDictionary built: data/port_dictionary.json ({fsize / 1024:.0f} KB)")
print(f"  Total port codes:     {len(port_lookup)}")
print(f"  Consolidated groups:  {len(consol_rollup)}")
print(f"  Coasts:               {list(hierarchy.keys())}")

# ── 8. Print top 30 ──
print(f"\nTOP 30 CONSOLIDATED PORTS BY TOTAL VALUE (Sep-Nov 2025)")
print("-" * 90)
for i, (name, info) in enumerate(list(consol_rollup.items())[:30], 1):
    val_b = info['total_value_usd'] / 1e9
    wt_mt = info['total_ves_weight_kg'] / 1e6
    n = len(info['port_codes'])
    print(f"  {i:2d}. {name:35s} ${val_b:8.1f}B  {wt_mt:10.1f}K MT  ({n:2d} codes) [{info['coast']}/{info['region']}]")

# ── 9. Verify key bug fixes ──
print("\n" + "="*70)
print("KEY VERIFICATION: Mobile should NOT be under port 2002")
print("="*70)
p2002 = port_lookup.get('2002', {})
p1901 = port_lookup.get('1901', {})
print(f"  Port 2002: name={p2002.get('port_name')}, consolidated={p2002.get('port_consolidated')}")
print(f"  Port 1901: name={p1901.get('port_name')}, consolidated={p1901.get('port_consolidated')}")
print(f"  Port 5201: consolidated={port_lookup.get('5201', {}).get('port_consolidated')} (should be South Florida)")
print(f"  Port 5203: consolidated={port_lookup.get('5203', {}).get('port_consolidated')} (should be South Florida)")
print(f"  Port 4909: consolidated={port_lookup.get('4909', {}).get('port_consolidated')} (should be San Juan)")

print("\nDone.")
