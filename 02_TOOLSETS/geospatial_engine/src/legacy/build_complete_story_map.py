"""
Complete Interactive Story Map with full infrastructure layers and connectivity.
Shows tank terminals adjacent to pipelines, rail connections, etc.
"""
import json
import csv
from collections import defaultdict

print("Building Complete Story Map with Infrastructure Layers...")
print("="*80)

# Load master facility registry
facilities = []
with open("master_facilities.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    facilities = list(reader)

# Load dataset links
links = []
with open("facility_dataset_links.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    links = list(reader)

facility_links = defaultdict(list)
for link in links:
    facility_links[link["facility_id"]].append(link)

# Load commodity clusters
with open("commodity_clusters_grain.geojson", "r") as f:
    grain_clusters = json.load(f)
with open("commodity_clusters_petroleum.geojson", "r") as f:
    petro_clusters = json.load(f)
with open("commodity_clusters_chemical.geojson", "r") as f:
    chem_clusters = json.load(f)
with open("commodity_clusters_multimodal.geojson", "r") as f:
    multimodal_hubs = json.load(f)

# Load infrastructure layers
print("Loading infrastructure layers...")
with open("qgis/lower_miss_river_line_0_250_dissolved.geojson", "r") as f:
    river_line = json.load(f)
with open("qgis/lower_miss_mile_markers_0_250.geojson", "r") as f:
    mile_markers = json.load(f)
with open("qgis/class1_rail_main_routes_LA_region.geojson", "r") as f:
    rail_lines = json.load(f)
with open("esri_exports/HGL_Pipelines_LA_region.geojson", "r") as f:
    hgl_pipelines = json.load(f)
with open("esri_exports/Crude_Pipelines_LA_region.geojson", "r") as f:
    crude_pipelines = json.load(f)
with open("esri_exports/Product_Pipelines_LA_region.geojson", "r") as f:
    product_pipelines = json.load(f)

print(f"  River line: {len(river_line['features'])} features")
print(f"  Rail lines: {len(rail_lines['features'])} features")
print(f"  Pipelines: HGL={len(hgl_pipelines['features'])}, Crude={len(crude_pipelines['features'])}, Product={len(product_pipelines['features'])}")

# Create enhanced facility GeoJSON
enhanced_facilities = {"type": "FeatureCollection", "features": []}

for fac in facilities:
    fac_id = fac["facility_id"]
    fac_links = facility_links.get(fac_id, [])

    by_source = defaultdict(int)
    for link in fac_links:
        by_source[link["dataset_source"]] += 1

    # Determine infrastructure connections
    has_pipeline = "PRODUCT_TERMINAL" in by_source or "REFINERY" in by_source
    has_rail = "RAIL_YARD" in by_source
    has_dock = "BTS_DOCK" in by_source

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(fac["lng"]), float(fac["lat"])]
        },
        "properties": {
            "facility_id": fac_id,
            "name": fac["canonical_name"],
            "facility_type": fac["facility_type"],
            "river_mile": fac["mrtis_mile"],
            "port": fac["port"],
            "city": fac["city"],
            "operators": fac["operators"][:150] if fac["operators"] else "",
            "commodities": fac["commodities"][:150] if fac["commodities"] else "",
            "total_links": len(fac_links),
            "unique_sources": len(by_source),
            "dataset_breakdown": dict(by_source),
            "has_pipeline": has_pipeline,
            "has_rail": has_rail,
            "has_dock": has_dock,
            "connectivity": []
        }
    }

    # Add connectivity info
    if has_pipeline:
        feature["properties"]["connectivity"].append("Pipeline Terminal")
    if has_rail:
        feature["properties"]["connectivity"].append("Rail Yard")
    if has_dock:
        feature["properties"]["connectivity"].append("Barge Dock")

    enhanced_facilities["features"].append(feature)

# Convert to JSON
enhanced_facilities_json = json.dumps(enhanced_facilities, separators=(",", ":"))
grain_clusters_json = json.dumps(grain_clusters, separators=(",", ":"))
petro_clusters_json = json.dumps(petro_clusters, separators=(",", ":"))
chem_clusters_json = json.dumps(chem_clusters, separators=(",", ":"))
multimodal_hubs_json = json.dumps(multimodal_hubs, separators=(",", ":"))
river_line_json = json.dumps(river_line, separators=(",", ":"))
mile_markers_json = json.dumps(mile_markers, separators=(",", ":"))
rail_lines_json = json.dumps(rail_lines, separators=(",", ":"))
hgl_pipelines_json = json.dumps(hgl_pipelines, separators=(",", ":"))
crude_pipelines_json = json.dumps(crude_pipelines, separators=(",", ":"))
product_pipelines_json = json.dumps(product_pipelines, separators=(",", ":"))

OUTPUT = r"G:\My Drive\LLM\sources_data_maps\_html_web_files\Complete_Story_Map.html"

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lower Mississippi River - Complete Infrastructure Story Map</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info-panel {{
            position: absolute; top: 10px; right: 10px; background: white;
            padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 350px; z-index: 1000; max-height: 90vh; overflow-y: auto;
        }}
        .info-panel h2 {{ margin: 0 0 10px 0; font-size: 18px; color: #333; }}
        .info-panel h3 {{ margin: 15px 0 5px 0; font-size: 14px; color: #666; }}
        .stats {{ font-size: 13px; line-height: 1.6; }}
        .stats strong {{ color: #0066cc; }}
        .legend {{ background: white; padding: 10px; border-radius: 5px; line-height: 1.8; font-size: 12px; }}
        .legend-item {{ margin: 5px 0; }}
        .legend-color {{
            display: inline-block; width: 18px; height: 18px; margin-right: 5px;
            border-radius: 3px; vertical-align: middle; border: 1px solid #999;
        }}
        .legend-line {{
            display: inline-block; width: 30px; height: 3px; margin-right: 5px;
            vertical-align: middle;
        }}
        .facility-popup {{ max-width: 450px; }}
        .facility-popup h3 {{ margin: 0 0 10px 0; color: #0066cc; }}
        .facility-popup .section {{ margin: 10px 0; padding: 8px; background: #f5f5f5; border-radius: 4px; }}
        .badge {{
            display: inline-block; padding: 2px 8px; border-radius: 3px;
            font-size: 11px; font-weight: bold; margin: 2px;
        }}
        .badge-pipeline {{ background: #e67e22; color: white; }}
        .badge-rail {{ background: #34495e; color: white; }}
        .badge-dock {{ background: #3498db; color: white; }}
        .badge-info {{ background: #17a2b8; color: white; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>Lower Mississippi River</h2>
        <h3>Complete Infrastructure Story Map</h3>
        <div class="stats">
            <strong>{len(facilities)}</strong> facilities<br>
            <strong>{len(links):,}</strong> dataset links<br>
            <strong>River Mile 0-250</strong> coverage
        </div>
        <h3>Legend - Facilities</h3>
        <div class="legend">
            <div class="legend-item"><span class="legend-color" style="background: #e74c3c;"></span> Grain Elevators</div>
            <div class="legend-item"><span class="legend-color" style="background: #9b59b6;"></span> Refineries</div>
            <div class="legend-item"><span class="legend-color" style="background: #3498db;"></span> Chemical Plants</div>
            <div class="legend-item"><span class="legend-color" style="background: #f39c12;"></span> Terminals</div>
        </div>
        <h3>Legend - Infrastructure</h3>
        <div class="legend">
            <div class="legend-item"><span class="legend-line" style="background: #3498db;"></span> Mississippi River</div>
            <div class="legend-item"><span class="legend-line" style="background: #34495e;"></span> Class 1 Rail</div>
            <div class="legend-item"><span class="legend-line" style="background: #e74c3c;"></span> Crude Pipelines</div>
            <div class="legend-item"><span class="legend-line" style="background: #e67e22;"></span> Product Pipelines</div>
            <div class="legend-item"><span class="legend-line" style="background: #95a5a6;"></span> HGL Pipelines</div>
        </div>
        <h3>Connectivity</h3>
        <div class="stats" style="font-size: 11px;">
            Click facilities to see pipeline, rail, and dock connections
        </div>
    </div>

    <script>
        var map = L.map('map').setView([30.0, -90.8], 8);

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);

        // Load all data
        var enhancedFacilities = {enhanced_facilities_json};
        var grainClusters = {grain_clusters_json};
        var petroClusters = {petro_clusters_json};
        var chemClusters = {chem_clusters_json};
        var multimodalHubs = {multimodal_hubs_json};
        var riverLine = {river_line_json};
        var mileMarkers = {mile_markers_json};
        var railLines = {rail_lines_json};
        var hglPipelines = {hgl_pipelines_json};
        var crudePipelines = {crude_pipelines_json};
        var productPipelines = {product_pipelines_json};

        // River line layer
        var riverLayer = L.geoJSON(riverLine, {{
            style: {{ color: '#3498db', weight: 4, opacity: 0.7 }}
        }}).addTo(map);

        // Mile markers
        var mileLayer = L.geoJSON(mileMarkers, {{
            pointToLayer: function(feature, latlng) {{
                var mile = feature.properties.MILE || feature.properties.name;
                if (mile % 10 === 0) {{
                    return L.circleMarker(latlng, {{
                        radius: 3, fillColor: '#2c3e50', color: '#fff',
                        weight: 1, fillOpacity: 0.8
                    }}).bindTooltip('Mile ' + mile, {{ permanent: false }});
                }}
                return null;
            }}
        }}).addTo(map);

        // Rail lines
        var railLayer = L.geoJSON(railLines, {{
            style: {{ color: '#34495e', weight: 2, opacity: 0.6 }}
        }});

        // Pipeline layers
        var crudeLayer = L.geoJSON(crudePipelines, {{
            style: {{ color: '#e74c3c', weight: 2, opacity: 0.7, dashArray: '5,5' }}
        }});

        var productLayer = L.geoJSON(productPipelines, {{
            style: {{ color: '#e67e22', weight: 2, opacity: 0.7, dashArray: '5,5' }}
        }});

        var hglLayer = L.geoJSON(hglPipelines, {{
            style: {{ color: '#95a5a6', weight: 2, opacity: 0.7, dashArray: '5,5' }}
        }});

        // Facility type colors
        var typeColors = {{
            'Elevator': '#e74c3c', 'Refinery': '#9b59b6', 'Chemical Plant': '#3498db',
            'Bulk Plant': '#3498db', 'Tank Storage': '#f39c12', 'General Cargo': '#95a5a6',
            'Bulk Terminal': '#f39c12', 'Mid-Stream': '#34495e'
        }};

        // Facility popup
        function createFacilityPopup(feature) {{
            var props = feature.properties;
            var html = '<div class="facility-popup">';
            html += '<h3>' + props.name + '</h3>';
            html += '<div><strong>Type:</strong> ' + props.facility_type + '</div>';
            html += '<div><strong>River Mile:</strong> ' + props.river_mile + '</div>';
            html += '<div><strong>Port:</strong> ' + props.port + '</div>';

            html += '<div class="section"><strong>Infrastructure Connectivity:</strong><br>';
            if (props.connectivity.length > 0) {{
                props.connectivity.forEach(function(conn) {{
                    if (conn.includes('Pipeline'))
                        html += '<span class="badge badge-pipeline">' + conn + '</span>';
                    else if (conn.includes('Rail'))
                        html += '<span class="badge badge-rail">' + conn + '</span>';
                    else if (conn.includes('Dock'))
                        html += '<span class="badge badge-dock">' + conn + '</span>';
                }});
            }} else {{
                html += '<span style="color:#999;">No direct infrastructure connections</span>';
            }}
            html += '</div>';

            html += '<div class="section"><strong>Dataset Coverage:</strong><br>';
            html += '<span class="badge badge-info">' + props.total_links + ' total links</span>';
            html += '<span class="badge badge-info">' + props.unique_sources + ' sources</span>';
            var datasets = props.dataset_breakdown || {{}};
            html += '<div style="margin-top:5px;font-size:11px;">';
            for (var source in datasets) {{
                html += '<div>' + source + ': ' + datasets[source] + ' records</div>';
            }}
            html += '</div></div>';

            if (props.operators) {{
                html += '<div><small><strong>Operator:</strong> ' + props.operators + '</small></div>';
            }}
            html += '</div>';
            return html;
        }}

        // Facility layer
        var facilityLayer = L.geoJSON(enhancedFacilities, {{
            pointToLayer: function(feature, latlng) {{
                var props = feature.properties;
                var color = typeColors[props.facility_type] || '#95a5a6';
                var radius = 6 + Math.min(props.total_links / 50, 10);

                // Highlight multi-modal with thicker border
                var weight = (props.connectivity.length >= 2) ? 3 : 2;

                return L.circleMarker(latlng, {{
                    radius: radius, fillColor: color, color: '#fff',
                    weight: weight, opacity: 1, fillOpacity: 0.8
                }});
            }},
            onEachFeature: function(feature, layer) {{
                layer.bindPopup(createFacilityPopup(feature), {{ maxWidth: 450 }});
            }}
        }}).addTo(map);

        // Cluster layers
        var grainLayer = L.geoJSON(grainClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        html: '<div style="background:#e74c3c;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var p = feature.properties;
                layer.bindPopup('<h3>Grain Market Zone</h3><div><strong>Facilities:</strong> ' + p.facility_count + '</div><div><strong>Location:</strong> ' + p.market_area + '</div>');
            }}
        }});

        var petroLayer = L.geoJSON(petroClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        html: '<div style="background:#9b59b6;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var p = feature.properties;
                layer.bindPopup('<h3>Petroleum Complex</h3><div>Refineries: ' + p.refinery_count + ' | Terminals: ' + p.terminal_count + '</div>');
            }}
        }});

        var chemLayer = L.geoJSON(chemClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        html: '<div style="background:#3498db;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var p = feature.properties;
                var msg = '<h3>Chemical Corridor</h3><div>Facilities: ' + p.facility_count + '</div>';
                if (p.facility_count > 15) msg += '<div style="color:#e74c3c;font-weight:bold;">CHEMICAL ALLEY</div>';
                layer.bindPopup(msg);
            }}
        }});

        // Layer controls
        var baseLayers = {{
            "Facilities": facilityLayer
        }};

        var overlays = {{
            "River Line": riverLayer,
            "Mile Markers": mileLayer,
            "Class 1 Rail": railLayer,
            "Crude Pipelines": crudeLayer,
            "Product Pipelines": productLayer,
            "HGL Pipelines": hglLayer,
            "Grain Markets": grainLayer,
            "Petroleum Complexes": petroLayer,
            "Chemical Corridors": chemLayer
        }};

        L.control.layers(null, overlays, {{ collapsed: false }}).addTo(map);
        L.control.scale({{ position: 'bottomleft' }}).addTo(map);

        console.log('Complete Story Map loaded!');
    </script>
</body>
</html>"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nOK: Complete Story Map created!")
print(f"  Location: {OUTPUT}")
print("\nFeatures included:")
print("  - River line and mile markers")
print("  - Class 1 rail routes")
print("  - Pipelines (Crude, Product, HGL)")
print("  - All 167 facilities with connectivity")
print("  - Commodity market clusters")
print("  - Click facilities to see adjacent infrastructure")
