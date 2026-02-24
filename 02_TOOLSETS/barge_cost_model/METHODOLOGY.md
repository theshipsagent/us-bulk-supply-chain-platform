# Barge Cost Model — Technical Methodology

## 1. Overview

The Barge Cost Model provides a comprehensive framework for estimating inland waterway freight costs across the US navigable waterway system. The model integrates USDA Grain Transportation Report (GTR) rate data, USACE lock performance statistics, and operational cost engineering to produce point-to-point barge freight cost estimates.

**Platform Path:** `02_TOOLSETS/barge_cost_model/`
**Primary Output:** $/ton freight cost estimates by origin-destination pair
**Key Dependencies:** NetworkX (graph routing), Pandas, Statsmodels (VAR forecasting)

## 2. Data Sources

### 2.1 USDA Grain Transportation Report (GTR)

The GTR, published weekly by USDA Agricultural Marketing Service, provides tariff rate indices for barge freight across seven Mississippi River System segments:

| Segment | Route | Coverage |
|---|---|---|
| Mid-Mississippi | St. Louis to Cairo, IL | Upper river grain corridor |
| Ohio River | Pittsburgh to Cairo, IL | Eastern coal and industrial |
| Illinois River | Chicago to Grafton, IL | Illinois Waterway grain |
| Lower Mississippi (Segment 1) | Cairo to Memphis | Upper Lower Miss |
| Lower Mississippi (Segment 2) | Memphis to Vicksburg | Mid Lower Miss |
| Lower Mississippi (Segment 3) | Vicksburg to Baton Rouge | Lower Miss industrial |
| Lower Mississippi (Segment 4) | Baton Rouge to New Orleans | Export corridor |

**Rate format:** Tariff index percentage (e.g., 300% = 3x base rate) plus $/ton spot rates
**History:** Weekly observations from 2003 to present (1,100+ data points)
**Refresh cadence:** Weekly (Friday publication)

### 2.2 USACE Lock Performance (NDC/LPMS)

The Navigation Data Center Lock Performance Monitoring System provides:
- Processing times by lock chamber
- Delay times (queue waiting)
- Number of vessels/tows processed
- Seasonal utilization patterns

**Coverage:** 192 lock sites, 239 chambers
**Key metrics used:** Average processing time, average delay time, utilization rate

### 2.3 Waterway Network Data

The model uses a graph representation of the inland waterway system:
- **Nodes:** 6,860 waterway points (mile markers, lock locations, port facilities)
- **Edges:** Navigable segments with distance, river name, and traffic attributes
- **Graph type:** NetworkX undirected graph with weighted edges

## 3. Routing Engine

### 3.1 Network Graph Construction

The waterway network is constructed from USACE waterway link data:

```
Graph G = (V, E) where:
  V = {waterway nodes: mile markers, locks, ports, junctions}
  E = {navigable segments with attributes: distance, river, direction}
```

Junction points are hardcoded for major river confluences:
- Ohio-Mississippi Confluence (Cairo, IL) — Mile 0/Mile 953
- Illinois-Mississippi Confluence (Grafton, IL)
- Missouri-Mississippi Confluence (Hartford, IL)
- Tennessee-Ohio Confluence (Paducah, KY)
- Arkansas-Mississippi Confluence
- Pittsburgh: Monongahela-Allegheny-Ohio confluence

### 3.2 Path Finding

**Primary algorithm:** Dijkstra's shortest path (distance-weighted)
**Alternative routing:** A* with haversine heuristic, K-shortest paths (up to 3 alternatives)

**Constraint checking:**
- Lock chamber width vs. tow beam (safety margin: 0.5m)
- Channel depth vs. loaded draft (safety margin: 1.5m)
- Lock availability (seasonal closures)

### 3.3 Lock Detection

For any computed route, the model identifies all locks traversed by matching route segments against the lock database (80 facilities). Each lock contributes:
- Processing time (single lockage: ~1.5 hours, double lockage: ~3.5 hours)
- Potential delay time (based on historical averages from LPMS)

## 4. Cost Components

### 4.1 Cost Structure

Total barge freight cost is decomposed into:

```
Total Cost = Fuel + Crew + Lock Fees + Terminal Fees + [Fleeting + Switching + Demurrage]
```

| Component | Calculation | Default Parameters |
|---|---|---|
| **Fuel** | gallons/day × price/gallon × transit days | 100 gal/day base, adjusted by DWT |
| **Crew** | crew size × daily rate × (transit + delay days) | 8 crew × $800/day |
| **Lock fees** | $50 per passage + delay time cost | Average 2 hrs delay per lock |
| **Terminal fees** | Flat fee per facility (origin + destination) | $750 per terminal |
| **Fleeting** | Staging and assembly charges | Varies by location |
| **Switching** | Tow reconfiguration at junctions | $2,000–5,000 per switch |
| **Demurrage** | Delay penalties beyond free time | $500–1,000/day per barge |

### 4.2 Transit Time Calculation

```
Transit Time (hours) = Distance (miles) / Speed (mph) + Σ(Lock Processing + Lock Delay)

Speed defaults:
  Downstream: 8.0 mph
  Upstream: 5.0 mph
  Average: 6.0 mph (when direction unknown)
```

### 4.3 Tow Configurations

| Configuration | Barges | Capacity (tons) | Typical Routes |
|---|---|---|---|
| 15-barge tow | 15 | 22,500 | Lower Mississippi |
| 6-barge tow | 6 | 9,000 | Ohio, Illinois rivers |
| Single barge | 1 | 1,500 | Short-haul, terminal moves |

## 5. Rate Forecasting (VAR/SpVAR)

### 5.1 Vector Autoregression (VAR) Model

The baseline forecasting model treats the 7 segment rates as a system of simultaneous equations:

```
Y(t) = A₁·Y(t-1) + A₂·Y(t-2) + ... + Aₚ·Y(t-p) + ε(t)

Where:
  Y(t) = [rate₁(t), rate₂(t), ..., rate₇(t)]' — vector of 7 segment rates
  p = lag order (optimized at 3-6 via AIC/BIC)
  ε(t) ~ N(0, Σ) — error terms
```

**Training data:** 2003–2020 (884 weekly observations)
**Validation data:** 2020–2025 (260 weekly observations)
**Forecast horizon:** 52 weeks ahead

### 5.2 Spatial VAR (SpVAR) Model

The SpVAR extends the baseline by incorporating spatial dependence through an inverse-distance weight matrix:

```
Y(t) = A₁·Y(t-1) + ... + Aₚ·Y(t-p) + ρ·W·Y(t) + ε(t)

Where:
  W = spatial weight matrix (inverse distance between segment centroids)
  ρ = spatial autoregressive parameter
```

This captures the empirical observation that adjacent waterway segments exhibit correlated rate movements (e.g., a rate spike on the Lower Mississippi propagates to the Ohio River within 2–4 weeks).

### 5.3 Forecast Performance

| Metric | Naïve | VAR | SpVAR |
|---|---|---|---|
| MAPE | Baseline | 15–22% improvement | 17–29% improvement |
| Directional accuracy | 50% | 62–68% | 65–72% |
| Economic value (2-yr) | — | ~$500K savings | ~$1M savings |

## 6. Rail Comparison

The model includes a rail cost comparison module to support modal choice analysis:

```
Rail Cost = Distance × Rail Rate ($/ton-mile) × Tons

Default rail rate: $0.04/ton-mile (adjustable by commodity and corridor)
```

The barge-vs-rail savings percentage is computed as:
```
Savings % = (Rail Cost - Barge Cost) / Rail Cost × 100
```

Typical savings range: 40–65% for bulk commodities on waterway-competitive routes.

## 7. Validation

### 7.1 Rate Validation

Model rates are validated against:
- Published USDA GTR spot rates (weekly)
- Broker quotes for specific origin-destination pairs
- Historical contract rates (where available)

### 7.2 Distance Validation

Route distances are validated against:
- USACE official river mile markers
- Published navigation charts (NOAA ENC)
- Commercial towing company route guides

### 7.3 Lock Delay Validation

Lock processing and delay estimates are validated against:
- USACE LPMS monthly reports
- NDC quarterly lock performance summaries

## 8. Limitations

1. **Rate data coverage:** GTR rates cover grain-focused segments; non-grain commodity rates may differ by 10–25%
2. **Lock delays:** Model uses historical averages; actual delays can vary significantly due to maintenance closures, high water, or ice
3. **Fleet utilization:** The model does not currently track real-time barge availability
4. **Fuel price sensitivity:** Default fuel cost is static; should be updated quarterly
5. **Terminal-specific costs:** Fleeting and switching charges vary significantly by terminal and are approximated

## 9. References

1. USDA Agricultural Marketing Service. *Grain Transportation Report.* Weekly. https://www.ams.usda.gov/services/transportation-analysis/gtr
2. USACE Navigation Data Center. *Lock Performance Monitoring System.* https://ndc.ops.usace.army.mil
3. USACE Waterborne Commerce Statistics Center. *Waterborne Commerce of the United States.* Annual. https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/
4. Hamilton, J.D. (1994). *Time Series Analysis.* Princeton University Press. (VAR methodology)
5. LeSage, J.P., and Pace, R.K. (2009). *Introduction to Spatial Econometrics.* CRC Press. (SpVAR methodology)

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | OceanDatum.ai*
