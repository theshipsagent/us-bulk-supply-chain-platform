"""
Build commodity market clusters from master facility registry.
Creates spatial groupings for grain, petroleum, chemicals, and multi-modal facilities.
"""
import csv
import json
import math
from collections import defaultdict
from sklearn.cluster import DBSCAN
import numpy as np

print("="*80)
print("BUILDING COMMODITY MARKET CLUSTERS")
print("Lower Mississippi River Industrial Infrastructure")
print("="*80)

# Load master facilities
print("\nLoading master facilities...")
facilities = []
with open("master_facilities.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["lat"] = float(row["lat"])
        row["lng"] = float(row["lng"])
        facilities.append(row)

print(f"  Loaded {len(facilities)} facilities")

# Group by facility type
by_type = defaultdict(list)
for fac in facilities:
    fac_type = fac["facility_type"]
    by_type[fac_type].append(fac)

print(f"\nFacility Types:")
for ftype, facs in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {ftype:30s}: {len(facs):3d} facilities")

# Helper functions
def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers."""
    R = 6371  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def create_cluster_polygon(facilities, buffer_km=5):
    """Create a convex hull or buffer polygon for a cluster."""
    if not facilities:
        return None

    # Calculate centroid
    lats = [f["lat"] for f in facilities]
    lngs = [f["lng"] for f in facilities]
    centroid = [sum(lats)/len(lats), sum(lngs)/len(lngs)]

    # Simple circular buffer around centroid
    # In a full implementation, use shapely for proper convex hull
    # For now, return centroid + radius
    return {
        "type": "Point",
        "coordinates": [centroid[1], centroid[0]],  # lng, lat
        "buffer_km": buffer_km
    }

def cluster_facilities(facilities, eps_km=10, min_samples=2):
    """
    Cluster facilities using DBSCAN.
    eps_km: maximum distance between facilities in same cluster (km)
    min_samples: minimum facilities to form a cluster
    """
    if len(facilities) < min_samples:
        # All facilities in one cluster
        return {0: facilities}

    # Create coordinate matrix
    coords = np.array([[f["lat"], f["lng"]] for f in facilities])

    # DBSCAN clustering
    # Convert eps from km to degrees (approximate)
    eps_degrees = eps_km / 111.0  # roughly 111 km per degree latitude

    clustering = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='euclidean')
    labels = clustering.fit_predict(coords)

    # Group facilities by cluster
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        if label != -1:  # -1 is noise
            clusters[label].append(facilities[i])

    # Add noise points as single-facility clusters
    for i, label in enumerate(labels):
        if label == -1:
            clusters[f"noise_{i}"] = [facilities[i]]

    return clusters

# ============================================================================
# 1. GRAIN MARKET ZONES
# ============================================================================
print("\n" + "="*80)
print("1. GRAIN MARKET ZONES")
print("="*80)

grain_facilities = by_type.get("Elevator", [])
print(f"\nTotal grain elevators: {len(grain_facilities)}")

if grain_facilities:
    # Cluster grain elevators
    grain_clusters = cluster_facilities(grain_facilities, eps_km=15, min_samples=2)

    print(f"  Identified {len(grain_clusters)} grain market clusters")

    grain_features = []
    cluster_stats = []

    for cluster_id, cluster_facs in grain_clusters.items():
        # Calculate cluster statistics
        miles = [float(f["mrtis_mile"]) for f in cluster_facs if f["mrtis_mile"]]
        avg_mile = sum(miles) / len(miles) if miles else 0

        # Get unique operators
        operators = set(f["operators"][:50] for f in cluster_facs if f["operators"])

        # Create cluster feature
        centroid_lat = sum(f["lat"] for f in cluster_facs) / len(cluster_facs)
        centroid_lng = sum(f["lng"] for f in cluster_facs) / len(cluster_facs)

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [centroid_lng, centroid_lat]
            },
            "properties": {
                "cluster_id": f"GRAIN_{cluster_id}",
                "cluster_type": "Grain Export Corridor",
                "facility_count": len(cluster_facs),
                "avg_river_mile": round(avg_mile, 1),
                "facilities": [f["canonical_name"] for f in cluster_facs],
                "operators": list(operators)[:5],  # Top 5
                "market_area": f"River Mile {min(miles):.0f}-{max(miles):.0f}" if miles else ""
            }
        }
        grain_features.append(feature)

        cluster_stats.append({
            "cluster_id": f"GRAIN_{cluster_id}",
            "facility_count": len(cluster_facs),
            "avg_mile": round(avg_mile, 1),
            "facilities": ", ".join(f["canonical_name"] for f in cluster_facs)
        })

    # Save GeoJSON
    grain_geojson = {
        "type": "FeatureCollection",
        "features": grain_features
    }

    with open("commodity_clusters_grain.geojson", "w", encoding="utf-8") as f:
        json.dump(grain_geojson, f, indent=2)

    # Save stats CSV
    with open("commodity_clusters_grain_stats.csv", "w", newline="", encoding="utf-8") as f:
        if cluster_stats:
            writer = csv.DictWriter(f, fieldnames=cluster_stats[0].keys())
            writer.writeheader()
            writer.writerows(cluster_stats)

    print(f"\n  Grain Market Clusters:")
    for stat in cluster_stats:
        print(f"    {stat['cluster_id']:15s}: {stat['facility_count']} elevators at Mile {stat['avg_mile']}")
        print(f"      Facilities: {stat['facilities'][:80]}...")

    print(f"\n  OK: commodity_clusters_grain.geojson")
    print(f"  OK: commodity_clusters_grain_stats.csv")

# ============================================================================
# 2. REFINERY COMPLEXES
# ============================================================================
print("\n" + "="*80)
print("2. REFINERY COMPLEXES")
print("="*80)

refinery_facilities = by_type.get("Refinery", [])
print(f"\nTotal refineries: {len(refinery_facilities)}")

if refinery_facilities:
    # Include associated petroleum terminals
    petroleum_terminals = by_type.get("Tank Storage", [])
    all_petroleum = refinery_facilities + petroleum_terminals

    print(f"  Including {len(petroleum_terminals)} petroleum terminals")
    print(f"  Total petroleum facilities: {len(all_petroleum)}")

    # Cluster petroleum facilities
    petro_clusters = cluster_facilities(all_petroleum, eps_km=12, min_samples=2)

    print(f"  Identified {len(petro_clusters)} petroleum market complexes")

    petro_features = []
    petro_stats = []

    for cluster_id, cluster_facs in petro_clusters.items():
        refineries = [f for f in cluster_facs if f["facility_type"] == "Refinery"]
        terminals = [f for f in cluster_facs if f["facility_type"] == "Tank Storage"]

        centroid_lat = sum(f["lat"] for f in cluster_facs) / len(cluster_facs)
        centroid_lng = sum(f["lng"] for f in cluster_facs) / len(cluster_facs)

        miles = [float(f["mrtis_mile"]) for f in cluster_facs if f["mrtis_mile"]]
        avg_mile = sum(miles) / len(miles) if miles else 0

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [centroid_lng, centroid_lat]
            },
            "properties": {
                "cluster_id": f"PETRO_{cluster_id}",
                "cluster_type": "Petroleum Refinery Complex",
                "facility_count": len(cluster_facs),
                "refinery_count": len(refineries),
                "terminal_count": len(terminals),
                "avg_river_mile": round(avg_mile, 1),
                "facilities": [f["canonical_name"] for f in cluster_facs],
                "major_refineries": [f["canonical_name"] for f in refineries]
            }
        }
        petro_features.append(feature)

        petro_stats.append({
            "cluster_id": f"PETRO_{cluster_id}",
            "facility_count": len(cluster_facs),
            "refineries": len(refineries),
            "terminals": len(terminals),
            "avg_mile": round(avg_mile, 1),
            "facilities": ", ".join(f["canonical_name"] for f in cluster_facs[:5])
        })

    # Save GeoJSON
    petro_geojson = {
        "type": "FeatureCollection",
        "features": petro_features
    }

    with open("commodity_clusters_petroleum.geojson", "w", encoding="utf-8") as f:
        json.dump(petro_geojson, f, indent=2)

    with open("commodity_clusters_petroleum_stats.csv", "w", newline="", encoding="utf-8") as f:
        if petro_stats:
            writer = csv.DictWriter(f, fieldnames=petro_stats[0].keys())
            writer.writeheader()
            writer.writerows(petro_stats)

    print(f"\n  Petroleum Market Complexes:")
    for stat in petro_stats:
        print(f"    {stat['cluster_id']:15s}: {stat['refineries']} refineries + {stat['terminals']} terminals at Mile {stat['avg_mile']}")

    print(f"\n  OK: commodity_clusters_petroleum.geojson")
    print(f"  OK: commodity_clusters_petroleum_stats.csv")

# ============================================================================
# 3. CHEMICAL CORRIDORS
# ============================================================================
print("\n" + "="*80)
print("3. CHEMICAL CORRIDORS")
print("="*80)

chemical_facilities = by_type.get("Chemical Plant", []) + by_type.get("Bulk Plant", [])
print(f"\nTotal chemical facilities: {len(chemical_facilities)}")

if chemical_facilities:
    chem_clusters = cluster_facilities(chemical_facilities, eps_km=20, min_samples=2)

    print(f"  Identified {len(chem_clusters)} chemical corridor zones")

    chem_features = []
    chem_stats = []

    for cluster_id, cluster_facs in chem_clusters.items():
        centroid_lat = sum(f["lat"] for f in cluster_facs) / len(cluster_facs)
        centroid_lng = sum(f["lng"] for f in cluster_facs) / len(cluster_facs)

        miles = [float(f["mrtis_mile"]) for f in cluster_facs if f["mrtis_mile"]]
        avg_mile = sum(miles) / len(miles) if miles else 0

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [centroid_lng, centroid_lat]
            },
            "properties": {
                "cluster_id": f"CHEM_{cluster_id}",
                "cluster_type": "Chemical Manufacturing Corridor",
                "facility_count": len(cluster_facs),
                "avg_river_mile": round(avg_mile, 1),
                "facilities": [f["canonical_name"] for f in cluster_facs],
                "river_stretch": f"Mile {min(miles):.0f}-{max(miles):.0f}" if miles else ""
            }
        }
        chem_features.append(feature)

        chem_stats.append({
            "cluster_id": f"CHEM_{cluster_id}",
            "facility_count": len(cluster_facs),
            "avg_mile": round(avg_mile, 1),
            "facilities": ", ".join(f["canonical_name"] for f in cluster_facs)
        })

    chem_geojson = {
        "type": "FeatureCollection",
        "features": chem_features
    }

    with open("commodity_clusters_chemical.geojson", "w", encoding="utf-8") as f:
        json.dump(chem_geojson, f, indent=2)

    with open("commodity_clusters_chemical_stats.csv", "w", newline="", encoding="utf-8") as f:
        if chem_stats:
            writer = csv.DictWriter(f, fieldnames=chem_stats[0].keys())
            writer.writeheader()
            writer.writerows(chem_stats)

    print(f"\n  Chemical Corridor Zones:")
    for stat in chem_stats:
        print(f"    {stat['cluster_id']:15s}: {stat['facility_count']} facilities at Mile {stat['avg_mile']}")

    print(f"\n  OK: commodity_clusters_chemical.geojson")
    print(f"  OK: commodity_clusters_chemical_stats.csv")

# ============================================================================
# 4. MULTI-MODAL LOGISTICS HUBS
# ============================================================================
print("\n" + "="*80)
print("4. MULTI-MODAL LOGISTICS HUBS")
print("="*80)

# Load facility links to identify multi-modal facilities
print("\nAnalyzing dataset links to find multi-modal facilities...")

links = []
with open("facility_dataset_links.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    links = list(reader)

# Count dataset sources per facility
facility_sources = defaultdict(set)
for link in links:
    facility_sources[link["facility_id"]].add(link["dataset_source"])

# Find facilities with multiple transportation modes
multimodal_facilities = []
for fac in facilities:
    sources = facility_sources.get(fac["facility_id"], set())

    has_water = "BTS_DOCK" in sources
    has_rail = "RAIL_YARD" in sources or "BTS_LOCK" in sources
    has_pipeline = "PRODUCT_TERMINAL" in sources or "REFINERY" in sources

    mode_count = sum([has_water, has_rail, has_pipeline])

    if mode_count >= 2:  # At least 2 modes
        fac["transport_modes"] = mode_count
        fac["modes"] = []
        if has_water:
            fac["modes"].append("Water")
        if has_rail:
            fac["modes"].append("Rail")
        if has_pipeline:
            fac["modes"].append("Pipeline")
        multimodal_facilities.append(fac)

print(f"  Found {len(multimodal_facilities)} multi-modal facilities")

if multimodal_facilities:
    multimodal_features = []

    for fac in multimodal_facilities:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [fac["lng"], fac["lat"]]
            },
            "properties": {
                "facility_id": fac["facility_id"],
                "facility_name": fac["canonical_name"],
                "facility_type": fac["facility_type"],
                "transport_modes": fac["transport_modes"],
                "modes": fac["modes"],
                "river_mile": fac["mrtis_mile"],
                "port": fac["port"],
                "logistics_hub": "Critical Intermodal Node"
            }
        }
        multimodal_features.append(feature)

    multimodal_geojson = {
        "type": "FeatureCollection",
        "features": multimodal_features
    }

    with open("commodity_clusters_multimodal.geojson", "w", encoding="utf-8") as f:
        json.dump(multimodal_geojson, f, indent=2)

    print(f"\n  Multi-Modal Logistics Hubs:")
    for fac in sorted(multimodal_facilities, key=lambda x: x["transport_modes"], reverse=True)[:10]:
        modes_str = " + ".join(fac["modes"])
        print(f"    {fac['canonical_name']:30s}: {modes_str}")

    print(f"\n  OK: commodity_clusters_multimodal.geojson")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nCommodity Market Clusters Created:")
print(f"  Grain Market Zones:          {len(grain_features) if grain_facilities else 0}")
print(f"  Petroleum Refinery Complexes: {len(petro_features) if refinery_facilities else 0}")
print(f"  Chemical Corridors:           {len(chem_features) if chemical_facilities else 0}")
print(f"  Multi-Modal Logistics Hubs:   {len(multimodal_features) if multimodal_facilities else 0}")

print(f"\nOutput Files:")
print(f"  - commodity_clusters_grain.geojson")
print(f"  - commodity_clusters_petroleum.geojson")
print(f"  - commodity_clusters_chemical.geojson")
print(f"  - commodity_clusters_multimodal.geojson")
print(f"  - *_stats.csv (cluster statistics)")

print("\n" + "="*80)
print("DONE: Commodity market clusters built!")
print("="*80)
print("\nNext: Add these GeoJSON files to your interactive Leaflet story map")
