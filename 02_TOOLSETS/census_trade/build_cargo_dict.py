"""Build Cargo HS6 Dictionary from Excel source with auto-expansion.

Source: data/us_hs6_dictionary_sep_nov_2025_user.xlsx
Output: data/cargo_hs6_dictionary.json

3-tier layered mapping:
  1. Manual    — William's 2,788 hand-classified mappings (unchanged)
  2. Heading   — Unmapped codes inherit from manual codes in the same 4-digit HS heading
  3. Chapter   — Remaining codes get a broad default by HS chapter
"""
import json
import os
import sys
from collections import Counter

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = 'data/us_hs6_dictionary_sep_nov_2025_user.xlsx'
SHEET_NAME = 'us_hs6_dictionary_sep_nov_2025'
OUTPUT_PATH = 'data/cargo_hs6_dictionary.json'

# ============================================================
# Chapter default table (tier 3)
# For headings with zero manual mappings, assign by HS chapter.
# cargo and cargo_detail are set equal to the commodity name.
# ============================================================

CHAPTER_DEFAULTS = {
    1:  ('Dry', 'Reefer'),
    2:  ('Dry', 'Reefer'),
    3:  ('Dry', 'Reefer'),
    4:  ('Dry', 'Reefer'),
    5:  ('Containerized', 'Animal Products'),
    6:  ('Dry', 'Reefer'),
    7:  ('Dry', 'Reefer'),
    8:  ('Dry', 'Reefer'),
    9:  ('Containerized', 'Spices & Coffee'),
    10: ('Dry Bulk', 'Agricultural'),
    11: ('Containerized', 'Prepared Foods'),
    12: ('Containerized', 'Oilseeds & Fats'),
    13: ('Containerized', 'Gums & Resins'),
    14: ('Containerized', 'Vegetable Products'),
    15: ('Liquid Bulk', 'Agricultural'),
    16: ('Containerized', 'Prepared Foods'),
    17: ('Dry Bulk', 'Agricultural'),
    18: ('Containerized', 'Prepared Foods'),
    19: ('Containerized', 'Prepared Foods'),
    20: ('Containerized', 'Prepared Foods'),
    21: ('Containerized', 'Prepared Foods'),
    22: ('Liquid Bulk', 'Agricultural'),
    23: ('Dry Bulk', 'Agricultural'),
    24: ('Containerized', 'Tobacco'),
    25: ('Dry Bulk', 'Minerals & Ores'),
    26: ('Dry Bulk', 'Minerals & Ores'),
    27: ('Liquid Bulk', 'Petroleum Products'),
    28: ('Liquid Bulk', 'Misc Chemicals'),
    29: ('Liquid Bulk', 'Misc Chemicals'),
    30: ('Containerized', 'Pharmaceuticals'),
    31: ('Dry Bulk', 'Fertilizer'),
    32: ('Liquid Bulk', 'Misc Chemicals'),
    33: ('Containerized', 'Cosmetics & Perfumery'),
    34: ('Containerized', 'Soaps & Detergents'),
    35: ('Containerized', 'Starches & Glues'),
    36: ('Containerized', 'Explosives'),
    37: ('Containerized', 'Photographic Goods'),
    38: ('Liquid Bulk', 'Misc Chemicals'),
    39: ('Dry Bulk', 'Plastics'),
    40: ('Containerized', 'Rubber Products'),
    41: ('Containerized', 'Hides & Skins'),
    42: ('Containerized', 'Leather Goods'),
    43: ('Containerized', 'Furskins'),
    44: ('Dry Bulk', 'Forestry'),
    45: ('Containerized', 'Cork Products'),
    46: ('Containerized', 'Basketware'),
    47: ('Dry Bulk', 'Forestry'),
    48: ('Containerized', 'Paper Products'),
    49: ('Containerized', 'Printed Materials'),
    50: ('Containerized', 'Textiles & Apparel'),
    51: ('Containerized', 'Textiles & Apparel'),
    52: ('Containerized', 'Textiles & Apparel'),
    53: ('Containerized', 'Textiles & Apparel'),
    54: ('Containerized', 'Textiles & Apparel'),
    55: ('Containerized', 'Textiles & Apparel'),
    56: ('Containerized', 'Textiles & Apparel'),
    57: ('Containerized', 'Textiles & Apparel'),
    58: ('Containerized', 'Textiles & Apparel'),
    59: ('Containerized', 'Textiles & Apparel'),
    60: ('Containerized', 'Textiles & Apparel'),
    61: ('Containerized', 'Textiles & Apparel'),
    62: ('Containerized', 'Textiles & Apparel'),
    63: ('Containerized', 'Textiles & Apparel'),
    64: ('Containerized', 'Footwear & Accessories'),
    65: ('Containerized', 'Footwear & Accessories'),
    66: ('Containerized', 'Footwear & Accessories'),
    67: ('Containerized', 'Footwear & Accessories'),
    68: ('Containerized', 'Stone/Glass Products'),
    69: ('Containerized', 'Stone/Glass Products'),
    70: ('Containerized', 'Stone/Glass Products'),
    71: ('Containerized', 'Precious Metals'),
    72: ('Dry Bulk', 'Steel'),
    73: ('Dry Bulk', 'Steel'),
    74: ('Dry Bulk', 'Metals'),
    75: ('Dry Bulk', 'Metals'),
    76: ('Dry Bulk', 'Metals'),
    78: ('Dry Bulk', 'Metals'),
    79: ('Dry Bulk', 'Metals'),
    80: ('Dry Bulk', 'Metals'),
    81: ('Dry Bulk', 'Metals'),
    82: ('Containerized', 'Metal Products'),
    83: ('Containerized', 'Metal Products'),
    84: ('Containerized', 'Machinery'),
    85: ('Containerized', 'Electrical Equipment'),
    86: ('Containerized', 'Vehicles & Transport'),
    87: ('Containerized', 'Vehicles & Transport'),
    88: ('Containerized', 'Vehicles & Transport'),
    89: ('Containerized', 'Vehicles & Transport'),
    90: ('Containerized', 'Instruments'),
    91: ('Containerized', 'Instruments'),
    92: ('Containerized', 'Instruments'),
    93: ('Containerized', 'Arms'),
    94: ('Containerized', 'Furniture & Misc'),
    95: ('Containerized', 'Furniture & Misc'),
    96: ('Containerized', 'Furniture & Misc'),
    97: ('Containerized', 'Art & Antiques'),
    98: ('Containerized', 'Special Provisions'),
    99: ('Containerized', 'Special Provisions'),
}


def is_mapped(group, commodity):
    """Return True if this row has a manual mapping (not 'x' or None)."""
    return (group is not None and group != 'x'
            and commodity is not None and commodity != 'x')


def read_excel(path):
    """Read the Excel source and return list of row dicts."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[SHEET_NAME]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        hs6_raw = row[0]
        if hs6_raw is None:
            continue
        hs6 = str(int(hs6_raw)).zfill(6)
        export_mt = float(row[6]) if row[6] is not None else 0.0
        import_mt = float(row[7]) if row[7] is not None else 0.0
        rows.append({
            'hs6': hs6,
            'description': str(row[1] or '').strip(),
            'group': row[2] if row[2] else None,
            'commodity': row[3] if row[3] else None,
            'cargo': row[4] if row[4] else None,
            'cargo_detail': row[5] if row[5] else None,
            'export_ves_mt': round(export_mt, 3),
            'import_ves_mt': round(import_mt, 3),
            'total_mt': round(export_mt + import_mt, 3),
        })
    wb.close()
    return rows


def build_heading_map(rows):
    """Build {4-digit heading: (group, commodity, cargo, cargo_detail)} from manual mappings.

    When a heading has multiple distinct manual mappings, pick the one with the
    most codes (ties broken by total_mt).
    """
    from collections import defaultdict
    heading_mappings = defaultdict(list)
    for r in rows:
        if is_mapped(r['group'], r['commodity']):
            heading = r['hs6'][:4]
            heading_mappings[heading].append(
                (r['group'], r['commodity'], r['cargo'], r['cargo_detail'], r['total_mt'])
            )

    result = {}
    for heading, entries in heading_mappings.items():
        # Count by (group, commodity, cargo, cargo_detail)
        mapping_counts = Counter()
        mapping_volume = Counter()
        for g, co, ca, cd, mt in entries:
            key = (g, co, ca, cd)
            mapping_counts[key] += 1
            mapping_volume[key] += mt
        # Pick the most common mapping; break ties by volume
        best = max(mapping_counts, key=lambda k: (mapping_counts[k], mapping_volume[k]))
        result[heading] = best
    return result


def get_chapter(hs6):
    """Extract 2-digit HS chapter from 6-digit code."""
    return int(hs6[:2])


def build_dictionary(rows):
    """Apply 3-tier mapping and return the full dictionary."""
    heading_map = build_heading_map(rows)

    counts = {'manual': 0, 'heading': 0, 'chapter': 0, 'unmapped': 0}

    hs6_lookup = {}
    for r in rows:
        hs6 = r['hs6']

        if is_mapped(r['group'], r['commodity']):
            # Tier 1: Manual
            source = 'manual'
            group, commodity, cargo, cargo_detail = (
                r['group'], r['commodity'], r['cargo'], r['cargo_detail']
            )
        else:
            heading = hs6[:4]
            if heading in heading_map:
                # Tier 2: Heading propagation
                source = 'heading'
                group, commodity, cargo, cargo_detail = heading_map[heading]
            else:
                chapter = get_chapter(hs6)
                if chapter in CHAPTER_DEFAULTS:
                    # Tier 3: Chapter default
                    source = 'chapter'
                    group, commodity = CHAPTER_DEFAULTS[chapter]
                    cargo = commodity
                    cargo_detail = commodity
                else:
                    # No mapping available
                    source = 'unmapped'
                    group = 'Unmapped'
                    commodity = 'Unmapped'
                    cargo = 'Unmapped'
                    cargo_detail = 'Unmapped'

        counts[source] += 1
        hs6_lookup[hs6] = {
            'description': r['description'],
            'group': group,
            'commodity': commodity,
            'cargo': cargo,
            'cargo_detail': cargo_detail,
            'export_ves_mt': r['export_ves_mt'],
            'import_ves_mt': r['import_ves_mt'],
            'total_mt': r['total_mt'],
            'mapping_source': source,
        }

    return hs6_lookup, counts


def build_hierarchy(hs6_lookup):
    """Build the group → commodity → [cargo] hierarchy from classified entries."""
    hierarchy = {}
    for entry in hs6_lookup.values():
        g, co, ca = entry['group'], entry['commodity'], entry['cargo']
        if g == 'Unmapped':
            continue
        if g not in hierarchy:
            hierarchy[g] = {}
        if co not in hierarchy[g]:
            hierarchy[g][co] = []
        if ca not in hierarchy[g][co]:
            hierarchy[g][co].append(ca)
    return hierarchy


def build_cargo_to_hs6(hs6_lookup):
    """Build the cargo → {group, commodity, hs6_codes, total_mt} reverse lookup."""
    from collections import defaultdict
    cargo_map = defaultdict(lambda: {'group': None, 'commodity': None, 'hs6_codes': [], 'total_mt': 0.0})
    for hs6, entry in hs6_lookup.items():
        cargo = entry['cargo']
        if cargo == 'Unmapped':
            continue
        cm = cargo_map[cargo]
        cm['group'] = entry['group']
        cm['commodity'] = entry['commodity']
        cm['hs6_codes'].append(hs6)
        cm['total_mt'] += entry['total_mt']

    result = {}
    for cargo in sorted(cargo_map, key=lambda c: -cargo_map[c]['total_mt']):
        cm = cargo_map[cargo]
        result[cargo] = {
            'group': cm['group'],
            'commodity': cm['commodity'],
            'hs6_codes': sorted(cm['hs6_codes']),
            'total_mt': round(cm['total_mt'], 3),
            'hs6_count': len(cm['hs6_codes']),
        }
    return result


def main():
    print(f"Reading Excel: {EXCEL_PATH}")
    rows = read_excel(EXCEL_PATH)
    print(f"  Rows read: {len(rows)}")

    print("\nApplying 3-tier mapping...")
    hs6_lookup, counts = build_dictionary(rows)

    print(f"\n  Total HS6 codes:    {len(hs6_lookup):,}")
    print(f"  Manual mappings:    {counts['manual']:,}")
    print(f"  Heading-propagated: {counts['heading']:,}")
    print(f"  Chapter defaults:   {counts['chapter']:,}")
    print(f"  Unmapped:           {counts['unmapped']:,}")

    hierarchy = build_hierarchy(hs6_lookup)
    cargo_to_hs6 = build_cargo_to_hs6(hs6_lookup)

    # Count unique cargo types (excluding Unmapped)
    cargo_types = set()
    for entry in hs6_lookup.values():
        if entry['cargo'] != 'Unmapped':
            cargo_types.add(entry['cargo'])

    master = {
        '_metadata': {
            'source_file': os.path.basename(EXCEL_PATH),
            'created': '2026-02-18',
            'total_hs6_codes': len(hs6_lookup),
            'manual_codes': counts['manual'],
            'heading_propagated_codes': counts['heading'],
            'chapter_default_codes': counts['chapter'],
            'unmapped_codes': counts['unmapped'],
            'cargo_types': len(cargo_types),
            'period': 'Sep-Nov 2025',
            'units': 'metric_tons',
            'notes': (
                'HS6 codes mapped to cargo classification by William Davis. '
                'Unmapped codes auto-classified via heading propagation and chapter defaults. '
                'Volumes are vessel-borne US trade Sep-Nov 2025.'
            ),
        },
        'hierarchy': hierarchy,
        'cargo_to_hs6': cargo_to_hs6,
        'hs6_lookup': hs6_lookup,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    fsize = os.path.getsize(OUTPUT_PATH)
    print(f"\nWrote: {OUTPUT_PATH} ({fsize / 1024:.0f} KB)")
    print(f"  Hierarchy groups: {list(hierarchy.keys())}")
    print(f"  Unique cargo types: {len(cargo_types)}")

    # Spot checks
    print("\n" + "=" * 70)
    print("SPOT CHECKS")
    print("=" * 70)

    def check(hs6, label):
        e = hs6_lookup.get(hs6)
        if e:
            print(f"  {hs6} ({label}): {e['group']}/{e['commodity']}/{e['cargo']} [{e['mapping_source']}]")
        else:
            print(f"  {hs6} ({label}): NOT FOUND")

    check('270900', 'Crude Oil')
    check('100390', 'Grain')
    check('270112', 'Coal')
    check('380210', 'Carbon Product — manual')
    check('380290', 'Carbon heading — should inherit')
    check('390690', 'Ch.39 plastics — was unmapped')
    check('870323', 'Ch.87 vehicles — chapter default')

    print("\nDone.")


if __name__ == '__main__':
    main()
