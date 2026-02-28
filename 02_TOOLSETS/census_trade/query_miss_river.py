"""
Query: Mississippi River annual import/export tonnage
by Group, Commodity, Cargo, Cargo_Detail, Country — Jan-Nov 2025 YTD.

Uses November 2025 files (PORTHS6MM2511 / PORTHS6XM2511) with YTD fields.
"""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ── Load dictionaries ──
with open('data/port_dictionary.json') as f:
    port_dict = json.load(f)

from census_trade.config.cargo_codes import load_cargo_reference
_cargo_ref = load_cargo_reference()

# ── Load country lookup from canonical reference ──
from census_trade.config.country_codes import load_country_reference
_cty_ref = load_country_reference()
countries = {code: row['cty_name'] for code, row in _cty_ref.items()}

# ── Mississippi River ports: all District 20 ──
miss_river_ports = set()
for pc, info in port_dict['port_lookup'].items():
    if info['district_code'] == '20':
        miss_river_ports.add(pc)

print(f"Mississippi River port codes ({len(miss_river_ports)}):")
for pc in sorted(miss_river_ports):
    info = port_dict['port_lookup'][pc]
    print(f"  {pc} {info['port_name']:35s} [{info['port_consolidated']}]")

# ── Layout positions (PORT_IMPORT_HS6 / PORT_EXPORT_HS6 — same structure) ──
# commodity(0:6), cty_code(6:10), port_code(10:14), year(14:18), month(18:20),
# value_mo(20:35), air_val_mo(35:50), air_swt_mo(50:65),
# ves_val_mo(65:80), ves_swt_mo(80:95),
# cnt_val_mo(95:110), cnt_swt_mo(110:125),
# value_yr(125:140), air_val_yr(140:155), air_swt_yr(155:170),
# ves_val_yr(170:185), ves_swt_yr(185:200),
# cnt_val_yr(200:215), cnt_swt_yr(215:230)


def parse_port_file(filepath, ports_filter):
    """Parse port HS6 file, return records for filtered ports using YTD fields."""
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            if len(line) < 200:
                continue
            port = line[10:14].strip()
            if port not in ports_filter:
                continue
            hs6 = line[0:6].strip()
            cty = line[6:10].strip()
            try:
                ves_swt_yr = int(line[185:200].strip() or '0')  # YTD vessel weight kg
                ves_val_yr = int(line[170:185].strip() or '0')  # YTD vessel value USD
            except ValueError:
                continue
            if ves_swt_yr == 0 and ves_val_yr == 0:
                continue
            records.append({
                'hs6': hs6,
                'cty_code': cty,
                'port_code': port,
                'ves_weight_kg': ves_swt_yr,
                'ves_value_usd': ves_val_yr,
            })
    return records


# ── Parse November 2025 files (YTD = Jan-Nov 2025) ──
print("\nParsing import data (Nov 2025 YTD)...")
imports = parse_port_file('data/extracted/PORTHS6MM2511/PORTHS6MM2511.TXT', miss_river_ports)
print(f"  Import records: {len(imports):,}")

print("Parsing export data (Nov 2025 YTD)...")
exports = parse_port_file('data/extracted/PORTHS6XM2511/PORTHS6XM2511.TXT', miss_river_ports)
print(f"  Export records: {len(exports):,}")

# ── Join to cargo dictionary + country lookup ──
def enrich_record(rec, trade_direction):
    hs6 = rec['hs6']
    cargo_info = _cargo_ref.get(hs6, {})
    cty_name = countries.get(rec['cty_code'], f"UNKNOWN ({rec['cty_code']})")
    port_info = port_dict['port_lookup'].get(rec['port_code'], {})
    return {
        'direction': trade_direction,
        'group': cargo_info.get('group', 'Unmapped'),
        'commodity': cargo_info.get('commodity', 'Unmapped'),
        'cargo': cargo_info.get('cargo', 'Unmapped'),
        'cargo_detail': cargo_info.get('cargo_detail', 'Unmapped'),
        'country': cty_name,
        'cty_code': rec['cty_code'],
        'port_code': rec['port_code'],
        'port_name': port_info.get('port_name', rec['port_code']),
        'port_consolidated': port_info.get('port_consolidated', ''),
        'ves_weight_kg': rec['ves_weight_kg'],
        'ves_value_usd': rec['ves_value_usd'],
        'hs6': hs6,
    }


enriched = []
for r in imports:
    enriched.append(enrich_record(r, 'Import'))
for r in exports:
    enriched.append(enrich_record(r, 'Export'))

print(f"\nTotal enriched records: {len(enriched):,}")

# ── Aggregate by direction, group, commodity, cargo, cargo_detail, country ──
agg = defaultdict(lambda: {'ves_mt': 0.0, 'ves_value_usd': 0, 'records': 0})

for r in enriched:
    key = (r['direction'], r['port_consolidated'], r['group'], r['commodity'], r['cargo'], r['cargo_detail'], r['country'])
    agg[key]['ves_mt'] += r['ves_weight_kg'] / 1000.0  # kg to metric tons
    agg[key]['ves_value_usd'] += r['ves_value_usd']
    agg[key]['records'] += 1

# Sort by direction then descending tonnage
rows = []
for key, vals in agg.items():
    rows.append({
        'direction': key[0],
        'port_consolidated': key[1],
        'group': key[2],
        'commodity': key[3],
        'cargo': key[4],
        'cargo_detail': key[5],
        'country': key[6],
        'ves_mt': round(vals['ves_mt'], 1),
        'ves_value_usd': vals['ves_value_usd'],
        'records': vals['records'],
    })

rows.sort(key=lambda x: (-1 if x['direction'] == 'Import' else 1, -x['ves_mt']))

# ── Write CSV ──
import csv
outpath = 'data/miss_river_annual_trade_by_cargo_country.csv'
with open(outpath, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['direction', 'port_consolidated', 'group', 'commodity', 'cargo',
                                       'cargo_detail', 'country', 'ves_mt', 'ves_value_usd', 'records'])
    w.writeheader()
    w.writerows(rows)

print(f"\nWrote {len(rows):,} aggregated rows to {outpath}")

# ── Summary tables ──
print("\n" + "=" * 100)
print("MISSISSIPPI RIVER PORTS — VESSEL TRADE JAN-NOV 2025 (YTD)")
print("=" * 100)

# By direction
for direction in ['Import', 'Export']:
    dir_rows = [r for r in rows if r['direction'] == direction]
    total_mt = sum(r['ves_mt'] for r in dir_rows)
    total_val = sum(r['ves_value_usd'] for r in dir_rows)
    print(f"\n{'='*80}")
    print(f"  {direction.upper()}S — Total: {total_mt:,.0f} MT  |  ${total_val/1e6:,.0f}M")
    print(f"{'='*80}")

    # By port consolidated
    port_agg = defaultdict(lambda: {'mt': 0.0, 'val': 0})
    for r in dir_rows:
        port_agg[r['port_consolidated']]['mt'] += r['ves_mt']
        port_agg[r['port_consolidated']]['val'] += r['ves_value_usd']
    port_sorted = sorted(port_agg.items(), key=lambda x: -x[1]['mt'])

    print(f"\n  BY PORT:")
    print(f"  {'Port':<35s} {'Metric Tons':>15s} {'Value USD':>18s}")
    print(f"  {'-'*35} {'-'*15} {'-'*18}")
    for port, vals in port_sorted:
        print(f"  {port:<35s} {vals['mt']:>15,.0f} ${vals['val']/1e6:>14,.0f}M")

    # By cargo (top 40)
    cargo_agg = defaultdict(lambda: {'mt': 0.0, 'val': 0})
    for r in dir_rows:
        cargo_agg[r['cargo']]['mt'] += r['ves_mt']
        cargo_agg[r['cargo']]['val'] += r['ves_value_usd']
    cargo_sorted = sorted(cargo_agg.items(), key=lambda x: -x[1]['mt'])

    print(f"\n  {'Cargo':<35s} {'Metric Tons':>15s} {'Value USD':>18s}")
    print(f"  {'-'*35} {'-'*15} {'-'*18}")
    for cargo, vals in cargo_sorted[:40]:
        print(f"  {cargo:<35s} {vals['mt']:>15,.0f} ${vals['val']/1e6:>14,.0f}M")

    # By group
    group_agg = defaultdict(lambda: {'mt': 0.0, 'val': 0})
    for r in dir_rows:
        group_agg[r['group']]['mt'] += r['ves_mt']
        group_agg[r['group']]['val'] += r['ves_value_usd']
    group_sorted = sorted(group_agg.items(), key=lambda x: -x[1]['mt'])

    print(f"\n  BY GROUP:")
    print(f"  {'Group':<25s} {'Metric Tons':>15s} {'Value USD':>18s}")
    print(f"  {'-'*25} {'-'*15} {'-'*18}")
    for grp, vals in group_sorted:
        print(f"  {grp:<25s} {vals['mt']:>15,.0f} ${vals['val']/1e6:>14,.0f}M")

    # Top 15 countries
    cty_agg = defaultdict(lambda: {'mt': 0.0, 'val': 0})
    for r in dir_rows:
        cty_agg[r['country']]['mt'] += r['ves_mt']
        cty_agg[r['country']]['val'] += r['ves_value_usd']
    cty_sorted = sorted(cty_agg.items(), key=lambda x: -x[1]['mt'])

    print(f"\n  TOP 20 COUNTRIES:")
    print(f"  {'Country':<40s} {'Metric Tons':>15s} {'Value USD':>18s}")
    print(f"  {'-'*40} {'-'*15} {'-'*18}")
    for cty, vals in cty_sorted[:20]:
        print(f"  {cty:<40s} {vals['mt']:>15,.0f} ${vals['val']/1e6:>14,.0f}M")

print("\nDone.")
