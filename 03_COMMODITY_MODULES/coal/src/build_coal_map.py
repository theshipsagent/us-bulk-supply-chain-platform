#!/usr/bin/env python3
"""
build_coal_map.py
Coal Module — US Coal Supply Chain Interactive Map (v2)

5 layer groups with production-weighted mine sizing and thermal/met classification:
  1. Coal Basin Polygons     (7 basins with approximate extents)
  2. MSHA Coal Mines         (sized by production; colored by coal type)
  3. Class I Rail Corridors  (BNSF, UP, CSX, NS)
  4. Coal Export Terminals   (5 major US terminals)
  5. Coal Barge Waterways    (Ohio, Mississippi, and tributaries)

Coal type classification method:
  - Known met coal counties (VA Buchanan/Dickenson, WV Taylor/Barbour/Logan/Mingo, AL Jefferson/Tuscaloosa)
  - Known HCC/met operator names (Warrior Met, Alpha Met, Coronado, Ramaco)
  - Surface mines in WY/MT/TX/ND → thermal/sub-bituminous/lignite
  - Underground mines in CAPP met counties → metallurgical

Usage:
    python src/build_coal_map.py
    python src/build_coal_map.py --output reports/drafts/coal_supply_chain_map.html
    python src/build_coal_map.py --min-prod 1000000   # Only show mines > 1M ST/yr
    python src/build_coal_map.py --all-mines          # Include small/idle mines too
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

try:
    import pandas as pd
    import folium
    from folium.plugins import MarkerCluster, MeasureControl, MiniMap
    import click
except ImportError:
    print("Install: pip install pandas folium click")
    sys.exit(1)

# ─── Paths ────────────────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MODULE_DIR.parent.parent

MSHA_TXT = MODULE_DIR / "data/raw/msha/Mines.txt"
PROD_TXT = MODULE_DIR / "data/raw/msha/MinesProdQuarterly.txt"
RAIL_GEOJSON = PROJECT_ROOT / "01_DATA_SOURCES/geospatial/rail_networks/class1_rail_main_routes.geojson"
WATERWAY_GEOJSON = (
    PROJECT_ROOT / "01_DATA_SOURCES/federal_waterway/09_bts_waterway_networks"
    / "Waterway_Networks_3525269991148215733.geojson"
)
DEFAULT_OUTPUT = MODULE_DIR / "reports/drafts/coal_supply_chain_map.html"

# ─── Coal Type Classification ─────────────────────────────────────────────────

# Counties where underground mines are presumed to be metallurgical coal
MET_COAL_COUNTIES = {
    # Central Appalachian premium HCC / low-vol met
    "VA": {"Buchanan", "Dickenson", "Wise", "Scott", "Tazewell", "Russell"},
    # Central Appalachian met/crossover
    "WV": {"Taylor", "Barbour", "Logan", "Mingo", "Boone", "McDowell",
           "Wyoming", "Raleigh", "Kanawha", "Lincoln", "Wayne"},
    # Kentucky eastern met
    "KY": {"Harlan", "Letcher", "Pike", "Martin", "Floyd"},
    # Warrior Basin HCC (Alabama)
    "AL": {"Jefferson", "Tuscaloosa", "Walker", "Bibb"},
    # Tennessee (small amounts of met)
    "TN": {"Campbell", "Claiborne"},
}

# Operators known to produce metallurgical coal
MET_OPERATORS_KEYWORDS = [
    "warrior met", "alpha met", "alphametallurgical", "coronado",
    "ramaco", "arch leer", "arch mountain laurel", "arch beckley",
    "icg tygart", "arch resources", "united coal", "red river coal",
    "metinvest", "affinity", "javelin", "bluegrass natural", "harlan cumberland",
    "iron senergy", "iron cumberland", "pocahontas", "buchanan minerals",
]

# Mine names that are known HCC/premium met
HCC_MINE_NAMES = {
    "leer mine": "HCC",
    "leer south": "HCC",
    "mountain laurel": "HCC",
    "beckley pocahontas": "HCC",
    "no 7 mine": "HCC",
    "no. 7 mine": "HCC",
    "mine no. 7": "HCC",
    "mine no. 4": "HCC",
    "buchanan mine": "HCC",
    "deep mine 41": "HCC",
    "kingston mine": "HCC",
    "elk creek": "HCC",
    "knox creek": "PCI",
    "affinity": "HCC",
    "panther mine": "HCC",
    "panther creek": "HCC",
}

# Surface mines in these states → thermal/sub-bituminous
SURFACE_THERMAL_STATES = {"WY", "MT", "TX", "ND", "MS", "LA", "NM", "CO", "UT"}
# Underground mines in these states → ILB thermal
THERMAL_UG_STATES = {"IL", "IN"}
# PRB states
PRB_STATES = {"WY", "MT"}


def classify_coal_type(row: pd.Series) -> str:
    """Assign coal type based on state, county, mine type, and operator name."""
    state = str(row.get("STATE", "")).strip().upper()
    county = str(row.get("FIPS_CNTY_NM", "")).strip().title()
    mine_type = str(row.get("CURRENT_MINE_TYPE", "")).strip()
    operator = str(row.get("CURRENT_OPERATOR_NAME", "")).strip().lower()
    mine_name = str(row.get("CURRENT_MINE_NAME", row.get("CURR_MINE_NM", ""))).strip().lower()

    # 1. Check for explicit HCC mine name
    for key, coal_type in HCC_MINE_NAMES.items():
        if key in mine_name:
            return coal_type

    # 2. Check met operator keywords
    for kw in MET_OPERATORS_KEYWORDS:
        if kw in operator:
            return "Metallurgical"

    # 3. Lignite states/types
    if state in {"TX", "ND", "MS", "LA"} or "Lignite" in mine_type:
        return "Lignite (Thermal)"

    # 4. PRB sub-bituminous
    if state in PRB_STATES and "Surface" in mine_type:
        return "Sub-bituminous (Thermal)"

    # 5. Anthracite (PA/VA anthracite regions)
    if state in {"PA", "VA"} and "Anthracite" in str(row.get("PRIMARY_SIC", "")):
        return "Anthracite"

    # 6. Met coal counties — underground only
    if "Underground" in mine_type:
        state_met_counties = MET_COAL_COUNTIES.get(state, set())
        if county in state_met_counties:
            return "Metallurgical"

    # 7. Illinois Basin thermal
    if state in THERMAL_UG_STATES:
        return "Thermal (ILB)"

    # 8. Surface in thermal states
    if state in SURFACE_THERMAL_STATES:
        return "Thermal (Surface)"

    # 9. Default: bituminous thermal for everything else
    if "Underground" in mine_type and state in {"WV", "VA", "KY", "PA", "OH"}:
        return "Thermal (NAPP/CAPP)"

    return "Thermal (Bituminous)"


# Coal type → map color
COAL_TYPE_COLORS = {
    "HCC":                    "#c0392b",   # Deep red — premium export met
    "Metallurgical":          "#e74c3c",   # Red — met/coking
    "PCI":                    "#e67e22",   # Orange — pulverized coal injection
    "Sub-bituminous (Thermal)": "#f39c12", # Amber — PRB
    "Thermal (ILB)":          "#8e44ad",   # Purple — Illinois Basin
    "Thermal (Surface)":      "#f1c40f",   # Yellow — generic surface thermal
    "Thermal (Bituminous)":   "#3498db",   # Blue — general bituminous thermal
    "Thermal (NAPP/CAPP)":    "#2980b9",   # Darker blue — NAPP thermal
    "Lignite (Thermal)":      "#95a5a6",   # Gray — lignite
    "Anthracite":             "#2c3e50",   # Near-black
}


# ─── Coal Basins ──────────────────────────────────────────────────────────────

COAL_BASINS = [
    {
        "name": "Powder River Basin (PRB)", "abbrev": "PRB",
        "color": "#f39c12", "rank": "Sub-bituminous",
        "production": "~240 MST/yr (2024)", "export_pct": "<5%",
        "notes": "Wyoming + Montana; largest US coal reserve by volume; BNSF/UP Joint Line; primarily domestic power gen",
        "coords": [[-110.0, 44.0], [-103.5, 44.0], [-103.5, 47.5], [-110.0, 47.5], [-110.0, 44.0]],
    },
    {
        "name": "Central Appalachian (CAPP)", "abbrev": "CAPP",
        "color": "#c0392b", "rank": "Bituminous (met + thermal)",
        "production": "~70 MST/yr (2024)", "export_pct": "~40–50%",
        "notes": "WV, VA, eastern KY; premier US metallurgical coal; served by CSX and NS; primary Hampton Roads feeder",
        "coords": [[-83.5, 36.5], [-78.5, 36.5], [-78.5, 39.5], [-83.5, 39.5], [-83.5, 36.5]],
    },
    {
        "name": "Northern Appalachian (NAPP)", "abbrev": "NAPP",
        "color": "#e74c3c", "rank": "Bituminous (thermal + some met)",
        "production": "~60 MST/yr (2024)", "export_pct": "~20–25%",
        "notes": "SW Pennsylvania (Greene/Washington counties), north WV, east Ohio; CONSOL PAMC complex; CSX and NS",
        "coords": [[-82.5, 38.5], [-78.0, 38.5], [-78.0, 42.0], [-82.5, 42.0], [-82.5, 38.5]],
    },
    {
        "name": "Illinois Basin (ILB)", "abbrev": "ILB",
        "color": "#8e44ad", "rank": "Bituminous (high-sulfur)",
        "production": "~110 MST/yr (2024)", "export_pct": "~15–20%",
        "notes": "IL, IN, western KY; high-sulfur coal viable due to power plant scrubbers; exports via New Orleans barge",
        "coords": [[-91.5, 36.5], [-85.5, 36.5], [-85.5, 42.5], [-91.5, 42.5], [-91.5, 36.5]],
    },
    {
        "name": "Warrior Basin (Alabama HCC)", "abbrev": "WARRIOR",
        "color": "#d35400", "rank": "High-vol HCC (premium coking)",
        "production": "~12 MST/yr (2024)", "export_pct": "~100%",
        "notes": "Tuscaloosa/Jefferson counties AL; world-class hard coking coal; Warrior Met Coal + Coronado Blue Creek; 100% export via Mobile, AL",
        "coords": [[-87.5, 33.0], [-86.0, 33.0], [-86.0, 34.3], [-87.5, 34.3], [-87.5, 33.0]],
    },
    {
        "name": "Uinta-Piceance Basin", "abbrev": "UIB",
        "color": "#27ae60", "rank": "Bituminous (thermal + some met)",
        "production": "~15 MST/yr (2024)", "export_pct": "~10%",
        "notes": "Utah and Colorado; SUFCO, West Elk mine; limited rail access constrains exports",
        "coords": [[-110.0, 38.5], [-106.0, 38.5], [-106.0, 40.5], [-110.0, 40.5], [-110.0, 38.5]],
    },
    {
        "name": "Gulf / Fort Union Lignite", "abbrev": "LIGNITE",
        "color": "#95a5a6", "rank": "Lignite",
        "production": "~60 MST/yr (2024)", "export_pct": "0%",
        "notes": "TX, ND, MS; mine-mouth power plants only; not economically viable for export",
        "coords": [[-97.0, 29.5], [-88.0, 29.5], [-88.0, 33.0], [-97.0, 33.0], [-97.0, 29.5]],
    },
]


# ─── Export Terminals ─────────────────────────────────────────────────────────

EXPORT_TERMINALS = [
    {
        "name": "Lamberts Point Coal Terminal", "port": "Hampton Roads, VA",
        "operator": "Norfolk Southern Railway", "lat": 36.913, "lon": -76.322,
        "capacity_mst": 28, "draft_ft": 47, "vessel": "Capesize",
        "rail": "NS only", "coal_type": "Metallurgical (primary) + Thermal",
        "notes": "Largest single coal terminal in Western Hemisphere by capacity; direct NS main-line conveyor; ~75% of US met coal exports",
    },
    {
        "name": "Dominion Terminal Associates (DTA)", "port": "Newport News, VA",
        "operator": "Core Natural Resources / partners", "lat": 37.003, "lon": -76.440,
        "capacity_mst": 22, "draft_ft": 45, "vessel": "Capesize capable",
        "rail": "CSX + NS", "coal_type": "Metallurgical + Thermal",
        "notes": "Blending capability; CONSOL (now Core Natural Resources) primary supplier; Newport News James River location",
    },
    {
        "name": "Curtis Bay Energy Terminal", "port": "Baltimore, MD",
        "operator": "Curtis Bay Energy LLC", "lat": 39.221, "lon": -76.577,
        "capacity_mst": 14, "draft_ft": 43, "vessel": "Panamax",
        "rail": "CSX only", "coal_type": "Metallurgical (NAPP)",
        "notes": "Former B&O mainline via Cumberland Gap; CONSOL/Core PAMC complex primary source; primarily NAPP met coal",
    },
    {
        "name": "McDuffie Coal Terminal", "port": "Mobile, AL",
        "operator": "Alabama State Port Authority", "lat": 30.699, "lon": -88.024,
        "capacity_mst": 32, "draft_ft": 43, "vessel": "Panamax (light-loaded)",
        "rail": "CSX + NS + CPKC",
        "coal_type": "Warrior HCC (Warrior Met) + Thermal (ILB/PRB)",
        "notes": "Largest designed capacity in US; serves 3 Class I railroads; Warrior Met Coal primary Alabama HCC shipper; also receives ILB via barge + rail",
    },
    {
        "name": "Kinder Morgan Deepwater Terminal", "port": "Burnside, LA (Mississippi Mile 170)",
        "operator": "Kinder Morgan Inc.", "lat": 30.117, "lon": -90.851,
        "capacity_mst": 15, "draft_ft": 43, "vessel": "Panamax",
        "rail": "BNSF + UP + CPKC", "coal_type": "Thermal (ILB + PRB)",
        "notes": "Barge-to-ship transload; Ohio River ILB coal delivered by barge; some PRB via rail; primarily European thermal coal market",
    },
]

# ─── Rail colors ──────────────────────────────────────────────────────────────

RAIL_COLORS = {
    "BNSF": "#f57c00", "UP": "#f9a825", "CSXT": "#1565c0",
    "NS": "#263238", "CN": "#c62828", "CPRS": "#880e4f",
}
COAL_RAIL = {"BNSF", "UP", "CSXT", "NS"}
COAL_RIVER_KEYWORDS = [
    "OHIO", "MISSISSIPPI", "KANAWHA", "BIG SANDY", "CUMBERLAND",
    "TENNESSEE", "TOMBIGBEE", "MONONGAHELA", "ALLEGHENY", "GREEN",
    "MOBILE", "WARRIOR", "GUYANDOTTE", "ELK RIVER",
]

# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_mines_with_production(min_prod: int = 0, all_statuses: bool = False) -> pd.DataFrame:
    """Load MSHA mines joined with annual production from MinesProdQuarterly."""
    if not MSHA_TXT.exists():
        print(f"  ⚠ {MSHA_TXT.name} not found")
        return pd.DataFrame()

    # Load mines
    mines = pd.read_csv(MSHA_TXT, sep="|", encoding="latin-1", low_memory=False)
    coal = mines[mines["COAL_METAL_IND"] == "C"].copy()

    if not all_statuses:
        coal = coal[coal["CURRENT_MINE_STATUS"].isin(["Active", "Temporarily Idled"])]

    # Load production if available
    if PROD_TXT.exists():
        print(f"  Loading production quarterly data ({PROD_TXT.stat().st_size/1024/1024:.0f} MB)...")
        prod = pd.read_csv(PROD_TXT, sep="|", encoding="latin-1", low_memory=False)
        coal_prod = prod[prod["COAL_METAL_IND"] == "C"]
        recent = coal_prod[coal_prod["CAL_YR"] >= 2022]

        annual = (
            recent.groupby(["MINE_ID", "CAL_YR"])["COAL_PRODUCTION"]
            .sum().reset_index()
        )
        latest = annual.groupby("MINE_ID")["CAL_YR"].max().reset_index()
        latest.columns = ["MINE_ID", "LATEST_YR"]
        annual = annual.merge(latest, on="MINE_ID")
        annual = annual[annual["CAL_YR"] == annual["LATEST_YR"]][
            ["MINE_ID", "COAL_PRODUCTION", "LATEST_YR"]
        ]

        coal = coal.merge(annual, on="MINE_ID", how="left")
        coal["COAL_PRODUCTION"] = pd.to_numeric(coal["COAL_PRODUCTION"], errors="coerce").fillna(0)
        print(f"  Production data joined: {(coal['COAL_PRODUCTION'] > 0).sum():,} mines with production data")
    else:
        coal["COAL_PRODUCTION"] = 0
        coal["LATEST_YR"] = 2024
        print("  ⚠ No production data — all mines shown at equal size")

    # Classify coal type
    coal["coal_type"] = coal.apply(classify_coal_type, axis=1)

    # Filter by minimum production
    if min_prod > 0:
        with_prod = coal[coal["COAL_PRODUCTION"] >= min_prod]
        without = coal[coal["COAL_PRODUCTION"] == 0]
        coal = pd.concat([with_prod, without])  # Keep zero-prod active mines too
        coal = coal[coal["COAL_PRODUCTION"] >= min_prod] if min_prod > 0 else coal

    # Drop missing coords
    coal["LATITUDE"] = pd.to_numeric(coal["LATITUDE"], errors="coerce")
    coal["LONGITUDE"] = pd.to_numeric(coal["LONGITUDE"], errors="coerce")
    coal = coal.dropna(subset=["LATITUDE", "LONGITUDE"])

    return coal.sort_values("COAL_PRODUCTION", ascending=False)


def load_rail_geojson() -> dict | None:
    if not RAIL_GEOJSON.exists():
        return None
    with open(RAIL_GEOJSON) as f:
        return json.load(f)


def load_waterway_geojson() -> dict | None:
    if not WATERWAY_GEOJSON.exists():
        return None
    with open(WATERWAY_GEOJSON) as f:
        raw = json.load(f)
    coal_feats = [
        f for f in raw["features"]
        if any(kw in (f["properties"].get("RIVERNAME") or "").upper()
               for kw in COAL_RIVER_KEYWORDS)
    ]
    print(f"  Waterway: {len(coal_feats)} coal river segments")
    return {"type": "FeatureCollection", "features": coal_feats}


# ─── Map Scale ────────────────────────────────────────────────────────────────

def production_to_radius(tons: float) -> float:
    """Scale circle radius from production tonnage (log scale, 3–18 px)."""
    if tons <= 0:
        return 4
    # log scale: 500K tons → ~5px, 5M → ~9px, 50M → ~15px, 100M → ~18px
    return min(18, max(4, 3 + math.log10(max(tons, 100000)) * 2.2))


# ─── Map Layers ───────────────────────────────────────────────────────────────

def add_basin_layer(m: folium.Map) -> None:
    group = folium.FeatureGroup(name="🟫 Coal Basins", show=True)
    for basin in COAL_BASINS:
        poly_coords = [[lat, lng] for lng, lat in basin["coords"]]
        popup_html = f"""
        <div style="font-family:Arial,sans-serif;width:270px">
          <b style="font-size:13px">{basin['name']}</b>
          <hr style="margin:4px 0">
          <b>Coal Rank:</b> {basin['rank']}<br>
          <b>Production:</b> {basin['production']}<br>
          <b>Export Share:</b> {basin['export_pct']}<br>
          <br><span style="color:#555;font-size:11px">{basin['notes']}</span>
        </div>
        """
        folium.Polygon(
            locations=poly_coords, color=basin["color"], weight=2,
            fill=True, fill_color=basin["color"], fill_opacity=0.10,
            popup=folium.Popup(popup_html, max_width=290),
            tooltip=f"{basin['abbrev']} — {basin['rank']}",
        ).add_to(group)
        # Label
        lats = [c[1] for c in basin["coords"][:-1]]
        lngs = [c[0] for c in basin["coords"][:-1]]
        folium.Marker(
            location=[sum(lats)/len(lats), sum(lngs)/len(lngs)],
            icon=folium.DivIcon(
                html=f"""<div style="font-family:Arial;font-size:10px;font-weight:bold;
                color:{basin['color']};text-shadow:1px 1px 2px #fff,-1px -1px 2px #fff;
                white-space:nowrap">{basin['abbrev']}</div>""",
                icon_size=(80, 20), icon_anchor=(40, 10),
            ),
        ).add_to(group)
    group.add_to(m)
    print(f"  ✓ Basin polygons: {len(COAL_BASINS)}")


def add_mine_layer(mines: pd.DataFrame, m: folium.Map, min_prod: int) -> None:
    """Production-weighted mine circles colored by coal type."""
    if mines.empty:
        print("  ⚠ No mine data")
        return

    # Separate large producers from small for clustering decisions
    major = mines[mines["COAL_PRODUCTION"] >= 1_000_000]
    minor = mines[mines["COAL_PRODUCTION"] < 1_000_000]

    # Layer for major mines (always shown, no clustering)
    major_group = folium.FeatureGroup(
        name=f"⛏ Major Mines (≥1M ST/yr): {len(major):,}", show=True
    )
    for _, row in major.iterrows():
        _add_mine_circle(row, major_group)
    major_group.add_to(m)

    # Layer for smaller mines (clustered)
    if len(minor) > 0 and min_prod < 1_000_000:
        minor_group = folium.FeatureGroup(
            name=f"⛏ Smaller Mines (<1M ST/yr): {len(minor):,}", show=False
        )
        cluster = MarkerCluster(options={"maxClusterRadius": 35, "showCoverageOnHover": False})
        for _, row in minor.iterrows():
            _add_mine_circle(row, cluster, small=True)
        cluster.add_to(minor_group)
        minor_group.add_to(m)

    print(f"  ✓ Mine layers: {len(major):,} major + {len(minor):,} smaller")


def _add_mine_circle(row: pd.Series, target, small: bool = False) -> None:
    prod = float(row.get("COAL_PRODUCTION", 0))
    coal_type = row.get("coal_type", "Thermal (Bituminous)")
    color = COAL_TYPE_COLORS.get(coal_type, "#3498db")
    radius = production_to_radius(prod) if not small else 4
    prod_str = f"{prod/1_000_000:.2f}M ST" if prod >= 1_000_000 else (
        f"{prod/1_000:.0f}K ST" if prod > 0 else "N/A"
    )
    employees = row.get("NO_EMPLOYEES", "N/A")
    yr = int(row.get("LATEST_YR", 0)) if row.get("LATEST_YR") else "N/A"

    popup_html = f"""
    <div style="font-family:Arial,sans-serif;width:270px">
      <b style="font-size:12px">{row['CURRENT_MINE_NAME']}</b>
      <span style="background:{color};color:white;padding:1px 6px;border-radius:3px;
            font-size:10px;margin-left:6px">{coal_type}</span><br>
      <hr style="margin:4px 0">
      <b>Operator:</b> {row.get('CURRENT_OPERATOR_NAME','N/A')}<br>
      <b>Parent Co:</b> {row.get('CURRENT_CONTROLLER_NAME','N/A')}<br>
      <b>Location:</b> {row.get('FIPS_CNTY_NM','')}, {row.get('STATE','')}<br>
      <b>Mine Type:</b> {row.get('CURRENT_MINE_TYPE','N/A')}<br>
      <b>Production:</b> <b style="color:{color}">{prod_str}</b>
      {'(' + str(yr) + ')' if yr != 'N/A' else ''}<br>
      <b>Employees:</b> {employees}<br>
      <b>MSHA ID:</b> {row['MINE_ID']}
    </div>
    """
    folium.CircleMarker(
        location=[row["LATITUDE"], row["LONGITUDE"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.80,
        weight=1.2,
        popup=folium.Popup(popup_html, max_width=290),
        tooltip=f"{row['CURRENT_MINE_NAME']} | {coal_type} | {prod_str}",
    ).add_to(target)


def add_rail_layer(rail_data: dict, m: folium.Map) -> None:
    if not rail_data:
        return
    group = folium.FeatureGroup(name="🚂 Class I Rail Corridors", show=True)
    for feat in rail_data["features"]:
        rr = feat["properties"].get("RROWNER1", "")
        name = feat["properties"].get("NAME", rr)
        miles = feat["properties"].get("TOTAL_MILES", 0)
        color = RAIL_COLORS.get(rr, "#888")
        weight = 3.5 if rr in COAL_RAIL else 1.5
        opacity = 0.85 if rr in COAL_RAIL else 0.35

        coal_desc = {
            "BNSF": "Primary PRB carrier — Wyoming surface mines to Midwest/Gulf power plants",
            "UP": "PRB carrier (joint line with BNSF); Gulf Coast to power plants; Colorado mines",
            "CSXT": "Appalachian coal to Hampton Roads/Baltimore/Great Lakes; Cumberland corridor",
            "NS": "Appalachian coal to Lamberts Point (Norfolk) + other Atlantic ports",
            "CN": "Canadian operations; some northern US coal",
            "CPRS": "Canadian Pacific; limited US coal service",
        }.get(rr, "")

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;width:250px">
          <b style="font-size:13px">{name}</b><br>
          <b>Coal Carrier:</b> {'Primary' if rr in COAL_RAIL else 'Limited'}<br>
          <b>Network:</b> {miles:,.0f} miles (STRACNET)<br>
          <span style="color:#555;font-size:11px">{coal_desc}</span>
        </div>
        """
        folium.GeoJson(
            feat,
            style_function=lambda f, c=color, w=weight, o=opacity: {
                "color": c, "weight": w, "opacity": o
            },
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{name} — Coal service: {'Yes' if rr in COAL_RAIL else 'Limited'}",
        ).add_to(group)
    group.add_to(m)
    print(f"  ✓ Rail corridors: {len(rail_data['features'])} Class I")


def add_waterway_layer(ww: dict, m: folium.Map) -> None:
    if not ww or not ww.get("features"):
        return
    group = folium.FeatureGroup(name="🚢 Coal Barge Waterways", show=True)
    folium.GeoJson(
        ww,
        style_function=lambda f: {"color": "#1a6ea3", "weight": 2, "opacity": 0.65},
        tooltip=folium.GeoJsonTooltip(fields=["RIVERNAME"], aliases=["River:"]),
    ).add_to(group)
    group.add_to(m)
    print(f"  ✓ Waterways: {len(ww['features'])} coal river segments")


def add_terminal_layer(m: folium.Map) -> None:
    group = folium.FeatureGroup(name="🏭 Coal Export Terminals", show=True)
    for t in EXPORT_TERMINALS:
        popup_html = f"""
        <div style="font-family:Arial,sans-serif;width:290px">
          <b style="font-size:13px">{t['name']}</b><br>
          <span style="color:#555;font-size:11px">{t['port']}</span>
          <hr style="margin:5px 0">
          <b>Operator:</b> {t['operator']}<br>
          <b>Capacity:</b> {t['capacity_mst']} MST/yr<br>
          <b>Max Draft:</b> {t['draft_ft']} ft ({t['vessel']})<br>
          <b>Rail Access:</b> {t['rail']}<br>
          <b>Coal Types:</b> {t['coal_type']}<br>
          <hr style="margin:5px 0">
          <span style="color:#666;font-size:10px">{t['notes']}</span>
        </div>
        """
        folium.Marker(
            location=[t["lat"], t["lon"]],
            icon=folium.DivIcon(
                html="""<div style="width:20px;height:20px;background:#d32f2f;
                border:2.5px solid #fff;border-radius:3px;transform:rotate(45deg);
                box-shadow:0 2px 8px rgba(0,0,0,0.5)"></div>""",
                icon_size=(24, 24), icon_anchor=(12, 12),
            ),
            popup=folium.Popup(popup_html, max_width=310),
            tooltip=f"🏭 {t['name']} — {t['capacity_mst']} MST/yr",
        ).add_to(group)
    group.add_to(m)
    print(f"  ✓ Export terminals: {len(EXPORT_TERMINALS)}")


def add_legend(m: folium.Map, mines: pd.DataFrame) -> None:
    type_counts = mines["coal_type"].value_counts().to_dict() if not mines.empty else {}
    n_major = int((mines["COAL_PRODUCTION"] >= 1_000_000).sum()) if not mines.empty else 0

    type_rows = ""
    for ctype, color in COAL_TYPE_COLORS.items():
        n = type_counts.get(ctype, 0)
        if n == 0:
            continue
        type_rows += f"""
        <div style="margin-bottom:3px">
          <span style="display:inline-block;width:11px;height:11px;border-radius:50%;
                background:{color};border:1px solid #aaa;vertical-align:middle"></span>
          <span style="vertical-align:middle;font-size:11px"> {ctype} ({n})</span>
        </div>"""

    legend_html = f"""
    <div id="coal-legend" style="position:fixed;bottom:35px;left:12px;z-index:1000;
        background:rgba(255,255,255,0.95);padding:12px 16px;border-radius:8px;
        border:1px solid #ccc;font-family:Arial,sans-serif;font-size:11px;
        box-shadow:0 2px 12px rgba(0,0,0,0.15);max-width:220px;
        transition:background 0.3s,color 0.3s,border-color 0.3s">
      <b style="font-size:12px">US Coal Supply Chain</b>
      <div style="color:#888;font-size:10px;margin-bottom:8px">
        Circle size ∝ production (ST/yr)
      </div>

      <b style="color:#555">COAL TYPES / MINES</b>
      {type_rows}
      <div style="margin-top:4px;color:#888;font-size:10px">
        Major (≥1M ST/yr): {n_major:,} mines shown
      </div>

      <div style="margin-top:8px;border-top:1px solid #eee;padding-top:6px">
        <b style="color:#555">BASINS</b>
        <div>🟧 PRB &nbsp; 🟥 CAPP/Warrior</div>
        <div>🟪 Illinois Basin &nbsp; 🟩 UIB</div>
      </div>

      <div style="margin-top:8px;border-top:1px solid #eee;padding-top:6px">
        <b style="color:#555">INFRASTRUCTURE</b>
        <div><span style="color:#f57c00">━━</span> BNSF (PRB)</div>
        <div><span style="color:#f9a825">━━</span> UP (PRB/Gulf)</div>
        <div><span style="color:#1565c0">━━</span> CSX (Appalachia)</div>
        <div><span style="color:#263238">━━</span> NS (Appalachia)</div>
        <div><span style="color:#1a6ea3">━━</span> Coal Waterways</div>
        <div><span style="color:#d32f2f">◆</span> Export Terminal</div>
      </div>

      <div style="margin-top:8px;padding-top:6px;border-top:1px solid #eee;
          color:#aaa;font-size:10px">
        Data: MSHA 2025 | BTS NTAD<br>
        © William S. Davis III
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def add_title(m: folium.Map, n_mines: int, min_prod: int) -> None:
    prod_label = f" | Mines ≥ {min_prod/1_000_000:.1f}M ST/yr" if min_prod >= 1_000_000 else \
                 f" | Mines ≥ {min_prod/1_000:.0f}K ST/yr" if min_prod > 0 else ""
    title_html = f"""
    <div id="coal-title" style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
        z-index:1000;background:rgba(25,25,25,0.88);color:white;
        padding:9px 22px;border-radius:6px;font-family:Arial,sans-serif;
        font-size:14px;font-weight:bold;box-shadow:0 2px 10px rgba(0,0,0,0.3);
        text-align:center;white-space:nowrap">
      US Coal Supply Chain — Thermal &amp; Metallurgical{prod_label}
      <div style="font-size:10px;font-weight:normal;color:#ccc;margin-top:2px">
        Click layers to toggle ∙ Click features for details ∙ Scroll to zoom
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))


# ─── Basemap Toggle ───────────────────────────────────────────────────────────

def add_basemap_controls(m: folium.Map, light_var: str, dark_var: str, sat_var: str) -> None:
    """Floating Light / Dark / Satellite switcher with legend theme adaptation."""
    map_var = m.get_name()
    control_html = f"""
    <div id="basemap-switcher" style="
        position:fixed;top:55px;right:12px;z-index:2000;
        display:flex;flex-direction:column;gap:5px;font-family:Arial,sans-serif">
      <button id="btn-light"     onclick="switchBasemap('light')"
        style="padding:5px 13px;border-radius:5px;cursor:pointer;font-size:12px;
               font-weight:bold;border:2px solid #bbb;background:rgba(255,255,255,0.93);
               color:#333;box-shadow:0 2px 6px rgba(0,0,0,0.25)">☀ Light</button>
      <button id="btn-dark"      onclick="switchBasemap('dark')"
        style="padding:5px 13px;border-radius:5px;cursor:pointer;font-size:12px;
               font-weight:bold;border:2px solid #555;background:rgba(35,35,40,0.93);
               color:#eee;box-shadow:0 2px 6px rgba(0,0,0,0.35)">🌑 Dark</button>
      <button id="btn-satellite" onclick="switchBasemap('satellite')"
        style="padding:5px 13px;border-radius:5px;cursor:pointer;font-size:12px;
               font-weight:bold;border:2px solid #1a4a7a;background:rgba(20,45,85,0.93);
               color:#c8dcf8;box-shadow:0 2px 6px rgba(0,0,0,0.35)">🛰 Satellite</button>
    </div>

    <script>
    (function() {{
        var MAP_VAR   = '{map_var}';
        var LIGHT_VAR = '{light_var}';
        var DARK_VAR  = '{dark_var}';
        var SAT_VAR   = '{sat_var}';
        var current   = 'dark';

        function getMap()   {{ return window[MAP_VAR]; }}
        function getLayers(){{ return {{ light: window[LIGHT_VAR], dark: window[DARK_VAR], satellite: window[SAT_VAR] }}; }}

        function highlightBtn(theme) {{
            ['light','dark','satellite'].forEach(function(t) {{
                var b = document.getElementById('btn-' + t);
                if (!b) return;
                b.style.outline      = (t === theme) ? '3px solid #4fc3f7' : 'none';
                b.style.outlineOffset= (t === theme) ? '1px' : '0';
            }});
        }}

        function applyTheme(theme) {{
            var legend = document.getElementById('coal-legend');
            if (!legend) return;
            var isDark = (theme !== 'light');
            legend.style.background  = isDark ? 'rgba(28,28,34,0.96)' : 'rgba(255,255,255,0.95)';
            legend.style.color       = isDark ? '#ddd'  : '#222';
            legend.style.borderColor = isDark ? '#555'  : '#ccc';
            // Section headers
            legend.querySelectorAll('b').forEach(function(el) {{
                el.style.color = isDark ? '#eee' : '';
            }});
            // Divider lines
            legend.querySelectorAll('div').forEach(function(el) {{
                if (el.style.borderTop) el.style.borderTopColor = isDark ? '#444' : '#eee';
            }});
        }}

        window.switchBasemap = function(theme) {{
            var map    = getMap();
            var layers = getLayers();
            if (!map || !layers[theme]) return;

            // Remove current base
            if (layers[current] && map.hasLayer(layers[current])) {{
                map.removeLayer(layers[current]);
            }}
            // Add new base and send to back so overlays stay visible
            layers[theme].addTo(map);
            layers[theme].bringToBack();

            current = theme;
            highlightBtn(theme);
            applyTheme(theme);
        }};

        // On load: apply dark theme as default
        document.addEventListener('DOMContentLoaded', function() {{
            highlightBtn('dark');
            applyTheme('dark');
        }});
    }})();
    </script>
    """
    m.get_root().html.add_child(folium.Element(control_html))


# ─── Main ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--output", default=str(DEFAULT_OUTPUT))
@click.option("--min-prod", default=100_000, type=int,
              help="Min annual production (ST) to show as major mine [default: 100000]")
@click.option("--all-mines", is_flag=True, help="Include all active mines regardless of size")
def main(output: str, min_prod: int, all_mines: bool):
    """Build US Coal Supply Chain map with thermal/met classification and production sizing."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    threshold = 0 if all_mines else min_prod

    print("\nBuilding US Coal Supply Chain Map (v2 — production-weighted + coal type)...")
    print(f"Output: {output_path}")
    print(f"Min production threshold: {threshold:,} ST/yr\n")

    # Base map — no default tiles; add all three explicitly so we track their JS var names
    m = folium.Map(location=[38.5, -95.0], zoom_start=5, tiles=None, prefer_canvas=True)

    light_layer = folium.TileLayer("CartoDB positron", name="☀ Light", show=False)
    light_layer.add_to(m)
    light_var = light_layer.get_name()

    dark_layer = folium.TileLayer("CartoDB dark_matter", name="🌑 Dark")   # default
    dark_layer.add_to(m)
    dark_var = dark_layer.get_name()

    sat_layer = folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="🛰 Satellite", show=False,
    )
    sat_layer.add_to(m)
    sat_var = sat_layer.get_name()

    # Data
    print("Loading data...")
    mines = load_mines_with_production(min_prod=threshold)
    rail = load_rail_geojson()
    waterways = load_waterway_geojson()

    # Layers (order matters for z-index: bottom first)
    print("\nAdding layers...")
    add_basin_layer(m)
    add_waterway_layer(waterways, m)
    add_rail_layer(rail, m)
    add_terminal_layer(m)
    add_mine_layer(mines, m, threshold)

    # Controls
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    MeasureControl(position="topleft").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    add_basemap_controls(m, light_var, dark_var, sat_var)
    add_legend(m, mines)
    add_title(m, len(mines), threshold)

    m.save(str(output_path))
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"\n✓ Map saved: {output_path} ({size_mb:.1f} MB)")

    # Summary
    if not mines.empty:
        print(f"\n── Mine Summary ─────────────────────────────────")
        print(mines["coal_type"].value_counts().to_string())
        major = mines[mines["COAL_PRODUCTION"] >= 1_000_000]
        print(f"\nTop 15 mines by production:")
        print(major[["CURRENT_MINE_NAME","STATE","CURRENT_CONTROLLER_NAME",
                      "coal_type","COAL_PRODUCTION"]].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
