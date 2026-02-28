"""
Census Foreign Trade Data Products - URL Pattern Registry

All download URLs for bulk data products from:
https://www.census.gov/foreign-trade/data/dataproducts.html

URL patterns use {YYYY} for 4-digit year, {YY} for 2-digit year,
{MM} for 2-digit month, {Q} for quarter number.
"""

BASE_URL = "https://www.census.gov/trade/downloads"

# --- Merchandise Trade ---
MERCHANDISE_EXPORTS = {
    "name": "Merchandise Trade Exports",
    "description": "Full export detail: Schedule B 10-digit commodity, country, district, transport mode",
    "url_template": f"{BASE_URL}/{{YYYY}}/Merch/ex_m/EXDB{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "files_inside": [
        "EXP_DETL.TXT", "EXP_COMM.TXT", "EXP_CTY.TXT", "EXP_DIST.TXT",
        "CONCORD.TXT", "COUNTRY.TXT", "DISTRICT.TXT", "HSDESC.TXT",
        "NAICS.TXT", "SITC.TXT", "ENDUSE.TXT", "HITECH.TXT"
    ],
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/exdb.html",
    "coverage_start": 2010,
}

MERCHANDISE_IMPORTS = {
    "name": "Merchandise Trade Imports",
    "description": "Full import detail: HTS 10-digit, country, district entry/unlading, rate provision, duty, CIF",
    "url_template": f"{BASE_URL}/{{YYYY}}/Merch/im_m/IMDB{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "files_inside": [
        "IMP_DETL.TXT", "IMP_COMM.TXT", "IMP_CTY.TXT", "IMP_DE.TXT", "IMP_DU.TXT",
        "CONCORD.TXT", "COUNTRY.TXT", "DISTRICT.TXT", "HSDESC.TXT",
        "NAICS.TXT", "SITC.TXT", "ENDUSE.TXT", "HITECH.TXT"
    ],
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/imdb.html",
    "coverage_start": 2010,
}

# --- Port Data ---
PORT_EXPORTS_HS6 = {
    "name": "Port Exports HS6",
    "description": "Export by port, HS 6-digit commodity, country, transport mode",
    "url_template": f"{BASE_URL}/{{YYYY}}/Port/ex_hs6_m/PORTHS6XM{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "files_inside": ["DPORTHS6E.TXT"],
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/dporths6e.html",
    "coverage_start": 2010,
}

PORT_IMPORTS_HS6 = {
    "name": "Port Imports HS6",
    "description": "Import by port, HS 6-digit commodity, country, transport mode",
    "url_template": f"{BASE_URL}/{{YYYY}}/Port/im_hs6_m/PORTHS6MM{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "files_inside": ["DPORTHS6I.TXT"],
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/dporths6i.html",
    "coverage_start": 2010,
}

# --- State Data ---
STATE_EXPORTS_HS6_ORIGIN = {
    "name": "State Exports HS6 - Origin of Movement",
    "description": "State-level exports by HS 6-digit, country, based on origin of movement",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/hs6_om_m/STHS6M{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/sths6.html",
    "coverage_start": 2010,
}

STATE_EXPORTS_HS6_ZIPCODE = {
    "name": "State Exports HS6 - Zipcode Based",
    "description": "State-level exports by HS 6-digit, country, based on zipcode",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/hs6_zip_m/STZHS6M{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/sths6.html",
    "coverage_start": 2010,
}

STATE_EXPORTS_NAICS_ORIGIN = {
    "name": "State Exports NAICS - Origin of Movement",
    "description": "State-level exports by NAICS, country, based on origin of movement",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/naics_om_m/STNAICS{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/stnaics.html",
    "coverage_start": 2010,
}

STATE_EXPORTS_NAICS_ZIPCODE = {
    "name": "State Exports NAICS - Zipcode Based",
    "description": "State-level exports by NAICS, country, based on zipcode",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/naics_zip_m/STNAICSZ{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/stnaics.html",
    "coverage_start": 2010,
}

STATE_IMPORTS_HS6 = {
    "name": "State Imports HS6",
    "description": "State-level imports by HS 6-digit, country",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_imp/hs6_m/ISTHSM{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/isths6.html",
    "coverage_start": 2010,
}

STATE_IMPORTS_NAICS = {
    "name": "State Imports NAICS",
    "description": "State-level imports by NAICS, country",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_imp/naics_m/ISNAICS{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/istnaics.html",
    "coverage_start": 2010,
}

STATE_PORT_EXPORTS_ORIGIN = {
    "name": "State/Port Exports - Origin of Movement",
    "description": "State + port level exports, quarterly, based on origin of movement",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/port_om_q/STPORT{{YY}}Q{{Q}}.ZIP",
    "frequency": "quarterly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/stport.html",
    "coverage_start": 2010,
}

STATE_PORT_EXPORTS_ZIPCODE = {
    "name": "State/Port Exports - Zipcode Based",
    "description": "State + port level exports, quarterly, based on zipcode",
    "url_template": f"{BASE_URL}/{{YYYY}}/state_exp/port_zip_q/STPORTZ{{YY}}Q{{Q}}.ZIP",
    "frequency": "quarterly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/stport.html",
    "coverage_start": 2010,
}

STATE_PORT_IMPORTS = {
    "name": "State/Port Imports",
    "description": "State + port level imports, quarterly",
    "url_template": f"{BASE_URL}/additional/ISTPORT/ISTPORT{{YY}}Q{{Q}}.ZIP",
    "frequency": "quarterly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/istport.html",
    "coverage_start": 2010,
}

# --- Special Products ---
TEXTILE_SUMMARY = {
    "name": "Textile Summary",
    "description": "3-year comparative textile import data",
    "url_template": f"{BASE_URL}/{{YYYY}}/Textile_summary_m/TEXSUMM{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/txtsum3yr.html",
    "coverage_start": 2010,
}

SPI_DATABANK = {
    "name": "Special Programs (SPI) Databank",
    "description": "Special program import data with primary/secondary indicators",
    "url_template": f"{BASE_URL}/{{YYYY}}/SPI/databank_m/SPIM{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/spidbank.html",
    "coverage_start": 2010,
}

POSSESSIONS_TRADE = {
    "name": "Trade with U.S. Possessions",
    "description": "Puerto Rico and U.S. Virgin Islands trade at HS 10-digit",
    "url_template": f"{BASE_URL}/{{YYYY}}/Pos/hs10_m/POSHS10M{{YY}}{{MM}}.ZIP",
    "frequency": "monthly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/ea695.html",
    "coverage_start": 2010,
}

ECCN_QUARTERLY = {
    "name": "Export Control Classification (Quarterly)",
    "description": "Export data by ECCN code, quarterly",
    "url_template": f"{BASE_URL}/additional/ECCN/ECCN_Q{{Q}}{{YYYY}}.TXT",
    "frequency": "quarterly",
    "record_layout_url": "https://www.census.gov/foreign-trade/reference/products/layouts/eccn.html",
    "coverage_start": 2010,
}

# --- Pre-built Reports (XLSX/PDF direct downloads) ---
REPORTS_BASE = "https://www.census.gov/foreign-trade"

FT900_REPORT = {
    "name": "FT900 - U.S. International Trade in Goods and Services",
    "url_pdf": f"{REPORTS_BASE}/Press-Release/current_press_release/ft900.pdf",
    "url_xlsx": f"{REPORTS_BASE}/Press-Release/current_press_release/ft900xlsx.zip",
    "prior_releases": f"{REPORTS_BASE}/Press-Release/ft900_index.html",
}

ENDUSE_IMPORTS_MONTHLY = {
    "name": "Monthly Imports by End-Use",
    "url_xlsx": f"{REPORTS_BASE}/statistics/historical/NSAIMP.xlsx",
    "url_pdf": f"{REPORTS_BASE}/statistics/historical/NSAIMP.pdf",
}

ENDUSE_EXPORTS_MONTHLY = {
    "name": "Monthly Exports by End-Use",
    "url_xlsx": f"{REPORTS_BASE}/statistics/historical/NSAEXP.xlsx",
    "url_pdf": f"{REPORTS_BASE}/statistics/historical/NSAEXP.pdf",
}

ENDUSE_ANNUAL_EXPORTS = {
    "name": "Annual Country by 5-digit End-Use (Exports)",
    "url_xlsx": f"{REPORTS_BASE}/statistics/product/enduse/exports/enduse_exports.xlsx",
}

ENDUSE_ANNUAL_IMPORTS = {
    "name": "Annual Country by 5-digit End-Use (Imports)",
    "url_xlsx": f"{REPORTS_BASE}/statistics/product/enduse/imports/enduse_imports.xlsx",
}

ALL_COUNTRIES_BALANCE = {
    "name": "All Countries Trade Balance Dataset",
    "url": f"{REPORTS_BASE}/balance/index.html",
    "description": "Full dataset for all countries (5MB Excel download from page)",
}

# --- Concordance Files ---
CONCORDANCE_BASE = f"{REPORTS_BASE}/data/dataproducts/concordance"

# --- Registry of all bulk products for iteration ---
ALL_BULK_PRODUCTS = {
    "merchandise_exports": MERCHANDISE_EXPORTS,
    "merchandise_imports": MERCHANDISE_IMPORTS,
    "port_exports_hs6": PORT_EXPORTS_HS6,
    "port_imports_hs6": PORT_IMPORTS_HS6,
    "state_exports_hs6_origin": STATE_EXPORTS_HS6_ORIGIN,
    "state_exports_hs6_zipcode": STATE_EXPORTS_HS6_ZIPCODE,
    "state_exports_naics_origin": STATE_EXPORTS_NAICS_ORIGIN,
    "state_exports_naics_zipcode": STATE_EXPORTS_NAICS_ZIPCODE,
    "state_imports_hs6": STATE_IMPORTS_HS6,
    "state_imports_naics": STATE_IMPORTS_NAICS,
    "state_port_exports_origin": STATE_PORT_EXPORTS_ORIGIN,
    "state_port_exports_zipcode": STATE_PORT_EXPORTS_ZIPCODE,
    "state_port_imports": STATE_PORT_IMPORTS,
    "textile_summary": TEXTILE_SUMMARY,
    "spi_databank": SPI_DATABANK,
    "possessions_trade": POSSESSIONS_TRADE,
    "eccn_quarterly": ECCN_QUARTERLY,
}

ALL_REPORTS = {
    "ft900": FT900_REPORT,
    "enduse_imports_monthly": ENDUSE_IMPORTS_MONTHLY,
    "enduse_exports_monthly": ENDUSE_EXPORTS_MONTHLY,
    "enduse_annual_exports": ENDUSE_ANNUAL_EXPORTS,
    "enduse_annual_imports": ENDUSE_ANNUAL_IMPORTS,
    "all_countries_balance": ALL_COUNTRIES_BALANCE,
}


def build_url(product: dict, year: int, month: int = None, quarter: int = None) -> str:
    """Build a download URL for a given product, year, and month/quarter."""
    template = product["url_template"]
    replacements = {
        "{YYYY}": str(year),
        "{YY}": f"{year % 100:02d}",
    }
    if month is not None:
        replacements["{MM}"] = f"{month:02d}"
    if quarter is not None:
        replacements["{Q}"] = str(quarter)

    url = template
    for placeholder, value in replacements.items():
        url = url.replace(placeholder, value)
    return url


def list_available_urls(product: dict, start_year: int = None, end_year: int = 2025,
                        start_month: int = 1, end_month: int = 12) -> list[str]:
    """Generate all available URLs for a product across a date range."""
    if start_year is None:
        start_year = product.get("coverage_start", 2010)

    urls = []
    freq = product.get("frequency", "monthly")

    for year in range(start_year, end_year + 1):
        if freq == "monthly":
            sm = start_month if year == start_year else 1
            em = end_month if year == end_year else 12
            for month in range(sm, em + 1):
                urls.append(build_url(product, year, month=month))
        elif freq == "quarterly":
            for q in range(1, 5):
                urls.append(build_url(product, year, quarter=q))

    return urls
