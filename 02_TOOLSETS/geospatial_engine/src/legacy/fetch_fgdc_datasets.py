#!/usr/bin/env python3
"""
Fetch all FGDC datasets from data.gov catalog
"""

import json
import requests
import time
from datetime import datetime

def fetch_all_fgdc_datasets():
    """Fetch all datasets from FGDC organization using data.gov API"""

    base_url = "https://catalog.data.gov/api/3/action/package_search"

    # Parameters for the API call
    params = {
        'fq': 'organization:fgdc-gov',
        'rows': 100,  # Maximum rows per request
        'start': 0
    }

    all_datasets = []

    print("Fetching FGDC datasets from data.gov...")

    # First request to get total count
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print(f"Error: API returned status code {response.status_code}")
        return None

    data = response.json()

    if not data.get('success'):
        print("Error: API request was not successful")
        return None

    total_count = data['result']['count']
    print(f"Total datasets found: {total_count}")

    # Fetch all datasets (pagination if needed)
    while params['start'] < total_count:
        print(f"Fetching datasets {params['start']} to {params['start'] + params['rows']}...")

        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print(f"Error fetching page: {response.status_code}")
            break

        data = response.json()
        results = data['result']['results']

        for dataset in results:
            # Extract key information
            dataset_info = {
                'title': dataset.get('title', ''),
                'name': dataset.get('name', ''),
                'description': dataset.get('notes', ''),
                'url': f"https://catalog.data.gov/dataset/{dataset.get('name', '')}",
                'publisher': dataset.get('publisher', ''),
                'organization': dataset.get('organization', {}).get('title', ''),
                'metadata_created': dataset.get('metadata_created', ''),
                'metadata_modified': dataset.get('metadata_modified', ''),
                'license_title': dataset.get('license_title', ''),
                'license_url': dataset.get('license_url', ''),
                'tags': [tag.get('display_name', '') for tag in dataset.get('tags', [])],
                'resources': []
            }

            # Extract resource information (data formats and URLs)
            for resource in dataset.get('resources', []):
                resource_info = {
                    'name': resource.get('name', ''),
                    'format': resource.get('format', ''),
                    'url': resource.get('url', ''),
                    'description': resource.get('description', '')
                }
                dataset_info['resources'].append(resource_info)

            # Get unique formats
            formats = list(set([r['format'] for r in dataset_info['resources'] if r['format']]))
            dataset_info['formats_available'] = sorted(formats)

            all_datasets.append(dataset_info)

        params['start'] += params['rows']
        time.sleep(0.5)  # Be nice to the API

    print(f"\nSuccessfully fetched {len(all_datasets)} datasets")
    return all_datasets

def save_to_json(datasets, filename):
    """Save datasets to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(datasets, f, indent=2, ensure_ascii=False)
    print(f"Saved to {filename}")

def save_to_markdown(datasets, filename):
    """Save datasets to Markdown catalog"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# FGDC (Federal Geographic Data Committee) Datasets Catalog\n\n")
        f.write(f"**Source:** data.gov - Federal Geographic Data Committee\n\n")
        f.write(f"**Total Datasets:** {len(datasets)}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        for idx, dataset in enumerate(datasets, 1):
            f.write(f"## {idx}. {dataset['title']}\n\n")

            # Description
            if dataset['description']:
                # Truncate very long descriptions
                desc = dataset['description']
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                f.write(f"**Description:** {desc}\n\n")

            # Metadata
            f.write(f"**Publisher:** {dataset.get('publisher', 'N/A')}\n\n")
            f.write(f"**Organization:** {dataset.get('organization', 'Federal Geographic Data Committee')}\n\n")

            # Dates
            if dataset['metadata_created']:
                try:
                    created = datetime.fromisoformat(dataset['metadata_created'].replace('Z', '+00:00'))
                    f.write(f"**Created:** {created.strftime('%Y-%m-%d')}\n\n")
                except:
                    f.write(f"**Created:** {dataset['metadata_created']}\n\n")

            if dataset['metadata_modified']:
                try:
                    modified = datetime.fromisoformat(dataset['metadata_modified'].replace('Z', '+00:00'))
                    f.write(f"**Last Updated:** {modified.strftime('%Y-%m-%d')}\n\n")
                except:
                    f.write(f"**Last Updated:** {dataset['metadata_modified']}\n\n")

            # Formats
            if dataset['formats_available']:
                f.write(f"**Data Formats:** {', '.join(dataset['formats_available'])}\n\n")

            # Tags
            if dataset['tags']:
                f.write(f"**Tags:** {', '.join(dataset['tags'])}\n\n")

            # URLs
            f.write(f"**Dataset URL:** [{dataset['url']}]({dataset['url']})\n\n")

            # Key Resources (limit to important formats)
            important_formats = ['CSV', 'JSON', 'XML', 'Shapefile', 'GeoJSON', 'KML', 'Excel', 'HTML']
            key_resources = [r for r in dataset['resources'] if r['format'] in important_formats]

            if key_resources:
                f.write("**Key Resources:**\n\n")
                for resource in key_resources[:5]:  # Limit to first 5
                    f.write(f"- {resource['format']}: [{resource['name'] or 'Download'}]({resource['url']})\n")

                if len(dataset['resources']) > 5:
                    f.write(f"\n*({len(dataset['resources'])} total resources available)*\n")
                f.write("\n")

            f.write("---\n\n")

    print(f"Saved to {filename}")

if __name__ == "__main__":
    # Fetch all datasets
    datasets = fetch_all_fgdc_datasets()

    if datasets:
        # Save to JSON
        json_file = r"G:\My Drive\LLM\sources_data_maps\fgdc_datasets_complete.json"
        save_to_json(datasets, json_file)

        # Save to Markdown
        md_file = r"G:\My Drive\LLM\sources_data_maps\FGDC_Datasets_Catalog.md"
        save_to_markdown(datasets, md_file)

        print("\n✓ All datasets successfully extracted and saved!")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")
    else:
        print("Failed to fetch datasets")
