#!/usr/bin/env python3
"""
build_lower_miss_report.py
Lower Mississippi River Grain Export Elevator Intelligence Report — 2025
Generates two HTML files from DuckDB / FGIS / Southport Agencies data.
Run from: 03_COMMODITY_MODULES/grain/
  python3 src/build_lower_miss_report.py
"""

import sys, os, json, math, re, tempfile, base64
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
import folium
from folium.plugins import MeasureControl

# ─── PATHS ───────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
GRAIN_DIR    = SCRIPT_DIR.parent
PROJECT_ROOT = GRAIN_DIR.parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "analytics.duckdb"
OUTPUT_DIR   = PROJECT_ROOT / "04_REPORTS" / "presentations"
OUTPUT_MAIN  = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025.html"
OUTPUT_INT   = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025_INTERNAL.html"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BUILD_DATE = datetime.now().strftime("%B %d, %Y")

# ─── TERMINAL METADATA ────────────────────────────────────────────────────────
TERMINALS = [
    {"key": "MGMT",               "display": "MGMT / Associated Terminals", "operator": "Associated Terminals",  "mile": 57.8,  "bank": "RDB", "cap": "N/A (Floating)",    "spouts": "1 (float)", "lat": 29.6346, "lon": -89.9272, "color": "#607D8B"},
    {"key": "CHS MYRTLE GROVE",   "display": "CHS Myrtle Grove",            "operator": "CHS, Inc.",             "mile": 61.5,  "bank": "RDB", "cap": "6,464,000 bu",      "spouts": 4,           "lat": 29.6729, "lon": -89.9612, "color": "#388E3C"},
    {"key": "CARGILL WESTWEGO",   "display": "Cargill Westwego",            "operator": "Cargill, Inc.",         "mile": 103.0, "bank": "RDB", "cap": "N/A",               "spouts": 6,           "lat": 29.9373, "lon": -90.1391, "color": "#C62828"},
    {"key": "ADM WOOD BUOYS",     "display": "ADM Wood Buoys",              "operator": "ADM Grain Co.",         "mile": 110.0, "bank": "RDB", "cap": "N/A (Midstream)",   "spouts": "1 (float)", "lat": 29.9350, "lon": -90.2400, "color": "#1565C0"},
    {"key": "ADM AMA",            "display": "ADM Ama",                     "operator": "ADM Grain Co.",         "mile": 117.6, "bank": "RDB", "cap": "5,500,000 bu",      "spouts": 4,           "lat": 29.9433, "lon": -90.3133, "color": "#1565C0"},
    {"key": "BUNGE DESTREHAN",    "display": "Bunge Destrehan",             "operator": "Bunge, Ltd.",           "mile": 120.0, "bank": "LDB", "cap": "N/A",               "spouts": "N/A",       "lat": 29.9400, "lon": -90.3520, "color": "#6A1B9A"},
    {"key": "ADM DESTREHAN",      "display": "ADM Destrehan",               "operator": "ADM Grain Co.",         "mile": 120.6, "bank": "LDB", "cap": "5,500,000 bu",      "spouts": 7,           "lat": 29.9380, "lon": -90.3585, "color": "#1565C0"},
    {"key": "COOPER DARROW",      "display": "Cooper / Darrow Buoy",        "operator": "Cooper Consolidated",   "mile": 133.0, "bank": "LDB", "cap": "N/A (Midstream)",   "spouts": "1 (float)", "lat": 30.0465, "lon": -90.4798, "color": "#607D8B"},
    {"key": "ADM RESERVE",        "display": "ADM Reserve",                 "operator": "ADM Grain Co.",         "mile": 139.1, "bank": "LDB", "cap": "3,500,000 bu",      "spouts": 3,           "lat": 30.0513, "lon": -90.5762, "color": "#1565C0"},
    {"key": "CARGILL RESERVE",    "display": "Cargill Reserve (Terre Haute)","operator": "Cargill, Inc.",        "mile": 139.6, "bank": "LDB", "cap": "N/A",               "spouts": 4,           "lat": 30.0500, "lon": -90.5843, "color": "#C62828"},
    {"key": "ZEN-NOH CONVENT",    "display": "Zen-Noh Convent",             "operator": "Zen-Noh Grain Corp.",   "mile": 163.8, "bank": "LDB", "cap": "4,200,000 bu",      "spouts": 4,           "lat": 30.0630, "lon": -90.8770, "color": "#E65100"},
    {"key": "MILE 228.5 (6.9MBU)","display": "LDC Port Allen",             "operator": "Louis Dreyfus Corp.",   "mile": 229.2, "bank": "RDB", "cap": "6,900,000 bu",      "spouts": 5,           "lat": 30.4390, "lon": -91.1967, "color": "#00838F"},
]

TERM_KEY_MAP = {t["key"]: t for t in TERMINALS}

# Country centroids for world trade flow map
COUNTRY_CENTROIDS = {
    "MEXICO":        (23.6,  -102.6), "CHINA":         (35.8,   104.2),
    "COLOMBIA":      (4.6,   -74.1),  "JAPAN":         (36.2,   138.3),
    "EGYPT":         (26.8,   30.8),  "SPAIN":         (40.5,   -3.7),
    "GERMANY":       (51.2,   10.5),  "GUATEMALA":     (15.8,  -90.2),
    "DOMINICN REP":  (18.7,  -70.2),  "MOROCCO":       (31.8,   -7.1),
    "HONDURAS":      (15.2,  -86.2),  "EL SALVADOR":   (13.8,  -88.9),
    "NICARAGUA":     (12.9,  -85.2),  "COSTA RICA":    (9.7,   -83.8),
    "ITALY":         (41.9,   12.5),  "PORTUGAL":      (39.4,   -8.2),
    "NETHERLANDS":   (52.1,    5.3),  "PANAMA":        (8.5,   -80.8),
    "ISRAEL":        (31.0,   35.0),  "INDONESIA":     (-0.8,  113.9),
    "VIETNAM":       (14.1,  108.3),  "TAIWAN":        (23.7,  120.9),
    "S. KOREA":      (36.5,  127.9),  "BANGLADESH":    (23.7,   90.4),
    "PAKISTAN":      (30.4,   69.3),  "TURKEY":        (39.9,   32.9),
    "ALGERIA":       (28.0,    1.7),  "TUNISIA":       (34.0,    9.0),
    "VENEZUELA":     (6.4,   -66.6),  "ECUADOR":       (-1.8,  -78.2),
    "CHILE":         (-35.7, -71.5),  "S.AFRICA":      (-30.6,  22.9),
    "FRANCE":        (46.2,    2.2),  "IRELAND":       (53.4,   -8.2),
    "UNITED KINGDOM":(54.4,   -2.0),  "SAUDI ARABIA":  (24.0,   45.0),
    "NEW ZEALAND":   (-40.9, 174.9),  "EUROPORT":      (51.9,    4.5),
    "EUROPORTS":     (51.9,    4.5),  "DOM REP":       (18.7,  -70.2),
    "S. AFRICA":     (-30.6,  22.9),
}

# Commodity colors for charts
COMM_COLORS = {
    "YSB":     "#F9A825", "CORN":    "#FDD835",
    "SBM":     "#8D6E63", "WHT":     "#D4AC0D",
    "DDGS":    "#FF8F00", "OTHER":   "#90A4AE",
    "UNKNOWN": "#CFD8DC",
}

# ─── DATABASE QUERIES ────────────────────────────────────────────────────────
def run_queries(con):
    """Run all DuckDB queries and return dict of DataFrames."""
    q = {}

    q["loading_stats"] = con.execute("""
        SELECT terminal_name, COUNT(*) loading_records,
               COUNT(DISTINCT vessel_name) unique_vessels,
               ROUND(AVG(mt_numeric),0) avg_mt,
               ROUND(MEDIAN(mt_numeric),0) median_mt,
               ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mt_numeric),0) p25_mt,
               ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY mt_numeric),0) p75_mt,
               ROUND(SUM(mt_numeric)/1000,0) total_mt_k
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING'
        GROUP BY terminal_name ORDER BY loading_records DESC
    """).fetchdf()

    q["destinations"] = con.execute("""
        SELECT terminal_name, destination, COUNT(*) cnt
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING'
          AND destination IS NOT NULL AND destination != ''
        GROUP BY 1,2 ORDER BY 1, cnt DESC
    """).fetchdf()

    q["commodity_mix"] = con.execute("""
        SELECT terminal_name,
               CASE WHEN commodity_code LIKE '%YSB%' THEN 'YSB'
                    WHEN commodity_code LIKE '%CORN%' THEN 'CORN'
                    WHEN commodity_code LIKE '%WHT%' THEN 'WHT'
                    WHEN commodity_code LIKE '%SBM%' THEN 'SBM'
                    WHEN commodity_code LIKE '%DDGS%' THEN 'DDGS'
                    WHEN commodity_code IS NULL THEN 'UNKNOWN'
                    ELSE 'OTHER' END AS primary_comm,
               COUNT(*) cnt
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING'
        GROUP BY 1,2 ORDER BY 1, cnt DESC
    """).fetchdf()

    q["delay_stats"] = con.execute("""
        SELECT terminal_name,
               ROUND(AVG(delay_days_min),1) avg_delay_min,
               ROUND(AVG(delay_days_max),1) avg_delay_max
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING' AND delay_days_min IS NOT NULL
        GROUP BY terminal_name
    """).fetchdf()

    q["queue_wait"] = con.execute("""
        WITH eta AS (
            SELECT terminal_name, vessel_name, MIN(report_date) first_eta
            FROM grain_southport_lineup
            WHERE region='MISS_RIVER' AND datepart('year', report_date)=2025
              AND status_type='ETA'
            GROUP BY 1, 2
        ),
        loading AS (
            SELECT terminal_name, vessel_name, MIN(report_date) first_loading
            FROM grain_southport_lineup
            WHERE region='MISS_RIVER' AND datepart('year', report_date)=2025
              AND status_type='LOADING'
            GROUP BY 1, 2
        )
        SELECT e.terminal_name, COUNT(*) n,
               ROUND(MEDIAN(DATEDIFF('day', e.first_eta, l.first_loading)),1) median_wait
        FROM eta e
        JOIN loading l ON e.terminal_name=l.terminal_name
          AND e.vessel_name=l.vessel_name
        WHERE l.first_loading >= e.first_eta
          AND DATEDIFF('day', e.first_eta, l.first_loading) <= 30
        GROUP BY e.terminal_name
    """).fetchdf()

    q["load_duration"] = con.execute("""
        WITH vl AS (
            SELECT terminal_name, vessel_name,
                   COUNT(DISTINCT report_date) loading_days
            FROM grain_southport_lineup
            WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
              AND status_type='LOADING'
            GROUP BY 1, 2
        )
        SELECT terminal_name,
               ROUND(MEDIAN(loading_days),1) median_load_days
        FROM vl GROUP BY terminal_name
    """).fetchdf()

    q["all_cargo_sizes"] = con.execute("""
        SELECT mt_numeric, terminal_name
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING' AND mt_numeric IS NOT NULL
          AND mt_numeric > 5000
        ORDER BY mt_numeric
    """).fetchdf()

    # FGIS queries
    q["fgis_overview"] = con.execute("""
        SELECT COUNT(*) total_certs, COUNT(DISTINCT vessel) vessels,
               ROUND(SUM(metric_ton)/1000000,1) total_mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
    """).fetchdf()

    q["fgis_grain_mix"] = con.execute("""
        SELECT grain, COUNT(*) certs, ROUND(SUM(metric_ton)/1000000,2) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
        GROUP BY grain ORDER BY mt_m DESC
    """).fetchdf()

    q["fgis_destinations"] = con.execute("""
        SELECT destination, COUNT(*) certs, ROUND(SUM(metric_ton)/1000000,2) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
        GROUP BY destination ORDER BY mt_m DESC LIMIT 25
    """).fetchdf()

    q["fgis_monthly"] = con.execute("""
        SELECT datepart('month', cert_date) AS mo, grain,
               ROUND(SUM(metric_ton)/1000000,3) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
        GROUP BY 1, 2 ORDER BY 1, mt_m DESC
    """).fetchdf()

    q["fgis_quality"] = con.execute("""
        SELECT grain,
               ROUND(AVG(moisture_avg),2) moisture,
               ROUND(AVG(fm_pct),2) fm,
               ROUND(AVG(protein_avg),2) protein,
               ROUND(AVG(test_weight),2) test_wt,
               COUNT(*) n
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND moisture_avg IS NOT NULL
        GROUP BY grain ORDER BY n DESC
    """).fetchdf()

    q["fgis_grades"] = con.execute("""
        SELECT grain, grade, COUNT(*) certs, ROUND(SUM(metric_ton)/1000000,2) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
        GROUP BY 1,2 ORDER BY 1, mt_m DESC
    """).fetchdf()

    q["fgis_top_ships"] = con.execute("""
        SELECT vessel, grain, destination, ROUND(MAX(metric_ton),0) mt,
               MIN(cert_date) cert_date
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND metric_ton > 50000
        GROUP BY vessel, grain, destination
        ORDER BY mt DESC LIMIT 25
    """).fetchdf()

    return q


def build_terminal_analytics(q):
    """Combine query results into per-terminal analytics dict."""
    ta = {}

    ls = q["loading_stats"].set_index("terminal_name")
    ds = q["delay_stats"].set_index("terminal_name")
    qw = q["queue_wait"].set_index("terminal_name")
    ld = q["load_duration"].set_index("terminal_name")

    for t in TERMINALS:
        key = t["key"]
        a = {}

        if key in ls.index:
            row = ls.loc[key]
            a["loading_records"]  = int(row["loading_records"])
            a["unique_vessels"]   = int(row["unique_vessels"])
            a["avg_mt"]           = int(row["avg_mt"]) if pd.notna(row["avg_mt"]) else None
            a["median_mt"]        = int(row["median_mt"]) if pd.notna(row["median_mt"]) else None
            a["p25_mt"]           = int(row["p25_mt"]) if pd.notna(row["p25_mt"]) else None
            a["p75_mt"]           = int(row["p75_mt"]) if pd.notna(row["p75_mt"]) else None
            a["total_mt_k"]       = int(row["total_mt_k"]) if pd.notna(row["total_mt_k"]) else 0
        else:
            a.update({"loading_records": 0, "unique_vessels": 0, "avg_mt": None,
                      "median_mt": None, "p25_mt": None, "p75_mt": None, "total_mt_k": 0})

        if key in ds.index:
            row = ds.loc[key]
            a["delay_min"] = float(row["avg_delay_min"]) if pd.notna(row["avg_delay_min"]) else None
            a["delay_max"] = float(row["avg_delay_max"]) if pd.notna(row["avg_delay_max"]) else None
        else:
            a["delay_min"] = None
            a["delay_max"] = None

        a["median_wait"] = float(qw.loc[key, "median_wait"]) if key in qw.index else None
        a["median_load"] = float(ld.loc[key, "median_load_days"]) if key in ld.index else None

        # Top 5 destinations
        dest_df = q["destinations"]
        t_dest = dest_df[dest_df["terminal_name"] == key].head(5)
        a["top_dests"] = list(zip(t_dest["destination"], t_dest["cnt"].astype(int)))

        # Commodity mix
        comm_df = q["commodity_mix"]
        t_comm = comm_df[comm_df["terminal_name"] == key]
        total_c = t_comm["cnt"].sum()
        a["comm_mix"] = {
            row["primary_comm"]: round(int(row["cnt"]) / total_c * 100, 1)
            for _, row in t_comm.iterrows()
        } if total_c > 0 else {}

        # Vessel class based on median MT
        med = a.get("median_mt") or 0
        if med >= 65000:
            a["vessel_class"] = "Capesize"
        elif med >= 40000:
            a["vessel_class"] = "Panamax"
        elif med >= 25000:
            a["vessel_class"] = "Handymax / Supramax"
        else:
            a["vessel_class"] = "Handymax"

        ta[key] = a

    return ta


# ─── FOLIUM MAPS ─────────────────────────────────────────────────────────────
def map_to_b64_iframe(m, height=520):
    """Save Folium map to temp file, encode as base64, return iframe HTML."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        m.save(f.name)
        fname = f.name
    with open(fname, "r", encoding="utf-8") as f:
        html_str = f.read()
    os.unlink(fname)
    b64 = base64.b64encode(html_str.encode("utf-8")).decode("ascii")
    return (f'<iframe src="data:text/html;base64,{b64}" '
            f'style="width:100%;height:{height}px;border:none;border-radius:8px;"></iframe>')


def build_river_map(terminal_analytics):
    m = folium.Map(location=[29.95, -90.5], zoom_start=8,
                   tiles="CartoDB positron")
    folium.TileLayer("Esri.WorldImagery", name="Satellite").add_to(m)
    folium.TileLayer("CartoDB positron", name="Light (default)").add_to(m)
    folium.LayerControl(position="topright").add_to(m)
    MeasureControl(position="bottomleft").add_to(m)

    for t in TERMINALS:
        key  = t["key"]
        ta   = terminal_analytics.get(key, {})
        disp = t["display"]
        med  = ta.get("median_mt")
        med_str = f"{med:,}" if med else "N/A"
        lv   = ta.get("loading_records", 0)
        vc   = ta.get("vessel_class", "N/A")
        top1 = ta["top_dests"][0][0] if ta.get("top_dests") else "N/A"

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;min-width:200px;padding:4px">
          <b style="color:#0D1B2A;font-size:13px">{disp}</b><br>
          <span style="color:#555;font-size:11px">{t['operator']}</span><hr style="margin:4px 0">
          <table style="font-size:11px;width:100%">
            <tr><td><b>Mile AHP</b></td><td>MM {t['mile']}</td></tr>
            <tr><td><b>Bank</b></td><td>{t['bank']}</td></tr>
            <tr><td><b>Capacity</b></td><td>{t['cap']}</td></tr>
            <tr><td><b>Spouts</b></td><td>{t['spouts']}</td></tr>
            <tr><td><b>Vessel Class</b></td><td>{vc}</td></tr>
            <tr><td><b>2025 Loads</b></td><td>{lv:,} records</td></tr>
            <tr><td><b>Median MT</b></td><td>{med_str} MT</td></tr>
            <tr><td><b>Top Destination</b></td><td>{top1}</td></tr>
          </table>
        </div>"""

        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=10,
            color="#FFFFFF",
            weight=2,
            fill=True,
            fill_color=t["color"],
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"MM {t['mile']} — {disp}",
        ).add_to(m)

        folium.Marker(
            location=[t["lat"] + 0.015, t["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:700;color:#0D1B2A;'
                     f'white-space:nowrap;text-shadow:1px 1px 2px white,-1px -1px 2px white">'
                     f'MM {t["mile"]}</div>',
                icon_size=(80, 14), icon_anchor=(0, 0)),
        ).add_to(m)

    # River label
    folium.Marker(
        location=[29.78, -89.98],
        icon=folium.DivIcon(
            html='<div style="font-size:11px;font-weight:700;color:#1565C0;'
                 'white-space:nowrap;letter-spacing:1px">MISSISSIPPI RIVER</div>',
            icon_size=(160, 16)),
    ).add_to(m)
    return m


def gc_arc(lat1, lon1, lat2, lon2, n=40):
    """Compute n intermediate points for a great-circle arc."""
    d2r = math.pi / 180
    lat1, lon1, lat2, lon2 = lat1*d2r, lon1*d2r, lat2*d2r, lon2*d2r
    d = 2 * math.asin(math.sqrt(
        math.sin((lat2-lat1)/2)**2 +
        math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2))
    if d < 1e-6:
        return [(lat1/d2r, lon1/d2r), (lat2/d2r, lon2/d2r)]
    pts = []
    for i in range(n+1):
        f = i / n
        A = math.sin((1-f)*d) / math.sin(d)
        B = math.sin(f*d) / math.sin(d)
        x = A*math.cos(lat1)*math.cos(lon1) + B*math.cos(lat2)*math.cos(lon2)
        y = A*math.cos(lat1)*math.sin(lon1) + B*math.cos(lat2)*math.sin(lon2)
        z = A*math.sin(lat1) + B*math.sin(lat2)
        lat = math.atan2(z, math.sqrt(x**2+y**2)) / d2r
        lon = math.atan2(y, x) / d2r
        pts.append((lat, lon))
    return pts


def build_world_map(fgis_dests):
    m = folium.Map(location=[20.0, -30.0], zoom_start=2,
                   tiles="CartoDB positron")
    origin = (29.3, -89.5)  # Mouth of Mississippi

    max_mt = fgis_dests["mt_m"].max()
    shown = 0
    for _, row in fgis_dests.iterrows():
        dest = row["destination"]
        mt   = row["mt_m"]
        certs = int(row["certs"])
        if dest not in COUNTRY_CENTROIDS:
            continue
        lat, lon = COUNTRY_CENTROIDS[dest]
        weight = max(1, int(8 * math.log(1 + mt) / math.log(1 + max_mt)))
        arc_pts = gc_arc(origin[0], origin[1], lat, lon, n=50)
        folium.PolyLine(
            locations=arc_pts,
            weight=weight,
            color="#F0A500",
            opacity=0.65,
            tooltip=f"{dest}: {mt:.1f}M MT — {certs:,} certs",
        ).add_to(m)
        folium.CircleMarker(
            location=[lat, lon],
            radius=6 + weight,
            color="#FFFFFF",
            weight=1.5,
            fill=True,
            fill_color="#C62828",
            fill_opacity=0.85,
            popup=folium.Popup(
                f"<b>{dest}</b><br>{mt:.2f}M MT<br>{certs:,} certificates", max_width=180),
            tooltip=f"{dest}: {mt:.1f}M MT",
        ).add_to(m)
        shown += 1

    # Origin marker
    folium.Marker(
        location=origin,
        icon=folium.Icon(color="blue", icon="ship", prefix="fa"),
        popup="Lower Mississippi River Elevators",
        tooltip="Lower Mississippi River (Origin)",
    ).add_to(m)
    print(f"  World map: {shown} destination countries plotted")
    return m


# ─── HTML COMPONENTS ─────────────────────────────────────────────────────────
def fmt_num(n, suffix=""):
    if n is None:
        return "N/A"
    return f"{n:,.0f}{suffix}"


def comm_donut_js(canvas_id, comm_mix):
    """Return Chart.js script for a commodity doughnut chart."""
    order  = ["YSB", "CORN", "SBM", "WHT", "DDGS", "OTHER", "UNKNOWN"]
    labels, values, colors = [], [], []
    for k in order:
        if k in comm_mix:
            labels.append({"YSB": "Soybeans", "CORN": "Corn", "SBM": "SBM",
                           "WHT": "Wheat", "DDGS": "DDGS", "OTHER": "Other",
                           "UNKNOWN": "Filed/Unspec"}[k])
            values.append(comm_mix[k])
            colors.append(COMM_COLORS[k])
    if not values:
        return ""
    lj = json.dumps(labels)
    vj = json.dumps(values)
    cj = json.dumps(colors)
    return f"""
new Chart(document.getElementById('{canvas_id}'), {{
  type: 'doughnut',
  data: {{ labels: {lj}, datasets: [{{
    data: {vj}, backgroundColor: {cj}, borderWidth: 1, borderColor: '#fff'
  }}]}},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins: {{
      legend: {{ position:'right', labels:{{ font:{{ size:10 }}, boxWidth:12, padding:6 }} }},
      tooltip: {{ callbacks: {{ label: function(c){{ return c.label+': '+c.raw.toFixed(1)+'%'; }} }} }}
    }}
  }}
}});"""


def build_terminal_card(t, ta, card_idx):
    key   = t["key"]
    cid   = "comm_" + re.sub(r"[^a-z0-9]", "_", key.lower())
    disp  = t["display"]
    op    = t["operator"]
    mile  = t["mile"]
    bank  = t["bank"]
    cap   = t["cap"]
    spout = t["spouts"]
    vc    = ta.get("vessel_class", "N/A")
    lv    = ta.get("loading_records", 0)
    uv    = ta.get("unique_vessels", 0)
    med   = ta.get("median_mt")
    p25   = ta.get("p25_mt")
    p75   = ta.get("p75_mt")
    wait  = ta.get("median_wait")
    load  = ta.get("median_load")
    dmin  = ta.get("delay_min")
    dmax  = ta.get("delay_max")
    cm    = ta.get("comm_mix", {})

    # Top destinations HTML
    dest_rows = ""
    max_cnt = ta["top_dests"][0][1] if ta.get("top_dests") else 1
    for dest, cnt in (ta.get("top_dests") or [])[:5]:
        pct = cnt / max_cnt * 100
        dest_rows += f"""
        <div style="margin-bottom:4px">
          <div style="display:flex;justify-content:space-between;font-size:11px">
            <span>{dest}</span><span style="color:#666">{cnt}</span>
          </div>
          <div style="background:#e9ecef;border-radius:3px;height:6px">
            <div style="background:{t['color']};width:{pct:.0f}%;height:100%;border-radius:3px"></div>
          </div>
        </div>"""

    # Cargo size bar
    if med and p25 and p75:
        bar_min, bar_max = 15000, 80000
        def ppos(v): return max(0, min(100, (v - bar_min) / (bar_max - bar_min) * 100))
        p25p, medp, p75p = ppos(p25), ppos(med), ppos(p75)
        iqr_left  = p25p
        iqr_width = p75p - p25p
        size_bar = f"""
        <div style="position:relative;height:18px;background:#e9ecef;border-radius:4px;margin:6px 0">
          <div style="position:absolute;left:{iqr_left:.1f}%;width:{iqr_width:.1f}%;
               height:100%;background:{t['color']};opacity:0.4;border-radius:3px"></div>
          <div style="position:absolute;left:{medp:.1f}%;width:3px;height:100%;
               background:{t['color']};border-radius:2px"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:#666">
          <span>15K MT</span>
          <span style="color:{t['color']};font-weight:700">{med:,} MT median</span>
          <span>80K MT</span>
        </div>"""
    else:
        size_bar = '<div style="color:#999;font-size:11px;padding:6px 0">Cargo size data limited</div>'

    # Operational badges
    def badge(label, value, color="#495057"):
        return (f'<div style="background:#f1f3f5;border-radius:6px;padding:6px 8px;'
                f'text-align:center;min-width:60px">'
                f'<div style="font-size:10px;color:#666">{label}</div>'
                f'<div style="font-size:13px;font-weight:700;color:{color}">{value}</div></div>')

    wait_str = f"{wait:.0f}d" if wait else "N/A"
    load_str = f"{load:.0f}d" if load else "N/A"
    delay_str = f"{dmin:.0f}–{dmax:.0f}d" if dmin is not None and dmax is not None else "N/A"

    # Tier label
    mt_total = ta.get("total_mt_k", 0) or 0
    if mt_total >= 6000 or lv >= 300:
        tier_badge = '<span style="background:#1565C0;color:white;font-size:10px;border-radius:4px;padding:2px 7px">Tier 1 — Major</span>'
    elif mt_total >= 2000 or lv >= 130:
        tier_badge = '<span style="background:#388E3C;color:white;font-size:10px;border-radius:4px;padding:2px 7px">Tier 2 — Active</span>'
    else:
        tier_badge = '<span style="background:#607D8B;color:white;font-size:10px;border-radius:4px;padding:2px 7px">Tier 3 — Specialty</span>'

    left_border = f"border-left:4px solid {t['color']}"

    return f"""
<div class="terminal-card" id="t_{card_idx}" style="{left_border}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
    <div>
      <h3 style="margin:0;font-size:17px;color:#0D1B2A">{disp}</h3>
      <span style="color:#555;font-size:13px">{op}</span>
      &nbsp;&nbsp;{tier_badge}
    </div>
    <div style="text-align:right;font-size:12px;color:#666">
      Mile Marker <b style="font-size:15px;color:{t['color']}">{mile}</b> AHP &nbsp;|&nbsp; {bank}
      <br>Cap: <b>{cap}</b> &nbsp;|&nbsp; Spouts: <b>{spout}</b>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:16px">
    <!-- Left column: cargo size + destinations -->
    <div>
      <div style="font-size:11px;font-weight:700;color:#666;letter-spacing:.5px;margin-bottom:4px">
        CARGO SIZE DISTRIBUTION (P25 / MEDIAN / P75)
      </div>
      {size_bar}

      <div style="margin-top:14px;font-size:11px;font-weight:700;color:#666;
           letter-spacing:.5px;margin-bottom:6px">TOP DESTINATIONS</div>
      {dest_rows if dest_rows else '<div style="color:#999;font-size:11px">No destination data</div>'}
    </div>

    <!-- Right column: donut + op stats -->
    <div>
      <div style="font-size:11px;font-weight:700;color:#666;letter-spacing:.5px;margin-bottom:4px">
        COMMODITY MIX (2025 LOADING)
      </div>
      <div style="height:130px">
        <canvas id="{cid}"></canvas>
      </div>
      <div style="margin-top:12px;font-size:11px;font-weight:700;color:#666;
           letter-spacing:.5px;margin-bottom:8px">OPERATIONAL PROFILE</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        {badge("Vessels", f"{uv:,}", t['color'])}
        {badge("Loads", f"{lv:,}", t['color'])}
        {badge("Vessel Class", vc.split("/")[0].strip(), "#333")}
        {badge("Queue Wait", wait_str, "#E65100")}
        {badge("Load Time", load_str, "#1565C0")}
        {badge("Dock Delay", delay_str, "#6A1B9A")}
      </div>
    </div>
  </div>
</div>
""", f"  {comm_donut_js(cid, cm)}"


# ─── MAIN HTML BUILDER ───────────────────────────────────────────────────────
def build_main_html(q, ta, river_map_html, world_map_html):
    fgis_ov  = q["fgis_overview"].iloc[0]
    total_mt = float(fgis_ov["total_mt_m"])
    total_cv = int(fgis_ov["total_certs"])
    fgis_v   = int(fgis_ov["vessels"])
    ls       = q["loading_stats"]
    fgis_gm  = q["fgis_grain_mix"]
    fgis_d   = q["fgis_destinations"]
    fgis_mo  = q["fgis_monthly"]
    fgis_q   = q["fgis_quality"]
    fgis_g   = q["fgis_grades"]
    fgis_top = q["fgis_top_ships"]

    # ── Hero KPI cards
    hero_cards = f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:32px">
      <div class="kpi-card">
        <div class="kpi-num">{total_mt:.1f}<span class="kpi-unit"> MMT</span></div>
        <div class="kpi-label">Certified Export Volume</div>
        <div class="kpi-sub">FGIS, Jan–Sep 2025</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-num">{fgis_v:,}</div>
        <div class="kpi-label">Certificated Vessels</div>
        <div class="kpi-sub">Unique vessels with FGIS certs</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-num">12</div>
        <div class="kpi-label">Terminals Profiled</div>
        <div class="kpi-sub">Lower Miss R. — MM 57 to MM 229</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-num">25+</div>
        <div class="kpi-label">Export Markets</div>
        <div class="kpi-sub">Mexico, China, Colombia top 3</div>
      </div>
    </div>
    <div style="margin-top:24px;display:flex;gap:16px;flex-wrap:wrap">
      <div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:10px 18px;font-size:13px">
        <b>Primary Grain:</b> Corn {fgis_gm[fgis_gm['grain']=='CORN']['mt_m'].values[0]:.1f}M MT
        &nbsp;|&nbsp; Soybeans {fgis_gm[fgis_gm['grain']=='SOYBEANS']['mt_m'].values[0]:.1f}M MT
        &nbsp;|&nbsp; Wheat {fgis_gm[fgis_gm['grain']=='WHEAT']['mt_m'].values[0]:.1f}M MT
      </div>
      <div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:10px 18px;font-size:13px">
        <b>Top Markets:</b> Mexico · China · Colombia · Japan · Egypt
      </div>
    </div>"""

    # ── Terminal profile cards
    terminal_cards_html = ""
    chart_scripts = []
    for idx, t in enumerate(TERMINALS):
        card_html, chart_js = build_terminal_card(t, ta[t["key"]], idx)
        terminal_cards_html += card_html
        chart_scripts.append(chart_js)

    # ── Vessel size histogram data (5K MT bins)
    cargo_df = q["all_cargo_sizes"]
    bins = list(range(5000, 90001, 5000))
    labels_h = [f"{b//1000}K" for b in bins[:-1]]
    counts_h = [int(((cargo_df["mt_numeric"] >= bins[i]) & (cargo_df["mt_numeric"] < bins[i+1])).sum())
                for i in range(len(bins)-1)]

    # ── Loading records ranking (horizontal bar)
    ls_sorted = ls.sort_values("loading_records", ascending=True)
    rank_labels = [TERM_KEY_MAP.get(k, {}).get("display", k)
                   for k in ls_sorted["terminal_name"]]
    rank_vals   = ls_sorted["loading_records"].tolist()
    rank_colors = [TERM_KEY_MAP.get(k, {}).get("color", "#607D8B")
                   for k in ls_sorted["terminal_name"]]

    # ── Queue wait chart
    qw = q["queue_wait"].sort_values("median_wait", ascending=False)
    qw_labels = [TERM_KEY_MAP.get(k, {}).get("display", k)
                 for k in qw["terminal_name"]]
    qw_vals   = qw["median_wait"].tolist()

    # ── Loading duration chart
    ld = q["load_duration"].sort_values("median_load_days", ascending=False)
    ld_labels = [TERM_KEY_MAP.get(k, {}).get("display", k)
                 for k in ld["terminal_name"]]
    ld_vals   = ld["median_load_days"].tolist()

    # ── Monthly throughput (stacked line) — pivot by grain
    grains_shown = ["CORN", "SOYBEANS", "WHEAT"]
    months = list(range(1, 10))
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep"]
    monthly_datasets = []
    g_colors = {"CORN": "#FDD835", "SOYBEANS": "#F9A825", "WHEAT": "#D4AC0D"}
    for g in grains_shown:
        gdf = fgis_mo[fgis_mo["grain"] == g].set_index("mo")
        vals = [round(float(gdf.loc[m, "mt_m"]) if m in gdf.index else 0, 3) for m in months]
        monthly_datasets.append({"label": g.capitalize(), "data": vals,
                                  "borderColor": g_colors[g], "backgroundColor": g_colors[g] + "33",
                                  "fill": True, "tension": 0.4})

    # ── FGIS destinations for world map section
    top_dest_rows = ""
    for i, (_, row) in enumerate(fgis_d.head(20).iterrows()):
        top_dest_rows += (f"<tr><td>{i+1}</td><td><b>{row['destination']}</b></td>"
                          f"<td>{row['mt_m']:.2f} MMT</td><td>{row['certs']:,}</td></tr>")

    # ── Grade distribution table
    grade_rows = ""
    for grain in ["CORN", "SOYBEANS", "WHEAT"]:
        gdf = fgis_g[fgis_g["grain"] == grain]
        total_g = gdf["mt_m"].sum()
        for _, row in gdf.iterrows():
            pct = row["mt_m"] / total_g * 100 if total_g > 0 else 0
            grade_rows += (f"<tr><td>{grain.capitalize()}</td><td>{row['grade']}</td>"
                           f"<td>{row['mt_m']:.2f} MMT</td>"
                           f"<td>{pct:.1f}%</td><td>{row['certs']:,}</td></tr>")

    # ── Quality table
    qual_rows = ""
    for _, row in fgis_q.iterrows():
        prot_str = "N/A" if pd.isna(row["protein"]) else f"{row['protein']:.1f}%"
        tw_str   = "N/A" if pd.isna(row["test_wt"]) else f"{row['test_wt']:.1f} lb/bu"
        qual_rows += (f"<tr><td><b>{row['grain'].capitalize()}</b></td>"
                      f"<td>{row['moisture']:.1f}%</td>"
                      f"<td>{row['fm']:.2f}%</td>"
                      f"<td>{prot_str}</td>"
                      f"<td>{tw_str}</td>"
                      f"<td>{row['n']:,}</td></tr>")

    # ── Top shipments table
    ship_rows = ""
    for _, row in fgis_top.head(20).iterrows():
        ship_rows += (f"<tr><td><b>{row['vessel']}</b></td>"
                      f"<td>{row['grain'].capitalize()}</td>"
                      f"<td>{row['destination']}</td>"
                      f"<td>{row['mt']:,.0f}</td>"
                      f"<td>{row['cert_date']}</td></tr>")

    # ── Market share (total_mt_k) for pie chart
    ms_labels, ms_vals, ms_colors = [], [], []
    for t in TERMINALS:
        mv = ta[t["key"]].get("total_mt_k", 0) or 0
        if mv > 0:
            ms_labels.append(t["display"])
            ms_vals.append(int(mv))
            ms_colors.append(t["color"])

    # ── Operator legend for river map
    op_legend = ""
    seen_ops = {}
    for t in TERMINALS:
        op = t["operator"]
        if op not in seen_ops:
            seen_ops[op] = t["color"]
    for op, col in seen_ops.items():
        op_legend += (f'<span style="display:inline-flex;align-items:center;gap:5px;'
                      f'margin:4px 8px;font-size:12px">'
                      f'<span style="width:14px;height:14px;border-radius:50%;'
                      f'background:{col};display:inline-block"></span>{op}</span>')

    # Build all Chart.js scripts
    all_scripts = "\n".join(chart_scripts) + f"""

// Vessel size histogram
new Chart(document.getElementById('hist_vessel_size'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(labels_h)},
    datasets: [{{ label: 'Vessel Count', data: {json.dumps(counts_h)},
      backgroundColor: '#1565C0BB', borderColor: '#1565C0', borderWidth: 1 }}]
  }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins: {{ legend:{{ display:false }},
      title:{{ display:true, text:'Cargo Size Distribution — All Terminals 2025', font:{{size:13}} }} }},
    scales: {{
      x: {{ title:{{ display:true, text:'Cargo Size (MT)' }} }},
      y: {{ title:{{ display:true, text:'Loading Records' }} }}
    }}
  }}
}});

// Terminal ranking bar chart
new Chart(document.getElementById('chart_rankings'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(rank_labels)},
    datasets: [{{ label: 'Loading Records', data: {json.dumps(rank_vals)},
      backgroundColor: {json.dumps(rank_colors)}, borderWidth: 0 }}]
  }},
  options: {{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
    plugins: {{ legend:{{ display:false }},
      title:{{ display:true, text:'2025 Loading Records by Terminal', font:{{size:13}} }} }},
    scales: {{ x:{{ title:{{ display:true, text:'Loading Records (daily lineup snapshots)' }} }} }}
  }}
}});

// Queue wait chart
new Chart(document.getElementById('chart_queue'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(qw_labels)},
    datasets: [{{ label: 'Median Wait (days)', data: {json.dumps(qw_vals)},
      backgroundColor: '#E65100BB', borderColor: '#E65100', borderWidth: 1 }}]
  }},
  options: {{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
    plugins: {{ legend:{{ display:false }},
      title:{{ display:true, text:'Median Queue Wait — ETA → Loading (days, ≤30-day window)', font:{{size:13}} }} }},
    scales: {{ x:{{ title:{{ display:true, text:'Days' }} }} }}
  }}
}});

// Loading duration chart
new Chart(document.getElementById('chart_load_dur'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(ld_labels)},
    datasets: [{{ label: 'Median Load Days', data: {json.dumps(ld_vals)},
      backgroundColor: '#1B3A5CBB', borderColor: '#1B3A5C', borderWidth: 1 }}]
  }},
  options: {{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
    plugins: {{ legend:{{ display:false }},
      title:{{ display:true, text:'Median Loading Duration per Vessel (days)', font:{{size:13}} }} }},
    scales: {{ x:{{ title:{{ display:true, text:'Days' }} }} }}
  }}
}});

// Monthly throughput
new Chart(document.getElementById('chart_monthly'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(month_labels)},
    datasets: {json.dumps(monthly_datasets)}
  }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins: {{ title:{{ display:true, text:'Monthly Certified Volume by Grain — FGIS 2025 (Million MT)', font:{{size:13}} }} }},
    scales: {{
      x: {{ title:{{ display:true, text:'Month' }} }},
      y: {{ title:{{ display:true, text:'Million MT' }}, stacked:false }}
    }}
  }}
}});

// Market share pie
new Chart(document.getElementById('chart_mktshare'), {{
  type: 'pie',
  data: {{
    labels: {json.dumps(ms_labels)},
    datasets: [{{ data: {json.dumps(ms_vals)},
      backgroundColor: {json.dumps(ms_colors)}, borderWidth: 1 }}]
  }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins: {{
      title:{{ display:true, text:'Relative Throughput Share (Estimated MT from Lineup)', font:{{size:13}} }},
      legend:{{ position:'right', labels:{{ font:{{ size:10 }}, boxWidth:12 }} }}
    }}
  }}
}});
"""

    # ── Sidebar nav items
    sidebar_items = [
        ("#section-cover",      "Overview"),
        ("#section-river-map",  "River Map"),
        ("#section-terminals",  "Terminal Profiles"),
        ("#section-analytics",  "Vessel Analytics"),
        ("#section-trade",      "Global Trade Flow"),
        ("#section-commodity",  "Commodity Intelligence"),
        ("#section-quality",    "Quality & Certification"),
        ("#section-rankings",   "Terminal Rankings"),
    ]
    nav_links = "".join(
        f'<li><a class="nav-link" href="{href}">{label}</a></li>'
        for href, label in sidebar_items)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lower Mississippi River — Grain Export Elevator Intelligence Report 2025</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
:root{{--navy:#0D1B2A;--navy2:#1B3A5C;--accent:#F0A500;--sidebar-w:248px}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:"Segoe UI",system-ui,sans-serif;background:#F0F2F5;color:#212529}}
.sidebar{{position:fixed;left:0;top:0;width:var(--sidebar-w);height:100vh;
  background:var(--navy);overflow-y:auto;z-index:1000;padding:20px 0;display:flex;flex-direction:column}}
.sidebar-logo{{padding:16px 20px 12px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:8px}}
.sidebar-logo .title{{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:1px;text-transform:uppercase}}
.sidebar-logo .sub{{font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px}}
.nav-link{{display:block;padding:9px 20px;color:rgba(255,255,255,0.72);font-size:13px;
  text-decoration:none;transition:.15s;border-left:3px solid transparent}}
.nav-link:hover,.nav-link.active{{color:#fff;background:rgba(255,255,255,0.08);
  border-left-color:var(--accent)}}
.sidebar-footer{{margin-top:auto;padding:14px 20px;border-top:1px solid rgba(255,255,255,0.1);
  font-size:10px;color:rgba(255,255,255,0.4)}}
.content{{margin-left:var(--sidebar-w)}}
.hero{{background:linear-gradient(135deg,var(--navy) 0%,var(--navy2) 60%,#2a4a7a 100%);
  color:#fff;padding:56px 48px 48px}}
.hero h1{{font-size:26px;font-weight:800;margin:0;line-height:1.3}}
.hero .sub{{font-size:14px;color:rgba(255,255,255,0.65);margin-top:6px}}
.kpi-card{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
  border-radius:12px;padding:18px 14px;text-align:center;backdrop-filter:blur(4px)}}
.kpi-num{{font-size:32px;font-weight:800;color:#fff;line-height:1}}
.kpi-unit{{font-size:18px;font-weight:600}}
.kpi-label{{font-size:12px;color:var(--accent);font-weight:700;margin-top:4px;letter-spacing:.5px;text-transform:uppercase}}
.kpi-sub{{font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px}}
.section{{background:#fff;padding:40px 48px;border-bottom:1px solid #e9ecef}}
.section-alt{{background:#F8F9FA;padding:40px 48px;border-bottom:1px solid #e9ecef}}
.section-title{{font-size:20px;font-weight:800;color:var(--navy);margin-bottom:4px}}
.section-sub{{font-size:13px;color:#666;margin-bottom:24px}}
.terminal-card{{background:#fff;border:1px solid #dee2e6;border-radius:12px;padding:24px;
  margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}}
.chart-box{{position:relative;height:340px}}
.chart-box-sm{{position:relative;height:260px}}
.tbl{{font-size:12px;width:100%}}
.tbl th{{background:#0D1B2A;color:#fff;padding:8px 10px;font-size:11px;letter-spacing:.4px;text-transform:uppercase}}
.tbl td{{padding:7px 10px;border-bottom:1px solid #e9ecef}}
.tbl tr:hover td{{background:#f8f9fa}}
.badge-pill{{font-size:10px;padding:3px 8px;border-radius:20px;font-weight:700}}
@media(max-width:900px){{.sidebar{{width:100%;height:auto;position:relative}}
  .content{{margin-left:0}}}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="sidebar-logo">
    <div class="title">Lower Mississippi River</div>
    <div class="sub">Grain Elevator Intelligence | 2025</div>
  </div>
  <ul style="list-style:none;padding:0;margin:0">
    {nav_links}
  </ul>
  <div class="sidebar-footer">
    Confidential &nbsp;|&nbsp; {BUILD_DATE}
  </div>
</nav>

<!-- CONTENT -->
<main class="content">

<!-- ═══ COVER / HERO ══════════════════════════════════════════════════════ -->
<section class="hero" id="section-cover">
  <p style="font-size:11px;color:rgba(255,255,255,0.45);margin:0 0 12px;letter-spacing:1px;text-transform:uppercase">
    Lower Mississippi River &nbsp;·&nbsp; Export Grain Elevator Intelligence
  </p>
  <h1>Lower Mississippi River<br>Grain Export Elevator Guide</h1>
  <p class="sub">2025 Operational Intelligence &nbsp;·&nbsp; 12 Terminals &nbsp;·&nbsp; MM 57 to MM 229 AHP</p>
  {hero_cards}
</section>

<!-- ═══ RIVER MAP ═════════════════════════════════════════════════════════ -->
<section class="section" id="section-river-map">
  <h2 class="section-title">River Map — Terminal Locations</h2>
  <p class="section-sub">Interactive map of 12 grain export terminals along the Lower Mississippi River.
     Click markers for terminal details. Switch base layer (top-right) for satellite view.</p>
  <div style="margin-bottom:12px;padding:10px 14px;background:#f8f9fa;border-radius:8px;font-size:12px">
    <b>Legend by Operator:</b>&nbsp;{op_legend}
  </div>
  {river_map_html}
</section>

<!-- ═══ TERMINAL PROFILES ═════════════════════════════════════════════════ -->
<section class="section-alt" id="section-terminals">
  <h2 class="section-title">Terminal Profiles</h2>
  <p class="section-sub">Individual profiles for each terminal — river order MM 57 (downstream) to MM 229 (upstream).
     Cargo size bars show P25 / Median / P75 range. Queue wait and loading duration are derived from
     daily lineup position reports.</p>
  {terminal_cards_html}
</section>

<!-- ═══ VESSEL ANALYTICS ══════════════════════════════════════════════════ -->
<section class="section" id="section-analytics">
  <h2 class="section-title">Vessel & Cargo Analytics</h2>
  <p class="section-sub">Fleet-wide vessel size distribution, queue wait times, and loading duration patterns
     across all Lower Mississippi terminals, 2025.</p>
  <div class="row g-4">
    <div class="col-md-6">
      <div class="chart-box"><canvas id="hist_vessel_size"></canvas></div>
    </div>
    <div class="col-md-6">
      <div style="background:#f8f9fa;border-radius:10px;padding:18px">
        <h5 style="font-size:14px;font-weight:700;color:#0D1B2A;margin-bottom:12px">Vessel Class Key</h5>
        <table class="tbl">
          <tr><th>Class</th><th>Cargo Range</th><th>Typical Route</th></tr>
          <tr><td><b>Handymax</b></td><td>25,000 – 39,999 MT</td><td>Short-haul, Caribbean</td></tr>
          <tr><td><b>Supramax</b></td><td>40,000 – 57,999 MT</td><td>Panamax trade lanes</td></tr>
          <tr><td><b>Panamax</b></td><td>58,000 – 79,999 MT</td><td>Transoceanic bulk trades</td></tr>
          <tr><td><b>Capesize</b></td><td>80,000+ MT</td><td>Long-haul, major importers</td></tr>
        </table>
        <div style="margin-top:14px;font-size:12px;color:#666">
          Lower Mississippi Median: <b>~50,000 MT</b> (Panamax/Supramax dominant)<br>
          Lowest-draft terminals (MGMT, Cooper, Wood Buoys) average Handymax.<br>
          ADM Reserve and Zen-Noh Convent achieve highest median cargo weights.
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="chart-box"><canvas id="chart_queue"></canvas></div>
      <div style="font-size:11px;color:#666;margin-top:6px">
        * Queue wait = days from ETA first appearance to first LOADING date, capped at 30 days per voyage cluster.
          Longer waits indicate higher congestion or tighter scheduling windows.
      </div>
    </div>
    <div class="col-md-6">
      <div class="chart-box"><canvas id="chart_load_dur"></canvas></div>
      <div style="font-size:11px;color:#666;margin-top:6px">
        * Loading duration = median consecutive LOADING report days per vessel visit.
          Cooper / Darrow and ADM Wood Buoys show longer load times (midstream float, multi-commodity SBM/DDGS).
      </div>
    </div>
  </div>

  <!-- Top Shipments Table -->
  <h4 style="font-size:16px;font-weight:700;margin:32px 0 12px;color:#0D1B2A">Largest Single Shipments — 2025</h4>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr><th>#</th><th>Vessel</th><th>Grain</th><th>Destination</th><th>Metric Tons</th><th>Cert Date</th></tr>
      {ship_rows}
    </table>
  </div>
  <div style="font-size:11px;color:#888;margin-top:6px">Source: USDA FGIS Certificates, Mississippi R., 2025</div>
</section>

<!-- ═══ GLOBAL TRADE FLOW ═════════════════════════════════════════════════ -->
<section class="section-alt" id="section-trade">
  <h2 class="section-title">Global Trade Flow</h2>
  <p class="section-sub">Certified export volumes from Lower Mississippi River terminals to global markets,
     Jan–Sep 2025. Arc thickness proportional to log(tonnage).</p>
  {world_map_html}
  <h4 style="font-size:16px;font-weight:700;margin:28px 0 12px;color:#0D1B2A">Top 20 Destination Markets</h4>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr><th>#</th><th>Country</th><th>Certified Volume (MMT)</th><th>FGIS Certificates</th></tr>
      {top_dest_rows}
    </table>
  </div>
</section>

<!-- ═══ COMMODITY INTELLIGENCE ════════════════════════════════════════════ -->
<section class="section" id="section-commodity">
  <h2 class="section-title">Commodity Intelligence</h2>
  <p class="section-sub">Monthly FGIS-certified volume by grain type and seasonal patterns, 2025.</p>
  <div class="chart-box" style="height:380px"><canvas id="chart_monthly"></canvas></div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:28px">
    <div style="background:#FFF9C4;border-radius:10px;padding:16px;border-left:4px solid #F9A825">
      <div style="font-weight:800;color:#0D1B2A;font-size:14px">Soybean Season</div>
      <div style="font-size:12px;margin-top:4px;color:#333">
        Peak: <b>January (104M MT)</b><br>
        Harvest flush drives Jan–Mar surge.<br>
        July–Sep wind-down before new crop.
      </div>
    </div>
    <div style="background:#FFFDE7;border-radius:10px;padding:16px;border-left:4px solid #FDD835">
      <div style="font-weight:800;color:#0D1B2A;font-size:14px">Corn Season</div>
      <div style="font-size:12px;margin-top:4px;color:#333">
        Peak: <b>Jan–Mar (~88–94M MT/mo)</b><br>
        Sustained Apr–Jun baseline.<br>
        Sharp decline Jul–Sep as new crop loads.
      </div>
    </div>
    <div style="background:#FFF8E1;border-radius:10px;padding:16px;border-left:4px solid #D4AC0D">
      <div style="font-weight:800;color:#0D1B2A;font-size:14px">Wheat Season</div>
      <div style="font-size:12px;margin-top:4px;color:#333">
        Peak: <b>March (9.4M MT)</b><br>
        Relatively flat Jan–Jun;<br>
        Smallest volume of the three major grains.
      </div>
    </div>
  </div>
</section>

<!-- ═══ QUALITY & CERTIFICATION ══════════════════════════════════════════ -->
<section class="section-alt" id="section-quality">
  <h2 class="section-title">Quality & Certification Intelligence</h2>
  <p class="section-sub">USDA FGIS quality parameters and grade distribution from {total_cv:,} certificates,
     Mississippi River, 2025.</p>
  <div class="row g-4">
    <div class="col-md-6">
      <h5 style="font-size:14px;font-weight:700;color:#0D1B2A;margin-bottom:10px">
        Average Quality Parameters by Grain
      </h5>
      <table class="tbl">
        <tr><th>Grain</th><th>Moisture</th><th>FM%</th><th>Protein</th><th>Test Wt</th><th>Certs</th></tr>
        {qual_rows}
      </table>
      <div style="font-size:11px;color:#888;margin-top:6px">
        FM = Foreign Material. Test weight in lb/bu. Protein for soybeans and wheat only.
      </div>
    </div>
    <div class="col-md-6">
      <h5 style="font-size:14px;font-weight:700;color:#0D1B2A;margin-bottom:10px">
        Grade Distribution (by certified MT)
      </h5>
      <table class="tbl">
        <tr><th>Grain</th><th>Grade</th><th>Volume (MMT)</th><th>Share</th><th>Certs</th></tr>
        {grade_rows}
      </table>
    </div>
  </div>
  <div style="margin-top:20px;padding:14px 18px;background:#E8F5E9;border-radius:8px;border-left:4px solid #388E3C">
    <b style="font-size:13px;color:#1B5E20">Grade Quality Summary:</b>
    <span style="font-size:12px;color:#333"> The vast majority of Lower Mississippi River exports
    achieve Grade 2 O/B (Other Basic) or better. Corn: 83% Grade 2 O/B.
    Soybeans: 96% Grade 2 O/B. Wheat: 94% Grade 2 O/B or better.
    This reflects the exceptional quality standards maintained by US export elevator operators.</span>
  </div>
</section>

<!-- ═══ TERMINAL RANKINGS ═════════════════════════════════════════════════ -->
<section class="section" id="section-rankings">
  <h2 class="section-title">Terminal Rankings & Market Share</h2>
  <p class="section-sub">Throughput ranking by 2025 loading activity. Loading records = daily lineup
     snapshots when a vessel appeared as LOADING at that terminal.</p>
  <div class="row g-4">
    <div class="col-md-7">
      <div class="chart-box" style="height:380px"><canvas id="chart_rankings"></canvas></div>
    </div>
    <div class="col-md-5">
      <div class="chart-box" style="height:380px"><canvas id="chart_mktshare"></canvas></div>
      <div style="font-size:10px;color:#888;margin-top:4px">
        * Based on estimated MT from loading records with filed cargo weight.
          Terminals with high NULL-MT rates (ADM AMA, ADM Destrehan) appear smaller than actual throughput.
      </div>
    </div>
  </div>

  <h4 style="font-size:16px;font-weight:700;margin:32px 0 12px;color:#0D1B2A">Tier Classification</h4>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr><th>Tier</th><th>Terminal</th><th>Operator</th><th>Mile</th>
          <th>2025 Loads</th><th>Unique Vessels</th><th>Est. Total MT</th><th>Vessel Class</th></tr>
"""

    for t in TERMINALS:
        k  = t["key"]
        a  = ta[k]
        mt_k = a.get("total_mt_k", 0) or 0
        mt_str = f"{mt_k:,}K MT" if mt_k else "N/A"
        mt_total = mt_k
        lv = a.get("loading_records", 0)
        if mt_total >= 6000 or lv >= 300:
            tier_str = "Tier 1"
            tier_col = "#1565C0"
        elif mt_total >= 2000 or lv >= 130:
            tier_str = "Tier 2"
            tier_col = "#388E3C"
        else:
            tier_str = "Tier 3"
            tier_col = "#607D8B"
        html += (f'<tr><td><b style="color:{tier_col}">{tier_str}</b></td>'
                 f'<td><b>{t["display"]}</b></td><td>{t["operator"]}</td>'
                 f'<td>MM {t["mile"]}</td>'
                 f'<td>{a.get("loading_records",0):,}</td>'
                 f'<td>{a.get("unique_vessels",0):,}</td>'
                 f'<td>{mt_str}</td>'
                 f'<td>{a.get("vessel_class","N/A")}</td></tr>\n')

    html += f"""    </table>
  </div>
</section>

</main><!-- /content -->

<script>
document.addEventListener('DOMContentLoaded', function() {{
  // Sidebar active link tracking
  const links = document.querySelectorAll('.nav-link');
  const observer = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      if (e.isIntersecting) {{
        links.forEach(l => l.classList.remove('active'));
        const id = e.target.id;
        const link = document.querySelector('.nav-link[href="#'+id+'"]');
        if (link) link.classList.add('active');
      }}
    }});
  }}, {{ threshold: 0.3 }});
  document.querySelectorAll('section[id]').forEach(s => observer.observe(s));

  // Initialize all Chart.js charts
  {all_scripts}
}});
</script>
</body>
</html>"""
    return html


# ─── INTERNAL ANNEX BUILDER ───────────────────────────────────────────────────
def build_internal_html(q, ta):
    fgis_ov = q["fgis_overview"].iloc[0]

    rows = ""
    for t in TERMINALS:
        k  = t["key"]
        a  = ta[k]
        rows += (f"<tr><td><b>{t['display']}</b></td>"
                 f"<td>MM {t['mile']}</td>"
                 f"<td>{a.get('loading_records',0):,}</td>"
                 f"<td>{a.get('unique_vessels',0):,}</td>"
                 f"<td>{a.get('median_mt') or 'N/A'}</td>"
                 f"<td>{a.get('median_wait') or 'N/A'}</td>"
                 f"<td>{a.get('median_load') or 'N/A'}</td>"
                 f"<td>{a.get('total_mt_k',0) or 0:,}K</td></tr>\n")

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>INTERNAL — Lower Miss River Elevator Guide 2025 — Methodology Annex</title>
<style>
body{{font-family:"Segoe UI",sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#212529}}
h1{{color:#0D1B2A;border-bottom:3px solid #F0A500;padding-bottom:8px}}
h2{{color:#1B3A5C;margin-top:32px;border-left:4px solid #1B3A5C;padding-left:12px}}
h3{{color:#1B3A5C;font-size:15px}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:12px 0}}
th{{background:#0D1B2A;color:#fff;padding:8px 10px;text-align:left}}
td{{padding:7px 10px;border-bottom:1px solid #dee2e6}}
tr:hover td{{background:#f8f9fa}}
.warn{{background:#FFF3E0;border-left:4px solid #FF8F00;padding:12px;border-radius:4px;margin:12px 0}}
.note{{background:#E3F2FD;border-left:4px solid #1565C0;padding:12px;border-radius:4px;margin:12px 0}}
.source{{background:#F3E5F5;border-left:4px solid #7B1FA2;padding:12px;border-radius:4px;margin:12px 0}}
code{{background:#f1f3f5;padding:2px 6px;border-radius:3px;font-size:11px}}
</style>
</head><body>

<h1>INTERNAL USE ONLY — Methodology &amp; Source Annex<br>
<small style="font-size:15px;color:#666">Lower Mississippi River Grain Export Elevator Intelligence Report — 2025</small></h1>

<p style="color:#888;font-size:12px">Generated: {BUILD_DATE} &nbsp;|&nbsp; Confidential — William S. Davis III</p>

<div class="warn">
  <b>Confidentiality Notice:</b> This document is for internal use only. The companion report
  (<code>lower_miss_grain_elevator_guide_2025.html</code>) does not contain source attribution or
  methodology notes. This annex provides full reproducibility documentation.
</div>

<h2>1. Data Sources</h2>
<div class="source">
  <b>Primary Sources Used in This Report:</b>
  <ul>
    <li><b>Southport Agencies Lineup Feed</b> — Daily vessel lineup reports for Mississippi River, Texas Gulf, and Pacific Northwest export terminals. 255 daily reports in 2025 loaded into <code>grain_southport_lineup</code> table. Coverage: Jan 1 – Dec 31, 2025. Rows: ~15,500 for MISS_RIVER region.</li>
    <li><b>USDA FGIS Export Certificates</b> — Official US grain export certification data. 30,057 certificates for Mississippi River, Jan 1 – Sep 25, 2025. Loaded into <code>grain_fgis_certs</code> table. Source: USDA Agricultural Marketing Service (AMS) / FGIS public export certificate database.</li>
    <li><b>Blue Water Shipping Port Maps</b> — Terminal facility details (capacity, spouts, mile markers) scraped from <code>bluewatershipping.com/portmaps.php</code>. Stored in <code>facilities_grain_export_elevator.geojson</code> with IENC-calibrated coordinates.</li>
    <li><b>USACE IENC (Inland Electronic Navigational Charts)</b> — Mile marker AHP data used to calibrate terminal coordinates on the Mississippi River.</li>
  </ul>
</div>

<h2>2. Database Schema</h2>
<h3>grain_southport_lineup</h3>
<table>
  <tr><th>Column</th><th>Type</th><th>Description</th></tr>
  <tr><td>report_date</td><td>DATE</td><td>Date of the lineup report</td></tr>
  <tr><td>region</td><td>VARCHAR</td><td>MISS_RIVER / TEXAS / PNW</td></tr>
  <tr><td>terminal_abbrev</td><td>VARCHAR</td><td>Short terminal code from lineup</td></tr>
  <tr><td>terminal_name</td><td>VARCHAR</td><td>Full terminal name (normalized)</td></tr>
  <tr><td>mile_ahp</td><td>DOUBLE</td><td>River mile AHP (some rows have parser artifacts)</td></tr>
  <tr><td>vessel_name</td><td>VARCHAR</td><td>Vessel name as appears in lineup</td></tr>
  <tr><td>status_type</td><td>VARCHAR</td><td>ETA / LOADING / FILED / IN PORT / etc.</td></tr>
  <tr><td>mt_numeric</td><td>DOUBLE</td><td>Cargo MT (NULL for unfiled or unknown)</td></tr>
  <tr><td>commodity_code</td><td>VARCHAR</td><td>Grain code (YSB, CORN, WHT, SBM, DDGS, etc.)</td></tr>
  <tr><td>destination</td><td>VARCHAR</td><td>Cargo destination country/port</td></tr>
  <tr><td>delay_days_min/max</td><td>INTEGER</td><td>Published dock delay range (when available)</td></tr>
</table>

<h3>grain_fgis_certs</h3>
<table>
  <tr><th>Column</th><th>Type</th><th>Description</th></tr>
  <tr><td>serial_no</td><td>VARCHAR</td><td>FGIS certificate serial number</td></tr>
  <tr><td>cert_date</td><td>DATE</td><td>Certificate issuance date</td></tr>
  <tr><td>vessel</td><td>VARCHAR</td><td>Vessel name</td></tr>
  <tr><td>grain</td><td>VARCHAR</td><td>Grain type (CORN, SOYBEANS, WHEAT, CANOLA)</td></tr>
  <tr><td>grain_class / grade</td><td>VARCHAR</td><td>Grain class and USDA grade</td></tr>
  <tr><td>metric_ton</td><td>DOUBLE</td><td>Certified metric tons</td></tr>
  <tr><td>destination</td><td>VARCHAR</td><td>Destination country</td></tr>
  <tr><td>port</td><td>VARCHAR</td><td>Export port (MISSISSIPPI R. for this report)</td></tr>
  <tr><td>moisture_avg, fm_pct, protein_avg, test_weight</td><td>DOUBLE</td><td>Quality parameters</td></tr>
</table>

<h2>3. Metric Methodology</h2>

<h3>3.1 Queue Wait Time</h3>
<div class="note">
  <b>Definition:</b> Median days from first ETA appearance to first LOADING date per vessel-terminal combination.<br>
  <b>Window:</b> Only vessel-terminal pairs where first LOADING date is within 30 days of first ETA date are included.
  This prevents multi-voyage vessel name collisions from inflating wait times.<br>
  <b>Limitation:</b> The lineup is a daily snapshot — actual arrival/departure timestamps not available.
  Queue wait is a proxy measured in calendar days between report appearances.
</div>
<code style="display:block;margin:8px 0;padding:10px;background:#f8f9fa;border-radius:4px;white-space:pre">
WITH eta AS (
    SELECT terminal_name, vessel_name, MIN(report_date) first_eta
    FROM grain_southport_lineup WHERE region='MISS_RIVER' AND YEAR=2025 AND status_type='ETA'
    GROUP BY 1, 2
),
loading AS (
    SELECT terminal_name, vessel_name, MIN(report_date) first_loading
    FROM grain_southport_lineup WHERE region='MISS_RIVER' AND YEAR=2025 AND status_type='LOADING'
    GROUP BY 1, 2
)
SELECT e.terminal_name, MEDIAN(DATEDIFF('day', e.first_eta, l.first_loading)) AS median_wait
FROM eta e JOIN loading l USING (terminal_name, vessel_name)
WHERE l.first_loading BETWEEN e.first_eta AND e.first_eta + 30
GROUP BY e.terminal_name
</code>

<h3>3.2 Loading Duration</h3>
<div class="note">
  <b>Definition:</b> Median count of distinct LOADING report dates per vessel-terminal per year.<br>
  <b>Limitation:</b> A vessel appearing as LOADING across multiple daily reports may span a weekend
  gap (no report) or represent multiple adjacent short berths. This metric counts unique LOADING
  report dates per vessel-terminal combination — it is a proxy for time alongside, not actual
  port hours.<br>
  <b>Interpretation:</b> ADM Wood Buoys and Cooper Darrow show 3-day medians vs. 1-2 days elsewhere,
  consistent with midstream float operations requiring multiple shifts.
</div>

<h3>3.3 Estimated Terminal Throughput MT</h3>
<div class="warn">
  <b>Caveat:</b> Approximately 40–70% of LOADING records (depending on terminal) have NULL mt_numeric
  because vessels file cargo details only when formally 'FILED'. The total_mt_k values in the ranking
  table significantly undercount actual throughput for terminals like ADM AMA and ADM Destrehan.
  FGIS total certified MT ({fgis_ov['total_mt_m']:.1f}M MT, Jan–Sep 2025) is the authoritative
  volume figure for the port as a whole. Terminal-level allocation would require vessel-to-terminal
  matching between FGIS and lineup data (not implemented in this version).
</div>

<h3>3.4 Commodity Mix</h3>
<div class="note">
  Primary commodity code assigned by majority presence in commodity_code string.
  Records with NULL commodity_code labeled 'Filed/Unspec' — these are valid loading records
  but without confirmed cargo details at time of report. The 'OTHER' category is predominantly
  rice and GDDG (Golden Dried Distillers Grains).
</div>

<h3>3.5 Dock Delay</h3>
<div class="note">
  When the lineup publishes a delay range (delay_days_min / delay_days_max), this represents
  the published terminal dock delay — vessels anchored or on order waiting for an available berth.
  Not all terminals publish delay consistently; ADM Reserve and ADM Destrehan rarely publish delay
  in the lineup. The avg values shown in terminal profiles are averages of published non-zero delays
  when available.
</div>

<h2>4. Terminal Raw Analytics Summary</h2>
<table>
  <tr><th>Terminal</th><th>Mile</th><th>Load Records</th><th>Unique Vessels</th>
      <th>Median MT</th><th>Median Queue Wait (d)</th><th>Median Load Days</th><th>Est. Total MT</th></tr>
  {rows}
</table>

<h2>5. Known Data Limitations</h2>
<ul>
  <li><b>FGIS coverage:</b> Jan 1 – Sep 25, 2025 only (9 months). Full-year 2025 data not yet published as of report build date.</li>
  <li><b>Lineup gaps:</b> 255 of 365 days in 2025 have lineup reports (70% coverage). Some weekend/holiday gaps expected.</li>
  <li><b>Mile marker artifacts:</b> Cooper Darrow, Zen-Noh Convent, and LDC Port Allen all show mile_ahp=164.0 in the lineup table — a parser artifact. True positions from GeoJSON/IENC data used for map display.</li>
  <li><b>Top shipments duplicates:</b> FGIS raw data contains one certificate row per grain elevator per vessel per day, meaning a large Capesize may generate 5-10 rows with the same total tonnage. The top shipments table uses MAX(metric_ton) per vessel-grain-destination to deduplicate.</li>
  <li><b>Bunge Destrehan:</b> Not present in BWS port maps GeoJSON; coordinate estimated at MM 120.0 LDB based on river interpolation between ADM Ama (MM 117.6) and ADM Destrehan (MM 120.6).</li>
  <li><b>ADM Wood Buoys:</b> Not in BWS port maps GeoJSON. Coordinate estimated at MM 110.0 based on river interpolation.</li>
</ul>

<h2>6. Reproducibility</h2>
<div class="note">
  <b>To regenerate this report:</b><br>
  <code>cd 03_COMMODITY_MODULES/grain</code><br>
  <code>python3 src/build_lower_miss_report.py</code><br><br>
  DuckDB: <code>data/analytics.duckdb</code> (project root)<br>
  GeoJSON: <code>07_KNOWLEDGE_BANK/master_facility_register/data/national_supply_chain/facilities_grain_export_elevator.geojson</code><br>
  Output: <code>04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025.html</code><br>
  Annex: <code>04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_INTERNAL.html</code>
</div>

</body></html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("Lower Mississippi River Grain Export Elevator Report — Build Script")
    print(f"  DB: {DB_PATH}")
    print(f"  Output: {OUTPUT_MAIN.name}")

    print("\n[1/6] Connecting to DuckDB and running queries...")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    q = run_queries(con)
    con.close()
    print(f"       FGIS: {q['fgis_overview'].iloc[0]['total_certs']:,} certs, "
          f"{q['fgis_overview'].iloc[0]['total_mt_m']:.1f}M MT")
    print(f"       Lineup terminals: {q['loading_stats'].shape[0]}")

    print("\n[2/6] Building terminal analytics...")
    ta = build_terminal_analytics(q)

    print("\n[3/6] Generating river map (Folium)...")
    river_m = build_river_map(ta)
    river_html = map_to_b64_iframe(river_m, height=540)
    print("       River map: OK")

    print("\n[4/6] Generating world trade flow map (Folium)...")
    world_m = build_world_map(q["fgis_destinations"])
    world_html = map_to_b64_iframe(world_m, height=480)
    print("       World map: OK")

    print("\n[5/6] Assembling main report HTML...")
    main_html = build_main_html(q, ta, river_html, world_html)
    OUTPUT_MAIN.write_text(main_html, encoding="utf-8")
    size_mb = OUTPUT_MAIN.stat().st_size / 1e6
    print(f"       Written: {OUTPUT_MAIN.name} ({size_mb:.1f} MB)")

    print("\n[6/6] Assembling internal methodology annex...")
    int_html = build_internal_html(q, ta)
    OUTPUT_INT.write_text(int_html, encoding="utf-8")
    size_mb2 = OUTPUT_INT.stat().st_size / 1e6
    print(f"       Written: {OUTPUT_INT.name} ({size_mb2:.1f} MB)")

    print("\n✓ Build complete.")
    print(f"  Main report : {OUTPUT_MAIN}")
    print(f"  Methodology : {OUTPUT_INT}")


if __name__ == "__main__":
    main()
