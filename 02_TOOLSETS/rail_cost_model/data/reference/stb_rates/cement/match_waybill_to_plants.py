"""
Match Waybill Cement Origins to EPA Cement Plants via BEA Economic Area codes.

Pipeline:
1. Assign each EPA cement plant a BEA code via haversine distance to BEA centroids
2. Join waybill records to plants on originbea = assigned BEA
3. Proportionally allocate tons/revenue when multiple plants share a BEA
4. Flag suppressed origins (000), Canadian imports (173+), and no-plant-in-BEA cases

Inputs:
  - cement_plants_epa.csv   (100 cement plants with lat/lon)
  - waybill_cement.csv      (156K waybill records with originbea)
  - BEA_AREAS from bea_complete.py (172 BEA centroids)

Outputs:
  - waybill_plant_matched.csv       (matched dataset)
  - waybill_plant_match_summary.txt (summary statistics)
"""

import csv
import math
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# BEA Economic Area centroids (from rail_analytics/src/bea_complete.py)
# Format: code -> (name, lat, lon)
# ---------------------------------------------------------------------------
BEA_AREAS = {
    '001': ('Bangor, ME', 44.8016, -68.7712),
    '002': ('Portland, ME', 43.6591, -70.2568),
    '003': ('Burlington, VT', 44.4759, -73.2121),
    '004': ('Albany, NY', 42.6526, -73.7562),
    '005': ('Syracuse, NY', 43.0481, -76.1474),
    '006': ('Rochester, NY', 43.1566, -77.6088),
    '007': ('Buffalo, NY', 42.8864, -78.8784),
    '008': ('State College, PA', 40.7934, -77.8600),
    '009': ('Harrisburg, PA', 40.2732, -76.8867),
    '010': ('Boston, MA', 42.3601, -71.0589),
    '011': ('Worcester, MA', 42.2626, -71.8023),
    '012': ('Providence, RI', 41.8240, -71.4128),
    '013': ('Hartford, CT', 41.7658, -72.6734),
    '014': ('New York, NY', 40.7128, -74.0060),
    '015': ('Binghamton, NY', 42.0987, -75.9180),
    '016': ('Scranton, PA', 41.4090, -75.6624),
    '017': ('Allentown, PA', 40.6084, -75.4902),
    '018': ('Philadelphia, PA', 39.9526, -75.1652),
    '019': ('Wilmington, DE', 39.7391, -75.5398),
    '020': ('Baltimore, MD', 39.2904, -76.6122),
    '021': ('Salisbury, MD', 38.3607, -75.5994),
    '022': ('Washington, DC', 38.9072, -77.0369),
    '023': ('Staunton, VA', 38.1496, -79.0717),
    '024': ('Richmond, VA', 37.5407, -77.4360),
    '025': ('Norfolk, VA', 36.8508, -76.2859),
    '026': ('Raleigh, NC', 35.7796, -78.6382),
    '027': ('Greenville, NC', 35.6127, -77.3664),
    '028': ('Charlotte, NC', 35.2271, -80.8431),
    '029': ('Wilmington, NC', 34.2257, -77.9447),
    '030': ('Fayetteville, NC', 35.0527, -78.8784),
    '031': ('Florence, SC', 34.1954, -79.7626),
    '032': ('Charleston, SC', 32.7765, -79.9311),
    '033': ('Columbia, SC', 34.0007, -81.0348),
    '034': ('Augusta, GA', 33.4735, -82.0105),
    '035': ('Savannah, GA', 32.0809, -81.0912),
    '036': ('Macon, GA', 32.8407, -83.6324),
    '037': ('Albany, GA', 31.5785, -84.1557),
    '038': ('Dothan, AL', 31.2232, -85.3905),
    '039': ('Tallahassee, FL', 30.4383, -84.2807),
    '040': ('Jacksonville, FL', 30.3322, -81.6557),
    '041': ('Orlando, FL', 28.5383, -81.3792),
    '042': ('Tampa, FL', 27.9506, -82.4572),
    '043': ('Fort Myers, FL', 26.6406, -81.8723),
    '044': ('Miami, FL', 25.7617, -80.1918),
    '045': ('Chattanooga, TN', 35.0456, -85.3097),
    '046': ('Atlanta, GA', 33.7490, -84.3880),
    '047': ('Columbus, GA', 32.4610, -84.9877),
    '048': ('Birmingham, AL', 33.5186, -86.8104),
    '049': ('Huntsville, AL', 34.7304, -86.5861),
    '050': ('Nashville, TN', 36.1627, -86.7816),
    '051': ('Knoxville, TN', 35.9606, -83.9207),
    '052': ('Johnson City, TN', 36.3134, -82.3535),
    '053': ('Charleston, WV', 38.3498, -81.6326),
    '054': ('Lexington, KY', 38.0406, -84.5037),
    '055': ('Louisville, KY', 38.2527, -85.7585),
    '056': ('Evansville, IN', 37.9716, -87.5711),
    '057': ('Fort Wayne, IN', 41.0793, -85.1394),
    '058': ('Grand Rapids, MI', 42.9634, -85.6681),
    '059': ('Traverse City, MI', 44.7631, -85.6206),
    '060': ('Saginaw, MI', 43.4195, -83.9508),
    '061': ('Detroit, MI', 42.3314, -83.0458),
    '062': ('Toledo, OH', 41.6528, -83.5379),
    '063': ('Cleveland, OH', 41.4993, -81.6944),
    '064': ('Columbus, OH', 39.9612, -82.9988),
    '065': ('Youngstown, OH', 41.0998, -80.6495),
    '066': ('Pittsburgh, PA', 40.4406, -79.9959),
    '067': ('Wheeling, WV', 40.0640, -80.7209),
    '068': ('Cincinnati, OH', 39.1031, -84.5120),
    '069': ('Dayton, OH', 39.7589, -84.1916),
    '070': ('Indianapolis, IN', 39.7684, -86.1581),
    '071': ('Terre Haute, IN', 39.4667, -87.4139),
    '072': ('Springfield, IL', 39.7817, -89.6501),
    '073': ('St. Louis, MO', 38.6270, -90.1994),
    '074': ('Paducah, KY', 37.0834, -88.6001),
    '075': ('Springfield, MO', 37.2090, -93.2923),
    '076': ('Joplin, MO', 37.0842, -94.5133),
    '077': ('Fort Smith, AR', 35.3859, -94.3985),
    '078': ('Fayetteville, AR', 36.0822, -94.1719),
    '079': ('Little Rock, AR', 34.7465, -92.2896),
    '080': ('Monroe, LA', 32.5093, -92.1193),
    '081': ('Jackson, MS', 32.2988, -90.1848),
    '082': ('Shreveport, LA', 32.5252, -93.7502),
    '083': ('Tyler, TX', 32.3513, -95.3011),
    '084': ('Beaumont, TX', 30.0802, -94.1266),
    '085': ('Lake Charles, LA', 30.2266, -93.2174),
    '086': ('Baton Rouge, LA', 30.4515, -91.1871),
    '087': ('New Orleans, LA', 29.9511, -90.0715),
    '088': ('Mobile, AL', 30.6954, -88.0399),
    '089': ('Pensacola, FL', 30.4213, -87.2169),
    '090': ('Biloxi, MS', 30.3960, -88.8853),
    '091': ('Montgomery, AL', 32.3792, -86.3077),
    '092': ('Meridian, MS', 32.3643, -88.7037),
    '093': ('Memphis, TN', 35.1495, -90.0490),
    '094': ('Tupelo, MS', 34.2576, -88.7034),
    '095': ('Greenville, MS', 33.4101, -91.0618),
    '096': ('Fargo, ND', 46.8772, -96.7898),
    '097': ('Minneapolis, MN', 44.9778, -93.2650),
    '098': ('Duluth, MN', 46.7867, -92.1005),
    '099': ('La Crosse, WI', 43.8014, -91.2396),
    '100': ('Eau Claire, WI', 44.8113, -91.4985),
    '101': ('Wausau, WI', 44.9591, -89.6301),
    '102': ('Green Bay, WI', 44.5133, -88.0133),
    '103': ('Madison, WI', 43.0731, -89.4012),
    '104': ('Milwaukee, WI', 43.0389, -87.9065),
    '105': ('Chicago, IL', 41.8781, -87.6298),
    '106': ('Rockford, IL', 42.2711, -89.0940),
    '107': ('Davenport, IA', 41.5236, -90.5776),
    '108': ('Cedar Rapids, IA', 41.9779, -91.6656),
    '109': ('Des Moines, IA', 41.5868, -93.6250),
    '110': ('Sioux Falls, SD', 43.5446, -96.7311),
    '111': ('Aberdeen, SD', 45.4647, -98.4865),
    '112': ('Rapid City, SD', 44.0805, -103.2310),
    '113': ('Bismarck, ND', 46.8083, -100.7837),
    '114': ('Minot, ND', 48.2325, -101.2963),
    '115': ('Great Falls, MT', 47.5053, -111.3008),
    '116': ('Billings, MT', 45.7833, -108.5007),
    '117': ('Sioux City, IA', 42.4963, -96.4049),
    '118': ('Omaha, NE', 41.2565, -95.9345),
    '119': ('Lincoln, NE', 40.8258, -96.6852),
    '120': ('Grand Island, NE', 40.9264, -98.3420),
    '121': ('North Platte, NE', 41.1403, -100.7601),
    '122': ('Denver, CO', 39.7392, -104.9903),
    '123': ('Colorado Springs, CO', 38.8339, -104.8214),
    '124': ('Pueblo, CO', 38.2545, -104.6091),
    '125': ('Albuquerque, NM', 35.0844, -106.6504),
    '126': ('Amarillo, TX', 35.2220, -101.8313),
    '127': ('Lubbock, TX', 33.5779, -101.8552),
    '128': ('Odessa, TX', 31.8457, -102.3676),
    '129': ('Abilene, TX', 32.4487, -99.7331),
    '130': ('San Angelo, TX', 31.4638, -100.4370),
    '131': ('Dallas, TX', 32.7767, -96.7970),
    '132': ('Waco, TX', 31.5493, -97.1467),
    '133': ('Austin, TX', 30.2672, -97.7431),
    '134': ('Houston, TX', 29.7604, -95.3698),
    '135': ('San Antonio, TX', 29.4241, -98.4936),
    '136': ('Corpus Christi, TX', 27.8006, -97.3964),
    '137': ('McAllen, TX', 26.2034, -98.2300),
    '138': ('El Paso, TX', 31.7619, -106.4850),
    '139': ('Scottsbluff, NE', 41.8666, -103.6672),
    '140': ('Casper, WY', 42.8666, -106.3131),
    '141': ('Salt Lake City, UT', 40.7608, -111.8910),
    '142': ('Idaho Falls, ID', 43.4666, -112.0341),
    '143': ('Boise, ID', 43.6150, -116.2023),
    '144': ('Missoula, MT', 46.8721, -113.9940),
    '145': ('Spokane, WA', 47.6587, -117.4260),
    '146': ('Richland, WA', 46.2856, -119.2845),
    '147': ('Pendleton, OR', 45.6721, -118.7886),
    '148': ('Portland, OR', 45.5152, -122.6784),
    '149': ('Eugene, OR', 44.0521, -123.0868),
    '150': ('Medford, OR', 42.3265, -122.8756),
    '151': ('Redding, CA', 40.5865, -122.3917),
    '152': ('Sacramento, CA', 38.5816, -121.4944),
    '153': ('Reno, NV', 39.5296, -119.8138),
    '154': ('Las Vegas, NV', 36.1699, -115.1398),
    '155': ('Flagstaff, AZ', 35.1983, -111.6513),
    '156': ('Phoenix, AZ', 33.4484, -112.0740),
    '157': ('Tucson, AZ', 32.2226, -110.9747),
    '158': ('San Francisco, CA', 37.7749, -122.4194),
    '159': ('San Jose, CA', 37.3382, -121.8863),
    '160': ('Fresno, CA', 36.7378, -119.7871),
    '161': ('Bakersfield, CA', 35.3733, -119.0187),
    '162': ('Santa Barbara, CA', 34.4208, -119.6982),
    '163': ('Los Angeles, CA', 34.0522, -118.2437),
    '164': ('San Diego, CA', 32.7157, -117.1611),
    '165': ('Seattle, WA', 47.6062, -122.3321),
    '166': ('Bellingham, WA', 48.7519, -122.4787),
    '167': ('Olympia, WA', 47.0379, -122.9007),
    '168': ('Anchorage, AK', 61.2181, -149.9003),
    '169': ('Fairbanks, AK', 64.8378, -147.7164),
    '170': ('Juneau, AK', 58.3019, -134.4197),
    '171': ('Honolulu, HI', 21.3069, -157.8583),
    '172': ('Hilo, HI', 19.7074, -155.0847),
}

# Canadian province BEA codes used in STB waybill
CANADIAN_BEA = {
    '173': 'British Columbia',
    '174': 'Alberta',
    '175': 'Saskatchewan',
    '176': 'Manitoba',
    '177': 'Ontario',
    '178': 'Quebec',
    '179': 'New Brunswick',
    '180': 'Nova Scotia',
    '181': 'Prince Edward Island',
    '182': 'Newfoundland',
    '183': 'Yukon/NWT',
}


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = (math.radians(x) for x in (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def load_plants(path):
    """Load cement plants and return list of dicts."""
    plants = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = row.get('latitude', '').strip()
            lon = row.get('longitude', '').strip()
            if not lat or not lon:
                continue
            plants.append({
                'facility_id': row['facility_id'].strip(),
                'facility_name': row['facility_name'].strip(),
                'city': row.get('city', '').strip(),
                'state': row.get('state', '').strip(),
                'county': row.get('county', '').strip(),
                'latitude': float(lat),
                'longitude': float(lon),
                'parent_company': row.get('parent_company', '').strip(),
            })
    return plants


def assign_bea_to_plants(plants):
    """Assign nearest BEA code to each plant via haversine distance."""
    bea_list = [(code, info[1], info[2]) for code, info in BEA_AREAS.items()
                if info[1] is not None]  # skip '000'

    for plant in plants:
        best_code = None
        best_dist = float('inf')
        for code, bea_lat, bea_lon in bea_list:
            d = haversine_miles(plant['latitude'], plant['longitude'], bea_lat, bea_lon)
            if d < best_dist:
                best_dist = d
                best_code = code
        plant['assigned_bea'] = best_code
        plant['bea_name'] = BEA_AREAS[best_code][0]
        plant['bea_distance_mi'] = round(best_dist, 1)
    return plants


def build_bea_plant_index(plants):
    """Build dict: BEA code -> list of plants in that area."""
    idx = defaultdict(list)
    for p in plants:
        idx[p['assigned_bea']].append(p)
    return idx


def load_waybill(path):
    """Load waybill records, return list of dicts with key fields."""
    records = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            originbea_raw = row.get('originbea', '').strip()
            # Pad to 3 digits
            originbea = originbea_raw.zfill(3) if originbea_raw else '000'

            # Parse numeric fields safely
            def safe_float(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0

            def safe_int(val):
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return 0

            records.append({
                'originbea': originbea,
                'terminationbea': row.get('terminationbea', '').strip().zfill(3),
                'datayear': safe_int(row.get('datayear', '')),
                'month': safe_int(row.get('month', '')),
                'stcc': row.get('stcc', '').strip(),
                'stcc_5_description': row.get('stcc_5_description', '').strip(),
                'actualweightintons': safe_float(row.get('actualweightintons', '')),
                'freightrevenue': safe_float(row.get('freightrevenue', '')),
                'exactexpansionfactor': safe_float(row.get('exactexpansionfactor', '')),
                'extons': safe_float(row.get('extons', '')),
                'exrev': safe_float(row.get('exrev', '')),
                'excars': safe_float(row.get('excars', '')),
                'numberofcarloads': safe_int(row.get('numberofcarloads', '')),
                'shipment_distance_category': row.get('shipment_distance_category', '').strip(),
                'typeofmoveimportexport': row.get('typeofmoveimportexport', '').strip(),
                'waybilldate': row.get('waybilldate', '').strip(),
            })
    return records



# BEA areas identified as Canadian cement re-origination points.
# These have no US cement plants but show steady production-level volumes
# traced to Canadian rail terminals (e.g., Lafarge Dakota / Amrize terminals
# in Fargo receiving cement by rail from Calgary, AB).
CANADIAN_REORIGINATION_BEAS = {'096'}  # Fargo, ND


def classify_origin(originbea):
    """Classify an origin BEA code into a match category."""
    if originbea == '000':
        return 'suppressed'
    if originbea in CANADIAN_REORIGINATION_BEAS:
        return 'canadian_reorigination'
    code_int = int(originbea)
    if 173 <= code_int <= 183:
        return 'canadian_import'
    if code_int > 183:
        return 'foreign_other'
    return 'domestic'


def match_waybill_to_plants(waybill, bea_plant_idx):
    """Match waybill records to plants, returning expanded output rows."""
    matched = []

    for rec in waybill:
        origin_class = classify_origin(rec['originbea'])

        if origin_class == 'suppressed':
            row = {**rec,
                   'match_status': 'suppressed',
                   'plant_count_in_bea': 0,
                   'allocation_share': 0.0,
                   'allocated_extons': 0.0,
                   'allocated_exrev': 0.0,
                   'allocated_excars': 0.0,
                   'plant_facility_id': '',
                   'plant_facility_name': '',
                   'plant_city': '',
                   'plant_state': '',
                   'plant_latitude': '',
                   'plant_longitude': '',
                   'bea_name': 'Suppressed',
                   'bea_distance_mi': ''}
            matched.append(row)
            continue

        if origin_class == 'canadian_import':
            prov = CANADIAN_BEA.get(rec['originbea'], 'Unknown Canada')
            row = {**rec,
                   'match_status': 'canadian_import',
                   'plant_count_in_bea': 0,
                   'allocation_share': 0.0,
                   'allocated_extons': 0.0,
                   'allocated_exrev': 0.0,
                   'allocated_excars': 0.0,
                   'plant_facility_id': '',
                   'plant_facility_name': '',
                   'plant_city': '',
                   'plant_state': '',
                   'plant_latitude': '',
                   'plant_longitude': '',
                   'bea_name': prov,
                   'bea_distance_mi': ''}
            matched.append(row)
            continue

        if origin_class == 'canadian_reorigination':
            bea_info = BEA_AREAS.get(rec['originbea'])
            bea_name = bea_info[0] if bea_info else f"BEA {rec['originbea']}"
            row = {**rec,
                   'match_status': 'canadian_reorigination',
                   'plant_count_in_bea': 0,
                   'allocation_share': 0.0,
                   'allocated_extons': 0.0,
                   'allocated_exrev': 0.0,
                   'allocated_excars': 0.0,
                   'plant_facility_id': '',
                   'plant_facility_name': '',
                   'plant_city': '',
                   'plant_state': '',
                   'plant_latitude': '',
                   'plant_longitude': '',
                   'bea_name': f'{bea_name} (Canadian re-origination)',
                   'bea_distance_mi': ''}
            matched.append(row)
            continue

        if origin_class == 'foreign_other':
            row = {**rec,
                   'match_status': 'foreign_other',
                   'plant_count_in_bea': 0,
                   'allocation_share': 0.0,
                   'allocated_extons': 0.0,
                   'allocated_exrev': 0.0,
                   'allocated_excars': 0.0,
                   'plant_facility_id': '',
                   'plant_facility_name': '',
                   'plant_city': '',
                   'plant_state': '',
                   'plant_latitude': '',
                   'plant_longitude': '',
                   'bea_name': 'Foreign/Other',
                   'bea_distance_mi': ''}
            matched.append(row)
            continue

        # Domestic origin - look up plants in this BEA
        plants = bea_plant_idx.get(rec['originbea'], [])
        n = len(plants)

        if n == 0:
            bea_info = BEA_AREAS.get(rec['originbea'])
            bea_name = bea_info[0] if bea_info else f"BEA {rec['originbea']}"
            row = {**rec,
                   'match_status': 'no_plant_in_bea',
                   'plant_count_in_bea': 0,
                   'allocation_share': 0.0,
                   'allocated_extons': 0.0,
                   'allocated_exrev': 0.0,
                   'allocated_excars': 0.0,
                   'plant_facility_id': '',
                   'plant_facility_name': '',
                   'plant_city': '',
                   'plant_state': '',
                   'plant_latitude': '',
                   'plant_longitude': '',
                   'bea_name': bea_name,
                   'bea_distance_mi': ''}
            matched.append(row)

        elif n == 1:
            p = plants[0]
            row = {**rec,
                   'match_status': 'unique_match',
                   'plant_count_in_bea': 1,
                   'allocation_share': 1.0,
                   'allocated_extons': rec['extons'],
                   'allocated_exrev': rec['exrev'],
                   'allocated_excars': rec['excars'],
                   'plant_facility_id': p['facility_id'],
                   'plant_facility_name': p['facility_name'],
                   'plant_city': p['city'],
                   'plant_state': p['state'],
                   'plant_latitude': p['latitude'],
                   'plant_longitude': p['longitude'],
                   'bea_name': p['bea_name'],
                   'bea_distance_mi': p['bea_distance_mi']}
            matched.append(row)

        else:
            # Multiple plants - proportional split (equal allocation)
            share = 1.0 / n
            status = 'proportional_split'
            for p in plants:
                row = {**rec,
                       'match_status': status,
                       'plant_count_in_bea': n,
                       'allocation_share': round(share, 6),
                       'allocated_extons': round(rec['extons'] * share, 2),
                       'allocated_exrev': round(rec['exrev'] * share, 2),
                       'allocated_excars': round(rec['excars'] * share, 2),
                       'plant_facility_id': p['facility_id'],
                       'plant_facility_name': p['facility_name'],
                       'plant_city': p['city'],
                       'plant_state': p['state'],
                       'plant_latitude': p['latitude'],
                       'plant_longitude': p['longitude'],
                       'bea_name': p['bea_name'],
                       'bea_distance_mi': p['bea_distance_mi']}
                matched.append(row)

    return matched


OUTPUT_FIELDS = [
    'datayear', 'month', 'originbea', 'terminationbea',
    'stcc', 'stcc_5_description',
    'actualweightintons', 'freightrevenue',
    'exactexpansionfactor', 'extons', 'exrev', 'excars',
    'numberofcarloads', 'shipment_distance_category',
    'typeofmoveimportexport', 'waybilldate',
    'match_status', 'plant_count_in_bea', 'allocation_share',
    'allocated_extons', 'allocated_exrev', 'allocated_excars',
    'plant_facility_id', 'plant_facility_name',
    'plant_city', 'plant_state',
    'plant_latitude', 'plant_longitude',
    'bea_name', 'bea_distance_mi',
]


def write_matched_csv(matched, path):
    """Write matched records to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(matched)
    print(f"  Wrote {len(matched):,} rows to {path}")


def generate_summary(plants, waybill, matched, path):
    """Generate summary statistics text file."""
    lines = []
    lines.append("=" * 72)
    lines.append("WAYBILL-TO-CEMENT-PLANT MATCHING SUMMARY")
    lines.append("=" * 72)

    # --- Input summary ---
    lines.append(f"\nINPUT FILES")
    lines.append(f"  Cement plants loaded:     {len(plants):>6,}")
    lines.append(f"  Waybill records loaded:   {len(waybill):>6,}")
    lines.append(f"  Output matched rows:      {len(matched):>6,}")

    # --- Plant BEA assignment ---
    lines.append(f"\nPLANT BEA ASSIGNMENTS")
    bea_counts = defaultdict(int)
    for p in plants:
        bea_counts[p['assigned_bea']] += 1
    beas_with_plants = len(bea_counts)
    multi_plant_beas = sum(1 for c in bea_counts.values() if c > 1)
    lines.append(f"  Distinct BEA areas with plants: {beas_with_plants}")
    lines.append(f"  BEA areas with >1 plant:        {multi_plant_beas}")
    lines.append(f"  Max plants in single BEA:       {max(bea_counts.values())}")

    lines.append(f"\n  Plants per BEA area:")
    for bea_code in sorted(bea_counts, key=lambda x: int(x)):
        plant_names = [p['facility_name'] for p in plants if p['assigned_bea'] == bea_code]
        bea_name = BEA_AREAS[bea_code][0]
        lines.append(f"    BEA {bea_code} ({bea_name}): {bea_counts[bea_code]} plant(s)")
        for name in sorted(plant_names):
            lines.append(f"      - {name}")

    # --- Match status breakdown ---
    lines.append(f"\nMATCH STATUS BREAKDOWN (waybill records)")
    status_counts = defaultdict(int)
    status_extons = defaultdict(float)
    status_exrev = defaultdict(float)
    for row in matched:
        s = row['match_status']
        status_counts[s] += 1
        # For allocated values, use those; for unmatched, use original
        if s in ('unique_match', 'proportional_split'):
            status_extons[s] += row['allocated_extons']
            status_exrev[s] += row['allocated_exrev']
        else:
            status_extons[s] += row['extons']
            status_exrev[s] += row['exrev']

    total_rows = len(matched)
    total_waybill = len(waybill)
    for s in ['unique_match', 'proportional_split', 'no_plant_in_bea',
              'suppressed', 'canadian_import', 'canadian_reorigination',
              'foreign_other']:
        c = status_counts.get(s, 0)
        pct = c / total_rows * 100 if total_rows else 0
        pct_wb = 0
        # For waybill-level percentage, use input count
        # (suppressed/canadian/no_plant are 1:1 with waybill records)
        if s in ('suppressed', 'canadian_import', 'foreign_other', 'no_plant_in_bea'):
            pct_wb = c / total_waybill * 100 if total_waybill else 0
        lines.append(f"  {s:25s}: {c:>8,} rows ({pct:5.1f}%)  "
                     f"extons={status_extons.get(s, 0):>12,.0f}  "
                     f"exrev=${status_exrev.get(s, 0):>13,.0f}")

    lines.append(f"\n  Waybill-level suppression rate: "
                 f"{status_counts.get('suppressed', 0) / total_waybill * 100:.1f}% "
                 f"({status_counts.get('suppressed', 0):,} of {total_waybill:,})")

    # --- Matched plant summary ---
    lines.append(f"\nMATCHED PLANT SUMMARY (unique_match + proportional_split)")
    plant_tons = defaultdict(float)
    plant_rev = defaultdict(float)
    plant_rows = defaultdict(int)
    for row in matched:
        if row['match_status'] in ('unique_match', 'proportional_split'):
            key = (row['plant_facility_id'], row['plant_facility_name'], row['plant_state'])
            plant_tons[key] += row['allocated_extons']
            plant_rev[key] += row['allocated_exrev']
            plant_rows[key] += 1

    lines.append(f"  Plants with matched shipments: {len(plant_tons)}")
    total_matched_tons = sum(plant_tons.values())
    total_matched_rev = sum(plant_rev.values())
    lines.append(f"  Total allocated extons:  {total_matched_tons:>14,.0f}")
    lines.append(f"  Total allocated exrev:   ${total_matched_rev:>13,.0f}")

    lines.append(f"\n  Top 20 plants by allocated tons:")
    ranked = sorted(plant_tons.items(), key=lambda x: -x[1])[:20]
    for (fid, fname, st), tons in ranked:
        rev = plant_rev[(fid, fname, st)]
        rows = plant_rows[(fid, fname, st)]
        lines.append(f"    {fname[:45]:45s} {st:2s}  "
                     f"tons={tons:>12,.0f}  rev=${rev:>11,.0f}  rows={rows:>5,}")

    # --- Year breakdown ---
    lines.append(f"\nYEAR BREAKDOWN (all waybill records)")
    year_counts = defaultdict(lambda: {'records': 0, 'extons': 0, 'exrev': 0})
    for rec in waybill:
        yr = rec['datayear']
        year_counts[yr]['records'] += 1
        year_counts[yr]['extons'] += rec['extons']
        year_counts[yr]['exrev'] += rec['exrev']

    for yr in sorted(year_counts):
        d = year_counts[yr]
        lines.append(f"  {yr}: {d['records']:>6,} records  "
                     f"extons={d['extons']:>12,.0f}  exrev=${d['exrev']:>13,.0f}")

    # --- No-plant BEA areas ---
    lines.append(f"\nNO-PLANT BEA AREAS (domestic origins with no assigned plant)")
    no_plant_beas = defaultdict(lambda: {'count': 0, 'extons': 0})
    for row in matched:
        if row['match_status'] == 'no_plant_in_bea':
            bea = row['originbea']
            no_plant_beas[bea]['count'] += 1
            no_plant_beas[bea]['extons'] += row['extons']

    if no_plant_beas:
        for bea in sorted(no_plant_beas, key=lambda x: -no_plant_beas[x]['extons']):
            d = no_plant_beas[bea]
            bea_info = BEA_AREAS.get(bea)
            bea_name = bea_info[0] if bea_info else f'BEA {bea}'
            lines.append(f"  BEA {bea} ({bea_name}): "
                         f"{d['count']:>5,} records  extons={d['extons']:>10,.0f}")
    else:
        lines.append("  (none)")

    lines.append(f"\n{'=' * 72}")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  Wrote summary to {path}")
    print(text)


def main():
    plants_path = os.path.join(SCRIPT_DIR, 'cement_plants_epa.csv')
    waybill_path = os.path.join(SCRIPT_DIR, 'waybill_cement.csv')
    output_csv = os.path.join(SCRIPT_DIR, 'waybill_plant_matched.csv')
    output_summary = os.path.join(SCRIPT_DIR, 'waybill_plant_match_summary.txt')

    # Step 1: Load and assign BEA codes to plants
    print("Step 1: Loading cement plants and assigning BEA codes...")
    plants = load_plants(plants_path)
    plants = assign_bea_to_plants(plants)
    print(f"  Loaded {len(plants)} plants, assigned to "
          f"{len(set(p['assigned_bea'] for p in plants))} distinct BEA areas")

    # Step 2: Build BEA -> plant index
    bea_plant_idx = build_bea_plant_index(plants)

    # Step 3: Load waybill
    print("Step 2: Loading waybill records...")
    waybill = load_waybill(waybill_path)
    print(f"  Loaded {len(waybill):,} waybill records")

    # Step 4: Match
    print("Step 3: Matching waybill origins to plants...")
    matched = match_waybill_to_plants(waybill, bea_plant_idx)

    # Step 5: Write outputs
    print("Step 4: Writing outputs...")
    write_matched_csv(matched, output_csv)
    generate_summary(plants, waybill, matched, output_summary)

    print("\nDone.")


if __name__ == '__main__':
    main()
