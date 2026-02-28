#!/usr/bin/env python3
"""
Rebuild sources_inventory.csv with all 249 datasets in correct order.
This is a standalone version with absolute paths embedded.
"""

import json
import csv
import re
import os
import sys

def clean_html_tags(text):
    """Remove HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def truncate_description(text, max_length=200):
    """Truncate description to max length."""
    if not text:
        return ""
    text = clean_html_tags(text)
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text

def format_source_id(index):
    """Format SOURCE_ID as DS-001, DS-002, etc."""
    return f"DS-{index:03d}"

def extract_formats_from_geospatial(format_str):
    """Extract formats from geospatial CSV data."""
    if not format_str:
        return "Geospatial"
    return format_str.strip()

def read_geospatial_csv():
    """Read original geospatial datasets from CSV (rows 2-37, 36 total)."""
    datasets = []
    csv_path = "G:\\My Drive\\LLM\\sources_data_maps\\_user_notes\\_drafts_source_library\\Master_GIS_Dataset_Index (2).csv"

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                if i > 36:  # Only read first 36 rows
                    break

                dataset = {
                    'source_id': format_source_id(i),
                    'name': row.get('Dataset Name', ''),
                    'type': extract_formats_from_geospatial(row.get('Data Format', '')),
                    'source': row.get('Department', ''),
                    'category': row.get('Category', ''),
                    'description': truncate_description(row.get('Description', '')),
                    'url': row.get('URL', ''),
                    'update_status': row.get('Update Status', '')
                }
                datasets.append(dataset)
    except Exception as e:
        print(f"ERROR reading geospatial CSV: {e}")
        return []

    print(f"Loaded {len(datasets)} geospatial datasets (DS-001 to DS-036)")
    return datasets

def read_eia_datasets():
    """Read EIA datasets from JSON (85 total, DS-037 to DS-121)."""
    datasets = []
    json_path = "G:\\My Drive\\LLM\\sources_data_maps\\eia_datasets_complete.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, item in enumerate(data, start=37):
            dataset = {
                'source_id': format_source_id(i),
                'name': item.get('title', ''),
                'type': '|'.join(item.get('formats', [])) if item.get('formats') else '',
                'source': item.get('publisher', ''),
                'category': item.get('organization', ''),
                'description': truncate_description(item.get('description', '')),
                'url': item.get('url', ''),
                'update_status': 'Current'  # EIA datasets default to Current
            }
            datasets.append(dataset)
    except Exception as e:
        print(f"ERROR reading EIA JSON: {e}")
        return []

    print(f"Loaded {len(datasets)} EIA datasets (DS-037 to DS-121)")
    return datasets

def read_fgdc_datasets():
    """Read FGDC datasets from JSON, filter out duplicates (47 total, DS-122 to DS-168)."""
    datasets = []
    json_path = "G:\\My Drive\\LLM\\sources_data_maps\\fgdc_datasets_complete.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        counter = 122
        duplicate_count = 0

        for item in data:
            # Skip duplicates marked as is_duplicate=true
            if item.get('is_duplicate', False):
                duplicate_count += 1
                continue

            # Extract formats from resources if available
            formats = []
            if item.get('resources'):
                for res in item['resources']:
                    fmt = res.get('format', '')
                    if fmt and fmt not in formats:
                        formats.append(fmt)

            dataset = {
                'source_id': format_source_id(counter),
                'name': item.get('title', ''),
                'type': '|'.join(formats) if formats else 'Geospatial',
                'source': item.get('organization', ''),
                'category': 'Transportation',  # FGDC is transportation focused
                'description': truncate_description(item.get('description', '')),
                'url': item.get('url', ''),
                'update_status': 'Current'
            }
            datasets.append(dataset)
            counter += 1
    except Exception as e:
        print(f"ERROR reading FGDC JSON: {e}")
        return []

    print(f"Loaded {len(datasets)} FGDC datasets (DS-122 to DS-168) - Skipped {duplicate_count} duplicates")
    return datasets

def read_maritime_datasets():
    """Read maritime/USACE/NOAA datasets from JSON (9 total, DS-169 to DS-177)."""
    datasets = []
    json_path = "G:\\My Drive\\LLM\\sources_data_maps\\maritime_usace_noaa_datasets.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, item in enumerate(data, start=169):
            dataset = {
                'source_id': format_source_id(i),
                'name': item.get('title', ''),
                'type': '|'.join(item.get('formats', [])) if item.get('formats') else 'Geospatial',
                'source': item.get('source', ''),
                'category': item.get('category', 'Maritime'),
                'description': truncate_description(item.get('description', '')),
                'url': item.get('url', ''),
                'update_status': item.get('update_status', 'Current')
            }
            datasets.append(dataset)
    except Exception as e:
        print(f"ERROR reading maritime JSON: {e}")
        return []

    print(f"Loaded {len(datasets)} maritime/USACE/NOAA datasets (DS-169 to DS-177)")
    return datasets

def read_chrome_bookmark_datasets():
    """Read Chrome bookmark datasets from JSON, filter out duplicates (72 total, DS-178 to DS-249)."""
    datasets = []
    json_path = "G:\\My Drive\\LLM\\sources_data_maps\\chrome_bookmarks_datasets.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        counter = 178
        duplicate_count = 0

        for item in data:
            # Skip duplicates marked as is_duplicate=true
            if item.get('is_duplicate', False):
                duplicate_count += 1
                continue

            dataset = {
                'source_id': format_source_id(counter),
                'name': item.get('title', ''),
                'type': 'Web Bookmark',
                'source': item.get('source', ''),
                'category': item.get('category', ''),
                'description': truncate_description(item.get('description', '') or 'Bookmark from Chrome browser'),
                'url': item.get('url', ''),
                'update_status': 'Static'
            }
            datasets.append(dataset)
            counter += 1
    except Exception as e:
        print(f"ERROR reading Chrome bookmarks JSON: {e}")
        return []

    print(f"Loaded {len(datasets)} Chrome bookmark datasets (DS-178 to DS-249) - Skipped {duplicate_count} duplicates")
    return datasets

def write_csv(all_datasets, output_path):
    """Write all datasets to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['SOURCE_ID', 'Name', 'Type', 'Source', 'Category', 'Description', 'URL', 'Update_Status'],
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()

        for dataset in all_datasets:
            writer.writerow({
                'SOURCE_ID': dataset['source_id'],
                'Name': dataset['name'],
                'Type': dataset['type'],
                'Source': dataset['source'],
                'Category': dataset['category'],
                'Description': dataset['description'],
                'URL': dataset['url'],
                'Update_Status': dataset['update_status']
            })

def main():
    """Main function to rebuild inventory."""
    print("=" * 80)
    print("Rebuilding sources_inventory.csv with 249 datasets")
    print("=" * 80)

    # Read all dataset sources
    geo_datasets = read_geospatial_csv()  # DS-001 to DS-036 (36 total)
    eia_datasets = read_eia_datasets()     # DS-037 to DS-121 (85 total)
    fgdc_datasets = read_fgdc_datasets()   # DS-122 to DS-168 (47 total)
    maritime_datasets = read_maritime_datasets()  # DS-169 to DS-177 (9 total)
    chrome_datasets = read_chrome_bookmark_datasets()  # DS-178 to DS-249 (72 total)

    # Combine all datasets in order
    all_datasets = (
        geo_datasets +
        eia_datasets +
        fgdc_datasets +
        maritime_datasets +
        chrome_datasets
    )

    # Verify counts
    print("\n" + "=" * 80)
    print("Verification:")
    print(f"  Geospatial (DS-001 to DS-036): {len(geo_datasets)}")
    print(f"  EIA (DS-037 to DS-121): {len(eia_datasets)}")
    print(f"  FGDC (DS-122 to DS-168): {len(fgdc_datasets)}")
    print(f"  Maritime (DS-169 to DS-177): {len(maritime_datasets)}")
    print(f"  Chrome Bookmarks (DS-178 to DS-249): {len(chrome_datasets)}")
    print(f"  Total: {len(all_datasets)}")
    print("=" * 80)

    if len(all_datasets) != 249:
        print(f"ERROR: Expected 249 datasets, got {len(all_datasets)}")
        return False

    # Write to CSV
    output_path = "G:\\My Drive\\LLM\\sources_data_maps\\_build_documents\\sources_inventory.csv"
    write_csv(all_datasets, output_path)

    # Verify output
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\nOutput CSV created: {output_path}")
    print(f"  Header row + {len(lines) - 1} data rows = {len(lines)} total rows")

    # Verify sequential IDs
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        ids = [row['SOURCE_ID'] for row in reader]

    expected_ids = [format_source_id(i) for i in range(1, 250)]
    if ids == expected_ids:
        print("  All SOURCE_IDs are sequential and correct!")
    else:
        print("  ERROR: SOURCE_IDs are not sequential!")
        missing = set(expected_ids) - set(ids)
        extra = set(ids) - set(expected_ids)
        if missing:
            print(f"    Missing: {sorted(list(missing))[:10]}")
        if extra:
            print(f"    Extra: {sorted(list(extra))[:10]}")
        return False

    print("\n" + "=" * 80)
    print("SUCCESS: sources_inventory.csv has been rebuilt with 249 datasets!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
