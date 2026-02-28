"""
Upload GeoJSON layers to ArcGIS Online
SESCO Cement Project - December 2025

Usage:
    python upload_to_arcgis.py --username YOUR_USERNAME --password YOUR_PASSWORD

Or set environment variables:
    set ARCGIS_USERNAME=your_username
    set ARCGIS_PASSWORD=your_password
    python upload_to_arcgis.py
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime

# Configuration
ARCGIS_ORG_URL = "https://www.arcgis.com"
GEOSPATIAL_DIR = r"G:\My Drive\LLM\project_cement\geospatial"

# Layers to upload
LAYERS_TO_UPLOAD = [
    {
        "filename": "north_american_cement_plants.geojson",
        "title": "North American Cement Plants",
        "description": "158 cement plants in US (100), Canada (20), and Mexico (38). Source: Global Energy Monitor Cement Tracker July 2025.",
        "tags": ["cement", "manufacturing", "plants", "North America", "SESCO", "infrastructure"],
        "snippet": "Cement manufacturing plants across North America with capacity data"
    },
    {
        "filename": "us_cement_import_ports_weighted.geojson",
        "title": "US Cement Import Ports (Weighted)",
        "description": "24 US ports with cement import volumes. Bubble size represents import volume. Total: ~12.3M MT. Source: Panjiva Trade Intelligence 2023-2025.",
        "tags": ["cement", "imports", "ports", "trade", "SESCO", "shipping"],
        "snippet": "US cement import ports with volume-weighted symbology"
    },
    {
        "filename": "class1_rail_part1.geojson",
        "title": "Class I Rail Network (US)",
        "description": "Class I railroad network segments for BNSF, UP, CSX, NS, CN, CPKC. Source: BTS National Transportation Atlas Database 2025.",
        "tags": ["rail", "railroad", "transportation", "infrastructure", "Class I", "SESCO"],
        "snippet": "Major Class I freight railroad network in the United States"
    },
    {
        "filename": "us_marine_highways.geojson",
        "title": "US Marine Highways",
        "description": "35 designated marine highway corridors representing navigable inland and coastal waterways. Source: BTS NTAD 2025.",
        "tags": ["marine", "waterways", "shipping", "transportation", "infrastructure", "SESCO"],
        "snippet": "Navigable marine highway corridors for bulk cargo shipping"
    }
]


def get_token(username, password):
    """Get ArcGIS Online authentication token."""
    token_url = f"{ARCGIS_ORG_URL}/sharing/rest/generateToken"
    params = {
        'username': username,
        'password': password,
        'referer': ARCGIS_ORG_URL,
        'f': 'json'
    }

    response = requests.post(token_url, data=params)
    result = response.json()

    if 'token' in result:
        print(f"[OK] Authentication successful")
        return result['token']
    else:
        print(f"[ERROR] Authentication failed: {result.get('error', {}).get('message', 'Unknown error')}")
        return None


def upload_geojson(token, username, layer_config):
    """Upload a GeoJSON file to ArcGIS Online."""
    filepath = os.path.join(GEOSPATIAL_DIR, layer_config['filename'])

    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {layer_config['filename']}")
        return None

    # Read the GeoJSON file
    with open(filepath, 'r', encoding='utf-8') as f:
        geojson_data = f.read()

    file_size = os.path.getsize(filepath)
    print(f"\n[UPLOAD] {layer_config['title']}")
    print(f"         File: {layer_config['filename']} ({file_size/1024:.1f} KB)")

    # Add item to ArcGIS Online
    add_url = f"{ARCGIS_ORG_URL}/sharing/rest/content/users/{username}/addItem"

    # Prepare item parameters
    item_params = {
        'token': token,
        'f': 'json',
        'type': 'GeoJson',
        'title': layer_config['title'],
        'description': layer_config['description'],
        'snippet': layer_config['snippet'],
        'tags': ','.join(layer_config['tags']),
        'accessInformation': 'SESCO Cement Corp / GEM / Panjiva / BTS NTAD',
        'licenseInfo': 'For internal use',
    }

    # Upload as multipart form data
    files = {
        'file': (layer_config['filename'], geojson_data, 'application/json')
    }

    response = requests.post(add_url, data=item_params, files=files)
    result = response.json()

    if result.get('success'):
        item_id = result.get('id')
        print(f"         [OK] Uploaded successfully")
        print(f"         Item ID: {item_id}")

        # Publish as hosted feature layer
        publish_result = publish_feature_layer(token, username, item_id, layer_config['title'])

        return {
            'item_id': item_id,
            'publish_result': publish_result
        }
    else:
        error_msg = result.get('error', {}).get('message', 'Unknown error')
        print(f"         [ERROR] Upload failed: {error_msg}")
        return None


def publish_feature_layer(token, username, item_id, title):
    """Publish a GeoJSON item as a hosted feature layer."""
    publish_url = f"{ARCGIS_ORG_URL}/sharing/rest/content/users/{username}/publish"

    publish_params = {
        'token': token,
        'f': 'json',
        'itemId': item_id,
        'filetype': 'geojson',
        'publishParameters': json.dumps({
            'name': title.replace(' ', '_').replace('(', '').replace(')', ''),
            'layerInfo': {'capabilities': 'Query'}
        })
    }

    response = requests.post(publish_url, data=publish_params)
    result = response.json()

    if result.get('services'):
        service = result['services'][0]
        service_id = service.get('serviceItemId')
        service_url = service.get('serviceurl')
        print(f"         [OK] Published as Feature Layer")
        print(f"         Service ID: {service_id}")
        return {
            'service_id': service_id,
            'service_url': service_url
        }
    else:
        error_msg = result.get('error', {}).get('message', 'Unknown error')
        # Check if it's a "name already exists" error
        if 'already exists' in str(error_msg).lower():
            print(f"         [WARN] Feature layer name already exists - using existing")
        else:
            print(f"         [WARN] Publish failed: {error_msg}")
        return None


def share_item(token, username, item_id, share_level='org'):
    """Share an item with organization or public."""
    share_url = f"{ARCGIS_ORG_URL}/sharing/rest/content/users/{username}/items/{item_id}/share"

    share_params = {
        'token': token,
        'f': 'json',
        'everyone': 'true' if share_level == 'public' else 'false',
        'org': 'true' if share_level in ['org', 'public'] else 'false',
    }

    response = requests.post(share_url, data=share_params)
    return response.json()


def main():
    parser = argparse.ArgumentParser(description='Upload GeoJSON layers to ArcGIS Online')
    parser.add_argument('--username', '-u', help='ArcGIS Online username')
    parser.add_argument('--password', '-p', help='ArcGIS Online password')
    parser.add_argument('--share', '-s', choices=['private', 'org', 'public'], default='org',
                        help='Sharing level (default: org)')
    args = parser.parse_args()

    # Get credentials
    username = args.username or os.environ.get('ARCGIS_USERNAME')
    password = args.password or os.environ.get('ARCGIS_PASSWORD')

    if not username or not password:
        print("=" * 60)
        print("ArcGIS Online Upload Script")
        print("=" * 60)
        print("\nCredentials required. Provide via:")
        print("  --username and --password arguments")
        print("  or ARCGIS_USERNAME and ARCGIS_PASSWORD environment variables")
        print("\nExample:")
        print("  python upload_to_arcgis.py -u myuser -p mypass")
        return

    print("=" * 60)
    print("ArcGIS Online Layer Upload")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Authenticate
    token = get_token(username, password)
    if not token:
        return

    # Upload each layer
    results = []
    for layer in LAYERS_TO_UPLOAD:
        result = upload_geojson(token, username, layer)
        if result:
            results.append({
                'layer': layer['title'],
                'filename': layer['filename'],
                **result
            })

    # Summary
    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)

    for r in results:
        print(f"\n{r['layer']}:")
        print(f"  File: {r['filename']}")
        print(f"  Item ID: {r.get('item_id', 'N/A')}")
        if r.get('publish_result'):
            print(f"  Service ID: {r['publish_result'].get('service_id', 'N/A')}")

    # Save results to file
    output_file = os.path.join(GEOSPATIAL_DIR, 'arcgis_upload_results.json')
    with open(output_file, 'w') as f:
        json.dump({
            'upload_date': datetime.now().isoformat(),
            'layers': results
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
