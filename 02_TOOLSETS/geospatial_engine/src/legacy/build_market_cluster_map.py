"""
Build National Supply Chain Map with Market Cluster Visualization
Shows industrial clusters color-coded by accessibility from Lower Mississippi
"""

import json
import pandas as pd
from pathlib import Path

# Paths
NATIONAL_DIR = Path("national_supply_chain")
OUTPUT_DIR = Path("_html_web_files")

# Load all data
print("Loading data layers...")
facilities = json.load(open(NATIONAL_DIR / "national_industrial_facilities.geojson"))
rail_network = json.load(open(NATIONAL_DIR / "rail_network_simplified.geojson"))
pipelines_product = json.load(open(NATIONAL_DIR / "pipelines_national.geojson"))
pipelines_hgl = json.load(open(NATIONAL_DIR / "pipelines_hgl.geojson"))
pipelines_crude = json.load(open(NATIONAL_DIR / "pipelines_crude.geojson"))
waterways = json.load(open(NATIONAL_DIR / "waterways_major.geojson"))
clusters_df = pd.read_csv(NATIONAL_DIR / "market_clusters_analysis.csv")

print(f"  Facilities: {len(facilities['features'])}")
print(f"  Market clusters: {len(clusters_df)}")

# Create market cluster GeoJSON
market_clusters = {
    "type": "FeatureCollection",
    "features": []
}

# Define accessibility zones and colors
def get_accessibility_zone(distance):
    if distance <= 200:
        return {"zone": "Direct Access", "color": "#00AA00", "tier": 1}
    elif distance <= 400:
        return {"zone": "Near Access", "color": "#66CC00", "tier": 2}
    elif distance <= 700:
        return {"zone": "Moderate Distance", "color": "#FFA500", "tier": 3}
    else:
        return {"zone": "Long Haul", "color": "#CC0000", "tier": 4}

for _, cluster in clusters_df.iterrows():
    zone_info = get_accessibility_zone(cluster['distance_from_lower_miss'])

    # Create circle feature for cluster
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [cluster['center_lng'], cluster['center_lat']]
        },
        "properties": {
            "cluster_id": int(cluster['cluster_id']),
            "name": cluster['name'],
            "states": cluster['states'],
            "facility_count": int(cluster['facility_count']),
            "distance": round(cluster['distance_from_lower_miss'], 0),
            "accessibility_score": round(cluster['accessibility_score'], 1),
            "density": round(cluster['density'], 1),
            "zone": zone_info['zone'],
            "zone_color": zone_info['color'],
            "tier": zone_info['tier'],
            "dominant_type": cluster['dominant_type'],
            "waterway": cluster['main_waterway'],
            "circle_radius": min(50 + cluster['facility_count'] * 200, 50000)  # Scale by facility count
        }
    }
    market_clusters['features'].append(feature)

print(f"  Created {len(market_clusters['features'])} market cluster visualizations")

# Add colors to facility features
FACILITY_COLORS = {
    'STEEL_MILL': '#8B0000', 'SMELTER': '#B22222', 'REFINERY': '#FF4500',
    'GRAIN_ELEVATOR': '#FFD700', 'CEMENT': '#696969', 'AGGREGATE': '#A9A9A9',
    'FERTILIZER': '#32CD32', 'CHEMICAL': '#9370DB', 'COAL_TERMINAL': '#000000',
    'PIPELINE_TERMINAL': '#FF8C00', 'TANK_TERMINAL': '#FF6347', 'GENERAL_CARGO': '#4682B4'
}

for feature in facilities['features']:
    fac_type = feature['properties']['facility_type']
    feature['properties']['marker_color'] = FACILITY_COLORS.get(fac_type, '#4682B4')

# Build enhanced HTML
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>National Bulk Commodity Markets - Accessibility Analysis</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }

        .map-overlay {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 320px;
            max-height: 85vh;
            overflow-y: auto;
        }

        .legend-title {
            font-size: 17px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
        }

        .legend-section {
            margin: 15px 0;
        }

        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #555;
            margin: 12px 0 8px 0;
        }

        .legend-item {
            margin: 8px 0;
            display: flex;
            align-items: center;
        }

        .legend-circle {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid #333;
            opacity: 0.7;
        }

        .legend-line {
            width: 30px;
            height: 3px;
            margin-right: 10px;
            border-radius: 2px;
        }

        .legend-label {
            font-size: 12px;
            color: #333;
            flex: 1;
        }

        .legend-stat {
            font-size: 11px;
            color: #666;
            margin-left: auto;
            padding-left: 8px;
        }

        .title-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 450px;
        }

        .main-title {
            font-size: 24px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 14px;
            color: #555;
            margin-bottom: 4px;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }

        .checkbox-item input {
            margin-right: 8px;
        }

        .checkbox-item label {
            font-size: 13px;
            color: #333;
            cursor: pointer;
        }

        .mapboxgl-popup-content {
            max-width: 400px;
            padding: 15px;
        }

        .popup-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1a1a1a;
        }

        .popup-section {
            margin: 12px 0;
            padding: 8px 0;
            border-top: 1px solid #eee;
        }

        .popup-label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .popup-value {
            font-size: 14px;
            color: #333;
            margin-top: 2px;
        }

        .zone-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            margin-top: 5px;
        }

        .tier-1 { background: #00AA00; }
        .tier-2 { background: #66CC00; }
        .tier-3 { background: #FFA500; }
        .tier-4 { background: #CC0000; }

        .stat-highlight {
            font-size: 16px;
            font-weight: bold;
            color: #007cbf;
        }
    </style>
</head>
<body>

<div id="map"></div>

<div class="title-overlay">
    <div class="main-title">U.S. Bulk Commodity Market Clusters</div>
    <div class="subtitle">Industrial Accessibility from Lower Mississippi River</div>
    <div class="subtitle" style="font-size: 12px; color: #777; margin-top: 10px;">
        16 Major Market Zones • 842 Industrial Facilities
    </div>
</div>

<div class="map-overlay">
    <div class="legend-title">Market Accessibility Zones</div>

    <div class="legend-section">
        <div class="legend-item">
            <div class="legend-circle" style="background-color: #00AA00;"></div>
            <div class="legend-label">Direct Access (0-200 mi)</div>
            <div class="legend-stat">45 fac</div>
        </div>

        <div class="legend-item">
            <div class="legend-circle" style="background-color: #FFA500;"></div>
            <div class="legend-label">Moderate Distance (400-700 mi)</div>
            <div class="legend-stat">347 fac</div>
        </div>

        <div class="legend-item">
            <div class="legend-circle" style="background-color: #CC0000;"></div>
            <div class="legend-label">Long Haul (700+ mi)</div>
            <div class="legend-stat">403 fac</div>
        </div>
    </div>

    <div class="legend-section">
        <div class="section-title">Top 5 Markets</div>
        <div style="font-size: 11px; line-height: 1.6; color: #555;">
            1. <strong>Memphis/Cincinnati</strong> - 292 fac<br>
            2. <strong>Chicago/Illinois River</strong> - 190 fac<br>
            3. <strong>Pittsburgh</strong> - 73 fac<br>
            4. <strong>Cleveland/Detroit</strong> - 72 fac<br>
            5. <strong>Houma/Port Fourchon</strong> - 45 fac
        </div>
    </div>

    <div class="legend-section">
        <div class="section-title">Infrastructure Layers</div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-clusters" checked onchange="toggleLayer('market-clusters')">
            <label for="toggle-clusters">Market Cluster Zones</label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-waterways" checked onchange="toggleLayer('waterways')">
            <label for="toggle-waterways">Rivers & Waterways</label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-rail" checked onchange="toggleLayer('rail-lines')">
            <label for="toggle-rail">Class 1 Rail</label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-pipelines" checked onchange="togglePipelines()">
            <label for="toggle-pipelines">Pipelines (All)</label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-facilities" checked onchange="toggleFacilities()">
            <label for="toggle-facilities">Industrial Facilities</label>
        </div>
    </div>

    <div class="legend-section" style="border-top: 1px solid #ddd; padding-top: 10px; margin-top: 15px;">
        <div style="font-size: 11px; color: #777;">
            <strong>Circle size</strong> = facility concentration<br>
            Click clusters or facilities for details
        </div>
    </div>
</div>

<script>
const facilitiesData = """ + json.dumps(facilities) + """;
const marketClustersData = """ + json.dumps(market_clusters) + """;
const railData = """ + json.dumps(rail_network) + """;
const pipelineProductData = """ + json.dumps(pipelines_product) + """;
const pipelineCrudeData = """ + json.dumps(pipelines_crude) + """;
const pipelineHGLData = """ + json.dumps(pipelines_hgl) + """;
const waterwaysData = """ + json.dumps(waterways) + """;

mapboxgl.accessToken = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v11',
    center: [-90.0, 39.0],
    zoom: 4.5
});

function toggleLayer(layerId) {
    const visibility = map.getLayoutProperty(layerId, 'visibility');
    map.setLayoutProperty(layerId, 'visibility', visibility === 'visible' ? 'none' : 'visible');
}

function togglePipelines() {
    ['pipeline-product', 'pipeline-crude', 'pipeline-hgl'].forEach(layer => toggleLayer(layer));
}

function toggleFacilities() {
    ['clusters', 'cluster-count', 'unclustered-point'].forEach(layer => toggleLayer(layer));
}

map.on('load', () => {
    // Add waterways
    map.addSource('waterways', { type: 'geojson', data: waterwaysData });
    map.addLayer({
        id: 'waterways',
        type: 'line',
        source: 'waterways',
        paint: {
            'line-color': '#4682B4',
            'line-width': ['interpolate', ['linear'], ['zoom'], 4, 2, 8, 3, 12, 4],
            'line-opacity': 0.5
        }
    });

    // Add rail
    map.addSource('rail', { type: 'geojson', data: railData });
    map.addLayer({
        id: 'rail-lines',
        type: 'line',
        source: 'rail',
        paint: { 'line-color': '#8B4513', 'line-width': 2, 'line-opacity': 0.6 }
    });

    // Add pipelines
    map.addSource('pipeline-product', { type: 'geojson', data: pipelineProductData });
    map.addLayer({
        id: 'pipeline-product',
        type: 'line',
        source: 'pipeline-product',
        paint: { 'line-color': '#FF6347', 'line-width': 2, 'line-opacity': 0.7 }
    });

    map.addSource('pipeline-crude', { type: 'geojson', data: pipelineCrudeData });
    map.addLayer({
        id: 'pipeline-crude',
        type: 'line',
        source: 'pipeline-crude',
        paint: { 'line-color': '#000000', 'line-width': 2, 'line-opacity': 0.6 }
    });

    map.addSource('pipeline-hgl', { type: 'geojson', data: pipelineHGLData });
    map.addLayer({
        id: 'pipeline-hgl',
        type: 'line',
        source: 'pipeline-hgl',
        paint: { 'line-color': '#FF4500', 'line-width': 2, 'line-opacity': 0.6 }
    });

    // Add market clusters
    map.addSource('market-clusters', { type: 'geojson', data: marketClustersData });

    // Cluster circles
    map.addLayer({
        id: 'market-clusters',
        type: 'circle',
        source: 'market-clusters',
        paint: {
            'circle-color': ['get', 'zone_color'],
            'circle-radius': ['interpolate', ['linear'], ['get', 'facility_count'], 5, 15, 50, 30, 200, 50, 300, 70],
            'circle-opacity': 0.25,
            'circle-stroke-width': 3,
            'circle-stroke-color': ['get', 'zone_color'],
            'circle-stroke-opacity': 0.8
        }
    });

    // Cluster labels
    map.addLayer({
        id: 'market-cluster-labels',
        type: 'symbol',
        source: 'market-clusters',
        layout: {
            'text-field': ['concat', ['get', 'name'], '\\n', ['get', 'facility_count'], ' facilities'],
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12,
            'text-offset': [0, 0],
            'text-anchor': 'center'
        },
        paint: {
            'text-color': '#000',
            'text-halo-color': '#fff',
            'text-halo-width': 2
        }
    });

    // Add facilities
    map.addSource('facilities', {
        type: 'geojson',
        data: facilitiesData,
        cluster: true,
        clusterMaxZoom: 8,
        clusterRadius: 40
    });

    map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'facilities',
        filter: ['has', 'point_count'],
        paint: {
            'circle-color': ['step', ['get', 'point_count'], '#51bbd6', 10, '#f1f075', 25, '#f28cb1', 50, '#e55e5e'],
            'circle-radius': ['step', ['get', 'point_count'], 12, 10, 17, 25, 22, 50, 27],
            'circle-stroke-width': 2,
            'circle-stroke-color': '#fff'
        }
    });

    map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'facilities',
        filter: ['has', 'point_count'],
        layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 11
        },
        paint: { 'text-color': '#ffffff' }
    });

    map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'facilities',
        filter: ['!', ['has', 'point_count']],
        paint: {
            'circle-color': ['get', 'marker_color'],
            'circle-radius': 5,
            'circle-stroke-width': 1.5,
            'circle-stroke-color': '#fff'
        }
    });

    // Market cluster click popup
    map.on('click', 'market-clusters', (e) => {
        const props = e.features[0].properties;
        const coords = e.features[0].geometry.coordinates.slice();

        const popupHTML = `
            <div class="popup-title">${props.name}</div>
            <div class="zone-badge tier-${props.tier}">${props.zone}</div>

            <div class="popup-section">
                <div class="popup-label">Market Size</div>
                <div class="popup-value"><span class="stat-highlight">${props.facility_count}</span> industrial facilities</div>
            </div>

            <div class="popup-section">
                <div class="popup-label">Distance from Lower Mississippi</div>
                <div class="popup-value">${props.distance} miles</div>
            </div>

            <div class="popup-section">
                <div class="popup-label">Accessibility Score</div>
                <div class="popup-value">${props.accessibility_score} (proximity × density)</div>
            </div>

            <div class="popup-section">
                <div class="popup-label">Primary Waterway</div>
                <div class="popup-value">${props.waterway}</div>
            </div>

            <div class="popup-section">
                <div class="popup-label">Location</div>
                <div class="popup-value">${props.states}</div>
            </div>
        `;

        new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(popupHTML)
            .addTo(map);
    });

    // Facility click handler
    map.on('click', 'unclustered-point', (e) => {
        const props = e.features[0].properties;
        const coords = e.features[0].geometry.coordinates.slice();

        const popupHTML = `
            <div class="popup-title" style="font-size: 14px;">${props.name}</div>
            <div style="display: inline-block; padding: 3px 8px; background: #007cbf; color: white; border-radius: 3px; font-size: 10px; font-weight: bold; margin-top: 6px;">
                ${props.facility_type.replace(/_/g, ' ')}
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #555;">
                <strong>Location:</strong> ${props.city}, ${props.state}<br>
                <strong>Waterway:</strong> ${props.waterway}
            </div>
        `;

        new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(popupHTML)
            .addTo(map);
    });

    // Cluster click to zoom
    map.on('click', 'clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['clusters'] });
        const clusterId = features[0].properties.cluster_id;
        map.getSource('facilities').getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.easeTo({ center: features[0].geometry.coordinates, zoom: zoom });
        });
    });

    // Cursor changes
    ['market-clusters', 'unclustered-point', 'clusters'].forEach(layer => {
        map.on('mouseenter', layer, () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', layer, () => { map.getCanvas().style.cursor = ''; });
    });
});
</script>

</body>
</html>
"""

# Save
output_file = OUTPUT_DIR / "National_Market_Clusters_Map.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\nMarket Cluster Map Created!")
print(f"  Location: {output_file}")
print(f"\nVisualization features:")
print(f"  - 16 market cluster zones (color-coded by accessibility)")
print(f"  - Circle size scaled by facility concentration")
print(f"  - 842 individual facilities (toggleable)")
print(f"  - Rivers, rail, pipelines (toggleable)")
print(f"  - Click clusters for detailed statistics")
