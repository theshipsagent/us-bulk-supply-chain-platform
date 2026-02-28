"""Interactive Folium maps for EPA FRS facility data.

Generates facility distribution maps, heatmaps, and cluster maps
using the geospatial_engine map_builder utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False


# NAICS-to-colour mapping for common industry sectors
_NAICS_COLORS: dict[str, str] = {
    "3273": "red",         # cement and concrete
    "3271": "orange",      # clay and refractory
    "3274": "darkred",     # lime and gypsum
    "2212": "blue",        # natural gas distribution
    "2211": "darkblue",    # electric power (coal plants — fly ash)
    "3311": "gray",        # iron and steel mills (slag)
    "3241": "green",       # petroleum and coal products
    "4247": "purple",      # petroleum wholesalers
}


def _require_folium() -> None:
    if not HAS_FOLIUM:
        raise ImportError("folium is required: pip install folium")


def create_facility_map(
    facilities: list[dict[str, Any]],
    center: tuple[float, float] | None = None,
    zoom: int = 7,
    title: str = "Facility Map",
    color: str = "blue",
    cluster: bool = True,
) -> "folium.Map":
    """Create an interactive map of facilities.

    Parameters
    ----------
    facilities : list[dict]
        Each dict should have lat/latitude, lon/longitude, fac_name,
        and optionally fac_state, fac_city, distance_miles.
    center : tuple, optional
        (lat, lon) for map center. If None, auto-centres on data.
    zoom : int
        Initial zoom level.
    title : str
        Map title.
    color : str
        Marker colour.
    cluster : bool
        Whether to cluster markers.
    """
    _require_folium()

    # Auto-center
    if center is None and facilities:
        lats = [f.get("latitude") or f.get("lat") for f in facilities if f.get("latitude") or f.get("lat")]
        lons = [f.get("longitude") or f.get("lon") for f in facilities if f.get("longitude") or f.get("lon")]
        if lats and lons:
            center = (sum(lats) / len(lats), sum(lons) / len(lons))
        else:
            center = (30.0, -90.0)

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    # Add title
    title_html = f'<h3 style="position:fixed;z-index:9999;top:10px;left:60px;">{title}</h3>'
    m.get_root().html.add_child(folium.Element(title_html))

    target = MarkerCluster(name="Facilities").add_to(m) if cluster else m

    for fac in facilities:
        lat = fac.get("latitude") or fac.get("lat")
        lon = fac.get("longitude") or fac.get("lon")
        if lat is None or lon is None:
            continue

        name = fac.get("fac_name", "Unknown")
        city = fac.get("fac_city", "")
        state = fac.get("fac_state", "")
        dist = fac.get("distance_miles")
        reg_id = fac.get("registry_id", "")

        popup_lines = [f"<b>{name}</b>"]
        if city or state:
            popup_lines.append(f"{city}, {state}")
        if reg_id:
            popup_lines.append(f"Registry ID: {reg_id}")
        if dist is not None:
            popup_lines.append(f"Distance: {dist:.1f} mi")

        popup = folium.Popup("<br>".join(popup_lines), max_width=300)

        # Colour by NAICS if available
        naics = str(fac.get("naics_primary", fac.get("naics_code", "")))
        marker_color = _NAICS_COLORS.get(naics[:4], color)

        folium.Marker(
            location=[float(lat), float(lon)],
            popup=popup,
            tooltip=name,
            icon=folium.Icon(color=marker_color, icon="industry", prefix="fa"),
        ).add_to(target)

    folium.LayerControl().add_to(m)
    return m


def create_heatmap(
    facilities: list[dict[str, Any]],
    center: tuple[float, float] | None = None,
    zoom: int = 6,
    title: str = "Facility Density Heatmap",
    radius: int = 15,
) -> "folium.Map":
    """Create a heatmap showing facility density."""
    _require_folium()

    heat_data = []
    lats, lons = [], []
    for fac in facilities:
        lat = fac.get("latitude") or fac.get("lat")
        lon = fac.get("longitude") or fac.get("lon")
        if lat is not None and lon is not None:
            heat_data.append([float(lat), float(lon)])
            lats.append(float(lat))
            lons.append(float(lon))

    if center is None and lats:
        center = (sum(lats) / len(lats), sum(lons) / len(lons))
    elif center is None:
        center = (30.0, -90.0)

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    title_html = f'<h3 style="position:fixed;z-index:9999;top:10px;left:60px;">{title}</h3>'
    m.get_root().html.add_child(folium.Element(title_html))

    HeatMap(heat_data, radius=radius, blur=10, max_zoom=12).add_to(m)
    return m


def create_radius_map(
    center_lat: float,
    center_lon: float,
    radius_miles: float,
    facilities: list[dict[str, Any]],
    title: str = "Radius Search Results",
) -> "folium.Map":
    """Create a map showing search center, radius circle, and results."""
    _require_folium()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles="CartoDB positron",
    )

    # Add search centre
    folium.Marker(
        location=[center_lat, center_lon],
        popup="Search Center",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)

    # Add radius circle (convert miles to meters)
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_miles * 1_609.34,
        color="red",
        weight=2,
        fill=True,
        fill_opacity=0.05,
        popup=f"{radius_miles} mile radius",
    ).add_to(m)

    # Add facility markers
    cluster = MarkerCluster(name="Facilities").add_to(m)
    for fac in facilities:
        lat = fac.get("latitude") or fac.get("lat")
        lon = fac.get("longitude") or fac.get("lon")
        if lat is None or lon is None:
            continue

        name = fac.get("fac_name", "Unknown")
        dist = fac.get("distance_miles", 0)

        folium.Marker(
            location=[float(lat), float(lon)],
            popup=f"<b>{name}</b><br>Distance: {dist:.1f} mi",
            tooltip=f"{name} ({dist:.1f} mi)",
            icon=folium.Icon(color="blue", icon="industry", prefix="fa"),
        ).add_to(cluster)

    folium.LayerControl().add_to(m)

    title_html = f'<h3 style="position:fixed;z-index:9999;top:10px;left:60px;">{title}</h3>'
    m.get_root().html.add_child(folium.Element(title_html))

    return m


def save_map(m: "folium.Map", output_path: str | Path) -> Path:
    """Save map to HTML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(path))
    return path
