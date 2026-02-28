# System Architecture

## Data Flow

```
Raw Sources (Federal APIs, Downloads, Manual)
    │
    ▼
01_DATA_SOURCES/ ──── Organized by agency/type
    │
    ▼
02_TOOLSETS/ ──────── Analysis engines (DuckDB, NetworkX, GeoPandas)
    │
    ├── barge_cost_model    → Freight rate calculation
    ├── rail_cost_model     → Rail routing and costing
    ├── port_cost_model     → Port/terminal cost estimation
    ├── vessel_intelligence → Trade flow analysis
    ├── facility_registry   → EPA FRS facility queries
    ├── geospatial_engine   → Shared GIS utilities
    └── policy_analysis     → Regulatory impact modeling
    │
    ▼
03_COMMODITY_MODULES/ ── Commodity-specific extensions
    │
    └── cement/ ── Market intel + supply chain models
    │
    ▼
04_REPORTS/ ──────────── Generated reports (MD + DOCX)
```

## Technology Stack

- **Language:** Python 3.11+
- **Database:** DuckDB (analytics), Parquet (intermediate storage)
- **Geospatial:** GeoPandas, Folium, Shapely
- **Network Analysis:** NetworkX (rail routing)
- **CLI:** Click (command groups)
- **Entity Resolution:** rapidfuzz
- **Visualization:** Plotly, Matplotlib, Folium
