"""
Build National Supply Chain Interactive Map
Mississippi River Basin + Great Lakes Industrial Infrastructure
"""

import json
from pathlib import Path

# Paths
NATIONAL_DIR = Path("national_supply_chain")
OUTPUT_DIR = Path("_html_web_files")
OUTPUT_DIR.mkdir(exist_ok=True)

# Load national facilities
facilities_geojson = json.load(open(NATIONAL_DIR / "national_industrial_facilities.geojson"))

print(f"Loading {len(facilities_geojson['features'])} national industrial facilities...")

# Facility type colors
FACILITY_COLORS = {
    'STEEL_MILL': '#8B0000',           # Dark Red
    'SMELTER': '#B22222',              # Fire Brick
    'REFINERY': '#FF4500',             # Orange Red
    'GRAIN_ELEVATOR': '#FFD700',       # Gold
    'CEMENT': '#696969',               # Dim Gray
    'AGGREGATE': '#A9A9A9',            # Dark Gray
    'FERTILIZER': '#32CD32',           # Lime Green
    'CHEMICAL': '#9370DB',             # Medium Purple
    'COAL_TERMINAL': '#000000',        # Black
    'PIPELINE_TERMINAL': '#FF8C00',    # Dark Orange
    'TANK_TERMINAL': '#FF6347',        # Tomato
    'GENERAL_CARGO': '#4682B4'         # Steel Blue
}

# Enhanced facility properties with colors
for feature in facilities_geojson['features']:
    fac_type = feature['properties']['facility_type']
    feature['properties']['marker_color'] = FACILITY_COLORS.get(fac_type, '#4682B4')

# HTML map template
html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>National Bulk Commodity Supply Chain Infrastructure</title>
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
            max-width: 300px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .legend-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }

        .legend-item {
            margin: 8px 0;
            display: flex;
            align-items: center;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid #333;
        }

        .legend-label {
            font-size: 13px;
            color: #333;
        }

        .legend-count {
            font-size: 11px;
            color: #666;
            margin-left: auto;
            padding-left: 10px;
        }

        .stats-section {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px solid #ddd;
        }

        .stat-item {
            margin: 6px 0;
            font-size: 12px;
            color: #555;
        }

        .stat-label {
            font-weight: bold;
            color: #333;
        }

        .title-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 400px;
        }

        .main-title {
            font-size: 22px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 14px;
            color: #555;
            margin-bottom: 4px;
        }

        .mapboxgl-popup-content {
            max-width: 350px;
            padding: 15px;
        }

        .popup-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1a1a1a;
        }

        .popup-detail {
            margin: 5px 0;
            font-size: 13px;
            color: #555;
        }

        .popup-type {
            display: inline-block;
            padding: 4px 8px;
            background: #007cbf;
            color: white;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-top: 8px;
        }
    </style>
</head>
<body>

<div id="map"></div>

<div class="title-overlay">
    <div class="main-title">U.S. Bulk Commodity Supply Chain</div>
    <div class="subtitle">Mississippi River Basin + Great Lakes Industrial Infrastructure</div>
    <div class="subtitle" style="font-size: 12px; color: #777; margin-top: 10px;">
        Steel Mills • Refineries • Grain Elevators • Chemical Plants • Cement • Fertilizer
    </div>
</div>

<div class="map-overlay">
    <div class="legend-title">Industrial Facility Types</div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #FFD700;"></div>
        <div class="legend-label">Grain Elevators</div>
        <div class="legend-count" id="count-grain">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #FF4500;"></div>
        <div class="legend-label">Petroleum Refineries</div>
        <div class="legend-count" id="count-refinery">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #8B0000;"></div>
        <div class="legend-label">Steel Mills</div>
        <div class="legend-count" id="count-steel">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #696969;"></div>
        <div class="legend-label">Cement Plants</div>
        <div class="legend-count" id="count-cement">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #32CD32;"></div>
        <div class="legend-label">Fertilizer Plants</div>
        <div class="legend-count" id="count-fertilizer">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #9370DB;"></div>
        <div class="legend-label">Chemical Plants</div>
        <div class="legend-count" id="count-chemical">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #000000;"></div>
        <div class="legend-label">Coal Terminals</div>
        <div class="legend-count" id="count-coal">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #A9A9A9;"></div>
        <div class="legend-label">Aggregate Terminals</div>
        <div class="legend-count" id="count-aggregate">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #FF8C00;"></div>
        <div class="legend-label">Pipeline Terminals</div>
        <div class="legend-count" id="count-pipeline">0</div>
    </div>

    <div class="legend-item">
        <div class="legend-color" style="background-color: #4682B4;"></div>
        <div class="legend-label">General Cargo/Other</div>
        <div class="legend-count" id="count-general">0</div>
    </div>

    <div class="stats-section">
        <div class="stat-item">
            <span class="stat-label">Total Facilities:</span> <span id="total-facilities">0</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">States Covered:</span> <span id="total-states">18</span>
        </div>
        <div class="stat-item" style="margin-top: 10px; font-size: 11px; color: #777;">
            Click any facility marker for details
        </div>
    </div>
</div>

<script>
const facilitiesData = """ + json.dumps(facilities_geojson) + """;

// Initialize map
mapboxgl.accessToken = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw'; // Public Mapbox token

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v11',
    center: [-90.0, 39.0], // Center on Mississippi River Basin
    zoom: 4.5
});

map.on('load', () => {
    // Add facilities source
    map.addSource('facilities', {
        type: 'geojson',
        data: facilitiesData,
        cluster: true,
        clusterMaxZoom: 8,
        clusterRadius: 40
    });

    // Clustered circles
    map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'facilities',
        filter: ['has', 'point_count'],
        paint: {
            'circle-color': [
                'step',
                ['get', 'point_count'],
                '#51bbd6', 10,
                '#f1f075', 25,
                '#f28cb1', 50,
                '#e55e5e'
            ],
            'circle-radius': [
                'step',
                ['get', 'point_count'],
                15, 10,
                20, 25,
                25, 50,
                30
            ],
            'circle-stroke-width': 2,
            'circle-stroke-color': '#fff'
        }
    });

    // Cluster count labels
    map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'facilities',
        filter: ['has', 'point_count'],
        layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12
        },
        paint: {
            'text-color': '#ffffff'
        }
    });

    // Individual facility points
    map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'facilities',
        filter: ['!', ['has', 'point_count']],
        paint: {
            'circle-color': ['get', 'marker_color'],
            'circle-radius': 6,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#fff'
        }
    });

    // Click event for facilities
    map.on('click', 'unclustered-point', (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const props = e.features[0].properties;

        const popupHTML = `
            <div class="popup-title">${props.name}</div>
            <div class="popup-type">${props.facility_type.replace(/_/g, ' ')}</div>
            <div class="popup-detail"><strong>Location:</strong> ${props.city}, ${props.state}</div>
            <div class="popup-detail"><strong>Waterway:</strong> ${props.waterway}</div>
            ${props.commodities && props.commodities !== 'nan' ?
                `<div class="popup-detail"><strong>Commodities:</strong> ${props.commodities.substring(0, 150)}...</div>` : ''}
        `;

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(popupHTML)
            .addTo(map);
    });

    // Click clusters to zoom
    map.on('click', 'clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, {
            layers: ['clusters']
        });
        const clusterId = features[0].properties.cluster_id;
        map.getSource('facilities').getClusterExpansionZoom(
            clusterId,
            (err, zoom) => {
                if (err) return;

                map.easeTo({
                    center: features[0].geometry.coordinates,
                    zoom: zoom
                });
            }
        );
    });

    // Change cursor on hover
    map.on('mouseenter', 'unclustered-point', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'unclustered-point', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('mouseenter', 'clusters', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'clusters', () => {
        map.getCanvas().style.cursor = '';
    });

    // Update facility counts
    updateCounts();
});

function updateCounts() {
    const counts = {
        grain: 0,
        refinery: 0,
        steel: 0,
        cement: 0,
        fertilizer: 0,
        chemical: 0,
        coal: 0,
        aggregate: 0,
        pipeline: 0,
        general: 0
    };

    facilitiesData.features.forEach(f => {
        const type = f.properties.facility_type;
        if (type === 'GRAIN_ELEVATOR') counts.grain++;
        else if (type === 'REFINERY') counts.refinery++;
        else if (type === 'STEEL_MILL') counts.steel++;
        else if (type === 'CEMENT') counts.cement++;
        else if (type === 'FERTILIZER') counts.fertilizer++;
        else if (type === 'CHEMICAL') counts.chemical++;
        else if (type === 'COAL_TERMINAL') counts.coal++;
        else if (type === 'AGGREGATE') counts.aggregate++;
        else if (type === 'PIPELINE_TERMINAL') counts.pipeline++;
        else counts.general++;
    });

    document.getElementById('count-grain').textContent = counts.grain;
    document.getElementById('count-refinery').textContent = counts.refinery;
    document.getElementById('count-steel').textContent = counts.steel;
    document.getElementById('count-cement').textContent = counts.cement;
    document.getElementById('count-fertilizer').textContent = counts.fertilizer;
    document.getElementById('count-chemical').textContent = counts.chemical;
    document.getElementById('count-coal').textContent = counts.coal;
    document.getElementById('count-aggregate').textContent = counts.aggregate;
    document.getElementById('count-pipeline').textContent = counts.pipeline;
    document.getElementById('count-general').textContent = counts.general;
    document.getElementById('total-facilities').textContent = facilitiesData.features.length;
}
</script>

</body>
</html>
"""

# Save HTML file
output_file = OUTPUT_DIR / "National_Supply_Chain_Map.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"\nNational Supply Chain Map Created!")
print(f"  Location: {output_file}")
print(f"  Facilities: {len(facilities_geojson['features'])}")
print(f"\nFeatures:")
print(f"  - Interactive clustering for performance")
print(f"  - Color-coded by facility type")
print(f"  - Click facilities for detailed pop-ups")
print(f"  - Coverage: Mississippi Basin + Great Lakes")
print(f"  - 18 states, 842 industrial facilities")
