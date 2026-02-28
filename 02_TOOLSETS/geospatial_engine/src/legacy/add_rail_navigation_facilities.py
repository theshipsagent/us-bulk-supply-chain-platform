"""
Add rail yards, product terminals, and refineries to the master facility registry.
Links these datasets to existing MRTIS anchor facilities using spatial matching.
"""
import json
import csv
import math
from difflib import SequenceMatcher

# ── File paths ──
MASTER_FACILITIES = r"G:\My Drive\LLM\sources_data_maps\master_facilities.csv"
EXISTING_LINKS = r"G:\My Drive\LLM\sources_data_maps\facility_dataset_links.csv"
RAIL_YARDS = r"G:\My Drive\LLM\sources_data_maps\esri_exports\Rail_Yards_Louisiana_v2_labels.geojson"
PRODUCT_TERMINALS = r"G:\My Drive\LLM\sources_data_maps\esri_exports\Product_Terminals_October_2025.geojson"
REFINERIES = r"G:\My Drive\LLM\sources_data_maps\esri_exports\Refineries_October_2025.geojson"
OUTPUT_LINKS = r"G:\My Drive\LLM\sources_data_maps\facility_dataset_links.csv"

# ── Configuration ──
MATCH_RADIUS_METERS = 3000  # 3km search radius
NAME_SIMILARITY_THRESHOLD = 0.6

# Louisiana bounding box (to filter national datasets)
LA_BBOX = {
    "min_lat": 28.9,
    "max_lat": 33.0,
    "min_lng": -94.0,
    "max_lng": -88.8
}

# ── Helper functions ──

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def fuzzy_similarity(str1, str2):
    """Calculate similarity ratio between two strings (0-1)."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()

def normalize_name(name):
    """Normalize facility name for matching."""
    if not name:
        return ""
    name = name.upper()
    replacements = {
        " LLC": "", " INC": "", " CORP": "", " CORPORATION": "",
        " LTD": "", " LP": "", " L.P.": "", " CO.": "", " CO": "",
        ",": "", ".": "", "  ": " "
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()

def in_louisiana(lat, lng):
    """Check if coordinates are in Louisiana bounding box."""
    return (LA_BBOX["min_lat"] <= lat <= LA_BBOX["max_lat"] and
            LA_BBOX["min_lng"] <= lng <= LA_BBOX["max_lng"])

# ── Load existing master facilities ──
print("Loading master facilities...")
anchor_facilities = []
with open(MASTER_FACILITIES, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["lat"] = float(row["lat"])
        row["lng"] = float(row["lng"])
        anchor_facilities.append(row)
print(f"  Loaded {len(anchor_facilities)} anchor facilities")

# ── Load existing links ──
print("\nLoading existing dataset links...")
existing_links = []
with open(EXISTING_LINKS, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    existing_links = list(reader)
print(f"  Loaded {len(existing_links)} existing links")

new_links = []
match_stats = {
    "rail_yards": {"total": 0, "high": 0, "medium": 0, "low": 0},
    "product_terminals": {"total": 0, "high": 0, "medium": 0, "low": 0},
    "refineries": {"total": 0, "high": 0, "medium": 0, "low": 0}
}

# ── Process Rail Yards ──
print("\n" + "="*60)
print("Processing Rail Yards...")
print("="*60)

with open(RAIL_YARDS, "r", encoding="utf-8") as f:
    rail_data = json.load(f)

print(f"Total rail yards: {len(rail_data['features'])}")

for feat in rail_data["features"]:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]

    rail_lat = coords[1]
    rail_lng = coords[0]
    rail_name = props.get("YARDNAME", "")
    rail_owner = props.get("RROWNER1", "")

    # Match to anchor facilities
    for anchor in anchor_facilities:
        distance = haversine_distance(anchor["lat"], anchor["lng"], rail_lat, rail_lng)

        if distance <= MATCH_RADIUS_METERS:
            similarity = fuzzy_similarity(
                normalize_name(anchor["canonical_name"]),
                normalize_name(rail_name)
            )

            # Determine confidence
            if distance < 500 and similarity > 0.8:
                confidence = "HIGH"
                match_stats["rail_yards"]["high"] += 1
            elif distance < 1500 and similarity > 0.6:
                confidence = "MEDIUM"
                match_stats["rail_yards"]["medium"] += 1
            elif distance <= MATCH_RADIUS_METERS:
                confidence = "LOW"
                match_stats["rail_yards"]["low"] += 1
            else:
                continue

            match_stats["rail_yards"]["total"] += 1

            link = {
                "facility_id": anchor["facility_id"],
                "dataset_source": "RAIL_YARD",
                "source_record_id": f"RY_{props.get('LABEL', '')}",
                "source_name": rail_name,
                "source_address": "",
                "source_city": "",
                "source_county": "",
                "source_lat": rail_lat,
                "source_lng": rail_lng,
                "distance_meters": round(distance, 1),
                "name_similarity": round(similarity, 3),
                "match_confidence": confidence,
                "match_method": "spatial+fuzzy_name"
            }
            new_links.append(link)

print(f"  Matched: {match_stats['rail_yards']['total']} links")
print(f"    HIGH: {match_stats['rail_yards']['high']}")
print(f"    MEDIUM: {match_stats['rail_yards']['medium']}")
print(f"    LOW: {match_stats['rail_yards']['low']}")

# ── Process Product Terminals (Louisiana only) ──
print("\n" + "="*60)
print("Processing Product Terminals...")
print("="*60)

with open(PRODUCT_TERMINALS, "r", encoding="utf-8") as f:
    terminal_data = json.load(f)

# Filter to Louisiana
la_terminals = []
for feat in terminal_data["features"]:
    if feat["geometry"] is None:
        continue
    coords = feat["geometry"]["coordinates"]
    if in_louisiana(coords[1], coords[0]):
        la_terminals.append(feat)

print(f"Total product terminals: {len(terminal_data['features'])}")
print(f"Louisiana terminals: {len(la_terminals)}")

for feat in la_terminals:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]

    term_lat = coords[1]
    term_lng = coords[0]
    term_name = props.get("Site_Name") or props.get("Company_Na", "")

    # Match to anchor facilities
    for anchor in anchor_facilities:
        distance = haversine_distance(anchor["lat"], anchor["lng"], term_lat, term_lng)

        if distance <= MATCH_RADIUS_METERS:
            similarity = fuzzy_similarity(
                normalize_name(anchor["canonical_name"]),
                normalize_name(term_name)
            )

            # Determine confidence
            if distance < 500 and similarity > 0.8:
                confidence = "HIGH"
                match_stats["product_terminals"]["high"] += 1
            elif distance < 1500 and similarity > 0.6:
                confidence = "MEDIUM"
                match_stats["product_terminals"]["medium"] += 1
            elif distance <= MATCH_RADIUS_METERS:
                confidence = "LOW"
                match_stats["product_terminals"]["low"] += 1
            else:
                continue

            match_stats["product_terminals"]["total"] += 1

            link = {
                "facility_id": anchor["facility_id"],
                "dataset_source": "PRODUCT_TERMINAL",
                "source_record_id": str(props.get("EIA_ID") or props.get("FID", "")),
                "source_name": term_name,
                "source_address": "",
                "source_city": props.get("City", ""),
                "source_county": "",
                "source_lat": term_lat,
                "source_lng": term_lng,
                "distance_meters": round(distance, 1),
                "name_similarity": round(similarity, 3),
                "match_confidence": confidence,
                "match_method": "spatial+fuzzy_name"
            }
            new_links.append(link)

print(f"  Matched: {match_stats['product_terminals']['total']} links")
print(f"    HIGH: {match_stats['product_terminals']['high']}")
print(f"    MEDIUM: {match_stats['product_terminals']['medium']}")
print(f"    LOW: {match_stats['product_terminals']['low']}")

# ── Process Refineries (Louisiana only) ──
print("\n" + "="*60)
print("Processing Refineries...")
print("="*60)

with open(REFINERIES, "r", encoding="utf-8") as f:
    refinery_data = json.load(f)

# Filter to Louisiana
la_refineries = []
for feat in refinery_data["features"]:
    if feat["geometry"] is None:
        continue
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]
    if in_louisiana(coords[1], coords[0]):
        la_refineries.append(feat)

print(f"Total refineries: {len(refinery_data['features'])}")
print(f"Louisiana refineries: {len(la_refineries)}")

for feat in la_refineries:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]

    ref_lat = coords[1]
    ref_lng = coords[0]
    ref_name = props.get("Facility", "")

    # Match to anchor facilities
    for anchor in anchor_facilities:
        distance = haversine_distance(anchor["lat"], anchor["lng"], ref_lat, ref_lng)

        if distance <= MATCH_RADIUS_METERS:
            similarity = fuzzy_similarity(
                normalize_name(anchor["canonical_name"]),
                normalize_name(ref_name)
            )

            # Determine confidence
            if distance < 500 and similarity > 0.8:
                confidence = "HIGH"
                match_stats["refineries"]["high"] += 1
            elif distance < 1500 and similarity > 0.6:
                confidence = "MEDIUM"
                match_stats["refineries"]["medium"] += 1
            elif distance <= MATCH_RADIUS_METERS:
                confidence = "LOW"
                match_stats["refineries"]["low"] += 1
            else:
                continue

            match_stats["refineries"]["total"] += 1

            link = {
                "facility_id": anchor["facility_id"],
                "dataset_source": "REFINERY",
                "source_record_id": str(props.get("SiteId") or props.get("FID", "")),
                "source_name": ref_name,
                "source_address": "",
                "source_city": "",
                "source_county": "",
                "source_lat": ref_lat,
                "source_lng": ref_lng,
                "distance_meters": round(distance, 1),
                "name_similarity": round(similarity, 3),
                "match_confidence": confidence,
                "match_method": "spatial+fuzzy_name"
            }
            new_links.append(link)

print(f"  Matched: {match_stats['refineries']['total']} links")
print(f"    HIGH: {match_stats['refineries']['high']}")
print(f"    MEDIUM: {match_stats['refineries']['medium']}")
print(f"    LOW: {match_stats['refineries']['low']}")

# ── Combine and save all links ──
print("\n" + "="*60)
print("Saving updated dataset links...")
print("="*60)

all_links = existing_links + new_links

with open(OUTPUT_LINKS, "w", newline="", encoding="utf-8") as f:
    if all_links:
        fieldnames = list(all_links[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_links)

print(f"  OK: {OUTPUT_LINKS}")
print(f"  Total links: {len(all_links)}")
print(f"    Previous: {len(existing_links)}")
print(f"    New: {len(new_links)}")

# ── Summary ──
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nDataset Links Added:")
print(f"  Rail Yards:        {match_stats['rail_yards']['total']:4d}")
print(f"  Product Terminals: {match_stats['product_terminals']['total']:4d}")
print(f"  Refineries:        {match_stats['refineries']['total']:4d}")
print(f"  {'-'*40}")
print(f"  Total New Links:   {len(new_links):4d}")
print(f"\nGrand Total Links: {len(all_links):4d}")

print("\nDONE: Rail and navigation facilities added to master registry!")
