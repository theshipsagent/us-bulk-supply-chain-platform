#!/usr/bin/env python3
"""
build_lower_miss_report_v3.py
Lower Mississippi River Grain Export Elevator Intelligence Report — 2025 (v3)
Key changes vs v2:
  - All Folium maps replaced with static matplotlib PNG maps (Bloomberg/WSJ/Economist style)
  - Grade-level grain quality with stow factor from formula: SF (ft³/LT) = 2788.08 / test_weight
  - Corrected MRTIS anchorages: real zone names from live query
  - 2025 total tons basis for all analysis
Run from: 03_COMMODITY_MODULES/grain/
  python3 src/build_lower_miss_report_v3.py
"""

import sys, os, json, math, re, io, base64
import numpy as np
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import geopandas as gpd
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

# ─── PATHS ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
GRAIN_DIR    = SCRIPT_DIR.parent
PROJECT_ROOT = GRAIN_DIR.parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "analytics.duckdb"
MRTIS_DIR    = PROJECT_ROOT / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean"
STOW_CSV     = PROJECT_ROOT / "02_TOOLSETS" / "vessel_voyage_analysis" / "grain_stowage_factors.csv"
NE_SHP       = Path("/opt/homebrew/lib/python3.14/site-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp")
OUTPUT_DIR   = PROJECT_ROOT / "04_REPORTS" / "presentations"
OUTPUT_MAIN  = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025_v3.html"
OUTPUT_INT   = OUTPUT_DIR / "lower_miss_grain_elevator_guide_2025_v3_INTERNAL.html"
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

# Corrected anchorage positions — real MRTIS zone names (v3 fix)
ANCHORAGES = [
    {"name": "9 Mile Anch",           "lat": 29.075, "lon": -89.210, "note": "Primary inbound anchorage — SW Pass approach"},
    {"name": "12 Mile Anch",          "lat": 29.110, "lon": -89.260, "note": "High-traffic queue zone — SW Pass"},
    {"name": "Lwr Kenner Bend Anch",  "lat": 29.960, "lon": -90.210, "note": "Near MM 105 — New Orleans reach"},
    {"name": "Belle Chasse Anch",     "lat": 29.860, "lon": -90.000, "note": "Near MM 75 — Belle Chasse"},
    {"name": "AMA Anch",              "lat": 29.940, "lon": -90.310, "note": "Near ADM Ama MM 117"},
    {"name": "Burnside Anch",         "lat": 30.070, "lon": -90.700, "note": "Near MM 155"},
    {"name": "Upr Kenner Bend Anch",  "lat": 29.970, "lon": -90.220, "note": "Near MM 108"},
    {"name": "Dockside Anch",         "lat": 29.950, "lon": -90.150, "note": "Near MM 103"},
    {"name": "Bonnet Carre Anch",     "lat": 30.050, "lon": -90.560, "note": "Near MM 128"},
    {"name": "Pt Celeste Anch",       "lat": 29.470, "lon": -89.780, "note": "Upbound staging"},
    {"name": "Davant Anch",           "lat": 29.580, "lon": -89.870, "note": "Longest avg wait 2025"},
    {"name": "Baton Rouge Gen Anch",  "lat": 30.430, "lon": -91.180, "note": "Upper river queue — near LDC Port Allen MM 229"},
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

# ─── MRTIS CORRECTED FALLBACK (v3 — real zone names verified by live query) ───
MRTIS_FALLBACK = {
    "port_time": {"total":159,"transit":26,"anchor":62,"terminal":67,"voyages":5518,"anchoring":3917},
    "anchorages": [
        {"zone":"9 Mile Anch",           "visits":722,"avg_h":29.7,"med_h":8.8},
        {"zone":"12 Mile Anch",          "visits":645,"avg_h":32.8,"med_h":8.4},
        {"zone":"Lwr Kenner Bend Anch",  "visits":515,"avg_h":29.3,"med_h":8.8},
        {"zone":"Belle Chasse Anch",     "visits":480,"avg_h":29.9,"med_h":9.3},
        {"zone":"AMA Anch",              "visits":476,"avg_h":27.8,"med_h":9.1},
        {"zone":"Burnside Anch",         "visits":380,"avg_h":26.4,"med_h":6.8},
        {"zone":"Upr Kenner Bend Anch",  "visits":346,"avg_h":26.7,"med_h":7.1},
        {"zone":"Dockside Anch",         "visits":269,"avg_h":32.1,"med_h":8.6},
        {"zone":"Bonnet Carre Anch",     "visits":260,"avg_h":30.4,"med_h":8.2},
        {"zone":"Pt Celeste Anch",       "visits":210,"avg_h":45.6,"med_h":7.2},
        {"zone":"Davant Anch",           "visits":185,"avg_h":49.1,"med_h":7.5},
        {"zone":"Baton Rouge Gen Anch",  "visits":89, "avg_h":40.8,"med_h":0.8},
    ],
    "monthly":{1:79,2:94,3:68,4:58,5:51,6:45,7:44,8:50,9:53,10:57,11:48,12:62},
    "source":"cached",
}

# ─── MRTIS DATA LOADER ────────────────────────────────────────────────────────
def load_mrtis(project_root):
    v_csv = project_root / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean" / "voyage_summary.csv"
    e_csv = project_root / "01_DATA_SOURCES" / "federal_waterway" / "mrtis" / "results_clean" / "event_log.csv"
    if not v_csv.exists() or not e_csv.exists():
        print("  MRTIS CSVs not found — using corrected cached data")
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

        # Top anchorages — corrected filter to match real MRTIS zone names
        anch_df = con.execute("""
            SELECT Zone,
                   COUNT(DISTINCT VoyageID) visits,
                   ROUND(AVG(DurationToNextEventHours),1) avg_h,
                   ROUND(MEDIAN(DurationToNextEventHours),1) med_h
            FROM el
            WHERE (ZoneType='ANCHORAGE' OR Zone LIKE '%Anch%')
              AND DurationToNextEventHours > 0
              AND DurationToNextEventHours < 500
              AND EventTime >= '2025-01-01' AND EventTime < '2026-01-01'
            GROUP BY Zone
            ORDER BY visits DESC
            LIMIT 12
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
        print(f"  MRTIS live error: {exc} — using corrected cached data")
        return MRTIS_FALLBACK


# ─── DATABASE QUERIES ─────────────────────────────────────────────────────────
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

    q["fgis_monthly_yoy"] = con.execute("""
        SELECT datepart('year',cert_date) AS yr,
               datepart('month',cert_date) AS mo,
               ROUND(SUM(metric_ton)/1000000,3) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.'
          AND datepart('year',cert_date) IN (2022,2023,2024)
        GROUP BY 1,2 ORDER BY 1,2
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
        WITH top_ships AS (
            SELECT vessel, grain, destination,
                   ROUND(MAX(metric_ton),0) mt,
                   MIN(cert_date) cert_date
            FROM grain_fgis_certs
            WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
              AND metric_ton > 50000
            GROUP BY vessel, grain, destination
            ORDER BY mt DESC LIMIT 25
        ),
        vessel_terminals AS (
            SELECT UPPER(TRIM(vessel_name)) vn, terminal_name, COUNT(*) cnt
            FROM grain_southport_lineup
            WHERE datepart('year', report_date) = 2025
              AND status_type IN ('LOADING','FILED')
            GROUP BY 1, 2
        ),
        best_terminal AS (
            SELECT vn, terminal_name
            FROM (
                SELECT vn, terminal_name,
                       ROW_NUMBER() OVER (PARTITION BY vn ORDER BY cnt DESC) rn
                FROM vessel_terminals
            ) t WHERE rn = 1
        )
        SELECT t.vessel, t.grain, t.destination, t.mt, t.cert_date,
               COALESCE(bt.terminal_name, '—') AS elevator
        FROM top_ships t
        LEFT JOIN best_terminal bt ON UPPER(TRIM(t.vessel)) = bt.vn
        ORDER BY t.mt DESC
    """).fetchdf()

    q["fgis_seasonal_grain"] = con.execute("""
        SELECT datepart('month',cert_date) mo,
               grain, ROUND(SUM(metric_ton)/1000000,3) mt_m
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND grain IN ('CORN','SOYBEANS','WHEAT')
        GROUP BY 1,2 ORDER BY 1,2
    """).fetchdf()

    # Grade-level quality for stow factor table (v3 new)
    q["fgis_grade_quality"] = con.execute("""
        SELECT grain, grade,
               COUNT(*) certs,
               ROUND(SUM(metric_ton),0) total_mt,
               ROUND(AVG(test_weight),2) avg_tw,
               ROUND(AVG(moisture_avg),2) avg_moisture,
               ROUND(AVG(fm_pct),2) avg_fm,
               ROUND(AVG(protein_avg),2) avg_protein
        FROM grain_fgis_certs
        WHERE port='MISSISSIPPI R.' AND datepart('year',cert_date)=2025
          AND grain IN ('CORN','SOYBEANS','WHEAT','SORGHUM')
          AND grade IS NOT NULL AND grade != ''
        GROUP BY grain, grade
        ORDER BY grain, total_mt DESC
    """).fetchdf()

    # Compute stow factors: SF (ft³/LT) = 2788.08 / test_weight
    # 2788.08 = 2240 lbs/LT × 1.2445 ft³/bu; untrimmed = SF × 1.06
    # Reference test weights (USDA standard grades, lbs/bu) used when
    # FGIS certificate data lacks test_weight (e.g. RECAP-format files).
    REF_TW = {"CORN": 56.0, "SOYBEANS": 60.0, "WHEAT": 60.0, "SORGHUM": 56.0}
    df_gq = q["fgis_grade_quality"].copy()
    if len(df_gq) > 0 and "avg_tw" in df_gq.columns:
        # Where test_weight is available use actual; else fall back to USDA standard
        def _eff_tw(row):
            if row.get("avg_tw") and row["avg_tw"] > 30:
                return row["avg_tw"]
            return REF_TW.get(row["grain"], None)
        eff_tw = df_gq.apply(_eff_tw, axis=1)
        mask = eff_tw.notna()
        df_gq.loc[mask, "sf_ft3_lt"]    = (2788.08 / eff_tw[mask]).round(2)
        df_gq.loc[mask, "sf_m3_mt"]     = ((2788.08 / eff_tw[mask]) * 0.028317 / 1.01605).round(3)
        df_gq.loc[mask, "sf_untrimmed"] = (df_gq.loc[mask, "sf_ft3_lt"] * 1.06).round(2)
        df_gq.loc[~mask, "sf_ft3_lt"]   = None
        df_gq.loc[~mask, "sf_m3_mt"]    = None
        df_gq.loc[~mask, "sf_untrimmed"]= None
    q["fgis_grade_quality"] = df_gq

    return q


# ─── TERMINAL ANALYTICS ───────────────────────────────────────────────────────
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
            a["avg_mt"]    = int(row["avg_mt"])    if pd.notna(row["avg_mt"])    else None
            a["median_mt"] = int(row["median_mt"]) if pd.notna(row["median_mt"]) else None
            a["p25_mt"]    = int(row["p25_mt"])    if pd.notna(row["p25_mt"])    else None
            a["p75_mt"]    = int(row["p75_mt"])    if pd.notna(row["p75_mt"])    else None
            a["total_mt_k"]= int(row["total_mt_k"]) if pd.notna(row["total_mt_k"]) else 0
        else:
            a.update({"loading_records":0,"unique_vessels":0,"avg_mt":None,
                      "median_mt":None,"p25_mt":None,"p75_mt":None,"total_mt_k":0})
        a["delay_min"]  = float(ds.loc[key,"avg_delay_min"]) if key in ds.index and pd.notna(ds.loc[key,"avg_delay_min"]) else None
        a["delay_max"]  = float(ds.loc[key,"avg_delay_max"]) if key in ds.index and pd.notna(ds.loc[key,"avg_delay_max"]) else None
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


# ─── GC ARC FUNCTION ──────────────────────────────────────────────────────────
def gc_arc(lat1, lon1, lat2, lon2, n=40):
    """Great-circle arc points between two lat/lon coordinates."""
    d2r = math.pi / 180
    la1, lo1, la2, lo2 = lat1*d2r, lon1*d2r, lat2*d2r, lon2*d2r
    d = 2*math.asin(math.sqrt(
        math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
    if d < 1e-6:
        return [(lat1, lon1), (lat2, lon2)]
    pts = []
    for i in range(n+1):
        f = i/n
        A = math.sin((1-f)*d)/math.sin(d)
        B = math.sin(f*d)/math.sin(d)
        x = A*math.cos(la1)*math.cos(lo1)+B*math.cos(la2)*math.cos(lo2)
        y = A*math.cos(la1)*math.sin(lo1)+B*math.cos(la2)*math.sin(lo2)
        z = A*math.sin(la1)+B*math.sin(la2)
        pts.append((math.atan2(z, math.sqrt(x**2+y**2))/d2r, math.atan2(y,x)/d2r))
    return pts


def _fig_to_b64_img(fig, dpi=150, style="width:100%;max-width:680px;display:block;margin:0 auto;border-radius:6px;box-shadow:0 2px 12px rgba(0,0,0,0.15)"):
    """Convert matplotlib figure to base64 <img> tag."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{b64}" style="{style}">'


# ─── MAP 1: RIVER MAP (STATIC) ────────────────────────────────────────────────
# Colour palette — dark nautical theme matching OceanDatum brand
_MC = {
    "fig_bg":     "#08090d",
    "map_bg":     "#0d1117",
    "river_body": "#1a3a5c",
    "river_mid":  "#2d6a9f",
    "river_hl":   "#4a9fd4",
    "river_glow": "#7ec8e8",
    "grain":      "#64ffb4",   # OceanDatum mint — grain elevators
    "anchorage":  "#a78bfa",   # lavender
    "text_white": "#ffffff",
    "text_dim":   "#8899aa",
    "text_river": "#6ac8f0",
    "accent":     "#64ffb4",
    "grid":       "#1e2a3a",
}
_LABEL_OFF = {
    # (dx_deg, dy_deg, ha, va)
    "LDC PORT ALLEN":          (-0.22,  0.14, "right",  "bottom"),
    "ZEN-NOH CONVENT":         ( 0.22,  0.12, "left",   "bottom"),
    "CARGILL RESERVE":         ( 0.20,  0.10, "left",   "bottom"),
    "ADM RESERVE":             (-0.20,  0.14, "right",  "bottom"),
    "COOPER / DARROW":         (-0.18, -0.14, "right",  "top"),
    "ADM DESTREHAN":           (-0.20,  0.14, "right",  "bottom"),
    "BUNGE DESTREHAN":         ( 0.20, -0.12, "left",   "top"),
    "ADM AMA":                 (-0.20, -0.12, "right",  "top"),
    "CARGILL WESTWEGO":        (-0.20, -0.12, "right",  "top"),
    "CHS MYRTLE GROVE":        (-0.18,  0.14, "right",  "bottom"),
    "MGMT / ASSOCIATED":       ( 0.18, -0.14, "left",   "top"),
    "ADM WOOD BUOYS":          ( 0.20,  0.12, "left",   "bottom"),
}


def build_river_map_static(terminal_analytics):
    """OceanDatum dark nautical style — CartoDB DarkMatter + river glow."""
    import pyproj
    import matplotlib.patheffects as pe

    try:
        import contextily as ctx
        HAS_CTX = True
    except ImportError:
        HAS_CTX = False

    _4326_to_3857 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    _3857_to_4326 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    def to3857(lon, lat):
        return _4326_to_3857.transform(lon, lat)

    # Map extent
    EXT = {"west": -91.55, "east": -89.75, "south": 29.55, "north": 30.50}
    x_min, y_min = to3857(EXT["west"],  EXT["south"])
    x_max, y_max = to3857(EXT["east"],  EXT["north"])

    fig, ax = plt.subplots(figsize=(11, 14))
    fig.patch.set_facecolor(_MC["fig_bg"])
    ax.set_facecolor(_MC["map_bg"])
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Basemap — CartoDB DarkMatter
    if HAS_CTX:
        try:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.DarkMatter,
                            zoom=10, crs="EPSG:3857",
                            reset_extent=False, attribution=False)
        except Exception:
            pass  # fallback: solid dark bg is still readable

    # River centerline glow overlay
    _CL = (PROJECT_ROOT / "07_KNOWLEDGE_BANK/master_facility_register"
           / "data/national_supply_chain/lower_miss_river_centerline.geojson")
    if _CL.exists():
        try:
            river_gdf = gpd.read_file(str(_CL)).to_crs("EPSG:3857")
            river_gdf.plot(ax=ax, color=_MC["river_body"], lw=18, zorder=4, alpha=0.80)
            river_gdf.plot(ax=ax, color=_MC["river_mid"],  lw=10, zorder=5, alpha=0.85)
            river_gdf.plot(ax=ax, color=_MC["river_hl"],   lw=5,  zorder=6, alpha=0.90)
            river_gdf.plot(ax=ax, color=_MC["river_glow"], lw=1.5,zorder=7, alpha=0.65)
        except Exception:
            pass

    # Terminal markers
    lats = [t["lat"] for t in TERMINALS]
    lons = [t["lon"] for t in TERMINALS]
    xs, ys = to3857(lons, lats)

    lr_vals = [terminal_analytics.get(t["key"], {}).get("loading_records", 0) for t in TERMINALS]
    lr_max  = max(lr_vals) if any(lr_vals) else 1

    _outline = [pe.withStroke(linewidth=3.5, foreground="#0d1117")]

    for i, t in enumerate(TERMINALS):
        sz = max(80, 300 * lr_vals[i] / lr_max)
        # shadow
        ax.scatter(xs[i], ys[i], s=sz * 2.2, c="#000000",
                   marker="o", zorder=14, linewidths=0, alpha=0.45)
        # marker
        ax.scatter(xs[i], ys[i], s=sz, c=_MC["grain"],
                   marker="o", zorder=15, edgecolors="white", linewidths=0.8)

        # Short label
        parts = t["display"].replace("/", " / ").split()
        short = " ".join(parts[:2]).upper()
        label_text = f"MM {t['mile']}\n{short}"
        dx, dy, ha, va = _LABEL_OFF.get(short, (0.18, 0.10, "left", "bottom"))
        lon_t, lat_t = _3857_to_4326.transform(xs[i], ys[i])
        x0_m, y0_m   = to3857(lon_t, lat_t)
        x1_m, y1_m   = to3857(lon_t + dx, lat_t + dy)
        dm_x = x1_m - x0_m
        dm_y = y1_m - y0_m

        ax.annotate(
            label_text,
            xy=(xs[i], ys[i]),
            xytext=(xs[i] + dm_x, ys[i] + dm_y),
            fontsize=7.5, fontweight="bold", color=_MC["grain"],
            ha=ha, va=va, zorder=20,
            path_effects=_outline,
            arrowprops=dict(arrowstyle="-", color=_MC["grain"],
                            lw=1.2, alpha=0.75,
                            connectionstyle="arc3,rad=0.0"),
            annotation_clip=False,
        )

    # Anchorage markers
    for a in ANCHORAGES[:10]:
        ax_m, ay_m = to3857(a["lon"], a["lat"])
        ax.scatter(ax_m, ay_m, s=45, c=_MC["anchorage"], marker="^",
                   zorder=12, edgecolors="white", linewidths=0.5, alpha=0.75)

    # Geographic labels
    for lon, lat, text, fs, rot in [
        (-90.08, 29.96, "MISSISSIPPI\nRIVER", 8, 80),
        (-90.56, 30.04, "MISSISSIPPI\nRIVER", 8, 65),
        (-91.18, 30.38, "MISSISSIPPI\nRIVER", 7, 55),
        (-90.0715, 29.9511, "NEW ORLEANS", 10, 0),
        (-91.1871, 30.4515, "BATON ROUGE", 10, 0),
        (-90.5843, 30.0594, "RESERVE", 7, 0),
        (-90.8779, 30.0630, "CONVENT", 7, 0),
    ]:
        if not (EXT["west"] < lon < EXT["east"] and EXT["south"] < lat < EXT["north"]):
            continue
        px, py = to3857(lon, lat)
        clr = _MC["text_river"] if "MISSISSIPPI" in text else _MC["text_white"]
        ax.text(px, py, text, fontsize=fs, color=clr,
                style="italic" if "MISSISSIPPI" in text else "normal",
                ha="center", va="center", rotation=rot, alpha=0.80, zorder=11,
                path_effects=[pe.withStroke(linewidth=2, foreground=_MC["map_bg"])])

    # Coordinate grid
    for lon in np.arange(-91.5, -89.7, 0.5):
        xg, _ = to3857(lon, EXT["south"])
        ax.axvline(xg, color=_MC["grid"], lw=0.3, alpha=0.5, zorder=1)
    for lat in np.arange(29.5, 30.6, 0.25):
        _, yg = to3857(EXT["west"], lat)
        ax.axhline(yg, color=_MC["grid"], lw=0.3, alpha=0.5, zorder=1)

    # Title block
    ax.text(0.50, 0.988,
            "Lower Mississippi River",
            transform=ax.transAxes, fontsize=16, color=_MC["accent"],
            fontweight="bold", va="top", ha="center", zorder=25,
            path_effects=[pe.withStroke(linewidth=4, foreground=_MC["fig_bg"])])
    ax.text(0.50, 0.968,
            "Grain Export Terminals  ·  Head of Passes to Port Allen  ·  2025",
            transform=ax.transAxes, fontsize=8, color=_MC["text_dim"],
            va="top", ha="center", zorder=25,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=_MC["fig_bg"])])

    # Legend
    legend_items = [
        mpatches.Patch(color=_MC["grain"],     label="Grain export elevator  (size ∝ 2025 loads)"),
        mpatches.Patch(color=_MC["anchorage"], label="Anchorage zone"),
        mpatches.Patch(color=_MC["river_hl"],  label="Mississippi River  (USACE centerline)"),
    ]
    leg = ax.legend(handles=legend_items, loc="lower left",
                    fontsize=7, framealpha=0.88,
                    facecolor="#0a0f18", edgecolor=_MC["accent"],
                    labelcolor=_MC["text_white"],
                    borderpad=1.0, labelspacing=0.6,
                    bbox_to_anchor=(0.01, 0.01))

    # North arrow
    ax.annotate("", xy=(0.965, 0.960), xytext=(0.965, 0.920),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=_MC["text_white"],
                                lw=1.4, mutation_scale=14), zorder=30)
    ax.text(0.965, 0.972, "N", transform=ax.transAxes, fontsize=11,
            color=_MC["text_white"], fontweight="bold",
            va="bottom", ha="center", zorder=30,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=_MC["fig_bg"])])

    ax.axis("off")
    for spine in ax.spines.values():
        spine.set_edgecolor(_MC["accent"])
        spine.set_linewidth(0.8)
    ax.axis("on")
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout(pad=0.3)
    style_str = ("width:100%;max-width:720px;display:block;margin:0 auto;"
                 "border-radius:6px;box-shadow:0 4px 24px rgba(0,0,0,0.6);"
                 "border:1px solid rgba(100,255,180,0.18)")
    return _fig_to_b64_img(fig, dpi=150, style=style_str)


# ─── MAP 2: WORLD TRADE FLOW MAP (STATIC) ─────────────────────────────────────
def build_world_map_static(fgis_dests):
    """Economist dark-style world export trade flow map."""
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor('#0A1628')
    ax.set_facecolor('#0A1628')

    # Load world polygons
    world = None
    if NE_SHP.exists():
        try:
            world = gpd.read_file(str(NE_SHP))
        except Exception:
            world = None
    if world is None:
        try:
            import geopandas as gpd2
            world = gpd2.read_file(gpd2.datasets.get_path('naturalearth_lowres'))
        except Exception:
            pass

    if world is not None:
        world.plot(ax=ax, color='#1C2D41', edgecolor='#2A3D55', linewidth=0.4)

    ax.set_xlim(-165, 178)
    ax.set_ylim(-58, 82)

    # Origin
    origin_lon, origin_lat = -89.5, 29.3
    max_mt = float(fgis_dests["mt_m"].max()) if len(fgis_dests) > 0 else 1.0
    if max_mt == 0:
        max_mt = 1.0

    shown = 0
    for _, row in fgis_dests.head(20).iterrows():
        dest = row["destination"]
        mt_val = float(row["mt_m"])
        if dest not in COUNTRY_CENTROIDS:
            continue
        dlat, dlon = COUNTRY_CENTROIDS[dest]
        lw = max(0.5, 5 * math.log(1 + mt_val) / math.log(1 + max_mt))
        arc_pts = gc_arc(origin_lat, origin_lon, dlat, dlon, n=40)
        # Split arcs that cross the antimeridian
        arc_lons = [p[1] for p in arc_pts]
        arc_lats = [p[0] for p in arc_pts]
        # Draw in segments to handle antimeridian crossing
        seg_lons, seg_lats = [], []
        for j in range(len(arc_lons)):
            if j > 0 and abs(arc_lons[j] - arc_lons[j-1]) > 90:
                if seg_lons:
                    ax.plot(seg_lons, seg_lats, color='#F0A500', alpha=0.55,
                            linewidth=lw, zorder=3, solid_capstyle='round')
                seg_lons, seg_lats = [arc_lons[j]], [arc_lats[j]]
            else:
                seg_lons.append(arc_lons[j])
                seg_lats.append(arc_lats[j])
        if seg_lons:
            ax.plot(seg_lons, seg_lats, color='#F0A500', alpha=0.55,
                    linewidth=lw, zorder=3, solid_capstyle='round')

        # Destination point
        s_pt = 30 + lw * 15
        ax.scatter([dlon], [dlat], c='#FF5722', s=s_pt, zorder=5,
                   edgecolors='white', linewidths=0.8)

        # Label for larger volumes
        if mt_val > 0.5:
            dest_title = dest.title().replace("S. Korea", "S.Korea")
            ax.annotate(dest_title, (dlon, dlat),
                        textcoords="offset points", xytext=(4, 3),
                        fontsize=7.0, color='#DDE4ED', fontweight='700', zorder=6)
        shown += 1

    # Origin star
    ax.scatter([origin_lon], [origin_lat], c='#42A5F5', s=140, marker='*',
               zorder=6, edgecolors='white', linewidths=1.5)
    ax.annotate('Lower Mississippi', (origin_lon, origin_lat),
                textcoords="offset points", xytext=(6, -12),
                fontsize=8, color='#42A5F5', fontweight='700', zorder=7)

    ax.axis('off')

    # Title
    total_mt_val = float(fgis_dests["mt_m"].sum()) if len(fgis_dests) > 0 else 0.0
    total_mt_str = f"{total_mt_val:.1f}"
    ax.set_title("Lower Mississippi River Grain Export Trade Flows — 2025",
                 color='#DDE4ED', fontsize=13, fontweight='800', loc='left', pad=10)
    src_note = f"Source: {total_mt_str}M MT certified — Jan\u2013Sep 2025 | USDA FGIS"
    ax.text(0.01, 0.03, src_note, transform=ax.transAxes,
            color='#7898B8', fontsize=8.5, va='bottom')

    print(f"  World map: {shown} destinations plotted")
    style_str = "width:100%;max-width:1100px;display:block;margin:0 auto;border-radius:6px;box-shadow:0 2px 12px rgba(0,0,0,0.18)"
    return _fig_to_b64_img(fig, dpi=150, style=style_str)


# ─── MAP 3: BARGE CORRIDOR MAP (STATIC) ───────────────────────────────────────
def build_barge_map_static():
    """OceanDatum dark style — CartoDB DarkMatter, glowing barge corridors."""
    import pyproj
    import matplotlib.patheffects as pe

    try:
        import contextily as ctx
        HAS_CTX = True
    except ImportError:
        HAS_CTX = False

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(_MC["fig_bg"])
    ax.set_facecolor(_MC["map_bg"])

    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    # CONUS extent
    lon_min, lon_max = -100, -76
    lat_min, lat_max = 27, 49
    xmin, ymin = transformer.transform(lon_min, lat_min)
    xmax, ymax = transformer.transform(lon_max, lat_max)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    if HAS_CTX:
        try:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.DarkMatter,
                            zoom=5, crs="EPSG:3857")
        except Exception:
            ax.set_facecolor(_MC["map_bg"])

    # Destination: Lower Mississippi grain complex
    dest_lat, dest_lon = 30.05, -90.35
    dx, dy = transformer.transform(dest_lon, dest_lat)

    # Draw corridors — glow (wide + dim) then bright line on top
    for corr in BARGE_CORRIDORS:
        wpts = corr["waypoints"]
        lw_base = max(2.0, corr["pct"] / 5 + 1.5)
        col = corr["color"]
        wx_list, wy_list = [], []
        for lat_w, lon_w in wpts:
            wx, wy = transformer.transform(lon_w, lat_w)
            wx_list.append(wx)
            wy_list.append(wy)
        # glow halo
        ax.plot(wx_list, wy_list, color=col, linewidth=lw_base * 3.5,
                alpha=0.18, zorder=4, solid_capstyle='round', solid_joinstyle='round')
        # mid glow
        ax.plot(wx_list, wy_list, color=col, linewidth=lw_base * 1.8,
                alpha=0.45, zorder=5, solid_capstyle='round', solid_joinstyle='round')
        # bright line
        ax.plot(wx_list, wy_list, color=col, linewidth=lw_base,
                alpha=0.92, zorder=6, solid_capstyle='round', solid_joinstyle='round')

        # Origin circle (first waypoint)
        orig_x, orig_y = wx_list[0], wy_list[0]
        r_size = 40 + corr["pct"] * 5
        ax.scatter([orig_x], [orig_y], s=r_size * 2.5, c=col,
                   zorder=7, alpha=0.20, linewidths=0)
        ax.scatter([orig_x], [orig_y], s=r_size, c=col,
                   zorder=8, edgecolors='white', linewidths=0.8, alpha=0.95)

        # Label at origin
        ax.annotate(f"{corr['name']}\n{corr['pct']}%",
                    (orig_x, orig_y),
                    textcoords="offset points", xytext=(6, 6),
                    fontsize=7, fontweight="600", color=col, zorder=10,
                    path_effects=[pe.withStroke(linewidth=2, foreground=_MC["fig_bg"])])

    # Destination star — mint
    ax.scatter([dx], [dy], s=350, c=_MC["grain"], marker="*",
               zorder=12, edgecolors=_MC["fig_bg"], linewidths=1.2)
    ax.scatter([dx], [dy], s=600, c=_MC["grain"], marker="*",
               zorder=11, alpha=0.25, linewidths=0)
    ax.annotate("Lower Miss.\nGrain Complex", (dx, dy),
                textcoords="offset points", xytext=(10, -20),
                fontsize=8.5, color=_MC["grain"], fontweight="800", zorder=13,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=_MC["fig_bg"])])

    # Legend — dark box
    legend_lines = [
        mlines.Line2D([], [], color=c["color"],
                      linewidth=max(2.0, c["pct"] / 5 + 1.5),
                      label=f"{c['name']}  {c['pct']}%")
        for c in BARGE_CORRIDORS
    ]
    leg = ax.legend(handles=legend_lines, loc="upper right", fontsize=8,
                    framealpha=0.82, edgecolor=_MC["grain"],
                    facecolor="#0d1117", labelcolor="white")
    leg.get_frame().set_linewidth(0.8)

    # Title
    ax.set_title("US Grain Barge Origin Corridors — Lower Mississippi Export Complex",
                 fontsize=11, fontweight="800", color=_MC["text_white"], pad=10)

    # Mint accent border
    for spine in ax.spines.values():
        spine.set_edgecolor(_MC["grain"])
        spine.set_linewidth(0.8)
        spine.set_visible(True)

    ax.axis('off')

    style_str = ("width:100%;max-width:960px;display:block;margin:0 auto;"
                 "border-radius:6px;border:1px solid #64ffb430;"
                 "box-shadow:0 4px 24px rgba(0,0,0,0.6)")
    return _fig_to_b64_img(fig, dpi=150, style=style_str)


# ─── HTML UTILITIES ───────────────────────────────────────────────────────────
def fmt_num(n, suffix=""):
    return "N/A" if n is None else f"{n:,.0f}{suffix}"


def comm_donut_js(canvas_id, comm_mix):
    order     = ["YSB","CORN","SBM","WHT","DDGS","OTHER","UNKNOWN"]
    label_map = {"YSB":"Soybeans","CORN":"Corn","SBM":"SBM","WHT":"Wheat",
                 "DDGS":"DDGS","OTHER":"Other","UNKNOWN":"Filed/Unspec"}
    labels, values, colors = [], [], []
    for k in order:
        if k in comm_mix:
            labels.append(label_map[k])
            values.append(comm_mix[k])
            colors.append(COMM_COLORS[k])
    if not values:
        return ""
    lbl_j  = json.dumps(labels)
    val_j  = json.dumps(values)
    col_j  = json.dumps(colors)
    return (
        f"registerChart(new Chart(document.getElementById('{canvas_id}'), {{"
        f"type:'doughnut',"
        f"data:{{labels:{lbl_j},datasets:[{{data:{val_j},"
        f"backgroundColor:{col_j},borderWidth:1,borderColor:'rgba(0,0,0,0.2)'}}]}},"
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
        def ppos(v):
            return max(0, min(100, (v - bar_min) / (bar_max - bar_min) * 100))
        p25p  = ppos(p25)
        medp  = ppos(med)
        p75p  = ppos(p75)
        iqr_l = p25p
        iqr_w = p75p - p25p
        size_bar = (
            f'<div style="position:relative;height:16px;background:var(--surface3);border-radius:4px;margin:6px 0">'
            f'<div style="position:absolute;left:{iqr_l:.1f}%;width:{iqr_w:.1f}%;'
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

    # Tier badge
    mt_total = ta.get("total_mt_k", 0) or 0
    if mt_total >= 6000 or lv >= 300:
        tier_badge = '<span style="background:#1565C0;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 1 \u2014 Major</span>'
    elif mt_total >= 2000 or lv >= 130:
        tier_badge = '<span style="background:#388E3C;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 2 \u2014 Active</span>'
    else:
        tier_badge = '<span style="background:#607D8B;color:#fff;font-size:10px;border-radius:4px;padding:2px 7px">Tier 3 \u2014 Specialty</span>'

    wait_str  = f"{wait:.0f}d"          if wait is not None else "N/A"
    load_str  = f"{load:.0f}d"          if load is not None else "N/A"
    delay_str = (f"{dmin:.0f}\u2013{dmax:.0f}d"
                 if dmin is not None and dmax is not None else "N/A")

    def badge(label, value, color="var(--text)"):
        return (f'<div class="stat-badge">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-value" style="color:{color}">{value}</div></div>')

    vc_short = vc.split("/")[0].strip()
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
        f'<div class="section-label">Cargo size \u2014 P25 / Median / P75</div>'
        f'{size_bar}'
        f'<div class="section-label" style="margin-top:14px">Top destinations</div>'
        f'{dest_rows if dest_rows else "<div style=\"color:var(--text-dim);font-size:11px\">No destination data</div>"}'
        f'</div>'
        f'<div>'
        f'<div class="section-label">Commodity mix (2025)</div>'
        f'<div style="height:130px"><canvas id="{cid}"></canvas></div>'
        f'<div class="section-label" style="margin-top:12px">Operational profile</div>'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap">'
        f'{badge("Vessels", f"{uv:,}", t["color"])}'
        f'{badge("Loads", f"{lv:,}", t["color"])}'
        f'{badge("Class", vc_short, "var(--text)")}'
        f'{badge("Queue Wait", wait_str, "#E65100")}'
        f'{badge("Load Time", load_str, "#1565C0")}'
        f'{badge("Dock Delay", delay_str, "#6A1B9A")}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return card, comm_donut_js(cid, cm)


def _seasonal_grain_table(df):
    months = list(range(1, 10))
    grains = ["CORN", "SOYBEANS", "WHEAT"]
    peak_window = {"CORN": "Apr\u2013Aug", "SOYBEANS": "Jan\u2013Mar", "WHEAT": "Mar\u2013May"}
    rows = ""
    for g in grains:
        gdf = df[df["grain"] == g].set_index("mo")
        vals = [float(gdf.loc[m, "mt_m"]) if m in gdf.index else 0.0 for m in months]
        max_v = max(vals) if max(vals) > 0 else 1
        row = f"<tr><td><b>{g.capitalize()}</b></td>"
        for v in vals:
            intensity = int(v / max_v * 5)
            bg_alpha  = [0.05, 0.15, 0.3, 0.55, 0.75, 0.95][intensity]
            if g == "CORN":
                bg = f"rgba(253,216,53,{bg_alpha})"
            elif g == "SOYBEANS":
                bg = f"rgba(249,168,37,{bg_alpha})"
            else:
                bg = f"rgba(212,172,13,{bg_alpha})"
            row += (f'<td style="text-align:center;background:{bg};color:var(--text);font-size:11px">'
                    f'{v:.2f}</td>')
        row += f'<td style="font-size:11px;color:var(--text-muted)">{peak_window.get(g,"")}</td></tr>'
        rows += row
    return rows


def _build_grade_quality_rows(df_gq):
    """Merged quality + stow factor rows (one table, all metrics)."""
    grains_order = ["CORN", "SOYBEANS", "WHEAT", "SORGHUM"]
    rows = ""
    for grain in grains_order:
        gdf = df_gq[df_gq["grain"] == grain].copy()
        if len(gdf) == 0:
            continue
        grain_total = gdf["total_mt"].sum()
        first = True
        for _, row in gdf.iterrows():
            sf_val  = row.get("sf_ft3_lt")
            sf_m3   = row.get("sf_m3_mt")
            sf_un   = row.get("sf_untrimmed")
            tw_val  = row.get("avg_tw")
            moist   = row.get("avg_moisture")
            fm      = row.get("avg_fm")
            prot    = row.get("avg_protein")
            mt_v    = row.get("total_mt", 0)
            certs_v = row.get("certs", 0)
            vol_pct = (float(mt_v) / grain_total * 100) if grain_total > 0 and pd.notna(mt_v) else 0

            sf_str   = f"{sf_val:.2f}"       if pd.notna(sf_val)  else "—"
            sf_m3_s  = f"{sf_m3:.3f}"        if pd.notna(sf_m3)   else "—"
            sf_un_s  = f"{sf_un:.2f}"        if pd.notna(sf_un)   else "—"
            tw_str   = f"{tw_val:.1f}"       if pd.notna(tw_val)  else "—"
            mo_str   = f"{moist:.2f}%"       if pd.notna(moist)   else "—"
            fm_str   = f"{fm:.2f}%"          if pd.notna(fm)      else "—"
            pr_str   = f"{prot:.1f}%"        if pd.notna(prot)    else "—"
            mt_str   = f"{int(mt_v):,}"      if pd.notna(mt_v)    else "—"
            cert_str = f"{int(certs_v):,}"   if pd.notna(certs_v) else "—"
            pct_str  = f"{vol_pct:.1f}%"

            sf_class = ""
            if pd.notna(sf_val):
                if sf_val > 52:   sf_class = ' class="sf-high"'
                elif sf_val < 47: sf_class = ' class="sf-low"'

            sep_class     = ' class="grain-sep"' if first else ""
            grain_display = grain.capitalize()    if first else ""
            rows += (
                f"<tr{sep_class}>"
                f"<td><b>{grain_display}</b></td>"
                f"<td>{row.get('grade','')}</td>"
                f"<td>{mt_str}</td>"
                f"<td style='color:var(--text-muted);font-size:11px'>{pct_str}</td>"
                f"<td>{cert_str}</td>"
                f"<td>{tw_str}</td>"
                f"<td>{mo_str}</td>"
                f"<td>{fm_str}</td>"
                f"<td>{pr_str}</td>"
                f"<td{sf_class}><b>{sf_str}</b></td>"
                f"<td>{sf_m3_s}</td>"
                f"<td>{sf_un_s}</td>"
                f"</tr>"
            )
            first = False
    return rows


# ─── MAIN HTML BUILDER ────────────────────────────────────────────────────────
def build_main_html(q, ta, mrtis, river_img, world_img, barge_img):
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
    df_gq    = q["fgis_grade_quality"]

    # Operator legend
    seen_ops = {}
    for t in TERMINALS:
        if t["operator"] not in seen_ops:
            seen_ops[t["operator"]] = t["color"]
    op_legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin:4px 8px;font-size:12px">'
        f'<span style="width:12px;height:12px;border-radius:50%;background:{col};display:inline-block"></span>'
        f'{op}</span>'
        for op, col in seen_ops.items()
    )

    # Terminal cards
    terminal_cards_html = ""
    chart_scripts = []
    for idx, t in enumerate(TERMINALS):
        card_html, chart_js = build_terminal_card(t, ta[t["key"]], idx)
        terminal_cards_html += card_html
        if chart_js:
            chart_scripts.append(chart_js)

    # Vessel size histogram
    cargo_df = q["all_cargo_sizes"]
    bins = list(range(5000, 90001, 5000))
    labels_h = [f"{b//1000}K" for b in bins[:-1]]
    counts_h = [int(((cargo_df["mt_numeric"]>=bins[i])&(cargo_df["mt_numeric"]<bins[i+1])).sum())
                for i in range(len(bins)-1)]

    # Loading ranking
    ls_s = ls.sort_values("loading_records", ascending=True)
    rank_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in ls_s["terminal_name"]]
    rank_vals   = ls_s["loading_records"].tolist()
    rank_colors = [TERM_KEY_MAP.get(k,{}).get("color","#607D8B") for k in ls_s["terminal_name"]]

    # Queue wait
    qw = q["queue_wait"].sort_values("median_wait", ascending=False)
    qw_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in qw["terminal_name"]]
    qw_vals   = [float(v) for v in qw["median_wait"].tolist()]

    # Load duration
    ld = q["load_duration"].sort_values("median_load_days", ascending=False)
    ld_labels = [TERM_KEY_MAP.get(k,{}).get("display",k) for k in ld["terminal_name"]]
    ld_vals   = [float(v) for v in ld["median_load_days"].tolist()]

    # Monthly throughput (3 grains) — 12-month x-axis; 2025 data through Sep (null beyond)
    grains_shown  = ["CORN","SOYBEANS","WHEAT"]
    month_labels  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    months12      = list(range(1, 13))
    g_colors      = {"CORN":"#FDD835","SOYBEANS":"#F9A825","WHEAT":"#D4AC0D"}
    fgis_mo_max   = int(fgis_mo["mo"].max()) if len(fgis_mo) else 9  # last reported month
    monthly_ds    = []
    for g in grains_shown:
        gdf = fgis_mo[fgis_mo["grain"]==g].set_index("mo")
        vals = [round(float(gdf.loc[m,"mt_m"]), 3) if m in gdf.index else None for m in months12]
        monthly_ds.append({"label":f"{g.capitalize()} 2025","data":vals,
                           "borderColor":g_colors[g],"backgroundColor":g_colors[g]+"33",
                           "fill":True,"tension":0.4,"spanGaps":False,"borderWidth":2})
    # Prior year totals (all grains combined) as thin comparison lines
    yoy_df        = q["fgis_monthly_yoy"]
    yoy_colors    = {2022:"rgba(120,180,255,0.6)",2023:"rgba(180,255,180,0.6)",2024:"rgba(255,180,120,0.6)"}
    for yr in [2022, 2023, 2024]:
        ydf = yoy_df[yoy_df["yr"]==yr].set_index("mo")
        vals = [round(float(ydf.loc[m,"mt_m"]), 3) if m in ydf.index else None for m in months12]
        monthly_ds.append({"label":str(yr),"data":vals,
                           "borderColor":yoy_colors[yr],"backgroundColor":"transparent",
                           "fill":False,"tension":0.4,"spanGaps":True,
                           "borderWidth":1,"borderDash":[5,4],"pointRadius":2})

    # MRTIS / Anchorage chart data
    anch_zones  = [a["zone"] for a in anchs[:8]]
    anch_avg    = [float(a["avg_h"]) for a in anchs[:8]]
    anch_med    = [float(a["med_h"]) for a in anchs[:8]]
    anch_visits = [int(a["visits"]) for a in anchs[:8]]
    mo_keys     = sorted(monthly_anch.keys())
    mo_vals     = [float(monthly_anch[k]) for k in mo_keys]
    mo_lbls     = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # River stages
    carrollton_vals     = [RIVER_STAGES["Carrollton"][i]     for i in range(1, 13)]
    donaldsonville_vals = [RIVER_STAGES["Donaldsonville"][i] for i in range(1, 13)]

    # Barge corridors
    corr_names  = [c["name"]  for c in BARGE_CORRIDORS]
    corr_pcts   = [c["pct"]   for c in BARGE_CORRIDORS]
    corr_colors = [c["color"] for c in BARGE_CORRIDORS]

    # FGIS destinations table
    top_dest_rows = ""
    for i, (_, row) in enumerate(fgis_d.head(20).iterrows()):
        top_dest_rows += (f"<tr><td>{i+1}</td><td><b>{row['destination']}</b></td>"
                          f"<td>{row['mt_m']:.2f} MMT</td><td>{int(row['certs']):,}</td></tr>")

    # Grade table (simple — shown alongside quality metrics)
    grade_rows = ""
    for grain in ["CORN","SOYBEANS","WHEAT"]:
        gdf = fgis_g[fgis_g["grain"]==grain]
        total_g = float(gdf["mt_m"].sum())
        for _, row in gdf.iterrows():
            pct = float(row["mt_m"])/total_g*100 if total_g > 0 else 0
            grade_rows += (f"<tr><td>{grain.capitalize()}</td><td>{row['grade']}</td>"
                           f"<td>{float(row['mt_m']):.2f} MMT</td><td>{pct:.1f}%</td>"
                           f"<td>{int(row['certs']):,}</td></tr>")

    # Quality table
    qual_rows = ""
    for _, row in fgis_q.iterrows():
        prot_str = "N/A" if pd.isna(row["protein"]) else f"{float(row['protein']):.1f}%"
        tw_str   = "N/A" if pd.isna(row["test_wt"])  else f"{float(row['test_wt']):.1f} lb/bu"
        moist_val = float(row["moisture"]) if pd.notna(row["moisture"]) else 0
        fm_val    = float(row["fm"])       if pd.notna(row["fm"])       else 0
        qual_rows += (f"<tr><td><b>{str(row['grain']).capitalize()}</b></td>"
                      f"<td>{moist_val:.1f}%</td><td>{fm_val:.2f}%</td>"
                      f"<td>{prot_str}</td><td>{tw_str}</td><td>{int(row['n']):,}</td></tr>")

    # Top shipments
    ship_rows = ""
    for i, (_, row) in enumerate(fgis_top.head(10).iterrows()):
        elev = str(row.get('elevator', '—'))
        ship_rows += (f"<tr><td><b>{row['vessel']}</b></td>"
                      f"<td>{float(row['mt']):,.0f}</td>"
                      f"<td>{str(row['cert_date'])[:10]}</td>"
                      f"<td>{str(row['grain']).capitalize()}</td>"
                      f"<td>{row['destination']}</td>"
                      f"<td style='font-size:11px;color:var(--text-muted)'>{elev}</td></tr>")

    # Market share doughnut
    ms_labels, ms_vals, ms_colors = [], [], []
    for t in TERMINALS:
        mv = ta[t["key"]].get("total_mt_k", 0) or 0
        if mv > 0:
            ms_labels.append(t["display"])
            ms_vals.append(int(mv))
            ms_colors.append(t["color"])

    # FGIS grain mix helper
    def fgis_val(grain):
        row = fgis_gm[fgis_gm["grain"]==grain]
        return float(row["mt_m"].values[0]) if len(row) else 0.0

    anchor_pct   = round(pt["anchor"] / pt["total"] * 100) if pt["total"] else 39
    seasonal_note = (
        "Soybean loading peaks Jan\u2013Mar (Southern Hemisphere off-season). "
        "Corn dominates Apr\u2013Aug. Wheat exports strongest Mar\u2013May ahead of US harvest."
    )

    # Grade quality rows (v3 new — stow factors)
    grade_quality_rows = _build_grade_quality_rows(df_gq)

    # NAV sidebar items
    sidebar_items = [
        ("#s-cover",       "01 \u2014 Overview"),
        ("#s-world",       "02 \u2014 Global Trade Flows"),
        ("#s-commodity",   "03 \u2014 Commodity Intelligence"),
        ("#s-quality",     "04 \u2014 Quality & Certification"),
        ("#s-rankings",    "05 \u2014 Terminal Rankings"),
        ("#s-analytics",   "06 \u2014 Vessel Analytics"),
        ("#s-map",         "07 \u2014 River Map"),
        ("#s-terminals",   "08 \u2014 Terminal Profiles"),
        ("#s-anchorage",   "09 \u2014 Anchorage Intelligence"),
        ("#s-river",       "10 \u2014 River Conditions"),
        ("#s-barge",       "11 \u2014 Barge Origins"),
    ]
    nav_links = "".join(
        f'<li><a class="nav-link" href="{h}">{l}</a></li>'
        for h, l in sidebar_items
    )

    all_scripts = "\n".join(chart_scripts)

    # JSON-serialise JS data
    labels_h_j    = json.dumps(labels_h)
    counts_h_j    = json.dumps(counts_h)
    qw_labels_j   = json.dumps(qw_labels)
    qw_vals_j     = json.dumps(qw_vals)
    ld_labels_j   = json.dumps(ld_labels)
    ld_vals_j     = json.dumps(ld_vals)
    month_lbl_j   = json.dumps(month_labels)
    monthly_ds_j  = json.dumps(monthly_ds)
    rank_lbl_j    = json.dumps(rank_labels)
    rank_val_j    = json.dumps(rank_vals)
    rank_col_j    = json.dumps(rank_colors)
    ms_lbl_j      = json.dumps(ms_labels)
    ms_val_j      = json.dumps(ms_vals)
    ms_col_j      = json.dumps(ms_colors)
    anch_zon_j    = json.dumps(anch_zones)
    anch_avg_j    = json.dumps(anch_avg)
    anch_med_j    = json.dumps(anch_med)
    mo_lbls_j     = json.dumps(mo_lbls[:len(mo_vals)])
    mo_vals_j     = json.dumps(mo_vals)
    carr_j        = json.dumps(carrollton_vals)
    don_j         = json.dumps(donaldsonville_vals)
    corr_n_j      = json.dumps(corr_names)
    corr_p_j      = json.dumps(corr_pcts)
    corr_c_j      = json.dumps(corr_colors)

    pt_transit    = pt['transit']
    pt_anchor     = pt['anchor']
    pt_terminal   = pt['terminal']
    pt_total      = pt['total']

    anchorage_table_rows = "".join(
        f"<tr><td><b>{a['zone']}</b></td><td>{int(a['visits']):,}</td>"
        f"<td>{float(a['avg_h']):.1f}h</td><td>{float(a['med_h']):.1f}h</td>"
        f"<td style='color:var(--text-muted);font-size:11px'>"
        f"{'Longest avg wait — staging area' if 'Davant' in a['zone'] else 'Inbound approach queue' if ('9 Mile' in a['zone'] or '12 Mile' in a['zone']) else 'River staging zone'}</td></tr>"
        for a in anchs[:10]
    )

    barge_corr_table = "".join(
        f"<tr><td style='border-left:3px solid {c['color']}'><b>{c['name']}</b></td>"
        f"<td>{c['pct']}%</td>"
        f"<td style='font-size:11px;color:var(--text-muted)'>{c['grains']}</td></tr>"
        for c in BARGE_CORRIDORS
    )

    seasonal_table_rows = _seasonal_grain_table(q["fgis_seasonal_grain"])

    fgis_corn_mt  = fgis_val('CORN')
    fgis_soy_mt   = fgis_val('SOYBEANS')
    fgis_wht_mt   = fgis_val('WHEAT')

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
  .print-hide{display:none!important}
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
.sb-title{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:1px;text-transform:none}
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
  letter-spacing:.5px;text-transform:none}
.kpi-sub{font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px}
.section{background:var(--surface);padding:40px 48px;border-bottom:1px solid var(--border)}
.section-alt{background:var(--surface2);padding:40px 48px;border-bottom:1px solid var(--border)}
.section-title{font-size:20px;font-weight:800;color:var(--text);margin-bottom:4px}
.section-sub{font-size:13px;color:var(--text-muted);margin-bottom:24px}
.section-label{font-size:11px;font-weight:700;color:var(--text-muted);
  letter-spacing:.5px;text-transform:none;margin-bottom:6px}
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
  letter-spacing:.4px;text-transform:none}
.tbl td{padding:7px 10px;border-bottom:1px solid var(--border);color:var(--text)}
.tbl tr:nth-child(even) td{background:var(--tbl-alt)}
.tbl tr:hover td{background:var(--surface3)}
.info-card{background:var(--surface2);border:1px solid var(--border);
  border-radius:10px;padding:18px;margin-bottom:16px}
.kpi-inline{background:var(--surface2);border-radius:10px;padding:14px 18px;
  display:inline-flex;flex-direction:column;align-items:center;min-width:100px;text-align:center}
.kpi-inline .val{font-size:26px;font-weight:800;color:var(--text)}
.kpi-inline .lbl{font-size:11px;color:var(--text-muted);margin-top:2px;text-transform:none}
.insight-tag{display:inline-block;background:var(--tag-bg);border:1px solid var(--border);
  border-radius:4px;padding:3px 9px;font-size:11px;color:var(--text-muted);margin:3px 4px}
.map-static{border-radius:10px;overflow:hidden;border:1px solid var(--border);
  background:var(--surface2);padding:12px;text-align:center}
#ctrl-bar{padding:14px 48px;background:var(--surface2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:900}
.ctrl-btn{background:var(--surface3);border:1px solid var(--border);color:var(--text);
  border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer;
  font-family:inherit;transition:.15s}
.ctrl-btn:hover{background:var(--surface);border-color:var(--accent);color:var(--accent)}
.sf-high{background:rgba(255,152,0,0.15);}
.sf-low{background:rgba(33,150,243,0.12);}
.grain-sep td{border-top:2px solid var(--accent);padding-top:8px;font-weight:700;}
@media(max-width:900px){#sidebar{width:100%;height:auto;position:relative}#main{margin-left:0}}
"""

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

    chart_js_all = all_scripts + f"""

// Vessel size histogram
registerChart(new Chart(document.getElementById('hist_vessel_size'),{{
  type:'bar',
  data:{{labels:{labels_h_j},
    datasets:[{{label:'Vessel Count',data:{counts_h_j},
      backgroundColor:'rgba(59,125,216,0.7)',borderColor:'#3B7DD8',borderWidth:1}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Vessel Cargo Size Distribution \u2014 All Miss. River 2025',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Vessel Count',color:getColors().text}}}}}}}}}}));

// Queue wait bar
registerChart(new Chart(document.getElementById('chart_queue'),{{
  type:'bar',
  data:{{labels:{qw_labels_j},
    datasets:[{{label:'Median Wait Days',data:{qw_vals_j},
      backgroundColor:'rgba(230,81,0,0.7)',borderColor:'#E65100',borderWidth:1}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Median Queue Wait (ETA \u2192 Loading)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Days',color:getColors().text}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:10}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Load duration bar
registerChart(new Chart(document.getElementById('chart_load_dur'),{{
  type:'bar',
  data:{{labels:{ld_labels_j},
    datasets:[{{label:'Median Load Days',data:{ld_vals_j},
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
  data:{{labels:{month_lbl_j},datasets:{monthly_ds_j}}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Monthly Export Volume — 2025 by Grain vs Prior Years (MMT)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{stacked:false,ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'MMT',color:getColors().text}}}}}}}}}}));

// Terminal rankings bar
registerChart(new Chart(document.getElementById('chart_rankings'),{{
  type:'bar',
  data:{{labels:{rank_lbl_j},
    datasets:[{{label:'Loading Records',data:{rank_val_j},
      backgroundColor:{rank_col_j},borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'2025 Loading Records by Terminal',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Market share doughnut
registerChart(new Chart(document.getElementById('chart_mktshare'),{{
  type:'doughnut',
  data:{{labels:{ms_lbl_j},
    datasets:[{{data:{ms_val_j},backgroundColor:{ms_col_j},
      borderWidth:2,borderColor:'var(--surface)'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{font:{{size:10}},boxWidth:12,color:getColors().text}}}},
      title:{{display:true,text:'Estimated Market Share by Loading Volume',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}}}}}}));

// MRTIS port time doughnut
registerChart(new Chart(document.getElementById('chart_porttime'),{{
  type:'doughnut',
  data:{{labels:['Transit','Anchor Wait','Terminal Operations'],
    datasets:[{{data:[{pt_transit},{pt_anchor},{pt_terminal}],
      backgroundColor:['rgba(66,165,245,0.85)','rgba(255,152,0,0.85)','rgba(76,175,80,0.85)'],
      borderWidth:2,borderColor:'var(--surface)'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{font:{{size:11}},boxWidth:14,color:getColors().text}}}},
      tooltip:{{callbacks:{{label:function(c){{return c.label+': '+c.raw+'h ('+Math.round(c.raw/{pt_total}*100)+'%)';}}}}}}}}}}}}));

// Anchorage wait bar
registerChart(new Chart(document.getElementById('chart_anchorage'),{{
  type:'bar',
  data:{{labels:{anch_zon_j},
    datasets:[
      {{label:'Avg Hours',data:{anch_avg_j},backgroundColor:'rgba(255,152,0,0.8)',borderWidth:0}},
      {{label:'Median Hours',data:{anch_med_j},backgroundColor:'rgba(255,213,79,0.8)',borderWidth:0}}
    ]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Anchorage Wait Time \u2014 2025 (Hours)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Hours',color:getColors().text}}}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));

// Monthly anchorage congestion
registerChart(new Chart(document.getElementById('chart_monthly_anch'),{{
  type:'line',
  data:{{labels:{mo_lbls_j},
    datasets:[{{label:'Avg Anchor Wait (hrs)',data:{mo_vals_j},
      borderColor:'#FF9800',backgroundColor:'rgba(255,152,0,0.15)',
      fill:true,tension:0.4,pointRadius:5,pointBackgroundColor:'#FF9800'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Monthly Anchorage Congestion \u2014 2025 (Avg Hours)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                min:0,title:{{display:true,text:'Hours',color:getColors().text}}}}}}}}}}));

// River stages
registerChart(new Chart(document.getElementById('chart_river_stages'),{{
  type:'bar',
  data:{{labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    datasets:[
      {{label:'Carrollton (USGS)',data:{carr_j},
        backgroundColor:'rgba(66,165,245,0.7)',borderColor:'#42A5F5',borderWidth:1}},
      {{label:'Donaldsonville',data:{don_j},
        backgroundColor:'rgba(38,198,218,0.7)',borderColor:'#26C6DA',borderWidth:1}}
    ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{color:getColors().text}}}},
      title:{{display:true,text:'Mississippi River Stage \u2014 Historical Monthly Averages (Feet)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}}}},
             y:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'Feet (NGVD29)',color:getColors().text}}}}}}}}}}));

// Barge corridor bar
registerChart(new Chart(document.getElementById('chart_barge_corr'),{{
  type:'bar',
  data:{{labels:{corr_n_j},
    datasets:[{{label:'Est. % of Barge Volume',data:{corr_p_j},
      backgroundColor:{corr_c_j},borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Barge Volume by Origin Corridor (Estimated)',
              color:getColors().text,font:{{size:13,weight:'700'}}}}}},
    scales:{{x:{{ticks:{{color:getColors().text}},grid:{{color:getColors().grid}},
                title:{{display:true,text:'% of Total Barge Volume',color:getColors().text}},max:45}},
             y:{{ticks:{{color:getColors().text,font:{{size:11}}}},grid:{{color:getColors().grid}}}}}}}}}}));
"""

    fgis_corn_str = f"{fgis_corn_mt:.1f}"
    fgis_soy_str  = f"{fgis_soy_mt:.1f}"
    fgis_wht_str  = f"{fgis_wht_mt:.1f}"
    total_mt_str  = f"{total_mt:.1f}"
    anchor_pct_str= str(anchor_pct)
    pt_anchor_str = str(pt['anchor'])
    pt_total_str  = str(pt['total'])
    pt_transit_s  = str(pt['transit'])
    pt_terminal_s = str(pt['terminal'])
    pt_voyages_s  = str(pt['voyages'])

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lower Mississippi River \u2014 Grain Export Elevator Intelligence Report 2025 v3</title>
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
    LOWER MISSISSIPPI RIVER \u2014 GRAIN ELEVATOR GUIDE 2025 v3
  </span>
  <div style="margin-left:auto;display:flex;gap:8px">
    <button class="ctrl-btn" id="theme-btn" onclick="toggleTheme()">&#9728; Light</button>
    <button class="ctrl-btn" onclick="printReport()">&#128438; Print</button>
  </div>
</div>

<!-- 01 COVER -->
<section class="hero" id="s-cover">
  <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 12px;
     letter-spacing:1px;text-transform:none">
    Lower Mississippi River &nbsp;&middot;&nbsp; Export Grain Elevator Intelligence
  </p>
  <h1>Lower Mississippi River<br>Grain Export Elevator Guide</h1>
  <p class="sub">2025 Operational Intelligence &nbsp;&middot;&nbsp; 12 Terminals &nbsp;&middot;&nbsp; MM 57 to MM 229 AHP</p>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:32px">
    <div class="kpi-card">
      <div class="kpi-num">{total_mt_str}<span class="kpi-unit"> MMT</span></div>
      <div class="kpi-label">Certified Export Volume</div>
      <div class="kpi-sub">FGIS Jan\u2013Sep 2025</div>
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
      <div class="kpi-num">{anchor_pct_str}%</div>
      <div class="kpi-label">Port Time at Anchor</div>
      <div class="kpi-sub">Avg {pt_anchor_str}h anchor / {pt_total_str}h total</div>
    </div>
  </div>
  <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap">
    <span style="background:rgba(255,255,255,0.1);border-radius:8px;padding:9px 16px;font-size:13px">
      <b>Corn</b> {fgis_corn_str}M MT &nbsp;|&nbsp;
      <b>Soybeans</b> {fgis_soy_str}M MT &nbsp;|&nbsp;
      <b>Wheat</b> {fgis_wht_str}M MT
    </span>
    <span style="background:rgba(255,255,255,0.1);border-radius:8px;padding:9px 16px;font-size:13px">
      <b>Top Markets:</b> Mexico &middot; China &middot; Colombia &middot; Japan &middot; Egypt
    </span>
  </div>
</section>

<!-- 02 GLOBAL TRADE FLOWS -->
<section class="section-alt" id="s-world">
  <h2 class="section-title">Global Trade Flows</h2>
  <p class="section-sub">Export destinations certified at Mississippi River ports, Jan\u2013Sep 2025.
     Arc thickness proportional to certified tonnage. Orange arcs = grain trade flows from Lower Mississippi origin.</p>
  <div class="map-static" style="background:#0A1628;padding:16px">
    {world_img}
  </div>
  <div class="row g-4 mt-3">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Top 20 Export Destinations \u2014 2025</h4>
      <div style="overflow-x:auto">
        <table class="tbl">
          <tr><th>#</th><th>Destination</th><th>Volume (MMT)</th><th>Certificates</th></tr>
          {top_dest_rows}
        </table>
      </div>
    </div>
  </div>
</section>

<!-- 03 COMMODITY INTELLIGENCE -->
<section class="section" id="s-commodity">
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
        <span class="insight-tag">Soybean peak: Jan\u2013Mar (South American off-season demand)</span>
        <span class="insight-tag">Corn peak: Apr\u2013Aug (post-US harvest flush)</span>
        <span class="insight-tag">Wheat: Mar\u2013May (HRW/SRW pre-harvest marketing)</span>
        <span class="insight-tag">YSB+DDGS: specialty terminals year-round</span>
      </div>
    </div>
  </div>
</section>

<!-- 04 QUALITY & CERTIFICATION -->
<section class="section-alt" id="s-quality">
  <h2 class="section-title">Quality &amp; Certification Intelligence</h2>
  <p class="section-sub">Export quality and stow factor data by grain and grade — derived from
     inspection certificates issued at Mississippi River ports, 2025.
     Stow factor: SF (ft³/LT) = 2788.08 / test weight (lb/bu); untrimmed = SF &times; 1.06.
     <span style="background:rgba(255,152,0,0.2);padding:1px 6px;border-radius:3px;margin-left:6px;font-size:11px">Orange: light grain &gt;52 ft³/LT</span>
     <span style="background:rgba(33,150,243,0.15);padding:1px 6px;border-radius:3px;margin-left:4px;font-size:11px">Blue: heavy &lt;47 ft³/LT</span>
  </p>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr>
        <th>Grain</th><th>Grade</th><th>2025 Volume (mt)</th><th>Vol%</th><th>Certs</th>
        <th>Test Wt (lb/bu)</th><th>Moisture</th><th>FM%</th><th>Protein</th>
        <th>SF (ft³/LT)</th><th>SF (m³/MT)</th><th>SF Untrimmed</th>
      </tr>
      {grade_quality_rows}
    </table>
  </div>
</section>

<!-- 05 TERMINAL RANKINGS -->
<section class="section" id="s-rankings">
  <h2 class="section-title">Terminal Rankings &amp; Market Position</h2>
  <p class="section-sub">Comparative terminal performance \u2014 2025 loading activity
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

<!-- 06 VESSEL ANALYTICS -->
<section class="section-alt" id="s-analytics">
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
          <tr><td><b>Handymax</b></td><td>25,000\u201339,999 MT</td><td>Short-haul, Caribbean</td></tr>
          <tr><td><b>Supramax</b></td><td>40,000\u201357,999 MT</td><td>Panamax lanes</td></tr>
          <tr><td><b>Panamax</b></td><td>58,000\u201379,999 MT</td><td>Transoceanic bulk</td></tr>
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
        Queue wait = ETA first appearance \u2192 first LOADING date, capped at 30 days per voyage.
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
    Largest Single Shipments \u2014 2025</h4>
  <div style="overflow-x:auto">
    <table class="tbl">
      <tr><th>Vessel</th><th>Metric tons</th><th>Date</th><th>Grain</th><th>Destination</th><th>Elevator</th></tr>
      {ship_rows}
    </table>
  </div>
</section>

<!-- 07 RIVER MAP -->
<section class="section" id="s-map">
  <h2 class="section-title">River Map \u2014 Terminal Locations</h2>
  <p class="section-sub">12 grain export terminals along the Lower Mississippi River, MM 57\u2013229.
     Terminal circle size scaled to 2025 loading activity. Diamond markers indicate key anchorage zones.</p>
  <div style="margin-bottom:12px;padding:10px 14px;background:var(--surface2);
     border-radius:8px;font-size:12px;color:var(--text)">
    <b style="color:var(--text-muted)">Operators:</b>&nbsp;{op_legend}
  </div>
  <div class="map-static">
    {river_img}
  </div>
</section>

<!-- 08 TERMINAL PROFILES -->
<section class="section-alt" id="s-terminals">
  <h2 class="section-title">Terminal Profiles</h2>
  <p class="section-sub">Individual profiles \u2014 downstream (MM 57) to upstream (MM 229).
     Cargo bars show P25/Median/P75 range. Queue wait and load duration derived from
     daily lineup position data.</p>
  {terminal_cards_html}
</section>

<!-- 09 ANCHORAGE INTELLIGENCE -->
<section class="section" id="s-anchorage">
  <h2 class="section-title">Anchorage &amp; Transit Intelligence</h2>
  <p class="section-sub">Vessel movement data across the Lower Mississippi approach: time at anchor
     before berthing, congestion patterns by location, and seasonal trends \u2014 2025.</p>
  <div class="row g-4 mb-4">
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val">{pt_total_str}h</span>
        <span class="lbl">Avg Total Port Time</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#FF9800">{pt_anchor_str}h</span>
        <span class="lbl">Avg Anchor Wait</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#4CAF50">{pt_terminal_s}h</span>
        <span class="lbl">Avg Terminal Time</span>
      </div>
    </div>
    <div class="col-sm-6 col-md-3">
      <div class="kpi-inline" style="width:100%">
        <span class="val" style="color:#42A5F5">{pt_transit_s}h</span>
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
        Vessels spend approximately <b style="color:var(--text)">{anchor_pct_str}% of total port time
        waiting at anchor</b> before reaching a berth \u2014 a critical factor in demurrage
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
        <b>Seasonal pattern:</b> Peak congestion typically Feb\u2013Mar coincides with South American
        soybean harvest window and pre-planting US corn-belt barge fleet buildup.
        Summer low (Jun\u2013Jul) reflects reduced harvest pressure and lower river traffic density.
      </p>
    </div>
  </div>
  <div class="row g-4 mt-2">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px">
        Key Anchorage Locations \u2014 2025 Activity</h4>
      <table class="tbl">
        <tr><th>Anchorage</th><th>2025 Visits</th><th>Avg Wait</th><th>Median Wait</th><th>Notes</th></tr>
        {anchorage_table_rows}
      </table>
    </div>
  </div>
</section>

<!-- 10 RIVER CONDITIONS -->
<section class="section-alt" id="s-river">
  <h2 class="section-title">River Conditions &amp; Seasonal Context</h2>
  <p class="section-sub">Gauge height and navigation context at key Lower Mississippi River
     measurement points \u2014 historical monthly averages.</p>
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
          <b style="color:#42A5F5">High water (Mar\u2013May):</b> Accelerated current
          (3\u20135 kt vs. 1\u20132 kt at low water) increases fuel consumption for upstream
          movements and can restrict draft near Old River Control.<br><br>
          <b style="color:#FF9800">Low water (Jul\u2013Oct):</b> Draft restrictions
          may apply below Carrollton. Sub-zero gauge readings can
          suspend loaded barge operations.<br><br>
          <b style="color:#66BB6A">Optimal loading window:</b> Dec\u2013Feb at most
          terminals \u2014 moderate stage, good visibility, pre-South American harvest
          demand peak.
        </div>
      </div>
      <div class="info-card">
        <div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:8px">
          Fog &amp; Visibility
        </div>
        <div style="font-size:12px;color:var(--text-muted);line-height:1.7">
          New Orleans averages <b style="color:var(--text)">34 fog days/year</b>,
          concentrated Nov\u2013Mar. River fog closures (Coast Guard VTS)
          typically last 2\u20138 hours and primarily affect the Lower Reach
          (Pilot Town \u2192 MM 30). Terminal operations above MM 57 are
          rarely impacted for more than one tidal cycle.
        </div>
      </div>
    </div>
  </div>
  <div class="row g-4 mt-2">
    <div class="col-12">
      <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:10px">
        Seasonal Export Activity \u2014 Grain Type Intensity</h4>
      <div style="overflow-x:auto">
        <table class="tbl">
          <tr><th>Grain</th><th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th>
              <th>Jun</th><th>Jul</th><th>Aug</th><th>Sep</th><th>Peak Window</th></tr>
          {seasonal_table_rows}
        </table>
      </div>
      <p style="font-size:12px;color:var(--text-muted);margin-top:8px">{seasonal_note}</p>
    </div>
  </div>
</section>

<!-- 11 BARGE ORIGINS -->
<section class="section" id="s-barge">
  <h2 class="section-title">Barge Origin Corridors</h2>
  <p class="section-sub">Approximately 55\u201360% of grain exported via the Lower Mississippi
     arrives by inland barge from key production corridors. The map shows primary
     tributary flows converging at the Lower Mississippi grain complex.</p>
  <div class="row g-4">
    <div class="col-md-7">
      <div class="map-static">
        {barge_img}
      </div>
    </div>
    <div class="col-md-5">
      <div class="chart-box-sm"><canvas id="chart_barge_corr"></canvas></div>
      <div style="margin-top:14px">
        <table class="tbl">
          <tr><th>Corridor</th><th>Est. %</th><th>Primary Grains</th></tr>
          {barge_corr_table}
        </table>
      </div>
    </div>
  </div>
  <div class="row g-4 mt-2">
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">55\u201360%</div>
        <div style="font-size:12px;color:var(--text-muted)">of Lower Miss. export grain<br>arrives via inland barge</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">35\u201338%</div>
        <div style="font-size:12px;color:var(--text-muted)">arrives by unit train<br>(shuttle and manifest)</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="info-card" style="text-align:center">
        <div style="font-size:28px;font-weight:800;color:var(--text)">5\u20137%</div>
        <div style="font-size:12px;color:var(--text-muted)">local truck delivery<br>(LA, MS production)</div>
      </div>
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


# ─── INTERNAL ANNEX ───────────────────────────────────────────────────────────
def build_internal_html(q, ta, mrtis):
    fgis_ov  = q["fgis_overview"].iloc[0]
    total_mt = float(fgis_ov["total_mt_m"])
    pt       = mrtis["port_time"]
    src_status = "Live queries" if mrtis["source"] == "live" else "Cached pre-computed values (v3 corrected) -- re-run to refresh."
    pt_total_s  = str(pt['total'])
    pt_anchor_s = str(pt['anchor'])
    pt_voyages_s= str(pt['voyages'])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>INTERNAL -- Lower Miss. Grain Elevator Guide 2025 v3 -- Methodology &amp; Sources</title>
<style>
body{{font-family:"Segoe UI",system-ui,sans-serif;max-width:1000px;margin:40px auto;
  padding:0 30px;background:#F8F9FA;color:#212529}}
h1{{font-size:22px;color:#0D1B2A}}
h2{{font-size:17px;color:#1B3A5C;border-bottom:2px solid #1B3A5C;padding-bottom:4px}}
h3{{font-size:14px;color:#333}}
.source-card{{background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:16px;margin-bottom:12px}}
.source-name{{font-weight:700;color:#1B3A5C;font-size:13px}}
.badge{{background:#0D1B2A;color:#fff;font-size:10px;border-radius:4px;padding:2px 8px;margin-left:6px}}
.warn{{background:#FFF3CD;border:1px solid #FFC107;border-radius:6px;padding:12px;margin:10px 0;font-size:12px}}
.note{{background:#E3F2FD;border:1px solid #90CAF9;border-radius:6px;padding:12px;margin:10px 0;font-size:12px}}
.fix{{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:6px;padding:12px;margin:10px 0;font-size:12px}}
code{{background:#f1f3f5;border-radius:4px;padding:2px 5px;font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px}}
th{{background:#0D1B2A;color:#fff;padding:7px 10px;text-align:left}}
td{{padding:6px 10px;border-bottom:1px solid #dee2e6}}
</style>
</head>
<body>
<h1>INTERNAL -- Methodology &amp; Data Sources (v3)</h1>
<p style="color:#666;font-size:13px">
  Lower Mississippi River Grain Export Elevator Intelligence Report -- 2025 v3<br>
  Build date: {BUILD_DATE} &nbsp;|&nbsp; CONFIDENTIAL -- FOR INTERNAL USE ONLY
</p>

<div class="fix">
  <b>v3 Key Fixes vs v2:</b>
  <ol style="margin:6px 0 0">
    <li>All Folium maps replaced with static matplotlib PNG maps (Bloomberg/WSJ/Economist style)</li>
    <li>Grade-level grain quality with stow factor: SF (ft\u00b3/LT) = 2788.08 / test_weight</li>
    <li>Corrected MRTIS anchorages: real zone names from live query (no "Natchez Anch" -- that zone name was fabricated in v2 fallback and does not exist in MRTIS data)</li>
    <li>MRTIS filter corrected to: ZoneType='ANCHORAGE' OR Zone LIKE '%Anch%'</li>
    <li>Corrected anchorage lat/lon positions match real zone names</li>
  </ol>
</div>

<h2>1. Data Sources</h2>

<div class="source-card">
  <div class="source-name">Southport Agencies -- Vessel Lineup Reports</div>
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
  <div class="warn">~40--70% NULL mt_numeric for LOADING records is a structural artifact --
    many vessels file "RVT" (quantity to be determined) until loading commences.
    FGIS certified tonnage is the authoritative volume measure.</div>
</div>

<div class="source-card">
  <div class="source-name">USDA FGIS -- Federal Grain Inspection Service Export Certificates</div>
  <span class="badge">PRIMARY</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Official grain inspection certificates for all US grain exports.
    Table: <code>grain_fgis_certs</code> -- {int(fgis_ov['total_certs']):,} certificates for
    port='MISSISSIPPI R.' in 2025 (Jan--Sep 2025). Total certified volume: {total_mt:.1f}M MT.
    Schema: serial_no, cert_date, vessel, grain, grade, pounds, metric_ton, destination, port,
    test_weight, moisture_avg, fm_pct, protein_avg.
    Data coverage: Jan 1 -- Sep 25, 2025.
  </p>
</div>

<div class="source-card">
  <div class="source-name">USACE MRTIS -- Mississippi River Traffic Information Service</div>
  <span class="badge">VESSEL MOVEMENT</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Processed vessel movement data derived from USACE MRTIS tracking records.
    Source files: <code>01_DATA_SOURCES/federal_waterway/mrtis/results_clean/</code><br>
    -- <code>voyage_summary.csv</code>: {pt_voyages_s} voyage records in 2025 with port time components<br>
    -- <code>event_log.csv</code>: zone-level events with anchorage names, zone types, dwell durations.<br>
    <b>2025 filter:</b> CrossInTime &gt;= '2025-01-01'. Status: {src_status}.
  </p>
  <div class="note">MRTIS data and source attribution are INTERNAL ONLY and must NOT appear
    in the main (demo/client) report. The main report presents these findings as
    "anchorage and transit intelligence" without naming the USACE MRTIS data feed.</div>
  <div class="fix">
    <b>v3 Correction:</b> v2 fallback data included "Natchez Anch" with 45 visits, avg 89.4h.
    This zone name does NOT exist in the MRTIS event_log data. It was fabricated in the v2
    fallback dict. Verified 2025 top anchorages from live MRTIS query are:<br>
    9 Mile Anch (722), 12 Mile Anch (645), Lwr Kenner Bend Anch (515), Belle Chasse Anch (480),
    AMA Anch (476), Burnside Anch (380), Upr Kenner Bend Anch (346), Dockside Anch (269),
    Bonnet Carre Anch (260), Pt Celeste Anch (210), Davant Anch (185), Baton Rouge Gen Anch (89).
  </div>
</div>

<div class="source-card">
  <div class="source-name">Blue Water Shipping (BWS) -- Port Maps / Terminal Registry</div>
  <span class="badge">GEOSPATIAL</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    Terminal positions and operational details from BWS port map publications.
    Source: <code>07_KNOWLEDGE_BANK/master_facility_register/data/national_supply_chain/
    facilities_grain_export_elevator.geojson</code> (29 terminals, IENC-calibrated
    AHP coordinates for Miss. River facilities).
  </p>
</div>

<div class="source-card">
  <div class="source-name">v3 Static Maps: matplotlib + contextily + GeoPandas</div>
  <span class="badge">VISUALIZATION</span>
  <p style="font-size:12px;color:#555;margin-top:8px">
    All Folium interactive maps replaced with static PNG maps embedded as base64 data URIs.
    Three maps: (1) River terminal map with CartoDB Positron basemap; (2) World trade flow
    map (Economist dark style, great-circle arcs); (3) US barge corridor map (WSJ style).
    Tools: matplotlib, contextily (CartoDB basemap tiles), geopandas (Natural Earth polygons),
    pyproj (EPSG:4326 to EPSG:3857 transform).
  </p>
</div>

<h2>2. Stow Factor Methodology (v3 New)</h2>
<p style="font-size:12px;line-height:1.8">
  Stow factors computed from USDA FGIS certified test weights per grain grade:
</p>
<table>
  <tr><th>Formula</th><th>Description</th></tr>
  <tr><td><code>SF (ft\u00b3/LT) = 2788.08 / TW</code></td>
      <td>2788.08 = 2240 lb/LT &times; 1.2445 ft\u00b3/bu (standard bushel volume)</td></tr>
  <tr><td><code>SF (m\u00b3/MT) = (2788.08 / TW) &times; 0.028317 / 1.01605</code></td>
      <td>Convert ft\u00b3/LT to m\u00b3/MT (1 ft\u00b3 = 0.028317 m\u00b3, 1 LT = 1.01605 MT)</td></tr>
  <tr><td><code>SF Untrimmed = SF (ft\u00b3/LT) &times; 1.06</code></td>
      <td>6% allowance for grain surface not leveled (standard bulk carrier practice)</td></tr>
</table>
<p style="font-size:12px;color:#555">
  Reference: Isbester, <i>Bulk Carrier Practice</i> Ch.5; Meurn &amp; Sauerbier, <i>Stowage</i>.
  Grain stowage factors CSV: <code>02_TOOLSETS/vessel_voyage_analysis/grain_stowage_factors.csv</code>
</p>
<p style="font-size:12px;color:#555">
  <b>Color coding in report:</b> Orange highlight = light grain &gt;52 ft\u00b3/LT (typically wheat, sorghum);
  Blue highlight = heavy corn &lt;47 ft\u00b3/LT. No highlight = typical 47--52 ft\u00b3/LT range.
</p>

<h2>3. Metric Methodology</h2>

<h3>Queue Wait Time</h3>
<p style="font-size:12px">
  ETA first appearance date per vessel--terminal pair to first LOADING date,
  filtered to &lt;= 30 days. Metric: MEDIAN. SQL: <code>DATEDIFF('day', first_eta, first_loading) &lt;= 30</code>.
</p>

<h3>Loading Duration</h3>
<p style="font-size:12px">
  Count of distinct LOADING report dates per vessel--terminal pair per year.
  Represents the number of daily lineup reports showing that vessel as LOADING.
  Metric: MEDIAN loading days per vessel visit.
</p>

<h3>Anchorage Wait Time (v3 corrected)</h3>
<p style="font-size:12px">
  From MRTIS event_log: DurationToNextEventHours for events where
  <code>ZoneType='ANCHORAGE' OR Zone LIKE '%Anch%'</code>, filtered to &lt; 500h.
  Aggregated by Zone. Monthly trend from voyage_summary.AnchorTimeHours.
  <b>v2 error corrected:</b> v2 used <code>Zone LIKE '%anch%'</code> (lowercase only) which
  missed zones written with capital A (the actual MRTIS naming convention).
</p>

<h3>Cargo Size (MT)</h3>
<p style="font-size:12px">
  Southport lineup mt_numeric field. Structural ~40--70% NULL rate expected.
  Non-null LOADING records used for size distribution. P25/Median/P75 via DuckDB PERCENTILE_CONT.
</p>

<h2>4. Data Caveats &amp; Limitations</h2>
<ul style="font-size:12px;line-height:1.8">
  <li>FGIS data covers Jan 1 -- Sep 25, 2025 only (Q4 extraction pending)</li>
  <li>Southport lineup data: 255 of 365 possible 2025 report days captured</li>
  <li>mile_ahp artifacts: COOPER DARROW, ZEN-NOH, LDC all show 164.0 -- true positions used from TERMINAL_META dict</li>
  <li>Barge origin corridor percentages are structural USDA GTR estimates, not 2025 observed flow data</li>
  <li>River stage values are historical climatological averages, not 2025 actual readings</li>
  <li>Fog day count (34/year) is NOAA NWS New Orleans climatological average</li>
  <li>ADM WOOD BUOYS and BUNGE DESTREHAN not in BWS GeoJSON -- approximate coordinates used</li>
  <li>Stow factors computed from FGIS certified test weights (USDA official scale); not from vessel manifest or bill of lading</li>
  <li>"Natchez Anch" in v2 fallback was fabricated -- removed in v3</li>
</ul>

<h2>5. Reproducibility</h2>
<p style="font-size:12px">
  Run from: <code>03_COMMODITY_MODULES/grain/</code><br>
  Command: <code>python3 src/build_lower_miss_report_v3.py</code><br>
  Requires: <code>duckdb</code>, <code>pandas</code>, <code>matplotlib</code>,
  <code>geopandas</code>, <code>shapely</code>, <code>pyproj</code>,
  <code>contextily</code> (optional, for basemap tiles).<br>
  Output: <code>04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3.html</code>
  and <code>_v3_INTERNAL.html</code>
</p>

<h2>6. v3 Map Implementation Notes</h2>
<p style="font-size:12px">
  Natural Earth shapefile path tested at:
  <code>{NE_SHP}</code><br>
  Falls back to <code>geopandas.datasets.get_path('naturalearth_lowres')</code> if not found.<br>
  Contextily basemap tiles require internet connection; falls back to solid background color if unavailable.<br>
  All maps saved at 150 DPI, embedded as base64 PNG data URIs. No external dependencies at view time.
</p>

</body>
</html>"""
    return html


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Building Lower Mississippi River Grain Elevator Guide v3 -- {BUILD_DATE}")
    print(f"  DB:    {DB_PATH}")
    print(f"  Out:   {OUTPUT_MAIN.name}")

    # Load MRTIS data (corrected anchorage zones)
    print("Loading MRTIS anchorage data (corrected zone names)...")
    mrtis = load_mrtis(PROJECT_ROOT)

    # Connect to analytics DB
    print("Querying analytics DB...")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    q   = run_queries(con)
    ta  = build_terminal_analytics(q)
    con.close()
    n_certs   = int(q["fgis_overview"]["total_certs"].iloc[0])
    n_terms   = len(q["loading_stats"])
    n_gq_rows = len(q["fgis_grade_quality"])
    print(f"  Loaded: {n_terms} terminal rows, {n_certs:,} FGIS certs, {n_gq_rows} grade-quality rows")

    # Build static maps
    print("Building static maps (matplotlib PNG)...")
    river_img = build_river_map_static(ta)
    print("  River map done")
    world_img = build_world_map_static(q["fgis_destinations"])
    print("  World map done")
    barge_img = build_barge_map_static()
    print("  Barge map done")

    # Assemble HTML
    print("Assembling main HTML...")
    main_html     = build_main_html(q, ta, mrtis, river_img, world_img, barge_img)
    internal_html = build_internal_html(q, ta, mrtis)

    # Write outputs
    OUTPUT_MAIN.write_text(main_html, encoding="utf-8")
    OUTPUT_INT.write_text(internal_html, encoding="utf-8")

    main_kb = OUTPUT_MAIN.stat().st_size // 1024
    int_kb  = OUTPUT_INT.stat().st_size // 1024
    print(f"\nDone: {main_kb} KB main, {int_kb} KB internal")
    print(f"  Main report:    {OUTPUT_MAIN}")
    print(f"  Internal annex: {OUTPUT_INT}")
    print(f"\nopen '{OUTPUT_MAIN}'")


if __name__ == "__main__":
    main()
