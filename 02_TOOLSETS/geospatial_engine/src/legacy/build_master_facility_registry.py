"""
Build Master Facility Registry - Link EPA FRS and other datasets to MRTIS anchor facilities.

Creates:
1. master_facilities.csv - One record per physical facility (anchors)
2. facility_dataset_links.csv - Links from facilities to all matching dataset records
"""
import json
import csv
import math
from collections import defaultdict
from difflib import SequenceMatcher

# ── File paths ──
MRTIS_FILE = r"G:\My Drive\LLM\sources_data_maps\qgis\mrtis_usace_matched.geojson"
EPA_FRS_FILE = r"G:\My Drive\LLM\sources_data_maps\epa_frs_louisiana_facilities.json"
OUTPUT_MASTER = r"G:\My Drive\LLM\sources_data_maps\master_facilities.csv"
OUTPUT_LINKS = r"G:\My Drive\LLM\sources_data_maps\facility_dataset_links.csv"

# ── Configuration ──
EXCLUDE_TYPES = {"Anchorage", "Pilot Station"}
EXCLUDE_ZONES = {
    "Andry St", "Buck Kreihs", "Poland St", "Esplanade Ave",
    "Gov Nicholls St", "Mandeville St", "Erato St", "Perry Street",
    "110 Buoys", "111 Buoys", "112 Buoys", "CGB 111 Buoys",
}

# Spatial matching radius (meters)
MATCH_RADIUS_METERS = 3000  # 3km for large industrial sites
NAME_SIMILARITY_THRESHOLD = 0.6  # 60% similarity for name matching

# ── Helper functions ──

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters using Haversine formula."""
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
    # Remove common suffixes/prefixes and normalize
    name = name.upper()
    replacements = {
        " LLC": "", " INC": "", " CORP": "", " CORPORATION": "",
        " LTD": "", " LP": "", " L.P.": "", " CO.": "", " CO": "",
        ",": "", ".": "", "  ": " "
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()

# ── Load MRTIS anchor facilities ──
print("Loading MRTIS anchor facilities...")
with open(MRTIS_FILE, "r", encoding="utf-8") as f:
    mrtis_data = json.load(f)

anchor_facilities = []
for feat in mrtis_data["features"]:
    props = feat["properties"]
    zone_type = props.get("ZoneType", "")
    zone_name = props.get("Zone", "")

    # Skip excluded types and zones
    if zone_type in EXCLUDE_TYPES or zone_name in EXCLUDE_ZONES:
        continue

    coords = feat["geometry"]["coordinates"]

    facility = {
        "facility_id": f"MRTIS_{len(anchor_facilities)+1:04d}",
        "canonical_name": props.get("Facility", zone_name),
        "zone_name": zone_name,
        "facility_type": zone_type,
        "lat": coords[1],
        "lng": coords[0],
        "mrtis_mile": props.get("MRTIS_Mile"),
        "usace_mile": props.get("USACE_Mile"),
        "usace_name": props.get("USACE_Name"),
        "port": props.get("Port"),
        "waterway": props.get("Waterway"),
        "owners": props.get("Owners", ""),
        "operators": props.get("Operators", ""),
        "commodities": props.get("Commodities", ""),
        "city": props.get("City", ""),
        "county": props.get("County", ""),
        "state": props.get("State", ""),
    }
    anchor_facilities.append(facility)

print(f"  Loaded {len(anchor_facilities)} anchor facilities (excluded {len(mrtis_data['features']) - len(anchor_facilities)} anchorages/buoys)")

# ── Load EPA FRS facilities ──
print("\nLoading EPA FRS facilities...")
with open(EPA_FRS_FILE, "r", encoding="utf-8") as f:
    epa_facilities = json.load(f)

# Filter to only those with coordinates
epa_with_coords = [
    f for f in epa_facilities
    if f.get("Latitude83") and f.get("Longitude83")
]
print(f"  Loaded {len(epa_with_coords)} EPA FRS facilities with coordinates")

# ── Spatial matching: Link EPA FRS to MRTIS anchors ──
print(f"\nMatching EPA FRS records to anchor facilities...")
print(f"  Search radius: {MATCH_RADIUS_METERS}m ({MATCH_RADIUS_METERS/1000}km)")
print(f"  Name similarity threshold: {NAME_SIMILARITY_THRESHOLD*100}%")

links = []
match_stats = {"high": 0, "medium": 0, "low": 0, "total": 0}

for anchor in anchor_facilities:
    anchor_lat = anchor["lat"]
    anchor_lng = anchor["lng"]
    anchor_name_norm = normalize_name(anchor["canonical_name"])

    # Find nearby EPA facilities
    for epa in epa_with_coords:
        try:
            epa_lat = float(epa["Latitude83"])
            epa_lng = float(epa["Longitude83"])
        except (ValueError, TypeError):
            continue

        # Calculate distance
        distance = haversine_distance(anchor_lat, anchor_lng, epa_lat, epa_lng)

        if distance <= MATCH_RADIUS_METERS:
            # Within radius - calculate name similarity
            epa_name_norm = normalize_name(epa.get("FacilityName", ""))
            similarity = fuzzy_similarity(anchor_name_norm, epa_name_norm)

            # Determine match confidence
            if distance < 500 and similarity > 0.8:
                confidence = "HIGH"
                match_stats["high"] += 1
            elif distance < 1500 and similarity > 0.6:
                confidence = "MEDIUM"
                match_stats["medium"] += 1
            elif distance <= MATCH_RADIUS_METERS:
                confidence = "LOW"
                match_stats["low"] += 1
            else:
                continue  # Skip if no confidence criteria met

            match_stats["total"] += 1

            link = {
                "facility_id": anchor["facility_id"],
                "dataset_source": "EPA_FRS",
                "source_record_id": epa.get("RegistryId", ""),
                "source_name": epa.get("FacilityName", ""),
                "source_address": epa.get("LocationAddress", ""),
                "source_city": epa.get("CityName", ""),
                "source_county": epa.get("CountyName", ""),
                "source_lat": epa_lat,
                "source_lng": epa_lng,
                "distance_meters": round(distance, 1),
                "name_similarity": round(similarity, 3),
                "match_confidence": confidence,
                "match_method": "spatial+fuzzy_name"
            }
            links.append(link)

print(f"\n  Match Results:")
print(f"    Total links: {match_stats['total']}")
print(f"    HIGH confidence: {match_stats['high']}")
print(f"    MEDIUM confidence: {match_stats['medium']}")
print(f"    LOW confidence: {match_stats['low']}")

# ── Calculate facility statistics ──
facility_link_counts = defaultdict(int)
for link in links:
    facility_link_counts[link["facility_id"]] += 1

facilities_with_links = len(facility_link_counts)
facilities_without_links = len(anchor_facilities) - facilities_with_links

print(f"\n  Facility Coverage:")
print(f"    Facilities with EPA matches: {facilities_with_links}/{len(anchor_facilities)}")
print(f"    Facilities with no matches: {facilities_without_links}/{len(anchor_facilities)}")

# ── Save master facilities table ──
print(f"\nSaving master facilities...")
with open(OUTPUT_MASTER, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "facility_id", "canonical_name", "zone_name", "facility_type",
        "lat", "lng", "mrtis_mile", "usace_mile", "usace_name",
        "port", "waterway", "owners", "operators", "commodities",
        "city", "county", "state", "epa_frs_links"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for fac in anchor_facilities:
        fac["epa_frs_links"] = facility_link_counts.get(fac["facility_id"], 0)
        writer.writerow(fac)

print(f"  OK: {OUTPUT_MASTER}")
print(f"  Rows: {len(anchor_facilities)}")

# ── Save links table ──
print(f"\nSaving dataset links...")
with open(OUTPUT_LINKS, "w", newline="", encoding="utf-8") as f:
    if links:
        fieldnames = list(links[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(links)

print(f"  OK: {OUTPUT_LINKS}")
print(f"  Rows: {len(links)}")

# ── Top facilities by EPA link count ──
print(f"\nTop 10 Facilities by EPA FRS Links:")
top_facilities = sorted(
    [(fid, cnt) for fid, cnt in facility_link_counts.items()],
    key=lambda x: x[1],
    reverse=True
)[:10]

for fid, count in top_facilities:
    fac = next(f for f in anchor_facilities if f["facility_id"] == fid)
    print(f"  {fac['canonical_name']:50s} : {count:3d} EPA links")

print("\nDONE: Master facility registry created!")
print(f"\nOutputs:")
print(f"  1. {OUTPUT_MASTER}")
print(f"  2. {OUTPUT_LINKS}")
