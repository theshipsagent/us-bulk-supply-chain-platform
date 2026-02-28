"""
Phase 05: HS4 Statistical Alignment
=====================================
Apply HS4 statistical inference rules.

Input:  phase_04_output.csv (from phase_04_main_classification/)
Output: phase_05_output.csv

Author: WSD3 / Claude Code
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

HS4_RULES = PROJECT_ROOT / "DICTIONARIES" / "hs4_alignment.csv"
INPUT_FILE = PIPELINE_DIR / "phase_04_main_classification" / "phase_04_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_05_output.csv"

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def apply_hs4_alignment():
    stamp("="*80)
    stamp("PHASE 05: HS4 STATISTICAL ALIGNMENT")
    stamp("="*80)
    start = datetime.now()

    stamp("\n1. Loading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    stamp(f"   Total records: {len(df):,}")

    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)
    unclassified_before = df['Group'].isna().sum()
    tons_before = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
    stamp(f"   Unclassified: {unclassified_before:,} records, {tons_before:,.0f} tons")

    stamp("\n2. Loading HS4 alignment rules...")
    hs4_rules = pd.read_csv(HS4_RULES, dtype=str)
    stamp(f"   Found {len(hs4_rules)} HS4 alignment rules")

    stamp("\n3. Applying HS4 alignments...")
    classified_count = 0
    classified_tons = 0

    for idx, rule in hs4_rules.iterrows():
        note = str(rule.get('Note', '')).upper()
        hs4_match = re.search(r'HS4\s+(\d{4})', note)

        if not hs4_match:
            continue

        hs4_code = hs4_match.group(1)

        unclassified_mask = df['Group'].isna()
        hs4_mask = df['HS4'] == hs4_code

        min_tons = float(rule['Min_Tons']) if pd.notna(rule['Min_Tons']) and str(rule['Min_Tons']) != 'NONE' else 0
        tonnage_mask = df['Tons_Numeric'] >= min_tons

        match_mask = unclassified_mask & hs4_mask & tonnage_mask
        match_count = match_mask.sum()

        if match_count > 0:
            match_tons = df.loc[match_mask, 'Tons_Numeric'].sum()

            df.loc[match_mask, 'Group'] = rule['Group']
            df.loc[match_mask, 'Commodity'] = rule['Commodity']
            df.loc[match_mask, 'Cargo'] = rule['Cargo']
            df.loc[match_mask, 'Cargo_Detail'] = rule.get('Cargo_Detail', rule['Cargo'])
            df.loc[match_mask, 'Classified_By_Rule'] = f'HS4_Alignment_{hs4_code}'

            classified_count += match_count
            classified_tons += match_tons

            if match_tons > 1000:
                cargo_detail = str(rule.get('Cargo_Detail', rule['Cargo']))[:40]
                stamp(f"   HS4 {hs4_code}: {match_count:>4,} records, {match_tons:>12,.0f} tons - {cargo_detail}")

    stamp("\n" + "="*80)
    stamp("4. RESULTS")
    stamp("="*80)

    unclassified_after = df['Group'].isna().sum()
    tons_after = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()

    stamp(f"\nBEFORE: {unclassified_before:,} records, {tons_before:,.0f} tons")
    stamp(f"CAPTURED: {classified_count:,} records, {classified_tons:,.0f} tons")
    stamp(f"AFTER: {unclassified_after:,} records, {tons_after:,.0f} tons")

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
    stamp(f"  Unclassified: {unclassified_after:,} records ({100-classified_pct-excluded_pct:.1f}%), {tons_after:,.0f} tons ({100-tons_classified_pct-tons_excluded_pct:.1f}%)")

    stamp("\n5. SAVING OUTPUT...")
    df.drop(columns=['Tons_Numeric'], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)
    stamp(f"   Saved: {OUTPUT_FILE.name}")

    duration = (datetime.now() - start).total_seconds() / 60
    stamp(f"\nPHASE 05 COMPLETE - Duration: {duration:.1f} minutes")

if __name__ == "__main__":
    apply_hs4_alignment()
