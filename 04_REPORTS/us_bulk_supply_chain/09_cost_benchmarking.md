# Chapter 9: Supply Chain Cost Benchmarking Framework

## Executive Summary

This chapter establishes a comprehensive cost benchmarking framework for US bulk supply chains, providing the analytical foundation for commodity-specific landed cost modeling in subsequent volumes. Inland waterway barge transportation remains the lowest-cost mode at $0.01--0.03 per ton-mile, compared to $0.02--0.05 for rail and $0.08--0.25 for truck, though effective costs vary significantly based on commodity density, lane-specific infrastructure constraints, and accessorial charges. Ocean-to-inland delivered cost for a representative Supramax bulk carrier is benchmarked at approximately $269,000 for a New Orleans port call ($8.97/ton) and $363,000 for Houston ($8.06/ton), before inland transportation. The Section 301 maritime shipping fee overlay adds $16--33 per ton for Chinese-built vessels, fundamentally altering the economics of affected trades. This framework enables consistent cost comparison across commodities by decomposing total landed cost into standardized components: FOB origin, ocean freight, insurance, duty, port charges, and inland transportation.

---

## 9.1 Modal Cost Comparison

### Benchmark Rates by Mode

The following table presents representative cost benchmarks for the three primary inland transportation modes used in US bulk supply chains. All figures represent 2024--2025 market conditions.

| Mode | Cost per Ton-Mile | Typical Payload | Fuel Efficiency (ton-miles/gallon) | Best Application |
|------|-------------------|-----------------|-----------------------------------|------------------|
| Barge (15-barge tow) | $0.01--0.03 | 22,500--27,000 tons | 576 | Long-haul, waterway-adjacent |
| Rail (unit train, 110 cars) | $0.02--0.05 | 11,000--13,200 tons | 470--500 | Long-haul, high-volume corridors |
| Rail (manifest/carload) | $0.04--0.08 | 100--120 tons/car | 300--400 | Smaller volumes, diverse origins |
| Truck (standard bulk trailer) | $0.08--0.25 | 22--26 tons | 68--100 | Short-haul, last mile, no rail/barge access |

### Key Observations

- **Barge advantage is distance-dependent.** The barge cost advantage over rail narrows on shorter movements (under 500 miles) due to fixed costs of fleeting, switching, and lock transit times.
- **Rail unit-train economics** require sufficient volume (typically 10,000+ tons per shipment) and dedicated loading/unloading infrastructure. Shippers unable to fill unit trains face manifest service rates that are 2--3x higher per ton-mile.
- **Truck is rarely competitive** for bulk movements beyond 100--150 miles but serves as the essential first/last mile connector in nearly all bulk supply chains.
- **Intermodal combinations** (barge-to-truck, rail-to-truck) are standard in bulk logistics, and the total cost must account for transload charges at each transfer point, typically $3--8/ton per handling.

{% if facility_total_count %}
### Platform Data: Production Facility Footprint

The EPA Facility Registry Service (FRS) identifies **{{ facility_total_count | commas }}** bulk commodity production and distribution facilities across **{{ facility_state_count }}** states. Key segments:

{% if facility_counts %}
| Facility Type | Count |
|--------------|-------|
{% for key, info in facility_counts.items() %}| {{ info.label }} | {{ info.count | commas }} |
{% endfor %}
{% endif %}

{% if cement_facilities_by_state %}
**Top states by cement industry facility count:**

| State | Cement Manufacturing | Ready-Mix | Total |
|-------|---------------------|-----------|-------|
{% for row in cement_facilities_by_state[:10] %}| {{ row.state }} | {{ row.cement_manufacturing | commas }} | {{ row.ready_mix | commas }} | {{ row.total_facilities | commas }} |
{% endfor %}

> **Source:** EPA FRS analysis outputs, last updated {{ facility_results_updated }}.
{% endif %}
{% endif %}

---

## 9.2 Barge Cost Model

### GTR-Based Rate Engine

Inland waterway barge rates are commonly referenced against the USDA Grain Transportation Report (GTR) tariff benchmarks, which provide weekly spot and contract rate indices for key corridors. While the GTR is grain-focused, it serves as the foundational pricing reference for all inland barge commerce because the same fleet and infrastructure serve multiple commodity segments.

Key GTR-referenced corridors and representative rates (per ton, southbound to New Orleans):

| Origin Region | River Miles to NOLA | GTR Benchmark ($/ton) | Effective $/ton-mile |
|--------------|--------------------|-----------------------|---------------------|
| St. Louis, MO | 180 | $6--12 | $0.033--0.067 |
| Cairo, IL | 955 | $12--20 | $0.013--0.021 |
| Minneapolis, MN | 1,850 | $22--35 | $0.012--0.019 |
| Cincinnati, OH | 1,530 (via Ohio) | $18--28 | $0.012--0.018 |
| Pittsburgh, PA | 1,950 (via Ohio) | $24--38 | $0.012--0.019 |

Rates are highly seasonal, with harvest-season peaks (September--November) producing rate spikes of 50--200% above off-season levels for grain corridors.

{% if barge_forecast_accuracy %}
### Platform Forecast Model Performance

The reporting platform's barge rate forecasting engine compares VAR(3) and SpVAR(3) models against a naive random-walk baseline across seven GTR corridor segments. Model accuracy metrics from the most recent backtesting run:

| Segment | Naive MAPE (%) | VAR MAPE (%) | SpVAR MAPE (%) | VAR R-squared | Improvement (%) |
|---------|---------------|-------------|---------------|--------------|----------------|
{% for row in barge_forecast_accuracy %}| {{ row.segment }} | {{ row.naive_mape }} | {{ row.var_mape }} | {{ row.spvar_mape }} | {{ row.var_r2 }} | {{ row.var_improvement_pct }} |
{% endfor %}
{% if barge_forecast_summary %}
> **Model Summary:** {{ barge_forecast_summary.segments }} corridor segments tested over {{ barge_forecast_summary.test_periods }} periods. Naive baseline average MAPE: {{ barge_forecast_summary.naive_avg_mape }}%. VAR model average MAPE: {{ barge_forecast_summary.var_avg_mape }}%. Average R-squared: {{ barge_forecast_summary.var_avg_r2 }}.
{% endif %}
{% endif %}

### Lock Delay Modeling

Lock delays are a significant and variable cost component in barge transportation. The cost of delay is calculated as:

**Delay Cost = (Delay Hours) x (Tow Operating Cost per Hour)**

Typical tow operating costs range from $500--$900 per hour (including fuel, crew, insurance, and capital charges), meaning a 3-hour lock delay costs approximately $1,500--$2,700 per lockage. A tow transiting 10 locks on a round trip through congested segments may accumulate $15,000--$27,000 in delay costs.

Key bottleneck locks and average delay times:

| Lock | Waterway | Average Delay (Hours) | Peak Delay (Hours) |
|------|----------|----------------------|-------------------|
| Lock 25 | Upper Mississippi | 4--8 | 12--24 |
| Lock 27 | Upper Mississippi | 3--6 | 8--16 |
| Markland | Ohio River | 2--4 | 6--12 |
| Lock 52 (replaced by Olmsted) | Ohio River | Replaced 2018 | N/A |
| Bayou Sorrel | GIWW | 2--5 | 8--18 |
| Inner Harbor Navigation Canal | GIWW/Mississippi | 3--6 | 10--20 |

### Fleet Utilization

Barge fleet utilization is a critical determinant of effective transport cost. Key metrics:

- **Annual utilization rate** for dry cargo barges: 65--80% (remainder in maintenance, repositioning, or idle)
- **Round-trip efficiency:** Southbound (loaded) / Northbound (typically empty for grain; may carry fertilizer, salt, or other backhaul cargo)
- **Backhaul availability** can reduce effective one-way cost by 15--30% when two-way cargo flows exist

### Barge Cost Components

A complete barge transportation cost includes the following components:

| Component | Description | Typical Cost Range |
|-----------|-------------|-------------------|
| **Linehaul** | Towboat and barge hire for mainline transit | $0.008--0.020/ton-mile |
| **Fuel surcharge** | Variable adjustment based on diesel price | $0.002--0.006/ton-mile |
| **Fleeting** | Barge staging and assembly at origin/destination | $1.50--4.00/ton |
| **Switching** | Moving barges between fleets, docks, and tow positions | $1.00--3.00/ton |
| **Loading/unloading** | Dock-side cargo handling (may be terminal charge) | $2.00--6.00/ton |
| **Demurrage** | Charges for barge detention beyond free time (typically 48--72 hrs) | $150--350/barge/day |
| **Waterway use tax** | Federal fuel tax at $0.29/gallon, allocated to cargo | $0.50--1.50/ton |
| **Insurance** | Hull, P&I, cargo coverage allocated to movement | $0.25--0.75/ton |

---

## 9.3 Rail Cost Model

### URCS Variable Cost Methodology

The Surface Transportation Board's Uniform Rail Costing System (URCS) provides a standardized methodology for estimating the variable cost of a specific rail movement. URCS costs are used as the denominator in Revenue-to-Variable-Cost (R/VC) ratio calculations that determine regulatory jurisdiction over rate challenges.

URCS variable cost components include:

1. **Running costs:** Locomotive fuel, crew wages, locomotive and car maintenance (varies with distance)
2. **Switching costs:** Yard operations at origin, intermediate, and destination terminals (per-car basis)
3. **Special service costs:** Hazmat compliance, heavy-load routing, dimensional clearance
4. **Overhead allocation:** Variable portion of administrative and general expenses

### R/VC Ratios by Commodity Category

R/VC ratios provide a measure of railroad pricing power relative to variable costs. Higher ratios indicate greater pricing leverage (and potential market dominance).

| Commodity Category | Typical R/VC Ratio Range | Regulatory Implication |
|-------------------|------------------------|----------------------|
| Coal | 150--250% | Heavily litigated; multiple rate cases |
| Grain and oilseeds | 170--280% | Seasonal pricing variation; shuttle train discounts |
| Construction materials | 200--350% | Often captive; limited modal alternatives |
| Chemicals and fertilizer | 180--300% | Mixed; some competitive pressure from barge |
| Metallic ores | 160--250% | Generally captive to single railroad |

The 180% R/VC threshold is the statutory standard for STB jurisdiction: below 180%, the railroad is presumed not to have market dominance, and rate challenges are generally not entertained.

{% if rail_cement_origins %}
### Platform Data: Cement Rail Origin Markets

STB Waybill Sample analysis identifies the following top cement shipping origin BEAs by tonnage (STCC 3241, millions of tons):

| Origin Market | States | Tons (M) | Revenue ($M) | Rev/Ton | Avg Miles | Destinations |
|--------------|--------|---------|-------------|---------|----------|-------------|
{% for row in rail_cement_origins %}| {{ row.origin }} | {{ row.states }} | {{ row.tons_M }} | {{ row.rev_M }} | ${{ row.rev_per_ton }} | {{ row.avg_miles }} | {{ row.num_dests }} |
{% endfor %}

> **Source:** STB Public Use Waybill Sample, extracted by platform rail analytics engine. {{ rail_total_origins }} origin BEAs, {{ rail_total_od_flows }} O-D pairs analyzed. Data as of {{ rail_results_updated }}.
{% endif %}

{% if rail_cement_od_flows %}
### Platform Data: Top Cement O-D Flows

The highest-volume cement rail movements by origin-destination pair:

| Origin | Destination | Tons (M) | Miles | Rate ($/ton) |
|--------|------------|---------|-------|-------------|
{% for row in rail_cement_od_flows %}| {{ row.origin }} | {{ row.destination }} | {{ row.tons_M }} | {{ row.miles }} | ${{ row.rate }} |
{% endfor %}
{% endif %}

### Commodity-Specific Cost Factors

Rail costs for bulk commodities are influenced by several commodity-specific factors:

- **Car type requirements:** Covered hoppers (grain, cement), open-top hoppers (coal, aggregates), gondolas (steel, scrap), and tank cars (chemicals, petroleum) each have different per-diem and maintenance cost profiles.
- **Train configuration:** Unit trains (single commodity, single origin-destination) achieve 30--50% lower per-ton costs than manifest service due to elimination of intermediate yard processing.
- **Loading/unloading infrastructure:** Shippers with loop tracks enabling in-motion unloading receive rate concessions reflecting the railroad's avoided switching costs.
- **Seasonal demand:** Grain harvest and coal stockpiling seasons create capacity competition that elevates rates on shared corridors.

---

## 9.4 Port Cost Model

### Cost Components for Bulk Vessel Port Calls

Port costs for bulk cargo vessels are composed of multiple discrete charges, each assessed by different entities (port authority, pilots' association, tug companies, terminal operators, government agencies). The following framework decomposes these charges:

| Cost Component | Assessing Entity | Basis of Charge | Typical Range (Supramax) |
|---------------|-----------------|-----------------|------------------------|
| **Pilotage (inbound)** | Pilots' association | Vessel draft and LOA | $15,000--$45,000 |
| **Pilotage (outbound)** | Pilots' association | Vessel draft and LOA | $12,000--$40,000 |
| **Pilotage (shifting)** | Pilots' association | Per shift | $5,000--$15,000 |
| **Towage (inbound)** | Tug companies | Number of tugs x hours | $20,000--$55,000 |
| **Towage (outbound)** | Tug companies | Number of tugs x hours | $15,000--$45,000 |
| **Dockage** | Port authority/terminal | Vessel LOA x days | $3,000--$8,000 |
| **Wharfage** | Port authority/terminal | Per ton of cargo | $1.00--3.50/ton |
| **Stevedoring** | Terminal operator | Per ton loaded/discharged | $3.00--8.00/ton |
| **Line handling** | Line handling company | Per operation | $2,000--$5,000 |
| **Agency fee** | Ship's agent | Per port call | $5,000--$10,000 |
| **Customs/CBP fees** | CBP | Per entry (MPF + HMF) | $1,000--$5,000 |
| **Surveying** | Independent surveyors | Per cargo survey | $3,000--$8,000 |
| **Security (ISPS)** | Terminal/port authority | Per vessel | $500--$2,000 |

### Port-Specific Benchmarks

Port costs vary significantly between US ports due to differences in pilotage tariffs, tug requirements, channel configurations, and terminal competition. The following section provides detailed benchmarks for two major bulk ports.

---

## 9.5 Sample Port Call Cost Calculations

### New Orleans (NOLA) -- Supramax Bulk Carrier (30,000 MT Cargo)

| Cost Item | Amount |
|-----------|--------|
| Pilotage -- Bar to berth (inbound) | $28,500 |
| Pilotage -- Berth to bar (outbound) | $25,200 |
| Towage -- Inbound (2 tugs) | $22,000 |
| Towage -- Outbound (2 tugs) | $18,500 |
| Dockage (3 days) | $5,400 |
| Wharfage (30,000 MT x $2.25) | $67,500 |
| Stevedoring (30,000 MT x $3.50) | $105,000 |
| Line handling (2 operations) | $3,800 |
| Agency fee | $7,500 |
| CBP/customs fees | $2,100 |
| Cargo survey | $4,500 |
| ISPS security | $1,000 |
| Miscellaneous (launch service, communications, fresh water) | $3,000 |
| **Total Port Call Cost** | **$294,000** |
| Less: Wharfage allocated to cargo receiver | ($25,000) |
| **Net Vessel-Side Port Cost** | **$269,000** |
| **Per-Ton Port Cost (30,000 MT)** | **$8.97** |

### Houston -- Supramax Bulk Carrier (45,000 MT Cargo)

| Cost Item | Amount |
|-----------|--------|
| Pilotage -- Sea buoy to berth (inbound) | $42,000 |
| Pilotage -- Berth to sea buoy (outbound) | $38,500 |
| Pilotage -- Shift (1 shift) | $12,000 |
| Towage -- Inbound (3 tugs, longer channel) | $38,000 |
| Towage -- Outbound (3 tugs) | $32,000 |
| Towage -- Shift (2 tugs) | $14,000 |
| Dockage (4 days) | $8,800 |
| Wharfage (45,000 MT x $2.00) | $90,000 |
| Stevedoring (45,000 MT x $3.25) | $146,250 |
| Line handling (3 operations) | $6,500 |
| Agency fee | $8,500 |
| CBP/customs fees | $3,200 |
| Cargo survey | $5,500 |
| ISPS security | $1,500 |
| Ship channel user fee | $4,200 |
| Miscellaneous | $4,500 |
| **Total Port Call Cost** | **$455,450** |
| Less: Wharfage and stevedoring allocated to cargo receiver | ($92,500) |
| **Net Vessel-Side Port Cost** | **$362,950** |
| **Per-Ton Port Cost (45,000 MT)** | **$8.07** |

**Note:** Houston's higher absolute cost reflects the longer ship channel transit (52 miles from sea buoy to inner turning basin), requiring additional tug assists and pilotage charges. However, the per-ton cost is slightly lower than NOLA due to the larger cargo parcel (45,000 vs. 30,000 MT), demonstrating the economies of scale in port operations.

---

## 9.6 Landed Cost Methodology

### Cost Build-Up Framework

Total landed cost for an imported bulk commodity is constructed by aggregating the following components in sequence:

```
Landed Cost = FOB Origin
            + Ocean Freight
            + Marine Insurance
            = CIF US Port
            + Customs Duty (ad valorem or specific)
            + Merchandise Processing Fee (0.3464%, capped at $614.35)
            + Harbor Maintenance Fee (0.125% of cargo value)
            + Port Charges (per Section 9.4--9.5)
            + Section 301 Fee (if applicable, per Chapter 8)
            + Inland Transportation (barge, rail, or truck per Sections 9.2--9.3)
            + Terminal/Transload Charges (if intermodal)
            = Delivered Price at Destination
```

### Component Definitions

| Component | Definition | Typical % of Landed Cost (Bulk) |
|-----------|-----------|-------------------------------|
| **FOB Origin** | Price at loading port, seller's country | 40--65% |
| **Ocean Freight** | Vessel charter or liner rate, loading port to discharge port | 15--35% |
| **Marine Insurance** | Cargo insurance, typically 110% of CIF value x rate | 0.1--0.5% |
| **Customs Duty** | HTS-specific rate applied to transaction value | 0--25% (commodity dependent) |
| **Port Charges** | All costs from Section 9.4 | 3--8% |
| **Inland Transport** | Origin port to final destination | 5--20% |

### Illustrative Landed Cost Calculation

**Example: Imported Bulk Mineral Commodity, 30,000 MT, Brazil to St. Louis, MO**

| Component | Per Ton | Total (30,000 MT) |
|-----------|---------|-------------------|
| FOB Santos, Brazil | $45.00 | $1,350,000 |
| Ocean freight (Santos to NOLA, Supramax) | $22.00 | $660,000 |
| Marine insurance (0.25% of CIF) | $0.17 | $5,025 |
| **CIF New Orleans** | **$67.17** | **$2,015,025** |
| Customs duty (free, HTS specific) | $0.00 | $0 |
| MPF (capped) | $0.02 | $615 |
| HMF (0.125% x $67.17 x 30,000) | $0.08 | $2,519 |
| Port charges (NOLA, per Section 9.5) | $8.97 | $269,000 |
| **Delivered NOLA** | **$76.24** | **$2,287,159** |
| Barge freight (NOLA to St. Louis, 1,050 miles) | $14.00 | $420,000 |
| Fleeting and switching | $3.50 | $105,000 |
| Terminal handling (St. Louis) | $4.00 | $120,000 |
| **Delivered St. Louis** | **$97.74** | **$2,932,159** |

---

## 9.7 Sensitivity Analysis

### Fuel Price Sensitivity

Fuel represents 25--40% of variable operating costs for barge and 20--30% for rail. The following table shows the impact of diesel price changes on per-ton-mile costs:

| Diesel Price ($/gallon) | Barge Cost ($/ton-mile) | Rail Cost ($/ton-mile) | Truck Cost ($/ton-mile) |
|------------------------|------------------------|----------------------|------------------------|
| $2.50 | $0.012 | $0.028 | $0.10 |
| $3.00 | $0.014 | $0.031 | $0.12 |
| $3.50 (baseline) | $0.016 | $0.034 | $0.14 |
| $4.00 | $0.018 | $0.037 | $0.16 |
| $4.50 | $0.020 | $0.040 | $0.18 |
| $5.00 | $0.022 | $0.043 | $0.20 |

**Observation:** Barge transportation shows the lowest absolute sensitivity to fuel prices due to superior fuel efficiency (576 ton-miles/gallon vs. 470 for rail and 68--100 for truck), though the proportional impact is similar across modes.

### Lock Delay Sensitivity

| Scenario | Avg. Delay per Lock (hrs) | Locks per Trip | Total Delay Cost | Added Cost per Ton (27,000-ton tow) |
|----------|--------------------------|----------------|-----------------|-------------------------------------|
| Low delay | 1.0 | 8 | $5,600 | $0.21 |
| Average | 3.0 | 8 | $16,800 | $0.62 |
| High delay | 6.0 | 8 | $33,600 | $1.24 |
| Extreme (closure event) | 24.0 | 3 | $50,400 | $1.87 |

### Vessel Size Sensitivity (Section 301 Impact)

| Vessel Type | DWT | Typical Cargo (MT) | Section 301 Fee (Phase 3) | Per-Ton Impact |
|-------------|-----|--------------------|--------------------------|--------------:|
| Handysize | 28,000--40,000 | 25,000--35,000 | $1,000,000 | $28.57--$40.00 |
| Supramax | 50,000--60,000 | 45,000--55,000 | $1,000,000 | $18.18--$22.22 |
| Panamax | 65,000--85,000 | 60,000--75,000 | $1,000,000 | $13.33--$16.67 |
| Capesize | 150,000--200,000 | 140,000--180,000 | $1,000,000 | $5.56--$7.14 |

**Key Insight:** The flat per-voyage fee structure creates a strong incentive to maximize vessel size, as the per-ton impact decreases dramatically with larger vessels. This will shift trade patterns toward larger ports capable of accommodating Panamax and Capesize vessels, disadvantaging smaller draft-restricted ports that rely on Handysize and Supramax traffic.

### Cargo Volume Sensitivity

Port costs per ton decrease with higher cargo volumes due to the fixed-cost nature of pilotage, towage, and agency fees:

| Cargo Volume (MT) | Fixed Port Costs | Variable Port Costs | Total Port Cost/Ton |
|-------------------|-----------------|--------------------|--------------------|
| 15,000 | $145,000 | $82,500 | $15.17 |
| 25,000 | $145,000 | $137,500 | $11.30 |
| 35,000 | $145,000 | $192,500 | $9.64 |
| 45,000 | $145,000 | $247,500 | $8.72 |
| 55,000 | $145,000 | $302,500 | $8.14 |

---

## 9.8 Section 301 Impact Overlay

### Cost Impact on Delivered Price

The Section 301 fee fundamentally alters delivered cost economics for commodities transported on Chinese-built vessels. Using the landed cost example from Section 9.6:

| Scenario | Delivered St. Louis ($/ton) | Section 301 Adder | Total | % Increase |
|----------|---------------------------|-------------------|-------|-----------|
| Baseline (no fee) | $97.74 | $0.00 | $97.74 | -- |
| Phase 1 (non-Chinese vessel) | $97.74 | $0.00 | $97.74 | 0% |
| Phase 1 (Chinese-built, Supramax) | $97.74 | $16.67 | $114.41 | 17.1% |
| Phase 3 (Chinese-built, Supramax) | $97.74 | $33.33 | $131.07 | 34.1% |
| Phase 3 (Chinese-built, Handysize) | $97.74 | $40.00 | $137.74 | 40.9% |

### Market Response Scenarios

1. **Fleet bifurcation:** Charter rates for non-Chinese-built vessels on US trades increase by $5,000--$15,000/day as demand concentrates on a reduced pool of eligible tonnage.
2. **Port diversion:** Cargo currently destined for draft-restricted US ports (requiring smaller, proportionally more impacted vessels) may shift to deeper-water ports or to rail/truck alternatives from Canadian or Mexican ports.
3. **Sourcing shifts:** For commodities with multiple global sourcing options, the effective cost increase may cause buyers to shift to origins served by non-Chinese-built vessel pools or to domestic sources.
4. **Contract renegotiation:** Long-term supply contracts with CIF or CFR delivery terms will face repricing pressure as vessel operators pass through Section 301 costs.

---

## 9.9 Comparative Cost Summary Tables

### Table 9.9.1: Modal Cost Comparison -- 1,000-Mile Movement, 25,000 Tons

| Cost Element | Barge | Rail (Unit Train) | Truck |
|-------------|-------|-------------------|-------|
| Linehaul | $275,000 | $625,000 | $3,750,000 |
| Fuel surcharge | $75,000 | $125,000 | Included |
| Terminal/switching | $100,000 | $75,000 | $50,000 |
| Loading/unloading | $100,000 | $62,500 | $125,000 |
| Lock delays/congestion | $25,000 | N/A | N/A |
| **Total** | **$575,000** | **$887,500** | **$3,925,000** |
| **Per Ton** | **$23.00** | **$35.50** | **$157.00** |
| **Per Ton-Mile** | **$0.023** | **$0.036** | **$0.157** |

### Table 9.9.2: Port Cost Comparison -- Major US Bulk Ports (Supramax, ~35,000 MT)

| Port | Pilotage | Towage | Dockage | Wharfage | Stevedoring | Other | Total/Ton |
|------|---------|--------|---------|----------|-------------|-------|----------|
| New Orleans | $53,700 | $40,500 | $5,400 | $78,750 | $122,500 | $22,150 | $9.23 |
| Houston | $92,500 | $84,000 | $8,800 | $70,000 | $113,750 | $28,400 | $11.36 |
| Baltimore | $38,000 | $35,000 | $6,200 | $87,500 | $140,000 | $20,800 | $9.36 |
| Mobile | $32,000 | $28,000 | $4,500 | $59,500 | $105,000 | $18,500 | $7.07 |
| Norfolk/Hampton Roads | $35,000 | $30,000 | $5,800 | $66,500 | $115,500 | $19,700 | $7.79 |

---

## 9.10 Implications for Commodity Analysis

The cost benchmarking framework established in this chapter provides the standardized analytical toolkit for commodity-specific supply chain cost modeling. When applying this framework to individual commodities, the following principles should guide the analysis:

1. **Use commodity-specific rate data where available.** The benchmarks in this chapter represent general market conditions. Individual commodity analyses should incorporate published tariff rates, contract rate indices (e.g., GTR for grain barges, Argus/Platts for coal), and shipper-reported actual costs where available.

2. **Model the full intermodal chain.** Most bulk supply chains involve at least two modes. The landed cost build-up must capture each modal segment and the transload/transfer costs between them.

3. **Apply Section 301 fees based on fleet composition analysis.** The per-ton impact varies by vessel type, and the proportion of Chinese-built vessels differs by trade lane and commodity. Each commodity analysis should include a fleet composition assessment for the relevant trade lanes.

4. **Conduct sensitivity analysis on the three highest-impact variables.** For most bulk commodities, these will be (a) ocean freight rates, (b) inland transportation distance and mode, and (c) Section 301 exposure. The sensitivity tables in Section 9.7 provide the methodology.

5. **Benchmark against competing supply origins.** Landed cost analysis is most valuable when comparing delivered costs from multiple sourcing origins, enabling identification of the marginal source that sets market price.

6. **Update cost inputs periodically.** Fuel prices, charter rates, and port tariffs change frequently. The framework is designed for annual or semi-annual recalibration with current market data.
