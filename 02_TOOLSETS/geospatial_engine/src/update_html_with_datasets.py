#!/usr/bin/env python3
"""
Update HTML with all 249 datasets from corrected CSV file
"""

import csv
import json
from pathlib import Path

# File paths
csv_path = Path(r"G:\My Drive\LLM\sources_data_maps\_build_documents\sources_inventory.csv")
html_input_path = Path(r"G:\My Drive\LLM\sources_data_maps\_html_web_files\data_sources_index.html")
html_output_path = Path(r"G:\My Drive\LLM\sources_data_maps\_html_web_files\data_sources_index.html")

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
        category = dataset.get('Category', 'Uncategorized')
        stats['categories'][category] = stats['categories'].get(category, 0) + 1

        # Count sources
        source = dataset.get('Source', 'Unknown')
        stats['sources'][source] = stats['sources'].get(source, 0) + 1

        # Count types
        dtype = dataset.get('Type', 'Unknown')
        stats['types'][dtype] = stats['types'].get(dtype, 0) + 1

    return stats

def escape_json_string(s):
    """Escape string for JSON"""
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    return s

def generate_dataset_array(datasets):
    """Generate JavaScript array of datasets"""
    js_array = "const allDatasets = [\n"

    for i, dataset in enumerate(datasets):
        source_id = dataset.get('SOURCE_ID', f'DS-{i+1:03d}')
        name = escape_json_string(dataset.get('Name', ''))
        dtype = escape_json_string(dataset.get('Type', ''))
        source = escape_json_string(dataset.get('Source', ''))
        category = escape_json_string(dataset.get('Category', ''))
        description = escape_json_string(dataset.get('Description', ''))
        url = escape_json_string(dataset.get('URL', ''))
        update_status = escape_json_string(dataset.get('Update_Status', ''))

        js_array += f"""    {{
        id: "{source_id}",
        name: "{name}",
        type: "{dtype}",
        source: "{source}",
        category: "{category}",
        description: "{description}",
        url: "{url}",
        updateStatus: "{update_status}"
    }}{'' if i == len(datasets) - 1 else ','}
"""

    js_array += "];\n"
    return js_array

def generate_category_options(categories):
    """Generate category filter options"""
    html = '                        <option value="">All Categories</option>\n'
    for category in sorted(categories.keys()):
        if category and category != 'Uncategorized':
            html += f'                        <option value="{category}">{category}</option>\n'
    return html

def generate_source_options(sources):
    """Generate source filter options"""
    html = '                        <option value="">All Sources</option>\n'
    for source in sorted(sources.keys()):
        if source and source != 'Unknown':
            html += f'                        <option value="{source}">{source}</option>\n'
    return html

def generate_type_options(types):
    """Generate type filter options"""
    html = '                        <option value="">All Types</option>\n'
    for dtype in sorted(types.keys()):
        if dtype and dtype != 'Unknown':
            html += f'                        <option value="{dtype}">{dtype}</option>\n'
    return html

def update_html(datasets, stats):
    """Update HTML file with new datasets and stats"""

    # Read the original HTML
    with open(html_input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Calculate top categories, sources, types
    top_categories = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:3]
    top_sources = sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)[:3]
    top_types = sorted(stats['types'].items(), key=lambda x: x[1], reverse=True)[:3]

    # Update header description
    html_content = html_content.replace(
        '<p>Interactive Data Sources Browser - 211 Datasets</p>',
        f'<p>Interactive Data Sources Browser - {stats["total"]} Datasets</p>'
    )

    # Update stats cards
    # Find and replace total datasets stat
    html_content = html_content.replace(
        '<div class="stat-number">211</div>',
        f'<div class="stat-number">{stats["total"]}</div>'
    )

    # Update category stat (should be most common category count)
    if top_categories:
        cat_count = top_categories[0][1]
        html_content = html_content.replace(
            '<div class="stat-number">38</div>\n                <div class="stat-label">Top Category</div>',
            f'<div class="stat-number">{cat_count}</div>\n                <div class="stat-label">Top Category</div>'
        )

    # Update source stat
    if top_sources:
        src_count = top_sources[0][1]
        html_content = html_content.replace(
            '<div class="stat-number">42</div>\n                <div class="stat-label">Top Source</div>',
            f'<div class="stat-number">{src_count}</div>\n                <div class="stat-label">Top Source</div>'
        )

    # Update type stat
    if top_types:
        type_count = top_types[0][1]
        html_content = html_content.replace(
            '<div class="stat-number">85</div>\n                <div class="stat-label">Top Type</div>',
            f'<div class="stat-number">{type_count}</div>\n                <div class="stat-label">Top Type</div>'
        )

    # Update category dropdown options
    category_options = generate_category_options(stats['categories'])
    # Find the category select and replace options
    start_marker = '<select id="categoryFilter">'
    end_marker = '</select>'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find(end_marker, start_idx)
        html_content = html_content[:start_idx] + '\n' + category_options + '                        ' + html_content[end_idx:]

    # Update source dropdown options
    source_options = generate_source_options(stats['sources'])
    start_marker = '<select id="sourceFilter">'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find('</select>', start_idx)
        html_content = html_content[:start_idx] + '\n' + source_options + '                        ' + html_content[end_idx:]

    # Update type dropdown options
    type_options = generate_type_options(stats['types'])
    start_marker = '<select id="typeFilter">'
    if start_marker in html_content:
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find('</select>', start_idx)
        html_content = html_content[:start_idx] + '\n' + type_options + '                        ' + html_content[end_idx:]

    # Generate and embed the datasets array
    dataset_array = generate_dataset_array(datasets)

    # Find the location to insert the dataset array (before the script tag that uses it)
    script_start = html_content.find('<script>')
    if script_start != -1:
        # Insert the dataset array before the script tag
        html_content = html_content[:script_start] + '<script>\n' + dataset_array + '\n    ' + html_content[script_start + 8:]

    return html_content

def main():
    print("Reading CSV file...")
    datasets = read_csv_datasets()
    print(f"Found {len(datasets)} datasets")

    print("Generating statistics...")
    stats = generate_stats(datasets)
    print(f"Categories: {len(stats['categories'])}")
    print(f"Sources: {len(stats['sources'])}")
    print(f"Types: {len(stats['types'])}")

    print("Updating HTML...")
    updated_html = update_html(datasets, stats)

    print("Writing updated HTML file...")
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    file_size = html_output_path.stat().st_size
    print(f"HTML file updated successfully!")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    # Verify
    print("\n=== VERIFICATION ===")
    with open(html_output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        dataset_count = content.count('"id": "DS-')
        print(f"Datasets embedded in HTML: {dataset_count}")
        print(f"CSV datasets count: {len(datasets)}")
        print(f"Match: {dataset_count == len(datasets)}")

if __name__ == '__main__':
    main()
