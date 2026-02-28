"""
Apply Fee Rules to USACE Entrance Data v1.0.0

Adds three columns based on ICST vessel type:
- Fee_Base: Base agency fee (authoritative)
- Fee_Adj: Adjusted fee (starts same as Fee_Base, adjusted in later steps)
- Fee_Class: Fee classification category

Special case: OTHER LAKERS - $0 for US/CA flags, $5750 for others

Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path

def apply_fee_rules(input_file, output_file):
    """Apply fee rules based on ICST vessel type"""

    print("=" * 80)
    print("USACE Fee Rules Application v1.0.0")
    print("=" * 80)
    print()

    # Read transformed data
    print(f"Reading: {input_file.name}")
    df = pd.read_csv(input_file, dtype=str)
    print(f"  Loaded {len(df):,} rows")
    print(f"  Columns: {len(df.columns)}")
    print()

    # Fee rules dictionary (ICST_DESC -> (fee, class))
    # Based on rulebuild.md
    fee_rules = {
        'CONTAINER': (650, 'container'),
        'CRUISE': (2000, 'cruise'),
        'CHEMICAL TANKER': (3750, 'parcel'),
        'OTHER BULK CARRIER': (9500, 'bulk'),
        'TUG/SUPPLY OFFSHORE SUPPORT': (0, 'filter'),
        'OTHER RO-RO CARGO': (750, 'ro-ro'),
        'GENERAL CARGO-MULTI DECK NEI': (4500, 'general cargo'),
        'CRUDE OIL TANKER': (4500, 'general cargo'),
        'LPG CARRIER': (3750, 'lpg'),
        'TUG': (0, 'filter'),
        'LNG CARRIER': (4500, 'lng'),
        'OTHER LAKERS': (0, 'bulk'),  # Special case - handled separately
        'CRUDE/PRODUCTS TANKER': (3750, 'tank'),
        'OTHER SPECIALIZED CARRIER NEI': (4500, 'general'),
        'OIL PRODUCTS TANKER': (4000, 'tank'),
        'OTHER TANK BARGE': (0, 'filter'),
        'REEFER': (4500, 'reefer'),
        'PUSH BOAT': (0, 'filter'),
        'RO-RO PASSENGER': (0, 'filter'),
        'OTHER DRY CARGO BARGE NEI': (0, 'filter'),
        'DECK BARGE': (0, 'filter'),
        'OTHER TANKER': (4000, 'tank'),
        'DRY CARGO BARGE': (0, 'filter'),
        'RESEARCH/SURVEY': (0, 'filter'),
        'RO-RO CONTAINER': (750, 'ro-ro'),
        'OTHER LIQUIFIED GAS CARRIER': (4500, 'lpg'),
        'OTHER TANKER NEI': (3750, 'tank'),
        'COVERED DRY CARGO BARGE': (0, 'filter'),
        'FISH CATCHING': (0, 'filter'),
        'OTHER NEI': (0, 'filter'),
        'OTHER OFFSHORE PRODUCTION & SUPPORT': (0, 'filter'),
        'FISH PROCESSING': (0, 'filter'),
        'OTHER PASSENGER': (0, 'filter'),
        'OTHER BULK/OIL CARRIER': (9500, 'bulk'),
        'OTHER GENERAL CARGO': (4500, 'general'),
        'LIVESTOCK CARRIER': (4500, 'general'),
        'DRILLING SHIP': (0, 'filter'),
        'DREDGER': (0, 'filter'),
        'VEHICLE CARRIER': (0, 'filter')
    }

    print("Applying fee rules...")
    print()

    # Initialize new columns
    df['Fee_Base'] = 0
    df['Fee_Adj'] = 0
    df['Fee_Class'] = ''

    # Apply rules
    matched = 0
    special_lakers = 0
    lakers_us_ca = 0
    lakers_foreign = 0

    for idx, row in df.iterrows():
        icst_desc = str(row.get('ICST_DESC', '')).strip().upper()

        # Special case: OTHER LAKERS
        if icst_desc == 'OTHER LAKERS':
            special_lakers += 1
            flag = str(row.get('FLAG_CTRY', '')).strip().upper()

            # Check if US or Canada flag
            if 'UNITED STATES' in flag or 'CANADA' in flag or flag == 'US' or flag == 'CA':
                df.at[idx, 'Fee_Base'] = 0
                df.at[idx, 'Fee_Adj'] = 0
                df.at[idx, 'Fee_Class'] = 'filter'
                lakers_us_ca += 1
            else:
                df.at[idx, 'Fee_Base'] = 5750
                df.at[idx, 'Fee_Adj'] = 5750
                df.at[idx, 'Fee_Class'] = 'bulk'
                lakers_foreign += 1

        # Normal cases
        elif icst_desc in fee_rules:
            fee, fee_class = fee_rules[icst_desc]
            df.at[idx, 'Fee_Base'] = fee
            df.at[idx, 'Fee_Adj'] = fee  # Starts same as Fee_Base
            df.at[idx, 'Fee_Class'] = fee_class
            matched += 1

        # Unmatched (shouldn't happen with complete rules)
        else:
            df.at[idx, 'Fee_Base'] = 0
            df.at[idx, 'Fee_Adj'] = 0
            df.at[idx, 'Fee_Class'] = 'unknown'

    print(f"  Matched {matched:,} records to standard fee rules")
    print(f"  OTHER LAKERS processed: {special_lakers:,}")
    print(f"    - US/CA flags (filter): {lakers_us_ca:,}")
    print(f"    - Foreign flags ($5750): {lakers_foreign:,}")
    print()

    # Summary statistics
    print("=" * 80)
    print("FEE ASSIGNMENT SUMMARY")
    print("=" * 80)
    print()

    print(f"Total Records: {len(df):,}")
    print()

    print("Fee Distribution:")
    fee_dist = df.groupby('Fee_Base').size().sort_values(ascending=False)
    for fee, count in fee_dist.items():
        pct = count / len(df) * 100
        print(f"  ${fee:>5}: {count:>7,} ({pct:>5.1f}%)")
    print()

    print("Fee Class Distribution:")
    class_dist = df['Fee_Class'].value_counts()
    for fee_class, count in class_dist.items():
        pct = count / len(df) * 100
        print(f"  {fee_class:20s}: {count:>7,} ({pct:>5.1f}%)")
    print()

    # Calculate revenue potential
    total_revenue = df['Fee_Base'].astype(int).sum()
    billable = len(df[df['Fee_Base'].astype(int) > 0])
    print(f"Revenue Summary:")
    print(f"  Billable records: {billable:,} ({billable/len(df)*100:.1f}%)")
    print(f"  Filtered records: {len(df) - billable:,} ({(len(df) - billable)/len(df)*100:.1f}%)")
    print(f"  Total potential revenue: ${total_revenue:,}")
    print()

    # Save output
    print(f"Saving to: {output_file.name}")
    df.to_csv(output_file, index=False)
    print("[OK] File saved successfully")
    print()

    print("=" * 80)
    print()

    return df

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "00_DATA" / "00.02_PROCESSED"

    print("\n\n")
    print("#" * 80)
    print("# APPLYING FEE RULES - USACE Data")
    print("#" * 80)
    print("\n")

    # Process ENTRANCE data
    entrance_input = data_dir / "usace_2023_inbound_entrance_transformed_v3.0.0.csv"
    entrance_output = data_dir / "usace_2023_inbound_entrance_with_fees_v3.1.0.csv"

    if entrance_input.exists():
        print("=" * 80)
        print("PROCESSING ENTRANCE (INBOUND) DATA")
        print("=" * 80)
        print()
        df_entrance = apply_fee_rules(entrance_input, entrance_output)
        print(f"[OK] ENTRANCE output: {entrance_output.name}")
        print()
    else:
        print(f"SKIP: Entrance file not found: {entrance_input.name}")
        print()

    # Process CLEARANCE data
    clearance_input = data_dir / "usace_2023_outbound_clearance_transformed_v3.0.0.csv"
    clearance_output = data_dir / "usace_2023_outbound_clearance_with_fees_v3.1.0.csv"

    if clearance_input.exists():
        print("=" * 80)
        print("PROCESSING CLEARANCE (OUTBOUND) DATA")
        print("=" * 80)
        print()
        df_clearance = apply_fee_rules(clearance_input, clearance_output)
        print(f"[OK] CLEARANCE output: {clearance_output.name}")
        print()
    else:
        print(f"SKIP: Clearance file not found: {clearance_input.name}")
        print()

    print("=" * 80)
    print("FEE RULES APPLICATION COMPLETE")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
