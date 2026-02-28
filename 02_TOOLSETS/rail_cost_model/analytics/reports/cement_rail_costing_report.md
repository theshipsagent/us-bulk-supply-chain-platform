# Cement Rail Transportation Cost Analysis
## Gulf Coast Origin Markets: Houston, Tampa, and New Orleans

**Prepared by:** Rail Analytics Platform
**Date:** February 2026
**Version:** 1.0

---

## Executive Summary

This report provides a comprehensive analysis of cement rail transportation costs originating from Gulf Coast markets, with primary focus on Houston, Texas. The analysis combines STB Public Use Waybill Sample data (2018-2023), URCS (Uniform Rail Costing System) variable cost methodology, and network-based routing analysis to develop rate benchmarks and cost estimates for key cement transportation lanes.

### Key Findings

| Metric | Value |
|--------|-------|
| Total Houston Cement Shipments (2018-2023) | 175,751 carloads |
| Total Tonnage | 14.2 million tons |
| Total Revenue | $530.7 million |
| Average Revenue per Ton | $37.30 |
| Average Revenue per Carload | $3,020 |
| Primary Destinations | Dallas (57%), Lubbock (28%), California (7%) |

**R/VC Ratio Analysis:**
- Short-haul (<300 mi): 350% average R/VC, 77% above 180% threshold
- Medium-haul (300-600 mi): 175% average R/VC, 16% above threshold
- Long-haul (>1000 mi): 92% average R/VC, 1% above threshold

**Conclusion:** Houston cement enjoys significant pricing power on short-haul Texas lanes due to limited modal competition and captive markets. Long-haul lanes to California operate near or below URCS variable cost recovery, suggesting competitive pressure from alternative sources.

---

## 1. Introduction and Scope

### 1.1 Purpose
This analysis provides rail transportation cost benchmarks for cement (STCC 32 - Stone, Clay, Glass, and Concrete Products) originating from Gulf Coast production facilities. The report supports:
- Rate negotiation and benchmarking
- Transportation procurement decisions
- Regulatory analysis (STB jurisdiction thresholds)
- Supply chain optimization

### 1.2 Geographic Scope
The analysis focuses on three Gulf Coast origin markets:

| Origin | BEA Code | Coordinates | Primary Railroad |
|--------|----------|-------------|------------------|
| Houston, TX | 134 | 29.76°N, 95.37°W | Union Pacific, BNSF |
| Tampa, FL | 042 | 27.95°N, 82.46°W | CSX |
| New Orleans, LA | 087 | 29.95°N, 90.07°W | UP, NS, CN, CSX |

**Note:** The STB Public Use Waybill Sample contains significant cement origination data only for Houston. Tampa and New Orleans appear primarily as cement destinations rather than origins in the sampled data, likely reflecting the concentration of cement manufacturing in Texas.

### 1.3 Commodity Classification
- **STCC 32:** Stone, Clay, Glass, and Concrete Products
- **STCC 324:** Hydraulic Cement
- **STCC 32411:** Portland Cement (primary focus)

---

## 2. Data Sources and Methodology

### 2.1 Primary Data Sources

| Source | Description | Coverage |
|--------|-------------|----------|
| STB Public Use Waybill Sample | Stratified sample of rail waybills | 2018-2023 |
| BTS NTAD Rail Network | North American rail nodes and lines | 2024 |
| URCS Phase III Costing | STB variable cost coefficients | 2023 |
| BEA Economic Areas | Geographic zone definitions | 172 zones |

### 2.2 Waybill Sample Methodology

The STB Public Use Waybill Sample is a stratified random sample of approximately 2-3% of all rail carload waybills. Key characteristics:

- **Expansion Factor:** Each sampled record includes an expansion factor to estimate universe totals
- **Geographic Masking:** Origin and destination reported at BEA Economic Area level (not specific stations)
- **Revenue:** Actual freight revenue as billed
- **Tonnage:** Reported actual weight

**Sample Statistics (Cement, Houston Origin):**
- Total sample records: 3,974
- Expanded carloads: 175,751
- Expansion factor range: 30-60x

### 2.3 Network Routing Methodology

Rail distances are calculated using two methods:

**Method 1: Haversine Distance (Straight-Line)**
$$d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\phi_2-\phi_1}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\lambda_2-\lambda_1}{2}\right)}\right)$$

Where:
- $r$ = Earth radius (3,959 miles)
- $\phi$ = latitude in radians
- $\lambda$ = longitude in radians

**Method 2: Network Routing (Actual Rail Miles)**

The BTS NTAD rail network contains:
- 197,485 nodes (junction points)
- 235,654 edges (track segments)
- 132,602 mainline miles

Dijkstra's shortest path algorithm calculates actual rail routing with:
- Mainline preference weighting
- Interchange detection (Class I carrier transitions)
- Circuity factor calculation

**Circuity Factor:** Ratio of actual rail miles to straight-line distance
- Typical range: 1.10 - 1.35
- Houston lanes average: 1.18

### 2.4 URCS Variable Cost Methodology

The Uniform Rail Costing System (URCS) is the STB's approved methodology for calculating rail variable costs. This analysis uses URCS Phase III coefficients:

**Variable Cost Components:**

| Cost Element | 2023 Coefficient | Unit |
|--------------|------------------|------|
| Gross Ton-Mile (GTM) | $0.048 | per GTM |
| Car-Mile | $0.140 | per car-mile |
| Switch Move | $8.50 | per car |
| Interchange | $5.00 | per interchange |

**Regional Adjustment Factors:**
- Eastern Region (FRA Districts 1-4): 1.18x
- Western Region (FRA Districts 5-8): 0.94x
- Cross-Region: 1.08x

**URCS Variable Cost Formula:**
$$VC = (GTM_{cost} \times Miles \times Tons) + (CM_{cost} \times Miles \times Cars) + (Switch \times Cars \times 2) + (IX_{cost} \times Interchanges \times Cars)$$

### 2.5 R/VC Ratio Calculation

The Revenue-to-Variable-Cost (R/VC) ratio is calculated as:

$$R/VC = \frac{Freight Revenue}{URCS Variable Cost} \times 100\%$$

**Regulatory Significance:**
- R/VC > 180%: Potentially subject to STB rate jurisdiction
- R/VC < 180%: Not subject to STB rate reasonableness review
- R/VC < 100%: Revenue does not cover variable costs (below marginal cost)

---

## 3. Houston Cement Market Analysis

### 3.1 Market Overview

Houston is a major cement production and distribution hub, with several large cement plants in the region including:
- Texas Industries (TXI) facilities
- Cemex plants
- Holcim/Lafarge operations
- Martin Marietta facilities

The Port of Houston also serves as an import point for cement from Mexico and other international sources.

### 3.2 Volume and Revenue Summary (2018-2023)

| Year | Carloads | Tons | Revenue ($M) | $/Ton |
|------|----------|------|--------------|-------|
| 2018 | 22,664 | 1,547,060 | $60.28 | $38.96 |
| 2019 | 24,440 | 1,796,114 | $70.48 | $39.24 |
| 2020 | 22,001 | 1,567,653 | $61.70 | $39.36 |
| 2021 | 19,087 | 1,705,128 | $59.12 | $34.67 |
| 2022 | 20,107 | 2,025,657 | $75.20 | $37.12 |
| 2023 | 16,298 | 1,691,201 | $55.20 | $32.64 |

**Observations:**
- Volume peaked in 2019 (pre-COVID)
- 2020-2021 COVID impact visible
- 2022 recovery with highest tonnage
- 2023 shows volume and rate softening

### 3.3 Primary Destination Markets

| Destination | Carloads | Tons | % of Total | Avg Miles | $/Ton |
|-------------|----------|------|------------|-----------|-------|
| Dallas, TX | 99,078 | 8,378,635 | 58.9% | 289 | $26.91 |
| Lubbock, TX | 48,393 | 3,531,643 | 24.8% | 309 | $43.34 |
| Fresno, CA | 8,310 | 603,255 | 4.2% | 1,486 | $79.47 |
| Los Angeles, CA | 1,370 | 156,245 | 1.1% | 1,894 | $91.65 |
| San Francisco, CA | 985 | 112,035 | 0.8% | 2,019 | $63.35 |
| Salt Lake City, UT | 980 | 107,315 | 0.8% | 1,324 | $67.45 |
| San Antonio, TX | 900 | 92,700 | 0.7% | 470 | $47.57 |

**Key Insights:**
- 84% of Houston cement moves within Texas (Dallas + Lubbock)
- California markets command premium rates but represent only 6% of volume
- Short-haul Texas lanes average $30-45/ton
- Long-haul California lanes average $65-95/ton

---

## 4. Pricing Structure Analysis

### 4.1 Distance-Based Pricing

| Distance Band | Shipments | Carloads | Avg Miles | $/Ton | $/Car |
|---------------|-----------|----------|-----------|-------|-------|
| Under 200 mi | 600 | 57,738 | 174 | $24.50 | $2,084 |
| 200-400 mi | 1,719 | 95,523 | 318 | $36.41 | $2,903 |
| 400-600 mi | 86 | 3,670 | 508 | $50.32 | $5,225 |
| 600-800 mi | 77 | 460 | 731 | $53.56 | $5,583 |
| 800-1000 mi | 41 | 255 | 899 | $56.93 | $6,164 |
| Over 1000 mi | 1,448 | 17,985 | 1,647 | $88.40 | $6,099 |

### 4.2 Rate Taper Analysis

The rate per ton-mile decreases with distance, reflecting economies of length of haul:

| Distance | Rate/Ton | Rate/Ton-Mile | Taper Index |
|----------|----------|---------------|-------------|
| 174 mi (short) | $24.50 | $0.141 | 1.00 (base) |
| 318 mi | $36.41 | $0.115 | 0.81 |
| 508 mi | $50.32 | $0.099 | 0.70 |
| 731 mi | $53.56 | $0.073 | 0.52 |
| 1,647 mi (long) | $88.40 | $0.054 | 0.38 |

**Taper Formula (Regression Estimate):**
$$Rate/TonMile = 0.141 \times Miles^{-0.25}$$

### 4.3 Price Distribution

| Percentile | $/Ton |
|------------|-------|
| 10th | $21.01 |
| 25th | $32.13 |
| Median (50th) | $49.75 |
| 75th | $82.25 |
| 90th | $106.87 |

---

## 5. URCS Cost Analysis

### 5.1 Variable Cost by Distance Band

| Distance Band | Actual $/Ton | URCS Cost/Ton | R/VC Ratio | % Above 180% |
|---------------|--------------|---------------|------------|--------------|
| Short (<300 mi) | $27.18 | $14.41 | 350% | 77% |
| Medium (300-600 mi) | $43.25 | $28.44 | 175% | 16% |
| Long (>1000 mi) | $80.25 | $90.21 | 92% | 1% |

### 5.2 Interpretation

**Short-Haul Lanes (Under 300 miles):**
- R/VC ratio of 350% indicates significant pricing power
- 77% of shipments exceed the 180% STB jurisdiction threshold
- Reflects captive shipper dynamics and limited modal alternatives
- Terminal costs represent a larger share of total cost

**Medium-Haul Lanes (300-600 miles):**
- R/VC ratio of 175% near the regulatory threshold
- Only 16% of shipments subject to potential STB review
- More competitive market structure

**Long-Haul Lanes (Over 1000 miles):**
- R/VC ratio of 92% indicates revenue below variable cost
- Suggests competitive pressure from alternative cement sources
- California markets may receive cement from local plants or imports
- Railroads may be pricing to capture contribution over marginal cost

### 5.3 Lane-Specific R/VC Analysis

| Lane | Carloads | Miles | $/Ton | URCS Cost | R/VC |
|------|----------|-------|-------|-----------|------|
| Houston → Dallas | 99,068 | 281 | $26.91 | $7.70 | 350% |
| Houston → Lubbock | 48,393 | 579 | $43.34 | $25.00 | 173% |
| Houston → San Antonio | 900 | 236 | $47.57 | $12.25 | 388% |
| Houston → LA | 1,370 | 1,714 | $91.65 | $80.28 | 114% |
| Houston → Fresno | 8,300 | 1,858 | $79.32 | $89.00 | 89% |
| Houston → Jacksonville | 310 | 1,026 | $118.28 | $51.19 | 231% |

---

## 6. Network Route Analysis

### 6.1 Rail Routing from Houston

| Destination | Rail Miles | Haversine | Circuity | Primary Carriers | Interchanges |
|-------------|------------|-----------|----------|------------------|--------------|
| Dallas, TX | 243 | 225 | 1.09 | UP, BNSF | 2 |
| Lubbock, TX | 535 | 464 | 1.16 | UP, BNSF | 1 |
| San Antonio, TX | 214 | 189 | 1.14 | UP | 0 |
| Los Angeles, CA | 1,624 | 1,371 | 1.19 | UP | 0 |
| Phoenix, AZ | 1,242 | 1,014 | 1.23 | UP | 0 |
| Salt Lake City, UT | 1,595 | 1,199 | 1.33 | UP, BNSF | 10 |
| Denver, CO | 1,028 | 878 | 1.17 | UP, BNSF | 8 |
| Kansas City, MO | 734 | 647 | 1.14 | UP, BNSF | 4 |
| Memphis, TN | 556 | 484 | 1.15 | UP, CPKC | 5 |
| Atlanta, GA | 845 | 701 | 1.21 | UP, CSX | 8 |

### 6.2 Carrier Analysis

**Western Lanes (UP/BNSF Territory):**
- Houston to California: Single-line UP via Sunset Route
- Houston to Denver: UP primary, BNSF alternative via Fort Worth
- Minimal interchanges, efficient routing

**Eastern Lanes (Cross-Gateway):**
- Houston to Atlanta: Requires UP→CSX interchange at New Orleans
- Houston to Memphis: UP→NS or CPKC alternatives
- Multiple interchanges add cost and transit time

### 6.3 Mainline Utilization

All major Houston cement lanes utilize 99-100% mainline track, reflecting:
- Cement moves on primary PSR (Precision Scheduled Railroading) corridors
- Unit train operations on dedicated routes
- Limited branch line or industrial switching

---

## 7. Rate Estimation Model

### 7.1 Model Components

The rate estimation model incorporates five adjustment factors:

**1. Base Rate (Commodity-Specific):**
$$BaseRate = 0.045 \text{ ($/ton-mile for cement)}$$

**2. Distance Taper:**
| Distance | Taper Factor |
|----------|--------------|
| <300 mi | 1.45 |
| 300-500 mi | 1.20 |
| 500-800 mi | 1.05 |
| 800-1200 mi | 0.92 |
| 1200-1800 mi | 0.85 |
| >1800 mi | 0.78 |

**3. Regional Factor:**
| Route Type | Factor |
|------------|--------|
| East-East | 1.18 |
| West-West | 0.94 |
| Cross-Region | 1.08 |

**4. Interchange Factor:**
$$InterchangeFactor = 1 + (0.03 \times NumberOfInterchanges)$$

**5. Competition Factor:**
| Carrier Options | Factor |
|-----------------|--------|
| Single Class I | 1.18 |
| Two Class I | 1.00 |
| Three+ Class I | 0.88 |

### 7.2 Complete Rate Formula

$$Rate/Ton = BaseRate \times Miles \times Taper \times Region \times Interchange \times Competition$$

### 7.3 Model Validation

| Lane | Model Estimate | Actual Rate | Variance |
|------|----------------|-------------|----------|
| Houston → Dallas | $15.08 | $26.91 | -44% |
| Houston → Lubbock | $23.28 | $43.34 | -46% |
| Houston → LA | $65.50 | $91.65 | -29% |
| Houston → San Antonio | $14.83 | $47.57 | -69% |

**Note:** Model estimates are below actual rates, suggesting:
- Market pricing exceeds cost-based estimates
- Contract premiums for service reliability
- Capacity constraints create pricing power
- Fuel surcharges and accessorials not fully captured

---

## 8. Conclusions and Recommendations

### 8.1 Market Structure

1. **Houston dominates Gulf Coast cement rail origination** with 175,000+ carloads annually
2. **Texas intrastate lanes** (Dallas, Lubbock) capture 85% of volume
3. **California lanes** command premium rates but limited volume
4. **No significant rail cement origination** from Tampa or New Orleans in sample data

### 8.2 Pricing Dynamics

1. **Short-haul captive markets** (Houston→Dallas, Houston→San Antonio) exhibit R/VC ratios of 350-400%, indicating significant railroad pricing power
2. **Medium-haul lanes** operate near the 180% STB threshold
3. **Long-haul competitive lanes** to California operate at or below URCS variable cost, suggesting alternative supply competition

### 8.3 Cost Drivers

1. **Distance** is the primary cost driver with clear taper pattern
2. **Interchanges** add approximately 3% per carrier transition
3. **Regional factors** (East vs West) create 25% cost differential
4. **Terminal costs** dominate short-haul economics

### 8.4 Recommendations

**For Shippers:**
- Negotiate aggressively on short-haul Texas lanes where R/VC exceeds 300%
- Consider alternative sourcing for California destinations
- Evaluate truck competition on sub-300 mile lanes

**For Railroads:**
- Pricing power exists on captive short-haul lanes
- Long-haul California business is margin-challenged
- Focus on service reliability to justify premiums

---

## Annex A: URCS Cost Formulas

### A.1 Gross Ton-Mile Cost
$$GTM_{cost} = 0.048 \times Miles \times (Tons + TareWeight)$$

Where TareWeight ≈ 30 tons for covered hopper cars

### A.2 Car-Mile Cost
$$CM_{cost} = 0.140 \times Miles \times Carloads$$

### A.3 Switching Cost
$$Switch_{cost} = 8.50 \times Carloads \times 2$$

(Origin and destination switching)

### A.4 Interchange Cost
$$IX_{cost} = 5.00 \times Interchanges \times Carloads$$

### A.5 Total Variable Cost
$$VC_{total} = (GTM_{cost} + CM_{cost} + Switch_{cost} + IX_{cost}) \times RegionalFactor$$

### A.6 Regional Factors
- Eastern (FRA Districts 1-4): 1.18
- Western (FRA Districts 5-8): 0.94

---

## Annex B: Data Tables

### B.1 Complete Lane Data (Houston Origin)

| Destination | Carloads | Tons | Revenue | $/Ton | $/Car | Miles | R/VC |
|-------------|----------|------|---------|-------|-------|-------|------|
| Dallas, TX | 99,068 | 8,378,635 | $225.5M | $26.91 | $2,276 | 281 | 350% |
| Lubbock, TX | 48,393 | 3,531,643 | $153.1M | $43.34 | $3,163 | 579 | 173% |
| Fresno, CA | 8,300 | 603,255 | $47.9M | $79.32 | $5,765 | 1,858 | 89% |
| Los Angeles, CA | 1,370 | 156,245 | $14.3M | $91.65 | $10,452 | 1,714 | 114% |
| San Francisco, CA | 985 | 112,035 | $7.1M | $63.35 | $7,205 | 2,053 | 62% |
| Salt Lake City, UT | 980 | 107,315 | $7.2M | $67.45 | $7,386 | 1,499 | 93% |
| San Antonio, TX | 900 | 92,700 | $4.4M | $47.57 | $4,900 | 236 | 388% |
| Sacramento, CA | 420 | 47,270 | $4.4M | $93.89 | $10,567 | 2,007 | 97% |
| Jacksonville, FL | 310 | 31,000 | $3.7M | $118.28 | $11,828 | 1,026 | 232% |
| New Orleans, LA | 295 | 31,135 | $1.1M | $33.94 | $3,582 | 397 | 172% |

### B.2 Annual Summary

| Year | Carloads | Tons | Revenue ($M) | $/Ton | $/Car |
|------|----------|------|--------------|-------|-------|
| 2018 | 22,664 | 1,547,060 | $60.28 | $38.96 | $2,660 |
| 2019 | 24,440 | 1,796,114 | $70.48 | $39.24 | $2,884 |
| 2020 | 22,001 | 1,567,653 | $61.70 | $39.36 | $2,804 |
| 2021 | 19,087 | 1,705,128 | $59.12 | $34.67 | $3,097 |
| 2022 | 20,107 | 2,025,657 | $75.20 | $37.12 | $3,740 |
| 2023 | 16,298 | 1,691,201 | $55.20 | $32.64 | $3,387 |

---

## Annex C: Methodology References

### C.1 Data Sources

1. **Surface Transportation Board (STB)**
   - Public Use Waybill Sample: https://www.stb.gov/reports-data/waybill/
   - URCS Costing Methodology: https://www.stb.gov/reports-data/uniform-rail-costing-system/

2. **Bureau of Transportation Statistics (BTS)**
   - National Transportation Atlas Database (NTAD)
   - North American Rail Network: https://geodata.bts.gov/

3. **Bureau of Economic Analysis (BEA)**
   - BEA Economic Areas: https://www.bea.gov/

### C.2 Rail Network Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Total US Nodes | 197,485 | NTAD 2024 |
| Total US Edges | 235,654 | NTAD 2024 |
| Mainline Miles | 132,602 | NTAD 2024 |
| Class I Carriers | 6 | AAR |

### C.3 Model Assumptions

1. Covered hopper car capacity: 100 tons (net)
2. Car tare weight: 30 tons
3. Average switching moves: 2 per car
4. Base year for URCS coefficients: 2023

---

## Annex D: Glossary

| Term | Definition |
|------|------------|
| BEA | Bureau of Economic Analysis Economic Area |
| Carload | Single railcar shipment |
| Circuity | Ratio of rail miles to straight-line distance |
| GTM | Gross Ton-Mile |
| PSR | Precision Scheduled Railroading |
| R/VC Ratio | Revenue to Variable Cost ratio |
| STCC | Standard Transportation Commodity Code |
| STB | Surface Transportation Board |
| Taper | Decrease in rate per mile as distance increases |
| URCS | Uniform Rail Costing System |

---

*Report generated by Rail Analytics Platform*
*Data current through December 2023*
