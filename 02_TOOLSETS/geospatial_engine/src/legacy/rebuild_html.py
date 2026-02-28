#!/usr/bin/env python3
"""
Rebuild HTML by removing duplicate dataset arrays and creating a clean single array
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

def escape_json_string(s):
    """Escape string for JSON"""
    if not s:
        return ""
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def generate_dataset_array_js(datasets):
    """Generate the dataset array JavaScript"""
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

# Read the HTML file
print("Reading HTML file...")
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find first occurrence of 'const allDatasets = [' and last occurrence of '];'
# We'll remove everything from first array to last array and put in a single clean one

# Find the start of first const allDatasets
first_start = html_content.find('const allDatasets = [')
if first_start == -1:
    print("ERROR: Could not find 'const allDatasets = [' in HTML")
    exit(1)

# Find the last occurrence of '];' after some number of lines (this should be the end of all arrays)
# We need to find where the last dataset ends
# Look for the pattern of the last dataset we know about
last_closing = html_content.rfind('];', 0, first_start + 1000000)  # Look in first part
if last_closing == -1:
    print("ERROR: Could not find closing ];")
    exit(1)

# Actually, we need to find all occurrences of "];
closing_positions = []
pos = 0
while True:
    pos = html_content.find('];', pos + 1)
    if pos == -1:
        break
    closing_positions.append(pos)

print(f"Found {len(closing_positions)} occurrences of ];")
print(f"First array start: {first_start}")
print(f"Possible closing positions: {closing_positions[-5:] if len(closing_positions) > 5 else closing_positions}")

# The dataset arrays should end before the JavaScript functions
# Look for "function" keyword which should come after the arrays
function_start = html_content.find('function ', first_start)
print(f"First function definition at: {function_start}")

# The last ]; before the first function should be the end of our datasets
for closing_pos in reversed(closing_positions):
    if closing_pos < function_start:
        last_end = closing_pos + 2  # Include the ];
        break
else:
    print("ERROR: Could not find appropriate ]; before functions")
    exit(1)

print(f"Will replace from {first_start} to {last_end}")
print(f"Content being replaced: {html_content[first_start:first_start+100]}...{html_content[last_end-100:last_end]}")

# Read CSV and generate new array
print("\nReading CSV file...")
datasets = read_csv_datasets()
print(f"Found {len(datasets)} datasets")

print("Generating new array...")
new_array = generate_dataset_array_js(datasets)

# Replace the old arrays with the new one
print("Replacing arrays in HTML...")
html_content = html_content[:first_start] + new_array + html_content[last_end:]

# Update the header and stats
print("Updating header...")
html_content = re.sub(
    r'<p>Interactive Data Sources Browser - \d+ Datasets</p>',
    f'<p>Interactive Data Sources Browser - {len(datasets)} Datasets</p>',
    html_content
)

# Write the new HTML
print("Writing updated HTML...")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

file_size = html_path.stat().st_size
print(f"\nHTML file updated!")
print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

# Verify
print("\n=== VERIFICATION ===")
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()
    dataset_count = content.count('"sourceId": "DS-')
    print(f"Datasets embedded: {dataset_count}")
    print(f"CSV datasets: {len(datasets)}")
    print(f"Match: {dataset_count == len(datasets)}")

    # Count array declarations
    array_count = content.count('const allDatasets = [')
    print(f"Array declarations: {array_count}")
