"""Interactive map builder using Folium/Leaflet.

Provides a high-level API for building interactive web maps with
standard base layers, markers, popups, and thematic overlays used
across all toolsets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap, MeasureControl
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False


# ---------------------------------------------------------------------------
# Tile layer presets
# ---------------------------------------------------------------------------

TILE_PRESETS: dict[str, dict[str, str]] = {
    "openstreetmap": {
        "tiles": "OpenStreetMap",
    },
    "cartodb_positron": {
        "tiles": "CartoDB positron",
    },
    "cartodb_dark": {
        "tiles": "CartoDB dark_matter",
    },
    "stamen_terrain": {
        "tiles": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
        "attr": "Stadia Maps / Stamen Terrain",
    },
    "esri_satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri World Imagery",
    },
    "esri_topo": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri World Topo Map",
    },
}


# Default map centres for common regions
MAP_CENTERS: dict[str, tuple[float, float]] = {
    "us_lower48": (39.5, -98.35),
    "gulf_coast": (29.5, -90.5),
    "lower_mississippi": (30.0, -90.8),
    "houston": (29.76, -95.37),
    "new_orleans": (29.95, -90.07),
    "baton_rouge": (30.45, -91.19),
    "mobile": (30.69, -88.04),
    "norfolk": (36.85, -76.29),
    "memphis": (35.15, -90.05),
    "tampa": (27.95, -82.46),
}


@dataclass
class MapConfig:
    """Configuration for a map instance."""
    center: tuple[float, float] = (30.0, -90.0)
    zoom: int = 6
    width: str = "100%"
    height: str = "600px"
    base_tile: str = "cartodb_positron"
    title: str = ""


def _require_folium() -> None:
    if not HAS_FOLIUM:
        raise ImportError("folium is required: pip install folium")


def create_map(config: MapConfig | None = None) -> "folium.Map":
    """Create a base Folium map with standard configuration."""
    _require_folium()
    cfg = config or MapConfig()

    tile_args: dict[str, Any] = {}
    preset = TILE_PRESETS.get(cfg.base_tile, {})
    if preset:
        tile_args = preset.copy()

    m = folium.Map(
        location=cfg.center,
        zoom_start=cfg.zoom,
        width=cfg.width,
        height=cfg.height,
        **tile_args,
    )

    # Add layer control for additional tile layers
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("CartoDB positron", name="CartoDB Light").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark").add_to(m)

    # Add measurement tool
    MeasureControl(position="topleft").add_to(m)

    return m


def add_markers(
    m: "folium.Map",
    points: list[dict[str, Any]],
    cluster: bool = True,
    layer_name: str = "Markers",
    icon_color: str = "blue",
    icon: str = "info-sign",
) -> "folium.Map":
    """Add point markers to a map.

    Each point dict should have keys: lat, lon, name, and optionally popup, tooltip.
    """
    _require_folium()

    fg = folium.FeatureGroup(name=layer_name)
    target = MarkerCluster().add_to(fg) if cluster else fg

    for pt in points:
        lat = pt.get("lat") or pt.get("latitude")
        lon = pt.get("lon") or pt.get("longitude") or pt.get("lng")
        if lat is None or lon is None:
            continue

        popup_html = pt.get("popup", pt.get("name", ""))
        tooltip_text = pt.get("tooltip", pt.get("name", ""))

        folium.Marker(
            location=[float(lat), float(lon)],
            popup=folium.Popup(str(popup_html), max_width=300),
            tooltip=str(tooltip_text),
            icon=folium.Icon(color=icon_color, icon=icon),
        ).add_to(target)

    fg.add_to(m)
    return m


def add_heatmap(
    m: "folium.Map",
    points: list[tuple[float, float]],
    layer_name: str = "Heatmap",
    radius: int = 15,
    blur: int = 10,
) -> "folium.Map":
    """Add a heatmap layer from (lat, lon) tuples."""
    _require_folium()
    heat_data = [[float(lat), float(lon)] for lat, lon in points if lat and lon]
    fg = folium.FeatureGroup(name=layer_name)
    HeatMap(heat_data, radius=radius, blur=blur).add_to(fg)
    fg.add_to(m)
    return m


def add_choropleth(
    m: "folium.Map",
    geo_data: str | dict,
    data: Any,
    columns: list[str],
    key_on: str,
    layer_name: str = "Choropleth",
    fill_color: str = "YlOrRd",
    legend_name: str = "",
) -> "folium.Map":
    """Add a choropleth layer to the map."""
    _require_folium()
    folium.Choropleth(
        geo_data=geo_data,
        data=data,
        columns=columns,
        key_on=key_on,
        fill_color=fill_color,
        fill_opacity=0.6,
        line_opacity=0.3,
        legend_name=legend_name,
        name=layer_name,
    ).add_to(m)
    return m


def add_polyline(
    m: "folium.Map",
    coords: list[tuple[float, float]],
    color: str = "blue",
    weight: int = 3,
    layer_name: str = "Route",
    tooltip: str = "",
) -> "folium.Map":
    """Add a polyline (route) to the map."""
    _require_folium()
    fg = folium.FeatureGroup(name=layer_name)
    folium.PolyLine(
        locations=coords,
        color=color,
        weight=weight,
        tooltip=tooltip,
    ).add_to(fg)
    fg.add_to(m)
    return m


def finalize_map(m: "folium.Map") -> "folium.Map":
    """Add layer control and finalize the map for display."""
    _require_folium()
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def save_map(m: "folium.Map", output_path: str | Path) -> Path:
    """Save map to an HTML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(path))
    return path
