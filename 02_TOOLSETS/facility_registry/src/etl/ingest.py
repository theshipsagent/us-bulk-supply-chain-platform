"""Ingest module for loading EPA FRS CSV data into DuckDB."""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import duckdb
import pandas as pd
import yaml
from tqdm import tqdm

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_db_connection() -> duckdb.DuckDBPyConnection:
    """Get DuckDB connection."""
    config = load_config()
    db_path = config['database']['path']

    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(db_path)
    # Install and load spatial extension for future geospatial operations
    conn.execute("INSTALL spatial")
    conn.execute("LOAD spatial")

    return conn


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize a dataframe.

    Args:
        df: Input dataframe

    Returns:
        Cleaned dataframe
    """
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]

    # Replace empty strings with None
    df = df.replace('', None)
    df = df.replace(r'^\s*$', None, regex=True)

    return df


def create_naics_lookup_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create NAICS code description lookup table."""
    # Abbreviated NAICS code descriptions (2-digit sectors)
    # Full 6-digit codes would be too extensive for initial setup
    naics_data = {
        'naics_code': [
            '11', '21', '22', '23',
            '31', '32', '33',
            '42', '44', '45',
            '48', '49', '51', '52', '53', '54', '55', '56',
            '61', '62', '71', '72', '81', '92'
        ],
        'description': [
            'Agriculture, Forestry, Fishing and Hunting',
            'Mining, Quarrying, and Oil and Gas Extraction',
            'Utilities',
            'Construction',
            'Manufacturing',
            'Manufacturing',
            'Manufacturing',
            'Wholesale Trade',
            'Retail Trade',
            'Retail Trade',
            'Transportation and Warehousing',
            'Transportation and Warehousing',
            'Information',
            'Finance and Insurance',
            'Real Estate and Rental and Leasing',
            'Professional, Scientific, and Technical Services',
            'Management of Companies and Enterprises',
            'Administrative and Support and Waste Management and Remediation Services',
            'Educational Services',
            'Health Care and Social Assistance',
            'Arts, Entertainment, and Recreation',
            'Accommodation and Food Services',
            'Other Services (except Public Administration)',
            'Public Administration'
        ]
    }

    df = pd.DataFrame(naics_data)
    conn.execute("DROP TABLE IF EXISTS naics_lookup")
    conn.execute("""
        CREATE TABLE naics_lookup (
            naics_code VARCHAR PRIMARY KEY,
            description VARCHAR
        )
    """)
    conn.execute("INSERT INTO naics_lookup SELECT * FROM df")
    logger.info(f"Created naics_lookup table with {len(df)} sectors")


def create_sic_lookup_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create SIC code description lookup table."""
    # Abbreviated SIC major groups
    sic_data = {
        'sic_code': [
            '01', '02', '07', '08', '09',
            '10', '12', '13', '14', '15', '16', '17',
            '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
            '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
            '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',
            '50', '51', '52', '53', '54', '55', '56', '57', '58', '59',
            '60', '61', '62', '63', '64', '65', '67',
            '70', '72', '73', '75', '76', '78', '79',
            '80', '81', '82', '83', '84', '86', '87', '88', '89',
            '91', '92', '93', '94', '95', '96', '97', '99'
        ],
        'description': [
            'Agricultural Production - Crops', 'Agricultural Production - Livestock', 'Agricultural Services',
            'Forestry', 'Fishing, Hunting and Trapping',
            'Metal Mining', 'Coal Mining', 'Oil and Gas Extraction', 'Mining and Quarrying of Nonmetallic Minerals',
            'Building Construction', 'Heavy Construction', 'Construction - Special Trade Contractors',
            'Food and Kindred Products', 'Tobacco Products', 'Textile Mill Products', 'Apparel Products',
            'Lumber and Wood Products', 'Furniture and Fixtures', 'Paper and Allied Products',
            'Printing, Publishing', 'Chemicals and Allied Products', 'Petroleum Refining',
            'Rubber and Plastics', 'Leather Products', 'Stone, Clay, Glass Products',
            'Primary Metal Industries', 'Fabricated Metal Products', 'Industrial Machinery',
            'Electronic Equipment', 'Transportation Equipment', 'Measuring Instruments', 'Miscellaneous Manufacturing',
            'Railroad Transportation', 'Local Passenger Transit', 'Motor Freight Transportation',
            'United States Postal Service', 'Water Transportation', 'Transportation by Air',
            'Pipelines', 'Transportation Services', 'Communications', 'Electric, Gas, Sanitary Services',
            'Wholesale Trade - Durable Goods', 'Wholesale Trade - Nondurable Goods',
            'Building Materials', 'General Merchandise Stores', 'Food Stores',
            'Automotive Dealers', 'Apparel Stores', 'Home Furniture Stores',
            'Eating and Drinking Places', 'Miscellaneous Retail',
            'Depository Institutions', 'Nondepository Credit', 'Security Brokers',
            'Insurance Carriers', 'Insurance Agents', 'Real Estate', 'Holding Offices',
            'Hotels and Lodging', 'Personal Services', 'Business Services',
            'Automotive Services', 'Miscellaneous Repair Services', 'Motion Pictures', 'Amusement and Recreation',
            'Health Services', 'Legal Services', 'Educational Services',
            'Social Services', 'Museums', 'Membership Organizations', 'Engineering Services',
            'Private Households', 'Miscellaneous Services',
            'Executive, Legislative', 'Justice, Public Order', 'Public Finance',
            'Administration of Human Resources', 'Environmental Quality', 'Administration of Economic Programs',
            'National Security', 'Nonclassifiable Establishments'
        ]
    }

    df = pd.DataFrame(sic_data)
    conn.execute("DROP TABLE IF EXISTS sic_lookup")
    conn.execute("""
        CREATE TABLE sic_lookup (
            sic_code VARCHAR PRIMARY KEY,
            description VARCHAR
        )
    """)
    conn.execute("INSERT INTO sic_lookup SELECT * FROM df")
    logger.info(f"Created sic_lookup table with {len(df)} major groups")


def ingest_echo_files(conn: duckdb.DuckDBPyConnection, force: bool = False) -> Dict[str, int]:
    """
    Ingest ECHO FRS CSV files into DuckDB.

    Args:
        conn: DuckDB connection
        force: Drop and recreate tables if they exist

    Returns:
        Dictionary of table names to row counts
    """
    config = load_config()
    raw_dir = Path(config['data']['raw_dir'])

    row_counts = {}

    # 1. Ingest FRS_FACILITIES.csv (try both uppercase and lowercase)
    facilities_path = raw_dir / "FRS_FACILITIES.csv"
    if not facilities_path.exists():
        facilities_path = raw_dir / "FRS_FACILITIES.CSV"
    if facilities_path.exists():
        logger.info(f"Ingesting {facilities_path.name}")

        df = pd.read_csv(facilities_path, encoding='latin1', low_memory=False)
        df = clean_dataframe(df)

        # Rename columns to match our schema
        # ECHO columns: FAC_NAME, FAC_STREET, FAC_CITY, FAC_STATE, FAC_ZIP, REGISTRY_ID,
        # FAC_COUNTY, FAC_EPA_REGION, LATITUDE_MEASURE, LONGITUDE_MEASURE
        df = df.rename(columns={
            'FAC_NAME': 'fac_name',
            'FAC_STREET': 'fac_street',
            'FAC_CITY': 'fac_city',
            'FAC_STATE': 'fac_state',
            'FAC_ZIP': 'fac_zip',
            'REGISTRY_ID': 'registry_id',
            'FAC_COUNTY': 'fac_county',
            'FAC_EPA_REGION': 'fac_epa_region',
            'LATITUDE_MEASURE': 'latitude',
            'LONGITUDE_MEASURE': 'longitude'
        })

        # Reorder columns to match table schema (registry_id first)
        df = df[['registry_id', 'fac_name', 'fac_street', 'fac_city', 'fac_state',
                 'fac_zip', 'fac_county', 'fac_epa_region', 'latitude', 'longitude']]

        # Create facilities table
        if force:
            conn.execute("DROP TABLE IF EXISTS facilities")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS facilities (
                registry_id VARCHAR,
                fac_name VARCHAR,
                fac_street VARCHAR,
                fac_city VARCHAR,
                fac_state VARCHAR,
                fac_zip VARCHAR,
                fac_county VARCHAR,
                fac_epa_region VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            )
        """)

        # Insert the data
        conn.execute("INSERT INTO facilities SELECT * FROM df")

        row_counts['facilities'] = len(df)
        logger.info(f"Loaded {len(df)} facilities")

    # 2. Ingest FRS_PROGRAM_LINKS.csv
    program_links_path = raw_dir / "FRS_PROGRAM_LINKS.csv"
    if not program_links_path.exists():
        program_links_path = raw_dir / "FRS_PROGRAM_LINKS.CSV"
    if program_links_path.exists():
        logger.info(f"Ingesting {program_links_path.name}")

        df = pd.read_csv(program_links_path, encoding='latin1', low_memory=False)
        df = clean_dataframe(df)

        # Rename columns to lowercase for consistency
        df = df.rename(columns={
            'PGM_SYS_ACRNM': 'pgm_sys_acrnm',
            'PGM_SYS_ID': 'pgm_sys_id',
            'REGISTRY_ID': 'registry_id',
            'PRIMARY_NAME': 'primary_name',
            'LOCATION_ADDRESS': 'location_address',
            'SUPPLEMENTAL_LOCATION': 'supplemental_location',
            'CITY_NAME': 'city_name',
            'COUNTY_NAME': 'county_name',
            'FIPS_CODE': 'fips_code',
            'STATE_CODE': 'state_code',
            'STATE_NAME': 'state_name',
            'COUNTRY_NAME': 'country_name',
            'POSTAL_CODE': 'postal_code'
        })

        if force:
            conn.execute("DROP TABLE IF EXISTS program_links")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS program_links (
                pgm_sys_acrnm VARCHAR,
                pgm_sys_id VARCHAR,
                registry_id VARCHAR,
                primary_name VARCHAR,
                location_address VARCHAR,
                supplemental_location VARCHAR,
                city_name VARCHAR,
                county_name VARCHAR,
                fips_code VARCHAR,
                state_code VARCHAR,
                state_name VARCHAR,
                country_name VARCHAR,
                postal_code VARCHAR
            )
        """)

        conn.execute("INSERT INTO program_links SELECT * FROM df")

        row_counts['program_links'] = len(df)
        logger.info(f"Loaded {len(df)} program links")

    # 3. Ingest FRS_NAICS_CODES.csv
    naics_path = raw_dir / "FRS_NAICS_CODES.csv"
    if not naics_path.exists():
        naics_path = raw_dir / "FRS_NAICS_CODES.CSV"
    if naics_path.exists():
        logger.info(f"Ingesting {naics_path.name}")

        df = pd.read_csv(naics_path, encoding='latin1', low_memory=False)
        df = clean_dataframe(df)

        # Rename columns - note ECHO has typo: PGM_SYS_ACNRM instead of ACRNM
        df = df.rename(columns={
            'PGM_SYS_ID': 'pgm_sys_id',
            'PGM_SYS_ACNRM': 'pgm_sys_acrnm',  # Fix the typo
            'NAICS_CODE': 'naics_code',
            'REGISTRY_ID': 'registry_id'
        })

        if force:
            conn.execute("DROP TABLE IF EXISTS naics_codes")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS naics_codes (
                pgm_sys_id VARCHAR,
                pgm_sys_acrnm VARCHAR,
                naics_code VARCHAR,
                registry_id VARCHAR
            )
        """)

        conn.execute("INSERT INTO naics_codes SELECT * FROM df")

        row_counts['naics_codes'] = len(df)
        logger.info(f"Loaded {len(df)} NAICS codes")

    # 4. Ingest FRS_SIC_CODES.csv
    sic_path = raw_dir / "FRS_SIC_CODES.csv"
    if not sic_path.exists():
        sic_path = raw_dir / "FRS_SIC_CODES.CSV"
    if sic_path.exists():
        logger.info(f"Ingesting {sic_path.name}")

        df = pd.read_csv(sic_path, encoding='latin1', low_memory=False)
        df = clean_dataframe(df)

        # Rename columns - note ECHO has typo: PGM_SYS_ACNRM instead of ACRNM
        df = df.rename(columns={
            'PGM_SYS_ID': 'pgm_sys_id',
            'PGM_SYS_ACNRM': 'pgm_sys_acrnm',  # Fix the typo
            'SIC_CODE': 'sic_code',
            'REGISTRY_ID': 'registry_id'
        })

        if force:
            conn.execute("DROP TABLE IF EXISTS sic_codes")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sic_codes (
                pgm_sys_id VARCHAR,
                pgm_sys_acrnm VARCHAR,
                sic_code VARCHAR,
                registry_id VARCHAR
            )
        """)

        conn.execute("INSERT INTO sic_codes SELECT * FROM df")

        row_counts['sic_codes'] = len(df)
        logger.info(f"Loaded {len(df)} SIC codes")

    # Create lookup tables
    create_naics_lookup_table(conn)
    create_sic_lookup_table(conn)

    return row_counts


def print_ingest_summary(conn: duckdb.DuckDBPyConnection) -> None:
    """Print summary statistics about ingested data."""
    print("\n" + "="*80)
    print("INGEST SUMMARY")
    print("="*80)

    # Table row counts
    tables = ['facilities', 'program_links', 'naics_codes', 'sic_codes']
    print("\nTable Row Counts:")
    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:20s}: {count:,}")
        except:
            print(f"  {table:20s}: (not found)")

    # State distribution
    try:
        print("\nTop 10 States by Facility Count:")
        result = conn.execute("""
            SELECT fac_state, COUNT(*) as count
            FROM facilities
            WHERE fac_state IS NOT NULL
            GROUP BY fac_state
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        for state, count in result:
            print(f"  {state}: {count:,}")
    except Exception as e:
        logger.error(f"Could not get state distribution: {e}")

    # NAICS distribution
    try:
        print("\nTop 10 NAICS Codes:")
        result = conn.execute("""
            SELECT
                SUBSTRING(naics_code, 1, 2) as sector,
                COUNT(*) as count
            FROM naics_codes
            WHERE naics_code IS NOT NULL
            GROUP BY sector
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        for sector, count in result:
            print(f"  {sector}: {count:,}")
    except Exception as e:
        logger.error(f"Could not get NAICS distribution: {e}")

    print("\n" + "="*80)
