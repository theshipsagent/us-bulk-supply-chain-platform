"""
Census Schedule C — Country Code Reference Constants

Source: data/reference/country_reference.csv (single source of truth)
Country codes are 4-digit zero-padded TEXT matching Census Schedule C.

Canonical reference file:
  - data/reference/country_reference.csv  (merged, ~243 codes)
    Columns: cty_code, cty_name, cty_abbrev, iso_alpha2, region, sub_region

Usage:
    from census_trade.config.country_codes import load_country_reference, REGIONS
    ref = load_country_reference()  # dict keyed by cty_code
"""

import csv
import os

# ============================================================
# REGION GROUPINGS (code range → region)
# ============================================================

REGIONS = {
    'North America':    ('1000', '1999'),
    'Central America':  ('2010', '2250'),
    'Caribbean':        ('2300', '2899'),
    'South America':    ('3000', '3799'),
    'Europe':           ('4000', '4999'),
    'Middle East':      ('5000', '5299'),
    'Asia':             ('5300', '5899'),
    'Oceania':          ('6000', '6899'),
    'Africa':           ('7000', '7999'),
    'Special':          ('8000', '8999'),
    'US Territories':   ('9000', '9999'),
}

# ============================================================
# KEY COUNTRY CODES (frequently referenced)
# ============================================================

# North America
CANADA = '1220'
MEXICO = '2010'

# Major trade partners — Americas
BRAZIL = '3510'
COLOMBIA = '3010'
CHILE = '3370'
ARGENTINA = '3570'
PERU = '3330'

# Europe
UNITED_KINGDOM = '4120'
GERMANY = '4280'
FRANCE = '4279'
ITALY = '4759'
NETHERLANDS = '4210'
SPAIN = '4700'
IRELAND = '4190'
SWITZERLAND = '4419'

# Asia
CHINA = '5700'
JAPAN = '5880'
SOUTH_KOREA = '5800'
TAIWAN = '5830'
INDIA = '5330'
VIETNAM = '5520'
THAILAND = '5490'
SINGAPORE = '5590'
INDONESIA = '5600'
MALAYSIA = '5570'
PHILIPPINES = '5650'

# Middle East
SAUDI_ARABIA = '5170'
UAE = '5200'
ISRAEL = '5081'
IRAQ = '5050'

# Oceania
AUSTRALIA = '6021'
NEW_ZEALAND = '6141'

# Africa
SOUTH_AFRICA = '7910'
NIGERIA = '7530'
EGYPT = '7290'

# Special
UNIDENTIFIED = '8220'
INTL_ORGS = '8500'

# US Territories
PUERTO_RICO = '9030'
VIRGIN_ISLANDS = '9110'
GUAM = '9350'


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_region(cty_code: str) -> str:
    """Get region name for a country code based on code range."""
    n = int(str(cty_code).zfill(4))
    for region, (lo, hi) in REGIONS.items():
        if int(lo) <= n <= int(hi):
            return region
    return 'Unknown'


def load_country_reference(base_path: str = None) -> dict:
    """Load the country reference CSV into a dict keyed by cty_code.

    This is THE single source of truth for all country lookups.

    Returns:
        dict: {cty_code: {cty_code, cty_name, cty_abbrev, iso_alpha2,
               region, sub_region}}
    """
    if base_path is None:
        base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reference')
    fpath = os.path.join(base_path, 'country_reference.csv')
    result = {}
    with open(fpath, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            result[row['cty_code']] = row
    return result
