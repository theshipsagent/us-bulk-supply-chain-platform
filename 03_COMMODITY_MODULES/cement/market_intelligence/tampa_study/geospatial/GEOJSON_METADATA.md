# Cement Market GeoJSON Layer Metadata

## Overview
This directory contains GeoJSON files for the Florida/US cement market analysis project for SESCO Cement Corp.

**Created:** December 2025
**Projection:** EPSG:4326 (WGS84)

---

## Layer Inventory

### Infrastructure Layers

| File | Features | Size | Description | Source |
|------|----------|------|-------------|--------|
| `north_american_cement_plants.geojson` | 158 | 72.8KB | Cement plants in US (100), Canada (20), Mexico (38) | GEM Tracker July 2025 |
| `us_cement_import_ports_weighted.geojson` | 24 | 9.3KB | US ports with cement import volumes (bubble size = volume) | Panjiva 2023-2025 |
| `class1_rail_part1.geojson` | 2,000 | 2.0MB | Class I Railroad network segments (BNSF, UP, CSX, NS, CN, CPKC) | BTS NTAD 2025 |
| `us_marine_highways.geojson` | 35 | 1.9MB | Marine highway corridors (navigable waterways) | BTS NTAD 2025 |

### Customer/Market Layers (NEW - Dec 2025)

| File | Features | Size | Description | Source |
|------|----------|------|-------------|--------|
| `florida_readymix_plants.geojson` | 894 | ~350KB | Florida ready-mix concrete plants (NAICS 327320) | EPA ECHO Dec 2025 |
| `gulf_coast_readymix_plants.geojson` | 1,694 | ~650KB | Gulf Coast ready-mix plants (FL, GA, AL, MS, LA, SC) | EPA ECHO Dec 2025 |

### Regional Layers (Florida Focus)

| File | Features | Size | Description |
|------|----------|------|-------------|
| `cement_plants_florida_gulf.geojson` | 13 | 7.7KB | Florida & Gulf Coast cement plants |
| `import_terminals_florida.geojson` | 6 | 5.4KB | Florida cement import terminals |
| `florida_counties_demand.geojson` | 67 | 14.1KB | Florida counties with demand indicators |
| `port_redwing_trucking_radius.geojson` | 3 | 4.3KB | 1hr, 3hr, 5hr trucking radii from Port Redwing |

### Trade Flow Layers

| File | Features | Size | Description |
|------|----------|------|-------------|
| `caribbean_markets.geojson` | 12 | 13.5KB | Caribbean cement export markets |
| `shipping_routes.geojson` | 8 | 7.8KB | Major cement shipping routes |
| `import_origins.geojson` | 8 | 6.3KB | Cement import origin countries |
| `trade_flows_weighted.geojson` | 10 | 7.8KB | Weighted trade flow arrows |
| `global_trade_flows_detailed.geojson` | 15 | 12.2KB | Global cement trade flows |
| `global_cement_producers.geojson` | 8 | 5.9KB | Major global cement exporters |

### Reference Layers

| File | Features | Size | Description |
|------|----------|------|-------------|
| `us_states_cement.geojson` | 50 | 8.0KB | US states with cement production capacity |
| `us_cement_plants_national.geojson` | 92 | 11.8KB | US-only cement plants |
| `us_ports_cement_imports.geojson` | 18 | 5.6KB | US cement import ports (legacy) |

---

## Data Sources

### Primary Sources
- **Global Energy Monitor (GEM)** - Global Cement and Concrete Tracker July 2025
- **Panjiva Trade Intelligence** - HS 2523 cement import manifests 2023-2025
- **BTS NTAD** - National Transportation Atlas Database (Rail, Marine Highways)
- **USGS** - Mineral Commodity Summaries 2025
- **EPA ECHO** - Enforcement and Compliance History Online (NAICS 327320 Ready-Mix Concrete)

### API Endpoints Used

**BTS Rail Network:**
```
https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0
```

**BTS Marine Highways:**
```
https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Marine_Highways/FeatureServer/0
```

**EPA ECHO Facility Search:**
```
https://echodata.epa.gov/echo/echo_rest_services.get_facility_info?p_st=FL&p_sic=3273&qcolumns=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30
```

---

## ArcGIS Online Layer IDs (Published)

The following layers have been published to ArcGIS Online:

| Layer Name | ArcGIS Item ID | URL |
|------------|----------------|-----|
| **North American Cement Plants** | `353a095f807d475e8a415c9d21e0be4f` | [View](https://www.arcgis.com/home/item.html?id=353a095f807d475e8a415c9d21e0be4f) |
| **US Cement Import Ports (Weighted)** | `1ee57142d20a4779a58e3abffe3d1c6e` | [View](https://www.arcgis.com/home/item.html?id=1ee57142d20a4779a58e3abffe3d1c6e) |
| **Class I Rail Network** | `cab0b48ec7224fd6b1e186db7f1de695` | [View](https://www.arcgis.com/home/item.html?id=cab0b48ec7224fd6b1e186db7f1de695) |
| **US Marine Highways** | `3f760be450b246e99dc1718e8d9284f0` | [View](https://www.arcgis.com/home/item.html?id=3f760be450b246e99dc1718e8d9284f0) |
| Port Redwing Trucking Radius | `03385e6b65524da2a0826f0534193f0d` | [View](https://www.arcgis.com/home/item.html?id=03385e6b65524da2a0826f0534193f0d) |
| **Florida Ready-Mix Plants** | `e8f87ec92b8044dd94104bf7f1b7faf4` | [View](https://www.arcgis.com/home/item.html?id=e8f87ec92b8044dd94104bf7f1b7faf4) |
| **Gulf Coast Ready-Mix Plants** | `704a24cdd7954790bfd696a21adec0eb` | [View](https://www.arcgis.com/home/item.html?id=704a24cdd7954790bfd696a21adec0eb) |

### Data URLs (for embedding)
```
https://www.arcgis.com/sharing/rest/content/items/353a095f807d475e8a415c9d21e0be4f/data
https://www.arcgis.com/sharing/rest/content/items/1ee57142d20a4779a58e3abffe3d1c6e/data
https://www.arcgis.com/sharing/rest/content/items/cab0b48ec7224fd6b1e186db7f1de695/data
https://www.arcgis.com/sharing/rest/content/items/3f760be450b246e99dc1718e8d9284f0/data
https://www.arcgis.com/sharing/rest/content/items/e8f87ec92b8044dd94104bf7f1b7faf4/data
https://www.arcgis.com/sharing/rest/content/items/704a24cdd7954790bfd696a21adec0eb/data
```

---

## Field Descriptions

### north_american_cement_plants.geojson
| Field | Type | Description |
|-------|------|-------------|
| `plant_name` | String | Name of the cement plant |
| `owner` | String | Parent company owner |
| `country` | String | Country (United States, Canada, Mexico) |
| `state` | String | State/Province |
| `capacity_mtpa` | Float | Annual capacity in million tons |
| `status` | String | Operating status |
| `latitude` | Float | Latitude coordinate |
| `longitude` | Float | Longitude coordinate |

### us_cement_import_ports_weighted.geojson
| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Port name and location |
| `import_volume_mt` | Integer | Total cement imports (metric tons) |
| `shipments` | Integer | Number of shipments |
| `volume_label` | String | Human-readable volume (e.g., "3.39M MT") |
| `bubble_size` | Float | Calculated bubble size for visualization |

### class1_rail_part1.geojson
| Field | Type | Description |
|-------|------|-------------|
| `RROWNER1` | String | Railroad owner (BNSF, UP, CSX, NS, CN, CPKC) |
| `COUNTRY` | String | Country |
| `STATEAB` | String | State abbreviation |
| `MILES` | Float | Segment length in miles |
| `TRACKS` | Integer | Number of tracks |

### florida_readymix_plants.geojson / gulf_coast_readymix_plants.geojson
| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Facility name (from EPA ECHO) |
| `address` | String | Street address |
| `city` | String | City name |
| `state` | String | State abbreviation |
| `zip` | String | ZIP code |
| `county` | String | County name |
| `registry_id` | String | EPA Registry ID |
| `naics` | String | NAICS code(s) - 327320 = Ready-Mix Concrete |
| `sic` | String | SIC code(s) - 3273 = Concrete products |

---

## Usage Notes

1. **Coordinate System:** All files use WGS84 (EPSG:4326)
2. **Encoding:** UTF-8
3. **Visualization:** Use the `CEMENT_INFRASTRUCTURE_MAP.html` in `/reports/` for interactive viewing
4. **WordPress:** Copy GeoJSON files to same directory as HTML for local file loading

---

## Updates Log

| Date | Update |
|------|--------|
| 2025-12-16 | Created Florida/Gulf regional layers |
| 2025-12-16 | Added Caribbean export market layers |
| 2025-12-16 | Created Port Redwing trucking radius |
| 2025-12-17 | Added North American cement plants (US+CA+MX) |
| 2025-12-17 | Added weighted import ports from Panjiva |
| 2025-12-17 | Downloaded BTS Class I rail network |
| 2025-12-17 | Downloaded BTS Marine Highways |
| 2025-12-17 | Created comprehensive infrastructure map |
| 2025-12-17 | Added Florida ready-mix plants (894) from EPA ECHO |
| 2025-12-17 | Added Gulf Coast ready-mix plants (1,694) from EPA ECHO |
