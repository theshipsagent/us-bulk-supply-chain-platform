# US Bulk Supply Chain Report — Executive Summary

**US Bulk Supply Chain Reporting Platform v1.0.0**
**OceanDatum.ai | Q1 2026**

---

## Overview

This report provides a comprehensive, commodity-agnostic assessment of the United States bulk supply chain infrastructure — the interconnected waterway, port, rail, pipeline, and vessel networks that move over 4 billion tons of raw materials, agricultural products, energy commodities, and manufactured goods annually. It establishes the analytical foundation upon which commodity-specific modules (cement, grain, fertilizer, petroleum, metals) are built, documenting infrastructure capacity, cost benchmarks, regulatory constraints, and investment outlook across all modes.

The US operates the world's most extensive inland waterway system (12,000+ commercially navigable miles), 140,000 miles of Class I railroad track, 300+ deep-water port facilities, and 2.7 million miles of pipeline. These assets are supported by a domestic Jones Act fleet and supplemented by foreign-flag ocean tonnage. Together, they constitute the physical backbone of the American economy's raw material supply chains.

---

## Key Findings

### 1. Aging Lock Infrastructure Threatens Waterway Reliability

Fifty-four percent (54%) of USACE-maintained locks have exceeded their 50-year engineered design life. The cumulative modernization backlog exceeds **$12 billion**, with the IIJA's $2.5 billion inland waterway allocation addressing only the most critical projects (Chickamauga, Kentucky, LaGrange locks). Lock delays cost the barge industry an estimated $1.1 billion annually in tow operating time, with the worst bottlenecks (Lock 25, Upper Mississippi) imposing average delays of 6--8 hours during peak season. Unscheduled closures due to mechanical failure are increasing in frequency, creating unpredictable supply chain disruptions.

### 2. Barge Transportation Delivers 40--65% Cost Savings Over Rail

Inland waterway barge transport costs **$0.008--$0.015 per ton-mile**, compared to rail at **$0.025--$0.045 per ton-mile** and truck at **$0.10--$0.25 per ton-mile**. For bulk commodities with waterway access, this translates to a **40--65% cost advantage** over rail on parallel corridors, making modal access to the waterway system a decisive factor in supply chain design. A 15-barge tow moves the equivalent of 1,050 trucks or 216 railcars, with one-sixth the carbon emissions per ton-mile of trucking.

### 3. Section 301 Maritime Fees Disrupt Import Economics

Section 301 maritime shipping fees targeting Chinese-built vessels, effective October 2025, impose **$500,000--$1,000,000 per voyage** on affected bulk carriers. This adds **$16--33 per ton** to delivered costs — a material impact for low-value bulk commodities where ocean freight already constitutes 25--40% of the landed price. The fees are accelerating fleet recomposition, with charterers and shippers shifting to non-Chinese-built tonnage at premium rates, and reshaping trade flow patterns away from direct China-origin sourcing.

### 4. Gulf Coast Dominates US Bulk Throughput

The US Gulf Coast handles approximately **65% of waterborne bulk commodity throughput**, with the Lower Mississippi River complex (Baton Rouge to Head of Passes) serving as the primary gateway for both import and export flows. Port Houston, New Orleans, and the South Louisiana port complex collectively process over 500 million tons annually. This geographic concentration creates efficiency through scale but also systemic vulnerability to hurricanes, low-water events, and single-point infrastructure failures.

### 5. Railroad Consolidation Constrains Bulk Shipper Options

Seven Class I railroads control **94% of US freight rail revenue**. The Western duopoly (BNSF/UP) and Eastern duopoly (CSX/NS) mean that many bulk shippers have access to at most two — and frequently only one — Class I carrier. The Surface Transportation Board's proposed **reciprocal switching access rules** could reduce rail rates **5--15%** for captive bulk shippers, though industry opposition has delayed implementation. Revenue-to-variable-cost ratios exceeding 180% for captive commodities (coal, chemicals) confirm significant pricing power by railroads over single-served shippers.

---

## Report Structure

| Chapter | Title | Key Topics |
|---------|-------|------------|
| 00 | Executive Summary | Key findings, report structure, data currency |
| 01 | Executive Overview | Purpose, scope, methodology, data sources |
| 02 | US Inland Waterway System | Mississippi River System, 239 lock chambers, traffic patterns, IWTF, lock delay analysis |
| 03 | Port Infrastructure | Gulf, Atlantic, Pacific bulk terminals; draft depths; berth capacity; tariff structures |
| 04 | Railroad Network | Class I operations, URCS cost methodology, R/VC ratios, captive shipper economics |
| 05 | Intermodal Connectivity | Barge-rail-truck transfer points, transload facilities, first/last mile constraints |
| 06 | US Vessel Fleet | Jones Act domestic fleet, foreign-flag import fleet, Section 301 vessel classification |
| 07 | Trade Flow Analysis | Import/export commodity patterns, Panjiva manifest analysis, origin-destination flows |
| 08 | Regulatory Environment | Section 301 fees, Jones Act, EPA emissions rules, STB proceedings, CBP requirements |
| 09 | Cost Benchmarking | Modal cost comparison framework, GTR barge rate engine, URCS rail costing, port proforma |
| 10 | Infrastructure Outlook | IIJA investment pipeline, lock modernization, port expansion, technology trends, demand projections |
| Annex A | Data Tables | Waterway statistics, port tonnage rankings, lock dimensions, railroad metrics, rate benchmarks |
| Annex B | Map Catalog | Waterway system, lock locations, port infrastructure, rail network, commodity flows |
| Annex C | Source Bibliography | Federal, industry, and academic sources with URLs and access dates |

---

## Analytical Framework

This report's quantitative analysis is produced by six integrated toolsets within the US Bulk Supply Chain Reporting Platform:

- **Barge Cost Model** — USDA GTR-based rate engine with VAR/SpVAR forecasting across 7 corridor segments
- **Rail Cost Model** — NTAD/NARN network graph with URCS variable cost methodology and R/VC ratio analysis
- **Port Cost Model** — Multi-component proforma estimation covering pilotage, towage, dockage, wharfage, cargo handling, and ancillary charges
- **Facility Registry** — EPA FRS integration with 4M+ facility records in DuckDB for geographic supply chain mapping
- **Vessel Intelligence** — 7-phase Panjiva classification pipeline for vessel build-origin, ownership, and Section 301 exposure analysis
- **Policy Analysis** — Section 301, Jones Act, tariff, and environmental compliance impact modeling

---

## Data Currency and Limitations

All statistics, cost benchmarks, and infrastructure project statuses reflect the most recent publicly available data as of the date below. Waterway tonnage and lock performance data are sourced from USACE WCSC/NDC. Railroad financial data are from STB annual reports and R-1 filings. Port statistics are from individual port authority annual reports and USACE waterborne commerce data. Vessel fleet data are from MARAD and USCG databases, supplemented by Panjiva import manifests.

Where data vintages differ across sources (e.g., USACE tonnage data lagging by 12--18 months), the most recent available year is used with the vintage clearly noted. Cost benchmarks represent 2024--2025 market conditions unless otherwise specified. Infrastructure project cost estimates are subject to revision as construction progresses.

**Data current as of Q1 2026.**

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | OceanDatum.ai*
