"""Fix zero-padding stripped by Excel, then re-sort by port_code.

RUN THIS after every manual edit to port_reference.csv.
  1. Re-pads port_code to 4 digits, district_code to 2 digits
  2. Strips trailing spaces from classification fields
  3. Sorts by port_code
  4. Writes back to data/reference/port_reference.csv
  5. Copies identical file to project_manifest/DICTIONARIES/port_reference.csv
  6. Verifies all padding is correct

Usage: python fix_zero_padding.py
"""
import csv
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

REF_PATH = 'data/reference/port_reference.csv'
MANIFEST_PATH = 'G:/My Drive/LLM/project_manifest/DICTIONARIES/port_reference.csv'

# ── 1. Read the user-edited file ──
rows = []
with open(REF_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        rows.append(row)

print(f"Read {len(rows)} rows")

# ── 2. Fix zero-padding ──
pad_fixes = 0
for row in rows:
    # port_code: always 4 digits
    old_pc = row['port_code']
    row['port_code'] = str(old_pc).strip().zfill(4)
    if old_pc != row['port_code']:
        pad_fixes += 1

    # district_code: always 2 digits
    old_dc = row['district_code']
    if old_dc:
        row['district_code'] = str(old_dc).strip().zfill(2)

print(f"Zero-padding fixes: {pad_fixes}")

# ── 3. Verify no duplicates ──
codes = [r['port_code'] for r in rows]
dupes = [c for c in set(codes) if codes.count(c) > 1]
if dupes:
    print(f"WARNING: Duplicate port_codes: {sorted(dupes)}")
else:
    print(f"No duplicate port_codes")

# ── 4. Sort by port_code ──
rows.sort(key=lambda r: r['port_code'])

# ── 5. Strip trailing spaces from consolidated names ──
for row in rows:
    for field in ['port_consolidated', 'port_coast', 'port_region']:
        if row.get(field):
            row[field] = row[field].strip()

# ── 6. Write back ──
with open(REF_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Written: {REF_PATH} ({len(rows)} rows, sorted by port_code)")

# ── 7. Copy to project_manifest ──
shutil.copy2(REF_PATH, MANIFEST_PATH)
print(f"Copied to: {MANIFEST_PATH}")

# ── 8. Verify padding ──
with open(REF_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    bad = []
    for row in reader:
        if len(row['port_code']) != 4:
            bad.append(row['port_code'])
        if row['district_code'] and len(row['district_code']) != 2:
            bad.append(f"district:{row['district_code']}")

if bad:
    print(f"STILL BAD: {bad[:10]}")
else:
    print(f"All port_codes are 4-digit, all district_codes are 2-digit")

# ── 9. Show first 10 and some key ports ──
with open(REF_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

print(f"\nFirst 5 rows:")
for r in all_rows[:5]:
    print(f"  {r['port_code']} | {r['district_code']} | {r['sked_d_name'][:30]} | {r['port_type']}")

print(f"\nKey ports:")
for code in ['0101', '0501', '0701', '1801', '1901', '2002', '5201']:
    matches = [r for r in all_rows if r['port_code'] == code]
    if matches:
        r = matches[0]
        print(f"  {r['port_code']} | {r['district_code']} | {r['sked_d_name'][:30]:30s} | {r['port_consolidated']}")
