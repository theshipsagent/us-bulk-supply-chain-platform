#!/usr/bin/env python3
"""Test script to count records in all JSON files."""

import json

files = {
    'eia_datasets_complete.json': r"G:\My Drive\LLM\sources_data_maps\eia_datasets_complete.json",
    'fgdc_datasets_complete.json': r"G:\My Drive\LLM\sources_data_maps\fgdc_datasets_complete.json",
    'maritime_usace_noaa_datasets.json': r"G:\My Drive\LLM\sources_data_maps\maritime_usace_noaa_datasets.json",
    'chrome_bookmarks_datasets.json': r"G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_datasets.json",
}

total = 0
for name, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Count non-duplicate entries
    if isinstance(data, list):
        count = len(data)
        duplicates = sum(1 for item in data if item.get('is_duplicate', False))
        unique = count - duplicates
        print(f"{name:40} - Total: {count:3d}, Duplicates: {duplicates:2d}, Unique: {unique:3d}")
        total += unique
    else:
        print(f"{name:40} - Not a list")

print(f"\nTotal unique records across all JSON files: {total}")
print(f"Expected: 85 + 47 + 9 + 72 = {85 + 47 + 9 + 72}")
