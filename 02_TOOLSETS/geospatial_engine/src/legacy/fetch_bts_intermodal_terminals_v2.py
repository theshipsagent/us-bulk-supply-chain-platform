"""
Fetch BTS Intermodal Freight Facilities (TOFC/COFC Rail Terminals) for Louisiana.
Try querying by state attribute instead of spatial filter.
"""
import requests
import json

# BTS Intermodal TOFC/COFC REST API endpoint
API_URL = "https://geo.dot.gov/server/rest/services/Hosted/Intermodal_Freight_Facilities_Rail_TOFC_COFC_DS/FeatureServer/0/query"

print("Fetching BTS Intermodal TOFC/COFC Terminals...")
print("Trying state filter: STATE = 'LA' or STATE = 'Louisiana'")

# First, try to get all terminals to see what states are available
params_all = {
    "where": "1=1",
    "outFields": "STATE",
    "returnGeometry": "false",
    "returnDistinctValues": "true",
    "f": "json"
}

try:
    response = requests.get(API_URL, params=params_all, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "features" in data:
        states = [f["attributes"]["STATE"] for f in data["features"] if f.get("attributes", {}).get("STATE")]
        print(f"\nAvailable states in dataset: {sorted(set(states))[:20]}")

        # Check if LA or Louisiana is in the list
        la_variants = [s for s in states if s and ("LA" in s.upper() or "LOUIS" in s.upper())]
        print(f"Louisiana variants found: {la_variants}")

    # Now try different state filters
    state_filters = [
        "STATE = 'LA'",
        "STATE = 'Louisiana'",
        "STATE LIKE '%LA%'",
        "STATE LIKE '%Louis%'"
    ]

    all_features = []

    for state_filter in state_filters:
        print(f"\nTrying filter: {state_filter}")

        params = {
            "where": state_filter,
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson"
        }

        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        feature_count = len(data.get("features", []))
        print(f"  Found: {feature_count} terminals")

        if feature_count > 0:
            all_features.extend(data["features"])
            break

    # If state filter didn't work, try downloading all and filtering locally
    if len(all_features) == 0:
        print("\nState filters didn't work. Downloading all terminals and filtering locally...")

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson"
        }

        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        total_count = len(data.get("features", []))
        print(f"Total terminals nationwide: {total_count}")

        # Filter to Louisiana by coordinates
        LA_BBOX = {"min_lat": 28.9, "max_lat": 33.0, "min_lng": -94.0, "max_lng": -88.8}

        for feat in data.get("features", []):
            if feat["geometry"] and feat["geometry"]["type"] == "Point":
                coords = feat["geometry"]["coordinates"]
                lng, lat = coords[0], coords[1]
                if (LA_BBOX["min_lat"] <= lat <= LA_BBOX["max_lat"] and
                    LA_BBOX["min_lng"] <= lng <= LA_BBOX["max_lng"]):
                    all_features.append(feat)

        print(f"Louisiana terminals (filtered by coordinates): {len(all_features)}")

    # Save results
    if all_features:
        output_geojson = "bts_intermodal_tofc_cofc_louisiana.geojson"
        geojson_data = {
            "type": "FeatureCollection",
            "features": all_features
        }

        with open(output_geojson, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

        print(f"\nSaved {len(all_features)} terminals to: {output_geojson}")

        # Display sample facilities
        print("\nSample facilities:")
        for i, feat in enumerate(all_features[:5], 1):
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"] if feat["geometry"] else [None, None]
            print(f"  {i}. {props.get('TERMINAL') or props.get('NAME', 'Unknown')}")
            print(f"     Location: {props.get('CITY', '')}, {props.get('STATE', '')} ({coords[1]:.4f}, {coords[0]:.4f})")
            print(f"     Railroad: {props.get('RAILROAD') or props.get('RR_CO', 'Unknown')}")

        # Save as CSV
        import csv
        output_csv = "bts_intermodal_tofc_cofc_louisiana.csv"

        if all_features:
            fieldnames = set()
            for feat in all_features:
                fieldnames.update(feat["properties"].keys())
            fieldnames = sorted(fieldnames) + ["latitude", "longitude"]

            with open(output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for feat in all_features:
                    row = feat["properties"].copy()
                    if feat["geometry"] and feat["geometry"]["type"] == "Point":
                        coords = feat["geometry"]["coordinates"]
                        row["longitude"] = coords[0]
                        row["latitude"] = coords[1]
                    writer.writerow(row)

            print(f"Also saved as CSV: {output_csv}")
    else:
        print("\nNo terminals found for Louisiana!")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    exit(1)
