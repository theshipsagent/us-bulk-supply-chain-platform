"""Parse CBP Appendix F (Schedule K) PDF into foreign_port_reference.csv.

Source: data/reference/cbp_appendix_f_schedule_k.pdf (96 pages)
  - Pages 9-90:  Main foreign port listing (5-digit codes, alphabetical by country)
  - Pages 91-95: Canadian Customs Office Codes (4-digit, SKIPPED — different system)
  - Page 96:     Supplemental cruise ship codes (97xxx, included)

Output:
  data/reference/foreign_port_reference.csv  (one row per unique 5-digit port code)

Usage: python parse_schedule_k.py
"""
import re
import csv
import sys
import shutil
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Extract text from PDF ──
pdf = pdfplumber.open('data/reference/cbp_appendix_f_schedule_k.pdf')
print(f"Pages: {len(pdf.pages)}")

# Lines to skip (headers, footers, section markers)
SKIP_PATTERNS = [
    re.compile(r'^ACE M1 Import Manifest'),
    re.compile(r'^Schedule K Foreign Port Codes'),
    re.compile(r'^Code\s+Ports by Country'),
    re.compile(r'^Code\s+Ports by U\.S\. CMC'),
    re.compile(r'^Code\s+Canadian Customs'),
    re.compile(r'^February.*Appendix F'),
    re.compile(r'^January.*Appendix F'),
    re.compile(r'^Foreign Port Codes\s*$'),
    re.compile(r'^Supplemental Schedule K\s*$'),
    re.compile(r'^Supplemental Schedule K Codes'),
    re.compile(r'^Codes for (AMS|Cruise Ship)'),
    re.compile(r'^Note: These codes'),
    re.compile(r'^stores, the vessel'),
    re.compile(r'^Date of Change'),
    re.compile(r'^Canadian Customs Office Codes'),
    re.compile(r'^Codes are for use in Canadian'),
]

# Port code pattern: 5 digits followed by space and port name
PORT_PATTERN = re.compile(r'^(\d{5})\s+(.+?)$')

# Country header: a line that is NOT a port code, NOT a skip line, and looks like a country name
# (starts with letter, no leading digits)
COUNTRY_HEADER_PATTERN = re.compile(r'^[A-Z][A-Za-z]')

# Pages to process:
#   9-90 (0-indexed: 8-89): Main listing + supplemental AMS
#   96 (0-indexed: 95): Cruise ship codes
MAIN_PAGES = list(range(8, 90))   # pages 9-90
CRUISE_PAGE = [95]                 # page 96
# Skip pages 91-95 (0-indexed 90-94): Canadian Customs Office Codes (4-digit, different system)

ports = {}          # code -> {port_name, country, all_names}
current_country = 'Unknown'
line_count = 0

for page_idx in MAIN_PAGES + CRUISE_PAGE:
    page = pdf.pages[page_idx]
    text = page.extract_text()
    if not text:
        continue

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip known header/footer lines
        if any(p.search(line) for p in SKIP_PATTERNS):
            continue

        # Check for port code line
        m = PORT_PATTERN.match(line)
        if m:
            code = m.group(1)
            name = m.group(2).strip()
            line_count += 1

            if code not in ports:
                ports[code] = {
                    'port_code': code,
                    'port_name': name,
                    'country': current_country,
                    'all_names': [name],
                }
            else:
                ports[code]['all_names'].append(name)
                # Prefer a specific name over "All Other" catchalls
                if ports[code]['port_name'].startswith('All Other') and not name.startswith('All Other'):
                    ports[code]['port_name'] = name
            continue

        # Check for country header line
        if COUNTRY_HEADER_PATTERN.match(line):
            # Heuristic: country headers are short-ish text lines without digits at start
            # Exclude things like region headers in the Canadian section
            if len(line) < 80 and not line[0].isdigit():
                current_country = line.strip()
                continue

pdf.close()

print(f"Port entries parsed: {line_count}")
print(f"Unique port codes: {len(ports)}")

# ── 2. Cross-reference with Schedule C country codes ──
# Load country_reference.csv to map country names → cty_code
country_ref = {}
with open('data/reference/country_reference.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        # Index by lowercase name for fuzzy matching
        country_ref[row['cty_name'].lower()] = row['cty_code']

# Also build a prefix-based lookup from the Schedule K 5-digit code
# First 2-3 digits of Schedule K code often correspond to Schedule C code ranges
# E.g., Schedule K 35xxx = Brazil/Argentina area, Schedule C 35xx
def guess_cty_code_from_port_code(port_code):
    """Guess Schedule C country code from Schedule K port code prefix."""
    # Schedule K uses the same code structure as Schedule C at the country level
    # E.g., port 57001 = China → cty_code 5700
    #        port 35701 = Argentina → cty_code 3570
    #        port 12201 = Canada → cty_code 1220
    # Try 4-digit prefix first, then 3-digit, then 2-digit
    prefix4 = port_code[:4]
    prefix3 = port_code[:3]

    # Look up exact 4-char match in country reference
    if prefix4 + '0' in country_ref.values() or prefix4 in country_ref.values():
        # Check if this exact code exists as a country code
        for cty_name, cty_code in country_ref.items():
            if cty_code == prefix4:
                return cty_code
    return ''

# Build a more reliable country name → cty_code mapping
COUNTRY_NAME_TO_CODE = {}
with open('data/reference/country_reference.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        name = row['cty_name']
        code = row['cty_code']
        # Exact name
        COUNTRY_NAME_TO_CODE[name.lower()] = code
        # Common variations
        COUNTRY_NAME_TO_CODE[name.lower().replace('(', '').replace(')', '')] = code

# Manual overrides for Schedule K country names that don't match Schedule C exactly
COUNTRY_ALIASES = {
    'azores': '4710',                    # Portugal
    'bonaire, sint eustatius and saba': '2777',  # Curacao area (Netherlands Antilles)
    'bonaire, sint eustatius & saba': '2777',
    'canary islands': '4700',            # Spain
    'congo': '7630',                     # Republic of Congo (Brazzaville)
    'congo, democratic republic': '7660',
    'congo (kinshasha)': '7660',         # DRC (Kinshasa) — typo in PDF
    'cote d\'ivoire': '7480',
    'cote d\u2019ivoire': '7480',        # Right single quote variant
    'cote d\u2018ivoire': '7480',        # Left single quote variant
    'cote d\u2019lvoire': '7480',        # PDF typo: right quote + lowercase L
    'curacao': '2777',
    'east timor': '5601',                # Timor-Leste
    'england': '4120',                   # United Kingdom
    'french indian ocean areas': '7905',
    'ivory coast': '7480',               # Cote d'Ivoire
    'korea': '5800',                     # South Korea default
    'macau': '5660',
    'macao': '5660',
    'madeira islands': '4710',           # Portugal
    'micronesia': '6820',
    'netherlands antilles': '2777',      # Curacao
    'northern ireland': '4120',          # United Kingdom
    'reunion': '7904',
    'russia': '4621',
    'scotland': '4120',                  # United Kingdom
    'sint maarten': '2774',
    'st. martin': '2774',
    'taiwan': '5830',
    'wales': '4120',                     # United Kingdom
    'west bank': '5083',
    'gaza strip': '5082',
    'yugoslavia': '4801',               # Historical → Serbia
    'burma': '5460',
    'burma (myanmar)': '5460',
    'myanmar': '5460',
    'antigua': '2484',
    'trinidad': '2740',
    'trinidad and tobago': '2740',
    'barbuda': '2484',
    'nevis': '2483',
    'tobago': '2740',
    'virgin islands': '9110',
    'u.s. virgin islands': '9110',
    'us virgin islands': '9110',
    'dominican republic': '2470',
    'dom rep': '2470',
    'south korea': '5800',
    'north korea': '5790',
    'democratic republic of the congo': '7660',
    'republic of the congo': '7630',
    'congo (brazzaville)': '7630',
    'congo (kinshasa)': '7660',
    'hong kong': '5820',
    'saudi arabia': '5170',
    'united arab emirates': '5200',
    'united kingdom': '4120',
    'new zealand': '6141',
    'papua new guinea': '6040',
    'solomon islands': '6223',
    'st. helena': '7580',
    'saint helena': '7580',
    'south africa': '7910',
    'equatorial guinea': '7380',
    'sierra leone': '7470',
    'burkina faso': '7600',
    'guinea-bissau': '7642',
    'cabo verde': '7643',
    'cape verde': '7643',
    'sao tome and principe': '7644',
    'central african republic': '7540',
    'costa rica': '2230',
    'el salvador': '2110',
    'sri lanka': '5420',
    'turks and caicos islands': '2430',
    'cayman islands': '2440',
    'british virgin islands': '2482',
    'marshall islands': '6810',
    'french polynesia': '6414',
    'new caledonia': '6412',
    'wallis and futuna': '6413',
    'falkland islands': '3720',
    'french guiana': '3170',
    'french southern and antarctic lands': '7905',
    'heard island and mcdonald islands': '6029',
    'christmas island': '6024',
    'cocos islands': '6023',
    'norfolk island': '6022',
    'pitcairn islands': '6225',
    'cook islands': '6142',
    'north macedonia': '4794',
    'bosnia and herzegovina': '4793',
    'czech republic': '4351',
    'faroe islands': '4091',
    'svalbard and jan mayen': '4031',
    'saint pierre and miquelon': '1610',
    'st. pierre & miquelon': '1610',
    'dominca island': '2486',            # Dominica — typo in PDF
    'st. kitts & nevis': '2483',
    'st. lucia': '2487',
    'st. vincent & the grenadines': '2488',
    'wallis & futuna': '6413',
    'sao tome & principe': '7644',
    'french southern & antarctic lands': '7905',
    'western sahara': '7140',            # Disputed territory, near Morocco
    'china (mainland)': '5700',
    'other pacific islands n.e.c.': '6864',  # Misc Pacific → Tonga code range
    'southern asia, n.e.c.': '5330',         # Misc South Asia → India code range
    'southern pacific islands': '6864',       # Misc Pacific
    'united states off-shore tanker transshipment points': '',  # No country code
    'united states outlying islands': '9800',
}

def lookup_cty_code(country_name):
    """Look up Schedule C country code from a country name string."""
    name = country_name.strip().lower()

    # Direct match
    if name in COUNTRY_NAME_TO_CODE:
        return COUNTRY_NAME_TO_CODE[name]

    # Alias match
    if name in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[name]

    # Try partial match (country name contained in reference)
    for ref_name, code in COUNTRY_NAME_TO_CODE.items():
        if name in ref_name or ref_name in name:
            return code

    return ''


# Assign cty_code to each port
matched = 0
unmatched_countries = set()
for code, port in ports.items():
    cty_code = lookup_cty_code(port['country'])
    port['cty_code'] = cty_code
    if cty_code:
        matched += 1
    else:
        unmatched_countries.add(port['country'])

print(f"\nCountry code matching:")
print(f"  Matched:   {matched}")
print(f"  Unmatched: {len(ports) - matched}")
if unmatched_countries:
    print(f"  Unmatched country names ({len(unmatched_countries)}):")
    for name in sorted(unmatched_countries):
        count = sum(1 for p in ports.values() if p['country'] == name)
        print(f"    '{name}' ({count} ports)")

# ── 3. Assign region from country_reference ──
region_lookup = {}
with open('data/reference/country_reference.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        region_lookup[row['cty_code']] = row['region']

for port in ports.values():
    port['region'] = region_lookup.get(port['cty_code'], '')

# ── 4. Write foreign_port_reference.csv ──
outfile = 'data/reference/foreign_port_reference.csv'
fieldnames = ['port_code', 'port_name', 'country', 'cty_code', 'region']

rows = sorted(ports.values(), key=lambda r: r['port_code'])
with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"\nWritten: {outfile} ({len(rows)} unique port codes)")

# ── 5. Copy to project_manifest ──
manifest_path = 'G:/My Drive/LLM/project_manifest/DICTIONARIES/foreign_port_reference.csv'
shutil.copy2(outfile, manifest_path)
print(f"Copied to: {manifest_path}")

# ── 6. Summary statistics ──
from collections import Counter
region_counts = Counter(p['region'] for p in ports.values() if p['region'])
print(f"\nRegion breakdown (top 15):")
for region, count in region_counts.most_common(15):
    print(f"  {region:25s}: {count}")

country_counts = Counter(p['country'] for p in ports.values())
print(f"\nCountries with most ports (top 15):")
for country, count in country_counts.most_common(15):
    print(f"  {country:30s}: {count}")

print(f"\nFirst 10 entries:")
for r in rows[:10]:
    print(f"  {r['port_code']} | {r.get('cty_code',''):4s} | {r['port_name'][:40]:40s} | {r['country']}")

print(f"\nLast 10 entries:")
for r in rows[-10:]:
    print(f"  {r['port_code']} | {r.get('cty_code',''):4s} | {r['port_name'][:40]:40s} | {r['country']}")
