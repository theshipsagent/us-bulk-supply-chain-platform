"""
Phase 00: Preprocessing
========================
Transform raw Panjiva import data (135 cols) -> preprocessed (60 cols)
ALL transformations consolidated into single preprocessing step.

Input:  RAW_DATA/00_01_panjiva_imports_raw/*.csv
Output: PIPELINE/phase_00_preprocessing/phase_00_output.csv

Author: WSD3 / Claude Code
Version: 2.1.0
"""

import pandas as pd
import numpy as np
import re
import glob
import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

RAW_DATA_PATH = PROJECT_ROOT / "RAW_DATA" / "00_01_panjiva_imports_raw"
SHIP_REGISTRY = PROJECT_ROOT / "DICTIONARIES" / "ships_register.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_00_output.csv"
LOG_DIR = PROJECT_ROOT / "logs"

# Create directories if needed
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = LOG_DIR / f"phase_00_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# ============================================================================
# COLUMN DEFINITIONS
# ============================================================================

COLUMNS_TO_KEEP = [
    'Bill of Lading Number',
    'Arrival Date',
    'Consignee',
    'Consignee (Original Format)',
    'Consignee SIC Codes',
    'Shipper',
    'Shipper (Original Format)',
    'Shipper SIC Codes',
    'Notify Party',
    'Carrier',
    'Shipment Origin',
    'Shipment Destination',
    'Port of Unlading',
    'Port of Lading',
    'Port of Lading Country',
    'Place of Receipt',
    'Vessel',
    'Vessel Voyage ID',
    'Vessel IMO',
    'Is Containerized',
    'Quantity',
    'Measurement',
    'Weight (kg)',
    'Weight (t)',
    'Weight (Original Format)',
    'Value of Goods (USD)',
    'HS Code',
    'Goods Shipped',
]

COLUMN_RENAME_MAP = {
    'Shipment Origin': 'Origin (F)',
    'Shipment Destination': 'Destination (D)',
    'Port of Unlading': 'Port of Discharge (D)',
    'Port of Lading': 'Port of Loading (F)',
    'Port of Lading Country': 'Country of Origin (F)',
    'Place of Receipt': 'Place of Receipt (F)',
    'Vessel Voyage ID': 'Voyage',
    'Vessel IMO': 'IMO',
    'Weight (kg)': 'Kilos',
    'Weight (t)': 'Tons',
    'Value of Goods (USD)': 'Value',
    'HS Code': 'HS Code Desc.',
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def stamp(msg):
    logging.info(msg)

def assign_rec_id(df, file_number):
    rec_ids = [
        f"PANV_IMP_FILE{file_number:03d}_R{i:06d}"
        for i in range(len(df))
    ]
    return rec_ids

def harmonize_name(name):
    if pd.isna(name) or name == '':
        return ''
    name = str(name).strip()
    name = name.title()
    abbrev_map = {
        ' Corp.': ' Corporation',
        ' Corp': ' Corporation',
        ' Co.': ' Company',
        ' Co': ' Company',
        ' Inc.': ' Incorporated',
        ' Inc': ' Incorporated',
        ' Ltd.': ' Limited',
        ' Ltd': ' Limited',
        ' Llc': ' LLC',
    }
    for abbrev, full in abbrev_map.items():
        name = name.replace(abbrev, full)
    name = re.sub(r'[,\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def split_quantity(qty_str):
    if pd.isna(qty_str) or qty_str == '':
        return None, None
    match = re.match(r'([0-9.,]+)\s*([A-Za-z]+.*)', str(qty_str))
    if match:
        try:
            qty_num = int(match.group(1).replace(',', ''))
            qty_pckg = match.group(2).strip()
            return qty_num, qty_pckg
        except:
            return None, None
    return None, None

def extract_hs_codes(hs_desc):
    if pd.isna(hs_desc) or hs_desc == '':
        return '', '', ''
    hs_clean = str(hs_desc).replace('.', '').strip()
    match = re.match(r'(\d{2})(\d{2})(\d{2})', hs_clean)
    if match:
        hs2 = match.group(1)
        hs4 = match.group(1) + match.group(2)
        hs6 = match.group(1) + match.group(2) + match.group(3)
        return hs2, hs4, hs6
    digits = re.findall(r'\d+', hs_clean)
    if digits:
        hs_str = ''.join(digits)[:6].ljust(6, '0')
        hs2 = hs_str[:2]
        hs4 = hs_str[:4]
        hs6 = hs_str[:6]
        return hs2, hs4, hs6
    return '', '', ''

def map_vessel_type(detailed_type):
    if pd.isna(detailed_type) or detailed_type == '':
        return ''
    detailed_type = str(detailed_type).upper()
    if any(x in detailed_type for x in ['BULK CARRIER', 'BULKER', 'CAPESIZE', 'PANAMAX',
                                          'HANDYMAX', 'HANDYSIZE', 'SUPRAMAX', 'ULTRAMAX']):
        return 'Bulk Carrier'
    if any(x in detailed_type for x in ['TANKER', 'VLCC', 'SUEZMAX', 'AFRAMAX', 'MR', 'LR']):
        return 'Tanker'
    if any(x in detailed_type for x in ['LPG', 'LNG', 'GAS CARRIER']):
        return 'LPG/LNG Carrier'
    if any(x in detailed_type for x in ['CONTAINER', 'TEU', 'FEEDER']):
        return 'Container'
    if any(x in detailed_type for x in ['RO-RO', 'RORO', 'CAR CARRIER', 'PCTC']):
        return 'RoRo'
    if any(x in detailed_type for x in ['REEFER', 'REFRIGERAT']):
        return 'Reefer'
    if any(x in detailed_type for x in ['GENERAL CARGO', 'MULTI-PURPOSE']):
        return 'General Cargo'
    return ''

def load_ship_registry():
    stamp("Loading ship registry...")
    try:
        df_ships = pd.read_csv(SHIP_REGISTRY, dtype=str)
        stamp(f"Loaded {len(df_ships):,} vessels from registry")
        return df_ships
    except Exception as e:
        stamp(f"WARNING: Could not load ship registry: {e}")
        return pd.DataFrame()

# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

def load_raw_files(sample_size=None, year=None):
    stamp("\n" + "="*80)
    stamp("STEP 1: LOADING RAW DATA")
    stamp("="*80)

    pattern = str(RAW_DATA_PATH / "*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DATA_PATH}")

    stamp(f"Found {len(files)} raw files")

    dfs = []
    file_info = []
    total_loaded = 0

    for file_num, file_path in enumerate(files, start=1):
        try:
            df_file = pd.read_csv(file_path, dtype=str, low_memory=False)
            file_info.extend([(file_num, file_path)] * len(df_file))
            dfs.append(df_file)
            total_loaded += len(df_file)
            stamp(f"File {file_num:03d}: {Path(file_path).name} ({len(df_file):,} records)")
            if sample_size and total_loaded >= sample_size:
                break
        except Exception as e:
            stamp(f"ERROR loading {file_path}: {e}")
            continue

    df = pd.concat(dfs, ignore_index=True)

    if sample_size and len(df) > sample_size:
        df = df.head(sample_size)
        file_info = file_info[:sample_size]

    stamp(f"\nLoaded {len(df):,} total records from {len(dfs)} files")
    stamp(f"Columns: {len(df.columns)}")

    return df, file_info

def remove_duplicates(df):
    stamp("\n" + "="*80)
    stamp("STEP 2: REMOVING DUPLICATES")
    stamp("="*80)

    initial_count = len(df)
    bol_duplicates = df['Bill of Lading Number'].duplicated(keep='first').sum()

    if bol_duplicates == 0:
        stamp("No duplicates found")
        return df

    stamp(f"Found {bol_duplicates:,} duplicate BOL numbers")
    df = df.drop_duplicates(subset=['Bill of Lading Number'], keep='first')
    final_count = len(df)
    removed_count = initial_count - final_count

    stamp(f"Before: {initial_count:,} records")
    stamp(f"After:  {final_count:,} records")
    stamp(f"Removed: {removed_count:,} duplicates ({removed_count/initial_count*100:.1f}%)")

    return df

def assign_rec_ids(df):
    stamp("\n" + "="*80)
    stamp("STEP 3: ASSIGNING REC_ID")
    stamp("="*80)

    rec_ids = [f"PANV_IMP_R{i:07d}" for i in range(len(df))]
    df['REC_ID'] = rec_ids

    if df['REC_ID'].is_unique:
        stamp(f"REC_ID assigned: {len(df):,} unique identifiers")
    else:
        duplicates = df['REC_ID'].duplicated().sum()
        stamp(f"WARNING: {duplicates} duplicate REC_IDs found!")

    return df

def select_and_rename_columns(df):
    stamp("\n" + "="*80)
    stamp("STEP 4: SELECTING & RENAMING COLUMNS")
    stamp("="*80)

    available_cols = [col for col in COLUMNS_TO_KEEP if col in df.columns]
    missing_cols = [col for col in COLUMNS_TO_KEEP if col not in df.columns]

    if missing_cols:
        stamp(f"WARNING: {len(missing_cols)} columns not found in data:")
        for col in missing_cols[:5]:
            stamp(f"  - {col}")

    df = df[available_cols + ['REC_ID']].copy()
    stamp(f"Kept {len(df.columns)} columns (dropped {135 - len(df.columns)})")

    df = df.rename(columns=COLUMN_RENAME_MAP)
    stamp(f"Renamed {len(COLUMN_RENAME_MAP)} columns")

    return df

def process_quantity_split(df):
    stamp("\n" + "="*80)
    stamp("STEP 5: SPLITTING QUANTITY -> QTY + PCKG")
    stamp("="*80)

    # Vectorized extraction using str methods
    qty_series = df['Quantity'].fillna('')
    match = qty_series.str.extract(r'^([0-9.,]+)\s*([A-Za-z]+.*)', expand=True)
    df['Qty'] = pd.to_numeric(match[0].str.replace(',', '', regex=False), errors='coerce').astype('Int64')
    df['Pckg'] = match[1].str.strip()
    df = df.drop(columns=['Quantity'])
    valid_splits = df['Qty'].notna().sum()
    stamp(f"Split {valid_splits:,} / {len(df):,} quantities ({valid_splits/len(df)*100:.1f}%)")

    return df

def extract_hs_code_levels(df):
    stamp("\n" + "="*80)
    stamp("STEP 6: EXTRACTING HS CODES (HS2, HS4, HS6)")
    stamp("="*80)

    # Vectorized HS code extraction
    hs_clean = df['HS Code Desc.'].fillna('').str.replace('.', '', regex=False).str.strip()
    # Extract first 6+ consecutive digits
    digits = hs_clean.str.extract(r'(\d{6,})', expand=False).fillna('')
    # Also try shorter matches for partial codes
    digits2 = hs_clean.str.extract(r'(\d{2,5})', expand=False).fillna('')
    # Prefer the 6+ digit match, fallback to shorter
    digits_final = digits.where(digits != '', digits2)
    # Pad to 6 digits
    digits_padded = digits_final.str[:6].str.ljust(6, '0')
    # Only set if we had any digits
    has_digits = digits_final != ''
    df['HS2'] = ''
    df['HS4'] = ''
    df['HS6'] = ''
    df.loc[has_digits, 'HS2'] = digits_padded[has_digits].str[:2]
    df.loc[has_digits, 'HS4'] = digits_padded[has_digits].str[:4]
    df.loc[has_digits, 'HS6'] = digits_padded[has_digits].str[:6]

    hs2_count = (df['HS2'] != '').sum()
    hs4_count = (df['HS4'] != '').sum()
    hs6_count = (df['HS6'] != '').sum()

    stamp(f"Extracted HS2: {hs2_count:,} / {len(df):,} ({hs2_count/len(df)*100:.1f}%)")
    stamp(f"Extracted HS4: {hs4_count:,} / {len(df):,} ({hs4_count/len(df)*100:.1f}%)")
    stamp(f"Extracted HS6: {hs6_count:,} / {len(df):,} ({hs6_count/len(df)*100:.1f}%)")

    return df

def harmonize_names(df):
    stamp("\n" + "="*80)
    stamp("STEP 7: HARMONIZING SHIPPER/CONSIGNEE NAMES")
    stamp("="*80)

    for col in ['Shipper', 'Consignee']:
        s = df[col].fillna('').astype(str).str.strip().str.title()
        # Apply abbreviation expansions
        s = s.str.replace(' Corp.', ' Corporation', regex=False)
        s = s.str.replace(' Corp', ' Corporation', regex=False)
        s = s.str.replace(' Co.', ' Company', regex=False)
        s = s.str.replace(r' Co$', ' Company', regex=True)
        s = s.str.replace(' Inc.', ' Incorporated', regex=False)
        s = s.str.replace(r' Inc$', ' Incorporated', regex=True)
        s = s.str.replace(' Ltd.', ' Limited', regex=False)
        s = s.str.replace(r' Ltd$', ' Limited', regex=True)
        s = s.str.replace(' Llc', ' LLC', regex=False)
        s = s.str.replace(r'[,\-]', ' ', regex=True)
        s = s.str.replace(r'\s+', ' ', regex=True).str.strip()
        df[col] = s

    stamp("Harmonized Shipper and Consignee names")
    stamp("   Original values preserved in '(Original Format)' columns")

    return df

def add_port_rollups(df):
    stamp("\n" + "="*80)
    stamp("STEP 8: ADDING PORT ROLLUPS")
    stamp("="*80)

    df['Port_Consolidated'] = ''
    df['Port_Coast'] = ''
    df['Port_Region'] = ''
    df['Port_Code'] = ''

    stamp("Port rollup columns added (empty - to be populated by phase 07)")

    return df

def enrich_vessel_data(df, df_ships):
    stamp("\n" + "="*80)
    stamp("STEP 9: ENRICHING VESSEL DATA")
    stamp("="*80)

    if df_ships.empty:
        df['Type'] = ''
        df['DWT'] = ''
        df['Vessel_Type_Simple'] = ''
        stamp("No ship registry available — skipping vessel enrichment")
        return df

    # Vectorized merge approach
    # Build lookup: uppercase vessel name -> Type, DWT
    ships_lookup = df_ships[['Vessel', 'Type', 'DWT']].copy()
    ships_lookup['Vessel'] = ships_lookup['Vessel'].fillna('').str.upper().str.strip()
    ships_lookup = ships_lookup.drop_duplicates(subset=['Vessel'], keep='first')

    # Add match key to main df
    df['_vessel_key'] = df['Vessel'].fillna('').str.upper().str.strip()

    before_cols = set(df.columns)
    df = df.merge(
        ships_lookup.rename(columns={'Vessel': '_vessel_key'}),
        on='_vessel_key',
        how='left',
        suffixes=('', '_ship')
    )

    # Fill empty with ''
    df['Type'] = df['Type'].fillna('')
    df['DWT'] = df['DWT'].fillna('')

    # Vectorized vessel type simplification
    type_upper = df['Type'].str.upper()
    df['Vessel_Type_Simple'] = ''
    df.loc[type_upper.str.contains('BULK CARRIER|BULKER|CAPESIZE|PANAMAX|HANDYMAX|HANDYSIZE|SUPRAMAX|ULTRAMAX', na=False), 'Vessel_Type_Simple'] = 'Bulk Carrier'
    df.loc[type_upper.str.contains('TANKER|VLCC|SUEZMAX|AFRAMAX', na=False), 'Vessel_Type_Simple'] = 'Tanker'
    df.loc[type_upper.str.contains('LPG|LNG|GAS CARRIER', na=False), 'Vessel_Type_Simple'] = 'LPG/LNG Carrier'
    df.loc[type_upper.str.contains('CONTAINER|TEU|FEEDER', na=False), 'Vessel_Type_Simple'] = 'Container'
    df.loc[type_upper.str.contains('RO-RO|RORO|CAR CARRIER|PCTC', na=False), 'Vessel_Type_Simple'] = 'RoRo'
    df.loc[type_upper.str.contains('REEFER|REFRIGERAT', na=False), 'Vessel_Type_Simple'] = 'Reefer'
    df.loc[type_upper.str.contains('GENERAL CARGO|MULTI-PURPOSE', na=False), 'Vessel_Type_Simple'] = 'General Cargo'

    # Cleanup
    df = df.drop(columns=['_vessel_key'])
    # Drop any duplicate columns from merge
    ship_cols = [c for c in df.columns if c.endswith('_ship')]
    if ship_cols:
        df = df.drop(columns=ship_cols)

    matched_count = (df['Type'] != '').sum()
    stamp(f"Matched vessels: {matched_count:,} / {len(df):,} ({matched_count/len(df)*100:.1f}%)")

    return df

def add_metadata_columns(df):
    stamp("\n" + "="*80)
    stamp("STEP 10: ADDING METADATA COLUMNS")
    stamp("="*80)

    df['Carrier Name'] = df['Carrier'].fillna('').str.split('-').str[0].str.strip()
    df['Package_Type'] = df['Pckg']
    df['Count'] = 1

    stamp("Added Carrier Name, Package_Type, and Count columns")

    return df

def initialize_classification_columns(df):
    stamp("\n" + "="*80)
    stamp("STEP 11: INITIALIZING CLASSIFICATION COLUMNS")
    stamp("="*80)

    # Classification columns (NaN = unclassified)
    df['Group'] = pd.NA
    df['Commodity'] = pd.NA
    df['Cargo'] = pd.NA
    df['Cargo_Detail'] = pd.NA
    df['Classified_By_Rule'] = pd.NA

    # Lock flags (FALSE)
    df['Group_Locked'] = 'FALSE'
    df['Commodity_Locked'] = 'FALSE'
    df['Cargo_Locked'] = 'FALSE'
    df['Cargo_Detail_Locked'] = 'FALSE'

    # Tracking columns (empty)
    df['Classified_Phase'] = ''
    df['Last_Rule_ID'] = ''

    # Reporting columns (empty)
    df['Report_One'] = ''
    df['Report_Two'] = ''
    df['Report_Three'] = ''
    df['Report_Four'] = ''
    df['Filter'] = ''
    df['Note'] = ''

    stamp("Initialized 20 classification/lock/tracking/reporting columns")

    return df

def save_output(df):
    stamp("\n" + "="*80)
    stamp("STEP 12: SAVING OUTPUT")
    stamp("="*80)

    df.to_csv(OUTPUT_FILE, index=False)

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    stamp(f"Saved: {OUTPUT_FILE.name}")
    stamp(f"   Records: {len(df):,}")
    stamp(f"   Columns: {len(df.columns)}")
    stamp(f"   Size: {file_size_mb:.1f} MB")

    return OUTPUT_FILE

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main(sample_size=None, year=None):
    try:
        stamp("\n" + "="*80)
        stamp("PHASE 00: PREPROCESSING")
        stamp("="*80)
        stamp(f"Start time: {datetime.now()}")
        stamp(f"Sample size: {sample_size if sample_size else 'FULL'}")
        stamp(f"Year filter: {year if year else 'ALL'}")

        df, file_info = load_raw_files(sample_size=sample_size, year=year)
        df = remove_duplicates(df)
        df = assign_rec_ids(df)
        df = select_and_rename_columns(df)
        df = process_quantity_split(df)
        df = extract_hs_code_levels(df)
        df = harmonize_names(df)
        df = add_port_rollups(df)
        df_ships = load_ship_registry()
        df = enrich_vessel_data(df, df_ships)
        df = add_metadata_columns(df)
        df = initialize_classification_columns(df)
        output_path = save_output(df)

        stamp("\n" + "="*80)
        stamp("PHASE 00 COMPLETE")
        stamp("="*80)
        stamp(f"End time: {datetime.now()}")
        stamp(f"Output: {output_path}")

        return df

    except Exception as e:
        stamp("\n" + "="*80)
        stamp("PHASE 00 FAILED")
        stamp("="*80)
        stamp(f"Error: {str(e)}")
        stamp(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Phase 00: Preprocess Panjiva import data')
    parser.add_argument('--sample', type=int, help='Sample size (e.g., 5000 for 5K test)')
    parser.add_argument('--year', type=int, help='Year to process (2023, 2024, 2025)')

    args = parser.parse_args()

    main(sample_size=args.sample, year=args.year)
