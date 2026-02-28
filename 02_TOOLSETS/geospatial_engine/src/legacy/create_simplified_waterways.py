"""
Create Simplified Waterway Network for National Map
Extract and simplify major rivers only
"""

import geopandas as gpd
import json
from pathlib import Path

print("="*80)
print("CREATING SIMPLIFIED WATERWAY NETWORK")
print("="*80)

# Major waterways to include
MAJOR_WATERWAYS = [
    'Mississippi River',
    'Ohio River',
    'Illinois River',
    'Missouri River',
    'Tennessee River',
    'Arkansas River',
    'Cumberland River',
    'White River',
    'Monongahela River',
    'Allegheny River',
    'Tennessee-Tombigbee',
    'Detroit River',
    'St. Clair River',
    'Calumet',
    'Illinois Waterway'
]

OUTPUT_DIR = Path("national_supply_chain")

print("\nLoading USACE waterway network...")
try:
    waterways_gdf = gpd.read_file("qgis/usace_waterway_network_lines_ALL.geojson")
    print(f"  Loaded: {len(waterways_gdf)} waterway segments")

    # Filter for major waterways
    print("\nFiltering for major waterways...")

    def is_major_waterway(name):
        if not name or str(name) == 'nan':
            return False
        name_upper = str(name).upper()
        for major in MAJOR_WATERWAYS:
            if major.upper() in name_upper:
                return True
        return False

    # Filter by waterway name or river name
    def check_waterway(row):
        waterway = str(row.get('WATERWAY', ''))
        rivername = str(row.get('RIVERNAME', ''))
        combined = (waterway + ' ' + rivername).upper()

        for major in MAJOR_WATERWAYS:
            if major.upper() in combined:
                return True
        return False

    major_waterways = waterways_gdf[waterways_gdf.apply(check_waterway, axis=1)]
    print(f"  Filtered: {len(major_waterways)} segments")

    if len(major_waterways) == 0:
        print(f"  No matches found, using bounding box filter instead...")
        bbox = {
            'minx': -106.0,
            'maxx': -75.0,
            'miny': 25.0,
            'maxy': 49.0
        }
        major_waterways = waterways_gdf.cx[bbox['minx']:bbox['maxx'], bbox['miny']:bbox['maxy']]
        print(f"  Filtered by bounding box: {len(major_waterways)} segments")

    # Simplify geometry
    print("\nSimplifying geometry...")
    major_waterways['geometry'] = major_waterways['geometry'].simplify(tolerance=0.005, preserve_topology=True)

    # Save
    output_file = OUTPUT_DIR / "waterways_major.geojson"
    major_waterways.to_file(output_file, driver='GeoJSON')

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\nOK: Saved simplified waterways")
    print(f"    {len(major_waterways)} segments, {file_size_mb:.1f}MB")

except Exception as e:
    print(f"Error with USACE data: {e}")
    print("\nTrying BTS waterway network...")

    try:
        waterways_gdf = gpd.read_file("01_geospatial/09_bts_waterway_networks/Waterway_Networks_3525269991148215733.geojson")
        print(f"  Loaded: {len(waterways_gdf)} waterway segments")

        # Filter by bounding box
        bbox = {
            'minx': -106.0,
            'maxx': -75.0,
            'miny': 25.0,
            'maxy': 49.0
        }

        major_waterways = waterways_gdf.cx[bbox['minx']:bbox['maxx'], bbox['miny']:bbox['maxy']]
        print(f"  Filtered: {len(major_waterways)} segments")

        # Simplify
        major_waterways['geometry'] = major_waterways['geometry'].simplify(tolerance=0.01, preserve_topology=True)

        # Save
        output_file = OUTPUT_DIR / "waterways_major.geojson"
        major_waterways.to_file(output_file, driver='GeoJSON')

        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\nOK: Saved simplified waterways")
        print(f"    {len(major_waterways)} segments, {file_size_mb:.1f}MB")

    except Exception as e2:
        print(f"Error with BTS data: {e2}")

print("\n" + "="*80)
print("WATERWAY SIMPLIFICATION COMPLETE")
print("="*80)
