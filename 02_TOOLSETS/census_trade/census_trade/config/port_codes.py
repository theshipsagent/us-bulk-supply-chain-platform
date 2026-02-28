"""
Census Schedule D — Port Code Reference Constants

Source: data/reference/port_reference.csv (single source of truth)
Port codes are 4-digit zero-padded TEXT: first 2 = district, last 2 = port.

Canonical reference file:
  - data/reference/port_reference.csv  (unified, ~549 codes)
    Columns: port_code, sked_d_name, cbp_appendix_e_name, district_code,
             district_name, state, port_consolidated, port_coast, port_region,
             port_type

Usage:
    from census_trade.config.port_codes import DISTRICTS, LOWER_MISS_PORTS, get_district
    from census_trade.config.port_codes import load_port_reference
"""

import csv
import os

# ============================================================
# DISTRICTS (2-digit district code → name)
# ============================================================

DISTRICTS = {
    '01': 'PORTLAND, ME',
    '02': 'ST. ALBANS, VT',
    '04': 'BOSTON, MA',
    '05': 'PROVIDENCE, RI',
    '07': 'OGDENSBURG, NY',
    '09': 'BUFFALO, NY',
    '10': 'NEW YORK CITY, NY',
    '11': 'PHILADELPHIA, PA',
    '13': 'BALTIMORE, MD',
    '14': 'NORFOLK, VA',
    '15': 'WILMINGTON, NC',
    '16': 'CHARLESTON, SC',
    '17': 'SAVANNAH, GA',
    '18': 'TAMPA, FL',
    '19': 'MOBILE, AL',
    '20': 'NEW ORLEANS, LA',
    '21': 'PORT ARTHUR, TX',
    '23': 'LAREDO, TX',
    '24': 'EL PASO, TX',
    '25': 'SAN DIEGO, CA',
    '26': 'NOGALES, AZ',
    '27': 'LOS ANGELES, CA',
    '28': 'SAN FRANCISCO, CA',
    '29': 'COLUMBIA-SNAKE, OR',
    '30': 'SEATTLE, WA',
    '31': 'ANCHORAGE, AK',
    '32': 'HONOLULU, HI',
    '33': 'GREAT FALLS, MT',
    '34': 'PEMBINA, ND',
    '35': 'MINNEAPOLIS, MN',
    '36': 'DULUTH, MN',
    '37': 'MILWAUKEE, WI',
    '38': 'DETROIT, MI',
    '39': 'CHICAGO, IL',
    '41': 'CLEVELAND, OH',
    '45': 'ST. LOUIS, MO',
    '49': 'SAN JUAN, PR',
    '51': 'U.S. VIRGIN ISLANDS',
    '52': 'MIAMI, FL',
    '53': 'HOUSTON-GALVESTON, TX',
    '54': 'WASHINGTON, DC',
    '55': 'DALLAS-FORT WORTH, TX',
    '58': 'SAVANNAH/WILMINGTON',
    '59': 'NORFOLK/MOBILE/CHARLESTON',
    '60': 'VESSELS UNDER OWN POWER',
    '70': 'LOW VALUE',
    '80': 'MAIL SHIPMENTS',
}

# ============================================================
# KEY PORT CODES (frequently referenced)
# ============================================================

# Gulf Coast — Major Seaports
HOUSTON = '5301'
GALVESTON = '5310'
FREEPORT_TX = '5311'
CORPUS_CHRISTI = '5312'
PORT_LAVACA = '5313'
TEXAS_CITY = '5306'
PORT_ARTHUR = '2101'
SABINE = '2102'
BEAUMONT = '2104'
NEW_ORLEANS = '2002'
MORGAN_CITY = '2001'
BATON_ROUGE = '2004'
GRAMERCY = '2010'
LAKE_CHARLES = '2017'
MOBILE = '1901'
GULFPORT = '1902'
PASCAGOULA = '1903'
TAMPA = '1801'
PENSACOLA = '1819'
PANAMA_CITY = '1818'
PORT_MANATEE = '1821'

# East Coast
NEW_YORK = '1001'
NEWARK = '1003'
PHILADELPHIA = '1101'
BALTIMORE = '1303'
NORFOLK = '1401'
WILMINGTON_NC = '1501'
CHARLESTON = '1601'
SAVANNAH = '1703'
JACKSONVILLE = '1803'
PORT_CANAVERAL = '1816'
MIAMI = '5201'
PORT_EVERGLADES = '5203'
KEY_WEST = '5202'

# West Coast
LA = '2704'
LONG_BEACH = '2709'
OAKLAND = '2811'
SEATTLE = '3001'
TACOMA = '3002'
PORTLAND_OR = '2904'
VANCOUVER_WA = '2908'

# Islands
SAN_JUAN = '4909'
PONCE = '4908'
CHARLOTTE_AMALIE = '5101'
HONOLULU = '3201'

# ============================================================
# LOWER MISSISSIPPI RIVER PORTS
# ============================================================

LOWER_MISS_PORTS = {
    '2001': 'Morgan City, LA',
    '2002': 'New Orleans, LA',
    '2004': 'Baton Rouge, LA',
    '2010': 'Gramercy, LA',
    '2011': 'Greenville, MS',
    '2015': 'Vicksburg, MS',
    '2017': 'Lake Charles, LA',
}

# ============================================================
# COAST GROUPINGS
# ============================================================

GULF_DISTRICTS = {'18', '19', '20', '21', '53'}
EAST_DISTRICTS = {'01', '04', '05', '10', '11', '13', '14', '15', '16', '17', '52', '54'}
WEST_DISTRICTS = {'27', '28', '29', '30', '32'}
GREAT_LAKES_DISTRICTS = {'09', '36', '37', '38', '39', '41'}
LAND_BORDER_DISTRICTS = {'02', '07', '23', '24', '25', '26', '33', '34'}
ISLAND_DISTRICTS = {'31', '49', '51'}
INLAND_DISTRICTS = {'35', '45', '55'}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_district(port_code: str) -> str:
    """Extract 2-digit district code from 4-digit port code."""
    return str(port_code).zfill(4)[:2]


def get_district_name(port_code: str) -> str:
    """Get district name for a port code."""
    return DISTRICTS.get(get_district(port_code), 'UNKNOWN')


def load_port_reference(base_path: str = None) -> dict:
    """Load the unified port reference CSV into a dict keyed by port_code.

    This is THE single source of truth for all port lookups.

    Returns:
        dict: {port_code: {port_code, sked_d_name, cbp_appendix_e_name,
               district_code, district_name, state, port_consolidated,
               port_coast, port_region, port_type}}
    """
    if base_path is None:
        base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reference')
    fpath = os.path.join(base_path, 'port_reference.csv')
    result = {}
    with open(fpath, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            result[row['port_code']] = row
    return result


# Backwards-compatible aliases
def load_schedule_d(base_path: str = None) -> dict:
    """Load Schedule D data from the unified port reference."""
    ref = load_port_reference(base_path)
    return {code: {'port_code': code, 'port_name': r['sked_d_name'],
                    'district_code': r['district_code'], 'district_name': r['district_name']}
            for code, r in ref.items()}


def load_classifications(base_path: str = None) -> dict:
    """Load classifications from the unified port reference."""
    return load_port_reference(base_path)
