# Chapter 7: Trade Flow Analysis

## Executive Summary

US bulk imports constitute one of the largest and most complex trade flow systems in the global economy, with hundreds of millions of metric tons of raw materials, semi-finished goods, and industrial commodities arriving annually at ports spanning the Atlantic, Gulf, and Pacific coasts. Analyzing these flows at commodity resolution requires a systematic data pipeline capable of transforming raw bill of lading records — which arrive as unstructured, inconsistently formatted, and frequently ambiguous text — into structured, classified, and geographically attributed trade flow datasets. This chapter documents the analytical framework for US bulk trade flow analysis, encompassing the Panjiva data pipeline's 7-phase classification methodology (processing 135 raw columns per record), the Harmonized Tariff Schedule code structure that governs commodity identification, port consolidation and regional aggregation logic, and the entity resolution processes that harmonize shipper and consignee identities across millions of transaction records. The resulting analytical capability supports commodity-specific volume trending, origin-destination mapping, market share analysis, and competitive intelligence across the full spectrum of US bulk imports.

---

## 7.1 US Bulk Import Patterns: Volume and Value

### 7.1.1 Scale of US Bulk Imports

The United States is the world's largest economy by GDP and one of its largest importers of bulk commodities by both volume and value. US bulk imports serve as feedstock for manufacturing, construction, energy production, agriculture, and infrastructure maintenance. Major commodity groups by volume include:

- **Crude petroleum and petroleum products** (HTS Chapter 27): The single largest import category by both weight and value, with volumes exceeding 200 million metric tons annually.
- **Iron and steel** (HTS Chapters 72–73): Including primary forms (slabs, billets, hot-rolled coil), semi-finished products, and finished steel products.
- **Minerals and aggregates** (HTS Chapter 25): Cement, salt, stone, sand, sulfur, and related construction and industrial minerals.
- **Fertilizers** (HTS Chapter 31): Nitrogen, phosphate, and potash fertilizers sourced globally.
- **Ores and concentrates** (HTS Chapter 26): Iron ore, bauxite, manganese, chromium, and other metallic ores.
- **Grain and agricultural bulk** (HTS Chapters 10–12): While the US is a net grain exporter, significant volumes of specialty grains and oilseeds are imported.
- **Forest products** (HTS Chapters 44–48): Lumber, pulp, and paper products, particularly from Canada and Scandinavia.
- **Aluminum and base metals** (HTS Chapters 74–81): Primary aluminum, copper, nickel, zinc, and their alloys.
- **Chemicals** (HTS Chapters 28–38): Industrial chemicals, caustic soda, acids, and organic compounds in bulk liquid and dry form.
- **Coal and solid fuels** (HTS Chapter 27, subheadings): Metallurgical coal imports for steelmaking.

### 7.1.2 Volume vs. Value Dynamics

Bulk commodity imports exhibit a characteristic inverse relationship between per-unit value and volume share. Low-value, high-volume commodities (aggregates, salt, crude oil) dominate tonnage statistics, while higher-value commodities (specialty steel, chemicals, metals) dominate value statistics. This dynamic has direct implications for supply chain analysis:

- **Low-value bulk**: Freight cost represents a large share of delivered price; supply chain optimization focuses on minimizing transport cost per ton.
- **High-value bulk**: Freight cost is a smaller share of delivered price; supply chain optimization focuses on reliability, transit time, and inventory carrying cost.

---

## 7.2 Top Import Origins for Bulk Commodities

US bulk import origins vary significantly by commodity group but are concentrated among a relatively small number of trading partners. The following table summarizes major origin countries by port of discharge patterns.

| Commodity Group | Primary Origins | Key US Discharge Ports |
|---|---|---|
| Crude petroleum | Canada (pipeline + marine), Saudi Arabia, Mexico, Colombia, Iraq | LOOP (LA), Houston, Corpus Christi, Philadelphia |
| Iron & steel | Canada, Brazil, South Korea, Japan, Germany, Turkey | Houston, New Orleans, Great Lakes ports, Baltimore |
| Cement & minerals | Canada, China, Turkey, Greece, Mexico | Tampa, Houston, New York/Newark, Los Angeles |
| Fertilizers | Canada, Trinidad & Tobago, Russia, Morocco, Israel | New Orleans, Tampa, Savannah, Portland (OR) |
| Ores & concentrates | Brazil, Canada, South Africa, Australia, Chile | Baltimore, New Orleans, Mobile, Philadelphia |
| Aluminum | Canada, UAE, Russia, Bahrain, India | New Orleans, Mobile, Newark, Longview |
| Forest products | Canada, Brazil, Sweden, Finland, Chile | Longview, Tacoma, Savannah, Jacksonville |
| Chemicals (bulk) | Canada, China, Germany, Netherlands, Trinidad | Houston, Baton Rouge, New York/Newark |
| Salt | Chile, Mexico, Canada, Egypt, Australia | Newark, Providence, Baltimore, Tampa |
| Gypsum | Mexico, Spain, Canada | Tampa, Norfolk, Philadelphia |

**Table 7.1**: Major US bulk import origins by commodity group and primary discharge ports.

### 7.2.1 Geographic Concentration

Analysis of port-of-discharge patterns reveals significant geographic concentration:

- **Gulf Coast ports** (Houston, New Orleans, Corpus Christi, Mobile, Tampa) handle the majority of US bulk imports by tonnage, reflecting proximity to petroleum refining, petrochemical manufacturing, and Mississippi River barge distribution networks.
- **East Coast ports** (Baltimore, Philadelphia, Newark, Norfolk) serve as primary receivers for steel, minerals, and construction materials destined for the heavily populated Northeast and Mid-Atlantic corridors.
- **West Coast ports** (Long Beach, Los Angeles, Longview, Tacoma) handle Pacific-origin commodities and serve as gateways for Asian-sourced bulk materials.
- **Great Lakes ports** (Burns Harbor, Cleveland, Detroit, Duluth) receive iron ore, steel, and limestone primarily from Canadian origins.

---

## 7.3 Panjiva Data Pipeline: 135-Column Processing Framework

### 7.3.1 Raw Data Structure

Each Panjiva bill of lading record contains up to **135 raw columns** encompassing:

| Column Category | Representative Fields | Count |
|---|---|---|
| Shipment identification | Bill of lading number, master BOL, house BOL, booking number | 8 |
| Date fields | Arrival date, departure date, notification date, filing date | 6 |
| Vessel and voyage | Vessel name, IMO number, voyage number, carrier SCAC | 12 |
| Ports | Port of lading, port of unlading, foreign port, US port | 8 |
| Parties | Shipper name/address, consignee name/address, notify party | 18 |
| Cargo description | Product description, marks and numbers, commodity keywords | 10 |
| Quantities | Weight (kg), weight (lbs), measure (CBM), piece count, container count | 12 |
| Container details | Container numbers, container type, seal numbers | 15 |
| Classification | HS code (where provided), SITC code, Schedule B | 6 |
| Administrative | Filer code, entry type, in-bond code, conveyance ID | 18 |
| Derived/calculated | Place of receipt, final destination, transit routing | 12 |
| Metadata | Record ID, update timestamp, source indicator, data quality flags | 10 |

**Table 7.2**: Panjiva raw data column structure (135 columns across 12 categories).

### 7.3.2 Data Quality Challenges

Raw Panjiva data presents several systematic quality challenges that necessitate the multi-phase processing pipeline:

- **Inconsistent cargo descriptions**: The same commodity may be described as "PORTLAND CEMENT," "OPC 42.5N," "GREY CEMENT IN BULK," or "CIMENT" across different records.
- **Missing or erroneous HS codes**: Many bill of lading records lack HS code classification, or carry codes copied from prior shipments that do not match the actual cargo.
- **Vessel name variants**: A single vessel may appear as "M/V OCEAN TRADER," "OCEAN TRADER," "OCEN TRADER" (misspelling), or by a prior name following vessel sale.
- **Party name variants**: A single company may appear under dozens of name variants, abbreviations, and address formats.
- **Non-cargo records**: Ship stores, personal effects, empty container repositioning, and other non-commercial cargo records contaminate the dataset.

---

## 7.4 Seven-Phase Classification Methodology

The Panjiva data pipeline processes raw bill of lading records through seven sequential phases to produce classified, enriched, and analytically ready trade flow records.

### Phase 1: Data Ingestion and Standardization

**Objective**: Normalize raw data fields into consistent formats.

- Date parsing and standardization to ISO 8601 format.
- Weight conversion to metric tons (from kg, lbs, or long/short tons as provided).
- Port name standardization to UN/LOCODE (e.g., "PORT OF HOUSTON" and "HOUSTON, TX" both resolve to USHOU).
- Character encoding normalization (handling of non-Latin characters in shipper/consignee names).
- Duplicate record identification and flagging based on BOL number, vessel, and date combinations.

### Phase 2: White Noise Filtering

**Objective**: Remove non-cargo and non-commercial records that would distort analytical outputs.

Records removed include:

- **Ship stores and provisions**: Identified by cargo descriptions containing "SHIP STORES," "VESSEL SUPPLIES," "PROVISIONS FOR CREW."
- **Personal effects**: "PERSONAL EFFECTS," "HOUSEHOLD GOODS," "USED HOUSEHOLD."
- **Empty containers**: Container movements with zero weight or descriptions indicating "EMPTY," "MTY," "SHIPPER OWNED CONTAINER — EMPTY."
- **Diplomatic and military cargo**: Records flagged with special entry types or consigned to government entities (retained in a separate analytical track where relevant).
- **Sample and exhibition goods**: Low-weight shipments described as "SAMPLE," "FOR EXHIBITION," "NOT FOR SALE."

Filtering rates vary by trade lane and commodity but typically remove 8–15% of raw records.

### Phase 3: Carrier Exclusion and Segmentation

**Objective**: Identify the transport mode and carrier type for each record, enabling separation of containerized vs. bulk/breakbulk shipments.

- **Container carrier identification**: Records associated with known container line SCAC codes (MAEU for Maersk, CMDU for CMA CGM, MSCU for MSC, etc.) are flagged as containerized cargo.
- **Bulk carrier identification**: Records associated with non-liner carriers, tramp operators, or bulk-specific SCAC codes are flagged as potential bulk cargo.
- **NVO/freight forwarder identification**: Records filed by NVOCCs (Non-Vessel Operating Common Carriers) are flagged for special handling, as these frequently consolidate multiple commodity types under a single bill of lading.

This segmentation is critical because the same commodity (e.g., steel coils) may move in either containerized or bulk/breakbulk mode, and the analytical treatment differs.

### Phase 4: Keyword Classification

**Objective**: Assign preliminary commodity classifications based on cargo description text analysis.

The keyword classification engine applies a hierarchical rule set:

1. **Exact phrase matching**: High-confidence commodity identifiers ("PORTLAND CEMENT TYPE I," "HOT ROLLED STEEL COIL," "UREA 46%").
2. **Keyword combination matching**: Multi-word patterns that together indicate a commodity ("IRON" + "ORE," "CRUDE" + "OIL," "SODA" + "ASH").
3. **Single keyword matching**: Individual terms with commodity significance, applied with lower confidence and subject to disambiguation rules.
4. **Negative keyword filtering**: Terms that exclude certain classifications (e.g., "STAINLESS" excludes carbon steel categories; "REFINED" excludes crude oil categories).

The keyword library contains approximately 2,500 commodity-specific terms and phrases organized into a taxonomy of 150+ commodity categories.

### Phase 5: HS4 Code Alignment

**Objective**: Map keyword-classified records to Harmonized System 4-digit codes (HS4), creating a standardized commodity classification consistent with international trade nomenclature.

- Where HS codes are provided in the raw data and pass validation checks, they take precedence over keyword classification.
- Where HS codes are missing or flagged as suspect, the keyword classification drives HS4 assignment.
- Conflict resolution rules adjudicate cases where the provided HS code and the keyword classification disagree.
- HS4 codes are further grouped into analytical commodity categories defined by the project (e.g., HS 2523 = "Cement," HS 7208–7212 = "Flat-Rolled Steel," HS 3102–3105 = "Fertilizers").

### Phase 6: Vessel Enrichment

**Objective**: Append vessel characteristics from the ship registry database (Chapter 6) to each trade flow record.

- Vessel name and IMO number from the bill of lading are matched to the 52,035-vessel ship registry.
- Matched records receive vessel type, DWT, draft, dimensions, flag state, and year built.
- Vessel type serves as a secondary classification signal: records arriving on bulk carriers are more likely to contain bulk commodities; records on container ships are containerized.
- Unmatched vessel records are flagged for manual review and iterative registry expansion.

### Phase 7: Final Classification and Quality Assurance

**Objective**: Produce final classified records with confidence scoring and analytical readiness indicators.

- Each record receives a **classification confidence score** (High / Medium / Low) based on the number and consistency of classification signals (keyword match strength, HS code agreement, vessel type consistency).
- Records with conflicting signals are routed to a manual review queue.
- Final output fields include: commodity category, HS4 code, commodity description (standardized), transport mode, vessel type, origin country, origin port, destination port, destination region, weight (MT), value (where available), shipper (harmonized), consignee (harmonized).

---

## 7.5 Port Consolidation and Regional Aggregation

### 7.5.1 Port Consolidation Logic

US Customs data references over 400 distinct port codes, many of which represent sub-facilities, anchorages, or administrative districts within a single port complex. The pipeline consolidates these to approximately 90 analytically distinct port entities. Examples:

| Raw Customs Port Codes | Consolidated Port Entity |
|---|---|
| 5301 (Houston), 5309 (Galveston), 5310 (Texas City), 5312 (Freeport) | Houston-Galveston Complex |
| 1001 (New York), 1003 (Newark), 4601 (Perth Amboy), 4602 (Elizabeth) | New York / New Jersey |
| 2709 (New Orleans), 2002 (Baton Rouge), 2004 (Gramercy), 2006 (Burnside) | Lower Mississippi River |
| 2704 (Los Angeles), 2709 (Long Beach) | San Pedro Bay (LA/LB) |
| 1303 (Baltimore) | Baltimore |
| 1801 (Philadelphia), 1802 (Chester), 1803 (Wilmington DE) | Delaware River Ports |

**Table 7.3**: Port consolidation examples.

### 7.5.2 Regional Aggregation

Consolidated ports are further grouped into regions for macro-level analysis:

- **US East Coast (USEC)**: Maine to Florida, including Great Lakes ports accessible via the St. Lawrence Seaway.
- **US Gulf Coast (USGC)**: Florida Panhandle to the Texas-Mexico border.
- **US West Coast (USWC)**: California, Oregon, Washington, Alaska, and Hawaii.
- **US Great Lakes (USGL)**: Ports on Lakes Superior, Michigan, Huron, Erie, and Ontario.

---

## 7.6 Commodity Flow Analysis by Transport Mode

### 7.6.1 Break Bulk

Break bulk cargo — unitized or packaged cargo loaded piece-by-piece rather than in containers or in bulk — includes:

- **Steel products**: Coils, plates, beams, pipe, and rebar loaded on specialized vessels with cranes.
- **Forest products**: Bundled lumber, plywood, and pulp bales.
- **Project cargo**: Heavy-lift items, industrial equipment, and oversized components.
- **Bagged cargo**: Cement, chemicals, and agricultural products in bags or supersacks.

Break bulk volumes have declined over decades as containerization has captured an increasing share of unitized cargo, but certain commodities remain inherently break bulk due to weight, dimensions, or handling requirements.

### 7.6.2 Dry Bulk

Dry bulk cargo — unpackaged, homogeneous commodities loaded directly into vessel holds — represents the largest share of US bulk import tonnage:

- **Major dry bulk**: Iron ore, coal, grain, bauxite/alumina, phosphate rock (the "five majors" of global dry bulk trade).
- **Minor dry bulk**: Cement, gypsum, salt, petcoke, limestone, sand, fertilizers, and numerous specialty minerals.

Dry bulk flows are characterized by large parcel sizes (10,000–200,000+ MT per vessel), port-specific handling infrastructure (grab cranes, conveyor systems, pneumatic unloaders), and strong seasonality in certain commodity segments (grain harvest cycles, winter heating fuel demand).

### 7.6.3 Liquid Bulk

Liquid bulk cargo — pumped through pipeline connections between vessel and shore storage — includes:

- **Crude petroleum**: The single largest commodity by tonnage in US imports.
- **Refined petroleum products**: Gasoline, diesel, jet fuel, fuel oil.
- **Chemicals**: Caustic soda, methanol, styrene, acids, and specialty chemicals.
- **Liquefied gases**: LNG and LPG at specialized terminals.
- **Vegetable oils and animal fats**: At dedicated food-grade terminals.

Liquid bulk flows require dedicated terminal infrastructure (tank farms, pipelines, vapor recovery systems) and are governed by stringent safety and environmental regulations.

### 7.6.4 Containerized Bulk (Neo-Bulk)

An increasing share of traditionally bulk commodities now moves in containers, a trend driven by:

- Smaller parcel sizes serving fragmented demand (e.g., specialty chemicals, food-grade minerals).
- Port accessibility — containerized movements can access any container port, while bulk movements require commodity-specific handling infrastructure.
- Supply chain flexibility — containers enable door-to-door logistics without transloading.

Commodities commonly moving as containerized bulk include:

- Titanium dioxide, calcium carbonate, and other industrial minerals in bags or supersacks.
- Specialty steel products (stainless, alloy) in smaller quantities.
- Food-grade commodities (rice, coffee, cocoa) in lined containers.
- Scrap metals (both ferrous and non-ferrous) in open-top containers.

---

## 7.7 Import Trend Analysis by Commodity Group

### 7.7.1 Analytical Dimensions

The classified trade flow dataset supports trend analysis across multiple dimensions:

- **Volume trending**: Monthly, quarterly, and annual metric tonnage by commodity category.
- **Origin shifting**: Changes in source country mix over time, reflecting trade policy changes (tariffs, sanctions), new production capacity, and competitive dynamics.
- **Port migration**: Shifts in port-of-discharge patterns driven by infrastructure investments, congestion, or hinterland demand changes.
- **Seasonality decomposition**: Identification of cyclical patterns in commodity flows (e.g., construction season for cement and steel, fertilizer application windows for agricultural chemicals).
- **Unit value trending**: Where value data is available, tracking of implied per-ton prices that reflect global commodity market dynamics.

### 7.7.2 Key Trend Indicators

For each commodity group, the pipeline generates:

- Rolling 12-month import volume (MT) and year-over-year change.
- Top 5 origin countries with share percentages and trend direction.
- Top 5 discharge ports with share percentages and trend direction.
- Vessel type distribution (share by bulk carrier class or container).
- Average parcel size (MT per bill of lading or per vessel call).

---

## 7.8 HTS Code Structure for Trade Data

### 7.8.1 Harmonized Tariff Schedule Architecture

The Harmonized Tariff Schedule of the United States (HTS) provides the legal framework for commodity classification of imported goods. The HTS is based on the international Harmonized System (HS) maintained by the World Customs Organization (WCO) and is structured hierarchically:

| Level | Digits | Example | Description |
|---|---|---|---|
| Chapter | 2 | 25 | Salt; sulfur; earths and stone; plastering materials, lime and cement |
| Heading | 4 (HS4) | 2523 | Portland cement, aluminous cement, slag cement |
| Subheading | 6 (HS6) | 2523.29 | Portland cement: other (not white) |
| US tariff line | 8 (HTS8) | 2523.29.00 | Portland cement, other than white, whether or not artificially colored |
| Statistical suffix | 10 (HTS10) | 2523.29.0000 | Full statistical reporting number |

**Table 7.4**: HTS code hierarchical structure.

### 7.8.2 Key HTS Chapters for Bulk Commodities

| HTS Chapter | Description | Bulk Commodity Examples |
|---|---|---|
| 25 | Salt; sulfur; earths and stone; lime and cement | Cement, salt, gypsum, limestone, sand, sulfur, natural calcium phosphates |
| 26 | Ores, slag and ash | Iron ore, manganese ore, chromium ore, bauxite, zinc ore |
| 27 | Mineral fuels, oils and products | Crude petroleum, coal, coke, petroleum products, natural gas |
| 28 | Inorganic chemicals | Sulfuric acid, caustic soda, soda ash, chlorine, hydrogen peroxide |
| 31 | Fertilizers | Urea, ammonium nitrate, DAP/MAP, potassium chloride (MOP) |
| 44 | Wood and articles of wood | Logs, lumber, wood chips, plywood, veneer |
| 47 | Pulp of wood | Mechanical pulp, chemical pulp, dissolving grades |
| 72 | Iron and steel | Pig iron, ferroalloys, ingots, slabs, HRC, CRC, plate, wire rod |
| 73 | Articles of iron or steel | Pipe, tube, structural shapes, castings, forgings |
| 74 | Copper and articles thereof | Copper cathode, wire, tube, scrap |
| 76 | Aluminum and articles thereof | Primary aluminum, extrusions, sheet, foil, scrap |

**Table 7.5**: Key HTS chapters for bulk commodity trade analysis.

### 7.8.3 HS Code Limitations in Bulk Trade Analysis

While the HS code system provides a standardized classification framework, several limitations affect its utility for bulk supply chain analysis:

- **Granularity gaps**: Some commodity distinctions important to industry (e.g., cement clinker vs. finished cement of specific strength classes) are not well differentiated in the HS code structure.
- **Classification inconsistency**: The same product may be classified under different HS codes by different customs brokers, particularly for processed or semi-finished goods that could logically fall under multiple headings.
- **Absence from bill of lading data**: Many Panjiva bill of lading records do not contain HS codes, as the HS code is applied at the customs entry stage, which is a separate process from the transportation documentation captured in bills of lading.

These limitations motivate the multi-signal classification approach described in Section 7.4, which uses cargo description keywords, vessel type, and trade lane context to supplement or replace HS code-based classification.

---

## 7.9 Party Harmonization and Entity Resolution

### 7.9.1 The Entity Resolution Challenge

A single commercial entity may appear in Panjiva data under dozens or hundreds of name variants:

| Raw Shipper Name Variants | Harmonized Entity |
|---|---|
| CEMEX S.A.B. DE C.V. | CEMEX |
| CEMEX MEXICO SA DE CV | CEMEX |
| CEMEX SAB DE CV | CEMEX |
| CEMEX OPERACIONES MEXICO | CEMEX |
| CEMEX CONCRETOS SA | CEMEX |

| Raw Consignee Name Variants | Harmonized Entity |
|---|---|
| US STEEL CORPORATION | United States Steel Corporation |
| USS - GARY WORKS | United States Steel Corporation |
| UNITED STATES STEEL CORP | United States Steel Corporation |
| U.S. STEEL TUBULAR PRODUCTS | United States Steel Corporation |
| USS-POSCO INDUSTRIES | USS-POSCO Industries (separate JV entity) |

**Table 7.6**: Entity resolution examples — shipper and consignee harmonization.

### 7.9.2 Harmonization Methodology

The party harmonization process employs:

1. **Standardization**: Removal of legal suffixes (SA, LLC, INC, CORP, GMBH, etc.), punctuation normalization, and whitespace trimming.
2. **Token-based matching**: Decomposition of names into tokens and comparison using TF-IDF weighted cosine similarity.
3. **Address-assisted matching**: Where address fields are populated, geographic consistency provides a secondary matching signal.
4. **Industry knowledge rules**: Domain-specific rules that link known subsidiaries, divisions, and trade names to parent entities (e.g., "NUCOR-YAMATO STEEL" maps to a Nucor Corporation subsidiary).
5. **Manual curation**: A curated master entity list of the top 500 shippers and consignees in US bulk trade, maintained and updated with each data refresh.

### 7.9.3 Analytical Applications of Harmonized Entities

Harmonized party data enables:

- **Market share analysis**: Identifying the largest importers (consignees) and exporters (shippers) of specific commodities into the US.
- **Supply chain mapping**: Tracing shipper-consignee relationships to understand which foreign producers supply which US buyers.
- **Concentration risk assessment**: Measuring supplier and buyer concentration (HHI index) within commodity-specific trade flows.
- **Corporate intelligence**: Tracking changes in a specific company's import patterns over time (volume, origin shifts, port selection, carrier choice).

---

## 7.10 Top 10 Bulk Import Commodity Groups by Tonnage

The following table presents the top 10 bulk import commodity groups by estimated annual tonnage based on classified Panjiva data, cross-referenced with USACE waterborne commerce statistics and US Census trade data.

| Rank | Commodity Group | Primary HTS Chapters | Estimated Annual Import Volume (Million MT) | Primary Transport Mode | Key Origins | Primary Discharge Ports |
|---|---|---|---|---|---|---|
| 1 | Crude petroleum | 27 | 200–250 | Liquid bulk (tanker) | Canada, Saudi Arabia, Mexico, Colombia | LOOP, Houston, Corpus Christi |
| 2 | Iron ore & concentrates | 26 | 35–45 | Dry bulk (Capesize/Panamax) | Brazil, Canada, Sweden, South Africa | Baltimore, Mobile, Cleveland |
| 3 | Refined petroleum products | 27 | 30–40 | Liquid bulk (tanker) | Canada, India, South Korea, Netherlands | New York/NJ, Houston, Philadelphia |
| 4 | Iron & steel products | 72–73 | 25–35 | Break bulk / dry bulk | Canada, Brazil, South Korea, Japan, Turkey | Houston, New Orleans, Great Lakes |
| 5 | Cement & clinker | 25 | 15–25 | Dry bulk (Handysize/Supramax) | Turkey, China, Greece, Mexico, Canada | Tampa, Houston, New York/NJ |
| 6 | Fertilizers | 31 | 15–20 | Dry bulk (Handysize/Supramax) | Trinidad, Canada, Morocco, Russia | New Orleans, Tampa, Savannah |
| 7 | Salt | 25 | 12–18 | Dry bulk (Handysize) | Chile, Mexico, Canada, Egypt | Newark, Providence, Baltimore |
| 8 | Aluminum & bauxite | 26, 76 | 10–15 | Dry bulk / break bulk | Canada, Jamaica, Brazil, UAE | New Orleans, Mobile, Longview |
| 9 | Gypsum | 25 | 8–12 | Dry bulk (Handysize) | Mexico, Spain, Canada | Tampa, Norfolk, Philadelphia |
| 10 | Industrial chemicals | 28–29 | 6–10 | Liquid bulk / dry bulk | Canada, China, Germany, Netherlands | Houston, Baton Rouge, Newark |

**Table 7.7**: Top 10 US bulk import commodity groups by estimated annual tonnage.

*Note: Estimates are approximate ranges reflecting multi-year averages. Crude petroleum volumes are highly variable based on domestic production levels and refinery demand. Steel import volumes fluctuate significantly based on tariff policy (Section 232), economic cycles, and domestic mill capacity utilization.*

---

## 7.11 Implications for Commodity Analysis

The trade flow analysis framework documented in this chapter creates several foundational capabilities for downstream commodity-specific studies:

1. **Commodity-specific deep dives**: The 7-phase classified dataset enables rapid extraction of trade flows for any commodity of interest, filtered by HS code, keyword, or commodity category. A commodity analyst can immediately access volume trends, origin mix, port distribution, vessel types, and key market participants for their target commodity without re-processing raw data.

2. **Competitive intelligence**: Harmonized shipper and consignee entities enable market share analysis at the company level. For any bulk commodity, analysts can identify who is shipping, who is receiving, how volumes are trending by party, and whether new entrants or exits are reshaping the competitive landscape.

3. **Port and logistics planning**: Port-level and region-level trade flow aggregations support infrastructure planning, congestion analysis, and logistics cost modeling. Commodity flows can be mapped against port capacity, channel depth constraints, and inland transportation networks to identify bottlenecks and optimization opportunities.

4. **Trade policy impact assessment**: The classified dataset enables rapid quantification of trade policy impacts — tariff changes, quota implementations, sanctions, or trade agreement modifications can be assessed by measuring volume and origin shifts in affected commodity categories before and after policy implementation dates.

5. **Supply chain risk identification**: Origin concentration analysis, shipper concentration analysis, and port concentration analysis collectively illuminate supply chain risk exposure. Commodities sourced predominantly from a single country, shipped by a single supplier, or discharged at a single port represent concentrated risk that may warrant diversification strategies.

6. **Cross-commodity correlation**: The standardized classification framework enables analysis of cross-commodity relationships — for example, tracking whether iron ore import volumes lead steel product import volumes (indicating domestic mill production), or whether cement and steel imports move together (indicating construction cycle dynamics).

7. **Data quality transparency**: The confidence scoring system embedded in the classification pipeline ensures that analysts understand the reliability of the data supporting their conclusions. High-confidence records (strong keyword match, consistent HS code, appropriate vessel type) can be distinguished from lower-confidence records that may require manual validation for critical analytical applications.

---

*This chapter establishes the trade flow analytical framework that serves as the data backbone for all commodity-specific supply chain analyses in subsequent chapters. The classified, enriched, and harmonized dataset produced by the 7-phase pipeline transforms raw bill of lading records into actionable trade intelligence capable of supporting strategic decision-making across the full spectrum of US bulk commodity imports.*
