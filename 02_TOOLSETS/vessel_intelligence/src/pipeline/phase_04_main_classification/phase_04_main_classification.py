"""
Phase 04: Main Classification (Keyword Rules)
===============================================
Apply keyword-based classification rules from cargo_classification.csv.

Input:  phase_03_output.csv (from phase_03_carrier_classification/)
Output: phase_04_output.csv

Author: WSD3 / Claude Code
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

DICTIONARY = PROJECT_ROOT / "DICTIONARIES" / "cargo_classification.csv"
INPUT_FILE = PIPELINE_DIR / "phase_03_carrier_classification" / "phase_03_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_04_output.csv"

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def apply_main_classification():
    stamp("="*80)
    stamp("PHASE 04: MAIN CLASSIFICATION (KEYWORD RULES)")
    stamp("="*80)
    start = datetime.now()

    stamp("\n1. Loading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    stamp(f"   Total records: {len(df):,}")

    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)
    unclassified_before = df['Group'].isna().sum()
    tons_before = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
    stamp(f"   Unclassified: {unclassified_before:,} records, {tons_before:,.0f} tons")

    stamp("\n2. Loading dictionary...")
    rules = pd.read_csv(DICTIONARY, dtype=str)
    stamp(f"   Found {len(rules)} rules")

    stamp("\n3. Applying rules...")
    classified_count = 0
    classified_tons = 0
    by_cargo = {}

    for idx, rule in rules.iterrows():
        rule_id = rule['Order']
        keywords = str(rule.get('Keywords', '')).strip()

        if not keywords or keywords == '' or keywords == 'nan':
            continue

        unclassified_mask = df['Group'].isna()
        goods_upper = df['Goods Shipped'].fillna('').str.upper()

        try:
            keyword_mask = goods_upper.str.contains(keywords, case=False, na=False, regex=True)
        except:
            continue

        match_mask = unclassified_mask & keyword_mask
        match_count = match_mask.sum()

        if match_count > 0:
            match_tons = df.loc[match_mask, 'Tons_Numeric'].sum()

            df.loc[match_mask, 'Group'] = rule['Group']
            df.loc[match_mask, 'Commodity'] = rule['Commodity']
            df.loc[match_mask, 'Cargo'] = rule['Cargo']
            df.loc[match_mask, 'Cargo_Detail'] = rule['Cargo_Detail']
            df.loc[match_mask, 'Classified_By_Rule'] = f'Rule_{rule_id}'

            # Safely get cargo as string
            try:
                cargo_val = rule['Cargo']
                if pd.isna(cargo_val) or cargo_val == '' or str(cargo_val).lower() == 'nan':
                    cargo = 'Unknown'
                else:
                    cargo = str(cargo_val)
            except:
                cargo = 'Unknown'

            if cargo not in by_cargo:
                by_cargo[cargo] = {'records': 0, 'tons': 0}
            by_cargo[cargo]['records'] += match_count
            by_cargo[cargo]['tons'] += match_tons

            classified_count += match_count
            classified_tons += match_tons

            if match_tons > 1000:
                cargo_display = cargo[:40] if len(cargo) > 40 else cargo
                stamp(f"   Rule {rule_id:>3s}: {cargo_display:40s} - {match_count:>5,} records, {match_tons:>12,.0f} tons")

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
    stamp(f"\nPHASE 04 COMPLETE - Duration: {duration:.1f} minutes")

if __name__ == "__main__":
    apply_main_classification()
