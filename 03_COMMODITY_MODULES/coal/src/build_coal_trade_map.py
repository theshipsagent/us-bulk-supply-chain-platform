#!/usr/bin/env python3
"""
build_coal_trade_map.py

Two separate publication-quality editorial infographic maps — USEC Coal Exports 2025.
D3.js v7 + TopoJSON. Economist / Financial Times editorial aesthetic.

Map 1: Global trade flows — Natural Earth projection, tapered great-circle arcs,
        destination circles, MET vs thermal color split.

Map 2: Mine origins & rail corridors — Full eastern US Albers projection,
        mine density glow dots, rail corridors, port markers.

Run from: 03_COMMODITY_MODULES/coal/
  python3 src/build_coal_trade_map.py
"""

import csv, json
from pathlib import Path
from datetime import datetime
import duckdb

SCRIPT_DIR = Path(__file__).parent.resolve()
COAL_DIR   = SCRIPT_DIR.parent
DB_PATH    = COAL_DIR / "data" / "coal_analytics.duckdb"
MINES_CSV  = COAL_DIR / "data" / "processed" / "top_us_coal_mines.csv"
PROJECT    = COAL_DIR.parent.parent
OUT_DIR    = PROJECT / "04_REPORTS" / "coal_export_report" / "output"
TODAY      = datetime.now().strftime("%Y%m%d")
BUILD_DATE = datetime.now().strftime("%B %Y")

# ─── Destination centroids (lon, lat) ─────────────────────────────────────────
COUNTRY_COORDS = {
    'INDIA':       (78.9, 20.6),
    'BRAZIL':      (-51.9, -14.2),
    'NETHERLANDS': (5.3, 52.1),
    'CHINA':       (104.2, 35.9),
    'JAPAN':       (138.3, 36.2),
    'SPAIN':       (-3.7, 40.5),
    'MOROCCO':     (-7.1, 31.8),
    'TURKEY':      (35.2, 38.9),
    'EGYPT':       (30.8, 26.8),
    'SOUTH KOREA': (127.8, 35.9),
    'ITALY':       (12.5, 41.9),
    'GERMANY':     (10.5, 51.2),
    'FRANCE':      (2.2, 46.2),
    'UKRAINE':     (31.2, 48.4),
    'INDONESIA':   (113.9, -0.8),
    'POLAND':      (19.1, 52.0),
}

COUNTRY_ISO = {
    'INDIA': 356, 'BRAZIL': 76, 'NETHERLANDS': 528, 'CHINA': 156,
    'JAPAN': 392, 'SPAIN': 724, 'MOROCCO': 504, 'TURKEY': 792,
    'EGYPT': 818, 'SOUTH KOREA': 410, 'ITALY': 380, 'GERMANY': 276,
    'FRANCE': 250, 'UKRAINE': 804, 'INDONESIA': 360, 'POLAND': 616,
}


# ─── DATA LOAD ────────────────────────────────────────────────────────────────
def load_flows():
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute("""
        SELECT destination_country,
               SUM(metric_tons)                                                    AS total_mt,
               SUM(CASE WHEN coal_type='MET'     THEN metric_tons ELSE 0 END)     AS met_mt,
               SUM(CASE WHEN coal_type='THERMAL' THEN metric_tons ELSE 0 END)     AS th_mt,
               COUNT(*)                                                            AS calls
        FROM coal_vessel_calls
        WHERE port IN ('H ROADS','BALTIMORE')
          AND datepart('year', report_date) = 2025
          AND destination_country IS NOT NULL
          AND metric_tons IS NOT NULL
        GROUP BY destination_country
        ORDER BY total_mt DESC
        LIMIT 16
    """).fetchall()
    con.close()

    flows = []
    for country, total, met, th, calls in rows:
        if country not in COUNTRY_COORDS:
            continue
        lon, lat = COUNTRY_COORDS[country]
        flows.append({
            'country':     country.title(),
            'country_key': country,
            'iso':         COUNTRY_ISO.get(country, -1),
            'lon': lon, 'lat': lat,
            'total_mt':   round(total / 1e6, 2),
            'met_mt':     round(met   / 1e6, 2),
            'th_mt':      round(th    / 1e6, 2),
            'met_pct':    round(met / total * 100) if total else 0,
            'calls':      calls,
        })
    return flows


def load_mines():
    mines = []
    with open(MINES_CSV) as f:
        for row in csv.DictReader(f):
            if row.get('export_relevant', '').lower() != 'true':
                continue
            if row['basin'] not in ('CAPP', 'NAPP'):
                continue
            try:
                ct = row['coal_type']
                if 'HCC' in ct or 'Semi' in ct:
                    grade = 'hcc'
                elif 'Thermal' in ct:
                    grade = 'thermal'
                else:
                    grade = 'crossover'
                mines.append({
                    'name':  row['mine_name'],
                    'lat':   float(row['lat']),
                    'lon':   float(row['lon']),
                    'prod':  float(row['prod_annualized_mst'] or 0),
                    'basin': row['basin'],
                    'grade': grade,
                })
            except (ValueError, KeyError):
                pass
    return mines


# ─── SHARED HEADER STYLE ─────────────────────────────────────────────────────
SHARED_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0d1b2a;
    font-family: 'Georgia', serif;
    display: flex; justify-content: center; align-items: flex-start;
    min-height: 100vh; padding: 32px 16px;
  }
  .card {
    background: #0d1b2a;
    width: 1140px;
    box-shadow: 0 4px 40px rgba(0,0,0,0.6);
  }
  .header-strip { background: #c8102e; height: 6px; width: 100%; }
  .header-block {
    padding: 18px 24px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }
  .kicker {
    font-family: 'Arial', sans-serif;
    font-size: 10px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #c8102e; margin-bottom: 6px;
  }
  .main-title { font-size: 22px; font-weight: 700; color: #f5f0e8; line-height: 1.2; margin-bottom: 4px; }
  .subtitle { font-size: 13px; color: rgba(255,255,255,0.55); font-family: 'Arial', sans-serif; }
  .map-area { position: relative; background: #0a1520; }
  .legend-block {
    padding: 14px 24px 18px;
    display: flex; gap: 32px; align-items: flex-start;
    border-top: 1px solid rgba(255,255,255,0.08); flex-wrap: wrap;
  }
  .legend-title {
    font-family: 'Arial', sans-serif; font-size: 9px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: rgba(255,255,255,0.35); margin-bottom: 6px;
  }
  .legend-row {
    display: flex; align-items: center; gap: 7px;
    font-family: 'Arial', sans-serif; font-size: 11px;
    color: rgba(255,255,255,0.55); margin-bottom: 4px;
  }
  .legend-swatch { width: 28px; height: 10px; border-radius: 2px; flex-shrink: 0; }
  .legend-dot    { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .footnote {
    padding: 10px 24px 16px;
    font-family: 'Arial', sans-serif; font-size: 10px;
    color: rgba(255,255,255,0.28); line-height: 1.5;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  .footnote strong { color: rgba(255,255,255,0.4); }
"""


# ─── MAP 1: GLOBAL TRADE FLOWS ────────────────────────────────────────────────
def build_global_html(flows):
    flows_js    = json.dumps(flows, indent=2)
    dest_iso_js = json.dumps([f['iso'] for f in flows if f['iso'] > 0])
    dest_vol_js = json.dumps({str(f['iso']): f['total_mt'] for f in flows if f['iso'] > 0})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US East Coast Coal Export Trade Flows 2025</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson@3.0.2/dist/topojson.min.js"></script>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<div class="card">

  <div class="header-strip"></div>

  <div class="header-block">
    <div class="kicker">Trade Intelligence &middot; {BUILD_DATE}</div>
    <div class="main-title">US East Coast Coal Export Trade Flows, 2025</div>
    <div class="subtitle">
      Hampton Roads and Baltimore — approximately 63 million tons shipped to steel mills
      and power utilities across four continents
    </div>
  </div>

  <div class="map-area">
    <svg id="main-map" viewBox="0 0 1140 620" preserveAspectRatio="xMidYMid meet"
         style="display:block;width:100%;"></svg>
  </div>

  <div class="legend-block">
    <div>
      <div class="legend-title">Trade Flow Arcs</div>
      <div class="legend-row">
        <div class="legend-swatch" style="background:rgba(82,175,240,0.75);"></div>
        Metallurgical coal — blast furnace coking grades
      </div>
      <div class="legend-row">
        <div class="legend-swatch" style="background:rgba(224,140,40,0.75);"></div>
        Thermal &amp; crossover coal — power generation grades
      </div>
      <div class="legend-row" style="margin-top:3px;color:rgba(255,255,255,0.3);font-size:10px;">
        Arc width proportional to tonnage. Narrow at load port, widening at destination.
      </div>
    </div>
    <div>
      <div class="legend-title">Destination Circles</div>
      <div class="legend-row">
        <div class="legend-dot" style="background:rgba(82,175,240,0.55);border:1px solid #52aff0;"></div>
        Predominantly metallurgical (&ge;60% met)
      </div>
      <div class="legend-row">
        <div class="legend-dot" style="background:rgba(224,140,40,0.55);border:1px solid #e08c28;"></div>
        Predominantly thermal (&lt;60% met)
      </div>
      <div class="legend-row" style="margin-top:3px;color:rgba(255,255,255,0.3);font-size:10px;">
        Circle area proportional to total tonnage received.
      </div>
    </div>
    <div>
      <div class="legend-title">Origin</div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#f5f0e8;border:1.5px solid #c8102e;"></div>
        US East Coast export complex (Hampton Roads &amp; Baltimore combined)
      </div>
    </div>
  </div>


</div>

<script>
const FLOWS    = {flows_js};
const DEST_ISO = new Set({dest_iso_js});
const DEST_VOLS = {dest_vol_js};

const ORIGIN = [-76.47, 37.9];   // USEC origin centroid

const W = 1140, H = 620;
const svg = d3.select("#main-map");

// Translate x left (0.40) to reduce empty western Pacific dead space;
// scale 220 zooms in slightly; rotate 20°W to centre Atlantic shipping lanes.
const proj = d3.geoNaturalEarth1()
  .scale(220)
  .rotate([-20, 0, 0])
  .translate([W * 0.40, H * 0.50]);

const path = d3.geoPath().projection(proj);

const maxMT   = d3.max(FLOWS, d => d.total_mt);
const arcWidth = d3.scaleSqrt().domain([0, maxMT]).range([0, 18]);
const dotR     = d3.scaleSqrt().domain([0, maxMT]).range([4, 22]);

// Pre-compute origin screen position (available before JSON load)
const originPx = proj(ORIGIN);

// ── Geographic tapered arc (great-circle) — used for Atlantic/Indian Ocean dests ─
function taperedArc(srcLL, dstLL, maxW, numPts) {{
  numPts = numPts || 90;
  const interp = d3.geoInterpolate(srcLL, dstLL);
  const pts = [];
  for (let i = 0; i <= numPts; i++) {{
    const ll = interp(i / numPts);
    const px = proj(ll);
    if (!px) return null;
    pts.push(px);
  }}
  const left = [], right = [];
  for (let i = 0; i <= numPts; i++) {{
    const t  = i / numPts;
    const hw = t * maxW * 0.5;
    const prev = pts[Math.max(0, i - 1)];
    const next = pts[Math.min(numPts, i + 1)];
    const dx = next[0] - prev[0], dy = next[1] - prev[1];
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const p = pts[i];
    left.push( [p[0] + nx*hw, p[1] + ny*hw]);
    right.push([p[0] - nx*hw, p[1] - ny*hw]);
  }}
  const all = left.concat(right.reverse());
  return 'M' + all.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L') + 'Z';
}}

// ── Screen-space quadratic Bezier arc — used for Pacific dests ────────────────
// Arc dips SOUTH through the bottom ocean space, creating a clean
// visual separation from the Atlantic arcs that fan upward.
function taperedBezier(p0, p2, ctrlY, maxW) {{
  const N = 90;
  const ctrlX = (p0[0] + p2[0]) / 2;
  const pts = [];
  for (let i = 0; i <= N; i++) {{
    const t = i / N, mt = 1 - t;
    pts.push([
      mt*mt*p0[0] + 2*mt*t*ctrlX + t*t*p2[0],
      mt*mt*p0[1] + 2*mt*t*ctrlY + t*t*p2[1],
    ]);
  }}
  const left = [], right = [];
  for (let i = 0; i <= N; i++) {{
    const t  = i / N;
    const hw = t * maxW * 0.5;
    const prev = pts[Math.max(0, i - 1)];
    const next = pts[Math.min(N, i + 1)];
    const dx = next[0] - prev[0], dy = next[1] - prev[1];
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const p = pts[i];
    left.push( [p[0] + nx*hw, p[1] + ny*hw]);
    right.push([p[0] - nx*hw, p[1] - ny*hw]);
  }}
  return 'M' + left.concat(right.reverse()).map(p => p[0].toFixed(1)+','+p[1].toFixed(1)).join('L') + 'Z';
}}

d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(world => {{

  const countries = topojson.feature(world, world.objects.countries);
  const borders   = topojson.mesh(world, world.objects.countries, (a,b) => a !== b);

  // Ocean
  svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#0a1520");
  svg.append("path").datum({{ type: "Sphere" }})
     .attr("d", path).attr("fill", "#0e2035")
     .attr("stroke", "rgba(255,255,255,0.06)").attr("stroke-width", 0.5);

  // Countries
  const maxDestVol    = d3.max(Object.values(DEST_VOLS).map(Number));
  const destIntensity = d3.scaleLinear().domain([0, maxDestVol]).range([0, 1]).clamp(true);

  svg.append("g").selectAll("path")
    .data(countries.features)
    .join("path").attr("d", path)
    .attr("fill", d => {{
      const iso = +d.id;
      if (+d.id === 840) return "#1e3550";           // US — origin highlight
      if (DEST_ISO.has(iso)) {{
        const vol = DEST_VOLS[String(iso)] || 0;
        const t   = destIntensity(vol);
        return `rgba(40,${{Math.round(80 + t*80)}},${{Math.round(120 + t*60)}},${{(0.35 + t*0.45).toFixed(2)}})`;
      }}
      return "#152234";
    }})
    .attr("stroke", "rgba(255,255,255,0.08)").attr("stroke-width", 0.4);

  svg.append("path").datum(borders).attr("d", path)
     .attr("fill", "none").attr("stroke", "rgba(255,255,255,0.07)").attr("stroke-width", 0.3);

  svg.append("path").datum(d3.geoGraticule()()).attr("d", path)
     .attr("fill", "none").attr("stroke", "rgba(255,255,255,0.04)").attr("stroke-width", 0.3);

  // Trade arcs — thermal behind, MET on top
  // Pacific (lon > 100°E): screen-space Bezier dipping south through bottom ocean space
  // Atlantic / Indian Ocean: geographic great-circle arcs fanning upper-right
  const PACIFIC_CTRL_Y = H * 0.88;  // dips into lower ocean band; more room from Atlantic arcs
  const arcLayer = svg.append("g");
  function drawArc(flow, useMet) {{
    const mt = useMet ? flow.met_mt : flow.th_mt;
    if (mt < 0.1) return;
    const w   = arcWidth(mt);
    const col  = useMet ? "rgba(82,175,240,0.70)"  : "rgba(224,140,40,0.72)";
    const glow = useMet ? "rgba(82,175,240,0.10)"  : "rgba(224,140,40,0.10)";
    let d, glowD;
    if (flow.lon > 100) {{
      const destPx = proj([flow.lon, flow.lat]);
      if (!destPx || !originPx) return;
      glowD = taperedBezier(originPx, destPx, PACIFIC_CTRL_Y, w * 2.8);
      d     = taperedBezier(originPx, destPx, PACIFIC_CTRL_Y, w);
    }} else {{
      glowD = taperedArc(ORIGIN, [flow.lon, flow.lat], w * 2.8);
      d     = taperedArc(ORIGIN, [flow.lon, flow.lat], w);
    }}
    if (glowD) arcLayer.append("path").attr("d", glowD).attr("fill", glow).attr("stroke","none");
    if (d) arcLayer.append("path").attr("d", d).attr("fill", col).attr("stroke","none")
             .append("title").text(`${{flow.country}} — ${{mt.toFixed(1)}}M t`);
  }}
  FLOWS.forEach(f => drawArc(f, false));
  FLOWS.forEach(f => drawArc(f, true));

  // Destination circles
  const destLayer = svg.append("g");
  FLOWS.forEach(f => {{
    const px = proj([f.lon, f.lat]);
    if (!px) return;
    const r   = dotR(f.total_mt);
    const col = f.met_pct >= 60 ? "#52aff0" : "#e08c28";
    destLayer.append("circle").attr("cx", px[0]).attr("cy", px[1]).attr("r", r * 1.6)
      .attr("fill", "none")
      .attr("stroke", f.met_pct >= 60 ? "rgba(82,175,240,0.22)" : "rgba(224,140,40,0.22)")
      .attr("stroke-width", 0.8);
    destLayer.append("circle").attr("cx", px[0]).attr("cy", px[1]).attr("r", r)
      .attr("fill", f.met_pct >= 60 ? "rgba(82,175,240,0.55)" : "rgba(224,140,40,0.55)")
      .attr("stroke", f.met_pct >= 60 ? "#52aff0" : "#e08c28").attr("stroke-width", 0.8);
  }});

  // Labels
  const labelOffsets = {{
    'India': [14,-4], 'Brazil': [12,4], 'Netherlands': [10,-8],
    'China': [12,-4], 'Japan': [12,4], 'Spain': [10,-8],
    'Morocco': [-62,8], 'Turkey': [10,6], 'Egypt': [12,4],
    'South Korea': [12,-6], 'Italy': [10,-8], 'Germany': [-76,-8],
    'France': [-64,-8], 'Ukraine': [10,-8], 'Indonesia': [10,8], 'Poland': [10,-8],
  }};
  const labelLayer = svg.append("g");
  FLOWS.forEach(f => {{
    const px  = proj([f.lon, f.lat]);
    if (!px) return;
    const r   = dotR(f.total_mt);
    const off = labelOffsets[f.country] || [r+5, -4];
    const sz  = f.total_mt >= 5 ? "11px" : f.total_mt >= 2 ? "10px" : "9px";
    const fw  = f.total_mt >= 3 ? "700" : "400";
    const anc = off[0] < 0 ? "end" : "start";
    labelLayer.append("text").attr("x", px[0]+off[0]).attr("y", px[1]+off[1])
      .attr("font-family","Arial,sans-serif").attr("font-size",sz).attr("font-weight",fw)
      .attr("fill","rgba(255,255,255,0.85)").attr("text-anchor",anc).text(f.country);
    const mtStr = f.total_mt >= 1 ? `~${{Math.round(f.total_mt)}}M t` : `~${{Math.round(f.total_mt*1000)}}K t`;
    const tag   = f.met_pct >= 60 ? "met" : f.met_pct <= 30 ? "thermal" : "mixed";
    labelLayer.append("text").attr("x", px[0]+off[0]).attr("y", px[1]+off[1]+11)
      .attr("font-family","Arial,sans-serif").attr("font-size","8.5px")
      .attr("fill", f.met_pct >= 60 ? "rgba(82,175,240,0.7)" : "rgba(224,140,40,0.7)")
      .attr("text-anchor",anc).text(`${{mtStr}} · ${{tag}}`);
  }});

  // Origin marker — uses originPx from outer scope (set before d3.json call)
  if (originPx) {{
    const portLayer = svg.append("g");
    portLayer.append("circle").attr("cx",originPx[0]).attr("cy",originPx[1])
      .attr("r",18).attr("fill","rgba(255,255,255,0.04)").attr("stroke","none");
    portLayer.append("circle").attr("cx",originPx[0]).attr("cy",originPx[1])
      .attr("r",7).attr("fill","rgba(245,240,232,0.9)")
      .attr("stroke","#c8102e").attr("stroke-width",1.5);
    portLayer.append("text").attr("x",originPx[0]+11).attr("y",originPx[1]-6)
      .attr("font-family","Arial,sans-serif").attr("font-size","10px").attr("font-weight","700")
      .attr("fill","rgba(255,255,255,0.9)").text("Hampton Roads");
    portLayer.append("text").attr("x",originPx[0]+11).attr("y",originPx[1]+5)
      .attr("font-family","Arial,sans-serif").attr("font-size","10px").attr("font-weight","700")
      .attr("fill","rgba(255,255,255,0.9)").text("& Baltimore");
  }}

}}).catch(err => {{
  svg.append("text").attr("x",60).attr("y",60).attr("fill","#e08c28")
     .text("Map data failed to load (check CDN). Error: " + err.message);
}});
</script>
</body>
</html>"""


# ─── MAP 2: MINE ORIGINS & RAIL CORRIDORS ─────────────────────────────────────
def build_origins_html(mines):
    mines_js = json.dumps(mines, indent=2)

    rails = [
        {
            "name": "NS Pocahontas Division",
            "label": "NS Pocahontas Div.",
            "color": "#52aff0",
            "desc": "Williamson WV → Roanoke → Hampton Roads. Primary CAPP HCC corridor.",
            "coords": [[-82.27,37.65],[-81.56,37.27],[-80.41,37.22],[-79.82,37.00],[-77.40,36.99],[-76.36,36.92]],
        },
        {
            "name": "CSX B&O / Sand Patch Grade",
            "label": "CSX B&O / Sand Patch",
            "color": "#e08c28",
            "desc": "Cumberland MD → Hagerstown → Baltimore Curtis Bay. NAPP thermal bituminous.",
            "coords": [[-80.25,39.82],[-79.27,39.49],[-78.80,39.62],[-77.72,39.72],[-76.59,39.28]],
        },
        {
            "name": "CSX Cardinal Corridor",
            "label": "CSX Cardinal Corridor",
            "color": "#a0b8c8",
            "desc": "Huntington WV → Newport News. Central Appalachian crossover grades.",
            "coords": [[-82.44,38.42],[-81.11,38.09],[-80.45,37.78],[-79.87,37.50],[-78.20,37.28],[-76.46,37.08]],
        },
    ]
    rails_js = json.dumps(rails)

    ports = [
        {"name": "Hampton Roads", "lon": -76.36, "lat": 36.92},
        {"name": "Baltimore",     "lon": -76.59, "lat": 39.28},
    ]
    ports_js = json.dumps(ports)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US East Coast Coal — Mine Origins &amp; Rail Corridors 2025</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson@3.0.2/dist/topojson.min.js"></script>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<div class="card">

  <div class="header-strip"></div>

  <div class="header-block">
    <div class="kicker">Supply Chain Intelligence &middot; {BUILD_DATE}</div>
    <div class="main-title">Appalachian Mine Origins &amp; Rail Corridors</div>
    <div class="subtitle">
      Export-relevant coal mines by basin and grade — with the three principal rail corridors
      serving Hampton Roads and Baltimore
    </div>
  </div>

  <div class="map-area">
    <svg id="origins-map" viewBox="0 0 1140 640" preserveAspectRatio="xMidYMid meet"
         style="display:block;width:100%;"></svg>
  </div>

  <div class="legend-block">
    <div>
      <div class="legend-title">Mine Grade</div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#52aff0;"></div>
        Hard coking coal (HCC) — Central Appalachian low-volatile
      </div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#e08c28;"></div>
        Thermal bituminous — Northern Appalachian (NAPP) high-BTU
      </div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#a0b8c8;"></div>
        Crossover / semi-soft coking grades
      </div>
      <div class="legend-row" style="margin-top:3px;color:rgba(255,255,255,0.3);font-size:10px;">
        Circle area proportional to annual production. Glow intensity reflects concentration.
      </div>
    </div>
    <div>
      <div class="legend-title">Rail Corridors</div>
      <div class="legend-row">
        <div class="legend-swatch" style="background:#52aff0;height:3px;border-radius:0;"></div>
        NS Pocahontas Division — CAPP HCC to Hampton Roads
      </div>
      <div class="legend-row">
        <div class="legend-swatch" style="background:#e08c28;height:3px;border-radius:0;"></div>
        CSX B&amp;O / Sand Patch Grade — NAPP thermal to Baltimore
      </div>
      <div class="legend-row">
        <div class="legend-swatch" style="background:#a0b8c8;height:3px;border-radius:0;"></div>
        CSX Cardinal Corridor — CAPP crossover to Newport News
      </div>
    </div>
    <div>
      <div class="legend-title">Export Terminals</div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#f5f0e8;border:1.5px solid #c8102e;"></div>
        Hampton Roads (NS Lamberts Point, DTA, Pier IX at Newport News)
      </div>
      <div class="legend-row">
        <div class="legend-dot" style="background:#f5f0e8;border:1.5px solid #c8102e;"></div>
        Baltimore (CNX Marine Terminal, CSX Curtis Bay)
      </div>
    </div>
  </div>


</div>

<script>
const MINES = {mines_js};
const RAILS = {rails_js};
const PORTS = {ports_js};

const W = 1140, H = 640;
const svg = d3.select("#origins-map");

// Mercator — CAPP + NAPP focus (Warrior Basin removed).
// Content bounds: lon -82.5°W (CAPP west) to -76.4°W (Hampton Roads) = 6.1°
//                 lat  36.5°N (HR / CAPP south) to 41.0°N (NAPP / Pittsburgh) = 4.5°
// Scale 6500 fills canvas comfortably; shift translate right to centre on corridor midpoint.
const proj = d3.geoMercator()
  .center([-79.5, 38.5])
  .scale(6500)
  .translate([W * 0.52, H * 0.52]);

const path = d3.geoPath().projection(proj);

const maxProd = d3.max(MINES, d => d.prod);
const mineR   = d3.scaleSqrt().domain([0, maxProd]).range([2.5, 11]);

const colMap = {{ hcc: "#52aff0", thermal: "#e08c28", crossover: "#a0b8c8" }};

d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json").then(world => {{

  // Use 50m (higher resolution) for cleaner eastern US coastline
  const countries = topojson.feature(world, world.objects.countries);

  // Background ocean
  svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#0a1520");

  // Only render North American countries — Mercator at this zoom renders the
  // entire globe off-screen otherwise, causing rendering artifacts.
  // US=840, Canada=124, Mexico=484, Cuba=192, Bahamas=44
  const naIDs = new Set([840, 124, 484, 192, 44]);

  svg.append("g").selectAll("path")
    .data(countries.features.filter(d => naIDs.has(+d.id)))
    .join("path").attr("d", path)
    .attr("fill", d => +d.id === 840 ? "#1a2d40" : "#141f2d")
    .attr("stroke", "rgba(255,255,255,0.12)").attr("stroke-width", 0.5);

  // ── Basin shading (subtle) ─────────────────────────────────────────────────
  // CAPP rectangle (rough outline)
  const basins = [
    {{ label:"CAPP", coords:[[-82.5,38.8],[-78.0,38.8],[-78.0,36.5],[-82.5,36.5]], color:"rgba(82,175,240,0.06)" }},
    {{ label:"NAPP", coords:[[-81.5,40.8],[-77.5,40.8],[-77.5,38.9],[-81.5,38.9]], color:"rgba(224,140,40,0.06)" }},
  ];
  basins.forEach(b => {{
    const closed = [...b.coords, b.coords[0]];
    const feat = {{ type:"Feature", geometry:{{ type:"LineString", coordinates: closed.map(c => [c[0],c[1]]) }} }};
    // Draw as filled path
    const pts = b.coords.map(c => proj(c)).filter(Boolean);
    if (pts.length) {{
      const d = 'M' + pts.map(p => p.join(',')).join('L') + 'Z';
      svg.append("path").attr("d",d).attr("fill",b.color).attr("stroke","none");
    }}
  }});

  // Basin labels
  const basinLabels = [
    {{ label:"CENTRAL APPALACHIAN\\n(CAPP)", lon:-80.5, lat:37.3, color:"rgba(82,175,240,0.35)" }},
    {{ label:"NORTHERN APPALACHIAN\\n(NAPP)", lon:-79.3, lat:40.1, color:"rgba(224,140,40,0.35)" }},
  ];
  basinLabels.forEach(b => {{
    const px = proj([b.lon, b.lat]);
    if (!px) return;
    const lines = b.label.split('\\n');
    lines.forEach((line, i) => {{
      svg.append("text").attr("x", px[0]).attr("y", px[1] + i*11)
        .attr("font-family","Arial,sans-serif").attr("font-size","8px")
        .attr("font-weight","700").attr("letter-spacing","0.8px")
        .attr("fill", b.color).attr("text-anchor","middle").text(line);
    }});
  }});

  // ── Rail corridors ─────────────────────────────────────────────────────────
  RAILS.forEach(rail => {{
    const feat = {{ type:"Feature", geometry:{{ type:"LineString", coordinates: rail.coords }} }};
    // Glow pass
    svg.append("path").datum(feat).attr("d", path)
       .attr("fill","none").attr("stroke", rail.color)
       .attr("stroke-width", 5).attr("opacity", 0.10)
       .attr("stroke-linecap","round");
    // Main line
    svg.append("path").datum(feat).attr("d", path)
       .attr("fill","none").attr("stroke", rail.color)
       .attr("stroke-width", 1.8).attr("stroke-dasharray","6,4")
       .attr("opacity", 0.75).attr("stroke-linecap","round");
  }});

  // ── Mine dots ─────────────────────────────────────────────────────────────
  const mineLayer = svg.append("g");
  MINES.forEach(m => {{
    const px = proj([m.lon, m.lat]);
    if (!px) return;
    const r   = mineR(m.prod);
    const col = colMap[m.grade] || "#888";
    // Glow rings
    [3.0, 1.8].forEach((mult, i) => {{
      mineLayer.append("circle").attr("cx", px[0]).attr("cy", px[1])
        .attr("r", r * mult).attr("fill", col)
        .attr("opacity", i === 0 ? 0.07 : 0.13).attr("stroke","none");
    }});
    // Core dot
    mineLayer.append("circle").attr("cx", px[0]).attr("cy", px[1]).attr("r", r)
      .attr("fill", col).attr("opacity", 0.78)
      .attr("stroke","rgba(0,0,0,0.35)").attr("stroke-width", 0.4)
      .append("title").text(`${{m.name}} (${{m.basin}}) — ${{m.prod.toFixed(1)}} M ST/yr`);
  }});

  // ── Port markers ──────────────────────────────────────────────────────────
  PORTS.forEach(p => {{
    const px = proj([p.lon, p.lat]);
    if (!px) return;
    // Glow
    svg.append("circle").attr("cx",px[0]).attr("cy",px[1])
       .attr("r",14).attr("fill","rgba(200,16,46,0.12)").attr("stroke","none");
    svg.append("circle").attr("cx",px[0]).attr("cy",px[1])
       .attr("r",6).attr("fill","rgba(245,240,232,0.9)")
       .attr("stroke","#c8102e").attr("stroke-width",1.5);
    svg.append("text").attr("x",px[0]+10).attr("y",px[1]-6)
       .attr("font-family","Arial,sans-serif").attr("font-size","10px")
       .attr("font-weight","700").attr("fill","rgba(255,255,255,0.9)")
       .text(p.name);
    // Terminal sub-label
    const sub = p.name === "Hampton Roads"
      ? "Lamberts Point · DTA · Pier IX"
      : "CNX Marine · CSX Curtis Bay";
    svg.append("text").attr("x",px[0]+10).attr("y",px[1]+5)
       .attr("font-family","Arial,sans-serif").attr("font-size","7.5px")
       .attr("fill","rgba(255,255,255,0.45)").text(sub);
  }});

  // ── Rail corridor labels (end-point labels) ────────────────────────────────
  // Place a small text label near the mine-origin end of each corridor
  const railLabelPts = [
    {{ rail: RAILS[0], idx: 0, dx: -8, dy: -8, anc: "end"   }},  // NS Poca — WV end
    {{ rail: RAILS[1], idx: 0, dx: -8, dy: -8, anc: "end"   }},  // CSX B&O — WV end
    {{ rail: RAILS[2], idx: 0, dx: -8, dy:  8, anc: "end"   }},  // CSX Cardinal — WV end
  ];
  railLabelPts.forEach(lp => {{
    const coord = lp.rail.coords[lp.idx];
    const px = proj(coord);
    if (!px) return;
    svg.append("text").attr("x", px[0]+lp.dx).attr("y", px[1]+lp.dy)
       .attr("font-family","Arial,sans-serif").attr("font-size","8px")
       .attr("font-weight","700").attr("letter-spacing","0.5px")
       .attr("fill", lp.rail.color).attr("opacity", 0.75)
       .attr("text-anchor", lp.anc).text(lp.rail.label);
  }});

  // ── State boundaries (approximate — from country paths isn't enough;
  //    draw key state name labels for orientation) ─────────────────────────
  const stateLabels = [
    {{ label:"W. VIRGINIA", lon:-80.5, lat:38.5 }},
    {{ label:"VIRGINIA",    lon:-78.5, lat:37.5 }},
    {{ label:"PENNSYLVANIA",lon:-77.5, lat:40.5 }},
    {{ label:"KENTUCKY",    lon:-83.5, lat:37.8 }},
    {{ label:"MARYLAND",    lon:-77.0, lat:39.5 }},
  ];
  stateLabels.forEach(s => {{
    const px = proj([s.lon, s.lat]);
    if (!px) return;
    svg.append("text").attr("x",px[0]).attr("y",px[1])
       .attr("font-family","Arial,sans-serif").attr("font-size","9px")
       .attr("fill","rgba(255,255,255,0.18)").attr("text-anchor","middle")
       .attr("letter-spacing","1px").text(s.label);
  }});

}}).catch(err => {{
  svg.append("text").attr("x",60).attr("y",60).attr("fill","#e08c28")
     .text("Map data failed to load (check CDN). Error: " + err.message);
}});
</script>
</body>
</html>"""


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading trade flow data...")
    flows = load_flows()
    print(f"  {len(flows)} destination flows loaded")

    print("Loading mine data...")
    mines = load_mines()
    print(f"  {len(mines)} Appalachian export mines loaded")

    print("\nBuilding Map 1 — Global Trade Flows...")
    html1 = build_global_html(flows)
    out1  = OUT_DIR / f"usec_coal_trade_flows_{TODAY}.html"
    out1.write_text(html1, encoding='utf-8')
    print(f"  {out1.name}  ({len(html1)//1024} KB)")

    print("Building Map 2 — Mine Origins & Rail Corridors...")
    html2 = build_origins_html(mines)
    out2  = OUT_DIR / f"usec_coal_mine_origins_{TODAY}.html"
    out2.write_text(html2, encoding='utf-8')
    print(f"  {out2.name}  ({len(html2)//1024} KB)")

    print(f"\n  Flows: {len(flows)} destinations")
    print(f"  Mines: {len(mines)} Appalachian operations")
    print(f"  Style: D3.js Economist editorial infographic (two separate maps)")
