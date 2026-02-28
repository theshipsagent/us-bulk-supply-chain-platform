"""
FAF (Freight Analysis Framework) Data Module

Provides data structures and loading functions for FAF multimodal freight data.
Includes SCTG commodity codes, FAF zones, transportation modes, and crosswalk tables.
"""

# =============================================================================
# SCTG COMMODITY CODES (Standard Classification of Transported Goods)
# 42 two-digit categories used by FAF
# =============================================================================

SCTG_CODES = [
    # Code, Name, Group, Rail Intensive, STCC Mapping
    ('01', 'Live animals and fish', 'Agriculture', False, '01'),
    ('02', 'Cereal grains', 'Agriculture', True, '01'),
    ('03', 'Other agricultural products', 'Agriculture', True, '01'),
    ('04', 'Animal feed and products of animal origin', 'Agriculture', True, '01'),
    ('05', 'Meat, fish, seafood, and preparations', 'Food', False, '20'),
    ('06', 'Milled grain products and preparations', 'Food', False, '20'),
    ('07', 'Other prepared foodstuffs and fats and oils', 'Food', False, '20'),
    ('08', 'Alcoholic beverages', 'Food', False, '20'),
    ('09', 'Tobacco products', 'Food', False, '21'),
    ('10', 'Monumental or building stone', 'Mining', True, '14'),
    ('11', 'Natural sands', 'Mining', True, '14'),
    ('12', 'Gravel and crushed stone', 'Mining', True, '14'),
    ('13', 'Nonmetallic minerals n.e.c.', 'Mining', True, '14'),
    ('14', 'Metallic ores and concentrates', 'Mining', True, '10'),
    ('15', 'Coal', 'Mining', True, '11'),
    ('16', 'Crude petroleum oil', 'Energy', True, '13'),
    ('17', 'Gasoline and aviation turbine fuel', 'Energy', False, '29'),
    ('18', 'Fuel oils', 'Energy', False, '29'),
    ('19', 'Coal and petroleum products, n.e.c.', 'Energy', True, '29'),
    ('20', 'Basic chemicals', 'Chemicals', True, '28'),
    ('21', 'Pharmaceutical products', 'Chemicals', False, '28'),
    ('22', 'Fertilizers', 'Chemicals', True, '28'),
    ('23', 'Chemical products and preparations', 'Chemicals', True, '28'),
    ('24', 'Plastics and rubber', 'Manufacturing', False, '30'),
    ('25', 'Logs and other wood in the rough', 'Forest Products', True, '24'),
    ('26', 'Wood products', 'Forest Products', True, '24'),
    ('27', 'Pulp, newsprint, paper, and paperboard', 'Forest Products', True, '26'),
    ('28', 'Paper or paperboard articles', 'Forest Products', False, '26'),
    ('29', 'Printed products', 'Manufacturing', False, '27'),
    ('30', 'Textiles, leather, and articles', 'Manufacturing', False, '22'),
    ('31', 'Nonmetal mineral products', 'Manufacturing', True, '32'),  # CEMENT!
    ('32', 'Base metal in primary or semi-finished forms', 'Manufacturing', True, '33'),
    ('33', 'Articles of base metal', 'Manufacturing', True, '33'),
    ('34', 'Machinery', 'Manufacturing', False, '35'),
    ('35', 'Electronic and electrical equipment', 'Manufacturing', False, '36'),
    ('36', 'Motorized and other vehicles (including parts)', 'Manufacturing', True, '37'),
    ('37', 'Transportation equipment, n.e.c.', 'Manufacturing', True, '37'),
    ('38', 'Precision instruments and apparatus', 'Manufacturing', False, '38'),
    ('39', 'Furniture, mattresses and mattress supports', 'Manufacturing', False, '25'),
    ('40', 'Miscellaneous manufactured products', 'Manufacturing', False, '39'),
    ('41', 'Waste and scrap', 'Waste', True, '40'),
    ('43', 'Mixed freight', 'Mixed', False, '46'),
]

# =============================================================================
# TRANSPORTATION MODES
# =============================================================================

TRANSPORT_MODES = [
    # Code, Name, Category
    (1, 'Truck', 'Surface'),
    (2, 'Rail', 'Surface'),
    (3, 'Water', 'Water'),
    (4, 'Air (includes truck-air)', 'Air'),
    (5, 'Multiple modes & mail', 'Intermodal'),
    (6, 'Pipeline', 'Pipeline'),
    (7, 'Other and unknown', 'Other'),
    (8, 'No domestic mode', 'Other'),
]

# =============================================================================
# FAF ZONES (132 CFS/FAF domestic zones)
# Derived from Commodity Flow Survey geographic areas
# =============================================================================

FAF_ZONES = [
    # Zone Code, Name, Type, State FIPS, State Name, Lat, Lon
    # Alabama
    ('011', 'Birmingham, AL', 'MA', '01', 'Alabama', 33.5207, -86.8025),
    ('012', 'Rest of Alabama', 'ROS', '01', 'Alabama', 32.3182, -86.9023),
    # Alaska
    ('020', 'Alaska', 'Whole State', '02', 'Alaska', 64.2008, -152.4937),
    # Arizona
    ('041', 'Phoenix, AZ', 'MA', '04', 'Arizona', 33.4484, -112.0740),
    ('042', 'Rest of Arizona', 'ROS', '04', 'Arizona', 34.0489, -111.0937),
    # Arkansas
    ('051', 'Little Rock, AR', 'MA', '05', 'Arkansas', 34.7465, -92.2896),
    ('052', 'Rest of Arkansas', 'ROS', '05', 'Arkansas', 35.2010, -91.8318),
    # California
    ('061', 'Los Angeles, CA', 'MA', '06', 'California', 34.0522, -118.2437),
    ('062', 'Fresno, CA', 'MA', '06', 'California', 36.7378, -119.7871),
    ('063', 'Sacramento, CA', 'MA', '06', 'California', 38.5816, -121.4944),
    ('064', 'San Diego, CA', 'MA', '06', 'California', 32.7157, -117.1611),
    ('065', 'San Francisco, CA', 'MA', '06', 'California', 37.7749, -122.4194),
    ('066', 'San Jose, CA', 'MA', '06', 'California', 37.3382, -121.8863),
    ('067', 'Rest of California', 'ROS', '06', 'California', 36.7783, -119.4179),
    # Colorado
    ('081', 'Denver, CO', 'MA', '08', 'Colorado', 39.7392, -104.9903),
    ('082', 'Rest of Colorado', 'ROS', '08', 'Colorado', 39.5501, -105.7821),
    # Connecticut
    ('091', 'Bridgeport, CT', 'MA', '09', 'Connecticut', 41.1865, -73.1952),
    ('092', 'Hartford, CT', 'MA', '09', 'Connecticut', 41.7658, -72.6734),
    ('093', 'New Haven, CT', 'MA', '09', 'Connecticut', 41.3083, -72.9279),
    ('094', 'Rest of Connecticut', 'ROS', '09', 'Connecticut', 41.6032, -73.0877),
    # Delaware
    ('100', 'Delaware', 'Whole State', '10', 'Delaware', 38.9108, -75.5277),
    # DC
    ('111', 'Washington, DC', 'MA', '11', 'DC', 38.9072, -77.0369),
    # Florida
    ('121', 'Jacksonville, FL', 'MA', '12', 'Florida', 30.3322, -81.6557),
    ('122', 'Miami, FL', 'MA', '12', 'Florida', 25.7617, -80.1918),
    ('123', 'Orlando, FL', 'MA', '12', 'Florida', 28.5383, -81.3792),
    ('124', 'Tampa, FL', 'MA', '12', 'Florida', 27.9506, -82.4572),
    ('125', 'Rest of Florida', 'ROS', '12', 'Florida', 27.6648, -81.5158),
    # Georgia
    ('131', 'Atlanta, GA', 'MA', '13', 'Georgia', 33.7490, -84.3880),
    ('132', 'Savannah, GA', 'MA', '13', 'Georgia', 32.0809, -81.0912),
    ('133', 'Rest of Georgia', 'ROS', '13', 'Georgia', 32.1656, -82.9001),
    # Hawaii
    ('150', 'Hawaii', 'Whole State', '15', 'Hawaii', 19.8968, -155.5828),
    # Idaho
    ('160', 'Idaho', 'Whole State', '16', 'Idaho', 44.0682, -114.7420),
    # Illinois
    ('171', 'Chicago, IL', 'MA', '17', 'Illinois', 41.8781, -87.6298),
    ('172', 'Rest of Illinois', 'ROS', '17', 'Illinois', 40.6331, -89.3985),
    # Indiana
    ('181', 'Indianapolis, IN', 'MA', '18', 'Indiana', 39.7684, -86.1581),
    ('182', 'Rest of Indiana', 'ROS', '18', 'Indiana', 40.2672, -86.1349),
    # Iowa
    ('191', 'Des Moines, IA', 'MA', '19', 'Iowa', 41.5868, -93.6250),
    ('192', 'Rest of Iowa', 'ROS', '19', 'Iowa', 41.8780, -93.0977),
    # Kansas
    ('201', 'Kansas City, KS', 'MA', '20', 'Kansas', 39.0997, -94.5786),
    ('202', 'Wichita, KS', 'MA', '20', 'Kansas', 37.6872, -97.3301),
    ('203', 'Rest of Kansas', 'ROS', '20', 'Kansas', 39.0119, -98.4842),
    # Kentucky
    ('211', 'Louisville, KY', 'MA', '21', 'Kentucky', 38.2527, -85.7585),
    ('212', 'Rest of Kentucky', 'ROS', '21', 'Kentucky', 37.8393, -84.2700),
    # Louisiana
    ('221', 'Baton Rouge, LA', 'MA', '22', 'Louisiana', 30.4583, -91.1403),
    ('222', 'New Orleans, LA', 'MA', '22', 'Louisiana', 29.9511, -90.0715),
    ('223', 'Rest of Louisiana', 'ROS', '22', 'Louisiana', 30.9843, -91.9623),
    # Maine
    ('231', 'Portland, ME', 'MA', '23', 'Maine', 43.6591, -70.2568),
    ('232', 'Rest of Maine', 'ROS', '23', 'Maine', 45.2538, -69.4455),
    # Maryland
    ('241', 'Baltimore, MD', 'MA', '24', 'Maryland', 39.2904, -76.6122),
    ('242', 'Rest of Maryland', 'ROS', '24', 'Maryland', 39.0458, -76.6413),
    # Massachusetts
    ('251', 'Boston, MA', 'MA', '25', 'Massachusetts', 42.3601, -71.0589),
    ('252', 'Rest of Massachusetts', 'ROS', '25', 'Massachusetts', 42.4072, -71.3824),
    # Michigan
    ('261', 'Detroit, MI', 'MA', '26', 'Michigan', 42.3314, -83.0458),
    ('262', 'Grand Rapids, MI', 'MA', '26', 'Michigan', 42.9634, -85.6681),
    ('263', 'Rest of Michigan', 'ROS', '26', 'Michigan', 44.3148, -85.6024),
    # Minnesota
    ('271', 'Minneapolis, MN', 'MA', '27', 'Minnesota', 44.9778, -93.2650),
    ('272', 'Rest of Minnesota', 'ROS', '27', 'Minnesota', 46.7296, -94.6859),
    # Mississippi
    ('280', 'Mississippi', 'Whole State', '28', 'Mississippi', 32.3547, -89.3985),
    # Missouri
    ('291', 'Kansas City, MO', 'MA', '29', 'Missouri', 39.0997, -94.5786),
    ('292', 'St. Louis, MO', 'MA', '29', 'Missouri', 38.6270, -90.1994),
    ('293', 'Rest of Missouri', 'ROS', '29', 'Missouri', 37.9643, -91.8318),
    # Montana
    ('300', 'Montana', 'Whole State', '30', 'Montana', 46.8797, -110.3626),
    # Nebraska
    ('311', 'Omaha, NE', 'MA', '31', 'Nebraska', 41.2565, -95.9345),
    ('312', 'Rest of Nebraska', 'ROS', '31', 'Nebraska', 41.4925, -99.9018),
    # Nevada
    ('321', 'Las Vegas, NV', 'MA', '32', 'Nevada', 36.1699, -115.1398),
    ('322', 'Rest of Nevada', 'ROS', '32', 'Nevada', 38.8026, -116.4194),
    # New Hampshire
    ('330', 'New Hampshire', 'Whole State', '33', 'New Hampshire', 43.1939, -71.5724),
    # New Jersey
    ('341', 'Newark, NJ', 'MA', '34', 'New Jersey', 40.7357, -74.1724),
    ('342', 'Rest of New Jersey', 'ROS', '34', 'New Jersey', 40.0583, -74.4057),
    # New Mexico
    ('351', 'Albuquerque, NM', 'MA', '35', 'New Mexico', 35.0844, -106.6504),
    ('352', 'Rest of New Mexico', 'ROS', '35', 'New Mexico', 34.5199, -105.8701),
    # New York
    ('361', 'Albany, NY', 'MA', '36', 'New York', 42.6526, -73.7562),
    ('362', 'Buffalo, NY', 'MA', '36', 'New York', 42.8864, -78.8784),
    ('363', 'New York City, NY', 'MA', '36', 'New York', 40.7128, -74.0060),
    ('364', 'Rochester, NY', 'MA', '36', 'New York', 43.1566, -77.6088),
    ('365', 'Rest of New York', 'ROS', '36', 'New York', 43.2994, -74.2179),
    # North Carolina
    ('371', 'Charlotte, NC', 'MA', '37', 'North Carolina', 35.2271, -80.8431),
    ('372', 'Greensboro, NC', 'MA', '37', 'North Carolina', 36.0726, -79.7920),
    ('373', 'Raleigh, NC', 'MA', '37', 'North Carolina', 35.7796, -78.6382),
    ('374', 'Rest of North Carolina', 'ROS', '37', 'North Carolina', 35.7596, -79.0193),
    # North Dakota
    ('380', 'North Dakota', 'Whole State', '38', 'North Dakota', 47.5515, -101.0020),
    # Ohio
    ('391', 'Cincinnati, OH', 'MA', '39', 'Ohio', 39.1031, -84.5120),
    ('392', 'Cleveland, OH', 'MA', '39', 'Ohio', 41.4993, -81.6944),
    ('393', 'Columbus, OH', 'MA', '39', 'Ohio', 39.9612, -82.9988),
    ('394', 'Rest of Ohio', 'ROS', '39', 'Ohio', 40.4173, -82.9071),
    # Oklahoma
    ('401', 'Oklahoma City, OK', 'MA', '40', 'Oklahoma', 35.4676, -97.5164),
    ('402', 'Tulsa, OK', 'MA', '40', 'Oklahoma', 36.1540, -95.9928),
    ('403', 'Rest of Oklahoma', 'ROS', '40', 'Oklahoma', 35.0078, -97.0929),
    # Oregon
    ('411', 'Portland, OR', 'MA', '41', 'Oregon', 45.5152, -122.6784),
    ('412', 'Rest of Oregon', 'ROS', '41', 'Oregon', 43.8041, -120.5542),
    # Pennsylvania
    ('421', 'Harrisburg, PA', 'MA', '42', 'Pennsylvania', 40.2732, -76.8867),
    ('422', 'Philadelphia, PA', 'MA', '42', 'Pennsylvania', 39.9526, -75.1652),
    ('423', 'Pittsburgh, PA', 'MA', '42', 'Pennsylvania', 40.4406, -79.9959),
    ('424', 'Rest of Pennsylvania', 'ROS', '42', 'Pennsylvania', 41.2033, -77.1945),
    # Rhode Island
    ('440', 'Rhode Island', 'Whole State', '44', 'Rhode Island', 41.5801, -71.4774),
    # South Carolina
    ('451', 'Charleston, SC', 'MA', '45', 'South Carolina', 32.7765, -79.9311),
    ('452', 'Greenville, SC', 'MA', '45', 'South Carolina', 34.8526, -82.3940),
    ('453', 'Rest of South Carolina', 'ROS', '45', 'South Carolina', 33.8361, -81.1637),
    # South Dakota
    ('460', 'South Dakota', 'Whole State', '46', 'South Dakota', 43.9695, -99.9018),
    # Tennessee
    ('471', 'Knoxville, TN', 'MA', '47', 'Tennessee', 35.9606, -83.9207),
    ('472', 'Memphis, TN', 'MA', '47', 'Tennessee', 35.1495, -90.0490),
    ('473', 'Nashville, TN', 'MA', '47', 'Tennessee', 36.1627, -86.7816),
    ('474', 'Rest of Tennessee', 'ROS', '47', 'Tennessee', 35.5175, -86.5804),
    # Texas
    ('481', 'Austin, TX', 'MA', '48', 'Texas', 30.2672, -97.7431),
    ('482', 'Beaumont, TX', 'MA', '48', 'Texas', 30.0802, -94.1266),
    ('483', 'Dallas, TX', 'MA', '48', 'Texas', 32.7767, -96.7970),
    ('484', 'El Paso, TX', 'MA', '48', 'Texas', 31.7619, -106.4850),
    ('485', 'Houston, TX', 'MA', '48', 'Texas', 29.7604, -95.3698),
    ('486', 'Laredo, TX', 'MA', '48', 'Texas', 27.5306, -99.4803),
    ('487', 'San Antonio, TX', 'MA', '48', 'Texas', 29.4241, -98.4936),
    ('488', 'Rest of Texas', 'ROS', '48', 'Texas', 31.9686, -99.9018),
    # Utah
    ('491', 'Salt Lake City, UT', 'MA', '49', 'Utah', 40.7608, -111.8910),
    ('492', 'Rest of Utah', 'ROS', '49', 'Utah', 39.3210, -111.0937),
    # Vermont
    ('500', 'Vermont', 'Whole State', '50', 'Vermont', 44.5588, -72.5778),
    # Virginia
    ('511', 'Norfolk, VA', 'MA', '51', 'Virginia', 36.8508, -76.2859),
    ('512', 'Richmond, VA', 'MA', '51', 'Virginia', 37.5407, -77.4360),
    ('513', 'Rest of Virginia', 'ROS', '51', 'Virginia', 37.4316, -78.6569),
    # Washington
    ('531', 'Seattle, WA', 'MA', '53', 'Washington', 47.6062, -122.3321),
    ('532', 'Rest of Washington', 'ROS', '53', 'Washington', 47.7511, -120.7401),
    # West Virginia
    ('540', 'West Virginia', 'Whole State', '54', 'West Virginia', 38.5976, -80.4549),
    # Wisconsin
    ('551', 'Milwaukee, WI', 'MA', '55', 'Wisconsin', 43.0389, -87.9065),
    ('552', 'Rest of Wisconsin', 'ROS', '55', 'Wisconsin', 43.7844, -88.7879),
    # Wyoming
    ('560', 'Wyoming', 'Whole State', '56', 'Wyoming', 43.0759, -107.2903),
]

# =============================================================================
# STCC to SCTG CROSSWALK (2-digit level)
# Maps rail STCC codes to FAF SCTG codes for cross-modal analysis
# =============================================================================

STCC_SCTG_CROSSWALK = [
    # STCC 2-digit, STCC Name, SCTG 2-digit, SCTG Name, Match Quality
    ('01', 'Farm Products', '02', 'Cereal grains', 'close'),
    ('01', 'Farm Products', '03', 'Other agricultural products', 'close'),
    ('01', 'Farm Products', '04', 'Animal feed', 'close'),
    ('08', 'Forest Products', '25', 'Logs and wood in the rough', 'exact'),
    ('09', 'Fresh Fish/Marine Products', '05', 'Meat, fish, seafood', 'close'),
    ('10', 'Metallic Ores', '14', 'Metallic ores and concentrates', 'exact'),
    ('11', 'Coal', '15', 'Coal', 'exact'),
    ('13', 'Crude Petroleum', '16', 'Crude petroleum oil', 'exact'),
    ('14', 'Non-Metallic Minerals', '10', 'Monumental or building stone', 'close'),
    ('14', 'Non-Metallic Minerals', '11', 'Natural sands', 'close'),
    ('14', 'Non-Metallic Minerals', '12', 'Gravel and crushed stone', 'close'),
    ('14', 'Non-Metallic Minerals', '13', 'Nonmetallic minerals n.e.c.', 'close'),
    ('19', 'Ordnance or Accessories', '40', 'Miscellaneous manufactured products', 'approximate'),
    ('20', 'Food or Kindred Products', '05', 'Meat, fish, seafood', 'close'),
    ('20', 'Food or Kindred Products', '06', 'Milled grain products', 'close'),
    ('20', 'Food or Kindred Products', '07', 'Other prepared foodstuffs', 'close'),
    ('20', 'Food or Kindred Products', '08', 'Alcoholic beverages', 'close'),
    ('21', 'Tobacco Products', '09', 'Tobacco products', 'exact'),
    ('22', 'Textile Mill Products', '30', 'Textiles, leather', 'exact'),
    ('23', 'Apparel', '30', 'Textiles, leather', 'close'),
    ('24', 'Lumber or Wood Products', '26', 'Wood products', 'exact'),
    ('25', 'Furniture or Fixtures', '39', 'Furniture, mattresses', 'exact'),
    ('26', 'Pulp, Paper or Allied Products', '27', 'Pulp, newsprint, paper', 'exact'),
    ('26', 'Pulp, Paper or Allied Products', '28', 'Paper articles', 'close'),
    ('27', 'Printed Matter', '29', 'Printed products', 'exact'),
    ('28', 'Chemicals or Allied Products', '20', 'Basic chemicals', 'close'),
    ('28', 'Chemicals or Allied Products', '21', 'Pharmaceutical products', 'close'),
    ('28', 'Chemicals or Allied Products', '22', 'Fertilizers', 'close'),
    ('28', 'Chemicals or Allied Products', '23', 'Chemical products', 'close'),
    ('29', 'Petroleum or Coal Products', '17', 'Gasoline and aviation fuel', 'close'),
    ('29', 'Petroleum or Coal Products', '18', 'Fuel oils', 'close'),
    ('29', 'Petroleum or Coal Products', '19', 'Coal and petroleum products n.e.c.', 'close'),
    ('30', 'Rubber or Misc. Plastics', '24', 'Plastics and rubber', 'exact'),
    ('31', 'Leather or Leather Products', '30', 'Textiles, leather', 'close'),
    ('32', 'Clay, Concrete, Glass, Stone', '31', 'Nonmetal mineral products', 'exact'),  # CEMENT!
    ('33', 'Primary Metal Products', '32', 'Base metal primary forms', 'exact'),
    ('34', 'Fabricated Metal Products', '33', 'Articles of base metal', 'exact'),
    ('35', 'Machinery', '34', 'Machinery', 'exact'),
    ('36', 'Electrical Machinery', '35', 'Electronic and electrical equipment', 'exact'),
    ('37', 'Transportation Equipment', '36', 'Motorized vehicles', 'close'),
    ('37', 'Transportation Equipment', '37', 'Transportation equipment n.e.c.', 'close'),
    ('38', 'Instruments', '38', 'Precision instruments', 'exact'),
    ('39', 'Misc. Products of Manufacturing', '40', 'Miscellaneous manufactured products', 'exact'),
    ('40', 'Waste or Scrap Materials', '41', 'Waste and scrap', 'exact'),
    ('41', 'Misc. Freight Shipments', '43', 'Mixed freight', 'close'),
    ('42', 'Empty Containers/Shipper Equipment', '43', 'Mixed freight', 'approximate'),
    ('43', 'Mail/Express Traffic', '43', 'Mixed freight', 'approximate'),
    ('44', 'Freight Forwarder Traffic', '43', 'Mixed freight', 'approximate'),
    ('45', 'Shipper Association Traffic', '43', 'Mixed freight', 'approximate'),
    ('46', 'Misc. Mixed Shipments', '43', 'Mixed freight', 'exact'),
    ('47', 'Small Packaged Freight', '43', 'Mixed freight', 'close'),
    ('48', 'Hazardous Waste', '41', 'Waste and scrap', 'close'),
    ('49', 'Hazardous Materials', '23', 'Chemical products', 'approximate'),
    ('50', 'Secondary Traffic', '43', 'Mixed freight', 'approximate'),
]


def init_faf_tables(conn):
    """Initialize FAF dimension tables in DuckDB."""

    # Create SCTG dimension table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_sctg (
            sctg_code VARCHAR(2) PRIMARY KEY,
            sctg_name VARCHAR(100),
            sctg_group VARCHAR(50),
            rail_intensive BOOLEAN,
            stcc_mapping VARCHAR(5)
        )
    """)

    # Load SCTG codes
    for code, name, group, rail_int, stcc in SCTG_CODES:
        conn.execute("""
            INSERT OR REPLACE INTO dim_sctg VALUES (?, ?, ?, ?, ?)
        """, [code, name, group, rail_int, stcc])

    # Create Mode dimension table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_mode (
            mode_code INTEGER PRIMARY KEY,
            mode_name VARCHAR(50),
            mode_category VARCHAR(20)
        )
    """)

    # Load modes
    for code, name, category in TRANSPORT_MODES:
        conn.execute("""
            INSERT OR REPLACE INTO dim_mode VALUES (?, ?, ?)
        """, [code, name, category])

    # Create FAF Zone dimension table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_faf_zone (
            faf_zone VARCHAR(3) PRIMARY KEY,
            zone_name VARCHAR(100),
            zone_type VARCHAR(20),
            state_fips VARCHAR(2),
            state_name VARCHAR(50),
            latitude DECIMAL(9,6),
            longitude DECIMAL(9,6)
        )
    """)

    # Load FAF zones
    for zone, name, ztype, fips, state, lat, lon in FAF_ZONES:
        conn.execute("""
            INSERT OR REPLACE INTO dim_faf_zone VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [zone, name, ztype, fips, state, lat, lon])

    # Create STCC-SCTG crosswalk table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS xwalk_stcc_sctg (
            id INTEGER PRIMARY KEY,
            stcc_2digit VARCHAR(2),
            stcc_name VARCHAR(100),
            sctg_code VARCHAR(2),
            sctg_name VARCHAR(100),
            match_quality VARCHAR(20)
        )
    """)

    # Load crosswalk
    for i, (stcc, stcc_name, sctg, sctg_name, quality) in enumerate(STCC_SCTG_CROSSWALK):
        conn.execute("""
            INSERT OR REPLACE INTO xwalk_stcc_sctg VALUES (?, ?, ?, ?, ?, ?)
        """, [i+1, stcc, stcc_name, sctg, sctg_name, quality])

    # Create FAF fact table (empty, to be populated from CSV)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_faf_flow (
            id INTEGER PRIMARY KEY,
            year INTEGER,
            origin_faf VARCHAR(3),
            dest_faf VARCHAR(3),
            sctg_code VARCHAR(2),
            mode_code INTEGER,
            tons_thousands DECIMAL(15,3),
            value_millions DECIMAL(15,3),
            tmiles_millions DECIMAL(15,3)
        )
    """)

    print(f"Initialized FAF tables:")
    print(f"  - dim_sctg: {len(SCTG_CODES)} commodity codes")
    print(f"  - dim_mode: {len(TRANSPORT_MODES)} modes")
    print(f"  - dim_faf_zone: {len(FAF_ZONES)} zones")
    print(f"  - xwalk_stcc_sctg: {len(STCC_SCTG_CROSSWALK)} mappings")


def create_faf_views(conn):
    """Create analytical views for FAF data."""

    # Modal share view
    conn.execute("""
        CREATE OR REPLACE VIEW v_modal_share AS
        SELECT
            f.year,
            f.sctg_code,
            s.sctg_name,
            f.mode_code,
            m.mode_name,
            SUM(f.tons_thousands) as tons_k,
            SUM(f.value_millions) as value_m,
            SUM(f.tmiles_millions) as tmiles_m
        FROM fact_faf_flow f
        JOIN dim_sctg s ON f.sctg_code = s.sctg_code
        JOIN dim_mode m ON f.mode_code = m.mode_code
        GROUP BY f.year, f.sctg_code, s.sctg_name, f.mode_code, m.mode_name
    """)

    # Rail vs Truck competition view
    conn.execute("""
        CREATE OR REPLACE VIEW v_rail_truck_competition AS
        SELECT
            year,
            sctg_code,
            SUM(CASE WHEN mode_code = 2 THEN tons_thousands ELSE 0 END) as rail_tons,
            SUM(CASE WHEN mode_code = 1 THEN tons_thousands ELSE 0 END) as truck_tons,
            SUM(CASE WHEN mode_code = 2 THEN tons_thousands ELSE 0 END) /
                NULLIF(SUM(CASE WHEN mode_code IN (1,2) THEN tons_thousands END), 0) * 100
                as rail_share_pct,
            SUM(CASE WHEN mode_code = 2 THEN tmiles_millions ELSE 0 END) as rail_tmiles,
            SUM(CASE WHEN mode_code = 1 THEN tmiles_millions ELSE 0 END) as truck_tmiles
        FROM fact_faf_flow
        GROUP BY year, sctg_code
    """)

    # Major trade lanes view
    conn.execute("""
        CREATE OR REPLACE VIEW v_faf_trade_lanes AS
        SELECT
            f.year,
            f.origin_faf,
            oz.zone_name as origin_name,
            oz.state_name as origin_state,
            f.dest_faf,
            dz.zone_name as dest_name,
            dz.state_name as dest_state,
            f.mode_code,
            m.mode_name,
            f.sctg_code,
            s.sctg_name,
            SUM(f.tons_thousands) as tons_k,
            SUM(f.value_millions) as value_m,
            SUM(f.tmiles_millions) as tmiles_m
        FROM fact_faf_flow f
        JOIN dim_faf_zone oz ON f.origin_faf = oz.faf_zone
        JOIN dim_faf_zone dz ON f.dest_faf = dz.faf_zone
        JOIN dim_mode m ON f.mode_code = m.mode_code
        JOIN dim_sctg s ON f.sctg_code = s.sctg_code
        GROUP BY f.year, f.origin_faf, oz.zone_name, oz.state_name,
                 f.dest_faf, dz.zone_name, dz.state_name,
                 f.mode_code, m.mode_name, f.sctg_code, s.sctg_name
    """)

    print("Created FAF analytical views:")
    print("  - v_modal_share")
    print("  - v_rail_truck_competition")
    print("  - v_faf_trade_lanes")


def load_faf_csv(conn, csv_path: str, year: int = None):
    """
    Load FAF data from a CSV file.

    Expected CSV columns:
    - dms_orig or fr_orig: Origin FAF zone
    - dms_dest or fr_dest: Destination FAF zone
    - sctg2: SCTG commodity code
    - dms_mode or fr_mode: Transportation mode
    - year (optional if passed as parameter)
    - tons: Tonnage in thousands
    - value: Value in millions of 2017 USD
    - tmiles: Ton-miles in millions
    """
    import pandas as pd

    print(f"Loading FAF data from {csv_path}...")

    df = pd.read_csv(csv_path)

    # Standardize column names (FAF files may have different naming conventions)
    column_map = {
        'dms_orig': 'origin_faf',
        'fr_orig': 'origin_faf',
        'dms_dest': 'dest_faf',
        'fr_dest': 'dest_faf',
        'sctg2': 'sctg_code',
        'dms_mode': 'mode_code',
        'fr_mode': 'mode_code',
        'tons': 'tons_thousands',
        'value': 'value_millions',
        'tmiles': 'tmiles_millions',
    }

    df = df.rename(columns=column_map)

    # Add year if not in data
    if 'year' not in df.columns and year:
        df['year'] = year

    # Convert zone codes to 3-digit strings
    df['origin_faf'] = df['origin_faf'].astype(str).str.zfill(3)
    df['dest_faf'] = df['dest_faf'].astype(str).str.zfill(3)
    df['sctg_code'] = df['sctg_code'].astype(str).str.zfill(2)

    # Select relevant columns
    cols = ['year', 'origin_faf', 'dest_faf', 'sctg_code', 'mode_code',
            'tons_thousands', 'value_millions', 'tmiles_millions']
    df = df[[c for c in cols if c in df.columns]]

    # Get current max ID
    result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM fact_faf_flow").fetchone()
    start_id = result[0] + 1

    # Add ID column
    df.insert(0, 'id', range(start_id, start_id + len(df)))

    # Insert into table
    conn.execute("INSERT INTO fact_faf_flow SELECT * FROM df")

    print(f"Loaded {len(df):,} FAF flow records")
    return len(df)


def get_faf_summary(conn):
    """Get summary statistics for loaded FAF data."""
    result = {}

    # Record count
    count = conn.execute("SELECT COUNT(*) FROM fact_faf_flow").fetchone()[0]
    result['total_records'] = count

    if count == 0:
        return result

    # Years
    years = conn.execute("""
        SELECT MIN(year), MAX(year), COUNT(DISTINCT year)
        FROM fact_faf_flow
    """).fetchone()
    result['year_range'] = f"{years[0]}-{years[1]}"
    result['year_count'] = years[2]

    # Total tonnage by mode
    modes = conn.execute("""
        SELECT m.mode_name, SUM(f.tons_thousands) as tons
        FROM fact_faf_flow f
        JOIN dim_mode m ON f.mode_code = m.mode_code
        GROUP BY m.mode_name
        ORDER BY tons DESC
    """).fetchall()
    result['tonnage_by_mode'] = {m[0]: m[1] for m in modes}

    # Top commodities
    commodities = conn.execute("""
        SELECT s.sctg_name, SUM(f.tons_thousands) as tons
        FROM fact_faf_flow f
        JOIN dim_sctg s ON f.sctg_code = s.sctg_code
        GROUP BY s.sctg_name
        ORDER BY tons DESC
        LIMIT 10
    """).fetchall()
    result['top_commodities'] = [(c[0], c[1]) for c in commodities]

    return result


if __name__ == "__main__":
    # Test initialization
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from database import get_connection

    conn = get_connection()
    init_faf_tables(conn)
    create_faf_views(conn)

    print("\nFAF data infrastructure initialized successfully!")
    print("\nTo load FAF data, download CSV from https://faf.ornl.gov/faf5/")
    print("Then run: load_faf_csv(conn, 'path/to/faf5_data.csv')")
