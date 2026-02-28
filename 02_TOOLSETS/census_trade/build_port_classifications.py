"""Build port_classifications.csv — classify every Census Schedule D port code."""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Load census_schedule_d.csv ──
schedule_d = {}
with open('data/reference/census_schedule_d.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        schedule_d[row['port_code']] = row

print(f"Schedule D loaded: {len(schedule_d)} ports")

# ── 2. Port type classifier ──
def classify_port_type(port_code, port_name):
    name = (port_name or '').upper()
    code = port_code

    # Administrative/special codes
    if code.startswith('70') or code.startswith('80') or code == '6000':
        return 'administrative'
    if 'VESSELS UNDER' in name:
        return 'administrative'

    # Courier hubs
    if any(x in name for x in ['FEDEX', 'UPS', 'DHL', 'TNT', 'EMERY', 'AIRBORNE',
                                 'IBC COURIER', 'IBC PACIFIC', 'NYACC', 'AVION BROKERS',
                                 'AIRCARGO', 'AIR FRANCE']):
        return 'courier'

    # FTZ
    if any(x in name for x in ['FTZ', 'FOREIGN TRADE ZONE']):
        return 'ftz'

    # Airports
    if any(x in name for x in ['AIRPORT', 'AIRP', 'FIELD', 'AIR ', ' ARPT',
                                 'IAH ', 'JFK', 'LAX', 'SFO', 'BWI',
                                 'INTL AIR', 'LOVE FIELD',
                                 'MIDWAY', 'EXECUTIVE AIRPORT']):
        return 'airport'

    # Land border crossings — based on district or known border ports
    land_border_districts = {'02', '07', '23', '24', '25', '26', '33', '34'}
    land_border_ports = {
        '0206', '0207', '0209', '0211', '0212', '0203',  # VT border
        '0712', '0714', '0715', '0704', '0708',  # NY border
        '2301', '2302', '2303', '2304', '2305', '2307', '2309', '2310',  # TX-MX border
        '2401', '2402', '2403', '2404', '2406', '2408',  # El Paso area
        '2501', '2502', '2503', '2504', '2505', '2506', '2507',  # San Diego area
        '2601', '2602', '2603', '2604', '2605', '2606', '2608', '2609',  # AZ border
        '3004', '3005', '3009', '3011', '3012', '3015', '3016', '3019', '3020', '3023',  # WA border
        '3104', '3106',  # AK border
        '3301', '3302', '3303', '3304', '3305', '3306', '3307', '3308', '3309', '3310',
        '3316', '3317', '3318', '3319', '3321', '3322', '3323',  # MT border
        '3401', '3403', '3404', '3405', '3406', '3407', '3408', '3409', '3410',
        '3411', '3413', '3414', '3415', '3416', '3417', '3419', '3420', '3421',
        '3422', '3423', '3424', '3425', '3426', '3427', '3430', '3434',  # ND/MN border
        '3604', '3613',  # MN border
        '3802', '3803', '3814', '3819',  # MI border
        '0901',  # Buffalo
    }
    # Inland cities that are NOT border crossings even if in border districts
    inland_exceptions = {
        '2605', '2609',  # Phoenix, Tucson — inland airports
        '3303', '3307',  # Salt Lake, Denver — inland cities
        '3411',  # Fargo — inland city
        '3501', '3502', '3510', '3512', '3513',  # Minneapolis, Sioux Falls, Duluth, Omaha, Des Moines
    }

    if code in land_border_ports and code not in inland_exceptions:
        return 'land_border'

    # Inland ports
    inland_codes = {
        '1904', '1910',  # Birmingham, Huntsville (AL inland)
        '2003',  # Little Rock
        '2006', '2007', '2008', '2016', '2027',  # Memphis, Nashville, Chattanooga, Knoxville, Tri-Cities
        '2018',  # Shreveport
        '2011', '2015',  # Greenville MS, Vicksburg
        '2722',  # Las Vegas
        '2833',  # Reno
        '2803',  # Fresno
        '3307',  # Denver
        '3411',  # Fargo
        '3501', '3502', '3512', '3513',  # Minneapolis, Sioux Falls, Omaha, Des Moines
        '3806', '3805', '3881',  # Grand Rapids, Battle Creek, Oakland/Pontiac
        '3902', '3908', '3909',  # Peoria, Davenport, Rockford
        '4101', '4102', '4103', '4104', '4110', '4115', '4116',  # OH/IN/KY inland
        '4501', '4502', '4503', '4504', '4505',  # MO/KS
        '5401', '5402',  # Washington DC
        '5501', '5502', '5503', '5504', '5505', '5506', '5507',  # TX/OK inland
        '1109',  # Harrisburg
        '1104',  # Pittsburgh
        '1106',  # Wilkes-Barre
        '1409', '1410',  # Charleston WV, Front Royal VA
        '1404',  # Richmond VA
        '1503', '1512',  # Durham, Charlotte NC
        '1604',  # Columbia SC
        '1704', '1791',  # Atlanta
        '1808', '1814',  # Orlando, St. Petersburg
        '2605', '2609',  # Phoenix, Tucson
        '3303',  # Salt Lake City
    }
    if code in inland_codes:
        return 'inland'

    # Default: seaport
    return 'seaport'


# ── 3. District → default classification ──
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
    '80': {'consolidated': 'Mail Shipments', 'coast': 'N/A', 'region': 'N/A'},
}

# ── 4. Port-level overrides (specific ports that differ from district default) ──
port_overrides = {
    # Mississippi River system (district 20 but specific consolidated groups)
    '2001': {'consolidated': 'Mississippi River', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2002': {'consolidated': 'New Orleans', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2003': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2004': {'consolidated': 'Mississippi River', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2006': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2007': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2008': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2010': {'consolidated': 'Mississippi River', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2011': {'consolidated': 'Mississippi River', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2015': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2016': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},
    '2017': {'consolidated': 'Lake Charles', 'coast': 'Gulf', 'region': 'Gulf East'},
    '2018': {'consolidated': 'Mississippi River', 'coast': 'Inland', 'region': 'Mississippi River'},

    # Mobile district 19 — specific ports
    '1901': {'consolidated': 'Mobile', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1902': {'consolidated': 'Gulfport', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1903': {'consolidated': 'Pascagoula', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1904': {'consolidated': 'Mobile', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1910': {'consolidated': 'Mobile', 'coast': 'Gulf', 'region': 'Gulf East'},

    # Tampa district 18 — specific ports
    '1801': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1803': {'consolidated': 'Jacksonville', 'coast': 'East', 'region': 'South Atlantic'},
    '1805': {'consolidated': 'Jacksonville', 'coast': 'East', 'region': 'South Atlantic'},
    '1807': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1808': {'consolidated': 'Orlando', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1809': {'consolidated': 'Orlando', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1814': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1816': {'consolidated': 'Port Canaveral', 'coast': 'East', 'region': 'South Atlantic'},
    '1818': {'consolidated': 'Panama City', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1819': {'consolidated': 'Pensacola', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1821': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},
    '1822': {'consolidated': 'Tampa', 'coast': 'Gulf', 'region': 'Gulf East'},

    # South Florida district 52
    '5201': {'consolidated': 'Miami', 'coast': 'East', 'region': 'South Atlantic'},
    '5202': {'consolidated': 'Key West', 'coast': 'East', 'region': 'South Atlantic'},
    '5203': {'consolidated': 'Port Everglades', 'coast': 'East', 'region': 'South Atlantic'},
    '5204': {'consolidated': 'South Florida', 'coast': 'East', 'region': 'South Atlantic'},
    '5205': {'consolidated': 'South Florida', 'coast': 'East', 'region': 'South Atlantic'},
    '5206': {'consolidated': 'Miami', 'coast': 'East', 'region': 'South Atlantic'},
    '5210': {'consolidated': 'Port Everglades', 'coast': 'East', 'region': 'South Atlantic'},

    # Houston district 53
    '5301': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},
    '5306': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},
    '5309': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},
    '5310': {'consolidated': 'Galveston', 'coast': 'Gulf', 'region': 'North Texas'},
    '5311': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},
    '5312': {'consolidated': 'Corpus Christi', 'coast': 'Gulf', 'region': 'South Texas'},
    '5313': {'consolidated': 'Houston', 'coast': 'Gulf', 'region': 'North Texas'},

    # Sabine River district 21
    '2101': {'consolidated': 'Port Arthur', 'coast': 'Gulf', 'region': 'North Texas'},
    '2102': {'consolidated': 'Sabine River', 'coast': 'Gulf', 'region': 'North Texas'},
    '2103': {'consolidated': 'Sabine River', 'coast': 'Gulf', 'region': 'North Texas'},
    '2104': {'consolidated': 'Beaumont', 'coast': 'Gulf', 'region': 'North Texas'},

    # NY/NJ district 10
    '1001': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '1002': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '1003': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '1004': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},
    '1012': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},

    # Philadelphia district 11
    '1101': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1102': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1103': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1104': {'consolidated': 'Pittsburgh', 'coast': 'Inland', 'region': 'Great Lakes'},
    '1106': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1107': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1108': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1109': {'consolidated': 'Delaware River', 'coast': 'Inland', 'region': 'Mid-Atlantic'},
    '1113': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1119': {'consolidated': 'Delaware River', 'coast': 'Inland', 'region': 'Mid-Atlantic'},

    # Norfolk district 14
    '1401': {'consolidated': 'Hampton Roads', 'coast': 'East', 'region': 'South Atlantic'},
    '1404': {'consolidated': 'Hampton Roads', 'coast': 'East', 'region': 'South Atlantic'},
    '1409': {'consolidated': 'Hampton Roads', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1410': {'consolidated': 'Hampton Roads', 'coast': 'Inland', 'region': 'South Atlantic'},

    # NC district 15
    '1501': {'consolidated': 'North Carolina Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '1502': {'consolidated': 'North Carolina Ports', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1503': {'consolidated': 'North Carolina Ports', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1511': {'consolidated': 'North Carolina Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '1512': {'consolidated': 'North Carolina Ports', 'coast': 'Inland', 'region': 'South Atlantic'},

    # SC district 16
    '1601': {'consolidated': 'Charleston', 'coast': 'East', 'region': 'South Atlantic'},
    '1602': {'consolidated': 'South Carolina Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '1603': {'consolidated': 'South Carolina Ports', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1604': {'consolidated': 'South Carolina Ports', 'coast': 'Inland', 'region': 'South Atlantic'},

    # Georgia district 17
    '1701': {'consolidated': 'Georgia Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '1703': {'consolidated': 'Georgia Ports', 'coast': 'East', 'region': 'South Atlantic'},
    '1704': {'consolidated': 'Atlanta', 'coast': 'Inland', 'region': 'South Atlantic'},
    '1791': {'consolidated': 'Atlanta', 'coast': 'Inland', 'region': 'South Atlantic'},

    # LA-Long Beach district 27
    '2704': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2709': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2712': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2713': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2715': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2719': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2720': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2721': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '2722': {'consolidated': 'Las Vegas', 'coast': 'Inland', 'region': 'California'},

    # San Francisco district 28
    '2801': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2802': {'consolidated': 'Eureka', 'coast': 'West', 'region': 'California'},
    '2805': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2809': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2810': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2811': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2812': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2815': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2820': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2821': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2827': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2828': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2829': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2830': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2833': {'consolidated': 'San Francisco Bay', 'coast': 'Inland', 'region': 'California'},
    '2834': {'consolidated': 'San Francisco Bay', 'coast': 'West', 'region': 'California'},
    '2835': {'consolidated': 'San Francisco Bay', 'coast': 'Inland', 'region': 'California'},
    '2803': {'consolidated': 'San Francisco Bay', 'coast': 'Inland', 'region': 'California'},

    # Seattle district 30
    '3001': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3002': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3003': {'consolidated': 'Grays Harbor', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3006': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3007': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3008': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3010': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3014': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3022': {'consolidated': 'Seattle-Tacoma', 'coast': 'Inland', 'region': 'Pacific Northwest'},
    '3026': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},
    '3029': {'consolidated': 'Seattle-Tacoma', 'coast': 'West', 'region': 'Pacific Northwest'},

    # Columbia River district 29
    '2901': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2902': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2903': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2904': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2905': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2907': {'consolidated': 'Columbia River', 'coast': 'Inland', 'region': 'Pacific Northwest'},
    '2908': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2909': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},
    '2910': {'consolidated': 'Columbia River', 'coast': 'West', 'region': 'Pacific Northwest'},

    # Puerto Rico district 49
    '4901': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},
    '4904': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},
    '4907': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},
    '4908': {'consolidated': 'Ponce', 'coast': 'Islands', 'region': 'Caribbean'},
    '4909': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},
    '4913': {'consolidated': 'San Juan', 'coast': 'Islands', 'region': 'Caribbean'},

    # Virgin Islands district 51
    '5101': {'consolidated': 'Virgin Islands', 'coast': 'Islands', 'region': 'Caribbean'},
    '5102': {'consolidated': 'Virgin Islands', 'coast': 'Islands', 'region': 'Caribbean'},
    '5104': {'consolidated': 'Virgin Islands', 'coast': 'Islands', 'region': 'Caribbean'},
    '5105': {'consolidated': 'Virgin Islands', 'coast': 'Islands', 'region': 'Caribbean'},

    # Laredo district 23
    '2304': {'consolidated': 'Laredo', 'coast': 'Land Ports', 'region': 'South Texas'},
    '2303': {'consolidated': 'Eagle Pass', 'coast': 'Land Ports', 'region': 'South Texas'},
    '2305': {'consolidated': 'Hidalgo/Pharr', 'coast': 'Land Ports', 'region': 'South Texas'},
    '2302': {'consolidated': 'Del Rio', 'coast': 'Land Ports', 'region': 'South Texas'},

    # El Paso district 24
    '2401': {'consolidated': 'El Paso', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '2402': {'consolidated': 'El Paso', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '2408': {'consolidated': 'Santa Teresa', 'coast': 'Land Ports', 'region': 'Land Ports'},

    # San Diego district 25
    '2506': {'consolidated': 'Otay Mesa', 'coast': 'Land Ports', 'region': 'California'},
    '2507': {'consolidated': 'Calexico', 'coast': 'Land Ports', 'region': 'California'},

    # Nogales/AZ district 26
    '2604': {'consolidated': 'Nogales', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '2605': {'consolidated': 'Phoenix', 'coast': 'Inland', 'region': 'Land Ports'},
    '2609': {'consolidated': 'Tucson', 'coast': 'Inland', 'region': 'Land Ports'},

    # Buffalo district 09
    '0901': {'consolidated': 'Buffalo-Niagara', 'coast': 'Great Lakes', 'region': 'Great Lakes'},

    # Detroit district 38
    '3801': {'consolidated': 'Detroit', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '3802': {'consolidated': 'Port Huron', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '3803': {'consolidated': 'Sault Ste. Marie', 'coast': 'Great Lakes', 'region': 'Great Lakes'},

    # Duluth district 36
    '3510': {'consolidated': 'Duluth-Superior', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '3604': {'consolidated': 'International Falls', 'coast': 'Great Lakes', 'region': 'Great Lakes'},

    # Cleveland district 41
    '4105': {'consolidated': 'Cleveland-Toledo', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '4106': {'consolidated': 'Cleveland-Toledo', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '4121': {'consolidated': 'Cleveland-Toledo', 'coast': 'Great Lakes', 'region': 'Great Lakes'},
    '4122': {'consolidated': 'Cleveland-Toledo', 'coast': 'Great Lakes', 'region': 'Great Lakes'},

    # Sweetgrass/MT district 33
    '3310': {'consolidated': 'Sweetgrass-MT', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '3303': {'consolidated': 'Salt Lake City', 'coast': 'Inland', 'region': 'Land Ports'},
    '3302': {'consolidated': 'Northern Border-ID', 'coast': 'Land Ports', 'region': 'Land Ports'},

    # Pembina/ND district 34
    '3401': {'consolidated': 'Pembina-ND', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '3403': {'consolidated': 'Portal-ND', 'coast': 'Land Ports', 'region': 'Land Ports'},

    # St. Louis district 45
    '4503': {'consolidated': 'St. Louis', 'coast': 'Inland', 'region': 'Mississippi River'},
    '4504': {'consolidated': 'Wichita', 'coast': 'Inland', 'region': 'Mississippi River'},

    # Washington DC district 54
    '5401': {'consolidated': 'Washington DC', 'coast': 'East', 'region': 'Mid-Atlantic'},

    # Norfolk/Mobile/Charleston consolidated district 59
    '5901': {'consolidated': 'Norfolk/Mobile/Charleston', 'coast': 'East', 'region': 'South Atlantic'},

    # FedEx Newark — district 46 (non-standard), really NY area
    '4671': {'consolidated': 'New York', 'coast': 'East', 'region': 'North Atlantic'},

    # Supplemental codes from trade data
    '1105': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1107': {'consolidated': 'Delaware River', 'coast': 'East', 'region': 'Mid-Atlantic'},
    '1297': {'consolidated': 'Hampton Roads', 'coast': 'East', 'region': 'South Atlantic'},
    '2707': {'consolidated': 'LA-Long Beach', 'coast': 'West', 'region': 'California'},
    '1791': {'consolidated': 'Atlanta', 'coast': 'Inland', 'region': 'South Atlantic'},
    '3279': {'consolidated': 'Honolulu', 'coast': 'West', 'region': 'Pacific'},
    '3325': {'consolidated': 'Northern Border-MT', 'coast': 'Land Ports', 'region': 'Land Ports'},
    '6000': {'consolidated': 'Vessels Under Own Power', 'coast': 'N/A', 'region': 'N/A'},
    '7070': {'consolidated': 'Low Value/Estimated', 'coast': 'N/A', 'region': 'N/A'},
    '8000': {'consolidated': 'Mail Shipments', 'coast': 'N/A', 'region': 'N/A'},

    # Various single overrides for inland/special
    '4110': {'consolidated': 'Indianapolis', 'coast': 'Inland', 'region': 'Great Lakes'},
    '4115': {'consolidated': 'Louisville', 'coast': 'Inland', 'region': 'Great Lakes'},
    '3501': {'consolidated': 'Minneapolis-St. Paul', 'coast': 'Inland', 'region': 'Great Lakes'},
    '3502': {'consolidated': 'Sioux Falls', 'coast': 'Inland', 'region': 'Great Lakes'},
    '3512': {'consolidated': 'Omaha', 'coast': 'Inland', 'region': 'Great Lakes'},
    '3513': {'consolidated': 'Des Moines', 'coast': 'Inland', 'region': 'Great Lakes'},
    '5505': {'consolidated': 'Tulsa', 'coast': 'Inland', 'region': 'North Texas'},
    '5506': {'consolidated': 'Austin', 'coast': 'Inland', 'region': 'North Texas'},
    '5507': {'consolidated': 'San Antonio', 'coast': 'Inland', 'region': 'South Texas'},
}


# ── 5. Build classifications for every port code ──
classifications = []
for port_code, sd_info in sorted(schedule_d.items()):
    dist = port_code[:2]
    port_name = sd_info['port_name']
    district_name = sd_info['district_name']

    port_type = classify_port_type(port_code, port_name)

    # Get classification: port override > district default > fallback
    if port_code in port_overrides:
        consol = port_overrides[port_code]['consolidated']
        coast = port_overrides[port_code]['coast']
        region = port_overrides[port_code]['region']
    elif dist in district_defaults:
        consol = district_defaults[dist]['consolidated']
        coast = district_defaults[dist]['coast']
        region = district_defaults[dist]['region']
    else:
        consol = f'District {dist}'
        coast = 'Unknown'
        region = 'Unknown'

    classifications.append({
        'port_code': port_code,
        'port_name': port_name,
        'district_code': dist,
        'district_name': district_name,
        'port_consolidated': consol,
        'port_coast': coast,
        'port_region': region,
        'port_type': port_type,
    })

# ── 6. Write port_classifications.csv ──
outfile = 'data/reference/port_classifications.csv'
fieldnames = ['port_code', 'port_name', 'district_code', 'district_name',
              'port_consolidated', 'port_coast', 'port_region', 'port_type']
with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in classifications:
        writer.writerow(row)

print(f"Written: {outfile} ({len(classifications)} ports)")

# ── 7. Summary stats ──
from collections import Counter
coast_counts = Counter(r['port_coast'] for r in classifications)
type_counts = Counter(r['port_type'] for r in classifications)
consol_counts = Counter(r['port_consolidated'] for r in classifications)

print(f"\nBy coast:")
for coast, n in sorted(coast_counts.items(), key=lambda x: -x[1]):
    print(f"  {coast:25s} {n:4d}")

print(f"\nBy type:")
for ptype, n in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ptype:25s} {n:4d}")

print(f"\nConsolidated groups: {len(consol_counts)}")

# Verify key entries
print("\nKey port verifications:")
key_checks = {
    '1901': 'Mobile',
    '2002': 'New Orleans',
    '2004': 'Mississippi River',
    '2101': 'Port Arthur',
    '5201': 'Miami',
    '5203': 'Port Everglades',
    '1902': 'Gulfport',
    '4909': 'San Juan',
    '4908': 'Ponce',
    '5101': 'Virgin Islands',
}
cl_lookup = {r['port_code']: r for r in classifications}
for code, expected_consol in key_checks.items():
    info = cl_lookup.get(code)
    if info:
        match = '✓' if info['port_consolidated'] == expected_consol else '✗'
        print(f"  {match} {code} {info['port_name']:35s} → consolidated={info['port_consolidated']}, coast={info['port_coast']}")
    else:
        print(f"  ✗ {code} NOT FOUND")
