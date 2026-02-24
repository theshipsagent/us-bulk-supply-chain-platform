# Barge Cost Model

Waterway transportation cost calculator and routing engine for US inland waterway system.

## Overview

This toolset provides comprehensive barge freight cost modeling for the Mississippi River system and connected inland waterways. It includes:

- **Route Planning**: NetworkX-based pathfinding with vessel constraint enforcement
- **Cost Calculation**: Multi-component cost engine (fuel, crew, locks, delays, terminals)
- **Transit Modeling**: Lock delay estimation and transit time calculation
- **Fleet Utilization**: Barge fleet capacity and utilization tracking
- **Rate Analysis**: USDA GTR-based rate lookups with seasonal adjustment

## Key Components

### Routing Engine (`src/engines/routing_engine.py`)
- Dijkstra's shortest path algorithm
- A* pathfinding with heuristics
- Vessel constraint enforcement (beam, draft, length)
- Lock detection and delay estimation
- K-shortest paths for route alternatives

### Cost Engine (`src/engines/cost_engine.py`)
- Fuel consumption and cost calculation
- Crew costs (daily rate × transit days)
- Lock passage fees and delay costs
- Terminal handling fees
- Cost per ton and cost per ton-mile metrics
- Route profitability estimation

### Data Models (`src/models/`)
- `route.py`: Route computation models (ComputedRoute, RouteSegment, RouteCost)
- `waterway.py`: Waterway network models
- `vessel.py`: Vessel specifications and constraints
- `cargo.py`: Cargo type definitions

### Data Loaders (`src/data_loaders/`)
- `load_waterways.py`: Waterway network and graph construction
- `load_locks.py`: Lock facilities with dimensional constraints
- `load_docks.py`: Navigation facilities and terminals
- `load_tonnages.py`: Cargo volume by commodity type
- `load_vessels.py`: Vessel registry with specifications

## Data Sources

Primary data from Bureau of Transportation Statistics (BTS) and USACE:

- **Waterway Networks**: 6,860 network segments with ANODE/BNODE graph structure
- **Locks**: 80 lock facilities with dimensional constraints
- **Docks**: 29,645 navigation facilities with depth data
- **Link Tonnages**: Cargo volume by commodity type per waterway segment
- **Vessels**: 52,035 vessel registry with beam/draft specifications

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL with PostGIS
createdb barge_db
psql -d barge_db -c "CREATE EXTENSION postgis;"
psql -d barge_db -f src/db/schema.sql

# Load data
python src/data_loaders/load_waterways.py
python src/data_loaders/load_locks.py
python src/data_loaders/load_docks.py
python src/data_loaders/load_tonnages.py
python src/data_loaders/load_vessels.py
```

## Usage

### Basic Route Calculation

```python
from src.engines.routing_engine import RoutingEngine
from src.engines.cost_engine import CostEngine

# Initialize engines
router = RoutingEngine()
costing = CostEngine()

# Find route
route = router.find_route(
    origin_node=12345,
    dest_node=67890,
    algorithm='dijkstra'
)

# Calculate costs
cost = costing.calculate_route_cost(
    route=route,
    vessel_dwt=15000,
    include_terminals=True
)

print(f"Distance: {route.total_distance_miles:.1f} miles")
print(f"Transit Time: {route.transit_time_days:.1f} days")
print(f"Total Cost: ${cost.total_cost_usd:,.2f}")
print(f"Cost per ton: ${cost.cost_per_ton(5000):.2f}")
```

### With Vessel Constraints

```python
from src.models.route import RouteConstraints

# Define vessel constraints
constraints = RouteConstraints(
    vessel_beam_m=35.0,      # 35 meter beam
    vessel_draft_m=12.0,     # 12 meter draft
    vessel_length_m=195.0    # 195 meter length
)

# Find feasible route
route = router.find_route(
    origin_node=12345,
    dest_node=67890,
    constraints=constraints
)

if route.is_feasible:
    print(f"Route feasible for vessel")
else:
    print(f"Constraints not met: {route.feasibility_notes}")
```

### API Server

```bash
# Start FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# Start Streamlit dashboard
streamlit run dashboard/app.py --server.port 8501
```

## Architecture

```
┌─────────────────────────────────────────┐
│   Streamlit Dashboard (Frontend)       │
│   Port: 8501                            │
└────────────┬────────────────────────────┘
             │
┌────────────┴────────────────────────────┐
│   FastAPI Backend (Processing)         │
│   Port: 8000                            │
└────────────┬────────────────────────────┘
             │
┌────────────┴────────────────────────────┐
│   PostgreSQL+PostGIS Database          │
│   Port: 5432                            │
│   - waterway_links (6,860 rows)        │
│   - locks (80 rows)                     │
│   - docks (29,645 rows)                 │
│   - link_tonnages (6,860 rows)          │
│   - vessels (52,035 rows)               │
└─────────────────────────────────────────┘
```

## Configuration

Create `.env` file:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/barge_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Cost Model Components

The cost engine calculates comprehensive transportation costs:

1. **Fuel Costs**: Consumption based on transit time and vessel size
2. **Crew Costs**: Daily crew rate × crew size × transit days
3. **Lock Fees**: Per-lock passage fees + delay time costs
4. **Terminal Fees**: Origin and destination handling fees
5. **Delay Costs**: Lock queue delays, weather delays

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for detailed white paper on:
- USDA GTR data integration
- Lock delay probabilistic modeling
- Fleet utilization impact on rates
- Variable cost component breakdown
- Route optimization algorithms

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_engines.py
pytest tests/test_loaders.py
```

## Documentation

- `METHODOLOGY.md`: Technical white paper on cost modeling approach
- `docs/QUICK_START.md`: Quick start guide for new users
- `docs/BUILD_STATUS.md`: Current implementation status
- `docs/PROJECT_SUMMARY.md`: Project overview and goals

## Integration with Master Platform

This toolset integrates with the master reporting platform:

- **Core Platform**: Provides commodity-agnostic waterway infrastructure analysis
- **Commodity Modules**: Cement, grain, fertilizer modules use this toolset for barge distribution costs
- **Geospatial Engine**: Shared mapping utilities for route visualization
- **Facility Registry**: EPA FRS integration for origin/destination facility lookups

## Knowledge Base

The original project included 79 research PDFs (3.6 GB) processed into 29,265 text chunks covering:
- Barge economics and rate forecasting
- Transit routing and lock operations
- Traffic forecasting and demand modeling
- Infrastructure capacity analysis
- Navigation history and waterway evolution

## Project Status

**Phase**: Foundation complete, API and dashboard operational
**Coverage**: Mississippi River system and connected inland waterways
**Data Vintage**: BTS/USACE datasets (latest available)
**Next Steps**:
- Integration with USDA GTR live data feeds
- Real-time lock delay prediction
- Machine learning for rate forecasting

## Original Source

Migrated from: `G:\My Drive\LLM\project_barge`
Migration date: 2026-02-23

## License

Internal use for OceanDatum.ai and SESCO Cement Corporation.

## Contact

William Davis - OceanDatum.ai Maritime Consultancy
