"""Parse Census Schedule C country sources into canonical country_reference.csv.

Sources:
  1. data/extracted/EXDB2501/COUNTRY.TXT  (fixed-width, 238 entries, has 7-char abbreviation)
  2. data/reference/country3_raw.txt      (CSV from census.gov, 244 entries, has ISO codes)

Output:
  data/reference/country_reference.csv   (merged, ~249 country codes)

Usage: python parse_schedule_c.py
"""
import csv
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Parse COUNTRY.TXT (fixed-width: 0:4=code, 4:11=abbrev, 11:61=name) ──
country_txt = {}
with open('data/extracted/EXDB2501/COUNTRY.TXT', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip()
        if len(line) < 15:
            continue
        code = line[0:4].strip()
        abbrev = line[4:11].strip()
        name = line[11:61].strip()
        if code and code.isdigit():
            country_txt[code] = {'cty_abbrev': abbrev, 'cty_name_txt': name}

print(f"COUNTRY.TXT entries: {len(country_txt)}")

# ── 2. Parse country3.txt (CSV: Code, Name, ISO Code) ──
country3 = {}
with open('data/reference/country3_raw.txt', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) != 3:
            continue
        code, name, iso = row[0].strip(), row[1].strip(), row[2].strip()
        if not code.isdigit() or len(code) != 4:
            continue
        country3[code] = {'cty_name_c3': name, 'iso_alpha2': iso}

print(f"country3.txt entries: {len(country3)}")

# ── 3. Merge into unified list ──
all_codes = sorted(set(list(country_txt.keys()) + list(country3.keys())))
print(f"Union of all codes: {len(all_codes)}")

# Show differences
only_txt = set(country_txt.keys()) - set(country3.keys())
only_c3 = set(country3.keys()) - set(country_txt.keys())
if only_txt:
    print(f"  Only in COUNTRY.TXT ({len(only_txt)}):")
    for c in sorted(only_txt):
        print(f"    {c}: {country_txt[c]['cty_name_txt']}")
if only_c3:
    print(f"  Only in country3.txt ({len(only_c3)}):")
    for c in sorted(only_c3):
        print(f"    {c}: {country3[c]['cty_name_c3']}")

# ── 4. Region / sub_region classification based on code ranges ──
def classify_country(code):
    """Assign region and sub_region based on Census Schedule C code ranges."""
    n = int(code)

    # North America (1000-1999)
    if 1000 <= n <= 1999:
        if code == '1000':
            return 'North America', 'United States'
        if code == '1010':
            return 'North America', 'Greenland'
        if code == '1220':
            return 'North America', 'Canada'
        return 'North America', 'North America Other'

    # Central America (2010-2250)
    if code in ('2010', '2050', '2080', '2110', '2150', '2190', '2230', '2250'):
        return 'Central America', 'Central America'

    # Caribbean (2320-2899)
    if 2300 <= n <= 2899:
        return 'Caribbean', 'Caribbean'

    # South America (3000-3799)
    if 3000 <= n <= 3799:
        if code in ('3510',):
            return 'South America', 'Brazil'
        if code in ('3570',):
            return 'South America', 'Southern Cone'
        if code in ('3530', '3550'):
            return 'South America', 'Southern Cone'
        if code in ('3310', '3330', '3350'):
            return 'South America', 'Andean'
        if code in ('3010', '3070'):
            return 'South America', 'Northern South America'
        if code in ('3120', '3150', '3170'):
            return 'South America', 'Guianas'
        return 'South America', 'South America Other'

    # Europe (4000-4999)
    if 4000 <= n <= 4999:
        # Nordic
        if code in ('4000', '4010', '4031', '4039', '4050', '4091', '4099'):
            return 'Europe', 'Nordic'
        # Western Europe
        if code in ('4120', '4190', '4210', '4231', '4239', '4271', '4272', '4279',
                     '4280', '4330', '4411', '4419'):
            return 'Europe', 'Western Europe'
        # Southern Europe
        if code in ('4700', '4710', '4720', '4730', '4751', '4752', '4759',
                     '4791', '4792', '4810', '4840', '4910'):
            return 'Europe', 'Southern Europe'
        # Central Europe
        if code in ('4351', '4359', '4370', '4550'):
            return 'Europe', 'Central Europe'
        # Balkans
        if code in ('4793', '4794', '4801', '4803', '4804', '4850', '4870', '4890'):
            return 'Europe', 'Balkans'
        # Baltic
        if code in ('4470', '4490', '4510'):
            return 'Europe', 'Baltic'
        # Former Soviet / Eastern Europe
        if code in ('4621', '4622', '4623', '4631', '4632', '4633',
                     '4634', '4635', '4641', '4642', '4643', '4644'):
            return 'Europe', 'Eastern Europe & Central Asia'
        return 'Europe', 'Europe Other'

    # Middle East (5000-5299)
    if 5000 <= n <= 5299:
        if code in ('5081', '5082', '5083'):
            return 'Middle East', 'Israel & Territories'
        if code in ('5130', '5170', '5180', '5200', '5230', '5250'):
            return 'Middle East', 'Gulf States'
        return 'Middle East', 'Middle East Other'

    # Asia (5300-5899)
    if 5300 <= n <= 5899:
        # South Asia
        if code in ('5310', '5330', '5350', '5360', '5380', '5420', '5682', '5683'):
            return 'Asia', 'South Asia'
        # Southeast Asia
        if code in ('5460', '5490', '5520', '5530', '5550', '5570', '5590',
                     '5600', '5601', '5610', '5650'):
            return 'Asia', 'Southeast Asia'
        # East Asia
        if code in ('5660', '5700', '5740', '5790', '5800', '5820', '5830', '5880'):
            return 'Asia', 'East Asia'
        return 'Asia', 'Asia Other'

    # Oceania (6000-6899)
    if 6000 <= n <= 6899:
        if code in ('6021', '6022', '6023', '6024', '6029'):
            return 'Oceania', 'Australia'
        if code in ('6141', '6142', '6143', '6144'):
            return 'Oceania', 'New Zealand'
        if code == '6040':
            return 'Oceania', 'Melanesia'
        if code in ('6223', '6224', '6412'):
            return 'Oceania', 'Melanesia'
        if code in ('6150', '6225', '6226', '6227', '6413', '6414',
                     '6810', '6820', '6830', '6862', '6863', '6864'):
            return 'Oceania', 'Pacific Islands'
        return 'Oceania', 'Oceania Other'

    # Africa (7000-7999)
    if 7000 <= n <= 7999:
        # North Africa
        if code in ('7140', '7210', '7230', '7250', '7290', '7321', '7323'):
            return 'Africa', 'North Africa'
        # West Africa
        if code in ('7410', '7420', '7440', '7450', '7460', '7470', '7480', '7490',
                     '7500', '7510', '7520', '7530', '7540', '7550', '7560', '7580',
                     '7600', '7610', '7642', '7643', '7644', '7650', '7380'):
            return 'Africa', 'West Africa'
        # Central Africa
        if code in ('7620', '7630', '7660', '7670', '7690'):
            return 'Africa', 'Central Africa'
        # East Africa
        if code in ('7700', '7741', '7749', '7770', '7780', '7790', '7800',
                     '7810', '7830', '7881', '7890', '7904', '7905'):
            return 'Africa', 'East Africa'
        # Southern Africa
        if code in ('7850', '7870', '7880', '7910', '7920', '7930',
                     '7940', '7950', '7960', '7970', '7990'):
            return 'Africa', 'Southern Africa'
        return 'Africa', 'Africa Other'

    # Special (8000-8999)
    if 8000 <= n <= 8999:
        return 'Special', 'Special'

    # US Territories (9000-9999)
    if 9000 <= n <= 9999:
        return 'US Territories', 'US Territories'

    return 'Unknown', 'Unknown'


# ── 5. Build merged rows ──
rows = []
for code in all_codes:
    txt = country_txt.get(code, {})
    c3 = country3.get(code, {})

    # Prefer country3 name (cleaner formatting), fall back to COUNTRY.TXT
    cty_name = c3.get('cty_name_c3', '') or txt.get('cty_name_txt', '')
    cty_abbrev = txt.get('cty_abbrev', '')
    iso_alpha2 = c3.get('iso_alpha2', '')

    region, sub_region = classify_country(code)

    rows.append({
        'cty_code': code,
        'cty_name': cty_name,
        'cty_abbrev': cty_abbrev,
        'iso_alpha2': iso_alpha2,
        'region': region,
        'sub_region': sub_region,
    })

# ── 6. Write country_reference.csv ──
outfile = 'data/reference/country_reference.csv'
fieldnames = ['cty_code', 'cty_name', 'cty_abbrev', 'iso_alpha2', 'region', 'sub_region']

with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"\nWritten: {outfile} ({len(rows)} countries)")

# ── 7. Copy to project_manifest ──
manifest_path = 'G:/My Drive/LLM/project_manifest/DICTIONARIES/country_reference.csv'
shutil.copy2(outfile, manifest_path)
print(f"Copied to: {manifest_path}")

# ── 8. Show summary by region ──
from collections import Counter
region_counts = Counter(r['region'] for r in rows)
print(f"\nRegion breakdown:")
for region, count in sorted(region_counts.items()):
    print(f"  {region:25s}: {count}")

# ── 9. Show first 10 and last 10 ──
print(f"\nFirst 10 entries:")
for r in rows[:10]:
    print(f"  {r['cty_code']} | {r['iso_alpha2']:2s} | {r['cty_name'][:40]:40s} | {r['region']:20s} | {r['sub_region']}")

print(f"\nLast 10 entries:")
for r in rows[-10:]:
    print(f"  {r['cty_code']} | {r['iso_alpha2']:2s} | {r['cty_name'][:40]:40s} | {r['region']:20s} | {r['sub_region']}")

# ── 10. Validate against trade data ──
print(f"\n{'='*60}")
print("VALIDATION: Check cty_codes against COUNTRY.TXT")
print(f"{'='*60}")

missing_from_ref = []
for code in country_txt:
    if code not in {r['cty_code'] for r in rows}:
        missing_from_ref.append(code)

if missing_from_ref:
    print(f"  FAIL: {len(missing_from_ref)} COUNTRY.TXT codes missing from reference:")
    for c in sorted(missing_from_ref):
        print(f"    {c}: {country_txt[c]['cty_name_txt']}")
else:
    print(f"  PASS: All {len(country_txt)} COUNTRY.TXT codes present in reference")

# Check ISO coverage
no_iso = [r for r in rows if not r['iso_alpha2'] and r['region'] != 'Special']
if no_iso:
    print(f"\n  Countries without ISO code ({len(no_iso)}):")
    for r in no_iso:
        print(f"    {r['cty_code']}: {r['cty_name']} [{r['region']}]")
else:
    print(f"  PASS: All non-special countries have ISO codes")

# Validate against EXP_CTY.TXT if available
import os
exp_cty_path = 'data/extracted/EXDB2501/EXP_CTY.TXT'
if os.path.exists(exp_cty_path):
    ref_codes = {r['cty_code'] for r in rows}
    trade_codes = set()
    with open(exp_cty_path, 'r', encoding='utf-8') as f:
        for line in f:
            if len(line) >= 4:
                trade_codes.add(line[0:4].strip())
    orphans = trade_codes - ref_codes
    print(f"\n  EXP_CTY.TXT validation:")
    print(f"    Trade codes found: {len(trade_codes)}")
    print(f"    Orphan codes (in trade but not in reference): {len(orphans)}")
    if orphans:
        for c in sorted(orphans):
            print(f"      {c}")
    else:
        print(f"    PASS: Zero orphan country codes")
