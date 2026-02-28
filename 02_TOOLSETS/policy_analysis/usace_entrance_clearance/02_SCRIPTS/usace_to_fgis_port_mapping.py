"""
USACE to FGIS Port Mapping

Maps USACE port names to FGIS regional port codes based on
FGIS Export Region Definition Tables.

Author: WSD3 / Claude Code
Date: 2026-02-06
Version: 1.0.0
"""

# USACE Port Name -> FGIS Regional Port Code
USACE_TO_FGIS_PORT_MAP = {
    # MISSISSIPPI RIVER - Louisiana Mississippi River ports
    'Port of New Orleans, LA': 'MISSISSIPPI R.',
    'Port of South Louisiana, LA': 'MISSISSIPPI R.',
    'Port of Plaquemines, LA': 'MISSISSIPPI R.',
    'Port of Baton Rouge, LA': 'MISSISSIPPI R.',
    'Plaquemines, LA': 'MISSISSIPPI R.',
    'New Orleans, LA': 'MISSISSIPPI R.',
    'South Louisiana, LA': 'MISSISSIPPI R.',

    # NORTH TEXAS - Houston and north
    'Port of Houston Authority of Harris County, TX': 'N. TEXAS',
    'Port of Corpus Christi Authority, TX': 'N. TEXAS',
    'Port of Beaumont, TX': 'N. TEXAS',
    'Houston, TX': 'N. TEXAS',
    'Corpus Christi, TX': 'N. TEXAS',
    'Beaumont, TX': 'N. TEXAS',
    'Port Arthur, TX': 'N. TEXAS',
    'Galveston, TX': 'N. TEXAS',
    'Texas City, TX': 'N. TEXAS',

    # SOUTH TEXAS - South of Houston
    'Port of Brownsville, TX': 'S. TEXAS',
    'Brownsville, TX': 'S. TEXAS',
    'Port Isabel, TX': 'S. TEXAS',

    # PUGET SOUND - Washington waterways
    'Port of Seattle, WA': 'PUGET SOUND',
    'Port of Tacoma, WA': 'PUGET SOUND',
    'Seattle, WA': 'PUGET SOUND',
    'Tacoma, WA': 'PUGET SOUND',
    'Longview, WA': 'COLUMBIA R.',  # Actually Columbia River
    'Kalama, WA': 'COLUMBIA R.',
    'Vancouver, WA': 'COLUMBIA R.',

    # COLUMBIA RIVER - Oregon/Washington border
    'Portland, OR': 'COLUMBIA R.',
    'Port of Portland, OR': 'COLUMBIA R.',
    'Astoria, OR': 'COLUMBIA R.',
    'Port of Astoria, OR': 'COLUMBIA R.',

    # CALIFORNIA
    'Port of Los Angeles, CA': 'CALIFORNIA',
    'Port of Long Beach, CA': 'CALIFORNIA',
    'Port of Oakland, CA': 'CALIFORNIA',
    'Port of San Diego, CA': 'CALIFORNIA',
    'Port of Sacramento, CA': 'CALIFORNIA',
    'Port of Stockton, CA': 'CALIFORNIA',
    'Los Angeles, CA': 'CALIFORNIA',
    'Long Beach, CA': 'CALIFORNIA',
    'Oakland, CA': 'CALIFORNIA',
    'Stockton, CA': 'CALIFORNIA',

    # EAST GULF - Gulf of Mexico east of Mississippi River
    'Port of Mobile, AL': 'EAST GULF',
    'Mobile, AL': 'EAST GULF',
    'Port of Pensacola, FL': 'EAST GULF',
    'Pensacola, FL': 'EAST GULF',
    'Port of Panama City, FL': 'EAST GULF',

    # SOUTH ATLANTIC - Maryland and south on Atlantic coast
    'Baltimore, MD': 'S. ATLANTIC',
    'Port of Baltimore, MD': 'S. ATLANTIC',
    'Norfolk, VA': 'S. ATLANTIC',
    'Port of Virginia, VA': 'S. ATLANTIC',
    'Charleston, SC': 'S. ATLANTIC',
    'Port of Charleston, SC': 'S. ATLANTIC',
    'Savannah, GA': 'S. ATLANTIC',
    'Port of Savannah, GA': 'S. ATLANTIC',
    'Jacksonville, FL': 'S. ATLANTIC',
    'Port Everglades, FL': 'S. ATLANTIC',
    'Port of Palm Beach, FL': 'S. ATLANTIC',
    'Port Canaveral, FL': 'S. ATLANTIC',
    'Port of Miami, FL': 'S. ATLANTIC',
    'Miami, FL': 'S. ATLANTIC',
    'Wilmington, NC': 'S. ATLANTIC',
    'Morehead City, NC': 'S. ATLANTIC',

    # NORTH ATLANTIC - North of Maryland on Atlantic coast
    'Port Authority of New York and New Jersey, NY & NJ': 'N. ATLANTIC',
    'New York, NY': 'N. ATLANTIC',
    'Port of Philadelphia, PA': 'N. ATLANTIC',
    'Philadelphia, PA': 'N. ATLANTIC',
    'Boston, MA': 'N. ATLANTIC',
    'Port of Boston, MA': 'N. ATLANTIC',
    'Providence, RI': 'N. ATLANTIC',
    'Portland, ME': 'N. ATLANTIC',

    # TOLEDO - Lake Erie
    'Toledo, OH': 'TOLEDO',
    'Port of Toledo, OH': 'TOLEDO',

    # DULUTH-SUPERIOR - Lake Superior
    'Duluth-Superior, MN & WI': 'DULUTH-SUP',
    'Duluth, MN': 'DULUTH-SUP',
    'Superior, WI': 'DULUTH-SUP',

    # CHICAGO - Lake Michigan
    'Chicago, IL': 'CHICAGO',
    'Port of Chicago, IL': 'CHICAGO',
    'Milwaukee, WI': 'CHICAGO',
    'Port of Milwaukee, WI': 'CHICAGO',

    # LAKE ERIE
    'Cleveland, OH': 'LAKE ERIE',
    'Erie, PA': 'LAKE ERIE',
    'Ashtabula, OH': 'LAKE ERIE',

    # SAGINAW - Lake Huron
    'Saginaw, MI': 'SAGINAW',

    # PORT HURON - Lake Huron
    'Port Huron, MI': 'PORT HURON',
}

def map_usace_to_fgis_port(usace_port):
    """Map USACE port name to FGIS regional port code"""
    if not usace_port or str(usace_port).strip() == '':
        return None

    usace_port = str(usace_port).strip()

    # Try exact match first
    if usace_port in USACE_TO_FGIS_PORT_MAP:
        return USACE_TO_FGIS_PORT_MAP[usace_port]

    # Try partial matching for variations
    usace_upper = usace_port.upper()

    # Louisiana/Mississippi River ports
    if 'NEW ORLEANS' in usace_upper or 'SOUTH LOUISIANA' in usace_upper or 'PLAQUEMINES' in usace_upper:
        return 'MISSISSIPPI R.'

    # Texas ports
    if 'HOUSTON' in usace_upper or 'CORPUS CHRISTI' in usace_upper or 'BEAUMONT' in usace_upper:
        return 'N. TEXAS'
    if 'BROWNSVILLE' in usace_upper:
        return 'S. TEXAS'

    # Pacific Northwest
    if 'SEATTLE' in usace_upper or 'TACOMA' in usace_upper:
        return 'PUGET SOUND'
    if 'PORTLAND' in usace_upper and 'OR' in usace_upper:
        return 'COLUMBIA R.'
    if 'LONGVIEW' in usace_upper or 'KALAMA' in usace_upper or 'VANCOUVER' in usace_upper and 'WA' in usace_upper:
        return 'COLUMBIA R.'

    # California
    if any(x in usace_upper for x in ['LOS ANGELES', 'LONG BEACH', 'OAKLAND', 'STOCKTON']) and 'CA' in usace_upper:
        return 'CALIFORNIA'

    # East Gulf
    if 'MOBILE' in usace_upper or ('PENSACOLA' in usace_upper and 'FL' in usace_upper):
        return 'EAST GULF'

    # Atlantic ports
    if 'BALTIMORE' in usace_upper:
        return 'S. ATLANTIC'
    if any(x in usace_upper for x in ['NORFOLK', 'VIRGINIA', 'CHARLESTON', 'SAVANNAH', 'JACKSONVILLE', 'EVERGLADES', 'MIAMI']):
        return 'S. ATLANTIC'
    if 'NEW YORK' in usace_upper or ('PHILADELPHIA' in usace_upper and 'PA' in usace_upper):
        return 'N. ATLANTIC'

    # Great Lakes
    if 'TOLEDO' in usace_upper and 'OH' in usace_upper:
        return 'TOLEDO'
    if 'DULUTH' in usace_upper or 'SUPERIOR' in usace_upper:
        return 'DULUTH-SUP'
    if 'CHICAGO' in usace_upper or ('MILWAUKEE' in usace_upper and 'WI' in usace_upper):
        return 'CHICAGO'

    return None
