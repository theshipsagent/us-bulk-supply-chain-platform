# BUILD NOTES — Slag Comprehensive Dossier
# Location: G:\My Drive\LLM\project_master_reporting\slag\
# Created: 2026-02-18

## Project Purpose

Comprehensive market intelligence dossier on slag used in construction and cement — focused on Ground Granulated Blast Furnace Slag (GGBFS) as a supplementary cementitious material (SCM), but also covering air-cooled BFS, steel slag, copper slag, phosphorus slag, and ferronickel slag. Covers domestic production, EAF transition supply risk, imports/trade flows, pricing, major producers, end uses, carbon/sustainability value, and regulatory drivers. Modeled after the fly ash and aggregates dossier formats.

## File Inventory

| File | Format | Size | Description |
|------|--------|------|-------------|
| `SLAG_COMPREHENSIVE_DOSSIER.html` | HTML5 | ~45KB | Main dossier: 15 sections with SVG charts, styled tables, dashboard metrics |
| `BUILD_NOTES.md` | Markdown | This file | Build methodology, data sources, NAICS/HTS codes, version history |
| `HANDOFF.md` | Markdown | ~8KB | Handoff document for master_reporting session with tool integration plan |

## Data Sources Used

### Primary (Quantitative)
- **USGS Mineral Commodity Summaries 2024-2025** — Iron and Steel Slag
  - Production/sales volumes, values, end-use breakdowns, trade data
  - URL: https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-iron-steel-slag.pdf
- **Slag Cement Association (SCA)** — Shipment data (4.4 Mt record 2023; 3.7 Mt 2024)
- **Skyway Cement Company** — Industry news, shipment trends
- **USGS Historical Statistics** — Iron and steel slag use patterns

### Company Data
- **Cleveland-Cliffs** — Blast furnace operations, granulation capacity, idlings
- **U.S. Steel / Nippon Steel** — Gary Works $3.1B reline investment
- **Heidelberg Materials** — Houston slag facility (500K t/yr, Sep 2024)
- **Holcim** — Slag grinding stations (IL 600K t/yr, Midfield AL 450K t/yr)
- **Edw. C. Levy Co.** — Largest US slag processor (10+ Mt/yr)
- **Charah Solutions** — Greens Port grinding, MultiCem product
- **Ecocem** — Europe's largest GGBS producer (2.4 Mt/yr); ACT product

### Market Research
- Transparency Market Research — GGBFS Market to $32.8B by 2031
- GM Insights — Slag Cement Market to $40.9B by 2034
- CW Group — Global GGBFS Demand forecasts
- ChemAnalyst — GGBFS spot pricing ($48-49/Mt Q1 2025)
- IMARC Group — GGBFS price trend analysis
- Business Research Insights — Market size estimates

### Steel Industry
- CATF — US Steel Sector Decarbonization Pathways
- Argus Media — EAF expansion analysis
- Fastmarkets — Americas steel industry timeline
- World Steel Association — Global production data

### Carbon & Sustainability
- CSMA (UK) — GGBS embodied carbon data (35-67 kg CO2e/t)
- PCA — Portland cement embodied carbon (844-967 kg CO2e/t)
- GSA — Buy Clean / Low-Embodied Carbon Program
- USGBC — LEED v5 embodied carbon requirements
- Ecocem — ACT product ASTM-certified 60% carbon reduction

### Trade Data
- TrendEconomy — HTS 2618 US trade flows
- OEC — Global granulated slag trade patterns
- Datamyne — US import records

### Regulatory
- ASTM C989/C989M-22 — Slag cement grades
- ASTM C595/C595M-24 — Blended hydraulic cements
- ASTM C1157 — Performance hydraulic cement
- EPA CPG — Slag cement as designated product
- FHWA — Air-cooled BFS usage guidelines

## HTML Template

Reused CSS/HTML framework from the fly ash and aggregates dossiers:
- Same color scheme (#1a365d, #2c5282, #2b6cb0)
- Same styled components: `.highlight`, `.alert`, `.success`, `.info`, `.price-box`, `.stat-grid`
- Same SVG chart approach (inline, no external dependencies)
- Print-ready (`@media print` rules)

## Key NAICS Codes (for facility matching via EPA FRS / project_rail)

| NAICS | Description | Relevance |
|-------|-------------|-----------|
| 331110 | Iron and Steel Mills and Ferroalloy Manufacturing | BF-BOF mills (GGBFS source) |
| 331111 | Iron and Steel Mills | Subset — integrated mills |
| 331112 | Electrometallurgical Ferroalloy Product Manufacturing | EAF operations (steel slag only) |
| 327310 | Cement Manufacturing | Slag cement consumers/producers |
| 327320 | Ready-Mix Concrete Manufacturing | GGBFS end users |
| 327390 | Other Concrete Product Manufacturing | GGBFS end users |
| 212399 | All Other Nonmetallic Mineral Mining | Slag reprocessing operations |
| 562998 | All Other Miscellaneous Waste Management Services | Slag pile reprocessing |

## Key HTS Codes (for Panjiva/trade flow analysis)

| HTS | Description | Relevance |
|-----|-------------|-----------|
| 2618.00.0000 | Granulated slag (slag sand) from iron/steel manufacture | **PRIMARY — GGBFS imports** |
| 2619.00 | Slag, dross (non-granulated) from iron/steel manufacture | Steel slag, air-cooled BFS |
| 2523 | Portland cement, aluminous cement, slag cement | Blended/slag cement products |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-18 | Initial comprehensive dossier — 15 sections covering GGBFS/slag types, US production, EAF transition, global market, trade flows, pricing, producers, SCM context, properties, carbon, regulatory, logistics, trends |

## Next Steps (for master_reporting integration)

1. **Plug into 03_COMMODITY_MODULES/slag/** in project_master_reporting structure
2. **Run EPA FRS queries** for NAICS 331110/331111 to map all integrated steel mills
3. **Query Panjiva manifests** for HTS 2618 to map GGBFS import flows by vessel, port, origin
4. **Cross-reference** with fly ash dossier (project_flyash) — both SCMs face parallel supply crises
5. **Cross-reference** with cement markets (project_cement_markets) — demand-side analysis
6. **Cross-reference** with aggregates dossier (aggregate/) — limestone feeds cement which consumes GGBFS
7. **Rail cost modeling** — distribution from Great Lakes steel mills to demand centers
8. **Barge cost modeling** — waterway distribution from BF locations on Great Lakes / Ohio River
9. **Terminal analysis** — map import terminal capacity vs. projected import demand growth
