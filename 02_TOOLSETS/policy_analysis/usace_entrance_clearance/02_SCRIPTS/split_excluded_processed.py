"""
Split USACE Entrance Data into Excluded and Processed Files v1.0.0

EXCLUDED:
- Records with Fee_Base = $0 (filtered vessel types)
- Records from: Alaska, Hawaii, Puerto Rico, US Virgin Islands, Guam

PROCESSED:
- All other billable records (Fee_Base > $0, mainland US)

Dynamic versioning for traceability.

Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def split_excluded_processed(input_file, output_dir):
    """Split data into excluded and processed files"""

    print("=" * 80)
    print("USACE Data Split: Excluded vs Processed v1.0.0")
    print("=" * 80)
    print()

    # Read data with fees
    print(f"Reading: {input_file.name}")
    df = pd.read_csv(input_file, dtype=str)
    print(f"  Loaded {len(df):,} rows")
    print(f"  Columns: {len(df.columns)}")
    print()

    # Define exclusion criteria
    print("Applying exclusion filters...")
    print()

    # 1. Fee_Base = 0 (filtered vessel types)
    df['Fee_Base_int'] = df['Fee_Base'].astype(int)
    filtered_vessels = df['Fee_Base_int'] == 0

    # 2. Excluded regions/territories
    # Check Port_Region, Port_Consolidated, Port_Coast, and port names
    excluded_locations = [
        'ALASKA',
        'HAWAII',
        'PUERTO RICO',
        'VIRGIN ISLANDS',
        'GUAM',
        'US ISLANDS',
        'CARIBBEAN'  # Includes Puerto Rico/Virgin Islands
    ]

    # Create exclusion mask for regions
    region_excluded = df['Port_Region'].str.upper().str.contains('|'.join(excluded_locations), na=False)
    coast_excluded = df['Port_Coast'].str.upper().str.contains('|'.join(excluded_locations), na=False)
    port_excluded = df['Port_Consolidated'].str.upper().str.contains('|'.join(excluded_locations), na=False)

    # Combined exclusion mask
    excluded_mask = filtered_vessels | region_excluded | coast_excluded | port_excluded

    # Split data
    df_excluded = df[excluded_mask].copy()
    df_processed = df[~excluded_mask].copy()

    # Clean up temp column
    df_excluded = df_excluded.drop(columns=['Fee_Base_int'])
    df_processed = df_processed.drop(columns=['Fee_Base_int'])

    print("=" * 80)
    print("SPLIT SUMMARY")
    print("=" * 80)
    print()

    print(f"Total Records:     {len(df):,}")
    print(f"  EXCLUDED:        {len(df_excluded):,} ({len(df_excluded)/len(df)*100:.1f}%)")
    print(f"  PROCESSED:       {len(df_processed):,} ({len(df_processed)/len(df)*100:.1f}%)")
    print()

    # Breakdown of excluded records
    print("EXCLUDED Breakdown:")
    print(f"  Fee_Base = $0 (filtered):  {filtered_vessels.sum():,}")
    print(f"  Alaska/US Islands:         {region_excluded.sum():,}")
    print(f"  Caribbean territories:     {(port_excluded | coast_excluded).sum():,}")
    print()

    # Excluded by region
    if len(df_excluded) > 0:
        print("Excluded Regions:")
        excl_regions = df_excluded['Port_Region'].value_counts()
        for region, count in excl_regions.items():
            if region and region.strip():
                pct = count / len(df_excluded) * 100
                print(f"  {region:30s}: {count:>6,} ({pct:>5.1f}%)")
        print()

    # Processed summary
    print("PROCESSED Summary:")
    print(f"  Billable records:          {len(df_processed):,}")

    # Revenue calculation
    if len(df_processed) > 0:
        processed_revenue = df_processed['Fee_Base'].astype(int).sum()
        print(f"  Total revenue potential:   ${processed_revenue:,}")
        print()

        # Top regions in processed
        print("Processed - Top Regions:")
        proc_regions = df_processed['Port_Region'].value_counts().head(10)
        for region, count in proc_regions.items():
            if region and region.strip():
                pct = count / len(df_processed) * 100
                print(f"  {region:30s}: {count:>6,} ({pct:>5.1f}%)")
    print()

    # Generate output filenames with version and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_version = "v3.2.0"

    # Detect direction from input filename
    if 'entrance' in input_file.name.lower() or 'inbound' in input_file.name.lower():
        direction = "inbound"
    elif 'clearance' in input_file.name.lower() or 'outbound' in input_file.name.lower():
        direction = "outbound"
    else:
        direction = "inbound"  # default

    excluded_file = output_dir / f"usace_2023_{direction}_EXCLUDED_{base_version}_{timestamp}.csv"
    processed_file = output_dir / f"usace_2023_{direction}_PROCESSED_{base_version}_{timestamp}.csv"

    # Save files
    print("Saving files...")
    print()

    print(f"[1] EXCLUDED: {excluded_file.name}")
    df_excluded.to_csv(excluded_file, index=False)
    print(f"    Saved {len(df_excluded):,} records")
    print()

    print(f"[2] PROCESSED: {processed_file.name}")
    df_processed.to_csv(processed_file, index=False)
    print(f"    Saved {len(df_processed):,} records")
    print()

    print("=" * 80)
    print()

    return df_excluded, df_processed, excluded_file, processed_file

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "00_DATA" / "00.02_PROCESSED"

    print("\n\n")
    print("#" * 80)
    print("# SPLITTING DATA - EXCLUDED vs PROCESSED")
    print("#" * 80)
    print("\n")

    # Process ENTRANCE data
    entrance_input = data_dir / "usace_2023_inbound_entrance_with_fees_v3.1.0.csv"

    if entrance_input.exists():
        print("=" * 80)
        print("PROCESSING ENTRANCE (INBOUND) DATA")
        print("=" * 80)
        print()
        df_excl_ent, df_proc_ent, excl_ent, proc_ent = split_excluded_processed(entrance_input, data_dir)
        print(f"[OK] ENTRANCE EXCLUDED: {excl_ent.name}")
        print(f"[OK] ENTRANCE PROCESSED: {proc_ent.name}")
        print()
    else:
        print(f"SKIP: Entrance file not found: {entrance_input.name}")
        print()

    # Process CLEARANCE data
    clearance_input = data_dir / "usace_2023_outbound_clearance_with_fees_v3.1.0.csv"

    if clearance_input.exists():
        print("=" * 80)
        print("PROCESSING CLEARANCE (OUTBOUND) DATA")
        print("=" * 80)
        print()
        df_excl_clr, df_proc_clr, excl_clr, proc_clr = split_excluded_processed(clearance_input, data_dir)
        print(f"[OK] CLEARANCE EXCLUDED: {excl_clr.name}")
        print(f"[OK] CLEARANCE PROCESSED: {proc_clr.name}")
        print()
    else:
        print(f"SKIP: Clearance file not found: {clearance_input.name}")
        print()

    print("=" * 80)
    print("DATA SPLIT COMPLETE")
    print("=" * 80)
    print()
    print("Dynamic versioning applied for traceability")
    print()

if __name__ == "__main__":
    main()
