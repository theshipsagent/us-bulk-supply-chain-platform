"""Build unified port reference CSV.

Primary key: port_code (4-digit, zero-padded TEXT).
One row per code. Columns from each source, then our classifications.
"""
import csv
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Load Census Schedule D ──
census_sd = {}
with open('data/reference/census_schedule_d.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        census_sd[row['port_code']] = row

# ── 2. Load CBP Appendix E ──
cbp_ae = {}
with open('data/reference/cbp_appendix_e_ports.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        cbp_ae[row['port_code']] = row['cbp_port_name']

# ── 3. Load existing classifications ──
old_cl = {}
with open('data/reference/port_classifications.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        old_cl[row['port_code']] = row

# ── 4. Extract state from CBP name (full state name) or Census name (abbreviation) ──
STATE_ABBREVS = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Guam': 'GU', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Puerto Rico': 'PR',
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
    'Tennessee': 'TN', 'Texas': 'TX', 'US Virgin Islands': 'VI',
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'Washington, DC': 'DC', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
}
# Reverse: abbreviation → full state
ABBREV_TO_STATE = {v: k for k, v in STATE_ABBREVS.items()}
# Census uses 2-letter codes after comma
CENSUS_STATE_PATTERN = re.compile(r',\s*([A-Z]{2})\s*$')
# CBP uses full state names
CBP_STATE_PATTERN = re.compile(r',\s*([\w\s]+?)\s*$')

def extract_state(port_code, cbp_name, census_name):
    """Extract 2-letter state abbreviation from port name."""
    # Skip non-geographic codes
    dist = port_code[:2]
    if dist in ('60', '70', '71', '80', '92'):
        return ''
    # Preclearance ports (74, 75, 76, 77, 79) - these say "Washington, DC" but aren't in DC
    if dist in ('74', '75', '76', '77', '79'):
        return ''
    # Canadian ports
    if cbp_name and ('Canada' in cbp_name or 'Alberta' in cbp_name):
        return ''

    # Try Census name first (has clean 2-letter abbreviation)
    if census_name:
        m = CENSUS_STATE_PATTERN.search(census_name)
        if m:
            abbrev = m.group(1)
            if abbrev in ABBREV_TO_STATE:
                return abbrev
    # Try CBP name — check longest state names first to avoid partial matches
    if cbp_name:
        # Check "Washington, DC" or "District of Columbia" before "Washington"
        if 'District of Columbia' in cbp_name or cbp_name.endswith('Washington, DC'):
            return 'DC'
        for state_full, abbrev in sorted(STATE_ABBREVS.items(), key=lambda x: -len(x[0])):
            if state_full in cbp_name:
                return abbrev
    return ''


# ── 5. District defaults + port overrides (from build_port_classifications.py) ──
# Import the classification logic
district_defaults = {
    '01': {'consolidated': 'Portland ME', 'coast': 'East', 'region': 'North Atlantic'},
    '02': {'consolidated': 'Northern Border-VT', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '04': {'consolidated': 'Boston', 'coast': 'East', 'region': 'North Atlantic'},
    '05': {'consolidated': 'Providence', 'coast': 'East', 'region': 'North Atlantic'},
    '07': {'consolidated': 'Northern Border-NY', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '09': {'consolidated': 'Buffalo-Niagara', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '10': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '11': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '13': {'consolidated': 'Baltimore', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '14': {'consolidated': 'Hampton Roads', 'coast': 'East', 'region': 'South Atlantic'},
    '15': {'consolidated': 'North Carolina Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '16': {'consolidated': 'South Carolina Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '17': {'consolidated': 'Georgia Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '18': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},
    '19': {'consolidated': 'Mobile', 'coast': 'Gulf', 'region': 'Gulf East'},
    '20': {'consolidated': 'New Orleans', 'coast': 'Gulf', 'region': 'Gulf East'},
    '21': {'consolidated': 'Sabine River', 'coast': 'Gulf', 'region': 'North Texas'},
    '23': {'consolidated': 'South Texas Border', 'coast': 'Land Ports', 'region': 'South Texas'},
    '24': {'consolidated': 'El Paso Border', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '25': {'consolidated': 'San Diego Border', 'coast': 'Land Ports', 'region': 'California'},
    '26': {'consolidated': 'Arizona Border', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '27': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '28': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '29': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '30': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '31': {'consolidated': 'Alaska', 'coast': 'Alaska/US Islands', 'region': 'Alaska/US Islands'},
    '32': {'consolidated': 'Honolulu', 'coast': 'West', 'region': 'Pacific'},
    '33': {'consolidated': 'Northern Border-MT', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '34': {'consolidated': 'Northern Border-ND', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '35': {'consolidated': 'Minneapolis-St. Paul', 'coast': 'Inland', 'region': 'Great Lakes'},
    '36': {'consolidated': 'Duluth-Superior', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '37': {'consolidated': 'Milwaukee', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '38': {'consolidated': 'Detroit', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '39': {'consolidated': 'Chicago', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '41': {'consolidated': 'Cleveland-Toledo', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '45': {'consolidated': 'St. Louis', 'coast': 'Inland', 'region': 'Mississippi River'},
    '46': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '47': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '49': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},
    '51': {'consolidated': 'Virgin Islands', 'coast': 'Islands', 'region': 'Caribbean'},
    '52': {'consolidated': 'South Florida', 'coast': 'East', 'region': 'South Atlantic'},
    '53': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},
    '54': {'consolidated': 'Washington DC', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '55': {'consolidated': 'Dallas-Fort Worth', 'coast': 'Inland', 'region': 'North Texas'},
    '58': {'consolidated': 'Savannah/Wilmington', 'coast': 'East', 'region': 'South Atlantic'},
    '59': {'consolidated': 'Norfolk/Mobile/Charleston', 'coast': 'East', 'region': 'South Atlantic'},
    '60': {'consolidated': 'Vessels Under Own Power', 'coast': 'N/A', 'region': 'N/A'},
    '70': {'consolidated': 'Low Value/Estimated', 'coast': 'N/A', 'region': 'N/A'},
    '71': {'consolidated': 'Low Value/Estimated', 'coast': 'N/A', 'region': 'N/A'},
    '74': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
    '75': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
    '76': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
    '77': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
    '79': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
    '80': {'consolidated': 'Mail Shipments', 'coast': 'N/A', 'region': 'N/A'},
    '92': {'consolidated': 'Preclearance', 'coast': 'N/A', 'region': 'N/A'},
}

# ── 6. Build unified set of ALL port codes ──
all_codes = sorted(set(list(census_sd.keys()) + list(cbp_ae.keys())))
print(f"Total unique port codes (Census + CBP): {len(all_codes)}")

# ── 7. Build unified rows ──
rows = []
for code in all_codes:
    dist = code[:2]

    # Census Schedule D name
    census_name = census_sd.get(code, {}).get('port_name', '')
    census_district = census_sd.get(code, {}).get('district_name', '')

    # CBP Appendix E name
    cbp_name = cbp_ae.get(code, '')

    # State
    state = extract_state(code, cbp_name, census_name)

    # Classifications — use existing if available, else district default
    if code in old_cl:
        cl = old_cl[code]
        consolidated = cl['port_consolidated']
        coast = cl['port_coast']
        region = cl['port_region']
        port_type = cl['port_type']
    elif dist in district_defaults:
        dd = district_defaults[dist]
        consolidated = dd['consolidated']
        coast = dd['coast']
        region = dd['region']
        port_type = ''
    else:
        consolidated = ''
        coast = ''
        region = ''
        port_type = ''

    rows.append({
        'port_code': code,
        'sked_d_name': census_name,
        'cbp_appendix_e_name': cbp_name,
        'district_code': dist,
        'district_name': census_district or '',
        'state': state,
        'port_consolidated': consolidated,
        'port_coast': coast,
        'port_region': region,
        'port_type': port_type,
    })

# ── 8. Write unified reference ──
outfile = 'data/reference/port_reference.csv'
fieldnames = [
    'port_code',
    'sked_d_name',
    'cbp_appendix_e_name',
    'district_code',
    'district_name',
    'state',
    'port_consolidated',
    'port_coast',
    'port_region',
    'port_type',
]
with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Written: {outfile} ({len(rows)} rows)")

# ── 9. Verify key ports ──
print(f"\nKey port verification:")
checks = [
    ('1801', 'Tampa'),
    ('5201', 'Miami'),
    ('1901', 'Mobile'),
    ('2002', 'New Orleans'),
    ('2101', 'Port Arthur'),
    ('5203', 'Port Everglades'),
    ('4909', 'San Juan'),
]
lookup = {r['port_code']: r for r in rows}
for code, expected in checks:
    r = lookup[code]
    print(f"  {code}: sked_d='{r['sked_d_name']}'  cbp='{r['cbp_appendix_e_name']}'  "
          f"state={r['state']}  consolidated={r['port_consolidated']}")

# Stats
states_found = sum(1 for r in rows if r['state'])
print(f"\nState coverage: {states_found}/{len(rows)} ({states_found*100//len(rows)}%)")
