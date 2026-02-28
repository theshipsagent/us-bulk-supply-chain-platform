"""
Complete BEA Economic Area Dictionary
Based on STB Waybill Reference Guide BEA Codes (1995 definitions)
172 Economic Areas used in the Public Use Waybill Sample
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "rail_analytics.duckdb"

# Complete BEA Economic Area codes
# Format: (code, name, primary_city, states, region, lat, lon)
BEA_AREAS = [
    # Northeast (001-014)
    ('001', 'Bangor, ME', 'Bangor', 'ME', 'Northeast', 44.8016, -68.7712),
    ('002', 'Portland, ME', 'Portland', 'ME', 'Northeast', 43.6591, -70.2568),
    ('003', 'Burlington, VT', 'Burlington', 'VT', 'Northeast', 44.4759, -73.2121),
    ('004', 'Albany, NY', 'Albany', 'NY', 'Northeast', 42.6526, -73.7562),
    ('005', 'Syracuse, NY', 'Syracuse', 'NY', 'Northeast', 43.0481, -76.1474),
    ('006', 'Rochester, NY', 'Rochester', 'NY', 'Northeast', 43.1566, -77.6088),
    ('007', 'Buffalo, NY', 'Buffalo', 'NY', 'Northeast', 42.8864, -78.8784),
    ('008', 'State College, PA', 'State College', 'PA', 'Northeast', 40.7934, -77.8600),
    ('009', 'Harrisburg, PA', 'Harrisburg', 'PA', 'Northeast', 40.2732, -76.8867),
    ('010', 'Boston, MA', 'Boston', 'MA,NH,RI', 'Northeast', 42.3601, -71.0589),
    ('011', 'Worcester, MA', 'Worcester', 'MA', 'Northeast', 42.2626, -71.8023),
    ('012', 'Providence, RI', 'Providence', 'RI,MA', 'Northeast', 41.8240, -71.4128),
    ('013', 'Hartford, CT', 'Hartford', 'CT', 'Northeast', 41.7658, -72.6734),
    ('014', 'New York, NY', 'New York', 'NY,NJ,CT,PA', 'Northeast', 40.7128, -74.0060),

    # Mid-Atlantic (015-027)
    ('015', 'Binghamton, NY', 'Binghamton', 'NY,PA', 'Northeast', 42.0987, -75.9180),
    ('016', 'Scranton, PA', 'Scranton', 'PA', 'Northeast', 41.4090, -75.6624),
    ('017', 'Allentown, PA', 'Allentown', 'PA,NJ', 'Northeast', 40.6084, -75.4902),
    ('018', 'Philadelphia, PA', 'Philadelphia', 'PA,NJ,DE,MD', 'Northeast', 39.9526, -75.1652),
    ('019', 'Wilmington, DE', 'Wilmington', 'DE,MD,NJ', 'Mid-Atlantic', 39.7391, -75.5398),
    ('020', 'Baltimore, MD', 'Baltimore', 'MD', 'Mid-Atlantic', 39.2904, -76.6122),
    ('021', 'Salisbury, MD', 'Salisbury', 'MD,DE,VA', 'Mid-Atlantic', 38.3607, -75.5994),
    ('022', 'Washington, DC', 'Washington', 'DC,MD,VA,WV', 'Mid-Atlantic', 38.9072, -77.0369),
    ('023', 'Staunton, VA', 'Staunton', 'VA,WV', 'Mid-Atlantic', 38.1496, -79.0717),
    ('024', 'Richmond, VA', 'Richmond', 'VA', 'Southeast', 37.5407, -77.4360),
    ('025', 'Norfolk, VA', 'Norfolk', 'VA,NC', 'Southeast', 36.8508, -76.2859),
    ('026', 'Raleigh, NC', 'Raleigh', 'NC', 'Southeast', 35.7796, -78.6382),
    ('027', 'Greenville, NC', 'Greenville', 'NC', 'Southeast', 35.6127, -77.3664),

    # Southeast (028-046)
    ('028', 'Charlotte, NC', 'Charlotte', 'NC,SC', 'Southeast', 35.2271, -80.8431),
    ('029', 'Wilmington, NC', 'Wilmington', 'NC', 'Southeast', 34.2257, -77.9447),
    ('030', 'Fayetteville, NC', 'Fayetteville', 'NC', 'Southeast', 35.0527, -78.8784),
    ('031', 'Florence, SC', 'Florence', 'SC', 'Southeast', 34.1954, -79.7626),
    ('032', 'Charleston, SC', 'Charleston', 'SC', 'Southeast', 32.7765, -79.9311),
    ('033', 'Columbia, SC', 'Columbia', 'SC', 'Southeast', 34.0007, -81.0348),
    ('034', 'Augusta, GA', 'Augusta', 'GA,SC', 'Southeast', 33.4735, -82.0105),
    ('035', 'Savannah, GA', 'Savannah', 'GA,SC', 'Southeast', 32.0809, -81.0912),
    ('036', 'Macon, GA', 'Macon', 'GA', 'Southeast', 32.8407, -83.6324),
    ('037', 'Albany, GA', 'Albany', 'GA', 'Southeast', 31.5785, -84.1557),
    ('038', 'Dothan, AL', 'Dothan', 'AL,FL,GA', 'Southeast', 31.2232, -85.3905),
    ('039', 'Tallahassee, FL', 'Tallahassee', 'FL,GA', 'Southeast', 30.4383, -84.2807),
    ('040', 'Jacksonville, FL', 'Jacksonville', 'FL,GA', 'Southeast', 30.3322, -81.6557),
    ('041', 'Orlando, FL', 'Orlando', 'FL', 'Southeast', 28.5383, -81.3792),
    ('042', 'Tampa, FL', 'Tampa', 'FL', 'Southeast', 27.9506, -82.4572),
    ('043', 'Fort Myers, FL', 'Fort Myers', 'FL', 'Southeast', 26.6406, -81.8723),
    ('044', 'Miami, FL', 'Miami', 'FL', 'Southeast', 25.7617, -80.1918),
    ('045', 'Chattanooga, TN', 'Chattanooga', 'TN,GA,AL', 'Southeast', 35.0456, -85.3097),
    ('046', 'Atlanta, GA', 'Atlanta', 'GA', 'Southeast', 33.7490, -84.3880),

    # Gulf Coast / South Central (047-083)
    ('047', 'Columbus, GA', 'Columbus', 'GA,AL', 'Southeast', 32.4610, -84.9877),
    ('048', 'Birmingham, AL', 'Birmingham', 'AL', 'Southeast', 33.5186, -86.8104),
    ('049', 'Huntsville, AL', 'Huntsville', 'AL,TN', 'Southeast', 34.7304, -86.5861),
    ('050', 'Nashville, TN', 'Nashville', 'TN,KY', 'Southeast', 36.1627, -86.7816),
    ('051', 'Knoxville, TN', 'Knoxville', 'TN', 'Southeast', 35.9606, -83.9207),
    ('052', 'Johnson City, TN', 'Johnson City', 'TN,VA', 'Southeast', 36.3134, -82.3535),
    ('053', 'Charleston, WV', 'Charleston', 'WV,KY,OH', 'Mid-Atlantic', 38.3498, -81.6326),
    ('054', 'Lexington, KY', 'Lexington', 'KY', 'Southeast', 38.0406, -84.5037),
    ('055', 'Louisville, KY', 'Louisville', 'KY,IN', 'Midwest', 38.2527, -85.7585),
    ('056', 'Evansville, IN', 'Evansville', 'IN,KY,IL', 'Midwest', 37.9716, -87.5711),
    ('057', 'Fort Wayne, IN', 'Fort Wayne', 'IN,OH', 'Midwest', 41.0793, -85.1394),
    ('058', 'Grand Rapids, MI', 'Grand Rapids', 'MI', 'Midwest', 42.9634, -85.6681),
    ('059', 'Traverse City, MI', 'Traverse City', 'MI', 'Midwest', 44.7631, -85.6206),
    ('060', 'Saginaw, MI', 'Saginaw', 'MI', 'Midwest', 43.4195, -83.9508),
    ('061', 'Detroit, MI', 'Detroit', 'MI', 'Midwest', 42.3314, -83.0458),
    ('062', 'Toledo, OH', 'Toledo', 'OH,MI', 'Midwest', 41.6528, -83.5379),
    ('063', 'Cleveland, OH', 'Cleveland', 'OH', 'Midwest', 41.4993, -81.6944),
    ('064', 'Columbus, OH', 'Columbus', 'OH', 'Midwest', 39.9612, -82.9988),
    ('065', 'Youngstown, OH', 'Youngstown', 'OH,PA', 'Midwest', 41.0998, -80.6495),
    ('066', 'Pittsburgh, PA', 'Pittsburgh', 'PA,WV,OH', 'Northeast', 40.4406, -79.9959),
    ('067', 'Wheeling, WV', 'Wheeling', 'WV,OH', 'Mid-Atlantic', 40.0640, -80.7209),
    ('068', 'Cincinnati, OH', 'Cincinnati', 'OH,KY,IN', 'Midwest', 39.1031, -84.5120),
    ('069', 'Dayton, OH', 'Dayton', 'OH', 'Midwest', 39.7589, -84.1916),
    ('070', 'Indianapolis, IN', 'Indianapolis', 'IN', 'Midwest', 39.7684, -86.1581),
    ('071', 'Terre Haute, IN', 'Terre Haute', 'IN,IL', 'Midwest', 39.4667, -87.4139),
    ('072', 'Springfield, IL', 'Springfield', 'IL', 'Midwest', 39.7817, -89.6501),
    ('073', 'St. Louis, MO', 'St. Louis', 'MO,IL', 'Midwest', 38.6270, -90.1994),
    ('074', 'Paducah, KY', 'Paducah', 'KY,IL', 'Southeast', 37.0834, -88.6001),
    ('075', 'Springfield, MO', 'Springfield', 'MO', 'Midwest', 37.2090, -93.2923),
    ('076', 'Joplin, MO', 'Joplin', 'MO,KS,OK', 'Plains', 37.0842, -94.5133),
    ('077', 'Fort Smith, AR', 'Fort Smith', 'AR,OK', 'South Central', 35.3859, -94.3985),
    ('078', 'Fayetteville, AR', 'Fayetteville', 'AR', 'South Central', 36.0822, -94.1719),
    ('079', 'Little Rock, AR', 'Little Rock', 'AR', 'South Central', 34.7465, -92.2896),
    ('080', 'Monroe, LA', 'Monroe', 'LA,AR', 'South Central', 32.5093, -92.1193),
    ('081', 'Jackson, MS', 'Jackson', 'MS,LA', 'Southeast', 32.2988, -90.1848),
    ('082', 'Shreveport, LA', 'Shreveport', 'LA,AR,TX', 'South Central', 32.5252, -93.7502),
    ('083', 'Tyler, TX', 'Tyler', 'TX', 'South Central', 32.3513, -95.3011),

    # South Central / Texas (084-095)
    ('084', 'Beaumont, TX', 'Beaumont', 'TX,LA', 'Gulf Coast', 30.0802, -94.1266),
    ('085', 'Lake Charles, LA', 'Lake Charles', 'LA', 'Gulf Coast', 30.2266, -93.2174),
    ('086', 'Baton Rouge, LA', 'Baton Rouge', 'LA,MS', 'Gulf Coast', 30.4515, -91.1871),
    ('087', 'New Orleans, LA', 'New Orleans', 'LA,MS', 'Gulf Coast', 29.9511, -90.0715),
    ('088', 'Mobile, AL', 'Mobile', 'AL,MS,FL', 'Gulf Coast', 30.6954, -88.0399),
    ('089', 'Pensacola, FL', 'Pensacola', 'FL,AL', 'Gulf Coast', 30.4213, -87.2169),
    ('090', 'Biloxi, MS', 'Biloxi', 'MS', 'Gulf Coast', 30.3960, -88.8853),
    ('091', 'Montgomery, AL', 'Montgomery', 'AL', 'Southeast', 32.3792, -86.3077),
    ('092', 'Meridian, MS', 'Meridian', 'MS,AL', 'Southeast', 32.3643, -88.7037),
    ('093', 'Memphis, TN', 'Memphis', 'TN,AR,MS', 'South Central', 35.1495, -90.0490),
    ('094', 'Tupelo, MS', 'Tupelo', 'MS,AL,TN', 'Southeast', 34.2576, -88.7034),
    ('095', 'Greenville, MS', 'Greenville', 'MS,AR', 'South Central', 33.4101, -91.0618),

    # Plains (096-109)
    ('096', 'Fargo, ND', 'Fargo', 'ND,MN', 'Upper Midwest', 46.8772, -96.7898),
    ('097', 'Minneapolis, MN', 'Minneapolis', 'MN,WI', 'Upper Midwest', 44.9778, -93.2650),
    ('098', 'Duluth, MN', 'Duluth', 'MN,WI', 'Upper Midwest', 46.7867, -92.1005),
    ('099', 'La Crosse, WI', 'La Crosse', 'WI,MN', 'Upper Midwest', 43.8014, -91.2396),
    ('100', 'Eau Claire, WI', 'Eau Claire', 'WI', 'Upper Midwest', 44.8113, -91.4985),
    ('101', 'Wausau, WI', 'Wausau', 'WI', 'Upper Midwest', 44.9591, -89.6301),
    ('102', 'Green Bay, WI', 'Green Bay', 'WI,MI', 'Upper Midwest', 44.5133, -88.0133),
    ('103', 'Madison, WI', 'Madison', 'WI', 'Upper Midwest', 43.0731, -89.4012),
    ('104', 'Milwaukee, WI', 'Milwaukee', 'WI', 'Midwest', 43.0389, -87.9065),
    ('105', 'Chicago, IL', 'Chicago', 'IL,IN,WI', 'Midwest', 41.8781, -87.6298),
    ('106', 'Rockford, IL', 'Rockford', 'IL', 'Midwest', 42.2711, -89.0940),
    ('107', 'Davenport, IA', 'Davenport', 'IA,IL', 'Midwest', 41.5236, -90.5776),
    ('108', 'Cedar Rapids, IA', 'Cedar Rapids', 'IA', 'Midwest', 41.9779, -91.6656),
    ('109', 'Des Moines, IA', 'Des Moines', 'IA', 'Plains', 41.5868, -93.6250),

    # Great Plains (110-128)
    ('110', 'Sioux Falls, SD', 'Sioux Falls', 'SD,MN,IA', 'Plains', 43.5446, -96.7311),
    ('111', 'Aberdeen, SD', 'Aberdeen', 'SD', 'Plains', 45.4647, -98.4865),
    ('112', 'Rapid City, SD', 'Rapid City', 'SD,NE,MT', 'Plains', 44.0805, -103.2310),
    ('113', 'Bismarck, ND', 'Bismarck', 'ND,MT,SD', 'Plains', 46.8083, -100.7837),
    ('114', 'Minot, ND', 'Minot', 'ND,MT', 'Plains', 48.2325, -101.2963),
    ('115', 'Great Falls, MT', 'Great Falls', 'MT', 'Mountain', 47.5053, -111.3008),
    ('116', 'Billings, MT', 'Billings', 'MT,WY', 'Mountain', 45.7833, -108.5007),
    ('117', 'Sioux City, IA', 'Sioux City', 'IA,NE,SD', 'Plains', 42.4963, -96.4049),
    ('118', 'Omaha, NE', 'Omaha', 'NE,IA', 'Plains', 41.2565, -95.9345),
    ('119', 'Lincoln, NE', 'Lincoln', 'NE', 'Plains', 40.8258, -96.6852),
    ('120', 'Grand Island, NE', 'Grand Island', 'NE', 'Plains', 40.9264, -98.3420),
    ('121', 'North Platte, NE', 'North Platte', 'NE', 'Plains', 41.1403, -100.7601),
    ('122', 'Denver, CO', 'Denver', 'CO,WY,NE', 'Mountain', 39.7392, -104.9903),
    ('123', 'Colorado Springs, CO', 'Colorado Springs', 'CO', 'Mountain', 38.8339, -104.8214),
    ('124', 'Pueblo, CO', 'Pueblo', 'CO', 'Mountain', 38.2545, -104.6091),
    ('125', 'Albuquerque, NM', 'Albuquerque', 'NM', 'Southwest', 35.0844, -106.6504),
    ('126', 'Amarillo, TX', 'Amarillo', 'TX,NM', 'Plains', 35.2220, -101.8313),
    ('127', 'Lubbock, TX', 'Lubbock', 'TX,NM', 'Plains', 33.5779, -101.8552),
    ('128', 'Odessa, TX', 'Odessa', 'TX,NM', 'Plains', 31.8457, -102.3676),

    # Texas (129-137)
    ('129', 'Abilene, TX', 'Abilene', 'TX', 'South Central', 32.4487, -99.7331),
    ('130', 'San Angelo, TX', 'San Angelo', 'TX', 'South Central', 31.4638, -100.4370),
    ('131', 'Dallas, TX', 'Dallas', 'TX', 'South Central', 32.7767, -96.7970),
    ('132', 'Waco, TX', 'Waco', 'TX', 'South Central', 31.5493, -97.1467),
    ('133', 'Austin, TX', 'Austin', 'TX', 'South Central', 30.2672, -97.7431),
    ('134', 'Houston, TX', 'Houston', 'TX', 'Gulf Coast', 29.7604, -95.3698),
    ('135', 'San Antonio, TX', 'San Antonio', 'TX', 'South Central', 29.4241, -98.4936),
    ('136', 'Corpus Christi, TX', 'Corpus Christi', 'TX', 'Gulf Coast', 27.8006, -97.3964),
    ('137', 'McAllen, TX', 'McAllen', 'TX', 'South Central', 26.2034, -98.2300),

    # Mountain / Southwest (138-156)
    ('138', 'El Paso, TX', 'El Paso', 'TX,NM', 'Southwest', 31.7619, -106.4850),
    ('139', 'Scottsbluff, NE', 'Scottsbluff', 'NE,WY', 'Plains', 41.8666, -103.6672),
    ('140', 'Casper, WY', 'Casper', 'WY', 'Mountain', 42.8666, -106.3131),
    ('141', 'Salt Lake City, UT', 'Salt Lake City', 'UT', 'Mountain', 40.7608, -111.8910),
    ('142', 'Idaho Falls, ID', 'Idaho Falls', 'ID,WY,MT', 'Mountain', 43.4666, -112.0341),
    ('143', 'Boise, ID', 'Boise', 'ID,OR', 'Mountain', 43.6150, -116.2023),
    ('144', 'Missoula, MT', 'Missoula', 'MT', 'Mountain', 46.8721, -113.9940),
    ('145', 'Spokane, WA', 'Spokane', 'WA,ID', 'Pacific Northwest', 47.6587, -117.4260),
    ('146', 'Richland, WA', 'Richland', 'WA', 'Pacific Northwest', 46.2856, -119.2845),
    ('147', 'Pendleton, OR', 'Pendleton', 'OR', 'Pacific Northwest', 45.6721, -118.7886),
    ('148', 'Portland, OR', 'Portland', 'OR,WA', 'Pacific Northwest', 45.5152, -122.6784),
    ('149', 'Eugene, OR', 'Eugene', 'OR', 'Pacific Northwest', 44.0521, -123.0868),
    ('150', 'Medford, OR', 'Medford', 'OR,CA', 'Pacific Northwest', 42.3265, -122.8756),
    ('151', 'Redding, CA', 'Redding', 'CA', 'Pacific', 40.5865, -122.3917),
    ('152', 'Sacramento, CA', 'Sacramento', 'CA', 'Pacific', 38.5816, -121.4944),
    ('153', 'Reno, NV', 'Reno', 'NV,CA', 'Mountain', 39.5296, -119.8138),
    ('154', 'Las Vegas, NV', 'Las Vegas', 'NV,AZ,UT', 'Southwest', 36.1699, -115.1398),
    ('155', 'Flagstaff, AZ', 'Flagstaff', 'AZ', 'Southwest', 35.1983, -111.6513),
    ('156', 'Phoenix, AZ', 'Phoenix', 'AZ', 'Southwest', 33.4484, -112.0740),

    # California / Pacific (157-167)
    ('157', 'Tucson, AZ', 'Tucson', 'AZ', 'Southwest', 32.2226, -110.9747),
    ('158', 'San Francisco, CA', 'San Francisco', 'CA', 'Pacific', 37.7749, -122.4194),
    ('159', 'San Jose, CA', 'San Jose', 'CA', 'Pacific', 37.3382, -121.8863),
    ('160', 'Fresno, CA', 'Fresno', 'CA', 'Pacific', 36.7378, -119.7871),
    ('161', 'Bakersfield, CA', 'Bakersfield', 'CA', 'Pacific', 35.3733, -119.0187),
    ('162', 'Santa Barbara, CA', 'Santa Barbara', 'CA', 'Pacific', 34.4208, -119.6982),
    ('163', 'Los Angeles, CA', 'Los Angeles', 'CA', 'Pacific', 34.0522, -118.2437),
    ('164', 'San Diego, CA', 'San Diego', 'CA', 'Pacific', 32.7157, -117.1611),
    ('165', 'Seattle, WA', 'Seattle', 'WA', 'Pacific Northwest', 47.6062, -122.3321),
    ('166', 'Bellingham, WA', 'Bellingham', 'WA', 'Pacific Northwest', 48.7519, -122.4787),
    ('167', 'Olympia, WA', 'Olympia', 'WA', 'Pacific Northwest', 47.0379, -122.9007),

    # Alaska / Hawaii (168-172)
    ('168', 'Anchorage, AK', 'Anchorage', 'AK', 'Alaska', 61.2181, -149.9003),
    ('169', 'Fairbanks, AK', 'Fairbanks', 'AK', 'Alaska', 64.8378, -147.7164),
    ('170', 'Juneau, AK', 'Juneau', 'AK', 'Alaska', 58.3019, -134.4197),
    ('171', 'Honolulu, HI', 'Honolulu', 'HI', 'Hawaii', 21.3069, -157.8583),
    ('172', 'Hilo, HI', 'Hilo', 'HI', 'Hawaii', 19.7074, -155.0847),

    # Special codes
    ('000', 'Masked/Suppressed', 'Unknown', 'XX', 'Unknown', None, None),
]


def update_bea_dimension():
    """Update the dim_bea table with complete BEA codes"""
    con = duckdb.connect(str(DB_PATH))

    print("Updating BEA dimension table with complete 172 codes...")

    # Clear existing data
    con.execute("DELETE FROM dim_bea")

    # Insert all BEA areas
    for row in BEA_AREAS:
        con.execute("""
            INSERT INTO dim_bea (bea_code, bea_name, primary_city, states, region, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, row)

    count = con.execute("SELECT COUNT(*) FROM dim_bea").fetchone()[0]
    print(f"Loaded {count} BEA economic areas")

    # Show sample
    print("\nSample BEA codes:")
    sample = con.execute("""
        SELECT bea_code, bea_name, region
        FROM dim_bea
        WHERE bea_code IN ('010', '105', '131', '163', '165')
        ORDER BY bea_code
    """).fetchdf()
    print(sample.to_string(index=False))

    con.close()
    print("\nBEA dimension update complete!")


if __name__ == "__main__":
    update_bea_dimension()
