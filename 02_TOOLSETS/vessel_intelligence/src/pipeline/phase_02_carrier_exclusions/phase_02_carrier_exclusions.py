"""
Phase 02: Carrier Exclusions
==============================
Mark excluded carriers (cruise lines, freight forwarders, tugs) as EXCLUDED.

Input:  phase_01_output.csv (from phase_01_white_noise/)
Output: phase_02_output.csv

Author: WSD3 / Claude Code
Date: 2026-02-08
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

EXCLUSION_LIST = PROJECT_ROOT / "DICTIONARIES" / "carrier_exclusions.csv"
INPUT_FILE = PIPELINE_DIR / "phase_01_white_noise" / "phase_01_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_02_output.csv"

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def apply_carrier_exclusions():
    """Mark excluded carriers"""

    stamp("="*80)
    stamp("PHASE 02: CARRIER EXCLUSIONS")
    stamp("="*80)
    start = datetime.now()

    # Load data
    stamp("\n1. Loading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    stamp(f"   Total records: {len(df):,}")

    # Convert tons
    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)

    # Count unclassified
    unclassified_before = df['Group'].isna().sum() if 'Group' in df.columns else len(df)
    tons_unclassified_before = df['Tons_Numeric'].sum() if unclassified_before == len(df) else df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
    stamp(f"   Unclassified: {unclassified_before:,} records, {tons_unclassified_before:,.0f} tons")

    # Load exclusion list
    stamp("\n2. Loading carrier exclusions...")
    exclusions = pd.read_csv(EXCLUSION_LIST, dtype=str)
    stamp(f"   Found {len(exclusions)} carriers to exclude")

    # Apply exclusions
    stamp("\n3. Marking excluded carriers...")

    if 'Group' not in df.columns:
        df['Group'] = None
        df['Commodity'] = None
        df['Cargo'] = None
        df['Cargo_Detail'] = None
        df['Classified_By_Rule'] = None

    unclassified_mask = df['Group'].isna()
    carrier_upper = df['Carrier'].fillna('').str.upper()

    excluded_count = 0
    excluded_tons = 0
    excluded_by_carrier = {}

    for _, row in exclusions.iterrows():
        scac = str(row['Carrier']).strip().upper()
        carrier_name = str(row.get('Carrier Name', scac))

        mask = unclassified_mask & carrier_upper.str.contains(scac, na=False, regex=False)
        match_count = mask.sum()

        if match_count > 0:
            match_tons = df.loc[mask, 'Tons_Numeric'].sum()

            df.loc[mask, 'Group'] = 'EXCLUDED'
            df.loc[mask, 'Commodity'] = 'Excluded Carrier'
            df.loc[mask, 'Cargo'] = carrier_name
            df.loc[mask, 'Cargo_Detail'] = 'Excluded Carrier'
            df.loc[mask, 'Classified_By_Rule'] = f'Excluded_{scac}'

            excluded_by_carrier[scac] = {'records': match_count, 'tons': match_tons}
            excluded_count += match_count
            excluded_tons += match_tons

            stamp(f"   {scac}: {match_count:,} records, {match_tons:,.0f} tons")

    # Results
    stamp("\n" + "="*80)
    stamp("4. RESULTS")
    stamp("="*80)

    unclassified_after = df['Group'].isna().sum()
    tons_unclassified_after = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()

    stamp(f"\nBEFORE:")
    stamp(f"  Unclassified: {unclassified_before:,} records, {tons_unclassified_before:,.0f} tons")

    stamp(f"\nEXCLUDED:")
    stamp(f"  Total:        {excluded_count:,} records, {excluded_tons:,.0f} tons")

    stamp(f"\nAFTER:")
    stamp(f"  Unclassified: {unclassified_after:,} records, {tons_unclassified_after:,.0f} tons")

    classified_total = ((df['Group'].notna()) & (df['Group'] != 'EXCLUDED')).sum()
    excluded_total = (df['Group'] == 'EXCLUDED').sum()
    classified_pct = (classified_total / len(df) * 100)
    excluded_pct = (excluded_total / len(df) * 100)

    tons_classified = df.loc[(df['Group'].notna()) & (df['Group'] != 'EXCLUDED'), 'Tons_Numeric'].sum()
    tons_excluded = df.loc[df['Group'] == 'EXCLUDED', 'Tons_Numeric'].sum()
    total_tons = df['Tons_Numeric'].sum()
    tons_classified_pct = (tons_classified / total_tons * 100) if total_tons > 0 else 0
    tons_excluded_pct = (tons_excluded / total_tons * 100) if total_tons > 0 else 0

    stamp(f"\nOVERALL:")
    stamp(f"  Classified:   {classified_total:,} records ({classified_pct:.1f}%), {tons_classified:,.0f} tons ({tons_classified_pct:.1f}%)")
    stamp(f"  Excluded:     {excluded_total:,} records ({excluded_pct:.1f}%), {tons_excluded:,.0f} tons ({tons_excluded_pct:.1f}%)")
    stamp(f"  Unclassified: {unclassified_after:,} records ({100-classified_pct-excluded_pct:.1f}%), {tons_unclassified_after:,.0f} tons ({100-tons_classified_pct-tons_excluded_pct:.1f}%)")

    # Save
    stamp("\n" + "="*80)
    stamp("5. SAVING OUTPUT")
    stamp("="*80)

    df.drop(columns=['Tons_Numeric'], inplace=True)

    df.to_csv(OUTPUT_FILE, index=False)
    stamp(f"   Saved: {OUTPUT_FILE.name}")

    duration = (datetime.now() - start).total_seconds() / 60
    stamp(f"\n" + "="*80)
    stamp(f"PHASE 02 COMPLETE - Duration: {duration:.1f} minutes")
    stamp("="*80)

if __name__ == "__main__":
    apply_carrier_exclusions()
