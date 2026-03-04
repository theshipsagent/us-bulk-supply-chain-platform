#!/usr/bin/env python3
"""
build_lower_miss_static_map.py
Lower Mississippi River Bulk Terminal Map — OceanDatum.ai brand edition

Architectural-D (36 × 24 in) vector PDF with raster basemap.
Style: CartoDB DarkMatter basemap + custom OceanDatum brand overlays.
Scope: Head of Passes (MM 0) → Port Allen (MM 229).

Usage (from any directory):
    python3 02_TOOLSETS/geospatial_engine/src/build_lower_miss_static_map.py
    python3 ...  --draft      # 96 DPI PNG preview only (fast, no PDF)
    python3 ...  --zoom 12    # Higher basemap zoom (sharper, slower)

Outputs:
    04_REPORTS/presentations/lower_miss_river_map_oceandatum_v1.pdf
    04_REPORTS/presentations/lower_miss_river_map_oceandatum_v1_preview.png
    07_KNOWLEDGE_BANK/.../lower_miss_bws_terminals.geojson
    07_KNOWLEDGE_BANK/.../lower_miss_river_centerline.geojson
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from pyproj import Transformer
from shapely.ops import unary_union

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

_HERE     = Path(__file__).resolve()
_TOOLSET  = _HERE.parent.parent                          # geospatial_engine/
_PROJECT  = _TOOLSET.parent.parent                       # project_master_reporting/
_KB_NSC   = _PROJECT / "07_KNOWLEDGE_BANK/master_facility_register/data/national_supply_chain"
_REPORTS  = _PROJECT / "04_REPORTS/presentations"
_NE_CACHE = _TOOLSET / "data/natural_earth"
_NE_SHP   = Path("/opt/homebrew/lib/python3.14/site-packages/pyogrio/tests/fixtures/"
                 "naturalearth_lowres/naturalearth_lowres.shp")

_NE_CACHE.mkdir(parents=True, exist_ok=True)
_REPORTS.mkdir(parents=True, exist_ok=True)

# Make sibling modules importable when run as a standalone script
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
from layer_catalog import get_layer_path  # noqa: E402

# ---------------------------------------------------------------------------
# COORDINATE PROJECTIONS
# ---------------------------------------------------------------------------

_4326_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
_3857_to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)


def to_3857(lon: float, lat: float) -> tuple[float, float]:
    return _4326_to_3857.transform(lon, lat)


def deg_offset_to_m(lon: float, lat: float,
                    dlon: float, dlat: float) -> tuple[float, float]:
    """Convert degree offsets to metre offsets in EPSG:3857 at a given position."""
    x0, y0 = to_3857(lon, lat)
    x1, y1 = to_3857(lon + dlon, lat + dlat)
    return x1 - x0, y1 - y0


# ---------------------------------------------------------------------------
# MAP EXTENT (WGS84 → EPSG:3857)
# ---------------------------------------------------------------------------

EXTENT_4326 = {"west": -92.00, "east": -89.10, "south": 28.75, "north": 30.92}

_xmin, _ymin = to_3857(EXTENT_4326["west"],  EXTENT_4326["south"])
_xmax, _ymax = to_3857(EXTENT_4326["east"],  EXTENT_4326["north"])
EXTENT_3857 = {"xmin": _xmin, "ymin": _ymin, "xmax": _xmax, "ymax": _ymax}

# Figure size (Architectural-D landscape)
FIG_W, FIG_H = 36.0, 24.0

# ---------------------------------------------------------------------------
# COLOUR PALETTE — OceanDatum.ai brand
# ---------------------------------------------------------------------------

C = {
    # Map chrome — dark nautical chart aesthetic (clean, tile-free)
    "fig_bg":      "#03060f",   # figure background — deep ocean black
    "map_bg":      "#03060f",   # axes background — open water / void (darkest)
    "land_fill":   "#1e3250",   # land polygon fill — clear charcoal-blue (noticeably lighter than void)
    "land_edge":   "#2e4668",   # land polygon outline — slightly lighter

    # River body polygon (wide fill — the main river visual)
    "river_fill":  "#124ea8",   # wide river body — vivid cobalt (clearly brighter than land)
    "river_fill2": "#1e68cc",   # inner band — even brighter cobalt

    # River centerline glow (on top of polygon)
    "river_body":  "#2272d8",   # thick outer glow
    "river_mid":   "#3a90e8",   # mid glow
    "river_hl":    "#58b8f8",   # inner surface sheen
    "river_glow":  "#90d8ff",   # thin bright centreline

    # Terminal categories
    "grain":       "#64ffb4",   # OceanDatum mint  — grain elevators
    "general":     "#ff9f47",   # amber            — general / coal / bulk
    "liquid":      "#4dd4ff",   # cyan             — liquid / chemical
    "anchorage":   "#a78bfa",   # lavender         — anchorage / nav

    # Typography
    "text_white":  "#ffffff",
    "text_dim":    "#8899aa",
    "text_city":   "#cce0ee",
    "text_river":  "#6ac8f0",
    "text_region": "#2a3a4a",

    # Accent / brand
    "accent":      "#64ffb4",   # OceanDatum mint
    "accent_dim":  "#2a7a60",

    # Grid / frame
    "grid":        "#1e2a3a",
    "frame":       "#64ffb4",
    "frame_inner": "#1e3050",
}

# ---------------------------------------------------------------------------
# TYPOGRAPHY
# ---------------------------------------------------------------------------

F_SERIF  = "Georgia"
F_SANS   = "Helvetica Neue"
F_MONO   = "Courier New"

# ---------------------------------------------------------------------------
# TERMINAL METADATA
# ---------------------------------------------------------------------------

def _classify(props: dict) -> str:
    t = str(props.get("terminal_type", "")).lower()
    n = str(props.get("name", "")).lower()
    if "anchorage" in t or "anchorage" in n:
        return "anchorage"
    if "grain" in t:
        return "grain"
    if "molasses" in n or "stolt" in n or "chemical" in n or "liquid" in n:
        return "liquid"
    return "general"


MARKER_STYLE = {
    "grain":     ("o", 140, 1.6),   # (marker, size, edge_scale)
    "general":   ("s", 110, 1.5),
    "liquid":    ("D",  90, 1.4),
    "anchorage": ("^",  95, 1.5),
}

# Short display labels — keyed by full BWS name
SHORT_LABELS: dict[str, str] = {
    "Louis Dreyfus Corp - Port Allen":
        "LDC PORT ALLEN\nMM 229.2",
    "ADM Grain Co. - Ama":
        "ADM AMA\nMM 117.6",
    "ADM Grain Co., - Destrehan":
        "ADM DESTREHAN\nMM 120.6",
    "ADM Grain Co. - St. Elmo - Paulina, Louisiana":
        "ADM ST. ELMO\nMM 150.5",
    "ADM Grain Co., - Reserve":
        "ADM RESERVE\nMM 139.1",
    "Cargill, Inc. - Terre Haute - Reserve, Louisiana":
        "CARGILL TH\nMM 139.6",
    "Cargill, Inc. - Westwego, Louisiana":
        "CARGILL WESTWEGO\nMM 103",
    "Cargill Molasses":
        "CARGILL MOLASSES\nMM 140",
    "CHS, Inc. - Myrtle Grove Terminal":
        "CHS MYRTLE GROVE\nMM 61.5",
    "Zen-Noh Grain Corp. - Convent, Louisiana":
        "ZEN-NOH CONVENT\nMM 163.8",
    "NUCOR - Terminal - Convent, Louisiana":
        "NUCOR CONVENT\nMM 162.5",
    "Convent Marine Terminal Co.":
        "CONVENT MARINE\nMM 161",
    "Cooper/Consolidated Midstream Buoy":
        "COOPER / CONSOL\nMM 133",
    "Associated Terminals Midstream Buoys, MGMT Rig and Globalplex in Reserve":
        "ASSOC. TERMINALS\nMGMT RIG MM 57.8",
    "International Marine Terminal - Myrtle Grove, Louisiana":
        "INTL MARINE TERM.\nMM 57",
    "United Ocean Terminal - Davant, Louisiana":
        "UNITED OCEAN\nMM 56",
    "IMTT St. Rose":
        "IMTT ST. ROSE\nMM 118",
    "Stolt-Haven":
        "STOLT-HAVEN\nMM 79.5",
    "SouthWest Pass":
        "SOUTHWEST PASS\n(Deep Draft Entry)",
    "Point Michel Anchorage - MM 40.8 to MM 42.2, AHP":
        "POINT MICHEL\nANCHORAGE",
    "Plaquemines Point Anchorage - MM 203.9 to MM 204.4, AHP":
        "PLAQUEMINES PT.\nANCHORAGE",
}

# Label offsets: (dlon°, dlat°, ha, va)
# LEFT BANK → negative dlon (labels push west into open space)
# RIGHT BANK → positive dlon (labels push east into open space)
# Dense clusters staggered with varying dlon AND dlat to prevent overlap.
# All offsets 0.14–0.30° to ensure labels clear the river at 36" print width.
LABEL_OFF: dict[str, tuple[float, float, str, str]] = {
    # ======== UPPER RIVER — isolated, simple offsets ========
    "Louis Dreyfus Corp - Port Allen":
        (-0.25,  0.04, "right", "center"),   # MM 229 — isolated, push well left
    "Plaquemines Point Anchorage - MM 203.9 to MM 204.4, AHP":
        ( 0.22,  0.06, "left",  "center"),   # MM 204 — push right

    # ======== CONVENT CLUSTER — MM 161–164 (4 terminals, tight) ========
    # Left bank: NUCOR, Convent Marine — stagger vertically
    "NUCOR - Terminal - Convent, Louisiana":
        (-0.22,  0.08, "right", "center"),   # push left+up
    "Convent Marine Terminal Co.":
        (-0.26, -0.06, "right", "center"),   # push left+down
    # Right bank: Zen-Noh — push right
    "Zen-Noh Grain Corp. - Convent, Louisiana":
        ( 0.20,  0.06, "left",  "center"),

    # ======== ADM ST ELMO — MM 150.5 ========
    "ADM Grain Co. - St. Elmo - Paulina, Louisiana":
        ( 0.22, -0.04, "left",  "center"),

    # ======== CARGILL MOLASSES — MM ~140, left bank ========
    "Cargill Molasses":
        (-0.24,  0.06, "right", "center"),

    # ======== RESERVE CLUSTER — MM 133–140 (5 terminals, very tight) ========
    # Left bank: ADM Destrehan (120.6), ADM Ama (117.6) slightly above cluster
    "ADM Grain Co., - Destrehan":
        (-0.28,  0.10, "right", "center"),   # echelon up-left
    "ADM Grain Co. - Ama":
        (-0.22,  0.05, "right", "center"),   # middle-left
    # Right bank: Cargill TH, ADM Reserve, Cooper
    "Cargill, Inc. - Terre Haute - Reserve, Louisiana":
        ( 0.24,  0.10, "left",  "center"),   # echelon up-right
    "ADM Grain Co., - Reserve":
        ( 0.18, -0.00, "left",  "center"),   # middle-right
    "Cooper/Consolidated Midstream Buoy":
        ( 0.26, -0.10, "left",  "center"),   # echelon down-right

    # ======== IMTT ST ROSE — MM 118, right bank ========
    "IMTT St. Rose":
        ( 0.20,  0.02, "left",  "center"),

    # ======== WESTWEGO / NEW ORLEANS CLUSTER — MM 95–110 ========
    "Cargill, Inc. - Westwego, Louisiana":
        (-0.24, -0.04, "right", "center"),

    # ======== STOLT-HAVEN — MM 79.5, right bank ========
    "Stolt-Haven":
        ( 0.22,  0.04, "left",  "center"),

    # ======== LOWER RIVER CLUSTER — MM 56–62 ========
    "CHS, Inc. - Myrtle Grove Terminal":
        (-0.22,  0.06, "right", "center"),   # left bank
    "Associated Terminals Midstream Buoys, MGMT Rig and Globalplex in Reserve":
        (-0.24, -0.06, "right", "center"),   # left bank, below
    "International Marine Terminal - Myrtle Grove, Louisiana":
        ( 0.22,  0.04, "left",  "center"),   # right bank
    "United Ocean Terminal - Davant, Louisiana":
        ( 0.20, -0.06, "left",  "center"),   # right bank, below

    # ======== NAVIGATION FEATURES ========
    "SouthWest Pass":
        ( 0.16, -0.06, "left",  "center"),
    "Point Michel Anchorage - MM 40.8 to MM 42.2, AHP":
        (-0.18,  0.06, "right", "center"),
}

# ---------------------------------------------------------------------------
# GEOGRAPHIC LABELS (in 4326, rendered in 3857)
# ---------------------------------------------------------------------------

# (lon, lat, text, fontsize, rotation, color_key)
WATER_LABELS = [
    (-91.20,  29.00, "GULF OF\nMEXICO",       16,  0, "text_river"),
    (-90.08,  29.96, "MISSISSIPPI\nRIVER",     11, 80, "text_river"),
    (-90.56,  30.04, "MISSISSIPPI\nRIVER",     11, 65, "text_river"),
    (-91.04,  30.16, "MISSISSIPPI\nRIVER",     10, 60, "text_river"),
    (-91.18,  30.38, "MISSISSIPPI\nRIVER",     10, 55, "text_river"),
    (-89.42,  28.94, "SOUTHWEST\nPASS",        10, 35, "text_river"),
    (-90.85,  29.88, "LAKE\nSALVADOR",          9,  0, "text_river"),
    (-89.92,  29.42, "BARATARIA\nBAY",           9,  0, "text_river"),
    (-90.10,  30.22, "LAKE\nPONTCHARTRAIN",    10,  0, "text_river"),
    (-90.28,  30.68, "LAKE\nMAURÉPAS",           9,  0, "text_river"),
    (-89.32,  29.28, "CHANDELEUR\nSOUND",        9,  0, "text_river"),
    (-89.55,  29.10, "BIRDFOOT\nDELTA",          9, 15, "text_river"),
]

# (lon, lat, text, fontsize)
CITY_LABELS = [
    (-90.0715, 29.9511, "NEW ORLEANS",    15),
    (-91.1871, 30.4515, "BATON ROUGE",    15),
    (-89.9578, 29.7752, "CHALMETTE",      10),
    (-90.3778, 29.9199, "LULING",          9),
    (-90.5843, 30.0594, "RESERVE",         9),
    (-90.8779, 30.0630, "CONVENT",         9),
    (-91.1998, 30.4394, "PORT ALLEN",     10),
    (-89.9614, 29.6731, "MYRTLE GROVE",    9),
    (-90.1152, 29.9378, "WESTWEGO",        9),
    (-89.9028, 29.6215, "DAVANT",          9),
    (-90.2200, 29.9600, "GRETNA",          9),
    (-90.5200, 30.0700, "LAPLACE",         9),
    (-90.8900, 30.0400, "ST. JAMES",       9),
    (-91.0500, 30.1800, "LUTCHER",         9),
    (-91.1600, 30.2400, "GRAMERCY",        9),
    (-89.3500, 29.2700, "VENICE",          9),
]

REGION_LABELS = [
    (-90.50, 30.80, "LOUISIANA",   24, "#2d5080"),
    (-89.40, 30.60, "MISSISSIPPI", 18, "#2d5080"),
]

# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

def load_bws_terminals() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(get_layer_path("facilities_bws_all_terminals"))
    miss = gdf[gdf["port_region"] == "Mississippi River"].copy()
    return miss.set_crs("EPSG:4326", allow_override=True)


def load_waterways_miss() -> gpd.GeoDataFrame:
    from shapely.geometry import box as sbox
    gdf = gpd.read_file(get_layer_path("waterways_major"))
    miss = gdf[gdf["RIVERNAME"].str.contains("MISSISSIPPI", case=False, na=False)].copy()
    clip_box = sbox(
        EXTENT_4326["west"] - 0.3, EXTENT_4326["south"] - 0.3,
        EXTENT_4326["east"] + 0.3, EXTENT_4326["north"] + 0.3,
    )
    miss = miss.set_crs("EPSG:4326", allow_override=True)
    return miss.clip(clip_box)


def load_ne_land() -> gpd.GeoDataFrame:
    """Low-res world countries — used as land background polygon."""
    if _NE_SHP.exists():
        world = gpd.read_file(_NE_SHP)
        # Keep only countries in the map extent
        from shapely.geometry import box as sbox
        clip = sbox(EXTENT_4326["west"] - 1, EXTENT_4326["south"] - 1,
                    EXTENT_4326["east"] + 1, EXTENT_4326["north"] + 1)
        subset = world[world.intersects(clip)].copy()
        return subset.set_crs("EPSG:4326", allow_override=True)
    return gpd.GeoDataFrame()


def save_layers(terminals: gpd.GeoDataFrame,
                waterways: gpd.GeoDataFrame) -> None:
    t_out = _KB_NSC / "lower_miss_bws_terminals.geojson"
    w_out = _KB_NSC / "lower_miss_river_centerline.geojson"
    terminals.to_file(t_out, driver="GeoJSON")
    waterways.to_file(w_out, driver="GeoJSON")
    print(f"  Saved: {t_out.name}  ({len(terminals)} features)")
    print(f"  Saved: {w_out.name}  ({len(waterways)} features)")


# ---------------------------------------------------------------------------
# DRAWING HELPERS
# ---------------------------------------------------------------------------

_outline_sm = [pe.withStroke(linewidth=2.5, foreground="#0d1117")]
_outline_md = [pe.withStroke(linewidth=4.0, foreground="#0d1117")]
_outline_lg = [pe.withStroke(linewidth=5.5, foreground="#0d1117")]


def draw_brand_lockup(ax: plt.Axes) -> None:
    """OceanDatum.ai brand block — bottom-left, floating over map."""
    # Semi-transparent backing panel
    bx = 0.012
    by = 0.012
    panel = FancyBboxPatch(
        (bx, by), 0.230, 0.118,
        boxstyle="round,pad=0.005",
        transform=ax.transAxes,
        facecolor="#0a0f18", edgecolor=C["accent"],
        linewidth=0.8, alpha=0.88, zorder=28,
    )
    ax.add_patch(panel)

    x, y = bx + 0.010, by + 0.010

    # Anchor glyph
    ax.text(x, y + 0.088, "\u2693",
            transform=ax.transAxes, fontsize=28, color=C["accent"],
            fontfamily=F_SANS, fontweight="bold",
            va="bottom", ha="left", zorder=30,
            path_effects=_outline_sm)

    # OCEAN DATUM  (two-toned, same line)
    ax.text(x + 0.044, y + 0.106, "OCEAN",
            transform=ax.transAxes, fontsize=17, color=C["accent"],
            fontfamily=F_SERIF, fontweight="bold",
            va="center", ha="left", zorder=30,
            path_effects=_outline_sm)
    ax.text(x + 0.044 + 0.062, y + 0.106, "DATUM",
            transform=ax.transAxes, fontsize=17, color=C["text_white"],
            fontfamily=F_SERIF, fontweight="bold",
            va="center", ha="left", zorder=30,
            path_effects=_outline_sm)

    # Intelligence sub-label
    ax.text(x + 0.044, y + 0.082, "Intelligence",
            transform=ax.transAxes, fontsize=9, color=C["text_dim"],
            fontfamily=F_SERIF, style="italic",
            va="center", ha="left", zorder=30,
            path_effects=_outline_sm)

    # Thin rule
    ax.plot([x, x + 0.205], [y + 0.060, y + 0.060],
            transform=ax.transAxes, color=C["accent"],
            lw=0.5, alpha=0.55, zorder=29)

    # Tagline
    ax.text(x, y + 0.046, "Charting Clarity from Complexity",
            transform=ax.transAxes, fontsize=8.5, color=C["text_dim"],
            fontfamily=F_SERIF, style="italic",
            va="center", ha="left", zorder=30,
            path_effects=_outline_sm)

    # Data credits
    ax.text(x, y + 0.026,
            "Data: USACE ERTM  ·  Blue Water Shipping  ·  Natural Earth",
            transform=ax.transAxes, fontsize=6.2, color=C["text_dim"],
            fontfamily=F_SANS,
            va="center", ha="left", zorder=30)
    ax.text(x, y + 0.010,
            "CRS: WGS84 / EPSG:4326  ·  © 2026 OceanDatum Intelligence. All rights reserved.",
            transform=ax.transAxes, fontsize=6.0, color=C["text_dim"],
            fontfamily=F_SANS,
            va="center", ha="left", zorder=30)


def draw_north_arrow(ax: plt.Axes,
                     x: float = 0.970, y: float = 0.880) -> None:
    """Minimal north arrow, upper-right area."""
    ax.annotate("",
                xy=(x, y + 0.060), xytext=(x, y),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=C["text_white"],
                                lw=1.6, mutation_scale=16),
                zorder=30)
    ax.text(x, y + 0.078, "N",
            transform=ax.transAxes, fontsize=14,
            color=C["text_white"], fontfamily=F_SERIF, fontweight="bold",
            va="bottom", ha="center", zorder=30,
            path_effects=_outline_sm)


def draw_scale_bar(ax: plt.Axes,
                   x: float = 0.958, y: float = 0.060,
                   length_nm: float = 30.0) -> None:
    """Scale bar in nautical miles, lower-right area."""
    lat_mid = (EXTENT_4326["south"] + EXTENT_4326["north"]) / 2
    lon_span = EXTENT_4326["east"] - EXTENT_4326["west"]
    nm_per_deg_lon = 60.0 * np.cos(np.radians(lat_mid))
    length_deg = length_nm / nm_per_deg_lon
    frac = length_deg / lon_span

    x0 = x - frac
    mid = x0 + frac / 2

    for seg, col in [([x0, mid], C["text_white"]), ([mid, x], C["accent"])]:
        ax.plot(seg, [y, y], transform=ax.transAxes,
                lw=6, color=col, solid_capstyle="butt", zorder=30)
    for tick_x in [x0, mid, x]:
        ax.plot([tick_x, tick_x], [y - 0.007, y + 0.007],
                transform=ax.transAxes, lw=1.2, color=C["text_white"], zorder=31)
    for tick_x, lbl in [(x0, "0"), (mid, f"{int(length_nm//2)}"), (x, f"{int(length_nm)}")]:
        ax.text(tick_x, y + 0.015, lbl,
                transform=ax.transAxes, fontsize=7.5, color=C["text_white"],
                fontfamily=F_SANS, va="bottom", ha="center",
                path_effects=_outline_sm, zorder=31)
    ax.text((x0 + x) / 2, y - 0.022, "NAUTICAL MILES",
            transform=ax.transAxes, fontsize=7, color=C["text_dim"],
            fontfamily=F_SANS, fontweight="bold",
            va="top", ha="center", path_effects=_outline_sm, zorder=31)


def draw_legend(ax: plt.Axes) -> None:
    """Expanded legend — positioned in the dead space on the west bank of the river."""
    from matplotlib.patches import Patch

    handles = [
        # ---- Section: Terminal Types ----
        Patch(facecolor="none", edgecolor="none",
              label="TERMINAL TYPES"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=C["grain"],   markeredgecolor="white",
               markeredgewidth=0.7, markersize=14,
               label="Export Grain Elevator"),
        Line2D([0], [0], marker="s", color="none",
               markerfacecolor=C["general"], markeredgecolor="white",
               markeredgewidth=0.7, markersize=13,
               label="General / Bulk Terminal"),
        Line2D([0], [0], marker="D", color="none",
               markerfacecolor=C["liquid"],  markeredgecolor="white",
               markeredgewidth=0.7, markersize=12,
               label="Liquid / Chemical Terminal"),
        Line2D([0], [0], marker="^", color="none",
               markerfacecolor=C["anchorage"], markeredgecolor="white",
               markeredgewidth=0.7, markersize=13,
               label="Anchorage / Navigation Buoy"),
        # ---- Spacer ----
        Line2D([0], [0], color="none", label=" "),
        # ---- Section: Waterway & Reference ----
        Patch(facecolor="none", edgecolor="none",
              label="WATERWAY & REFERENCE"),
        Line2D([0], [0], color=C["river_hl"], lw=4.5,
               label="Mississippi River  (USACE)"),
        Line2D([0], [0], color=C["text_dim"], lw=1.2,
               marker="|", markersize=11, markeredgewidth=2.0,
               label="AHP Mile Marker"),
        # ---- Spacer ----
        Line2D([0], [0], color="none", label=" "),
        # ---- Notes ----
        Patch(facecolor="none", edgecolor="none",
              label="NOTES"),
        Line2D([0], [0], color="none",
               label="MM = Statute Miles Above"),
        Line2D([0], [0], color="none",
               label="       Head of Passes (AHP)"),
        Line2D([0], [0], color="none",
               label="Data: USACE ERTM · BWS Port Maps"),
        Line2D([0], [0], color="none",
               label="CRS: WGS 84 / EPSG:4326"),
    ]

    leg = ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.028, 0.640),   # west bank dead space — middle-left
        frameon=True, framealpha=0.92,
        facecolor="#0a0f18", edgecolor=C["accent"],
        labelcolor=C["text_white"],
        fontsize=12, borderpad=1.4,
        labelspacing=0.72,
        handlelength=2.2,
        handleheight=1.2,
        title="MAP LEGEND",
        title_fontsize=14.0,
    )
    leg.get_title().set_color(C["accent"])
    leg.get_title().set_fontfamily(F_SERIF)
    leg.get_title().set_fontweight("bold")

    # Style individual entries
    for text in leg.get_texts():
        label = text.get_text()
        if label in ("TERMINAL TYPES", "WATERWAY & REFERENCE", "NOTES"):
            text.set_color(C["accent"])
            text.set_fontfamily(F_SERIF)
            text.set_fontweight("bold")
            text.set_fontsize(12.5)
        else:
            text.set_fontfamily(F_SANS)


def draw_title_block(ax: plt.Axes) -> None:
    ax.text(0.500, 0.978,
            "LOWER MISSISSIPPI RIVER",
            transform=ax.transAxes, fontsize=34, color=C["accent"],
            fontfamily=F_SERIF, fontweight="bold",
            va="top", ha="center", zorder=30,
            path_effects=_outline_lg)
    ax.text(0.500, 0.950,
            "BULK TERMINAL & NAVIGATION GUIDE  ·  HEAD OF PASSES TO PORT ALLEN",
            transform=ax.transAxes, fontsize=13.5, color=C["text_white"],
            fontfamily=F_SANS,
            va="top", ha="center", zorder=30,
            path_effects=_outline_md)
    ax.text(0.500, 0.930,
            "Mile Points AHP (Above Head of Passes)  ·  New Orleans District, U.S. Army Corps of Engineers",
            transform=ax.transAxes, fontsize=8.5, color=C["text_dim"],
            fontfamily=F_SANS, style="italic",
            va="top", ha="center", zorder=30,
            path_effects=_outline_sm)


def draw_inset_map(fig: plt.Figure,
                   world: gpd.GeoDataFrame) -> None:
    """Compact locator thumbnail — upper-right corner, unobtrusive."""
    if world.empty:
        return

    # Small axes: 11% wide × 9% tall, anchored upper-right with margin
    inset_ax = fig.add_axes([0.872, 0.860, 0.112, 0.095])
    inset_ax.set_facecolor("#0a0e18")
    inset_ax.set_xlim(-98, -78)
    inset_ax.set_ylim(24, 36)

    world.plot(ax=inset_ax, facecolor="#1c2540", edgecolor="#2e3f60", lw=0.3)

    # Small accent dot marking the map area
    cx = (EXTENT_4326["west"] + EXTENT_4326["east"]) / 2
    cy = (EXTENT_4326["south"] + EXTENT_4326["north"]) / 2
    inset_ax.scatter([cx], [cy], s=28, c=C["accent"],
                     marker="o", zorder=5, linewidths=0)
    # Crosshair lines
    inset_ax.axvline(cx, color=C["accent"], lw=0.5, alpha=0.5, zorder=4)
    inset_ax.axhline(cy, color=C["accent"], lw=0.5, alpha=0.5, zorder=4)

    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    for spine in inset_ax.spines.values():
        spine.set_edgecolor(C["accent"])
        spine.set_linewidth(0.6)
    inset_ax.set_title("LOCATION", fontsize=5.5, color=C["text_dim"],
                        fontfamily=F_SANS, pad=2)


# ---------------------------------------------------------------------------
# MILE MARKERS
# ---------------------------------------------------------------------------

MILE_MARKS = list(range(20, 225, 10))   # every 10 AHP miles


def draw_mile_markers(ax: plt.Axes,
                      miss_ww_3857: gpd.GeoDataFrame) -> None:
    """Draw AHP mile marker ticks + labels along the river."""
    if miss_ww_3857.empty:
        return

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        return

    # Build (mile, x_3857, y_3857) from segment midpoints
    mile_pts: list[tuple[float, float, float]] = []
    for _, row in miss_ww_3857.iterrows():
        try:
            amile = float(row.get("AMILE") or 0)
            bmile = float(row.get("BMILE") or 0)
        except (TypeError, ValueError):
            continue
        if str(row.get("LINKTYPE", "")).upper() == "LOCK":
            continue
        geom = row.geometry
        if geom is None:
            continue
        try:
            mid = geom.interpolate(0.5, normalized=True)
            mile_pts.append(((amile + bmile) / 2, mid.x, mid.y))
        except Exception:
            continue

    if not mile_pts:
        return

    miles_arr  = np.array([p[0] for p in mile_pts])
    coords_arr = np.array([(p[1], p[2]) for p in mile_pts])

    for target in MILE_MARKS:
        idx = int(np.argmin(np.abs(miles_arr - target)))
        px, py = coords_arr[idx]

        # Check inside 3857 extent
        if not (EXTENT_3857["xmin"] < px < EXTENT_3857["xmax"] and
                EXTENT_3857["ymin"] < py < EXTENT_3857["ymax"]):
            continue

        ax.scatter(px, py, s=22, c=C["text_dim"], marker="|",
                   zorder=14, linewidths=0.9, alpha=0.65)

        # Prominent labels every 20 miles
        if target % 20 == 0:
            ax.text(px + 3000, py + 3000, f"MM {target}",
                    fontsize=5.5, color=C["text_dim"],
                    fontfamily=F_MONO, fontweight="bold",
                    ha="left", va="bottom", zorder=14,
                    path_effects=_outline_sm)


# ---------------------------------------------------------------------------
# MAIN BUILD FUNCTION
# ---------------------------------------------------------------------------

def build_map(draft: bool = False,
              zoom: int = 12,
              skip_pdf: bool = False) -> None:

    print("\n=== Lower Mississippi River Map — OceanDatum.ai ===\n")

    # ---- 1. Load data ----
    print("[1/5] Loading data...")
    terminals_4326 = load_bws_terminals()
    miss_ww_4326   = load_waterways_miss()
    ne_land        = load_ne_land()
    print(f"  {len(terminals_4326)} BWS terminals (Mississippi River)")
    print(f"  {len(miss_ww_4326)} USACE waterway segments")
    print(f"  {len(ne_land)} Natural Earth land polygons")

    # ---- 2. Save filtered GIS layers ----
    print("\n[2/5] Saving filtered GIS layers...")
    save_layers(terminals_4326, miss_ww_4326)
    print(f"  Land polygons loaded: {len(ne_land)}")

    # ---- 3. Project to EPSG:3857 ----
    print("\n[3/5] Projecting to EPSG:3857...")
    terminals_3857 = terminals_4326.to_crs("EPSG:3857")
    miss_ww_3857   = miss_ww_4326.to_crs("EPSG:3857")

    # ---- 4. Build figure ----
    print("\n[4/5] Building map...")
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor(C["fig_bg"])
    ax.set_facecolor(C["map_bg"])

    ax.set_xlim(EXTENT_3857["xmin"], EXTENT_3857["xmax"])
    ax.set_ylim(EXTENT_3857["ymin"], EXTENT_3857["ymax"])

    # ---- Land background (Natural Earth polygons) ----
    print("  Drawing land background...")
    if not ne_land.empty:
        ne_land_3857 = ne_land.to_crs("EPSG:3857")
        ne_land_3857.plot(ax=ax, color=C["land_fill"],
                          edgecolor=C["land_edge"], linewidth=0.6, zorder=2)

    # ---- Tile basemap — CartoDB DarkMatter for geographic context ----
    try:
        import contextily as ctx
        print(f"  Adding CartoDB.DarkMatter basemap (zoom={zoom})...")
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.DarkMatter,
            zoom=zoom,
            crs="EPSG:3857",
            reset_extent=False,
            attribution=False,
        )
        for img_art in ax.get_images():
            img_art.set_alpha(0.55)
        print("  Basemap OK.")
    except Exception as exc:
        print(f"  Basemap skipped ({exc}).")

    # ---- River body POLYGON (wide fill — the primary river visual) ----
    print("  Drawing river body polygon...")
    if not miss_ww_4326.empty:
        _buf = miss_ww_4326.copy()
        _buf.geometry = miss_ww_4326.geometry.buffer(0.024)  # ~2.4 km each side
        _buf_3857 = _buf.to_crs("EPSG:3857")
        _river_merged = gpd.GeoDataFrame(
            geometry=[unary_union(_buf_3857.geometry)], crs="EPSG:3857")
        _river_merged.plot(ax=ax, color=C["river_fill"], edgecolor="none", alpha=0.97, zorder=3)
        # Slightly brighter inner band — no edge, clean flat body
        _buf2 = miss_ww_4326.copy()
        _buf2.geometry = miss_ww_4326.geometry.buffer(0.012)
        _buf2_3857 = _buf2.to_crs("EPSG:3857")
        _river2 = gpd.GeoDataFrame(
            geometry=[unary_union(_buf2_3857.geometry)], crs="EPSG:3857")
        _river2.plot(ax=ax, color=C["river_fill2"], edgecolor="none", alpha=0.55, zorder=3)
        # Narrow bright riverbank line — draws once on unified polygon edge
        _river_merged.plot(ax=ax, facecolor="none",
                           edgecolor=C["river_hl"], linewidth=0.9, alpha=0.55, zorder=4)

    # ---- Coordinate graticule (lat/lon grid lines in 3857 space) ----
    lon_ticks = np.arange(-91.5, -89.0, 0.5)
    lat_ticks = np.arange(29.0, 31.0, 0.5)

    for lon in lon_ticks:
        x_m, _ = to_3857(lon, 29.0)
        ax.axvline(x_m, color=C["grid"], lw=0.35, alpha=0.6, zorder=1)
    for lat in lat_ticks:
        _, y_m = to_3857(-90.0, lat)
        ax.axhline(y_m, color=C["grid"], lw=0.35, alpha=0.6, zorder=1)

    xtick_pos = [to_3857(lon, 29.0)[0] for lon in lon_ticks]
    ytick_pos = [to_3857(-90.0, lat)[1] for lat in lat_ticks]

    ax.set_xticks(xtick_pos)
    ax.set_xticklabels([f"{abs(lon):.1f}°W" for lon in lon_ticks],
                       fontsize=7, color=C["text_dim"], fontfamily=F_SANS)
    ax.set_yticks(ytick_pos)
    ax.set_yticklabels([f"{lat:.1f}°N" for lat in lat_ticks],
                       fontsize=7, color=C["text_dim"], fontfamily=F_SANS)
    for spine in ax.spines.values():
        spine.set_edgecolor(C["frame"])
        spine.set_linewidth(1.2)

    # ---- No centerline glow — clean flat polygon is the river. Navigation chart style. ----

    # ---- Water / geographic labels ----
    print("  Adding geographic labels...")
    for lon, lat, text, fs, rot, ck in WATER_LABELS:
        if not (EXTENT_4326["west"] < lon < EXTENT_4326["east"] and
                EXTENT_4326["south"] < lat < EXTENT_4326["north"]):
            continue
        px, py = to_3857(lon, lat)
        ax.text(px, py, text, fontsize=fs, color=C[ck],
                fontfamily=F_SERIF, style="italic",
                ha="center", va="center", rotation=rot, alpha=0.75, zorder=12,
                path_effects=[pe.withStroke(linewidth=2, foreground=C["map_bg"])])

    for lon, lat, name, fs in CITY_LABELS:
        px, py = to_3857(lon, lat)
        ax.text(px, py, name, fontsize=fs, color=C["text_city"],
                fontfamily=F_SANS, fontweight="bold",
                ha="center", va="center", zorder=13,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=C["fig_bg"])])

    for lon, lat, name, fs, col in REGION_LABELS:
        px, py = to_3857(lon, lat)
        ax.text(px, py, name, fontsize=fs, color=col,
                fontfamily=F_SERIF, fontweight="bold",
                ha="center", va="center", alpha=0.55, zorder=8)

    # ---- Terminals ----
    print("  Rendering terminals...")
    for _, row in terminals_3857.iterrows():
        props = row.to_dict()
        px = row.geometry.x
        py = row.geometry.y
        name = str(props.get("name", ""))
        cat = _classify(props)
        col = C[cat]
        marker, msize, es = MARKER_STYLE[cat]

        # Drop shadow
        ax.scatter(px, py, s=msize * es * 1.6, c="#000000",
                   marker=marker, zorder=15, linewidths=0, alpha=0.5)
        # Main marker
        ax.scatter(px, py, s=msize, c=col,
                   marker=marker, zorder=16,
                   edgecolors="white", linewidths=0.7)

        # Label with leader line — convert 3857 point back to 4326 for degree-based offset
        dlon, dlat, ha, va = LABEL_OFF.get(name, (0.06, 0.04, "left", "bottom"))
        lon_4326, lat_4326 = _3857_to_4326.transform(px, py)
        dm_x, dm_y = deg_offset_to_m(lon_4326, lat_4326, dlon, dlat)
        short = SHORT_LABELS.get(name, name.split(" - ")[0].upper())

        ax.annotate(
            short,
            xy=(px, py),
            xytext=(px + dm_x, py + dm_y),
            fontsize=11, color=col,
            fontfamily=F_SANS, fontweight="bold",
            ha=ha, va=va, zorder=20,
            path_effects=_outline_md,
            arrowprops=dict(
                arrowstyle="-",
                color=col, lw=1.2, alpha=0.80,
                connectionstyle="arc3,rad=0.0",
            ),
            annotation_clip=False,
        )

    # ---- Mile markers ----
    print("  Adding mile markers...")
    draw_mile_markers(ax, miss_ww_3857)

    # ---- Map decoration ----
    draw_title_block(ax)
    draw_brand_lockup(ax)
    draw_north_arrow(ax)
    draw_scale_bar(ax)
    draw_legend(ax)
    # inset locator removed per user feedback

    plt.tight_layout(pad=0.4)

    # ---- 5. Export ----
    print("\n[5/5] Exporting...")

    # Master image — PNG at full DPI (primary deliverable)
    png_dpi = 96 if draft else 300
    suffix = "_draft" if draft else "_master"
    png_out = _REPORTS / f"lower_miss_river_map_oceandatum_v1{suffix}.png"
    fig.savefig(png_out, format="png", dpi=png_dpi,
                bbox_inches="tight", facecolor=C["fig_bg"])
    size_mb = png_out.stat().st_size / 1_048_576
    print(f"  PNG master:  {png_out.name}  ({png_dpi} DPI, {size_mb:.1f} MB)")

    if not skip_pdf:
        pdf_out = _REPORTS / "lower_miss_river_map_oceandatum_v1.pdf"
        fig.savefig(
            pdf_out, format="pdf", dpi=300,
            bbox_inches="tight", facecolor=C["fig_bg"],
            metadata={
                "Title":    "Lower Mississippi River Bulk Terminal & Navigation Guide",
                "Author":   "OceanDatum Intelligence",
                "Subject":  "Lower Mississippi River Navigation & Bulk Terminal Map",
                "Keywords": "Mississippi River, grain elevators, bulk terminals, navigation",
                "Creator":  "OceanDatum geospatial_engine v1.0",
            },
        )
        print(f"  PDF:         {pdf_out.name}")

    print(f"\n  Open master:\n    open '{png_out}'")
    plt.close(fig)
    print("\n  Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Build Lower Mississippi River poster map PDF (OceanDatum.ai)")
    p.add_argument("--draft",    action="store_true",
                   help="Draft mode: PNG only at 96 DPI (fast)")
    p.add_argument("--zoom",     type=int, default=12,
                   help="Basemap tile zoom level (10=draft, 12=print-quality default)")
    p.add_argument("--no-pdf",   action="store_true",
                   help="Skip PDF export (PNG preview only)")
    args = p.parse_args()
    build_map(draft=args.draft, zoom=args.zoom, skip_pdf=args.no_pdf)


if __name__ == "__main__":
    main()
