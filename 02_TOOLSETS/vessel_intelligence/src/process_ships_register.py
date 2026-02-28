#!/usr/bin/env python3
"""
Ships Register Analysis and IMO Cleanup Script
Processes 52,035 ship records and creates cleaned IMO matching dictionary
"""

import pandas as pd
import re
from collections import Counter, defaultdict
from pathlib import Path

def clean_imo(imo_value):
    """
    Clean IMO number to standard 7-digit format.
    Returns tuple: (cleaned_imo, match_quality)

    Rules:
    - Valid IMO is exactly 7 digits
    - Remove non-digits
    - Pad with leading zeros if < 7 digits
    - Truncate or handle if > 7 digits
    """
    if pd.isna(imo_value):
        return None, "Invalid"

    # Convert to string
    imo_str = str(imo_value).strip()

    if not imo_str:
        return None, "Invalid"

    # Remove non-digit characters
    imo_digits = re.sub(r'\D', '', imo_str)

    if not imo_digits:
        return None, "Invalid"

    original_length = len(imo_digits)

    # Pad with leading zeros if less than 7 digits
    if original_length < 7:
        cleaned = imo_digits.zfill(7)
        return cleaned, "Padded"

    # If exactly 7 digits, it's exact
    elif original_length == 7:
        return imo_digits, "Exact"

    # If more than 7 digits, try different strategies
    else:
        # Try taking first 7 digits
        first_7 = imo_digits[:7]
        # Try taking last 7 digits
        last_7 = imo_digits[-7:]

        # Prefer first 7 if it doesn't start with zeros (more natural)
        if first_7[0] != '0':
            return first_7, "Truncated"
        else:
            return last_7, "Truncated"

def analyze_ships_register():
    """Main analysis function"""

    csv_file = r"G:\My Drive\LLM\project_mrtis\ships_register_012926_1530\01_ships_register.csv"
    output_dir = Path(r"G:\My Drive\LLM\project_mrtis")

    print("Reading ships register file...")
    df = pd.read_csv(csv_file)

    total_records = len(df)
    print(f"Total records: {total_records}")

    # Initialize tracking variables
    results = []
    imo_cleanup_stats = Counter()
    imo_duplicates = defaultdict(list)
    missing_characteristics = []
    invalid_imos = 0
    valid_exact_imos = 0

    # Process each record
    print("Processing records...")
    for idx, row in df.iterrows():
        imo_original = row['IMO']
        imo_clean, match_quality = clean_imo(imo_original)

        # Track statistics
        imo_cleanup_stats[match_quality] += 1

        if match_quality == "Invalid":
            invalid_imos += 1
            continue
        elif match_quality == "Exact":
            valid_exact_imos += 1

        # Track duplicates
        imo_duplicates[imo_clean].append({
            'vessel': row['Vessel'],
            'imo_original': imo_original,
            'row_idx': idx
        })

        # Extract characteristics
        ship_type = row['Type'] if pd.notna(row['Type']) else ""
        dwt = row['DWT'] if pd.notna(row['DWT']) else 0
        draft = row['Dwt_Draft(m)'] if pd.notna(row['Dwt_Draft(m)']) else 0
        tpc = row['TPC'] if pd.notna(row['TPC']) else 0

        # Check for missing characteristics
        if not ship_type or ship_type == "":
            missing_characteristics.append(("Type", idx))
        if dwt == 0:
            missing_characteristics.append(("DWT", idx))
        if draft == 0:
            missing_characteristics.append(("Draft", idx))
        if tpc == 0:
            missing_characteristics.append(("TPC", idx))

        # Add to results
        results.append({
            'IMO_Clean': imo_clean,
            'IMO_Original': imo_original,
            'VesselName': row['Vessel'],
            'ShipType': ship_type,
            'DWT': dwt,
            'Draft_m': draft,
            'TPC': tpc,
            'MatchQuality': match_quality
        })

    # Create results dataframe
    results_df = pd.DataFrame(results)

    # Identify duplicate IMOs (same IMO, different vessel names)
    imo_name_mismatches = []
    for imo, vessels in imo_duplicates.items():
        if len(vessels) > 1:
            vessel_names = set([v['vessel'] for v in vessels])
            if len(vessel_names) > 1:
                imo_name_mismatches.append({
                    'imo': imo,
                    'count': len(vessels),
                    'vessel_names': vessel_names
                })

    # Calculate statistics
    records_with_valid_imo = len(results_df)
    records_with_complete_chars = len(results_df[
        (results_df['ShipType'] != "") &
        (results_df['DWT'] > 0) &
        (results_df['Draft_m'] > 0) &
        (results_df['TPC'] > 0)
    ])

    records_with_missing_chars = total_records - records_with_valid_imo + len(
        results_df[
            (results_df['ShipType'] == "") |
            (results_df['DWT'] == 0) |
            (results_df['Draft_m'] == 0) |
            (results_df['TPC'] == 0)
        ]
    )

    # Top ship types
    top_ship_types = results_df[results_df['ShipType'] != ""].groupby('ShipType').size().sort_values(ascending=False).head(20)

    # Save cleaned dictionary
    dict_file = output_dir / "ships_register_dictionary.csv"
    print(f"Saving cleaned dictionary to {dict_file}...")
    results_df.to_csv(dict_file, index=False)
    print(f"Saved {len(results_df)} records")

    # Generate analysis report
    report_file = output_dir / "ships_register_analysis.txt"
    print(f"Generating analysis report...")

    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SHIPS REGISTER ANALYSIS AND IMO CLEANUP REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total records in register:                  {total_records:,}\n")
        f.write(f"Records with valid IMO (processed):        {records_with_valid_imo:,}\n")
        f.write(f"Records with invalid/missing IMO:          {invalid_imos:,}\n")
        f.write(f"Processing success rate:                   {(records_with_valid_imo/total_records)*100:.2f}%\n\n")

        f.write("IMO CLEANUP STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Exact match (already 7 digits):            {imo_cleanup_stats['Exact']:,}\n")
        f.write(f"Padded with leading zeros:                 {imo_cleanup_stats['Padded']:,}\n")
        f.write(f"Truncated/cleaned (>7 digits):             {imo_cleanup_stats['Truncated']:,}\n")
        f.write(f"Could not clean to valid IMO:              {invalid_imos:,}\n")
        f.write(f"Total processing breakdown:\n")
        for quality, count in sorted(imo_cleanup_stats.items(), key=lambda x: -x[1]):
            f.write(f"  - {quality}: {count:,}\n")
        f.write("\n")

        f.write("SHIP CHARACTERISTICS DATA QUALITY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Records with complete characteristics:     {records_with_complete_chars:,}\n")
        f.write(f"Records with missing characteristics:      {records_with_valid_imo - records_with_complete_chars:,}\n")
        f.write(f"Completeness rate:                         {(records_with_complete_chars/records_with_valid_imo)*100:.2f}%\n\n")

        f.write("MISSING CHARACTERISTICS BREAKDOWN\n")
        f.write("-" * 80 + "\n")
        missing_types = Counter([m[0] for m in missing_characteristics])
        for char_type in ['Type', 'DWT', 'Draft', 'TPC']:
            count = missing_types.get(char_type, 0)
            f.write(f"{char_type} missing:                              {count:,}\n")
        f.write("\n")

        f.write("DUPLICATE IMO ANALYSIS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Unique IMO numbers:                        {len(imo_duplicates):,}\n")
        f.write(f"IMOs with multiple vessel entries:         {len([v for v in imo_duplicates.values() if len(v) > 1]):,}\n")
        f.write(f"IMO/Name mismatch issues found:            {len(imo_name_mismatches)}\n")

        if imo_name_mismatches:
            f.write("\nTop 20 IMO/Name Mismatch Issues:\n")
            f.write("-" * 80 + "\n")
            sorted_mismatches = sorted(imo_name_mismatches, key=lambda x: -x['count'])[:20]
            for i, mismatch in enumerate(sorted_mismatches, 1):
                f.write(f"\n{i}. IMO {mismatch['imo']} - {mismatch['count']} different vessels:\n")
                for vessel_name in sorted(mismatch['vessel_names']):
                    f.write(f"   - {vessel_name}\n")
        f.write("\n")

        f.write("TOP 20 SHIP TYPES BY FREQUENCY\n")
        f.write("-" * 80 + "\n")
        for i, (ship_type, count) in enumerate(top_ship_types.items(), 1):
            percentage = (count / records_with_valid_imo) * 100
            f.write(f"{i:2d}. {ship_type:50s} {count:6,} ({percentage:5.2f}%)\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    print(f"Analysis report saved to {report_file}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total records: {total_records:,}")
    print(f"Valid records processed: {records_with_valid_imo:,}")
    print(f"Invalid IMOs: {invalid_imos:,}")
    print(f"Exact IMOs: {imo_cleanup_stats['Exact']:,}")
    print(f"Padded IMOs: {imo_cleanup_stats['Padded']:,}")
    print(f"Truncated IMOs: {imo_cleanup_stats['Truncated']:,}")
    print(f"Complete ship characteristics: {records_with_complete_chars:,}")
    print(f"IMO/Name mismatch issues: {len(imo_name_mismatches)}")
    print("=" * 80)

    return results_df, imo_name_mismatches

if __name__ == "__main__":
    results_df, mismatches = analyze_ships_register()
    print("\nProcessing complete!")
