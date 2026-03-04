#!/usr/bin/env python3
"""
build_coal_export_report.py
USEC Coal Exports — 2025 Year in Review
Hampton Roads & Baltimore

Generates a standalone HTML report in the OceanDatum dark glassmorphism style.
Narrative-first. Tables as support. No Chart.js.

Run from: 03_COMMODITY_MODULES/coal/
  python3 src/build_coal_export_report.py
"""

import base64, json, sys, re as _re
from pathlib import Path
from datetime import datetime

import click
import duckdb
import pandas as pd

# ─── PATHS ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
COAL_DIR     = SCRIPT_DIR.parent
PROJECT_ROOT = COAL_DIR.parent.parent
DB_PATH      = COAL_DIR / "data" / "coal_analytics.duckdb"
DATA_DIR     = COAL_DIR / "data" / "processed"
SUPPLY_CHAIN_MAP = COAL_DIR / "reports" / "drafts" / "coal_supply_chain_map.html"

BUILD_DATE  = datetime.now().strftime("%B %d, %Y")
TODAY       = datetime.now().strftime("%Y%m%d")


def _extract_map_inline(full_html):
    """Extract (card_html, init_js) from a complete map HTML string."""
    body_m = _re.search(r'<body>(.*?)</body>', full_html, _re.DOTALL)
    if not body_m:
        return full_html, ''
    body = body_m.group(1).strip()
    script_m = _re.search(r'<script>(.*?)</script>', body, _re.DOTALL)
    if script_m:
        card = body[:body.rfind('<script>')].strip()
        js = script_m.group(1).strip()
    else:
        card, js = body, ''
    return card, js


# ─── RAIL CORRIDORS (for Leaflet map) ────────────────────────────────────────
RAIL_CORRIDORS = [
    {
        "name": "NS Pocahontas Division",
        "desc": "Williamson WV → Roanoke → Hampton Roads. Primary CAPP HCC artery.",
        "color": "#64ffb4",
        "coords": [[37.27,-81.56],[37.22,-80.41],[37.00,-79.82],[36.99,-77.40],[36.92,-76.36]],
    },
    {
        "name": "CSX B&O / Sand Patch Grade",
        "desc": "Cumberland MD → Hagerstown → Baltimore Curtis Bay. NAPP thermal bituminous.",
        "color": "#ff6464",
        "coords": [[39.65,-79.96],[39.49,-79.27],[39.72,-77.72],[39.30,-76.62]],
    },
    {
        "name": "CSX Cardinal Corridor",
        "desc": "Huntington WV → Clifton Forge → Newport News (Pier IX).",
        "color": "#ffb464",
        "coords": [[38.42,-82.44],[38.09,-81.11],[37.78,-80.45],[37.50,-79.87],[37.08,-76.46]],
    },
    {
        "name": "NS Birmingham District",
        "desc": "Warrior Basin mines → Birmingham → Port of Mobile (primary export route). Note: current Warrior Met production exports via Mobile, not Hampton Roads.",
        "color": "#b464ff",
        "coords": [[33.60,-87.10],[33.50,-86.80],[33.00,-88.04]],
    },
]

TERMINALS = [
    {"name":"NS Lamberts Point","lat":36.9163,"lon":-76.3618,"type":"Hampton Roads",
     "desc":"48M ST/yr. Capesize-capable. NS Pocahontas Division feed. Western Hemisphere's largest coal export terminal."},
    {"name":"Dominion Terminal Associates","lat":36.9124,"lon":-76.3018,"type":"Hampton Roads",
     "desc":"26M ST/yr. 100% MET in 2025. ALPHA / Core Natural Resources primary loading facility."},
    {"name":"Pier IX (VPA)","lat":36.9976,"lon":-76.4418,"type":"Hampton Roads",
     "desc":"14M ST/yr. CSX Cardinal Corridor feed. Mixed CAPP MET and crossover grades."},
    {"name":"CNX Marine Terminal","lat":39.2142,"lon":-76.5527,"type":"Baltimore",
     "desc":"14M ST/yr. Curtis Bay. Core Natural Resources / CNX. NAPP thermal and crossover grades."},
    {"name":"CSX Curtis Bay","lat":39.2084,"lon":-76.5546,"type":"Baltimore",
     "desc":"12M ST/yr. CSX direct rail loop. Largest average vessel size in Baltimore."},
    {"name":"CONSOL Marine Terminal","lat":39.2108,"lon":-76.5535,"type":"Baltimore",
     "desc":"10M ST/yr. Curtis Bay. Now Core Natural Resources. NAPP bituminous specialist."},
]

KEY_MINES = [
    {"name":"Bailey Mine (CNX/Core)","lat":39.818,"lon":-80.236,"basin":"NAPP"},
    {"name":"Enlow Fork (CNX/Core)","lat":39.862,"lon":-80.297,"basin":"NAPP"},
    {"name":"Buchanan Mine (Coronado)","lat":37.236,"lon":-81.986,"basin":"CAPP"},
    {"name":"Leer Mine (Arch/Core)","lat":39.237,"lon":-80.059,"basin":"CAPP"},
    {"name":"Mine No. 7 (Warrior Met)","lat":33.567,"lon":-87.133,"basin":"Warrior"},
    {"name":"Oak Grove (Warrior Met)","lat":33.615,"lon":-87.049,"basin":"Warrior"},
    {"name":"Deep Mine 41 (Alpha)","lat":37.211,"lon":-82.223,"basin":"CAPP"},
    {"name":"No. 2 Gas Mine (Ramaco)","lat":37.854,"lon":-81.892,"basin":"CAPP"},
]


# ─── DATA LOAD ────────────────────────────────────────────────────────────────
def load_data(con):
    d = {}

    # ── Annual port totals (December YTD from monthly_summary) ─────────────────
    for port, key_met, key_th in [
        ('H ROADS',   'hr_met_annual_mt',  'hr_thermal_annual_mt'),
        ('BALTIMORE', 'bal_met_annual_mt', 'bal_thermal_annual_mt'),
    ]:
        for coal_type, key in [('MET', key_met), ('THERMAL', key_th)]:
            val = con.execute(
                "SELECT MAX(metric_tons) FROM coal_monthly_summary "
                "WHERE port=? AND coal_type=? AND datepart('year',report_date)=2025",
                [port, coal_type]
            ).fetchone()[0]
            d[key] = float(val) if val else 0.0

    # ── Terminal MT 2025 (vessel_calls) ────────────────────────────────────────
    d['terms_mt_2025'] = con.execute("""
        SELECT terminal, port,
               SUM(metric_tons) AS mt,
               ROUND(100.0 * SUM(CASE WHEN coal_type='MET' THEN metric_tons ELSE 0 END)
                     / NULLIF(SUM(metric_tons),0), 1) AS met_pct
        FROM coal_vessel_calls
        WHERE port IN ('H ROADS','BALTIMORE')
          AND datepart('year',report_date) = 2025
          AND metric_tons IS NOT NULL
        GROUP BY terminal, port ORDER BY mt DESC
    """).fetchall()

    # ── Shipper MT 2025 (vessel_calls) ─────────────────────────────────────────
    d['shippers_mt_2025'] = con.execute("""
        SELECT shipper_norm,
               SUM(metric_tons) AS mt,
               ROUND(100.0 * SUM(CASE WHEN coal_type='MET' THEN metric_tons ELSE 0 END)
                     / NULLIF(SUM(metric_tons),0), 1) AS met_pct,
               ROUND(100.0 * SUM(CASE WHEN port='H ROADS' THEN metric_tons ELSE 0 END)
                     / NULLIF(SUM(metric_tons),0), 0) AS hr_pct
        FROM coal_vessel_calls
        WHERE port IN ('H ROADS','BALTIMORE')
          AND datepart('year',report_date) = 2025
          AND shipper_norm IS NOT NULL AND metric_tons IS NOT NULL
        GROUP BY shipper_norm ORDER BY mt DESC LIMIT 12
    """).fetchall()

    # ── Destination MT 2025 (vessel_calls) ────────────────────────────────────
    d['dests_mt_2025'] = con.execute("""
        SELECT destination_country,
               SUM(metric_tons) AS mt,
               ROUND(100.0 * SUM(CASE WHEN coal_type='MET' THEN metric_tons ELSE 0 END)
                     / NULLIF(SUM(metric_tons),0), 1) AS met_pct
        FROM coal_vessel_calls
        WHERE port IN ('H ROADS','BALTIMORE')
          AND datepart('year',report_date) = 2025
          AND destination_country IS NOT NULL AND metric_tons IS NOT NULL
        GROUP BY destination_country ORDER BY mt DESC LIMIT 18
    """).fetchall()

    # ── Named receivers (call counts — receiver-level MT not available) ─────────
    d['receivers_2025'] = con.execute("""
        SELECT receiver_group, COUNT(*) AS calls
        FROM coal_vessel_calls
        WHERE port IN ('H ROADS','BALTIMORE') AND datepart('year',report_date) = 2025
          AND receiver_group IS NOT NULL AND receiver_group != 'TO ORDER'
        GROUP BY receiver_group ORDER BY calls DESC LIMIT 12
    """).fetchall()

    # ── Monthly MT 2025 from monthly_summary (individual months only) ──────────
    monthly_mt_rows = con.execute("""
        SELECT datepart('month', report_date) AS mo, port, SUM(metric_tons) AS mt
        FROM coal_monthly_summary
        WHERE port IN ('H ROADS','BALTIMORE')
          AND datepart('year', report_date) = 2025
          AND metric_tons IS NOT NULL AND metric_tons < 5000000
        GROUP BY mo, port ORDER BY mo, port
    """).fetchall()
    d['monthly_mt_2025'] = {(r[0], r[1]): r[2] for r in monthly_mt_rows}

    # ── YoY annual MT from monthly_summary ────────────────────────────────────
    # 2022-2023: monthly rows only (Format 1) → SUM = annual total
    # 2024-2025: MAX = December YTD annual total (2024 backfill + Format 2 rows)
    yoy_mt_rows = con.execute("""
        SELECT yr, port, SUM(annual_mt) AS total_mt
        FROM (
            -- 2024 & 2025: take MAX (December YTD = annual total)
            SELECT datepart('year', report_date) AS yr, port, coal_type,
                   MAX(metric_tons) AS annual_mt
            FROM coal_monthly_summary
            WHERE port IN ('H ROADS','BALTIMORE')
              AND datepart('year', report_date) IN (2024, 2025)
              AND metric_tons IS NOT NULL
            GROUP BY yr, port, coal_type

            UNION ALL

            -- 2022-2023: monthly rows only → SUM = annual total
            SELECT datepart('year', report_date) AS yr, port, coal_type,
                   SUM(metric_tons) AS annual_mt
            FROM coal_monthly_summary
            WHERE port IN ('H ROADS','BALTIMORE')
              AND datepart('year', report_date) IN (2022, 2023)
              AND metric_tons IS NOT NULL
            GROUP BY yr, port, coal_type
        ) sub
        GROUP BY yr, port ORDER BY yr, port
    """).fetchall()
    d['yoy_mt'] = {(r[0], r[1]): r[2] for r in yoy_mt_rows}

    return d


# ─── HELPER ───────────────────────────────────────────────────────────────────
def fmt_mt(mt):
    """Format metric tons — whole numbers, tilde prefix, K below 1M."""
    if mt >= 1e6:
        return f"~{round(mt/1e6)}M tons"
    return f"~{round(mt/1e3)}K tons"

def pct_chg(a, b):
    """Percent change from a to b."""
    if a == 0:
        return "N/A"
    c = (b - a) / a * 100
    sign = "+" if c > 0 else ""
    return f"{sign}{c:.0f}%"


# ─── CSS ─────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:      #0a1520;
  --surface: #0f1e2e;
  --text:    rgba(255,255,255,0.90);
  --muted:   rgba(255,255,255,0.60);
  --faint:   rgba(255,255,255,0.30);
  --accent:  #64ffb4;
  --red:     #ff6464;
  --border:  rgba(255,255,255,0.08);
}

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 1.02rem;
  line-height: 1.82;
  -webkit-font-smoothing: antialiased;
}

/* ── NAV ── */
nav {
  position: sticky; top: 0; z-index: 100;
  background: rgba(10,21,32,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 52px;
  max-width: 100%;
}
.nav-brand { font-size: 0.78rem; font-weight: 600; color: var(--accent); letter-spacing: 1px; text-transform: uppercase; text-decoration: none; }
.nav-links { display: flex; gap: 28px; }
.nav-links a { font-size: 0.8rem; color: var(--muted); text-decoration: none; transition: color 0.2s; }
.nav-links a:hover { color: var(--text); }

/* ── HERO ── */
.hero {
  max-width: 760px; margin: 0 auto;
  padding: 64px 24px 40px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0;
}
.hero-tag {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 2.5px;
  text-transform: uppercase; color: var(--accent);
  margin-bottom: 18px;
}
.hero h1 {
  font-size: 2.4rem; font-weight: 700; line-height: 1.15;
  color: #fff; margin-bottom: 16px; letter-spacing: -0.5px;
}
.hero h1 em { font-style: italic; font-weight: 300; }
.hero-sub {
  font-size: 1.08rem; color: var(--muted); line-height: 1.7;
  margin-bottom: 28px; font-weight: 300;
}
.hero hr { border: none; border-top: 1px solid var(--border); margin-bottom: 18px; }
.hero-byline { font-size: 0.8rem; color: var(--faint); }
.hero-byline strong { color: var(--muted); font-weight: 500; }

/* ── ARTICLE BODY ── */
.article-body {
  max-width: 760px; margin: 0 auto;
  padding: 48px 24px 80px;
}

p {
  color: var(--muted);
  margin-bottom: 0;
}
p + p { margin-top: 0.85em; text-indent: 1.5em; }

h2 {
  font-size: 1.22rem; font-weight: 500;
  color: var(--text); letter-spacing: -0.2px;
  margin: 52px 0 18px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

h3 {
  font-size: 0.95rem; font-weight: 600;
  color: var(--text); margin: 32px 0 10px;
  letter-spacing: -0.1px;
}

/* ── SECTION DIVIDER ── */
.divider {
  text-align: center; color: var(--faint);
  letter-spacing: 10px; font-size: 0.75rem;
  margin: 52px 0; user-select: none;
}

/* ── TABLES ── */
.data-table {
  width: 100%; border-collapse: collapse;
  font-size: 0.85rem; margin: 24px 0;
}
.data-table th {
  background: rgba(100,255,180,0.06);
  color: var(--accent); font-weight: 600;
  padding: 10px 14px; text-align: left;
  font-size: 0.78rem; letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.04);
  color: var(--muted);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table .num { text-align: right; font-variant-numeric: tabular-nums; }
.data-table .accent-cell { color: var(--accent); }

/* ── CHARTS ── */
.chart-wrap {
  margin: 32px 0;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 6px; padding: 20px;
}
.chart-label {
  font-size: 0.75rem; color: var(--faint);
  letter-spacing: 0.5px; margin-bottom: 14px;
  text-transform: uppercase; font-weight: 600;
}
canvas { max-height: 320px; }

/* ── PULL NOTE ── */
.pull-note {
  border-left: 2px solid var(--accent);
  padding: 12px 18px; margin: 28px 0;
  font-size: 0.93rem; color: var(--muted);
  font-style: italic; line-height: 1.65;
}

/* ── INLINE MAPS ── */
.map-inline-wrap { margin: 32px 0; border-radius: 6px; overflow: hidden; }
.card { background: #0a1520; }
.header-strip { background: #c8102e; height: 6px; width: 100%; }
.header-block { padding: 18px 24px 14px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.kicker { font-family: 'Arial', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #c8102e; margin-bottom: 6px; }
.main-title { font-size: 20px; font-weight: 700; color: #f5f0e8; line-height: 1.2; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: rgba(255,255,255,0.55); font-family: 'Arial', sans-serif; }
.map-area { position: relative; background: #0a1520; }
.legend-block { padding: 14px 24px 18px; display: flex; gap: 32px; align-items: flex-start; border-top: 1px solid rgba(255,255,255,0.08); flex-wrap: wrap; }
.legend-title { font-family: 'Arial', sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.35); margin-bottom: 6px; }
.legend-row { display: flex; align-items: center; gap: 7px; font-family: 'Arial', sans-serif; font-size: 11px; color: rgba(255,255,255,0.55); margin-bottom: 4px; }
.legend-swatch { width: 28px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.map-footnote { padding: 10px 24px 16px; font-family: 'Arial', sans-serif; font-size: 10px; color: rgba(255,255,255,0.28); line-height: 1.5; border-top: 1px solid rgba(255,255,255,0.05); }

/* ── DROP CAP ── */
.drop-cap::first-letter {
  font-size: 4.0em; font-weight: 700;
  float: left; line-height: 0.73;
  margin: 0.06em 0.12em 0 0;
  color: #fff;
}

/* ── INLINE FLOAT IMAGE ── */
.article-img-float {
  float: left;
  width: 210px;
  margin: 4px 28px 20px 0;
  clear: left;
}
.article-img-placeholder {
  width: 100%; height: 155px;
  background: rgba(255,255,255,0.025);
  border: 1px dashed rgba(255,255,255,0.10);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 6px;
}
.article-img-placeholder span {
  font-size: 0.66rem; letter-spacing: 1.5px;
  text-transform: uppercase; color: rgba(255,255,255,0.18);
}
.article-img-placeholder svg { opacity: 0.12; }
.article-img-caption {
  font-size: 0.70rem; color: rgba(255,255,255,0.22);
  text-align: center; margin-top: 6px;
  font-style: italic; line-height: 1.4;
}
.article-img-clear { clear: both; }

/* ── AUTHOR BIO ── */
.author-bio {
  max-width: 760px; margin: 0 auto;
  padding: 40px 24px 52px;
  border-top: 1px solid var(--border);
  display: flex; gap: 22px; align-items: flex-start;
}
.author-bio-text { flex: 1; }
.author-bio-text p {
  font-size: 0.88rem; color: var(--faint);
  line-height: 1.72; margin: 0; text-indent: 0 !important;
}
.author-bio-text p + p { margin-top: 0; text-indent: 0 !important; }
.author-name {
  font-size: 0.78rem; font-weight: 600; color: var(--muted);
  letter-spacing: 0.5px; margin-bottom: 6px;
}

/* ── FOOTER ── */
footer {
  border-top: 1px solid var(--border);
  padding: 24px 24px; text-align: center;
  font-size: 0.78rem; color: var(--faint);
  max-width: 760px; margin: 0 auto;
}
footer strong { color: var(--muted); }

/* ── RESPONSIVE ── */
@media (max-width: 640px) {
  .hero h1 { font-size: 1.8rem; }
  .hero, .article-body { padding-left: 18px; padding-right: 18px; }
  .nav-links { display: none; }
}

p strong { font-weight: inherit; color: inherit; }
"""


# ─── MAP JAVASCRIPT ───────────────────────────────────────────────────────────
def build_map_js():
    corridors_json = json.dumps(RAIL_CORRIDORS)
    terminals_json = json.dumps(TERMINALS)
    mines_json     = json.dumps(KEY_MINES)
    return f"""
<script>
(function() {{
  var map = L.map('supply-map', {{
    center: [37.5, -79.0], zoom: 5,
    zoomControl: true
  }});

  // Dark basemap
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd', maxZoom: 18
  }}).addTo(map);

  // Rail corridors
  var corridors = {corridors_json};
  corridors.forEach(function(c) {{
    L.polyline(c.coords, {{
      color: c.color, weight: 2.5, dashArray: '8,5', opacity: 0.75
    }}).bindTooltip('<b style="color:'+c.color+'">'+c.name+'</b><br><span style="font-size:0.78rem;color:#aaa;">'+c.desc+'</span>', {{sticky:true}})
      .addTo(map);
  }});

  // Terminals
  var terms = {terminals_json};
  var termColors = {{'Hampton Roads':'#64ffb4','Baltimore':'#ff6464'}};
  terms.forEach(function(t) {{
    var col = termColors[t.type] || '#888';
    L.circleMarker([t.lat,t.lon], {{
      radius: 9, color: col, weight: 2.5,
      fillColor: '#0a0a0a', fillOpacity: 0.9
    }}).bindPopup(
      '<div style="font-family:Space Grotesk,system-ui;background:#111;color:#ccc;padding:12px;border-radius:6px;min-width:200px;">' +
      '<b style="color:'+col+';">'+t.name+'</b><br>' +
      '<span style="color:#666;font-size:0.78rem;">'+t.type+'</span>' +
      '<hr style="border-color:#333;margin:6px 0;">' +
      '<span style="font-size:0.8rem;">'+t.desc+'</span></div>',
      {{maxWidth:240}}
    ).addTo(map);
  }});

  // Mines
  var mines = {mines_json};
  var mineColors = {{'NAPP':'#ff6464','CAPP':'#ffb464','Warrior':'#b464ff'}};
  mines.forEach(function(m) {{
    var col = mineColors[m.basin] || '#888';
    L.circleMarker([m.lat,m.lon], {{
      radius: 5, color: col, weight: 1.5,
      fillColor: col, fillOpacity: 0.5
    }}).bindTooltip('<b>'+m.name+'</b> ('+m.basin+')', {{sticky:true}}).addTo(map);
  }});

  // Legend
  var legend = L.control({{position:'bottomright'}});
  legend.onAdd = function() {{
    var div = L.DomUtil.create('div');
    div.style.cssText = 'background:rgba(10,10,10,0.9);border:1px solid #333;border-radius:6px;padding:12px;font-family:Space Grotesk,system-ui;font-size:0.75rem;color:#aaa;';
    div.innerHTML =
      '<div style="color:#64ffb4;font-weight:600;margin-bottom:8px;">USEC COAL INFRASTRUCTURE</div>' +
      '<div style="margin-bottom:4px;"><span style="color:#64ffb4;">●</span> Hampton Roads Terminal</div>' +
      '<div style="margin-bottom:4px;"><span style="color:#ff6464;">●</span> Baltimore Terminal</div>' +
      '<div style="margin-bottom:6px;"></div>' +
      '<div style="margin-bottom:4px;"><span style="color:#ff6464;">— —</span> NAPP Mine</div>' +
      '<div style="margin-bottom:4px;"><span style="color:#ffb464;">— —</span> CAPP Mine</div>' +
      '<div style="margin-bottom:4px;"><span style="color:#b464ff;">— —</span> Warrior Basin Mine</div>' +
      '<div style="margin-top:8px;border-top:1px solid #333;padding-top:8px;">' +
      '<span style="color:#64ffb4;">━</span> NS Pocahontas Division<br>' +
      '<span style="color:#ff6464;">━</span> CSX B&amp;O / Sand Patch<br>' +
      '<span style="color:#ffb464;">━</span> CSX Cardinal Corridor<br>' +
      '<span style="color:#b464ff;">━</span> NS Birmingham District' +
      '</div>';
    return div;
  }};
  legend.addTo(map);
}})();
</script>"""


# ─── HTML BUILDER ─────────────────────────────────────────────────────────────
def build_html(d, flow_map_block='', mine_map_block='', photo_b64='', og_image_url=''):

    # ── Port totals (monthly_summary confirmed annual figures) ────────────────
    hr_met_mt     = d.get('hr_met_annual_mt',   0) or 0.0
    hr_th_mt      = d.get('hr_thermal_annual_mt', 0) or 0.0
    bal_met_mt    = d.get('bal_met_annual_mt',  0) or 0.0
    bal_th_mt     = d.get('bal_thermal_annual_mt', 0) or 0.0

    hr_total_mt   = hr_met_mt  + hr_th_mt
    bal_total_mt  = bal_met_mt + bal_th_mt
    usec_total_mt = hr_total_mt + bal_total_mt
    hr_share_mt   = round(100 * hr_total_mt  / usec_total_mt) if usec_total_mt else 0
    met_share_pct = round(100 * (hr_met_mt + bal_met_mt) / usec_total_mt) if usec_total_mt else 0

    usec_str  = fmt_mt(usec_total_mt) if usec_total_mt else "N/A"
    hr_str    = fmt_mt(hr_total_mt)   if hr_total_mt   else "N/A"
    bal_str   = fmt_mt(bal_total_mt)  if bal_total_mt  else "N/A"
    hr_met_str = fmt_mt(hr_met_mt)    if hr_met_mt     else "N/A"

    # YoY MT comparison
    yoy_2024 = (d['yoy_mt'].get((2024,'H ROADS'), 0) or 0) + \
               (d['yoy_mt'].get((2024,'BALTIMORE'), 0) or 0)
    pct_yr = pct_chg(yoy_2024, usec_total_mt) if yoy_2024 else "N/A"

    # Top shipper by MT
    top_shipper = d['shippers_mt_2025'][0][0] if d['shippers_mt_2025'] else "N/A"

    # ArcelorMittal (receivers — call count only, no MT at receiver level)
    am_calls = next((r[1] for r in d['receivers_2025'] if 'ARCELOR' in r[0]), 0)

    # Top destination (for stat card)
    top_dest = d['dests_mt_2025'][0][0].title() if d['dests_mt_2025'] else "N/A"

    # Growth from 2022 to 2025
    usec_2022 = (d['yoy_mt'].get((2022,'H ROADS'),0) or 0) + \
                (d['yoy_mt'].get((2022,'BALTIMORE'),0) or 0)
    growth_22_25 = pct_chg(usec_2022, usec_total_mt) if usec_2022 else "N/A"

    # H Roads met pct (for narrative use)
    hr_met_pct = round(100 * hr_met_mt / hr_total_mt) if hr_total_mt else 0
    bal_met_pct = round(100 * bal_met_mt / bal_total_mt) if bal_total_mt else 0

    # ── Chart.js data (embedded as JS) ───────────────────────────────────────
    yoy_years = [2022, 2023, 2024, 2025]
    chart_hr_mt   = json.dumps([round((d['yoy_mt'].get((yr,'H ROADS'),0) or 0)/1e6,1) for yr in yoy_years])
    chart_bal_mt  = json.dumps([round((d['yoy_mt'].get((yr,'BALTIMORE'),0) or 0)/1e6,1) for yr in yoy_years])

    dest_top8     = d['dests_mt_2025'][:8]
    chart_dest_labels = json.dumps([r[0].title() for r in dest_top8])
    chart_dest_mt     = json.dumps([round((r[1] or 0)/1e6,2) for r in dest_top8])
    chart_dest_met    = json.dumps([round(r[2] or 0, 0) for r in dest_top8])

    chart_split_met = json.dumps([round(hr_met_mt/1e6,1), round(bal_met_mt/1e6,1)])
    chart_split_th  = json.dumps([round(hr_th_mt/1e6,1),  round(bal_th_mt/1e6,1)])

    # Aliases used by new template
    dest_labels = chart_dest_labels
    dest_mt     = chart_dest_mt

    # ── Monthly MT table rows ─────────────────────────────────────────────────
    mo_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    monthly_rows = ""
    for mo in range(1, 13):
        hr_mt  = d['monthly_mt_2025'].get((mo, 'H ROADS'))
        bal_mt = d['monthly_mt_2025'].get((mo, 'BALTIMORE'))
        tot_mt = (hr_mt or 0) + (bal_mt or 0)
        monthly_rows += f"""
        <tr>
          <td><strong>{mo_names[mo-1]}</strong></td>
          <td class="num">{fmt_mt(hr_mt) if hr_mt else '—'}</td>
          <td class="num">{fmt_mt(bal_mt) if bal_mt else '—'}</td>
          <td class="num accent-cell">{fmt_mt(tot_mt) if tot_mt else '—'}</td>
        </tr>"""

    # ── Terminal MT rows (vessel_calls scaled to monthly_summary port totals) ──
    vc_hr_mt  = sum(r[2] for r in d['terms_mt_2025'] if r[1]=='H ROADS'   and r[2]) or 0
    vc_bal_mt = sum(r[2] for r in d['terms_mt_2025'] if r[1]=='BALTIMORE' and r[2]) or 0
    scale_hr  = hr_total_mt  / vc_hr_mt  if vc_hr_mt  else 1.0
    scale_bal = bal_total_mt / vc_bal_mt if vc_bal_mt else 1.0

    term_rows = ""
    for term, port, vc_mt, met_pct in d['terms_mt_2025']:
        if vc_mt is None:
            continue
        est_mt = vc_mt * (scale_hr if port == 'H ROADS' else scale_bal)
        met_p  = met_pct or 0
        badge  = f'<span class="met-badge">{met_p:.0f}% MET</span>' if met_p >= 60 else \
                 f'<span class="thermal-badge">{100-met_p:.0f}% THERMAL</span>'
        term_rows += f"""
        <tr>
          <td><strong>{term}</strong></td>
          <td>{port}</td>
          <td class="num accent-cell">{fmt_mt(est_mt)}</td>
          <td>{badge}</td>
        </tr>"""

    # ── Shipper MT rows ───────────────────────────────────────────────────────
    shipper_rows = ""
    for sn, vc_mt, met_pct, hr_pct in d['shippers_mt_2025']:
        if vc_mt is None:
            continue
        met_p = met_pct or 0
        badge = f'<span class="met-badge">{met_p:.0f}%</span>' if met_p >= 60 else \
                f'<span class="thermal-badge">{met_p:.0f}%</span>'
        shipper_rows += f"""
        <tr>
          <td><strong>{sn}</strong></td>
          <td class="num accent-cell">{fmt_mt(vc_mt)}</td>
          <td>{badge}</td>
          <td class="num">{int(hr_pct or 0)}% H Roads</td>
        </tr>"""

    # ── Destination MT rows ───────────────────────────────────────────────────
    dest_rows = ""
    for country, vc_mt, met_pct in d['dests_mt_2025']:
        if vc_mt is None:
            continue
        coal_type = "Metallurgical" if (met_pct or 0) >= 75 else \
                    "Thermal"       if (met_pct or 0) <= 25 else "Mixed"
        dest_rows += f"""
        <tr>
          <td><strong>{country}</strong></td>
          <td class="num accent-cell">{fmt_mt(vc_mt)}</td>
          <td class="num">{met_pct or 0:.0f}%</td>
          <td>{coal_type}</td>
        </tr>"""

    # ── YoY MT rows ───────────────────────────────────────────────────────────
    yoy_rows = ""
    for yr in [2022, 2023, 2024, 2025]:
        hr_mt  = d['yoy_mt'].get((yr,'H ROADS'),   0) or 0
        bal_mt = d['yoy_mt'].get((yr,'BALTIMORE'),  0) or 0
        tot_mt = hr_mt + bal_mt
        # Fallback if data missing
        if not tot_mt:
            yoy_rows += f"""
        <tr>
          <td><strong>{yr}</strong></td>
          <td class="num" style="color:var(--text-faint)">—</td>
          <td class="num" style="color:var(--text-faint)">—</td>
          <td class="num" style="color:var(--text-faint)">—</td>
          <td class="num" style="color:var(--text-faint);font-size:0.78rem;">data gap</td>
        </tr>"""
            continue
        if yr > 2022:
            pr_hr  = d['yoy_mt'].get((yr-1,'H ROADS'),   0) or 0
            pr_bal = d['yoy_mt'].get((yr-1,'BALTIMORE'),  0) or 0
            pr_tot = pr_hr + pr_bal
            chg = pct_chg(pr_tot, tot_mt) if pr_tot else "—"
        else:
            chg = "—"
        highlight = ' style="background:rgba(100,255,180,0.04);"' if yr == 2025 else ''
        yoy_rows += f"""
        <tr{highlight}>
          <td><strong>{yr}</strong></td>
          <td class="num">{fmt_mt(hr_mt) if hr_mt else '—'}</td>
          <td class="num">{fmt_mt(bal_mt) if bal_mt else '—'}</td>
          <td class="num accent-cell">{fmt_mt(tot_mt) if tot_mt else '—'}</td>
          <td class="num">{chg}</td>
        </tr>"""

    # ── Receivers table (call counts — receiver MT not available) ─────────────
    recv_rows = ""
    for rg, calls in d['receivers_2025']:
        recv_rows += f'<tr><td><strong>{rg}</strong></td><td class="num accent-cell">{calls}</td></tr>'

    # Cost reference table
    cost_panamax_hr = [
        ("Pilotage (incl. Chesapeake Bay surcharge)", "$10,800"),
        ("Towage (2 tugs, in + out)", "$42,000"),
        ("Coal Wharfage ($0.80/ST × 44,000 ST)", "$35,200"),
        ("Stevedoring ($3.00/ST, grab crane)", "$132,000"),
        ("Harbour Dues, Dockage & Lines", "$17,738"),
        ("Agency & Miscellaneous", "$9,500"),
    ]
    cost_rows_hr = "".join(f'<tr><td>{i}</td><td class="num">{v}</td></tr>'
                           for i, v in cost_panamax_hr)
    total_hr = "$247,238"
    per_mt_hr = "$6.18/MT"

    # Receivers table
    recv_rows = ""
    for rg, calls in d['receivers_2025']:
        recv_rows += f'<tr><td><strong>{rg}</strong></td><td class="num accent-cell">{calls}</td></tr>'

    _html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US East Coast Coal Exports — 2025 Year in Review</title>
<!-- Open Graph / Social sharing -->
<meta property="og:type" content="article">
<meta property="og:title" content="US East Coast Coal Exports — 2025 Year in Review">
<meta property="og:description" content="Hampton Roads and Baltimore shipped approximately {usec_str} of coal in 2025, sustaining near-record volumes as the industry restructured around its largest corporate consolidation in a decade.">
<meta property="og:site_name" content="OceanDatum">
<meta property="article:author" content="William S. Davis III">
{f'<meta property="og:image" content="{og_image_url}">' if og_image_url else ''}
<!-- Twitter / X card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="US East Coast Coal Exports — 2025 Year in Review">
<meta name="twitter:description" content="Hampton Roads and Baltimore shipped approximately {usec_str} of coal in 2025, sustaining near-record volumes.">
{f'<meta name="twitter:image" content="{og_image_url}">' if og_image_url else ''}
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson@3.0.2/dist/topojson.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>

<nav>
  <a class="nav-brand" href="#">OceanDatum</a>
  <div class="nav-links">
    <a href="#markets">Markets</a>
    <a href="#supply">Supply Chain</a>
    <a href="#economics">Economics</a>
    <a href="#outlook">Outlook</a>
  </div>
</nav>

<div class="hero">
  <div class="hero-tag">Ocean Datum &middot; Analysis &middot; {BUILD_DATE}</div>
  <h1>US East Coast Coal Exports<br><em>2025 Year in Review</em></h1>
  <p class="hero-sub">
    Hampton Roads and Baltimore shipped approximately {usec_str} of coal in 2025,
    sustaining near-record volumes as the industry restructured around its largest
    corporate consolidation in a decade.
  </p>
  <hr>
  <div class="hero-byline"><strong>William S. Davis III</strong> &middot; Maritime &amp; Commodity Intelligence</div>
</div>

<div class="article-body">

  __ARTICLE_PHOTO__

  <p class="drop-cap">The year did not move the tonnage needle in any dramatic direction. Hampton Roads and
  Baltimore together exported {usec_str} — within 1% of the prior year and approximately
  {growth_22_25} above the 2022 baseline. That stability is, itself, the story. The emergency
  demand that drove USEC volumes sharply higher in 2022 and 2023 — European utilities
  rebuilding stockpiles after Russian supply was sanctioned, Australian mine disruptions
  redirecting Asian steel mills toward Appalachian alternatives — has fully unwound.
  What has settled into place is something more durable: a trade anchored by long-term
  blast furnace supply contracts, premium coal grades that command loyalty from buyers,
  and two ports that have quietly become among the most consequential bulk export
  facilities in the world.</p>

  <p>{met_share_pct}% of all USEC exports in 2025 were metallurgical coal — coking-grade
  product destined for blast furnaces, not power plants. That fraction is a structural
  characteristic, not a cyclical fluctuation. Metallurgical coal demand tracks crude steel
  output, and crude steel output tracks capital investment in infrastructure and
  manufacturing. Hampton Roads and Baltimore function, in that sense, as an industrial
  barometer for global manufacturing health.</p>

  <p>The most consequential development of the year occurred off the water entirely.
  In December 2024, Arch Resources and CONSOL Energy completed a merger to form
  Core Natural Resources — the largest US coal producer by combined output. The new
  entity entered 2025 with loading positions at both Hampton Roads and Baltimore
  simultaneously, a degree of terminal concentration with no recent precedent in the
  USEC export complex. The integration was visible in the shipping record through the year:
  Alpha, Arch, and CONSOL shipment identities consolidating, gradually, under a single banner.</p>

  <div class="article-img-clear"></div>

  <div class="chart-wrap">
    <div class="chart-label">Annual export volume — Hampton Roads &amp; Baltimore (million metric tons)</div>
    <canvas id="chartVolume"></canvas>
  </div>

<div class="divider">&bull; &bull; &bull;</div>

<h2 id="markets">Where the Coal Went</h2>

  <p>Four countries absorbed the majority of all USEC coal exports in 2025: India, Brazil,
  the Netherlands, and China. No single secondary market approached the scale of any one
  of these four. The destinations are more concentrated than they were five years ago —
  a pattern consistent with the long-term supply contract structure that governs how
  blast furnace coal is purchased.</p>

  __FLOW_MAP__

  <div class="chart-wrap" style="max-height:380px;">
    <div class="chart-label">Top export destinations by tonnage — 2025 (million MT)</div>
    <canvas id="chartDest" style="max-height:300px;"></canvas>
  </div>

  <p>India is the only major destination purchasing significant volumes of both metallurgical
  and thermal coal from US East Coast ports simultaneously. Blast furnace coking coal flows
  to integrated steelworks at Visakhapatnam, Jamshedpur, and Bhilai. High-BTU thermal
  bituminous flows to coastal power utilities. The split reflects India's simultaneous
  expansion of industrial steel capacity and electricity generation infrastructure, and it
  has made India the leading USEC destination by volume in every year since 2021.</p>

  <p>Brazil's import book is a pure metallurgical programme. Domestic hard coking coal is
  absent, and integrated steelmakers — including Gerdau, CSN, and Ternium — rely entirely
  on imported blend components. Hampton Roads to Atlantic Brazil is a direct haul requiring
  no canal transit, and multi-year supply contracts provide the volume stability that makes
  Brazil one of the most predictable USEC destinations year on year. The route is among
  the most logistically efficient in the global seaborne coal trade.</p>

  <p>Netherlands tonnage is primarily Rotterdam in transit — coal arriving for blending and
  onward distribution to ArcelorMittal's Belgian and Dutch steelworks, or movement up
  the Rhine to German and French buyers. ArcelorMittal is the most prominent buyer in the
  USEC shipping record overall, operating blast furnaces across Belgium, France, Spain,
  and Brazil, none of which have access to domestic coking coal. Spain and Italy record
  near-pure metallurgical imports as Iberian and Mediterranean steel producers supplement
  declining European domestic coal supply with Appalachian coking grades.</p>

  <p>China and Japan represent the premium-grade corridor. Both are purchasing high-CSR,
  low-volatile coking coal for blast furnaces operating to stringent quality specifications.
  The round-Cape freight to Japan runs $38–$52 per metric ton — the highest freight cost
  in the USEC export matrix — but the premium grades destined for Japanese furnaces carry
  margins sufficient to absorb it. The consistency of these supply relationships, maintained
  across multiple price cycles, reflects how deeply Appalachian low-vol HCC is embedded
  in Far East blast furnace blend specifications.</p>

  <div class="pull-note">
    Morocco and Egypt both recorded material import volumes in 2025 at minimal metallurgical
    content. TAQA Morocco's Jorf Lasfar power complex and Egyptian utilities have been
    building US coal procurement relationships as generation capacity expands and supply
    diversification away from South African origins accelerates. Both markets were
    negligible in 2021–2023.
  </div>

  <p>The steel mill buyer set behind these flows is anchored by a small number of very
  large programmes. Indian state steelmakers SAIL and RINL have systematically expanded
  US supply relationships as a hedge against concentration in Australian origins — a
  strategy that accelerated after the Australia-China trade disruptions reshuffled global
  met coal flows in 2020–2021. Shipments linked to what the market understands to be
  Adani Group entities appeared in the USEC buyer set in 2025 — if confirmed, procurement
  at that scale would reflect committed greenfield steelmaking capacity coming into
  production, not opportunistic spot purchasing. SSAB's Swedish and Finnish
  furnaces operate to stringent low-sulfur, low-volatile specifications that only a
  limited number of global mines can satisfy. Metinvest of Ukraine has sustained USEC
  procurement through redirected supply chains despite significant operational disruption —
  an illustration of how blast furnace coal relationships function on multi-year contractual
  frameworks that absorb short-term market dislocations.</p>

  <p>On the thermal side, JERA — Japan's largest power generator — exemplifies the stable,
  long-horizon buyer. Multi-year supply agreements with Northern Appalachian producers
  underpin consistent Baltimore volumes that persist through spot market cycles. Morocco
  and Egypt, as noted, represent the structural demand growth that is absorbing Northern
  Appalachian thermal coal as US domestic utility consumption declines.</p>

  <div class="chart-wrap">
    <div class="chart-label">Metallurgical vs thermal coal by port — 2025</div>
    <canvas id="chartSplit"></canvas>
  </div>

<div class="divider">&bull; &bull; &bull;</div>

<h2 id="supply">The Infrastructure Behind It</h2>

  <p>Hampton Roads and Baltimore are not interchangeable. They serve different parts of the
  same trade, connected by geography, geology, and the railroad systems that link Appalachian
  mines to tidewater. Hampton Roads handled {hr_share_mt}% of all USEC exports in 2025,
  with {hr_met_pct}% of that volume classified as metallurgical coal. Baltimore's share
  was the remainder — a predominantly thermal book, served exclusively by CSX, with
  metallurgical coal representing approximately {bal_met_pct}% of throughput.</p>

  <p>Within Hampton Roads, terminal specialisation is pronounced. Dominion Terminal
  Associates operated as a near-pure metallurgical loading point in 2025 — the primary
  berth for Core Natural Resources' coking coal programme following the Arch-CONSOL merger.
  NS Lamberts Point, the largest coal export terminal in the Northern Hemisphere by
  throughput capacity and capable of accommodating Capesize vessels at full draught, moved a predominantly
  metallurgical book with a small crossover fraction. Pier IX at Newport News handled
  the most diversified mix, receiving both CAPP coking coal and crossover-specification
  material that prices into metallurgical or thermal markets depending on the prevailing
  spread.</p>

  <p>At Baltimore, the Core Natural Resources merger placed a single entity in effective
  control of both Curtis Bay loading positions simultaneously. By mid-year, consolidated
  shipments under the Core banner had surpassed legacy CONSOL volumes as pre-existing
  contracts transitioned to the new operating structure. The March 2024 collapse of the
  Francis Scott Key Bridge closed Baltimore's main shipping channel for eleven weeks, but
  the Curtis Bay berths — accessed via the outer Chesapeake Bay approach — maintained
  export operations through the closure using barge lightering and rerouted vessel calls;
  full-year 2025 volumes confirmed the port's throughput capacity was not permanently impaired.</p>

  <p>All coal loaded at both ports originates in the Appalachian coalfields and moves
  exclusively by rail to tidewater. The specific corridor a mine connects to determines
  everything downstream: which port it can serve, which terminal receives it, which
  ocean market it can reach. NS's Pocahontas Division runs approximately 350 miles from
  the coalfields centred on Williamson, West Virginia — the heart of the CAPP low-volatile
  hard coking coal district — through Roanoke and into Hampton Roads. The geology along
  this corridor produces the premium coking grades that steel mills in Brazil, Japan, and
  Europe require as blast furnace blend components. NS Lamberts Point and Dominion Terminal
  Associates sit at the tidal end of this line.</p>

  <p>CSX's primary Appalachian route to Baltimore follows the former Baltimore &amp; Ohio
  mainline, climbing Sand Patch Grade near Cumberland before descending into the Northern
  Appalachian fields of southwestern Pennsylvania. Core Natural Resources' Bailey Mine
  and Enlow Fork complex supply directly to Curtis Bay via this corridor — a haul of
  approximately 200 rail miles, shorter than the Hampton Roads run, providing a cost
  offset for a coal grade that does not command metallurgical premiums. A second CSX
  route — the Cardinal Corridor through Huntington, West Virginia to Newport News — feeds
  Pier IX with Central Appalachian crossover-specification coal that floats between
  the two markets depending on the prevailing price spread.</p>

  __MINE_MAP__

  <p>For both Class I railroads, coal remains the single most significant bulk commodity
  by revenue. Norfolk Southern recorded approximately $1.57 billion in coal revenue in
  2024 — roughly 13% of total operating revenue — with export met coal the primary
  driver. CSX's coal book is larger still: approximately $2.25 billion in 2024, or
  roughly 15–16% of total revenue, reflecting the combined weight of NAPP thermal
  exports through Baltimore and CAPP met exports through Newport News.
  For CSX, coal is the single largest commodity segment by revenue. Any sustained shift
  in export volumes registers directly in quarterly rail earnings — a structural linkage
  that makes the carrier as much a stakeholder in global steel demand cycles as the
  mines it serves.</p>

<div class="divider">&bull; &bull; &bull;</div>

<h2 id="economics">What It Costs to Move Coal to Water</h2>

  <p>Appalachian coking coal is priced on a free-on-board basis at Hampton Roads or
  Baltimore. Low-volatile hard coking coal from CAPP and the Warrior Basin traded in
  the range of $170–$210 per metric ton FOB Hampton Roads through most of 2025 —
  significantly off the $280–$340 range seen in 2022. Mid-volatile HCC settled in the
  $145–$180 range. High-vol A and B specifications traded at $120–$150 FOB, competitive
  with Australian mid-vol on a blend-adjusted basis. Baltimore thermal bituminous —
  NAPP high-BTU coal from Core's Bailey and Enlow Fork complex — traded in the
  $75–$100 per metric ton FOB range through 2025, a significant reduction from the 2022
  peak above $300. At these levels, the spread between NAPP thermal and CAPP met coking
  coal ran approximately $70–$110 per
  ton FOB — the incentive that drives crossover-specification material toward the
  metallurgical market whenever quality specifications allow.</p>

  <table class="data-table">
    <thead>
      <tr>
        <th>Grade</th><th>Origin</th>
        <th class="num">2025 FOB USEC</th>
        <th class="num">2022 Peak</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Low-Vol HCC</td><td>CAPP / Warrior Basin</td><td class="num accent-cell">$170–$210/MT</td><td class="num">$280–$340</td></tr>
      <tr><td>Mid-Vol HCC</td><td>CAPP</td><td class="num accent-cell">$145–$180/MT</td><td class="num">$240–$290</td></tr>
      <tr><td>High-Vol A/B</td><td>CAPP / NAPP crossover</td><td class="num accent-cell">$120–$150/MT</td><td class="num">$200–$250</td></tr>
      <tr><td>Thermal bituminous</td><td>NAPP</td><td class="num accent-cell">$75–$100/MT</td><td class="num">$280–$350</td></tr>
    </tbody>
  </table>

  <p>Ocean freight ran well below the 2021–2022 surge levels across all USEC routes.
  The trans-Atlantic haul to Rotterdam — the shortest voyage in the matrix — ran
  $10–$18 per metric ton, making European steel mills the natural marginal buyer
  when met coal premiums justify the FOB price. India is the highest-freight major
  destination at $22–$32 per metric ton, offset by consistent and large demand
  from multiple import terminals on both coasts. The round-Cape voyage to Japan
  and South Korea ran $38–$52 per metric ton — the highest freight cost in the
  matrix — absorbed by premium-grade margins on low-vol HCC.</p>

  <table class="data-table">
    <thead>
      <tr><th>Route</th><th>Vessel</th><th class="num">2025 Freight (approx.)</th></tr>
    </thead>
    <tbody>
      <tr><td>Hampton Roads → Rotterdam</td><td>Capesize / Panamax</td><td class="num accent-cell">$10–$18/MT</td></tr>
      <tr><td>Hampton Roads → Brazil</td><td>Panamax</td><td class="num accent-cell">$12–$17/MT</td></tr>
      <tr><td>Hampton Roads → India</td><td>Capesize / Panamax</td><td class="num accent-cell">$22–$32/MT</td></tr>
      <tr><td>Hampton Roads → Japan / Korea</td><td>Panamax (via Cape)</td><td class="num accent-cell">$38–$52/MT</td></tr>
    </tbody>
  </table>

  <p>Rail is the dominant cost in the mine-to-ship stack. Unit train movements from
  Central Appalachian origins to Hampton Roads ran approximately $18–$24 per short ton
  in 2025. NAPP to Baltimore via CSX is a shorter corridor at approximately $14–$19.
  Combined mine-to-ship cost for CAPP low-vol HCC loading at Hampton Roads runs
  approximately $24–$30 per metric ton — well within the margin available at $170–$210
  FOB. US metallurgical coal exports averaged approximately 45–55 million short tons
  annually in 2024–2025, with USEC terminals accounting for approximately 65–70% of
  that total. The remaining 30–35% moves through Gulf Coast terminals at higher rail
  cost to origin but with access to Panama Canal routing for Pacific markets.</p>

<div class="divider">&bull; &bull; &bull;</div>

<h2 id="outlook">What 2025 Tells Us</h2>

  <p>The structural story from 2025 is one of market entrenchment, not retreat. Total
  volumes are off the emergency highs of 2022 and 2023, but the trade is durable. The
  destinations are more concentrated — India, Brazil, and Europe now account for the
  majority of all USEC throughput. The supply side is more concentrated too: Core Natural
  Resources enters 2026 controlling production assets across both the CAPP coking belt
  and the NAPP thermal complex, with captive loading positions at both major ports. No
  other Appalachian exporter currently replicates that structural position.</p>

  <p>The reported appearance of Adani Group-linked entities in the USEC buyer set is
  perhaps the most significant demand-side signal of the year. A company widely understood
  to be building greenfield steelmaking capacity in India at scale does not enter new
  long-term coal supply relationships opportunistically. That procurement, if the market
  attribution is correct, reflects a view about where steel demand will be in five years —
  not where spot prices are today. It is a useful corrective to the narrative that coal
  demand is in structural decline, at least in the blast furnace segment.</p>

  <p>The risk that deserves attention is not on the demand side. Steel production is
  growing in India, the Middle East, and Southeast Asia, and coking coal requirements
  grow with it. The risk is supply-side concentration: Core Natural Resources controlling
  a material share of Appalachian coking coal production and multiple Hampton Roads
  loading positions means that any significant operational disruption — flood, strike,
  geological event — now carries a larger market footprint than it would have five years
  ago. The physical infrastructure provides a buffer: NS Lamberts Point at approximately
  48 million short ton annual capacity is a facility built for a larger world than the
  one it currently serves. Whether that headroom is a legacy artefact or a platform
  for resumed growth is the question the next demand cycle will answer.</p>

</div>

<div class="author-bio">
  <div class="author-bio-text">
    <div class="author-name">William S. Davis III</div>
    <p>William S. Davis III is a maritime operations and intelligence practitioner
    with over 30 years of experience across ship agency, terminal operations, and
    commercial maritime consulting on the U.S. Atlantic and Gulf Coasts. He works
    at the intersection of maritime domain expertise and AI system architecture.</p>
  </div>
</div>

<footer>
  OceanDatum &middot; {BUILD_DATE}
</footer>

<script>
(function() {{
  Chart.defaults.color = 'rgba(255,255,255,0.45)';
  Chart.defaults.font.family = "'Space Grotesk', system-ui, sans-serif";
  Chart.defaults.font.size = 11;

  var gridColor = 'rgba(255,255,255,0.06)';
  var accent = '#64ffb4';
  var balCol = 'rgba(255,100,100,0.75)';
  var hrCol  = 'rgba(100,255,180,0.75)';

  // ── Chart 1: Annual volume stacked bar ─────────────────────────────────────
  new Chart(document.getElementById('chartVolume'), {{
    type: 'bar',
    data: {{
      labels: ['2022', '2023', '2024', '2025'],
      datasets: [
        {{
          label: 'Hampton Roads',
          data: {chart_hr_mt},
          backgroundColor: hrCol,
          borderRadius: 4,
        }},
        {{
          label: 'Baltimore',
          data: {chart_bal_mt},
          backgroundColor: balCol,
          borderRadius: 4,
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      plugins: {{
        legend: {{ position: 'top', labels: {{ boxWidth: 12, padding: 16 }} }},
        tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.raw.toFixed(1) + ' MMT' }} }}
      }},
      scales: {{
        x: {{ stacked: true, grid: {{ display: false }} }},
        y: {{ stacked: true, grid: {{ color: gridColor }}, ticks: {{ callback: v => v + ' MMT' }} }}
      }}
    }}
  }});

  // ── Chart 2: Met/Thermal split by port ─────────────────────────────────────
  var splitCtx = document.getElementById('chartSplit');
  if (splitCtx) {{
    new Chart(splitCtx, {{
      type: 'bar',
      data: {{
        labels: ['Hampton Roads', 'Baltimore'],
        datasets: [
          {{
            label: 'Metallurgical',
            data: [{hr_met_mt:.1f}, {bal_met_mt:.1f}],
            backgroundColor: 'rgba(82,175,240,0.75)',
            borderRadius: 4,
          }},
          {{
            label: 'Thermal',
            data: [{hr_th_mt:.1f}, {bal_th_mt:.1f}],
            backgroundColor: 'rgba(224,140,40,0.70)',
            borderRadius: 4,
          }}
        ]
      }},
      options: {{
        responsive: true, indexAxis: 'y',
        plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 12, padding: 16 }} }} }},
        scales: {{
          x: {{ stacked: true, grid: {{ color: gridColor }}, ticks: {{ callback: v => v + ' MMT' }} }},
          y: {{ stacked: true, grid: {{ display: false }} }}
        }}
      }}
    }});
  }}

  // ── Chart 3: Top destinations horizontal bar ────────────────────────────────
  var destCtx = document.getElementById('chartDest');
  if (destCtx) {{
    new Chart(destCtx, {{
      type: 'bar',
      data: {{
        labels: {dest_labels},
        datasets: [{{
          label: 'Million MT',
          data: {dest_mt},
          backgroundColor: 'rgba(100,255,180,0.65)',
          borderRadius: 3,
        }}]
      }},
      options: {{
        responsive: true, indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ color: gridColor }}, ticks: {{ callback: v => v + ' MMT' }} }},
          y: {{ grid: {{ display: false }} }}
        }}
      }}
    }});
  }}

}})();
</script>

</body>
</html>"""
    _html = _html.replace('__FLOW_MAP__', flow_map_block)
    _html = _html.replace('__MINE_MAP__', mine_map_block)

    if photo_b64:
        photo_block = (
            '<div class="article-img-float">'
            f'<img src="data:image/jpeg;base64,{photo_b64}" '
            'alt="Working in the Coal Mine — Lee Dorsey" style="width:100%;display:block;">'
            '<div class="article-img-caption">'
            '<em>Working in the Coal Mine</em> — Lee Dorsey, 1966'
            '</div></div>'
        )
    else:
        photo_block = (
            '<div class="article-img-float">'
            '<div class="article-img-placeholder">'
            '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.2">'
            '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>'
            '<polyline points="21 15 16 10 5 21"/></svg><span>Photo</span></div>'
            '<div class="article-img-caption">Photo placeholder</div></div>'
        )
    _html = _html.replace('__ARTICLE_PHOTO__', photo_block)
    return _html


# ─── CLI ─────────────────────────────────────────────────────────────────────
PHOTO_PATH = Path('/Users/wsd/Downloads/coalmine1.jpeg')


@click.command()
@click.option('--output-dir', default=None,
              help='Output directory (default: 04_REPORTS/coal_export_report/output/)')
@click.option('--open-browser/--no-open-browser', default=True)
@click.option('--og-image-url', default='',
              help='Absolute URL for og:image / twitter:image (e.g. https://yourdomain.com/coalmine1.jpg). '
                   'Leave blank for self-contained HTML; set when hosting the file online.')
def main(output_dir, open_browser, og_image_url):
    """Generate USEC Coal Exports — 2025 Year in Review."""
    if not DB_PATH.exists():
        click.echo(f"ERROR: Database not found: {DB_PATH}", err=True)
        sys.exit(1)

    out_dir = Path(output_dir) if output_dir else \
              PROJECT_ROOT / "04_REPORTS" / "coal_export_report" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    click.echo("Querying coal_analytics.duckdb...")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        d = load_data(con)
    finally:
        con.close()

    click.echo("Building maps...")
    import importlib.util as _ilu
    _map_spec = _ilu.spec_from_file_location("coal_trade_map", SCRIPT_DIR / "build_coal_trade_map.py")
    _map_mod  = _ilu.module_from_spec(_map_spec)
    _map_spec.loader.exec_module(_map_mod)

    try:
        _flows  = _map_mod.load_flows()
        _mines  = _map_mod.load_mines()
        _flow_full = _map_mod.build_global_html(_flows)
        _mine_full = _map_mod.build_origins_html(_mines)
        _flow_card, _flow_js = _extract_map_inline(_flow_full)
        _mine_card, _mine_js = _extract_map_inline(_mine_full)
        flow_map_block = (
            '<div class="map-inline-wrap">' + _flow_card + '</div>\n'
            '<script>(function() {\n' + _flow_js + '\n})();</script>'
        )
        mine_map_block = (
            '<div class="map-inline-wrap">' + _mine_card + '</div>\n'
            '<script>(function() {\n' + _mine_js + '\n})();</script>'
        )
    except Exception as e:
        click.echo(f"  Warning: map build failed ({e}) — maps will be omitted", err=True)
        flow_map_block = ''
        mine_map_block = ''

    photo_b64 = ''
    if PHOTO_PATH.exists():
        photo_b64 = base64.b64encode(PHOTO_PATH.read_bytes()).decode('ascii')
        click.echo(f"  Photo embedded: {PHOTO_PATH.name} ({PHOTO_PATH.stat().st_size//1024} KB)")
        # Write a standalone copy to output dir (useful for og:image hosting)
        cover_img_out = out_dir / PHOTO_PATH.name
        cover_img_out.write_bytes(PHOTO_PATH.read_bytes())
        click.echo(f"  Cover image saved: {cover_img_out.name}")
    else:
        click.echo(f"  Photo not found at {PHOTO_PATH} — placeholder used", err=True)

    click.echo("Rendering HTML...")
    html = build_html(d, flow_map_block=flow_map_block, mine_map_block=mine_map_block,
                      photo_b64=photo_b64, og_image_url=og_image_url)

    out_file = out_dir / f"usec_coal_2025_year_in_review_{TODAY}.html"
    out_file.write_text(html, encoding='utf-8')

    size_kb = out_file.stat().st_size / 1024
    click.echo(f"\n  Report: {out_file}")
    click.echo(f"  Size:   {size_kb:.0f} KB")
    click.echo(f"  Style:  OceanDatum dark glassmorphism")
    click.echo(f"  Focus:  2025 Year in Review — narrative-first")

    if open_browser:
        import webbrowser
        webbrowser.open(out_file.as_uri())


if __name__ == '__main__':
    main()
