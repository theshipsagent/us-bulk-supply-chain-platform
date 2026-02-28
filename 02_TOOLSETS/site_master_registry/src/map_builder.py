"""Interactive Leaflet map builder for the Site Master Registry.

Generates a standalone HTML file with commodity-coded, toggleable
GeoJSON layers rendered client-side for performance at 11K+ sites.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .query import SiteRegistryQuery

logger = logging.getLogger(__name__)

# Commodity sector → hex color
SECTOR_COLORS: dict[str, str] = {
    "steel": "#808080",
    "aluminum": "#4682B4",
    "copper": "#FF8C00",
    "cement": "#DC143C",
    "petroleum": "#228B22",
    "chemicals": "#8B008B",
    "grain": "#DAA520",
    "concrete": "#8B0000",
    "nonferrous_metals": "#5F9EA0",
    "aggregates": "#90EE90",
    "industrial": "#4169E1",
}

US_CENTER = [39.5, -98.35]


def _sites_to_geojson(sites: list[dict]) -> dict:
    """Convert site dicts to a GeoJSON FeatureCollection."""
    features = []
    for site in sites:
        lat = site.get("latitude")
        lon = site.get("longitude")
        if lat is None or lon is None:
            continue
        props = {
            "n": site.get("canonical_name", ""),
            "ci": site.get("city", ""),
            "st": site.get("state", ""),
            "se": site.get("commodity_sectors", ""),
            "pa": site.get("parent_company", ""),
            "sc": site.get("source_count", 0),
            "r": 1 if site.get("rail_served") else 0,
            "w": 1 if site.get("water_access") else 0,
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def build_registry_map(
    query: SiteRegistryQuery,
    output_path: str,
    sectors: Optional[list[str]] = None,
    min_sources: int = 0,
    title: str = "US Industrial Site Master Registry",
) -> Path:
    """Build interactive Leaflet map with commodity-coded GeoJSON layers."""
    sites = query.all_sites_for_map(sectors=sectors, min_sources=min_sources)
    logger.info(f"Building map with {len(sites)} sites...")

    # Group by sector
    by_sector: dict[str, list[dict]] = {}
    for site in sites:
        sector = site.get("commodity_sectors") or "industrial"
        by_sector.setdefault(sector, []).append(site)

    # Build per-sector GeoJSON + JS config
    sector_data_blocks = []
    layer_js_lines = []
    overlay_entries = []

    for sector in sorted(by_sector.keys()):
        sector_sites = by_sector[sector]
        color = SECTOR_COLORS.get(sector, "#4169E1")
        geojson = _sites_to_geojson(sector_sites)
        var_name = f"data_{sector.replace(' ', '_')}"
        label = f"{sector.title()} ({len(sector_sites)})"

        sector_data_blocks.append(f"var {var_name} = {json.dumps(geojson, separators=(',', ':'))};")

        layer_js_lines.append(f"""
var layer_{var_name} = L.geoJSON({var_name}, {{
  pointToLayer: function(f, ll) {{
    var r = Math.min(4 + f.properties.sc * 0.5, 12);
    return L.circleMarker(ll, {{
      radius: r, fillColor: '{color}', color: '{color}',
      weight: 1, opacity: 0.8, fillOpacity: 0.6
    }});
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    var h = '<b>' + p.n + '</b>';
    if (p.ci) h += '<br>' + p.ci + ', ' + p.st;
    else if (p.st) h += '<br>' + p.st;
    if (p.se) h += '<br>Sector: ' + p.se;
    if (p.pa) h += '<br>Parent: ' + p.pa;
    var fl = [];
    if (p.r) fl.push('Rail');
    if (p.w) fl.push('Water');
    if (fl.length) h += '<br>Logistics: ' + fl.join(' | ');
    h += '<br>Sources: ' + p.sc;
    layer.bindPopup(h, {{maxWidth: 300}});
    layer.bindTooltip(p.n);
  }}
}}).addTo(map);
""")
        overlay_entries.append(f'  "{label}": layer_{var_name}')

    sector_data_js = "\n".join(sector_data_blocks)
    layers_js = "\n".join(layer_js_lines)
    overlays_js = "{\n" + ",\n".join(overlay_entries) + "\n}"

    # Legend HTML
    legend_rows = "".join(
        f'<div><span class="dot" style="background:{SECTOR_COLORS.get(s, "#4169E1")}"></span>'
        f'{s.title()} ({len(sl)})</div>'
        for s, sl in sorted(by_sector.items())
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body {{ margin:0; padding:0; height:100%; }}
  #map {{ width:100%; height:100%; }}
  .info-box {{
    position:fixed; top:10px; left:55px; z-index:1000;
    background:white; padding:14px 20px; border-radius:6px;
    box-shadow:0 2px 8px rgba(0,0,0,0.3); font-family:Arial,sans-serif;
    font-size:13px; line-height:1.7; max-width:260px;
  }}
  .info-box b {{ font-size:15px; }}
  .info-box hr {{ margin:6px 0; border:0; border-top:1px solid #ddd; }}
  .dot {{
    width:10px; height:10px; display:inline-block;
    border-radius:50%; margin-right:6px; vertical-align:middle;
  }}
</style>
</head>
<body>
<div id="map"></div>
<div class="info-box">
  <b>{title}</b><br>
  <small>{len(sites):,} sites across {len(by_sector)} sectors</small>
  <hr>
  {legend_rows}
</div>
<script>
var map = L.map('map').setView({US_CENTER}, 5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}@2x.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}}).addTo(map);

{sector_data_js}

{layers_js}

L.control.layers(null, {overlays_js}, {{collapsed: false}}).addTo(map);
</script>
</body>
</html>"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
    logger.info(f"Map saved to {path} ({len(sites):,} sites)")
    return path
