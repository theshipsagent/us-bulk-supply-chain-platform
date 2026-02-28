# BUILD NOTES — Aggregates Comprehensive Dossier
# Location: G:\My Drive\LLM\project_master_reporting\aggregate\
# Created: 2026-02-18

## Project Purpose

Comprehensive market intelligence dossier on US construction aggregates (crushed stone, sand & gravel, limestone) — covering domestic production, demand drivers, pricing, trade flows, major producers, end uses, logistics, and regulatory environment. Modeled after the fly ash dossier format from `project_flyash`.

## File Inventory

| File | Format | Size | Description |
|------|--------|------|-------------|
| `AGGREGATES_COMPREHENSIVE_DOSSIER.html` | HTML5 | ~35KB | Main dossier with embedded SVG charts, styled tables, dashboard metrics |
| `BUILD_NOTES.md` | Markdown | This file | Build methodology, data sources, version history |
| `HANDOFF.md` | Markdown | ~10KB | Handoff document for master_reporting session with tool integration plan |

## Data Sources Used

### Primary (Quantitative)
- **USGS Mineral Commodity Summaries 2025** — Crushed Stone, Sand & Gravel, Cement, Lime
  - Production volumes, values, state rankings, end-use breakdowns
  - URL: https://pubs.usgs.gov/periodicals/mcs2025/
- **US Census Bureau** — Monthly Construction Spending (Dec 2024)
- **Vulcan Materials** — Q4/FY2024 Earnings Release (Feb 2025)
- **Martin Marietta** — Q4/FY2024 Earnings Release (Feb 2025)
- **CRH plc** — Q3 2024 Results

### Secondary (Market Intelligence)
- Technavio — US Construction Aggregates Market Report
- SNS Insider — Global Aggregates Market to $771.5B by 2033
- Credence Research — US Construction Aggregates Market
- Precedence Research — Global Aggregates Market
- GM Insights — Construction Aggregates Market Analysis
- Phoenix Center — Aggregates Industry 2025 Scorecard

### Regulatory
- MSHA — 30 CFR Mine Safety & Health Regulations
- EPA — Clean Water Act (NPDES), Clean Air Act
- OSMRE — Surface Mining Control & Reclamation Act
- USACE — Section 404 Wetlands Permits

### Trade Publications
- Pit & Quarry Magazine
- Equipment World — Top US Aggregates Producers
- Concrete Financial Insights
- Rock Products

## HTML Template

Reused CSS/HTML framework from `G:\My Drive\LLM\project_flyash\FLY_ASH_COMPREHENSIVE_DOSSIER_v2.html`:
- Same color scheme (#1a365d, #2c5282, #2b6cb0)
- Same styled components: `.highlight`, `.alert`, `.success`, `.info`, `.price-box`, `.stat-grid`
- Same SVG chart approach (inline, no external dependencies)
- Same section hierarchy (H1 > H2 > H3 > H4)
- Print-ready (`@media print` rules)

## Build Method

1. Research phase: Web searches for USGS MCS 2025, company filings, market reports
2. Data compilation: Extracted key metrics into structured tables
3. HTML authoring: Applied fly ash dossier template with aggregates-specific content
4. Chart creation: SVG bar charts, line charts, pie charts, conceptual diagrams
5. Review: Cross-referenced data points across multiple sources

## Key NAICS Codes (for facility matching via EPA FRS / project_rail)

| NAICS | Description |
|-------|-------------|
| 212321 | Crushed and Broken Limestone Mining |
| 212322 | Crushed and Broken Granite Mining |
| 212324 | Crushed and Broken Slate Mining |
| 212325 | Construction Sand and Gravel Mining |
| 212399 | All Other Crushed and Broken Stone Mining and Quarrying |
| 327310 | Cement Manufacturing |
| 327320 | Ready-Mix Concrete Manufacturing |
| 327390 | Other Concrete Product Manufacturing |
| 327420 | Gypsum Product Manufacturing |
| 327991 | Cut Stone and Stone Product Manufacturing |
| 424510 | Metals and Minerals Merchant Wholesalers |

## Key HTS Codes (for Panjiva/trade flow analysis)

| HTS | Description |
|-----|-------------|
| 2517 | Pebbles, gravel, broken stone (road/railway ballast) |
| 2518 | Dolomite, agglomerated dolomite |
| 2521 | Limestone flux; limestone for cement/lime |
| 2522 | Quicklime, slaked lime, hydraulic lime |
| 2523 | Portland cement, aluminous cement, slag cement |
| 2525 | Mica (crude and processed) |
| 2530 | Mineral substances NES |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-18 | Initial comprehensive dossier — production, demand, pricing, producers, logistics, regulatory, trends |

## Next Steps (for master_reporting integration)

1. **Plug into 03_COMMODITY_MODULES/aggregates/** in project_master_reporting structure
2. **Run EPA FRS queries** using NAICS codes above to build facility database
3. **Query Panjiva manifests** for HTS 2517-2523 to map import trade flows
4. **Rail cost modeling** — identify rail-served quarries using project_rail/SCRS data
5. **Barge cost modeling** — map waterway-served aggregate terminals
6. **Geospatial analysis** — quarry proximity to demand centers, transportation network overlay
7. **Competitive landscape** — entity resolution on producer names using EPA FRS + rail data
