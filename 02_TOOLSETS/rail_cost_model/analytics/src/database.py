"""
Rail Analytics Database Module
Handles DuckDB connection and core data operations
"""

import duckdb
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "rail_analytics" / "data"
WAYBILL_DIR = PROJECT_ROOT / "read_rail" / "STB" / "stb_build_1" / "Versions"
DB_PATH = DATA_DIR / "rail_analytics.duckdb"


def get_connection():
    """Get DuckDB connection"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def init_database():
    """Initialize database with all tables"""
    con = get_connection()

    logger.info("Initializing Rail Analytics Database...")

    # Create dimension tables
    _create_stcc_dimension(con)
    _create_bea_dimension(con)
    _create_car_type_dimension(con)
    _create_time_dimension(con)

    # Load waybill data
    _load_waybill_data(con)

    # Create analytical views
    _create_analytical_views(con)

    logger.info("Database initialization complete!")
    con.close()


def _create_stcc_dimension(con):
    """Create STCC commodity code dimension table with industry knowledge"""
    logger.info("Creating STCC dimension table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_stcc (
            stcc_code VARCHAR(7) PRIMARY KEY,
            stcc_2digit VARCHAR(2),
            stcc_group VARCHAR(50),
            description VARCHAR(255),
            category VARCHAR(100),
            typical_equipment VARCHAR(100),
            seasonality VARCHAR(100),
            hazmat_flag BOOLEAN DEFAULT FALSE,
            notes TEXT
        )
    """)

    # Major STCC codes with industry knowledge
    stcc_data = [
        # Farm Products (01)
        ('0113210', '01', 'Farm Products', 'Wheat', 'Grain', 'Covered Hopper', 'Jul-Nov harvest', False, 'Export via PNW, Gulf'),
        ('0113230', '01', 'Farm Products', 'Corn', 'Grain', 'Covered Hopper', 'Oct-Dec harvest', False, 'Ethanol feedstock, exports'),
        ('0113240', '01', 'Farm Products', 'Soybeans', 'Grain', 'Covered Hopper', 'Sep-Nov harvest', False, 'Export to China, crushing'),
        ('0114110', '01', 'Farm Products', 'Cotton, Raw', 'Agriculture', 'Boxcar', 'Oct-Dec harvest', False, 'TX, MS, CA origins'),

        # Coal (11)
        ('1121210', '11', 'Coal', 'Bituminous Coal', 'Energy', 'Open Top Hopper', 'Counter-seasonal', False, 'PRB dominant, declining'),
        ('1121220', '11', 'Coal', 'Sub-bituminous Coal', 'Energy', 'Open Top Hopper', 'Counter-seasonal', False, 'PRB Wyoming'),
        ('1121310', '11', 'Coal', 'Anthracite', 'Energy', 'Open Top Hopper', 'Steady', False, 'PA origin'),

        # Metallic Ores (10)
        ('1011110', '10', 'Metallic Ores', 'Iron Ore', 'Mining', 'Open Top Hopper', 'Steady', False, 'MN Mesabi Range'),
        ('1021110', '10', 'Metallic Ores', 'Copper Ore', 'Mining', 'Open Top Hopper', 'Steady', False, 'AZ, UT, MT'),

        # Non-Metallic Minerals (14)
        ('1411110', '14', 'Non-Metallic Minerals', 'Sand and Gravel', 'Construction', 'Open Top Hopper', 'Spring-Fall', False, 'Frac sand WI'),
        ('1422110', '14', 'Non-Metallic Minerals', 'Crushed Stone', 'Construction', 'Open Top Hopper', 'Spring-Fall', False, 'Construction material'),
        ('1455110', '14', 'Non-Metallic Minerals', 'ite and Rock Salt', 'Industrial', 'Covered Hopper', 'Winter peak', False, 'Road salt, industrial'),

        # Food Products (20)
        ('2011110', '20', 'Food Products', 'Meat, Fresh', 'Food', 'Refrigerated', 'Steady', False, 'Midwest processing'),
        ('2041110', '20', 'Food Products', 'Flour', 'Food', 'Covered Hopper', 'Steady', False, 'From wheat milling'),
        ('2046110', '20', 'Food Products', 'Corn Starch', 'Food', 'Covered Hopper', 'Steady', False, 'Wet milling product'),
        ('2062110', '20', 'Food Products', 'Sugar, Refined', 'Food', 'Covered Hopper', 'Steady', False, 'Beet and cane'),

        # Lumber/Wood (24)
        ('2411110', '24', 'Lumber/Wood', 'Logs', 'Forest Products', 'Flat Car', 'Year-round', False, 'PNW, Southeast'),
        ('2421110', '24', 'Lumber/Wood', 'Lumber, Softwood', 'Forest Products', 'Center Beam Flat', 'Construction season', False, 'Housing market driven'),
        ('2431110', '24', 'Lumber/Wood', 'Plywood', 'Forest Products', 'Boxcar', 'Construction season', False, 'PNW, South'),

        # Pulp/Paper (26)
        ('2611110', '26', 'Paper Products', 'Wood Pulp', 'Forest Products', 'Boxcar', 'Steady', False, 'Paper mill feedstock'),
        ('2621110', '26', 'Paper Products', 'Paper, Newsprint', 'Forest Products', 'Boxcar', 'Declining', False, 'Print media decline'),

        # Chemicals (28)
        ('2812110', '28', 'Chemicals', 'Chlorine', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Water treatment, hazmat'),
        ('2813110', '28', 'Chemicals', 'Industrial Gases', 'Industrial Chemicals', 'Tank Car', 'Steady', False, 'Manufacturing input'),
        ('2816110', '28', 'Chemicals', 'Pigments, Inorganic', 'Industrial Chemicals', 'Covered Hopper', 'Steady', False, 'Paint, coating'),
        ('2818110', '28', 'Chemicals', 'Industrial Organic Chemicals', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Varied hazmat'),
        ('2819110', '28', 'Chemicals', 'Industrial Inorganic Chemicals', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Varied hazmat'),
        ('2821110', '28', 'Chemicals', 'Plastic Materials, Resins', 'Plastics', 'Covered Hopper', 'Steady', False, 'Gulf Coast origin'),
        ('2869110', '28', 'Chemicals', 'Industrial Organic Chemicals NEC', 'Industrial Chemicals', 'Tank Car', 'Steady', True, 'Various'),
        ('2871110', '28', 'Chemicals', 'Nitrogenous Fertilizers', 'Fertilizer', 'Covered Hopper', 'Mar-Jun spring', False, 'Ammonia-based, corn belt'),
        ('2873110', '28', 'Chemicals', 'Phosphatic Fertilizers', 'Fertilizer', 'Covered Hopper', 'Mar-Jun spring', False, 'FL origin'),
        ('2874110', '28', 'Chemicals', 'Mixed Fertilizers', 'Fertilizer', 'Covered Hopper', 'Mar-Jun spring', False, 'Blended products'),

        # Petroleum (29)
        ('2911110', '29', 'Petroleum', 'Petroleum Refining Products', 'Energy', 'Tank Car', 'Steady', True, 'Gasoline, diesel'),
        ('2911130', '29', 'Petroleum', 'Gasoline', 'Energy', 'Tank Car', 'Summer peak', True, 'Refined product'),
        ('2911150', '29', 'Petroleum', 'Fuel Oils', 'Energy', 'Tank Car', 'Winter peak', True, 'Heating oil'),
        ('2911210', '29', 'Petroleum', 'Lubricating Oils', 'Energy', 'Tank Car', 'Steady', False, 'Industrial lubricants'),
        ('2911310', '29', 'Petroleum', 'Asphalt', 'Construction', 'Tank Car', 'Spring-Fall', False, 'Road construction'),

        # Rubber/Plastics (30)
        ('3011110', '30', 'Rubber/Plastics', 'Tires', 'Automotive', 'Boxcar', 'Steady', False, 'Automotive supply chain'),

        # Primary Metals (33)
        ('3312110', '33', 'Primary Metals', 'Steel, Hot Rolled', 'Metals', 'Coil Car', 'Steady', False, 'Integrated mills'),
        ('3312210', '33', 'Primary Metals', 'Steel, Cold Rolled', 'Metals', 'Coil Car', 'Steady', False, 'Automotive, appliance'),
        ('3341110', '33', 'Primary Metals', 'Aluminum, Primary', 'Metals', 'Coil Car', 'Steady', False, 'Smelter to fab'),

        # Fabricated Metals (34)
        ('3411110', '34', 'Fabricated Metals', 'Metal Cans', 'Packaging', 'Boxcar', 'Steady', False, 'Beverage cans'),

        # Transportation Equipment (37)
        ('3711110', '37', 'Transportation Equipment', 'Motor Vehicles', 'Automotive', 'Auto Rack', 'Model year cycle', False, 'Plant to dealer'),
        ('3714110', '37', 'Transportation Equipment', 'Motor Vehicle Parts', 'Automotive', 'Boxcar', 'Steady', False, 'JIT supply chain'),

        # Waste/Scrap (40)
        ('4011110', '40', 'Waste/Scrap', 'Waste, Hazardous', 'Waste', 'Tank Car', 'Steady', True, 'Regulated waste'),
        ('4021110', '40', 'Waste/Scrap', 'Iron and Steel Scrap', 'Metals', 'Gondola', 'Steady', False, 'EAF feedstock'),

        # Intermodal (46)
        ('4610110', '46', 'Intermodal', 'TOFC Shipments', 'Intermodal', 'Flat Car', 'Steady', False, 'Trailer on flat car'),
        ('4620110', '46', 'Intermodal', 'COFC Shipments', 'Intermodal', 'Well Car', 'Steady', False, 'Container on flat car'),
    ]

    con.executemany("""
        INSERT OR REPLACE INTO dim_stcc
        (stcc_code, stcc_2digit, stcc_group, description, category,
         typical_equipment, seasonality, hazmat_flag, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, stcc_data)

    logger.info(f"Loaded {len(stcc_data)} STCC codes")


def _create_bea_dimension(con):
    """Create BEA Economic Area dimension table"""
    logger.info("Creating BEA dimension table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_bea (
            bea_code VARCHAR(5) PRIMARY KEY,
            bea_name VARCHAR(100),
            primary_city VARCHAR(100),
            states VARCHAR(50),
            region VARCHAR(50),
            lat DOUBLE,
            lon DOUBLE
        )
    """)

    # Key BEA areas (179 total - adding major ones with coords)
    bea_data = [
        ('001', 'Bangor, ME', 'Bangor', 'ME', 'Northeast', 44.8016, -68.7712),
        ('002', 'Portland, ME', 'Portland', 'ME', 'Northeast', 43.6591, -70.2568),
        ('003', 'Burlington, VT', 'Burlington', 'VT', 'Northeast', 44.4759, -73.2121),
        ('010', 'Boston, MA', 'Boston', 'MA,NH', 'Northeast', 42.3601, -71.0589),
        ('013', 'Hartford, CT', 'Hartford', 'CT', 'Northeast', 41.7658, -72.6734),
        ('014', 'New York, NY', 'New York', 'NY,NJ,CT,PA', 'Northeast', 40.7128, -74.0060),
        ('018', 'Philadelphia, PA', 'Philadelphia', 'PA,NJ,DE,MD', 'Northeast', 39.9526, -75.1652),
        ('020', 'Baltimore, MD', 'Baltimore', 'MD', 'Mid-Atlantic', 39.2904, -76.6122),
        ('022', 'Washington, DC', 'Washington', 'DC,MD,VA,WV', 'Mid-Atlantic', 38.9072, -77.0369),
        ('024', 'Richmond, VA', 'Richmond', 'VA', 'Southeast', 37.5407, -77.4360),
        ('028', 'Charlotte, NC', 'Charlotte', 'NC,SC', 'Southeast', 35.2271, -80.8431),
        ('034', 'Atlanta, GA', 'Atlanta', 'GA', 'Southeast', 33.7490, -84.3880),
        ('036', 'Jacksonville, FL', 'Jacksonville', 'FL,GA', 'Southeast', 30.3322, -81.6557),
        ('038', 'Tampa, FL', 'Tampa', 'FL', 'Southeast', 27.9506, -82.4572),
        ('039', 'Miami, FL', 'Miami', 'FL', 'Southeast', 25.7617, -80.1918),
        ('044', 'Birmingham, AL', 'Birmingham', 'AL', 'Southeast', 33.5186, -86.8104),
        ('048', 'New Orleans, LA', 'New Orleans', 'LA,MS', 'Gulf Coast', 29.9511, -90.0715),
        ('051', 'Houston, TX', 'Houston', 'TX', 'Gulf Coast', 29.7604, -95.3698),
        ('055', 'Dallas, TX', 'Dallas', 'TX', 'South Central', 32.7767, -96.7970),
        ('058', 'San Antonio, TX', 'San Antonio', 'TX', 'South Central', 29.4241, -98.4936),
        ('064', 'Memphis, TN', 'Memphis', 'TN,AR,MS', 'South Central', 35.1495, -90.0490),
        ('066', 'Nashville, TN', 'Nashville', 'TN,KY', 'Southeast', 36.1627, -86.7816),
        ('068', 'Louisville, KY', 'Louisville', 'KY,IN', 'Midwest', 38.2527, -85.7585),
        ('070', 'Cincinnati, OH', 'Cincinnati', 'OH,KY,IN', 'Midwest', 39.1031, -84.5120),
        ('072', 'Columbus, OH', 'Columbus', 'OH', 'Midwest', 39.9612, -82.9988),
        ('074', 'Cleveland, OH', 'Cleveland', 'OH', 'Midwest', 41.4993, -81.6944),
        ('077', 'Detroit, MI', 'Detroit', 'MI', 'Midwest', 42.3314, -83.0458),
        ('080', 'Indianapolis, IN', 'Indianapolis', 'IN', 'Midwest', 39.7684, -86.1581),
        ('082', 'Chicago, IL', 'Chicago', 'IL,IN,WI', 'Midwest', 41.8781, -87.6298),
        ('085', 'St. Louis, MO', 'St. Louis', 'MO,IL', 'Midwest', 38.6270, -90.1994),
        ('088', 'Kansas City, MO', 'Kansas City', 'MO,KS', 'Plains', 39.0997, -94.5786),
        ('094', 'Minneapolis, MN', 'Minneapolis', 'MN,WI', 'Upper Midwest', 44.9778, -93.2650),
        ('098', 'Des Moines, IA', 'Des Moines', 'IA', 'Plains', 41.5868, -93.6250),
        ('100', 'Omaha, NE', 'Omaha', 'NE,IA', 'Plains', 41.2565, -95.9345),
        ('104', 'Wichita, KS', 'Wichita', 'KS', 'Plains', 37.6872, -97.3301),
        ('108', 'Oklahoma City, OK', 'Oklahoma City', 'OK', 'South Central', 35.4676, -97.5164),
        ('110', 'Denver, CO', 'Denver', 'CO', 'Mountain', 39.7392, -104.9903),
        ('120', 'Salt Lake City, UT', 'Salt Lake City', 'UT', 'Mountain', 40.7608, -111.8910),
        ('124', 'Phoenix, AZ', 'Phoenix', 'AZ', 'Southwest', 33.4484, -112.0740),
        ('128', 'Albuquerque, NM', 'Albuquerque', 'NM', 'Southwest', 35.0844, -106.6504),
        ('130', 'Las Vegas, NV', 'Las Vegas', 'NV', 'Southwest', 36.1699, -115.1398),
        ('140', 'Los Angeles, CA', 'Los Angeles', 'CA', 'Pacific', 34.0522, -118.2437),
        ('143', 'San Diego, CA', 'San Diego', 'CA', 'Pacific', 32.7157, -117.1611),
        ('145', 'Fresno, CA', 'Fresno', 'CA', 'Pacific', 36.7378, -119.7871),
        ('147', 'San Francisco, CA', 'San Francisco', 'CA', 'Pacific', 37.7749, -122.4194),
        ('150', 'Sacramento, CA', 'Sacramento', 'CA', 'Pacific', 38.5816, -121.4944),
        ('155', 'Portland, OR', 'Portland', 'OR,WA', 'Pacific Northwest', 45.5152, -122.6784),
        ('160', 'Seattle, WA', 'Seattle', 'WA', 'Pacific Northwest', 47.6062, -122.3321),
        ('164', 'Spokane, WA', 'Spokane', 'WA,ID', 'Pacific Northwest', 47.6587, -117.4260),
        ('170', 'Billings, MT', 'Billings', 'MT,WY', 'Mountain', 45.7833, -108.5007),
        ('172', 'Casper, WY', 'Casper', 'WY', 'Mountain', 42.8666, -106.3131),
    ]

    con.executemany("""
        INSERT OR REPLACE INTO dim_bea
        (bea_code, bea_name, primary_city, states, region, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, bea_data)

    logger.info(f"Loaded {len(bea_data)} BEA regions")


def _create_car_type_dimension(con):
    """Create car type dimension table"""
    logger.info("Creating car type dimension table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_car_type (
            stb_car_type VARCHAR(5) PRIMARY KEY,
            description VARCHAR(100),
            category VARCHAR(50),
            typical_commodities VARCHAR(255)
        )
    """)

    car_types = [
        ('TB', 'Tank Car - General', 'Tank', 'Chemicals, petroleum, food liquids'),
        ('TL', 'Tank Car - Lined', 'Tank', 'Corrosive chemicals'),
        ('TP', 'Tank Car - Pressure', 'Tank', 'LPG, anhydrous ammonia'),
        ('HT', 'Hopper - Open Top', 'Hopper', 'Coal, aggregates, ore'),
        ('HC', 'Hopper - Covered', 'Hopper', 'Grain, fertilizer, cement, plastic'),
        ('XM', 'Boxcar - General', 'Boxcar', 'Paper, lumber, general freight'),
        ('XL', 'Boxcar - Insulated', 'Boxcar', 'Temperature sensitive goods'),
        ('FM', 'Flat Car - General', 'Flat', 'Steel, lumber, machinery'),
        ('FC', 'Flat Car - Centerbeam', 'Flat', 'Lumber, wallboard'),
        ('GS', 'Gondola - General', 'Gondola', 'Steel, scrap, aggregates'),
        ('GB', 'Gondola - Coil', 'Gondola', 'Steel coils'),
        ('RS', 'Refrigerator Car', 'Refrigerated', 'Produce, meat, dairy'),
        ('AU', 'Auto Rack - Multi-level', 'Autorack', 'Finished vehicles'),
        ('IM', 'Intermodal - Well Car', 'Intermodal', 'Containers'),
        ('IT', 'Intermodal - Spine Car', 'Intermodal', 'Trailers, containers'),
    ]

    con.executemany("""
        INSERT OR REPLACE INTO dim_car_type
        (stb_car_type, description, category, typical_commodities)
        VALUES (?, ?, ?, ?)
    """, car_types)

    logger.info(f"Loaded {len(car_types)} car types")


def _create_time_dimension(con):
    """Create time dimension table for 2015-2030"""
    logger.info("Creating time dimension table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_time (
            date_key INTEGER PRIMARY KEY,
            full_date DATE,
            year INTEGER,
            quarter INTEGER,
            month INTEGER,
            month_name VARCHAR(20),
            week_of_year INTEGER,
            day_of_week INTEGER,
            day_name VARCHAR(20),
            is_weekend BOOLEAN
        )
    """)

    con.execute("""
        INSERT OR IGNORE INTO dim_time
        SELECT
            CAST(strftime(d, '%Y%m%d') AS INTEGER) as date_key,
            d as full_date,
            EXTRACT(YEAR FROM d) as year,
            EXTRACT(QUARTER FROM d) as quarter,
            EXTRACT(MONTH FROM d) as month,
            strftime(d, '%B') as month_name,
            EXTRACT(WEEK FROM d) as week_of_year,
            EXTRACT(DOW FROM d) as day_of_week,
            strftime(d, '%A') as day_name,
            EXTRACT(DOW FROM d) IN (0, 6) as is_weekend
        FROM (
            SELECT CAST('2015-01-01' AS DATE) + INTERVAL (i) DAY as d
            FROM generate_series(0, 5844) t(i)
        )
    """)

    logger.info("Created time dimension 2015-2030")


def _load_waybill_data(con):
    """Load waybill CSV chunks into fact table"""
    logger.info("Loading waybill data...")

    # Check if chunks exist
    chunk_pattern = str(WAYBILL_DIR / "waybill_2023_chunk_*.csv")

    # Create staging table from CSV files
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS fact_waybill AS
        SELECT
            ROW_NUMBER() OVER () as waybill_id,
            TRY_CAST(Waybill_Date AS DATE) as waybill_date,
            TRY_CAST(Accounting_Period AS DATE) as accounting_period,
            CAST(Num_Carloads AS INTEGER) as num_carloads,
            Car_Ownership as car_ownership,
            Car_Type as car_type,
            STB_Car_Type as stb_car_type,
            CAST(STCC AS VARCHAR) as stcc,
            LEFT(CAST(STCC AS VARCHAR), 2) as stcc_2digit,
            TRY_CAST(Billed_Weight AS DOUBLE) as billed_weight,
            TRY_CAST(Actual_Weight AS DOUBLE) as actual_weight,
            TRY_CAST(Freight_Revenue AS DOUBLE) as freight_revenue,
            TRY_CAST(Transit_Charges AS DOUBLE) as transit_charges,
            TRY_CAST(Misc_Charges AS DOUBLE) as misc_charges,
            Inter_Intra as inter_intra,
            Type_Move as type_move,
            All_Rail_Intermodal as all_rail_intermodal,
            LPAD(CAST(Origin_BEA AS VARCHAR), 3, '0') as origin_bea,
            LPAD(CAST(Term_BEA AS VARCHAR), 3, '0') as term_bea,
            CAST(Short_Line_Miles AS INTEGER) as short_line_miles,
            CAST(Num_Interchanges AS INTEGER) as num_interchanges,
            TRY_CAST(Exact_Exp_Factor AS DOUBLE) as expansion_factor,
            TRY_CAST(Exp_Carloads AS DOUBLE) as exp_carloads,
            TRY_CAST(Exp_Tons AS DOUBLE) as exp_tons,
            TRY_CAST(Exp_Freight_Rev AS DOUBLE) as exp_freight_rev,
            Haz_Bulk as hazmat_flag,
            Error_Codes as error_codes
        FROM read_csv_auto('{chunk_pattern}',
            ignore_errors=true,
            null_padding=true
        )
        WHERE STCC IS NOT NULL
    """)

    # Get row count
    count = con.execute("SELECT COUNT(*) FROM fact_waybill").fetchone()[0]
    logger.info(f"Loaded {count:,} waybill records")


def _create_analytical_views(con):
    """Create pre-computed analytical views"""
    logger.info("Creating analytical views...")

    # Commodity flow summary
    con.execute("""
        CREATE OR REPLACE VIEW v_commodity_flows AS
        SELECT
            w.stcc_2digit,
            COALESCE(s.stcc_group, 'Unknown') as commodity_group,
            w.origin_bea,
            COALESCE(o.bea_name, 'Unknown') as origin_name,
            COALESCE(o.region, 'Unknown') as origin_region,
            w.term_bea,
            COALESCE(d.bea_name, 'Unknown') as dest_name,
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
        LEFT JOIN dim_stcc s ON LEFT(w.stcc, 7) = s.stcc_code
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    """)

    # Top O-D pairs by volume
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
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY total_carloads DESC
    """)

    # Commodity summary
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

    logger.info("Created analytical views")


def query(sql: str) -> pd.DataFrame:
    """Execute query and return DataFrame"""
    con = get_connection()
    result = con.execute(sql).fetchdf()
    con.close()
    return result


def get_commodity_flows(stcc_2digit: str = None, year: int = None) -> pd.DataFrame:
    """Get commodity flow data with optional filters"""
    where_clauses = []
    if stcc_2digit:
        where_clauses.append(f"stcc_2digit = '{stcc_2digit}'")
    if year:
        where_clauses.append(f"year = {year}")

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    return query(f"""
        SELECT * FROM v_commodity_flows
        {where_sql}
        ORDER BY total_carloads DESC
        LIMIT 1000
    """)


def get_top_od_pairs(limit: int = 50, commodity_group: str = None) -> pd.DataFrame:
    """Get top O-D pairs by volume"""
    where_sql = f"WHERE commodity_group = '{commodity_group}'" if commodity_group else ""

    return query(f"""
        SELECT * FROM v_top_od_pairs
        {where_sql}
        LIMIT {limit}
    """)


def get_commodity_summary() -> pd.DataFrame:
    """Get summary by commodity group"""
    return query("SELECT * FROM v_commodity_summary ORDER BY total_carloads DESC")


if __name__ == "__main__":
    init_database()
