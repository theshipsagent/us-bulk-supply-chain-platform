"""Fix ports_master.csv — pull classifications from port_reference.csv (single source of truth)."""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

MANIFEST_PATH = "G:/My Drive/LLM/project_manifest/DICTIONARIES/ports_master.csv"
PORT_REF_PATH = "data/reference/port_reference.csv"

# ── 1. Load unified port reference ──
port_ref = {}
with open(PORT_REF_PATH, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        port_ref[row['port_code']] = row

print(f"Port reference: {len(port_ref)} ports")

# ── 2. Load current ports_master ──
rows = []
with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"ports_master.csv: {len(rows)} rows")

# ── 3. Define port code fixes (from bug table) ──
# Key: Panjiva discharge text substring → correct port code
port_code_fixes = {
    'Alabama State Port Authority, Mobile': '1901',           # Was 2002
    'Baton Rouge (BTR) Airport, Baton Rouge': '2004',         # Was 2002
    'Port Arthur, Texas': '2101',                              # Was 5301
    'Port Of Entry-Miami Seaport, Miami': '5201',             # Was 1801
    'Port Of Entry-Port Everglades/Fort Lauderdale': '5203',  # Was 1801
    'Mississippi State Port Authority, Gulfport': '1902',     # Was 2002
    'San Juan, San Juan, Puerto Rico': '4909',                # Was 5501
    'Ponce, Ponce, Puerto Rico': '4908',                      # Was 5501
    'Cyril E King Airport, Charlotte Amalie': '5101',         # Was 5501
    'Cruz Bay, Virgin Islands': '5102',                        # Was 5501 (Cruz Bay is VI, not Dallas)
}

# Additional code fixes found by auditing against Schedule D:
additional_fixes = {
    # Port of Virginia Norfolk is district 14, code 1401 (not 1501 which is Wilmington NC)
    'Port of Virginia, Norfolk': '1401',
    # Port of Vancouver USA is 2908 (Vancouver WA), not 3001 (Seattle)
    'Port of Vancouver USA, Vancouver': '2908',
    # Port of New Haven is 0412, correct
    # Port Canaveral is 1816, not 1801 (Tampa)
    'Port Canaveral, Port Canaveral': '1816',
    # Port Manatee is 1821, not 1801 (Tampa)
    'Port Manatee, Florida': '1821',
    # Greater Orlando is 1808, not 1801
    'Greater Orlando Aviation Authority, Orlando': '1808',
    # Port Lavaca is 5313, not 5301 (Houston)
    'Port Lavaca, Port Lavaca, Texas': '5313',
    # Houston Intercontinental Airport is 5309, not 5301
    'Houston Intercontinental Airport, Houston': '5309',
    # Port Hueneme is 2713, not 2704 (LA)
    'Port Hueneme, California': '2713',
    # Port of Stockton is 2810, not 2804
    'Port of Stockton, Stockton': '2810',
    # ProvPort Providence is 0502 not 0601
    'ProvPort, Providence': '0502',
    # Beaufort-Morehead City is 1511, not 1001
    'Port Of Entry-Morehead City': '1511',
    # Buffalo-Niagara Falls is 0901, not 1001
    'Buffalo': '0901',
    # Erie is 4106, not 1001
    'Erie-Western Pennsylvania Port Authority, Erie': '4106',
    # Richmond VA is 1404, not 1001
    'Port of Richmond, Richmond‑Petersburg, Virginia': '1404',
    # South Jersey/Camden NJ is 1107, not 1001
    'South Jersey Port Corporation, Camden': '1107',
    # Atlanta is 1704, not 1001 (though we also accept 1791 for airport)
    'Service Port-Atlanta, Atlanta': '1704',
    # Memphis is 2006, not 1001
    'The International Port of Memphis, Memphis': '2006',
    # Phoenix is 2605, not 1001
    'Service Port-Phoenix, Phoenix': '2605',
    # Eastport ME is 0103, not 1001
    'Eastport Port Authority, Eastport, Maine': '0103',
    # Salem MA is 0408, not 1001
    'Salem, Massachusetts': '0408',
    # Massena is 0704, not 1001
    'Massena International Airport, Massena': '0704',
    # UPS Newark is 1069 (UPS NJ), not 1001
    'UPS, Newark, New Jersey': '1069',
    # New York/Newark Area — 4601 not in Schedule D, use 1003 (Newark NJ)
    'New York/Newark Area, Newark': '1003',
    # Perth Amboy NJ — 4602 not in Schedule D, use 1004 (Perth Amboy NJ)
    'Port Of Entry-Perth Amboy, Perth Amboy': '1004',
    # South Jersey/Camden NJ — 1107 not in Schedule D, use 1113 (Gloucester City NJ, same area)
    'South Jersey Port Corporation, Camden': '1113',
    # Port Huron is 3802, not 3801
    'Port Huron, Port Huron': '3802',
    # Sault Ste Marie is 3803, not 3801
    'Sault Ste. Marie': '3803',
    # Toledo is 4105, not 3801
    'Toledo-Lucas Port Authority, Toledo': '4105',
    # Milwaukee is 3701, not 3801
    'THE PORT OF MILWAUKEE, Milwaukee': '3701',
    # Duluth is 3510, not 3801
    'Duluth Seaway Port Authority, Duluth': '3510',
    # Minneapolis airport is 3501, not 3801
    'Minneapolis St.Paul International Airport': '3501',
    # Illinois International Port District, Chicago is 3901, not 3801
    'Illinois International Port District, Chicago': '3901',
    # Saginaw/Bay City is 3804, not 3801
    'Saginaw-Bay City-Flint': '3804',
    # Rogers City is 3818, not 3801
    'Rogers City Harbor': '3818',
    # Delta County Airport/Escanaba is 3808, not 3801
    'Delta County Airport, Escanaba': '3808',
    # Newport RI is 0501, correct
    # Nawiliwili is 3204, not 3201
    'Port Of Entry-Nawiliwili': '3204',
    # Port Angeles WA is 3007, not 3001
    'Port Angeles, Washington': '3007',
    # Coos Bay OR is 2903, not 3001
    'Oregon International Port of Coos Bay': '2903',
    # Blaine WA is 3004, not 3001
    'Service Port-Blaine, Blaine': '3004',
    # Everett is 3006, not 3010
    'Port of Everett, Everett': '3006',
    # San Francisco International Airport is 2801, already correct
    # Fajardo PR is 4904, not 4904 — wait, check coast classification
    # Mayaguez PR is 4907, coast should be Islands/Caribbean
    # Hilo is 3202, coast should be changed
    # Kahului is 3203, coast should be changed
}

# Merge all fixes
all_fixes = {**port_code_fixes, **additional_fixes}

# ── 4. Apply fixes ──
fix_count = 0
code_changes = []

for row in rows:
    discharge = row['Port of Discharge (D)']
    old_code = str(row['Port_Code']).strip()

    # Check for port code fix
    new_code = None
    for search_text, correct_code in all_fixes.items():
        if search_text in discharge:
            if old_code != correct_code:
                new_code = correct_code
                code_changes.append(f"  {discharge[:60]:60s} {old_code} → {new_code}")
                fix_count += 1
            break

    if new_code:
        row['Port_Code'] = new_code

    # Ensure port code is clean
    code = str(row['Port_Code']).strip().zfill(4)
    row['Port_Code'] = code

    # Look up classification from unified port reference
    if code in port_ref:
        ref = port_ref[code]
        row['Port_Consolidated'] = ref['port_consolidated']
        row['Port_Coast'] = ref['port_coast']
        row['Port_Region'] = ref['port_region']
    else:
        # Leave existing values but warn
        print(f"  WARNING: Port_Code {code} not in port reference: {discharge[:50]}")

print(f"\nPort code fixes applied: {fix_count}")
for change in sorted(code_changes):
    print(change)

# ── 5. Fix text quality issues ──
typo_fixes = 0
for row in rows:
    # Fix "San Franciso" typo
    if 'San Franciso' in str(row.get('Port_Consolidated', '')):
        row['Port_Consolidated'] = row['Port_Consolidated'].replace('San Franciso', 'San Francisco Bay')
        typo_fixes += 1

    # Fix "Land  Ports" double-space
    if 'Land  Ports' in str(row.get('Port_Coast', '')):
        row['Port_Coast'] = row['Port_Coast'].replace('Land  Ports', 'Land Ports')
        typo_fixes += 1
    if 'Land  Ports' in str(row.get('Port_Region', '')):
        row['Port_Region'] = row['Port_Region'].replace('Land  Ports', 'Land Ports')
        typo_fixes += 1

    # Fix trailing spaces
    for field in ['Port_Consolidated', 'Port_Coast', 'Port_Region']:
        if field in row and row[field]:
            row[field] = row[field].strip()

print(f"Text quality fixes: {typo_fixes}")

# ── 6. Validate all Port_Codes exist in port reference ──
orphans = []
for row in rows:
    code = str(row['Port_Code']).strip().zfill(4)
    if code not in port_ref:
        orphans.append(f"  {code}: {row['Port of Discharge (D)'][:50]}")

if orphans:
    print(f"\nWARNING: {len(orphans)} Port_Codes not in port reference:")
    for o in orphans:
        print(o)
else:
    print(f"\n✓ All Port_Codes validated against port_reference.csv")

# ── 7. Write fixed ports_master.csv ──
fieldnames = ['Port of Discharge (D)', 'Port_Code', 'Port_Consolidated', 'Port_Coast', 'Port_Region']
with open(MANIFEST_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in fieldnames})

print(f"\n✓ Written: {MANIFEST_PATH} ({len(rows)} rows)")

# ── 8. Verify the specific bugs from the plan ──
print("\n" + "="*70)
print("VERIFICATION OF CONFIRMED BUGS:")
print("="*70)
bug_checks = [
    ('Alabama State Port Authority, Mobile', '1901', 'Mobile'),
    ('Baton Rouge (BTR) Airport', '2004', 'Mississippi River'),
    ('Port Arthur, Texas', '2101', 'Sabine River'),
    ('Port Of Entry-Miami Seaport', '5201', 'South Florida'),
    ('Port Everglades/Fort Lauderdale', '5203', 'South Florida'),
    ('Mississippi State Port Authority, Gulfport', '1902', 'Gulfport'),
    ('San Juan, San Juan, Puerto Rico', '4909', 'San Juan'),
    ('Ponce, Ponce, Puerto Rico', '4908', 'Ponce'),
    ('Cyril E King Airport, Charlotte Amalie', '5101', 'Virgin Islands'),
]
for search, expected_code, expected_consol in bug_checks:
    found = False
    for row in rows:
        if search in row['Port of Discharge (D)']:
            code_ok = row['Port_Code'] == expected_code
            consol_ok = row['Port_Consolidated'] == expected_consol
            status = '✓' if (code_ok and consol_ok) else '✗'
            print(f"  {status} {search[:50]:50s} code={row['Port_Code']} consol={row['Port_Consolidated']}")
            found = True
            break
    if not found:
        print(f"  ? {search[:50]:50s} NOT FOUND IN ports_master")
