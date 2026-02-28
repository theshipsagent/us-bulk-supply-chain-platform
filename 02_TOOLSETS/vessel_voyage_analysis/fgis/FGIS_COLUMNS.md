# FGIS Export Grain Database — Column Reference & Data Definitions

**Database:** `G:\My Drive\LLM\project_mrtis\fgis\fgis_export_grain.duckdb`
**Raw CSVs:** `G:\My Drive\LLM\project_mrtis\fgis\raw_data\CY*.csv`
**Source:** https://fgisonline.ams.usda.gov/ExportGrainReport/default.aspx
**Total Columns:** 113 (112 original + 1 added)
**Total Rows:** 580,081 (1983–2026, 44 calendar year files)

---

## Data Definitions

### Carrier Classification Codes

| Code | Carrier Type |
|------|-------------|


*| 1 | Ship | filter on carrier type ship 




| 2 | Rail (Single Lot) |
| 3 | Rail (CU-SUM) |
| 4 | Truck |
| 5 | Barge |
| 6 | Container |
| 7 | Other |
| 8 | Rail (Composite) |

### Shipment Type (Type Shipm)

| Code | Description |
|------|-------------|

*| BU | Bulk (570,932 records) | filter on shipment type bulk 


| SA | Sacked (9,149 records) |

### Service Type (Type Serv)

| Code | Description |
|------|-------------|
| IW | Inspection & Weighing (455,661) |
| I | Inspection only (89,857) |
| PS | Phytosanitary (32,450) |
| OT | Other (1,678) |
| W | Weighing only (359) |
| TR | Transfer (60) |
| WT | Weight ticket (16) |

### Grade Codes

| Code | Description |
|------|-------------|
| 1 | U.S. No. 1 |
| 2 | U.S. No. 2 |
| 2 O/B | U.S. No. 2 or Better (most common — 281,550 records) |
| 3 | U.S. No. 3 |
| 3 O/B | U.S. No. 3 or Better |
| 4 | U.S. No. 4 |
| 4 O/B | U.S. No. 4 or Better |
| 5 | U.S. No. 5 |
| 5 O/B | U.S. No. 5 or Better |
| NG | No Grade |
| SG | Sample Grade |
| SG O/B | Sample Grade or Better |
| OT | Other |

### Grain Commodities & Classes

| Grain | Class Code | Class Name |
|-------|-----------|------------|
| SOYBEANS | YSB | Yellow Soybeans |
| SOYBEANS | XSB | Mixed Soybeans |
| CORN | YC | Yellow Corn |
| CORN | WHC | White Corn |
| CORN | XC | Mixed Corn |
| WHEAT | HRW | Hard Red Winter |
| WHEAT | HRS | Hard Red Spring |
| WHEAT | SRW | Soft Red Winter |
| WHEAT | SWW | Soft White Winter |
| WHEAT | DUWH | Durum |
| WHEAT | HDWH | Hard White |
| WHEAT | XWHT | Mixed Wheat |
| SORGHUM | S | Sorghum |
| SORGHUM | WHS | White Sorghum |
| SORGHUM | TANS | Tannin Sorghum |
| SORGHUM | XS | Mixed Sorghum |
| BARLEY | BAR | Barley |
| BARLEY | MBLY | Malting Barley |
| OATS | O | Oats |
| SUNFLOWER | SF | Sunflower Seed |
| FLAXSEED | FLAX | Flaxseed |
| CANOLA | K | Canola |
| RYE | RYE | Rye |
| TRITICALE | TRIT | Triticale |
| MIXED | XGR | Mixed Grain |

### Wheat Subclasses (HRS only)

| SubClass Code | Description |
|--------------|-------------|
| DNS | Dark Northern Spring |
| NS | Northern Spring |
| RS | Red Spring |

### AMS Regions

| Region | Record Count |
|--------|-------------|
| INTERIOR | 325,232 |
| GULF | 144,169 |
| PACIFIC | 61,182 |
| ATLANTIC | 33,806 |
| LAKES | 13,038 |
| ST LAWR SWY | 2,654 |

### FGIS Regions

| Region | Record Count |
|--------|-------------|
| INTERIOR | 325,211 |
| EAST GULF | 114,214 |
| WEST COAST | 61,193 |
| EAST COAST | 33,806 |
| WEST GULF | 29,965 |
| LAKES | 13,038 |
| CANADA | 2,654 |

### Moisture Load Order (M LD ORD)

| Code | Description |
|------|-------------|
| MA | Maximum |
| AV | Average |
| MI | Minimum |
| MX | Max |
| NA | Not Applicable |

### Date Formats

| Field | Format | Example |
|-------|--------|---------|
| Thursday | YYYYMMDD | 20260101 (report/publication date) |

*|Cert Date | YYYYMMDD | 20260102 (certification date) | output this is the data of departure from port and data of loading, format for timeseries anslayis


| MKT YR | YYYYYY | 2526 (marketing year 2025–2026) |

### Volume / Weight Fields

| Field | Description |
|-------|-------------|

*output | Pounds | Weight of shipment in pounds |
*output| 1000 Bushels | Volume in thousands of bushels |
*output| Metric Ton | Weight in metric tons |

### Quality Factor Abbreviations

| Abbrev | Full Name |
|--------|-----------|
| DKG | Dockage |

*output | TW | Test Weight (lbs/bushel) |

| M | Moisture (%) |
| P | Protein (%) |
| FN | Falling Number |
| FM | Foreign Material (%) |
| HT | Heat Damaged Kernels (%) |
| DKT | Damaged Kernels Total (%) |
| SHBN | Shrunken & Broken (%) |
| DEF | Total Defects (%) |
| CCL | Contrasting Classes (%) |
| WOCL | Wheat of Other Classes (%) |
| DHV-HVAC-HARD | Dark Hard Vitreous / HVAC / Hardness |
| OWH | Other Wheat Hardness |
| WC | Waxy Content |
| OCOL | Other Color |
| SPL | Splits (%) |
| BNFM | Beans & Foreign Material (%) |
| SBLY | Soybeans of Other Color (%) |
| THIN | Thin Kernels (%) |
| BN | Broken (%) |
| BB | Broken & Beyond (%) |
| SKBN | Skins & Broken (%) |
| WO | Wild Oats (%) |
| SMUT | Smut (%) |
| PL | Purple / Plump (%) |
| OG | Other Grains (%) |
| HTMJ | Heat Major (%) |
| HTMI | Heat Minor (%) |
| FMJ | Foreign Material Major (%) |
| FMI | Foreign Material Minor (%) |
| MMJ | Material Other Major (%) |
| MMI | Material Other Minor (%) |
| DH | Dehulled (%) |
| AD | Admixture (%) |
| FMOW | Foreign Material & Other Wheat (%) |
| SO | Stones (%) |
| FMOWR | Foreign Material Other Wheat Residue (%) |
| DKG CERT | Dockage Certified (%) |
| BCFM | Broken Corn & Foreign Material (%) |
| BC | Broken Corn (%) |
| W HARD | Wheat Hardness |

### Oil Content Fields

| Abbrev | Full Name |
|--------|-----------|
| O AVG | Oil Average (%) |
| O LD ORD | Oil Load Order |
| O BASIS | Oil Basis |
| O SP | Oil Spec |
| O LD % | Oil Load Percent |
| O HIGH | Oil High (%) |
| O LOW | Oil Low (%) |

### Aflatoxin Fields

| Abbrev | Full Name |
|--------|-----------|
| AFLA PERF | Aflatoxin Performed (Y/N) |
| AFLA REQ | Aflatoxin Required (Y/N) |
| AFLA BASIS | Aflatoxin Basis (SL = Sublot) |
| AFLA SCR N | Aflatoxin Screen Negative count |
| AFLA SCN P | Aflatoxin Screen Positive count |
| AFLA QT N | Aflatoxin Quantitative Negative count |
| AFLA QT P | Aflatoxin Quantitative Positive count |
| AFLA AVG PPB | Aflatoxin Average (parts per billion) |
| AFLA REJ | Aflatoxin Rejected count |

### DON / Vomitoxin Fields

| Abbrev | Full Name |
|--------|-----------|
| DON REQ | DON Required (Y/N) |
| DON BASIS | DON Basis |
| DON QL | DON Qualitative |
| DON QT | DON Quantitative |
| DON AVG PPM | DON Average (parts per million) |
| DON REJ | DON Rejected |

### Insect / Treatment Fields

| Abbrev | Full Name |
|--------|-----------|
| SUBL W INS | Sublots with Insects |
| COMP INF | Complete Infestation |
| INS IN LOT | Insects in Lot |
| Insecticide | Insecticide applied |
| DUST SUPR | Dust Suppressant |
| DYE | Dye applied |
| Fumigant | Fumigant applied |

### External References

- **Grain Classifications (APS):** https://fgisonline.ams.usda.gov/G_APS/G_APS_ComClassHierarchy.aspx?pEM=D
- **Port & Region Definitions (PDF):** https://fgisonline.ams.usda.gov/F_DEC/exportRegionDefinitionTables0801.pdf
- **Destination Country Codes (Census Bureau):** https://www.census.gov/foreign-trade/schedules/c/countrycode.html
- **Contact:** FGISPoliciesProceduresMarketAnalysisBranch@usda.gov

---

## Column List (113 columns)

| # | Column Name | Type | Category | Definition |
|---|-------------|------|----------|------------|
| 1 | source_year | INTEGER | Added | Calendar year extracted from source filename (CY1983–CY2026) |
| 2 | Thursday | VARCHAR | Shipment | Report/publication date (YYYYMMDD — data released on Thursdays) |
| 3 | Serial No. | VARCHAR | Shipment | Unique inspection serial number |
*| 4 | Type Shipm | VARCHAR | Shipment | Shipment type: BU=Bulk, SA=Sacked |
| 5 | Type Serv | VARCHAR | Shipment | Service type: IW=Inspect&Weigh, I=Inspect, PS=Phyto, OT=Other, W=Weigh, TR=Transfer, WT=Weight Ticket |
*| 6 | Cert Date | VARCHAR | Shipment | Certification date (YYYYMMDD) |
*| 7 | Type Carrier | VARCHAR | Carrier | Carrier code: 1=Ship, 2=Rail Single, 3=Rail CU-SUM, 4=Truck, 5=Barge, 6=Container, 7=Other, 8=Rail Composite |
*| 8 | Carrier Name | VARCHAR | Carrier | Name of vessel, railcar, truck, or container ID |
*| 9 | Grade | VARCHAR | Quality | U.S. grain grade (1, 2, 2 O/B, 3, NG, SG, etc.) |
*| 10 | Grain | VARCHAR | Identity | Commodity name (SOYBEANS, CORN, WHEAT, SORGHUM, etc.) |
*| 11 | Class | VARCHAR | Identity | Grain class code (YSB, YC, HRW, HRS, SRW, etc.) |
*| 12 | SubClass | VARCHAR | Identity | Grain subclass code (DNS, NS, RS, etc. — mainly wheat) |
*| 13 | Spec Gr 1 | VARCHAR | Identity | Special grade designation 1 |
*| 14 | Spec Gr 2 | VARCHAR | Identity | Special grade designation 2 |
*| 15 | Pounds | VARCHAR | Volume | Shipment weight in pounds |
*| 16 | Destination | VARCHAR | Geography | Export destination country |
*| 17 | Subl/Carrs | VARCHAR | Carrier | Number of sublots or carriers in the shipment |
*| 18 | Field Office | VARCHAR | Geography | FGIS field office name |
*| 19 | Port | VARCHAR | Geography | Export port or location (MISSISSIPPI R., COLUMBIA R., INTERIOR, etc.) |
*| 20 | AMS Reg | VARCHAR | Geography | AMS region (GULF, PACIFIC, ATLANTIC, INTERIOR, LAKES, ST LAWR SWY) |
*| 21 | FGIS Reg | VARCHAR | Geography | FGIS region (EAST GULF, WEST GULF, WEST COAST, EAST COAST, INTERIOR, LAKES, CANADA) |
*| 22 | City | VARCHAR | Geography | City of inspection (primarily for interior shipments) |
*| 23 | State | VARCHAR | Geography | State of inspection (2-letter abbrev) |
| 24 | MKT YR | VARCHAR | Shipment | Marketing year code (e.g. 2526 = crop year 2025–2026) |
| 25 | DKG HIGH | VARCHAR | Dockage | Dockage high value (%) |
| 26 | DKG LOW | VARCHAR | Dockage | Dockage low value (%) |
| 27 | DKG AVG | VARCHAR | Dockage | Dockage average (%) |
*| 28 | TW | VARCHAR | Test Weight | Test weight (lbs/bushel) |
| 29 | M LD ORD | VARCHAR | Moisture | Moisture load order (MA=Max, AV=Avg, MI=Min) |
| 30 | M LD % | VARCHAR | Moisture | Moisture load order percent limit |
| 31 | M HIGH | VARCHAR | Moisture | Moisture high (%) |
| 32 | M LOW | VARCHAR | Moisture | Moisture low (%) |
| 33 | M AVG | VARCHAR | Moisture | Moisture average (%) |
| 34 | DHV-HVAC-HARD | VARCHAR | Quality | Dark Hard Vitreous kernels / HVAC / Hardness (%) |
| 35 | OWH | VARCHAR | Quality | Other wheat hardness (%) |
| 36 | WC | VARCHAR | Quality | Waxy content (%) |
| 37 | HT | VARCHAR | Quality | Heat damaged kernels (%) |
| 38 | DKT | VARCHAR | Quality | Damaged kernels total (%) |
| 39 | FM | VARCHAR | Quality | Foreign material (%) |
| 40 | SHBN | VARCHAR | Quality | Shrunken & broken kernels (%) |
| 41 | DEF | VARCHAR | Quality | Total defects (%) |
| 42 | CCL | VARCHAR | Quality | Contrasting classes (%) |
| 43 | WOCL | VARCHAR | Quality | Wheat of other classes (%) |
| 44 | P LD ORD | VARCHAR | Protein | Protein load order |
| 45 | P LD % | VARCHAR | Protein | Protein load order percent limit |
| 46 | P BASIS | VARCHAR | Protein | Protein basis (dry/wet) |
| 47 | P SP M | VARCHAR | Protein | Protein spec moisture |
| 48 | P HIGH | VARCHAR | Protein | Protein high (%) |
| 49 | P LOW | VARCHAR | Protein | Protein low (%) |
| 50 | P AVG | VARCHAR | Protein | Protein average (%) |
| 51 | FN BASIS | VARCHAR | Falling Number | Falling number basis |
| 52 | FN SP M | VARCHAR | Falling Number | Falling number spec moisture |
| 53 | FN | VARCHAR | Falling Number | Falling number value (seconds) |
| 54 | SUBL W INS | VARCHAR | Insect | Number of sublots with insects |
| 55 | COMP INF | VARCHAR | Insect | Complete infestation count |
| 56 | INS IN LOT | VARCHAR | Insect | Insects found in lot count |
| 57 | Insecticide | VARCHAR | Treatment | Insecticide applied (type/name) |
| 58 | DUST SUPR | VARCHAR | Treatment | Dust suppressant applied (Y/N or type) |
| 59 | DYE | VARCHAR | Treatment | Dye applied (Y/N or type) |
*| 60 | Fumigant | VARCHAR | Treatment | Fumigant applied (type: OP=open, etc.) |
| 61 | OCOL | VARCHAR | Quality | Other color (%) |
| 62 | AFLA PERF | VARCHAR | Aflatoxin | Aflatoxin test performed (Y/N) |
| 63 | SPL | VARCHAR | Quality | Splits (%) — primarily soybeans |
| 64 | BNFM | VARCHAR | Quality | Beans & foreign material (%) |
| 65 | SBLY | VARCHAR | Quality | Soybeans of other color (%) |
| 66 | THIN | VARCHAR | Quality | Thin kernels (%) |
| 67 | BN | VARCHAR | Quality | Broken (%) |
| 68 | BB | VARCHAR | Quality | Broken & beyond (%) |
| 69 | SKBN | VARCHAR | Quality | Skins & broken (%) |
| 70 | WO | VARCHAR | Quality | Wild oats (%) |
| 71 | SMUT | VARCHAR | Quality | Smut (%) |
| 72 | PL | VARCHAR | Quality | Plump kernels (%) |
| 73 | OG | VARCHAR | Quality | Other grains (%) |
| 74 | HTMJ | VARCHAR | Heat Damage | Heat damage major (%) |
| 75 | HTMI | VARCHAR | Heat Damage | Heat damage minor (%) |
| 76 | FMJ | VARCHAR | Foreign Material | Foreign material major (%) |
| 77 | FMI | VARCHAR | Foreign Material | Foreign material minor (%) |
| 78 | MMJ | VARCHAR | Quality | Material other major (%) |
| 79 | MMI | VARCHAR | Quality | Material other minor (%) |
| 80 | DH | VARCHAR | Quality | Dehulled (%) |
| 81 | O AVG | VARCHAR | Oil | Oil content average (%) |
| 82 | AD | VARCHAR | Quality | Admixture (%) |
| 83 | FMOW | VARCHAR | Quality | Foreign material & other wheat (%) |
| 84 | SO | VARCHAR | Quality | Stones (%) |
| 85 | FMOWR | VARCHAR | Quality | Foreign material other wheat residue (%) |
*| 86 | 1000 Bushels | VARCHAR | Volume | Shipment volume in thousands of bushels |
*| 87 | Metric Ton | VARCHAR | Volume | Shipment weight in metric tons |
| 88 | DKG CERT | VARCHAR | Dockage | Dockage as certified (%) |
| 89 | BCFM | VARCHAR | Quality | Broken corn & foreign material (%) — corn specific |
| 90 | O LD ORD | VARCHAR | Oil | Oil load order |
| 91 | O BASIS | VARCHAR | Oil | Oil basis |
| 92 | BC | VARCHAR | Quality | Broken corn (%) |
| 93 | O SP | VARCHAR | Oil | Oil spec |
| 94 | O LD % | VARCHAR | Oil | Oil load order percent |
| 95 | O HIGH | VARCHAR | Oil | Oil content high (%) |
| 96 | O LOW | VARCHAR | Oil | Oil content low (%) |
| 97 | AFLA REQ | VARCHAR | Aflatoxin | Aflatoxin test required (Y/N) |
| 98 | AFLA BASIS | VARCHAR | Aflatoxin | Aflatoxin basis (SL=Sublot) |
| 99 | AFLA SCR N | VARCHAR | Aflatoxin | Aflatoxin screen — negative count |
| 100 | AFLA SCN P | VARCHAR | Aflatoxin | Aflatoxin screen — positive count |
| 101 | AFLA QT N | VARCHAR | Aflatoxin | Aflatoxin quantitative — negative count |
| 102 | AFLA QT P | VARCHAR | Aflatoxin | Aflatoxin quantitative — positive count |
| 103 | AFLA AVG PPB | VARCHAR | Aflatoxin | Aflatoxin average (parts per billion) |
| 104 | AFLA REJ | VARCHAR | Aflatoxin | Aflatoxin rejected count |
| 105 | W HARD | VARCHAR | Quality | Wheat hardness value |
| 106 | P LD ORD 2 | VARCHAR | Protein | Protein load order (secondary) |
| 107 | P LD % 2 | VARCHAR | Protein | Protein load order percent (secondary) |
| 108 | DON REQ | VARCHAR | DON | DON/Vomitoxin test required (Y/N) |
| 109 | DON BASIS | VARCHAR | DON | DON basis |
| 110 | DON QL | VARCHAR | DON | DON qualitative result |
| 111 | DON QT | VARCHAR | DON | DON quantitative result |
| 112 | DON AVG PPM | VARCHAR | DON | DON average (parts per million) |
| 113 | DON REJ | VARCHAR | DON | DON rejected count |
