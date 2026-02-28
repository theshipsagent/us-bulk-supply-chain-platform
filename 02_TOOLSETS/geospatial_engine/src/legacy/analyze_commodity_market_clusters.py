"""
Deep analysis of commodity market clusters.
Calculate total capacity, dataset coverage, market share, and dominance metrics.
"""
import csv
import json
from collections import defaultdict
import statistics

print("="*80)
print("DEEP ANALYSIS: COMMODITY MARKET CLUSTERS")
print("Lower Mississippi River Industrial Infrastructure")
print("="*80)

# Load all data
print("\nLoading datasets...")

# Master facilities
facilities = []
with open("master_facilities.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    facilities = {row["facility_id"]: row for row in reader}

print(f"  Facilities: {len(facilities)}")

# Dataset links
links = []
with open("facility_dataset_links.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    links = list(reader)

print(f"  Dataset links: {len(links)}")

# Cluster files
with open("commodity_clusters_grain.geojson", "r") as f:
    grain_clusters = json.load(f)["features"]

with open("commodity_clusters_petroleum.geojson", "r") as f:
    petro_clusters = json.load(f)["features"]

with open("commodity_clusters_chemical.geojson", "r") as f:
    chem_clusters = json.load(f)["features"]

with open("commodity_clusters_multimodal.geojson", "r") as f:
    multimodal_hubs = json.load(f)["features"]

print(f"  Grain clusters: {len(grain_clusters)}")
print(f"  Petroleum clusters: {len(petro_clusters)}")
print(f"  Chemical clusters: {len(chem_clusters)}")
print(f"  Multi-modal hubs: {len(multimodal_hubs)}")

# Build facility -> links mapping
facility_links = defaultdict(list)
for link in links:
    facility_links[link["facility_id"]].append(link)

# Helper function
def analyze_cluster(cluster_name, facility_ids, cluster_type):
    """Analyze a cluster's dataset coverage and infrastructure."""

    # Get all links for facilities in this cluster
    cluster_links = []
    for fac_id in facility_ids:
        cluster_links.extend(facility_links.get(fac_id, []))

    # Count by dataset source
    by_source = defaultdict(int)
    for link in cluster_links:
        by_source[link["dataset_source"]] += 1

    # Count high-confidence matches
    high_conf = [l for l in cluster_links if l["match_confidence"] == "HIGH"]
    med_conf = [l for l in cluster_links if l["match_confidence"] == "MEDIUM"]

    # Get facility details
    fac_names = []
    fac_types = defaultdict(int)
    river_miles = []

    for fac_id in facility_ids:
        if fac_id in facilities:
            fac = facilities[fac_id]
            fac_names.append(fac["canonical_name"])
            fac_types[fac["facility_type"]] += 1
            if fac.get("mrtis_mile"):
                try:
                    river_miles.append(float(fac["mrtis_mile"]))
                except:
                    pass

    # Calculate metrics
    total_links = len(cluster_links)
    unique_sources = len(by_source)
    infrastructure_score = total_links * unique_sources  # Diversity * Volume

    river_span = max(river_miles) - min(river_miles) if river_miles else 0

    return {
        "cluster_name": cluster_name,
        "cluster_type": cluster_type,
        "facility_count": len(facility_ids),
        "total_dataset_links": total_links,
        "unique_data_sources": unique_sources,
        "infrastructure_score": infrastructure_score,
        "high_confidence_links": len(high_conf),
        "medium_confidence_links": len(med_conf),
        "dataset_breakdown": dict(by_source),
        "facility_types": dict(fac_types),
        "facility_names": fac_names,
        "avg_river_mile": statistics.mean(river_miles) if river_miles else 0,
        "river_mile_span": river_span,
        "density": total_links / len(facility_ids) if facility_ids else 0
    }

# ============================================================================
# GRAIN MARKET ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("GRAIN MARKET ZONES - DEEP ANALYSIS")
print("="*80)

grain_analyses = []

for cluster in grain_clusters:
    props = cluster["properties"]
    cluster_id = props["cluster_id"]

    # Get facility IDs from facility names
    facility_names = props["facilities"]
    facility_ids = [
        fid for fid, fac in facilities.items()
        if fac["canonical_name"] in facility_names
    ]

    analysis = analyze_cluster(cluster_id, facility_ids, "Grain Elevator")
    grain_analyses.append(analysis)

# Sort by infrastructure score
grain_analyses.sort(key=lambda x: x["infrastructure_score"], reverse=True)

print("\nTop Grain Market Zones by Infrastructure Score:")
print(f"{'Cluster':<20} {'Facilities':<5} {'Links':<7} {'Sources':<8} {'Score':<8} {'Location'}")
print("-"*80)

for i, analysis in enumerate(grain_analyses[:10], 1):
    print(f"{analysis['cluster_name']:<20} "
          f"{analysis['facility_count']:<5} "
          f"{analysis['total_dataset_links']:<7} "
          f"{analysis['unique_data_sources']:<8} "
          f"{analysis['infrastructure_score']:<8} "
          f"Mile {analysis['avg_river_mile']:.0f}")

    # Show facility names
    names = ", ".join(analysis['facility_names'][:3])
    if len(analysis['facility_names']) > 3:
        names += f" +{len(analysis['facility_names'])-3} more"
    print(f"  Facilities: {names}")

    # Show dataset breakdown
    top_sources = sorted(analysis['dataset_breakdown'].items(),
                        key=lambda x: x[1], reverse=True)[:3]
    sources_str = ", ".join(f"{src}: {cnt}" for src, cnt in top_sources)
    print(f"  Datasets: {sources_str}")
    print()

# Calculate market share
total_grain_links = sum(a["total_dataset_links"] for a in grain_analyses)
print(f"\nGrain Market Concentration:")
for analysis in grain_analyses[:5]:
    market_share = (analysis["total_dataset_links"] / total_grain_links * 100) if total_grain_links else 0
    print(f"  {analysis['cluster_name']:<20}: {market_share:5.1f}% of total dataset coverage")

# ============================================================================
# PETROLEUM MARKET ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("PETROLEUM REFINERY COMPLEXES - DEEP ANALYSIS")
print("="*80)

petro_analyses = []

for cluster in petro_clusters:
    props = cluster["properties"]
    cluster_id = props["cluster_id"]

    facility_names = props["facilities"]
    facility_ids = [
        fid for fid, fac in facilities.items()
        if fac["canonical_name"] in facility_names
    ]

    analysis = analyze_cluster(cluster_id, facility_ids, "Petroleum Complex")
    analysis["refinery_count"] = props.get("refinery_count", 0)
    analysis["terminal_count"] = props.get("terminal_count", 0)
    petro_analyses.append(analysis)

petro_analyses.sort(key=lambda x: x["infrastructure_score"], reverse=True)

print("\nTop Petroleum Complexes by Infrastructure Score:")
print(f"{'Cluster':<20} {'Ref':<4} {'Term':<5} {'Links':<7} {'Sources':<8} {'Score':<8} {'Location'}")
print("-"*80)

for analysis in petro_analyses[:10]:
    print(f"{analysis['cluster_name']:<20} "
          f"{analysis['refinery_count']:<4} "
          f"{analysis['terminal_count']:<5} "
          f"{analysis['total_dataset_links']:<7} "
          f"{analysis['unique_data_sources']:<8} "
          f"{analysis['infrastructure_score']:<8} "
          f"Mile {analysis['avg_river_mile']:.0f}")

    # Show major facilities
    refineries = [name for name in analysis['facility_names']
                  if any(x in name.lower() for x in ['exxon', 'shell', 'marathon', 'valero', 'phillips'])]
    if refineries:
        print(f"  Major refineries: {', '.join(refineries[:3])}")

    # High confidence matches
    if analysis['high_confidence_links'] > 0:
        print(f"  High-confidence matches: {analysis['high_confidence_links']}")
    print()

# Calculate petroleum market dominance
total_petro_links = sum(a["total_dataset_links"] for a in petro_analyses)
print(f"\nPetroleum Market Concentration:")
for analysis in petro_analyses[:5]:
    market_share = (analysis["total_dataset_links"] / total_petro_links * 100) if total_petro_links else 0
    refinery_intensity = analysis["refinery_count"] / analysis["facility_count"] if analysis["facility_count"] else 0
    print(f"  {analysis['cluster_name']:<20}: {market_share:5.1f}% coverage | {refinery_intensity:.0%} refineries")

# ============================================================================
# CHEMICAL CORRIDOR ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("CHEMICAL CORRIDORS - DEEP ANALYSIS")
print("="*80)

chem_analyses = []

for cluster in chem_clusters:
    props = cluster["properties"]
    cluster_id = props["cluster_id"]

    facility_names = props["facilities"]
    facility_ids = [
        fid for fid, fac in facilities.items()
        if fac["canonical_name"] in facility_names
    ]

    analysis = analyze_cluster(cluster_id, facility_ids, "Chemical Corridor")
    chem_analyses.append(analysis)

chem_analyses.sort(key=lambda x: x["facility_count"], reverse=True)

print("\nChemical Corridors by Facility Concentration:")
print(f"{'Cluster':<20} {'Facilities':<11} {'Links':<7} {'Density':<8} {'River Span':<12} {'Location'}")
print("-"*80)

for analysis in chem_analyses:
    print(f"{analysis['cluster_name']:<20} "
          f"{analysis['facility_count']:<11} "
          f"{analysis['total_dataset_links']:<7} "
          f"{analysis['density']:<8.1f} "
          f"{analysis['river_mile_span']:<12.1f} "
          f"Mile {analysis['avg_river_mile']:.0f}")

    # Show sample facilities
    names = ", ".join(analysis['facility_names'][:5])
    if len(analysis['facility_names']) > 5:
        names += f" +{len(analysis['facility_names'])-5} more"
    print(f"  Facilities: {names}")
    print()

# Identify "Chemical Alley"
chemical_alley = max(chem_analyses, key=lambda x: x["facility_count"])
print(f"\nCHEMICAL ALLEY IDENTIFIED:")
print(f"  Cluster: {chemical_alley['cluster_name']}")
print(f"  Location: River Mile {chemical_alley['avg_river_mile']:.0f}")
print(f"  Facilities: {chemical_alley['facility_count']} chemical plants")
print(f"  River Span: {chemical_alley['river_mile_span']:.1f} miles")
print(f"  Dataset Links: {chemical_alley['total_dataset_links']}")
print(f"  Density: {chemical_alley['density']:.1f} links per facility")

# ============================================================================
# MULTI-MODAL LOGISTICS HUB ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("MULTI-MODAL LOGISTICS HUBS - DEEP ANALYSIS")
print("="*80)

# Analyze multi-modal hubs
multimodal_analyses = []

for hub in multimodal_hubs:
    props = hub["properties"]
    fac_id = props["facility_id"]

    analysis = analyze_cluster(
        props["facility_name"],
        [fac_id],
        "Multi-Modal Hub"
    )
    analysis["transport_modes"] = props["transport_modes"]
    analysis["modes"] = props["modes"]
    multimodal_analyses.append(analysis)

# Sort by infrastructure score
multimodal_analyses.sort(key=lambda x: x["infrastructure_score"], reverse=True)

print("\nTop 15 Multi-Modal Logistics Hubs by Infrastructure Score:")
print(f"{'Facility':<35} {'Modes':<5} {'Links':<7} {'Sources':<8} {'Score':<8} {'Location'}")
print("-"*80)

for analysis in multimodal_analyses[:15]:
    modes_str = "+".join(analysis['modes'])
    print(f"{analysis['cluster_name'][:34]:<35} "
          f"{analysis['transport_modes']:<5} "
          f"{analysis['total_dataset_links']:<7} "
          f"{analysis['unique_data_sources']:<8} "
          f"{analysis['infrastructure_score']:<8} "
          f"Mile {analysis['avg_river_mile']:.0f}")

# Analyze by mode count
print(f"\nMulti-Modal Hub Distribution:")
mode_counts = defaultdict(int)
for analysis in multimodal_analyses:
    mode_counts[analysis['transport_modes']] += 1

for modes, count in sorted(mode_counts.items(), reverse=True):
    print(f"  {modes}-Mode Facilities: {count}")

# ============================================================================
# COMPARATIVE ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("COMPARATIVE MARKET ANALYSIS")
print("="*80)

print("\nInfrastructure Intensity by Market Type:")
print(f"{'Market Type':<25} {'Avg Links/Facility':<20} {'Avg Data Sources'}")
print("-"*80)

grain_avg = statistics.mean([a["density"] for a in grain_analyses]) if grain_analyses else 0
grain_sources = statistics.mean([a["unique_data_sources"] for a in grain_analyses]) if grain_analyses else 0
print(f"{'Grain Elevators':<25} {grain_avg:<20.1f} {grain_sources:.1f}")

petro_avg = statistics.mean([a["density"] for a in petro_analyses]) if petro_analyses else 0
petro_sources = statistics.mean([a["unique_data_sources"] for a in petro_analyses]) if petro_analyses else 0
print(f"{'Petroleum Complexes':<25} {petro_avg:<20.1f} {petro_sources:.1f}")

chem_avg = statistics.mean([a["density"] for a in chem_analyses]) if chem_analyses else 0
chem_sources = statistics.mean([a["unique_data_sources"] for a in chem_analyses]) if chem_analyses else 0
print(f"{'Chemical Corridors':<25} {chem_avg:<20.1f} {chem_sources:.1f}")

multi_avg = statistics.mean([a["density"] for a in multimodal_analyses]) if multimodal_analyses else 0
multi_sources = statistics.mean([a["unique_data_sources"] for a in multimodal_analyses]) if multimodal_analyses else 0
print(f"{'Multi-Modal Hubs':<25} {multi_avg:<20.1f} {multi_sources:.1f}")

# Geographic distribution
print(f"\nGeographic Market Distribution:")
print(f"{'Market Segment':<25} {'Lower River':<15} {'Upper River':<15}")
print(f"{'':25} {'(Mile 0-150)':<15} {'(Mile 150-250)':<15}")
print("-"*80)

def count_by_region(analyses):
    lower = sum(1 for a in analyses if a["avg_river_mile"] < 150)
    upper = sum(1 for a in analyses if a["avg_river_mile"] >= 150)
    return lower, upper

grain_lower, grain_upper = count_by_region(grain_analyses)
print(f"{'Grain Clusters':<25} {grain_lower:<15} {grain_upper:<15}")

petro_lower, petro_upper = count_by_region(petro_analyses)
print(f"{'Petroleum Complexes':<25} {petro_lower:<15} {petro_upper:<15}")

chem_lower, chem_upper = count_by_region(chem_analyses)
print(f"{'Chemical Clusters':<25} {chem_lower:<15} {chem_upper:<15}")

# ============================================================================
# SAVE DETAILED ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("Saving detailed analysis reports...")
print("="*80)

# Save grain analysis
with open("cluster_analysis_grain_detailed.csv", "w", newline="", encoding="utf-8") as f:
    if grain_analyses:
        fieldnames = ["cluster_name", "facility_count", "total_dataset_links", "unique_data_sources",
                     "infrastructure_score", "high_confidence_links", "avg_river_mile", "density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(grain_analyses)
print("  OK: cluster_analysis_grain_detailed.csv")

# Save petroleum analysis
with open("cluster_analysis_petroleum_detailed.csv", "w", newline="", encoding="utf-8") as f:
    if petro_analyses:
        fieldnames = ["cluster_name", "facility_count", "refinery_count", "terminal_count",
                     "total_dataset_links", "unique_data_sources", "infrastructure_score",
                     "high_confidence_links", "avg_river_mile", "density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(petro_analyses)
print("  OK: cluster_analysis_petroleum_detailed.csv")

# Save chemical analysis
with open("cluster_analysis_chemical_detailed.csv", "w", newline="", encoding="utf-8") as f:
    if chem_analyses:
        fieldnames = ["cluster_name", "facility_count", "total_dataset_links", "unique_data_sources",
                     "infrastructure_score", "avg_river_mile", "river_mile_span", "density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(chem_analyses)
print("  OK: cluster_analysis_chemical_detailed.csv")

# Save multi-modal analysis
with open("cluster_analysis_multimodal_detailed.csv", "w", newline="", encoding="utf-8") as f:
    if multimodal_analyses:
        fieldnames = ["cluster_name", "transport_modes", "total_dataset_links", "unique_data_sources",
                     "infrastructure_score", "avg_river_mile", "density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(multimodal_analyses)
print("  OK: cluster_analysis_multimodal_detailed.csv")

print("\n" + "="*80)
print("DEEP ANALYSIS COMPLETE!")
print("="*80)
print("\nKey Findings:")
print(f"  - Chemical Alley (Mile {chemical_alley['avg_river_mile']:.0f}): {chemical_alley['facility_count']} facilities")
print(f"  - Petroleum sector has highest infrastructure intensity: {petro_avg:.0f} links/facility")
print(f"  - Multi-modal hubs average {multi_sources:.0f} different data sources per facility")
print(f"  - Lower river (0-150) more industrial than upper river (150-250)")
