"""
Build National Supply Chain Map with Rail & Pipeline Infrastructure
"""

import json
from pathlib import Path

# Paths
NATIONAL_DIR = Path("national_supply_chain")
OUTPUT_DIR = Path("_html_web_files")

# Load data
print("Loading infrastructure layers...")
facilities = json.load(open(NATIONAL_DIR / "national_industrial_facilities.geojson"))
rail_network = json.load(open(NATIONAL_DIR / "rail_network_simplified.geojson"))
pipelines_product = json.load(open(NATIONAL_DIR / "pipelines_national.geojson"))
pipelines_hgl = json.load(open(NATIONAL_DIR / "pipelines_hgl.geojson"))
pipelines_crude = json.load(open(NATIONAL_DIR / "pipelines_crude.geojson"))
waterways = json.load(open(NATIONAL_DIR / "waterways_major.geojson"))

print(f"  Facilities: {len(facilities['features'])}")
print(f"  Rail segments: {len(rail_network['features'])}")
print(f"  Product pipelines: {len(pipelines_product['features'])}")
print(f"  HGL pipelines: {len(pipelines_hgl['features'])}")
print(f"  Crude pipelines: {len(pipelines_crude['features'])}")
print(f"  Waterways: {len(waterways['features'])}")

# Facility colors
FACILITY_COLORS = {
    'STEEL_MILL': '#8B0000', 'SMELTER': '#B22222', 'REFINERY': '#FF4500',
    'GRAIN_ELEVATOR': '#FFD700', 'CEMENT': '#696969', 'AGGREGATE': '#A9A9A9',
    'FERTILIZER': '#32CD32', 'CHEMICAL': '#9370DB', 'COAL_TERMINAL': '#000000',
    'PIPELINE_TERMINAL': '#FF8C00', 'TANK_TERMINAL': '#FF6347', 'GENERAL_CARGO': '#4682B4'
}

# Add colors to facilities
for feature in facilities['features']:
    fac_type = feature['properties']['facility_type']
    feature['properties']['marker_color'] = FACILITY_COLORS.get(fac_type, '#4682B4')

# Build HTML
html_content = """<!DOCTYPE html>
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
            max-height: 85vh;
            overflow-y: auto;
        }

        .legend-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
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
            margin: 12px 0 6px 0;
        }

        .legend-item {
            margin: 6px 0;
            display: flex;
            align-items: center;
            cursor: pointer;
        }

        .legend-item:hover {
            background: #f0f0f0;
            padding: 2px;
            margin: 4px -2px;
        }

        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid #333;
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
        }

        .legend-count {
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
    </style>
</head>
<body>

<div id="map"></div>

<div class="title-overlay">
    <div class="main-title">U.S. Bulk Commodity Supply Chain</div>
    <div class="subtitle">Mississippi River Basin + Great Lakes Industrial Infrastructure</div>
    <div class="subtitle" style="font-size: 12px; color: #777; margin-top: 10px;">
        Rail Networks • Pipelines • Industrial Facilities
    </div>
</div>

<div class="map-overlay">
    <div class="legend-title">Infrastructure Layers</div>

    <div class="legend-section">
        <div class="section-title">Transportation Networks</div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-waterways" checked onchange="toggleLayer('waterways')">
            <label for="toggle-waterways">
                <span class="legend-line" style="background: #4682B4; display: inline-block; vertical-align: middle; height: 4px;"></span>
                Rivers & Waterways
            </label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-rail" checked onchange="toggleLayer('rail-lines')">
            <label for="toggle-rail">
                <span class="legend-line" style="background: #8B4513; display: inline-block; vertical-align: middle;"></span>
                Class 1 Rail Network
            </label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-product" checked onchange="toggleLayer('pipeline-product')">
            <label for="toggle-product">
                <span class="legend-line" style="background: #FF6347; display: inline-block; vertical-align: middle;"></span>
                Product Pipelines
            </label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-crude" checked onchange="toggleLayer('pipeline-crude')">
            <label for="toggle-crude">
                <span class="legend-line" style="background: #000000; display: inline-block; vertical-align: middle;"></span>
                Crude Oil Pipelines
            </label>
        </div>

        <div class="checkbox-item">
            <input type="checkbox" id="toggle-hgl" checked onchange="toggleLayer('pipeline-hgl')">
            <label for="toggle-hgl">
                <span class="legend-line" style="background: #FF4500; display: inline-block; vertical-align: middle;"></span>
                HGL Pipelines
            </label>
        </div>
    </div>

    <div class="legend-section">
        <div class="section-title">Industrial Facilities</div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFD700;"></div>
            <div class="legend-label">Grain Elevators</div>
            <div class="legend-count" id="count-grain">178</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF4500;"></div>
            <div class="legend-label">Petroleum Refineries</div>
            <div class="legend-count" id="count-refinery">70</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #8B0000;"></div>
            <div class="legend-label">Steel Mills</div>
            <div class="legend-count" id="count-steel">55</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #696969;"></div>
            <div class="legend-label">Cement Plants</div>
            <div class="legend-count" id="count-cement">60</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #32CD32;"></div>
            <div class="legend-label">Fertilizer Plants</div>
            <div class="legend-count" id="count-fertilizer">33</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #9370DB;"></div>
            <div class="legend-label">Chemical Plants</div>
            <div class="legend-count" id="count-chemical">26</div>
        </div>

        <div class="legend-item">
            <div class="legend-color" style="background-color: #4682B4;"></div>
            <div class="legend-label">Other Facilities</div>
            <div class="legend-count" id="count-other">418</div>
        </div>
    </div>

    <div class="legend-section" style="border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
        <div class="stat-item" style="font-size: 11px; color: #777;">
            <strong>Total:</strong> 842 facilities across 18 states
        </div>
    </div>
</div>

<script>
const facilitiesData = """ + json.dumps(facilities) + """;
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
    if (visibility === 'visible') {
        map.setLayoutProperty(layerId, 'visibility', 'none');
    } else {
        map.setLayoutProperty(layerId, 'visibility', 'visible');
    }
}

map.on('load', () => {
    // Add waterways
    map.addSource('waterways', {
        type: 'geojson',
        data: waterwaysData
    });

    map.addLayer({
        id: 'waterways',
        type: 'line',
        source: 'waterways',
        paint: {
            'line-color': '#4682B4',
            'line-width': [
                'interpolate',
                ['linear'],
                ['zoom'],
                4, 2,
                8, 3,
                12, 4
            ],
            'line-opacity': 0.6
        }
    });

    // Add rail network
    map.addSource('rail', {
        type: 'geojson',
        data: railData
    });

    map.addLayer({
        id: 'rail-lines',
        type: 'line',
        source: 'rail',
        paint: {
            'line-color': '#8B4513',
            'line-width': 2,
            'line-opacity': 0.7
        }
    });

    // Add product pipelines
    map.addSource('pipeline-product', {
        type: 'geojson',
        data: pipelineProductData
    });

    map.addLayer({
        id: 'pipeline-product',
        type: 'line',
        source: 'pipeline-product',
        paint: {
            'line-color': '#FF6347',
            'line-width': 2,
            'line-opacity': 0.8
        }
    });

    // Add crude pipelines
    map.addSource('pipeline-crude', {
        type: 'geojson',
        data: pipelineCrudeData
    });

    map.addLayer({
        id: 'pipeline-crude',
        type: 'line',
        source: 'pipeline-crude',
        paint: {
            'line-color': '#000000',
            'line-width': 2,
            'line-opacity': 0.7
        }
    });

    // Add HGL pipelines
    map.addSource('pipeline-hgl', {
        type: 'geojson',
        data: pipelineHGLData
    });

    map.addLayer({
        id: 'pipeline-hgl',
        type: 'line',
        source: 'pipeline-hgl',
        paint: {
            'line-color': '#FF4500',
            'line-width': 2,
            'line-opacity': 0.7
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
            'circle-radius': ['step', ['get', 'point_count'], 15, 10, 20, 25, 25, 50, 30],
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
            'text-size': 12
        },
        paint: {
            'text-color': '#ffffff'
        }
    });

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

    // Facility click handler
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

    // Cluster click handler
    map.on('click', 'clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['clusters'] });
        const clusterId = features[0].properties.cluster_id;
        map.getSource('facilities').getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.easeTo({
                center: features[0].geometry.coordinates,
                zoom: zoom
            });
        });
    });

    // Cursor changes
    map.on('mouseenter', 'unclustered-point', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'unclustered-point', () => { map.getCanvas().style.cursor = ''; });
    map.on('mouseenter', 'clusters', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'clusters', () => { map.getCanvas().style.cursor = ''; });
});
</script>

</body>
</html>
"""

# Save
output_file = OUTPUT_DIR / "National_Supply_Chain_Infrastructure_Map.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\nNational Supply Chain Infrastructure Map Created!")
print(f"  Location: {output_file}")
print(f"\nLayers included:")
print(f"  - 842 Industrial facilities (color-coded by type)")
print(f"  - {len(waterways['features'])} River & waterway segments")
print(f"  - {len(rail_network['features'])} Class 1 rail segments")
print(f"  - {len(pipelines_product['features'])} Product pipeline segments")
print(f"  - {len(pipelines_crude['features'])} Crude oil pipeline segments")
print(f"  - {len(pipelines_hgl['features'])} HGL pipeline segments")
print(f"\nFeatures:")
print(f"  - Toggle infrastructure layers on/off")
print(f"  - Interactive facility clustering")
print(f"  - Click facilities for details")
print(f"  - Full Mississippi Basin + Great Lakes coverage")
print(f"\nMajor Waterways:")
print(f"  - Mississippi River (Upper, Middle, Lower)")
print(f"  - Ohio River")
print(f"  - Illinois River")
print(f"  - Missouri River")
print(f"  - Tennessee River")
print(f"  - Arkansas River")
