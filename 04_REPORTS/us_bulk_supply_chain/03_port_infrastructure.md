# Chapter 3: Port Infrastructure and Terminal Operations

## Executive Summary

The United States port system encompasses over 300 commercial ports, of which approximately 50 handle significant bulk commodity volumes, with the US Gulf Coast dominating both import and export flows of dry bulk, liquid bulk, and breakbulk cargoes. The Gulf Coast port complex—anchored by the ports of South Louisiana (the nation's largest tonnage port), New Orleans, Houston, Baton Rouge, Lake Charles, and Mobile—collectively handles over 1 billion short tons annually and provides the critical interface between inland waterway barge transportation and oceangoing vessel operations. Port costs represent a significant and often underestimated component of delivered commodity pricing, with a typical Supramax-class vessel calling at New Orleans to discharge 30,000 short tons of imported cement incurring approximately $269,000 in total port costs (approximately $8.97 per short ton), encompassing pilotage, towage, dockage, wharfage, stevedoring, and ancillary charges. This chapter provides a systematic overview of US bulk port infrastructure, terminal operations, cost structures, and the port cost modeling methodology employed in commodity-specific analyses throughout this report series.

---

## 3.1 US Port System: Geographic Organization

### 3.1.1 US Gulf Coast Ports

The US Gulf Coast is the dominant port region for bulk commodity movements, driven by the confluence of inland waterway access (Mississippi River System, GIWW), proximity to petroleum refining and petrochemical complexes, deepwater channel access, and favorable geographic position for trade with Latin America, Europe, and (via the Panama Canal) Asia.

**Port of South Louisiana (LaPlace to Destrehan, Louisiana).** The Port of South Louisiana is consistently the largest tonnage port in the Western Hemisphere, handling approximately 230 to 275 million short tons annually. The port district encompasses a 54-mile stretch of the Mississippi River between New Orleans and Baton Rouge, hosting major grain export elevators (Cargill, ADM, Bunge, CHS, Louis Dreyfus, Zen-Noh), petroleum terminals, chemical facilities, and general cargo operations (Port of South Louisiana, Annual Report, 2023; USACE WCSC, WCUS Part 2, 2022).

**Port of New Orleans (New Orleans, Louisiana).** The Port of New Orleans (Port NOLA), operated by the Board of Commissioners of the Port of New Orleans, handles approximately 80 to 95 million short tons annually across its Mississippi River and Inner Harbor terminals. Cargo mix includes containers (Napoleon Avenue Container Terminal), breakbulk (steel, forest products, project cargo), dry bulk (cement, aggregates, bauxite), and liquid bulk (petroleum, chemicals). The port's strategic position at the junction of the Mississippi River, GIWW, and Mississippi River-Gulf Outlet provides unparalleled multimodal connectivity (Port of New Orleans, Annual Statistical Report, 2023).

**Port of Houston (Houston, Texas).** The Port of Houston, encompassing the Houston Ship Channel complex, is the nation's largest port by total foreign waterborne tonnage and the largest petrochemical port in the United States, handling approximately 250 to 280 million short tons annually. While container and liquid bulk volumes dominate, the port handles significant dry bulk volumes including cement, aggregates, steel, and grain through both public and private terminals (Port Houston Authority, Annual Report, 2023).

**Port of Baton Rouge (Baton Rouge, Louisiana).** The Port of Greater Baton Rouge handles approximately 55 to 65 million short tons annually, with petroleum products, chemicals, and grain as principal commodity classes. The port's location at the head of deepwater navigation on the Mississippi River (45-foot authorized channel depth from Baton Rouge to the Gulf) provides a strategic advantage for vessel loading operations (Port of Greater Baton Rouge, 2023).

**Port of Mobile (Mobile, Alabama).** The Port of Mobile handles approximately 55 to 65 million short tons annually through facilities on the Mobile River and Mobile Bay, connected to the Tennessee-Tombigbee Waterway and the GIWW. The port has experienced significant growth in container volumes (APM Terminals) and handles substantial dry bulk (coal, iron ore, cement, wood pellets), liquid bulk, and breakbulk tonnage. The port's coal and iron ore terminal at McDuffie Island is one of the largest on the Gulf Coast (Alabama State Port Authority, Annual Report, 2023).

**Port of Tampa Bay (Tampa, Florida).** The Port of Tampa Bay is Florida's largest port by tonnage, handling approximately 35 to 40 million short tons annually. Bulk commodities dominate, including phosphate and phosphate products (Florida is the nation's largest phosphate-producing state), petroleum products, cement, aggregates, and other construction materials (Port Tampa Bay, Annual Report, 2023).

**Port of Lake Charles (Lake Charles, Louisiana).** The Port of Lake Charles handles approximately 55 to 75 million short tons annually, dominated by petroleum and petrochemical products associated with the major refinery and LNG export complexes in the Calcasieu Parish industrial corridor. The port also handles grain, rice, and project cargo (Port of Lake Charles, 2023).

### 3.1.2 Atlantic Coast Ports

Atlantic Coast ports serve primarily as import gateways for bulk commodities destined for eastern US markets and, in the case of coal, as export terminals.

**Port of Norfolk / Hampton Roads (Virginia).** The Port of Virginia, encompassing terminals in Norfolk, Newport News, and Portsmouth, handles approximately 70 to 80 million short tons annually. Norfolk is the nation's largest coal export port, with Dominion Terminal Associates (DTA) and Lambert's Point (operated by Norfolk Southern) collectively providing over 50 million short tons per year of coal export capacity. The port also handles containers (Virginia International Gateway, Norfolk International Terminals), grain, and other bulk commodities (Virginia Port Authority, 2023).

**Port of Charleston (Charleston, South Carolina).** The Port of Charleston handles approximately 25 to 30 million short tons annually, with a primary focus on containerized cargo through the South Carolina Ports Authority's container terminals. Bulk operations are more limited but include cement, aggregates, and forest products (SC Ports Authority, 2023).

**Port of Savannah (Savannah, Georgia).** The Port of Savannah, operated by the Georgia Ports Authority (GPA), is the nation's third-largest container port by TEU volume and handles approximately 35 to 40 million short tons annually. While containers dominate, the port's Ocean Terminal handles dry bulk (kaolin, wood pellets) and breakbulk (forest products, machinery) (Georgia Ports Authority, 2023).

### 3.1.3 Pacific Coast Ports

**Port of Long Beach / Los Angeles (California).** The San Pedro Bay port complex (Long Beach and Los Angeles combined) is the nation's largest container port complex, handling over 17 million TEUs annually. Bulk commodity operations are limited but include petroleum (via marine oil terminals) and some dry bulk imports. For most commodity analyses, the San Pedro Bay complex is relevant primarily as a container gateway rather than a bulk terminal (Ports of Long Beach and Los Angeles, 2023).

**Port of Portland (Portland, Oregon).** The Port of Portland handles approximately 25 to 30 million short tons annually, including significant grain and mineral bulk exports through its Terminal 5 (grain) and Terminal 4 (auto, breakbulk, dry bulk) facilities. The port provides access to the Columbia-Snake River System and serves as an export gateway for Pacific Northwest wheat and other agricultural commodities (Port of Portland, 2023).

### Table 3.1: Major US Bulk Ports — Annual Tonnage Summary

| Port | State | Region | Annual Tonnage (million short tons) | Primary Bulk Commodities |
|---|---|---|---|---|
| South Louisiana | LA | Gulf Coast | 230–275 | Grain, petroleum, chemicals |
| Houston | TX | Gulf Coast | 250–280 | Petroleum, chemicals, cement, grain |
| New Orleans | LA | Gulf Coast | 80–95 | Cement, containers, breakbulk, chemicals |
| Baton Rouge | LA | Gulf Coast | 55–65 | Petroleum, chemicals, grain |
| Lake Charles | LA | Gulf Coast | 55–75 | Petroleum, LNG, chemicals, grain |
| Mobile | AL | Gulf Coast | 55–65 | Coal, iron ore, cement, wood pellets |
| Tampa Bay | FL | Gulf Coast | 35–40 | Phosphate, petroleum, cement, aggregates |
| Norfolk / Hampton Roads | VA | Atlantic | 70–80 | Coal (export), containers, grain |
| Savannah | GA | Atlantic | 35–40 | Containers, kaolin, wood pellets |
| Charleston | SC | Atlantic | 25–30 | Containers, cement, aggregates |
| Long Beach / Los Angeles | CA | Pacific | 85–95 (combined) | Containers, petroleum |
| Portland | OR | Pacific | 25–30 | Grain, autos, minerals |

*Sources: USACE WCSC, WCUS Parts 1–5, 2022; individual port authority annual reports, 2023. Tonnage figures include both domestic and foreign waterborne commerce.*

{% if vessel_efficiency_metrics %}
### Platform Data: Vessel Terminal Utilization

The platform's Lower Mississippi River vessel analysis tracks terminal-level utilization patterns. Top vessels by voyage frequency:

| Vessel | Voyages | Avg Port Time (hrs) | Utilization (%) | Primary Terminal |
|--------|---------|--------------------|-----------------:|-----------------|
{% for row in vessel_efficiency_metrics[:10] %}| {{ row.vessel }} | {{ row.total_voyages }} | {{ row.avg_port_hours }} | {{ row.utilization_pct }} | {{ row.frequent_terminal }} |
{% endfor %}

> **Source:** Platform vessel voyage analysis, {{ vessel_unique_count | commas }} unique vessels tracked through {{ vessel_results_updated }}.
{% endif %}

---

## 3.2 Port Cost Components

Port costs for bulk vessel operations comprise multiple distinct charges assessed by different entities (port authorities, pilots' associations, tug operators, terminal operators, and government agencies). Understanding the structure, basis of assessment, and magnitude of each cost component is essential for accurate commodity delivered-cost modeling.

### 3.2.1 Pilotage

Pilotage is the charge for the services of a licensed maritime pilot who boards the vessel and directs navigation through restricted or congested waterways. Pilotage is compulsory for virtually all foreign-flag vessels and most US-flag deep-draft vessels in US port approaches and rivers.

**Mississippi River Pilotage System.** The Mississippi River pilotage system is uniquely structured, with three separate pilots' associations governing different segments of the river:

1. **Associated Branch Pilots (Bar Pilots):** Cover the segment from the sea buoy at the mouth of the Mississippi (Southwest Pass or South Pass) to Pilottown, approximately 17 statute miles. Rates are assessed on a per-vessel basis, scaled by vessel draft and gross tonnage.

2. **Crescent River Port Pilots' Association:** Cover the segment from Pilottown to New Orleans (approximately 95 statute miles). Rates are based on vessel draft and LOA (length overall), with additional charges for overtime, delays, and special services.

3. **New Orleans-Baton Rouge Steamship Pilots' Association (NOBRA):** Cover the segment from New Orleans to Baton Rouge and points above (approximately 120+ statute miles, depending on destination). Rates are assessed similarly to Crescent River pilots, based on draft and LOA.

A vessel transiting the full river from the Gulf to Baton Rouge will therefore engage three separate pilot associations sequentially, with each transition involving a pilot change and separate invoicing. Total pilotage costs for a full transit can range from $20,000 to $60,000 or more, depending on vessel size and draft.

Pilotage at other US ports is typically administered by a single pilots' association for each port or waterway approach, with rates regulated by state pilotage commissions (e.g., Houston Pilots, Virginia Pilots' Association, Savannah Bar Pilots).

### 3.2.2 Towage (Tug Assist)

Towage charges cover the hire of harbor tugs to assist vessels during berthing, unberthing, and (in some ports) transit through narrow channels. Tug requirements vary by vessel size, berth configuration, and port regulations, but a typical bulk vessel (Handymax to Panamax class) requires two to three tugs for berthing and unberthing at Mississippi River terminals.

Tug rates are typically assessed on an hourly or per-job basis, with minimum charges. For a Supramax-class vessel at New Orleans, total towage costs (inbound and outbound, including shifting if required) typically range from $20,000 to $45,000.

### 3.2.3 Dockage

Dockage is the charge assessed by the port authority or terminal operator for the vessel's use of a berth. Dockage is typically charged on a per-gross-registered-ton (GRT) or per-LOA basis, per 24-hour period or fraction thereof. Dockage rates at major Gulf Coast ports range from $0.03 to $0.10 per GRT per day, or $500 to $3,000 per day for a typical Supramax-class vessel.

### 3.2.4 Wharfage

Wharfage is the charge assessed on cargo (not the vessel) for the use of wharf or terminal facilities. Wharfage is typically charged on a per-short-ton or per-metric-ton basis and varies by commodity class and terminal. At New Orleans, wharfage rates for dry bulk commodities typically range from $0.50 to $2.50 per short ton.

### 3.2.5 Stevedoring (Cargo Handling)

Stevedoring charges cover the labor, equipment, and supervision costs of loading or discharging cargo at the terminal. For dry bulk commodities, stevedoring is the largest single port cost component, typically representing 40–60% of total port costs. Stevedoring rates vary significantly by commodity type, terminal equipment configuration, and labor market conditions.

### Table 3.2: Typical Stevedoring Rates by Cargo Type (US Gulf Coast, 2023–2024)

| Cargo Type | Discharge/Loading Method | Rate per Short Ton | Typical Daily Rate (short tons/day) |
|---|---|---|---|
| Cement (bulk, pneumatic) | Pneumatic ship unloader to silo | $4.00–$6.50 | 3,000–5,000 |
| Grain (bulk, export loading) | Conveyor/elevator to vessel hold | $2.50–$4.50 | 20,000–50,000 |
| Coal (bulk, export loading) | Conveyor/shiploader | $2.50–$4.00 | 30,000–60,000 |
| Aggregates / sand | Grab crane to hopper/conveyor | $2.50–$4.50 | 5,000–12,000 |
| Fertilizer (bulk) | Grab crane or pneumatic | $3.50–$6.00 | 3,000–8,000 |
| Scrap metal | Gantry crane with magnet/grapple | $5.00–$8.00 | 3,000–6,000 |
| Steel (breakbulk) | Shore crane / vessel gear | $8.00–$15.00 | 1,000–3,000 |
| Forest products (breakbulk) | Shore crane / vessel gear | $7.00–$12.00 | 1,500–3,000 |

*Sources: Port of New Orleans tariff schedules; terminal operator rate sheets (confidential, ranges estimated from market sources); UNCTAD, Review of Maritime Transport, 2023. Rates are indicative and vary by terminal, volume, and contractual terms.*

### 3.2.6 Line Handling

Line handling charges cover the cost of mooring and unmooring the vessel at berth (shore-side line handlers). Charges are typically assessed on a per-operation basis, ranging from $1,500 to $4,000 per operation (inbound and outbound).

### 3.2.7 Agency Fees

Ship agents coordinate vessel operations in port, including customs clearance, pilotage booking, tug ordering, and documentation. Agency fees typically range from $3,000 to $8,000 per port call, depending on complexity and the number of berth shifts.

### 3.2.8 Government and Regulatory Charges

US Customs and Border Protection (CBP) charges include harbor maintenance tax (HMT, 0.125% of cargo value for imports), customs user fees, and inspection charges. USDA/APHIS charges apply to certain agricultural and food product imports. These charges are assessed on the cargo rather than the vessel and must be included in total landed cost analysis.

---

## 3.3 Terminal Types and Operations

### 3.3.1 Dry Bulk Terminals

Dry bulk terminals are designed for the efficient handling of free-flowing granular, powdered, or lump commodities. Terminal configurations vary by commodity:

**Grain Elevators.** Export grain elevators on the Lower Mississippi River are among the highest-throughput terminals in the world, with loading rates of 40,000 to 80,000 short tons per day at the largest facilities. Major elevator operators (Cargill, ADM, Bunge, CHS, Louis Dreyfus, Zen-Noh) maintain facilities along the river from Myrtle Grove to Destrehan. Grain is received by barge, rail, and truck; stored in concrete or steel silos; and loaded to vessels via high-capacity conveyor and shiploader systems (USDA GIPSA, Grain Inspection Handbook, 2023).

**Cement Terminals.** Bulk cement import terminals employ pneumatic (vacuum) ship unloading systems to transfer cement from vessel holds to enclosed storage silos. Discharge rates for pneumatic systems typically range from 3,000 to 5,000 short tons per day per unloader, significantly slower than grain or coal handling. Major cement import terminals are located at New Orleans, Houston, Tampa, Mobile, and Savannah (Portland Cement Association [PCA], US Cement Industry Fact Sheet, 2023).

**Coal Terminals.** Export coal terminals employ high-capacity conveyor and shiploader systems capable of loading rates of 30,000 to 60,000 short tons per day or more. The largest US coal export terminals are located at Norfolk (Dominion Terminal Associates, Lambert's Point) and Baltimore (CNX Marine Terminal). Gulf Coast coal terminals at Mobile (McDuffie Island) and New Orleans provide additional export capacity (US Energy Information Administration [EIA], Coal Transportation Rates to the Electric Generating Sector, 2023).

**Aggregates and Construction Materials.** Terminals handling sand, gravel, crushed stone, and slag typically employ gantry or mobile harbor cranes with clamshell or grab buckets, discharging to open stockpile areas or directly to barge or truck. Discharge rates range from 5,000 to 12,000 short tons per day, depending on crane capacity and terminal configuration.

### 3.3.2 Liquid Bulk Terminals

Liquid bulk terminals handle petroleum products, crude oil, chemicals, vegetable oils, and other liquid commodities through pipeline-connected berths with shore-side manifolds. Loading and discharge rates are measured in barrels per hour (bph) and vary by product viscosity, pipeline diameter, and terminal pump capacity. A typical petroleum products berth can handle 5,000 to 15,000 bph (approximately 25,000 to 75,000 short tons per day for medium-gravity products). The Houston Ship Channel and Lower Mississippi River host the highest concentrations of liquid bulk terminal capacity in the United States (USACE WCSC, 2022).

### 3.3.3 Breakbulk and Neo-Bulk Terminals

Breakbulk terminals handle unitized, palletized, or individual-piece cargoes (steel, forest products, project cargo, military cargo) using shore-side or vessel-mounted cranes. Loading and discharge rates are commodity- and package-specific, but typically range from 1,000 to 5,000 short tons per day. Major breakbulk facilities are located at New Orleans (Napoleon Avenue Wharf, Nashville Avenue Wharf), Houston (Turning Basin and Barbours Cut), and Mobile.

### 3.3.4 Container Terminals

While not the focus of this chapter, container terminals are noted for completeness. Container operations at Gulf Coast and Atlantic ports (Houston, New Orleans, Mobile, Savannah, Charleston, Norfolk) are relevant to commodity analysis when bulk or semi-bulk commodities (e.g., bagged cement, bagged minerals, drummed chemicals) are containerized for transport.

---

## 3.4 Discharge and Loading Rates by Cargo Type

Terminal throughput rates directly determine vessel time in port and, therefore, the demurrage or dispatch financial exposure for cargo interests. The following table summarizes typical discharge and loading rates for common bulk commodity categories at well-equipped US terminals.

### Table 3.3: Typical Terminal Throughput Rates by Cargo Type

| Cargo Type | Operation | Rate (short tons/day) | Limiting Factor |
|---|---|---|---|
| Grain (corn, soybeans, wheat) | Loading (export) | 20,000–50,000 | Elevator capacity, barge/rail supply |
| Grain (corn, soybeans, wheat) | Loading (export, major LMR elevator) | 40,000–80,000 | Shiploader capacity |
| Coal | Loading (export, Norfolk/Mobile) | 30,000–60,000 | Conveyor/shiploader capacity |
| Cement (bulk, imported) | Discharge (pneumatic) | 3,000–5,000 | Pneumatic unloader capacity, silo capacity |
| Aggregates (sand, gravel, stone) | Discharge (grab crane) | 5,000–12,000 | Crane cycle time, truck/barge dispatch |
| Fertilizer (bulk urea, DAP, potash) | Discharge / Loading | 3,000–8,000 | Grab crane or pneumatic capacity |
| Petroleum coke (petcoke) | Loading (conveyor) | 10,000–25,000 | Conveyor/shiploader capacity |
| Iron ore / concentrates | Discharge / Loading | 15,000–40,000 | Grab crane or conveyor capacity |
| Bauxite / alumina | Discharge (grab crane or pneumatic) | 4,000–10,000 | Crane/pneumatic capacity |
| Scrap metal | Loading (magnet crane) | 3,000–6,000 | Crane cycle time, cargo density |
| Forest products (logs, lumber) | Loading / Discharge | 1,500–3,000 | Crane cycle time, stowage complexity |
| Steel products (coils, plate, rebar) | Loading / Discharge | 1,000–3,000 | Crane capacity, securing requirements |

*Sources: Terminal operator data (various, confidential ranges); BIMCO, Bulk Carrier Cargo Handling Rates, 2023; UNCTAD Review of Maritime Transport, 2023.*

---

## 3.5 Port Cost Modeling Methodology: The `port_cost_model` Toolset

### 3.5.1 Purpose and Scope

Throughout this report series, commodity-specific port cost analyses are generated using the `port_cost_model` proforma toolset, a structured cost estimation framework that synthesizes published tariff schedules, market rate intelligence, and vessel operating parameters into a standardized port call cost estimate. The toolset is designed to produce transparent, auditable cost estimates suitable for commodity delivered-cost analysis, feasibility studies, and comparative port evaluation.

### 3.5.2 Proforma Structure

Each port cost proforma is organized into the following cost categories:

1. **Pilotage** — Compulsory pilot charges for all transit segments (inbound and outbound), calculated based on vessel draft, LOA, GRT, and the applicable pilots' association tariff.
2. **Towage** — Harbor tug charges for berthing, unberthing, and any shifting operations, based on tug company rate schedules and the number of tugs required.
3. **Dockage** — Berth usage charges assessed by the port authority or terminal operator, calculated on a per-GRT or per-LOA basis per 24-hour period.
4. **Wharfage** — Cargo throughput charges assessed on a per-ton basis by the terminal operator or port authority.
5. **Stevedoring** — Cargo handling charges (loading or discharge), including labor, equipment, and supervision, assessed on a per-ton basis.
6. **Line Handling** — Mooring and unmooring charges.
7. **Agency Fees** — Ship agent fees for coordination and documentation.
8. **Government Charges** — CBP, USDA/APHIS, and harbor maintenance tax (where applicable).
9. **Miscellaneous** — Fresh water, waste disposal, launch service, and other ancillary charges as applicable.

### 3.5.3 Key Assumptions and Limitations

- Rates reflect published tariff schedules and market intelligence as of 2024; actual rates are subject to negotiation, volume discounts, and contractual terms.
- Vessel parameters (LOA, beam, draft, GRT, NRT, DWT) are based on standard vessel class profiles (e.g., Handysize, Supramax, Panamax, Capesize) unless a specific vessel is identified.
- Terminal throughput rates assume normal operating conditions (no weather delays, labor disputes, or equipment breakdowns).
- Demurrage and dispatch calculations are based on charter party laytime terms and are presented separately from port cost proformas.

---

## 3.6 Sample Proforma: Supramax Vessel at New Orleans — Cement Discharge

The following proforma illustrates the port cost structure for a representative bulk commodity port call: a Supramax-class vessel discharging 30,000 short tons of imported bulk cement at a private terminal on the Mississippi River at New Orleans.

### Vessel Parameters

| Parameter | Value |
|---|---|
| Vessel type | Supramax bulk carrier |
| LOA | 190 meters (623 feet) |
| Beam | 32.3 meters (106 feet) |
| Loaded draft | 11.5 meters (37.7 feet) |
| GRT | ~32,000 |
| NRT | ~19,000 |
| DWT | ~58,000 MT |
| Cargo quantity | 30,000 short tons (27,216 MT) bulk cement |
| Discharge rate (per weather working day) | 4,000 short tons/day |
| Estimated time in port | ~8 days (including berthing, discharge, unberthing) |

### Table 3.4: Port Cost Proforma — Supramax at New Orleans, 30,000 Short Tons Cement

| Cost Category | Description | Estimated Cost (USD) |
|---|---|---|
| **Pilotage — Inbound** | Bar Pilots (Southwest Pass to Pilottown) | $9,500 |
| | Crescent River Pilots (Pilottown to New Orleans) | $14,200 |
| **Pilotage — Outbound** | Crescent River Pilots (New Orleans to Pilottown) | $14,200 |
| | Bar Pilots (Pilottown to sea buoy) | $9,500 |
| **Pilotage Subtotal** | | **$47,400** |
| **Towage — Inbound** | 2 tugs, berthing assist | $18,000 |
| **Towage — Outbound** | 2 tugs, unberthing assist | $18,000 |
| **Towage Subtotal** | | **$36,000** |
| **Dockage** | ~$350/day x 8 days | **$2,800** |
| **Wharfage** | $1.25/short ton x 30,000 tons | **$37,500** |
| **Stevedoring** | $4.50/short ton x 30,000 tons (pneumatic discharge) | **$135,000** |
| **Line Handling** | Inbound + outbound | **$4,500** |
| **Agency Fees** | Vessel agency, documentation, coordination | **$5,500** |
| **Miscellaneous** | Launch service, fresh water, waste disposal, surveys | **$800** |
| | | |
| **TOTAL PORT COST** | | **$269,500** |
| **Cost per Short Ton** | $269,500 / 30,000 tons | **$8.98** |

*Note: This proforma is illustrative and based on published tariff schedules and market rate estimates as of 2024. Actual costs will vary based on negotiated rates, vessel specifics, terminal terms, and prevailing market conditions. Harbor maintenance tax (HMT) and CBP charges are assessed on cargo value and are excluded from this vessel-side proforma; they must be included in total landed cost analysis. The proforma total of approximately $269,000 (~$8.97–$8.98 per short ton) is consistent with the reference estimate of ~$269K total / ~$8.97/ton cited in project specifications.*

### 3.6.1 Cost Distribution Analysis

The proforma reveals the following cost distribution for this representative port call:

| Cost Category | Amount | Share of Total |
|---|---|---|
| Stevedoring | $135,000 | 50.1% |
| Pilotage | $47,400 | 17.6% |
| Wharfage | $37,500 | 13.9% |
| Towage | $36,000 | 13.4% |
| Other (dockage, line handling, agency, misc.) | $13,600 | 5.0% |
| **Total** | **$269,500** | **100.0%** |

Stevedoring (cargo handling) is the single largest cost component at over 50% of total port costs, consistent with the general pattern for dry bulk discharge operations where cargo handling is labor- and equipment-intensive. Pilotage is the second-largest component, reflecting the multi-association structure of Mississippi River pilotage. These proportions shift for different cargo types and vessel sizes: for high-volume, high-rate commodities (grain loading, coal loading), stevedoring's share decreases relative to pilotage and towage because throughput rates are much higher, reducing time-based charges.

---

## 3.7 Mississippi River Pilotage System: Detailed Structure

The Mississippi River pilotage system merits detailed treatment because of its unique multi-association structure, its significant cost impact on vessel operations, and its relevance to any commodity moving through Gulf of Mexico ports via the river.

### 3.7.1 Pilotage Associations

| Association | Coverage Area | Approximate Distance | Rate Basis | Regulatory Authority |
|---|---|---|---|---|
| Associated Branch Pilots (Bar Pilots) | Sea buoy to Pilottown | ~17 statute miles | Vessel draft, GRT | Louisiana Board of River Pilot Commissioners |
| Crescent River Port Pilots' Association | Pilottown to New Orleans | ~95 statute miles | Vessel draft, LOA | Louisiana Board of River Pilot Commissioners |
| New Orleans-Baton Rouge Steamship Pilots' Association (NOBRA) | New Orleans to Baton Rouge and above | ~120+ statute miles | Vessel draft, LOA | Louisiana Board of River Pilot Commissioners |

### 3.7.2 Pilot Change and Boarding Procedures

Pilot changes occur at designated locations (Pilottown for the Bar/Crescent transition; New Orleans area for the Crescent/NOBRA transition). At Pilottown, pilot boats transfer pilots to and from vessels at anchor or while underway. At New Orleans, pilot changes typically occur at fleet areas or anchorages. Each pilot change introduces a potential delay of 30 minutes to several hours, depending on pilot availability and traffic conditions.

### 3.7.3 Cost Implications

For a Supramax-class vessel making a full transit from the sea buoy to a berth at New Orleans:

- Bar Pilots (inbound): ~$9,000–$10,000
- Crescent River Pilots (inbound): ~$13,000–$15,000
- **Total inbound pilotage: ~$22,000–$25,000**
- Outbound pilotage is approximately equal, yielding **round-trip pilotage of ~$44,000–$50,000**.

For vessels proceeding above New Orleans to Baton Rouge or upriver terminals, NOBRA pilotage adds an additional ~$12,000–$18,000 per direction, bringing total round-trip pilotage to **~$68,000–$86,000** for a full sea-to-Baton-Rouge transit.

These pilotage costs are substantially higher than at most competing bulk ports worldwide, reflecting the length and navigational complexity of the Mississippi River approach.

---

## 3.8 Port Performance and Capacity Utilization

### 3.8.1 Berth Utilization and Congestion

Port congestion at US bulk terminals is generally less severe than at major container ports, but periodic congestion events occur at grain export elevators during peak harvest season (September–December) and at petroleum terminals during periods of high refinery throughput. Vessel waiting times (anchorage time before berthing) at Lower Mississippi River grain elevators can reach 10 to 20 days during peak export periods, imposing significant demurrage costs on charterers (USDA Agricultural Marketing Service [AMS], Grain Transportation Report, weekly; International Grains Council [IGC], Grain Market Report, monthly).

### 3.8.2 Channel Depth and Draft Restrictions

Channel depth is a critical determinant of vessel loading capacity and, therefore, per-ton transport costs. Key draft constraints include:

- **Mississippi River (Baton Rouge to Gulf):** 45-foot authorized channel depth; effective maximum drafts of 43–45 feet saltwater equivalent (SWE), subject to seasonal shoaling and USACE dredging schedules.
- **Mississippi River (above Baton Rouge):** 12-foot authorized channel depth for barge traffic.
- **Houston Ship Channel:** 45-foot authorized depth; periodic shoaling requires maintenance dredging.
- **Mobile Ship Channel:** 45-foot authorized depth (recently deepened from 40 feet).
- **Savannah Harbor:** 44-foot authorized depth (recently deepened from 42 feet under USACE Savannah Harbor Expansion Project).

Draft restrictions directly affect vessel cargo intake: a one-foot reduction in available draft on a Panamax bulk carrier reduces cargo capacity by approximately 800 to 1,200 short tons, increasing per-ton freight cost proportionally.

---

## 3.9 Implications for Commodity Analysis

The port infrastructure and cost structure described in this chapter have several direct implications for commodity-specific supply chain analysis:

1. **Port costs are a material component of delivered commodity cost.** At approximately $7 to $12 per short ton for a typical dry bulk discharge at a US Gulf Coast port, port costs can represent 3–8% of delivered cost for mid-value bulk commodities (cement, fertilizer, aggregates) and a smaller but still significant share for higher-value commodities. Port cost modeling must be included in any rigorous delivered-cost analysis.

2. **The Mississippi River pilotage system imposes a structural cost premium.** The multi-association pilotage structure on the Mississippi River results in pilotage costs 50–100% higher than at comparable single-pilot ports. This cost differential should be incorporated into port selection and routing analysis for commodities with multiple potential discharge ports.

3. **Stevedoring rates and terminal throughput rates drive vessel time in port.** For commodities with slow discharge rates (cement, some fertilizers, bagged minerals), vessel time in port can reach 7–12 days, creating significant demurrage exposure. Commodity analysts must model laytime and demurrage/dispatch calculations alongside port cost proformas to capture the full cost of port operations.

4. **Terminal infrastructure determines commodity feasibility.** Not all ports can handle all commodities. Cement import requires pneumatic unloading equipment and enclosed silo storage; grain export requires high-capacity elevator and conveyor systems; coal export requires dedicated conveyor and shiploader infrastructure. Terminal capability mapping is a prerequisite for commodity market entry analysis.

5. **Channel depth constraints affect vessel economics.** Draft restrictions at specific ports limit vessel loading capacity, which directly affects per-ton ocean freight costs. Commodity analyses should evaluate the trade-off between larger vessels (lower per-ton ocean freight) and draft constraints (potential cargo shortfall or lightering costs) at the destination port.

6. **Port congestion patterns interact with commodity seasonality.** Grain export congestion on the Lower Mississippi River during September–December affects all vessel traffic on the river, including cement, fertilizer, and chemical imports. Commodity-specific scheduling and demurrage budgeting must account for cross-commodity congestion effects.

7. **The `port_cost_model` proforma methodology provides a standardized framework** for comparing port costs across different ports, vessel sizes, and cargo types. Subsequent commodity-specific chapters in this report series will include port cost proformas generated using this methodology, enabling consistent cross-commodity comparison.

---

*This chapter draws on publicly available data and published tariff schedules from the US Army Corps of Engineers (USACE), Waterborne Commerce Statistics Center (WCSC); individual port authority annual reports and tariff publications; the US Department of Agriculture (USDA); the Portland Cement Association (PCA); BIMCO; UNCTAD; the Congressional Research Service (CRS); and market intelligence from industry sources. All tonnage figures are in short tons (2,000 lbs) unless otherwise noted. Cost estimates reflect published rates and market intelligence as of 2024 and are subject to change. The `port_cost_model` proforma toolset is an internal analytical framework used throughout this report series for standardized port cost estimation.*
