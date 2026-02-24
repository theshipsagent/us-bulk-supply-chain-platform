# BUILD NOTES — Natural Pozzolans Comprehensive Dossier
# Location: G:\My Drive\LLM\project_master_reporting\natural_pozzolan\
# Created: 2026-02-18

## Project Purpose

Comprehensive market intelligence dossier on natural pozzolans used as SCMs in cement and concrete — covering volcanic ash/pumice, calcined clay, metakaolin, diatomaceous earth, LC3 (Limestone Calcined Clay Cement), and their role as replacements for declining fly ash and GGBFS supplies. Modeled after the fly ash, aggregates, and slag dossier formats.

## File Inventory

| File | Format | Size | Description |
|------|--------|------|-------------|
| `NATURAL_POZZOLAN_COMPREHENSIVE_DOSSIER.html` | HTML5 | ~50KB | Main dossier: 15 sections with SVG charts, styled tables, dashboard |
| `BUILD_NOTES.md` | Markdown | This file | Build methodology, data sources, NAICS/HTS codes |
| `HANDOFF.md` | Markdown | ~8KB | Handoff for master_reporting session |

## Data Sources Used

### Primary (Quantitative)
- **USGS MCS 2024-2025** — Pumice and Pumicite (production, trade, reserves)
- **National Pozzolan Association (NPA)** — 2.5 Mt shipments (2024); 3.5-4.0 Mt capacity by 2028
- **ACAA 2024 Production & Use Survey** — CCP 63.6 Mt; fly ash to concrete 14.7 Mt
- **DOE OCED** — $1.6B Industrial Demonstrations Program (6 cement decarb projects, 3 LC3)
- **Concrete Products Magazine** — SCM shipments exceed 20 Mt (2024)

### Company Data
- Hess Pumice Products — Largest processed pumice producer globally
- CR Minerals — ~18% revenue share; Santa Fe NM
- Eco Material Technologies — >4 Mt/yr SCM capacity; 9 plants; 45 states
- Kirkland Mining — 39 Mt reserves; 500K t/yr; opened 2022
- Ash Grove/CRH — Acquired Geofortis pozzolan ops Sep 2024
- Sunrise Resources — Hazen Pozzolan Project NV
- Burgess Pigment — OPTIPOZZ metakaolin (Sandersville GA)
- Advanced Cement Technologies — PowerPozz metakaolin

### Market Research
- Technavio, Intel Market Research, Verified Market Reports — Natural pozzolan market sizing
- IMARC Group — US perlite market ($370M); fly ash pricing
- ChemAnalyst — Metakaolin pricing ($171/Mt US Q3 2025)
- McKinsey — SCM revenues $15-30B today → $40-60B by 2035

### LC3 / Sustainability
- RMI — Business Case for LC3 (Dec 2024)
- ACEEE — LC3 could save 7.3 Mt CO2/yr in US
- LC3.ch — Official LC3 technology documentation
- BIS IS 18189:2023 — India LC3 standard

### Regulatory / Standards
- ASTM C618-25a, C595/C595M-24, C1157, C1240, C1697, C1945
- TxDOT DMS-4635; NYSDOT Section 501; WSDOT M 41-10; Caltrans
- FHWA Natural Pozzolan SCMs Research
- EPA CPG; GSA Buy Clean / IRA

## Key NAICS Codes

| NAICS | Description | Relevance |
|-------|-------------|-----------|
| 212399 | All Other Nonmetallic Mineral Mining and Quarrying | Pumice, volcanic ash mining |
| 212325 | Clay and Ceramic and Refractory Minerals Mining | Kaolin for metakaolin/calcined clay |
| 212312 | Crushed and Broken Limestone Mining | Limestone for LC3 |
| 327310 | Cement Manufacturing | Blended cement with pozzolans |
| 327320 | Ready-Mix Concrete Manufacturing | Pozzolan consumers |
| 327999 | All Other Miscellaneous Nonmetallic Mineral Product Mfg | Pozzolan processing |
| 325199 | All Other Basic Organic Chemical Manufacturing | Some pozzolan processing |

## Key HTS Codes

| HTS | Description | Relevance |
|-----|-------------|-----------|
| 2513.10.0010 | Pumice, crude or in irregular pieces | Primary import code |
| 2513.10.0080 | Pumice, except crude or crushed | Processed pumice imports |
| 2530.90 | Other mineral substances NES | Some volcanic ash/pozzolans |
| 2507 | Kaolin and other kaolinic clays | Metakaolin/calcined clay feedstock |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-18 | Initial comprehensive dossier — 15 sections covering types, production, market size, SCM crisis context, pricing, producers, LC3, properties, carbon, logistics, regulatory, outlook |

## Next Steps (for master_reporting integration)

1. Plug into `03_COMMODITY_MODULES/natural_pozzolan/` in master_reporting structure
2. Run EPA FRS queries for NAICS 212399 to find nonmetallic mineral mining operations
3. Query Panjiva manifests for HTS 2513 to map pumice import flows
4. Cross-reference with fly ash (project_flyash), GGBFS (slag/), and aggregates (aggregate/) dossiers
5. Build combined SCM supply outlook: fly ash + GGBFS + natural pozzolan + LC3
6. Map pozzolan deposit locations vs concrete demand centers for distribution cost analysis
7. Track LC3 demonstration project progress (National Cement CA, Roanoke VA, Summit)
