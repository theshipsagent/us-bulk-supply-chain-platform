"""
Create Simplified National Infrastructure Layers
Simplify rail and pipeline data for web map performance
"""

import json
import geopandas as gpd
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely import simplify

print("="*80)
print("CREATING SIMPLIFIED NATIONAL INFRASTRUCTURE LAYERS")
print("="*80)

# Paths
QGIS_DIR = Path("qgis")
ESRI_DIR = Path("esri_exports")
OUTPUT_DIR = Path("national_supply_chain")

# Simplify rail network
print("\n1. Simplifying Class 1 Rail Network...")
print("   Loading main routes (43MB)...")

try:
    rail_gdf = gpd.read_file(QGIS_DIR / "class1_rail_main_routes.geojson")
    print(f"   Loaded: {len(rail_gdf)} rail segments")

    # Simplify geometry - reduce coordinate precision
    print("   Simplifying geometry...")
    rail_gdf['geometry'] = rail_gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

    # Filter to only include Mississippi Basin + Great Lakes states
    basin_states = ['IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'MN', 'MS', 'MO', 'MT',
                    'ND', 'NE', 'OH', 'OK', 'PA', 'SD', 'TN', 'TX', 'WI', 'WV',
                    'AL', 'AR', 'MI', 'NY', 'GA', 'FL', 'NC', 'SC', 'VA']

    # Bounding box filter for faster processing
    bbox = {
        'minx': -106.0,  # Montana
        'maxx': -75.0,   # Pennsylvania
        'miny': 25.0,    # Louisiana
        'maxy': 49.0     # Minnesota/North Dakota
    }

    rail_filtered = rail_gdf.cx[bbox['minx']:bbox['maxx'], bbox['miny']:bbox['maxy']]
    print(f"   Filtered to study area: {len(rail_filtered)} segments")

    # Save simplified version
    output_rail = OUTPUT_DIR / "rail_network_simplified.geojson"
    rail_filtered.to_file(output_rail, driver='GeoJSON')

    file_size_mb = output_rail.stat().st_size / (1024 * 1024)
    print(f"   OK: Saved simplified rail network")
    print(f"       {len(rail_filtered)} segments, {file_size_mb:.1f}MB")

except Exception as e:
    print(f"   Error: {e}")
    print("   Skipping rail network - will use Mapbox base layer")

# Load product pipelines
print("\n2. Loading Product Pipelines...")
try:
    pipelines = json.load(open(ESRI_DIR / "Product_Pipelines_April_2025.geojson"))
    print(f"   Loaded: {len(pipelines['features'])} pipeline segments")

    # Copy to output
    output_pipelines = OUTPUT_DIR / "pipelines_national.geojson"
    with open(output_pipelines, 'w') as f:
        json.dump(pipelines, f)

    file_size_kb = output_pipelines.stat().st_size / 1024
    print(f"   OK: {len(pipelines['features'])} segments, {file_size_kb:.0f}KB")

except Exception as e:
    print(f"   Error: {e}")

# Also copy HGL and Crude pipelines if they exist
print("\n3. Checking for additional pipeline data...")
for pipeline_type in ['HGL', 'Crude']:
    try:
        filename = f"{pipeline_type}_Pipelines_LA_region.geojson"
        pipeline_file = ESRI_DIR / filename

        if pipeline_file.exists():
            data = json.load(open(pipeline_file))
            output_file = OUTPUT_DIR / f"pipelines_{pipeline_type.lower()}.geojson"
            with open(output_file, 'w') as f:
                json.dump(data, f)
            print(f"   OK: {pipeline_type} pipelines ({len(data['features'])} segments)")
    except Exception as e:
        print(f"   {pipeline_type}: Not found or error")

print("\n" + "="*80)
print("INFRASTRUCTURE SIMPLIFICATION COMPLETE")
print("="*80)
print("\nFiles ready for national map:")
print("  - Rail network (simplified)")
print("  - Product pipelines (national)")
print("  - HGL & Crude pipelines (regional)")
