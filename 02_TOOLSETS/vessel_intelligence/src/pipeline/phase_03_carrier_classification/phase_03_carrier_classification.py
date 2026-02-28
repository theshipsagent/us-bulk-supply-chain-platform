"""
Phase 03: Carrier Classification (RoRo/Reefer)
================================================
Classify RoRo and Reefer carriers based on carrier SCAC.

Input:  phase_02_output.csv (from phase_02_carrier_exclusions/)
Output: phase_03_output.csv

Author: WSD3 / Claude Code
Date: 2026-02-08
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

CARRIER_RULES = PROJECT_ROOT / "DICTIONARIES" / "carrier_classification_rules.csv"
INPUT_FILE = PIPELINE_DIR / "phase_02_carrier_exclusions" / "phase_02_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_03_output.csv"

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def apply_carrier_classification():
    """Apply carrier-based classification for RoRo/Reefer"""

    stamp("="*80)
    stamp("PHASE 03: CARRIER CLASSIFICATION (RoRo/Reefer)")
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

    # Load carrier rules
    stamp("\n2. Loading carrier classification rules...")
    df_carriers = pd.read_csv(CARRIER_RULES, dtype=str)
    stamp(f"   Found {len(df_carriers)} carrier rules")

    # Apply carrier classifications
    stamp("\n3. Applying carrier classifications...")

    classified_count = 0
    classified_tons = 0
    by_commodity = {}

    carrier_col = df['Carrier'].fillna('').str.upper()

    for idx, rule in df_carriers.iterrows():
        scac = str(rule['Carrier']).upper().strip()

        # Find unclassified records with this carrier
        unclassified_mask = df['Group'].isna()
        carrier_mask = carrier_col.str.contains(scac, na=False, regex=False)

        match_mask = unclassified_mask & carrier_mask
        match_count = match_mask.sum()

        if match_count > 0:
            match_tons = df.loc[match_mask, 'Tons_Numeric'].sum()

            # Apply classification
            df.loc[match_mask, 'Group'] = rule['Group']
            df.loc[match_mask, 'Commodity'] = rule['Commodity']
            df.loc[match_mask, 'Cargo'] = rule['Cargo']
            df.loc[match_mask, 'Cargo_Detail'] = rule['CargoDetail']
            df.loc[match_mask, 'Classified_By_Rule'] = 'Carrier_Classification'

            # Track
            commodity = rule['Commodity']
            if commodity not in by_commodity:
                by_commodity[commodity] = {'records': 0, 'tons': 0}
            by_commodity[commodity]['records'] += match_count
            by_commodity[commodity]['tons'] += match_tons

            classified_count += match_count
            classified_tons += match_tons

            stamp(f"   Carrier {scac}: {match_count:,} records, {match_tons:,.0f} tons - {rule['Commodity']}")

    # Results
    stamp("\n" + "="*80)
    stamp("4. RESULTS BY COMMODITY")
    stamp("="*80)

    for commodity, stats in sorted(by_commodity.items(), key=lambda x: x[1]['tons'], reverse=True):
        stamp(f"  {commodity:30s}: {stats['records']:>6,} records, {stats['tons']:>15,.0f} tons")

    stamp("\n" + "="*80)
    stamp("5. OVERALL RESULTS")
    stamp("="*80)

    unclassified_after = df['Group'].isna().sum()
    tons_unclassified_after = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()

    stamp(f"\nBEFORE:")
    stamp(f"  Unclassified: {unclassified_before:,} records, {tons_unclassified_before:,.0f} tons")

    stamp(f"\nCAPTURED (carrier-based):")
    stamp(f"  Total:        {classified_count:,} records, {classified_tons:,.0f} tons")

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
    stamp("6. SAVING OUTPUT")
    stamp("="*80)

    df.drop(columns=['Tons_Numeric'], inplace=True)

    df.to_csv(OUTPUT_FILE, index=False)
    stamp(f"   Saved: {OUTPUT_FILE.name}")

    duration = (datetime.now() - start).total_seconds() / 60
    stamp(f"\n" + "="*80)
    stamp(f"PHASE 03 COMPLETE - Duration: {duration:.1f} minutes")
    stamp("="*80)

if __name__ == "__main__":
    apply_carrier_classification()
