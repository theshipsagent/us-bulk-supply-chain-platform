"""
Download and Load Historical STB Waybill Data (2018-2022)

This script downloads Public Use Waybill Sample files from the STB website,
extracts and parses them from fixed-width format, and loads them into the database.

Data source: https://www.stb.gov/reports-data/waybill/
"""

import os
import sys
import zipfile
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Setup paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data" / "waybill_historical"
DATA_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPT_DIR / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# STB Waybill download URLs
WAYBILL_URLS = {
    2018: "https://www.stb.gov/wp-content/uploads/PublicUseWaybillSample2018-REV-1-13-23.zip",
    2019: "https://www.stb.gov/wp-content/uploads/PublicUseWaybillSample2019.zip",
    2020: "https://www.stb.gov/wp-content/uploads/PublicUseWaybillSample2020.zip",
    2021: "https://www.stb.gov/wp-content/uploads/PublicUseWaybillSample2021.zip",
    2022: "https://www.stb.gov/wp-content/uploads/PublicUseWaybillSample2022.zip",
}

# Fixed-width column specifications for STB waybill format
# (start, end) positions for each field
COL_SPECS = [
    (0, 6),      # Waybill Date (YYMMDD)
    (6, 10),     # Accounting Period (YYMM)
    (10, 14),    # Number of Carloads
    (14, 15),    # Car Ownership Code
    (15, 19),    # Car Type
    (19, 23),    # Mechanical Designation
    (23, 25),    # STB/ICC Car Type
    (25, 28),    # TOFC/COFC Plan Code
    (28, 32),    # Number of TOFC/COFC Units
    (32, 33),    # TOFC/COFC Ownership
    (33, 34),    # TOFC/COFC Type
    (34, 35),    # Hazardous/Bulk Flag
    (35, 40),    # STCC Commodity Code
    (40, 47),    # Billed Weight
    (47, 54),    # Actual Weight
    (54, 63),    # Freight Revenue
    (63, 72),    # Transit Charges
    (72, 81),    # Misc Charges
    (81, 82),    # Inter/Intra Code
    (82, 83),    # Type of Move
    (83, 84),    # All Rail/Intermodal
    (84, 85),    # Type Move via Water
    (85, 86),    # Transit Code
    (86, 87),    # Substituted Truck
    (87, 88),    # Rebill Code
    (88, 92),    # Estimated Short Line Miles
    (92, 93),    # Stratum ID
    (93, 94),    # Subsample Code
    (94, 99),    # Exact Expansion Factor
    (99, 102),   # Theoretical Expansion Factor
    (102, 103),  # Number of Interchanges
    (103, 106),  # Origin BEA
    (106, 107),  # Origin Territory
    (107, 109),  # Interchange State #1
    (109, 111),  # Interchange State #2
    (111, 113),  # Interchange State #3
    (113, 115),  # Interchange State #4
    (115, 117),  # Interchange State #5
    (117, 119),  # Interchange State #6
    (119, 121),  # Interchange State #7
    (121, 123),  # Interchange State #8
    (123, 125),  # Interchange State #9
    (125, 128),  # Termination BEA
    (128, 129),  # Termination Territory
    (129, 130),  # Reporting Period Length
    (130, 135),  # Car Capacity
    (135, 138),  # Nominal Capacity
    (138, 142),  # Tare Weight
    (142, 147),  # Outside Length
    (147, 151),  # Outside Width
    (151, 155),  # Outside Height
    (155, 159),  # Extreme Height
    (159, 160),  # Wheel Bearings/Brakes
    (160, 161),  # Number of Axles
    (161, 163),  # Draft Gear
    (163, 164),  # Articulated Units
    (164, 168),  # Error Codes
    (168, 214),  # Blank Padding
    (214, 215),  # Routing Error Flag
    (215, 221),  # Expanded Carloads
    (221, 230),  # Expanded Tons
    (230, 241),  # Expanded Freight Revenue
    (241, 247),  # Expanded Trailer Count
]

# Column names matching the CSV format from 2023
COL_NAMES = [
    'Waybill_Date', 'Accounting_Period', 'Num_Carloads', 'Car_Ownership',
    'Car_Type', 'Mech_Designation', 'STB_Car_Type', 'TOFC_COFC_Code',
    'Num_TOFC_COFC', 'TOFC_Ownership', 'TOFC_Type', 'Haz_Bulk',
    'STCC', 'Billed_Weight', 'Actual_Weight', 'Freight_Revenue',
    'Transit_Charges', 'Misc_Charges', 'Inter_Intra', 'Type_Move',
    'All_Rail_Intermodal', 'Move_Via_Water', 'Transit_Code', 'Truck_for_Rail',
    'Rebill_Code', 'Short_Line_Miles', 'Stratum_ID', 'Subsample_Code',
    'Exact_Exp_Factor', 'Theo_Exp_Factor', 'Num_Interchanges',
    'Origin_BEA', 'Territory_Origin', 'State_1', 'State_2', 'State_3',
    'State_4', 'State_5', 'State_6', 'State_7', 'State_8', 'State_9',
    'Term_BEA', 'Territory_Term', 'Rep_Period_Len', 'Car_Capacity',
    'Nom_Car_Cap', 'Tare_Weight', 'Outside_Length', 'Outside_Width',
    'Outside_Height', 'Extreme_Height', 'Wheel_Bearings', 'Num_Axles',
    'Draft_Gear', 'Num_Articulated', 'Error_Codes', 'Blank',
    'Routing_Error', 'Exp_Carloads', 'Exp_Tons', 'Exp_Freight_Rev',
    'Exp_TOFC_Count'
]


def download_waybill(year: int) -> Path:
    """Download waybill ZIP file for a given year."""
    url = WAYBILL_URLS.get(year)
    if not url:
        raise ValueError(f"No URL defined for year {year}")

    zip_path = DATA_DIR / f"waybill_{year}.zip"

    if zip_path.exists():
        logger.info(f"ZIP file already exists: {zip_path}")
        return zip_path

    logger.info(f"Downloading {year} waybill from {url}...")
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = downloaded / total_size * 100
                print(f"\r  Downloading: {pct:.1f}%", end='', flush=True)

    print()  # Newline after progress
    logger.info(f"Downloaded: {zip_path} ({downloaded / 1024 / 1024:.1f} MB)")
    return zip_path


def extract_waybill(zip_path: Path, year: int) -> Path:
    """Extract the waybill data file from ZIP."""
    extract_dir = DATA_DIR / f"extracted_{year}"
    extract_dir.mkdir(exist_ok=True)

    logger.info(f"Extracting {zip_path}...")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        all_files = [f for f in zf.namelist() if not f.startswith('__MACOSX')]
        logger.info(f"Files in ZIP: {all_files}")

        # Prioritize .txt files (the actual data files)
        txt_files = [f for f in all_files if f.lower().endswith('.txt')]

        # If no .txt files, look for files without common non-data extensions
        if not txt_files:
            data_files = [f for f in all_files
                          if not any(f.lower().endswith(ext)
                                     for ext in ['.pdf', '.docx', '.jpg', '.jpeg', '.png', '.gif'])]
        else:
            data_files = txt_files

        logger.info(f"Data files to try: {data_files}")

        for file in data_files:
            zf.extract(file, extract_dir)
            extracted_path = extract_dir / file
            if extracted_path.exists() and extracted_path.stat().st_size > 1000:
                logger.info(f"Extracted: {extracted_path}")
                return extracted_path

    raise FileNotFoundError(f"No data file found in {zip_path}")


def parse_date(date_str: str, is_accounting: bool = False) -> str:
    """Parse MMDDYY (waybill) or YYMM (accounting) date string to ISO format."""
    try:
        date_str = str(date_str).strip()
        if not date_str or date_str == '0' or date_str == '000000':
            return ''

        if is_accounting:
            # YYMM format
            if len(date_str) == 4:
                yy = int(date_str[:2])
                mm = int(date_str[2:4])
                year = 2000 + yy if yy < 50 else 1900 + yy
                if 1 <= mm <= 12:
                    return f"{year}-{mm:02d}-01"
        else:
            # MMDDYY format (historical waybill files use this format)
            if len(date_str) == 6:
                mm = int(date_str[:2])
                dd = int(date_str[2:4])
                yy = int(date_str[4:6])
                year = 2000 + yy if yy < 50 else 1900 + yy
                # Validate date components
                if 1 <= mm <= 12 and 1 <= dd <= 31:
                    return f"{year}-{mm:02d}-{dd:02d}"

        return ''
    except:
        return ''


def process_waybill_file(data_path: Path, year: int) -> pd.DataFrame:
    """Parse fixed-width waybill file into DataFrame."""
    logger.info(f"Parsing {data_path}...")

    # Read fixed-width file
    df = pd.read_fwf(
        data_path,
        colspecs=COL_SPECS,
        names=COL_NAMES,
        dtype=str,
        encoding='latin-1'
    )

    logger.info(f"Parsed {len(df):,} records from {year}")

    # Clean and transform data
    df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)

    # Convert dates
    df['Waybill_Date'] = df['Waybill_Date'].apply(lambda x: parse_date(x, False))
    df['Accounting_Period'] = df['Accounting_Period'].apply(lambda x: parse_date(x, True))

    # Convert numeric columns
    numeric_cols = [
        'Num_Carloads', 'Billed_Weight', 'Actual_Weight', 'Freight_Revenue',
        'Transit_Charges', 'Misc_Charges', 'Short_Line_Miles', 'Num_Interchanges',
        'Exact_Exp_Factor', 'Exp_Carloads', 'Exp_Tons', 'Exp_Freight_Rev'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Pad BEA codes to 3 digits
    df['Origin_BEA'] = df['Origin_BEA'].apply(lambda x: str(x).zfill(3) if pd.notna(x) else '000')
    df['Term_BEA'] = df['Term_BEA'].apply(lambda x: str(x).zfill(3) if pd.notna(x) else '000')

    # Filter valid records
    df = df[df['STCC'].notna() & (df['STCC'] != '')]

    logger.info(f"Cleaned to {len(df):,} valid records")

    return df


def save_to_csv(df: pd.DataFrame, year: int) -> Path:
    """Save DataFrame to CSV."""
    csv_path = DATA_DIR / f"waybill_{year}_processed.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved: {csv_path}")
    return csv_path


def load_to_database(csv_paths: list):
    """Load all CSV files into the database."""
    from database import get_connection

    conn = get_connection()

    # Create a new fact table for historical data
    logger.info("Creating historical waybill table...")

    # First, check if we need to backup existing data
    try:
        existing_count = conn.execute("SELECT COUNT(*) FROM fact_waybill").fetchone()[0]
        logger.info(f"Existing records in fact_waybill: {existing_count:,}")
    except:
        existing_count = 0

    # Load each CSV file
    for csv_path in csv_paths:
        if not csv_path.exists():
            logger.warning(f"File not found: {csv_path}")
            continue

        year = int(csv_path.stem.split('_')[1])
        logger.info(f"Loading {year} data from {csv_path}...")

        # Load into a temp table first
        conn.execute(f"""
            CREATE OR REPLACE TEMP TABLE temp_waybill_{year} AS
            SELECT
                TRY_CAST(Waybill_Date AS DATE) as waybill_date,
                TRY_CAST(Accounting_Period AS DATE) as accounting_period,
                CAST(Num_Carloads AS INTEGER) as num_carloads,
                CAST(Car_Ownership AS VARCHAR) as car_ownership,
                CAST(Car_Type AS VARCHAR) as car_type,
                CAST(STB_Car_Type AS VARCHAR) as stb_car_type,
                CAST(STCC AS VARCHAR) as stcc,
                LEFT(CAST(STCC AS VARCHAR), 2) as stcc_2digit,
                TRY_CAST(Billed_Weight AS DOUBLE) as billed_weight,
                TRY_CAST(Actual_Weight AS DOUBLE) as actual_weight,
                TRY_CAST(Freight_Revenue AS DOUBLE) as freight_revenue,
                TRY_CAST(Transit_Charges AS DOUBLE) as transit_charges,
                TRY_CAST(Misc_Charges AS DOUBLE) as misc_charges,
                CAST(Inter_Intra AS VARCHAR) as inter_intra,
                CAST(Type_Move AS VARCHAR) as type_move,
                CAST(All_Rail_Intermodal AS VARCHAR) as all_rail_intermodal,
                CAST(Origin_BEA AS VARCHAR) as origin_bea,
                CAST(Term_BEA AS VARCHAR) as term_bea,
                CAST(Short_Line_Miles AS INTEGER) as short_line_miles,
                CAST(Num_Interchanges AS INTEGER) as num_interchanges,
                TRY_CAST(Exact_Exp_Factor AS DOUBLE) as expansion_factor,
                TRY_CAST(Exp_Carloads AS DOUBLE) as exp_carloads,
                TRY_CAST(Exp_Tons AS DOUBLE) as exp_tons,
                TRY_CAST(Exp_Freight_Rev AS DOUBLE) as exp_freight_rev,
                CAST(Haz_Bulk AS VARCHAR) as hazmat_flag,
                CAST(Error_Codes AS VARCHAR) as error_codes
            FROM read_csv_auto('{csv_path}', ignore_errors=true)
            WHERE STCC IS NOT NULL
        """)

        count = conn.execute(f"SELECT COUNT(*) FROM temp_waybill_{year}").fetchone()[0]
        logger.info(f"Loaded {count:,} records for {year}")

        # Insert into main table
        conn.execute(f"""
            INSERT INTO fact_waybill
            SELECT
                (SELECT COALESCE(MAX(waybill_id), 0) FROM fact_waybill) + ROW_NUMBER() OVER () as waybill_id,
                t.*
            FROM temp_waybill_{year} t
        """)

        conn.execute(f"DROP TABLE temp_waybill_{year}")

    # Verify final counts
    result = conn.execute("""
        SELECT
            EXTRACT(YEAR FROM waybill_date) as year,
            COUNT(*) as records,
            SUM(exp_carloads) as carloads,
            SUM(exp_tons) as tons,
            SUM(exp_freight_rev) as revenue
        FROM fact_waybill
        WHERE waybill_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).fetchall()

    print("\n" + "=" * 70)
    print("WAYBILL DATA BY YEAR")
    print("=" * 70)
    print(f"{'Year':<8} {'Records':>12} {'Carloads':>15} {'Tons':>18} {'Revenue':>18}")
    print("-" * 70)
    for row in result:
        year, records, carloads, tons, revenue = row
        if year is not None:
            print(f"{int(year):<8} {records:>12,} {carloads:>15,.0f} {tons:>18,.0f} ${revenue:>17,.0f}")
    print("=" * 70)


def main():
    """Main function to download and load historical waybill data."""
    print("=" * 70)
    print("STB WAYBILL HISTORICAL DATA LOADER")
    print("=" * 70)
    print(f"Data directory: {DATA_DIR}")
    print()

    years_to_load = [2018, 2019, 2020, 2021, 2022]
    csv_paths = []

    for year in years_to_load:
        print(f"\n--- Processing {year} ---")

        # Check if already processed
        csv_path = DATA_DIR / f"waybill_{year}_processed.csv"
        if csv_path.exists():
            logger.info(f"Already processed: {csv_path}")
            csv_paths.append(csv_path)
            continue

        try:
            # Download
            zip_path = download_waybill(year)

            # Extract
            data_path = extract_waybill(zip_path, year)

            # Parse
            df = process_waybill_file(data_path, year)

            # Save
            csv_path = save_to_csv(df, year)
            csv_paths.append(csv_path)

        except Exception as e:
            logger.error(f"Error processing {year}: {e}")
            continue

    # Load to database
    if csv_paths:
        print("\n--- Loading to Database ---")
        load_to_database(csv_paths)

    print("\nDone!")


if __name__ == "__main__":
    main()
