"""
SCM (Supplementary Cementitious Materials) and Aggregates Classification
=========================================================================
Version: 1.0.0
Date: 2026-02-09

Classifies construction materials into refined categories:

SCM (Supplementary Cementitious Materials):
- GGBFS (Ground Granulated Blast Furnace Slag)
- Fly Ash (Coal combustion byproduct)
- Pozzolan (Natural volcanic ash)
- Silica Fume (Microsilica)
- Slag Cement (Blended cement with slag)

Aggregates:
- Limestone (crusite, construction grade)
- Sand (construction, industrial)
- Gravel (construction aggregate)
- Granite (dimension stone, aggregate)
- Crushed Stone (quarry products)
- Bauxite (aluminum ore, also used as aggregate)
- Gypsum (wallboard, cement addite)

Taxonomy Structure:
Group: Dry Bulk
Commodity: Construction Materials
Cargo: [SCM | Aggregates | Gypsum]
Cargo_Detail: [Specific material type]
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(r"G:\My Drive\LLM\project_manifest")
INPUT_FILE = BASE_DIR / "00_DATA" / "00.03_MATCHED" / "panjiva_ALL_YEARS_FINAL.csv"
OUTPUT_DIR = BASE_DIR / "00_DATA" / "00.03_MATCHED"

# Pre-compiled regex patterns for performance
PATTERNS = {}

def compile_pattern(keywords: list) -> re.Pattern:
    """Compile keyword list into efficient regex pattern."""
    escaped = [re.escape(k) for k in keywords]
    pattern = '|'.join(escaped)
    return re.compile(pattern, re.IGNORECASE)

# ============================================================
# SCM CLASSIFICATION RULES
# ============================================================
SCM_RULES = [
    # GGBFS - Ground Granulated Blast Furnace Slag
    {
        'cargo_detail': 'GGBFS (Ground Granulated Blast Furnace Slag)',
        'cargo': 'SCM',
        'keywords': ['GGBFS', 'GBFS', 'GROUND GRANULATED BLAST FURNACE SLAG',
                     'GRANULATED BLAST FURNACE SLAG', 'BLAST FURNACE SLAG',
                     'GROUND SLAG', 'GRANULATED SLAG'],
        'exclude': ['IRON SLAG', 'STEEL SLAG'],
        'hs4': ['2618', '2619'],  # Slag from iron/steel
        'min_tons': 100,
        'tier': 1,
    },
    # Fly Ash
    {
        'cargo_detail': 'Fly Ash',
        'cargo': 'SCM',
        'keywords': ['FLY ASH', 'FLYASH', 'COAL ASH', 'PULVERIZED FUEL ASH', 'PFA'],
        'exclude': ['BOTTOM ASH'],
        'hs4': ['2621'],  # Other slag and ash
        'min_tons': 100,
        'tier': 1,
    },
    # Pozzolan
    {
        'cargo_detail': 'Pozzolan',
        'cargo': 'SCM',
        'keywords': ['POZZOLAN', 'POZZOLANA', 'POZZOLANIC', 'NATURAL POZZOLAN',
                     'VOLCANIC ASH', 'TRASS', 'SANTORIN EARTH'],
        'exclude': [],
        'hs4': ['2530'],  # Mineral substances NES
        'min_tons': 50,
        'tier': 1,
    },
    # Silica Fume
    {
        'cargo_detail': 'Silica Fume',
        'cargo': 'SCM',
        'keywords': ['SILICA FUME', 'MICROSILICA', 'CONDENSED SILICA FUME'],
        'exclude': [],
        'hs4': ['2811'],  # Other inorganic acids
        'min_tons': 10,
        'tier': 1,
    },
    # Slag Cement (blended)
    {
        'cargo_detail': 'Slag Cement',
        'cargo': 'SCM',
        'keywords': ['SLAG CEMENT', 'PORTLAND SLAG CEMENT', 'BLENDED SLAG CEMENT'],
        'exclude': [],
        'hs4': ['2523'],  # Portland cement
        'min_tons': 100,
        'tier': 1,
    },
    # Generic Slag (fallback)
    {
        'cargo_detail': 'Slag - Other',
        'cargo': 'SCM',
        'keywords': ['SLAG'],
        'exclude': ['GGBFS', 'BLAST FURNACE', 'SLAG CEMENT', 'IRON SLAG', 'STEEL SLAG',
                    'COPPER SLAG', 'NICKEL SLAG', 'FERRONICKEL SLAG'],
        'hs4': ['2618', '2619', '2621'],
        'min_tons': 100,
        'tier': 3,  # Lower priority
    },
]

# ============================================================
# AGGREGATES CLASSIFICATION RULES
# ============================================================
AGGREGATE_RULES = [
    # Limestone - Construction Grade
    {
        'cargo_detail': 'Limestone',
        'cargo': 'Aggregates',
        'keywords': ['LIMESTONE', 'LIME STONE', 'CALCITE', 'CALCIUM CARBITE',
                     'CRUSHED LIMESTONE', 'LIMESTONE AGGREGATE'],
        'exclude': ['CALCIUM CARBITE POWDER', 'PRECIPITATED'],
        'hs4': ['2521', '2517'],  # Limestone, broken stone
        'min_tons': 100,
        'tier': 1,
    },
    # Sand - Construction
    {
        'cargo_detail': 'Sand - Construction',
        'cargo': 'Aggregates',
        'keywords': ['CONSTRUCTION SAND', 'BUILDING SAND', 'MASONRY SAND',
                     'CONCRETE SAND', 'WASHED SAND', 'RIVER SAND', 'PIT SAND'],
        'exclude': ['SILICA SAND', 'INDUSTRIAL SAND', 'FOUNDRY SAND', 'FRAC SAND'],
        'hs4': ['2505'],  # Natural sands
        'min_tons': 100,
        'tier': 1,
    },
    # Sand - Industrial (Silica)
    {
        'cargo_detail': 'Sand - Industrial (Silica)',
        'cargo': 'Aggregates',
        'keywords': ['SILICA SAND', 'INDUSTRIAL SAND', 'QUARTZ SAND', 'FOUNDRY SAND',
                     'FRAC SAND', 'GLASS SAND', 'FILTER SAND'],
        'exclude': [],
        'hs4': ['2505', '2506'],  # Natural sands, quartz
        'min_tons': 50,
        'tier': 1,
    },
    # Sand - Generic (fallback)
    {
        'cargo_detail': 'Sand - NOS',
        'cargo': 'Aggregates',
        'keywords': ['SAND'],
        'exclude': ['SANDAL', 'SANDWICH', 'ANDERSON', 'QUICKSAND', 'SANDERS'],
        'hs4': ['2505'],
        'min_tons': 500,  # Higher threshold for generic
        'tier': 3,
    },
    # Gravel
    {
        'cargo_detail': 'Gravel',
        'cargo': 'Aggregates',
        'keywords': ['GRAVEL', 'PEA GRAVEL', 'CRUSHED GRAVEL', 'BANK RUN GRAVEL'],
        'exclude': [],
        'hs4': ['2517'],  # Pebbles, gravel
        'min_tons': 100,
        'tier': 1,
    },
    # Crushed Stone
    {
        'cargo_detail': 'Crushed Stone',
        'cargo': 'Aggregates',
        'keywords': ['CRUSHED STONE', 'CRUSHED ROCK', 'BROKEN STONE', 'STONE AGGREGATE',
                     'COARSE AGGREGATE', 'ROAD STONE', 'BALLAST STONE'],
        'exclude': [],
        'hs4': ['2517'],
        'min_tons': 100,
        'tier': 1,
    },
    # Granite
    {
        'cargo_detail': 'Granite',
        'cargo': 'Aggregates',
        'keywords': ['GRANITE', 'GRANITE BLOCKS', 'GRANITE SLABS', 'DIMENSION GRANITE'],
        'exclude': ['GRANITE COUNTERTOP', 'GRANITE TILE'],
        'hs4': ['2516'],  # Granite
        'min_tons': 50,
        'tier': 1,
    },
    # Marble
    {
        'cargo_detail': 'Marble',
        'cargo': 'Aggregates',
        'keywords': ['MARBLE', 'MARBLE BLOCKS', 'MARBLE SLABS', 'TRAVERTINE'],
        'exclude': ['MARBLE TILE', 'MARBLE COUNTERTOP', 'CULTURED MARBLE'],
        'hs4': ['2515'],  # Marble
        'min_tons': 50,
        'tier': 1,
    },
    # Pumice
    {
        'cargo_detail': 'Pumice',
        'cargo': 'Aggregates',
        'keywords': ['PUMICE', 'PUMICE STONE', 'VOLCANIC PUMICE'],
        'exclude': [],
        'hs4': ['2513'],  # Pumice
        'min_tons': 50,
        'tier': 1,
    },
    # Aggregate - Generic
    {
        'cargo_detail': 'Aggregate - NOS',
        'cargo': 'Aggregates',
        'keywords': ['AGGREGATE', 'CONSTRUCTION AGGREGATE', 'ROAD AGGREGATE'],
        'exclude': [],
        'hs4': ['2517'],
        'min_tons': 500,
        'tier': 3,
    },
]

# ============================================================
# GYPSUM RULES (already partially classified, add refinement)
# ============================================================
GYPSUM_RULES = [
    # Natural Gypsum
    {
        'cargo_detail': 'Gypsum - Natural',
        'cargo': 'Gypsum',
        'keywords': ['NATURAL GYPSUM', 'GYPSUM ROCK', 'RAW GYPSUM', 'CRUDE GYPSUM',
                     'GYPSUM ORE'],
        'exclude': ['FGD', 'SYNTHETIC', 'WALLBOARD'],
        'hs4': ['2520'],  # Gypsum
        'min_tons': 100,
        'tier': 1,
    },
    # FGD Gypsum (synthetic from power plants)
    {
        'cargo_detail': 'Gypsum - FGD (Synthetic)',
        'cargo': 'Gypsum',
        'keywords': ['FGD GYPSUM', 'SYNTHETIC GYPSUM', 'FLUE GAS DESULFURIZATION',
                     'DESULFOGYPSUM'],
        'exclude': [],
        'hs4': ['2520'],
        'min_tons': 100,
        'tier': 1,
    },
    # Gypsum Generic
    {
        'cargo_detail': 'Gypsum - NOS',
        'cargo': 'Gypsum',
        'keywords': ['GYPSUM'],
        'exclude': ['WALLBOARD', 'DRYWALL', 'PLASTER'],
        'hs4': ['2520'],
        'min_tons': 500,
        'tier': 3,
    },
]

# ============================================================
# BAUXITE RULES (for aggregates context)
# ============================================================
BAUXITE_RULES = [
    {
        'cargo_detail': 'Bauxite',
        'cargo': 'Mineral Ores',
        'keywords': ['BAUXITE', 'BAUXITE ORE', 'ALUMINA ORE'],
        'exclude': ['CALCINED BAUXITE'],
        'hs4': ['2606'],  # Aluminum ores
        'min_tons': 500,
        'tier': 1,
    },
    {
        'cargo_detail': 'Calcined Bauxite',
        'cargo': 'Mineral Ores',
        'keywords': ['CALCINED BAUXITE', 'REFRACTORY BAUXITE'],
        'exclude': [],
        'hs4': ['2606', '2508'],
        'min_tons': 100,
        'tier': 1,
    },
]


def check_keywords(text: str, keywords: list, exclude: list = None) -> bool:
    """Check if text contains any keyword but no exclude terms."""
    if pd.isna(text):
        return False

    text_upper = text.upper()

    # Check excludes first
    if exclude:
        for excl in exclude:
            if excl.upper() in text_upper:
                return False

    # Check keywords
    for kw in keywords:
        if kw.upper() in text_upper:
            return True

    return False


def classify_record(row, rules_by_tier):
    """Apply rules to classify a single record."""
    goods = str(row.get('Goods Shipped', ''))
    hs4 = str(row.get('HS4', ''))
    tons = float(row.get('Tons_Numeric', 0))

    # Try rules in tier order (1 = most specific, 3 = generic fallback)
    for tier in [1, 2, 3]:
        if tier not in rules_by_tier:
            continue

        for rule in rules_by_tier[tier]:
            # Check tonnage threshold
            if tons < rule['min_tons']:
                continue

            # Check HS code if specified
            if rule.get('hs4') and hs4[:4] not in rule['hs4']:
                continue

            # Check keywords
            if check_keywords(goods, rule['keywords'], rule.get('exclude', [])):
                return rule['cargo'], rule['cargo_detail']

    return None, None


def main():
    """Main classification execution."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("=" * 70)
    print("SCM & AGGREGATES CLASSIFICATION - v1.0.0")
    print("=" * 70)
    print(f"Timestamp: {timestamp}")

    # Load data
    print("\nLoading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)

    print(f"  Total records: {len(df):,}")
    print(f"  Total tonnage: {df['Tons_Numeric'].sum()/1e6:.1f}M tons")

    # Combine all rules
    all_rules = SCM_RULES + AGGREGATE_RULES + GYPSUM_RULES + BAUXITE_RULES

    # Organize by tier
    rules_by_tier = {}
    for rule in all_rules:
        tier = rule.get('tier', 2)
        if tier not in rules_by_tier:
            rules_by_tier[tier] = []
        rules_by_tier[tier].append(rule)

    print(f"\n  Rules loaded: {len(all_rules)}")
    for tier in sorted(rules_by_tier.keys()):
        print(f"    Tier {tier}: {len(rules_by_tier[tier])} rules")

    # Find unclassified or refineable records
    # Focus on records that need SCM/Aggregate classification
    target_mask = (
        (df['Cargo'].isna()) |
        (df['Cargo'] == 'TBN') |
        (df['Cargo'] == 'To Be Named') |
        (df['Cargo'].isin(['Aggregates', 'Gypsum', 'Bauxite', 'Barite'])) |
        (df['Cargo_Detail'].isna()) |
        (df['Cargo_Detail'] == 'TBN')
    )

    # Also include records with relevant HS codes
    hs_mask = df['HS4'].fillna('').str[:4].isin([
        '2505', '2506', '2513', '2515', '2516', '2517', '2520', '2521',
        '2523', '2530', '2606', '2618', '2619', '2621'
    ])

    target_df = df[target_mask | hs_mask].copy()
    print(f"\n  Target records for classification: {len(target_df):,}")

    # Apply classification
    print("\nClassifying records...")
    classified_count = 0
    refined_count = 0

    results = []
    for idx, row in target_df.iterrows():
        cargo, cargo_detail = classify_record(row, rules_by_tier)
        if cargo and cargo_detail:
            old_cargo = df.at[idx, 'Cargo']
            old_detail = df.at[idx, 'Cargo_Detail']

            # Update the main dataframe
            df.at[idx, 'Group'] = 'Dry Bulk'
            df.at[idx, 'Commodity'] = 'Construction Materials'
            df.at[idx, 'Cargo'] = cargo
            df.at[idx, 'Cargo_Detail'] = cargo_detail

            if pd.isna(old_cargo) or old_cargo in ['TBN', 'To Be Named']:
                classified_count += 1
            else:
                refined_count += 1

            results.append({
                'idx': idx,
                'cargo': cargo,
                'cargo_detail': cargo_detail,
                'tons': row['Tons_Numeric'],
                'old_cargo': old_cargo,
                'old_detail': old_detail
            })

    print(f"\n  New classifications: {classified_count:,}")
    print(f"  Refinements: {refined_count:,}")
    print(f"  Total changes: {len(results):,}")

    # Summarize by cargo detail
    if results:
        results_df = pd.DataFrame(results)
        print("\n" + "-" * 70)
        print("CLASSIFICATION SUMMARY BY CARGO DETAIL")
        print("-" * 70)

        summary = results_df.groupby(['cargo', 'cargo_detail']).agg({
            'tons': ['count', 'sum']
        }).round(0)
        summary.columns = ['Records', 'Tons']
        summary = summary.sort_values('Tons', ascending=False)

        for (cargo, detail), row in summary.iterrows():
            print(f"  {cargo} > {detail}")
            print(f"    Records: {int(row['Records']):,}")
            print(f"    Tonnage: {row['Tons']/1e6:.2f}M tons")
            print()

    # Save output
    output_file = OUTPUT_DIR / f"panjiva_ALL_YEARS_with_scm_agg_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file.name}")

    # Create summary statistics
    print("\n" + "=" * 70)
    print("FINAL STATISTICS")
    print("=" * 70)

    scm_agg_mask = df['Commodity'] == 'Construction Materials'
    scm_agg_df = df[scm_agg_mask]

    print(f"\nConstruction Materials Total:")
    print(f"  Records: {len(scm_agg_df):,}")
    print(f"  Tonnage: {scm_agg_df['Tons_Numeric'].sum()/1e6:.2f}M tons")

    cargo_summary = scm_agg_df.groupby('Cargo')['Tons_Numeric'].agg(['count', 'sum'])
    cargo_summary.columns = ['Records', 'Tons']
    cargo_summary = cargo_summary.sort_values('Tons', ascending=False)

    print("\nBy Cargo Category:")
    for cargo, row in cargo_summary.iterrows():
        print(f"  {cargo}: {int(row['Records']):,} records, {row['Tons']/1e6:.2f}M tons")

    return df, output_file


if __name__ == "__main__":
    df, output_file = main()
