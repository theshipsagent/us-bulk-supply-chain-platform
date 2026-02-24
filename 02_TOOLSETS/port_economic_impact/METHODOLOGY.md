# Port Economic Impact Model — Technical Methodology

## 1. Overview

The Port Economic Impact Model estimates the direct, indirect, and induced economic effects of port operations on regional economies within the United States. The model applies input-output multiplier analysis — drawing on BEA RIMS II tables and IMPLAN data — to quantify how port-related expenditures ripple through local and state economies in terms of output (business revenue), employment (jobs), and earnings (personal income and tax revenue).

**Platform Path:** `02_TOOLSETS/port_economic_impact/`
**Primary Output:** Regional economic impact estimates (output, employment, earnings, tax revenue) with scenario comparison
**Key Dependencies:** Pandas, NumPy, SciPy (input-output matrix operations)

The model is composed of four integrated modules:

| Module | File | Function |
|---|---|---|
| Multiplier Engine | `multiplier_engine.py` | RIMS II / IMPLAN multiplier application and I-O matrix operations |
| Employment Model | `employment_model.py` | Direct, indirect, and induced employment estimation with wage analysis |
| Revenue Model | `revenue_model.py` | Federal, state, and local tax revenue and fiscal impact calculation |
| Scenario Builder | `scenario_builder.py` | What-if scenario construction, comparison, and sensitivity analysis |

The model is designed for US port facilities with initial calibration to Gulf Coast ports (Houston, New Orleans, Mobile, Tampa, Lake Charles, Baton Rouge). Regional parameters can be extended to Atlantic and Pacific coast facilities by substituting the appropriate RIMS II region codes and state/local tax structures.

---

## 2. Theoretical Framework

### 2.1 Economic Base Theory

Port facilities function as export-base industries: they bring external revenue into a regional economy through the movement of goods in international and domestic commerce. Under economic base theory, these "basic" industries generate a chain of secondary spending that supports "non-basic" local-serving industries. The ratio of total economic activity to basic activity defines the base multiplier.

For port economies, the export-base relationship is particularly strong because:
- Port operations are almost entirely driven by extra-regional demand (vessel calls, cargo throughput)
- Port-related expenditures — pilotage, stevedoring, trucking, warehousing — are purchased locally
- Worker earnings are spent primarily within the metropolitan statistical area (MSA)

### 2.2 Input-Output Analysis (Leontief Model)

The model's mathematical foundation is the Leontief input-output framework, which represents an economy as a system of interindustry transactions. For an economy with *n* industries, the total output vector **x** is determined by:

```
x = (I - A)^(-1) * f

Where:
  x = vector of total industry outputs (n × 1)
  I = identity matrix (n × n)
  A = technical coefficients matrix (n × n), where a_ij = purchases by industry j from industry i per dollar of j's output
  f = vector of final demand (n × 1)
  (I - A)^(-1) = Leontief inverse matrix (total requirements matrix)
```

Each element of the Leontief inverse represents the total output required from industry *i* (directly and indirectly) to deliver one dollar of final demand from industry *j*. Column sums of the Leontief inverse yield the output multipliers.

### 2.3 RIMS II Methodology

The Bureau of Economic Analysis Regional Input-Output Modeling System (RIMS II) provides regional multipliers derived from national I-O accounts adjusted for regional industry structure using County Business Patterns and BEA Regional Economic Accounts data.

**RIMS II multiplier types used by this model:**

| Multiplier Type | Definition | Scope |
|---|---|---|
| Final-demand output | Total output change per dollar of final-demand change | Direct + indirect + induced |
| Final-demand earnings | Total earnings change per dollar of final-demand change | Direct + indirect + induced |
| Final-demand employment | Total employment change per million dollars of final-demand change | Direct + indirect + induced |
| Direct-effect earnings | Total earnings change per dollar of direct earnings change | Ratio-based |
| Direct-effect employment | Total employment change per unit of direct employment change | Ratio-based |

RIMS II regions are defined at county, multi-county, metropolitan area, or state level. The model maps each port to its BEA economic area (EA) or MSA for multiplier selection.

### 2.4 IMPLAN Comparison

IMPLAN (Impact Analysis for Planning) uses a social accounting matrix (SAM) framework that extends the Leontief model by incorporating institutional accounts (households, government, capital) alongside interindustry transactions. IMPLAN's SAM multipliers are generally larger than RIMS II multipliers because they capture additional feedback loops — for example, the effect of government tax-and-spending cycles on household income.

| Feature | RIMS II | IMPLAN |
|---|---|---|
| Publisher | Bureau of Economic Analysis (BEA) | IMPLAN Group LLC |
| Basis | National I-O tables + regional adjustments | County-level SAM with 546 sectors |
| Cost | ~$275 per region (one-time) | ~$1,500/year subscription + per-region data |
| Multiplier types | Type II (with induced) | Type I, Type II, SAM |
| Sector detail | ~64 aggregated industries (BEA) | 546 IMPLAN sectors |
| Customisation | Limited (fixed coefficients) | Full coefficient adjustment, margining |
| Typical output multiplier | 1.8–2.5 for port sectors | 2.0–3.0 for port sectors |
| Use case | Quick, defensible federal studies | Detailed state/local project-level analysis |

This model supports both RIMS II and IMPLAN multiplier inputs. When IMPLAN data is available, it is preferred for its finer sector resolution. When only RIMS II data is available (the more common case for rapid assessment), RIMS II multipliers are used with documented adjustment factors.

### 2.5 Social Accounting Matrix (SAM) Approach

The SAM extends the I-O framework by adding rows and columns for:
- Factor payments (labour, capital)
- Household income groups
- Government accounts (federal, state, local)
- Capital accounts (savings, investment)
- Rest-of-world accounts (imports, exports)

SAM multipliers capture the full circular flow of income and are particularly relevant for port impact analysis because port operations generate substantial government revenue (customs duties, property taxes, harbour maintenance tax) that is partially recycled into the regional economy through public spending.

```
SAM Multiplier > Type II Multiplier > Type I Multiplier

Type I:   direct + indirect effects only
Type II:  direct + indirect + induced effects (household spending)
SAM:      direct + indirect + induced + institutional effects (government, capital)
```

---

## 3. Multiplier Engine

### 3.1 Architecture

The multiplier engine (`multiplier_engine.py`) accepts direct economic activity as input and applies regional multipliers to estimate total economic impact. The engine supports three multiplier modes:

1. **RIMS II mode:** Uses BEA final-demand and direct-effect multipliers by region and industry
2. **IMPLAN mode:** Uses IMPLAN SAM-based multipliers with 546-sector resolution
3. **Custom mode:** Uses user-supplied multipliers for sensitivity analysis or non-standard regions

### 3.2 Multiplier Types

**Type I Multipliers (Direct + Indirect)**

Type I multipliers capture the interindustry supply chain effects of port spending. When a port terminal purchases equipment maintenance, the maintenance provider purchases parts, the parts supplier purchases raw materials, and so on.

```
Type I Multiplier = (Direct Effect + Indirect Effect) / Direct Effect
```

**Type II Multipliers (Direct + Indirect + Induced)**

Type II multipliers add household spending effects. Workers employed directly and indirectly by port operations spend their wages on housing, food, healthcare, and other goods and services, generating additional economic activity.

```
Type II Multiplier = (Direct + Indirect + Induced) / Direct Effect
```

**SAM Multipliers**

SAM multipliers further incorporate government spending feedback and capital account effects.

### 3.3 Industry-Specific Multipliers for Maritime/Port Sectors

The model uses NAICS-based sector mapping to assign appropriate multipliers to each component of port economic activity:

| NAICS Code | Industry | RIMS II Output Multiplier (Gulf Coast Avg.) | RIMS II Employment Multiplier (jobs/$M) |
|---|---|---|---|
| 483111 | Deep Sea Freight Transportation | 1.94 | 10.8 |
| 483113 | Coastal & Great Lakes Freight | 1.87 | 11.2 |
| 483211 | Inland Water Freight Transportation | 1.91 | 12.4 |
| 488310 | Port and Harbour Operations | 2.12 | 14.6 |
| 488320 | Marine Cargo Handling | 2.08 | 16.3 |
| 488330 | Navigational Services to Shipping | 1.95 | 13.1 |
| 488390 | Other Water Transport Support | 1.89 | 12.7 |
| 484110 | General Freight Trucking, Local | 2.04 | 15.2 |
| 484121 | General Freight Trucking, Long-Distance (TL) | 1.98 | 13.8 |
| 493110 | General Warehousing and Storage | 2.15 | 17.1 |
| 524126 | Marine Insurance (direct) | 1.82 | 9.4 |
| 541614 | Process/Logistics Consulting | 2.21 | 14.9 |

**NAICS sector groupings used in the model:**

| Sector Group | NAICS Range | Description |
|---|---|---|
| Water Transportation | 483xxx | Vessel operations (deep sea, coastal, inland) |
| Support Activities | 488xxx | Port operations, cargo handling, pilotage, towage |
| Trucking | 484xxx | Drayage and local/long-haul freight |
| Warehousing | 493xxx | Storage and distribution |
| Wholesale Trade | 423xxx–424xxx | Commodity distribution |
| Professional Services | 541xxx | Maritime consulting, engineering, legal |
| Government | 926120 | Port authority operations (public sector) |

### 3.4 Regional Adjustment Factors

National multipliers are adjusted for regional economic characteristics using location quotients (LQ) and regional purchase coefficients (RPC):

```
Regional Multiplier = National Multiplier × Regional Adjustment Factor

Where:
  Regional Adjustment Factor = f(LQ, RPC, regional industry mix)
  LQ = (Regional employment in sector i / Total regional employment) /
       (National employment in sector i / Total national employment)
```

Regions with higher location quotients for port-related industries (e.g., the Houston-Galveston MSA for NAICS 483/488) will have larger multipliers because more of the supply chain is sourced locally.

**Regional adjustment factors for Gulf Coast port regions:**

| Port Region (MSA/EA) | BEA Region Code | Adjustment Factor | Rationale |
|---|---|---|---|
| Houston-The Woodlands-Sugar Land | 26420 | 1.08 | Large, diversified metro; deep maritime cluster |
| New Orleans-Metairie | 35380 | 1.12 | High port concentration relative to economy size |
| Mobile | 33660 | 0.95 | Smaller metro, higher leakage to adjacent regions |
| Tampa-St. Petersburg-Clearwater | 45300 | 1.02 | Large metro, moderate port share |
| Baton Rouge | 12940 | 0.98 | Petrochemical-dominant; port is secondary sector |
| Lake Charles | 29340 | 0.91 | Small metro, substantial leakage |
| Beaumont-Port Arthur | 13140 | 0.93 | Small metro, petrochemical focus |
| Plaquemines Parish (standalone) | Custom | 1.18 | Extremely port-dependent economy |

### 3.5 Calculation Procedure

The multiplier engine executes the following steps:

1. **Accept direct spending inputs** by NAICS sector (e.g., $50M in NAICS 488320 marine cargo handling)
2. **Look up regional multipliers** for each sector-region combination
3. **Apply final-demand multipliers** to compute total output, earnings, and employment
4. **Decompose results** into direct, indirect, and induced components using ratio analysis
5. **Aggregate across sectors** to produce total port economic impact
6. **Generate summary tables** with confidence intervals based on multiplier uncertainty (typically +/- 10-15%)

---

## 4. Employment Model

### 4.1 Employment Categories

The employment model (`employment_model.py`) estimates jobs supported by port operations across three tiers:

**Direct Employment:** Workers whose jobs exist because of port operations and who work at or directly serve the port.

**Indirect Employment:** Workers in supply chain industries that provide goods and services to port operations (equipment suppliers, fuel distributors, insurance, ship repair).

**Induced Employment:** Workers whose jobs are supported by the household spending of direct and indirect workers (retail, restaurants, healthcare, housing).

### 4.2 Direct Employment Categories

The model tracks direct employment across 12 occupation categories specific to port operations:

| Occupation Category | Typical FTE per Port (Major Gulf) | Avg. Annual Wage | NAICS Alignment |
|---|---|---|---|
| Terminal operators/managers | 150–400 | $72,000 | 488310 |
| Longshoremen/stevedores (ILA) | 800–3,500 | $78,000 | 488320 |
| Marine pilots | 40–120 | $425,000 | 488330 |
| Ship agents and brokers | 80–250 | $68,000 | 488510 |
| Tugboat operators | 100–350 | $82,000 | 483113 |
| Drayage truckers | 500–2,500 | $52,000 | 484110 |
| Warehouse workers | 200–1,200 | $38,000 | 493110 |
| Customs brokers | 60–200 | $65,000 | 488510 |
| Marine surveyors | 30–100 | $85,000 | 541380 |
| Ship repair/maintenance | 200–1,500 | $58,000 | 336611 |
| Port authority staff | 100–800 | $62,000 | 926120 |
| Security personnel | 80–400 | $45,000 | 561612 |

**Gulf Coast port direct employment benchmarks:**

| Port | Direct Employment (FTE) | Cargo Throughput (M tons) | Jobs per Million Tons |
|---|---|---|---|
| Houston | 68,300 | 285 | 240 |
| South Louisiana (SLPA) | 31,400 | 275 | 114 |
| New Orleans | 18,900 | 95 | 199 |
| Baton Rouge | 8,200 | 62 | 132 |
| Mobile | 10,800 | 58 | 186 |
| Tampa | 7,600 | 37 | 205 |
| Lake Charles | 6,400 | 56 | 114 |
| Beaumont-Port Arthur | 5,100 | 87 | 59 |
| Plaquemines (planned) | 800–2,400 | 8–25 | 100–160 |

### 4.3 Indirect Employment

Indirect employment is estimated by applying RIMS II direct-effect employment multipliers to the direct employment count:

```
Indirect Employment = Direct Employment × (Employment Multiplier - 1) × Indirect Share

Where:
  Indirect Share = portion of the multiplier effect attributable to supply chain (typically 0.45-0.55)
```

Key indirect employment sectors for ports:

| Sector | Indirect Employment Ratio (per 1,000 direct port jobs) |
|---|---|
| Equipment manufacturing and supply | 120–180 |
| Fuel and petroleum distribution | 80–130 |
| Ship repair and marine services | 100–160 |
| Insurance and financial services | 60–90 |
| Professional/technical services | 70–110 |
| Utilities (electric, water, telecom) | 40–65 |
| Construction and maintenance | 50–85 |
| **Total indirect** | **520–820** |

### 4.4 Induced Employment

Induced employment captures the household spending multiplier. Port workers and supply chain workers spend wages locally, supporting retail, healthcare, education, and other community services:

```
Induced Employment = Direct Employment × (Employment Multiplier - 1) × Induced Share

Where:
  Induced Share = 1 - Indirect Share (typically 0.45-0.55)
```

Induced employment sectors with highest port-related generation:

| Sector | Induced Employment Ratio (per 1,000 direct port jobs) |
|---|---|
| Retail trade | 150–220 |
| Healthcare and social services | 110–170 |
| Accommodation and food services | 100–160 |
| Real estate and housing | 60–90 |
| Educational services | 40–70 |
| Personal services | 30–50 |
| **Total induced** | **490–760** |

### 4.5 Total Employment Impact Ratios

Combining all three tiers, the model produces total employment impact ratios:

| Port Type | Direct | Indirect | Induced | Total | Total Multiplier |
|---|---|---|---|---|---|
| Large diversified (Houston) | 1.00 | 0.72 | 0.65 | 2.37 | 2.37x |
| Mid-size bulk (New Orleans) | 1.00 | 0.68 | 0.58 | 2.26 | 2.26x |
| Bulk commodity (Baton Rouge) | 1.00 | 0.55 | 0.48 | 2.03 | 2.03x |
| Small regional (Lake Charles) | 1.00 | 0.48 | 0.42 | 1.90 | 1.90x |
| New development (Plaquemines) | 1.00 | 0.40 | 0.35 | 1.75 | 1.75x |

### 4.6 FTE Conversion Methodology

The model converts headcount to full-time equivalents (FTE) using occupation-specific factors:

```
FTE = Headcount × FTE_Factor

Where FTE_Factor accounts for:
  - Part-time workers (factor < 1.0)
  - Seasonal/intermittent workers (ILA longshoremen: factor = 0.65-0.85)
  - Contract workers (drayage truckers: factor = 0.75-0.90)
  - Full-time salaried (port authority staff: factor = 1.0)
```

| Occupation | Typical Headcount-to-FTE Factor |
|---|---|
| Port authority staff | 1.00 |
| Pilots | 1.00 |
| Terminal managers | 1.00 |
| Longshoremen (ILA) | 0.75 |
| Drayage truckers | 0.80 |
| Warehouse workers | 0.85 |
| Security | 0.90 |
| Ship agents | 0.95 |

### 4.7 Wage Estimation

Total earnings impact is estimated by combining FTE counts with occupation-specific average wages:

```
Total Direct Earnings = Σ(FTE_i × Annual_Wage_i) for all occupation categories i

Total Earnings Impact = Total Direct Earnings × Earnings Multiplier
```

The earnings multiplier for Gulf Coast port regions typically ranges from 1.85 to 2.45, meaning every dollar of direct port wages generates $0.85 to $1.45 in additional regional earnings through indirect and induced channels.

---

## 5. Revenue/Fiscal Impact Model

### 5.1 Architecture

The revenue model (`revenue_model.py`) estimates the fiscal impact of port operations on three levels of government: federal, state, and local. It also quantifies port authority self-generated revenue and infrastructure investment returns.

### 5.2 Federal Tax Revenue

Port operations generate federal revenue through multiple channels:

| Revenue Source | Calculation Method | Typical Rate/Amount |
|---|---|---|
| Federal income tax (individual) | Total port-related earnings × effective rate | 15.8% effective rate on port wages |
| Federal income tax (corporate) | Corporate profits from port-related businesses × rate | 21% statutory, ~14% effective |
| FICA/payroll taxes | Total port-related earnings × FICA rate | 7.65% employer + 7.65% employee |
| Customs duties | Dutiable import value × average duty rate | 2.0–4.5% average across all commodities |
| Harbour Maintenance Tax (HMT) | Value of commercial cargo × HMT rate | 0.125% of cargo value |
| Federal excise taxes | Fuel, equipment, vehicle excise | Varies by type |

**Customs duty estimation by commodity class:**

| Commodity Category | Average Effective Duty Rate | Major Port of Entry |
|---|---|---|
| Petroleum and products | 0.5–1.5% | Houston, Beaumont, Lake Charles |
| Iron and steel | 0–25% (varies by product/origin) | New Orleans, Houston, Mobile |
| Cement and clinker | 0–10% (varies by origin) | Houston, Tampa, New Orleans |
| Grain (export) | N/A (duty-free export) | South Louisiana, New Orleans |
| Chemicals | 0–6.5% | Houston, Baton Rouge |
| Containers (mixed) | 2.0–4.5% weighted average | Houston, Mobile |
| Automobiles | 2.5% (passenger), 25% (trucks) | Houston, Mobile |

**Federal revenue benchmarks for Gulf Coast ports (annual estimates):**

| Port Region | Individual Income Tax ($M) | Corporate Tax ($M) | FICA ($M) | Customs ($M) | HMT ($M) | Total Federal ($M) |
|---|---|---|---|---|---|---|
| Houston | 1,420 | 380 | 1,180 | 2,850 | 245 | 6,075 |
| South Louisiana | 540 | 145 | 430 | 180 | 85 | 1,380 |
| New Orleans | 380 | 95 | 305 | 420 | 62 | 1,262 |
| Mobile | 155 | 42 | 125 | 185 | 28 | 535 |
| Tampa | 130 | 38 | 108 | 210 | 24 | 510 |
| Baton Rouge | 120 | 35 | 100 | 65 | 18 | 338 |

### 5.3 State Tax Revenue

State tax revenue varies significantly by state tax structure. The model incorporates state-specific parameters:

| Revenue Source | Texas | Louisiana | Alabama | Florida |
|---|---|---|---|---|
| State income tax (individual) | None | 1.85–4.25% | 2.0–5.0% | None |
| State income tax (corporate) | None (franchise tax 0.375–0.75%) | 3.5–7.5% | 6.5% | 5.5% |
| State sales tax | 6.25% | 4.45% | 4.0% | 6.0% |
| Fuel tax (per gallon) | $0.20 | $0.20 | $0.29 | $0.35 |
| Property tax (state share) | None (local only) | Varies by parish | State + county | None (local only) |
| Port-specific fees | Texas Maritime Fee | LA port development fund | AL State Docks royalties | FL seaport grants |

**State revenue calculation:**

```
State Income Tax Revenue = Total Port-Related Earnings × State Effective Tax Rate
State Sales Tax Revenue  = Induced Spending × (1 - Savings Rate) × Taxable Share × State Sales Rate
State Fuel Tax Revenue   = Port-Related Fuel Consumption (gallons) × State Fuel Tax Rate
```

### 5.4 Local Tax Revenue

Local governments (county, parish, municipality) derive port-related revenue from:

| Revenue Source | Calculation Method | Typical Annual Amount (Major Port MSA) |
|---|---|---|
| Property tax (real) | Assessed value of port-related properties × millage rate | $25M–$180M |
| Property tax (personal/equipment) | Assessed value of movable equipment × rate | $5M–$40M |
| Local sales tax | Induced consumer spending × local rate | $15M–$95M |
| Business licence and permit fees | Count of port-related businesses × average fee | $2M–$12M |
| Hotel/motel occupancy tax | Maritime visitor spending × occupancy rate × tax rate | $3M–$15M |
| Ad valorem tax on cargo | Cargo value × local ad valorem rate (where applicable) | $1M–$8M |

### 5.5 Port Authority Self-Generated Revenue

Port authorities generate operating revenue from facility operations independent of tax levies:

| Revenue Source | Description | Typical Range (Major Gulf Port) |
|---|---|---|
| Dockage and wharfage | Vessel and cargo tariff fees | $25M–$120M |
| Lease revenue | Long-term terminal and land leases | $30M–$200M |
| Handling and throughput fees | Per-ton or per-container charges | $15M–$80M |
| Rail and intermodal fees | On-dock rail switching, container transfer | $5M–$30M |
| Cruise terminal revenue | Per-passenger and vessel fees | $0–$45M |
| Real estate and development | Non-maritime land development | $5M–$40M |
| Foreign Trade Zone fees | FTZ activation, zone lot payments | $2M–$15M |

**Gulf Coast port authority revenue benchmarks:**

| Port Authority | Total Operating Revenue ($M) | Net Operating Income ($M) | Capital Budget ($M) |
|---|---|---|---|
| Port Houston | 478 | 162 | 1,200 (5-year) |
| Port of New Orleans | 112 | 28 | 420 (5-year) |
| Port of South Louisiana | 18 | 5 | 85 (5-year) |
| Alabama State Port Authority (Mobile) | 145 | 38 | 350 (5-year) |
| Port Tampa Bay | 82 | 22 | 280 (5-year) |
| Port of Lake Charles | 32 | 8 | 120 (5-year) |
| Plaquemines Port | 24 | 6 | 180 (5-year) |

### 5.6 Infrastructure Investment Return Analysis

The model evaluates the return on public infrastructure investment in port facilities:

```
ROI_fiscal = (Annual Tax Revenue Generated - Annual Debt Service) / Total Public Investment

Benefit-Cost Ratio = NPV(Total Economic Benefits over Project Life) / NPV(Total Public Costs)

Where:
  Total Economic Benefits = Output Impact + Tax Revenue + Consumer Surplus + Externalities
  Total Public Costs = Capital Investment + Operating Subsidies + Opportunity Cost
  Discount Rate = 7% (OMB Circular A-94 real rate) or 3% (social discount rate)
  Project Life = 30 years (typical port infrastructure)
```

**Typical benefit-cost ratios for Gulf Coast port investments:**

| Investment Type | Benefit-Cost Ratio | Payback Period (years) |
|---|---|---|
| New container terminal | 2.5–4.0 | 8–15 |
| Channel deepening project | 3.0–6.0 | 5–10 |
| Bulk terminal expansion | 2.0–3.5 | 7–12 |
| Intermodal connector (road/rail) | 2.8–5.5 | 6–10 |
| Navigation lock rehabilitation | 4.0–8.0 | 4–8 |

---

## 6. Scenario Builder

### 6.1 Architecture

The scenario builder (`scenario_builder.py`) constructs and compares economic impact scenarios by varying input parameters against a defined baseline. Each scenario is a self-contained set of assumptions about cargo throughput, commodity mix, employment levels, and capital investment, run through the multiplier engine, employment model, and revenue model to produce a full impact assessment.

### 6.2 Baseline Scenario

The baseline represents current port operations using the most recent available data:

```
Baseline Parameters:
  - Cargo throughput: actual tonnage from most recent USACE WCSC data
  - Employment: actual FTE from port authority annual report and BLS QCEW
  - Revenue: actual port authority operating revenue from audited financials
  - Multipliers: current RIMS II or IMPLAN multipliers for the port's MSA/EA
  - Tax rates: current federal, state, and local rates
```

The baseline scenario serves as the reference point (index = 100) against which all other scenarios are measured.

### 6.3 Expansion Scenarios

The model supports four types of expansion scenarios:

**6.3.1 New Terminal Development**

Models the impact of constructing a new terminal facility:

| Parameter | Input Required | Example Value |
|---|---|---|
| Construction cost | Total capital expenditure | $450M |
| Construction period | Years to complete | 3 years |
| Operational capacity | Annual throughput at maturity | 12M tons/year |
| Ramp-up schedule | Years to reach full capacity | 5 years (20%/40%/60%/80%/100%) |
| Direct employment at capacity | FTE when fully operational | 850 FTE |
| Commodity type | Primary cargo category | Bulk dry (cement, aggregates) |

The model separates construction-phase impacts (temporary, high Type I multiplier) from operational-phase impacts (permanent, Type II multiplier).

**6.3.2 Increased Throughput**

Models the impact of growing cargo volume at existing facilities:

```
Throughput Growth Scenario:
  Base tonnage: 95M tons (current)
  Target tonnage: 115M tons (projected)
  Growth rate: 3.2% CAGR over 5 years
  Employment elasticity: 0.4 (10% tonnage growth = 4% employment growth)
  Revenue elasticity: 0.6 (10% tonnage growth = 6% revenue growth)
```

Employment and revenue elasticities reflect the capital-intensive nature of modern port operations — throughput growth does not translate linearly to proportional job or revenue growth due to productivity improvements and automation.

**6.3.3 New Commodity Introduction**

Models the impact of introducing a new commodity vertical:

| Scenario Parameter | Cement Terminal Example | LNG Export Example |
|---|---|---|
| Annual throughput | 2.5M tons | 15M tons LNG equivalent |
| Average cargo value ($/ton) | $120 | $280 |
| Jobs per million tons | 160 | 45 |
| Average wage (direct) | $62,000 | $95,000 |
| Capital investment | $180M | $12B |
| Construction jobs (peak) | 450 | 8,500 |
| Tax incentives (NPV) | $15M | $850M |

**6.3.4 Capacity Expansion at Existing Terminal**

Models incremental capacity additions such as additional berth, expanded laydown area, or new equipment:

```
Expansion Impact = Incremental Throughput × (Marginal Output per Ton) × Regional Multiplier

Where:
  Marginal Output per Ton is typically 60-80% of average output per ton
  (reflecting diminishing returns as existing infrastructure is more fully utilised)
```

### 6.4 Disruption Scenarios

The model quantifies economic losses from operational disruptions:

**6.4.1 Lock Closure (Inland Waterway)**

| Parameter | 30-Day Closure | 90-Day Closure | 180-Day Closure |
|---|---|---|---|
| Cargo diversion (% of normal) | 40–60% | 60–80% | 70–90% |
| Estimated output loss ($M) | 85–140 | 350–580 | 800–1,400 |
| Employment impact (temporary layoffs) | 1,200–2,000 | 3,500–5,800 | 6,000–10,500 |
| Recovery period after reopening | 2–4 weeks | 4–10 weeks | 8–16 weeks |
| Modal shift (barge → rail/truck) | 20–30% | 25–40% | 30–45% |
| Transport cost increase | 35–65% | 40–75% | 45–80% |

**6.4.2 Hurricane/Storm Event**

Based on historical Gulf Coast hurricane impacts (Katrina 2005, Harvey 2017, Ida 2021, Francine 2024):

| Storm Category | Port Closure Duration | Regional Output Loss | Recovery Period |
|---|---|---|---|
| Category 1–2 | 3–7 days | $50M–$200M | 2–6 weeks |
| Category 3 | 7–21 days | $200M–$800M | 1–4 months |
| Category 4–5 | 14–60 days | $500M–$3B | 3–12 months |
| Near-miss (no direct hit) | 1–3 days | $15M–$75M | 1–2 weeks |

**6.4.3 Regulatory Change**

Models the impact of policy changes such as tariff adjustments, environmental regulations, or fee structures:

```
Regulatory Impact = Δ(Cargo Volume) × Output per Ton × Regional Multiplier
                  + Δ(Operating Cost) × Cost Pass-Through Rate × Demand Elasticity

Example: Section 301 maritime fee on Chinese-built vessels
  - Estimated fee per port call: $500K–$1.5M
  - Volume reduction estimate: 5–15% for affected vessels
  - Modal/routing shift: some cargo redirected through Canadian/Mexican ports
  - Net regional impact: depends on substitution elasticity and fleet composition
```

### 6.5 Comparative Analysis

The scenario builder supports side-by-side comparison of port regional impacts:

```
Port A vs Port B Comparison Matrix:

Metric                    | Port A (Houston) | Port B (Mobile) | Difference
--------------------------|------------------|-----------------|----------
Direct employment         | 68,300           | 10,800          | 57,500
Total employment impact   | 161,871          | 20,412          | 141,459
Total output ($B)         | 265.3            | 15.2            | 250.1
Total earnings ($B)       | 12.8             | 0.92            | 11.88
Employment multiplier     | 2.37             | 1.89            | +0.48
Output per direct job ($K)| 3,884            | 1,407           | +2,477
```

### 6.6 Sensitivity Analysis

The scenario builder performs sensitivity analysis on key parameters to assess result robustness:

**Parameters tested (one-at-a-time and combinatorial):**

| Parameter | Baseline | Low (-20%) | High (+20%) | Impact on Total Output |
|---|---|---|---|---|
| Output multiplier | 2.10 | 1.68 | 2.52 | +/- 18.5% |
| Direct employment | 18,900 | 15,120 | 22,680 | +/- 14.2% |
| Average wage | $68,000 | $54,400 | $81,600 | +/- 11.8% |
| Cargo throughput | 95M tons | 76M tons | 114M tons | +/- 16.9% |
| Regional adjustment factor | 1.12 | 0.90 | 1.34 | +/- 8.7% |

The model reports results as point estimates with sensitivity ranges and identifies the parameters with the greatest influence on outcomes (tornado diagram ordering).

---

## 7. Data Sources

### 7.1 Primary Data Sources

| Source | Provider | Data Type | Refresh Cadence | Access |
|---|---|---|---|---|
| RIMS II Multiplier Tables | Bureau of Economic Analysis (BEA) | Regional I-O multipliers by industry and area | Updated annually | Purchase ($275/region) |
| IMPLAN Data | IMPLAN Group LLC | 546-sector SAM by county | Annual | Subscription (~$1,500/yr) |
| Quarterly Census of Employment and Wages (QCEW) | Bureau of Labor Statistics | Employment and wages by NAICS and county | Quarterly | Free (BLS website) |
| County Business Patterns (CBP) | Census Bureau | Establishment counts by NAICS and county | Annual | Free (Census website) |
| Waterborne Commerce Statistics | USACE WCSC | Tonnage by commodity, waterway, port | Annual | Free (USACE website) |
| Port Authority Annual Reports | Individual port authorities | Revenue, throughput, employment, capital plans | Annual | Free (port websites) |
| American Community Survey (ACS) | Census Bureau | Regional income, commuting, demographics | Annual (1-year and 5-year) | Free (Census website) |
| Regional Economic Accounts | BEA | GDP, personal income, employment by metro/county | Annual | Free (BEA website) |

### 7.2 Supplementary Data Sources

| Source | Provider | Use in Model |
|---|---|---|
| Occupational Employment and Wage Statistics (OEWS) | BLS | Wage estimates by occupation for port-related SOC codes |
| Current Employment Statistics (CES) | BLS | Monthly employment by sector for trend analysis |
| IRS Statistics of Income | IRS | Federal effective tax rates by income bracket |
| State tax commission reports | Individual states | State-specific effective tax rates and revenue data |
| MARAD Port Performance Statistics | US DOT MARAD | Port throughput, vessel calls, TEU counts |
| National Waterway Network | USACE/BTS | Waterway infrastructure for connectivity analysis |

### 7.3 Benchmark Studies

The model is calibrated against published port economic impact studies:

| Study | Port/Region | Year | Methodology | Total Jobs Reported | Total Output Reported |
|---|---|---|---|---|---|
| Martin Associates | Port Houston | 2022 | RIMS II | 1,350,000+ (statewide) | $439B |
| Martin Associates | Port of New Orleans | 2018 | RIMS II | 75,100 (MSA) | $24.4B |
| Martin Associates | Port of South Louisiana | 2018 | RIMS II | 88,400 (region) | $31.6B |
| University of South Alabama | Port of Mobile | 2019 | IMPLAN | 151,700 (state) | $25.4B |
| Tampa Bay Regional Planning Council | Port Tampa Bay | 2020 | IMPLAN | 85,000 (region) | $17.2B |
| LSU Economics | Port of Baton Rouge | 2017 | RIMS II | 21,500 (MSA) | $4.8B |
| AECOM | Plaquemines Port | 2021 | IMPLAN | 6,800 (parish) | $1.2B |

---

## 8. Validation

### 8.1 Cross-Validation Against Published Studies

The model's outputs are validated against the benchmark studies listed in Section 7.3. For each validated port, the model is run using the same base year, same geographic scope, and same direct inputs as the published study. Acceptable variance thresholds:

| Metric | Acceptable Variance | Typical Achieved Variance |
|---|---|---|
| Total output | +/- 15% | +/- 8–12% |
| Total employment | +/- 15% | +/- 10–14% |
| Total earnings | +/- 15% | +/- 9–13% |
| Tax revenue | +/- 20% | +/- 12–18% |

Variance exceeding thresholds triggers a parameter review to identify whether the divergence stems from multiplier selection, direct input estimation, or geographic scope differences.

### 8.2 IMPLAN Comparison

When both RIMS II and IMPLAN multipliers are available for the same region, the model is run under both frameworks and results are compared:

| Metric | RIMS II Result | IMPLAN Result | Typical Divergence |
|---|---|---|---|
| Output multiplier | 2.05–2.25 | 2.15–2.55 | IMPLAN 5–15% higher |
| Employment multiplier | 2.10–2.40 | 2.25–2.65 | IMPLAN 7–12% higher |
| Earnings multiplier | 1.85–2.15 | 2.00–2.45 | IMPLAN 8–15% higher |

The divergence is expected and documented: IMPLAN's SAM framework captures institutional feedback loops (government and capital accounts) that RIMS II does not include. When reporting results, both estimates are presented where available, with a note on the methodological source of the difference.

### 8.3 Historical Forecast Accuracy

For ports where the model has been applied in prior years, forecasted impact is compared to subsequently observed outcomes:

```
Forecast Accuracy = 1 - |Forecasted Value - Actual Value| / Actual Value

Assessment protocol:
  1. Retrieve model forecast from Year T for Year T+1 through T+5
  2. Obtain actual BLS/BEA employment and output data for Year T+1 through T+5
  3. Compute forecast accuracy by metric and by time horizon
  4. Document sources of forecast error (demand shock, policy change, natural disaster)
```

Target accuracy: 85%+ within a 2-year horizon, 75%+ within a 5-year horizon. Accuracy degrades at longer horizons primarily due to unforeseeable exogenous shocks (pandemic, hurricane, trade war) rather than model specification errors.

### 8.4 Internal Consistency Checks

The model performs automated consistency checks on each run:

- Output per job must fall within $50K–$500K range (flags outliers)
- Earnings-to-output ratio must fall within 0.25–0.55 (flags unrealistic wage assumptions)
- Employment multiplier must not exceed 4.0 (flags potential double-counting)
- Induced effects must not exceed indirect effects by more than 50% (flags leakage errors)
- Total tax revenue must not exceed 35% of total earnings (flags rate calculation errors)

---

## 9. Limitations

### 9.1 Methodological Limitations

1. **Fixed-coefficient assumption.** Input-output models assume that production technology (the A matrix) is fixed. In reality, firms substitute inputs in response to price changes. This assumption overstates impacts when relative prices shift significantly.

2. **No supply constraints.** The model assumes that increased demand can be met without supply bottlenecks or price inflation. For labour-constrained port markets (e.g., ILA longshoreman shortages), this may overestimate employment responses.

3. **Linear relationships.** Multiplier effects are linear: doubling direct spending doubles total impact. Actual economies exhibit diminishing returns, congestion effects, and threshold nonlinearities not captured by linear I-O models.

4. **Static analysis.** The model produces point-in-time impact estimates. It does not capture dynamic effects such as capital accumulation, technological change, or labour market adjustment over time.

5. **No displacement effects.** The model assumes port-related economic activity is entirely additional. In practice, some induced spending displaces existing economic activity rather than creating net new activity.

### 9.2 Data Limitations

6. **Multiplier age.** RIMS II multipliers are based on BEA benchmark I-O tables updated approximately every 5 years. Between updates, the regional economy may change structurally, causing multiplier drift.

7. **Geographic boundary effects.** Impact estimates are sensitive to the geographic boundary chosen (parish, MSA, EA, state). Narrower boundaries produce smaller multipliers due to higher economic leakage. Results should always be reported with the geographic scope explicitly stated.

8. **Direct input estimation.** The accuracy of total impact estimates is bounded by the accuracy of direct inputs (employment counts, wage levels, spending categories). Port authority self-reported employment figures may include or exclude contract workers inconsistently.

9. **Tax rate assumptions.** Effective tax rates vary by individual circumstances. The model uses average effective rates by income bracket and business type, which may not reflect the actual tax burden on port-related workers and businesses.

### 9.3 Scope Limitations

10. **Environmental externalities.** The model does not account for environmental costs (air emissions, water quality, habitat disruption) or benefits (modal shift from truck to water reducing per-ton emissions). A full social accounting would require integration of environmental valuation methods.

11. **Quality of life effects.** Port operations generate noise, traffic, and land use impacts that affect residential property values and community wellbeing. These effects are not captured in standard I-O analysis.

12. **National vs. regional framing.** The model estimates regional impacts. It does not account for the possibility that economic activity at one port may be displaced from another port region, resulting in no net national gain. Inter-port competition effects require a national-level general equilibrium model.

---

## 10. References

1. Bureau of Economic Analysis. *RIMS II: An Essential Tool for Regional Developers and Planners.* Washington, DC: US Department of Commerce, 2013. https://www.bea.gov/resources/methodologies/RIMSII-user-guide

2. Miller, R.E. and Blair, P.D. *Input-Output Analysis: Foundations and Extensions.* 2nd ed. Cambridge: Cambridge University Press, 2009.

3. IMPLAN Group LLC. *IMPLAN Methodology.* Huntersville, NC. https://implan.com/resources/

4. Leontief, W. *The Structure of the American Economy, 1919-1939.* 2nd ed. New York: Oxford University Press, 1951.

5. Martin Associates. *The Local and Regional Economic Impacts of the Port of Houston.* Lancaster, PA, 2022.

6. Martin Associates. *Economic Impacts of the Port of New Orleans.* Lancaster, PA, 2018.

7. Martin Associates. *Economic Impacts of the Port of South Louisiana.* Lancaster, PA, 2018.

8. University of South Alabama. *The Economic Impact of the Alabama State Port Authority.* Mobile, AL, 2019.

9. Bureau of Labor Statistics. *Quarterly Census of Employment and Wages.* https://www.bls.gov/cew/

10. US Census Bureau. *County Business Patterns.* https://www.census.gov/programs-surveys/cbp.html

11. US Army Corps of Engineers. *Waterborne Commerce of the United States.* WCSC Annual Reports. https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/

12. US Department of Transportation, Maritime Administration. *Port Performance Freight Statistics Program.* Annual Report. https://www.maritime.dot.gov/

13. Office of Management and Budget. *Circular A-94: Guidelines and Discount Rates for Benefit-Cost Analysis of Federal Programs.* Revised 2023.

14. Tiebout, C.M. "The Community Economic Base Study." *Supplementary Paper No. 16.* New York: Committee for Economic Development, 1962. (Economic base theory)

15. Isard, W. *Methods of Regional Analysis: An Introduction to Regional Science.* Cambridge: MIT Press, 1960. (Regional I-O methodology)

16. American Association of Port Authorities. *Seaports of the Americas.* Annual directory and statistics. https://www.aapa-ports.org/

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | OceanDatum.ai*
