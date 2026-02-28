# Module Interface Guide

**Purpose**: This guide explains how commodity modules call universal modules for transport/infrastructure analysis.

---

## Architecture Principle

**Universal modules** (02_TOOLSETS/) contain commodity-agnostic analytical engines.
**Commodity modules** (03_COMMODITY_MODULES/) contain market-specific intelligence.

**Key Rule**: Commodity modules DO NOT duplicate transport analysis code. Instead, they CALL universal modules with commodity-specific parameters.

---

## Universal Module APIs

### barge_river

**Purpose**: Inland waterway freight cost modeling and transit analysis

**Primary Functions**:

```python
from report_platform.toolsets import barge_river

# Calculate barge freight cost
cost = barge_river.calculate_cost(
    origin="Huntington, WV",
    destination="New Orleans, LA",
    commodity="coal",
    tonnage=15000,
    season="Q4"  # Optional: for seasonal rate adjustments
)
# Returns: {
#   'linehaul_cost': 125000,
#   'fuel_surcharge': 8500,
#   'lock_fees': 2400,
#   'total_cost': 135900,
#   'cost_per_ton': 9.06
# }

# Calculate transit time including lock delays
transit = barge_river.calculate_transit(
    origin="Memphis, TN",
    destination="New Orleans, LA",
    lock_delay_model="probabilistic"  # or "average"
)
# Returns: {
#   'distance_miles': 684,
#   'base_transit_days': 5.2,
#   'lock_delay_days': 1.8,
#   'total_transit_days': 7.0
# }
```

**Use Cases**:
- Coal: Appalachian coal barge movements (Ohio/Monongahela rivers)
- Grain: Mississippi River grain barge (Illinois River to Gulf)
- Fertilizers: Fertilizer terminal to farm distribution
- Aggregates: Sand and gravel barge movements

---

### rail

**Purpose**: Railroad freight routing and cost analysis

**Primary Functions**:

```python
from report_platform.toolsets import rail

# Find optimal rail route
route = rail.calculate_route(
    origin="Des Moines, IA",
    destination="Portland, OR",
    commodity="grain",
    carloads=110,  # Unit train
    car_type="covered_hopper",
    optimization="cost"  # or "distance", "time"
)
# Returns: {
#   'route': ['BNSF', 'UP'],
#   'distance_miles': 1842,
#   'transit_days': 5.5,
#   'cost_per_car': 3250,
#   'total_cost': 357500
# }

# Calculate rail cost using STB URCS factors
cost = rail.calculate_urcs_cost(
    origin_splc="123456",
    destination_splc="789012",
    commodity_stcc="01131",  # Corn
    tonnage=11000  # 100 cars × 110 tons/car
)
```

**Use Cases**:
- Coal: Powder River Basin unit trains to power plants
- Grain: Corn/wheat unit trains to PNW/Gulf export terminals
- Cement: Cement plant to distribution terminal
- Steel: Steel slab from port to mini-mill

---

### highway_truck

**Purpose**: Highway freight routing and trucking cost analysis

**Primary Functions**:

```python
from report_platform.toolsets import highway_truck

# Calculate truck delivery cost
cost = highway_truck.calculate_cost(
    origin="Houston, TX",
    destination="Dallas, TX",
    commodity="cement",
    weight_tons=25,
    truck_type="pneumatic_tanker",
    return_empty=True  # Backhaul considerations
)
# Returns: {
#   'distance_miles': 239,
#   'fuel_cost': 142,
#   'driver_cost': 380,
#   'truck_cost': 215,
#   'tolls': 0,
#   'total_cost': 737,
#   'cost_per_ton': 29.48
# }
```

**Use Cases**:
- Cement: Terminal to ready-mix plant delivery
- Aggregates: Quarry to construction site
- Fertilizers: Terminal to farm delivery
- Chemicals: Plant to end-user delivery

---

### ocean_vessel

**Purpose**: Ocean freight, vessel tracking, and trade flow analysis

**Primary Functions**:

```python
from report_platform.toolsets import ocean_vessel

# Search import manifests by commodity HTS code
imports = ocean_vessel.search_manifests(
    hts_codes=["2523.29"],  # Portland cement
    ports=["USMOB", "USNOL"],  # Mobile, New Orleans
    date_range=("2024-01-01", "2024-12-31")
)
# Returns: DataFrame with columns:
#   vessel_name, imo, port, arrival_date, shipper, consignee,
#   tonnage, hts_code, origin_country

# Track vessel voyages
voyage = ocean_vessel.reconstruct_voyage(
    vessel_imo="9876543",
    date_range=("2024-06-01", "2024-06-30")
)
```

**Use Cases**:
- Cement: Import manifest analysis (Turkish, Egyptian cement)
- Steel: Steel slab import tracking
- Grain: Grain export vessel tracking
- Fertilizers: Potash import movements

---

### epa_facility

**Purpose**: Facility location and industry analysis using EPA FRS

**Primary Functions**:

```python
from report_platform.toolsets import epa_facility

# Find facilities by NAICS code
facilities = epa_facility.query_facilities(
    naics_codes=["327310"],  # Cement manufacturing
    states=["TX", "LA"],
    status="active"
)
# Returns: DataFrame with facility_id, name, address, lat, lon, naics

# Find facilities near a location
nearby = epa_facility.proximity_search(
    reference_point="New Orleans, LA",
    radius_miles=100,
    naics_codes=["327310", "327320"]  # Cement + ready-mix
)

# Resolve parent company
resolved = epa_facility.resolve_entity(
    facility_names=["Holcim Inc", "Holcim USA", "Holcim Louisiana"]
)
# Returns harmonized parent: "Holcim Group"
```

**Use Cases**:
- Cement: Map all cement plants and import terminals
- Coal: Identify power plants (NAICS 221112)
- Steel: Locate integrated mills and mini-mills
- Grain: Find grain elevators and processors
- All: Competitive landscape mapping

---

### geospatial

**Purpose**: GIS operations, mapping, and spatial analysis

**Primary Functions**:

```python
from report_platform.toolsets import geospatial

# Create interactive map
map_obj = geospatial.create_map(
    center=(30.0, -90.0),
    zoom=7,
    basemap="openstreetmap"
)

# Add facility layer
geospatial.add_point_layer(
    map_obj=map_obj,
    data=cement_plants_df,
    lat_col="latitude",
    lon_col="longitude",
    popup_cols=["name", "capacity_tons"],
    color="red",
    icon="industry"
)

# Perform spatial join (point-in-polygon)
result = geospatial.spatial_join(
    points_df=facilities_df,
    polygons_df=counties_df,
    join_type="intersects"
)

# Calculate distance matrix
distances = geospatial.distance_matrix(
    origins_df=plants_df,
    destinations_df=terminals_df,
    mode="haversine"  # or "network" for road distance
)
```

**Use Cases**:
- All commodities: Facility mapping
- Supply chain: Origin-destination distance calculations
- Market analysis: Catchment area analysis

---

### economic

**Purpose**: Economic impact modeling and fiscal analysis

**Primary Functions**:

```python
from report_platform.toolsets import economic

# Calculate economic impact using RIMS II multipliers
impact = economic.calculate_impact(
    direct_output=50000000,  # $50M direct output
    industry_code="483211",   # Inland water freight
    region_fips="22051",      # Jefferson Parish, LA
    multiplier_type="Type_II"
)
# Returns: {
#   'direct_output': 50000000,
#   'indirect_output': 12500000,
#   'induced_output': 8300000,
#   'total_output': 70800000,
#   'direct_jobs': 125,
#   'total_jobs': 287
# }
```

**Use Cases**:
- Port studies: Economic impact of port operations
- Facility analysis: Regional economic contribution
- Policy analysis: Impact of regulatory changes

---

## Example: Commodity Module Calling Universal Modules

### Coal Commodity Report Example

```python
# FILE: 03_COMMODITY_MODULES/coal/reports/appalachian_barge_analysis.py

from report_platform.toolsets import barge_river, epa_facility, geospatial

# Step 1: Find coal mines in Appalachia
coal_mines = epa_facility.query_facilities(
    naics_codes=["212100"],  # Coal mining
    states=["WV", "KY", "PA"],
    status="active"
)

# Step 2: Calculate barge costs from key origins to export terminals
routes = [
    {"origin": "Huntington, WV", "destination": "New Orleans, LA"},
    {"origin": "Pittsburgh, PA", "destination": "Mobile, AL"},
]

barge_costs = []
for route in routes:
    cost = barge_river.calculate_cost(
        origin=route["origin"],
        destination=route["destination"],
        commodity="coal",
        tonnage=15000
    )
    barge_costs.append({**route, **cost})

# Step 3: Create map showing mines and routes
map_obj = geospatial.create_map(center=(38.0, -81.0), zoom=6)
geospatial.add_point_layer(map_obj, coal_mines, "lat", "lon", color="black")
geospatial.add_route_layer(map_obj, routes, color="blue", weight=3)

# Step 4: Save results to commodity-specific output
save_coal_report(barge_costs, map_obj)
```

**Key Principle Demonstrated**: The coal module does NOT implement barge cost calculations or GIS operations. It CALLS the universal modules and provides coal-specific parameters (NAICS 212100, coal origins/destinations).

---

## Best Practices

### ✅ DO:
- Call universal modules from commodity modules
- Pass commodity-specific parameters (NAICS codes, HTS codes, origins/destinations)
- Store commodity-specific outputs in `03_COMMODITY_MODULES/<commodity>/reports/`
- Document commodity-specific data sources in `data_sources.json`

### ❌ DON'T:
- Duplicate transport analysis code in commodity modules
- Hard-code NAICS/HTS codes in universal modules (accept as parameters)
- Store commodity-specific data in universal module `/data` folders
- Mix commodity market intelligence with universal analytical code

---

## CLI Usage

All universal modules are accessible via CLI:

```bash
# Barge cost calculation
report-platform barge cost --origin "Huntington, WV" --dest "New Orleans, LA" --commodity coal --tonnage 15000

# Rail route analysis
report-platform rail route --origin "Des Moines, IA" --dest "Portland, OR" --commodity grain --carloads 110

# Facility search
report-platform facility search --naics 327310 --state LA --radius 100 --reference "New Orleans, LA"

# Commodity-specific operations
report-platform commodity analyze --name coal --report barge-economics
report-platform commodity analyze --name grain --report export-flows
```

---

## Next Steps

1. Populate each universal module's `api_reference.md` with detailed API documentation
2. Add code examples to each commodity module's README
3. Build integration tests showing commodity → universal module calls
4. Create Jupyter notebook tutorials for common analysis patterns

---

**Related Documentation**:
- [Master Catalog](master_catalog.md) — Full inventory of modules and commodities
- [Commodity Directory Guide](commodity_directory_guide.md) — How to create new commodity modules
