"""Interactive Leaflet map builder for the Site Master Registry.

Generates a standalone HTML file with commodity-coded, toggleable
GeoJSON layers rendered client-side for performance at 11K+ sites.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .query import SiteRegistryQuery

logger = logging.getLogger(__name__)

# Commodity sector → hex color
SECTOR_COLORS: dict[str, str] = {
    "steel": "#808080",
    "aluminum": "#4682B4",
    "copper": "#FF8C00",
    "cement": "#DC143C",
    "petroleum": "#228B22",
    "chemicals": "#8B008B",
    "grain": "#DAA520",
    "concrete": "#8B0000",
    "nonferrous_metals": "#5F9EA0",
    "aggregates": "#90EE90",
    "industrial": "#4169E1",
}

US_CENTER = [39.5, -98.35]


def _sites_to_geojson(sites: list[dict]) -> dict:
    """Convert site dicts to a GeoJSON FeatureCollection."""
    features = []
    for site in sites:
        lat = site.get("latitude")
        lon = site.get("longitude")
        if lat is None or lon is None:
            continue
        props = {
            "n": site.get("canonical_name", ""),
            "ci": site.get("city", ""),
            "st": site.get("state", ""),
            "se": site.get("commodity_sectors", ""),
            "pa": site.get("parent_company", ""),
            "sc": site.get("source_count", 0),
            "r": 1 if site.get("rail_served") else 0,
            "w": 1 if site.get("water_access") else 0,
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def build_registry_map(
    query: SiteRegistryQuery,
    output_path: str,
    sectors: Optional[list[str]] = None,
    min_sources: int = 0,
    title: str = "US Industrial Site Master Registry",
) -> Path:
    """Build interactive Leaflet map with commodity-coded GeoJSON layers."""
    sites = query.all_sites_for_map(sectors=sectors, min_sources=min_sources)
    logger.info(f"Building map with {len(sites)} sites...")

    # Group by sector
    by_sector: dict[str, list[dict]] = {}
    for site in sites:
        sector = site.get("commodity_sectors") or "industrial"
        by_sector.setdefault(sector, []).append(site)

    # Build per-sector GeoJSON + JS config
    sector_data_blocks = []
    layer_js_lines = []
    overlay_entries = []

    for sector in sorted(by_sector.keys()):
        sector_sites = by_sector[sector]
        color = SECTOR_COLORS.get(sector, "#4169E1")
        geojson = _sites_to_geojson(sector_sites)
        var_name = f"data_{sector.replace(' ', '_')}"
        label = f"{sector.title()} ({len(sector_sites)})"

        sector_data_blocks.append(f"var {var_name} = {json.dumps(geojson, separators=(',', ':'))};")

        layer_js_lines.append(f"""
var layer_{var_name} = L.geoJSON({var_name}, {{
  pointToLayer: function(f, ll) {{
    var r = Math.min(4 + f.properties.sc * 0.5, 12);
    return L.circleMarker(ll, {{
      radius: r, fillColor: '{color}', color: '{color}',
      weight: 1, opacity: 0.8, fillOpacity: 0.6
    }});
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    var h = '<b>' + p.n + '</b>';
    if (p.ci) h += '<br>' + p.ci + ', ' + p.st;
    else if (p.st) h += '<br>' + p.st;
    if (p.se) h += '<br>Sector: ' + p.se;
    if (p.pa) h += '<br>Parent: ' + p.pa;
    var fl = [];
    if (p.r) fl.push('Rail');
    if (p.w) fl.push('Water');
    if (fl.length) h += '<br>Logistics: ' + fl.join(' | ');
    h += '<br>Sources: ' + p.sc;
    layer.bindPopup(h, {{maxWidth: 300}});
    layer.bindTooltip(p.n);
  }}
}}).addTo(map);
""")
        overlay_entries.append(f'  "{label}": layer_{var_name}')

    sector_data_js = "\n".join(sector_data_blocks)
    layers_js = "\n".join(layer_js_lines)
    overlays_js = "{\n" + ",\n".join(overlay_entries) + "\n}"

    # Legend HTML
    legend_rows = "".join(
        f'<div><span class="dot" style="background:{SECTOR_COLORS.get(s, "#4169E1")}"></span>'
        f'{s.title()} ({len(sl)})</div>'
        for s, sl in sorted(by_sector.items())
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body {{ margin:0; padding:0; height:100%; }}
  #map {{ width:100%; height:100%; }}
  .info-box {{
    position:fixed; top:10px; left:55px; z-index:1000;
    background:white; padding:14px 20px; border-radius:6px;
    box-shadow:0 2px 8px rgba(0,0,0,0.3); font-family:Arial,sans-serif;
    font-size:13px; line-height:1.7; max-width:260px;
  }}
  .info-box b {{ font-size:15px; }}
  .info-box hr {{ margin:6px 0; border:0; border-top:1px solid #ddd; }}
  .dot {{
    width:10px; height:10px; display:inline-block;
    border-radius:50%; margin-right:6px; vertical-align:middle;
  }}
</style>
</head>
<body>
<div id="map"></div>
<div class="info-box">
  <b>{title}</b><br>
  <small>{len(sites):,} sites across {len(by_sector)} sectors</small>
  <hr>
  {legend_rows}
</div>
<script>
var map = L.map('map').setView({US_CENTER}, 5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}@2x.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}}).addTo(map);

{sector_data_js}

{layers_js}

L.control.layers(null, {overlays_js}, {{collapsed: false}}).addTo(map);
</script>
</body>
</html>"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
    logger.info(f"Map saved to {path} ({len(sites):,} sites)")
    return path


# ---------------------------------------------------------------------------
# Dashboard (search + filter + map + export)
# ---------------------------------------------------------------------------

def _sites_to_js_array(sites: list[dict]) -> str:
    """Serialize sites to a compact JS array with abbreviated keys.

    Index: 0=uid, 1=name, 2=city, 3=state, 4=county, 5=lat, 6=lon,
           7=parent, 8=facility_types, 9=naics, 10=sector,
           11=rail, 12=barge, 13=water, 14=port_adjacent,
           15=capacity_kt, 16=source_count, 17=confidence_score,
           18=confidence_tier
    """
    rows = []
    for s in sites:
        lat = s.get("latitude")
        lon = s.get("longitude")
        if lat is None or lon is None:
            continue
        row = [
            s.get("facility_uid", ""),
            s.get("canonical_name", ""),
            s.get("city", "") or "",
            s.get("state", "") or "",
            s.get("county", "") or "",
            round(lat, 5),
            round(lon, 5),
            s.get("parent_company", "") or "",
            s.get("facility_types", "") or "",
            s.get("naics_codes", "") or "",
            s.get("commodity_sectors", "") or "",
            1 if s.get("rail_served") else 0,
            1 if s.get("barge_access") else 0,
            1 if s.get("water_access") else 0,
            1 if s.get("port_adjacent") else 0,
            s.get("capacity_kt_year") or 0,
            s.get("source_count", 0) or 0,
            round(s.get("confidence_score", 0) or 0, 2),
            s.get("confidence_tier", 3) or 3,
        ]
        rows.append(row)
    return json.dumps(rows, separators=(",", ":"))


def build_registry_dashboard(
    query: "SiteRegistryQuery",
    output_path: str,
    sectors: Optional[list[str]] = None,
    min_sources: int = 0,
    title: str = "US Industrial Site Master Registry",
) -> Path:
    """Build an interactive search/filter/map/export dashboard as standalone HTML."""
    sites = query.all_sites_for_dashboard(sectors=sectors, min_sources=min_sources)
    logger.info(f"Building dashboard with {len(sites)} sites...")

    summary = query.summary()
    states_list = query.distinct_values("state")
    sectors_list = query.distinct_values("commodity_sectors")

    sites_js = _sites_to_js_array(sites)

    state_options = "".join(f'<option value="{s}">{s}</option>' for s in states_list)
    sector_options = "".join(
        f'<option value="{s}">{s.title()}</option>' for s in sectors_list
    )

    # Sector color map for JS
    sector_color_js = json.dumps(SECTOR_COLORS, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box}}
html,body{{margin:0;padding:0;height:100%;font-family:'Segoe UI',Arial,sans-serif;font-size:13px;color:#333;overflow:hidden}}

/* Header */
#header{{height:52px;background:#1a2332;color:#fff;display:flex;align-items:center;padding:0 20px;gap:24px;flex-shrink:0}}
#header h1{{font-size:16px;margin:0;white-space:nowrap}}
.stat{{font-size:12px;color:#8bb4e0}}
.stat b{{color:#fff;font-size:14px;margin-right:2px}}

/* Main layout */
#main{{display:flex;height:calc(100% - 52px)}}

/* Sidebar */
#sidebar{{width:420px;min-width:380px;background:#f7f8fa;border-right:1px solid #ddd;display:flex;flex-direction:column;overflow:hidden}}
#filters{{padding:12px 14px;border-bottom:1px solid #ddd;background:#fff}}
#filters label{{display:block;font-weight:600;margin:6px 0 2px;font-size:11px;text-transform:uppercase;color:#666;letter-spacing:.3px}}
#filters input[type=text],#filters select{{width:100%;padding:6px 8px;border:1px solid #ccc;border-radius:4px;font-size:13px}}
.filter-row{{display:flex;gap:8px}}
.filter-row>div{{flex:1}}
.cb-row{{display:flex;gap:14px;margin:8px 0 4px;align-items:center}}
.cb-row label{{margin:0;font-weight:normal;text-transform:none;font-size:13px;color:#333}}
.slider-row{{display:flex;align-items:center;gap:8px;margin:4px 0}}
.slider-row input[type=range]{{flex:1}}
.slider-row span{{min-width:20px;text-align:center;font-weight:600}}
.btn-row{{display:flex;gap:8px;margin-top:8px}}
.btn{{padding:6px 14px;border:1px solid #ccc;border-radius:4px;cursor:pointer;font-size:12px;background:#fff}}
.btn:hover{{background:#e8e8e8}}
.btn-primary{{background:#2a6cb6;color:#fff;border-color:#2a6cb6}}
.btn-primary:hover{{background:#1e5a9e}}
.btn-export{{background:#27834a;color:#fff;border-color:#27834a}}
.btn-export:hover{{background:#1e6b3b}}

/* Results count */
#result-count{{padding:8px 14px;font-size:12px;color:#555;border-bottom:1px solid #eee;background:#fff;flex-shrink:0}}

/* Table */
#table-wrap{{flex:1;overflow-y:auto;overflow-x:hidden}}
#sites-table{{width:100%;border-collapse:collapse}}
#sites-table th{{position:sticky;top:0;background:#e9ecf0;padding:6px 8px;text-align:left;font-size:11px;text-transform:uppercase;color:#555;border-bottom:2px solid #ccc;cursor:pointer;user-select:none;white-space:nowrap}}
#sites-table th:hover{{background:#dce0e6}}
#sites-table th .arrow{{font-size:9px;margin-left:3px;color:#999}}
#sites-table td{{padding:5px 8px;border-bottom:1px solid #eee;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px}}
#sites-table tr:hover{{background:#e6f0ff;cursor:pointer}}
#sites-table tr.selected{{background:#cce0ff}}

/* Pagination */
#pagination{{display:flex;align-items:center;justify-content:center;gap:4px;padding:8px;border-top:1px solid #ddd;background:#fff;flex-shrink:0}}
#pagination button{{padding:4px 10px;border:1px solid #ccc;border-radius:3px;cursor:pointer;background:#fff;font-size:12px}}
#pagination button:hover{{background:#e8e8e8}}
#pagination button.active{{background:#2a6cb6;color:#fff;border-color:#2a6cb6}}
#pagination button:disabled{{opacity:.4;cursor:default}}

/* Map */
#map-container{{flex:1;position:relative}}
#map{{width:100%;height:100%}}

/* Legend */
.legend{{background:#fff;padding:10px 14px;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,.25);font-size:12px;line-height:1.8}}
.legend b{{font-size:13px}}
.legend .dot{{width:10px;height:10px;display:inline-block;border-radius:50%;margin-right:6px;vertical-align:middle}}

/* Tier badges */
.tbadge{{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;border-radius:50%;font-size:10px;font-weight:700;color:#fff}}
.tier1{{background:#2a7b3f}}
.tier2{{background:#b8860b}}
.tier3{{background:#999}}

/* Popup */
.leaflet-popup-content{{font-size:12px;line-height:1.6}}
.leaflet-popup-content b{{font-size:13px}}
</style>
</head>
<body>

<!-- Header -->
<div id="header">
  <h1>{title}</h1>
  <span class="stat"><b>{summary['total_sites']:,}</b> Total Sites</span>
  <span class="stat"><b>{summary['rail_served']:,}</b> Rail Served</span>
  <span class="stat"><b>{summary['water_access']:,}</b> Water Access</span>
  <span class="stat"><b>{summary['multimodal']:,}</b> Multimodal</span>
</div>

<div id="main">
  <!-- Sidebar -->
  <div id="sidebar">
    <div id="filters">
      <label for="f-name">Search Name / Parent</label>
      <input type="text" id="f-name" placeholder="Type to filter...">

      <div class="filter-row">
        <div>
          <label for="f-state">State</label>
          <select id="f-state"><option value="">All States</option>{state_options}</select>
        </div>
        <div>
          <label for="f-sector">Sector</label>
          <select id="f-sector"><option value="">All Sectors</option>{sector_options}</select>
        </div>
      </div>

      <div class="filter-row">
        <div>
          <label for="f-tier">Confidence Tier</label>
          <select id="f-tier">
            <option value="0">All Tiers</option>
            <option value="1" selected>Tier 1 — Confirmed</option>
            <option value="12">Tier 1 + 2</option>
            <option value="2">Tier 2 — Probable</option>
            <option value="3">Tier 3 — Unverified</option>
          </select>
        </div>
        <div style="flex:0 0 auto;padding-top:18px">
          <label><input type="checkbox" id="f-rail"> Rail</label>
          <label><input type="checkbox" id="f-water"> Water</label>
          <label><input type="checkbox" id="f-barge"> Barge</label>
        </div>
      </div>

      <label>Min Sources</label>
      <div class="slider-row">
        <input type="range" id="f-minsrc" min="0" max="6" value="0" step="1">
        <span id="minsrc-val">0</span>
      </div>

      <div class="btn-row">
        <button class="btn btn-primary" onclick="applyFilters()">Apply</button>
        <button class="btn" onclick="resetFilters()">Reset</button>
        <button class="btn btn-export" onclick="exportCSV()">&#11015; CSV Export</button>
      </div>
    </div>

    <div id="result-count">Loading...</div>

    <div id="table-wrap">
      <table id="sites-table">
        <thead>
          <tr>
            <th data-col="18" onclick="sortBy(18)">T <span class="arrow"></span></th>
            <th data-col="1" onclick="sortBy(1)">Name <span class="arrow"></span></th>
            <th data-col="2" onclick="sortBy(2)">City <span class="arrow"></span></th>
            <th data-col="3" onclick="sortBy(3)">St <span class="arrow"></span></th>
            <th data-col="10" onclick="sortBy(10)">Sector <span class="arrow"></span></th>
            <th data-col="16" onclick="sortBy(16)">Src <span class="arrow"></span></th>
            <th>Flags</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>

    <div id="pagination"></div>
  </div>

  <!-- Map -->
  <div id="map-container">
    <div id="map"></div>
  </div>
</div>

<script>
// --- Data ---
// Each row: [uid, name, city, state, county, lat, lon, parent, fac_types,
//            naics, sector, rail, barge, water, port_adj, capacity, src_count, confidence, tier]
var SITES={sites_js};
var COLORS={sector_color_js};
var DEFAULT_COLOR="#4169E1";

// --- State ---
var filtered=SITES.slice();
var markers=[];
var markerIndex={{}};
var page=0, perPage=50;
var sortCol=18, sortAsc=true;  // default: tier asc (best first)
var selectedUid=null;
var debounceTimer=null;

// --- Map init ---
var map=L.map('map').setView({US_CENTER},5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}@2x.png',{{
  attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19
}}).addTo(map);

// --- Legend ---
var legendCtrl=L.control({{position:'topright'}});
legendCtrl.onAdd=function(){{
  var d=L.DomUtil.create('div','legend');
  var html='<b>Sectors</b><br>';
  var seen={{}};
  for(var i=0;i<SITES.length;i++){{
    var se=SITES[i][10]||'industrial';
    if(!seen[se]){{seen[se]=0}}
    seen[se]++;
  }}
  var keys=Object.keys(seen).sort();
  for(var k=0;k<keys.length;k++){{
    var s=keys[k];
    var c=COLORS[s]||DEFAULT_COLOR;
    html+='<div><span class="dot" style="background:'+c+'"></span>'+
          s.charAt(0).toUpperCase()+s.slice(1)+' ('+seen[s].toLocaleString()+')</div>';
  }}
  d.innerHTML=html;
  return d;
}};
legendCtrl.addTo(map);

// --- Create all markers once ---
function initMarkers(){{
  for(var i=0;i<SITES.length;i++){{
    var s=SITES[i];
    var color=COLORS[s[10]]||DEFAULT_COLOR;
    var r=Math.min(4+s[16]*0.5,12);
    var m=L.circleMarker([s[5],s[6]],{{
      radius:r,fillColor:color,color:color,weight:1,opacity:0.8,fillOpacity:0.6
    }});
    m._siteIdx=i;
    m.on('click',function(e){{
      var idx=e.target._siteIdx;
      showPopup(idx,e.target);
    }});
    markers.push(m);
    markerIndex[s[0]]=i;
  }}
}}

function showPopup(idx,marker){{
  var s=SITES[idx];
  var tl=s[18]===1?'Confirmed':s[18]===2?'Probable':'Unverified';
  var h='<b>'+esc(s[1])+'</b>';
  h+=' <span style="font-size:10px;padding:1px 5px;border-radius:3px;color:#fff;background:'+(s[18]===1?'#2a7b3f':s[18]===2?'#b8860b':'#999')+'">Tier '+s[18]+' — '+tl+'</span>';
  if(s[2]) h+='<br>'+esc(s[2])+', '+s[3];
  else if(s[3]) h+='<br>'+s[3];
  if(s[4]) h+='<br>County: '+esc(s[4]);
  if(s[10]) h+='<br>Sector: '+s[10];
  if(s[7]) h+='<br>Parent: '+esc(s[7]);
  var fl=[];
  if(s[11]) fl.push('Rail');
  if(s[12]) fl.push('Barge');
  if(s[13]) fl.push('Water');
  if(s[14]) fl.push('Port-Adj');
  if(fl.length) h+='<br>Logistics: '+fl.join(' | ');
  if(s[15]) h+='<br>Capacity: '+s[15]+' kt/yr';
  h+='<br>Sources: '+s[16];
  if(s[9]) h+='<br><small>NAICS: '+esc(s[9])+'</small>';
  h+='<br><small>UID: '+s[0]+'</small>';
  marker.bindPopup(h,{{maxWidth:320}}).openPopup();
}}

function esc(t){{
  if(!t) return '';
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

// --- Filtering ---
function applyFilters(){{
  var nm=(document.getElementById('f-name').value||'').toLowerCase();
  var st=document.getElementById('f-state').value;
  var se=document.getElementById('f-sector').value;
  var tierVal=document.getElementById('f-tier').value;
  var rail=document.getElementById('f-rail').checked;
  var water=document.getElementById('f-water').checked;
  var barge=document.getElementById('f-barge').checked;
  var minSrc=parseInt(document.getElementById('f-minsrc').value)||0;

  filtered=[];
  for(var i=0;i<SITES.length;i++){{
    var s=SITES[i];
    if(nm && s[1].toLowerCase().indexOf(nm)===-1 &&
       (s[7]||'').toLowerCase().indexOf(nm)===-1) continue;
    if(st && s[3]!==st) continue;
    if(se && s[10]!==se) continue;
    // Tier filter: '0'=all, '1'=tier1, '12'=tier1+2, '2'=tier2, '3'=tier3
    if(tierVal==='1' && s[18]!==1) continue;
    if(tierVal==='2' && s[18]!==2) continue;
    if(tierVal==='3' && s[18]!==3) continue;
    if(tierVal==='12' && s[18]>2) continue;
    if(rail && !s[11]) continue;
    if(water && !s[13]) continue;
    if(barge && !s[12]) continue;
    if(minSrc && s[16]<minSrc) continue;
    filtered.push(s);
  }}

  doSort();
  page=0;
  updateMap();
  renderTable();
}}

function resetFilters(){{
  document.getElementById('f-name').value='';
  document.getElementById('f-state').value='';
  document.getElementById('f-sector').value='';
  document.getElementById('f-tier').value='1';
  document.getElementById('f-rail').checked=false;
  document.getElementById('f-water').checked=false;
  document.getElementById('f-barge').checked=false;
  document.getElementById('f-minsrc').value=0;
  document.getElementById('minsrc-val').textContent='0';
  applyFilters();
}}

// --- Sorting ---
function doSort(){{
  var col=sortCol, asc=sortAsc;
  filtered.sort(function(a,b){{
    var va=a[col], vb=b[col];
    if(va==null) va='';
    if(vb==null) vb='';
    if(typeof va==='string') va=va.toLowerCase();
    if(typeof vb==='string') vb=vb.toLowerCase();
    if(va<vb) return asc?-1:1;
    if(va>vb) return asc?1:-1;
    return 0;
  }});
}}

function sortBy(col){{
  if(sortCol===col) sortAsc=!sortAsc;
  else {{ sortCol=col; sortAsc=true; }}
  doSort();
  page=0;
  renderTable();
  // Update arrows
  var ths=document.querySelectorAll('#sites-table th');
  for(var i=0;i<ths.length;i++){{
    var ar=ths[i].querySelector('.arrow');
    if(ar){{
      var dc=parseInt(ths[i].getAttribute('data-col'));
      if(dc===sortCol) ar.textContent=sortAsc?'\\u25B2':'\\u25BC';
      else ar.textContent='';
    }}
  }}
}}

// --- Map sync ---
function updateMap(){{
  var visibleSet={{}};
  for(var i=0;i<filtered.length;i++){{
    visibleSet[filtered[i][0]]=true;
  }}
  for(var j=0;j<markers.length;j++){{
    var uid=SITES[j][0];
    if(visibleSet[uid]){{
      if(!map.hasLayer(markers[j])) markers[j].addTo(map);
    }} else {{
      if(map.hasLayer(markers[j])) map.removeLayer(markers[j]);
    }}
  }}
}}

function flyToSite(uid){{
  selectedUid=uid;
  var idx=markerIndex[uid];
  if(idx===undefined) return;
  var s=SITES[idx];
  var m=markers[idx];
  map.flyTo([s[5],s[6]],12,{{duration:0.8}});
  showPopup(idx,m);
  // highlight table row
  var rows=document.querySelectorAll('#sites-table tbody tr');
  for(var i=0;i<rows.length;i++){{
    rows[i].classList.toggle('selected',rows[i].getAttribute('data-uid')===uid);
  }}
}}

// --- Table rendering ---
function renderTable(){{
  document.getElementById('result-count').textContent=
    'Showing '+filtered.length.toLocaleString()+' of '+SITES.length.toLocaleString()+' sites';

  var start=page*perPage;
  var end=Math.min(start+perPage,filtered.length);
  var html='';
  for(var i=start;i<end;i++){{
    var s=filtered[i];
    var fl=[];
    if(s[11]) fl.push('R');
    if(s[12]) fl.push('B');
    if(s[13]) fl.push('W');
    var tc=s[18]===1?'tier1':s[18]===2?'tier2':'tier3';
    html+='<tr data-uid="'+s[0]+'" onclick="flyToSite(\\''+s[0]+'\\')">'+
      '<td><span class="tbadge '+tc+'">'+s[18]+'</span></td>'+
      '<td title="'+esc(s[1])+'">'+esc(s[1])+'</td>'+
      '<td>'+esc(s[2])+'</td>'+
      '<td>'+s[3]+'</td>'+
      '<td>'+esc(s[10])+'</td>'+
      '<td>'+s[16]+'</td>'+
      '<td>'+fl.join(',')+'</td></tr>';
  }}
  document.getElementById('tbody').innerHTML=html;
  renderPagination();
}}

function renderPagination(){{
  var totalPages=Math.ceil(filtered.length/perPage);
  if(totalPages<=1){{document.getElementById('pagination').innerHTML='';return}}

  var html='<button '+(page===0?'disabled':'')+' onclick="goPage(0)">&laquo;</button>';
  html+='<button '+(page===0?'disabled':'')+' onclick="goPage('+(page-1)+')">&lsaquo;</button>';

  var lo=Math.max(0,page-3), hi=Math.min(totalPages-1,page+3);
  if(lo>0) html+='<button onclick="goPage(0)">1</button>';
  if(lo>1) html+='<span style="padding:0 4px">...</span>';
  for(var p=lo;p<=hi;p++){{
    html+='<button class="'+(p===page?'active':'')+'" onclick="goPage('+p+')">'+(p+1)+'</button>';
  }}
  if(hi<totalPages-2) html+='<span style="padding:0 4px">...</span>';
  if(hi<totalPages-1) html+='<button onclick="goPage('+(totalPages-1)+')">'+totalPages+'</button>';

  html+='<button '+(page>=totalPages-1?'disabled':'')+' onclick="goPage('+(page+1)+')">&rsaquo;</button>';
  html+='<button '+(page>=totalPages-1?'disabled':'')+' onclick="goPage('+(totalPages-1)+')">&raquo;</button>';

  document.getElementById('pagination').innerHTML=html;
}}

function goPage(p){{
  var totalPages=Math.ceil(filtered.length/perPage);
  if(p<0) p=0;
  if(p>=totalPages) p=totalPages-1;
  page=p;
  renderTable();
  document.getElementById('table-wrap').scrollTop=0;
}}

// --- CSV Export ---
function exportCSV(){{
  var hdr='facility_uid,canonical_name,city,state,county,latitude,longitude,parent_company,facility_types,naics_codes,commodity_sectors,rail_served,barge_access,water_access,port_adjacent,capacity_kt_year,source_count,confidence_score,confidence_tier';
  var lines=[hdr];
  for(var i=0;i<filtered.length;i++){{
    var r=filtered[i];
    var row=[];
    for(var j=0;j<r.length;j++){{
      var v=r[j];
      if(v===null||v===undefined) v='';
      v=String(v);
      if(v.indexOf(',')!==-1||v.indexOf('"')!==-1||v.indexOf('\\n')!==-1)
        v='"'+v.replace(/"/g,'""')+'"';
      row.push(v);
    }}
    lines.push(row.join(','));
  }}
  var blob=new Blob([lines.join('\\n')],{{type:'text/csv;charset=utf-8;'}});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;
  a.download='site_registry_export_'+filtered.length+'_sites.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

// --- Debounced name search ---
document.getElementById('f-name').addEventListener('input',function(){{
  clearTimeout(debounceTimer);
  debounceTimer=setTimeout(applyFilters,300);
}});

// --- Slider display ---
document.getElementById('f-minsrc').addEventListener('input',function(){{
  document.getElementById('minsrc-val').textContent=this.value;
}});

// --- Init ---
initMarkers();
applyFilters();
</script>
</body>
</html>"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
    logger.info(f"Dashboard saved to {path} ({len(sites):,} sites)")
    return path
