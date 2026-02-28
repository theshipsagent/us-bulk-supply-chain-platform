#!/usr/bin/env python3
"""
Update HTML with all datasets from CSV file - Final version
"""

import csv
import re
from pathlib import Path

# File paths
csv_path = Path(r"G:\My Drive\LLM\sources_data_maps\_build_documents\sources_inventory.csv")
html_path = Path(r"G:\My Drive\LLM\sources_data_maps\_html_web_files\data_sources_index.html")

def read_csv_datasets():
    """Read all datasets from CSV file"""
    datasets = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            datasets.append(row)
    return datasets

def generate_stats(datasets):
    """Generate statistics from datasets"""
    stats = {
        'total': len(datasets),
        'categories': {},
        'sources': {},
        'types': {}
    }

    for dataset in datasets:
        # Count categories
        category = dataset.get('Category', 'Uncategorized').strip()
        if category:
            stats['categories'][category] = stats['categories'].get(category, 0) + 1

        # Count sources
        source = dataset.get('Source', 'Unknown').strip()
        if source:
            stats['sources'][source] = stats['sources'].get(source, 0) + 1

        # Count types
        dtype = dataset.get('Type', 'Unknown').strip()
        if dtype:
            stats['types'][dtype] = stats['types'].get(dtype, 0) + 1

    return stats

def escape_json_string(s):
    """Escape string for JSON"""
    if not s:
        return ""
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    # Clean up multiple spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def generate_dataset_json_array(datasets):
    """Generate JavaScript array of datasets in JSON format"""
    lines = ["const allDatasets = ["]

    for i, dataset in enumerate(datasets):
        source_id = dataset.get('SOURCE_ID', '').strip()
        name = escape_json_string(dataset.get('Name', ''))
        dtype = escape_json_string(dataset.get('Type', ''))
        source = escape_json_string(dataset.get('Source', ''))
        category = escape_json_string(dataset.get('Category', ''))
        description = escape_json_string(dataset.get('Description', ''))
        url = escape_json_string(dataset.get('URL', ''))
        update_status = escape_json_string(dataset.get('Update_Status', ''))

        comma = "," if i < len(datasets) - 1 else ""
        lines.append(f"""        {{
                "sourceId": "{source_id}",
                "name": "{name}",
                "type": "{dtype}",
                "source": "{source}",
                "category": "{category}",
                "description": "{description}",
                "url": "{url}",
                "updateStatus": "{update_status}"
        }}{comma}""")

    lines.append("];")
    return "\n".join(lines)

def update_html(datasets, stats):
    """Update HTML file with new datasets and stats"""

    # Read the original HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Update header description
    html_content = re.sub(
        r'<p>Interactive Data Sources Browser - \d+ Datasets</p>',
        f'<p>Interactive Data Sources Browser - {stats["total"]} Datasets</p>',
        html_content
    )

    # Generate new dataset array
    new_dataset_array = generate_dataset_json_array(datasets)

    # Find the first 'const allDatasets = [' and replace until the matching ];
    # This is the main data array that will be used
    start_pattern = r'const allDatasets = \['
    match = re.search(start_pattern, html_content)

    if match:
        start_pos = match.start()
        # Find the matching closing ]; after this point
        bracket_count = 0
        in_string = False
        escape_next = False
        pos = match.end() - 1  # Start from the opening bracket

        for i in range(pos, len(html_content)):
            char = html_content[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the matching ];
                        end_pos = i + 1
                        if i + 1 < len(html_content) and html_content[i + 1] == ';':
                            end_pos = i + 2

                        # Replace the entire array
                        html_content = html_content[:start_pos] + new_dataset_array + html_content[end_pos:]
                        break

    return html_content

def main():
    print("Reading CSV file...")
    datasets = read_csv_datasets()
    print(f"Found {len(datasets)} datasets")

    # Verify dataset IDs
    ids = [d.get('SOURCE_ID', '').strip() for d in datasets]
    min_id = min(ids)
    max_id = max(ids)
    print(f"SOURCE_ID range: {min_id} to {max_id}")

    print("Generating statistics...")
    stats = generate_stats(datasets)
    print(f"Categories: {len(stats['categories'])}")
    print(f"Sources: {len(stats['sources'])}")
    print(f"Types: {len(stats['types'])}")

    print("Updating HTML...")
    updated_html = update_html(datasets, stats)

    print("Writing updated HTML file...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    file_size = html_path.stat().st_size
    print(f"HTML file updated successfully!")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    # Verify
    print("\n=== VERIFICATION ===")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        dataset_count = content.count('"sourceId": "DS-')
        print(f"Datasets embedded in HTML: {dataset_count}")
        print(f"CSV datasets count: {len(datasets)}")
        print(f"Match: {dataset_count == len(datasets)}")

        # Check for header description
        if f"Datasets</p>" in content:
            match = re.search(r'(\d+) Datasets</p>', content)
            if match:
                print(f"Header shows: {match.group(1)} Datasets")

        # List first and last dataset IDs
        ds_ids = re.findall(r'"sourceId": "([^"]+)"', content)
        if ds_ids:
            print(f"First dataset ID: {ds_ids[0]}")
            print(f"Last dataset ID: {ds_ids[-1]}")

if __name__ == '__main__':
    main()
