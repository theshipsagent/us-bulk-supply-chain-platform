"""
Build National Supply Chain Infrastructure Map
Mississippi River Basin + Great Lakes Industrial Network
"""

import json
import csv
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Paths
BTS_NAV_DIR = Path("01_geospatial/05_bts_navigation_fac/split_by_type/by_fac_type")
OUTPUT_DIR = Path("national_supply_chain")
OUTPUT_DIR.mkdir(exist_ok=True)

# Industrial facility keywords for filtering
INDUSTRIAL_KEYWORDS = [
    'STEEL', 'MILL', 'SMELTER', 'REFINERY', 'PETROLEUM', 'CRUDE', 'OIL',
    'CEMENT', 'CONCRETE', 'GRAIN', 'ELEVATOR', 'TERMINAL', 'FERTILIZER',
    'CHEMICAL', 'PLANT', 'AGGREGATE', 'QUARRY', 'COAL', 'PETCOKE',
    'ALUMINUM', 'COPPER', 'IRON', 'METALS', 'ADM', 'CARGILL', 'BUNGE',
    'CHS', 'NUCOR', 'ARCELORMITTAL', 'US STEEL', 'EXXON', 'SHELL',
    'VALERO', 'MARATHON', 'CHEVRON', 'PHILLIPS', 'LAFARGE', 'HOLCIM',
    'MARTIN MARIETTA', 'VULCAN', 'MOSAIC', 'CF INDUSTRIES', 'YARA',
    'BASF', 'DOW', 'DUPONT', 'EASTMAN', 'HUNTSMAN', 'WESTLAKE',
    'ENERGY TRANSFER', 'KINDER MORGAN', 'ENTERPRISE', 'MAGELLAN'
]

# Facility type keywords
FACILITY_TYPES = {
    'STEEL_MILL': ['STEEL', 'MILL', 'FOUNDRY', 'IRON WORKS', 'NUCOR', 'US STEEL', 'ARCELORMITTAL'],
    'SMELTER': ['SMELTER', 'ALUMINUM', 'COPPER REFINING', 'ZINC'],
    'REFINERY': ['REFINERY', 'PETROLEUM', 'CRUDE OIL', 'EXXON', 'SHELL', 'VALERO', 'MARATHON', 'CHEVRON', 'PHILLIPS'],
    'GRAIN_ELEVATOR': ['GRAIN', 'ELEVATOR', 'ADM', 'CARGILL', 'BUNGE', 'CHS', 'GAVILON', 'LOUIS DREYFUS'],
    'CEMENT': ['CEMENT', 'LAFARGE', 'HOLCIM'],
    'AGGREGATE': ['AGGREGATE', 'QUARRY', 'MARTIN MARIETTA', 'VULCAN', 'GRAVEL', 'STONE'],
    'FERTILIZER': ['FERTILIZER', 'MOSAIC', 'CF INDUSTRIES', 'YARA', 'NUTRIEN', 'KOCH'],
    'CHEMICAL': ['CHEMICAL', 'BASF', 'DOW', 'DUPONT', 'EASTMAN', 'HUNTSMAN', 'WESTLAKE', 'SASOL'],
    'COAL_TERMINAL': ['COAL', 'PETCOKE'],
    'PIPELINE_TERMINAL': ['PIPELINE', 'ENERGY TRANSFER', 'KINDER MORGAN', 'ENTERPRISE', 'MAGELLAN', 'PLAINS'],
    'TANK_TERMINAL': ['TANK TERMINAL', 'STORAGE', 'TANK FARM', 'IMTT', 'NuSTAR', 'BUCKEYE']
}

def classify_facility_type(facility_name):
    """Classify facility by primary type"""
    name_upper = facility_name.upper()

    # Check each type in priority order
    for fac_type, keywords in FACILITY_TYPES.items():
        for keyword in keywords:
            if keyword in name_upper:
                return fac_type

    return 'GENERAL_CARGO'

def is_industrial_facility(facility_name):
    """Check if facility is an industrial anchor"""
    name_upper = facility_name.upper()

    for keyword in INDUSTRIAL_KEYWORDS:
        if keyword in name_upper:
            return True

    return False

def load_bts_docks(region_name, file_path):
    """Load BTS dock facilities from CSV"""
    facilities = []

    try:
        df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)

        for idx, row in df.iterrows():
            # Get coordinates
            lat = row.get('LATITUDE', None)
            lng = row.get('LONGITUDE', None)

            if pd.isna(lat) or pd.isna(lng):
                continue

            try:
                lat = float(lat)
                lng = float(lng)
            except (ValueError, TypeError):
                continue

            # Get facility info
            facility_name = str(row.get('NAV_UNIT_NAME', row.get('Facility', 'Unknown')))

            # Only include industrial facilities
            if not is_industrial_facility(facility_name):
                continue

            facility_type = classify_facility_type(facility_name)

            facilities.append({
                'name': facility_name,
                'facility_type': facility_type,
                'lat': lat,
                'lng': lng,
                'region': region_name,
                'waterway': str(row.get('WTWY_NAME', '')),
                'city': str(row.get('CITY_OR_TOWN', row.get('CITY', ''))),
                'state': str(row.get('STATE', '')),
                'source': 'BTS_DOCK',
                'dock_type': str(row.get('FAC_TYPE', '')),
                'commodities': str(row.get('COMMODITIES', ''))
            })

    except Exception as e:
        print(f"    Error loading {file_path}: {e}")

    return facilities

def main():
    print("="*80)
    print("BUILDING NATIONAL SUPPLY CHAIN INFRASTRUCTURE MAP")
    print("Mississippi River Basin + Great Lakes Industrial Network")
    print("="*80)

    all_facilities = []

    # Load Inland Ports (Mississippi River system)
    print("\nLoading Inland Waterway System...")
    print("  Inland Ports (Mississippi, Ohio, Illinois, Arkansas, Tennessee)...")
    inland_docks = load_bts_docks('Inland_Ports',
                                  BTS_NAV_DIR / 'Inland_Ports' / 'Dock.csv')
    all_facilities.extend(inland_docks)
    print(f"    Industrial facilities: {len(inland_docks)}")

    # Load Great Lakes
    print("  Great Lakes (Chicago, Detroit, Cleveland, Buffalo)...")
    greatlakes_docks = load_bts_docks('Great_Lakes',
                                       BTS_NAV_DIR / 'Great_Lakes' / 'Dock.csv')
    all_facilities.extend(greatlakes_docks)
    print(f"    Industrial facilities: {len(greatlakes_docks)}")

    print(f"\n  Total industrial facilities: {len(all_facilities)}")

    # Facility type breakdown
    print("\n" + "="*80)
    print("FACILITY TYPE BREAKDOWN")
    print("="*80)

    type_counts = defaultdict(int)
    for fac in all_facilities:
        type_counts[fac['facility_type']] += 1

    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    for fac_type, count in sorted_types:
        print(f"  {fac_type.replace('_', ' ').title()}: {count}")

    # Geographic distribution
    print("\n" + "="*80)
    print("GEOGRAPHIC DISTRIBUTION - Top 20 States")
    print("="*80)

    state_counts = defaultdict(int)
    for fac in all_facilities:
        state = fac['state']
        if state and state != 'nan':
            state_counts[state] += 1

    sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
    for state, count in sorted_states[:20]:
        print(f"  {state}: {count} facilities")

    # Waterway distribution
    print("\n" + "="*80)
    print("MAJOR WATERWAYS - Top 15 by Industrial Facilities")
    print("="*80)

    waterway_counts = defaultdict(int)
    for fac in all_facilities:
        wtwy = fac['waterway']
        if wtwy and wtwy != 'nan' and len(wtwy) > 5:
            waterway_counts[wtwy] += 1

    sorted_waterways = sorted(waterway_counts.items(), key=lambda x: x[1], reverse=True)
    for waterway, count in sorted_waterways[:15]:
        # Truncate long waterway names
        wtwy_display = waterway[:60] + '...' if len(waterway) > 60 else waterway
        print(f"  {count:4d}: {wtwy_display}")

    # Save to CSV
    print("\n" + "="*80)
    print("SAVING NATIONAL FACILITY REGISTRY")
    print("="*80)

    output_csv = OUTPUT_DIR / "national_industrial_facilities.csv"

    fieldnames = ['name', 'facility_type', 'lat', 'lng', 'region', 'waterway',
                  'city', 'state', 'source', 'dock_type', 'commodities']

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_facilities)

    print(f"  OK: {output_csv}")
    print(f"      {len(all_facilities)} facilities")

    # Save to GeoJSON for mapping
    print("\n  Creating GeoJSON...")

    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for fac in all_facilities:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [fac['lng'], fac['lat']]
            },
            "properties": {
                "name": fac['name'],
                "facility_type": fac['facility_type'],
                "region": fac['region'],
                "waterway": fac['waterway'],
                "city": fac['city'],
                "state": fac['state'],
                "commodities": fac['commodities'][:200] if fac['commodities'] else ''
            }
        }
        geojson['features'].append(feature)

    output_geojson = OUTPUT_DIR / "national_industrial_facilities.geojson"
    with open(output_geojson, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)

    print(f"  OK: {output_geojson}")

    # Create facility type GeoJSONs
    print("\n  Creating facility type layers...")
    for fac_type in type_counts.keys():
        if type_counts[fac_type] >= 10:  # Only create layers with 10+ facilities
            type_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [f['lng'], f['lat']]},
                        "properties": {
                            "name": f['name'],
                            "waterway": f['waterway'],
                            "city": f['city'],
                            "state": f['state']
                        }
                    }
                    for f in all_facilities if f['facility_type'] == fac_type
                ]
            }

            output_file = OUTPUT_DIR / f"facilities_{fac_type.lower()}.geojson"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(type_geojson, f)

            print(f"    {fac_type}: {len(type_geojson['features'])} facilities")

    print("\n" + "="*80)
    print("NATIONAL SUPPLY CHAIN MAP - DATA READY!")
    print("="*80)
    print(f"\nNext: Build interactive map with:")
    print(f"  - {len(all_facilities)} industrial facilities")
    print(f"  - {len(type_counts)} facility types")
    print(f"  - {len(state_counts)} states")
    print(f"  - Mississippi River Basin + Great Lakes networks")

if __name__ == "__main__":
    main()
