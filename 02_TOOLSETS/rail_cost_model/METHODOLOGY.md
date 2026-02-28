# Rail Cost Model — Technical Methodology

## 1. Overview

The Rail Cost Model provides freight rate estimation for US railroad shipments using the Surface Transportation Board's Uniform Rail Costing System (URCS) methodology, combined with NTAD/NARN network graph-based routing. The model supports route computation, variable cost calculation, and corridor-level analysis for bulk commodity transport.

**Platform Path:** `02_TOOLSETS/rail_cost_model/`
**Primary Output:** $/carload and $/ton freight cost estimates
**Key Dependencies:** NetworkX (graph routing), DuckDB (waybill analytics), GeoPandas (spatial)

## 2. Data Sources

### 2.1 National Transportation Atlas Database (NTAD)

The NTAD Rail Network dataset, maintained by the Bureau of Transportation Statistics (BTS), provides the physical rail network topology:

| Dataset | Source | Format | Content |
|---|---|---|---|
| Rail Lines | BTS/ArcGIS REST | Shapefile/GeoJSON | Track segments with owner, class, signals |
| Rail Nodes | BTS/ArcGIS REST | Shapefile/GeoJSON | Junctions, terminals, yards |
| Rail Yards | BTS/ArcGIS REST | Shapefile/GeoJSON | Classification and intermodal yards |

**Node/edge count:** Full continental US + partial Canada
**Loading method:** ArcGIS REST API with Parquet caching

### 2.2 STB Uniform Rail Costing System (URCS)

The URCS provides standardised unit costs for railroad operations, published annually by the Surface Transportation Board:

| Cost Category | Unit | Typical Range (2023) |
|---|---|---|
| Car-mile | $/car-mile | $0.15–0.35 |
| Gross ton-mile (GTM) | $/GTM | $0.003–0.008 |
| Train-mile | $/train-mile | $8.00–15.00 |
| Car-day (equipment) | $/car-day | $25–50 |
| Terminal switching | $/car | $150–400 |

**Regional variations:** East (CSX, NS territory), West (BNSF, UP territory), System average
**Annual updates:** Published Q2 for prior year data

### 2.3 Public Use Waybill Sample

The STB Public Use Waybill Sample provides a stratified sample of US rail shipments:

| Year | Records | File Size | Coverage |
|---|---|---|---|
| 2018 | ~500K | 166 MB | All Class I railroads |
| 2019 | ~480K | 161 MB | All Class I railroads |
| 2020 | ~450K | 153 MB | All Class I railroads |
| 2021 | ~600K | 495 MB | All Class I railroads |
| 2022 | ~620K | 499 MB | All Class I railroads |

**Key fields used:** Origin BEA, Destination BEA, STCC code, carloads, tons, revenue, distance
**Storage:** DuckDB analytical database (314 MB)

### 2.4 Freight Analysis Framework (FAF5)

FHWA's FAF5 database provides commodity flow forecasts by mode:
- Base year 2017, forecasts to 2050
- Rail mode filtering for freight flow volumes
- Origin-destination commodity matrices by FAF zone

### 2.5 State Rail Plans

The model references 50+ state rail plans (638 MB of PDF documents) for:
- State-level rail infrastructure priorities
- Short line railroad connectivity
- Rail-served industrial development zones

## 3. Network Graph Construction

### 3.1 Graph Structure

The rail network is represented as a NetworkX MultiDiGraph:

```
Graph G = (V, E) where:
  V = {rail nodes: junctions, terminals, yards, stations}
  E = {track segments with attributes: owner, class, distance, signals}

Properties:
  - MultiDiGraph supports parallel tracks (e.g., double-track mainlines)
  - Directed edges model one-way restrictions and directional costs
  - Spatial index for efficient node lookup by coordinates
```

### 3.2 Edge Weighting

Edges are weighted by a composite cost factor:

```
Weight(e) = Distance(e) × TypeFactor(e) × ClassFactor(e)

Where:
  TypeFactor: mainline = 1.0, branch = 1.3, yard = 2.0
  ClassFactor: Class 4+ = 1.0, Class 3 = 1.1, Class 2 = 1.3, Class 1 = 1.8
```

This weighting ensures route optimization favours mainline trackage over branch lines and higher-class track over lower-class track.

### 3.3 Carrier Interchange

The model identifies carrier interchange points where shipments transfer between Class I railroads:

| Gateway | Railroads | Region |
|---|---|---|
| Chicago | BNSF, UP, CSX, NS, CN, CP | Midwest hub |
| Kansas City | BNSF, UP, KCS | Western gateway |
| Memphis | BNSF, UP, CSX, NS, CN | Southern corridor |
| St. Louis | BNSF, UP, NS | Mississippi crossing |
| New Orleans | BNSF, UP, CSX, NS, CN, KCS | Gulf gateway |

Each interchange adds a switching cost ($150–400/car) and transit time (12–24 hours).

## 4. Cost Calculation (URCS Methodology)

### 4.1 Variable Cost Components

The URCS variable cost for a shipment is:

```
Total Variable Cost = Line-Haul Cost + Terminal Cost + Equipment Cost

Line-Haul Cost:
  = (Car-Miles × Unit Cost/Car-Mile)
  + (Gross Ton-Miles × Unit Cost/GTM)
  + (Train-Miles × Unit Cost/Train-Mile × Cars-per-Train factor)

Terminal Cost:
  = Origin Switching + Destination Switching + Interchange Switching
  = Σ(switching events × $/car switching cost)

Equipment Cost:
  = Car-Days × $/Car-Day
  = (Transit Days + Terminal Days + Delay Days) × Equipment Rate
```

### 4.2 Revenue-to-Variable-Cost (R/VC) Ratio

The R/VC ratio is the standard STB metric for rate reasonableness:

```
R/VC = Revenue per Car / Variable Cost per Car

Interpretation:
  R/VC = 1.0  → Rate equals variable cost (below full cost)
  R/VC = 1.8  → STB jurisdictional threshold for rate complaints
  R/VC > 3.0  → Potentially captive shipper situation
```

**Bulk commodity R/VC benchmarks (from waybill analysis):**

| Commodity | Typical R/VC | Interpretation |
|---|---|---|
| Coal | 1.5–2.2 | Competitive, high volume |
| Grain | 1.8–2.5 | Moderately competitive |
| Chemicals | 2.0–3.0 | Mixed competitiveness |
| Stone/clay/glass (cement) | 2.2–3.5 | Often captive |
| Petroleum | 1.8–2.8 | Pipeline-competitive |

### 4.3 Cost Output Metrics

For each route calculation, the model produces:

| Metric | Unit | Description |
|---|---|---|
| Total variable cost | $ | Sum of all variable cost components |
| Cost per carload | $/car | Total ÷ number of cars |
| Cost per ton | $/ton | Total ÷ cargo tonnage |
| Cost per mile | $/mile | Total ÷ route distance |
| Cost per ton-mile | $/ton-mi | Total ÷ (tons × miles) |

## 5. Analysis Capabilities

### 5.1 Corridor Analysis

The model identifies and analyses key freight corridors:
- Bottleneck segment identification (highest traffic-to-capacity ratio)
- Cost efficiency ranking (lowest cost per ton-mile corridors)
- Alternative route comparison

### 5.2 Node Criticality

Network analysis identifies critical infrastructure:
- **Betweenness centrality:** Nodes through which the most shortest paths pass
- **Degree centrality:** Most-connected junctions
- **Bridge detection:** Links whose removal would disconnect the network

### 5.3 Commodity Flow Assignment

FAF5 commodity flows are assigned to the rail network:
- O-D pairs mapped to nearest rail nodes
- Flows routed via shortest path
- Segment-level traffic volumes aggregated

## 6. Validation

### 6.1 Rate Validation

Model cost estimates are validated against:
- Published waybill revenue data (R/VC analysis)
- Railroad tariff publications (where publicly available)
- Industry benchmark studies (AAR, STB annual reports)

### 6.2 Network Validation

Route distances and transit times validated against:
- Railroad operating timetables
- Published mileage guides (Official Railway Guide)
- Google Maps rail routing (directional validation)

## 7. Limitations

1. **URCS approximation:** Published URCS unit costs are system averages; actual railroad-specific costs may differ by 15–30%
2. **Network currency:** NTAD data may lag actual track construction/abandonment by 1–2 years
3. **Interchange costs:** Switching charges are estimated; actual charges vary by terminal and railroad
4. **Capacity constraints:** The model does not account for real-time congestion or capacity limits
5. **Short line railroads:** Coverage of Class II/III railroads may be incomplete
6. **Tariff rates:** Published tariff rates are not modelled; the model estimates variable costs which represent the floor for rate negotiations

## 8. References

1. Surface Transportation Board. *Uniform Rail Costing System.* Annual. https://www.stb.gov/reports-data/uniform-rail-costing-system/
2. Bureau of Transportation Statistics. *National Transportation Atlas Database.* https://data-usdot.opendata.arcgis.com/
3. Surface Transportation Board. *Public Use Waybill Sample.* Annual. https://www.stb.gov/reports-data/waybill/
4. Federal Highway Administration. *Freight Analysis Framework Version 5.* https://faf.ornl.gov/faf5/
5. Association of American Railroads. *Railroad Facts.* Annual publication.

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | William S. Davis III*
