"""
Fetch National Industrial Anchors - High-tonnage Bulk Commodity Facilities
Fetches major steel mills, refineries, cement plants, smelters nationwide
"""

import requests
import json
import time
import csv
from pathlib import Path

# EPA FRS API endpoint
API_BASE = "https://data.epa.gov/efservice/V_FAC_PROGRAM_FACILITY"

# Output directory
OUTPUT_DIR = Path("01_geospatial/EPA_FRS")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Major industrial facility types by NAICS code
FACILITY_TYPES = {
    'steel_mills': {
        'naics': ['331110', '331111', '331112', '331210', '331221', '331222'],  # Iron, steel mills, foundries
        'description': 'Steel Mills & Iron Foundries'
    },
    'smelters': {
        'naics': ['331313', '331314', '331315', '331410', '331420', '331491', '331492'],  # Aluminum, copper, other smelters
        'description': 'Aluminum & Nonferrous Metal Smelters'
    },
    'refineries': {
        'naics': ['324110', '324121', '324122', '324191', '324199'],  # Petroleum refineries, asphalt
        'description': 'Petroleum Refineries & Processing'
    },
    'cement': {
        'naics': ['327310', '327320', '327331', '327332'],  # Cement, ready-mix concrete
        'description': 'Cement Plants & Concrete Manufacturing'
    },
    'grain_processors': {
        'naics': ['311211', '311212', '311213', '311221', '311222', '311223'],  # Flour mills, rice, malt, soybean
        'description': 'Grain Mills & Processors'
    },
    'aggregate': {
        'naics': ['212321', '212322', '212323', '212324', '212325'],  # Sand, gravel, crushed stone
        'description': 'Aggregate & Mining Operations'
    },
    'fertilizer': {
        'naics': ['325311', '325312', '325314'],  # Nitrogen, phosphate, fertilizer
        'description': 'Fertilizer & Agricultural Chemical Plants'
    }
}

def fetch_facilities_by_naics(naics_codes, facility_type):
    """Fetch facilities by NAICS code from EPA FRS"""
    all_facilities = []

    print(f"\nFetching {facility_type}...")
    print(f"  NAICS codes: {', '.join(naics_codes)}")

    for naics in naics_codes:
        print(f"  Querying NAICS {naics}...", end=" ", flush=True)

        try:
            # EPA FRS API query by NAICS code
            url = f"{API_BASE}/NAICS_CODE/{naics}/ROWS/0:5000/JSON"
            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                data = response.json()

                if data and len(data) > 0:
                    # Filter for facilities with coordinates
                    for facility in data:
                        if facility.get('LATITUDE83') and facility.get('LONGITUDE83'):
                            all_facilities.append({
                                'registry_id': facility.get('REGISTRY_ID', ''),
                                'facility_name': facility.get('PRIMARY_NAME', ''),
                                'address': facility.get('LOCATION_ADDRESS', ''),
                                'city': facility.get('CITY_NAME', ''),
                                'state': facility.get('STATE_CODE', ''),
                                'county': facility.get('COUNTY_NAME', ''),
                                'zip': facility.get('POSTAL_CODE', ''),
                                'lat': float(facility.get('LATITUDE83')),
                                'lng': float(facility.get('LONGITUDE83')),
                                'naics_code': naics,
                                'facility_type': facility_type,
                                'frs_programs': facility.get('PGM_SYS_ACRNMS', '')
                            })

                    print(f"OK ({len([f for f in all_facilities if f['naics_code'] == naics])} facilities)")
                else:
                    print("No results")
            else:
                print(f"Error {response.status_code}")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"Error: {e}")
            continue

    return all_facilities

def main():
    print("="*80)
    print("FETCHING NATIONAL INDUSTRIAL ANCHORS")
    print("High-Tonnage Bulk Commodity Facilities")
    print("="*80)

    all_facilities = []
    summary = {}

    # Fetch each facility type
    for type_key, type_info in FACILITY_TYPES.items():
        facilities = fetch_facilities_by_naics(type_info['naics'], type_info['description'])
        all_facilities.extend(facilities)
        summary[type_info['description']] = len(facilities)
        print(f"  Total {type_info['description']}: {len(facilities)}")

    # Remove duplicates (same facility may have multiple NAICS codes)
    unique_facilities = {}
    for fac in all_facilities:
        reg_id = fac['registry_id']
        if reg_id not in unique_facilities:
            unique_facilities[reg_id] = fac
        else:
            # Keep the one with more program affiliations
            if len(fac['frs_programs']) > len(unique_facilities[reg_id]['frs_programs']):
                unique_facilities[reg_id] = fac

    facilities_list = list(unique_facilities.values())

    print("\n" + "="*80)
    print("SUMMARY - National Industrial Anchors")
    print("="*80)
    for fac_type, count in summary.items():
        print(f"  {fac_type}: {count}")
    print(f"\nTotal facilities (before dedup): {len(all_facilities)}")
    print(f"Unique facilities: {len(facilities_list)}")

    # Save to CSV
    output_file = OUTPUT_DIR / "national_industrial_anchors.csv"

    if facilities_list:
        fieldnames = ['registry_id', 'facility_name', 'facility_type', 'address', 'city',
                     'state', 'county', 'zip', 'lat', 'lng', 'naics_code', 'frs_programs']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(facilities_list)

        print(f"\nOK: Saved to {output_file}")
        print(f"    {len(facilities_list)} facilities")
    else:
        print("\nNo facilities found!")

    # Geographic distribution
    print("\n" + "="*80)
    print("GEOGRAPHIC DISTRIBUTION - Top 15 States")
    print("="*80)

    state_counts = {}
    for fac in facilities_list:
        state = fac['state']
        if state not in state_counts:
            state_counts[state] = 0
        state_counts[state] += 1

    sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
    for state, count in sorted_states[:15]:
        print(f"  {state}: {count} facilities")

    print("\n" + "="*80)
    print("NATIONAL INDUSTRIAL ANCHORS FETCH COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
