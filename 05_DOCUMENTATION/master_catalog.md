# Master Catalog — US Bulk Supply Chain Reporting Platform

**Last Updated**: 2026-02-23

This document provides a complete inventory of all universal modules and commodity directories in the reporting platform.

---

## Universal Modules (02_TOOLSETS/)

These are commodity-agnostic analytical engines that can be called by any commodity module.

### Transport & Infrastructure Modules

| Module | Description | Status | Primary Use Cases |
|--------|-------------|---------|-------------------|
| **barge_river** | Inland waterway freight analysis | 🟡 Partial | Barge cost modeling, lock delays, transit time, GTR rates |
| **rail** | Railroad freight analysis | 🟡 Partial | Rail routing, STB costing, URCS factors, network optimization |
| **highway_truck** | Highway freight analysis | 🔴 Stub | Truck routing, cost per mile, delivery time estimation |
| **ocean_vessel** | Ocean freight and vessel tracking | 🟡 Partial | Manifest processing, trade flows, vessel voyages, HTS codes |
| **pipeline** | Pipeline infrastructure analysis | 🔴 Stub | Pipeline routing, capacity modeling, terminal analysis |

### Data & Analysis Modules

| Module | Description | Status | Primary Use Cases |
|--------|-------------|---------|-------------------|
| **geospatial** | GIS and mapping utilities | 🟡 Partial | Map generation, spatial joins, layer management, network graphs |
| **epa_facility** | EPA facility registry analysis | 🟢 Built | Facility search by NAICS, entity resolution, spatial proximity |
| **economic** | Economic impact modeling | 🟡 Partial | RIMS II multipliers, employment modeling, fiscal impact analysis |
| **historical** | Historical data and time-series | 🔴 Stub | Archival research, trend analysis, data versioning |

**Legend**:
- 🟢 **Built**: Functional code exists, ready to use
- 🟡 **Partial**: Some code exists, needs completion/consolidation
- 🔴 **Stub**: Directory structure only, needs implementation

---

## Commodity Modules (03_COMMODITY_MODULES/)

These are vertical market intelligence directories that call universal modules for transport/infrastructure analysis.

| Commodity | Description | Status | Priority |
|-----------|-------------|--------|----------|
| **cement** | Portland cement, white cement, clinker, SCMs (slag, fly ash, pozzolans) | 🟡 Partial | P1 |
| **coal** | Thermal coal, metallurgical coal, petcoke | 🔴 Scaffold | P1 |
| **grain** | Wheat, corn, soybeans, sorghum, barley | 🔴 Scaffold | P1 |
| **steel_metals** | Steel, aluminum, copper, pig iron, iron ore | 🔴 Scaffold | P1 |
| **fertilizers** | Nitrogen, phosphate, potash | 🔴 Scaffold | P2 |
| **oil_gas** | Crude oil, refined products, LNG, petrochemicals | 🔴 Scaffold | P2 |
| **chemicals** | Industrial chemicals, bulk liquids | 🔴 Scaffold | P2 |
| **aggregates** | Sand, gravel, crushed stone | 🔴 Scaffold | P3 |
| **petcoke** | Petroleum coke | 🔴 Scaffold | P3 |

---

## Module Interface Pattern

All commodity modules follow this pattern when calling universal modules:

```python
from report_platform.toolsets import barge_river, rail, epa_facility

# Example: Coal commodity needs barge cost estimate
barge_cost = barge_river.calculate_cost(
    origin="Huntington, WV",
    destination="New Orleans, LA",
    commodity="coal",
    tonnage=15000
)

# Example: Grain commodity needs facility search
grain_elevators = epa_facility.query_facilities(
    naics_codes=["424510"],  # Grain merchant wholesalers
    states=["IA", "IL", "MO"],
    radius_miles=50,
    reference_point="Des Moines, IA"
)
```

---

## Cross-Reference Matrix

Which universal modules are used by which commodities:

|  | barge_river | rail | highway_truck | ocean_vessel | pipeline | geospatial | epa_facility | economic |
|--|:-----------:|:----:|:-------------:|:------------:|:--------:|:----------:|:------------:|:--------:|
| **cement** | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| **coal** | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| **grain** | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| **steel_metals** | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| **fertilizers** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **oil_gas** | - | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **chemicals** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **aggregates** | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | ✓ |
| **petcoke** | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |

---

## Navigation

- **Universal Module Details**: See `02_TOOLSETS/<module_name>/README.md`
- **Commodity Module Details**: See `03_COMMODITY_MODULES/<commodity_name>/README.md`
- **How to Call Modules**: See `05_DOCUMENTATION/module_interface_guide.md`
- **How to Add Commodities**: See `05_DOCUMENTATION/commodity_directory_guide.md`

---

**Next Steps**: Populate universal module README files with API documentation and usage examples.
