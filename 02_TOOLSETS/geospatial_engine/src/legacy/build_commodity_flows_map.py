"""
Build Commodity Flow Map
Layered by commodity type with flow visualization to Lower Mississippi
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Paths
NATIONAL_DIR = Path("national_supply_chain")
OUTPUT_DIR = Path("_html_web_files")

print("="*80)
print("BUILDING COMMODITY FLOW MAP")
print("="*80)

# Load data
facilities = json.load(open(NATIONAL_DIR / "national_industrial_facilities.geojson"))
clusters_df = pd.read_csv(NATIONAL_DIR / "market_clusters_analysis.csv")
waterways = json.load(open(NATIONAL_DIR / "waterways_major.geojson"))
rail_network = json.load(open(NATIONAL_DIR / "rail_network_simplified.geojson"))

print(f"\nLoaded {len(facilities['features'])} facilities")

# Organize facilities by commodity type
commodity_layers = defaultdict(list)

for feature in facilities['features']:
    fac_type = feature['properties']['facility_type']
    commodity_layers[fac_type].append(feature)

# Create separate GeoJSON for each commodity type
commodity_geojsons = {}

for commodity, features in commodity_layers.items():
    commodity_geojsons[commodity] = {
        "type": "FeatureCollection",
        "features": features
    }

print(f"\nCommodity layer breakdown:")
for commodity, geojson in sorted(commodity_geojsons.items(), key=lambda x: len(x[1]['features']), reverse=True):
    print(f"  {commodity.replace('_', ' ').title()}: {len(geojson['features'])} facilities")

# Create commodity flow lines
# Flow from major production clusters to Lower Mississippi River (New Orleans area)
lower_miss_destination = [-90.07, 29.95]  # New Orleans

commodity_flows = {
    "type": "FeatureCollection",
    "features": []
}

# Define major production clusters and their primary commodities
production_hubs = [
    {"name": "Chicago Grain Belt", "coords": [-87.9, 41.5], "commodity": "GRAIN_ELEVATOR", "facilities": 190},
    {"name": "Ohio River Steel", "coords": [-80.0, 40.4], "commodity": "STEEL_MILL", "facilities": 55},
    {"name": "Memphis Distribution", "coords": [-90.0, 35.1], "commodity": "GENERAL_CARGO", "facilities": 100},
    {"name": "Cleveland/Detroit Steel", "coords": [-83.0, 41.5], "commodity": "STEEL_MILL", "facilities": 72},
    {"name": "Illinois Refineries", "coords": [-89.5, 39.8], "commodity": "REFINERY", "facilities": 20},
    {"name": "Tennessee Valley", "coords": [-86.7, 34.7], "commodity": "CHEMICAL", "facilities": 26},
    {"name": "Minnesota Grain", "coords": [-93.2, 44.9], "commodity": "GRAIN_ELEVATOR", "facilities": 25},
    {"name": "Gulf Petrochemicals", "coords": [-90.5, 30.2], "commodity": "REFINERY", "facilities": 45},
]

# Create curved flow lines from each hub to Lower Mississippi
for hub in production_hubs:
    # Create curved line (simple midpoint offset)
    start_lng, start_lat = hub['coords']
    end_lng, end_lat = lower_miss_destination

    # Calculate midpoint with offset for curve
    mid_lng = (start_lng + end_lng) / 2
    mid_lat = (start_lat + end_lat) / 2

    # Offset perpendicular to flow direction for curve
    offset = 2.0  # degrees
    mid_lng += offset

    flow_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [start_lng, start_lat],
                [mid_lng, mid_lat],
                [end_lng, end_lat]
            ]
        },
        "properties": {
            "origin": hub['name'],
            "commodity": hub['commodity'],
            "facilities": hub['facilities'],
            "destination": "Lower Mississippi Export Terminals"
        }
    }
    commodity_flows['features'].append(flow_feature)

print(f"\nCreated {len(commodity_flows['features'])} commodity flow routes")

# Build HTML map
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>U.S. Commodity Flows to Lower Mississippi River</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }

        .control-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.98);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.3);
            max-width: 320px;
            max-height: 85vh;
            overflow-y: auto;
        }

        .panel-title {
            font-size: 18px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007cbf;
        }

        .section {
            margin: 20px 0;
        }

        .section-header {
            font-size: 14px;
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .commodity-toggle {
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 6px 0;
            background: #f8f8f8;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .commodity-toggle:hover {
            background: #e8e8e8;
            transform: translateX(2px);
        }

        .commodity-toggle input[type="checkbox"] {
            margin-right: 10px;
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .commodity-label {
            flex: 1;
            font-size: 13px;
            font-weight: 500;
            color: #333;
        }

        .commodity-count {
            font-size: 11px;
            color: #666;
            background: white;
            padding: 3px 8px;
            border-radius: 10px;
        }

        .commodity-color {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            margin-right: 8px;
            border: 1px solid #999;
        }

        .infrastructure-toggle {
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 5px 0;
            cursor: pointer;
        }

        .infrastructure-toggle input {
            margin-right: 8px;
        }

        .infrastructure-toggle label {
            font-size: 12px;
            color: #555;
            cursor: pointer;
        }

        .title-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.98);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.3);
            max-width: 450px;
        }

        .main-title {
            font-size: 26px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 15px;
            color: #555;
            margin: 5px 0;
        }

        .help-text {
            font-size: 12px;
            color: #777;
            margin-top: 12px;
            font-style: italic;
        }

        .mapboxgl-popup-content {
            max-width: 350px;
            padding: 15px;
        }

        .popup-title {
            font-size: 16px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 8px;
        }

        .popup-detail {
            font-size: 13px;
            color: #555;
            margin: 5px 0;
        }

        .flow-popup {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
        }

        .flow-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .flow-detail {
            font-size: 13px;
            margin: 5px 0;
            opacity: 0.95;
        }

        .active-layer {
            background: #e3f2fd !important;
            border-left: 4px solid #007cbf;
        }
    </style>
</head>
<body>

<div id="map"></div>

<div class="title-overlay">
    <div class="main-title">U.S. Commodity Flows</div>
    <div class="subtitle">Bulk Commodity Supply Chains to Lower Mississippi River</div>
    <div class="help-text">
        Toggle commodity types to see production regions and flow patterns.
        Arrows show movement from production clusters to export terminals.
    </div>
</div>

<div class="control-panel">
    <div class="panel-title">Commodity Layers</div>

    <div class="section">
        <div class="section-header">Primary Commodities</div>

        <div class="commodity-toggle" onclick="toggleCommodity('GRAIN_ELEVATOR', this)">
            <input type="checkbox" id="grain-check" checked>
            <div class="commodity-color" style="background: #FFD700;"></div>
            <div class="commodity-label">Grain Elevators</div>
            <div class="commodity-count">178</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('REFINERY', this)">
            <input type="checkbox" id="refinery-check">
            <div class="commodity-color" style="background: #FF4500;"></div>
            <div class="commodity-label">Petroleum Refineries</div>
            <div class="commodity-count">70</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('STEEL_MILL', this)">
            <input type="checkbox" id="steel-check">
            <div class="commodity-color" style="background: #8B0000;"></div>
            <div class="commodity-label">Steel Mills</div>
            <div class="commodity-count">55</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('CHEMICAL', this)">
            <input type="checkbox" id="chemical-check">
            <div class="commodity-color" style="background: #9370DB;"></div>
            <div class="commodity-label">Chemical Plants</div>
            <div class="commodity-count">26</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('FERTILIZER', this)">
            <input type="checkbox" id="fertilizer-check">
            <div class="commodity-color" style="background: #32CD32;"></div>
            <div class="commodity-label">Fertilizer Plants</div>
            <div class="commodity-count">33</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('CEMENT', this)">
            <input type="checkbox" id="cement-check">
            <div class="commodity-color" style="background: #696969;"></div>
            <div class="commodity-label">Cement Plants</div>
            <div class="commodity-count">60</div>
        </div>

        <div class="commodity-toggle" onclick="toggleCommodity('COAL_TERMINAL', this)">
            <input type="checkbox" id="coal-check">
            <div class="commodity-color" style="background: #000000;"></div>
            <div class="commodity-label">Coal Terminals</div>
            <div class="commodity-count">39</div>
        </div>
    </div>

    <div class="section">
        <div class="section-header">Infrastructure</div>

        <div class="infrastructure-toggle">
            <input type="checkbox" id="flows-check" checked onchange="toggleLayer('commodity-flows')">
            <label for="flows-check">Commodity Flow Routes</label>
        </div>

        <div class="infrastructure-toggle">
            <input type="checkbox" id="waterways-check" checked onchange="toggleLayer('waterways')">
            <label for="waterways-check">Rivers & Waterways</label>
        </div>

        <div class="infrastructure-toggle">
            <input type="checkbox" id="rail-check" onchange="toggleLayer('rail-lines')">
            <label for="rail-check">Rail Network</label>
        </div>
    </div>

    <div class="section" style="border-top: 1px solid #ddd; padding-top: 15px; margin-top: 15px;">
        <div style="font-size: 12px; color: #777; line-height: 1.5;">
            <strong>Total:</strong> 842 facilities<br>
            <strong>Flow Routes:</strong> 8 major corridors<br>
            <strong>Click</strong> facilities or flows for details
        </div>
    </div>
</div>

<script>
// Data
const commodityData = {
    GRAIN_ELEVATOR: """ + json.dumps(commodity_geojsons.get('GRAIN_ELEVATOR', {"type": "FeatureCollection", "features": []})) + """,
    REFINERY: """ + json.dumps(commodity_geojsons.get('REFINERY', {"type": "FeatureCollection", "features": []})) + """,
    STEEL_MILL: """ + json.dumps(commodity_geojsons.get('STEEL_MILL', {"type": "FeatureCollection", "features": []})) + """,
    CHEMICAL: """ + json.dumps(commodity_geojsons.get('CHEMICAL', {"type": "FeatureCollection", "features": []})) + """,
    FERTILIZER: """ + json.dumps(commodity_geojsons.get('FERTILIZER', {"type": "FeatureCollection", "features": []})) + """,
    CEMENT: """ + json.dumps(commodity_geojsons.get('CEMENT', {"type": "FeatureCollection", "features": []})) + """,
    COAL_TERMINAL: """ + json.dumps(commodity_geojsons.get('COAL_TERMINAL', {"type": "FeatureCollection", "features": []})) + """
};

const flowsData = """ + json.dumps(commodity_flows) + """;
const waterwaysData = """ + json.dumps(waterways) + """;
const railData = """ + json.dumps(rail_network) + """;

const commodityColors = {
    GRAIN_ELEVATOR: '#FFD700',
    REFINERY: '#FF4500',
    STEEL_MILL: '#8B0000',
    CHEMICAL: '#9370DB',
    FERTILIZER: '#32CD32',
    CEMENT: '#696969',
    COAL_TERMINAL: '#000000'
};

mapboxgl.accessToken = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v11',
    center: [-90.0, 37.0],
    zoom: 4.5
});

function toggleLayer(layerId) {
    const visibility = map.getLayoutProperty(layerId, 'visibility');
    map.setLayoutProperty(layerId, 'visibility', visibility === 'visible' ? 'none' : 'visible');
}

function toggleCommodity(commodity, element) {
    const checkbox = element.querySelector('input[type="checkbox"]');
    const isChecked = checkbox.checked;

    // Toggle layer visibility
    map.setLayoutProperty('facilities-' + commodity, 'visibility', isChecked ? 'visible' : 'none');
    map.setLayoutProperty('flow-' + commodity, 'visibility', isChecked ? 'visible' : 'none');

    // Toggle active styling
    if (isChecked) {
        element.classList.add('active-layer');
    } else {
        element.classList.remove('active-layer');
    }
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
            'line-width': ['interpolate', ['linear'], ['zoom'], 4, 2, 8, 3],
            'line-opacity': 0.4
        }
    });

    // Add rail
    map.addSource('rail', { type: 'geojson', data: railData });
    map.addLayer({
        id: 'rail-lines',
        type: 'line',
        source: 'rail',
        layout: { 'visibility': 'none' },
        paint: { 'line-color': '#8B4513', 'line-width': 2, 'line-opacity': 0.5 }
    });

    // Add commodity flow lines
    map.addSource('flows', { type: 'geojson', data: flowsData });

    // Add commodity-specific layers
    Object.keys(commodityData).forEach(commodity => {
        // Facility points
        map.addSource('facilities-' + commodity, {
            type: 'geojson',
            data: commodityData[commodity]
        });

        map.addLayer({
            id: 'facilities-' + commodity,
            type: 'circle',
            source: 'facilities-' + commodity,
            layout: { 'visibility': commodity === 'GRAIN_ELEVATOR' ? 'visible' : 'none' },
            paint: {
                'circle-color': commodityColors[commodity],
                'circle-radius': 6,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#fff',
                'circle-opacity': 0.8
            }
        });

        // Flow lines for this commodity
        map.addLayer({
            id: 'flow-' + commodity,
            type: 'line',
            source: 'flows',
            filter: ['==', ['get', 'commodity'], commodity],
            layout: {
                'visibility': commodity === 'GRAIN_ELEVATOR' ? 'visible' : 'none',
                'line-cap': 'round'
            },
            paint: {
                'line-color': commodityColors[commodity],
                'line-width': 4,
                'line-opacity': 0.7,
                'line-gradient': [
                    'interpolate',
                    ['linear'],
                    ['line-progress'],
                    0, commodityColors[commodity],
                    1, '#ffffff'
                ]
            }
        });

        // Click handler for facilities
        map.on('click', 'facilities-' + commodity, (e) => {
            const props = e.features[0].properties;
            const coords = e.features[0].geometry.coordinates.slice();

            const popupHTML = `
                <div class="popup-title">${props.name}</div>
                <div style="display: inline-block; padding: 4px 10px; background: ${commodityColors[commodity]}; color: white; border-radius: 4px; font-size: 11px; font-weight: bold; margin: 8px 0;">
                    ${commodity.replace(/_/g, ' ')}
                </div>
                <div class="popup-detail"><strong>Location:</strong> ${props.city}, ${props.state}</div>
                <div class="popup-detail"><strong>Waterway:</strong> ${props.waterway}</div>
            `;

            new mapboxgl.Popup()
                .setLngLat(coords)
                .setHTML(popupHTML)
                .addTo(map);
        });

        // Cursor
        map.on('mouseenter', 'facilities-' + commodity, () => {
            map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'facilities-' + commodity, () => {
            map.getCanvas().style.cursor = '';
        });
    });

    // Flow line click handler
    map.on('click', 'commodity-flows', (e) => {
        const props = e.features[0].properties;
        const coords = e.lngLat;

        const popupHTML = `
            <div class="flow-popup">
                <div class="flow-title">🚢 Commodity Flow Route</div>
                <div class="flow-detail"><strong>Origin:</strong> ${props.origin}</div>
                <div class="flow-detail"><strong>Destination:</strong> ${props.destination}</div>
                <div class="flow-detail"><strong>Facilities:</strong> ${props.facilities}</div>
                <div class="flow-detail"><strong>Commodity:</strong> ${props.commodity.replace(/_/g, ' ')}</div>
            </div>
        `;

        new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(popupHTML)
            .addTo(map);
    });

    // Set initial active state for grain
    document.querySelector('.commodity-toggle').classList.add('active-layer');
});
</script>

</body>
</html>
"""

# Save
output_file = OUTPUT_DIR / "Commodity_Flows_Map.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n" + "="*80)
print("COMMODITY FLOW MAP CREATED!")
print("="*80)
print(f"Location: {output_file}")
print(f"\nFeatures:")
print(f"  - 7 commodity-specific toggleable layers")
print(f"  - 8 major commodity flow routes")
print(f"  - Clean interface - toggle one commodity at a time")
print(f"  - Flow lines from production to Lower Mississippi")
print(f"  - Color-coded by commodity type")
print(f"\nDefault view: Grain elevators + grain flow routes")
