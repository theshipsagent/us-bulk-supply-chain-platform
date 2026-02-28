"""
Fetch EPA FRS facility data for Louisiana using the FRS REST API.
Since the API requires 2 parameters with state, we'll fetch by major parishes/cities.
"""
import requests
import json
import time
from collections import defaultdict

# Louisiana parishes with major industrial activity
LA_PARISHES = [
    "East Baton Rouge",
    "West Baton Rouge",
    "Iberville",
    "Ascension",
    "St. James",
    "St. John the Baptist",
    "St. Charles",
    "Jefferson",
    "Orleans",
    "Plaquemines",
    "St. Bernard",
    "Tangipahoa",
    "Livingston",
    "St. Tammany",
    "Calcasieu",
    "Lafayette",
    "Terrebonne",
    "Lafourche",
    "Vermilion",
    "Iberia",
    "St. Mary",
    "Assumption",
    "Pointe Coupee",
    "Concordia",
    "Madison",
    "Tensas"
]

API_BASE = "https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities"

all_facilities = []
seen_registry_ids = set()

print(f"Fetching EPA FRS facilities for Louisiana...")
print(f"Querying {len(LA_PARISHES)} parishes...\n")

for i, parish in enumerate(LA_PARISHES, 1):
    print(f"[{i}/{len(LA_PARISHES)}] Fetching {parish} Parish...")

    params = {
        "state_abbr": "LA",
        "county_name": parish,
        "output": "JSON"
    }

    try:
        response = requests.get(API_BASE, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Check if we got results
        if "Results" in data and "FRSFacility" in data["Results"]:
            facilities = data["Results"]["FRSFacility"]

            # Handle single result (returns dict) vs multiple (returns list)
            if isinstance(facilities, dict):
                facilities = [facilities]

            # Deduplicate based on RegistryId
            new_count = 0
            for fac in facilities:
                reg_id = fac.get("RegistryId")
                if reg_id and reg_id not in seen_registry_ids:
                    seen_registry_ids.add(reg_id)
                    all_facilities.append(fac)
                    new_count += 1

            print(f"  Found {len(facilities)} facilities ({new_count} new, {len(facilities)-new_count} duplicates)")
        else:
            print(f"  No facilities found")

        # Be nice to the API
        time.sleep(0.5)

    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        continue

print(f"\n{'='*60}")
print(f"Total unique facilities: {len(all_facilities)}")
print(f"{'='*60}\n")

# Save raw JSON
output_json = "epa_frs_louisiana_facilities.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_facilities, f, indent=2)
print(f"OK Saved raw JSON: {output_json}")

# Convert to simplified CSV format
import csv

output_csv = "epa_frs_louisiana_facilities.csv"
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    if all_facilities:
        # Get all possible field names
        all_fields = set()
        for fac in all_facilities:
            all_fields.update(fac.keys())

        fieldnames = sorted(all_fields)

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_facilities)

        print(f"OK Saved CSV: {output_csv}")
        print(f"  Rows: {len(all_facilities)}")
        print(f"  Columns: {len(fieldnames)}")

# Print statistics
print(f"\n{'='*60}")
print("Dataset Statistics:")
print(f"{'='*60}")

# Count by parish
parish_counts = defaultdict(int)
for fac in all_facilities:
    county = fac.get("CountyName", "Unknown")
    parish_counts[county] += 1

print("\nTop 10 Parishes by Facility Count:")
for parish, count in sorted(parish_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {parish:30s}: {count:4d}")

# Count facilities with coordinates
with_coords = sum(1 for fac in all_facilities
                  if fac.get("Latitude83") and fac.get("Longitude83"))
print(f"\nFacilities with coordinates: {with_coords}/{len(all_facilities)} ({100*with_coords/len(all_facilities):.1f}%)")

print("\nDONE: EPA FRS Louisiana data fetch complete!")
