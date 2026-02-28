"""
Phase 00 (Exports): Preprocessing
==================================
Transform raw Panjiva export data (74 cols) -> preprocessed (60 cols)
Reads ZIP archives directly. Maps export schema to import pipeline schema
so phases 01-07 can run without modification.

Input:  RAW_DATA/00_02_panjiva_exports_raw/*.zip  (12 files, 2023)
Output: PIPELINE_EXPORTS/phase_00_preprocessing/phase_00_output.csv

Column Mapping Notes:
  Export 'Shipment Date'   -> 'Arrival Date'   (pipeline-compatible name)
  Export 'Port of Lading'  -> 'Port of Discharge (D)'  (U.S. export origin port)
  Export 'Port of Unlading'-> 'Port of Loading (F)'    (foreign destination)
  Export 'Port of Unlading Country' -> 'Country of Origin (F)' (destination country)
  Export 'Carrier' (fallback 'Vessel SCAC') -> 'Carrier'
  IMO / Voyage -> '' (not available in export manifests)
  Consignee / Notify Party -> '' (not in export manifests)

REC_ID prefix: PANV_EXP_R{n:07d}

Author: WSD3 / Claude Code
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import zipfile
import re
import logging
import sys
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR   = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

RAW_DATA_PATH = PROJECT_ROOT / "RAW_DATA" / "00_02_panjiva_exports_raw"
SHIP_REGISTRY = PROJECT_ROOT / "DICTIONARIES" / "ships_register.csv"
OUTPUT_FILE   = SCRIPT_DIR / "phase_00_output.csv"
LOG_DIR       = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file  = LOG_DIR / f"phase_00_exports_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

def stamp(msg):
    logging.info(msg)

# ============================================================================
# COLUMNS TO LOAD FROM RAW ZIP FILES
# ============================================================================

RAW_COLS_NEEDED = [
    'Bill of Lading Number',
    'Shipment Date',
    'Shipper',
    'Shipper (Original Format)',
    'Shipper SIC Codes',
    'Carrier',
    'Vessel SCAC',
    'Shipment Destination',
    'Port of Lading',
    'Port of Lading Country',
    'Port of Unlading',
    'Port of Unlading Country',
    'Place of Receipt',
    'Vessel',
    'Vessel Country',
    'Is Containerized',
    'Item Quantity',
    'Weight (kg)',
    'Weight (t)',
    'Weight (Original Format)',
    'Value of Goods (USD)',
    'HS Code',
    'Goods Shipped',
]

# ============================================================================
# LOAD RAW FILES FROM ZIP ARCHIVES
# ============================================================================

def load_raw_files(sample_size=None):
    stamp("=" * 80)
    stamp("STEP 1: LOADING RAW EXPORT DATA FROM ZIP FILES")
    stamp("=" * 80)

    zip_files = sorted(RAW_DATA_PATH.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No ZIP files found in {RAW_DATA_PATH}")

    stamp(f"Found {len(zip_files)} ZIP files")

    dfs = []
    total_loaded = 0

    for file_num, zf in enumerate(zip_files, start=1):
        try:
            with zipfile.ZipFile(zf) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as csf:
                    # Only load needed columns (speeds up I/O)
                    chunk = pd.read_csv(csf, dtype=str, low_memory=False)
                    available = [c for c in RAW_COLS_NEEDED if c in chunk.columns]
                    missing   = [c for c in RAW_COLS_NEEDED if c not in chunk.columns]
                    if missing:
                        stamp(f"  WARNING File {file_num}: {len(missing)} cols missing: {missing}")
                    chunk = chunk[available].copy()
                    dfs.append(chunk)
                    total_loaded += len(chunk)
                    stamp(f"  File {file_num:02d}: {zf.name[-30:]} -> {len(chunk):,} records")
                    if sample_size and total_loaded >= sample_size:
                        break
        except Exception as e:
            stamp(f"  ERROR loading {zf.name}: {e}")

    df = pd.concat(dfs, ignore_index=True)

    if sample_size and len(df) > sample_size:
        df = df.head(sample_size)

    stamp(f"\nTotal loaded: {len(df):,} records from {len(dfs)} files")
    stamp(f"Columns available: {len(df.columns)}")
    return df


# ============================================================================
# REMOVE DUPLICATES
# ============================================================================

def remove_duplicates(df):
    stamp("=" * 80)
    stamp("STEP 2: REMOVING DUPLICATES")
    stamp("=" * 80)

    before = len(df)
    dupes = df['Bill of Lading Number'].duplicated(keep='first').sum()

    if dupes == 0:
        stamp("No BOL duplicates found")
        return df

    df = df.drop_duplicates(subset=['Bill of Lading Number'], keep='first')
    after = len(df)
    stamp(f"Before: {before:,}  After: {after:,}  Removed: {before-after:,} ({(before-after)/before*100:.1f}%)")
    return df


# ============================================================================
# ASSIGN REC_ID
# ============================================================================

def assign_rec_ids(df):
    stamp("=" * 80)
    stamp("STEP 3: ASSIGNING REC_ID")
    stamp("=" * 80)

    df['REC_ID'] = [f"PANV_EXP_R{i:07d}" for i in range(len(df))]
    stamp(f"Assigned {len(df):,} unique REC_IDs (PANV_EXP_R0000000 ... PANV_EXP_R{len(df)-1:07d})")
    return df


# ============================================================================
# MAP COLUMNS TO IMPORT PIPELINE SCHEMA
# ============================================================================
# The pipeline (phases 01-07) is built around the import schema.
# We map exports to the same column names so all downstream phases
# run without modification.
#
#  GEOGRAPHY NOTE (exports):
#   'Port of Discharge (D)' <- Port of Lading  (U.S. loading/export port)
#   'Port of Loading (F)'   <- Port of Unlading (foreign destination port)
#   'Country of Origin (F)' <- Port of Unlading Country (destination country)
#
# ============================================================================

def map_and_rename_columns(df):
    stamp("=" * 80)
    stamp("STEP 4: MAPPING COLUMNS TO IMPORT PIPELINE SCHEMA")
    stamp("=" * 80)

    out = pd.DataFrame()

    out['Bill of Lading Number'] = df['Bill of Lading Number']
    out['Arrival Date']          = df['Shipment Date']   # renamed for pipeline compatibility
    out['Consignee']             = ''                    # not in export manifests
    out['Consignee (Original Format)'] = ''
    out['Consignee SIC Codes']   = ''
    out['Shipper']               = df['Shipper'].fillna('')
    out['Shipper (Original Format)'] = df['Shipper (Original Format)'].fillna('') \
                                       if 'Shipper (Original Format)' in df.columns else ''
    out['Shipper SIC Codes']     = df['Shipper SIC Codes'].fillna('') \
                                    if 'Shipper SIC Codes' in df.columns else ''
    out['Notify Party']          = ''  # not in export manifests

    # Carrier: prefer 'Carrier', fall back to 'Vessel SCAC'
    carrier_raw  = df['Carrier'].fillna('') if 'Carrier' in df.columns else pd.Series('', index=df.index)
    vscac_raw    = df['Vessel SCAC'].fillna('') if 'Vessel SCAC' in df.columns else pd.Series('', index=df.index)
    out['Carrier'] = carrier_raw.where(carrier_raw != '', vscac_raw)

    out['Origin (F)']           = ''  # U.S. origin — not a field in export manifests
    out['Destination (D)']      = df['Shipment Destination'].fillna('') \
                                   if 'Shipment Destination' in df.columns else ''

    # KEY MAPPING: Port of Lading (U.S.) -> Port of Discharge (D)
    # Phase 07 enrichment looks up Port_Consolidated / Port_Coast / Port_Region
    # using this field — so the U.S. loading port goes here.
    out['Port of Discharge (D)'] = df['Port of Lading'].fillna('') \
                                    if 'Port of Lading' in df.columns else ''

    # Foreign destination port -> Port of Loading (F)
    out['Port of Loading (F)']   = df['Port of Unlading'].fillna('') \
                                    if 'Port of Unlading' in df.columns else ''

    # Destination country stored in 'Country of Origin (F)' (semantically reversed for exports)
    out['Country of Origin (F)'] = df['Port of Unlading Country'].fillna('') \
                                    if 'Port of Unlading Country' in df.columns else ''

    out['Place of Receipt (F)']  = df['Place of Receipt'].fillna('') \
                                    if 'Place of Receipt' in df.columns else ''
    out['Vessel']                = df['Vessel'].fillna('') \
                                    if 'Vessel' in df.columns else ''
    out['Voyage']                = ''   # not available in export manifests
    out['IMO']                   = ''   # not available in export manifests
    out['Is Containerized']      = df['Is Containerized'].fillna('') \
                                    if 'Is Containerized' in df.columns else ''
    out['Measurement']           = ''   # not in export manifests
    out['Kilos']                 = df['Weight (kg)'].fillna('') \
                                    if 'Weight (kg)' in df.columns else ''
    out['Tons']                  = df['Weight (t)'].fillna('') \
                                    if 'Weight (t)' in df.columns else ''
    out['Weight (Original Format)'] = df['Weight (Original Format)'].fillna('') \
                                       if 'Weight (Original Format)' in df.columns else ''
    out['Value']                 = df['Value of Goods (USD)'].fillna('') \
                                    if 'Value of Goods (USD)' in df.columns else ''
    out['HS Code Desc.']         = df['HS Code'].fillna('') \
                                    if 'HS Code' in df.columns else ''
    out['Goods Shipped']         = df['Goods Shipped'].fillna('') \
                                    if 'Goods Shipped' in df.columns else ''
    out['REC_ID']                = df['REC_ID']

    # Item Quantity: export field is a raw number (no package suffix)
    # Split into Qty (numeric) + Pckg (package type = '' for exports)
    qty_raw = df['Item Quantity'].fillna('') if 'Item Quantity' in df.columns else pd.Series('', index=df.index)
    out['Qty']  = pd.to_numeric(qty_raw.str.replace(',', '', regex=False), errors='coerce').astype('Int64')
    out['Pckg'] = ''  # exports have no package type field

    stamp(f"Mapped {len(out.columns)} output columns")
    stamp("  Port of Discharge (D) <- Port of Lading  [U.S. export port]")
    stamp("  Port of Loading (F)   <- Port of Unlading [foreign destination]")
    stamp("  Country of Origin (F) <- Port of Unlading Country [destination country]")
    stamp("  Carrier               <- Carrier (fallback: Vessel SCAC)")
    stamp("  IMO / Voyage          <- '' [not available in export manifests]")
    stamp("  Consignee             <- '' [not in export manifests]")
    return out


# ============================================================================
# HARMONIZE SHIPPER NAME
# ============================================================================

def harmonize_names(df):
    stamp("=" * 80)
    stamp("STEP 5: HARMONIZING SHIPPER NAMES")
    stamp("=" * 80)

    s = df['Shipper'].fillna('').astype(str).str.strip().str.title()
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
    df['Shipper'] = s
    stamp("Harmonized Shipper names (original preserved in 'Shipper (Original Format)')")
    return df


# ============================================================================
# EXTRACT HS CODES
# ============================================================================

def extract_hs_code_levels(df):
    stamp("=" * 80)
    stamp("STEP 6: EXTRACTING HS CODES (HS2, HS4, HS6)")
    stamp("=" * 80)

    # Export HS codes are already numeric (e.g., "2303.1", "1005.90")
    hs_clean = df['HS Code Desc.'].fillna('').str.replace('.', '', regex=False).str.strip()
    digits   = hs_clean.str.extract(r'(\d{6,})', expand=False).fillna('')
    digits2  = hs_clean.str.extract(r'(\d{2,5})', expand=False).fillna('')
    digits_f = digits.where(digits != '', digits2)
    padded   = digits_f.str[:6].str.ljust(6, '0')
    has_d    = digits_f != ''

    df['HS2'] = ''
    df['HS4'] = ''
    df['HS6'] = ''
    df.loc[has_d, 'HS2'] = padded[has_d].str[:2]
    df.loc[has_d, 'HS4'] = padded[has_d].str[:4]
    df.loc[has_d, 'HS6'] = padded[has_d].str[:6]

    hs2_n = (df['HS2'] != '').sum()
    stamp(f"Extracted HS2: {hs2_n:,} / {len(df):,} ({hs2_n/len(df)*100:.1f}%)")
    return df


# ============================================================================
# ADD PORT ROLLUP PLACEHOLDERS
# ============================================================================

def add_port_rollups(df):
    stamp("=" * 80)
    stamp("STEP 7: ADDING PORT ROLLUP COLUMNS (empty — populated by phase 07)")
    stamp("=" * 80)

    df['Port_Consolidated'] = ''
    df['Port_Coast']        = ''
    df['Port_Region']       = ''
    df['Port_Code']         = ''
    stamp("Port rollup columns added (empty)")
    return df


# ============================================================================
# VESSEL ENRICHMENT
# ============================================================================

def enrich_vessel_data(df):
    stamp("=" * 80)
    stamp("STEP 8: ENRICHING VESSEL DATA FROM SHIP REGISTRY")
    stamp("=" * 80)

    try:
        df_ships = pd.read_csv(SHIP_REGISTRY, dtype=str)
        stamp(f"Loaded {len(df_ships):,} vessels from registry")
    except Exception as e:
        stamp(f"WARNING: Could not load ship registry: {e} — skipping vessel enrichment")
        df['Type'] = ''
        df['DWT']  = ''
        df['Vessel_Type_Simple'] = ''
        return df

    # Lookup by vessel name (no IMO available in exports)
    ships_lkp = df_ships[['Vessel', 'Type', 'DWT']].copy()
    ships_lkp['Vessel'] = ships_lkp['Vessel'].fillna('').str.upper().str.strip()
    ships_lkp = ships_lkp.drop_duplicates(subset=['Vessel'], keep='first')

    df['_vkey'] = df['Vessel'].fillna('').str.upper().str.strip()
    df = df.merge(
        ships_lkp.rename(columns={'Vessel': '_vkey'}),
        on='_vkey', how='left'
    )
    df['Type'] = df['Type'].fillna('')
    df['DWT']  = df['DWT'].fillna('')

    type_u = df['Type'].str.upper()
    df['Vessel_Type_Simple'] = ''
    df.loc[type_u.str.contains('BULK CARRIER|BULKER|CAPESIZE|PANAMAX|HANDYMAX|HANDYSIZE|SUPRAMAX|ULTRAMAX', na=False), 'Vessel_Type_Simple'] = 'Bulk Carrier'
    df.loc[type_u.str.contains('TANKER|VLCC|SUEZMAX|AFRAMAX', na=False), 'Vessel_Type_Simple'] = 'Tanker'
    df.loc[type_u.str.contains('LPG|LNG|GAS CARRIER', na=False), 'Vessel_Type_Simple'] = 'LPG/LNG Carrier'
    df.loc[type_u.str.contains('CONTAINER|TEU|FEEDER', na=False), 'Vessel_Type_Simple'] = 'Container'
    df.loc[type_u.str.contains('RO-RO|RORO|CAR CARRIER|PCTC', na=False), 'Vessel_Type_Simple'] = 'RoRo'
    df.loc[type_u.str.contains('REEFER|REFRIGERAT', na=False), 'Vessel_Type_Simple'] = 'Reefer'
    df.loc[type_u.str.contains('GENERAL CARGO|MULTI-PURPOSE', na=False), 'Vessel_Type_Simple'] = 'General Cargo'

    df = df.drop(columns=['_vkey'])
    ship_cols = [c for c in df.columns if c.endswith('_ship') or (c.endswith('_y') and c[:-2] in df.columns)]
    if ship_cols:
        df = df.drop(columns=ship_cols, errors='ignore')

    matched = (df['Type'] != '').sum()
    stamp(f"Vessel matches: {matched:,} / {len(df):,} ({matched/len(df)*100:.1f}%)")
    return df


# ============================================================================
# METADATA COLUMNS
# ============================================================================

def add_metadata_columns(df):
    stamp("=" * 80)
    stamp("STEP 9: ADDING METADATA COLUMNS")
    stamp("=" * 80)

    df['Carrier Name']   = df['Carrier'].fillna('').str.split('-').str[0].str.strip()
    df['Package_Type']   = df['Pckg']
    df['Count']          = 1
    stamp("Added Carrier Name, Package_Type, Count")
    return df


# ============================================================================
# INITIALIZE CLASSIFICATION COLUMNS
# ============================================================================

def initialize_classification_columns(df):
    stamp("=" * 80)
    stamp("STEP 10: INITIALIZING CLASSIFICATION COLUMNS")
    stamp("=" * 80)

    df['Group']          = pd.NA
    df['Commodity']      = pd.NA
    df['Cargo']          = pd.NA
    df['Cargo_Detail']   = pd.NA
    df['Classified_By_Rule'] = pd.NA
    df['Group_Locked']   = 'FALSE'
    df['Commodity_Locked'] = 'FALSE'
    df['Cargo_Locked']   = 'FALSE'
    df['Cargo_Detail_Locked'] = 'FALSE'
    df['Classified_Phase'] = ''
    df['Last_Rule_ID']   = ''
    df['Report_One']     = ''
    df['Report_Two']     = ''
    df['Report_Three']   = ''
    df['Report_Four']    = ''
    df['Filter']         = ''
    df['Note']           = ''
    stamp("Initialized 18 classification / lock / tracking / reporting columns")
    return df


# ============================================================================
# SAVE OUTPUT
# ============================================================================

def save_output(df):
    stamp("=" * 80)
    stamp("STEP 11: SAVING OUTPUT")
    stamp("=" * 80)

    df.to_csv(OUTPUT_FILE, index=False)
    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    stamp(f"Saved: {OUTPUT_FILE}")
    stamp(f"  Records: {len(df):,}")
    stamp(f"  Columns: {len(df.columns)}")
    stamp(f"  Size:    {size_mb:.1f} MB")

    # Quick quality summary
    stamp("")
    stamp("=== QUALITY SUMMARY ===")
    tons = pd.to_numeric(df['Tons'], errors='coerce')
    stamp(f"  Total tonnage:    {tons.sum()/1e6:.2f}M tons")
    stamp(f"  Non-null Tons:    {tons.notna().sum():,} / {len(df):,}")
    stamp(f"  Non-null HS2:     {(df['HS2'] != '').sum():,} / {len(df):,}")
    stamp(f"  Non-null Carrier: {(df['Carrier'] != '').sum():,} / {len(df):,}")
    stamp(f"  Non-null Vessel:  {(df['Vessel'] != '').sum():,} / {len(df):,}")
    stamp(f"  Vessel enriched:  {(df['Vessel_Type_Simple'] != '').sum():,} / {len(df):,}")
    stamp("")
    stamp("=== PORT OF DISCHARGE DISTRIBUTION (U.S. Export Ports) ===")
    top_ports = df['Port of Discharge (D)'].value_counts().head(10)
    for port, cnt in top_ports.items():
        stamp(f"  {port[:60]:<60} {cnt:>6,}")

    return OUTPUT_FILE


# ============================================================================
# MAIN
# ============================================================================

def main(sample_size=None):
    stamp("")
    stamp("=" * 80)
    stamp("PHASE 00 (EXPORTS): PREPROCESSING")
    stamp("=" * 80)
    stamp(f"Start: {datetime.now()}")
    stamp(f"Input: {RAW_DATA_PATH}")
    stamp(f"Output: {OUTPUT_FILE}")
    stamp(f"Sample size: {sample_size if sample_size else 'FULL'}")

    df = load_raw_files(sample_size=sample_size)
    df = remove_duplicates(df)
    df = assign_rec_ids(df)
    df = map_and_rename_columns(df)
    df = harmonize_names(df)
    df = extract_hs_code_levels(df)
    df = add_port_rollups(df)
    df = enrich_vessel_data(df)
    df = add_metadata_columns(df)
    df = initialize_classification_columns(df)
    save_output(df)

    stamp("")
    stamp("=" * 80)
    stamp("PHASE 00 (EXPORTS) COMPLETE")
    stamp(f"End: {datetime.now()}")
    stamp("=" * 80)
    stamp("")
    stamp("NEXT STEPS:")
    stamp("  Copy phase_00_output.csv -> ../phase_01_white_noise/phase_00_output.csv")
    stamp("  Run phase_01_white_noise.py  (from PIPELINE/phase_01_white_noise/)")
    stamp("    -> adjust INPUT path to PIPELINE_EXPORTS/phase_01_white_noise/phase_00_output.csv")
    stamp("  Continue phases 02-07 following the same copy-then-run pattern.")
    stamp("  NOTE: Phases 01-07 scripts require no modification — they are generic engines.")
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Phase 00 (Exports): Preprocess Panjiva export data')
    parser.add_argument('--sample', type=int, help='Sample size for testing (e.g., 5000)')
    args = parser.parse_args()
    main(sample_size=args.sample)
