"""Fix dimension table mappings"""
import duckdb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "rail_analytics.duckdb"

con = duckdb.connect(str(DB_PATH))

# Fix STCC dimension - add 5-digit codes
print('Updating STCC dimension with 5-digit codes...')
stcc_5digit = [
    ('37111', '37', 'Transportation Equipment', 'Motor Vehicles, Passenger', 'Automotive', 'Auto Rack', 'Model year cycle', False, 'Finished autos'),
    ('37112', '37', 'Transportation Equipment', 'Motor Vehicles, Trucks', 'Automotive', 'Auto Rack', 'Model year cycle', False, 'Trucks, SUVs'),
    ('37422', '37', 'Transportation Equipment', 'Railroad Equipment', 'Rail Equipment', 'Flat Car', 'Steady', False, 'Rail cars, locomotives'),
    ('46111', '46', 'Intermodal', 'COFC Shipments', 'Intermodal', 'Well Car', 'Steady', False, 'Container traffic'),
    ('46211', '46', 'Intermodal', 'TOFC Shipments', 'Intermodal', 'Flat Car', 'Steady', False, 'Trailer traffic'),
    ('28211', '28', 'Chemicals', 'Plastics Materials', 'Plastics', 'Covered Hopper', 'Steady', False, 'Plastic resins, pellets'),
    ('29121', '29', 'Petroleum', 'Petroleum Refining Products', 'Energy', 'Tank Car', 'Steady', True, 'Refined petroleum'),
    ('33123', '33', 'Primary Metals', 'Steel Mill Products', 'Metals', 'Coil Car', 'Steady', False, 'Steel sheets, coils'),
    ('42211', '42', 'Shipping Containers', 'Shipping Containers Empty', 'Intermodal', 'Well Car', 'Steady', False, 'Empty container repo'),
    ('26311', '26', 'Paper Products', 'Paperboard', 'Forest Products', 'Boxcar', 'Steady', False, 'Cardboard, packaging'),
    ('24211', '24', 'Lumber/Wood', 'Sawmill Products', 'Forest Products', 'Center Beam Flat', 'Construction season', False, 'Dimensional lumber'),
    ('11211', '11', 'Coal', 'Bituminous Coal', 'Energy', 'Open Top Hopper', 'Counter-seasonal', False, 'Steam coal'),
    ('11212', '11', 'Coal', 'Subbituminous Coal', 'Energy', 'Open Top Hopper', 'Counter-seasonal', False, 'PRB Coal'),
    ('01132', '01', 'Farm Products', 'Grain', 'Grain', 'Covered Hopper', 'Harvest season', False, 'Wheat, corn, soybeans'),
    ('01137', '01', 'Farm Products', 'Soybeans', 'Grain', 'Covered Hopper', 'Sep-Nov harvest', False, 'Export, crushing'),
    ('28181', '28', 'Chemicals', 'Industrial Organic Chemicals', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Various organics'),
    ('28711', '28', 'Chemicals', 'Fertilizers, Nitrogenous', 'Fertilizer', 'Covered Hopper', 'Mar-Jun', False, 'Ammonia-based'),
    ('20411', '20', 'Food Products', 'Flour and Meal', 'Food', 'Covered Hopper', 'Steady', False, 'Milled grain'),
    ('14111', '14', 'Non-Metallic Minerals', 'Sand and Gravel', 'Construction', 'Open Top Hopper', 'Spring-Fall', False, 'Frac sand, construction'),
    ('32731', '32', 'Stone/Clay/Glass', 'Cement', 'Construction', 'Covered Hopper', 'Spring-Fall', False, 'Portland cement'),
    ('10111', '10', 'Metallic Ores', 'Iron Ore', 'Mining', 'Open Top Hopper', 'Steady', False, 'Taconite'),
    ('40211', '40', 'Waste/Scrap', 'Ferrous Scrap', 'Metals', 'Gondola', 'Steady', False, 'EAF feedstock'),
    ('28691', '28', 'Chemicals', 'Industrial Chemicals NEC', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Various'),
    ('29113', '29', 'Petroleum', 'Crude Petroleum', 'Energy', 'Tank Car', 'Steady', True, 'Crude oil by rail'),
    ('28731', '28', 'Chemicals', 'Phosphatic Fertilizers', 'Fertilizer', 'Covered Hopper', 'Mar-Jun', False, 'DAP, MAP'),
]

for row in stcc_5digit:
    con.execute("""
        INSERT OR REPLACE INTO dim_stcc
        (stcc_code, stcc_2digit, stcc_group, description, category, typical_equipment, seasonality, hazmat_flag, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

print(f'Added {len(stcc_5digit)} 5-digit STCC codes')

# Add more BEA codes
print('Adding more BEA regions...')
bea_extra = [
    ('000', 'Masked/Unknown', 'Unknown', 'XX', 'Unknown', None, None),
    ('096', 'Fargo, ND', 'Fargo', 'ND,MN', 'Upper Midwest', 46.8772, -96.7898),
    ('131', 'Tucson, AZ', 'Tucson', 'AZ', 'Southwest', 32.2226, -110.9747),
    ('092', 'Duluth, MN', 'Duluth', 'MN,WI', 'Upper Midwest', 46.7867, -92.1005),
    ('106', 'Tulsa, OK', 'Tulsa', 'OK', 'South Central', 36.1540, -95.9928),
    ('112', 'Colorado Springs, CO', 'Colorado Springs', 'CO', 'Mountain', 38.8339, -104.8214),
    ('114', 'Cheyenne, WY', 'Cheyenne', 'WY', 'Mountain', 41.1400, -104.8202),
    ('116', 'Boise, ID', 'Boise', 'ID', 'Mountain', 43.6150, -116.2023),
    ('118', 'Reno, NV', 'Reno', 'NV', 'Mountain', 39.5296, -119.8138),
    ('126', 'El Paso, TX', 'El Paso', 'TX,NM', 'Southwest', 31.7619, -106.4850),
    ('132', 'Bakersfield, CA', 'Bakersfield', 'CA', 'Pacific', 35.3733, -119.0187),
    ('134', 'Santa Barbara, CA', 'Santa Barbara', 'CA', 'Pacific', 34.4208, -119.6982),
    ('152', 'Eugene, OR', 'Eugene', 'OR', 'Pacific Northwest', 44.0521, -123.0868),
    ('162', 'Tacoma, WA', 'Tacoma', 'WA', 'Pacific Northwest', 47.2529, -122.4443),
    ('168', 'Great Falls, MT', 'Great Falls', 'MT', 'Mountain', 47.5053, -111.3008),
    ('174', 'Sioux Falls, SD', 'Sioux Falls', 'SD', 'Plains', 43.5446, -96.7311),
    ('176', 'Rapid City, SD', 'Rapid City', 'SD', 'Plains', 44.0805, -103.2310),
    ('178', 'Bismarck, ND', 'Bismarck', 'ND', 'Plains', 46.8083, -100.7837),
    ('030', 'Raleigh, NC', 'Raleigh', 'NC', 'Southeast', 35.7796, -78.6382),
    ('032', 'Columbia, SC', 'Columbia', 'SC', 'Southeast', 34.0007, -81.0348),
    ('040', 'Orlando, FL', 'Orlando', 'FL', 'Southeast', 28.5383, -81.3792),
    ('042', 'Mobile, AL', 'Mobile', 'AL', 'Gulf Coast', 30.6954, -88.0399),
    ('046', 'Jackson, MS', 'Jackson', 'MS', 'Southeast', 32.2988, -90.1848),
    ('050', 'Baton Rouge, LA', 'Baton Rouge', 'LA', 'Gulf Coast', 30.4515, -91.1871),
    ('052', 'Beaumont, TX', 'Beaumont', 'TX', 'Gulf Coast', 30.0802, -94.1266),
    ('054', 'Corpus Christi, TX', 'Corpus Christi', 'TX', 'Gulf Coast', 27.8006, -97.3964),
    ('056', 'Austin, TX', 'Austin', 'TX', 'South Central', 30.2672, -97.7431),
    ('060', 'Amarillo, TX', 'Amarillo', 'TX', 'Plains', 35.2220, -101.8313),
    ('062', 'Little Rock, AR', 'Little Rock', 'AR', 'South Central', 34.7465, -92.2896),
    ('076', 'Toledo, OH', 'Toledo', 'OH', 'Midwest', 41.6528, -83.5379),
    ('078', 'Grand Rapids, MI', 'Grand Rapids', 'MI', 'Midwest', 42.9634, -85.6681),
    ('084', 'Milwaukee, WI', 'Milwaukee', 'WI', 'Midwest', 43.0389, -87.9065),
    ('086', 'Springfield, MO', 'Springfield', 'MO', 'Midwest', 37.2090, -93.2923),
    ('090', 'Davenport, IA', 'Davenport', 'IA,IL', 'Midwest', 41.5236, -90.5776),
    ('102', 'Lincoln, NE', 'Lincoln', 'NE', 'Plains', 40.8258, -96.6852),
]

for row in bea_extra:
    con.execute("""
        INSERT OR REPLACE INTO dim_bea
        (bea_code, bea_name, primary_city, states, region, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

print(f'Added {len(bea_extra)} BEA regions')

# Recreate views with better STCC matching using 2-digit fallback
print('Recreating analytical views with 2-digit STCC fallback...')

con.execute("""
    CREATE OR REPLACE VIEW v_commodity_flows AS
    SELECT
        w.stcc_2digit,
        COALESCE(s.stcc_group,
                 CASE w.stcc_2digit
                     WHEN '01' THEN 'Farm Products'
                     WHEN '10' THEN 'Metallic Ores'
                     WHEN '11' THEN 'Coal'
                     WHEN '14' THEN 'Non-Metallic Minerals'
                     WHEN '20' THEN 'Food Products'
                     WHEN '24' THEN 'Lumber/Wood'
                     WHEN '26' THEN 'Paper Products'
                     WHEN '28' THEN 'Chemicals'
                     WHEN '29' THEN 'Petroleum'
                     WHEN '32' THEN 'Stone/Clay/Glass'
                     WHEN '33' THEN 'Primary Metals'
                     WHEN '34' THEN 'Fabricated Metals'
                     WHEN '35' THEN 'Machinery'
                     WHEN '37' THEN 'Transportation Equipment'
                     WHEN '40' THEN 'Waste/Scrap'
                     WHEN '42' THEN 'Shipping Containers'
                     WHEN '46' THEN 'Intermodal'
                     WHEN '49' THEN 'Hazmat NEC'
                     ELSE 'Other (' || w.stcc_2digit || ')'
                 END) as commodity_group,
        w.origin_bea,
        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin_name,
        COALESCE(o.region, 'Unknown') as origin_region,
        w.term_bea,
        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as dest_name,
        COALESCE(d.region, 'Unknown') as dest_region,
        EXTRACT(YEAR FROM w.waybill_date) as year,
        EXTRACT(QUARTER FROM w.waybill_date) as quarter,
        SUM(w.exp_carloads) as total_carloads,
        SUM(w.exp_tons) as total_tons,
        SUM(w.exp_freight_rev) as total_revenue,
        COUNT(*) as sample_count,
        AVG(w.exp_freight_rev / NULLIF(w.exp_carloads, 0)) as avg_rev_per_car,
        AVG(w.exp_freight_rev / NULLIF(w.exp_tons, 0)) as avg_rev_per_ton
    FROM fact_waybill w
    LEFT JOIN dim_stcc s ON w.stcc = s.stcc_code
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
""")

con.execute("""
    CREATE OR REPLACE VIEW v_top_od_pairs AS
    SELECT
        origin_bea,
        origin_name,
        term_bea,
        dest_name,
        commodity_group,
        SUM(total_carloads) as total_carloads,
        SUM(total_tons) as total_tons,
        SUM(total_revenue) as total_revenue
    FROM v_commodity_flows
    WHERE origin_bea != '000' AND term_bea != '000'
    GROUP BY 1, 2, 3, 4, 5
    ORDER BY total_carloads DESC
""")

con.execute("""
    CREATE OR REPLACE VIEW v_commodity_summary AS
    SELECT
        stcc_2digit,
        commodity_group,
        year,
        SUM(total_carloads) as total_carloads,
        SUM(total_tons) as total_tons,
        SUM(total_revenue) as total_revenue,
        SUM(sample_count) as sample_count,
        AVG(avg_rev_per_car) as avg_rev_per_car,
        AVG(avg_rev_per_ton) as avg_rev_per_ton
    FROM v_commodity_flows
    GROUP BY 1, 2, 3
    ORDER BY total_carloads DESC
""")

con.close()
print('Done! Views recreated with improved matching.')
