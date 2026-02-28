# Geospatial Data Resources

## Port Nickel GeoJSON Parcel Data

**Location:** `G:\My Drive\LLM\p_nick_map_export\`

### Available Parish Data Files

| Parish | Filename | Size (MB) | Features |
|--------|----------|-----------|----------|
| Ascension | ascension_parcels.geojson | 4.8 | Parcel boundaries, ownership |
| Iberville | iberville_parcels.geojson | 4.8 | Parcel boundaries, ownership |
| Jefferson | jefferson_parcels.geojson | 4.1 | Parcel boundaries, ownership |
| Plaquemines | plaquemines_parcels.geojson | 4.0 | **AMAX SITE LOCATION** |
| Saint Bernard | saint_bernard_parcels.geojson | 4.1 | Parcel boundaries, ownership |
| Saint Charles | saint_charles_parcels.geojson | 7.4 | Parcel boundaries, ownership |
| Saint James | saint_james_parcels.geojson | 4.3 | Parcel boundaries, ownership |
| Saint John | saint_john_parcels.geojson | 4.0 | Parcel boundaries, ownership |

### Combined Dataset
- **combined_all_parcels.geojson** (40.1 MB)
  - All 8 parishes merged
  - Comprehensive regional dataset

## Usage for Pipeline Analysis

### AMAX Site Coordinate Determination
1. Query `plaquemines_parcels.geojson` for AMAX Port Nickel Terminal properties
2. Extract precise coordinates for proximity analysis
3. Establish 10-mile radius for pipeline identification

### Pipeline Proximity Mapping
1. Use combined dataset to establish regional context
2. Overlay with Louisiana ArcGIS pipeline feature services
3. Calculate distances from AMAX site to identified pipelines
4. Identify potential rights-of-way and interconnection points

### River Mile Context
- AMAX site: ~80 AHP (Above Head of Passes)
- Use parcel data to confirm exact river frontage
- Document West Bank vs East Bank pipeline access

## Data Integration Strategy

### With Louisiana State GIS
- Cross-reference with Louisiana Natural Gas Pipelines feature service
- Overlay with Louisiana Ethylene Pipelines feature service
- Validate pipeline routes against parcel data

### With Federal Data
- Match FERC pipeline route data to parcel locations
- Identify pipeline rights-of-way crossing analysis area
- Document interconnection facilities

## Coordinate Reference System
- Assumed: WGS84 (EPSG:4326) - standard for GeoJSON
- Verify CRS in file metadata
- Ensure compatibility with ArcGIS web services

**Last Updated:** 2026-02-04
