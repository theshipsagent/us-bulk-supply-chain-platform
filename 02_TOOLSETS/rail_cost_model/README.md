# Rail Network Geospatial Cost Model

**Project Codename:** RAILCOST-GEO

## Overview

A geospatial freight rail cost and flow model integrating:
1. Federal railroad network topology (NTAD/NARN lines and nodes)
2. STB economic data (URCS costing system, Waybill Sample)
3. Freight Analysis Framework (FAF5) commodity flows

The end goal is a working analytical tool that can:
- Visualize rail network topology with cost attributes
- Route commodities across the network with cost estimation
- Analyze trade flow corridors and identify cost drivers
- Support "what-if" scenarios for routing alternatives

## Project Structure

```
rail_cost_model/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── config/
│   └── config.yaml              # Data source URLs, parameters, paths
├── data/
│   ├── raw/                     # Downloaded source files (gitignored)
│   │   ├── ntad/               # NARN shapefiles
│   │   ├── stb/                # URCS workbooks, waybill data
│   │   └── faf/                # FAF5 databases
│   ├── processed/              # Cleaned/transformed data
│   └── reference/              # Lookup tables, crosswalks
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_network_build.ipynb
│   ├── 03_cost_integration.ipynb
│   └── 04_flow_assignment.ipynb
├── src/
│   ├── data_ingestion/         # Download and parse data
│   ├── network/                # Graph construction and routing
│   ├── costing/                # URCS cost models
│   ├── analysis/               # Flow and corridor analysis
│   └── visualization/          # Map generation
├── outputs/
│   ├── maps/                   # Generated HTML maps
│   ├── reports/                # Analysis outputs
│   └── exports/                # Data exports (CSV, GeoJSON)
└── tests/                      # Unit tests
```

## Installation

### 1. Navigate to project directory

```bash
cd "G:\My Drive\LLMail_cost_model"
```

### 2. Create Python virtual environment

```bash
python -m venv venv
venv\Scriptsctivate  # Windows
# or: source venv/bin/activate  # Unix/Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Download NTAD Data

```bash
python -m src.main --action download
```

Downloads and caches:
- Rail Lines (track segments)
- Rail Nodes (junctions, terminals)
- Rail Yards (classification facilities)

Data is cached as Parquet files in `data/raw/ntad/` for fast subsequent loads.

### Build Network Graph

```bash
python -m src.main --action build
```

Creates NetworkX graph with:
- Nodes: Rail junctions, terminals, interchanges
- Edges: Track segments with distance, owner, track class attributes
- Saved to `data/processed/rail_network.gpickle`

### Create Visualization

```bash
python -m src.main --action visualize
```

Generates interactive map at `outputs/maps/network_map.html`

### Run Analysis

```bash
python -m src.main --action analyze
```

Runs network analysis and example route costing.

### Jupyter Notebooks

```bash
jupyter lab notebooks/
```

Available notebooks:
- **01_data_exploration.ipynb**: Explore NTAD and STB datasets
- **02_network_build.ipynb**: Build and validate network graph
- **03_cost_integration.ipynb**: Apply URCS costs to routes
- **04_flow_assignment.ipynb**: Assign FAF5 flows to network

## Data Sources

### NTAD (National Transportation Atlas Database)
- **Rail Lines**: Track ownership, class, signals
- **Rail Nodes**: Junctions and connection points
- **Rail Yards**: Classification facilities
- **Source**: https://www.bts.gov/ntad

### STB (Surface Transportation Board)
- **URCS**: Uniform Rail Costing System
- **Waybill Sample**: Public Use Waybill (commodity flows)
- **Source**: https://www.stb.gov/reports-data/

### FAF5 (Freight Analysis Framework)
- Commodity flow forecasts by mode
- **Source**: https://www.bts.gov/faf

## Cost Model

URCS-based variable cost components:

### Running Costs (Distance-Based)
- Train-mile costs
- Car-mile costs
- Gross ton-mile costs

### Terminal/Switching Costs
- Per car switched
- Per carrier interchange

### Equipment Costs
- Car-days (time in transit)

## Key Modules

### Data Ingestion
- `ntad_loader.py`: NARN data from ArcGIS REST API
- `stb_loader.py`: URCS workbooks and STB data
- `faf_loader.py`: FAF5 databases

### Network Analysis
- `graph_builder.py`: NetworkX graph from NARN
- `topology.py`: Connectivity validation
- `routing.py`: Shortest path algorithms

### Costing
- `urcs_model.py`: URCS unit cost calculations
- `route_costing.py`: Apply costs to routes

### Visualization
- `network_maps.py`: Interactive Folium maps
- `flow_maps.py`: Commodity flow visualization

## Development Status

### Phase 1: Data Acquisition ✓
- [x] NARN data loader with ArcGIS REST API
- [x] URCS workbook parser
- [x] FAF5 loader
- [x] Data caching (Parquet)

### Phase 2: Network Construction ✓
- [x] NetworkX graph builder
- [x] Topology validation
- [x] Shortest path routing
- [ ] Multi-path analysis

### Phase 3: Cost Integration ✓
- [x] Variable cost calculator
- [x] Route cost application
- [ ] Railroad-specific cost curves
- [ ] Commodity-specific parameters

### Phase 4: Visualization ✓
- [x] Network map generation
- [x] Route highlighting
- [ ] Flow volume visualization
- [ ] Cost heatmaps

## Author

**William Davis**  
Maritime/Logistics Industry Consultant  
30+ years experience in terminal operations and commodity trade flows

## References

1. **NTAD Data**: https://www.bts.gov/ntad
2. **NARN ArcGIS**: https://geodata.bts.gov/
3. **STB Economic Data**: https://www.stb.gov/reports-data/
4. **URCS Program**: https://www.stb.gov/reports-data/uniform-rail-costing-system/
5. **FAF5**: https://www.bts.gov/faf
6. **Waybill Sample**: https://www.stb.gov/reports-data/waybill/

## License

Internal use - Maritime Infrastructure Project
