"""
Enrich USACE Data with Vessel Register Information v1.0.0

Matches USACE entrance/clearance records with ships register on IMO.
Adds vessel specifications: Type, DWT, Draft, Grain capacity, TPC

Match rate expected: ~100% (IMO is universal identifier)

Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def enrich_vessel_data(usace_file, ships_register_file, output_dir):
    """Enrich USACE data with vessel specifications from ships register"""

    print("=" * 80)
    print("USACE Vessel Data Enrichment v1.0.0")
    print("=" * 80)
    print()

    # Read USACE data
    print(f"Reading USACE data: {usace_file.name}")
    df_usace = pd.read_csv(usace_file, dtype=str)
    print(f"  Loaded {len(df_usace):,} USACE records")
    print()

    # Read ships register
    print(f"Reading ships register: {ships_register_file.name}")
    df_ships = pd.read_csv(ships_register_file, dtype=str)
    print(f"  Loaded {len(df_ships):,} vessel records")
    print()

    # Prepare ships register lookup (IMO -> vessel details)
    print("Building vessel lookup index...")
    vessel_lookup = {}
    for _, row in df_ships.iterrows():
        imo = str(row.get('IMO', '')).strip()
        if imo:
            vessel_lookup[imo] = {
                'Ships_Vessel': str(row.get('Vessel', '')).strip(),
                'Ships_Type': str(row.get('Type', '')).strip(),
                'Ships_DWT': str(row.get('DWT', '')).strip(),
                'Ships_Draft': str(row.get('Dwt_Draft(m)', '')).strip(),
                'Ships_Grain': str(row.get('Grain', '')).strip(),
                'Ships_TPC': str(row.get('TPC', '')).strip(),
                'Ships_LOA': str(row.get('LOA', '')).strip(),
                'Ships_Beam': str(row.get('Beam', '')).strip(),
                'Ships_GT': str(row.get('GT', '')).strip()
            }
    print(f"  Indexed {len(vessel_lookup):,} vessels by IMO")
    print()

    # Initialize new columns
    print("Enriching USACE records with vessel data...")
    df_usace['Ships_Vessel'] = ''
    df_usace['Ships_Type'] = ''
    df_usace['Ships_DWT'] = ''
    df_usace['Ships_Draft'] = ''
    df_usace['Ships_Grain'] = ''
    df_usace['Ships_TPC'] = ''
    df_usace['Ships_LOA'] = ''
    df_usace['Ships_Beam'] = ''
    df_usace['Ships_GT'] = ''
    df_usace['Ships_Match'] = 'NO'

    # Match and enrich
    matched = 0
    unmatched = 0

    for idx, row in df_usace.iterrows():
        imo = str(row.get('IMO', '')).strip()

        if imo in vessel_lookup:
            vessel_data = vessel_lookup[imo]
            df_usace.at[idx, 'Ships_Vessel'] = vessel_data['Ships_Vessel']
            df_usace.at[idx, 'Ships_Type'] = vessel_data['Ships_Type']
            df_usace.at[idx, 'Ships_DWT'] = vessel_data['Ships_DWT']
            df_usace.at[idx, 'Ships_Draft'] = vessel_data['Ships_Draft']
            df_usace.at[idx, 'Ships_Grain'] = vessel_data['Ships_Grain']
            df_usace.at[idx, 'Ships_TPC'] = vessel_data['Ships_TPC']
            df_usace.at[idx, 'Ships_LOA'] = vessel_data['Ships_LOA']
            df_usace.at[idx, 'Ships_Beam'] = vessel_data['Ships_Beam']
            df_usace.at[idx, 'Ships_GT'] = vessel_data['Ships_GT']
            df_usace.at[idx, 'Ships_Match'] = 'YES'
            matched += 1
        else:
            unmatched += 1

    print(f"  Matched: {matched:,} ({matched/len(df_usace)*100:.1f}%)")
    print(f"  Unmatched: {unmatched:,} ({unmatched/len(df_usace)*100:.1f}%)")
    print()

    # Match statistics
    print("=" * 80)
    print("ENRICHMENT SUMMARY")
    print("=" * 80)
    print()

    print(f"Total USACE Records: {len(df_usace):,}")
    print(f"  Matched to ships register: {matched:,} ({matched/len(df_usace)*100:.1f}%)")
    print(f"  No match found: {unmatched:,} ({unmatched/len(df_usace)*100:.1f}%)")
    print()

    # Field population rates (for matched records)
    if matched > 0:
        df_matched = df_usace[df_usace['Ships_Match'] == 'YES']
        print("Enriched Field Population (matched records only):")

        fields_to_check = [
            ('Ships_Vessel', 'Vessel Name'),
            ('Ships_Type', 'Vessel Type'),
            ('Ships_DWT', 'Deadweight Tonnage'),
            ('Ships_Draft', 'Draft at DWT (m)'),
            ('Ships_Grain', 'Grain Capacity'),
            ('Ships_TPC', 'Tonnes per CM'),
            ('Ships_LOA', 'Length Overall'),
            ('Ships_Beam', 'Beam'),
            ('Ships_GT', 'Gross Tonnage')
        ]

        for field, label in fields_to_check:
            populated = df_matched[field].notna() & (df_matched[field] != '')
            pop_count = populated.sum()
            pop_pct = pop_count / len(df_matched) * 100
            print(f"  {label:25s}: {pop_count:>6,} ({pop_pct:>5.1f}%)")
        print()

    # Unmatched analysis
    if unmatched > 0:
        print("Unmatched Records Analysis:")
        df_unmatched = df_usace[df_usace['Ships_Match'] == 'NO']

        # By vessel type
        print("  Top 10 Unmatched by ICST Type:")
        unmatched_types = df_unmatched['ICST_DESC'].value_counts().head(10)
        for vessel_type, count in unmatched_types.items():
            pct = count / len(df_unmatched) * 100
            print(f"    {vessel_type:35s}: {count:>5,} ({pct:>5.1f}%)")
        print()

    # Generate output filename with version and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_version = "v3.3.0"

    # Extract direction from filename (ENTRANCE or CLEARANCE)
    if 'entrance' in usace_file.name.lower() or 'inbound' in usace_file.name.lower():
        direction = "ENTRANCE"
    elif 'clearance' in usace_file.name.lower() or 'outbound' in usace_file.name.lower():
        direction = "CLEARANCE"
    else:
        direction = "PROCESSED"

    output_file = output_dir / f"usace_2023_{direction.lower()}_enriched_{base_version}_{timestamp}.csv"

    # Save enriched file
    print(f"Saving enriched data: {output_file.name}")
    df_usace.to_csv(output_file, index=False)
    print(f"  Saved {len(df_usace):,} records")
    print()

    print("=" * 80)
    print()

    return df_usace, output_file

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent

    # Paths
    SHIPS_REGISTER = project_root / "01_DICTIONARIES" / "01_ships_register.csv"
    DATA_DIR = project_root / "00_DATA" / "00.02_PROCESSED"
    OUTPUT_DIR = DATA_DIR

    # Ensure ships register exists
    if not SHIPS_REGISTER.exists():
        print(f"ERROR: Ships register not found: {SHIPS_REGISTER}")
        print()
        return

    print("\n\n")
    print("#" * 80)
    print("# VESSEL DATA ENRICHMENT - USACE Records")
    print("#" * 80)
    print("\n")

    # Find most recent PROCESSED files (entrance and clearance)
    processed_files = sorted(DATA_DIR.glob("*_PROCESSED_*.csv"), reverse=True)

    if not processed_files:
        print("ERROR: No PROCESSED files found in:")
        print(f"  {DATA_DIR}")
        print()
        print("Please run split_excluded_processed.py first")
        return

    # Process entrance file
    entrance_files = [f for f in processed_files if 'inbound' in f.name.lower() or 'entrance' in f.name.lower()]
    if entrance_files:
        entrance_file = entrance_files[0]
        print(f"Processing ENTRANCE (inbound) data: {entrance_file.name}")
        print()
        df_entrance, entrance_output = enrich_vessel_data(entrance_file, SHIPS_REGISTER, OUTPUT_DIR)
        print(f"[OK] ENTRANCE enriched: {entrance_output}")
        print()

    # Process clearance file
    clearance_files = [f for f in processed_files if 'outbound' in f.name.lower() or 'clearance' in f.name.lower()]
    if clearance_files:
        clearance_file = clearance_files[0]
        print(f"Processing CLEARANCE (outbound) data: {clearance_file.name}")
        print()
        df_clearance, clearance_output = enrich_vessel_data(clearance_file, SHIPS_REGISTER, OUTPUT_DIR)
        print(f"[OK] CLEARANCE enriched: {clearance_output}")
        print()

    print("=" * 80)
    print("VESSEL ENRICHMENT COMPLETE")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
