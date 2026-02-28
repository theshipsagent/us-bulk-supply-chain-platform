# Methodology Index — Toolset Technical Documentation

This index links to all `METHODOLOGY.md` files across the platform's toolsets. Each methodology document provides a comprehensive technical description of the models, algorithms, data sources, and validation approaches used in the corresponding toolset.

## Core Toolset Methodologies

| Toolset | Path | Description | Key Methods |
|---|---|---|---|
| **Barge Cost Model** | [`02_TOOLSETS/barge_cost_model/METHODOLOGY.md`](../02_TOOLSETS/barge_cost_model/METHODOLOGY.md) | Inland waterway freight cost estimation | USDA GTR rates, VAR/SpVAR forecasting, USACE lock delay modeling, NetworkX waterway routing |
| **Rail Cost Model** | [`02_TOOLSETS/rail_cost_model/METHODOLOGY.md`](../02_TOOLSETS/rail_cost_model/METHODOLOGY.md) | Railroad freight cost estimation | NTAD/NARN network graph, STB URCS variable costing, Dijkstra routing, waybill analytics |
| **Port Cost Model** | [`02_TOOLSETS/port_cost_model/METHODOLOGY.md`](../02_TOOLSETS/port_cost_model/METHODOLOGY.md) | Port call proforma cost estimation | Multi-association pilotage, towage brackets, dockage/wharfage tariffs, stevedoring rates |
| **Port Economic Impact** | [`02_TOOLSETS/port_economic_impact/METHODOLOGY.md`](../02_TOOLSETS/port_economic_impact/METHODOLOGY.md) | Regional economic impact modeling | RIMS II/IMPLAN multipliers, direct/indirect/induced employment, fiscal impact, scenario analysis |

## Supporting Toolset Documentation

| Toolset | Path | Description |
|---|---|---|
| **Facility Registry** | `02_TOOLSETS/facility_registry/` | EPA FRS geospatial facility search — DuckDB-backed, 4M+ US facilities, NAICS/SIC classification, spatial queries |
| **Vessel Intelligence** | `02_TOOLSETS/vessel_intelligence/` | Panjiva import manifest processing — 7-phase classification pipeline, 800K+ records, entity resolution |
| **Geospatial Engine** | `02_TOOLSETS/geospatial_engine/` | Shared GIS utilities — Folium map generation, layer management, spatial joins, export (GeoJSON/SHP/KML) |
| **Policy Analysis** | `02_TOOLSETS/policy_analysis/` | Maritime regulatory modeling — Section 301 fee calculator, Jones Act analysis, tariff impact, regulatory tracker |

## Cross-References

### How Toolsets Interact

```
Vessel Intelligence ──→ Trade Flow Analysis ──→ Port Cost Model
       │                                              │
       ▼                                              ▼
Policy Analysis ──────→ Landed Cost Models    Proforma Estimates
       │                       │                      │
       ▼                       ▼                      ▼
Section 301 Impact     Total Import Cost       Port Call Cost
       │                       │                      │
       └───────────────────────┴──────────────────────┘
                               │
                    Commodity Module Reports
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
         Barge Cost       Rail Cost     Facility Registry
          Model            Model         (EPA FRS)
                │              │              │
                ▼              ▼              ▼
         Modal Cost      Modal Cost     Demand Mapping
         Estimates       Estimates      (NAICS spatial)
```

### Data Flow Summary

1. **Raw Data** (`01_DATA_SOURCES/`) feeds into toolsets
2. **Toolsets** (`02_TOOLSETS/`) produce cost estimates, routes, facility maps
3. **Commodity Modules** (`03_COMMODITY_MODULES/`) apply toolsets to specific commodity verticals
4. **Reports** (`04_REPORTS/`) consume toolset outputs for publication-quality analysis

## Methodology Standards

All methodology documents follow these conventions:

- **Data sources**: Cited with URL, format, refresh cadence, and access date
- **Formulas**: Presented in code blocks with variable definitions
- **Rate tables**: Include source, effective date, and units
- **Validation**: Cross-referenced against published data and industry benchmarks
- **Limitations**: Explicitly documented with estimated impact ranges
- **References**: Numbered list with full citation

## Version History

| Date | Version | Changes |
|---|---|---|
| Q1 2026 | 1.0.0 | Initial methodology documentation for all 4 core toolsets |

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | OceanDatum.ai*
