"""Interactive Folium map builder for the Site Master Registry.

Generates commodity-coded, layered maps with clustering.
Color scheme: steel=gray, aluminum=lightblue, copper=orange,
cement=red, petroleum=green, chemicals=purple, grain=beige,
concrete=darkred, nonferrous_metals=cadetblue.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

from .query import SiteRegistryQuery

logger = logging.getLogger(__name__)

# Commodity sector → marker color
SECTOR_COLORS: dict[str, str] = {
    "steel": "gray",
    "aluminum": "lightblue",
    "copper": "orange",
    "cement": "red",
    "petroleum": "green",
    "chemicals": "purple",
    "grain": "beige",
    "concrete": "darkred",
    "nonferrous_metals": "cadetblue",
    "aggregates": "lightgreen",
    "industrial": "blue",
}

# Sector → Folium icon
SECTOR_ICONS: dict[str, str] = {
    "steel": "industry",
    "aluminum": "industry",
    "copper": "industry",
    "cement": "industry",
    "petroleum": "tint",
    "chemicals": "flask",
    "grain": "leaf",
    "concrete": "building",
}

US_CENTER = (39.5, -98.35)


def _require_folium():
    if not HAS_FOLIUM:
        raise ImportError("folium is required: pip install folium")


def build_registry_map(
    query: SiteRegistryQuery,
    output_path: str,
    sectors: Optional[list[str]] = None,
    min_sources: int = 0,
    title: str = "US Industrial Site Master Registry",
) -> Path:
    """Build interactive Folium map with commodity-coded layers.

    Each sector gets its own clustered layer that can be toggled
    in the layer control panel.
    """
    _require_folium()

    sites = query.all_sites_for_map(sectors=sectors, min_sources=min_sources)
    logger.info(f"Building map with {len(sites)} sites...")

    # Create base map
    m = folium.Map(
        location=US_CENTER,
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # Group sites by sector
    by_sector: dict[str, list[dict]] = {}
    for site in sites:
        sector = site.get("commodity_sectors") or "industrial"
        by_sector.setdefault(sector, []).append(site)

    # Create a cluster layer per sector
    for sector in sorted(by_sector.keys()):
        sector_sites = by_sector[sector]
        color = SECTOR_COLORS.get(sector, "blue")
        icon_name = SECTOR_ICONS.get(sector, "info-sign")

        cluster = MarkerCluster(name=f"{sector.title()} ({len(sector_sites)})")

        for site in sector_sites:
            lat = site.get("latitude")
            lon = site.get("longitude")
            if lat is None or lon is None:
                continue

            # Build popup HTML
            popup_html = _build_popup(site)

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=site.get("canonical_name", ""),
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
            ).add_to(cluster)

        cluster.add_to(m)

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Add title
    title_html = f"""
    <div style="position:fixed;top:10px;left:60px;z-index:1000;
         background:white;padding:10px 20px;border-radius:5px;
         box-shadow:0 2px 6px rgba(0,0,0,0.3);font-family:Arial;">
        <b>{title}</b><br>
        <small>{len(sites):,} sites across {len(by_sector)} sectors</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Save
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(path))
    logger.info(f"Map saved to {path} ({len(sites):,} sites)")
    return path


def _build_popup(site: dict[str, Any]) -> str:
    """Build HTML popup content for a site marker."""
    name = site.get("canonical_name", "Unknown")
    city = site.get("city", "")
    state = site.get("state", "")
    sector = site.get("commodity_sectors", "")
    parent = site.get("parent_company", "")
    sources = site.get("source_count", 0)

    flags = []
    if site.get("rail_served"):
        flags.append("🚂 Rail")
    if site.get("water_access"):
        flags.append("🚢 Water")

    lines = [
        f"<b>{name}</b>",
        f"{city}, {state}" if city else state,
    ]
    if sector:
        lines.append(f"Sector: {sector}")
    if parent:
        lines.append(f"Parent: {parent}")
    if flags:
        lines.append(" | ".join(flags))
    lines.append(f"Sources: {sources}")

    return "<br>".join(lines)
