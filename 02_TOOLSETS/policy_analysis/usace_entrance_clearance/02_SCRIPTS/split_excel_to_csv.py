"""
Split Excel file with multiple worksheets into separate CSV files

Isolated USACE Project Version
Adapted from master project: G:\My Drive\LLM\project_manifest
Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path

def split_excel_to_csv(excel_file):
    """Split Excel file into separate CSV files, one per worksheet"""

    excel_path = Path(excel_file)
    output_dir = excel_path.parent
    base_name = excel_path.stem

    print(f"Reading: {excel_path.name}")
    print()

    # Read all sheets
    excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')

    print(f"Found {len(excel_data)} worksheets:")
    print()

    # Save each sheet as CSV
    for sheet_name, df in excel_data.items():
        # Create clean filename from sheet name
        clean_sheet_name = sheet_name.replace(' ', '_').replace('/', '_')
        csv_filename = f"{base_name}_{clean_sheet_name}.csv"
        csv_path = output_dir / csv_filename

        # Save to CSV
        df.to_csv(csv_path, index=False)

        print(f"[OK] {sheet_name}")
        print(f"  -> {csv_filename}")
        print(f"  Rows: {len(df):,} | Columns: {len(df.columns)}")
        print()

    print("Done!")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    # Default path for this isolated project
    project_root = Path(__file__).parent.parent
    excel_file = project_root / "00_DATA" / "00.01_RAW" / "Entrances_Clearances_2023.xlsx"

    print("=" * 80)
    print("USACE Excel to CSV Splitter")
    print("=" * 80)
    print()

    if excel_file.exists():
        split_excel_to_csv(excel_file)
    else:
        print(f"ERROR: Excel file not found at: {excel_file}")
        print()
        print("Please ensure the file exists in 00_DATA/00.01_RAW/")
