"""
Analyze National Market Clusters
Identify key industrial markets and their accessibility from Lower Mississippi River
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.cluster import DBSCAN

# Load facilities
NATIONAL_DIR = Path("national_supply_chain")
facilities = json.load(open(NATIONAL_DIR / "national_industrial_facilities.geojson"))

print("="*80)
print("NATIONAL MARKET CLUSTER ANALYSIS")
print("Industrial Density & Accessibility from Lower Mississippi River")
print("="*80)

# Convert to DataFrame
facility_data = []
for feat in facilities['features']:
    props = feat['properties']
    coords = feat['geometry']['coordinates']
    facility_data.append({
        'name': props['name'],
        'type': props['facility_type'],
        'lng': coords[0],
        'lat': coords[1],
        'city': props.get('city', ''),
        'state': props['state'],
        'waterway': props['waterway'],
        'region': props['region']
    })

df = pd.DataFrame(facility_data)

print(f"\nTotal facilities: {len(df)}")

# Geographic clustering using DBSCAN
print("\n" + "="*80)
print("IDENTIFYING GEOGRAPHIC MARKET CLUSTERS")
print("="*80)

coords = df[['lat', 'lng']].values

# Use DBSCAN for clustering - eps in degrees (roughly 50 miles = 0.7 degrees)
clustering = DBSCAN(eps=0.7, min_samples=5, metric='euclidean')
df['cluster'] = clustering.fit_predict(coords)

# Analyze clusters
clusters = []
for cluster_id in sorted(df['cluster'].unique()):
    if cluster_id == -1:  # Skip noise points
        continue

    cluster_df = df[df['cluster'] == cluster_id]

    # Get dominant states
    state_counts = cluster_df['state'].value_counts()
    dominant_states = ', '.join(state_counts.head(3).index.tolist())

    # Get dominant cities
    city_counts = cluster_df['city'].value_counts()
    top_cities = [c for c in city_counts.head(3).index.tolist() if c and c != 'nan']
    city_name = ', '.join(top_cities[:2]) if top_cities else dominant_states

    # Get facility type mix
    type_counts = cluster_df['type'].value_counts()
    dominant_type = type_counts.index[0] if len(type_counts) > 0 else 'MIXED'

    # Calculate center
    center_lat = cluster_df['lat'].mean()
    center_lng = cluster_df['lng'].mean()

    # Calculate distance from Lower Miss (approx New Orleans: 29.95, -90.07)
    lower_miss_lat, lower_miss_lng = 29.95, -90.07
    distance = np.sqrt((center_lat - lower_miss_lat)**2 + (center_lng - lower_miss_lng)**2) * 69  # degrees to miles

    # Accessibility score (inverse of distance, scaled by facility count)
    # Facilities closer to Lower Miss with more facilities score higher
    accessibility = (len(cluster_df) * 100) / (distance + 1)

    # Density (facilities per square degree area)
    lat_range = cluster_df['lat'].max() - cluster_df['lat'].min()
    lng_range = cluster_df['lng'].max() - cluster_df['lng'].min()
    area = max(lat_range * lng_range, 0.01)  # Avoid division by zero
    density = len(cluster_df) / area

    # Get waterway connections
    waterways = cluster_df['waterway'].value_counts()
    main_waterway = waterways.index[0] if len(waterways) > 0 else 'Unknown'
    if main_waterway and len(main_waterway) > 50:
        main_waterway = main_waterway[:50] + '...'

    clusters.append({
        'cluster_id': cluster_id,
        'name': city_name,
        'states': dominant_states,
        'facility_count': len(cluster_df),
        'center_lat': center_lat,
        'center_lng': center_lng,
        'distance_from_lower_miss': distance,
        'accessibility_score': accessibility,
        'density': density,
        'dominant_type': dominant_type,
        'type_diversity': len(type_counts),
        'main_waterway': main_waterway,
        'facility_types': dict(type_counts.head(5))
    })

clusters_df = pd.DataFrame(clusters)

# Rank by accessibility
print("\nTOP 15 MARKET CLUSTERS BY ACCESSIBILITY TO LOWER MISSISSIPPI")
print("(Considers both proximity and facility concentration)")
print("-"*80)
print(f"{'Rank':<5} {'Market':<25} {'State':<8} {'Fac':<5} {'Dist(mi)':<9} {'Access':<8} {'Main Waterway':<30}")
print("-"*80)

top_accessible = clusters_df.nlargest(15, 'accessibility_score')
for idx, row in enumerate(top_accessible.itertuples(), 1):
    print(f"{idx:<5} {row.name[:24]:<25} {row.states[:7]:<8} {row.facility_count:<5} "
          f"{row.distance_from_lower_miss:>8.0f} {row.accessibility_score:>7.1f} {row.main_waterway[:29]:<30}")

# Rank by density
print("\n" + "="*80)
print("TOP 15 MARKET CLUSTERS BY INDUSTRIAL DENSITY")
print("(Facilities per square degree)")
print("-"*80)
print(f"{'Rank':<5} {'Market':<25} {'State':<8} {'Fac':<5} {'Density':<10} {'Dominant Type':<20}")
print("-"*80)

top_dense = clusters_df.nlargest(15, 'density')
for idx, row in enumerate(top_dense.itertuples(), 1):
    dominant = row.dominant_type.replace('_', ' ').title()[:19]
    print(f"{idx:<5} {row.name[:24]:<25} {row.states[:7]:<8} {row.facility_count:<5} "
          f"{row.density:>9.1f} {dominant:<20}")

# Market segmentation by waterway
print("\n" + "="*80)
print("MARKET CLUSTERS BY MAJOR WATERWAY SYSTEM")
print("="*80)

waterway_markets = defaultdict(list)
for _, cluster in clusters_df.iterrows():
    waterway = cluster['main_waterway']
    if 'Mississippi' in waterway:
        if 'Mouth of Missouri' in waterway or 'Minneapolis' in waterway:
            waterway_markets['Upper Mississippi'].append(cluster)
        elif 'Mouth of Ohio' in waterway or 'Baton Rouge' in waterway:
            waterway_markets['Lower Mississippi'].append(cluster)
        else:
            waterway_markets['Middle Mississippi'].append(cluster)
    elif 'Ohio' in waterway:
        waterway_markets['Ohio River'].append(cluster)
    elif 'Illinois' in waterway:
        waterway_markets['Illinois River'].append(cluster)
    elif 'Tennessee' in waterway:
        waterway_markets['Tennessee River'].append(cluster)
    elif 'Missouri' in waterway:
        waterway_markets['Missouri River'].append(cluster)
    else:
        waterway_markets['Other Waterways'].append(cluster)

for waterway, cluster_list in sorted(waterway_markets.items(), key=lambda x: sum(c['facility_count'] for c in x[1]), reverse=True):
    total_fac = sum(c['facility_count'] for c in cluster_list)
    cluster_count = len(cluster_list)
    avg_distance = np.mean([c['distance_from_lower_miss'] for c in cluster_list])

    print(f"\n{waterway}:")
    print(f"  Market clusters: {cluster_count}")
    print(f"  Total facilities: {total_fac}")
    print(f"  Avg distance from Lower Miss: {avg_distance:.0f} miles")
    print(f"  Top markets:")

    for cluster in sorted(cluster_list, key=lambda x: x['facility_count'], reverse=True)[:3]:
        print(f"    - {cluster['name']} ({cluster['states']}): {cluster['facility_count']} facilities")

# Facility type concentration analysis
print("\n" + "="*80)
print("SPECIALIZED MARKET CLUSTERS")
print("="*80)

# Find clusters with >50% concentration in one type
specialized_clusters = []
for _, cluster in clusters_df.iterrows():
    total = cluster['facility_count']
    for fac_type, count in cluster['facility_types'].items():
        if count / total > 0.5 and total >= 5:  # >50% concentration, min 5 facilities
            specialized_clusters.append({
                'market': cluster['name'],
                'state': cluster['states'],
                'type': fac_type,
                'count': count,
                'total': total,
                'concentration': count/total,
                'distance': cluster['distance_from_lower_miss']
            })

spec_df = pd.DataFrame(specialized_clusters)
if len(spec_df) > 0:
    print(f"\n{'Market':<25} {'State':<8} {'Specialization':<20} {'Fac':<5} {'Conc%':<6} {'Dist(mi)':<9}")
    print("-"*80)
    for _, row in spec_df.sort_values('count', ascending=False).head(10).iterrows():
        spec_name = row['type'].replace('_', ' ').title()[:19]
        print(f"{row['market'][:24]:<25} {row['state'][:7]:<8} {spec_name:<20} "
              f"{row['count']:<5} {row['concentration']*100:>5.0f} {row['distance']:>8.0f}")

# Summary statistics
print("\n" + "="*80)
print("ACCESSIBILITY ZONES FROM LOWER MISSISSIPPI RIVER")
print("="*80)

zones = {
    'Direct Access (0-200 miles)': clusters_df[clusters_df['distance_from_lower_miss'] <= 200],
    'Near Access (200-400 miles)': clusters_df[(clusters_df['distance_from_lower_miss'] > 200) &
                                                (clusters_df['distance_from_lower_miss'] <= 400)],
    'Moderate Distance (400-700 miles)': clusters_df[(clusters_df['distance_from_lower_miss'] > 400) &
                                                       (clusters_df['distance_from_lower_miss'] <= 700)],
    'Long Haul (700+ miles)': clusters_df[clusters_df['distance_from_lower_miss'] > 700]
}

for zone_name, zone_df in zones.items():
    total_fac = df[df['cluster'].isin(zone_df['cluster_id'])]['name'].count()
    print(f"\n{zone_name}:")
    print(f"  Market clusters: {len(zone_df)}")
    print(f"  Total facilities: {total_fac}")
    if len(zone_df) > 0:
        print(f"  Avg facilities per cluster: {total_fac/len(zone_df):.1f}")

# Save detailed cluster data
output_file = NATIONAL_DIR / "market_clusters_analysis.csv"
clusters_df.to_csv(output_file, index=False)
print(f"\n" + "="*80)
print(f"Detailed cluster data saved to: {output_file}")
print("="*80)
