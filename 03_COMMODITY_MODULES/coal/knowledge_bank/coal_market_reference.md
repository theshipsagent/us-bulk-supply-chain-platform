# Coal Market Reference
**Coal Commodity Module — Knowledge Bank**
*Last updated: 2026-03-02*

---

## US Coal Production Overview

- **Total US production (~2023):** ~580-600 million short tons (MST)
- **Powder River Basin:** ~250 MST (~42% of total) — all surface-mined sub-bituminous
- **Illinois Basin:** ~110 MST (~19%) — high-sulfur bituminous, resurgent due to scrubber adoption
- **Appalachian (all):** ~130 MST (~22%) — combination thermal/met coal
- **Other Western:** ~70 MST (~12%)

## Thermal vs. Metallurgical Split (exports)
- US exports ~90-95 MST/yr (2022-2024)
- Met coal: ~55-60% of export tonnage but ~65-70% of export revenue (higher price)
- Thermal coal: ~40-45% of export tonnage, declining market share globally

---

## Coal Rank and Market Implications

| Rank | BTU/lb | Key Property | Price Premium | Market |
|---|---|---|---|---|
| Low-vol HCC | 14,000+ | CSR > 68, ash < 7% | Very high | Premium steel mills |
| Mid-vol coking | 13,500+ | CSR 55-68 | High | Steel blend |
| High-vol A coking | 13,500-14,000 | Crossover met/thermal | Moderate | Steel or power |
| High-vol B thermal | 12,500-13,500 | High BTU steam coal | Moderate | Power plants |
| Sub-bituminous (PRB) | 8,400-8,800 | Very low sulfur | Low per ton, high volume | US power plants |
| Lignite | < 7,000 | Very high moisture | Lowest | Mine-mouth power only |

---

## Key Export Port Facts

### Hampton Roads, VA — #1 US Coal Export Hub
- **Capesize capable** — only major US East Coast coal port with 47 ft+ draft
- ~65-70% of all US metallurgical coal exports flow through Hampton Roads
- CSX "Cardinal Corridor" and NS "Pocahontas Division" feed this complex
- Lamberts Point (NS): Direct rail-to-vessel conveyor; largest single terminal
- DTA (Dominion Terminal): CONSOL Energy-linked; blending capability

### Mobile, AL — McDuffie Terminal
- Largest designed capacity in US: 32 MST/yr
- Uniquely serves THREE Class I railroads: CSX, NS, and CPKC (Kansas City Southern)
- Important for Alabama met coal (Warrior Basin) AND Illinois Basin/PRB thermal
- Panamax-limited (45 ft channel) — cannot load full Capesize; light-loads common

### Baltimore, MD — Curtis Bay
- CSX-only (former B&O "Sand Patch Grade" mainline via Cumberland, MD)
- Primarily Pennsylvania/NAPP metallurgical coal
- CONSOL's PAMC complex (Bailey/Enlow Fork/Harvey mines) feeds this terminal

---

## Competitive Global Position

### US Met Coal Strengths
- CAPP premium HCC (Buchanan, Pocahontas, Leer) = world's highest-quality hard coking coals
- Only Capesize loading capability (Hampton Roads) on US East Coast
- Rail to port transit time: 2-4 days (very reliable vs. Australia 6-8 week voyage to Asia)
- Atlantic basin proximity: 3,800 nm to ARA vs. 14,000+ nm from Australia

### US Met Coal Weaknesses
- Deep Appalachian mines = high cost vs. Australian surface mines
- Production declining structurally (seam depletion, regulatory pressure)
- Cannot economically export PRB coal to Asia (too far, too low BTU)

### Key Competitors
| Country | Product | Market | Benchmark |
|---|---|---|---|
| Australia | HCC + thermal | Asia (Japan/Korea/India) | NEWC, HCC Australian Premium |
| Indonesia | Sub-bituminous thermal | Asia | HBA, ICI 4 |
| Russia | Thermal + some met | Europe, Asia | FOB Kuznetsk |
| South Africa | Thermal | Europe, India | API4/RBIX |
| Colombia | Thermal | Europe, Caribbean | API2 blend |

---

## US Coal Demand Side (Consumption)

### Electric Power (~90% of domestic thermal demand)
- 2023: ~400 MST consumed at power plants (~60% of US domestic production)
- Declining ~5-8% per year due to gas switching and renewable growth
- Key consumers: Southeast utilities (TVA, Southern Co.), Midwest coops
- Plant retirement accelerating: 40+ GW of coal capacity retired 2015-2024

### Metallurgical/Industrial (~10% of domestic use)
- US blast furnace coke plants (Clairton PA = ArcelorMittal, largest US coke plant)
- Industrial coal for cement, paper, lime
- 2023: ~30-35 MST industrial + coke

### Export Market (~15-16% of production)
- 2023: ~95 MST exported
- Growing importance as domestic power demand declines
- Met coal: 100% export-oriented for premium CAPP grades (pricing discipline)

---

## Railroad Rate Context

### PRB Coal Economics
- Typical rail rate: $10-16/ST for 1,000+ mile hauls (BNSF/UP)
- Mine cost: $8-12/ST (surface mine, low labor cost)
- Power plant delivered cost: $25-35/ST (including mining, rail, handling)
- PRB spot price: ~$12-15/ST (8,800 BTU basis)

### Appalachian Coal Economics
- Mine cost: $55-85/ST (underground, high labor + regulatory)
- Rail rate: $15-25/ST (CSX/NS, shorter haul to Hampton Roads)
- Export FOB Hampton Roads: $90-180/ST (depending on grade and global market)
- Met coal price premium vs. thermal: often 2-4x at Hampton Roads FOB

---

## Site Registry Integration Notes

MSHA Mines.csv integration into `site_master_registry`:
- Filter: `COAL_METAL_IND = 'C'`
- NAICS: Surface=212111, Underground=212112, Anthracite=212113
- `commodity_sector`: `coal_mining`
- Join production data: `MINE_ID` in Mines.csv = `MINE_ID` in MinesProdQuarterly.csv
- Cross-reference with EIA-923 Schedule 2: EIA uses same MSHA Mine ID

EIA-923 → MSHA join:
- EIA-923 Schedule 2 field `COALMINE_ID` (or `MINE_ID`) = MSHA `MINE_ID`
- This links power plant coal receipts back to source mine with coordinates

---

## Price Data Update Cadence

| Data | Source | Update | Format |
|---|---|---|---|
| US spot prices (5 regions) | EIA Coal Markets | Weekly (Wednesday) | Excel/API |
| API2/API4/NEWC | CME/ICE settlements | Daily | Web/CSV |
| World Bank benchmarks | Pink Sheet | Monthly | Excel |
| Indonesian HBA | MEMR | Monthly | PDF/Web |
| EIA production | EIA Quarterly Report | Quarterly | Excel/API |
| Export volumes | EIA Annual Coal Report | Annual | Excel |
| Mine-level production | MSHA quarterly | Quarterly | CSV |

---

## Associations and Industry Calendar

- **NMA Coal Producer Survey** — published Q2 (prior year data)
- **World Coal Association Coal Facts** — published Q3 annually
- **Coal Age Top Producers** — published Q1 annually
- **IEA Coal Market Update** — quarterly (spring, summer, fall, winter)
- **Australia REQ** — quarterly (March, June, September, December)
- **ARLP quarterly earnings** — best mine-level benchmarks for Illinois Basin
