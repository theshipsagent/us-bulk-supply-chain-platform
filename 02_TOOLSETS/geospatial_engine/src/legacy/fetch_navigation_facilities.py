"""
Fetch navigation facility data from Marine Cadastre and process existing BTS data.
"""
import requests
import json
import zipfile
import os
import glob

print("="*60)
print("Fetching Navigation Facility Data")
print("="*60)

# Step 1: Download Marine Cadastre Anchorages
print("\n1. Downloading Marine Cadastre Anchorages...")
anchorage_url = "https://marinecadastre.gov/downloads/data/mc/Anchorage.zip"

try:
    response = requests.get(anchorage_url, timeout=60)
    response.raise_for_status()

    # Save zip file
    zip_path = "marinecadastre_anchorages.zip"
    with open(zip_path, "wb") as f:
        f.write(response.content)

    print(f"  Downloaded: {len(response.content)} bytes")

    # Extract zip
    extract_dir = "marinecadastre_anchorages"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f"  Extracted to: {extract_dir}/")

    # List extracted files
    files = os.listdir(extract_dir)
    shapefiles = [f for f in files if f.endswith('.shp')]
    print(f"  Shapefiles found: {shapefiles}")

    # Try to read shapefile using ogr2ogr to convert to GeoJSON
    if shapefiles:
        for shp in shapefiles:
            shp_path = os.path.join(extract_dir, shp)
            geojson_path = shp.replace('.shp', '.geojson')

            # Use ogr2ogr if available, otherwise note for manual conversion
            print(f"\n  Converting {shp} to GeoJSON...")
            try:
                import subprocess
                result = subprocess.run(
                    ["ogr2ogr", "-f", "GeoJSON", geojson_path, shp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"    OK: {geojson_path}")
                else:
                    print(f"    Note: ogr2ogr not available or failed")
                    print(f"    Shapefile ready at: {shp_path}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print(f"    Note: ogr2ogr not available")
                print(f"    Shapefile ready at: {shp_path}")

except Exception as e:
    print(f"  Error downloading anchorages: {e}")

# Step 2: Check for existing BTS dock/navigation data
print("\n2. Checking for existing BTS navigation data...")

bts_paths = [
    "01_geospatial/01_bts_docks",
    "01_geospatial/04_bts_locks",
    "01_geospatial/05_bts_navigation_fac",
    "01_geospatial/08_bts_principal_ports"
]

for path in bts_paths:
    if os.path.exists(path):
        print(f"\n  Found: {path}/")
        files = glob.glob(f"{path}/*.*")
        for f in files[:5]:  # Show first 5 files
            size = os.path.getsize(f)
            print(f"    - {os.path.basename(f)} ({size:,} bytes)")
        if len(files) > 5:
            print(f"    ... and {len(files)-5} more files")
    else:
        print(f"  Not found: {path}/")

# Step 3: Attempt to fetch NOAA ATON (Aids to Navigation) for Louisiana
print("\n3. Fetching NOAA Aids to Navigation for Louisiana...")

aton_url = "https://coast.noaa.gov/arcgismc/rest/services/hosted/atons/featureserver/0/query"

# Louisiana bounding box
LA_BBOX = {
    "xmin": -94.0,
    "ymin": 28.9,
    "xmax": -88.8,
    "ymax": 33.0
}

params = {
    "where": "1=1",
    "geometry": f"{LA_BBOX['xmin']},{LA_BBOX['ymin']},{LA_BBOX['xmax']},{LA_BBOX['ymax']}",
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson"
}

try:
    response = requests.get(aton_url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    feature_count = len(data.get("features", []))

    if feature_count > 0:
        output_file = "noaa_aton_louisiana.geojson"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"  Downloaded {feature_count} navigation aids")
        print(f"  Saved to: {output_file}")

        # Show sample
        if feature_count > 0:
            print("\n  Sample aids:")
            for i, feat in enumerate(data["features"][:5], 1):
                props = feat["properties"]
                name = props.get("aidname") or props.get("name", "Unknown")
                aid_type = props.get("type") or props.get("aidtype", "Unknown")
                print(f"    {i}. {name} ({aid_type})")
    else:
        print("  No navigation aids found in Louisiana bounding box")

except Exception as e:
    print(f"  Error fetching NOAA ATON: {e}")

print("\n" + "="*60)
print("Navigation Data Fetch Complete!")
print("="*60)
print("\nSummary:")
print("  1. Marine Cadastre anchorages downloaded")
print("  2. Existing BTS data checked")
print("  3. NOAA navigation aids fetched")
