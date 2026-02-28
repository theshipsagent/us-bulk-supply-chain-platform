"""
Fetch National EPA FRS Facilities - All States
Then filter for industrial anchor facilities
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

# All 50 states + DC + territories
ALL_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

# Mississippi River Basin + major industrial states (prioritize these)
PRIORITY_STATES = [
    'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'MN', 'MS', 'MO', 'MT',
    'ND', 'NE', 'OH', 'OK', 'PA', 'SD', 'TN', 'TX', 'WI', 'WV',
    'AL', 'AR', 'MI', 'NY'
]

# Industrial facility keywords in facility names
INDUSTRIAL_KEYWORDS = [
    'STEEL', 'MILL', 'FOUNDRY', 'SMELTER', 'REFINERY', 'PETROLEUM',
    'CEMENT', 'CONCRETE', 'GRAIN', 'ELEVATOR', 'TERMINAL', 'FERTILIZER',
    'CHEMICAL', 'PLANT', 'AGGREGATE', 'QUARRY', 'MINING', 'ALUMINUM',
    'COPPER', 'IRON', 'METALS', 'PROCESSING', 'MANUFACTURING',
    'ADM', 'CARGILL', 'BUNGE', 'CHS', 'NUCOR', 'ARCELORMITTAL',
    'US STEEL', 'EXXON', 'SHELL', 'VALERO', 'MARATHON', 'CHEVRON',
    'LAFARGE', 'HOLCIM', 'MARTIN MARIETTA', 'VULCAN', 'MOSAIC'
]

def fetch_state_facilities(state_code):
    """Fetch all EPA FRS facilities for a state"""
    facilities = []

    try:
        # Query EPA FRS by state
        url = f"{API_BASE}/STATE_CODE/{state_code}/ROWS/0:10000/JSON"
        response = requests.get(url, timeout=90)

        if response.status_code == 200:
            data = response.json()

            if data and len(data) > 0:
                for facility in data:
                    if facility.get('LATITUDE83') and facility.get('LONGITUDE83'):
                        facilities.append({
                            'registry_id': facility.get('REGISTRY_ID', ''),
                            'facility_name': facility.get('PRIMARY_NAME', '').upper(),
                            'address': facility.get('LOCATION_ADDRESS', ''),
                            'city': facility.get('CITY_NAME', ''),
                            'state': facility.get('STATE_CODE', ''),
                            'county': facility.get('COUNTY_NAME', ''),
                            'zip': facility.get('POSTAL_CODE', ''),
                            'lat': float(facility.get('LATITUDE83')),
                            'lng': float(facility.get('LONGITUDE83')),
                            'naics_code': facility.get('NAICS_CODES', ''),
                            'sic_code': facility.get('SIC_CODES', ''),
                            'frs_programs': facility.get('PGM_SYS_ACRNMS', ''),
                            'federal_facility': facility.get('FEDERAL_FACILITY_INDICATOR', '')
                        })

        return facilities

    except Exception as e:
        print(f"    Error: {e}")
        return []

def is_industrial_facility(facility):
    """Check if facility matches industrial anchor criteria"""
    name = facility['facility_name']

    # Check for industrial keywords
    for keyword in INDUSTRIAL_KEYWORDS:
        if keyword in name:
            return True

    # Check for specific program affiliations
    programs = facility.get('frs_programs', '')
    if any(prog in programs for prog in ['TRI', 'RMP', 'NPDES', 'RCRA']):
        return True

    return False

def main():
    print("="*80)
    print("FETCHING NATIONAL EPA FRS FACILITIES")
    print("All Industrial Facilities - State by State")
    print("="*80)

    all_facilities = []
    state_summary = {}

    # Process priority states first
    print("\nProcessing PRIORITY STATES (Mississippi Basin + Industrial)...")
    for i, state in enumerate(PRIORITY_STATES, 1):
        print(f"  [{i}/{len(PRIORITY_STATES)}] {state}...", end=" ", flush=True)

        facilities = fetch_state_facilities(state)

        if facilities:
            all_facilities.extend(facilities)
            state_summary[state] = len(facilities)
            print(f"OK ({len(facilities)} facilities)")
        else:
            print("No data")

        time.sleep(1)  # Rate limiting

    print(f"\n  Priority states total: {len(all_facilities)} facilities")

    # Save initial dataset
    print("\n" + "="*80)
    print("FILTERING FOR INDUSTRIAL ANCHORS")
    print("="*80)

    industrial_facilities = [f for f in all_facilities if is_industrial_facility(f)]

    print(f"  Total facilities: {len(all_facilities)}")
    print(f"  Industrial anchors: {len(industrial_facilities)}")
    print(f"  Filter rate: {len(industrial_facilities)/len(all_facilities)*100:.1f}%")

    # Save filtered industrial facilities
    output_file = OUTPUT_DIR / "national_industrial_facilities.csv"

    if industrial_facilities:
        fieldnames = ['registry_id', 'facility_name', 'address', 'city', 'state',
                     'county', 'zip', 'lat', 'lng', 'naics_code', 'sic_code',
                     'frs_programs', 'federal_facility']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(industrial_facilities)

        print(f"\nOK: Saved to {output_file}")
        print(f"    {len(industrial_facilities)} facilities")
    else:
        print("\nNo facilities found!")
        return

    # Category breakdown
    print("\n" + "="*80)
    print("FACILITY TYPE BREAKDOWN")
    print("="*80)

    type_counts = {}
    for keyword in ['STEEL', 'REFINERY', 'CEMENT', 'GRAIN', 'FERTILIZER',
                    'CHEMICAL', 'ALUMINUM', 'TERMINAL']:
        count = sum(1 for f in industrial_facilities if keyword in f['facility_name'])
        if count > 0:
            type_counts[keyword] = count

    for fac_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {fac_type}: {count}")

    # Geographic distribution
    print("\n" + "="*80)
    print("GEOGRAPHIC DISTRIBUTION - Top 15 States")
    print("="*80)

    state_ind_counts = {}
    for fac in industrial_facilities:
        state = fac['state']
        if state not in state_ind_counts:
            state_ind_counts[state] = 0
        state_ind_counts[state] += 1

    sorted_states = sorted(state_ind_counts.items(), key=lambda x: x[1], reverse=True)
    for state, count in sorted_states[:15]:
        print(f"  {state}: {count} facilities")

    print("\n" + "="*80)
    print("NATIONAL EPA FRS FETCH COMPLETE!")
    print("="*80)
    print("\nNext: Fetch remaining 26 states for complete national coverage")

if __name__ == "__main__":
    main()
