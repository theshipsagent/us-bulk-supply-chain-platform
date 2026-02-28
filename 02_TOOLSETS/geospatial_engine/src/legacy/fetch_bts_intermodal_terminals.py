"""
Fetch BTS Intermodal Freight Facilities (TOFC/COFC Rail Terminals) for Louisiana.
Uses ArcGIS REST API to download facility data.
"""
import requests
import json

# BTS Intermodal TOFC/COFC REST API endpoint
API_URL = "https://geo.dot.gov/server/rest/services/Hosted/Intermodal_Freight_Facilities_Rail_TOFC_COFC_DS/FeatureServer/0/query"

# Louisiana bounding box for spatial filter
LA_BBOX = {
    "xmin": -94.0,
    "ymin": 28.9,
    "xmax": -88.8,
    "ymax": 33.0
}

print("Fetching BTS Intermodal TOFC/COFC Terminals for Louisiana...")

# Query parameters
params = {
    "where": "1=1",  # Get all records
    "geometry": f"{LA_BBOX['xmin']},{LA_BBOX['ymin']},{LA_BBOX['xmax']},{LA_BBOX['ymax']}",
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",  # All fields
    "returnGeometry": "true",
    "f": "geojson"
}

try:
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Save as GeoJSON
    output_geojson = "bts_intermodal_tofc_cofc_louisiana.geojson"
    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    feature_count = len(data.get("features", []))
    print(f"\nSuccess! Downloaded {feature_count} intermodal terminals")
    print(f"Saved to: {output_geojson}")

    # Display sample facility info
    if feature_count > 0:
        print("\nSample facilities:")
        for i, feat in enumerate(data["features"][:5], 1):
            props = feat["properties"]
            print(f"  {i}. {props.get('TERMINAL', 'Unknown')} - {props.get('CITY', '')}, {props.get('STATE', '')}")
            print(f"     Railroad: {props.get('RAILROAD', 'Unknown')}")
            print(f"     Services: {props.get('SERVICES', 'Unknown')}")

    # Convert to simple CSV for easy viewing
    import csv

    output_csv = "bts_intermodal_tofc_cofc_louisiana.csv"
    if feature_count > 0:
        features = data["features"]

        # Get all field names
        fieldnames = set()
        for feat in features:
            fieldnames.update(feat["properties"].keys())

        # Add geometry fields
        fieldnames = sorted(fieldnames) + ["latitude", "longitude"]

        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for feat in features:
                row = feat["properties"].copy()
                if feat["geometry"] and feat["geometry"]["type"] == "Point":
                    coords = feat["geometry"]["coordinates"]
                    row["longitude"] = coords[0]
                    row["latitude"] = coords[1]
                else:
                    row["longitude"] = None
                    row["latitude"] = None
                writer.writerow(row)

        print(f"\nAlso saved as CSV: {output_csv}")
        print(f"Fields: {len(fieldnames)}")

    print("\nDone!")

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    exit(1)
