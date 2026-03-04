# Geospatial Engine

Shared GIS utilities for the US Bulk Supply Chain Reporting Platform.

## Overview

The geospatial engine provides spatial operations used across all toolsets:
haversine distance, radius search, nearest-neighbour lookup, spatial joins,
GeoJSON/Shapefile export, and layer management for the Knowledge Bank.

## Modules

| Module | Purpose |
|--------|---------|
| `spatial_joins.py` | Haversine distance, radius search, nearest neighbours, bounding box, GeoPandas spatial joins |
| `layer_manager.py` | Load/cache/transform GIS layers (Shapefile, GeoJSON, GeoPackage, Parquet) |
| `layer_catalog.py` | Registry of all Knowledge Bank GeoJSON layers with CLI integration |
| `export_utils.py` | Export to GeoJSON, Shapefile, KML, CSV |
| `map_builder.py` | Interactive Folium/Leaflet map generation |

## Usage

```python
from geospatial_engine.src.spatial_joins import haversine, radius_search, nearest_neighbours
from geospatial_engine.src.layer_catalog import LAYER_CATALOG, get_layer_path
from geospatial_engine.src.export_utils import export_geojson
```

## Haversine Distance

The canonical haversine implementation lives in `spatial_joins.py`.
All other toolsets import from here rather than maintaining local copies.

```python
from geospatial_engine.src.spatial_joins import haversine

# Distance in miles (default)
d = haversine(29.95, -90.07, 30.45, -91.19)

# Distance in km
d = haversine(29.95, -90.07, 30.45, -91.19, unit="km")
```

## Layer Catalog

20 GeoJSON layers from the Knowledge Bank are registered in `layer_catalog.py`:

```python
from geospatial_engine.src.layer_catalog import LAYER_CATALOG, get_layer_path

# List all layers
for name, meta in LAYER_CATALOG.items():
    print(f"{name}: {meta['description']}")

# Get absolute path to a layer
path = get_layer_path("facilities_cement")
```

## CLI

```bash
report-platform geospatial layers              # List all available GIS layers
report-platform geospatial info <layer-name>    # Show metadata for a layer
report-platform geospatial map --layers cement,rail --output map.html
```

## Data

- `data/projections.json` — coordinate reference system definitions
- Knowledge Bank GeoJSON: `07_KNOWLEDGE_BANK/master_facility_register/`

## Legacy Scripts

Original analysis/map-building scripts (40 files) archived to
`06_ARCHIVE/geospatial_legacy/` for reference.
