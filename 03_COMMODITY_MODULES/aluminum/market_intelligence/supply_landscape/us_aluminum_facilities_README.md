# US & North American Aluminum Facilities Geospatial Database

## Overview

Comprehensive geospatial database of **68 facilities** consuming or producing unwrought aluminum (ingots, sows, T-bars, billets, rolling slab) across North America. Designed for import supply chain mapping against Panjiva/CBP ocean manifest records under HS 7601 (unwrought aluminum).

**Data Vintage:** Current as of February 2026
**Coordinate System:** WGS84 (EPSG:4326)

## Supply Chain Context

The US imports ~5.5 million metric tons of unwrought aluminum annually, primarily from Canada (~65%), UAE, Russia (restricted), Bahrain, and others. This database maps the domestic consumers of that imported metal:

```
Primary Smelter (alumina → primary ingot)
         ↓
Imported Unwrought → Rolling Mill (slab → sheet/plate/coil)
  (ingot/sow/T-bar)  → Secondary Smelter (scrap+prime → alloy ingot)
                      → Billet Caster (scrap+prime → extrusion billet)
                      → Die Caster/Foundry (ingot → automotive castings)
                               ↓
                         End-Use Markets:
                         - Packaging (36% - cans, foil, containers)
                         - Automotive (23% - body panels, structural)
                         - Building/Construction (14%)
                         - Electrical (9%)
                         - Aerospace/Defense (8%)
                         - Consumer/Industrial (10%)
```

## Facility Categories

| Type | Count | Description |
|------|-------|-------------|
| `primary_smelter` | 7 | Electrolytic reduction of alumina; only 4 operating in US (2 at reduced capacity, 2 idled, 1 planned) |
| `integrated_mill` | 11 | Combined casthouse + hot/cold rolling; largest consumers of imported slab |
| `rolling_mill` | 16 | Hot and/or cold rolling of slab to sheet, plate, foil |
| `secondary_smelter` | 27 | Remelt scrap + imported prime into specification alloy ingot |
| `billet_caster` | 8 | Remelt scrap + prime into extrusion billet and forging stock |

## Key Statistics

- **Total operating/reduced capacity:** ~7,600 kt/yr across all types
- **Integrated mill capacity:** 3,380 kt/yr (Novelis, Arconic, Constellium, Kaiser, SDI, Tri-Arrows)
- **Rolling mill capacity:** 1,480 kt/yr
- **Secondary smelter capacity:** 1,005 kt/yr
- **Billet caster capacity:** 888 kt/yr (Matalco alone: 848 kt/yr)
- **Primary smelter capacity:** 848 kt/yr (only 2 at full capacity)

## Top Companies

| Company | Total Capacity (kt/yr) | Facility Count | Primary Products |
|---------|----------------------|----------------|------------------|
| Arconic | 1,550 | 5 | Aerospace/auto sheet & plate |
| Novelis (Hindalco) | 1,170 | 7 | Can stock, auto body sheet |
| Matalco (Giampaolo/Rio Tinto) | 848 | 7 | Extrusion billet |
| Constellium | 700 | 3 | Can stock, aerospace plate |
| Kaiser Aluminum | 500 | 2 | Can stock, aerospace plate |
| Century Aluminum | 449 | 3 | Primary ingot (high-purity) |
| Alcoa | 399 | 2 | Primary ingot |
| Real Alloy | 395 | 12 | Secondary alloy ingot |

## New Facilities (Construction/Planned)

| Facility | Company | Location | Capacity | Status | Expected |
|----------|---------|----------|----------|--------|----------|
| Bay Minette | Novelis | AL | 600-1,000 kt | Construction | H2 2026 |
| Columbus | Aluminum Dynamics (SDI) | MS | 650 kt | Construction | Mid-2025 |
| Inola Green Smelter | Century Aluminum | OK | 500 kt | Planned | ~2031 |

## Geographic Distribution

**Kentucky dominates** with 14 facilities — the Ohio River corridor from Louisville to Henderson is the densest aluminum processing cluster in North America. Other concentrations:

- **Ohio River Valley** (KY/IN/OH): Rolling mills, billet casters, secondary smelters
- **Southeast** (AL/TN/MS): New integrated mills, secondary smelters, can stock
- **Northeast** (NY/PA): Legacy Alcoa/Arconic rolling, aerospace plate

## Files

| File | Format | Description |
|------|--------|-------------|
| `us_aluminum_facilities.py` | Python 3 | Source module with dataclasses, geocoded facilities, export functions |
| `us_aluminum_facilities.geojson` | GeoJSON | 68 point features with full properties |
| `us_aluminum_facilities.csv` | CSV | Flat table, pipe-delimited facility types |
| `us_aluminum_facilities_README.md` | Markdown | This file |

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Facility name |
| `company` | string | Current owner/operator |
| `facility_types` | string | Pipe-delimited: primary_smelter, rolling_mill, secondary_smelter, billet_caster, integrated_mill |
| `city` | string | City |
| `state` | string | State/province code |
| `country` | string | US, Canada |
| `lat` | float | Latitude (WGS84) |
| `lon` | float | Longitude (WGS84) |
| `capacity_kt` | float | Annual capacity in thousand metric tons |
| `capacity_notes` | string | Capacity context and qualifications |
| `products` | string | Product types (sheet, plate, can_stock, billet, ingot, etc.) |
| `markets` | string | End markets served |
| `alloys` | string | Alloy series produced (1xxx through 7xxx) |
| `has_hot_mill` | bool | Hot rolling capability |
| `has_cold_mill` | bool | Cold rolling capability |
| `has_casthouse` | bool | Melting/casting capability |
| `has_recycling` | bool | Scrap recycling/remelting capability |
| `num_potlines` | int | Number of potlines (primary smelters) |
| `port_adjacent` | bool | Adjacent to ocean/deep-water port |
| `water_access` | bool | River or lake access |
| `barge_access` | bool | Active barge loading/unloading |
| `rail_served` | bool | Railroad access |
| `status` | string | operating, reduced, idled, construction, planned, closed |
| `startup_year` | int | Year operations began |
| `employees` | int | Approximate headcount |
| `notes` | string | Detailed context, recent investments, ownership changes |

## Integration with Steel Database

Combined with the AIST Steel Plants database (68 facilities) and US Flat-Rolled End Users database (53 facilities), this creates a **189-facility** geospatial dataset covering the full US metals value chain:

- **Aluminum production & processing:** 68 facilities (this database)
- **Steel production:** 68 facilities (AIST database)
- **Steel end users/service centers:** 53 facilities

## Panjiva Import Matching

For HS 7601 (unwrought aluminum) consignee matching:
- **Rolling mills and integrated mills** are the primary receivers of imported slab/ingot
- **Billet casters** (especially Matalco) receive prime aluminum to blend with scrap
- **Secondary smelters** receive smaller volumes of prime metal for alloying
- Key import ports: New Orleans, Houston, Savannah, Newark, Baltimore, Mobile

## Data Sources

- USGS Mineral Commodity Summaries 2024-2025 (Aluminum chapter)
- CRS Report R47294: U.S. Aluminum Manufacturing: Industry Trends and Sustainability
- The Aluminum Association "Powering Up American Aluminum" white paper (May 2025)
- Aluminum Association member directories (Producer, Associate)
- EPI Section 232 Aluminum Report (2021)
- Light Metal Age Magazine facility reports (2016-2025)
- Recycling Today Secondary Aluminum Producers directory (2015)
- Company websites, SEC filings, press releases (Novelis, Arconic, Constellium, Kaiser, Century, Alcoa, Matalco, Real Alloy, SDI)
- Fastmarkets, S&P Global Platts metals reporting

## Limitations

1. **Extruders not included** — 100+ extrusion plants exist but receive billet by truck, rarely ocean import consignees. Add as Phase 2 via AEC Buyers' Guide.
2. **Die casters/foundries not included** — Nemak, Ryobi, etc. receive ingot but are auto-parts manufacturers. Phase 3.
3. **Capacity estimates** — Some secondary smelter capacities estimated from industry reports; exact figures often proprietary.
4. **Mexico facilities** — Only US and one Canada facility included; Mexican operations (Nemak, INALUM) would expand dataset.
5. **Continuous updates needed** — Bay Minette and Columbus commissioning in 2025-2026 will add 1,250 kt/yr.
