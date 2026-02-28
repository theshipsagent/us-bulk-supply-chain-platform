"""
Phase 01: White Noise Filter
==============================
Mark white noise records as EXCLUDED (keywords OR <2 tons).

Input:  phase_00_output.csv (from phase_00_preprocessing/)
Output: phase_01_output.csv

Author: WSD3 / Claude Code
Date: 2026-02-08
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent

INPUT_FILE = PIPELINE_DIR / "phase_00_preprocessing" / "phase_00_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_01_output.csv"

# White noise keywords
WHITE_NOISE_KEYWORDS = [
    'SHIP SPARES', 'SHIP SPARE', 'SHIPS SPARES', 'SHIPS SPARE',
    'SHIP EQUIPMENT', 'SHIPS EQUIPMENT',
    'SHIP STORES', 'SHIPS STORES',
    'LANDED', 'FROB', 'FOREIGN CARGO REMAINING ON BOARD'
]

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def exclude_white_noise():
    """Exclude white noise records"""

    stamp("="*80)
    stamp("PHASE 01: WHITE NOISE FILTER")
    stamp("="*80)
    start = datetime.now()

    # Load data
    stamp("\n1. Loading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    stamp(f"   Total records: {len(df):,}")

    # Convert tons
    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)

    # Count unclassified
    unclassified_before = df['Group'].isna().sum()
    tons_unclassified_before = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
    stamp(f"   Unclassified: {unclassified_before:,} records, {tons_unclassified_before:,.0f} tons")

    # Find white noise
    stamp("\n2. Finding white noise records (keywords OR <2 tons)...")

    # Build regex pattern
    pattern = '|'.join([re.escape(kw) for kw in WHITE_NOISE_KEYWORDS])

    # Check keywords
    goods_upper = df['Goods Shipped'].fillna('').str.upper()
    keyword_mask = goods_upper.str.contains(pattern, case=False, na=False, regex=True)

    # Check low tonnage
    low_tonnage_mask = df['Tons_Numeric'] < 2

    # Combine (either condition)
    white_noise_mask = (df['Group'].isna()) & (keyword_mask | low_tonnage_mask)

    white_noise_count = white_noise_mask.sum()
    white_noise_tons = df.loc[white_noise_mask, 'Tons_Numeric'].sum()

    keyword_count = (keyword_mask & df['Group'].isna()).sum()
    low_tonnage_count = (low_tonnage_mask & df['Group'].isna()).sum()
    both_count = (keyword_mask & low_tonnage_mask & df['Group'].isna()).sum()

    stamp(f"   Found: {white_noise_count:,} records, {white_noise_tons:,.0f} tons")
    stamp(f"      - Keyword matches: {keyword_count:,}")
    stamp(f"      - Low tonnage (<2 tons): {low_tonnage_count:,}")
    stamp(f"      - Both: {both_count:,}")

    # Mark as excluded
    stamp("\n3. Marking as EXCLUDED...")
    df.loc[white_noise_mask, 'Group'] = 'EXCLUDED'
    df.loc[white_noise_mask, 'Commodity'] = 'White Noise'
    df.loc[white_noise_mask, 'Cargo'] = 'White Noise'
    df.loc[white_noise_mask, 'Cargo_Detail'] = 'White Noise'
    df.loc[white_noise_mask, 'Classified_By_Rule'] = 'White_Noise_Filter'

    stamp(f"   Marked {white_noise_count:,} records as EXCLUDED")

    # Results
    stamp("\n" + "="*80)
    stamp("4. RESULTS")
    stamp("="*80)

    unclassified_after = df['Group'].isna().sum()
    tons_unclassified_after = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()

    stamp(f"\nBEFORE:")
    stamp(f"  Unclassified: {unclassified_before:,} records, {tons_unclassified_before:,.0f} tons")

    stamp(f"\nEXCLUDED (white noise):")
    stamp(f"  Records:      {white_noise_count:,} records, {white_noise_tons:,.0f} tons")

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
    stamp(f"PHASE 01 COMPLETE - Duration: {duration:.1f} minutes")
    stamp("="*80)

if __name__ == "__main__":
    exclude_white_noise()
