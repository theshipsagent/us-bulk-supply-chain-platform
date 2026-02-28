# Comprehensive Research Compendium: US Inland River Barge Transportation Economics

## Document Overview
This compendium synthesizes academic research, dissertations, white papers, and datasets on inland waterway transportation econometrics, focusing on the Mississippi River system. Organized by research type with direct access links, mathematical formulations, and data sources.

**Last Updated:** January 2026  
**Coverage:** 2003-2025 research horizon  
**Primary Focus:** Barge freight rates, modal competition, disruption economics, spatial analysis

---

## PART I: KEY DISSERTATIONS & THESES

### 1. **Econometric Modeling of Barge-Freight Rates on the Mississippi River**

**Author:** Brian M. Wetzstein  
**Institution:** Purdue University  
**Degree:** M.S. in Agricultural Economics  
**Year:** 2015  
**Dissertation ID:** AAI1603138  
**Access Link:** https://docs.lib.purdue.edu/dissertations/AAI1603138/

#### Key Methodologies:
- **Models Developed:** 4 models (2 Vector Autoregressive, 2 Spatial Vector Autoregressive)
- **Data Period:** January 2003 - June 2014 (594 weekly observations)
- **River Segments:** 5 (Illinois River, Upper Ohio, Lower Ohio, Lower Mississippi, St. Louis segment)
- **Dependent Variable:** Barge freight rates ($/ton)
- **Forecast Horizon:** 1-, 2-, and 5-week ahead predictions

#### Major Findings:
- **Forecast Savings:** $1 million+ over 2-year period with 5-week forecast horizon
- **Draft Depth Elasticity:** Significantly larger magnitude than lock delay elasticity
- **Channel Depth Impact:** Estimated cost to increase channel depth by 1 foot; calculated corresponding transportation cost savings
- **Spatial Interdependence:** Significant interaction among river segments

#### Exogenous Variables Analyzed:
- Water levels and discharge
- Lock delays
- River draft depth
- Commodity price indices
- Fuel prices
- Seasonal factors
- Barge fleet utilization

---

### 2. **Barge Prioritization, Assignment, and Scheduling During Inland Waterway Disruption Responses**

**Author:** Liliana Delgado-Hidalgo  
**Institution:** University of Arkansas, Fayetteville  
**Degree:** PhD in Industrial Engineering  
**Year:** 2018  
**Access Link:** https://scholarworks.uark.edu/etd/2852/

#### Problem Statement:
Develops optimization models for redirecting disrupted barges to inland terminals while minimizing cargo value loss during infrastructure disruptions.

#### Three Optimization Approaches:
1. **Decomposition-Based Sequential Heuristic (DBSH)**
   - Integrates Analytic Hierarchy Process with linear programming
   - Subproblem decomposition: cargo prioritization → assignment → scheduling
   - Validates quality compared to genetic algorithm solutions

2. **Mixed Integer Linear Programming (MILP')**
   - Adds valid inequalities to standard formulation
   - Uses lower bounds to validate all prior solutions
   - Outperforms genetic algorithm approaches

3. **Branch-and-Price (Dantzig-Wolfe Decomposition)**
   - Exact method for larger instances
   - Scales to: 10 terminals × 30 barges (vs. prior 5 terminals × 9 barges)
   - Polynomial computational time for realistic scenarios

#### Applications:
- Natural and man-made disruption response planning
- Terminal allocation optimization
- Cargo prioritization by value density

---

### 3. **Economic Consequences of Inland Waterway Disruptions in the Upper Mississippi River Region in a Changing Climate**

**Publication:** The Annals of Regional Science, 2024  
**Research Type:** Spatial econometric + CGE modeling integration

#### Methodology:
- **Data Source:** USDA Grain Transportation Report (2013-2021, weekly)
- **Spatial Approach:** Spatial econometric modeling capturing inter-lock dependencies
- **Economic Impact:** Multi-regional computable general equilibrium (CGE) models
- **Variables:** Barge rates, tonnage, weather, water levels, lock disruptions

#### Key Data Inputs:
- Weekly total barge grain movement (1,000 tons) by lock/dam
- Weekly freight rates ($/ton to New Orleans)
- Daily temperature and precipitation (NOAA)
- River gage height and discharge
- Scheduled and unscheduled lock disruption events

---

## PART II: PEER-REVIEWED PUBLICATIONS

### Primary Research Papers by Wetzstein et al.

#### **Transportation Costs: Mississippi River Barge Rates (2021)**

**Authors:** Brian Wetzstein, Raymond Florax, Kenneth Foster, James Binkley  
**Journal:** Journal of Commodity Markets, Vol. 21(C)  
**DOI:** 10.1016/j.jcomm.2019.100123  
**REPEC Handle:** RePEc:eee:jocoma:v:21:y:2021:i:c:s2405851319300881

**Abstract Summary:**
- Develops spatial vector autoregressive (SpVAR) forecasting models
- Forecasts barge rates outperform naïve models on multiple comparison metrics
- **Out-of-sample Results:** 17-29% savings on transportation costs depending on segment
- Variables: commodity prices, water levels, lock utilization, fuel costs

---

#### **Rejuvenating Mississippi River's Post-Harvest Shipping (2019)**

**Authors:** Brian Wetzstein, Raymond Florax, Kenneth Foster, James Binkley  
**Journal:** Applied Economic Perspectives and Policy, Vol. 41(4), pp. 723-741  
**Published:** December 2019  
**JSTOR Link:** https://www.jstor.org/stable/48628604

**Presentation Version:** 2016 Annual Meeting, Agricultural and Applied Economics Association

---

### Related Research on Modal Demand & Elasticities

#### **The Measurement of Grain Barge Demand on Inland Waterways**

**Author(s):** Tun-Hsiang (Edward) Yu et al.  
**Focus:** Direct and cross-elasticity estimates (rail, road, inland waterways)
**Methodology:** Simultaneous equation econometric system
**Access:** ResearchGate (available as PDF)

#### **Impacts of Inland Waterway User Fees on Grain Transportation and Implied Barge Rate Elasticities**

**Institutional Source:** University of Illinois Agricultural Economics  
**Fingerprint URL:** https://experts.illinois.edu/en/publications/impacts-of-inland-waterway-user-fees-on-grain-transportation-and-/fingerprints/

---

## PART III: MATHEMATICAL FORMULATIONS & ECONOMETRIC MODELS

### A. Vector Autoregressive (VAR) Models for Barge Rates

#### Standard VAR Specification (Wetzstein et al.):
```
R_t = A_0 + Σ(A_i * R_{t-i}) + ε_t

Where:
R_t = vector of barge rates in 5 river segments (at time t)
A_0 = constant vector
A_i = lag coefficient matrix (dimension: 5×5)
ε_t = error terms
Σ = summation over lag length (typically 4-6 weeks)
```

#### Spatial Vector Autoregressive (SpVAR) Specification:
```
R_t = A_0 + Σ(A_i * R_{t-i}) + ρ(W ⊗ R_t) + X_t*β + ε_t

Where:
ρ = spatial autoregressive coefficient
W = 5×5 spatial weight matrix (inverse distance or nearest neighbor)
⊗ = Kronecker product
X_t = exogenous variables (lock delays, water levels, fuel prices)
β = coefficients on exogenous variables
```

#### Spatial Weight Matrix Example (Inverse Distance):
```
W_ij = 1/d_ij^φ  (for i≠j)
W_ii = 0
where d_ij = river distance between segments i and j
      φ = distance decay parameter (typically 1 or 2)
```

**Normalization:** Row-standardize W so each row sums to 1

#### Forecast Evaluation Metrics Used:
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Theil U-statistic
- Directional accuracy tests
- Diebold-Mariano tests (statistical significance of forecast improvement)

---

### B. Basic Barge Rate Calculation Formula (Industry Standard)

#### Percent-of-Tariff System (Historical Basis: 1976 ICC Tariff No. 7):
```
Barge Rate ($/ton) = (Rate Percentage × 1976 Benchmark Rate) / 100

Benchmark Rates by River Segment (1976 dollars):
├─ Twin Cities (Minneapolis area): $6.19/ton
├─ Mid-Mississippi (IA-IL border): $5.32/ton
├─ St. Louis segment: $3.99/ton
├─ Illinois River: $4.64/ton
├─ Cincinnati (Middle Ohio): $4.69/ton
├─ Lower Ohio River: $4.46/ton
└─ Cairo-Memphis: $3.14/ton

Example Calculation:
If spot rate = 300% at St. Louis
Cost = (300 × $3.99) / 100 = $11.97/ton
```

**Note:** While deregulated in 1976, industry continues using these benchmarks for rate quotation and comparison purposes.

---

### C. Basic Cost Minimization Formula for Barge Operators

#### Total Cost per Barge Movement:
```
TC = (FixedCost + DayCost + FuelCost + PortCost + LaborCost) / Tons

Where:
FixedCost = equipment amortization, insurance
DayCost = daily towboat + barge rental
FuelCost = fuel burn rate (gal/day) × fuel price ($/gal) × days
PortCost = loading/unloading, demurrage
LaborCost = crew wages + benefits
Tons = cargo tonnage (capacity-limited)
```

#### Simplified Unit Rate Formula:
```
BR = TC / W (as shown in baseline rate formula)

Where:
BR = Barge Rate ($/ton-mile or $/ton)
TC = Total Cost
W = Weight in tons

Capacity-constrained barge typically carries 1,500 tons (dry bulk)
```

---

### D. Lock Delay Cost Quantification

#### Lock Transit Time Components:
```
Total Lock Time = Queuing Time + Processing Time + Lockage Time

Typical 600-ft lock:
├─ Processing: 15-20 minutes
├─ Lockage (fill/empty): 10-15 minutes
└─ 15-barge tow: 2.5-3.5 hours total

Cost per hour delay = (Fuel burn × Fuel Price) + (Daily Labor Cost / 24)
Typical: $200-500/hour depending on fuel prices
```

#### Delay Elasticity Estimates (from Wetzstein research):
- Lock delay elasticity on barge rates: 0.15-0.35
- Meaning: 1% increase in lock delays → 0.15-0.35% increase in rates
- **Less elastic than draft depth effects** (elasticity: 0.40-0.60)

---

### E. Transportation Mode Substitution Model

#### Modal Choice Framework:
```
Demand(Mode_i) = f(Rate_i, Rate_j, Capacity_i, Quality_i, Distance, Commodity)

Cross-elasticity examples:
├─ Barge-to-Rail: 0.3-0.6 (10% barge rate ↑ → 3-6% shift to rail)
├─ Barge-to-Truck: 0.1-0.3 (for long-haul; truck not competitive)
└─ Rail-to-Barge: 0.5-0.8 (more elastic, barge offers major savings)

Distance threshold for barge competitiveness: typically > 300 miles
```

---

## PART IV: HISTORICAL DATA & BENCHMARKS

### A. Barge Rate Time Series (2003-2025)

#### Recent Historical Rates (Sample Data):

| Year | St. Louis ($/ton) | Mid-Mississippi | Illinois River | Status |
|------|-------------------|-----------------|-----------------|---------|
| 2019 | $18-22 | $20-25 | $22-28 | Normal operations |
| 2020 | $15-18 | $18-22 | $20-25 | COVID disruption |
| 2021 | $12-15 | $14-18 | $16-20 | Low water constraints |
| 2022 | $88-106 | $95-115 | $100-125 | Severe drought (peak) |
| 2023 | $16-25 | $18-28 | $20-35 | Recovery period |
| 2024-25 | $18-30 | $20-32 | $22-40 | Normal-elevated |

**Data Source:** USDA Agricultural Marketing Service Grain Transportation Report (weekly)

---

### B. Tonnage Volume Data

#### 2023 Mississippi River System Tonnage (USACE):
```
Total Internal: 449 million short tons
├─ Petroleum & products: 135.5 million st (30.2%)
├─ Chemicals: 48.0 million st (10.7%)
├─ Food & farm products: 73.3 million st (16.3%)
├─ Coal: (declining, shift to natural gas)
├─ Metals & minerals: 50+ million st
└─ Other: remainder

Ton-Mile Data (2022):
└─ Mississippi River: 148 billion ton-miles
   ├─ Ohio River: 46.8 billion ton-miles
   └─ Illinois River: 18.0 billion ton-miles
```

**Historical Trend:** 622 million st (2007) → 449 million st (2023) - **28% decline**

---

### C. Fleet Characteristics (2006-present, per USACE)

```
Total Barge Fleet: ~22,000+ units
├─ Covered barges (grain): 13,062 units
│  └─ 36% aged 25+ years (average useful life: 25-30 years)
├─ Open barges (coal): 8,673 units
└─ Tank barges (liquids): 4,250 units

Standard Tow Configuration:
├─ Mississippi with locks: 15 barges (3 wide × 5 long)
├─ Lower Mississippi (no locks): 30-40 barges per towboat
└─ Grain barge specs:
   ├─ Length: 195-200 feet
   ├─ Width: 35 feet
   ├─ Draft: 9 feet (normal), 6-9 feet (drought-constrained)
   └─ Capacity: 1,500 tons average; 15 barges = 22,500 tons

Equivalent Modal Capacity:
├─ 1 barge tow = 1,050 trucks OR 216 rail cars + 6 locomotives
└─ Annual truck equivalent: 58 million truck trips replaced by waterway
```

---

## PART V: GOVERNMENT & ACADEMIC DATA SOURCES

### A. USACE Waterborne Commerce Data

**Waterborne Commerce of the United States (WCUS) Annual Report**
- **Published by:** Institute for Water Resources, USACE Navigation & Civil Works Decision Support Center
- **Access:** https://www.iwr.usace.army.mil/About/Technical-Centers/NDC-Navigation-and-Civil-Works-Decision-Support/
- **Data:** Vessel movements, tonnage by commodity, origin/destination, lock operations
- **Frequency:** Monthly vessel operating reports aggregated annually
- **Format:** CSV, Excel, PDF

**Waterborne Commerce Statistics Center (WCSC)**
- **Location:** New Orleans
- **Data Collection:** ENG Forms 3925, 3925b (Vessel Operating Reports)
- **Portal:** https://usace.contentdm.oclc.org/digital/collection/p16021coll2/

---

### B. USDA Agricultural Marketing Service (AMS)

**Grain Transportation Report (Weekly)**
- **Access:** https://www.ams.usda.gov/services/transportation-analysis/grain-transport
- **Data Elements:**
  - Barge rates (7 river segments)
  - Truck, rail rates
  - Barge movement data (tons)
  - Lock performance
  - Railcar bids/offers
  - Export prices
- **Format:** Excel, PDF, Dashboard
- **Update Frequency:** Weekly (Thursdays)

**Barge Dashboard**
- **Access:** https://agtransport.usda.gov/stories/s/Barge-Dashboard/965a-yzgy/
- **Real-time:** Weekly rates, movements, forecasts

**Downbound Grain Barge Rates Data**
- **Access:** https://agtransport.usda.gov/widgets/deqi-uken
- **Format:** Interactive dashboard + CSV export
- **Historical:** 2003-present

---

### C. Bureau of Transportation Statistics (BTS)

**Freight Analysis Framework (FAF)**
- **Version:** FAF 5.7.1 (current)
- **Download:** https://faf.ornl.gov/faf5/data/
- **Data:** Regional freight flows by mode, commodity, origin-destination
- **Format:** CSV, Access Database

**Transportation Services Index - Inland Waterborne**
- **Series:** WATERBORNE (monthly, not seasonally adjusted)
- **Access:** https://fred.stlouisfed.org/series/WATERBORNE
- **FRED Series:** WATERBORNED11 (seasonally adjusted)

**National Transportation Atlas Database (NTAD)**
- **Portal:** https://geodata.bts.gov/
- **GIS Resources:** Navigation networks, rail, ports
- **Format:** Shapefile, GeoJSON, REST API

---

### D. University of Tennessee Research

**Economic Impacts Analysis of Inland Waterway Disruption**
- **Research Leader:** Dr. Edward (Tun-Hsiang) Yu, University of Tennessee AREC
- **Reports:** Multiple studies on lock closure scenarios, modal diversion
- **Publications:** Staff reports, peer-reviewed journal articles
- **Access:** University of Tennessee Department of Agricultural and Resource Economics

**University of Tennessee Center for Transportation Research**
- **URL:** https://ctr.utk.edu/
- **Focus:** Waterway disruption, barge-rail competition analysis
- **Key Report:** "Barge Traffic Disruptions and Their Effects on Shipping Costs" (Burton, 2019)

---

### E. National Waterways Foundation Studies

**Commissioned Research on Inland Waterways Economics**
- **Portal:** https://nationalwaterwaysfoundation.org/foundation-studies/view-all-studies
- **Key Studies:**
  - Modal Comparison: Barge vs. Truck/Rail (2022 update, Texas A&M)
  - Lock Outage Economic Impact Studies
  - Non-Navigation Benefits of Waterways
  - Competitive Analysis: US vs. International Waterway Investments

---

## PART VI: MATHEMATICAL MODELING RESOURCES

### A. Spatial Econometrics References (for VAR/SpVAR implementation)

**Key Textbooks & Methodologies:**
- **Spatial Econometrics:** Anselin & Bera (key papers on spatial weight matrices)
- **Vector Autoregression:** Sims (1980) foundational VAR methodology
- **Forecasting:** Diebold & Mariano (1995) forecast comparison tests

**Software Implementations:**
- R: `spatial` package, `spatialreg`, `vars` (VAR models)
- Python: `statsmodels` (VAR), `scikit-learn` (spatial weights)
- Stata: `spregress`, `vecrank`, `varwle`
- MATLAB: Econometrics Toolbox

---

### B. Optimization Model Resources (for disruption response)

**Integer Programming Frameworks (Delgado-Hidalgo approach):**
- Dantzig-Wolfe decomposition methodology
- Branch-and-price exact algorithms
- MILP solver comparison: CPLEX, Gurobi, SCIP (open-source)

**Software:**
- GAMS (algebraic modeling language)
- AMPL (mathematical programming language)
- Python: `PuLP`, `Pyomo`

---

## PART VII: RELATED RESEARCH ON MARITIME SUPPLY CHAIN ECONOMETRICS

### A. Ocean-Going Vessel Rate Forecasting

**Translog Cost Functions for Bulk Shipping**
- **Reference:** Alizadeh & Talley (2011) "Microeconomic Determinants of Dry Bulk Shipping Freight Rates"
- **Methodology:** Flexible functional form for cost-output relationships
- **Relevance to Inland:** Cost structure concepts (labor substitutability, scale economies)

**Baltic Dry Index (BDI) Forecasting**
- **Recent Study:** "A New Exploration in Baltic Dry Index Forecasting" (Su et al., 2024)
- **Methods:** Deep ensemble learning, neural networks
- **Transferability:** Rate forecasting techniques applicable to inland barge indices

---

### B. Port Efficiency & Maritime Transport Costs

**Port-Specific Research:**
- Sánchez et al. (2003) "Port Efficiency and International Trade"
- **Key Finding:** Port efficiency elasticity ~0.20 on shipping rates
- **Application:** Inland terminal efficiency likely has similar elasticity

---

## PART VIII: POLICY & INFRASTRUCTURE REPORTS

### A. Failure to Act: Ports and Inland Waterways (ASCE 2021)

**American Society of Civil Engineers Infrastructure Report Card**
- **Inland Waterways Grade:** C+
- **Funding Gap (2020-2029):** $24.8 billion
- **Breakdown:**
  - Lock/dam modernization: ~90%
  - Dredging: ~10%
- **Trust Fund:** Inland Waterways Trust Fund (IWTF) - $0.29/gal fuel tax

---

### B. Water Resources Development Acts (WRDA)

**Recent Legislation:**
- **WRDA 2024:** Signed January 2025
  - Increased general fund contribution to inland projects (75% general, 25% IWTF)
  - Authorization for multiple USACE projects
  - Feasibility studies for future improvements

---

## PART IX: KEY METRICS & EFFICIENCY BENCHMARKS

### A. Fuel Efficiency Comparisons

```
Ton-Miles per Gallon of Fuel:
├─ Barge: 514 miles/gallon
├─ Rail: 202 miles/gallon
└─ Truck: 59 miles/gallon

Annual Savings (USDA estimate):
├─ Cost savings vs. truck: $11/ton average
├─ Aggregate: ~$6.5 billion annually
├─ Annual fuel savings: [barge tonnage × 455 miles/gal premium]
└─ CO2 reduction: 10 million metric tons annually (vs. rail alternative)
```

### B. Lock Performance Metrics

```
Typical 600-foot lock capacity:
├─ Single barge: quick pass
├─ 15-barge tow: 2.5-3.5 hours total
├─ Queue time: 30 minutes - 6+ hours (depends on traffic)

2020 Performance (recent disruption data):
├─ Average delay: 172.2 minutes
├─ Unavailability events: 9,147
├─ Scheduled: 6,361 (69%)
├─ Unscheduled: 2,786 (31%)

Cost of delay:
├─ Fuel + Labor: $200-500/hour
├─ Revenue loss: highly variable by commodity
└─ Total economic impact: $1+ billion/year (estimated) from inefficiency
```

---

## PART X: FINDING FULL TEXTS & ACCESSING PAYWALLED RESEARCH

### Open Access & Preprint Repositories

1. **ResearchGate** (https://www.researchgate.net/)
   - Authors often share published papers
   - Search: "Wetzstein barge" or specific article titles
   - Request functionality available

2. **SSRN / arXiv** (domain-specific)
   - Economic papers sometimes preprinted before journal publication
   - Spatial econometrics papers frequently preprinted

3. **Google Scholar** (https://scholar.google.com/)
   - Link to free full-text PDFs when available
   - "Cited by" functionality to find related work

4. **ProQuest Dissertations & Theses** (https://www.proquest.com/pqdtglobal)
   - University-affiliated access often free for dissertations
   - InterLibrary loan if institutional access unavailable

5. **Internet Archive Scholar** (https://archive.org/)
   - Books and some journal articles
   - Search by title or author

### University Library Access

- **If affiliated with university:** Use institutional proxy access to paywalled journals
- **If not affiliated:**
  - Contact university libraries for individual borrowing privileges
  - Request articles via RapidILL or similar interlibrary loan services
  - Email authors directly for preprints

### Paywalled Journal Access Strategy

**Journal of Commodity Markets** (Elsevier)
- Wetzstein et al. 2021 paper
- **Cost:** ~$30-40 per article via ScienceDirect
- **Alternatives:** ResearchGate author request, institutional access

**Applied Economic Perspectives and Policy** (Wiley)
- Wetzstein et al. 2019 paper
- Open access on some platforms through agricultural economics associations

---

## PART XI: RESEARCH GAPS & FUTURE DIRECTIONS

### Identified Gaps in Current Literature:

1. **Real-time Cost Modeling:** Limited models incorporating real-time vessel tracking (AIS) data
2. **Climate Adaptation:** Growing focus on low-water scenarios; more detailed flood impact models needed
3. **Intermodal Integration:** Limited research on optimal mode-switching algorithms under uncertainty
4. **Terminal Efficiency:** Sparse data on terminal-level operations impact on overall system costs
5. **Fuel Price Volatility:** Models accounting for hedging strategies and fuel surcharges not well developed
6. **Commodity-Specific Rates:** Most research aggregates across commodities; commodity-specific models limited
7. **Labor Shortages:** Impact of crew availability on rates not extensively modeled

### Future Research Opportunities:

- **AI/ML Applications:** Neural networks for non-linear rate forecasting
- **Real-time Optimization:** Dynamic programming for disruption response
- **Supply Chain Integration:** Optimization across port-rail-barge interfaces
- **Sustainability Metrics:** Carbon accounting and ESG reporting integration
- **Climate Resilience:** Scenario planning for extended drought/flood periods

---

## PART XII: COMPREHENSIVE REFERENCE LIST

### Dissertations & Theses
1. Wetzstein, B. M. (2015). "Econometric modeling of barge-freight rates on the Mississippi River." Master's thesis, Purdue University. AAI1603138.

2. Delgado-Hidalgo, L. (2018). "Barge Prioritization, Assignment, and Scheduling During Inland Waterway Disruption Responses." PhD dissertation, University of Arkansas. https://scholarworks.uark.edu/etd/2852/

### Peer-Reviewed Journal Articles
3. Wetzstein, B., Florax, R., Foster, K., & Binkley, J. (2021). "Transportation costs: Mississippi River barge rates." *Journal of Commodity Markets*, 21(C). DOI: 10.1016/j.jcomm.2019.100123

4. Wetzstein, B., Florax, R., Foster, K., & Binkley, J. (2019). "Rejuvenating Mississippi River's Post‐Harvest Shipping." *Applied Economic Perspectives and Policy*, 41(4), 723-741.

5. (2024). "Economic consequences of inland waterway disruptions in the Upper Mississippi River region in a changing climate." *The Annals of Regional Science*.

6. Alizadeh, A. H., & Talley, W. K. (2011). "Microeconomic determinants of dry bulk shipping freight rates and contract times." *Transportation*, 38(3), 561-579.

### Government & Institutional Reports
7. U.S. Army Corps of Engineers, Institute for Water Resources. (2023). *Waterborne Commerce of the United States: Annual Report*. Navigation & Civil Works Decision Support Center.

8. USDA Agricultural Marketing Service. (2024). *Grain Transportation Report*. Weekly publication.

9. American Society of Civil Engineers (ASCE). (2021). *Failure to Act: Ports and Inland Waterways – Anchoring the U.S. Economy*. Infrastructure Report Card.

10. National Waterways Foundation. (2022). *A Modal Comparison of Domestic Freight Transportation Effects on the General Public: 2001–2019*. Texas A&M Transportation Institute.

### Additional References (Partial List)
- Texas Transportation Institute. (2017). "A Modal Comparison of Domestic Freight Transportation Effects on the General Public: 2001-2014."
- University of Tennessee Center for Transportation Research. "Barge Traffic Disruptions and Their Effects on Shipping Costs."
- PwC. "Economic Contribution of the US Tugboat, Towboat, and Barge Industry."

---

## APPENDIX A: GLOSSARY OF TERMS

**Barge Tow:** Group of barges pushed together by a towboat (15 barges typical on locks-constrained Mississippi)

**Draft Depth:** Vertical distance from waterline to bottom of vessel; affects load capacity

**Lock and Dam:** Infrastructure allowing vessels to navigate around elevation changes

**LPMS:** Lock Performance Monitoring System (USACE real-time tracking)

**Percent of Tariff:** Industry convention quoting barge rates as percentage of 1976 ICC benchmark

**SpVAR:** Spatial Vector Autoregressive model incorporating geographic interdependence

**Ton-Mile:** Freight movement metric: one ton moved one mile

**Waterborne Commerce Statistics Center (WCSC):** USACE data collection and publication entity

---

## APPENDIX B: KEY ACADEMIC & GOVERNMENT CONTACTS

**Purdue University Agricultural Economics:**
- Prof. Kenneth Foster (Wetzstein dissertation advisor)
- Contact: Purdue Department of Agricultural Economics

**University of Tennessee AREC:**
- Dr. Edward (Tun-Hsiang) Yu - Leading waterway disruption researcher
- Department of Agricultural and Resource Economics

**USDA Agricultural Marketing Service:**
- Grain Transportation Report data team
- Contact: https://www.ams.usda.gov/services/transportation-analysis

**U.S. Army Corps of Engineers:**
- Institute for Water Resources (Waterborne Commerce Statistics Center)
- Contact: https://www.iwr.usace.army.mil/

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial compilation; 2003-2025 research horizon |

---

**Prepared for:** William (Freight, Commodities & Infrastructure Data Infrastructure Project)  
**Compendium Status:** Comprehensive research synthesis with direct source access links  
**Recommended Citation:** [Author]. (2026). Comprehensive Research Compendium: US Inland River Barge Transportation Economics. Accessed January 2026.

