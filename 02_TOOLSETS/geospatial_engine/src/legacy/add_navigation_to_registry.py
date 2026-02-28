"""
Add BTS navigation facilities (docks, locks, ports) to the master facility registry.
Uses existing BTS data from 01_geospatial directory.
"""
import json
import csv
import math
import os
from difflib import SequenceMatcher

# File paths
MASTER_FACILITIES = r"G:\My Drive\LLM\sources_data_maps\master_facilities.csv"
EXISTING_LINKS = r"G:\My Drive\LLM\sources_data_maps\facility_dataset_links.csv"
OUTPUT_LINKS = r"G:\My Drive\LLM\sources_data_maps\facility_dataset_links.csv"

# BTS navigation data paths
BTS_DOCKS_GEOJSON = r"G:\My Drive\LLM\sources_data_maps\01_geospatial\05_bts_navigation_fac\Docks_7158805788074691473.geojson"
BTS_LOCKS_GEOJSON = r"G:\My Drive\LLM\sources_data_maps\01_geospatial\04_bts_locks\Locks_-8780008747154303725.geojson"
BTS_PORTS_GEOJSON = r"G:\My Drive\LLM\sources_data_maps\01_geospatial\08_bts_principal_ports\Principal_Ports_-68781543534027147.geojson"

# Configuration
MATCH_RADIUS_METERS = 3000
NAME_SIMILARITY_THRESHOLD = 0.6

# Louisiana bounding box
LA_BBOX = {"min_lat": 28.9, "max_lat": 33.0, "min_lng": -94.0, "max_lng": -88.8}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
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

# Load master facilities
print("Loading master facilities...")
anchor_facilities = []
with open(MASTER_FACILITIES, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["lat"] = float(row["lat"])
        row["lng"] = float(row["lng"])
        anchor_facilities.append(row)
print(f"  Loaded {len(anchor_facilities)} anchor facilities")

# Load existing links
print("\nLoading existing dataset links...")
existing_links = []
with open(EXISTING_LINKS, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    existing_links = list(reader)
print(f"  Loaded {len(existing_links)} existing links")

new_links = []
match_stats = {
    "bts_docks": {"total": 0, "high": 0, "medium": 0, "low": 0, "count_la": 0},
    "bts_locks": {"total": 0, "high": 0, "medium": 0, "low": 0, "count_la": 0},
    "bts_ports": {"total": 0, "high": 0, "medium": 0, "low": 0, "count_la": 0}
}

# Process BTS Docks
print("\n" + "="*60)
print("Processing BTS Docks...")
print("="*60)

if os.path.exists(BTS_DOCKS_GEOJSON):
    with open(BTS_DOCKS_GEOJSON, "r", encoding="utf-8") as f:
        docks_data = json.load(f)

    # Filter to Louisiana
    la_docks = []
    for feat in docks_data.get("features", []):
        if feat["geometry"] and feat["geometry"]["type"] == "Point":
            coords = feat["geometry"]["coordinates"]
            if in_louisiana(coords[1], coords[0]):
                la_docks.append(feat)

    match_stats["bts_docks"]["count_la"] = len(la_docks)
    print(f"Total docks: {len(docks_data.get('features', []))}")
    print(f"Louisiana docks: {len(la_docks)}")

    for feat in la_docks:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        dock_lat = coords[1]
        dock_lng = coords[0]
        dock_name = props.get("DOCK_NAME") or props.get("NAME") or props.get("Facility", "")

        for anchor in anchor_facilities:
            distance = haversine_distance(anchor["lat"], anchor["lng"], dock_lat, dock_lng)

            if distance <= MATCH_RADIUS_METERS:
                similarity = fuzzy_similarity(
                    normalize_name(anchor["canonical_name"]),
                    normalize_name(dock_name)
                )

                if distance < 500 and similarity > 0.8:
                    confidence = "HIGH"
                    match_stats["bts_docks"]["high"] += 1
                elif distance < 1500 and similarity > 0.6:
                    confidence = "MEDIUM"
                    match_stats["bts_docks"]["medium"] += 1
                elif distance <= MATCH_RADIUS_METERS:
                    confidence = "LOW"
                    match_stats["bts_docks"]["low"] += 1
                else:
                    continue

                match_stats["bts_docks"]["total"] += 1

                link = {
                    "facility_id": anchor["facility_id"],
                    "dataset_source": "BTS_DOCK",
                    "source_record_id": str(props.get("OBJECTID") or props.get("FID", "")),
                    "source_name": dock_name,
                    "source_address": props.get("ADDRESS", ""),
                    "source_city": props.get("CITY", ""),
                    "source_county": props.get("COUNTY", ""),
                    "source_lat": dock_lat,
                    "source_lng": dock_lng,
                    "distance_meters": round(distance, 1),
                    "name_similarity": round(similarity, 3),
                    "match_confidence": confidence,
                    "match_method": "spatial+fuzzy_name"
                }
                new_links.append(link)

    print(f"  Matched: {match_stats['bts_docks']['total']} links")
    print(f"    HIGH: {match_stats['bts_docks']['high']}")
    print(f"    MEDIUM: {match_stats['bts_docks']['medium']}")
    print(f"    LOW: {match_stats['bts_docks']['low']}")
else:
    print("  BTS Docks GeoJSON not found")

# Process BTS Locks (note: no locks on Lower Mississippi, but process for completeness)
print("\n" + "="*60)
print("Processing BTS Locks...")
print("="*60)

if os.path.exists(BTS_LOCKS_GEOJSON):
    with open(BTS_LOCKS_GEOJSON, "r", encoding="utf-8") as f:
        locks_data = json.load(f)

    la_locks = []
    for feat in locks_data.get("features", []):
        if feat["geometry"] and feat["geometry"]["type"] == "Point":
            coords = feat["geometry"]["coordinates"]
            if in_louisiana(coords[1], coords[0]):
                la_locks.append(feat)

    match_stats["bts_locks"]["count_la"] = len(la_locks)
    print(f"Total locks: {len(locks_data.get('features', []))}")
    print(f"Louisiana locks: {len(la_locks)}")

    for feat in la_locks:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        lock_lat = coords[1]
        lock_lng = coords[0]
        lock_name = props.get("LOCK_NAME") or props.get("NAME") or props.get("Facility", "")

        for anchor in anchor_facilities:
            distance = haversine_distance(anchor["lat"], anchor["lng"], lock_lat, lock_lng)

            if distance <= MATCH_RADIUS_METERS:
                similarity = fuzzy_similarity(
                    normalize_name(anchor["canonical_name"]),
                    normalize_name(lock_name)
                )

                if distance < 500 and similarity > 0.8:
                    confidence = "HIGH"
                    match_stats["bts_locks"]["high"] += 1
                elif distance < 1500 and similarity > 0.6:
                    confidence = "MEDIUM"
                    match_stats["bts_locks"]["medium"] += 1
                elif distance <= MATCH_RADIUS_METERS:
                    confidence = "LOW"
                    match_stats["bts_locks"]["low"] += 1
                else:
                    continue

                match_stats["bts_locks"]["total"] += 1

                link = {
                    "facility_id": anchor["facility_id"],
                    "dataset_source": "BTS_LOCK",
                    "source_record_id": str(props.get("OBJECTID") or props.get("FID", "")),
                    "source_name": lock_name,
                    "source_address": "",
                    "source_city": "",
                    "source_county": "",
                    "source_lat": lock_lat,
                    "source_lng": lock_lng,
                    "distance_meters": round(distance, 1),
                    "name_similarity": round(similarity, 3),
                    "match_confidence": confidence,
                    "match_method": "spatial+fuzzy_name"
                }
                new_links.append(link)

    print(f"  Matched: {match_stats['bts_locks']['total']} links")
else:
    print("  BTS Locks GeoJSON not found")

# Process BTS Principal Ports
print("\n" + "="*60)
print("Processing BTS Principal Ports...")
print("="*60)

if os.path.exists(BTS_PORTS_GEOJSON):
    with open(BTS_PORTS_GEOJSON, "r", encoding="utf-8") as f:
        ports_data = json.load(f)

    la_ports = []
    for feat in ports_data.get("features", []):
        if feat["geometry"] and feat["geometry"]["type"] == "Point":
            coords = feat["geometry"]["coordinates"]
            if in_louisiana(coords[1], coords[0]):
                la_ports.append(feat)

    match_stats["bts_ports"]["count_la"] = len(la_ports)
    print(f"Total ports: {len(ports_data.get('features', []))}")
    print(f"Louisiana ports: {len(la_ports)}")

    for feat in la_ports:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        port_lat = coords[1]
        port_lng = coords[0]
        port_name = props.get("PORT_NAME") or props.get("NAME") or props.get("Facility", "")

        for anchor in anchor_facilities:
            distance = haversine_distance(anchor["lat"], anchor["lng"], port_lat, port_lng)

            if distance <= MATCH_RADIUS_METERS:
                similarity = fuzzy_similarity(
                    normalize_name(anchor["canonical_name"]),
                    normalize_name(port_name)
                )

                if distance < 500 and similarity > 0.8:
                    confidence = "HIGH"
                    match_stats["bts_ports"]["high"] += 1
                elif distance < 1500 and similarity > 0.6:
                    confidence = "MEDIUM"
                    match_stats["bts_ports"]["medium"] += 1
                elif distance <= MATCH_RADIUS_METERS:
                    confidence = "LOW"
                    match_stats["bts_ports"]["low"] += 1
                else:
                    continue

                match_stats["bts_ports"]["total"] += 1

                link = {
                    "facility_id": anchor["facility_id"],
                    "dataset_source": "BTS_PORT",
                    "source_record_id": str(props.get("OBJECTID") or props.get("FID", "")),
                    "source_name": port_name,
                    "source_address": "",
                    "source_city": props.get("CITY", ""),
                    "source_county": "",
                    "source_lat": port_lat,
                    "source_lng": port_lng,
                    "distance_meters": round(distance, 1),
                    "name_similarity": round(similarity, 3),
                    "match_confidence": confidence,
                    "match_method": "spatial+fuzzy_name"
                }
                new_links.append(link)

    print(f"  Matched: {match_stats['bts_ports']['total']} links")
    print(f"    HIGH: {match_stats['bts_ports']['high']}")
    print(f"    MEDIUM: {match_stats['bts_ports']['medium']}")
    print(f"    LOW: {match_stats['bts_ports']['low']}")
else:
    print("  BTS Ports GeoJSON not found")

# Save updated links
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

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nLouisiana Navigation Facilities:")
print(f"  BTS Docks:  {match_stats['bts_docks']['count_la']:4d} (matched: {match_stats['bts_docks']['total']})")
print(f"  BTS Locks:  {match_stats['bts_locks']['count_la']:4d} (matched: {match_stats['bts_locks']['total']})")
print(f"  BTS Ports:  {match_stats['bts_ports']['count_la']:4d} (matched: {match_stats['bts_ports']['total']})")
print(f"  {'-'*40}")
print(f"  Total New Links:   {len(new_links):4d}")
print(f"\nGrand Total Links: {len(all_links):4d}")

print("\nDONE: Navigation facilities added to master registry!")
