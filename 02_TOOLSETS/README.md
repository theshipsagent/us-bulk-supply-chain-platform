# Toolsets Catalog

Reusable, commodity-agnostic analysis engines.

## Available Toolsets

| Toolset | Purpose | Status |
|---------|---------|--------|
| `barge_cost_model/` | Inland waterway freight cost calculator (GTR-based) | Migrating |
| `rail_cost_model/` | Railroad freight cost calculator (STB/URCS, NTAD routing) | Partially built |
| `port_cost_model/` | Port/terminal cost estimator (pilotage, towage, stevedoring) | Partially built |
| `port_economic_impact/` | Regional economic impact modeling (RIMS II/IMPLAN) | New |
| `vessel_intelligence/` | Vessel tracking and trade flow analysis (Panjiva pipeline) | Partially built |
| `facility_registry/` | EPA FRS geospatial analysis engine (DuckDB, 4M+ facilities) | Partially built |
| `geospatial_engine/` | Shared mapping and GIS utilities (Folium/Leaflet) | New |
| `policy_analysis/` | Maritime policy tools (Section 301, Jones Act, tariffs) | Migrating |

## Usage Pattern

Each toolset follows the same structure:
```
toolset_name/
├── src/           Source code
├── data/          Model-specific reference data
├── tests/         Unit and integration tests
└── METHODOLOGY.md White paper documentation
```

## Dependencies

All toolsets share the project-level `requirements.txt`. Toolset-specific deps are documented in each `METHODOLOGY.md`.
