"""Parse Census Schedule D dist2.txt into canonical reference CSV."""
import csv
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Parse district names from DISTRICT.TXT ──
districts = {}
with open('data/extracted/EXDB2501/DISTRICT.TXT', 'r') as f:
    for line in f:
        code = line[0:2].strip()
        name = line[9:59].strip()
        if code:
            districts[code] = name

print(f"Districts loaded: {len(districts)}")

# ── 2. Parse dist2.txt ──
ports = []
with open('data/reference/dist2_raw.txt', 'r') as f:
    for line in f:
        line = line.rstrip()
        # Skip header/separator lines
        if line.startswith('---') or not line or 'Name' in line and 'Code' in line:
            continue
        if 'Source:' in line or 'This listing' in line:
            continue

        # Parse pipe-delimited format: Name | Code | District/Port
        parts = [p.strip() for p in line.split('|')]
        if len(parts) != 3:
            continue

        name, code, entry_type = parts

        if entry_type == 'Port':
            port_code = code.strip().zfill(4)
            district_code = port_code[:2]
            district_name = districts.get(district_code, 'UNKNOWN')
            ports.append({
                'port_code': port_code,
                'port_name': name.strip(),
                'district_code': district_code,
                'district_name': district_name,
            })

print(f"Port codes parsed from dist2.txt: {len(ports)}")

# ── 2b. Add supplemental codes found in trade data but not in dist2.txt ──
existing_codes = {p['port_code'] for p in ports}
supplemental = [
    ('1105', 'MARCUS HOOK, PA'),
    ('1107', 'CAMDEN, NJ'),
    ('1297', 'RICHMOND, VA'),
    ('1791', 'ATLANTA HARTSFIELD AIRPORT, GA'),
    ('3279', 'HONOLULU FTZ, HI'),
    ('3325', 'GLACIER PARK INTL AIRPORT, MT'),
    ('2707', 'PORT 2707, CA'),  # Historical LA district code
    ('6000', 'VESSELS UNDER OWN POWER'),
    ('7070', 'LOW VALUE ESTIMATED'),
    ('8000', 'MAIL SHIPMENTS'),
]
for code, name in supplemental:
    if code not in existing_codes:
        dist = code[:2]
        ports.append({
            'port_code': code,
            'port_name': name,
            'district_code': dist,
            'district_name': districts.get(dist, 'UNKNOWN'),
        })
        print(f"  + Added supplemental: {code} {name}")

print(f"Total port codes: {len(ports)}")

# ── 3. Write census_schedule_d.csv ──
outfile = 'data/reference/census_schedule_d.csv'
with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['port_code', 'port_name', 'district_code', 'district_name'])
    writer.writeheader()
    for p in sorted(ports, key=lambda x: x['port_code']):
        writer.writerow(p)

print(f"Written: {outfile} ({len(ports)} ports)")

# ── 4. Verify key ports from bug table ──
sd_lookup = {p['port_code']: p['port_name'] for p in ports}
checks = [
    ('1901', 'MOBILE'),
    ('2004', 'BATON ROUGE'),
    ('2101', 'PORT ARTHUR'),
    ('5201', 'MIAMI'),
    ('5203', 'PORT EVERGLADES'),
    ('1902', 'GULFPORT'),
    ('4909', 'SAN JUAN'),
    ('4908', 'PONCE'),
    ('5101', 'CHARLOTTE AMALIE'),
    ('2002', 'NEW ORLEANS'),
]
print("\nVerification of key port codes:")
for code, expected in checks:
    actual = sd_lookup.get(code, 'NOT FOUND')
    match = '✓' if expected.upper() in actual.upper() else '✗'
    print(f"  {match} {code}: {actual} (expected: {expected})")
