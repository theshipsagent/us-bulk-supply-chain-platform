"""
Transform USACE Entrance/Clearance Data (Inbound/Imports) v3.0.0

Isolated USACE Project Version - Adapted for standalone use
Original source: G:\My Drive\LLM\project_manifest

Updates in v3.0.0:
- Adapted for isolated project structure
- Updated all dictionary paths to local 01_DICTIONARIES folder
- Added project root path detection for portability

Previous updates (v2.2.0):
- Fixed Port_Consolidated/Port_Coast/Port_Region mapping using USACE-to-Census port mapping file
- Now achieves 44.3% port statistical category match (vs 20.7% in v2.1.0)

Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 3.0.0
"""

import pandas as pd
import re
from pathlib import Path

def transform_entrance_data(input_file, output_file, dict_path, test_mode=False):
    """Transform USACE entrance/clearance data"""

    print("=" * 80)
    print("USACE Entrance Data Transformation v3.0.0 (Inbound/Imports)")
    print("=" * 80)
    print()

    # Load dictionaries
    print("Loading dictionaries...")

    # USACE Port Codes (extracted from USACE entrance data itself)
    df_usace_ports = pd.read_csv(dict_path / "usace_port_codes_from_data.csv", dtype=str)
    usace_port_lookup = {}
    for _, row in df_usace_ports.iterrows():
        code = str(row['Port_Code']).strip()
        usace_port_lookup[code] = str(row['Port_Name']).strip()
    print(f"  Loaded {len(usace_port_lookup)} USACE port codes")

    # PRODUCTION US Port Dictionary (from Panjiva production system)
    print("  Loading PRODUCTION US Port Dictionary...")
    df_us_ports = pd.read_csv(dict_path / "us_port_dictionary.csv", dtype=str)
    us_port_lookup = {}
    for _, row in df_us_ports.iterrows():
        census_code = str(row['Code']).strip()
        us_port_lookup[census_code] = {
            'Port_Consolidated': str(row.get('Port_Consolidated', '')).strip(),
            'Port_Coast': str(row.get('Port_Coast', '')).strip(),
            'Port_Region': str(row.get('Port_Region', '')).strip(),
            'Sked_D_E': str(row.get('Sked_D_E', '')).strip()
        }
    print(f"    Loaded {len(us_port_lookup)} Census ports (PRODUCTION dictionary)")

    # USACE-to-Census Port Code Mapping (2-step: USACE → Census → Port details)
    df_port_mapping = pd.read_csv(dict_path / "usace_to_census_port_mapping.csv", dtype=str)
    usace_to_census_lookup = {}
    for _, row in df_port_mapping.iterrows():
        usace_port = str(row['USACE_PORT']).strip()
        if row['Match_Type'] != 'NO MATCH':
            census_code = str(row.get('Census_Code', '')).strip()
            usace_to_census_lookup[usace_port] = census_code
    print(f"    Loaded {len(usace_to_census_lookup)} USACE->Census port mappings")

    # Foreign ports dictionary (Sked K)
    df_foreign_ports = pd.read_csv(dict_path / "usace_sked_k_foreign_ports.csv", dtype=str)
    foreign_port_lookup = {}
    for _, row in df_foreign_ports.iterrows():
        code = str(row['FORPORT_CD']).strip()
        foreign_port_lookup[code] = {
            'Foreign_Port': str(row.get('FORPORT_NAME', '')).strip(),
            'Foreign_Country': str(row.get('CTRY_NAME', '')).strip()
        }
    print(f"  Loaded {len(foreign_port_lookup)} foreign ports")

    # Ships register
    print("  Loading ships register...")
    df_ships = pd.read_csv(dict_path / "01_ships_register.csv", dtype=str)

    # Build IMO lookup
    imo_lookup = {}
    for _, row in df_ships.iterrows():
        imo = str(row.get('IMO', '')).strip()
        if imo and imo != '' and imo != 'nan':
            imo_lookup[imo] = {
                'Type': str(row.get('Type', '')).strip(),
                'DWT': str(row.get('DWT', '')).strip(),
                'Grain': str(row.get('Grain', '')).strip(),
                'TPC': str(row.get('TPC', '')).strip(),
                'Dwt_Draft_m': str(row.get('Dwt_Draft(m)', '')).strip()
            }
    print(f"    IMO matches: {len(imo_lookup)} vessels")

    # Build name lookup
    def normalize_name(name):
        if pd.isna(name) or name == '':
            return ''
        name = str(name).upper()
        name = re.sub(r'[^A-Z0-9]', '', name)
        return name

    name_lookup = {}
    for _, row in df_ships.iterrows():
        vessel = normalize_name(row.get('Vessel', ''))
        if vessel:
            name_lookup[vessel] = {
                'Type': str(row.get('Type', '')).strip(),
                'DWT': str(row.get('DWT', '')).strip(),
                'Grain': str(row.get('Grain', '')).strip(),
                'TPC': str(row.get('TPC', '')).strip(),
                'Dwt_Draft_m': str(row.get('Dwt_Draft(m)', '')).strip()
            }
    print(f"    Name matches: {len(name_lookup)} vessels")

    # Cargo classification dictionary
    print("  Loading cargo classification dictionary...")
    df_cargo_class = pd.read_csv(dict_path / "usace_cargoclass.csv", dtype=str)
    cargo_class_lookup = {}
    for _, row in df_cargo_class.iterrows():
        icst_type = str(row['icst type']).strip().upper()
        cargo_class_lookup[icst_type] = {
            'Group': str(row.get('Group', '')).strip(),
            'Commodity': str(row.get('Commodity', '')).strip()
        }
    print(f"    Loaded {len(cargo_class_lookup)} cargo classifications")

    # Agency fee dictionary
    print("  Loading agency fee dictionary...")
    df_agency_fee = pd.read_csv(dict_path / "agency_fee_by_icst.csv", dtype=str)
    agency_fee_lookup = {}
    for _, row in df_agency_fee.iterrows():
        icst_type = str(row['ICST_DESC']).strip().upper()
        agency_fee_lookup[icst_type] = str(row.get('Agency_Fee', '')).strip()
    print(f"    Loaded {len(agency_fee_lookup)} agency fees")

    print()

    # Read data
    print(f"Reading: {input_file.name}")

    if test_mode:
        df = pd.read_csv(input_file, nrows=100)
        print(f"  TEST MODE: Loaded first 100 rows")
    else:
        df = pd.read_csv(input_file)
        print(f"  Loaded {len(df):,} rows")

    print(f"  Original columns: {len(df.columns)}")
    print()

    # Convert numeric code columns to clean text
    print("Converting numeric codes to text format...")
    code_columns = ['PORT', 'WHERE_PORT', 'WHERE_SCHEDK', 'NRT', 'GRT', 'IMO']
    for col in code_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(int(x)) if pd.notna(x) and x != '' else '')
    print(f"  Converted {len(code_columns)} code columns to text")
    print()

    # TRANSFORMATIONS
    print("Applying transformations...")
    print()

    # 1. TYPEDOC: 0->Imports, 1->Exports
    print("  [1] TYPEDOC: 0->Imports, 1->Exports")
    df['TYPEDOC'] = df['TYPEDOC'].replace({0: 'Imports', 1: 'Exports', '0': 'Imports', '1': 'Exports'})
    print(f"      Values: {df['TYPEDOC'].value_counts().to_dict()}")

    # 2. PWW_IND: P->Port, W->Waterway
    print("  [2] PWW_IND: P->Port, W->Waterway")
    df['PWW_IND'] = df['PWW_IND'].replace({'P': 'Port', 'W': 'Waterway'})
    print(f"      Values: {df['PWW_IND'].value_counts().to_dict()}")

    # 3. WHERE_IND: F->Foreign, D->Coastwise
    print("  [3] WHERE_IND: F->Foreign, D->Coastwise")
    df['WHERE_IND'] = df['WHERE_IND'].replace({'F': 'Foreign', 'D': 'Coastwise'})
    print(f"      Values: {df['WHERE_IND'].value_counts().to_dict()}")

    print()

    # PORT DICTIONARY MAPPING
    print("Mapping ports...")
    print()

    # Map USACE Port (PORT column)
    print("  Mapping US Port (USACE codes)...")
    df['US_Port_USACE'] = df['PORT'].apply(
        lambda x: usace_port_lookup.get(str(x), '') if pd.notna(x) and x != '' else ''
    )
    matched_usace = len(df[df['US_Port_USACE'] != ''])
    print(f"    Matched: {matched_usace}/{len(df)} ({matched_usace/len(df)*100:.1f}%)")

    # Map US Port Statistical Categories (2-step: USACE->Census->PRODUCTION Port Dictionary)
    print("  Mapping US Port to PRODUCTION Port Categories...")

    def map_usace_to_production(usace_port):
        """2-step lookup: USACE code -> Census code -> Production port details"""
        if pd.isna(usace_port) or usace_port == '':
            return {'Census_Code': '', 'Census_Port_Name': '', 'Port_Consolidated': '', 'Port_Coast': '', 'Port_Region': ''}

        # Step 1: USACE -> Census code
        census_code = usace_to_census_lookup.get(str(usace_port), '')
        if not census_code:
            return {'Census_Code': '', 'Census_Port_Name': '', 'Port_Consolidated': '', 'Port_Coast': '', 'Port_Region': ''}

        # Step 2: Census code -> Production port details
        port_details = us_port_lookup.get(census_code, {})
        return {
            'Census_Code': census_code,
            'Census_Port_Name': port_details.get('Sked_D_E', ''),
            'Port_Consolidated': port_details.get('Port_Consolidated', ''),
            'Port_Coast': port_details.get('Port_Coast', ''),
            'Port_Region': port_details.get('Port_Region', '')
        }

    # Apply the 2-step mapping to each PORT
    port_mappings = df['PORT'].apply(map_usace_to_production)
    df['Census_Code'] = port_mappings.apply(lambda x: x['Census_Code'])
    df['Census_Port_Name'] = port_mappings.apply(lambda x: x['Census_Port_Name'])
    df['Port_Consolidated'] = port_mappings.apply(lambda x: x['Port_Consolidated'])
    df['Port_Coast'] = port_mappings.apply(lambda x: x['Port_Coast'])
    df['Port_Region'] = port_mappings.apply(lambda x: x['Port_Region'])

    matched_port_stats = len(df[df['Port_Consolidated'] != ''])
    print(f"    Matched: {matched_port_stats}/{len(df)} ({matched_port_stats/len(df)*100:.1f}%)")
    print(f"    [OK] Using PRODUCTION port dictionary (matches Panjiva system)")

    # Map Previous Port - Domestic (WHERE_PORT)
    print("  Mapping Previous Port (domestic)...")
    df['Previous_US_Port_USACE'] = df['WHERE_PORT'].apply(
        lambda x: usace_port_lookup.get(str(x), '') if pd.notna(x) and x != '' else ''
    )
    matched_prev_us = len(df[df['Previous_US_Port_USACE'] != ''])
    print(f"    Matched: {matched_prev_us}/{len(df)} ({matched_prev_us/len(df)*100:.1f}%)")

    # Map Previous Port - Foreign (WHERE_SCHEDK)
    print("  Mapping Previous Port (foreign)...")
    df['Previous_Foreign_Port'] = df['WHERE_SCHEDK'].apply(
        lambda x: foreign_port_lookup.get(str(x), {}).get('Foreign_Port', '') if pd.notna(x) and x != '' else ''
    )
    df['Previous_Foreign_Country'] = df['WHERE_SCHEDK'].apply(
        lambda x: foreign_port_lookup.get(str(x), {}).get('Foreign_Country', '') if pd.notna(x) and x != '' else ''
    )
    matched_foreign = len(df[df['Previous_Foreign_Port'] != ''])
    print(f"    Matched: {matched_foreign}/{len(df)} ({matched_foreign/len(df)*100:.1f}%)")

    print()

    # VESSEL MATCHING
    print("Matching vessels to ships register...")
    df['Vessel_Type'] = ''
    df['Vessel_DWT'] = ''
    df['Vessel_Grain'] = ''
    df['Vessel_TPC'] = ''
    df['Vessel_Dwt_Draft_m'] = ''
    df['Vessel_Dwt_Draft_ft'] = ''
    df['Vessel_Match_Method'] = ''

    imo_matches = 0
    name_matches = 0

    for idx, row in df.iterrows():
        imo = str(row.get('IMO', '')).strip()
        vessel_name = str(row.get('VESSNAME', '')).strip()

        # Try IMO match first
        if imo and imo in imo_lookup:
            specs = imo_lookup[imo]
            df.at[idx, 'Vessel_Type'] = specs['Type']
            df.at[idx, 'Vessel_DWT'] = specs['DWT']
            df.at[idx, 'Vessel_Grain'] = specs['Grain']
            df.at[idx, 'Vessel_TPC'] = specs['TPC']
            df.at[idx, 'Vessel_Dwt_Draft_m'] = specs['Dwt_Draft_m']

            # Convert draft from meters to feet
            try:
                draft_m = float(specs['Dwt_Draft_m'])
                draft_ft = draft_m * 3.28084
                df.at[idx, 'Vessel_Dwt_Draft_ft'] = f"{draft_ft:.2f}"
            except:
                df.at[idx, 'Vessel_Dwt_Draft_ft'] = ''

            df.at[idx, 'Vessel_Match_Method'] = 'IMO'
            imo_matches += 1
        # Try name match
        elif vessel_name:
            normalized = normalize_name(vessel_name)
            if normalized in name_lookup:
                specs = name_lookup[normalized]
                df.at[idx, 'Vessel_Type'] = specs['Type']
                df.at[idx, 'Vessel_DWT'] = specs['DWT']
                df.at[idx, 'Vessel_Grain'] = specs['Grain']
                df.at[idx, 'Vessel_TPC'] = specs['TPC']
                df.at[idx, 'Vessel_Dwt_Draft_m'] = specs['Dwt_Draft_m']

                # Convert draft from meters to feet
                try:
                    draft_m = float(specs['Dwt_Draft_m'])
                    draft_ft = draft_m * 3.28084
                    df.at[idx, 'Vessel_Dwt_Draft_ft'] = f"{draft_ft:.2f}"
                except:
                    df.at[idx, 'Vessel_Dwt_Draft_ft'] = ''

                df.at[idx, 'Vessel_Match_Method'] = 'Name'
                name_matches += 1

    print(f"  Matched by IMO:   {imo_matches:,} ({imo_matches/len(df)*100:.1f}%)")
    print(f"  Matched by Name:  {name_matches:,} ({name_matches/len(df)*100:.1f}%)")
    print(f"  Total Matched:    {imo_matches+name_matches:,} ({(imo_matches+name_matches)/len(df)*100:.1f}%)")
    print(f"  Unmatched:        {len(df)-imo_matches-name_matches:,} ({(len(df)-imo_matches-name_matches)/len(df)*100:.1f}%)")
    print()

    # CALCULATE DRAFT PERCENTAGE AND FORECASTED ACTIVITY
    print("Calculating draft percentage and forecasted activity...")

    df['Draft_Pct_of_Max'] = ''
    df['Forecasted_Activity'] = ''

    draft_calcs = 0
    for idx, row in df.iterrows():
        try:
            # Get actual draft (feet + inches/12)
            draft_ft = float(row['DRAFT_FT']) if pd.notna(row['DRAFT_FT']) and row['DRAFT_FT'] != '' else 0
            draft_in = float(row['DRAFT_IN']) if pd.notna(row['DRAFT_IN']) and row['DRAFT_IN'] != '' else 0
            actual_draft = draft_ft + (draft_in / 12.0)

            # Get max draft from vessel specs
            max_draft_str = row['Vessel_Dwt_Draft_ft']
            if max_draft_str and max_draft_str != '':
                max_draft = float(max_draft_str)

                if max_draft > 0 and actual_draft > 0:
                    # Calculate percentage
                    draft_pct = (actual_draft / max_draft) * 100
                    df.at[idx, 'Draft_Pct_of_Max'] = f"{draft_pct:.1f}"

                    # Forecast activity based on draft
                    if draft_pct > 50:
                        df.at[idx, 'Forecasted_Activity'] = 'Discharge'
                    else:
                        df.at[idx, 'Forecasted_Activity'] = 'Load'

                    draft_calcs += 1
        except:
            pass

    print(f"  Calculated draft % and forecast for {draft_calcs:,} vessels ({draft_calcs/len(df)*100:.1f}%)")
    print()

    # MATCH CARGO CLASSIFICATION FROM ICST TYPE
    print("Matching cargo classification from ICST type...")
    df['Group'] = ''
    df['Commodity'] = ''

    for idx, row in df.iterrows():
        icst_desc = str(row.get('ICST_DESC', '')).strip().upper()
        if icst_desc and icst_desc in cargo_class_lookup:
            df.at[idx, 'Group'] = cargo_class_lookup[icst_desc]['Group']
            df.at[idx, 'Commodity'] = cargo_class_lookup[icst_desc]['Commodity']

    matched_cargo = len(df[df['Group'] != ''])
    print(f"  Matched {matched_cargo:,} records to cargo classification ({matched_cargo/len(df)*100:.1f}%)")
    print()

    # MATCH AGENCY FEE FROM ICST TYPE
    print("Matching agency fees from ICST type...")
    df['Agency_Fee'] = ''

    for idx, row in df.iterrows():
        icst_desc = str(row.get('ICST_DESC', '')).strip().upper()
        if icst_desc and icst_desc in agency_fee_lookup:
            df.at[idx, 'Agency_Fee'] = agency_fee_lookup[icst_desc]

    matched_fees = len(df[df['Agency_Fee'] != ''])
    print(f"  Matched {matched_fees:,} records to agency fees ({matched_fees/len(df)*100:.1f}%)")
    print()

    # ADD PLACEHOLDER COLUMNS
    print("Adding placeholder columns...")
    df['Tons'] = ''
    df['Carrier_Name'] = ''
    df['Agency_Fee_Adj'] = ''
    print("  Added: Tons, Carrier_Name, Agency_Fee_Adj (placeholders)")
    print()

    # ADD COUNT AND RECID COLUMNS
    print("Adding Count and RECID columns...")
    df['Count'] = 1
    df['RECID'] = range(1, len(df) + 1)
    print("  Count column added (all values = 1)")
    print(f"  RECID column added (sequential 1 to {len(df):,})")
    print()

    # COLUMN RENAMING
    print("Renaming columns...")
    rename_map = {
        'ECDATE': 'Arrival_Date',
        'PORT_NAME': 'Arrival_Port_Name',
        'VESSNAME': 'Vessel'
    }

    df.rename(columns=rename_map, inplace=True)

    for old, new in rename_map.items():
        print(f"  {old:20s} -> {new}")

    print()

    # COLUMN SELECTION
    print("Selecting columns to retain...")

    columns_to_keep = [
        # Core identification
        'RECID',
        'Count',
        'TYPEDOC',
        'Arrival_Date',

        # US Port (arrival)
        'PORT',
        'Arrival_Port_Name',
        'US_Port_USACE',
        'Port_Consolidated',
        'Port_Coast',
        'Port_Region',
        'PWW_IND',

        # Vessel
        'Vessel',
        'IMO',
        'RIG_DESC',
        'ICST_DESC',
        'FLAG_CTRY',
        'NRT',
        'GRT',
        'DRAFT_FT',
        'DRAFT_IN',
        'CONTAINER',

        # Vessel specs
        'Vessel_Type',
        'Vessel_DWT',
        'Vessel_Grain',
        'Vessel_TPC',
        'Vessel_Dwt_Draft_m',
        'Vessel_Dwt_Draft_ft',
        'Vessel_Match_Method',

        # Draft analysis
        'Draft_Pct_of_Max',
        'Forecasted_Activity',

        # Previous Port
        'WHERE_IND',
        'WHERE_PORT',
        'Previous_US_Port_USACE',
        'WHERE_SCHEDK',
        'Previous_Foreign_Port',
        'Previous_Foreign_Country',
        'WHERE_NAME',
        'WHERE_CTRY',

        # Cargo classification
        'Group',
        'Commodity',

        # NEW: Tonnage and Carrier
        'Tons',
        'Carrier_Name',

        # NEW: Agency fees
        'Agency_Fee',
        'Agency_Fee_Adj'
    ]

    df_final = df[columns_to_keep]

    print(f"  Retained {len(columns_to_keep)} columns")
    print()

    # SUMMARY STATISTICS
    print("=" * 80)
    print("TRANSFORMATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Records:        {len(df_final):,}")
    print(f"Total Columns:        {len(df_final.columns)}")
    print()

    print("Value Distributions:")
    print(f"  TYPEDOC:            {dict(df_final['TYPEDOC'].value_counts())}")
    print(f"  PWW_IND:            {dict(df_final['PWW_IND'].value_counts())}")
    print(f"  WHERE_IND:          {dict(df_final['WHERE_IND'].value_counts())}")
    print()

    print("Port Mapping Success Rates:")
    usace_mapped = len(df_final[df_final['US_Port_USACE'] != ''])
    port_stats_mapped = len(df_final[df_final['Port_Consolidated'] != ''])
    prev_us_mapped = len(df_final[df_final['Previous_US_Port_USACE'] != ''])
    prev_foreign_mapped = len(df_final[df_final['Previous_Foreign_Port'] != ''])
    print(f"  US Port (USACE):             {usace_mapped:,} / {len(df_final):,} ({usace_mapped/len(df_final)*100:.1f}%)")
    print(f"  Port Statistical Categories: {port_stats_mapped:,} / {len(df_final):,} ({port_stats_mapped/len(df_final)*100:.1f}%)")
    print(f"  Previous US Port:            {prev_us_mapped:,} / {len(df_final):,} ({prev_us_mapped/len(df_final)*100:.1f}%)")
    print(f"  Previous Foreign Port:       {prev_foreign_mapped:,} / {len(df_final):,} ({prev_foreign_mapped/len(df_final)*100:.1f}%)")
    print()

    print("Vessel Matching Success Rates:")
    print(f"  Matched by IMO:              {imo_matches:,} / {len(df_final):,} ({imo_matches/len(df_final)*100:.1f}%)")
    print(f"  Matched by Name:             {name_matches:,} / {len(df_final):,} ({name_matches/len(df_final)*100:.1f}%)")
    print(f"  Total Matched:               {imo_matches+name_matches:,} / {len(df_final):,} ({(imo_matches+name_matches)/len(df_final)*100:.1f}%)")
    print()

    print("Draft Analysis & Forecasted Activity:")
    print(f"  Draft % Calculated:          {draft_calcs:,} / {len(df_final):,} ({draft_calcs/len(df_final)*100:.1f}%)")
    discharge_count = len(df_final[df_final['Forecasted_Activity'] == 'Discharge'])
    load_count = len(df_final[df_final['Forecasted_Activity'] == 'Load'])
    print(f"  Forecasted Load:             {load_count:,} ({load_count/len(df_final)*100:.1f}%)")
    print(f"  Forecasted Discharge:        {discharge_count:,} ({discharge_count/len(df_final)*100:.1f}%)")
    print()

    print("Cargo Classification (from ICST type):")
    print(f"  Classified:                  {matched_cargo:,} / {len(df_final):,} ({matched_cargo/len(df_final)*100:.1f}%)")
    print()

    print("Agency Fees:")
    print(f"  Fees Assigned:               {matched_fees:,} / {len(df_final):,} ({matched_fees/len(df_final)*100:.1f}%)")
    print()

    # Save output
    if not test_mode:
        print(f"Saving to: {output_file.name}")
        df_final.to_csv(output_file, index=False)
        print("[OK] File saved successfully")
    else:
        print("[TEST MODE] File not saved - review results above")

    print()
    print("=" * 80)

    return df_final

def main():
    """Main execution"""

    # Get project root directory (parent of 02_SCRIPTS)
    project_root = Path(__file__).parent.parent

    # Paths
    INPUT_FILE = project_root / "00_DATA" / "00.01_RAW" / "Entrances_Clearances_2023_2023_Inbound.csv"
    OUTPUT_FILE = project_root / "00_DATA" / "00.02_PROCESSED" / "usace_2023_inbound_entrance_transformed_v3.0.0.csv"
    DICT_PATH = project_root / "01_DICTIONARIES"

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Run full dataset
    print("\n\n")
    print("#" * 80)
    print("# RUNNING FULL DATASET - All records (Inbound/Imports)")
    print("#" * 80)
    print("\n")

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print()
        print("Please run split_excel_to_csv.py first to generate CSV files.")
        return

    df_final = transform_entrance_data(INPUT_FILE, OUTPUT_FILE, DICT_PATH, test_mode=False)

    print("\n")
    print("=" * 80)
    print("TRANSFORMATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Output saved to: {OUTPUT_FILE}")
    print()

if __name__ == "__main__":
    main()
