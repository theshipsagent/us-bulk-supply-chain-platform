"""
Build an interactive Leaflet web map of Lower Mississippi River
Industrial Infrastructure from the MRTIS-USACE matched GeoJSON.
Excludes anchorages and pilot stations.
Consolidates multiple berths/docks into one point per physical facility.
Labels as "Facility Name (Mile XXX)".
"""
import json
import os
import re
import html as html_module

GEOJSON = r"G:\My Drive\LLM\sources_data_maps\qgis\mrtis_usace_matched.geojson"
RIVER_LINE = r"G:\My Drive\LLM\sources_data_maps\qgis\lower_miss_river_line_0_250_dissolved.geojson"
MILE_MARKERS = r"G:\My Drive\LLM\sources_data_maps\qgis\lower_miss_mile_markers_0_250.geojson"
CLASS1_RAIL = r"G:\My Drive\LLM\sources_data_maps\qgis\class1_rail_main_routes_LA_region.geojson"
CLASS1_LABELS_50 = r"G:\My Drive\LLM\sources_data_maps\qgis\class1_main_routes_labels_state_50mi_LA_region.geojson"
CLASS1_LABELS_5 = r"G:\My Drive\LLM\sources_data_maps\qgis\class1_main_routes_labels_local_5mi_LA_region.geojson"
NOPB_NOGC = r"G:\My Drive\LLM\sources_data_maps\qgis\LA_NOPB_NOGC_dissolved.geojson"
NOPB_NOGC_LABELS = r"G:\My Drive\LLM\sources_data_maps\qgis\LA_NOPB_NOGC_label_points_5mi.geojson"
PIPELINES_HGL = r"G:\My Drive\LLM\sources_data_maps\esri_exports\HGL_Pipelines_LA_region.geojson"
PIPELINES_CRUDE = r"G:\My Drive\LLM\sources_data_maps\esri_exports\Crude_Pipelines_LA_region.geojson"
PIPELINES_PRODUCT = r"G:\My Drive\LLM\sources_data_maps\esri_exports\Product_Pipelines_LA_region.geojson"
OUTPUT = r"G:\My Drive\LLM\sources_data_maps\_html_web_files\Lower_Mississippi_Industrial_Infrastructure_Map.html"

EXCLUDE_TYPES = {"Anchorage", "Pilot Station"}

# Individual zones to exclude from map
EXCLUDE_ZONES = {
    "Andry St",
    "Buck Kreihs",
    "Poland St",
    "Esplanade Ave",
    "Gov Nicholls St",
    "Mandeville St",
    "Erato St",
    "Perry Street",
    "110 Buoys",
    "111 Buoys",
    "112 Buoys",
    "CGB 111 Buoys",
}

with open(GEOJSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# Load river line and mile markers
with open(RIVER_LINE, "r", encoding="utf-8") as f:
    river_line_data = json.load(f)

with open(MILE_MARKERS, "r", encoding="utf-8") as f:
    mile_markers_data = json.load(f)

# Extract river line coordinates (MultiLineString -> array of [lat,lng] arrays)
river_coords = []
geom = river_line_data["features"][0]["geometry"]
if geom["type"] == "MultiLineString":
    for part in geom["coordinates"]:
        river_coords.append([[c[1], c[0]] for c in part])
else:
    river_coords.append([[c[1], c[0]] for c in geom["coordinates"]])

# Extract mile markers: only every 5 miles for labels, all for ticks
mile_markers = []
for feat in mile_markers_data["features"]:
    p = feat["properties"]
    c = feat["geometry"]["coordinates"]
    mile_markers.append({
        "mile": p.get("MILE", p.get("name", 0)),
        "lat": c[1],
        "lng": c[0],
    })
mile_markers.sort(key=lambda m: m["mile"])

river_coords_json = json.dumps(river_coords)
mile_markers_json = json.dumps(mile_markers)

# ---- Load rail and pipeline layers ----
with open(CLASS1_RAIL, "r", encoding="utf-8") as f:
    class1_rail_data = json.load(f)
with open(CLASS1_LABELS_50, "r", encoding="utf-8") as f:
    class1_labels_50_data = json.load(f)
with open(CLASS1_LABELS_5, "r", encoding="utf-8") as f:
    class1_labels_5_data = json.load(f)
with open(NOPB_NOGC, "r", encoding="utf-8") as f:
    nopb_nogc_data = json.load(f)
with open(NOPB_NOGC_LABELS, "r", encoding="utf-8") as f:
    nopb_nogc_labels_data = json.load(f)

# Load pipeline data (pre-filtered to LA region from Esri)
with open(PIPELINES_HGL, "r", encoding="utf-8") as f:
    hgl_data = json.load(f)
with open(PIPELINES_CRUDE, "r", encoding="utf-8") as f:
    crude_data = json.load(f)
with open(PIPELINES_PRODUCT, "r", encoding="utf-8") as f:
    product_data = json.load(f)

# Tag each feature with pipeline type, normalize name/operator fields
pipeline_all = []
for feat in hgl_data.get("features", []):
    feat["properties"]["_pipeType"] = "HGL"
    feat["properties"]["_pipeName"] = feat["properties"].get("Pipename", "Unknown")
    feat["properties"]["_pipeOp"] = feat["properties"].get("Opername", "")
    pipeline_all.append(feat)
for feat in crude_data.get("features", []):
    feat["properties"]["_pipeType"] = "Crude"
    feat["properties"]["_pipeName"] = feat["properties"].get("Pipeline_N", "Unknown")
    feat["properties"]["_pipeOp"] = feat["properties"].get("Operator", "")
    pipeline_all.append(feat)
for feat in product_data.get("features", []):
    feat["properties"]["_pipeType"] = "Product"
    feat["properties"]["_pipeName"] = feat["properties"].get("Pipeline_N", "Unknown")
    feat["properties"]["_pipeOp"] = feat["properties"].get("Operator", "")
    pipeline_all.append(feat)

pipeline_geojson = {"type": "FeatureCollection", "features": pipeline_all}
print(f"Pipelines: {len(pipeline_all)} total (HGL: {len(hgl_data.get('features',[]))}, Crude: {len(crude_data.get('features',[]))}, Product: {len(product_data.get('features',[]))})")

class1_rail_json = json.dumps(class1_rail_data, separators=(",", ":"))
class1_labels_50_json = json.dumps(class1_labels_50_data, separators=(",", ":"))
class1_labels_5_json = json.dumps(class1_labels_5_data, separators=(",", ":"))
nopb_nogc_json = json.dumps(nopb_nogc_data, separators=(",", ":"))
nopb_nogc_labels_json = json.dumps(nopb_nogc_labels_data, separators=(",", ":"))
pipeline_json = json.dumps(pipeline_geojson, separators=(",", ":"))

CARRIER_COLORS = {
    "UP": {"name": "Union Pacific", "color": "#ffe119"},
    "BNSF": {"name": "BNSF Railway", "color": "#f58231"},
    "NS": {"name": "Norfolk Southern", "color": "#e0e0e0"},
    "CSXT": {"name": "CSX Transportation", "color": "#3cb44b"},
    "CN": {"name": "Canadian National", "color": "#4363d8"},
    "CPRS": {"name": "CPKC", "color": "#911eb4"},
    "NOPB": {"name": "New Orleans Public Belt", "color": "#e6194b"},
    "NOGC": {"name": "New Orleans & Gulf Coast", "color": "#a9a9a9"},
}
carrier_colors_json = json.dumps(CARRIER_COLORS, separators=(",", ":"))

# Add Formosa Plastics manually
formosa = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-91.2050, 30.5150]},
    "properties": {
        "Zone": "Formosa Plastics",
        "Facility": "Formosa Plastics Baton Rouge",
        "ZoneType": "Chemical Plant",
        "VesselTypes": "Tanker",
        "Activity": "Load or Discharge",
        "Cargoes": "PVC, VCM, Caustic Soda, EDC",
        "MRTIS_Mile": 234.0,
        "EventCount": 0,
        "Note": "Manually added",
        "MatchQuality": "MANUAL",
        "USACE_Name": "FORMOSA PLASTICS CORP",
        "USACE_Mile": 234.0,
        "Port": "Port of Greater Baton Rouge, LA",
        "Waterway": "Mississippi River",
        "Owners": "Formosa Plastics Corp. (Taiwan)",
        "Operators": "Formosa Plastics Corporation, Louisiana",
        "Purpose": "PVC, VCM, chlor-alkali chemical manufacturing",
        "Commodities": "PVC resin, VCM, caustic soda, EDC",
        "City": "Baton Rouge",
        "County": "East Baton Rouge",
        "State": "LA",
    }
}
data["features"].append(formosa)

# ---- Facility consolidation mapping ----
# Maps zone name -> consolidated facility key
# Zones not listed here use auto-grouping logic
MANUAL_GROUP = {
    # Refineries
    "Marathon 1": "Marathon Garyville",
    "Marathon 2": "Marathon Garyville",
    "Marathon 5": "Marathon Garyville",
    "Shell Convent 1": "Shell Convent",
    "Shell Convent 2": "Shell Convent",
    "Shell Norco 1": "Shell Norco",
    "Shell Norco 2": "Shell Norco",
    "Shell Norco 4": "Shell Norco",
    "Valero St Charles 2": "Valero St. Charles",
    "Valero St Charles 3": "Valero St. Charles",
    "Valero St Charles 4": "Valero St. Charles",
    "Valero St Charles 5": "Valero St. Charles",
    # Chemical Plants
    "Corner Stone": "Cornerstone Chemical",
    "Cornerstone": "Cornerstone Chemical",
    "CFI Donaldsonville": "CF Industries Donaldsonville",
    "CFI Donaldsonville 101": "CF Industries Donaldsonville",
    "CFI Donaldsonville 106": "CF Industries Donaldsonville",
    "IMC Faustina": "Mosaic Faustina",
    "Occidental Convent": "OxyChem Convent",
    "Occidental Taft": "OxyChem Taft",
    "Axiall Plaquemine": "Westlake Plaquemine",
    "PCS Nitrogen": "Nutrien Geismar",
    "Total Carville": "TotalEnergies / Cos-Mar Carville",
    "Baker Hughes": "Baker Hughes Geismar",
    "Dow Missouri": "Dow Plaquemine Complex (Missouri)",
    "Dow Plaquemine": "Dow Plaquemine Complex",
    "Mosaic Uncle Sam": "Mosaic Uncle Sam",
    # Tank Storage
    "IMTT St Rose 2": "IMTT St. Rose",
    "IMTT St Rose 4": "IMTT St. Rose",
    "IMTT St Rose 8": "IMTT St. Rose",
    "IMTT St Rose 14": "IMTT St. Rose",
    "IMTT Avondale": "IMTT Avondale",
    "IMTT Gretna": "IMTT Gretna",
    "IMTT Geismar": "IMTT Geismar",
    "KMI Harvey 1": "Kinder Morgan Harvey",
    "KMI Harvey 2": "Kinder Morgan Harvey",
    "KMI Harvey 3": "Kinder Morgan Harvey",
    "KMI Harvey 4": "Kinder Morgan Harvey",
    "KMI Seven Oaks": "Kinder Morgan Seven Oaks",
    "KMI St Gabriel": "Kinder Morgan St. Gabriel",
    "MPLX Garyville 1": "MPLX Garyville",
    "MPLX Garyville 2": "MPLX Garyville",
    "MPLX Garyville 5": "MPLX Garyville",
    "MPLX Mt Airy 1": "MPLX Mt. Airy",
    "MPLX Mt Airy 2": "MPLX Mt. Airy",
    "Phillips 66 Alliance 1": "Phillips 66 Alliance",
    "Phillips 66 Alliance 2": "Phillips 66 Alliance",
    "NuStar St James 2": "NuStar St. James",
    "NuStar St James 5": "NuStar St. James",
    "Capline St James 1": "Capline St. James",
    "Capline St James 2": "Capline St. James",
    "Sugarland St James 1": "Sugarland St. James",
    "Sugarland St James 2": "Sugarland St. James",
    "Stolthaven 3": "Stolthaven Braithwaite",
    "Stolthaven 4": "Stolthaven Braithwaite",
    "Magellan Marrero 1": "Magellan Marrero",
    "Magellan Marrero 2": "Magellan Marrero",
    "Buckeye Marrero 2": "Buckeye Marrero",
    "Blackwater Harvey": "Blackwater Harvey",
    "Blackwater Westwego": "Blackwater Westwego",
    "Crosstex Energy": "EnLink Midstream (Crosstex)",
    "LBC Sunshine": "LBC Tank Terminals",
    "Ergon St James": "Ergon St. James",
    "Plains St James": "Plains St. James",
    "Pin Oak Mt Airy": "Pin Oak Mt. Airy",
    "Apex Mt Airy": "Apex Mt. Airy",
    "Apex Baton Rouge": "Apex Baton Rouge",
    "Genesis Baton Rouge": "Genesis Energy Baton Rouge",
    "Chevron Empire": "Chevron Empire",
    "Chevron Oak Point": "Chevron Oak Point",
    "Shell Geismar": "Shell Geismar",
    "Placid Oil": "Placid Refining",
    "Willow Glen": "Willow Glen Terminal",
    "Cargill Molasses": "Cargill Molasses (Garyville)",
    # Elevators
    "ADM AMA": "ADM Ama",
    "ADM Destrehan": "ADM Destrehan",
    "ADM Reserve": "ADM Reserve",
    "Cargill Reserve Lower": "Cargill Reserve",
    "Cargill Reserve Upper": "Cargill Reserve",
    "Cargill Westwego Lower": "Cargill Westwego",
    "Cargill Westwego Upper": "Cargill Westwego",
    "Zen-Noh Grain": "Zen-Noh Convent",
    "Zen-Noh Lower": "Zen-Noh Convent",
    "Zen-Noh Upper": "Zen-Noh Convent",
    "Cenex Harvest States": "CHS Myrtle Grove",
    "Bunge Destrehan": "Bunge Destrehan",
    "Dreyfuss": "Louis Dreyfus Port Allen",
    # Bulk Terminals
    "IMT Coal": "IMT Myrtle Grove",
    "IMT Coal Ship Dock": "IMT Myrtle Grove",
    "United Bulk": "United Bulk Terminal",
    "United Bulk Terminal": "United Bulk Terminal",
    "Burnside Terminal": "ABT Burnside",
    "Convent Marine Terminal": "Convent Marine Terminal",
    # Bulk Plants
    "Domino Sugar": "Domino Sugar",
    "Domnio Sugar": "Domino Sugar",
    "Calciner Industries": "RAIN Gramercy",
    "Louisiana Sugar Refining": "Louisiana Sugar Refining",
    "Noranda Alumina": "Noranda Alumina (Gramercy)",
    "Nucor Steel": "Nucor Steel (Convent)",
    "Chalmette Terminal": "RAIN Chalmette",
    "Vulcan Westwego": "Vulcan Materials Westwego",
    "Drax Biomass": "Drax Biomass",
    "Yara Fertilizer": "Yara Fertilizer",
    # General Cargo
    "Violet Dock 1": "Violet Dock",
    "Violet Dock 2": "Violet Dock",
    "Violet Dock 3": "Violet Dock",
    "Violet Dock 4": "Violet Dock",
    "Violet Dock 5": "Violet Dock",
    "Nashville Ave A": "Nashville Ave Wharves",
    "Nashville Ave B C": "Nashville Ave Wharves",
    "Napolean Ave": "Napoleon Ave Wharf",
    "Napoleon Ave": "Napoleon Ave Wharf",
    "Louisana Ave": "Louisiana Ave Wharf",
    "Louisiana Ave": "Louisiana Ave Wharf",
    "Chalmette Slip": "Chalmette Slip",
    "Baton Rouge General Cargo": "Port of Greater Baton Rouge",
    "Alabo St": "Alabo St Wharf",
    "Andry St": "Andry St Wharf",
    "Buck Kreihs": "Buck Kreihs Wharf",
    "Poland St": "Poland St Wharf",
    "Esplanade Ave": "Esplanade Ave Wharf",
    "Gov Nicholls St": "Gov. Nicholls St Wharf",
    "Mandeville St": "Mandeville St Wharf",
    "Julia St": "Julia St Wharf",
    "Perry Street": "Perry St Wharf",
    "Erato St": "Erato St Wharf",
    "Harmony St": "Harmony St Wharf",
    "1st Street": "1st St Wharf",
    "7th Street": "7th St Wharf",
    "Henry Clay Ave": "Henry Clay Ave Wharf",
    "Marlex": "Marlex Terminal",
    "Avondale": "Avondale Global Gateway",
    "Globalplex": "Globalplex Intermodal",
    # Mid-Stream
    "ADM 110 Buoys": "ARTCO 110-112 Buoys",
    "ADM 110-1 Buoys": "ARTCO 110-112 Buoys",
    "ADM 110-2 Buoys": "ARTCO 110-112 Buoys",
    "ADM 110-3 Buoys": "ARTCO 110-112 Buoys",
    "ADM 110-4 Buoys": "ARTCO 110-112 Buoys",
    "ADM 111 Buoys": "ARTCO 110-112 Buoys",
    "ADM Destrehan Buoys Lower": "ARTCO Destrehan Buoys",
    "ADM Destrehan Buoys Upper": "ARTCO Destrehan Buoys",
    "110 Buoys": "110-112 Buoys",
    "111 Buoys": "110-112 Buoys",
    "112 Buoys": "110-112 Buoys",
    "CGB 111 Buoys": "110-112 Buoys",
    "133 Buoys": "133-134 Buoys",
    "134 Buoys": "133-134 Buoys",
    "136 Buoys": "136-138 Buoys",
    "136.7 Buoys": "136-138 Buoys",
    "137.5 Buoys": "136-138 Buoys",
    "140 Buoys": "140 Buoys",
    "140.5 Buoys": "140 Buoys",
    "158 Buoys Lower": "158 Buoys",
    "158 Buoys Middle": "158 Buoys",
    "158 Buoys Upper": "158 Buoys",
    "167 Buoys": "167 Buoys",
    "171 Buoys": "171-172 Buoys",
    "172 Buoys": "171-172 Buoys",
    "175 Buoys": "175 Buoys",
    "179 Buoys": "179-180 Buoys",
    "180 Buoys": "179-180 Buoys",
    "Meraux Buoys Lower": "Meraux Buoys",
    "Meraux Buoys Upper": "Meraux Buoys",
    "Dockside Buoys Lower": "Dockside Buoys",
    "Dockside Buoys Upper": "Dockside Buoys",
    "Chalmette Buoys": "Chalmette Buoys",
    "Burnside Buoys": "Burnside Buoys",
    "Waggaman Buoys": "Waggaman Buoys",
    "Zito HPL Buoys": "Zito HPL Buoys",
    "MGMT": "MGMT",
    "Mrytle Grove Marine Terminal": "MGMT",
    "Arabi Terminal": "Arabi Terminal",
    "Vulcan St Rose": "Vulcan St. Rose",
    "Americas Styrenics": "Americas Styrenics (St. James)",
    "Shintech": "Shintech Plaquemine",
    "Exxon Baton Rouge": "ExxonMobil Baton Rouge",
    "PBF Chalmette": "PBF Chalmette",
    "Valero Meraux": "Valero Meraux",
    "Formosa Plastics": "Formosa Plastics Baton Rouge",
}

# Zone type color scheme
COLORS = {
    "Refinery": "#e94560",
    "Chemical Plant": "#ff6b35",
    "Tank Storage": "#0ea5e9",
    "Elevator": "#22c55e",
    "Bulk Terminal": "#a855f7",
    "Bulk Plant": "#8b5cf6",
    "General Cargo": "#eab308",
    "Mid-Stream": "#94a3b8",
}

# ---- Group zones into facilities ----
# key = (facility_name, zone_type) -> list of feature data
groups = {}
for feat in data["features"]:
    props = feat["properties"]
    zone_type = props.get("ZoneType", "Unknown")
    if zone_type in EXCLUDE_TYPES:
        continue

    zone = props.get("Zone", "")
    if zone in EXCLUDE_ZONES:
        continue
    fac_key = MANUAL_GROUP.get(zone, zone)
    group_key = (fac_key, zone_type)

    coords = feat["geometry"]["coordinates"]
    if group_key not in groups:
        groups[group_key] = {
            "name": fac_key,
            "zoneType": zone_type,
            "zones": [],
            "lats": [],
            "lngs": [],
            "events": 0,
            "props_best": None,
            "best_events": -1,
        }

    g = groups[group_key]
    g["zones"].append(zone)
    g["lats"].append(coords[1])
    g["lngs"].append(coords[0])
    ec = props.get("EventCount", 0) or 0
    g["events"] += ec

    # Keep properties from the zone with highest event count (richest data)
    if ec > g["best_events"]:
        g["best_events"] = ec
        g["props_best"] = props

# ---- Build facility list ----
facilities = []
for (fac_name, zone_type), g in groups.items():
    avg_lat = sum(g["lats"]) / len(g["lats"])
    avg_lng = sum(g["lngs"]) / len(g["lngs"])
    mile = g["props_best"].get("MRTIS_Mile", 0)
    mile_int = int(round(mile)) if isinstance(mile, (int, float)) else 0

    color = COLORS.get(zone_type, "#9ca3af")
    props = g["props_best"]

    # Build popup
    usace_name = html_module.escape(str(props.get("USACE_Name", "") or ""))
    owners = html_module.escape(str(props.get("Owners", "") or ""))
    operators = html_module.escape(str(props.get("Operators", "") or ""))
    purpose = html_module.escape(str(props.get("Purpose", "") or ""))
    commodities = html_module.escape(str(props.get("Commodities", "") or ""))
    cargoes = html_module.escape(str(props.get("Cargoes", "") or ""))
    city = html_module.escape(str(props.get("City", "") or ""))
    county = html_module.escape(str(props.get("County", "") or ""))
    depth_min = props.get("DepthMin", "")
    depth_max = props.get("DepthMax", "")
    bank = html_module.escape(str(props.get("Bank", "") or ""))
    match_q = html_module.escape(str(props.get("MatchQuality", "") or ""))

    depth_str = ""
    if depth_min and depth_max:
        depth_str = f"{depth_min}-{depth_max} ft"
    elif depth_min:
        depth_str = f"{depth_min} ft"

    display_name = f"{fac_name} (Mile {mile_int})"

    popup_lines = [
        f"<div style='min-width:280px;max-width:380px;font-family:system-ui;font-size:13px;'>",
        f"<div style='font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px;'>{html_module.escape(fac_name)}</div>",
        f"<div style='color:#666;font-size:11px;margin-bottom:6px;'>Mile {mile_int} | {zone_type} | {city}, {county} Parish</div>",
    ]
    if len(g["zones"]) > 1:
        popup_lines.append(f"<div style='margin-bottom:4px;color:#888;font-size:11px;'><b>Berths/Zones:</b> {', '.join(g['zones'])}</div>")
    if usace_name:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>USACE Dock:</b> {usace_name}</div>")
    if owners:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Owner:</b> {owners}</div>")
    if operators:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Operator:</b> {operators}</div>")
    if purpose:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Purpose:</b> {purpose}</div>")
    if commodities:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Commodities:</b> {commodities}</div>")
    elif cargoes:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Cargoes:</b> {cargoes}</div>")
    if depth_str:
        popup_lines.append(f"<div style='margin-bottom:4px;'><b>Depth:</b> {depth_str} | <b>Bank:</b> {bank}</div>")
    if g["events"]:
        popup_lines.append(f"<div style='color:#888;font-size:11px;margin-top:4px;'>MRTIS Events: {g['events']:,} | Match: {match_q}</div>")
    popup_lines.append("</div>")
    popup_html = "".join(popup_lines)
    popup_js = popup_html.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "")

    facilities.append({
        "lat": avg_lat,
        "lng": avg_lng,
        "name": fac_name,
        "displayName": display_name,
        "zoneType": zone_type,
        "mile": mile_int,
        "color": color,
        "popup": popup_js,
        "eventCount": g["events"],
        "zoneCount": len(g["zones"]),
    })

# Sort by mile
facilities.sort(key=lambda f: f["mile"])

features_json = json.dumps(facilities, ensure_ascii=False)

# ---- Port Authority Jurisdiction Polygons ----
# Dense river centerline (mile, lat, lon) for polygon generation
river_centerline = [
    (-2, 29.00, -89.25),
    (0, 29.01, -89.26),    # Head of Passes
    (3, 29.06, -89.27),
    (6, 29.12, -89.29),
    (10, 29.18, -89.31),
    (14, 29.23, -89.34),
    (18, 29.27, -89.37),
    (22, 29.30, -89.40),
    (27, 29.34, -89.44),
    (32, 29.37, -89.48),
    (37, 29.39, -89.54),
    (42, 29.42, -89.59),
    (47, 29.46, -89.63),
    (52, 29.50, -89.66),
    (55, 29.53, -89.68),
    (58, 29.56, -89.71),
    (62, 29.59, -89.76),
    (66, 29.62, -89.81),
    (70, 29.65, -89.87),
    (73, 29.67, -89.90),
    (76, 29.72, -89.93),
    (79, 29.78, -89.94),
    (81, 29.82, -89.95),
    (82.1, 29.84, -89.95),
    (84, 29.87, -89.96),
    (86, 29.90, -89.97),
    (88, 29.93, -89.97),
    (90, 29.94, -89.97),
    (90.5, 29.945, -89.98),
    (92, 29.96, -90.02),
    (94, 29.96, -90.06),
    (96, 29.96, -90.07),
    (98, 29.95, -90.08),
    (100, 29.94, -90.10),
    (103, 29.92, -90.14),
    (106, 29.91, -90.18),
    (108, 29.91, -90.20),
    (110, 29.93, -90.22),
    (112, 29.96, -90.24),
    (114.9, 29.97, -90.27),
    (117, 29.99, -90.32),
    (120, 30.00, -90.37),
    (123, 30.00, -90.40),
    (126, 29.99, -90.42),
    (128, 30.01, -90.45),
    (131, 30.03, -90.49),
    (134, 30.04, -90.53),
    (137, 30.05, -90.56),
    (140, 30.06, -90.62),
    (143, 30.07, -90.66),
    (146, 30.07, -90.71),
    (149, 30.06, -90.75),
    (152, 30.05, -90.78),
    (155, 30.04, -90.80),
    (158, 30.03, -90.83),
    (160, 30.02, -90.87),
    (163, 30.04, -90.89),
    (166, 30.05, -90.91),
    (168.5, 30.06, -90.93),
    (171, 30.08, -90.95),
    (175, 30.10, -90.97),
    (179, 30.13, -91.00),
    (183, 30.18, -91.02),
    (187, 30.21, -91.05),
    (191, 30.24, -91.08),
    (195, 30.27, -91.10),
    (200, 30.28, -91.16),
    (205, 30.28, -91.22),
    (210, 30.30, -91.22),
    (215, 30.33, -91.22),
    (220, 30.37, -91.22),
    (225, 30.40, -91.21),
    (229, 30.44, -91.19),
    (232, 30.47, -91.18),
    (236, 30.50, -91.19),
    (240, 30.52, -91.18),
    (245, 30.55, -91.17),
    (250, 30.57, -91.16),
    (253, 30.59, -91.15),
]

import math

def interpolate_at_mile(mile, pts):
    """Interpolate lat/lon at a given mile along the centerline."""
    for i in range(len(pts) - 1):
        m1, lat1, lon1 = pts[i]
        m2, lat2, lon2 = pts[i + 1]
        if m1 <= mile <= m2:
            t = (mile - m1) / (m2 - m1) if m2 != m1 else 0
            return (lat1 + t * (lat2 - lat1), lon1 + t * (lon2 - lon1))
    # Clamp to ends
    if mile <= pts[0][0]:
        return (pts[0][1], pts[0][2])
    return (pts[-1][1], pts[-1][2])

def offset_point(lat, lon, bearing_deg, dist_deg):
    """Offset a point by dist_deg in the given bearing direction."""
    rad = math.radians(bearing_deg)
    return (lat + dist_deg * math.cos(rad), lon + dist_deg * math.sin(rad))

def get_segment_points(mile_start, mile_end, pts):
    """Get centerline points within a mile range, including interpolated endpoints."""
    result = []
    start_pt = interpolate_at_mile(mile_start, pts)
    result.append((mile_start, start_pt[0], start_pt[1]))
    for m, lat, lon in pts:
        if mile_start < m < mile_end:
            result.append((m, lat, lon))
    end_pt = interpolate_at_mile(mile_end, pts)
    result.append((mile_end, end_pt[0], end_pt[1]))
    return result

def make_river_polygon(mile_start, mile_end, pts, width_deg=0.025):
    """Create a polygon following the river from mile_start to mile_end."""
    seg = get_segment_points(mile_start, mile_end, pts)
    left_bank = []
    right_bank = []
    for i in range(len(seg)):
        m, lat, lon = seg[i]
        # Compute bearing from previous to next point
        if i == 0:
            nm, nlat, nlon = seg[i + 1]
            bearing = math.degrees(math.atan2(nlon - lon, nlat - lat))
        elif i == len(seg) - 1:
            pm, plat, plon = seg[i - 1]
            bearing = math.degrees(math.atan2(lon - plon, lat - plat))
        else:
            pm, plat, plon = seg[i - 1]
            nm, nlat, nlon = seg[i + 1]
            bearing = math.degrees(math.atan2(nlon - plon, nlat - plat))
        # Perpendicular offsets
        left_bearing = bearing + 90
        right_bearing = bearing - 90
        left_bank.append(offset_point(lat, lon, left_bearing, width_deg))
        right_bank.append(offset_point(lat, lon, right_bearing, width_deg))
    # Polygon: left bank forward, then right bank reversed
    coords = left_bank + list(reversed(right_bank))
    # Close the polygon
    coords.append(coords[0])
    # Return as [[lng, lat], ...] for Leaflet
    return [[lon, lat] for lat, lon in coords]

PORT_AUTHORITIES = [
    {
        "name": "Port of Greater Baton Rouge",
        "abbr": "PGBR",
        "mile_start": 168.5,
        "mile_end": 253.0,
        "color": "#f59e0b",
        "landmarks": "ExxonMobil refinery to Sunshine Bridge",
    },
    {
        "name": "Port of South Louisiana",
        "abbr": "PSL",
        "mile_start": 114.9,
        "mile_end": 168.5,
        "color": "#10b981",
        "landmarks": "St. James, St. John, St. Charles Parishes",
    },
    {
        "name": "Port of New Orleans",
        "abbr": "NOLA",
        "mile_start": 82.1,
        "mile_end": 114.9,
        "color": "#6366f1",
        "landmarks": "Jefferson Parish line to St. Bernard/Plaquemines line",
    },
    {
        "name": "St. Bernard Port",
        "abbr": "StB",
        "mile_start": 82.1,
        "mile_end": 90.5,
        "color": "#ec4899",
        "landmarks": "Overlaps NOLA tri-parish jurisdiction",
    },
    {
        "name": "Plaquemines Port",
        "abbr": "PLAQ",
        "mile_start": 0.0,
        "mile_end": 81.0,
        "color": "#06b6d4",
        "landmarks": "Parish line to Head of Passes (the Gulf)",
    },
]

port_polygons = []
for pa in PORT_AUTHORITIES:
    coords = make_river_polygon(pa["mile_start"], pa["mile_end"], river_centerline, width_deg=0.028)
    # Label position: midpoint of the segment
    mid_mile = (pa["mile_start"] + pa["mile_end"]) / 2
    mid_pt = interpolate_at_mile(mid_mile, river_centerline)
    port_polygons.append({
        "name": pa["name"],
        "abbr": pa["abbr"],
        "color": pa["color"],
        "landmarks": pa["landmarks"],
        "mileStart": pa["mile_start"],
        "mileEnd": pa["mile_end"],
        "coords": coords,
        "labelLat": mid_pt[0],
        "labelLng": mid_pt[1],
    })

port_polygons_json = json.dumps(port_polygons, ensure_ascii=False)

# Build sidebar legend grouped by type, listing each facility
type_order = ["Refinery", "Chemical Plant", "Tank Storage", "Elevator",
              "Bulk Terminal", "Bulk Plant", "General Cargo", "Mid-Stream"]

legend_html = ""
for zt in type_order:
    items = sorted([f for f in facilities if f["zoneType"] == zt], key=lambda x: x["mile"])
    if not items:
        continue
    clr = COLORS.get(zt, "#9ca3af")
    legend_html += f'<div class="leg-group" data-type="{zt}">\n'
    legend_html += f'  <div class="leg-header" data-type="{zt}"><span class="leg-dot" style="background:{clr}"></span>{zt} ({len(items)})<span class="leg-toggle">&#9660;</span></div>\n'
    legend_html += f'  <div class="leg-list" data-type="{zt}">\n'
    for item in items:
        legend_html += f'    <div class="leg-fac" data-lat="{item["lat"]}" data-lng="{item["lng"]}" data-type="{zt}">{item["displayName"]}</div>\n'
    legend_html += f'  </div>\n'
    legend_html += f'</div>\n'

# Port authority section in sidebar
legend_html += '<div class="leg-group">\n'
legend_html += '  <div class="leg-header" id="portAuthToggle"><span class="leg-dot" style="background:#fff;opacity:0.4"></span>Port Authorities (5)<span class="leg-toggle">&#9660;</span></div>\n'
legend_html += '  <div class="leg-list" id="portAuthList">\n'
for pa in port_polygons:
    legend_html += f'    <div class="leg-fac port-auth-item" data-lat="{pa["labelLat"]}" data-lng="{pa["labelLng"]}" data-abbr="{pa["abbr"]}" style="border-left:3px solid {pa["color"]};padding-left:10px;">{pa["name"]}<br><span style="font-size:10px;color:#666;">RM {pa["mileStart"]:.0f}-{pa["mileEnd"]:.0f} | {pa["landmarks"]}</span></div>\n'
legend_html += '  </div>\n'
legend_html += '</div>\n'

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lower Mississippi River Industrial Infrastructure Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #1a1a2e; display: flex; }}

  .sidebar {{
    width: 340px;
    min-width: 340px;
    height: 100vh;
    background: #12122a;
    border-right: 1px solid #2a2a4a;
    display: flex;
    flex-direction: column;
    z-index: 1001;
  }}
  .sidebar-header {{
    padding: 14px 16px;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
  }}
  .sidebar-header h1 {{ font-size: 15px; color: #fff; margin-bottom: 2px; }}
  .sidebar-header .sub {{ font-size: 11px; color: #0ea5e9; }}
  .sidebar-search {{
    padding: 8px 12px;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
  }}
  .sidebar-search input {{
    width: 100%;
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #fff;
    padding: 7px 12px;
    border-radius: 6px;
    font-size: 12px;
    outline: none;
  }}
  .sidebar-search input:focus {{ border-color: #0ea5e9; }}
  .sidebar-body {{
    flex: 1;
    overflow-y: auto;
    padding: 6px 0;
  }}
  .sidebar-body::-webkit-scrollbar {{ width: 6px; }}
  .sidebar-body::-webkit-scrollbar-track {{ background: #12122a; }}
  .sidebar-body::-webkit-scrollbar-thumb {{ background: #2a2a4a; border-radius: 3px; }}

  .leg-group {{ margin-bottom: 2px; }}
  .leg-header {{
    display: flex;
    align-items: center;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    color: #e0e0e0;
    background: #1a1a2e;
    position: sticky;
    top: 0;
    z-index: 2;
    user-select: none;
  }}
  .leg-header:hover {{ background: #1e1e3a; }}
  .leg-header.type-hidden {{ opacity: 0.35; }}
  .leg-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
    flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.15);
  }}
  .leg-toggle {{
    margin-left: auto;
    font-size: 10px;
    color: #666;
    transition: transform 0.2s;
  }}
  .leg-header.collapsed .leg-toggle {{ transform: rotate(-90deg); }}
  .leg-list {{ display: block; }}
  .leg-list.collapsed {{ display: none; }}

  .leg-fac {{
    padding: 4px 14px 4px 32px;
    font-size: 11.5px;
    color: #b0b0c0;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.1s;
  }}
  .leg-fac:hover {{
    background: rgba(14,165,233,0.12);
    color: #fff;
  }}
  .leg-fac.active {{
    background: rgba(14,165,233,0.2);
    color: #0ea5e9;
  }}

  /* Layer toggles */
  .layers-panel {{
    padding: 8px 14px;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
  }}
  .layers-panel .lp-title {{
    font-size: 10px;
    font-weight: 600;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }}
  .layer-toggle {{
    display: flex;
    align-items: center;
    padding: 3px 0;
    font-size: 11.5px;
    color: #b0b0c0;
    cursor: pointer;
    user-select: none;
  }}
  .layer-toggle:hover {{ color: #fff; }}
  .layer-toggle .lt-switch {{
    position: relative;
    width: 30px;
    height: 16px;
    background: #2a2a4a;
    border-radius: 8px;
    margin-right: 8px;
    flex-shrink: 0;
    transition: background 0.2s;
  }}
  .layer-toggle .lt-switch::after {{
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 12px;
    height: 12px;
    background: #666;
    border-radius: 50%;
    transition: all 0.2s;
  }}
  .layer-toggle.active .lt-switch {{
    background: #0ea5e9;
  }}
  .layer-toggle.active .lt-switch::after {{
    left: 16px;
    background: #fff;
  }}
  .layer-toggle .lt-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    flex-shrink: 0;
  }}

  .sidebar-footer {{
    padding: 8px 14px;
    border-top: 1px solid #2a2a4a;
    font-size: 11px;
    color: #666;
    flex-shrink: 0;
  }}
  .sidebar-footer .val {{ color: #0ea5e9; font-weight: 600; }}

  #map {{ flex: 1; height: 100vh; }}

  .leaflet-popup-content-wrapper {{
    border-radius: 8px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
  }}

  .facility-label {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 10px;
    font-weight: 600;
    color: #e0e0e0;
    text-shadow: 1px 1px 3px #000, -1px -1px 3px #000, 0 0 6px #000;
    white-space: nowrap;
    pointer-events: none !important;
  }}

  /* Landmark labels - always visible, offset right with arrow */
  .landmark-label {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 700;
    white-space: nowrap;
    pointer-events: none !important;
    display: flex;
    align-items: center;
  }}
  .landmark-label .lm-text {{
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(10,10,25,0.8);
  }}
  .landmark-label .lm-arrow {{
    width: 60px;
    height: 2px;
    position: relative;
    margin-right: 4px;
  }}
  .landmark-label .lm-arrow::after {{
    content: '';
    position: absolute;
    left: -1px;
    top: -4px;
    border: 5px solid transparent;
    border-right-width: 8px;
  }}
  .landmark-label.anchor {{
    font-size: 17px;
  }}
  .landmark-label.anchor .lm-text {{
    color: #fbbf24;
    text-shadow: 0 0 10px rgba(251,191,36,0.4);
    border: 1px solid rgba(251,191,36,0.3);
  }}
  .landmark-label.anchor .lm-arrow {{
    background: #fbbf24;
  }}
  .landmark-label.anchor .lm-arrow::after {{
    border-right-color: #fbbf24;
  }}

  /* Port authority callout labels - west side of river, arrow points right */
  .pa-callout {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 700;
    white-space: nowrap;
    pointer-events: none !important;
    display: flex;
    align-items: center;
    font-size: 13px;
  }}
  .pa-callout .pa-text {{
    padding: 3px 10px;
    border-radius: 4px;
    background: rgba(10,10,25,0.8);
    text-shadow: 0 0 8px #000;
  }}
  .pa-callout .pa-arrow {{
    width: 90px;
    height: 2px;
    position: relative;
    margin-left: 4px;
  }}
  .pa-callout .pa-arrowhead {{
    width: 0;
    height: 0;
    border: 5px solid transparent;
    border-left-width: 8px;
    margin-left: 0px;
  }}

  /* Mile marker labels */
  .mile-label {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 9px;
    font-weight: 600;
    color: rgba(180,200,220,0.7);
    text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;
    white-space: nowrap;
    pointer-events: none !important;
    font-variant-numeric: tabular-nums;
  }}
  .mile-label-major {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 11px;
    font-weight: 700;
    color: rgba(200,220,240,0.85);
    text-shadow: 1px 1px 3px #000, -1px -1px 3px #000, 0 0 6px #000;
    white-space: nowrap;
    pointer-events: none !important;
    font-variant-numeric: tabular-nums;
  }}

  /* Star marker for Port Nickel */
  .port-nickel-icon {{
    width: 36px !important;
    height: 36px !important;
    background: none !important;
    border: none !important;
    opacity: 0.25;
  }}
  .port-nickel-icon svg {{
    filter: drop-shadow(0 0 8px rgba(251,191,36,0.6));
  }}

  /* POI markers */
  .poi-icon {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    opacity: 0.8;
  }}
  .poi-label {{
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 700;
    white-space: nowrap;
    pointer-events: none !important;
    display: flex;
    align-items: center;
    font-size: 12px;
  }}
  .poi-label .poi-text {{
    padding: 2px 7px;
    border-radius: 3px;
    background: rgba(10,10,25,0.8);
    text-shadow: 0 0 6px #000;
  }}
  .poi-label .poi-line {{
    width: 50px;
    height: 2px;
    margin-right: 4px;
  }}
  .poi-label .poi-tip {{
    width: 0; height: 0;
    border: 4px solid transparent;
    border-right-width: 6px;
  }}

  /* Scene/Story map buttons */
  .scenes-panel {{
    padding: 8px 14px;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
  }}
  .scenes-panel .sp-title {{
    font-size: 9px;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }}
  .scene-btn {{
    display: block;
    width: 100%;
    padding: 6px 10px;
    margin: 3px 0;
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 5px;
    color: #b0b0c0;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
  }}
  .scene-btn:hover {{
    background: #1e1e3a;
    border-color: #0ea5e9;
    color: #fff;
  }}
  .scene-btn.active {{
    background: rgba(14,165,233,0.15);
    border-color: #0ea5e9;
    color: #0ea5e9;
  }}
  .scene-btn .sb-label {{
    display: block;
    font-size: 11px;
    font-weight: 600;
  }}
  .scene-btn .sb-desc {{
    display: block;
    font-size: 9px;
    color: #666;
    margin-top: 1px;
  }}

  /* Rail carrier labels */
  .carrier-label {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 10px;
    font-weight: 700;
    text-shadow: 0 0 4px #000, 0 0 8px #000, 1px 1px 2px #000;
    white-space: nowrap;
    pointer-events: none !important;
  }}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>Lower Mississippi River</h1>
    <div class="sub">Industrial Infrastructure | Mile 0-234 | {len(facilities)} Facilities</div>
  </div>
  <div class="sidebar-search">
    <input type="text" id="sideSearch" placeholder="Filter facilities..." oninput="filterLegend(this.value)">
  </div>
  <div class="scenes-panel">
    <div class="sp-title">Story Map Views</div>
    <button class="scene-btn active" data-scene="overview">
      <span class="sb-label">Overview</span>
      <span class="sb-desc">Full corridor, Mile 0-234</span>
    </button>
    <button class="scene-btn" data-scene="industrial">
      <span class="sb-label">Industrial Corridor</span>
      <span class="sb-desc">St. James to Norco refineries &amp; plants</span>
    </button>
    <button class="scene-btn" data-scene="nola">
      <span class="sb-label">New Orleans Hub</span>
      <span class="sb-desc">Port NOLA terminals &amp; cargo</span>
    </button>
    <button class="scene-btn" data-scene="gulf">
      <span class="sb-label">Gulf &amp; Offshore</span>
      <span class="sb-desc">LOOP, Port Fourchon, SW Pass</span>
    </button>
    <button class="scene-btn" data-scene="transport">
      <span class="sb-label">Transport Network</span>
      <span class="sb-desc">Pipelines &amp; rail overview</span>
    </button>
    <button class="scene-btn" data-scene="grain">
      <span class="sb-label">Grain Belt</span>
      <span class="sb-desc">Export elevators, Reserve to Westwego</span>
    </button>
  </div>
  <div class="layers-panel">
    <div class="lp-title">Layers</div>
    <div class="layer-toggle active" data-layer="river"><span class="lt-switch"></span><span class="lt-dot" style="background:#3b82f6"></span>River Line</div>
    <div class="layer-toggle active" data-layer="milemarkers"><span class="lt-switch"></span><span class="lt-dot" style="background:#94a3b8"></span>Mile Markers</div>
    <div class="layer-toggle active" data-layer="portauth"><span class="lt-switch"></span><span class="lt-dot" style="background:#fff;opacity:0.5"></span>Port Authorities</div>
    <div class="layer-toggle active" data-layer="landmarks"><span class="lt-switch"></span><span class="lt-dot" style="background:#fbbf24"></span>Port Nickel</div>
    <div class="layer-toggle active" data-layer="pois"><span class="lt-switch"></span><span class="lt-dot" style="background:#e879f9"></span>Points of Interest</div>
    <div style="border-top:1px solid #2a2a4a;margin:6px 0 2px;"></div>
    <div style="font-size:9px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;padding:0 0 3px;">Transport</div>
    <div class="layer-toggle active" data-layer="class1rail"><span class="lt-switch"></span><span class="lt-dot" style="background:#ffe119"></span>Class I Rail</div>
    <div class="layer-toggle active" data-layer="termrail"><span class="lt-switch"></span><span class="lt-dot" style="background:#e6194b"></span>Terminal Rail</div>
    <div class="layer-toggle active" data-layer="pipelines"><span class="lt-switch"></span><span class="lt-dot" style="background:#ff4444"></span>Crude Pipelines</div>
    <div class="layer-toggle active" data-layer="pipelines-hgl"><span class="lt-switch"></span><span class="lt-dot" style="background:#ff44aa"></span>HGL Pipelines</div>
    <div class="layer-toggle active" data-layer="pipelines-product"><span class="lt-switch"></span><span class="lt-dot" style="background:#44aaff"></span>Product Pipelines</div>
    <div style="border-top:1px solid #2a2a4a;margin:6px 0 2px;"></div>
    <div style="font-size:9px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;padding:0 0 3px;">Facilities</div>
    <div class="layer-toggle active" data-layer="type-Refinery"><span class="lt-switch"></span><span class="lt-dot" style="background:#e94560"></span>Refineries</div>
    <div class="layer-toggle active" data-layer="type-Chemical Plant"><span class="lt-switch"></span><span class="lt-dot" style="background:#ff6b35"></span>Chemical Plants</div>
    <div class="layer-toggle active" data-layer="type-Tank Storage"><span class="lt-switch"></span><span class="lt-dot" style="background:#0ea5e9"></span>Tank Storage</div>
    <div class="layer-toggle active" data-layer="type-Elevator"><span class="lt-switch"></span><span class="lt-dot" style="background:#22c55e"></span>Elevators</div>
    <div class="layer-toggle active" data-layer="type-Bulk Terminal"><span class="lt-switch"></span><span class="lt-dot" style="background:#a855f7"></span>Bulk Terminals</div>
    <div class="layer-toggle active" data-layer="type-Bulk Plant"><span class="lt-switch"></span><span class="lt-dot" style="background:#8b5cf6"></span>Bulk Plants</div>
    <div class="layer-toggle active" data-layer="type-General Cargo"><span class="lt-switch"></span><span class="lt-dot" style="background:#eab308"></span>General Cargo</div>
    <div class="layer-toggle active" data-layer="type-Mid-Stream"><span class="lt-switch"></span><span class="lt-dot" style="background:#94a3b8"></span>Mid-Stream</div>
  </div>
  <div class="sidebar-body" id="legendBody">
    {legend_html}
  </div>
  <div class="sidebar-footer">
    Showing <span class="val" id="visCount">{len(facilities)}</span> / {len(facilities)} facilities
  </div>
</div>

<div id="map"></div>

<script>
const features = {features_json};

const map = L.map('map', {{
  center: [29.95, -90.15],
  zoom: 9,
  zoomControl: true,
}});

const dark = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OSM &copy; CARTO', maxZoom: 19
}});
const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: '&copy; Esri', maxZoom: 19
}});
const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OSM', maxZoom: 19
}});

dark.addTo(map);
L.control.layers({{ 'Dark': dark, 'Satellite': satellite, 'OpenStreetMap': osm }}, {{}}, {{ position: 'bottomright' }}).addTo(map);

const markers = [];
const labels = [];

features.forEach(function(f, idx) {{
  const marker = L.circleMarker([f.lat, f.lng], {{
    radius: getRadius(f),
    fillColor: f.color,
    color: '#fff',
    weight: 1.2,
    opacity: 0.9,
    fillOpacity: 0.85,
  }});
  marker.bindPopup(f.popup, {{ maxWidth: 400 }});
  marker.featureData = f;
  marker.addTo(map);
  markers.push(marker);

  const label = L.marker([f.lat, f.lng], {{
    icon: L.divIcon({{
      className: 'facility-label',
      html: f.displayName,
      iconSize: [0, 0],
      iconAnchor: [-10, 6],
    }}),
    interactive: false,
  }});
  label.featureData = f;
  labels.push(label);
}});

// ---- River Line ----
const riverCoords = {river_coords_json};
const riverLine = L.polyline(riverCoords, {{
  color: '#3b82f6',
  weight: 2.5,
  opacity: 0.5,
  smoothFactor: 1,
}}).addTo(map);

// ---- Mile Markers ----
const mileMarkers = {mile_markers_json};
const mileTickLayers = [];
const mileLabelLayers = [];

mileMarkers.forEach(function(mm) {{
  const mile = mm.mile;
  // Small tick for every mile
  const tick = L.circleMarker([mm.lat, mm.lng], {{
    radius: 1.5,
    fillColor: '#94a3b8',
    color: '#94a3b8',
    weight: 0,
    fillOpacity: 0.5,
  }});
  tick.mmData = mm;
  mileTickLayers.push(tick);

  // Labels: every 10 miles = major, every 5 = minor
  if (mile % 5 === 0) {{
    const isMajor = mile % 10 === 0;
    const cls = isMajor ? 'mile-label-major' : 'mile-label';
    const label = L.marker([mm.lat, mm.lng], {{
      icon: L.divIcon({{
        className: cls,
        html: 'RM ' + mile,
        iconSize: [0, 0],
        iconAnchor: [15, -4],
      }}),
      interactive: false,
      zIndexOffset: isMajor ? 600 : 500,
    }});
    label.mmData = mm;
    label.isMajor = isMajor;
    mileLabelLayers.push(label);

    // Slightly larger tick at 5-mile intervals
    const majorTick = L.circleMarker([mm.lat, mm.lng], {{
      radius: isMajor ? 3 : 2,
      fillColor: isMajor ? '#cbd5e1' : '#94a3b8',
      color: '#fff',
      weight: isMajor ? 0.8 : 0.5,
      fillOpacity: 0.7,
    }});
    majorTick.mmData = mm;
    mileTickLayers.push(majorTick);
  }}
}});

// ---- Layer State (declared early so toggle-aware functions can reference it) ----
const layerState = {{
  river: true,
  milemarkers: true,
  portauth: true,
  landmarks: true,
  pois: true,
  class1rail: true,
  termrail: true,
  pipelines: true,
}};

// Show ticks/labels based on zoom and layer toggle state
function updateMileMarkers() {{
  const z = map.getZoom();
  const show = layerState.milemarkers !== false;
  mileTickLayers.forEach(function(t) {{
    if (show && z >= 10) t.addTo(map);
    else map.removeLayer(t);
  }});
  mileLabelLayers.forEach(function(lbl) {{
    if (show && lbl.isMajor && z >= 10) lbl.addTo(map);
    else if (show && !lbl.isMajor && z >= 12) lbl.addTo(map);
    else map.removeLayer(lbl);
  }});
}}
// (zoom-dependent updates handled by unified updateAllZoomLayers below)

// ---- Class I Rail (LA Region, Main Routes) ----
const class1Data = {class1_rail_json};
const class1Labels50 = {class1_labels_50_json};
const class1Labels5 = {class1_labels_5_json};
const carrierColors = {carrier_colors_json};
const class1Order = ['UP','BNSF','CSXT','NS','CN','CPRS'];
const class1Layers = {{}};

class1Order.forEach(function(code) {{
  const cc = carrierColors[code];
  if (!cc) return;
  const feats = class1Data.features.filter(f => f.properties.RROWNER1 === code);
  if (feats.length === 0) return;
  const lyr = L.geoJSON({{type:'FeatureCollection', features:feats}}, {{
    style: {{ color: cc.color, weight: 3, opacity: 0.75 }},
    onEachFeature: function(f, layer) {{
      layer.bindPopup('<b>' + cc.name + '</b><br><i>Class I Main Route</i>');
    }}
  }});
  lyr.addTo(map);
  class1Layers[code] = lyr;
}});

// Class 1 labels - zoom dependent
const c1Labels50Layer = L.geoJSON(class1Labels50, {{
  pointToLayer: function(f, ll) {{ return L.circleMarker(ll, {{radius:0, opacity:0, fillOpacity:0}}); }},
  onEachFeature: function(f, layer) {{
    const cc = carrierColors[f.properties.RROWNER1];
    const clr = cc ? cc.color : '#fff';
    layer.bindTooltip(f.properties.LABEL, {{
      permanent:true, direction:'center', className:'carrier-label',
    }});
    layer._labelColor = clr;
  }}
}});

const c1Labels5Layer = L.geoJSON(class1Labels5, {{
  pointToLayer: function(f, ll) {{ return L.circleMarker(ll, {{radius:0, opacity:0, fillOpacity:0}}); }},
  onEachFeature: function(f, layer) {{
    const cc = carrierColors[f.properties.RROWNER1];
    const clr = cc ? cc.color : '#fff';
    layer.bindTooltip(f.properties.LABEL, {{
      permanent:true, direction:'center', className:'carrier-label',
    }});
    layer._labelColor = clr;
  }}
}});

function colorRailLabels(layerGroup) {{
  layerGroup.eachLayer(function(layer) {{
    const tt = layer.getTooltip();
    if (tt && tt._container && layer._labelColor) {{
      tt._container.style.color = layer._labelColor;
    }}
  }});
}}

function updateClass1Labels() {{
  const z = map.getZoom();
  const show = layerState.class1rail;
  if (show && z >= 8 && z <= 10) {{
    if (!map.hasLayer(c1Labels50Layer)) c1Labels50Layer.addTo(map);
    if (map.hasLayer(c1Labels5Layer)) map.removeLayer(c1Labels5Layer);
    setTimeout(function() {{ colorRailLabels(c1Labels50Layer); }}, 100);
  }} else if (show && z >= 11) {{
    if (map.hasLayer(c1Labels50Layer)) map.removeLayer(c1Labels50Layer);
    if (!map.hasLayer(c1Labels5Layer)) c1Labels5Layer.addTo(map);
    setTimeout(function() {{ colorRailLabels(c1Labels5Layer); }}, 100);
  }} else {{
    if (map.hasLayer(c1Labels50Layer)) map.removeLayer(c1Labels50Layer);
    if (map.hasLayer(c1Labels5Layer)) map.removeLayer(c1Labels5Layer);
  }}
}}

// ---- Terminal Railroads (NOPB & NOGC) ----
const nopbNogcData = {nopb_nogc_json};
const nopbNogcLabelsData = {nopb_nogc_labels_json};
const termLayers = {{}};

['NOPB','NOGC'].forEach(function(code) {{
  const cc = carrierColors[code];
  if (!cc) return;
  const feats = nopbNogcData.features.filter(f => f.properties.RROWNER1 === code);
  if (feats.length === 0) return;
  const lyr = L.geoJSON({{type:'FeatureCollection', features:feats}}, {{
    style: {{ color: cc.color, weight: 3, opacity: 0.75 }},
    onEachFeature: function(f, layer) {{
      layer.bindPopup('<b>' + cc.name + '</b><br><i>Terminal Railroad</i>');
    }}
  }});
  lyr.addTo(map);
  termLayers[code] = lyr;
}});

const termLabelsLayer = L.geoJSON(nopbNogcLabelsData, {{
  pointToLayer: function(f, ll) {{ return L.circleMarker(ll, {{radius:0, opacity:0, fillOpacity:0}}); }},
  onEachFeature: function(f, layer) {{
    const cc = carrierColors[f.properties.RROWNER1];
    const clr = cc ? cc.color : '#fff';
    layer.bindTooltip(f.properties.LABEL, {{
      permanent:true, direction:'center', className:'carrier-label',
    }});
    layer._labelColor = clr;
  }}
}});

function updateTermLabels() {{
  const z = map.getZoom();
  const show = layerState.termrail;
  if (show && z >= 11) {{
    if (!map.hasLayer(termLabelsLayer)) termLabelsLayer.addTo(map);
    setTimeout(function() {{ colorRailLabels(termLabelsLayer); }}, 100);
  }} else {{
    if (map.hasLayer(termLabelsLayer)) map.removeLayer(termLabelsLayer);
  }}
}}

// ---- Pipelines (HGL, Crude, Product) ----
const pipelineData = {pipeline_json};
const pipelineLayers = [];
const pipeTypeColors = {{
  'Crude': '#ff4444',
  'HGL': '#ff44aa',
  'Product': '#44aaff',
}};

const pipeLayersByType = {{ 'Crude': [], 'HGL': [], 'Product': [] }};

pipelineData.features.forEach(function(feat) {{
  const name = feat.properties._pipeName || 'Unknown';
  const op = feat.properties._pipeOp || '';
  const ptype = feat.properties._pipeType || 'Unknown';
  const clr = pipeTypeColors[ptype] || '#ff44aa';
  const lyr = L.geoJSON(feat, {{
    style: {{ color: clr, weight: 2.5, opacity: 0.55, dashArray: '8,4' }},
    onEachFeature: function(f, layer) {{
      layer.bindPopup('<b>' + name + '</b><br>Operator: ' + op + '<br><i>' + ptype + ' Pipeline</i>');
    }}
  }});
  lyr.addTo(map);
  pipelineLayers.push(lyr);
  if (pipeLayersByType[ptype]) pipeLayersByType[ptype].push(lyr);
}});

// ---- Port Authority Jurisdiction Polygons ----
const portPolygons = {port_polygons_json};
const portLayers = [];
const portLabelLayers = [];

portPolygons.forEach(function(pa) {{
  // Convert [lng, lat] to [lat, lng] for Leaflet
  const latlngs = pa.coords.map(c => [c[1], c[0]]);
  const poly = L.polygon(latlngs, {{
    color: pa.color,
    weight: 2,
    opacity: 0.7,
    fillColor: pa.color,
    fillOpacity: 0.12,
    dashArray: '6,4',
  }});
  poly.bindPopup(
    '<div style="font-family:system-ui;font-size:13px;">' +
    '<div style="font-size:15px;font-weight:700;color:#1a1a2e;">' + pa.name + '</div>' +
    '<div style="color:#666;font-size:11px;margin:4px 0;">RM ' + pa.mileStart.toFixed(1) + ' to RM ' + pa.mileEnd.toFixed(1) + '</div>' +
    '<div>' + pa.landmarks + '</div></div>',
    {{ maxWidth: 300 }}
  );
  poly.paData = pa;
  portLayers.push(poly);

  // Callout label on the west (left) side of river
  const paLabelHtml = '<span class="pa-text" style="color:' + pa.color + ';border:1px solid ' + pa.color + '40;">' + pa.name + '</span><span class="pa-arrow" style="background:' + pa.color + ';"></span><span class="pa-arrowhead" style="border-left-color:' + pa.color + ';"></span>';
  const portLabel = L.marker([pa.labelLat, pa.labelLng], {{
    icon: L.divIcon({{
      className: 'pa-callout',
      html: paLabelHtml,
      iconSize: [400, 30],
      iconAnchor: [400, 15],
    }}),
    interactive: false,
    zIndexOffset: 700,
  }});
  portLabelLayers.push(portLabel);
}});

// Toggle port authority visibility from sidebar
document.getElementById('portAuthToggle').addEventListener('click', function() {{
  const list = document.getElementById('portAuthList');
  if (list.classList.contains('collapsed')) {{
    list.classList.remove('collapsed');
    this.classList.remove('collapsed');
  }} else {{
    list.classList.add('collapsed');
    this.classList.add('collapsed');
  }}
}});
document.getElementById('portAuthToggle').addEventListener('contextmenu', function(e) {{
  e.preventDefault();
  layerState.portauth = !layerState.portauth;
  updatePortAuthZoom();
  this.classList.toggle('type-hidden');
  // Sync toggle panel
  const toggle = document.querySelector('.layer-toggle[data-layer="portauth"]');
  if (toggle) {{
    if (layerState.portauth) toggle.classList.add('active');
    else toggle.classList.remove('active');
  }}
}});

// Click port authority in sidebar -> fly to it
document.querySelectorAll('.port-auth-item').forEach(function(el) {{
  el.addEventListener('click', function() {{
    const lat = parseFloat(this.dataset.lat);
    const lng = parseFloat(this.dataset.lng);
    map.flyTo([lat, lng], 10, {{ duration: 1.2 }});
  }});
}});

// ---- Reference Landmarks (always visible) ----
// Port Nickel - star marker with label
const landmarkLayers = [];
(function() {{
  const starSvg = '<svg viewBox="0 0 36 36" width="36" height="36"><polygon points="18,2 22.5,13 34,13 24.8,20.5 28.5,32 18,25 7.5,32 11.2,20.5 2,13 13.5,13" fill="#fbbf24" stroke="#fff" stroke-width="1.5"/></svg>';
  const starIcon = L.divIcon({{
    className: 'port-nickel-icon',
    html: starSvg,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  }});
  const dot = L.marker([29.8597, -89.9728], {{ icon: starIcon, interactive: false, zIndexOffset: 900 }});
  dot.addTo(map);
  landmarkLayers.push(dot);

  const labelHtml = '<span class="lm-arrow"></span><span class="lm-text">Port Nickel (Mile 76)</span>';
  const lbl = L.marker([29.8597, -89.9728], {{
    icon: L.divIcon({{
      className: 'landmark-label anchor',
      html: labelHtml,
      iconSize: [300, 30],
      iconAnchor: [-80, 15],
    }}),
    interactive: false,
    zIndexOffset: 800,
  }});
  lbl.addTo(map);
  landmarkLayers.push(lbl);

  // New Orleans reference label
  const nolaHtml = '<span class="lm-arrow"></span><span class="lm-text">New Orleans (Mile 100)</span>';
  const nolaLbl = L.marker([29.94, -90.10], {{
    icon: L.divIcon({{
      className: 'landmark-label anchor',
      html: nolaHtml,
      iconSize: [300, 30],
      iconAnchor: [-80, 15],
    }}),
    interactive: false,
    zIndexOffset: 800,
  }});
  nolaLbl.addTo(map);
  landmarkLayers.push(nolaLbl);

  // Baton Rouge reference label
  const brHtml = '<span class="lm-arrow"></span><span class="lm-text">Baton Rouge (Mile 232)</span>';
  const brLbl = L.marker([30.47, -91.18], {{
    icon: L.divIcon({{
      className: 'landmark-label anchor',
      html: brHtml,
      iconSize: [300, 30],
      iconAnchor: [-80, 15],
    }}),
    interactive: false,
    zIndexOffset: 800,
  }});
  brLbl.addTo(map);
  landmarkLayers.push(brLbl);
}})();

// ---- Points of Interest (LOOP, Port Fourchon, SW Pass Lightering) ----
const poiLayers = [];
const poisData = [
  {{
    name: 'LOOP (LA Offshore Oil Port)',
    lat: 28.885,
    lng: -90.025,
    color: '#e879f9',
    desc: 'Louisiana Offshore Oil Port — deepwater crude terminal 18 mi offshore. Handles supertanker imports via subsea pipeline to Clovelly.',
  }},
  {{
    name: 'Port Fourchon',
    lat: 29.1155,
    lng: -90.2067,
    color: '#e879f9',
    desc: 'Major service base for Gulf of Mexico oil &amp; gas operations. Supports 90%+ of deepwater Gulf activity.',
  }},
  {{
    name: 'SW Pass Lightering Zone',
    lat: 28.70,
    lng: -89.50,
    color: '#e879f9',
    desc: 'Ship-to-ship transfer area south of Head of Passes. Crude lightering for draft-restricted vessels entering the river.',
  }},
  {{
    name: 'Mile 0 SWP',
    lat: 29.0085,
    lng: -89.3398,
    color: '#e879f9',
    desc: 'Southwest Pass Mile 0 — Head of Passes, where the Mississippi splits into its distributary passes entering the Gulf of Mexico.',
  }},
];

poisData.forEach(function(poi) {{
  const diamondSvg = '<svg viewBox="0 0 24 24" width="24" height="24"><polygon points="12,2 22,12 12,22 2,12" fill="' + poi.color + '" stroke="#fff" stroke-width="1.5" opacity="0.8"/></svg>';
  const icon = L.divIcon({{
    className: 'poi-icon',
    html: diamondSvg,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  }});
  const m = L.marker([poi.lat, poi.lng], {{ icon: icon, zIndexOffset: 850 }});
  m.bindPopup('<div style="font-family:system-ui;font-size:13px;min-width:220px;"><div style="font-size:15px;font-weight:700;color:#1a1a2e;">' + poi.name + '</div><div style="margin-top:6px;color:#444;">' + poi.desc + '</div></div>');
  m.addTo(map);
  poiLayers.push(m);

  const labelHtml = '<span class="poi-line" style="background:' + poi.color + ';"></span><span class="poi-tip" style="border-right-color:' + poi.color + ';"></span><span class="poi-text" style="color:' + poi.color + ';border:1px solid ' + poi.color + '40;">' + poi.name + '</span>';
  const lbl = L.marker([poi.lat, poi.lng], {{
    icon: L.divIcon({{
      className: 'poi-label',
      html: labelHtml,
      iconSize: [300, 30],
      iconAnchor: [-20, 15],
    }}),
    interactive: false,
    zIndexOffset: 800,
  }});
  lbl.addTo(map);
  poiLayers.push(lbl);
}});

function updateLabels() {{
  const z = map.getZoom();
  labels.forEach(function(lbl) {{
    if (z >= 11 && !hiddenTypes.has(lbl.featureData.zoneType)) {{
      lbl.addTo(map);
    }} else {{
      map.removeLayer(lbl);
    }}
  }});
}}

// ---- Zoom-dependent layer visibility ----
// Port authority polygons/labels: show at zoom <= 12, fade at 13+
// Facility labels: zoom 11+
// Mile markers: zoom 10+/12+ (handled in updateMileMarkers)
function updatePortAuthZoom() {{
  const z = map.getZoom();
  const show = layerState.portauth && z <= 12;
  portLayers.forEach(function(pl) {{
    if (show) pl.addTo(map);
    else map.removeLayer(pl);
  }});
  portLabelLayers.forEach(function(pl) {{
    if (show) pl.addTo(map);
    else map.removeLayer(pl);
  }});
}}

function updateAllZoomLayers() {{
  updateLabels();
  updateMileMarkers();
  updatePortAuthZoom();
  updateClass1Labels();
  updateTermLabels();
}}
map.on('zoomend', updateAllZoomLayers);
updateAllZoomLayers();

function getRadius(f) {{
  const ec = f.eventCount || 0;
  if (ec > 5000) return 11;
  if (ec > 2000) return 9;
  if (ec > 500) return 7;
  if (ec > 100) return 6;
  return 5;
}}

const hiddenTypes = new Set();
document.querySelectorAll('.leg-header').forEach(function(hdr) {{
  hdr.addEventListener('contextmenu', function(e) {{
    e.preventDefault();
    const t = this.dataset.type;
    if (!t) return;
    if (hiddenTypes.has(t)) {{
      hiddenTypes.delete(t);
      this.classList.remove('type-hidden');
    }} else {{
      hiddenTypes.add(t);
      this.classList.add('type-hidden');
    }}
    updateVisibility();
    // Sync toggle panel
    const toggle = document.querySelector('.layer-toggle[data-layer="type-' + t + '"]');
    if (toggle) {{
      if (hiddenTypes.has(t)) toggle.classList.remove('active');
      else toggle.classList.add('active');
    }}
  }});
  hdr.addEventListener('click', function() {{
    const t = this.dataset.type;
    const list = document.querySelector('.leg-list[data-type="' + t + '"]');
    if (list.classList.contains('collapsed')) {{
      list.classList.remove('collapsed');
      this.classList.remove('collapsed');
    }} else {{
      list.classList.add('collapsed');
      this.classList.add('collapsed');
    }}
  }});
}});

function updateVisibility() {{
  let count = 0;
  markers.forEach(function(m) {{
    if (hiddenTypes.has(m.featureData.zoneType)) {{
      map.removeLayer(m);
    }} else {{
      m.addTo(map);
      count++;
    }}
  }});
  updateLabels();
  document.getElementById('visCount').textContent = count;
}}

document.querySelectorAll('.leg-fac').forEach(function(el) {{
  el.addEventListener('click', function() {{
    const lat = parseFloat(this.dataset.lat);
    const lng = parseFloat(this.dataset.lng);
    map.flyTo([lat, lng], 14, {{ duration: 1.2 }});
    document.querySelectorAll('.leg-fac.active').forEach(a => a.classList.remove('active'));
    this.classList.add('active');
    let nearest = null;
    let minDist = Infinity;
    markers.forEach(function(m) {{
      const d = Math.abs(m.featureData.lat - lat) + Math.abs(m.featureData.lng - lng);
      if (d < minDist) {{ minDist = d; nearest = m; }}
    }});
    if (nearest) setTimeout(function() {{ nearest.openPopup(); }}, 1300);
  }});
}});

function filterLegend(q) {{
  const lower = q.toLowerCase();
  document.querySelectorAll('.leg-fac').forEach(function(el) {{
    if (!q || q.length < 2) {{
      el.style.display = '';
    }} else {{
      el.style.display = el.textContent.toLowerCase().includes(lower) ? '' : 'none';
    }}
  }});
  document.querySelectorAll('.leg-group').forEach(function(grp) {{
    const anyVisible = grp.querySelectorAll('.leg-fac:not([style*="display: none"])').length > 0;
    grp.style.display = (!q || q.length < 2 || anyVisible) ? '' : 'none';
  }});
}}

// ---- Layer Toggle Controls ----
document.querySelectorAll('.layer-toggle').forEach(function(el) {{
  el.addEventListener('click', function() {{
    const layer = this.dataset.layer;
    const isActive = this.classList.contains('active');

    if (isActive) {{
      this.classList.remove('active');
    }} else {{
      this.classList.add('active');
    }}

    if (layer === 'river') {{
      if (isActive) map.removeLayer(riverLine);
      else riverLine.addTo(map);
      layerState.river = !isActive;
    }}
    else if (layer === 'milemarkers') {{
      layerState.milemarkers = !isActive;
      updateMileMarkers();
    }}
    else if (layer === 'portauth') {{
      layerState.portauth = !isActive;
      updatePortAuthZoom();
    }}
    else if (layer === 'landmarks') {{
      layerState.landmarks = !isActive;
      landmarkLayers.forEach(function(ll) {{
        if (isActive) map.removeLayer(ll);
        else ll.addTo(map);
      }});
    }}
    else if (layer === 'pois') {{
      layerState.pois = !isActive;
      poiLayers.forEach(function(pl) {{
        if (isActive) map.removeLayer(pl);
        else pl.addTo(map);
      }});
    }}
    else if (layer === 'class1rail') {{
      layerState.class1rail = !isActive;
      Object.values(class1Layers).forEach(function(lyr) {{
        if (isActive) map.removeLayer(lyr);
        else lyr.addTo(map);
      }});
      updateClass1Labels();
    }}
    else if (layer === 'termrail') {{
      layerState.termrail = !isActive;
      Object.values(termLayers).forEach(function(lyr) {{
        if (isActive) map.removeLayer(lyr);
        else lyr.addTo(map);
      }});
      updateTermLabels();
    }}
    else if (layer === 'pipelines') {{
      pipeLayersByType['Crude'].forEach(function(lyr) {{
        if (isActive) map.removeLayer(lyr);
        else lyr.addTo(map);
      }});
    }}
    else if (layer === 'pipelines-hgl') {{
      pipeLayersByType['HGL'].forEach(function(lyr) {{
        if (isActive) map.removeLayer(lyr);
        else lyr.addTo(map);
      }});
    }}
    else if (layer === 'pipelines-product') {{
      pipeLayersByType['Product'].forEach(function(lyr) {{
        if (isActive) map.removeLayer(lyr);
        else lyr.addTo(map);
      }});
    }}
    else if (layer.startsWith('type-')) {{
      const typeName = layer.replace('type-', '');
      if (isActive) {{
        hiddenTypes.add(typeName);
      }} else {{
        hiddenTypes.delete(typeName);
      }}
      updateVisibility();
      // Also update the legend header appearance
      document.querySelectorAll('.leg-header[data-type="' + typeName + '"]').forEach(function(h) {{
        if (isActive) h.classList.add('type-hidden');
        else h.classList.remove('type-hidden');
      }});
    }}
  }});
}});

// ---- Story Map Scene Switching ----
const scenePresets = {{
  overview:    {{ center: [29.95, -90.15], zoom: 9 }},
  industrial:  {{ center: [30.05, -90.70], zoom: 10 }},
  nola:        {{ center: [29.94, -90.05], zoom: 11 }},
  gulf:        {{ center: [29.0, -89.8],   zoom: 8 }},
  transport:   {{ center: [29.95, -90.15], zoom: 9 }},
  grain:       {{ center: [29.98, -90.35], zoom: 11 }},
}};

document.querySelectorAll('.scene-btn').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    const key = this.dataset.scene;
    const scene = scenePresets[key];
    if (!scene) return;

    document.querySelectorAll('.scene-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    this.classList.add('active');

    map.flyTo(scene.center, scene.zoom, {{ duration: 1.5 }});
  }});
}});

document.addEventListener('keydown', function(e) {{
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
    e.preventDefault();
    document.getElementById('sideSearch').focus();
  }}
}});
</script>

</body>
</html>"""

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html_doc)

size_kb = os.path.getsize(OUTPUT) / 1024
print(f"Map written: {OUTPUT}")
print(f"Size: {size_kb:.0f} KB")
print(f"Facilities: {len(facilities)} (consolidated from 180 zones)")
for zt in type_order:
    items = [f for f in facilities if f["zoneType"] == zt]
    if items:
        print(f"  {zt}: {len(items)}")
