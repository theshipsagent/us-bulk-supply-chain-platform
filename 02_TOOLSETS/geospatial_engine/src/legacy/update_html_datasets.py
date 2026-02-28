#!/usr/bin/env python3
"""
Update HTML with all datasets from CSV file
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
    js_array = "        const allDatasets = [\n"

    for i, dataset in enumerate(datasets):
        source_id = dataset.get('SOURCE_ID', '').strip()
        name = escape_json_string(dataset.get('Name', ''))
        dtype = escape_json_string(dataset.get('Type', ''))
        source = escape_json_string(dataset.get('Source', ''))
        category = escape_json_string(dataset.get('Category', ''))
        description = escape_json_string(dataset.get('Description', ''))
        url = escape_json_string(dataset.get('URL', ''))
        update_status = escape_json_string(dataset.get('Update_Status', ''))

        js_array += f"""        {{
                "sourceId": "{source_id}",
                "name": "{name}",
                "type": "{dtype}",
                "source": "{source}",
                "category": "{category}",
                "description": "{description}",
                "url": "{url}",
                "updateStatus": "{update_status}"
        }}{'' if i == len(datasets) - 1 else ','}
"""

    js_array += "        ];\n"
    return js_array

def generate_category_options(categories):
    """Generate category filter options"""
    html = '                        <option value="">All Categories</option>\n'
    for category in sorted(categories.keys()):
        if category:
            html += f'                        <option value="{category}">{category}</option>\n'
    return html

def generate_source_options(sources):
    """Generate source filter options"""
    html = '                        <option value="">All Sources</option>\n'
    for source in sorted(sources.keys()):
        if source:
            html += f'                        <option value="{source}">{source}</option>\n'
    return html

def generate_type_options(types):
    """Generate type filter options"""
    html = '                        <option value="">All Types</option>\n'
    for dtype in sorted(types.keys()):
        if dtype:
            html += f'                        <option value="{dtype}">{dtype}</option>\n'
    return html

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

    # Calculate top categories, sources, types
    top_categories = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)
    top_sources = sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)
    top_types = sorted(stats['types'].items(), key=lambda x: x[1], reverse=True)

    # Update stat cards - look for pattern and replace
    # Find and replace the first stat number (total datasets)
    stat_pattern = r'<div class="stat-number">\d+</div>\s*<div class="stat-label">Total Datasets</div>'
    stat_replacement = f'<div class="stat-number">{stats["total"]}</div>\n                <div class="stat-label">Total Datasets</div>'
    html_content = re.sub(stat_pattern, stat_replacement, html_content, count=1)

    # Update category dropdown options
    category_options = generate_category_options(stats['categories'])
    start_marker = '<select id="categoryFilter">'
    end_marker = '</select>'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find(end_marker, start_idx)
        if end_idx > start_idx:
            html_content = html_content[:start_idx] + '\n' + category_options + '                        ' + html_content[end_idx:]

    # Update source dropdown options
    source_options = generate_source_options(stats['sources'])
    start_marker = '<select id="sourceFilter">'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find('</select>', start_idx)
        if end_idx > start_idx:
            html_content = html_content[:start_idx] + '\n' + source_options + '                        ' + html_content[end_idx:]

    # Update type dropdown options
    type_options = generate_type_options(stats['types'])
    start_marker = '<select id="typeFilter">'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find('</select>', start_idx)
        if end_idx > start_idx:
            html_content = html_content[:start_idx] + '\n' + type_options + '                        ' + html_content[end_idx:]

    # Generate new dataset array
    new_dataset_array = generate_dataset_json_array(datasets)

    # Find and replace the existing dataset array
    # Match from 'const allDatasets = [' to '];'
    pattern = r'const allDatasets = \[[\s\S]*?\];'
    html_content = re.sub(pattern, new_dataset_array.strip() + ';', html_content, count=1)

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

if __name__ == '__main__':
    main()
