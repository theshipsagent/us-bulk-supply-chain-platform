"""Geographic identity enrichment for the Site Master Registry.

Adds 15 columns to every master site record, providing standardized
geographic identifiers that link to Census, EPA, BEA, and trade datasets:

  - latitude_dms, longitude_dms     Coordinate format conversion
  - fips_state_code                  2-digit state FIPS
  - fips_county_code                 5-digit county FIPS
  - census_region, census_division   Census Bureau classifications
  - bea_region                       Bureau of Economic Analysis regions
  - epa_region                       EPA regions (1-10)
  - congressional_district           119th Congress (spatial join)
  - market_region                    Custom 7-region classification
  - nearest_port_code                Census Schedule D seaport code
  - nearest_port_name                Port Schedule D name (from geo-dictionary)
  - nearest_port_consolidated        Consolidated port group
  - nearest_port_coast               Coast classification
  - nearest_port_region              Sub-region classification

All enrichments run locally using lookup tables and spatial joins.
Zero external API calls.
"""

from __future__ import annotations

import csv
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import duckdb

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DMS Coordinate Conversion
# ---------------------------------------------------------------------------

def decimal_to_dms(lat: float, lon: float) -> tuple[str, str]:
    """Convert decimal degrees to DMS format.

    Examples:
        31.0035  -> '31\u00b000\'12.6"N'
        -88.0137 -> '88\u00b000\'49.3"W'
    """
    def _fmt(dd: float, pos: str, neg: str) -> str:
        direction = pos if dd >= 0 else neg
        dd = abs(dd)
        deg = int(dd)
        minutes_full = (dd - deg) * 60
        mins = int(minutes_full)
        secs = (minutes_full - mins) * 60
        return f"{deg}\u00b0{mins:02d}'{secs:04.1f}\"{direction}"

    return _fmt(lat, "N", "S"), _fmt(lon, "E", "W")


# ---------------------------------------------------------------------------
# State FIPS Lookup (56 entries: 50 states + DC + 5 territories)
# ---------------------------------------------------------------------------

def build_fips_state_lookup() -> dict[str, str]:
    """State abbreviation -> 2-digit FIPS code."""
    return {
        "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
        "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
        "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
        "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
        "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
        "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
        "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
        "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
        "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
        "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
        "DC": "11", "GU": "66", "MP": "69", "PR": "72", "VI": "78",
    }


# ---------------------------------------------------------------------------
# Census Region & Division Lookup
# ---------------------------------------------------------------------------

def build_census_region_lookup() -> dict[str, tuple[str, str]]:
    """State -> (census_region, census_division)."""
    return {
        # Northeast - New England
        "CT": ("Northeast", "New England"), "ME": ("Northeast", "New England"),
        "MA": ("Northeast", "New England"), "NH": ("Northeast", "New England"),
        "RI": ("Northeast", "New England"), "VT": ("Northeast", "New England"),
        # Northeast - Middle Atlantic
        "NJ": ("Northeast", "Middle Atlantic"), "NY": ("Northeast", "Middle Atlantic"),
        "PA": ("Northeast", "Middle Atlantic"),
        # Midwest - East North Central
        "IL": ("Midwest", "East North Central"), "IN": ("Midwest", "East North Central"),
        "MI": ("Midwest", "East North Central"), "OH": ("Midwest", "East North Central"),
        "WI": ("Midwest", "East North Central"),
        # Midwest - West North Central
        "IA": ("Midwest", "West North Central"), "KS": ("Midwest", "West North Central"),
        "MN": ("Midwest", "West North Central"), "MO": ("Midwest", "West North Central"),
        "NE": ("Midwest", "West North Central"), "ND": ("Midwest", "West North Central"),
        "SD": ("Midwest", "West North Central"),
        # South - South Atlantic
        "DE": ("South", "South Atlantic"), "FL": ("South", "South Atlantic"),
        "GA": ("South", "South Atlantic"), "MD": ("South", "South Atlantic"),
        "NC": ("South", "South Atlantic"), "SC": ("South", "South Atlantic"),
        "VA": ("South", "South Atlantic"), "WV": ("South", "South Atlantic"),
        "DC": ("South", "South Atlantic"),
        # South - East South Central
        "AL": ("South", "East South Central"), "KY": ("South", "East South Central"),
        "MS": ("South", "East South Central"), "TN": ("South", "East South Central"),
        # South - West South Central
        "AR": ("South", "West South Central"), "LA": ("South", "West South Central"),
        "OK": ("South", "West South Central"), "TX": ("South", "West South Central"),
        # West - Mountain
        "AZ": ("West", "Mountain"), "CO": ("West", "Mountain"),
        "ID": ("West", "Mountain"), "MT": ("West", "Mountain"),
        "NV": ("West", "Mountain"), "NM": ("West", "Mountain"),
        "UT": ("West", "Mountain"), "WY": ("West", "Mountain"),
        # West - Pacific
        "AK": ("West", "Pacific"), "CA": ("West", "Pacific"),
        "HI": ("West", "Pacific"), "OR": ("West", "Pacific"),
        "WA": ("West", "Pacific"),
        # Territories
        "GU": ("Territories", "Pacific Territories"),
        "MP": ("Territories", "Pacific Territories"),
        "PR": ("Territories", "Caribbean Territories"),
        "VI": ("Territories", "Caribbean Territories"),
    }


# ---------------------------------------------------------------------------
# BEA Region Lookup (8 regions)
# ---------------------------------------------------------------------------

def build_bea_region_lookup() -> dict[str, str]:
    """State -> BEA economic region."""
    return {
        "CT": "New England", "ME": "New England", "MA": "New England",
        "NH": "New England", "RI": "New England", "VT": "New England",
        "DE": "Mideast", "DC": "Mideast", "MD": "Mideast",
        "NJ": "Mideast", "NY": "Mideast", "PA": "Mideast",
        "IL": "Great Lakes", "IN": "Great Lakes", "MI": "Great Lakes",
        "OH": "Great Lakes", "WI": "Great Lakes",
        "IA": "Plains", "KS": "Plains", "MN": "Plains",
        "MO": "Plains", "NE": "Plains", "ND": "Plains", "SD": "Plains",
        "AL": "Southeast", "AR": "Southeast", "FL": "Southeast",
        "GA": "Southeast", "KY": "Southeast", "LA": "Southeast",
        "MS": "Southeast", "NC": "Southeast", "SC": "Southeast",
        "TN": "Southeast", "VA": "Southeast", "WV": "Southeast",
        "AZ": "Southwest", "NM": "Southwest", "OK": "Southwest", "TX": "Southwest",
        "CO": "Rocky Mountain", "ID": "Rocky Mountain", "MT": "Rocky Mountain",
        "UT": "Rocky Mountain", "WY": "Rocky Mountain",
        "AK": "Far West", "CA": "Far West", "HI": "Far West",
        "NV": "Far West", "OR": "Far West", "WA": "Far West",
        "GU": "Territories", "MP": "Territories",
        "PR": "Territories", "VI": "Territories",
    }


# ---------------------------------------------------------------------------
# EPA Region Lookup (10 regions)
# ---------------------------------------------------------------------------

def build_epa_region_lookup() -> dict[str, int]:
    """State -> EPA region number (1-10)."""
    return {
        "CT": 1, "ME": 1, "MA": 1, "NH": 1, "RI": 1, "VT": 1,
        "NJ": 2, "NY": 2, "PR": 2, "VI": 2,
        "DE": 3, "DC": 3, "MD": 3, "PA": 3, "VA": 3, "WV": 3,
        "AL": 4, "FL": 4, "GA": 4, "KY": 4, "MS": 4,
        "NC": 4, "SC": 4, "TN": 4,
        "IL": 5, "IN": 5, "MI": 5, "MN": 5, "OH": 5, "WI": 5,
        "AR": 6, "LA": 6, "NM": 6, "OK": 6, "TX": 6,
        "IA": 7, "KS": 7, "MO": 7, "NE": 7,
        "CO": 8, "MT": 8, "ND": 8, "SD": 8, "UT": 8, "WY": 8,
        "AZ": 9, "CA": 9, "HI": 9, "NV": 9, "GU": 9, "MP": 9,
        "AK": 10, "ID": 10, "OR": 10, "WA": 10,
    }


# ---------------------------------------------------------------------------
# Market Region Lookup (7 custom regions, aligned with rail_regional_summaries)
# ---------------------------------------------------------------------------

def build_market_region_lookup() -> dict[str, str]:
    """State -> custom market region."""
    return {
        "TX": "Gulf Coast", "LA": "Gulf Coast", "MS": "Gulf Coast",
        "AL": "Gulf Coast", "FL": "Gulf Coast",
        "ME": "East Coast", "NH": "East Coast", "VT": "East Coast",
        "MA": "East Coast", "RI": "East Coast", "CT": "East Coast",
        "NY": "East Coast", "NJ": "East Coast", "PA": "East Coast",
        "DE": "East Coast", "MD": "East Coast", "DC": "East Coast",
        "VA": "East Coast", "NC": "East Coast", "SC": "East Coast",
        "GA": "East Coast",
        "OH": "Great Lakes", "MI": "Great Lakes", "IN": "Great Lakes",
        "IL": "Great Lakes", "WI": "Great Lakes", "MN": "Great Lakes",
        "WV": "Interior", "KY": "Interior", "TN": "Interior",
        "MO": "Interior", "AR": "Interior", "OK": "Interior",
        "IA": "Interior", "KS": "Interior", "NE": "Interior",
        "SD": "Interior", "ND": "Interior",
        "MT": "Mountain West", "WY": "Mountain West", "CO": "Mountain West",
        "NM": "Mountain West", "AZ": "Mountain West", "UT": "Mountain West",
        "ID": "Mountain West", "NV": "Mountain West",
        "CA": "West Coast", "OR": "West Coast", "WA": "West Coast",
        "AK": "West Coast", "HI": "West Coast",
        "GU": "Territories", "MP": "Territories",
        "PR": "Territories", "VI": "Territories",
    }


# ---------------------------------------------------------------------------
# County FIPS Loader (from Census national_county.txt)
# ---------------------------------------------------------------------------

def _normalize_county(name: str) -> str:
    """Normalize county name for matching."""
    name = name.upper().strip()
    for suffix in [
        " COUNTY", " PARISH", " BOROUGH", " CENSUS AREA",
        " MUNICIPALITY", " CITY AND BOROUGH", " CITY",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    name = name.replace("ST.", "ST").replace("SAINT ", "ST ")
    return name


def load_county_fips(csv_path: str) -> dict[tuple[str, str], str]:
    """Load Census county FIPS from national_county.txt.

    2020 format (pipe-delimited):
        STATE|STATEFP|COUNTYFP|COUNTYNS|COUNTYNAME|CLASSFP|FUNCSTAT
    Returns dict: (state_abbrev, normalized_county_name) -> 5-digit FIPS.
    """
    lookup: dict[tuple[str, str], str] = {}
    path = Path(csv_path)
    if not path.exists():
        logger.warning(f"County FIPS file not found: {csv_path}")
        return lookup

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("STATE"):
                continue
            parts = line.split("|")
            if len(parts) < 6:
                continue
            state_abbrev = parts[0].strip()
            state_fips = parts[1].strip()
            county_fips = parts[2].strip()
            county_name = parts[4].strip().upper()
            norm = _normalize_county(county_name)
            fips_5 = f"{state_fips}{county_fips}"
            lookup[(state_abbrev, norm)] = fips_5

    logger.info(f"Loaded {len(lookup)} county FIPS codes")
    return lookup


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometres between two WGS84 points."""
    R = 6371.0
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Nearest Port Lookup — Curated seaport coordinates
# ---------------------------------------------------------------------------

def build_seaport_coordinates() -> dict[str, tuple[float, float]]:
    """port_code -> (lat, lon) for major US ports.

    Keys are Census Schedule D 4-digit codes (the same codes used in
    port_reference.csv and port_geo_dictionary.json).

    Coordinates are representative centroids of each port area.
    Coverage: ~115 ports across all US coasts, Great Lakes, and rivers.
    """
    return {
        # ----- Maine -----
        "0101": (43.6591, -70.2568),   # Portland, ME
        "0102": (44.8012, -68.7681),   # Bangor, ME
        "0103": (44.9062, -66.9856),   # Eastport, ME
        "0111": (43.9108, -69.8208),   # Bath, ME
        "0112": (44.3876, -68.2039),   # Bar Harbor, ME
        "0121": (44.1037, -69.1089),   # Rockland, ME
        "0152": (44.4609, -68.9226),   # Searsport, ME
        # ----- New Hampshire -----
        "0131": (43.0718, -70.7626),   # Portsmouth, NH
        # ----- Massachusetts -----
        "0401": (42.3601, -71.0589),   # Boston, MA
        "0405": (41.6362, -70.9342),   # New Bedford, MA
        "0407": (41.7060, -71.1554),   # Fall River, MA
        # ----- Rhode Island -----
        "0501": (41.4901, -71.3128),   # Newport, RI
        "0502": (41.8236, -71.4222),   # Providence, RI
        # ----- Connecticut -----
        "0410": (41.1743, -73.2013),   # Bridgeport, CT
        "0412": (41.3083, -72.9279),   # New Haven, CT
        "0413": (41.3523, -72.0990),   # New London, CT
        # ----- New York -----
        "0901": (42.8864, -78.8784),   # Buffalo-Niagara Falls, NY
        "0903": (43.2610, -77.6109),   # Rochester, NY
        "1001": (40.6892, -74.0445),   # New York, NY (Port of NY/NJ)
        # ----- Delaware River -----
        "1101": (39.9526, -75.1652),   # Philadelphia, PA
        "1103": (39.7391, -75.5398),   # Wilmington, DE
        # ----- Maryland -----
        "1303": (39.2904, -76.6122),   # Baltimore, MD
        # ----- Virginia (Hampton Roads) -----
        "1297": (37.5407, -77.4360),   # Richmond, VA
        "1401": (36.8468, -76.2852),   # Norfolk-Newport News, VA
        # ----- North Carolina -----
        "1501": (34.2257, -77.9447),   # Wilmington, NC
        "1511": (34.7178, -76.6585),   # Beaufort-Morehead City, NC
        # ----- South Carolina -----
        "1601": (32.7765, -79.9311),   # Charleston, SC
        # ----- Georgia -----
        "1701": (31.1499, -81.4915),   # Brunswick, GA
        "1703": (32.0809, -81.0912),   # Savannah, GA
        # ----- Florida (Gulf / North Atlantic) -----
        "1801": (27.9506, -82.4572),   # Tampa, FL
        "1803": (30.3322, -81.6557),   # Jacksonville, FL
        "1816": (28.4001, -80.6228),   # Port Canaveral, FL
        "1818": (30.1588, -85.6602),   # Panama City, FL
        "1819": (30.4383, -87.2110),   # Pensacola, FL
        "1821": (27.6364, -82.5621),   # Port Manatee, FL
        # ----- Florida (South — district 52) -----
        "5201": (25.7617, -80.1918),   # Miami, FL
        "5202": (24.5551, -81.7800),   # Key West, FL
        "5203": (26.1003, -80.1096),   # Port Everglades, FL
        "5204": (26.7153, -80.0534),   # West Palm Beach, FL
        "5205": (27.6506, -80.4128),   # Fort Pierce, FL
        # ----- Alabama -----
        "1901": (30.6954, -88.0399),   # Mobile, AL
        # ----- Mississippi -----
        "1902": (30.3674, -89.0928),   # Gulfport, MS
        "1903": (30.3585, -88.5561),   # Pascagoula, MS
        # ----- Louisiana (Lower Mississippi River) -----
        "2001": (29.6994, -91.2068),   # Morgan City, LA
        "2002": (29.9511, -90.0715),   # New Orleans, LA
        "2004": (30.4508, -91.1874),   # Baton Rouge, LA
        "2010": (30.0511, -90.6898),   # Gramercy, LA
        "2017": (30.2266, -93.2174),   # Lake Charles, LA
        # ----- Texas (Sabine River) -----
        "2101": (29.8611, -93.9388),   # Port Arthur, TX
        "2102": (29.7244, -93.8700),   # Sabine, TX
        "2103": (30.0930, -93.7366),   # Orange, TX
        "2104": (30.0802, -94.1266),   # Beaumont, TX
        # ----- Texas (Brownsville) -----
        "2301": (26.0710, -97.4981),   # Brownsville, TX
        # ----- Texas (Houston / Gulf — district 53) -----
        "5301": (29.7604, -95.3698),   # Houston, TX
        "5306": (29.3849, -94.9049),   # Texas City, TX
        "5310": (29.3013, -94.7977),   # Galveston, TX
        "5311": (28.9530, -95.3597),   # Freeport, TX
        "5312": (27.8006, -97.3964),   # Corpus Christi, TX
        "5313": (28.6475, -96.6053),   # Port Lavaca, TX
        # ----- California (San Diego — district 25) -----
        "2501": (32.7157, -117.1611),  # San Diego, CA
        # ----- California (LA / Long Beach — district 27) -----
        "2704": (33.7400, -118.2700),  # Los Angeles, CA
        "2709": (33.7490, -118.2162),  # Long Beach, CA
        # ----- California (San Francisco Bay — district 28) -----
        "2802": (40.8021, -124.1637),  # Eureka, CA
        "2805": (36.6002, -121.8947),  # Monterey, CA
        "2809": (37.7749, -122.4194),  # San Francisco, CA
        "2810": (37.9577, -121.2908),  # Stockton, CA
        "2811": (37.7957, -122.2788),  # Oakland, CA
        # ----- Oregon (Columbia River — district 29) -----
        "2901": (46.1879, -123.8313),  # Astoria, OR
        "2903": (43.3665, -124.2179),  # Coos Bay, OR
        "2904": (45.5051, -122.6750),  # Portland, OR
        # ----- Washington (Columbia River — district 29) -----
        "2905": (46.1479, -122.9135),  # Longview, WA
        "2908": (45.6326, -122.6717),  # Vancouver, WA
        "2909": (46.0326, -122.8417),  # Kalama, WA
        # ----- Washington (Puget Sound — district 30) -----
        "3001": (47.6062, -122.3321),  # Seattle, WA
        "3002": (47.2529, -122.4443),  # Tacoma, WA
        "3003": (46.9765, -123.8471),  # Aberdeen-Hoquiam, WA (Grays Harbor)
        "3006": (47.9790, -122.2021),  # Everett, WA
        "3007": (48.1106, -123.4307),  # Port Angeles, WA
        "3010": (48.5126, -122.6127),  # Anacortes, WA
        # ----- Alaska (district 31) -----
        "3101": (58.3005, -134.4197),  # Juneau, AK
        "3102": (55.3422, -131.6461),  # Ketchikan, AK
        "3126": (61.2181, -149.9003),  # Anchorage, AK
        # ----- Hawaii (district 32) -----
        "3201": (21.3069, -157.8583),  # Honolulu, HI
        "3202": (19.7297, -155.0900),  # Hilo, HI
        "3203": (20.8893, -156.4729),  # Kahului, HI
        "3204": (21.9544, -159.3674),  # Nawiliwili, HI
        # ----- Great Lakes: Minnesota / Wisconsin -----
        "3501": (44.9778, -93.2650),   # Minneapolis-St. Paul, MN
        "3510": (46.7867, -92.1005),   # Duluth, MN - Superior, WI
        "3701": (43.0389, -87.9065),   # Milwaukee, WI
        "3703": (44.5133, -87.9806),   # Green Bay, WI
        # ----- Great Lakes: Michigan -----
        "3801": (42.3314, -83.0458),   # Detroit, MI
        "3804": (43.5945, -83.8889),   # Saginaw/Bay City, MI
        "3809": (46.5436, -87.3954),   # Marquette, MI
        # ----- Great Lakes: Illinois / Indiana -----
        "3901": (41.6528, -87.5389),   # Chicago, IL
        # ----- Great Lakes: Ohio / Pennsylvania -----
        "4101": (41.4993, -81.6944),   # Cleveland, OH
        "4105": (41.6528, -83.5379),   # Toledo-Sandusky, OH
        "4106": (42.1292, -80.0851),   # Erie, PA
        "4121": (41.4525, -82.1824),   # Lorain, OH
        "4122": (41.8940, -80.7682),   # Ashtabula/Conneaut, OH
        # ----- Puerto Rico -----
        "4907": (18.2208, -67.1539),   # Mayaguez, PR
        "4908": (18.0008, -66.6141),   # Ponce, PR
        "4909": (18.4655, -66.1057),   # San Juan, PR
        # ----- Virgin Islands -----
        "5101": (18.3358, -64.9307),   # Charlotte Amalie (St. Thomas), VI
        "5104": (17.7466, -64.7024),   # Christiansted (St. Croix), VI
    }


def find_nearest_port(
    lat: float,
    lon: float,
    port_coords: dict[str, tuple[float, float]],
) -> tuple[Optional[str], Optional[float]]:
    """Find nearest seaport by Haversine distance.

    Returns (port_code, distance_km) or (None, None).
    """
    if not port_coords:
        return None, None

    best_code = None
    best_dist = float("inf")

    for code, (plat, plon) in port_coords.items():
        d = _haversine_km(lat, lon, plat, plon)
        if d < best_dist:
            best_dist = d
            best_code = code

    return best_code, round(best_dist, 1)


# ---------------------------------------------------------------------------
# Congressional District - Spatial Join
# ---------------------------------------------------------------------------

def spatial_join_congressional_districts(
    sites: list[dict],
    cd_shapefile: str,
) -> dict[str, str]:
    """Spatial join site points against TIGER CD shapefile.

    Returns dict: facility_uid -> "ST-NN" district code.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        logger.warning("geopandas/shapely not installed - skipping CD spatial join")
        return {}

    shapefile_path = Path(cd_shapefile)
    if not shapefile_path.exists():
        logger.warning(f"CD shapefile not found: {cd_shapefile}")
        return {}

    logger.info("Loading Congressional District shapefile...")
    cd_gdf = gpd.read_file(cd_shapefile)
    cd_gdf = cd_gdf.to_crs(epsg=4326)

    points = []
    uids = []
    for s in sites:
        if s["latitude"] is not None and s["longitude"] is not None:
            points.append(Point(s["longitude"], s["latitude"]))
            uids.append(s["facility_uid"])

    if not points:
        return {}

    sites_gdf = gpd.GeoDataFrame(
        {"facility_uid": uids}, geometry=points, crs="EPSG:4326",
    )

    logger.info(
        f"Spatial joining {len(sites_gdf)} sites against "
        f"{len(cd_gdf)} districts..."
    )
    joined = gpd.sjoin(sites_gdf, cd_gdf, how="left", predicate="within")

    fips_to_state = {v: k for k, v in build_fips_state_lookup().items()}

    # Detect column names (varies across TIGER vintages)
    statefp_col = None
    cd_col = None
    for c in joined.columns:
        cl = c.upper()
        if cl.startswith("STATEFP") and statefp_col is None:
            statefp_col = c
        if ("CD" in cl and "FP" in cl) and cd_col is None:
            cd_col = c

    if not statefp_col or not cd_col:
        logger.warning(
            f"Could not identify STATEFP/CD columns in shapefile. "
            f"Available: {list(joined.columns)}"
        )
        return {}

    result: dict[str, str] = {}
    for _, row in joined.iterrows():
        uid = row["facility_uid"]
        if uid in result:
            continue

        statefp = row.get(statefp_col)
        cd = row.get(cd_col)

        if statefp is not None and cd is not None and str(cd) != "nan":
            state_abbrev = fips_to_state.get(
                str(statefp).zfill(2), str(statefp)
            )
            cd_str = str(int(float(cd))).zfill(2)
            if cd_str == "00":
                cd_str = "AL"  # At-large district
            result[uid] = f"{state_abbrev}-{cd_str}"

    logger.info(f"Matched {len(result)} sites to congressional districts")
    return result


# ---------------------------------------------------------------------------
# County FIPS - Spatial Fill (for ~20 records with NULL county)
# ---------------------------------------------------------------------------

def spatial_fill_county_fips(
    sites: list[dict],
    county_shapefile: str,
) -> dict[str, tuple[str, str]]:
    """Spatial join to fill missing county FIPS via point-in-polygon.

    Processes the provided list of sites (caller filters as needed).
    Returns dict: facility_uid -> (5-digit FIPS, county_name).
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        logger.warning("geopandas/shapely not installed - skipping county fill")
        return {}

    shapefile_path = Path(county_shapefile)
    if not shapefile_path.exists():
        logger.warning(f"County shapefile not found: {county_shapefile}")
        return {}

    if not sites:
        logger.info("No sites to fill - skipping spatial fill")
        return {}

    logger.info(f"Loading county shapefile for {len(sites)} sites...")
    county_gdf = gpd.read_file(county_shapefile)
    county_gdf = county_gdf.to_crs(epsg=4326)

    points = [Point(s["longitude"], s["latitude"]) for s in sites]
    uids = [s["facility_uid"] for s in sites]

    sites_gdf = gpd.GeoDataFrame(
        {"facility_uid": uids}, geometry=points, crs="EPSG:4326",
    )

    joined = gpd.sjoin(sites_gdf, county_gdf, how="left", predicate="within")

    result: dict[str, tuple[str, str]] = {}
    for _, row in joined.iterrows():
        uid = row["facility_uid"]
        if uid in result:
            continue
        # Detect column names
        statefp = None
        countyfp = None
        name = None
        for c in row.index:
            cl = c.upper()
            if cl.startswith("STATEFP") and statefp is None:
                statefp = row[c]
            if cl.startswith("COUNTYFP") and countyfp is None:
                countyfp = row[c]
            if cl == "NAME" and name is None:
                name = row[c]

        if statefp is not None and countyfp is not None:
            fips_5 = f"{str(statefp).zfill(2)}{str(countyfp).zfill(3)}"
            county_name = str(name).upper() if name else ""
            result[uid] = (fips_5, county_name)
            logger.info(
                f"  Spatial fill: {uid[:8]}... -> {county_name} ({fips_5})"
            )

    return result


# ---------------------------------------------------------------------------
# Port Geo-Dictionary Loader
# ---------------------------------------------------------------------------

def _load_port_geo_dictionary(json_path: str | Path) -> dict[str, dict[str, Any]]:
    """Load port_geo_dictionary.json and return dict keyed by port_code.

    Each value has: sked_d_name, port_consolidated, port_coast, port_region.
    Returns empty dict if file not found.
    """
    path = Path(json_path)
    if not path.exists():
        logger.warning(f"Port geo-dictionary not found: {json_path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ports = data.get("ports", {})
    logger.info(f"Loaded port geo-dictionary: {len(ports)} ports")
    return ports


# ---------------------------------------------------------------------------
# Shapefile finders
# ---------------------------------------------------------------------------

def _find_cd_shapefile(reference_dir: str) -> Optional[str]:
    """Find Congressional District shapefile in reference_dir."""
    ref = Path(reference_dir)
    for shp in ref.rglob("*cd*119*.shp"):
        return str(shp)
    for shp in ref.rglob("*cd*.shp"):
        return str(shp)
    return None


def _find_county_shapefile(reference_dir: str) -> Optional[str]:
    """Find county shapefile in reference_dir."""
    ref = Path(reference_dir)
    for shp in ref.rglob("*county*.shp"):
        return str(shp)
    return None


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def enrich_master_sites(
    db_path: str,
    reference_dir: str,
    project_root: str,
) -> dict[str, int]:
    """Run all geographic enrichments on master_sites.

    All steps are local lookups or spatial joins - zero API calls.
    Returns dict of column -> enriched count.
    """
    from schema import migrate_add_geo_columns

    print(f"\n  Database: {db_path}")
    print(f"  Reference data: {reference_dir}")

    conn = duckdb.connect(db_path)
    migrate_add_geo_columns(conn)

    # Load all sites
    rows = conn.execute("""
        SELECT facility_uid, canonical_name, city, state, county,
               latitude, longitude
        FROM master_sites
    """).fetchall()

    sites = [
        {
            "facility_uid": r[0], "canonical_name": r[1],
            "city": r[2], "state": r[3], "county": r[4],
            "latitude": r[5], "longitude": r[6],
        }
        for r in rows
    ]
    print(f"  Loaded {len(sites):,} master sites for enrichment")

    # Build lookups
    fips_state = build_fips_state_lookup()
    census_regions = build_census_region_lookup()
    bea_regions = build_bea_region_lookup()
    epa_regions = build_epa_region_lookup()
    market_regions = build_market_region_lookup()
    port_coords = build_seaport_coordinates()

    # Load port geo-dictionary for port roll-up columns
    port_dict_path = (
        Path(reference_dir) / "port_geo_dictionary.json"
    )
    port_dict = _load_port_geo_dictionary(port_dict_path)

    # County FIPS from Census file
    county_fips_file = Path(reference_dir) / "national_county.txt"
    county_fips = load_county_fips(str(county_fips_file))

    # ---- Process all sites (steps 1-7, 9) ----
    columns = [
        "latitude_dms", "longitude_dms", "fips_state_code",
        "fips_county_code", "census_region", "census_division",
        "bea_region", "epa_region", "congressional_district",
        "market_region", "nearest_port_code",
        "nearest_port_name", "nearest_port_consolidated",
        "nearest_port_coast", "nearest_port_region",
    ]
    stats = {col: 0 for col in columns}
    updates: list[dict] = []

    for site in sites:
        uid = site["facility_uid"]
        state = site["state"]
        lat = site["latitude"]
        lon = site["longitude"]
        county = site["county"]
        upd: dict = {"facility_uid": uid}

        # 1. DMS coordinates
        if lat is not None and lon is not None:
            lat_dms, lon_dms = decimal_to_dms(lat, lon)
            upd["latitude_dms"] = lat_dms
            upd["longitude_dms"] = lon_dms
            stats["latitude_dms"] += 1
            stats["longitude_dms"] += 1

        # 2. FIPS state code
        if state in fips_state:
            upd["fips_state_code"] = fips_state[state]
            stats["fips_state_code"] += 1

        # 3. Census region + division
        if state in census_regions:
            region, division = census_regions[state]
            upd["census_region"] = region
            upd["census_division"] = division
            stats["census_region"] += 1
            stats["census_division"] += 1

        # 4. BEA region
        if state in bea_regions:
            upd["bea_region"] = bea_regions[state]
            stats["bea_region"] += 1

        # 5. EPA region
        if state in epa_regions:
            upd["epa_region"] = epa_regions[state]
            stats["epa_region"] += 1

        # 6. Market region
        if state in market_regions:
            upd["market_region"] = market_regions[state]
            stats["market_region"] += 1

        # 7. County FIPS (name match)
        if county and state:
            norm_county = _normalize_county(county)
            fips_5 = county_fips.get((state, norm_county))
            if fips_5:
                upd["fips_county_code"] = fips_5
                stats["fips_county_code"] += 1

        # 9. Nearest port + port identity roll-up
        if lat is not None and lon is not None:
            port_code, _dist = find_nearest_port(lat, lon, port_coords)
            if port_code:
                upd["nearest_port_code"] = port_code
                stats["nearest_port_code"] += 1

                # Look up port details from geo-dictionary
                port_info = port_dict.get(port_code)
                if port_info:
                    upd["nearest_port_name"] = port_info.get("sked_d_name", "")
                    upd["nearest_port_consolidated"] = port_info.get(
                        "port_consolidated", ""
                    )
                    upd["nearest_port_coast"] = port_info.get("port_coast", "")
                    upd["nearest_port_region"] = port_info.get("port_region", "")
                    stats["nearest_port_name"] += 1
                    stats["nearest_port_consolidated"] += 1
                    stats["nearest_port_coast"] += 1
                    stats["nearest_port_region"] += 1

        updates.append(upd)

    # 8. Congressional district (batch spatial join)
    cd_shapefile = _find_cd_shapefile(reference_dir)
    if cd_shapefile:
        print(f"  Running congressional district spatial join...")
        cd_results = spatial_join_congressional_districts(sites, cd_shapefile)
        for upd in updates:
            uid = upd["facility_uid"]
            if uid in cd_results:
                upd["congressional_district"] = cd_results[uid]
                stats["congressional_district"] += 1
    else:
        print("  WARNING: Congressional District shapefile not found - skipping")

    # 10. Spatial fill for ALL missing county FIPS (NULL county + name mismatches)
    county_shapefile = _find_county_shapefile(reference_dir)
    if county_shapefile:
        # Build list of sites still missing county FIPS
        uids_with_fips = {
            upd["facility_uid"]
            for upd in updates
            if "fips_county_code" in upd
        }
        missing_fips_sites = [
            s for s in sites
            if s["facility_uid"] not in uids_with_fips
            and s.get("latitude") is not None
            and s.get("longitude") is not None
        ]
        if missing_fips_sites:
            county_spatial = spatial_fill_county_fips(
                missing_fips_sites, county_shapefile,
            )
            for upd in updates:
                uid = upd["facility_uid"]
                if "fips_county_code" not in upd and uid in county_spatial:
                    fips_5, county_name = county_spatial[uid]
                    upd["fips_county_code"] = fips_5
                    stats["fips_county_code"] += 1
                    if county_name and county_name != "NAN":
                        upd["_county_fill"] = county_name

    # ---- Write all updates to DuckDB ----
    print(f"  Writing enrichment updates to database...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    county_fills = 0

    for upd in updates:
        uid = upd.pop("facility_uid")
        county_name_fill = upd.pop("_county_fill", None)

        if not upd and not county_name_fill:
            continue

        set_clauses = []
        values = []
        for col, val in upd.items():
            set_clauses.append(f"{col} = ?")
            values.append(val)

        if county_name_fill:
            set_clauses.append("county = ?")
            values.append(county_name_fill)
            county_fills += 1

        set_clauses.append("updated_at = ?")
        values.append(now)
        values.append(uid)

        conn.execute(
            f"UPDATE master_sites SET {', '.join(set_clauses)} "
            f"WHERE facility_uid = ?",
            values,
        )

    # Log enrichment run
    conn.execute("""
        INSERT INTO build_log (run_id, phase, started_at, finished_at,
                               sites_created, sites_updated, links_created, notes)
        VALUES (nextval('seq_run_id'), 'geo_enrichment',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                0, ?, 0, ?)
    """, [
        len(updates),
        f"Geographic identity enrichment: {len(columns)} columns, "
        f"{county_fills} county spatial fills",
    ])

    conn.close()

    # Print results
    print(f"\n{'=' * 60}")
    print(f"  Geographic Identity Enrichment - Complete")
    print(f"{'=' * 60}")
    print(f"  Total sites processed: {len(sites):,}")
    if county_fills:
        print(f"  Counties spatially filled: {county_fills}")
    print(f"\n  Column coverage:")
    for col in columns:
        count = stats[col]
        pct = (count / len(sites) * 100) if sites else 0
        print(f"    {col:<28s}: {count:>6,} / {len(sites):,} ({pct:.1f}%)")
    print(f"{'=' * 60}\n")

    return stats
