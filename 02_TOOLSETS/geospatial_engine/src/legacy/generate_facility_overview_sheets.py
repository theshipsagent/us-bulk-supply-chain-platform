"""
Generate facility overview sheets showing all connected dataset records.
Demonstrates the entity resolution system with real examples.
"""
import csv
import json
from collections import defaultdict

# Load master facilities
facilities = []
with open("master_facilities.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    facilities = list(reader)

# Load dataset links
links = []
with open("facility_dataset_links.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    links = list(reader)

# Group links by facility
facility_links = defaultdict(list)
for link in links:
    facility_links[link["facility_id"]].append(link)

# Find facilities with most diverse dataset coverage
facility_scores = []
for fac in facilities:
    fac_id = fac["facility_id"]
    fac_links = facility_links.get(fac_id, [])

    # Count unique dataset sources
    sources = set(link["dataset_source"] for link in fac_links)

    # Score by number of links and diversity
    score = len(fac_links) * len(sources)

    facility_scores.append({
        "facility": fac,
        "link_count": len(fac_links),
        "source_count": len(sources),
        "sources": sources,
        "score": score
    })

# Sort by score
facility_scores.sort(key=lambda x: x["score"], reverse=True)

# Pick top facilities from different types
selected = []
seen_types = set()

# First pass: get one of each major type
for fs in facility_scores:
    fac_type = fs["facility"]["facility_type"]
    if fac_type not in seen_types and len(selected) < 6:
        selected.append(fs)
        seen_types.add(fac_type)

# Fill remaining slots with highest scoring
for fs in facility_scores:
    if fs not in selected and len(selected) < 10:
        selected.append(fs)

print("="*80)
print("SAMPLE FACILITY OVERVIEW SHEETS")
print("Lower Mississippi River Industrial Infrastructure")
print("="*80)

for i, fs in enumerate(selected[:6], 1):
    fac = fs["facility"]
    fac_id = fac["facility_id"]
    fac_links = facility_links.get(fac_id, [])

    print(f"\n{'#'*80}")
    print(f"FACILITY #{i}: {fac['canonical_name']}")
    print(f"{'#'*80}")

    # Basic info
    print(f"\n{'-'*80}")
    print("BASIC INFORMATION")
    print(f"{'-'*80}")
    print(f"Facility ID:      {fac_id}")
    print(f"Canonical Name:   {fac['canonical_name']}")
    print(f"Zone Name:        {fac['zone_name']}")
    print(f"Type:             {fac['facility_type']}")
    print(f"Location:         {fac['city']}, {fac['county']}, {fac['state']}")
    print(f"Coordinates:      {fac['lat']}, {fac['lng']}")
    print(f"River Mile:       MRTIS {fac['mrtis_mile']} / USACE {fac['usace_mile']}")
    print(f"Waterway:         {fac['waterway']}")
    print(f"Port:             {fac['port']}")
    print(f"Owners:           {fac['owners'][:100]}...")
    print(f"Operators:        {fac['operators'][:100]}...")
    print(f"Commodities:      {fac['commodities'][:100]}...")

    # Dataset coverage
    print(f"\n{'-'*80}")
    print(f"DATASET COVERAGE: {len(fac_links)} total records from {len(fs['sources'])} sources")
    print(f"{'-'*80}")

    # Group by source
    by_source = defaultdict(list)
    for link in fac_links:
        by_source[link["dataset_source"]].append(link)

    for source in sorted(by_source.keys()):
        source_links = by_source[source]
        print(f"\n  [{source}] - {len(source_links)} records")

        # Show HIGH and MEDIUM confidence matches first
        high_med = [l for l in source_links if l["match_confidence"] in ["HIGH", "MEDIUM"]]
        if high_med:
            print(f"    High-quality matches: {len(high_med)}")
            for link in high_med[:3]:  # Show top 3
                dist = float(link["distance_meters"])
                sim = float(link["name_similarity"])
                print(f"      - {link['source_name'][:50]}")
                print(f"        Distance: {dist:.0f}m | Name match: {sim:.1%} | Confidence: {link['match_confidence']}")
                if link.get('source_city'):
                    print(f"        Location: {link['source_city']}, {link.get('source_county', '')}")

        # Summary of LOW confidence
        low = [l for l in source_links if l["match_confidence"] == "LOW"]
        if low:
            print(f"    Additional matches (LOW confidence): {len(low)}")
            if len(low) <= 3:
                for link in low:
                    print(f"      - {link['source_name'][:50]} ({float(link['distance_meters']):.0f}m)")

    # High-confidence summary
    high_conf_links = [l for l in fac_links if l["match_confidence"] == "HIGH"]
    if high_conf_links:
        print(f"\n{'-'*80}")
        print(f"HIGH CONFIDENCE MATCHES ({len(high_conf_links)})")
        print(f"{'-'*80}")
        for link in high_conf_links:
            print(f"  {link['dataset_source']:20s} | {link['source_name'][:45]:45s} | {float(link['distance_meters']):5.0f}m | {float(link['name_similarity']):.1%}")

    print()

# Generate summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTop 10 Facilities by Dataset Coverage:")
print(f"{'Rank':<6} {'Facility':<40} {'Links':<8} {'Sources':<10} {'Types'}")
print("-"*80)
for i, fs in enumerate(selected[:10], 1):
    fac = fs["facility"]
    sources_str = ", ".join(sorted(fs["sources"]))[:30] + "..."
    print(f"{i:<6} {fac['canonical_name'][:40]:<40} {fs['link_count']:<8} {fs['source_count']:<10} {sources_str}")

print(f"\nDataset Source Coverage Across All Facilities:")
all_sources = defaultdict(int)
for link in links:
    all_sources[link["dataset_source"]] += 1

for source, count in sorted(all_sources.items(), key=lambda x: x[1], reverse=True):
    print(f"  {source:20s}: {count:5d} records")

print("\n" + "="*80)
print("Facility overview sheets complete!")
print("="*80)
