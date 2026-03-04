# Geospatial Engine — Methodology

**Last Updated:** 2026-03-02
**Owner:** William S. Davis III
**Status:** Operational (21 layers)

---

## Overview

The geospatial engine is the platform's shared spatial computation layer. It provides
canonical implementations of all GIS operations used across toolsets — preventing
duplicate code and ensuring consistent spatial logic throughout the platform.

**Design principle:** Every toolset that needs a distance calculation, spatial join,
or map output imports from here rather than maintaining its own copy.

---

## Module Architecture

```
geospatial_engine/
├── src/
│   ├── spatial_joins.py    ← Distances, radius search, GeoPandas operations
│   ├── layer_catalog.py    ← Registry of 21 GeoJSON layers (Knowledge Bank)
│   ├── layer_manager.py    ← Load/cache GIS files (Shapefile, GeoJSON, GeoPackage)
│   ├── map_builder.py      ← Interactive Folium/Leaflet map generation
│   └── export_utils.py     ← Export to GeoJSON, Shapefile, KML, CSV
├── data/
│   └── projections.json    ← CRS definitions
└── METHODOLOGY.md          ← This file
```

---

## Coordinate Reference System

- **Platform standard:** WGS84 / EPSG:4326 (decimal degrees, lat/lon)
- All layers stored and served in WGS84
- Reprojections for area/buffer calculations use:
  - EPSG:3857 (Web Mercator) — for buffer operations
  - EPSG:5070 (NAD83 / Conus Albers) — for area density calculations

---

## Spatial Operations (spatial_joins.py)

### Haversine Distance

Canonical great-circle distance implementation. All toolsets import from here.

```python
from geospatial_engine.src.spatial_joins import haversine

dist_miles = haversine(lat1, lon1, lat2, lon2)             # miles (default)
dist_km    = haversine(lat1, lon1, lat2, lon2, unit="km")  # kilometers
```

**Formula:** Standard haversine; Earth radius = 3,958.8 miles / 6,371.0 km

### Radius Search

Find all points within N miles of a center location.

```python
from geospatial_engine.src.spatial_joins import radius_search

results = radius_search(
    center_lat=29.95, center_lon=-90.07,
    points=facility_list,
    radius_miles=50,
)
# Returns points sorted by distance_miles (ascending)
```

**Use:** Facility proximity analysis, terminal catchment areas, port-shed mapping.

### Nearest Neighbours

Find the K closest points to a target.

```python
from geospatial_engine.src.spatial_joins import nearest_neighbours

nearest = nearest_neighbours(target_lat, target_lon, points, k=5)
```

### Bounding Box Pre-filter

Compute a lat/lon bounding box before exact haversine for large datasets.

```python
from geospatial_engine.src.spatial_joins import bounding_box

min_lat, min_lon, max_lat, max_lon = bounding_box(lat, lon, radius_miles=100)
# Use to pre-filter: df[(df.lat >= min_lat) & (df.lat <= max_lat) & ...]
```

**Performance:** Reduces candidate set by ~95% before running exact haversine on
datasets with 100k+ facilities.

### GeoPandas Operations (require geopandas + shapely)

| Function | Purpose |
|---|---|
| `points_to_geodf()` | Convert point-dict list → GeoDataFrame |
| `spatial_join_points_to_polygons()` | Assign facilities to states/counties |
| `buffer_points()` | Create buffer polygons around point features |
| `calculate_density()` | Count points per polygon + density per sq mile |

---

## Layer Catalog (layer_catalog.py)

21 registered GeoJSON layers covering the full US bulk supply chain network.

### Facility Layers (11)

| Layer Key | Description | Count |
|---|---|---|
| `facilities_cement` | Cement plants — kilns, grinding, terminals | ~150 |
| `facilities_grain_elevator` | Grain elevators — river, rail, country | ~2,000+ |
| `facilities_steel_mill` | Steel mills — integrated, EAF, rolling | ~68 |
| `facilities_fertilizer` | Fertilizer production and distribution | ~200+ |
| `facilities_chemical` | Chemical manufacturing facilities | ~500+ |
| `facilities_refinery` | Petroleum refineries | ~130 |
| `facilities_coal_terminal` | Coal loading/unloading terminals | ~100 |
| `facilities_aggregate` | Aggregate quarries and distribution | ~300+ |
| `facilities_pipeline_terminal` | Pipeline terminals — tank farms, pump stations | ~200+ |
| `facilities_general_cargo` | General cargo handling facilities | — |
| `seaports_us` | US seaports — Census Schedule D | 99 |
| `national_industrial_facilities` | Combined national facility layer | — |

### Infrastructure Layers (5)

| Layer Key | Description | Source |
|---|---|---|
| `rail_network` | Simplified US rail network (Class I + short line) | NTAD |
| `waterways_major` | Major navigable waterways (USACE) | USACE NWD |
| `pipelines_national` | National pipeline network (all products) | EIA |
| `pipelines_crude` | Crude oil pipelines | EIA |
| `pipelines_hgl` | HGL / NGL / LPG pipelines | EIA |

### Cluster Layers (4)

| Layer Key | Description |
|---|---|
| `clusters_grain` | Grain commodity market clusters |
| `clusters_petroleum` | Petroleum commodity market clusters |
| `clusters_chemical` | Chemical commodity market clusters |
| `clusters_multimodal` | Multimodal transport hub clusters |

### Layer Lookup

```python
from geospatial_engine.src.layer_catalog import get_layer_path, list_layers

# All layers
layers = list_layers()

# Filter by category
infra = list_layers(category="infrastructure")

# Absolute path to a layer file
path = get_layer_path("seaports_us")

# Layer metadata + file size
info = get_layer_info("facilities_grain_elevator")
```

---

## Layer Manager (layer_manager.py)

Loads and caches GIS files in memory across a session.

```python
from geospatial_engine.src.layer_manager import LayerManager

lm = LayerManager()
waterways = lm.load(get_layer_path("waterways_major"), name="waterways")
ports     = lm.load(get_layer_path("seaports_us"),     name="ports")

# Get cached layer
gdf = lm.get("waterways")
print(lm.info("waterways"))  # LayerInfo: crs, bounds, feature_count, columns
```

**Supported formats:** GeoJSON, Shapefile (.shp), GeoPackage (.gpkg), GeoParquet (.parquet)

---

## Map Builder (map_builder.py)

Folium/Leaflet interactive HTML map generation.

```python
from geospatial_engine.src.map_builder import (
    MapConfig, create_map, add_markers, add_polyline,
    add_heatmap, add_choropleth, finalize_map, save_map
)

cfg = MapConfig(center=(29.95, -90.07), zoom=8, title="New Orleans Terminal Study")
m = create_map(cfg)
m = add_markers(m, facilities, cluster=True, layer_name="Terminals", icon_color="blue")
m = finalize_map(m)
save_map(m, "output/terminals.html")
```

### Base Tile Presets

| Key | Description |
|---|---|
| `cartodb_positron` | Clean light basemap (default) |
| `cartodb_dark` | Dark basemap for presentations |
| `openstreetmap` | Standard OSM |
| `esri_satellite` | Esri World Imagery |
| `esri_topo` | Esri World Topo Map |

### Map Center Presets

`us_lower48`, `gulf_coast`, `lower_mississippi`, `houston`, `new_orleans`,
`baton_rouge`, `mobile`, `norfolk`, `memphis`, `tampa`

---

## CLI

```bash
# List all registered layers
report-platform geospatial layers

# Filter by category
report-platform geospatial layers --category facilities
report-platform geospatial layers --category infrastructure

# Layer metadata
report-platform geospatial info seaports_us
report-platform geospatial info facilities_grain_elevator

# Generate interactive map (opens in browser)
report-platform geospatial map \
    --layers "facilities_grain_elevator,waterways_major,rail_network,seaports_us" \
    --output map.html \
    --title "US Grain Supply Chain Network" \
    --center gulf_coast
```

### Map Layer Color Scheme

| Layer type | Rendering | Color |
|---|---|---|
| Point facilities | Clustered markers | Per-commodity color |
| Seaports | Clustered markers | Dark blue / anchor icon |
| Rail network | GeoJson lines | Brown (#8B4513) |
| Waterways | GeoJson lines | Dark blue (#1565C0) |
| Pipelines (national) | GeoJson lines | Amber (#FF6F00) |
| Pipelines (crude) | GeoJson lines | Dark red (#B71C1C) |
| Clusters | GeoJson polygons | Per-commodity color |

---

## Export Utilities (export_utils.py)

```python
from geospatial_engine.src.export_utils import export_geojson, export_csv

# Export GeoDataFrame
export_geojson(gdf, "output/facilities.geojson")
export_csv(gdf, "output/facilities.csv")
```

Supported output formats: GeoJSON, Shapefile (.shp), KML, CSV

---

## Integration with Other Toolsets

| Toolset | Integration Point |
|---|---|
| `site_master_registry` | `geo_enrichment.py` imports `haversine` for nearest-port calc |
| `site_master_registry` | `spatial_matcher.py` wraps haversine for km/meter units |
| `vessel_voyage_analysis` | `grain_matcher.py` uses spatial proximity matching |
| All commodity modules | `layer_catalog` provides GeoJSON paths for map outputs |
| `report_platform CLI` | `geospatial` command group wires all operations to CLI |

---

## Data Sources for Layers

| Layer group | Primary source |
|---|---|
| Facility layers | EPA FRS (4M+ records), USDA SCRS, AIST, company filings |
| Rail network | NTAD National Rail Network / TIGER |
| Waterways | USACE Navigation Data Center |
| Pipelines | EIA Natural Gas / Petroleum Pipeline datasets |
| Seaports | Census Schedule D (port_geo_dictionary.json — 549 codes, 99 geocoded) |
| Clusters | Derived from facility layer spatial clustering |

---

## Adding New Layers

1. Place GeoJSON in `07_KNOWLEDGE_BANK/master_facility_register/geojson/` or
   `data/national_supply_chain/`
2. Register in `layer_catalog.py` — add entry to `LAYER_CATALOG` dict
3. Run `report-platform geospatial layers` to verify it shows as `OK`
4. Add color/style entry in cli.py `_LAYER_COLORS` or `_LINE_COLORS` dicts
