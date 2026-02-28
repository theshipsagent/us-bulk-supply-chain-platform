"""
Mississippi River Facilities Overview - HTML Presentation
Creates interactive HTML slide deck with embedded maps
"""

import pandas as pd
import folium
from folium.plugins import MarkerCluster

# Read facility data
facilities = pd.read_csv('master_facilities.csv')

# Create facility map
def create_facility_map(facilities_df):
    """Create folium map of facilities"""
    center_lat = facilities_df['lat'].mean()
    center_lon = facilities_df['lng'].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB positron'
    )

    # Color mapping for facility types
    colors = {
        'Tank Storage': '#e74c3c',
        'Refinery': '#c0392b',
        'Bulk Terminal': '#3498db',
        'Elevator': '#f39c12',
        'General Cargo': '#27ae60',
        'Mid-Stream': '#9b59b6',
        'Bulk Plant': '#16a085',
    }

    # Add facilities with clustering
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in facilities_df.iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lng']):
            color = colors.get(row['facility_type'], '#95a5a6')

            popup_html = f"""
            <div style="width: 300px; font-family: Arial;">
                <h4 style="margin-bottom: 10px; color: #2c3e50;">{row['canonical_name']}</h4>
                <p style="margin: 5px 0;"><b>Type:</b> {row['facility_type']}</p>
                <p style="margin: 5px 0;"><b>Location:</b> {row['city']}, {row['state']}</p>
                <p style="margin: 5px 0;"><b>River Mile:</b> {row['mrtis_mile']}</p>
                <p style="margin: 5px 0;"><b>Commodities:</b> {str(row['commodities'])[:150] if pd.notna(row['commodities']) else 'N/A'}...</p>
            </div>
            """

            folium.CircleMarker(
                location=[row['lat'], row['lng']],
                radius=8,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=row['canonical_name'],
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(marker_cluster)

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; right: 50px; width: 220px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                padding: 10px; border-radius: 5px;">
    <p style="margin: 0 0 10px 0; font-weight: bold;">Facility Types</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#e74c3c"></i> Tank Storage</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#c0392b"></i> Refinery</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#3498db"></i> Bulk Terminal</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#f39c12"></i> Elevator</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#27ae60"></i> General Cargo</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#9b59b6"></i> Mid-Stream</p>
    <p style="margin: 5px 0;"><i class="fa fa-circle" style="color:#16a085"></i> Bulk Plant</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

# Generate the map
facility_map = create_facility_map(facilities)
map_html = facility_map._repr_html_()

# Count facilities by type
facility_counts = facilities['facility_type'].value_counts().to_dict()

# Create HTML presentation
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mississippi River Facilities Overview</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #12234d 0%, #1e3c72 100%);
            color: white;
            padding: 60px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}

        header h1 {{
            font-size: 3.5em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        header p {{
            font-size: 1.5em;
            opacity: 0.9;
        }}

        .nav {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .nav a {{
            display: inline-block;
            margin: 5px 10px;
            padding: 10px 20px;
            background: #12234d;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: all 0.3s ease;
            font-weight: 600;
        }}

        .nav a:hover {{
            background: #1e3c72;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .section {{
            background: white;
            padding: 40px;
            margin-bottom: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            color: #12234d;
            font-size: 2.5em;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}

        .section h3 {{
            color: #1e3c72;
            font-size: 1.8em;
            margin: 25px 0 15px 0;
        }}

        .section p, .section li {{
            line-height: 1.8;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 20px 0;
        }}

        .facility-type {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #667eea;
            margin: 15px 0;
            border-radius: 5px;
        }}

        .facility-type h4 {{
            color: #12234d;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}

        .vessel-card, .cargo-card {{
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 5px solid #764ba2;
        }}

        .zone {{
            background: linear-gradient(to right, #f8f9fa, white);
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 6px solid #667eea;
        }}

        .zone h4 {{
            color: #12234d;
            font-size: 1.5em;
            margin-bottom: 10px;
        }}

        .map-container {{
            margin: 30px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}

        ul {{
            margin-left: 20px;
        }}

        .highlight {{
            background: #fff3cd;
            padding: 3px 8px;
            border-radius: 3px;
            font-weight: 600;
        }}

        @media (max-width: 768px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}

            header h1 {{
                font-size: 2em;
            }}

            .section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚢 Mississippi River Infrastructure</h1>
            <p>Comprehensive Overview of Facilities, Vessels & Cargo Operations</p>
        </header>

        <div class="nav">
            <a href="#overview">Overview</a>
            <a href="#facilities">Facilities</a>
            <a href="#vessels">Vessels</a>
            <a href="#cargo">Cargo</a>
            <a href="#geography">Geography</a>
            <a href="#map">Interactive Map</a>
            <a href="#flows">Flows</a>
            <a href="#capacity">Capacity</a>
        </div>

        <!-- SECTION 1: OVERVIEW -->
        <div id="overview" class="section">
            <h2>📊 Mississippi River System Overview</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">2,340</div>
                    <div class="label">Miles Total System</div>
                </div>
                <div class="stat-card">
                    <div class="number">842+</div>
                    <div class="label">Facilities Tracked</div>
                </div>
                <div class="stat-card">
                    <div class="number">233</div>
                    <div class="label">Miles Lower Miss</div>
                </div>
                <div class="stat-card">
                    <div class="number">60M+</div>
                    <div class="label">Metric Tons Grain/Year</div>
                </div>
            </div>

            <div class="two-column">
                <div>
                    <h3>System Components</h3>
                    <ul>
                        <li>Export grain elevators</li>
                        <li>Petroleum refineries & tank terminals</li>
                        <li>Chemical plants & bulk terminals</li>
                        <li>Intermodal facilities</li>
                        <li>Mid-stream transfer points</li>
                        <li>General cargo terminals</li>
                    </ul>
                </div>
                <div>
                    <h3>Facility Count by Type</h3>
                    <ul>
                        <li>Tank Storage: <span class="highlight">{facility_counts.get('Tank Storage', 0)}</span></li>
                        <li>Refineries: <span class="highlight">{facility_counts.get('Refinery', 0)}</span></li>
                        <li>Bulk Terminals: <span class="highlight">{facility_counts.get('Bulk Terminal', 0)}</span></li>
                        <li>Grain Elevators: <span class="highlight">{facility_counts.get('Elevator', 0)}</span></li>
                        <li>General Cargo: <span class="highlight">{facility_counts.get('General Cargo', 0)}</span></li>
                        <li>Mid-Stream: <span class="highlight">{facility_counts.get('Mid-Stream', 0)}</span></li>
                        <li>Bulk Plants: <span class="highlight">{facility_counts.get('Bulk Plant', 0)}</span></li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- SECTION 2: FACILITIES -->
        <div id="facilities" class="section">
            <h2>🏭 Major Facility Types</h2>

            <div class="facility-type">
                <h4>🌾 Export Grain Elevators</h4>
                <ul>
                    <li>Receive grain by barge from Midwest</li>
                    <li>Load ocean-going vessels (Panamax, Handymax)</li>
                    <li>Capacity: 4-10 million bushels per facility</li>
                    <li>Loading rates: 50,000-80,000 bushels/hour</li>
                    <li><strong>Key operators:</strong> ADM, Bunge, Cargill, CHS, Zen-Noh</li>
                </ul>
            </div>

            <div class="facility-type">
                <h4>⛽ Petroleum Refineries & Tank Terminals</h4>
                <ul>
                    <li>Process crude oil into refined products</li>
                    <li>Store crude oil, gasoline, diesel, jet fuel</li>
                    <li>Capacity: 1-16 million barrels</li>
                    <li>Deep-water vessel access for crude imports</li>
                    <li><strong>Key operators:</strong> Valero, Marathon, ExxonMobil, IMTT, Kinder Morgan</li>
                </ul>
            </div>

            <div class="facility-type">
                <h4>🧪 Chemical Terminals & Bulk Plants</h4>
                <ul>
                    <li>Store chemicals, vegetable oils, specialty products</li>
                    <li>Heating/cooling/mixing capabilities</li>
                    <li>Vapor control systems</li>
                    <li><strong>Key operators:</strong> Stolthaven, IMTT, International Raw Materials</li>
                </ul>
            </div>

            <div class="facility-type">
                <h4>📦 Bulk Terminals</h4>
                <ul>
                    <li>Coal, iron ore, steel products</li>
                    <li>Aggregates, fertilizers</li>
                    <li>Conveyor systems for loading/unloading</li>
                    <li>Barge and ocean vessel capability</li>
                </ul>
            </div>
        </div>

        <!-- SECTION 3: VESSELS -->
        <div id="vessels" class="section">
            <h2>⛴️ Vessel Types Operating on the River</h2>

            <h3>Inland Waterway Vessels</h3>
            <div class="vessel-card">
                <h4>Towboats & Barge Tows</h4>
                <ul>
                    <li>Typical tow: <strong>15-40 barges</strong> (jumbo barges: 195' x 35')</li>
                    <li>Each barge: <strong>~1,500 tons capacity</strong></li>
                    <li>Full tow capacity: <strong>22,500-60,000 tons</strong></li>
                    <li>Primary cargo: grain, coal, petroleum products, chemicals, aggregates</li>
                </ul>
            </div>

            <h3>Ocean-Going Vessels</h3>

            <div class="vessel-card">
                <h4>Panamax Vessels</h4>
                <ul>
                    <li>Length: ~700-750 feet</li>
                    <li>Beam: 106 feet (Panama Canal max)</li>
                    <li>Capacity: <strong>60,000-80,000 DWT</strong> (deadweight tons)</li>
                    <li>Draft: 39-45 feet (Mississippi River channel depth)</li>
                    <li>Primary cargo: Export grain, bulk commodities</li>
                </ul>
            </div>

            <div class="vessel-card">
                <h4>Handymax Vessels</h4>
                <ul>
                    <li>Length: ~550-600 feet</li>
                    <li>Capacity: <strong>40,000-60,000 DWT</strong></li>
                    <li>More flexible for smaller ports</li>
                    <li>Common for grain, steel, forest products</li>
                </ul>
            </div>

            <div class="vessel-card">
                <h4>Aframax Tankers (crude oil)</h4>
                <ul>
                    <li>Capacity: <strong>80,000-120,000 DWT</strong></li>
                    <li>Deep-draft vessels for crude imports</li>
                    <li>Access limited to lower river deepwater berths</li>
                </ul>
            </div>

            <div class="vessel-card">
                <h4>Specialized Vessels</h4>
                <ul>
                    <li>Chemical tankers (stainless steel tanks)</li>
                    <li>Product tankers (refined petroleum)</li>
                    <li>Container ships (limited Mississippi operations)</li>
                    <li>RoRo (roll-on/roll-off) for vehicles</li>
                </ul>
            </div>
        </div>

        <!-- SECTION 4: CARGO -->
        <div id="cargo" class="section">
            <h2>📦 Major Cargo Categories</h2>

            <div class="two-column">
                <div>
                    <div class="cargo-card">
                        <h4>🌾 Agricultural Commodities</h4>
                        <p><strong>Export Grains:</strong></p>
                        <ul>
                            <li>Corn (largest by volume)</li>
                            <li>Soybeans</li>
                            <li>Wheat, Rice, Sorghum</li>
                            <li>DDGS (distillers grains)</li>
                        </ul>
                        <p><strong>Annual throughput:</strong> Port of South Louisiana handles >50% of U.S. grain exports (~60 million metric tons/year)</p>
                        <p><strong>Destinations:</strong> Asia Pacific (60%), Latin America (25%), Middle East/Africa (15%)</p>
                    </div>

                    <div class="cargo-card">
                        <h4>⛽ Petroleum & Refined Products</h4>
                        <p><strong>Crude Oil:</strong></p>
                        <ul>
                            <li>Heavy Louisiana Sweet</li>
                            <li>Light Louisiana Sweet</li>
                            <li>Imported crude</li>
                        </ul>
                        <p><strong>Refined Products:</strong></p>
                        <ul>
                            <li>Gasoline, diesel, jet fuel</li>
                            <li>Heating oil, residual fuel</li>
                            <li>Asphalt, petroleum coke</li>
                        </ul>
                    </div>
                </div>

                <div>
                    <div class="cargo-card">
                        <h4>🧪 Chemicals & Specialty Products</h4>
                        <p><strong>Bulk Chemicals:</strong></p>
                        <ul>
                            <li>Petrochemicals (benzene, toluene)</li>
                            <li>Fertilizers (ammonia, urea)</li>
                            <li>Caustic soda, acids</li>
                            <li>Specialty chemicals</li>
                        </ul>
                        <p><strong>Oils & Biodiesel:</strong></p>
                        <ul>
                            <li>Soybean oil, Palm oil</li>
                            <li>Renewable diesel feedstocks</li>
                        </ul>
                    </div>

                    <div class="cargo-card">
                        <h4>🏗️ Bulk Materials</h4>
                        <p><strong>Coal & Metals:</strong></p>
                        <ul>
                            <li>Steam coal, Metallurgical coal</li>
                            <li>Iron ore, Steel products</li>
                            <li>Scrap metal</li>
                        </ul>
                        <p><strong>Construction:</strong></p>
                        <ul>
                            <li>Aggregates (sand, gravel, stone)</li>
                            <li>Cement</li>
                        </ul>
                        <p><strong>Forest Products:</strong></p>
                        <ul>
                            <li>Lumber, logs, wood chips</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECTION 5: GEOGRAPHY -->
        <div id="geography" class="section">
            <h2>🗺️ Lower Mississippi River - Key Zones</h2>

            <div class="zone">
                <h4>Zone 1: Below New Orleans (Mile 0-80)</h4>
                <ul>
                    <li><strong>Chevron Empire (Mile 27)</strong> - Crude oil offshore delivery</li>
                    <li><strong>Phillips 66/Harvest Belle Chasse (Mile 63)</strong> - Crude terminal (former refinery)</li>
                    <li><strong>Stolthaven (Mile 80)</strong> - Chemical storage (2.1M bbl)</li>
                    <li>Closest to Gulf of Mexico, deepwater access</li>
                </ul>
            </div>

            <div class="zone">
                <h4>Zone 2: New Orleans Metro (Mile 80-103)</h4>
                <ul>
                    <li>Violet Dock, Domino Sugar, Port of NOLA terminals</li>
                    <li><strong>Harvey/Marrero/Gretna cluster:</strong>
                        <ul>
                            <li>IMTT Gretna (now BWC Terminals)</li>
                            <li>Kinder Morgan Harvey</li>
                            <li>Magellan/Buckeye terminals</li>
                        </ul>
                    </li>
                    <li>Container terminals, general cargo</li>
                </ul>
            </div>

            <div class="zone">
                <h4>Zone 3: Westwego to Destrehan (Mile 103-155) ⭐ GRAIN CORRIDOR</h4>
                <ul>
                    <li><strong>Cargill Westwego (Mile 103)</strong> - Dual-berth grain elevator, 4.3M bu</li>
                    <li><strong>ADM Ama (Mile 121)</strong> - Grain elevator, 6M bu</li>
                    <li><strong>Zen-Noh Convent (Mile 140)</strong> - Grain elevator, 7.6M bu</li>
                    <li><strong>ADM Destrehan (Mile 147)</strong> - Largest grain elevator, 9.8M bu</li>
                </ul>
            </div>

            <div class="zone">
                <h4>Zone 4: Reserve to Gramercy (Mile 155-175) ⭐ REFINING HUB</h4>
                <ul>
                    <li><strong>Marathon Garyville Refinery (Mile 160)</strong> - 578,000 bpd, largest in Louisiana</li>
                    <li><strong>Shell Norco (Mile 153-156)</strong> - Chemical complex</li>
                    <li><strong>Valero St. Charles (Mile 158)</strong> - Refinery</li>
                    <li>Major refining & petrochemical hub</li>
                </ul>
            </div>

            <div class="zone">
                <h4>Zone 5: Baton Rouge Area (Mile 175-233) ⭐ PETROCHEMICAL COMPLEX</h4>
                <ul>
                    <li><strong>ExxonMobil Baton Rouge (Mile 228-230)</strong> - Refinery complex, 520,000 bpd</li>
                    <li><strong>IMTT Geismar (Mile 184)</strong> - Renewable fuels terminal</li>
                    <li>Dow Plaquemine, Westlake, Shintech - Chemical plants</li>
                    <li>Port of Greater Baton Rouge - Upriver terminal zone</li>
                </ul>
            </div>
        </div>

        <!-- SECTION 6: INTERACTIVE MAP -->
        <div id="map" class="section">
            <h2>🗺️ Interactive Facility Location Map</h2>
            <p style="margin-bottom: 20px; font-size: 1.2em;">
                Click on any marker to see facility details. Markers are color-coded by facility type (see legend on map).
            </p>
            <div class="map-container">
                {map_html}
            </div>
        </div>

        <!-- SECTION 7: COMMODITY FLOWS -->
        <div id="flows" class="section">
            <h2>🔄 Commodity Flow Patterns</h2>

            <h3>📤 Export Flows (Outbound from Louisiana)</h3>
            <div class="cargo-card">
                <h4>Grain Exports (Mississippi River → Gulf → World)</h4>
                <ul>
                    <li><strong>Origin:</strong> Iowa, Illinois, Minnesota, Missouri grain belt</li>
                    <li><strong>Transport:</strong> 15-40 barge tows → Lower Miss elevators</li>
                    <li><strong>Destinations:</strong> Asia Pacific (60%), Latin America (25%), Middle East/Africa (15%)</li>
                    <li><strong>Peak season:</strong> Post-harvest (Oct-Feb)</li>
                    <li><strong>Volume:</strong> 60+ million metric tons annually</li>
                </ul>
            </div>

            <div class="cargo-card">
                <h4>Petroleum Product Exports</h4>
                <ul>
                    <li><strong>Origin:</strong> Gulf Coast refineries</li>
                    <li><strong>Transport:</strong> Pipeline → tank terminal → ocean vessel</li>
                    <li><strong>Destinations:</strong> Latin America, Europe</li>
                    <li><strong>Products:</strong> Diesel, gasoline, jet fuel, petroleum coke</li>
                </ul>
            </div>

            <h3>📥 Import Flows (Inbound to Louisiana)</h3>
            <div class="cargo-card">
                <h4>Crude Oil Imports</h4>
                <ul>
                    <li><strong>Origin:</strong> Mexico, Colombia, Saudi Arabia, Iraq</li>
                    <li><strong>Transport:</strong> Aframax tankers → deepwater terminals → pipeline</li>
                    <li><strong>Destination:</strong> Louisiana/Texas refineries</li>
                    <li><strong>Trend:</strong> Declining due to U.S. shale production</li>
                </ul>
            </div>

            <h3>🔁 Internal Flows (River-borne domestic commerce)</h3>
            <ul style="margin-left: 20px; font-size: 1.1em; line-height: 1.8;">
                <li>Coal (Upper Mississippi/Illinois → Louisiana power plants)</li>
                <li>Steel Products (Great Lakes → Gulf construction markets)</li>
                <li>Aggregates (Local quarries → construction sites)</li>
                <li>Fertilizers (Gulf production → Midwest farms)</li>
                <li>Chemicals (Louisiana plants → industrial users nationwide)</li>
            </ul>
        </div>

        <!-- SECTION 8: CAPACITY -->
        <div id="capacity" class="section">
            <h2>📊 System Capacity Summary</h2>

            <div class="two-column">
                <div>
                    <h3>🌾 Grain Export Capacity</h3>
                    <div class="cargo-card">
                        <p><strong>Louisiana Export Elevators (9 total)</strong></p>
                        <ul>
                            <li>Total storage: ~64 million bushels</li>
                            <li>Annual throughput: 60+ million metric tons</li>
                            <li>Loading capacity: 50,000-80,000 bu/hr per facility</li>
                        </ul>
                        <p><strong>Top Facilities:</strong></p>
                        <ol>
                            <li>ADM Destrehan: 9.8M bu</li>
                            <li>Zen-Noh Convent: 7.6M bu</li>
                            <li>CHS Myrtle Grove: 6.5M bu</li>
                            <li>ADM Ama: 6M bu</li>
                            <li>Cargill Reserve: 5.5M bu</li>
                        </ol>
                    </div>

                    <h3>⛽ Petroleum Storage</h3>
                    <div class="cargo-card">
                        <ul>
                            <li><strong>IMTT St. Rose:</strong> 14.8M barrels (largest)</li>
                            <li><strong>Total Louisiana:</strong> 40+ million bbl across all operators</li>
                            <li><strong>Products:</strong> Crude, gasoline, diesel, chemicals</li>
                        </ul>
                    </div>
                </div>

                <div>
                    <h3>🏭 Refinery Capacity</h3>
                    <div class="cargo-card">
                        <p><strong>Louisiana Refineries (Top 3)</strong></p>
                        <ol>
                            <li>Marathon Garyville: 578,000 bpd</li>
                            <li>ExxonMobil Baton Rouge: 520,000 bpd</li>
                            <li>Valero Meraux: 340,000 bpd</li>
                        </ol>
                        <p><strong>Total Louisiana:</strong> ~2.9M bpd<br>
                        (3rd largest refining state in U.S.)</p>
                    </div>

                    <h3>🚢 Waterway Capacity</h3>
                    <div class="cargo-card">
                        <p><strong>Navigation Channel</strong></p>
                        <ul>
                            <li>Depth: 45 feet (SW Pass entrance)</li>
                            <li>Width: 500-750 feet</li>
                        </ul>
                        <p><strong>Vessel Traffic</strong></p>
                        <ul>
                            <li>~5,000 oceangoing vessels/year</li>
                            <li>~60,000 barge movements/year</li>
                            <li>~500,000 barges on inland system</li>
                        </ul>
                    </div>

                    <h3>🚂 Intermodal Connections</h3>
                    <div class="cargo-card">
                        <ul>
                            <li><strong>Rail:</strong> Class 1 railroads (UP, BNSF, CN, KCS, NS, CSX)</li>
                            <li><strong>Pipelines:</strong> 50+ crude & product pipelines</li>
                            <li><strong>Connections:</strong> Cushing OK hub, Gulf to Midwest corridors</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- FOOTER / SUMMARY -->
        <div class="section" style="background: linear-gradient(135deg, #12234d 0%, #1e3c72 100%); color: white;">
            <h2 style="color: white; border-bottom-color: rgba(255,255,255,0.3);">🎯 Key Takeaways</h2>
            <ul style="font-size: 1.2em; line-height: 2;">
                <li>Mississippi River system is the backbone of U.S. bulk commodity export infrastructure</li>
                <li>Louisiana Lower Mississippi (Mile 0-233) contains the <strong>world's largest concentration of export grain elevators</strong></li>
                <li>System handles <strong>500+ million tons of cargo annually</strong> across all commodity types</li>
                <li>Deep-draft navigation channel supports <strong>Panamax vessels up to Baton Rouge</strong></li>
                <li>Multimodal connectivity: River + Rail + Pipeline creates integrated logistics network</li>
            </ul>

            <h3 style="margin-top: 30px; color: white;">📚 Additional Resources</h3>
            <p style="font-size: 1.1em; line-height: 1.8;">
                <strong>Interactive Maps Available:</strong><br>
                • Lower_Mississippi_Industrial_Infrastructure_Map.html<br>
                • National_Supply_Chain_Infrastructure_Map.html<br>
                • National_Market_Clusters_Map.html<br>
                • Commodity_Flows_Map.html<br><br>

                <strong>Reports Available:</strong><br>
                • Lower_Mississippi_River_Terminal_Facilities_Report.md<br>
                • Lower_Mississippi_River_Export_Grain_Elevators_Report.md<br>
                • Lower_Mississippi_River_Industrial_Infrastructure_Report.md
            </p>
        </div>
    </div>
</body>
</html>
"""

# Save HTML file
output_file = "_html_web_files/Mississippi_River_Facilities_Overview.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n{'='*80}")
print(f"SUCCESS! HTML Presentation created:")
print(f"  {output_file}")
print(f"\nSections included:")
print(f"  • Overview with statistics")
print(f"  • Major Facility Types")
print(f"  • Vessel Types (inland & ocean-going)")
print(f"  • Major Cargo Categories")
print(f"  • Geographic Overview (5 zones)")
print(f"  • Interactive Facility Map (embedded)")
print(f"  • Commodity Flow Patterns")
print(f"  • System Capacity Summary")
print(f"  • Key Takeaways & Resources")
print(f"\nFeatures:")
print(f"  ✓ Smooth scrolling navigation")
print(f"  ✓ Embedded interactive Folium map")
print(f"  ✓ Color-coded facility markers")
print(f"  ✓ Responsive design")
print(f"  ✓ Professional styling")
print(f"{'='*80}\n")
