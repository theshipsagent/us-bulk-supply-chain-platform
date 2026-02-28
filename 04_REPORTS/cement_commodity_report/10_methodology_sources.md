# Chapter 10: Methodology & Sources

## US Cement & Cementitious Materials Commodity Report

**US Bulk Supply Chain Reporting Platform**
**Report Period:** Q1 2026

---

This chapter documents the data sources, analytical methodologies, platform toolsets, and known limitations underlying the US Cement and Cementitious Materials Commodity Report. The report draws on a combination of US government statistical programs, international trade databases, industry association publications, proprietary market intelligence, and the platform's integrated toolset modules for freight, port cost, and geospatial analysis. Data currency reflects Q1 2026 conditions, with underlying datasets ranging from 2023 (most recent complete-year USACE waterborne commerce statistics) through January 2026 (real-time trade and freight data). This methodology chapter is intended to provide full transparency into the analytical foundation of each report chapter, enabling readers to assess data quality, identify limitations, and understand the basis for forward-looking projections.

---

## 10.1 Primary Government Data Sources

### 10.1.1 USGS Mineral Commodity Summaries -- Cement

**Source:** US Geological Survey, National Minerals Information Center
**Publication:** Mineral Commodity Summaries (annual), Mineral Industry Surveys (quarterly)
**Data coverage:** US cement production, consumption, capacity, trade, pricing
**Currency:** 2025 edition (based on 2024 data), published January 2025
**URL:** https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information

**Data elements used in this report:**
- US cement production volume (84 million MT, 2024)
- Number of active plants (99 in 34 states + PR)
- Nameplate production capacity (120 million MT)
- Capacity utilization rate (72%)
- Total cement shipments (110 million MT, $17 billion value)
- Import volume by origin country
- Average import price ($79/ton CIF, 2024)
- Export volume and value
- State-level production rankings

**Methodology notes:** USGS data is collected through voluntary surveys of domestic cement producers supplemented by US Census Bureau import/export records. Production data is estimated for non-respondents. USGS withholds individual company data to avoid disclosing proprietary information, publishing only aggregated state and national totals. Some state-level data is estimated or withheld when fewer than three producers operate in a state.

**Limitations:** USGS production data lags by approximately 12-18 months for final figures. Preliminary estimates used in this report (2024 data) may be revised in subsequent publications. Plant-level capacity and production data is not publicly disclosed; estimates in this report are derived from industry sources and the Global Energy Monitor Cement Tracker.

### 10.1.2 EPA Facility Registry Service (FRS) -- NAICS 327310

**Source:** US Environmental Protection Agency, Facility Registry Service
**Data coverage:** Locations, permit data, and regulatory status of cement manufacturing facilities
**NAICS code:** 327310 (Cement Manufacturing)
**Currency:** Continuously updated; data pulled December 2025
**URL:** https://www.epa.gov/frs

**Data elements used in this report:**
- Cement plant locations and addresses
- Facility operating status (active, closed, idle)
- Environmental permit IDs (Clean Air Act, NPDES)
- Parent company identification
- Geographic coordinates for geospatial analysis

**Methodology notes:** FRS data is compiled from multiple EPA programs (CAA Title V permits, Toxics Release Inventory, NPDES permits). The database provides the most comprehensive geographic inventory of US cement manufacturing facilities. Facility data was cross-referenced with USGS and Global Energy Monitor data to validate plant locations and operational status.

**Limitations:** FRS data does not include production capacity, output volumes, or product types. Some facilities may be listed under parent company names that differ from operating brand names, requiring manual matching. Non-manufacturing facilities (terminals, distribution centers) are generally not included.

### 10.1.3 US Census Bureau -- Foreign Trade Statistics

**Source:** US Census Bureau, Foreign Trade Division
**Data coverage:** US imports and exports by HTS code, origin/destination country, port, value, quantity
**HTS codes:** 2523 (Portland cement, aluminous cement, slag cement, hydraulic cements)
- 2523.10 -- Cement clinkers
- 2523.21 -- White Portland cement
- 2523.29 -- Other Portland cement (gray)
- 2523.30 -- Aluminous cement
- 2523.90 -- Other hydraulic cements
**Currency:** Monthly, approximately 45-day lag; data through November 2025 used
**URL:** https://usatrade.census.gov/

**Data elements used in this report:**
- Total US cement import volume and value by origin country
- Import volume by US customs district and port
- HTS-level product detail (clinker vs. finished cement, white vs. gray)
- Average unit values (CIF price per metric ton)
- Export volume and value by destination
- Year-over-year trend analysis

**Methodology notes:** Census trade data is compiled from Customs and Border Protection (CBP) entry documents. Values are reported CIF (Cost, Insurance, Freight) for imports and FAS (Free Alongside Ship) for exports. Quantities are reported in metric tons. Data at the 10-digit HTS level provides the most granular product classification available.

### 10.1.4 Panjiva Import Manifests -- HTS 2523

**Source:** S&P Global Market Intelligence / Panjiva
**Data coverage:** Individual US import manifests including shipper, consignee, port, weight, value
**HTS codes:** 2523.xx (all cement sub-headings)
**Currency:** Real-time with 3-7 day lag; 2023-2025 data used
**URL:** https://panjiva.com (subscription required)

**Data elements used in this report:**
- Individual shipment records (1,646 records analyzed, 2023-2025)
- Shipper (exporter) identification and origin country
- Consignee (importer) identification
- US port of entry
- Shipment weight and declared value
- Vessel name and IMO number
- Bill of lading details

**Methodology notes:** Panjiva data is compiled from US Customs import manifests filed by carriers and customs brokers. The database provides the only publicly available source for company-level import volume analysis, enabling identification of specific importer-exporter relationships, port preferences, and trade flow patterns. Data was filtered by HTS heading 2523 and aggregated by consignee, port, and origin to develop the competitive import analysis in Chapters 5, 6, and 9.

**Limitations:** Panjiva data may undercount total import volume due to confidential treatment requests, consolidated manifests, and data processing lags. Approximately 5-10% of import volume is estimated to be missing from the Panjiva dataset due to these factors. Value data on import manifests is less reliable than Census customs value data due to declarant inconsistencies. Individual shipment weights may represent full vessel cargo or partial cargo allocations, requiring careful interpretation.

### 10.1.5 USDA Grain Transportation Report (GTR) -- Barge Rates

**Source:** US Department of Agriculture, Agricultural Marketing Service, Transportation and Marketing Division
**Publication:** Grain Transportation Report (weekly)
**Data coverage:** Barge rate indices for Mississippi River system, by region
**Currency:** Weekly; data through January 2026 used
**URL:** https://www.ams.usda.gov/services/transportation-analysis/gtr

**Data elements used in this report:**
- Barge rate indices (percent of tariff) for Upper Mississippi, Mid-Mississippi, Lower Mississippi, Ohio River, and Gulf Intracoastal Waterway
- Barge fleet statistics (fleet size, age distribution, utilization)
- Seasonal rate patterns
- Historical rate trend analysis

**Methodology notes:** The GTR reports barge rates as a percentage of a base tariff schedule established by the Waterways Freight Bureau. While the GTR focuses on grain movements, the covered barge fleet is shared across commodity types (grain, cement, fertilizer, salt), making GTR rate indices a reasonable proxy for cement barge rates. Actual cement barge rates may deviate from GTR indices due to commodity-specific factors (loading/unloading requirements, equipment specifications, backhaul patterns).

**Limitations:** GTR data is specific to grain barge movements and may not precisely reflect cement barge rates, which can carry premiums for specialized loading equipment, covered barge requirements, and route-specific factors. The platform's barge cost model applies adjustment factors to GTR rates based on commodity-specific cost analysis.

### 10.1.6 Surface Transportation Board (STB) -- Rail Freight Statistics

**Source:** Surface Transportation Board
**Data coverage:** Rail freight commodity statistics by STCC code, waybill sample data
**STCC codes:** 32xx (Clay, Concrete, Glass, or Stone Products -- includes cement as 3241)
**Currency:** Annual; 2023 data (most recent complete year)
**URL:** https://www.stb.gov/reports-data/economic-data/freight-commodity-statistics/

**Data elements used in this report:**
- Rail carload volume for nonmetallic minerals and cement
- Revenue per ton-mile benchmarks
- URCS (Uniform Rail Costing System) variable cost estimates for cement corridors
- Origin-destination flow analysis from waybill sample (aggregated)

**Methodology notes:** STB data is compiled from Class I railroad annual reports (R-1 filings) and the 1% waybill sample. The waybill sample provides the most detailed origin-destination rail freight data available, though public access is limited to aggregated statistics to protect shipper confidentiality. URCS variable costs are used as a regulatory benchmark for assessing rail rate reasonableness and are referenced in the rail cost analysis in Chapter 7.

**Limitations:** STB data groups cement with broader "nonmetallic minerals" in some published reports, requiring extraction of cement-specific data from the STCC-level detail. Waybill sample data lags by 12-18 months. URCS costs represent a regulatory estimate of railroad variable cost, not actual market rates; actual rates are typically 1.3-2.0x URCS variable cost.

### 10.1.7 USACE Waterborne Commerce Statistics

**Source:** US Army Corps of Engineers, Waterborne Commerce Statistics Center (WCSC), New Orleans
**Data coverage:** Domestic waterborne commerce by commodity, origin, destination, waterway
**Currency:** 2023 data (published late 2024); most recent complete year available
**URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/

**Data elements used in this report:**
- Total Mississippi River system barge tonnage (449 million short tons, 2023)
- Commodity breakdown by waterway segment
- Port-level domestic waterborne commerce
- Lock performance data (Navigation Data Center)

**Methodology notes:** WCSC data is the authoritative source for US inland waterborne commerce statistics. Data is compiled from vessel trip reports filed by barge operators and published annually with an approximately 12-month lag. Tonnage is reported in short tons (2,000 lbs); this report converts to metric tons where noted.

**Limitations:** WCSC data does not distinguish cement from other "nonmetallic minerals" in commodity classifications at the waterway level. Port-level data provides better cement-specific detail. The 12-month publication lag means the most recent available data (2023) may not reflect current market conditions.

---

## 10.2 Industry and Commercial Data Sources

### 10.2.1 Portland Cement Association (PCA)

**Source:** Portland Cement Association
**Publications:** US Cement Industry Annual Report, PCA Market Intelligence, Long-Term Cement Outlook
**Data coverage:** US cement consumption forecasts, regional demand analysis, capacity data
**Currency:** 2025 Long-Term Outlook (published Q4 2025)
**URL:** https://www.cement.org

**Data elements used:** Consumption forecasts, regional demand projections, cement intensity ratios, end-use sector breakdowns. PCA projections form the basis for the demand outlook in Chapter 8.

**Limitations:** PCA publications are available only to members and subscribers. Projections reflect industry consensus but may be optimistic given PCA's role as an industry trade association. Independent demand estimates in this report cross-reference PCA projections with construction spending data and building permit trends.

### 10.2.2 Global Energy Monitor (GEM) -- Cement Tracker

**Source:** Global Energy Monitor
**Publication:** Global Cement and Concrete Tracker
**Data coverage:** Individual plant-level data including owner, capacity, technology, location
**Currency:** July 2025 update
**URL:** https://globalenergymonitor.org/projects/global-cement-tracker/

**Data elements used:** Florida cement plant capacities (Table in Chapter 6), US plant-level capacity estimates, ownership attribution, technology type (wet/dry process).

**Limitations:** GEM capacity data is compiled from public disclosures, regulatory filings, and industry publications. Actual operating capacities may differ from nameplate capacities due to operational constraints, maintenance schedules, and market conditions. GEM does not provide production volume data.

### 10.2.3 Clarksons Research -- Shipping Market Data

**Source:** Clarksons Research Services Ltd.
**Data coverage:** Dry bulk freight rates (spot and forward), vessel fleet data, route economics
**Currency:** December 2025 spot rates; calendar 2026 forward rates
**URL:** https://www.clarksons.com/services/research/ (subscription required)

**Data elements used:** Handysize, Supramax, and Panamax spot and forward freight rates used in ocean freight cost modeling (Chapters 7, 9, and 12). Route-specific rates for Mediterranean-USG, Egypt-USG, and Caribbean routes. Vessel fleet composition data for Section 301 impact analysis.

### 10.2.4 Association of American Railroads (AAR)

**Source:** Association of American Railroads
**Publication:** Weekly Rail Traffic Reports, AAR Facts and Figures
**Data coverage:** Weekly carload data by commodity group, intermodal volumes
**Currency:** Weekly through January 2026
**URL:** https://www.aar.org/data-center/

**Data elements used:** Nonmetallic minerals weekly carload data (Chapter 12), year-over-year rail traffic trends, seasonal patterns.

---

## 10.3 Platform Toolset References

The US Bulk Supply Chain Reporting Platform integrates multiple analytical toolsets that support the data analysis, cost modeling, and market intelligence presented in this report. The following toolsets were utilized:

### 10.3.1 Barge Cost Model

**Location:** `02_TOOLSETS/barge_cost_model/`
**Function:** Models barge transportation costs for cement and other dry bulk commodities on the Mississippi/Ohio River system and Gulf Intracoastal Waterway.
**Inputs:** USDA GTR barge rate indices, WCSC tonnage data, commodity-specific adjustment factors, barge fleet utilization rates.
**Outputs:** Per-ton barge cost estimates by route, seasonal rate projections, modal comparison analysis.
**Application in report:** Chapter 7 (barge freight cost structure, comparison to rail and truck), Chapter 12 (freight economics).

### 10.3.2 Rail Cost Model

**Location:** `02_TOOLSETS/rail_cost_model/`
**Function:** Models rail transportation costs for cement corridors using STB waybill data and URCS variable cost benchmarks.
**Inputs:** STB waybill sample (aggregated), URCS cost tables, Class I railroad tariff schedules, fuel surcharge indices.
**Outputs:** Per-ton rail cost by origin-destination pair, revenue-to-variable-cost ratios, competitive comparison with barge and truck.
**Application in report:** Chapter 7 (rail freight cost structure, URCS analysis, key corridor rates), Chapter 9 (SESCO Houston rail distribution economics).

### 10.3.3 Port Cost Model

**Location:** `02_TOOLSETS/port_cost_model/`
**Function:** Develops proforma vessel call costs for bulk carriers at US ports, including pilotage, towage, wharfage, dockage, stevedoring, and agency fees.
**Inputs:** Port tariff schedules, vessel specifications (DWT, LOA, draft), cargo type and volume, discharge rate assumptions.
**Outputs:** Total vessel call cost, per-ton port cost allocation, comparative port cost analysis.
**Application in report:** Chapter 7 (Houston and NOLA vessel cost proformas), Chapter 9 (SESCO terminal cost analysis).

### 10.3.4 Facility Registry

**Location:** `02_TOOLSETS/facility_registry/`
**Function:** Maintains a database of US cement production facilities, import terminals, and distribution terminals, integrating EPA FRS data with industry-sourced capacity and ownership data.
**Inputs:** EPA FRS (NAICS 327310), GEM Cement Tracker, USGS plant census, Panjiva terminal identification.
**Outputs:** Facility location database, capacity estimates, ownership attribution, regulatory status.
**Application in report:** Chapter 6 (producer profiles, plant lists), Chapter 9 (terminal specifications).

### 10.3.5 Vessel Intelligence

**Location:** `02_TOOLSETS/vessel_intelligence/`
**Function:** Tracks vessel movements, specifications, and build origin for cement trade analysis and Section 301 fee exposure assessment.
**Inputs:** AIS vessel tracking data, vessel registry databases (Equasis, ClassNK, Lloyd's), Panjiva vessel identifications.
**Outputs:** Vessel build origin (country of construction), vessel specifications, trading patterns, Section 301 exposure assessment.
**Application in report:** Chapter 7 (Section 301 fee impact analysis), Chapter 9 (SESCO vessel exposure assessment).

### 10.3.6 Policy Analysis

**Location:** `02_TOOLSETS/policy_analysis/`
**Function:** Monitors and analyzes trade policy developments affecting US cement imports, including tariff rates, AD/CVD orders, Section 301 actions, and Section 232 investigations.
**Inputs:** USITC tariff database, Federal Register notices, USTR Section 301 actions, CBP rulings.
**Outputs:** Current tariff rate tables by HTS/origin, policy change impact modeling, scenario analysis.
**Application in report:** Chapter 7 (tariff regime analysis), Chapter 9 (SESCO tariff position, Section 301 assessment).

### 10.3.7 Geospatial Engine

**Location:** `02_TOOLSETS/geospatial_engine/`
**Function:** Provides geographic analysis including trucking radius calculations, drive-time zones, facility proximity analysis, and market coverage mapping.
**Inputs:** Facility coordinates (from facility registry), road network data, population/census data, customer location data.
**Outputs:** Trucking zone analysis (1-hour, 3-hour, 5-hour radii), population coverage estimates, competitive proximity mapping.
**Application in report:** Chapter 9 (Port Redwing distribution radius analysis, Tampa market reach), Chapter 6 (regional competitive proximity).

---

## 10.4 Chapter-Specific Methodology Notes

### Chapter 6: Competitive Landscape

**Producer capacity estimates:** National producer capacity estimates are derived from a triangulation of USGS aggregate data (120 million MT total US capacity), GEM plant-level data, industry publications (Global Cement Magazine, CemNet), and company disclosures (annual reports, investor presentations). Individual plant capacities should be treated as estimates with +/-15% uncertainty ranges.

**Market share calculations:** National and regional market share estimates are derived from capacity data, import volume data (Panjiva), and industry knowledge. Actual production-based market shares are not publicly available at the company level due to USGS confidentiality restrictions. Estimates represent informed approximations rather than precise measurements.

### Chapter 7: Pricing & Cost Analysis

**Ex-plant pricing:** Domestic cement pricing is not publicly reported on a regular basis. Price estimates are derived from industry surveys (PCA, USGS), investor presentations of publicly traded producers (Eagle Materials, Martin Marietta, Summit Materials), construction industry cost databases (RSMeans, Dodge), and market participant interviews. Actual transaction prices may vary significantly based on volume commitments, contract terms, and customer relationships.

**Landed cost models:** Import landed cost models are constructed from FOB price estimates (derived from CIF import prices minus estimated freight costs), tariff rate schedules (USITC), port cost proformas (platform port cost model), and trucking/rail cost schedules. Individual cost components carry estimation uncertainty of +/-10-20%.

### Chapter 8: Demand Drivers & Outlook

**Consumption forecasts:** Forward-looking consumption projections are based on PCA baseline forecasts, adjusted for platform-level analysis of federal spending pipelines (IIJA, CHIPS, IRA), building permit trends, and state DOT contract awards. Forecasts carry inherent uncertainty and should be interpreted as scenario-based ranges rather than point predictions.

**Cement intensity ratios:** Cement consumption per unit of construction output (MT per housing unit, MT per lane-mile, etc.) is derived from industry standards (ACI, PCA), engineering reference manuals, and project-level analysis. Ratios vary significantly by project design, local specifications, and climate conditions.

### Chapter 9: SESCO Market Position

**SESCO import data:** SESCO-specific import volume and source country data is derived entirely from Panjiva import manifests for the 2023-2025 period. This data captures ocean import manifests filed with US Customs and represents the most comprehensive publicly available source for company-level import analysis. Volumes may slightly undercount actual imports due to confidential treatment or manifest consolidation.

**Tampa market entry projections:** Volume targets and financial projections for SESCO's Tampa operations are drawn from the January 2026 Tampa Bay Cement Market Study prepared for SESCO Cement Corporation. These projections represent management targets and are subject to execution risk, market conditions, and competitive responses.

---

## 10.5 Data Currency Statement

**Report data currency: Q1 2026**

| Data Source | Most Recent Data Used | Lag |
|-------------|----------------------|-----|
| USGS Mineral Commodity Summaries | 2025 edition (2024 data) | ~12 months |
| EPA FRS | December 2025 pull | Current |
| Census Foreign Trade | November 2025 | ~45 days |
| Panjiva Import Manifests | January 2026 | ~7 days |
| USDA GTR Barge Rates | January 2026 | Weekly current |
| STB Rail Statistics | 2023 (annual) | ~18 months |
| USACE Waterborne Commerce | 2023 (annual) | ~12 months |
| Clarksons Freight Rates | December 2025 spot, CY2026 forward | ~30 days |
| AAR Weekly Rail Traffic | January 2026 | Weekly current |
| GEM Cement Tracker | July 2025 update | ~6 months |
| PCA Outlook | Q4 2025 publication | ~3 months |

**Data refresh schedule:** This report will be updated quarterly, with the next planned update in Q2 2026. Interim updates may be issued if significant market events occur (tariff changes, major plant announcements, Section 301 fee implementation changes).

---

## 10.6 Known Limitations

### 10.6.1 Data Gaps

1. **Company-level production data.** USGS withholds individual company and plant-level production data. All company market share estimates are approximations based on capacity, import data, and industry knowledge. Actual production-based shares may differ from capacity-based estimates due to varying utilization rates.

2. **Real-time pricing data.** US cement is not traded on an exchange, and transaction prices are negotiated bilaterally between producers/importers and customers. No real-time price index exists for US cement comparable to commodity benchmarks for oil, steel, or grain. Price estimates in this report represent market ranges based on multiple indicators.

3. **Cement-specific barge and rail data.** Federal transportation statistics group cement with broader "nonmetallic minerals" categories, making it difficult to isolate cement-specific freight volumes. Platform estimates for cement-specific volumes are derived from commodity proportion analysis and cross-referencing with plant location and distribution data.

4. **White cement market data.** The US white cement market is poorly documented in public data sources. Market size estimates (42,000-55,000 MT/yr for Florida, 350,000-500,000 MT/yr nationally) are derived from industry participant estimates and should be treated as order-of-magnitude approximations.

5. **Section 301 vessel fee implementation.** The Section 301 maritime fee structure was announced in early 2025 with phased implementation through 2026. Final fee levels, exemptions, and enforcement mechanisms are still evolving. The analysis in this report uses announced fee ranges and may require revision as implementation details are finalized.

6. **Terminal capacity data.** Import terminal storage capacities and throughput rates are not systematically reported. Terminal specifications in this report are based on company disclosures, port authority data, and industry estimates.

### 10.6.2 Analytical Limitations

1. **Forward-looking projections.** All forecasts and projections in this report are based on current data, identified trends, and stated assumptions. Actual outcomes may differ materially due to unforeseen economic, policy, or market developments.

2. **Regional generalization.** The US cement market operates as a collection of regional markets with distinct competitive dynamics. National averages and generalizations may not accurately represent conditions in specific local markets.

3. **Tariff policy uncertainty.** US trade policy is subject to change with limited advance notice. Tariff rates cited in this report reflect current law and regulation as of Q1 2026. Policy changes subsequent to this report's publication may invalidate tariff-dependent analysis.

4. **Competitive intelligence limitations.** Competitor strategies, financial conditions, and operational capabilities described in this report are based on publicly available information and informed industry analysis. Non-public competitive developments may not be reflected.

---

## 10.7 Source Bibliography

### Government Sources

| Source | Agency | URL |
|--------|--------|-----|
| Mineral Commodity Summaries - Cement | USGS | https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information |
| Facility Registry Service | EPA | https://www.epa.gov/frs |
| Foreign Trade Statistics | US Census Bureau | https://usatrade.census.gov/ |
| Grain Transportation Report | USDA AMS | https://www.ams.usda.gov/services/transportation-analysis/gtr |
| Freight Commodity Statistics | STB | https://www.stb.gov/reports-data/economic-data/freight-commodity-statistics/ |
| Waterborne Commerce Statistics | USACE WCSC | https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/ |
| Navigation Data Center | USACE NDC | https://ndc.ops.usace.army.mil/ |
| Freight Analysis Framework | BTS | https://www.bts.gov/faf |
| USITC Tariff Database | USITC | https://hts.usitc.gov/ |
| Weekly Rail Traffic Reports | AAR | https://www.aar.org/data-center/ |

### Industry Sources

| Source | Publisher | Notes |
|--------|-----------|-------|
| PCA Long-Term Cement Outlook | Portland Cement Association | Subscription; consumption forecasts |
| Global Cement Tracker | Global Energy Monitor | Open access; plant-level data |
| Clarksons Shipping Intelligence | Clarksons Research | Subscription; freight rates |
| Panjiva Trade Data | S&P Global Market Intelligence | Subscription; import manifests |
| Global Cement Magazine | Global Cement | Industry news and analysis |
| CemNet | The European Cement Association | Industry news portal |
| Rock Products Magazine | Endeavor Business Media | Industry news |
| Minerals Education Coalition | National Mining Association | Reference materials |
| Waterways Journal | Waterways Journal Inc. | Barge industry news |

### Platform Toolsets

| Toolset | Location | Application |
|---------|----------|-------------|
| Barge Cost Model | `02_TOOLSETS/barge_cost_model/` | Barge freight modeling |
| Rail Cost Model | `02_TOOLSETS/rail_cost_model/` | Rail freight modeling |
| Port Cost Model | `02_TOOLSETS/port_cost_model/` | Vessel call cost proformas |
| Facility Registry | `02_TOOLSETS/facility_registry/` | Plant and terminal database |
| Vessel Intelligence | `02_TOOLSETS/vessel_intelligence/` | Vessel tracking and Section 301 |
| Policy Analysis | `02_TOOLSETS/policy_analysis/` | Trade policy monitoring |
| Geospatial Engine | `02_TOOLSETS/geospatial_engine/` | Geographic analysis and mapping |

### Reference Reports

| Report | Author | Date | Relevance |
|--------|--------|------|-----------|
| Tampa Bay Cement Market Study | Market Intelligence Division | January 2026 | SESCO Florida market entry analysis |
| Florida Cement Market Research Consolidation | Platform Research Team | December 2025 | Florida competitive and demand data |
| Rail and Barge Freight Statistics | Platform Research Team | December 2025 | Freight mode analysis |
| Gulf Cement Report | Platform Analysis | August 2025 | Gulf Coast market intelligence |

---

## 10.8 Disclaimer

This report is prepared for strategic planning and market intelligence purposes. While every effort has been made to ensure accuracy and completeness, the data, analysis, and projections contained herein are based on publicly available sources, proprietary analytical models, and informed industry judgment. No representation or warranty is made as to the accuracy, completeness, or reliability of the information. Forward-looking statements and projections are inherently uncertain and should not be relied upon as predictions of actual outcomes. Users of this report should independently verify critical data points and consult with qualified professionals before making investment, operational, or strategic decisions based on the information presented.

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | Data current as of Q1 2026*
