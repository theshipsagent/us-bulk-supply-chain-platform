"""
Enhanced Interactive Story Map - Lower Mississippi River Industrial Infrastructure
Integrates master facility registry, commodity market clusters, and dataset links.
"""
import json
import csv
from collections import defaultdict

print("Building Enhanced Interactive Story Map...")
print("="*80)

# Load master facility registry
print("\nLoading master facility registry...")
facilities = []
with open("master_facilities.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    facilities = list(reader)

print(f"  Facilities: {len(facilities)}")

# Load dataset links
print("Loading dataset links...")
links = []
with open("facility_dataset_links.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    links = list(reader)

print(f"  Dataset links: {len(links)}")

# Group links by facility
facility_links = defaultdict(list)
for link in links:
    facility_links[link["facility_id"]].append(link)

# Load commodity clusters
print("Loading commodity market clusters...")
with open("commodity_clusters_grain.geojson", "r") as f:
    grain_clusters = json.load(f)

with open("commodity_clusters_petroleum.geojson", "r") as f:
    petro_clusters = json.load(f)

with open("commodity_clusters_chemical.geojson", "r") as f:
    chem_clusters = json.load(f)

with open("commodity_clusters_multimodal.geojson", "r") as f:
    multimodal_hubs = json.load(f)

print(f"  Grain clusters: {len(grain_clusters['features'])}")
print(f"  Petroleum clusters: {len(petro_clusters['features'])}")
print(f"  Chemical clusters: {len(chem_clusters['features'])}")
print(f"  Multi-modal hubs: {len(multimodal_hubs['features'])}")

# Create enhanced facility GeoJSON with dataset links
print("\nCreating enhanced facility layer...")
enhanced_facilities = {"type": "FeatureCollection", "features": []}

for fac in facilities:
    fac_id = fac["facility_id"]
    fac_links = facility_links.get(fac_id, [])

    # Count by dataset source
    by_source = defaultdict(int)
    for link in fac_links:
        by_source[link["dataset_source"]] += 1

    # Count high confidence
    high_conf = sum(1 for l in fac_links if l["match_confidence"] == "HIGH")

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(fac["lng"]), float(fac["lat"])]
        },
        "properties": {
            "facility_id": fac_id,
            "name": fac["canonical_name"],
            "zone_name": fac["zone_name"],
            "facility_type": fac["facility_type"],
            "river_mile": fac["mrtis_mile"],
            "usace_mile": fac["usace_mile"],
            "port": fac["port"],
            "city": fac["city"],
            "county": fac["county"],
            "operators": fac["operators"][:100] if fac["operators"] else "",
            "commodities": fac["commodities"][:100] if fac["commodities"] else "",
            "total_links": len(fac_links),
            "unique_sources": len(by_source),
            "high_conf_links": high_conf,
            "dataset_breakdown": dict(by_source)
        }
    }
    enhanced_facilities["features"].append(feature)

print(f"  Created {len(enhanced_facilities['features'])} enhanced facility points")

# Save enhanced data as JSON variables for embedding
enhanced_facilities_json = json.dumps(enhanced_facilities, separators=(",", ":"))
grain_clusters_json = json.dumps(grain_clusters, separators=(",", ":"))
petro_clusters_json = json.dumps(petro_clusters, separators=(",", ":"))
chem_clusters_json = json.dumps(chem_clusters, separators=(",", ":"))
multimodal_hubs_json = json.dumps(multimodal_hubs, separators=(",", ":"))

# Build HTML
print("\nBuilding HTML map...")

OUTPUT = r"G:\My Drive\LLM\sources_data_maps\_html_web_files\Enhanced_Story_Map.html"

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lower Mississippi River Industrial Infrastructure - Interactive Story Map</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 350px;
            z-index: 1000;
            max-height: 90vh;
            overflow-y: auto;
        }}
        .info-panel h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
            color: #333;
        }}
        .info-panel h3 {{
            margin: 15px 0 5px 0;
            font-size: 14px;
            color: #666;
        }}
        .stats {{
            font-size: 13px;
            line-height: 1.6;
        }}
        .stats strong {{
            color: #0066cc;
        }}
        .legend {{
            background: white;
            padding: 10px;
            border-radius: 5px;
            line-height: 1.8;
            font-size: 12px;
        }}
        .legend-item {{
            margin: 5px 0;
        }}
        .legend-color {{
            display: inline-block;
            width: 18px;
            height: 18px;
            margin-right: 5px;
            border-radius: 3px;
            vertical-align: middle;
            border: 1px solid #999;
        }}
        .facility-popup {{
            max-width: 400px;
        }}
        .facility-popup h3 {{
            margin: 0 0 10px 0;
            color: #0066cc;
        }}
        .facility-popup .section {{
            margin: 10px 0;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        .facility-popup .dataset-list {{
            margin: 5px 0;
            padding-left: 15px;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin: 2px;
        }}
        .badge-high {{ background: #28a745; color: white; }}
        .badge-medium {{ background: #ffc107; color: black; }}
        .badge-info {{ background: #17a2b8; color: white; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>Lower Mississippi River</h2>
        <h3>Industrial Infrastructure Story Map</h3>
        <div class="stats">
            <strong>{len(facilities)}</strong> facilities<br>
            <strong>{len(links):,}</strong> government dataset links<br>
            <strong>6</strong> data sources integrated<br>
            <strong>{len(grain_clusters['features'])}</strong> grain market zones<br>
            <strong>{len(petro_clusters['features'])}</strong> petroleum complexes<br>
            <strong>{len(chem_clusters['features'])}</strong> chemical corridors<br>
            <strong>{len(multimodal_hubs['features'])}</strong> multi-modal hubs
        </div>
        <h3>How to Use</h3>
        <div class="stats" style="font-size: 11px;">
            • Click any facility to see all connected government datasets<br>
            • Use layer controls (top right) to toggle markets<br>
            • Zoom in/out to explore different regions<br>
            • Clusters show market concentration
        </div>
        <h3>Legend</h3>
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color" style="background: #e74c3c;"></span> Grain Elevators
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #9b59b6;"></span> Refineries
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #3498db;"></span> Chemical Plants
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #f39c12;"></span> Terminals
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #2ecc71;"></span> Multi-Modal Hubs
            </div>
        </div>
    </div>

    <script>
        // Initialize map
        var map = L.map('map').setView([30.0, -90.8], 9);

        // Base map
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            maxZoom: 19
        }}).addTo(map);

        // Data
        var enhancedFacilities = {enhanced_facilities_json};
        var grainClusters = {grain_clusters_json};
        var petroClusters = {petro_clusters_json};
        var chemClusters = {chem_clusters_json};
        var multimodalHubs = {multimodal_hubs_json};

        // Facility type colors
        var typeColors = {{
            'Elevator': '#e74c3c',
            'Refinery': '#9b59b6',
            'Chemical Plant': '#3498db',
            'Bulk Plant': '#3498db',
            'Tank Storage': '#f39c12',
            'General Cargo': '#95a5a6',
            'Bulk Terminal': '#f39c12',
            'Mid-Stream': '#34495e'
        }};

        // Create facility popup content
        function createFacilityPopup(feature) {{
            var props = feature.properties;
            var datasets = props.dataset_breakdown || {{}};

            var html = '<div class="facility-popup">';
            html += '<h3>' + props.name + '</h3>';
            html += '<div><strong>Type:</strong> ' + props.facility_type + '</div>';
            html += '<div><strong>River Mile:</strong> ' + props.river_mile + '</div>';
            html += '<div><strong>Port:</strong> ' + props.port + '</div>';

            html += '<div class="section">';
            html += '<strong>Dataset Coverage:</strong><br>';
            html += '<span class="badge badge-info">' + props.total_links + ' total links</span>';
            html += '<span class="badge badge-info">' + props.unique_sources + ' sources</span>';
            if (props.high_conf_links > 0) {{
                html += '<span class="badge badge-high">' + props.high_conf_links + ' high confidence</span>';
            }}
            html += '<div class="dataset-list">';
            for (var source in datasets) {{
                html += '<div>' + source + ': <strong>' + datasets[source] + '</strong> records</div>';
            }}
            html += '</div>';
            html += '</div>';

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

                // Size by dataset coverage
                var radius = 6 + Math.min(props.total_links / 50, 10);

                return L.circleMarker(latlng, {{
                    radius: radius,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }});
            }},
            onEachFeature: function(feature, layer) {{
                layer.bindPopup(createFacilityPopup(feature), {{
                    maxWidth: 400
                }});
            }}
        }}).addTo(map);

        // Grain cluster markers
        var grainLayer = L.geoJSON(grainClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        className: 'cluster-marker',
                        html: '<div style="background:#e74c3c;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var props = feature.properties;
                var html = '<h3>Grain Market Zone</h3>';
                html += '<div><strong>Cluster:</strong> ' + props.cluster_id + '</div>';
                html += '<div><strong>Facilities:</strong> ' + props.facility_count + '</div>';
                html += '<div><strong>Location:</strong> ' + props.market_area + '</div>';
                html += '<div><strong>Elevators:</strong></div><ul>';
                props.facilities.forEach(function(f) {{
                    html += '<li>' + f + '</li>';
                }});
                html += '</ul>';
                layer.bindPopup(html);
            }}
        }});

        // Petroleum cluster markers
        var petroLayer = L.geoJSON(petroClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        className: 'cluster-marker',
                        html: '<div style="background:#9b59b6;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var props = feature.properties;
                var html = '<h3>Petroleum Refinery Complex</h3>';
                html += '<div><strong>Cluster:</strong> ' + props.cluster_id + '</div>';
                html += '<div><strong>Total Facilities:</strong> ' + props.facility_count + '</div>';
                html += '<div><strong>Refineries:</strong> ' + props.refinery_count + '</div>';
                html += '<div><strong>Terminals:</strong> ' + props.terminal_count + '</div>';
                html += '<div><strong>River Mile:</strong> ~' + props.avg_river_mile + '</div>';
                layer.bindPopup(html);
            }}
        }});

        // Chemical corridor markers
        var chemLayer = L.geoJSON(chemClusters, {{
            pointToLayer: function(feature, latlng) {{
                return L.marker(latlng, {{
                    icon: L.divIcon({{
                        className: 'cluster-marker',
                        html: '<div style="background:#3498db;color:white;padding:8px;border-radius:50%;width:40px;height:40px;text-align:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + feature.properties.facility_count + '</div>',
                        iconSize: [40, 40]
                    }})
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var props = feature.properties;
                var html = '<h3>Chemical Manufacturing Corridor</h3>';
                html += '<div><strong>Cluster:</strong> ' + props.cluster_id + '</div>';
                html += '<div><strong>Facilities:</strong> ' + props.facility_count + '</div>';
                html += '<div><strong>River Stretch:</strong> ' + props.river_stretch + '</div>';
                if (props.facility_count > 15) {{
                    html += '<div style="color:#e74c3c;font-weight:bold;">CHEMICAL ALLEY - Major Industrial Zone</div>';
                }}
                layer.bindPopup(html);
            }}
        }});

        // Multi-modal hub highlights
        var multimodalLayer = L.geoJSON(multimodalHubs, {{
            pointToLayer: function(feature, latlng) {{
                return L.circleMarker(latlng, {{
                    radius: 10,
                    fillColor: '#2ecc71',
                    color: '#fff',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 0.6
                }});
            }},
            onEachFeature: function(feature, layer) {{
                var props = feature.properties;
                var html = '<h3>Multi-Modal Logistics Hub</h3>';
                html += '<div><strong>Facility:</strong> ' + props.facility_name + '</div>';
                html += '<div><strong>Type:</strong> ' + props.facility_type + '</div>';
                html += '<div><strong>Transport Modes:</strong> ' + props.modes.join(' + ') + '</div>';
                html += '<div><strong>River Mile:</strong> ' + props.river_mile + '</div>';
                html += '<div style="margin-top:10px;padding:8px;background:#f0f0f0;border-radius:3px;">';
                html += 'Critical intermodal node with water, rail, and pipeline access';
                html += '</div>';
                layer.bindPopup(html);
            }}
        }});

        // Layer controls
        var overlays = {{
            "Facilities (Master Registry)": facilityLayer,
            "Grain Market Zones": grainLayer,
            "Petroleum Complexes": petroLayer,
            "Chemical Corridors": chemLayer,
            "Multi-Modal Hubs": multimodalLayer
        }};

        L.control.layers(null, overlays, {{
            collapsed: false,
            position: 'topright'
        }}).addTo(map);

        // Add scale
        L.control.scale({{position: 'bottomleft'}}).addTo(map);

        console.log('Enhanced Story Map loaded successfully!');
        console.log('Facilities:', enhancedFacilities.features.length);
        console.log('Dataset links: {len(links):,}');
    </script>
</body>
</html>"""

# Write HTML file
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nOK: Enhanced Story Map created!")
print(f"  Location: {OUTPUT}")
print(f"  Size: {len(html):,} bytes")
print("\n" + "="*80)
print("DONE! Interactive story map ready to view.")
print("="*80)
print(f"\nTo view: open {OUTPUT} in your web browser")
