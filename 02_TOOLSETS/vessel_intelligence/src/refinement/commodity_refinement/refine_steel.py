"""
Steel Product Refinement Classification
========================================
Version: 1.0.0
Date: 2026-02-09

Refines steel classifications into specific product forms:

FLAT ROLLED PRODUCTS:
- Hot Rolled Coil (HRC)
- Cold Rolled Coil (CRC)
- Galvanized (HDGI, GI)
- Electro-Galvanized (EG)
- Stainless Steel
- Tin Plate / Tinmill
- Plate (Heavy/Medium)
- Silicon Steel (Electrical)

TUBULAR PRODUCTS:
- Seamless Pipe
- ERW Pipe (Electric Resistance Welded)
- OCTG (Oil Country Tubular Goods)
- Line Pipe
- Structural Tube
- Stainless Tube

LONG PRODUCTS:
- Rebar (Reinforcing Bar)
- Wire Rod
- Merchant Bar
- Structural Sections (Beams, Channels, Angles)
- Rails

SEMI-FINISHED:
- Slabs
- Billets
- Blooms
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(r"G:\My Drive\LLM\project_manifest")
INPUT_FILE = BASE_DIR / "00_DATA" / "00.03_MATCHED" / "panjiva_ALL_YEARS_with_scm_agg_20260209_170326.csv"
OUTPUT_DIR = BASE_DIR / "00_DATA" / "00.03_MATCHED"

# ============================================================
# STEEL REFINEMENT RULES - Ordered by specificity (most specific first)
# ============================================================

FLAT_ROLLED_RULES = [
    # Stainless Steel (most specific first)
    {
        'cargo_detail': 'Stainless Steel Coil',
        'keywords': ['STAINLESS', 'SS304', 'SS316', 'INOX', 'AISI 304', 'AISI 316'],
        'require_any': ['COIL', 'CRC', 'HRC', 'COLD ROLL', 'HOT ROLL'],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    {
        'cargo_detail': 'Stainless Steel Sheet',
        'keywords': ['STAINLESS', 'SS304', 'SS316', 'INOX'],
        'require_any': ['SHEET', 'PLATE'],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    # Galvanized Products
    {
        'cargo_detail': 'Hot-Dip Galvanized (HDGI)',
        'keywords': ['HOT DIP GALV', 'HOT-DIP GALV', 'HDGI', 'HDG COIL', 'HGI'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    {
        'cargo_detail': 'Electro-Galvanized (EG)',
        'keywords': ['ELECTRO GALV', 'ELECTRO-GALV', 'EG COIL', 'EGI'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    {
        'cargo_detail': 'Galvanized Coil',
        'keywords': ['GALVANIZED', 'GALVANISED', 'GI COIL', 'ZINC COATED'],
        'require_any': ['COIL'],
        'exclude': ['PIPE', 'TUBE', 'WIRE'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    {
        'cargo_detail': 'Galvanized Sheet',
        'keywords': ['GALVANIZED', 'GALVANISED', 'GI SHEET'],
        'require_any': ['SHEET'],
        'exclude': ['PIPE', 'TUBE'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    # Tin Plate / Tinmill
    {
        'cargo_detail': 'Tin Plate',
        'keywords': ['TIN PLATE', 'TINPLATE', 'TIN MILL', 'TINMILL', 'TFS', 'ECCS'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    # Silicon Steel / Electrical Steel
    {
        'cargo_detail': 'Silicon Steel (Electrical)',
        'keywords': ['SILICON STEEL', 'ELECTRICAL STEEL', 'CRGO', 'CRNO',
                     'GRAIN ORIENTED', 'NON-GRAIN ORIENTED', 'TRANSFORMER STEEL'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    # Cold Rolled Products
    {
        'cargo_detail': 'Cold Rolled Coil (CRC)',
        'keywords': ['COLD ROLLED', 'COLD-ROLLED', 'CRC', 'CR COIL', 'CRCA',
                     'COLD ROLL COIL', 'FULL HARD'],
        'require_any': ['COIL', 'STEEL'],
        'exclude': ['STAINLESS', 'GALV', 'TIN'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    {
        'cargo_detail': 'Cold Rolled Sheet (CRS)',
        'keywords': ['COLD ROLLED', 'COLD-ROLLED', 'CRS'],
        'require_any': ['SHEET'],
        'exclude': ['STAINLESS', 'GALV'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    # Hot Rolled Products
    {
        'cargo_detail': 'Hot Rolled Coil (HRC)',
        'keywords': ['HOT ROLLED', 'HOT-ROLLED', 'HRC', 'HR COIL', 'HRCA',
                     'HOT ROLL COIL', 'PICKLED', 'P&O'],
        'require_any': ['COIL', 'STEEL'],
        'exclude': ['STAINLESS', 'GALV', 'COLD'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    {
        'cargo_detail': 'Hot Rolled Sheet (HRS)',
        'keywords': ['HOT ROLLED', 'HOT-ROLLED', 'HRS'],
        'require_any': ['SHEET'],
        'exclude': ['STAINLESS', 'GALV', 'COLD'],
        'product_form': 'Flat Rolled',
        'tier': 2,
    },
    # Plate Products
    {
        'cargo_detail': 'Heavy Plate',
        'keywords': ['HEAVY PLATE', 'SHIP PLATE', 'BOILER PLATE', 'PRESSURE VESSEL',
                     'STRUCTURAL PLATE', 'CLAD PLATE'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Flat Rolled',
        'tier': 1,
    },
    {
        'cargo_detail': 'Steel Plate',
        'keywords': ['STEEL PLATE', 'CARBON PLATE', 'ALLOY PLATE', 'PLATE'],
        'require_any': [],
        'exclude': ['TIN PLATE', 'FLOOR PLATE', 'LICENSE PLATE', 'NAME PLATE'],
        'product_form': 'Flat Rolled',
        'tier': 3,
    },
    # Generic Coil (fallback)
    {
        'cargo_detail': 'Steel Coil - NOS',
        'keywords': ['STEEL COIL', 'COIL'],
        'require_any': ['STEEL'],
        'exclude': ['STAINLESS', 'GALV', 'COLD ROLL', 'HOT ROLL', 'WIRE', 'SPRING'],
        'product_form': 'Flat Rolled',
        'tier': 4,
    },
]

TUBULAR_RULES = [
    # OCTG (Oil Country Tubular Goods)
    {
        'cargo_detail': 'OCTG - Casing',
        'keywords': ['CASING', 'OCTG CASING', 'OIL CASING'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    {
        'cargo_detail': 'OCTG - Tubing',
        'keywords': ['OCTG TUBING', 'OIL TUBING', 'PRODUCTION TUBING'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    {
        'cargo_detail': 'OCTG - Drill Pipe',
        'keywords': ['DRILL PIPE', 'DRILL COLLAR', 'DRILLING PIPE'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # Seamless Pipe
    {
        'cargo_detail': 'Seamless Pipe',
        'keywords': ['SEAMLESS PIPE', 'SEAMLESS TUBE', 'SMLS PIPE', 'SMLS TUBE'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # ERW Pipe
    {
        'cargo_detail': 'ERW Pipe',
        'keywords': ['ERW PIPE', 'ERW TUBE', 'ELECTRIC RESISTANCE WELD',
                     'WELDED PIPE', 'WELDED TUBE'],
        'require_any': [],
        'exclude': ['SEAMLESS', 'SAW', 'SPIRAL'],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # Line Pipe
    {
        'cargo_detail': 'Line Pipe',
        'keywords': ['LINE PIPE', 'API 5L', 'PIPELINE', 'GAS PIPE', 'OIL PIPE'],
        'require_any': [],
        'exclude': ['FITTING'],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # SAW/LSAW/SSAW Pipe
    {
        'cargo_detail': 'SAW Pipe (Submerged Arc Welded)',
        'keywords': ['SAW PIPE', 'LSAW', 'SSAW', 'SPIRAL PIPE', 'SPIRAL WELD',
                     'SUBMERGED ARC'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # Structural Tube
    {
        'cargo_detail': 'Structural Tube (HSS)',
        'keywords': ['HSS', 'HOLLOW SECTION', 'STRUCTURAL TUBE', 'SQUARE TUBE',
                     'RECTANGULAR TUBE', 'RHS', 'SHS'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # Stainless Tube
    {
        'cargo_detail': 'Stainless Steel Pipe/Tube',
        'keywords': ['STAINLESS'],
        'require_any': ['PIPE', 'TUBE'],
        'exclude': [],
        'product_form': 'Tubular',
        'tier': 1,
    },
    # Generic Pipe/Tube
    {
        'cargo_detail': 'Steel Pipe - NOS',
        'keywords': ['STEEL PIPE', 'CARBON PIPE', 'BLACK PIPE'],
        'require_any': [],
        'exclude': ['SEAMLESS', 'ERW', 'SAW', 'LINE', 'STAINLESS', 'FITTING'],
        'product_form': 'Tubular',
        'tier': 3,
    },
    {
        'cargo_detail': 'Steel Tube - NOS',
        'keywords': ['STEEL TUBE', 'CARBON TUBE'],
        'require_any': [],
        'exclude': ['SEAMLESS', 'ERW', 'STRUCTURAL', 'STAINLESS'],
        'product_form': 'Tubular',
        'tier': 3,
    },
]

LONG_PRODUCT_RULES = [
    # Rebar
    {
        'cargo_detail': 'Rebar (Reinforcing Bar)',
        'keywords': ['REBAR', 'REINFORCING BAR', 'DEFORMED BAR', 'REINFORCEMENT BAR',
                     'TMT BAR', 'RIBBED BAR'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Long Products',
        'tier': 1,
    },
    # Wire Rod
    {
        'cargo_detail': 'Wire Rod',
        'keywords': ['WIRE ROD', 'WIREROD', 'STEEL WIRE ROD', 'CHQ WIRE'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Long Products',
        'tier': 1,
    },
    # Merchant Bar
    {
        'cargo_detail': 'Merchant Bar',
        'keywords': ['MERCHANT BAR', 'FLAT BAR', 'ROUND BAR', 'SQUARE BAR',
                     'HEXAGONAL BAR', 'HEX BAR'],
        'require_any': [],
        'exclude': ['REBAR', 'REINFORC'],
        'product_form': 'Long Products',
        'tier': 1,
    },
    # Structural Sections
    {
        'cargo_detail': 'I-Beam / H-Beam',
        'keywords': ['I-BEAM', 'H-BEAM', 'I BEAM', 'H BEAM', 'WIDE FLANGE',
                     'W BEAM', 'IPE', 'HEA', 'HEB'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Long Products',
        'tier': 1,
    },
    {
        'cargo_detail': 'Channel Section',
        'keywords': ['CHANNEL', 'C-CHANNEL', 'U-CHANNEL', 'UPN', 'UPE'],
        'require_any': [],
        'exclude': ['TV CHANNEL'],
        'product_form': 'Long Products',
        'tier': 1,
    },
    {
        'cargo_detail': 'Angle Section',
        'keywords': ['ANGLE', 'L-ANGLE', 'ANGLE BAR', 'EQUAL ANGLE', 'UNEQUAL ANGLE'],
        'require_any': ['STEEL', 'IRON'],
        'exclude': ['GRINDER', 'FITTING'],
        'product_form': 'Long Products',
        'tier': 2,
    },
    # Rails
    {
        'cargo_detail': 'Steel Rail',
        'keywords': ['STEEL RAIL', 'RAILWAY RAIL', 'RAILROAD RAIL', 'CRANE RAIL',
                     'LIGHT RAIL', 'HEAVY RAIL'],
        'require_any': [],
        'exclude': ['GUARDRAIL', 'HANDRAIL'],
        'product_form': 'Long Products',
        'tier': 1,
    },
    # Wire
    {
        'cargo_detail': 'Steel Wire',
        'keywords': ['STEEL WIRE', 'GALVANIZED WIRE', 'WIRE ROPE', 'PC WIRE',
                     'PRESTRESSED WIRE', 'SPRING WIRE', 'MUSIC WIRE'],
        'require_any': [],
        'exclude': ['WIRE ROD', 'WIREROD', 'BARBED WIRE'],
        'product_form': 'Long Products',
        'tier': 2,
    },
]

SEMI_FINISHED_RULES = [
    # Slabs
    {
        'cargo_detail': 'Steel Slab',
        'keywords': ['STEEL SLAB', 'SLAB', 'CC SLAB', 'CONTINUOUS CAST SLAB'],
        'require_any': [],
        'exclude': ['CONCRETE'],
        'product_form': 'Semi-Finished',
        'tier': 1,
    },
    # Billets
    {
        'cargo_detail': 'Steel Billet',
        'keywords': ['STEEL BILLET', 'BILLET', 'CC BILLET', 'SQUARE BILLET'],
        'require_any': [],
        'exclude': [],
        'product_form': 'Semi-Finished',
        'tier': 1,
    },
    # Blooms
    {
        'cargo_detail': 'Steel Bloom',
        'keywords': ['STEEL BLOOM', 'BLOOM'],
        'require_any': [],
        'exclude': ['ALGAE'],
        'product_form': 'Semi-Finished',
        'tier': 1,
    },
    # Ingots
    {
        'cargo_detail': 'Steel Ingot',
        'keywords': ['STEEL INGOT', 'INGOT'],
        'require_any': [],
        'exclude': ['ALUMINUM', 'ZINC', 'COPPER'],
        'product_form': 'Semi-Finished',
        'tier': 2,
    },
]


def check_keywords(text: str, keywords: list, require_any: list = None, exclude: list = None) -> bool:
    """Check if text matches keyword criteria."""
    if pd.isna(text):
        return False

    text_upper = str(text).upper()

    # Check excludes first
    if exclude:
        for excl in exclude:
            if excl.upper() in text_upper:
                return False

    # Check main keywords
    has_keyword = False
    for kw in keywords:
        if kw.upper() in text_upper:
            has_keyword = True
            break

    if not has_keyword:
        return False

    # Check require_any (at least one must be present)
    if require_any:
        has_required = False
        for req in require_any:
            if req.upper() in text_upper:
                has_required = True
                break
        if not has_required:
            return False

    return True


def classify_steel_record(goods: str, rules_by_tier: dict) -> tuple:
    """Apply rules to classify a steel record."""
    # Try rules in tier order
    for tier in sorted(rules_by_tier.keys()):
        for rule in rules_by_tier[tier]:
            if check_keywords(goods, rule['keywords'],
                             rule.get('require_any'),
                             rule.get('exclude')):
                return rule['cargo_detail'], rule['product_form']

    return None, None


def main():
    """Main classification execution."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("=" * 70)
    print("STEEL PRODUCT REFINEMENT - v1.0.0")
    print("=" * 70)
    print(f"Timestamp: {timestamp}")

    # Load data
    print("\nLoading data...")

    # Find latest SCM/Agg file
    matched_dir = BASE_DIR / "00_DATA" / "00.03_MATCHED"
    scm_files = list(matched_dir.glob("panjiva_ALL_YEARS_with_scm_agg_*.csv"))
    if scm_files:
        input_file = sorted(scm_files)[-1]
    else:
        input_file = INPUT_FILE

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)

    print(f"  Total records: {len(df):,}")
    print(f"  Total tonnage: {df['Tons_Numeric'].sum()/1e6:.1f}M tons")

    # Filter to steel records that need refinement
    steel_mask = (
        (df['Commodity'] == 'Steel') |
        (df['Cargo'].str.contains('Steel', na=False, case=False)) |
        (df['HS2'].isin(['72', '73']))
    )
    steel_df = df[steel_mask].copy()

    print(f"\n  Steel records: {len(steel_df):,}")
    print(f"  Steel tonnage: {steel_df['Tons_Numeric'].sum()/1e6:.1f}M tons")

    # Combine all rules and organize by tier
    all_rules = FLAT_ROLLED_RULES + TUBULAR_RULES + LONG_PRODUCT_RULES + SEMI_FINISHED_RULES
    rules_by_tier = {}
    for rule in all_rules:
        tier = rule.get('tier', 3)
        if tier not in rules_by_tier:
            rules_by_tier[tier] = []
        rules_by_tier[tier].append(rule)

    print(f"\n  Rules loaded: {len(all_rules)}")
    for tier in sorted(rules_by_tier.keys()):
        print(f"    Tier {tier}: {len(rules_by_tier[tier])} rules")

    # Apply classification
    print("\nClassifying steel products...")
    refined_count = 0
    results = []

    for idx in steel_df.index:
        goods = str(df.at[idx, 'Goods Shipped'])
        cargo_detail, product_form = classify_steel_record(goods, rules_by_tier)

        if cargo_detail:
            old_detail = df.at[idx, 'Cargo_Detail']

            # Only update if it's a more specific classification
            if pd.isna(old_detail) or old_detail in ['TBN', 'To Be Named', 'Steel',
                                                       'Flat Rolled', 'Tubular Goods',
                                                       'Long Products', 'Slabs', 'Billets']:
                df.at[idx, 'Cargo_Detail'] = cargo_detail
                refined_count += 1

                results.append({
                    'idx': idx,
                    'cargo_detail': cargo_detail,
                    'product_form': product_form,
                    'tons': df.at[idx, 'Tons_Numeric'],
                    'old_detail': old_detail
                })

    print(f"\n  Records refined: {refined_count:,}")

    # Summarize results
    if results:
        results_df = pd.DataFrame(results)
        print("\n" + "-" * 70)
        print("REFINEMENT SUMMARY BY PRODUCT")
        print("-" * 70)

        summary = results_df.groupby(['product_form', 'cargo_detail']).agg({
            'tons': ['count', 'sum']
        }).round(0)
        summary.columns = ['Records', 'Tons']
        summary = summary.sort_values('Tons', ascending=False)

        current_form = None
        for (form, detail), row in summary.iterrows():
            if form != current_form:
                print(f"\n  {form}:")
                current_form = form
            print(f"    {detail}: {int(row['Records']):,} records, {row['Tons']/1e6:.2f}M tons")

    # Save output
    output_file = OUTPUT_DIR / f"panjiva_ALL_YEARS_steel_refined_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file.name}")

    # Final statistics
    print("\n" + "=" * 70)
    print("FINAL STEEL CLASSIFICATION STATISTICS")
    print("=" * 70)

    steel_final = df[steel_mask]
    detail_summary = steel_final.groupby('Cargo_Detail')['Tons_Numeric'].agg(['count', 'sum'])
    detail_summary.columns = ['Records', 'Tons']
    detail_summary = detail_summary.sort_values('Tons', ascending=False)

    print("\nTop 25 Steel Cargo_Detail Classifications:")
    for detail, row in detail_summary.head(25).iterrows():
        print(f"  {detail}: {int(row['Records']):,} records, {row['Tons']/1e6:.2f}M tons")

    return df, output_file


if __name__ == "__main__":
    df, output_file = main()
