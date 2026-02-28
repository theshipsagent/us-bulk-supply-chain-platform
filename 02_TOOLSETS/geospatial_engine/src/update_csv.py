import json
import csv
from datetime import datetime
import re

def extract_source(description, organization):
    """Extract source agency from description or use organization"""
    if not description:
        return organization if organization else 'Bureau of Transportation Statistics'

    # Common patterns in descriptions
    patterns = [
        r'from the ([^(]+) \(',
        r'by the ([^(]+) \(',
        r'updated by ([^,]+),',
        r'compiled by ([^,]+),',
    ]

    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            agency = match.group(1).strip()
            # Clean up common abbreviations
            if agency == 'Federal Highway Administration':
                return 'Federal Highway Administration (FHWA)'
            elif agency == 'Federal Aviation Administration':
                return 'Federal Aviation Administration (FAA)'
            elif agency == 'Federal Railroad Administration':
                return 'Federal Railroad Administration (FRA)'
            elif agency == 'Bureau of Transportation Statistics':
                return 'Bureau of Transportation Statistics (BTS)'
            elif 'Army Corp of Engineers' in agency or 'USACE' in agency:
                return 'U.S. Army Corps of Engineers (USACE)'
            return agency

    # Default to organization or BTS
    return organization if organization else 'Bureau of Transportation Statistics'

def categorize_dataset(title, description, tags):
    """Determine category based on title, description, and tags"""
    title_lower = title.lower()
    desc_lower = description.lower() if description else ''

    # Handle tags - they might be strings or dicts
    if isinstance(tags, list):
        tags_lower = ' '.join([
            tag.get('display_name', '') if isinstance(tag, dict) else str(tag)
            for tag in tags
        ]).lower()
    else:
        tags_lower = ''

    combined = title_lower + ' ' + desc_lower + ' ' + tags_lower

    # Category mapping logic - order matters, more specific first
    if any(word in combined for word in ['bridge', 'tunnel']):
        return 'Bridges & Structures'
    elif any(word in combined for word in ['airport', 'aviation', 'runway', 'heliport', 'flight']):
        return 'Aviation'
    elif any(word in combined for word in ['rail', 'railroad', 'railway', 'amtrak', 'grade crossing', 'milepost']) and 'trail' not in combined:
        return 'Rail'
    elif any(word in combined for word in ['trail', 'hiking', 'walking']) and 'rail' in combined:
        return 'Rail Trails'
    elif any(word in combined for word in ['trail', 'hiking', 'walking']):
        return 'Trails & Recreation'
    elif any(word in combined for word in ['port', 'maritime', 'vessel', 'waterway', 'navigation', 'channel', 'lock', 'dock', 'navigable']):
        return 'Maritime & Waterways'
    elif any(word in combined for word in ['transit', 'bus', 'subway', 'public transport', 'passenger']):
        return 'Transit'
    elif any(word in combined for word in ['freight', 'cargo', 'commodity', 'truck']):
        return 'Freight'
    elif any(word in combined for word in ['highway', 'road', 'pavement', 'traffic']):
        return 'Transportation Infrastructure'
    elif any(word in combined for word in ['border', 'crossing', 'customs']):
        return 'Border Infrastructure'
    elif any(word in combined for word in ['geospatial', 'gis', 'metadata', 'coordinate', 'projection', 'schema', 'standard', 'ngda']):
        return 'Geospatial Standards'
    elif any(word in combined for word in ['multimodal', 'intermodal']):
        return 'Intermodal'
    else:
        return 'Transportation Infrastructure'

def get_update_status(metadata_modified):
    """Parse metadata_modified to determine update status"""
    try:
        mod_date = datetime.fromisoformat(metadata_modified.replace('Z', '+00:00'))
        year = mod_date.year
        month = mod_date.strftime('%B')

        if year >= 2024:
            return 'Current'
        else:
            return f'Updated {month} {year}'
    except:
        return 'Current'

def truncate_description(desc, max_length=200):
    """Truncate description to max length"""
    if not desc or desc == '{{description}}':
        return ''
    if len(desc) <= max_length:
        return desc
    return desc[:max_length].rsplit(' ', 1)[0] + '...'

# Read the JSON file
with open('fgdc_datasets_complete.json', 'r', encoding='utf-8') as f:
    datasets = json.load(f)

print(f'Processing {len(datasets)} datasets...')

# Read existing CSV
csv_file = '_build_documents/sources_inventory.csv'
with open(csv_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    existing_rows = list(reader)

# Get the last SOURCE_ID to determine starting number
if existing_rows:
    last_id = existing_rows[-1]['SOURCE_ID']
    start_num = int(last_id.split('-')[1]) + 1
else:
    start_num = 1

print(f'Starting from DS-{start_num:03d}')

# Prepare new CSV rows
csv_rows = []
for idx, dataset in enumerate(datasets, start=start_num):
    source_id = f'DS-{idx:03d}'

    # Get formats
    formats = dataset.get('formats_available', [])
    type_str = ', '.join(formats) if formats else 'Multiple'

    # Get source/publisher
    org_data = dataset.get('organization', {})
    org_title = org_data.get('title', '') if isinstance(org_data, dict) else org_data if org_data else ''

    source = extract_source(
        dataset.get('description', ''),
        org_title
    )

    # Determine category
    category = categorize_dataset(
        dataset.get('title', ''),
        dataset.get('description', ''),
        dataset.get('tags', [])
    )

    # Get description
    description = truncate_description(dataset.get('description', ''))

    # Get update status
    update_status = get_update_status(dataset.get('metadata_modified', ''))

    row = {
        'SOURCE_ID': source_id,
        'Name': dataset.get('title', ''),
        'Type': type_str,
        'Source': source,
        'Category': category,
        'Description': description,
        'URL': dataset.get('url', ''),
        'Update_Status': update_status
    }

    csv_rows.append(row)

# Append new rows to CSV file
with open(csv_file, 'a', newline='', encoding='utf-8') as f:
    fieldnames = ['SOURCE_ID', 'Name', 'Type', 'Source', 'Category', 'Description', 'URL', 'Update_Status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    for row in csv_rows:
        writer.writerow(row)

print(f'Successfully appended {len(csv_rows)} datasets to {csv_file}')
print(f'Total rows now in CSV: {len(existing_rows) + len(csv_rows) + 1} (including header)')
print(f'New range: DS-{start_num:03d} to DS-{start_num + len(csv_rows) - 1:03d}')
