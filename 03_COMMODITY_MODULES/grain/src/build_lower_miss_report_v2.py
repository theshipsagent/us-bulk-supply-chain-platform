#!/usr/bin/env python3
"""
build_lower_miss_report_v2.py
Lower Mississippi River Grain Export Elevator Intelligence Report — 2025 (v2)
Enhanced: dark/light theme, print support, anchorage intelligence, river stages,
          barge origin corridors, weather/seasonal context.
Run from: 03_COMMODITY_MODULES/grain/
  python3 src/build_lower_miss_report_v2.py
"""

import sys, os, json, math, re, tempfile, base64
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
import folium
from folium.plugins import MeasureControl

# ─── PATHS ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
GRAIN_DIR    = SCRIPT_DIR.parent
PROJECT_ROOT = GRAIN_DIR.parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "analytics.duckdb"
MRTIS_DIR    = PROJECT_ROOT / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean"
OUTPUT_DIR   = PROJECT_ROOT / "04_REPORTS" / "presentations"
OUTPUT_MAIN  = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025_v2.html"
OUTPUT_INT   = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025_v2_INTERNAL.html"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BUILD_DATE = datetime.now().strftime("%B %d, %Y")

# ─── TERMINAL METADATA ────────────────────────────────────────────────────────
TERMINALS = [
    {"key": "MGMT",               "display": "MGMT / Associated Terminals", "operator": "Associated Terminals", "mile": 57.8,  "bank": "RDB", "cap": "N/A (Floating)",   "spouts": "1 (float)", "lat": 29.6346, "lon": -89.9272, "color": "#607D8B"},
    {"key": "CHS MYRTLE GROVE",   "display": "CHS Myrtle Grove",            "operator": "CHS, Inc.",            "mile": 61.5,  "bank": "RDB", "cap": "6,464,000 bu",     "spouts": 4,           "lat": 29.6729, "lon": -89.9612, "color": "#388E3C"},
    {"key": "CARGILL WESTWEGO",   "display": "Cargill Westwego",            "operator": "Cargill, Inc.",        "mile": 103.0, "bank": "RDB", "cap": "N/A",              "spouts": 6,           "lat": 29.9373, "lon": -90.1391, "color": "#C62828"},
    {"key": "ADM WOOD BUOYS",     "display": "ADM Wood Buoys",              "operator": "ADM Grain Co.",        "mile": 110.0, "bank": "RDB", "cap": "N/A (Midstream)",  "spouts": "1 (float)", "lat": 29.9350, "lon": -90.2400, "color": "#1565C0"},
    {"key": "ADM AMA",            "display": "ADM Ama",                     "operator": "ADM Grain Co.",        "mile": 117.6, "bank": "RDB", "cap": "5,500,000 bu",     "spouts": 4,           "lat": 29.9433, "lon": -90.3133, "color": "#1565C0"},
    {"key": "BUNGE DESTREHAN",    "display": "Bunge Destrehan",             "operator": "Bunge, Ltd.",          "mile": 120.0, "bank": "LDB", "cap": "N/A",              "spouts": "N/A",       "lat": 29.9400, "lon": -90.3520, "color": "#6A1B9A"},
    {"key": "ADM DESTREHAN",      "display": "ADM Destrehan",               "operator": "ADM Grain Co.",        "mile": 120.6, "bank": "LDB", "cap": "5,500,000 bu",     "spouts": 7,           "lat": 29.9380, "lon": -90.3585, "color": "#1565C0"},
    {"key": "COOPER DARROW",      "display": "Cooper / Darrow Buoy",        "operator": "Cooper Consolidated",  "mile": 133.0, "bank": "LDB", "cap": "N/A (Midstream)",  "spouts": "1 (float)", "lat": 30.0465, "lon": -90.4798, "color": "#607D8B"},
    {"key": "ADM RESERVE",        "display": "ADM Reserve",                 "operator": "ADM Grain Co.",        "mile": 139.1, "bank": "LDB", "cap": "3,500,000 bu",     "spouts": 3,           "lat": 30.0513, "lon": -90.5762, "color": "#1565C0"},
    {"key": "CARGILL RESERVE",    "display": "Cargill Reserve (Terre Haute)","operator": "Cargill, Inc.",       "mile": 139.6, "bank": "LDB", "cap": "N/A",              "spouts": 4,           "lat": 30.0500, "lon": -90.5843, "color": "#C62828"},
    {"key": "ZEN-NOH CONVENT",    "display": "Zen-Noh Convent",             "operator": "Zen-Noh Grain Corp.",  "mile": 163.8, "bank": "LDB", "cap": "4,200,000 bu",     "spouts": 4,           "lat": 30.0630, "lon": -90.8770, "color": "#E65100"},
    {"key": "MILE 228.5 (6.9MBU)","display": "LDC Port Allen",             "operator": "Louis Dreyfus Corp.",  "mile": 229.2, "bank": "RDB", "cap": "6,900,000 bu",     "spouts": 5,           "lat": 30.4390, "lon": -91.1967, "color": "#00838F"},
]
TERM_KEY_MAP = {t["key"]: t for t in TERMINALS}

# Lower Miss anchorage positions (approx, used for map markers)
ANCHORAGES = [
    {"name": "9 Mile Anch",          "lat": 29.075, "lon": -89.210, "note": "Primary inbound anchorage"},
    {"name": "12 Mile Anch",         "lat": 29.110, "lon": -89.260, "note": "High-traffic queue zone"},
    {"name": "Pt Celeste",           "lat": 29.470, "lon": -89.775, "note": "Upbound staging"},
    {"name": "Davant Anch",          "lat": 29.580, "lon": -89.870, "note": "Longest median wait 2025"},
    {"name": "SW Pass Anch",         "lat": 28.960, "lon": -89.430, "note": "SWP approach anchorage"},
    {"name": "Baton Rouge Gen Anch", "lat": 30.430, "lon": -91.180, "note": "Upper river queue"},
]

# Country centroids for world trade flow map
COUNTRY_CENTROIDS = {
    "MEXICO":(23.6,-102.6),"CHINA":(35.8,104.2),"COLOMBIA":(4.6,-74.1),"JAPAN":(36.2,138.3),
    "EGYPT":(26.8,30.8),"SPAIN":(40.5,-3.7),"GERMANY":(51.2,10.5),"GUATEMALA":(15.8,-90.2),
    "DOMINICN REP":(18.7,-70.2),"MOROCCO":(31.8,-7.1),"HONDURAS":(15.2,-86.2),
    "EL SALVADOR":(13.8,-88.9),"NICARAGUA":(12.9,-85.2),"COSTA RICA":(9.7,-83.8),
    "ITALY":(41.9,12.5),"PORTUGAL":(39.4,-8.2),"NETHERLANDS":(52.1,5.3),"PANAMA":(8.5,-80.8),
    "ISRAEL":(31.0,35.0),"INDONESIA":(-0.8,113.9),"VIETNAM":(14.1,108.3),"TAIWAN":(23.7,120.9),
    "S. KOREA":(36.5,127.9),"BANGLADESH":(23.7,90.4),"PAKISTAN":(30.4,69.3),"TURKEY":(39.9,32.9),
    "ALGERIA":(28.0,1.7),"TUNISIA":(34.0,9.0),"VENEZUELA":(6.4,-66.6),"ECUADOR":(-1.8,-78.2),
    "CHILE":(-35.7,-71.5),"S.AFRICA":(-30.6,22.9),"FRANCE":(46.2,2.2),"IRELAND":(53.4,-8.2),
    "UNITED KINGDOM":(54.4,-2.0),"SAUDI ARABIA":(24.0,45.0),"NEW ZEALAND":(-40.9,174.9),
    "EUROPORT":(51.9,4.5),"EUROPORTS":(51.9,4.5),"DOM REP":(18.7,-70.2),"S. AFRICA":(-30.6,22.9),
}

COMM_COLORS = {
    "YSB":"#F9A825","CORN":"#FDD835","SBM":"#8D6E63",
    "WHT":"#D4AC0D","DDGS":"#FF8F00","OTHER":"#90A4AE","UNKNOWN":"#CFD8DC",
}

# Historical monthly averages — river gauges (feet NGVD29)
RIVER_STAGES = {
    "Carrollton":      {1:8.5,2:11.2,3:13.8,4:14.2,5:11.5,6:6.8,7:3.5,8:1.8,9:1.5,10:2.8,11:5.2,12:7.1},
    "Donaldsonville":  {1:12.0,2:15.2,3:18.8,4:19.5,5:16.0,6:9.8,7:5.5,8:3.2,9:2.8,10:4.5,11:7.8,12:10.5},
}

# Barge origin corridors
BARGE_CORRIDORS = [
    {"name":"Upper Mississippi R.","pct":38,"grains":"Corn, Soybeans","color":"#F9A825",
     "waypoints":[(44.9,-93.1),(43.0,-91.2),(41.5,-90.5),(38.6,-90.2),(30.4,-91.0)]},
    {"name":"Ohio River","pct":20,"grains":"Corn, Soybeans, Wheat","color":"#42A5F5",
     "waypoints":[(38.5,-85.5),(37.2,-88.1),(37.0,-88.7),(30.4,-91.0)]},
    {"name":"Illinois River","pct":12,"grains":"Corn, Soybeans","color":"#66BB6A",
     "waypoints":[(40.7,-89.6),(39.5,-90.1),(38.6,-90.2),(30.4,-91.0)]},
    {"name":"Missouri River","pct":12,"grains":"Corn, Wheat, Soybeans","color":"#FF7043",
     "waypoints":[(39.1,-94.7),(38.9,-92.0),(38.6,-90.2),(30.4,-91.0)]},
    {"name":"Arkansas River","pct":8,"grains":"Soybeans, Wheat, Sorghum","color":"#AB47BC",
     "waypoints":[(34.7,-92.3),(33.8,-91.5),(33.1,-91.1),(30.5,-91.0)]},
    {"name":"Tennessee / Cumberland","pct":5,"grains":"Corn, Soybeans","color":"#26C6DA",
     "waypoints":[(36.2,-86.7),(37.0,-88.7),(30.4,-91.0)]},
    {"name":"Local (LA / MS)","pct":5,"grains":"Soybeans, Rice","color":"#8D6E63",
     "waypoints":[(31.5,-91.0),(30.5,-91.1),(30.4,-91.0)]},
]

# ─── MRTIS DATA LOADER ───────────────────────────────────────────────────────
MRTIS_FALLBACK = {
    "port_time": {"total":159,"transit":26,"anchor":62,"terminal":67,"voyages":5518,"anchoring":3917},
    "anchorages": [
        {"zone":"9 Mile Anch",          "visits":720,"avg_h":57.1,"med_h":30.4},
        {"zone":"12 Mile Anch",         "visits":657,"avg_h":62.3,"med_h":33.2},
        {"zone":"Pt Celeste",           "visits":207,"avg_h":91.8,"med_h":47.9},
        {"zone":"Davant Anch",          "visits":186,"avg_h":104.3,"med_h":61.7},
        {"zone":"SW Pass Anch",         "visits":98, "avg_h":71.2,"med_h":45.3},
        {"zone":"Baton Rouge Gen Anch", "visits":92, "avg_h":82.1,"med_h":62.0},
        {"zone":"Head of Passes Anch",  "visits":87, "avg_h":68.5,"med_h":41.2},
        {"zone":"Natchez Anch",         "visits":45, "avg_h":89.4,"med_h":67.1},
    ],
    "monthly":{1:79,2:94,3:68,4:58,5:51,6:45,7:44,8:50,9:53,10:57,11:48,12:62},
    "source":"cached",
}


def load_mrtis(project_root):
    v_csv = project_root / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean" / "voyage_summary.csv"
    e_csv = project_root / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean" / "event_log.csv"
    if not v_csv.exists() or not e_csv.exists():
        print("  MRTIS CSVs not found — using cached data")
        return MRTIS_FALLBACK
    try:
        con = duckdb.connect(":memory:")
        vp = str(v_csv)
        ep = str(e_csv)
        con.execute(f"CREATE TABLE vs AS SELECT * FROM read_csv_auto('{vp}', types={{'IMO': 'VARCHAR'}})")
        con.execute(f"CREATE TABLE el AS SELECT * FROM read_csv_auto('{ep}', types={{'IMO': 'VARCHAR'}})")

        # Port time components
        pt_row = con.execute("""
            SELECT ROUND(AVG(TotalPortTimeHours),1)  total,
                   ROUND(AVG(TransitTimeHours),1)    transit,
                   ROUND(AVG(AnchorTimeHours),1)     anchor,
                   ROUND(AVG(TerminalTimeHours),1)   terminal,
                   COUNT(*)                          voyages,
                   SUM(CASE WHEN AnchorTimeHours > 0 THEN 1 ELSE 0 END) anchoring
            FROM vs
            WHERE CrossInTime >= '2025-01-01' AND CrossInTime < '2026-01-01'
        """).fetchone()
        port_time = {
            "total":    round(float(pt_row[0] or 159), 1),
            "transit":  round(float(pt_row[1] or 26), 1),
            "anchor":   round(float(pt_row[2] or 62), 1),
            "terminal": round(float(pt_row[3] or 67), 1),
            "voyages":  int(pt_row[4] or 5518),
            "anchoring":int(pt_row[5] or 3917),
        }

        # Top anchorages
        anch_df = con.execute("""
            SELECT Zone,
                   COUNT(DISTINCT VoyageID) visits,
                   ROUND(AVG(DurationToNextEventHours),1) avg_h,
                   ROUND(MEDIAN(DurationToNextEventHours),1) med_h
            FROM el
            WHERE (ZoneType = 'ANCHORAGE' OR Zone LIKE '%Anch%' OR Zone LIKE '%anch%')
              AND DurationToNextEventHours > 0
              AND DurationToNextEventHours < 500
              AND EventTime >= '2025-01-01' AND EventTime < '2026-01-01'
            GROUP BY Zone
            ORDER BY visits DESC
            LIMIT 10
        """).fetchdf()
        anchorages = anch_df.rename(columns={"Zone":"zone","visits":"visits",
                                              "avg_h":"avg_h","med_h":"med_h"}).to_dict("records")
        if not anchorages:
            anchorages = MRTIS_FALLBACK["anchorages"]

        # Monthly trend
        mo_df = con.execute("""
            SELECT datepart('month', CrossInTime::TIMESTAMP) mo,
                   ROUND(AVG(AnchorTimeHours),1) avg_anch
            FROM vs
            WHERE AnchorTimeHours > 0
              AND CrossInTime >= '2025-01-01' AND CrossInTime < '2026-01-01'
            GROUP BY mo ORDER BY mo
        """).fetchdf()
        monthly = {int(r["mo"]): float(r["avg_anch"]) for _, r in mo_df.iterrows()}
        if not monthly:
            monthly = MRTIS_FALLBACK["monthly"]

        con.close()
        print(f"  MRTIS live: {port_time['voyages']:,} voyages, {len(anchorages)} anchorages")
        return {"port_time": port_time, "anchorages": anchorages, "monthly": monthly, "source": "live"}
    except Exception as exc:
        print(f"  MRTIS live error: {exc} — using cached data")
        return MRTIS_FALLBACK


# ─── DATABASE QUERIES ────────────────────────────────────────────────────────
def run_queries(con):
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
               CASE WHEN commodity_code LIKE '%YSB%'  THEN 'YSB'
                    WHEN commodity_code LIKE '%CORN%' THEN 'CORN'
                    WHEN commodity_code LIKE '%WHT%'  THEN 'WHT'
                    WHEN commodity_code LIKE '%SBM%'  THEN 'SBM'
                    WHEN commodity_code LIKE '%DDGS%' THEN 'DDGS'
                    WHEN commodity_code IS NULL        THEN 'UNKNOWN'
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
            WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
              AND status_type='ETA'
            GROUP BY 1,2
        ), loading AS (
            SELECT terminal_name, vessel_name, MIN(report_date) first_loading
            FROM grain_southport_lineup
            WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
              AND status_type='LOADING'
            GROUP BY 1,2
        )
        SELECT e.terminal_name, COUNT(*) n,
               ROUND(MEDIAN(DATEDIFF('day',e.first_eta,l.first_loading)),1) median_wait
        FROM eta e
        JOIN loading l ON e.terminal_name=l.terminal_name AND e.vessel_name=l.vessel_name
        WHERE l.first_loading >= e.first_eta
          AND DATEDIFF('day',e.first_eta,l.first_loading) <= 30
        GROUP BY e.terminal_name
    """).fetchdf()

    q["load_duration"] = con.execute("""
        WITH vl AS (
            SELECT terminal_name, vessel_name,
                   COUNT(DISTINCT report_date) loading_days
            FROM grain_southport_lineup
            WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
              AND status_type='LOADING'
            GROUP BY 1,2
        )
        SELECT terminal_name, ROUND(MEDIAN(loading_days),1) median_load_days
        FROM vl GROUP BY terminal_name
    """).fetchdf()

    q["all_cargo_sizes"] = con.execute("""
        SELECT mt_numeric, terminal_name
        FROM grain_southport_lineup
        WHERE region='MISS_RIVER' AND datepart('year',report_date)=2025
          AND status_type='LOADING' AND mt_numeric IS NOT NULL AND mt_numeric > 5000
        ORDER BY mt_numeric
    """).fetchdf()

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
        SELECT datepart('month',cert_date) AS mo, grain,
               ROUND(SUM(metric_ton)/1000000,3) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
        GROUP BY 1,2 ORDER BY 1, mt_m DESC
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
        SELECT vessel, grain, destination, ROUND(MAX(metric_ton),0) mt, MIN(cert_date) cert_date
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND metric_ton > 50000
        GROUP BY vessel, grain, destination
        ORDER BY mt DESC LIMIT 25
    """).fetchdf()

    # Seasonal: commodity mix by month from FGIS
    q["fgis_seasonal_grain"] = con.execute("""
        SELECT datepart('month',cert_date) mo,
               grain, ROUND(SUM(metric_ton)/1000000,3) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND grain IN ('CORN','SOYBEANS','WHEAT')
        GROUP BY 1,2 ORDER BY 1,2
    """).fetchdf()

    return q


# ─── TERMINAL ANALYTICS ──────────────────────────────────────────────────────
def build_terminal_analytics(q):
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
            a["loading_records"] = int(row["loading_records"])
            a["unique_vessels"]  = int(row["unique_vessels"])
            a["avg_mt"]   = int(row["avg_mt"])   if pd.notna(row["avg_mt"])   else None
            a["median_mt"]= int(row["median_mt"])if pd.notna(row["median_mt"])else None
            a["p25_mt"]   = int(row["p25_mt"])   if pd.notna(row["p25_mt"])   else None
            a["p75_mt"]   = int(row["p75_mt"])   if pd.notna(row["p75_mt"])   else None
            a["total_mt_k"]= int(row["total_mt_k"]) if pd.notna(row["total_mt_k"]) else 0
        else:
            a.update({"loading_records":0,"unique_vessels":0,"avg_mt":None,
                      "median_mt":None,"p25_mt":None,"p75_mt":None,"total_mt_k":0})
        a["delay_min"] = float(ds.loc[key,"avg_delay_min"]) if key in ds.index and pd.notna(ds.loc[key,"avg_delay_min"]) else None
        a["delay_max"] = float(ds.loc[key,"avg_delay_max"]) if key in ds.index and pd.notna(ds.loc[key,"avg_delay_max"]) else None
        a["median_wait"]= float(qw.loc[key,"median_wait"]) if key in qw.index else None
        a["median_load"]= float(ld.loc[key,"median_load_days"]) if key in ld.index else None

        t_dest = q["destinations"][q["destinations"]["terminal_name"]==key].head(5)
        a["top_dests"] = list(zip(t_dest["destination"], t_dest["cnt"].astype(int)))

        t_comm = q["commodity_mix"][q["commodity_mix"]["terminal_name"]==key]
        total_c = t_comm["cnt"].sum()
        a["comm_mix"] = {r["primary_comm"]: round(int(r["cnt"])/total_c*100,1)
                         for _, r in t_comm.iterrows()} if total_c > 0 else {}

        med = a.get("median_mt") or 0
        a["vessel_class"] = ("Capesize" if med >= 65000 else
                             "Panamax"  if med >= 40000 else
                             "Handymax / Supramax" if med >= 25000 else "Handymax")
        ta[key] = a
    return ta


# ─── FOLIUM MAPS ─────────────────────────────────────────────────────────────
def map_to_b64_iframe(m, height=540):
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        m.save(f.name); fname = f.name
    with open(fname, "r", encoding="utf-8") as f:
        html_str = f.read()
    os.unlink(fname)
    b64 = base64.b64encode(html_str.encode("utf-8")).decode("ascii")
    return (f'<iframe src="data:text/html;base64,{b64}" '
            f'style="width:100%;height:{height}px;border:none;border-radius:8px;"></iframe>')


def build_river_map(terminal_analytics):
    m = folium.Map(location=[30.04, -90.55], zoom_start=9,
                   tiles="CartoDB DarkMatter")
    folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Satellite").add_to(m)

    # Anchorage layer
    anch_fg = folium.FeatureGroup(name="Anchorages", show=True)
    for anch in ANCHORAGES:
        folium.CircleMarker(
            location=[anch["lat"], anch["lon"]],
            radius=7, color="#FFC107", weight=2, fill=True,
            fill_color="#FFC107", fill_opacity=0.3,
            tooltip=f"{anch['name']} — {anch['note']}",
            popup=folium.Popup(
                f"<b>{anch['name']}</b><br><span style='font-size:11px;color:#555'>{anch['note']}</span>",
                max_width=200),
        ).add_to(anch_fg)
    anch_fg.add_to(m)

    # Terminal layer
    term_fg = folium.FeatureGroup(name="Grain Elevators", show=True)
    for t in TERMINALS:
        key = t["key"]
        ta  = terminal_analytics.get(key, {})
        med = ta.get("median_mt")
        med_str = f"{med:,}" if med else "N/A"
        lv  = ta.get("loading_records", 0)
        vc  = ta.get("vessel_class", "N/A")
        top1 = ta["top_dests"][0][0] if ta.get("top_dests") else "N/A"
        popup_html = (
            f'<div style="font-family:Arial,sans-serif;min-width:210px;padding:4px">'
            f'<b style="font-size:13px">{t["display"]}</b><br>'
            f'<span style="color:#777;font-size:11px">{t["operator"]}</span>'
            f'<hr style="margin:4px 0">'
            f'<table style="font-size:11px;width:100%">'
            f'<tr><td><b>Mile AHP</b></td><td>MM {t["mile"]}</td></tr>'
            f'<tr><td><b>Bank</b></td><td>{t["bank"]}</td></tr>'
            f'<tr><td><b>Capacity</b></td><td>{t["cap"]}</td></tr>'
            f'<tr><td><b>Spouts</b></td><td>{t["spouts"]}</td></tr>'
            f'<tr><td><b>Vessel Class</b></td><td>{vc}</td></tr>'
            f'<tr><td><b>2025 Loads</b></td><td>{lv:,} records</td></tr>'
            f'<tr><td><b>Median Cargo</b></td><td>{med_str} MT</td></tr>'
            f'<tr><td><b>Top Destination</b></td><td>{top1}</td></tr>'
            f'</table></div>'
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]], radius=11,
            color="#FFFFFF", weight=2, fill=True,
            fill_color=t["color"], fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"MM {t['mile']} — {t['display']}",
        ).add_to(term_fg)
        folium.Marker(
            location=[t["lat"] + 0.013, t["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:700;color:#FFFFFF;'
                     f'white-space:nowrap;text-shadow:1px 1px 3px #000,-1px -1px 3px #000">'
                     f'MM {t["mile"]}</div>',
                icon_size=(80, 14), icon_anchor=(0, 0)),
        ).add_to(term_fg)
    term_fg.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    MeasureControl(position="bottomleft").add_to(m)
    return m


def gc_arc(lat1, lon1, lat2, lon2, n=40):
    d2r = math.pi / 180
    la1, lo1, la2, lo2 = lat1*d2r, lon1*d2r, lat2*d2r, lon2*d2r
    d = 2*math.asin(math.sqrt(
        math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
    if d < 1e-6:
        return [(lat1, lon1), (lat2, lon2)]
    pts = []
    for i in range(n+1):
        f = i/n
        A = math.sin((1-f)*d)/math.sin(d); B = math.sin(f*d)/math.sin(d)
        x = A*math.cos(la1)*math.cos(lo1)+B*math.cos(la2)*math.cos(lo2)
        y = A*math.cos(la1)*math.sin(lo1)+B*math.cos(la2)*math.sin(lo2)
        z = A*math.sin(la1)+B*math.sin(la2)
        pts.append((math.atan2(z, math.sqrt(x**2+y**2))/d2r, math.atan2(y,x)/d2r))
    return pts


def build_world_map(fgis_dests):
    m = folium.Map(location=[20.0, -30.0], zoom_start=2,
                   tiles="CartoDB DarkMatter")
    origin = (29.3, -89.5)
    max_mt = fgis_dests["mt_m"].max()
    shown = 0
    for _, row in fgis_dests.iterrows():
        dest = row["destination"]; mt = row["mt_m"]; certs = int(row["certs"])
        if dest not in COUNTRY_CENTROIDS: continue
        lat, lon = COUNTRY_CENTROIDS[dest]
        w = max(1, int(8*math.log(1+mt)/math.log(1+max_mt)))
        folium.PolyLine(gc_arc(origin[0], origin[1], lat, lon, n=50),
                        weight=w, color="#F0A500", opacity=0.6,
                        tooltip=f"{dest}: {mt:.1f}M MT — {certs:,} certs").add_to(m)
        folium.CircleMarker([lat, lon], radius=6+w, color="#FFF", weight=1.5,
                            fill=True, fill_color="#C62828", fill_opacity=0.85,
                            popup=folium.Popup(f"<b>{dest}</b><br>{mt:.2f}M MT<br>{certs:,} certs",
                                               max_width=180),
                            tooltip=f"{dest}: {mt:.1f}M MT").add_to(m)
        shown += 1
    folium.Marker(origin, icon=folium.Icon(color="blue", icon="ship", prefix="fa"),
                  popup="Lower Mississippi River Elevators",
                  tooltip="Lower Mississippi River (Origin)").add_to(m)
    print(f"  World map: {shown} destinations")
    return m


def build_barge_map():
    m = folium.Map(location=[38.0, -91.0], zoom_start=5,
                   tiles="CartoDB DarkMatter")
    dest = (30.0, -90.3)  # New Orleans area
    # Destination marker
    folium.Marker(
        dest, icon=folium.Icon(color="red", icon="anchor", prefix="fa"),
        tooltip="Lower Mississippi Grain Elevators", popup="Lower Mississippi Export Elevators"
    ).add_to(m)
    # Draw corridors
    for corr in BARGE_CORRIDORS:
        wpts = corr["waypoints"]
        w = max(1, round(corr["pct"] / 5))
        folium.PolyLine(wpts, weight=w+1, color=corr["color"], opacity=0.75,
                        tooltip=f"{corr['name']} — ~{corr['pct']}% of barge volume").add_to(m)
        # Origin circle at first waypoint
        orig = wpts[0]
        folium.CircleMarker(orig, radius=6+w, color=corr["color"], weight=2,
                            fill=True, fill_color=corr["color"], fill_opacity=0.5,
                            tooltip=f"{corr['name']} — {corr['grains']}").add_to(m)
    # Mississippi River label
    folium.Marker([31.5, -91.4],
                  icon=folium.DivIcon(
                      html='<div style="font-size:10px;font-weight:700;color:#F0A500;'
                           'white-space:nowrap;text-shadow:1px 1px 3px #000">MISSISSIPPI RIVER</div>',
                      icon_size=(160, 14))).add_to(m)
    return m


# ─── HTML UTILITIES ───────────────────────────────────────────────────────────
def fmt_num(n, suffix=""):
    return "N/A" if n is None else f"{n:,.0f}{suffix}"


def comm_donut_js(canvas_id, comm_mix):
    order  = ["YSB","CORN","SBM","WHT","DDGS","OTHER","UNKNOWN"]
    label_map = {"YSB":"Soybeans","CORN":"Corn","SBM":"SBM","WHT":"Wheat",
                 "DDGS":"DDGS","OTHER":"Other","UNKNOWN":"Filed/Unspec"}
    labels, values, colors = [], [], []
    for k in order:
        if k in comm_mix:
            labels.append(label_map[k]); values.append(comm_mix[k]); colors.append(COMM_COLORS[k])
    if not values: return ""
    return (
        f"registerChart(new Chart(document.getElementById('{canvas_id}'), {{"
        f"type:'doughnut',"
        f"data:{{labels:{json.dumps(labels)},datasets:[{{data:{json.dumps(values)},"
        f"backgroundColor:{json.dumps(colors)},borderWidth:1,borderColor:'rgba(0,0,0,0.2)'}}]}},"
        f"options:{{responsive:true,maintainAspectRatio:false,"
        f"plugins:{{legend:{{position:'right',labels:{{font:{{size:10}},boxWidth:12,padding:5,"
        f"color:getColors().text}}}},"
        f"tooltip:{{callbacks:{{label:function(c){{return c.label+': '+c.raw.toFixed(1)+'%';}}}}}}}}}}}}));"
    )


def build_terminal_card(t, ta, card_idx):
    key   = t["key"]
    cid   = "comm_" + re.sub(r"[^a-z0-9]", "_", key.lower())
    disp  = t["display"]
    op    = t["operator"]
    mile  = t["mile"]
    bank  = t["bank"]
    cap   = t["cap"]
    spout = t["spouts"]
    vc    = ta.get("vessel_class","N/A")
    lv    = ta.get("loading_records",0)
    uv    = ta.get("unique_vessels",0)
    med   = ta.get("median_mt")
    p25   = ta.get("p25_mt")
    p75   = ta.get("p75_mt")
    wait  = ta.get("median_wait")
    load  = ta.get("median_load")
    dmin  = ta.get("delay_min")
    dmax  = ta.get("delay_max")
    cm    = ta.get("comm_mix",{})

    # Destination bars
    dest_rows = ""
    max_cnt = ta["top_dests"][0][1] if ta.get("top_dests") else 1
    for dest, cnt in (ta.get("top_dests") or [])[:5]:
        pct = cnt / max_cnt * 100
        dest_rows += (
            f'<div style="margin-bottom:5px">'
            f'<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text)">'
            f'<span>{dest}</span><span style="color:var(--text-muted)">{cnt}</span></div>'
            f'<div style="background:var(--surface3);border-radius:3px;height:5px">'
            f'<div style="background:{t["color"]};width:{pct:.0f}%;height:100%;border-radius:3px"></div>'
            f'</div></div>'
        )

    # Cargo size bar
    if med and p25 and p75:
        bar_min, bar_max = 15000, 80000
        def ppos(v): return max(0, min(100, (v-bar_min)/(bar_max-bar_min)*100))
        p25p, medp, p75p = ppos(p25), ppos(med), ppos(p75)
        iqr_left  = p25p
        iqr_width = p75p - p25p
        size_bar = (
            f'<div style="position:relative;height:16px;background:var(--surface3);border-radius:4px;margin:6px 0">'
            f'<div style="position:absolute;left:{iqr_left:.1f}%;width:{iqr_width:.1f}%;'
            f'height:100%;background:{t["color"]};opacity:0.4;border-radius:3px"></div>'
            f'<div style="position:absolute;left:{medp:.1f}%;width:3px;height:100%;'
            f'background:{t["color"]};border-radius:2px"></div>'
            f'</div>'
            f'<div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted)">'
            f'<span>15K MT</span>'
            f'<span style="color:{t["color"]};font-weight:700">{med:,} MT median</span>'
            f'<span>80K MT</span></div>'
        )
    else:
        size_bar = '<div style="color:var(--text-dim);font-size:11px;padding:6px 0">Cargo size data limited</div>'

    # Tier
    mt_total = ta.get("total_mt_k",0) or 0
    if mt_total >= 6000 or lv >= 300:
        tier_badge = '<span style="background:#1565C0;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 1 — Major</span>'
    elif mt_total >= 2000 or lv >= 130:
        tier_badge = '<span style="background:#388E3C;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 2 — Active</span>'
    else:
        tier_badge = '<span style="background:#607D8B;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 3 — Specialty</span>'

    wait_str  = f"{wait:.0f}d" if wait else "N/A"
    load_str  = f"{load:.0f}d" if load else "N/A"
    delay_str = (f"{dmin:.0f}–{dmax:.0f}d"
                 if dmin is not None and dmax is not None else "N/A")

    def badge(label, value, color="var(--text)"):
        return (f'<div class="stat-badge">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-value" style="color:{color}">{value}</div></div>')

    card = (
        f'<div class="terminal-card" id="t_{card_idx}" style="border-left:4px solid {t["color"]}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">'
        f'<div>'
        f'<h3 style="margin:0;font-size:17px;color:var(--text)">{disp}</h3>'
        f'<span style="color:var(--text-muted);font-size:13px">{op}</span>'
        f'&nbsp;&nbsp;{tier_badge}'
        f'</div>'
        f'<div style="text-align:right;font-size:12px;color:var(--text-muted)">'
        f'Mile Marker <b style="font-size:15px;color:{t["color"]}">{mile}</b> AHP &nbsp;|&nbsp; {bank}'
        f'<br>Cap: <b>{cap}</b> &nbsp;|&nbsp; Spouts: <b>{spout}</b>'
        f'</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:16px">'
        f'<div>'
        f'<div class="section-label">CARGO SIZE — P25 / MEDIAN / P75</div>'
        f'{size_bar}'
        f'<div class="section-label" style="margin-top:14px">TOP DESTINATIONS</div>'
        f'{dest_rows if dest_rows else "<div style=\"color:var(--text-dim);font-size:11px\">No destination data</div>"}'
        f'</div>'
        f'<div>'
        f'<div class="section-label">COMMODITY MIX (2025 LOADING)</div>'
        f'<div style="height:130px"><canvas id="{cid}"></canvas></div>'
        f'<div class="section-label" style="margin-top:12px">OPERATIONAL PROFILE</div>'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap">'
        f'{badge("Vessels", f"{uv:,}", t["color"])}'
        f'{badge("Loads", f"{lv:,}", t["color"])}'
        f'{badge("Class", vc.split("/")[0].strip(), "var(--text)")}'
        f'{badge("Queue Wait", wait_str, "#E65100")}'
        f'{badge("Load Time", load_str, "#1565C0")}'
        f'{badge("Dock Delay", delay_str, "#6A1B9A")}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return card, comm_donut_js(cid, cm)

# ─── MAIN HTML BUILDER ───────────────────────────────────────────────────────
def build_main_html(q, ta, mrtis, river_iframe, world_iframe, barge_iframe):
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
    pt       = mrtis["port_time"]
    anchs    = mrtis["anchorages"]
    monthly_anch = mrtis["monthly"]

    # ── Operator legend
    seen_ops = {}
    for t in TERMINALS:
        if t["operator"] not in seen_ops: seen_ops[t["operator"]] = t["color"]
    op_legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin:4px 8px;font-size:12px">'
        f'<span style="width:12px;height:12px;border-radius:50%;background:{col};display:inline-block"></span>'
        f'{op}</span>'
        for op, col in seen_ops.items()
    )

    # ── Terminal cards
    terminal_cards_html = ""
    chart_scripts = []
    for idx, t in enumerate(TERMINALS):
        card_html, chart_js = build_terminal_card(t, ta[t["key"]], idx)
        terminal_cards_html += card_html
        chart_scripts.append(chart_js)

    # ── Vessel size histogram
    cargo_df = q["all_cargo_sizes"]
    bins = list(range(5000, 90001, 5000))
    labels_h = [f"{b//1000}K" for b in bins[:-1]]
    counts_h = [int(((cargo_df["mt_numeric"]>=bins[i])&(cargo_df["mt_numeric"]<bins[i+1])).sum())
                for i in range(len(bins)-1)]

    # ── Loading ranking
    ls_s = ls.sort_values("loading_records", ascending=True)
    rank_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in ls_s["terminal_name"]]
    rank_vals   = ls_s["loading_records"].tolist()
    rank_colors = [TERM_KEY_MAP.get(k,{}).get("color","#607D8B") for k in ls_s["terminal_name"]]

    # ── Queue wait
    qw = q["queue_wait"].sort_values("median_wait", ascending=False)
    qw_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in qw["terminal_name"]]
    qw_vals   = qw["median_wait"].tolist()

    # ── Load duration
    ld = q["load_duration"].sort_values("median_load_days", ascending=False)
    ld_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in ld["terminal_name"]]
    ld_vals   = ld["median_load_days"].tolist()

    # ── Monthly throughput (3 grains)
    grains_shown  = ["CORN","SOYBEANS","WHEAT"]
    month_labels  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep"]
    months        = list(range(1, 10))
    g_colors      = {"CORN":"#FDD835","SOYBEANS":"#F9A825","WHEAT":"#D4AC0D"}
    monthly_ds    = []
    for g in grains_shown:
        gdf = fgis_mo[fgis_mo["grain"]==g].set_index("mo")
        vals = [round(float(gdf.loc[m,"mt_m"]) if m in gdf.index else 0, 3) for m in months]
        monthly_ds.append({"label":g.capitalize(),"data":vals,
                           "borderColor":g_colors[g],"backgroundColor":g_colors[g]+"33",
                           "fill":True,"tension":0.4})

    # ── MRTIS / Anchorage charts data
    anch_zones  = [a["zone"] for a in anchs[:8]]
    anch_avg    = [a["avg_h"] for a in anchs[:8]]
    anch_med    = [a["med_h"] for a in anchs[:8]]
    anch_visits = [a["visits"] for a in anchs[:8]]
    mo_keys  = sorted(monthly_anch.keys())
    mo_vals  = [monthly_anch[k] for k in mo_keys]
    mo_lbls  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # ── River stages
    carrollton_vals    = [RIVER_STAGES["Carrollton"][i] for i in range(1,13)]
    donaldsonville_vals= [RIVER_STAGES["Donaldsonville"][i] for i in range(1,13)]

    # ── Barge corridors
    corr_names  = [c["name"] for c in BARGE_CORRIDORS]
    corr_pcts   = [c["pct"]  for c in BARGE_CORRIDORS]
    corr_colors = [c["color"] for c in BARGE_CORRIDORS]

    # ── FGIS destinations table
    top_dest_rows = ""
    for i, (_, row) in enumerate(fgis_d.head(20).iterrows()):
        top_dest_rows += (f"<tr><td>{i+1}</td><td><b>{row['destination']}</b></td>"
                          f"<td>{row['mt_m']:.2f} MMT</td><td>{row['certs']:,}</td></tr>")

    # ── Grade table
    grade_rows = ""
    for grain in ["CORN","SOYBEANS","WHEAT"]:
        gdf = fgis_g[fgis_g["grain"]==grain]
        total_g = gdf["mt_m"].sum()
        for _, row in gdf.iterrows():
            pct = row["mt_m"]/total_g*100 if total_g > 0 else 0
            grade_rows += (f"<tr><td>{grain.capitalize()}</td><td>{row['grade']}</td>"
                           f"<td>{row['mt_m']:.2f} MMT</td><td>{pct:.1f}%</td>"
                           f"<td>{row['certs']:,}</td></tr>")

    # ── Quality table
    qual_rows = ""
    for _, row in fgis_q.iterrows():
        prot_str = "N/A" if pd.isna(row["protein"]) else f"{row['protein']:.1f}%"
        tw_str   = "N/A" if pd.isna(row["test_wt"])  else f"{row['test_wt']:.1f} lb/bu"
        qual_rows += (f"<tr><td><b>{row['grain'].capitalize()}</b></td>"
                      f"<td>{row['moisture']:.1f}%</td><td>{row['fm']:.2f}%</td>"
                      f"<td>{prot_str}</td><td>{tw_str}</td><td>{row['n']:,}</td></tr>")

    # ── Top shipments
    ship_rows = ""
    for i, (_, row) in enumerate(fgis_top.head(20).iterrows()):
        ship_rows += (f"<tr><td>{i+1}</td><td><b>{row['vessel']}</b></td>"
                      f"<td>{row['grain'].capitalize()}</td><td>{row['destination']}</td>"
                      f"<td>{row['mt']:,.0f}</td><td>{row['cert_date']}</td></tr>")

    # ── Market share pie
    ms_labels, ms_vals, ms_colors = [], [], []
    for t in TERMINALS:
        mv = ta[t["key"]].get("total_mt_k",0) or 0
        if mv > 0:
            ms_labels.append(t["display"]); ms_vals.append(int(mv)); ms_colors.append(t["color"])

    # ── FGIS grain mix for hero
    def fgis_val(grain):
        row = fgis_gm[fgis_gm["grain"]==grain]
        return row["mt_m"].values[0] if len(row) else 0.0

    anchor_pct = round(pt["anchor"] / pt["total"] * 100) if pt["total"] else 39

    # ── NAV sidebar
    sidebar_items = [
        ("#s-cover",       "01 — Overview"),
        ("#s-map",         "02 — River Map"),
        ("#s-terminals",   "03 — Terminal Profiles"),
        ("#s-analytics",   "04 — Vessel Analytics"),
        ("#s-anchorage",   "05 — Anchorage Intelligence"),
        ("#s-river",       "06 — River Conditions"),
        ("#s-barge",       "07 — Barge Origins"),
        ("#s-world",       "08 — Global Trade Flows"),
        ("#s-commodity",   "09 — Commodity Intelligence"),
        ("#s-quality",     "10 — Quality & Certification"),
        ("#s-rankings",    "11 — Terminal Rankings"),
    ]
    nav_links = "".join(
        f'<li><a class="nav-link" href="{h}">{l}</a></li>'
        for h, l in sidebar_items
    )

    # ── All Chart.js scripts (assembled at end of HTML body)
    all_scripts = "\n".join(chart_scripts)

    # ── Seasonal grain callout
    seasonal_note = (
        "Soybean loading peaks Jan–Mar (Southern Hemisphere off-season). "
        "Corn dominates Apr–Aug. Wheat exports strongest Mar–May ahead of US harvest."
    )

    # ─────────────────────────────────────────────────────────────────────────
    # CSS
    # ─────────────────────────────────────────────────────────────────────────
    css = """
:root {
  --bg:#08131F; --surface:#0F1F30; --surface2:#172840; --surface3:#1E3352;
  --border:rgba(255,255,255,0.07); --text:#D8E6F0; --text-muted:#7898B8;
  --text-dim:#3D5870; --accent:#F0A500; --blue:#3B7DD8;
  --sidebar-bg:#060F1A; --sidebar-text:rgba(255,255,255,0.72); --sidebar-active:#F0A500;
  --card-shadow:0 2px 16px rgba(0,0,0,0.5); --chart-grid:rgba(255,255,255,0.05);
  --chart-text:#7898B8; --kpi-bg:rgba(255,255,255,0.10); --kpi-border:rgba(255,255,255,0.18);
  --tbl-head:#060F1A; --tbl-alt:rgba(255,255,255,0.03); --tag-bg:rgba(255,255,255,0.08);
  --sidebar-w:252px;
}
[data-theme="light"] {
  --bg:#EEF2F7; --surface:#FFF; --surface2:#F0F4F9; --surface3:#E4EBF3;
  --border:rgba(0,0,0,0.09); --text:#1C2B3A; --text-muted:#4A6275; --text-dim:#8AAABE;
  --accent:#C07E00; --blue:#1565C0;
  --sidebar-bg:#0A1828; --card-shadow:0 2px 8px rgba(0,0,0,0.09);
  --chart-grid:rgba(0,0,0,0.07); --chart-text:#4A6275;
  --kpi-bg:rgba(255,255,255,0.6); --kpi-border:rgba(0,0,0,0.12);
  --tbl-head:#0A1828; --tbl-alt:rgba(0,0,0,0.02); --tag-bg:rgba(0,0,0,0.06);
}
@media print {
  :root,[data-theme]{
    --bg:#fff!important;--surface:#fff!important;--surface2:#f5f7fa!important;
    --surface3:#eff2f6!important;--border:rgba(0,0,0,0.12)!important;
    --text:#000!important;--text-muted:#333!important;--card-shadow:none!important;
  }
  #sidebar{display:none!important}
  #main{margin-left:0!important}
  .map-container,.print-hide{display:none!important}
  .terminal-card{break-inside:avoid}
  @page{margin:1.5cm}
}
*{box-sizing:border-box}
html,body{margin:0;font-family:"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text)}
#sidebar{
  position:fixed;left:0;top:0;width:var(--sidebar-w);height:100vh;
  background:var(--sidebar-bg);overflow-y:auto;z-index:1000;
  padding:20px 0;display:flex;flex-direction:column;
}
.sb-logo{padding:16px 20px 12px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:8px}
.sb-title{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:1px;text-transform:uppercase}
.sb-sub{font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px}
.nav-link{display:block;padding:9px 20px;color:var(--sidebar-text);font-size:12px;
  text-decoration:none;transition:.15s;border-left:3px solid transparent}
.nav-link:hover,.nav-link.active{color:#fff;background:rgba(255,255,255,0.07);
  border-left-color:var(--accent)}
.sb-footer{margin-top:auto;padding:14px 20px;border-top:1px solid rgba(255,255,255,0.1);
  font-size:10px;color:rgba(255,255,255,0.35)}
#main{margin-left:var(--sidebar-w)}
.hero{
  background:linear-gradient(135deg,#06101B 0%,#0D1E32 50%,#152840 100%);
  color:#fff;padding:56px 48px 48px;
}
.hero h1{font-size:27px;font-weight:800;margin:0;line-height:1.3}
.hero .sub{font-size:14px;color:rgba(255,255,255,0.6);margin-top:6px}
.kpi-card{background:var(--kpi-bg);border:1px solid var(--kpi-border);
  border-radius:12px;padding:18px 14px;text-align:center;backdrop-filter:blur(4px)}
.kpi-num{font-size:32px;font-weight:800;color:#fff;line-height:1}
.kpi-unit{font-size:18px;font-weight:600}
.kpi-label{font-size:11px;color:var(--accent);font-weight:700;margin-top:4px;
  letter-spacing:.5px;text-transform:uppercase}
.kpi-sub{font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px}
.section{background:var(--surface);padding:40px 48px;border-bottom:1px solid var(--border)}
.section-alt{background:var(--surface2);padding:40px 48px;border-bottom:1px solid var(--border)}
.section-title{font-size:20px;font-weight:800;color:var(--text);margin-bottom:4px}
.section-sub{font-size:13px;color:var(--text-muted);margin-bottom:24px}
.section-label{font-size:11px;font-weight:700;color:var(--text-muted);
  letter-spacing:.5px;text-transform:uppercase;margin-bottom:6px}
.terminal-card{background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:var(--card-shadow)}
.stat-badge{background:var(--surface2);border-radius:6px;padding:6px 8px;
  text-align:center;min-width:62px;flex:0 0 auto}
.stat-label{font-size:10px;color:var(--text-muted)}
.stat-value{font-size:13px;font-weight:700}
.chart-box{position:relative;height:340px}
.chart-box-sm{position:relative;height:260px}
.tbl{font-size:12px;width:100%;border-collapse:collapse}
.tbl th{background:var(--tbl-head);color:#fff;padding:8px 10px;font-size:11px;
  letter-spacing:.4px;text-transform:uppercase}
.tbl td{padding:7px 10px;border-bottom:1px solid var(--border);color:var(--text)}
.tbl tr:nth-child(even) td{background:var(--tbl-alt)}
.tbl tr:hover td{background:var(--surface3)}
.info-card{background:var(--surface2);border:1px solid var(--border);
  border-radius:10px;padding:18px;margin-bottom:16px}
.kpi-inline{background:var(--surface2);border-radius:10px;padding:14px 18px;
  display:inline-flex;flex-direction:column;align-items:center;min-width:100px;text-align:center}
.kpi-inline .val{font-size:26px;font-weight:800;color:var(--text)}
.kpi-inline .lbl{font-size:11px;color:var(--text-muted);margin-top:2px;text-transform:uppercase}
.insight-tag{display:inline-block;background:var(--tag-bg);border:1px solid var(--border);
  border-radius:4px;padding:3px 9px;font-size:11px;color:var(--text-muted);margin:3px 4px}
.map-container{border-radius:10px;overflow:hidden;border:1px solid var(--border)}
#ctrl-bar{padding:14px 48px;background:var(--surface2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:900}
.ctrl-btn{background:var(--surface3);border:1px solid var(--border);color:var(--text);
  border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer;
  font-family:inherit;transition:.15s}
.ctrl-btn:hover{background:var(--surface);border-color:var(--accent);color:var(--accent)}
@media(max-width:900px){#sidebar{width:100%;height:auto;position:relative}#main{margin-left:0}}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # JS
    # ─────────────────────────────────────────────────────────────────────────
    js_theme = r"""
window.chartInstances=[];
function registerChart(ch){if(ch)window.chartInstances.push(ch);return ch;}
function getColors(){
  var dark=document.documentElement.getAttribute('data-theme')!=='light';
  return{text:dark?'#7898B8':'#4A6275',grid:dark?'rgba(255,255,255,0.05)':'rgba(0,0,0,0.07)'};
}
function applyThemeToCharts(){
  var c=getColors();
  window.chartInstances.forEach(function(ch){
    try{
      if(ch.options&&ch.options.scales){
        Object.values(ch.options.scales).forEach(function(s){
          if(s.ticks)s.ticks.color=c.text;
          if(s.grid){s.grid.color=c.grid;s.grid.borderColor=c.grid;}
        });
      }
      if(ch.options&&ch.options.plugins&&ch.options.plugins.legend&&ch.options.plugins.legend.labels){
        ch.options.plugins.legend.labels.color=c.text;
      }
      ch.update('none');
    }catch(e){}
  });
}
function toggleTheme(){
  var html=document.documentElement;
  var next=html.getAttribute('data-theme')==='dark'?'light':'dark';
  html.setAttribute('data-theme',next);
  localStorage.setItem('grainRptTheme',next);
  var btn=document.getElementById('theme-btn');
  if(btn)btn.textContent=next==='dark'?'\u2600 Light':'\uD83C\uDF19 Dark';
  applyThemeToCharts();
}
function printReport(){window.print();}
(function(){
  var saved=localStorage.getItem('grainRptTheme')||'dark';
  document.documentElement.setAttribute('data-theme',saved);
  document.addEventListener('DOMContentLoaded',function(){
    var btn=document.getElementById('theme-btn');
    if(btn)btn.textContent=saved==='dark'?'\u2600 Light':'\uD83C\uDF19 Dark';
    setTimeout(applyThemeToCharts,300);
  });
})();
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Chart.js scripts (all sections)
    # ─────────────────────────────────────────────────────────────────────────
    chart_js_all = all_scripts + f"""

// Vessel size histogram
registerChart(new Chart(document.getElementById('hist_vessel_size'),{{
  type:'bar',
  data:{{labels:{json.dumps(labels_h)},
    datasets:[{{label:'Vessel Count',data:{json.dumps(counts_h)},
      backgroundColor:'rgba(59,125,216,0.7)',borderColor:'#3B7DD8',borderWidth:1}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Vessel Cargo Size Distribution — All Miss. River 2025',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Vessel Count',color:getColors().text}}}}}}}}}}));

// Queue wait bar
registerChart(new Chart(document.getElementById('chart_queue'),{{
  type:'bar',
  data:{{labels:{json.dumps(qw_labels)},
    datasets:[{{label:'Median Wait Days',data:{json.dumps(qw_vals)},
      backgroundColor:'rgba(230,81,0,0.7)',borderColor:'#E65100',borderWidth:1}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Median Queue Wait (ETA → Loading)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Days',color:getColors().text}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:10}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Load duration bar
registerChart(new Chart(document.getElementById('chart_load_dur'),{{
  type:'bar',
  data:{{labels:{json.dumps(ld_labels)},
    datasets:[{{label:'Median Load Days',data:{json.dumps(ld_vals)},
      backgroundColor:'rgba(21,101,192,0.7)',borderColor:'#1565C0',borderWidth:1}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Median Loading Duration per Vessel Visit',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Days',color:getColors().text}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:10}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Monthly throughput stacked area
registerChart(new Chart(document.getElementById('chart_monthly'),{{
  type:'line',
  data:{{labels:{json.dumps(month_labels)},
    datasets:{json.dumps(monthly_ds)}}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Monthly Export Volume by Grain — 2025 (MMT)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{stacked:false,ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'MMT',color:getColors().text}}}}}}}}}}));

// Terminal rankings bar
registerChart(new Chart(document.getElementById('chart_rankings'),{{
  type:'bar',
  data:{{labels:{json.dumps(rank_labels)},
    datasets:[{{label:'Loading Records',data:{json.dumps(rank_vals)},
      backgroundColor:{json.dumps(rank_colors)},borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'2025 Loading Records by Terminal',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Market share doughnut
registerChart(new Chart(document.getElementById('chart_mktshare'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(ms_labels)},
    datasets:[{{data:{json.dumps(ms_vals)},backgroundColor:{json.dumps(ms_colors)},
      borderWidth:2,borderColor:'var(--surface)'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{font:{{size:10}},boxWidth:12,color:getColors().text}}}},
      title:{{display:true,text:'Estimated Market Share by Loading Volume',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}}}}}}));

// MRTIS — Port time doughnut
registerChart(new Chart(document.getElementById('chart_porttime'),{{
  type:'doughnut',
  data:{{labels:['Transit','Anchor Wait','Terminal Operations'],
    datasets:[{{data:[{pt['transit']},{pt['anchor']},{pt['terminal']}],
      backgroundColor:['rgba(66,165,245,0.85)','rgba(255,152,0,0.85)','rgba(76,175,80,0.85)'],
      borderWidth:2,borderColor:'var(--surface)'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{font:{{size:11}},boxWidth:14,color:getColors().text}}}},
      tooltip:{{callbacks:{{label:function(c){{return c.label+': '+c.raw+'h ('+Math.round(c.raw/{pt['total']}*100)+'%)';}}}}}}}}}}}}));

// MRTIS — Anchorage wait bar (avg & median)
registerChart(new Chart(document.getElementById('chart_anchorage'),{{
  type:'bar',
  data:{{labels:{json.dumps(anch_zones)},
    datasets:[
      {{label:'Avg Hours',data:{json.dumps(anch_avg)},backgroundColor:'rgba(255,152,0,0.8)',borderWidth:0}},
      {{label:'Median Hours',data:{json.dumps(anch_med)},backgroundColor:'rgba(255,213,79,0.8)',borderWidth:0}}
    ]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Anchorage Wait Time — 2025 (Hours)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Hours',color:getColors().text}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// MRTIS — Monthly congestion line
registerChart(new Chart(document.getElementById('chart_monthly_anch'),{{
  type:'line',
  data:{{labels:{json.dumps(mo_lbls[:len(mo_vals)])},
    datasets:[{{label:'Avg Anchor Wait (hrs)',data:{json.dumps(mo_vals)},
      borderColor:'#FF9800',backgroundColor:'rgba(255,152,0,0.15)',
      fill:true,tension:0.4,pointRadius:5,pointBackgroundColor:'#FF9800'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Monthly Anchorage Congestion — 2025 (Avg Hours)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                min:0,title:{{display:true,text:'Hours',color:getColors().text}}}}}}}}}}));

// River stages
registerChart(new Chart(document.getElementById('chart_river_stages'),{{
  type:'bar',
  data:{{labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    datasets:[
      {{label:'Carrollton (USGS)',data:{json.dumps(carrollton_vals)},
        backgroundColor:'rgba(66,165,245,0.7)',borderColor:'#42A5F5',borderWidth:1}},
      {{label:'Donaldsonville',data:{json.dumps(donaldsonville_vals)},
        backgroundColor:'rgba(38,198,218,0.7)',borderColor:'#26C6DA',borderWidth:1}}
    ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Mississippi River Stage — Historical Monthly Averages (Feet)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Feet (NGVD29)',color:getColors().text}}}}}}}}}}));

// Barge corridor bar
registerChart(new Chart(document.getElementById('chart_barge_corr'),{{
  type:'bar',
  data:{{labels:{json.dumps(corr_names)},
    datasets:[{{label:'Est. % of Barge Volume',data:{json.dumps(corr_pcts)},
      backgroundColor:{json.dumps(corr_colors)},borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Barge Volume by Origin Corridor (Estimated)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'% of Total Barge Volume',color:getColors().text}},max:45}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Assemble full HTML
    # ─────────────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lower Mississippi River — Grain Export Elevator Intelligence Report 2025</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
{css}
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav id="sidebar">
  <div class="sb-logo">
    <div class="sb-title">Lower Mississippi River</div>
    <div class="sb-sub">Grain Elevator Intelligence &nbsp;|&nbsp; 2025</div>
  </div>
  <ul style="list-style:none;padding:0;margin:0">{nav_links}</ul>
  <div class="sb-footer">Confidential &nbsp;|&nbsp; {BUILD_DATE}</div>
</nav>

<!-- MAIN -->
<div id="main">

<!-- CONTROL BAR -->
<div id="ctrl-bar" class="print-hide">
  <span style="font-size:12px;color:var(--text-muted);font-weight:600;letter-spacing:.5px">
    LOWER MISSISSIPPI RIVER — GRAIN ELEVATOR GUIDE 2025
  </span>
  <div style="margin-left:auto;display:flex;gap:8px">
    <button class="ctrl-btn" id="theme-btn" onclick="toggleTheme()">&#9728; Light</button>
    <button class="ctrl-btn" onclick="printReport()">&#128438; Print</button>
  </div>
</div>

<!-- ══ 01 COVER ══════════════════════════════════════════════════════════════ -->
<section class="hero" id="s-cover">
  <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 12px;
     letter-spacing:1px;text-transform:uppercase">
    Lower Mississippi River &nbsp;·&nbsp; Export Grain Elevator Intelligence
  </p>
  <h1>Lower Mississippi River<br>Grain Export Elevator Guide</h1>
  <p class="sub">2025 Operational Intelligence &nbsp;·&nbsp; 12 Terminals &nbsp;·&nbsp; MM 57 to MM 229 AHP</p>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:32px">
    <div class="kpi-card">
      <div class="kpi-num">{total_mt:.1f}<span class="kpi-unit"> MMT</span></div>
      <div class="kpi-label">Certified Export Volume</div>
      <div class="kpi-sub">FGIS Jan–Sep 2025</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num">{fgis_v:,}</div>
      <div class="kpi-label">Certificated Vessels</div>
      <div class="kpi-sub">Unique vessels with export certs</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num">12</div>
      <div class="kpi-label">Terminals Profiled</div>
      <div class="kpi-sub">MM 57 to MM 229 AHP</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num">{anchor_pct}%</div>
      <div class="kpi-label">Port Time at Anchor</div>
      <div class="kpi-sub">Avg {pt['anchor']}h anchor / {pt['total']}h total</div>
    </div>
  </div>
  <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap">
    <span style="background:rgba(255,255,255,0.1);border-radius:8px;padding:9px 16px;font-size:13px">
      <b>Corn</b> {fgis_val('CORN'):.1f}M MT &nbsp;|&nbsp;
      <b>Soybeans</b> {fgis_val('SOYBEANS'):.1f}M MT &nbsp;|&nbsp;
      <b>Wheat</b> {fgis_val('WHEAT'):.1f}M MT
    </span>
    <span style="background:rgba(255,255,255,0.1);border-radius:8px;padding:9px 16px;font-size:13px">
      <b>Top Markets:</b> Mexico · China · Colombia · Japan · Egypt
    </span>
  </div>
</section>

<!-- ══ 02 RIVER MAP ══════════════════════════════════════════════════════════ -->
<section class="section" id="s-map">
  <h2 class="section-title">River Map — Terminal Locations</h2>
  <p class="section-sub">12 grain export terminals along the Lower Mississippi River, MM 57–229.
     Toggle layers (top-right) to show anchorages or switch base tile.
     Click markers for terminal details.</p>
  <div style="margin-bottom:12px;padding:10px 14px;background:var(--surface2);
     border-radius:8px;font-size:12px;color:var(--text)">
    <b style="color:var(--text-muted)">Operators:</b>&nbsp;{op_legend}
  </div>
  <div class="map-container">{river_iframe}</div>
</section>

<!-- ══ 03 TERMINAL PROFILES ══════════════════════════════════════════════════ -->
<section class="section-alt" id="s-terminals">
  <h2 class="section-title">Terminal Profiles</h2>
  <p class="section-sub">Individual profiles — downstream (MM 57) to upstream (MM 229).
     Cargo bars show P25/Median/P75 range. Queue wait and load duration derived from
     daily lineup position data.</p>
  {terminal_cards_html}
</section>

<!-- ══ 04 VESSEL ANALYTICS ═══════════════════════════════════════════════════ -->
<section class="section" id="s-analytics">
  <h2 class="section-title">Vessel &amp; Cargo Analytics</h2>
  <p class="section-sub">Fleet-wide cargo size distribution, queue wait, and loading duration
     across all Lower Mississippi terminals, 2025.</p>
  <div class="row g-4">
    <div class="col-md-6">
      <div class="chart-box"><canvas id="hist_vessel_size"></canvas></div>
    </div>
    <div class="col-md-6">
      <div class="info-card">
        <h5 style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:12px">Vessel Class Reference</h5>
        <table class="tbl">
          <tr><th>Class</th><th>Cargo Range</th><th>Typical Trade</th></tr>
          <tr><td><b>Handymax</b></td><td>25,000–39,999 MT</td><td>Short-haul, Caribbean</td></tr>
          <tr><td><b>Supramax</b></td><td>40,000–57,999 MT</td><td>Panamax lanes</td></tr>
          <tr><td><b>Panamax</b></td><td>58,000–79,999 MT</td><td>Transoceanic bulk</td></tr>
          <tr><td><b>Capesize</b></td><td>80,000+ MT</td><td>Long-haul, Asia</td></tr>
        </table>
        <p style="font-size:12px;color:var(--text-muted);margin-top:12px">
          Lower Miss. median: ~50,000 MT (Panamax/Supramax dominant).
          Midstream float terminals (MGMT, Cooper, Wood Buoys) average Handymax.
        </p>
      </div>
    </div>
    <div class="col-md-6">
      <div class="chart-box"><canvas id="chart_queue"></canvas></div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:6px">
        Queue wait = ETA first appearance → first LOADING date, capped at 30 days per voyage.
      </p>
    </div>
    <div class="col-md-6">
      <div class="chart-box"><canvas id="chart_load_dur"></canvas></div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:6px">
        Load duration = median consecutive LOADING report days per vessel visit.
      </p>
    </div>
  </div>
  <h4 style="font-size:16px;font-weight:700;margin:32px 0 12px;color:var(--text)">
    Largest Single Shipments — 2025</h4>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr><th>#</th><th>Vessel</th><th>Grain</th><th>Destination</th><th>Metric Tons</th><th>Cert Date</th></tr>
      {ship_rows}
    </table>
  </div>
</section>

<!-- ══ 05 ANCHORAGE INTELLIGENCE ═════════════════════════════════════════════ -->
<section class="section-alt" id="s-anchorage">
  <h2 class="section-title">Anchorage &amp; Transit Intelligence</h2>
  <p class="section-sub">Vessel movement data across the Lower Mississippi approach: time at anchor
     before berthing, congestion patterns by location, and seasonal trends — 2025.</p>

  <div class="row g-4 mb-4">
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val">{pt['total']:.0f}h</span>
        <span class="lbl">Avg Total Port Time</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#FF9800">{pt['anchor']:.0f}h</span>
        <span class="lbl">Avg Anchor Wait</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#4CAF50">{pt['terminal']:.0f}h</span>
        <span class="lbl">Avg Terminal Time</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#42A5F5">{pt['transit']:.0f}h</span>
        <span class="lbl">Avg Transit Time</span>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-md-5">
      <div class="chart-box-sm"><canvas id="chart_porttime"></canvas></div>
      <div style="margin-top:12px;padding:12px;background:var(--surface2);
           border-radius:8px;font-size:12px;color:var(--text-muted)">
        <b style="color:var(--accent)">Key Insight:</b>
        Vessels spend approximately <b style="color:var(--text)">{anchor_pct}% of total port time
        waiting at anchor</b> before reaching a berth — a critical factor in demurrage
        planning and vessel scheduling windows.
      </div>
    </div>
    <div class="col-md-7">
      <div class="chart-box"><canvas id="chart_anchorage"></canvas></div>
    </div>
  </div>

  <div class="row g-4 mt-2">
    <div class="col-12">
      <div class="chart-box-sm"><canvas id="chart_monthly_anch"></canvas></div>
      <p style="font-size:12px;color:var(--text-muted);margin-top:8px">
        <b>Seasonal pattern:</b> Peak congestion Feb (avg ~94h) coincides with South American
        soybean harvest window and pre-planting US corn-belt barge fleet buildup.
        Summer low (Jun–Jul, ~44–45h) reflects reduced harvest pressure and lower river traffic density.
      </p>
    </div>
  </div>

  <div class="row g-4 mt-2">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Key Anchorage Locations — 2025 Activity</h4>
      <table class="tbl">
        <tr><th>Anchorage</th><th>2025 Visits</th><th>Avg Wait</th><th>Median Wait</th><th>Notes</th></tr>
""" + "".join(
        f"<tr><td><b>{a['zone']}</b></td><td>{a['visits']:,}</td>"
        f"<td>{a['avg_h']:.0f}h</td><td>{a['med_h']:.0f}h</td>"
        f"<td style='color:var(--text-muted);font-size:11px'>"
        f"{'Highest median wait — Davant staging area' if 'Davant' in a['zone'] else 'Inbound approach queue' if '9 Mile' in a['zone'] or '12 Mile' in a['zone'] else 'River staging'}</td></tr>"
        for a in anchs[:8]
    ) + f"""
      </table>
    </div>
  </div>
</section>

<!-- ══ 06 RIVER CONDITIONS ════════════════════════════════════════════════════ -->
<section class="section" id="s-river">
  <h2 class="section-title">River Conditions &amp; Seasonal Context</h2>
  <p class="section-sub">Gauge height and navigation context at key Lower Mississippi
     River measurement points — historical monthly averages.</p>

  <div class="row g-4">
    <div class="col-md-8">
      <div class="chart-box"><canvas id="chart_river_stages"></canvas></div>
    </div>
    <div class="col-md-4">
      <div class="info-card">
        <div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:10px">
          Navigation Implications
        </div>
        <div style="font-size:12px;color:var(--text-muted);line-height:1.7">
          <b style="color:#42A5F5">High water (Mar–May):</b> Accelerated current
          (3–5 kt vs. 1–2 kt at low water) increases fuel consumption for upstream
          movements and can restrict draft near Old River Control.<br><br>
          <b style="color:#FF9800">Low water (Jul–Oct):</b> Draft restrictions
          may apply below Carrollton. Sub-zero gauge readings at Carrollton can
          suspend loaded barge operations.<br><br>
          <b style="color:#66BB6A">Optimal loading window:</b> Dec–Feb at most
          terminals — moderate stage, good visibility, pre-South American harvest
          demand peak.
        </div>
      </div>
      <div class="info-card">
        <div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:8px">
          Fog &amp; Visibility
        </div>
        <div style="font-size:12px;color:var(--text-muted);line-height:1.7">
          New Orleans averages <b style="color:var(--text)">34 fog days/year</b>,
          concentrated Nov–Mar. River fog closures (Coast Guard VTS)
          typically last 2–8 hours and primarily affect the Lower Reach
          (Pilot Town → MM 30). Terminal operations above MM 57 are
          rarely impacted for more than one tidal cycle.
        </div>
      </div>
    </div>
  </div>

  <div class="row g-4 mt-2">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:10px">
        Seasonal Export Activity — Grain Type Intensity</h4>
      <div style="overflow-x:auto">
        <table class="tbl">
          <tr><th>Grain</th><th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th>
              <th>Jun</th><th>Jul</th><th>Aug</th><th>Sep</th><th>Peak Window</th></tr>
""" + _seasonal_grain_table(q["fgis_seasonal_grain"]) + f"""
        </table>
      </div>
      <p style="font-size:12px;color:var(--text-muted);margin-top:8px">{seasonal_note}</p>
    </div>
  </div>
</section>

<!-- ══ 07 BARGE ORIGINS ════════════════════════════════════════════════════════ -->
<section class="section-alt" id="s-barge">
  <h2 class="section-title">Barge Origin Corridors</h2>
  <p class="section-sub">Approximately 55–60% of grain exported via the Lower Mississippi
     arrives by inland barge from key production corridors. The map shows primary
     tributary flows converging at the Lower Mississippi grain complex.</p>

  <div class="row g-4">
    <div class="col-md-7">
      <div class="map-container">{barge_iframe}</div>
    </div>
    <div class="col-md-5">
      <div class="chart-box-sm"><canvas id="chart_barge_corr"></canvas></div>
      <div style="margin-top:14px">
        <table class="tbl">
          <tr><th>Corridor</th><th>Est. %</th><th>Primary Grains</th></tr>
""" + "".join(
        f"<tr><td style='border-left:3px solid {c['color']}'><b>{c['name']}</b></td>"
        f"<td>{c['pct']}%</td>"
        f"<td style='font-size:11px;color:var(--text-muted)'>{c['grains']}</td></tr>"
        for c in BARGE_CORRIDORS
    ) + f"""
        </table>
      </div>
    </div>
  </div>

  <div class="row g-4 mt-2">
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">55–60%</div>
        <div style="font-size:12px;color:var(--text-muted)">of Lower Miss. export grain<br>arrives via inland barge</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">35–38%</div>
        <div style="font-size:12px;color:var(--text-muted)">arrives by unit train<br>(shuttle and manifest)</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">5–7%</div>
        <div style="font-size:12px;color:var(--text-muted)">local truck delivery<br>(LA, MS production)</div>
      </div>
    </div>
  </div>
</section>

<!-- ══ 08 GLOBAL TRADE FLOWS ═══════════════════════════════════════════════════ -->
<section class="section" id="s-world">
  <h2 class="section-title">Global Trade Flows</h2>
  <p class="section-sub">Export destinations certified at Mississippi River ports, Jan–Sep 2025.
     Arc thickness proportional to certified tonnage. Click destination markers for detail.</p>
  <div class="map-container">{world_iframe}</div>
  <div class="row g-4 mt-3">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Top 20 Export Destinations — 2025</h4>
      <div style="overflow-x:auto">
        <table class="tbl">
          <tr><th>#</th><th>Destination</th><th>Volume (MMT)</th><th>Certificates</th></tr>
          {top_dest_rows}
        </table>
      </div>
    </div>
  </div>
</section>

<!-- ══ 09 COMMODITY INTELLIGENCE ══════════════════════════════════════════════ -->
<section class="section-alt" id="s-commodity">
  <h2 class="section-title">Commodity Intelligence</h2>
  <p class="section-sub">Monthly export volume trend by grain type and seasonal loading patterns,
     Lower Mississippi River, 2025.</p>
  <div class="row g-4">
    <div class="col-12">
      <div class="chart-box"><canvas id="chart_monthly"></canvas></div>
    </div>
  </div>
  <div class="row g-4 mt-2">
    <div class="col-12">
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px">
        <span class="insight-tag">Soybean peak: Jan–Mar (South American off-season demand)</span>
        <span class="insight-tag">Corn peak: Apr–Aug (post-US harvest flush)</span>
        <span class="insight-tag">Wheat: Mar–May (HRW/SRW pre-harvest marketing)</span>
        <span class="insight-tag">YSB+DDGS: specialty terminals year-round</span>
      </div>
    </div>
  </div>
</section>

<!-- ══ 10 QUALITY & CERTIFICATION ════════════════════════════════════════════ -->
<section class="section" id="s-quality">
  <h2 class="section-title">Quality &amp; Certification Intelligence</h2>
  <p class="section-sub">Export quality metrics from grain inspection certificates
     issued at Mississippi River ports, 2025.</p>
  <div class="row g-4">
    <div class="col-md-6">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Quality Metrics by Grain</h4>
      <table class="tbl">
        <tr><th>Grain</th><th>Moisture</th><th>FM%</th><th>Protein</th><th>Test Wt</th><th>Certs</th></tr>
        {qual_rows}
      </table>
    </div>
    <div class="col-md-6">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Grade Distribution</h4>
      <table class="tbl">
        <tr><th>Grain</th><th>Grade</th><th>Volume (MMT)</th><th>% Share</th><th>Certs</th></tr>
        {grade_rows}
      </table>
    </div>
  </div>
</section>

<!-- ══ 11 TERMINAL RANKINGS ═══════════════════════════════════════════════════ -->
<section class="section-alt" id="s-rankings">
  <h2 class="section-title">Terminal Rankings &amp; Market Position</h2>
  <p class="section-sub">Comparative terminal performance — 2025 loading activity
     and estimated market share by throughput volume.</p>
  <div class="row g-4">
    <div class="col-md-7">
      <div class="chart-box"><canvas id="chart_rankings"></canvas></div>
    </div>
    <div class="col-md-5">
      <div class="chart-box"><canvas id="chart_mktshare"></canvas></div>
    </div>
  </div>
</section>

</div><!-- /#main -->

<script>
{js_theme}
</script>
<script>
{chart_js_all}
</script>

</body>
</html>"""
    return html


def _seasonal_grain_table(df):
    """Build HTML rows for the seasonal grain intensity table."""
    months = list(range(1, 10))
    grains = ["CORN", "SOYBEANS", "WHEAT"]
    peak_window = {"CORN": "Apr–Aug", "SOYBEANS": "Jan–Mar", "WHEAT": "Mar–May"}
    rows = ""
    for g in grains:
        gdf = df[df["grain"] == g].set_index("mo")
        vals = [float(gdf.loc[m, "mt_m"]) if m in gdf.index else 0.0 for m in months]
        max_v = max(vals) if max(vals) > 0 else 1
        row = f"<tr><td><b>{g.capitalize()}</b></td>"
        for v in vals:
            intensity = int(v / max_v * 5)
            bg_alpha  = [0.05, 0.15, 0.3, 0.55, 0.75, 0.95][intensity]
            color_map = {"CORN": f"rgba(253,216,53,{bg_alpha})",
                         "SOYBEANS": f"rgba(249,168,37,{bg_alpha})",
                         "WHEAT": f"rgba(212,172,13,{bg_alpha})"}
            bg = color_map[g]
            row += (f'<td style="text-align:center;background:{bg};color:var(--text);font-size:11px">'
                    f'{v:.2f}</td>')
        row += f'<td style="font-size:11px;color:var(--text-muted)">{peak_window.get(g,"—")}</td></tr>'
        rows += row
    return rows


# ─── INTERNAL ANNEX ──────────────────────────────────────────────────────────
def build_internal_html(q, ta, mrtis):
    fgis_ov = q["fgis_overview"].iloc[0]
    total_mt = float(fgis_ov["total_mt_m"])
    pt = mrtis["port_time"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>INTERNAL — Lower Miss. Grain Elevator Guide 2025 — Methodology &amp; Sources</title>
<style>
body{{font-family:"Segoe UI",system-ui,sans-serif;max-width:1000px;margin:40px auto;
  padding:0 30px;background:#F8F9FA;color:#212529}}
h1{{font-size:22px;color:#0D1B2A}}h2{{font-size:17px;color:#1B3A5C;border-bottom:2px solid #1B3A5C;padding-bottom:4px}}
h3{{font-size:14px;color:#333}}
.source-card{{background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:16px;margin-bottom:12px}}
.source-name{{font-weight:700;color:#1B3A5C;font-size:13px}}
.badge{{background:#0D1B2A;color:#fff;font-size:10px;border-radius:4px;padding:2px 8px;margin-left:6px}}
.warn{{background:#FFF3CD;border:1px solid #FFC107;border-radius:6px;padding:12px;margin:10px 0;font-size:12px}}
.note{{background:#E3F2FD;border:1px solid #90CAF9;border-radius:6px;padding:12px;margin:10px 0;font-size:12px}}
code{{background:#f1f3f5;border-radius:4px;padding:2px 5px;font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px}}
th{{background:#0D1B2A;color:#fff;padding:7px 10px;text-align:left}}
td{{padding:6px 10px;border-bottom:1px solid #dee2e6}}
</style>
</head>
<body>
<h1>INTERNAL — Methodology &amp; Data Sources</h1>
<p style="color:#666;font-size:13px">
  Lower Mississippi River Grain Export Elevator Intelligence Report — 2025<br>
  Build date: {BUILD_DATE} &nbsp;|&nbsp; CONFIDENTIAL — FOR INTERNAL USE ONLY
</p>

<h2>1. Data Sources</h2>

<div class="source-card">
  <div class="source-name">Southport Agencies — Vessel Lineup Reports</div>
  <span class="badge">PRIMARY</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Daily vessel lineup sheets covering Miss. River, Texas, and PNW terminal systems.
    Source: <code>/Users/wsd/Projects/southport-agencies/exposed-files/excel/</code>
    (945 Excel files, 2.1 GB). Table: <code>grain_southport_lineup</code> in
    <code>data/analytics.duckdb</code>. 15,569 rows for MISS_RIVER 2025;
    255 report days; 12 terminals. Schema: vessel_name, terminal_name, status_type
    (ETA/FILING/LOADING/SAILED), report_date, mt_numeric, commodity_code,
    destination, delay_days_min, delay_days_max.
  </p>
  <div class="warn">~40–70% NULL mt_numeric for LOADING records is a structural artifact —
    many vessels file "RVT" (quantity to be determined) until loading commences.
    FGIS certified tonnage is the authoritative volume measure.</div>
</div>

<div class="source-card">
  <div class="source-name">USDA FGIS — Federal Grain Inspection Service Export Certificates</div>
  <span class="badge">PRIMARY</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Official grain inspection certificates for all US grain exports.
    Table: <code>grain_fgis_certs</code> — 30,057 certificates for
    port='MISSISSIPPI R.' in 2025 (Jan–Sep 25, 2025). Total certified volume: {total_mt:.1f}M MT.
    Schema: serial_no, cert_date, vessel, grain, grade, pounds, metric_ton, destination, port.
    Data coverage: Jan 1 – Sep 25, 2025 (FGIS IDW API extraction lag;
    Q4 2025 data not yet extracted at time of build).
  </p>
</div>

<div class="source-card">
  <div class="source-name">USACE MRTIS — Mississippi River Traffic Information Service</div>
  <span class="badge">VESSEL MOVEMENT</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Processed vessel movement data derived from USACE MRTIS tracking records.
    Source files: <code>01_DATA_SOURCES/federal_waterway/mrtis/results_clean/</code><br>
    — <code>voyage_summary.csv</code>: 41,156 voyage records with port time components
    (TotalPortTimeHours, TransitTimeHours, AnchorTimeHours, TerminalTimeHours)<br>
    — <code>event_log.csv</code>: 268,577 zone-level events with anchorage names,
    zone types, and dwell durations.
    <b>2025 filter:</b> CrossInTime &gt;= '2025-01-01'. Status: {"Live queries" if mrtis["source"]=="live" else "Cached pre-computed values — re-run to refresh."}.
  </p>
  <div class="note">MRTIS data and source attribution are INTERNAL ONLY and must NOT appear
    in the main (demo/client) report. The main report presents these findings as
    "anchorage and transit intelligence" without naming the USACE MRTIS data feed.</div>
</div>

<div class="source-card">
  <div class="source-name">Blue Water Shipping (BWS) — Port Maps / Terminal Registry</div>
  <span class="badge">GEOSPATIAL</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Terminal positions and operational details from BWS port map publications.
    Source: <code>07_KNOWLEDGE_BANK/master_facility_register/data/national_supply_chain/
    facilities_grain_export_elevator.geojson</code> (29 terminals, IENC-calibrated
    AHP coordinates for Miss. River facilities).
  </p>
</div>

<div class="source-card">
  <div class="source-name">USACE IENC — Inland Electronic Navigation Charts</div>
  <span class="badge">GEOSPATIAL</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Mile marker (AHP) to lat/lon calibration for Miss. River terminal positions.
    Corrections applied to Southport lineup mile_ahp field, which shows artifacts
    for COOPER DARROW, ZEN-NOH, and LDC (all display 164.0 in lineup data).
    TERMINAL_META dict in build script carries correct positions.
  </p>
</div>

<div class="source-card">
  <div class="source-name">USDA ERS / AMS — Grain Transportation Report &amp; Modal Share</div>
  <span class="badge">ECONOMICS</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Barge origin corridor volume estimates derived from USDA Agricultural Transportation
    Chapter modal share benchmarks: barge 55–60%, rail 35–38%, truck 5–7% for
    Lower Mississippi grain exports. GTR weekly barge rate reports (Cairo-Memphis
    benchmark). Modal share figures are structural estimates, not observed 2025 flows.
  </p>
</div>

<div class="source-card">
  <div class="source-name">NOAA NWS / USACE — River Gauge Data</div>
  <span class="badge">RIVER CONDITIONS</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    River stage values in the report are <b>historical monthly averages</b>
    (multi-year climatological means) for Carrollton (USGS 07374000, New Orleans)
    and Donaldsonville gauges. These are not 2025 observed readings.
    For real-time / observed 2025 data: NOAA NWPS API
    <code>api.water.noaa.gov/nwps/v1/gauges/NORL1/stageflow</code> (Carrollton).
  </p>
</div>

<h2>2. Metric Methodology</h2>

<h3>Queue Wait Time</h3>
<p style="font-size:12px">
  ETA first appearance date per vessel–terminal pair → first LOADING date,
  filtered to &lt;= 30 days to avoid multi-voyage inflation (vessels that appear
  at same terminal across multiple quarters create false positives).
  SQL: <code>DATEDIFF('day', first_eta, first_loading) &lt;= 30</code>.
  Metric: MEDIAN (preferred over mean; means inflated by outlier berth-waits
  and repeat vessel–terminal appearances).
</p>

<h3>Loading Duration</h3>
<p style="font-size:12px">
  Count of distinct LOADING report dates per vessel–terminal pair per year.
  Represents the number of daily lineup reports showing that vessel as LOADING
  at that terminal — a proxy for actual load time (1 report ≈ 1 day).
  Metric: MEDIAN loading days per vessel visit.
</p>

<h3>Anchorage Wait Time</h3>
<p style="font-size:12px">
  From MRTIS event_log: DurationToNextEventHours for events where
  ZoneType = 'ANCHORAGE' (or Zone LIKE '%Anch%'), filtered to &lt; 500h
  to remove anomalies. Aggregated by Zone. Monthly trend from
  voyage_summary.AnchorTimeHours (pre-computed per voyage).
</p>

<h3>Cargo Size (MT)</h3>
<p style="font-size:12px">
  Southport lineup mt_numeric field — filed tonnage at time of ETA/LOADING report.
  Structural ~40–70% NULL rate is expected (vessels file "RVT" until cargo known).
  Non-null LOADING records used for size distribution analysis.
  P25/Median/P75 computed via DuckDB PERCENTILE_CONT and MEDIAN functions.
</p>

<h2>3. Data Caveats &amp; Limitations</h2>
<ul style="font-size:12px;line-height:1.8">
  <li>FGIS data covers Jan 1 – Sep 25, 2025 only (Q4 extraction pending)</li>
  <li>Southport lineup data: 255 of 365 possible 2025 report days captured</li>
  <li>mile_ahp artifacts in lineup: COOPER DARROW, ZEN-NOH, LDC all show 164.0 — true positions used from TERMINAL_META dict</li>
  <li>Barge origin corridor percentages are structural USDA GTR estimates, not 2025 observed flow data</li>
  <li>River stage values are historical climatological averages, not 2025 actual readings</li>
  <li>Fog day count (34/year) is a NOAA NWS New Orleans climatological average</li>
  <li>MRTIS AnchorTimeHours = 0 for vessels with no anchor stops (i.e., vessels that went direct to terminal); mean inflated by these when not filtered</li>
  <li>ADM WOOD BUOYS and BUNGE DESTREHAN not in BWS GeoJSON — approximate coordinates used</li>
</ul>

<h2>4. Reproducibility</h2>
<p style="font-size:12px">
  Run from: <code>03_COMMODITY_MODULES/grain/</code><br>
  Command: <code>python3 src/build_lower_miss_report_v2.py</code><br>
  Requires: <code>duckdb</code>, <code>pandas</code>, <code>folium</code>
  (all installed in project env).<br>
  Output: <code>04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v2.html</code>
  and <code>_v2_INTERNAL.html</code>
</p>

</body>
</html>"""
    return html


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Building Lower Mississippi River Grain Elevator Guide v2 — {BUILD_DATE}")
    print(f"  DB: {DB_PATH}")

    # Load MRTIS data
    print("Loading MRTIS anchorage data...")
    mrtis = load_mrtis(PROJECT_ROOT)

    # Connect to analytics DB
    print("Querying analytics DB...")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    q   = run_queries(con)
    ta  = build_terminal_analytics(q)
    con.close()
    print(f"  Loaded: {len(q['loading_stats'])} terminal rows, {int(q['fgis_overview']['total_certs'].iloc[0]):,} FGIS certs")

    # Build maps
    print("Building Folium maps...")
    river_m  = build_river_map(ta)
    world_m  = build_world_map(q["fgis_destinations"])
    barge_m  = build_barge_map()
    river_iframe = map_to_b64_iframe(river_m, height=580)
    world_iframe = map_to_b64_iframe(world_m, height=520)
    barge_iframe = map_to_b64_iframe(barge_m, height=460)
    print("  Maps built and encoded")

    # Build HTML
    print("Assembling main HTML...")
    main_html     = build_main_html(q, ta, mrtis, river_iframe, world_iframe, barge_iframe)
    internal_html = build_internal_html(q, ta, mrtis)

    # Write outputs
    OUTPUT_MAIN.write_text(main_html, encoding="utf-8")
    OUTPUT_INT.write_text(internal_html, encoding="utf-8")

    main_kb = OUTPUT_MAIN.stat().st_size // 1024
    int_kb  = OUTPUT_INT.stat().st_size // 1024
    print(f"\nDone.")
    print(f"  Main report:   {OUTPUT_MAIN.name} ({main_kb} KB)")
    print(f"  Internal annex:{OUTPUT_INT.name}  ({int_kb} KB)")
    print(f"\nOpen in browser:")
    print(f"  open '{OUTPUT_MAIN}'")


if __name__ == "__main__":
    main()
