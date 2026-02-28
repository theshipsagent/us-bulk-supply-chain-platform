# Chapter 4: Railroad Network and Freight Economics

## Executive Summary

The United States railroad network constitutes the backbone of domestic bulk commodity transportation, with seven Class I railroads operating approximately 140,000 statute miles of track and generating combined annual revenues of roughly $80 billion --- accounting for 94% of total freight rail revenue. This chapter examines the structure, economics, and regulatory environment of the Class I railroad system as it pertains to bulk commodity movement, drawing on Surface Transportation Board (STB) cost methodologies, the Public Use Waybill Sample, and the National Transportation Atlas Database (NTAD) / North American Rail Network (NARN) geospatial datasets. Understanding railroad network topology, freight rate economics, and regulatory dynamics is essential for any commodity-specific supply chain analysis that follows.

---

## 4.1 Class I Railroad Overview

The Association of American Railroads (AAR) classifies a railroad as "Class I" when its annual operating revenues exceed a threshold adjusted for inflation (approximately $944 million in recent reporting years). Seven carriers currently hold this designation and collectively dominate the North American freight rail landscape.

### Table 4.1: Class I Railroad Summary Metrics

| Railroad | Abbreviation | Headquarters | Approximate Route Miles | Approximate Annual Revenue ($B) | Primary Geographic Coverage |
|---|---|---|---|---|---|
| BNSF Railway | BNSF | Fort Worth, TX | 32,500 | $23--24 | Western US (transcontinental) |
| Union Pacific Railroad | UP | Omaha, NE | 32,200 | $23--24 | Western US (transcontinental) |
| CSX Transportation | CSX | Jacksonville, FL | 21,000 | $14--15 | Eastern US |
| Norfolk Southern Railway | NS | Atlanta, GA | 19,300 | $11--12 | Eastern US |
| Canadian National Railway | CN | Montreal, QC | 19,600 (US + Canada) | $12--14 | Central corridor (US/Canada) |
| Canadian Pacific Kansas City | CPKC | Calgary, AB | 20,000 (US + Canada + Mexico) | $7--8 | Central/Southern corridor (North America) |
| **Total (approximate)** | | | **~140,000 (US network)** | **~$78--82** | |

**Note:** Route miles reflect mainline and branch line operations. Revenue figures are approximate and reflect recent full-year filings. CN and CPKC mileage includes Canadian and, for CPKC, Mexican segments; US-only mileage is lower. The 2023 merger of Canadian Pacific and Kansas City Southern created CPKC as North America's only single-line railroad spanning Canada, the United States, and Mexico.

### Network Geography

The US Class I railroad network divides broadly into **Western** and **Eastern** territories:

- **Western railroads** (BNSF and UP) operate in a duopoly west of the Mississippi River, with overlapping coverage on key corridors (e.g., Chicago--Los Angeles, Powder River Basin--Gulf Coast) and exclusive territories on certain branch lines.
- **Eastern railroads** (CSX and NS) dominate east of the Mississippi, with significant interline connections at gateway cities such as Chicago, Memphis, St. Louis, and New Orleans.
- **North-South carriers** (CN and CPKC) provide critical cross-border connectivity, with CN linking the Gulf Coast (New Orleans, Mobile) to the Canadian prairies, and CPKC connecting Mexico's industrial heartland through Kansas City to the Upper Midwest and Canada.

The NTAD and NARN datasets, maintained by the Bureau of Transportation Statistics (BTS) and the Federal Railroad Administration (FRA), provide authoritative GIS shapefiles for the entire US rail network, including line ownership, track class, and operational status. These data sources underpin the spatial analyses referenced throughout this report.

{% if rail_cement_destinations %}
### Platform Data: Cement Rail Destination Markets

The platform's STB Waybill analysis identifies major cement-receiving markets by rail tonnage:

| Destination Market | States | Tons (M) | Revenue ($M) | Origins Served |
|-------------------|--------|---------|-------------|---------------|
{% for row in rail_cement_destinations[:10] %}| {{ row.destination }} | {{ row.states }} | {{ row.tons_M }} | {{ row.rev_M }} | {{ row.num_origins }} |
{% endfor %}

> **Source:** Platform rail analytics engine (STB Waybill Sample, STCC 3241). {{ rail_total_destinations }} destination BEAs identified. Data as of {{ rail_results_updated }}.
{% endif %}

---

## 4.2 Network Infrastructure and Capacity

### Track Classification and Capacity

The FRA classifies track into Classes 1 through 9 based on maximum allowable operating speeds:

| FRA Track Class | Maximum Freight Speed (mph) | Typical Application |
|---|---|---|
| Class 1 | 10 | Branch lines, yard tracks |
| Class 2 | 25 | Secondary branch lines |
| Class 3 | 40 | Secondary mainlines |
| Class 4 | 60 | Primary mainlines |
| Class 5 | 80 | High-density corridors |

Bulk commodity unit trains (coal, grain, potash, soda ash) typically operate on Class 4 and Class 5 track at speeds of 40--60 mph when in transit, though average speed including terminal dwell is considerably lower (often 20--30 mph origin-to-destination).

### Key Bulk Commodity Corridors

The following corridors carry the highest volumes of bulk freight by tonnage:

- **Powder River Basin (Wyoming) to Gulf Coast / Midwest utilities** --- Coal unit trains via BNSF and UP; historically the single highest-tonnage corridor in the US network, though volumes have declined with coal-fired generation retirements.
- **Upper Midwest to Pacific Northwest (PNW) and Gulf Coast** --- Grain shuttle trains (BNSF, UP, CP) moving wheat, corn, and soybeans to export elevators.
- **Gulf Coast chemical corridor** --- Chemical tank car movements originating along the Louisiana/Texas petrochemical belt, primarily via UP, BNSF, NS, and CSX.
- **Appalachian coal fields to Eastern seaboard** --- NS and CSX move thermal and metallurgical coal from West Virginia, Kentucky, and Virginia to domestic utilities and export terminals (Hampton Roads, Baltimore).
- **Chicago gateway** --- The nation's most congested rail hub, where six of seven Class I railroads interchange traffic. Approximately 25% of all US rail freight passes through the Chicago terminal area.

---

## 4.3 STB Uniform Rail Costing System (URCS) Methodology

The Surface Transportation Board maintains the **Uniform Rail Costing System (URCS)** as the regulatory standard for estimating railroad variable costs. URCS is central to rate reasonableness proceedings, revenue adequacy determinations, and competitive access disputes. Analysts building commodity-specific logistics cost models should understand its structure.

### Variable Cost Components

URCS decomposes railroad variable costs into three primary unit cost drivers:

| Cost Component | Unit of Measure | What It Captures |
|---|---|---|
| **Car-mile costs** | $ per car-mile | Costs that vary with the number of loaded and empty car-miles: car ownership/leasing, car maintenance, switching |
| **Train-mile costs** | $ per train-mile | Costs that vary with train movement: locomotive fuel, crew wages, locomotive maintenance, dispatching |
| **Gross-ton-mile (GTM) costs** | $ per gross-ton-mile | Costs that vary with weight over distance: rail and tie wear, roadbed maintenance, bridge stress |

Additional cost elements include:

- **Terminal costs** --- Switching, classification, inspection at origin and destination yards
- **Administrative overhead allocation** --- A percentage markup applied to direct variable costs
- **Loss and damage** --- Commodity-specific claim rates

### Regional Cost Variations

URCS calculates separate cost sets for **Eastern** and **Western** regions (divided approximately at the Mississippi River), reflecting structural differences in:

- **Terrain and grade profiles** --- Western railroads contend with mountain grades (e.g., Donner Pass, Raton Pass, Stampede Pass) that increase fuel consumption and limit train tonnage. Eastern railroads face the Appalachian grades but generally operate on flatter profiles in the Midwest corridor.
- **Labor cost differentials** --- Wage rates and crew-consist agreements vary by region and carrier.
- **Traffic density** --- Higher-density Western mainlines spread fixed-cost infrastructure over more gross-ton-miles, potentially lowering per-unit variable costs for GTM-driven components.
- **Equipment mix** --- The Western network handles proportionally more unit-train bulk traffic (coal, grain), while the Eastern network has a higher share of manifest (mixed-car) and intermodal traffic.

### Using the `rail_cost_model` Toolset

The `rail_cost_model` toolset referenced in this report series implements URCS-based calculations for estimating shipment-level variable costs. Key inputs include:

- **Origin and destination (O-D) pair** --- Specified by railroad junction codes or geographic coordinates, mapped to the NARN network
- **Commodity STCC code** --- Determines car type, loading characteristics, and loss/damage factors
- **Car type and capacity** --- Covered hopper, open-top hopper, tank car, gondola, etc.
- **Train type** --- Unit train vs. manifest service (unit trains receive lower per-car costs due to reduced switching)
- **Number of cars and lading weight** --- Used to compute gross trailing tons and GTM

The toolset outputs variable cost per car, per ton, and per ton-mile, along with a breakdown by URCS cost component. These outputs serve as the denominator in Revenue-to-Variable-Cost (R/VC) ratio calculations discussed in Section 4.5.

---

## 4.4 Public Use Waybill Sample

The STB's **Public Use Waybill Sample** is the most comprehensive publicly available dataset on US rail freight movements. It is a stratified sample of carload waybills filed by Class I railroads, released annually (with a typical two-year lag).

### Dataset Structure

Each record in the Waybill Sample contains:

- **Origin and destination BEA areas** --- Geographic coding at the Bureau of Economic Analysis area level (not precise station-level, to protect shipper confidentiality)
- **STCC commodity code** --- Standard Transportation Commodity Code identifying the lading
- **Car type and count** --- Equipment used for the shipment
- **Tons and revenue** --- Total tonnage and freight charges
- **Expansion factor** --- A statistical weight used to scale sample records to the full population of carloads

### Carload Statistics and Commodity Mix

The Waybill Sample enables analysis of:

- **Volume trends** --- Year-over-year changes in carloads and tonnage by commodity group
- **Revenue per ton-mile** --- Average rate benchmarks by commodity, equipment type, and O-D pair
- **Origin-destination flow patterns** --- Identification of dominant shipping lanes for specific commodities
- **Carrier market share** --- Distribution of traffic among Class I railroads on competitive corridors

### Limitations

- Geographic granularity is limited to BEA areas (not individual stations or facilities)
- Confidential contract rates may be masked or aggregated
- The two-year publication lag means the most recent data reflects conditions from prior years
- Short-line and regional railroad movements are not included unless they involve a Class I carrier as part of a through-movement

---

## 4.5 Rail Rate Benchmarks: Revenue-to-Variable-Cost Ratios

The **Revenue-to-Variable-Cost (R/VC) ratio** is the principal regulatory and analytical metric for assessing railroad pricing relative to cost. It is computed as:

> **R/VC Ratio = Total Revenue for Shipment / URCS Variable Cost for Shipment**

### Interpretation

| R/VC Ratio | Interpretation |
|---|---|
| < 1.0 | Below variable cost --- railroad loses money on each shipment (rare in practice) |
| 1.0 | Revenue equals variable cost --- no contribution to fixed costs or profit |
| 1.0 -- 1.8 | Competitive pricing; limited regulatory concern |
| 1.8 ("180% of variable cost") | STB jurisdictional threshold --- above this level, a shipper may file a rate reasonableness complaint |
| > 3.0 | Potentially captive shipper situation; high regulatory scrutiny |

### R/VC Ratios by Commodity Group

Typical R/VC ratios vary significantly by commodity, reflecting differences in competitive alternatives, demand elasticity, and shipment characteristics:

| STCC Code | Commodity Group | Typical R/VC Range | Notes |
|---|---|---|---|
| 01 | Farm Products (grain) | 1.5 -- 2.5 | Highly seasonal; competitive with barge on major river corridors |
| 11 | Coal | 1.5 -- 3.5+ | Wide range reflects captive vs. competitively served mines; declining volumes |
| 28 | Chemicals & Allied Products | 2.0 -- 3.5 | Includes plastics, fertilizers, industrial chemicals; hazmat surcharges apply |
| 32 | Stone, Clay, Glass Products | 1.8 -- 3.0 | Aggregates, cement, glass; often short-haul with limited modal alternatives |
| 29 | Petroleum & Coal Products | 1.5 -- 2.5 | Includes crude-by-rail; volumes fluctuate with pipeline capacity and spreads |
| 14 | Nonmetallic Minerals | 1.5 -- 2.5 | Potash, soda ash, phosphate rock |

These benchmarks are derived from Waybill Sample analysis and STB annual reporting. Commodity-specific chapters in this report series will develop more granular R/VC analysis using the `rail_cost_model` toolset.

---

## 4.6 STCC Commodity Codes Relevant to Bulk

The **Standard Transportation Commodity Code (STCC)** system is the classification framework used in railroad waybills and regulatory filings. The following two-digit groups are most relevant to bulk supply chain analysis:

| STCC Group | Description | Typical Rail Equipment | Key Sub-Commodities |
|---|---|---|---|
| 01 | Farm Products | Covered hoppers (grain); refrigerated cars (produce) | Wheat, corn, soybeans, rice, cotton |
| 10 | Metallic Ores | Open-top hoppers, gondolas | Iron ore, copper ore, zinc ore |
| 11 | Coal | Open-top hoppers (unit trains) | Bituminous, sub-bituminous, anthracite, lignite |
| 14 | Nonmetallic Minerals (except fuels) | Covered hoppers, open-top hoppers | Potash, soda ash, phosphate rock, sand/gravel |
| 20 | Food & Kindred Products | Covered hoppers, tank cars | Sugar, corn syrup, vegetable oils, animal feed |
| 28 | Chemicals & Allied Products | Tank cars, covered hoppers | Fertilizers (urea, ammonium nitrate), plastics, industrial chemicals |
| 29 | Petroleum & Coal Products | Tank cars | Crude oil, refined products, asphalt, petroleum coke |
| 32 | Stone, Clay, Glass Products | Open-top hoppers, gondolas, covered hoppers | Cement, aggregates, flat glass, gypsum |
| 33 | Primary Metal Products | Gondolas, coil cars | Steel slabs, coils, billets, aluminum ingots |

Each commodity-specific chapter will map relevant STCC sub-codes to supply chain flows, equipment requirements, and cost parameters.

---

## 4.7 Rail-Served Terminal Infrastructure

Efficient loading and unloading at origin and destination terminals is critical to bulk rail economics. Terminal design and throughput capacity directly affect car cycle times, demurrage costs, and overall supply chain velocity.

### Terminal Types

- **Unit train loadout facilities** --- Designed to load 100--150 car trains without stopping (loop track configuration) or with rapid batch loading. Common for coal, grain, and potash. Loadout rates of 3,000--5,000 tons per hour are typical at modern facilities.
- **Manifest service terminals** --- Classification yards where individual cars or blocks of cars are sorted and assembled into outbound trains. Key yards include Bailey Yard (North Platte, NE --- UP), Roseville Yard (CA --- UP), and Selkirk Yard (NY --- CSX).
- **Transload facilities** --- Points where commodities are transferred between rail cars and trucks, typically for last-mile delivery to customers not directly served by rail. Critical for chemicals, building materials, and agricultural products.
- **Port and export terminals** --- Rail-served facilities at coastal and river ports where bulk commodities are transferred to or from vessels. Major examples include Hampton Roads coal terminals (NS/CSX), PNW grain export elevators (BNSF/UP), and Houston-area petrochemical terminals.
- **Unit train unloading (dumper) facilities** --- Rotary dumpers, bottom-dump pits, and tilt-unload systems at power plants, steel mills, and processing facilities.

### Demurrage and Accessorial Charges

Railroads assess **demurrage** charges when cars are held at shipper or receiver facilities beyond allowed free time (typically 24--48 hours). Recent years have seen significant increases in demurrage rates ($75--$150+ per car per day) and tightened free-time allowances, making terminal efficiency a major cost factor in bulk supply chains. The STB has issued rulemaking on demurrage billing practices, requiring greater transparency and dispute resolution mechanisms.

---

## 4.8 STB Regulatory Environment

The Surface Transportation Board, an independent federal agency, exercises economic regulation over freight railroads. Several ongoing and recent regulatory proceedings are directly relevant to bulk commodity shippers.

### Reciprocal Switching

The STB has proposed rules to expand **reciprocal switching** --- a regulatory remedy that would require a railroad serving a facility to switch traffic to a competing railroad at a prescribed rate, effectively providing captive shippers access to a second carrier. Key elements of the proposal include:

- Applicability to facilities served by only one Class I railroad within a defined terminal area
- Prescribed switching charges based on STB-determined costs
- Distance limitations (proposed switching radius of approximately 30 statute miles)
- Potential to reduce R/VC ratios for captive shippers by introducing competitive alternatives

The railroad industry has vigorously opposed the proposal, arguing it would undermine investment incentives and network efficiency. Shipper groups have strongly supported it. As of the current reporting period, final rulemaking remains pending.

### Rate Reasonableness

Shippers paying rates above the 180% R/VC jurisdictional threshold may challenge rates before the STB through several procedural tracks:

- **Full Stand-Alone Cost (SAC) test** --- A comprehensive (and expensive) proceeding in which the complainant must demonstrate that a hypothetically efficient railroad could serve the traffic at a lower rate. Historically used only in major coal rate cases.
- **Simplified SAC** --- A streamlined version with lower evidentiary burdens, applicable to cases involving $5 million or less in annual rate relief.
- **Final Offer Rate Review (FORR)** --- A "baseball arbitration" approach where the STB selects between the shipper's and railroad's proposed rate. Designed for smaller disputes.
- **Three-Benchmark methodology** --- A newer, simplified approach using comparable traffic benchmarks to assess rate reasonableness.

### Revenue Adequacy

The STB annually determines whether each Class I railroad is **revenue adequate** --- that is, whether its return on investment equals or exceeds the railroad industry's cost of capital. Revenue adequacy findings are relevant because the STB is directed by statute to balance shipper protection against the need for railroads to earn adequate revenues to maintain and invest in their networks.

---

## 4.9 Data Sources and References

| Source | Description | Update Frequency |
|---|---|---|
| STB Uniform Rail Costing System (URCS) | Variable cost estimation methodology and cost tables | Annual |
| STB Public Use Waybill Sample | Stratified sample of Class I carload waybills | Annual (2-year lag) |
| NTAD / NARN | National rail network GIS shapefiles | Annual |
| AAR Railroad Facts | Industry-level statistics on Class I railroads | Annual |
| STB Annual Report | Regulatory proceedings, revenue adequacy findings | Annual |
| FRA Safety Data | Track classification, accident/incident data | Ongoing |
| `rail_cost_model` toolset | URCS-based shipment cost calculations | Internal toolset |

All distance measurements in this chapter are expressed in **statute miles** (5,280 feet), consistent with US railroad industry convention.

---

## Implications for Commodity Analysis

The railroad network analysis presented in this chapter establishes several foundational parameters for the commodity-specific chapters that follow:

1. **Cost estimation framework** --- The URCS methodology and `rail_cost_model` toolset provide a consistent, defensible approach for estimating railroad variable costs for any commodity. Subsequent chapters will apply these tools with commodity-specific STCC codes, car types, and loading parameters.

2. **Rate benchmarking** --- R/VC ratios from the Waybill Sample establish baseline expectations for railroad pricing by commodity group. Commodities with high R/VC ratios (coal to captive utilities, chemicals from single-served plants) face different supply chain economics than competitively served commodities (grain with barge alternatives).

3. **Network geography** --- The Western duopoly (BNSF/UP) and Eastern duopoly (CSX/NS) structure means that for many origin-destination pairs, shippers have at most two Class I carrier options, and frequently only one. This competitive structure directly influences rates and service quality.

4. **Regulatory dynamics** --- Pending reciprocal switching rules and evolving rate reasonableness procedures may materially alter the economics of rail-dependent bulk supply chains. Commodity chapters will flag specific corridors and commodities most likely to be affected.

5. **Terminal infrastructure** --- The efficiency and capacity of rail-served loading, unloading, and transload facilities are often the binding constraint on supply chain throughput. Commodity chapters will inventory key terminal facilities and assess capacity relative to demand.

6. **Modal competition** --- Rail rates and service levels are disciplined by competition from barge transportation (on river-served corridors), trucking (for short-haul movements), and pipelines (for liquid commodities). Chapter 5 explores these intermodal dynamics in detail.
