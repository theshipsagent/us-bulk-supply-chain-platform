# Aluminum Commodity Module

**US Aluminum Production, Trade Flows, and Supply Chain Intelligence**

---

## Overview

The **Aluminum Module** provides comprehensive analysis of the US aluminum industry, covering primary smelting, integrated rolling, secondary refining, and end-user consumption patterns. Integrates production facility data (industry sources), import manifests (Panjiva), rail-served facilities (SCRS), and environmental compliance (EPA FRS).

### Scope

- **68 aluminum production facilities** (US + 1 Canada)
  - 7 primary smelters (848 kt/year operating capacity, 515 kt idled, 500 kt planned)
  - 11 integrated mills (5,080 kt/year capacity including 1,250 kt under construction)
  - 16 rolling mills (1,480 kt/year capacity)
  - 27 secondary smelters (1,005 kt/year capacity)
  - 8 billet casters (888 kt/year capacity, dominated by Matalco at 848 kt)
- **Trade flow analysis** (imports, Section 232 tariffs, country-specific impacts)
- **Rail and barge logistics** (Ohio River corridor, Great Lakes, Mississippi River)

---

## Key Features

### 🏭 **Production Landscape**

**Top 5 Producers by Rolling Capacity:**

| Company | Capacity (kt/yr) | Major Facilities | Ownership Notes |
|---------|------------------|------------------|-----------------|
| **Arconic Corporation** | 1,550 | Tennessee (Alcoa), Davenport IA, Lancaster PA | Spun off from Alcoa 2016; aerospace/auto focus |
| **Novelis (Hindalco)** | 1,170 | Oswego NY, Bay Minette AL, Logan KY, Berea KY, Guthrie KY | Indian-owned (Hindalco); world's largest recycler |
| **Matalco (Giampaolo/Rio Tinto JV)** | 848 | 7 billet casting facilities (OH, IN, KY, WI) | Dominant extrusion billet supplier |
| **Constellium SE** | 700 | Muscle Shoals AL, Ravenswood WV, Bowling Green KY | French-owned; aerospace/defense plate |
| **Aluminum Dynamics (SDI)** | 650 | Columbus MS | Steel Dynamics' first aluminum mill; operational mid-2025 |

**Total US Aluminum Production:**
- **Primary smelting capacity:** 1,863 kt/year (848 kt operating, 515 kt idled, 500 kt planned)
- **Integrated mill capacity:** 5,080 kt/year (includes 1,250 kt under construction)
- **Rolling mill capacity:** 1,480 kt/year
- **Secondary smelter capacity:** 1,005 kt/year
- **Billet caster capacity:** 888 kt/year

### 📊 **Industry Structure**

**Primary vs. Secondary Aluminum:**
- **Primary Smelters**: Electrolytic reduction of alumina → primary ingot (P1020)
  - Century Sebree KY, Mt. Holly SC; Alcoa Warrick IN, Massena NY
  - High energy intensity (~15 MWh/ton); dependent on low-cost power
  - 2 operating at full capacity, 1 at reduced capacity, 2 idled, 1 planned
- **Secondary Smelters**: Scrap remelt + prime metal → specification alloy ingot
  - Real Alloy (12 facilities), Scepter (4 facilities), Spectro Rosemount MN
  - Automotive die casting alloys (A356, A380), industrial alloys
  - ~95% less energy-intensive than primary production

**Integrated vs. Standalone Mills:**
- **Integrated Mills**: Casthouse + hot rolling + cold rolling + finishing
  - Novelis Oswego/Bay Minette, Arconic Tennessee/Davenport, Constellium Muscle Shoals/Ravenswood
  - Full control of metallurgy from melt to finished product
- **Standalone Rolling Mills**: Purchase ingot/slab, focus on rolling/finishing
  - JW Aluminum (3 facilities), Granges (3 facilities), Kaiser Trentwood

**Geographic Concentration:**
- **Kentucky** — 14 facilities (Ohio River corridor dominance)
  - Louisville, Lewisport, Henderson, Bowling Green, Shelbyville, Franklin, Berea, Guthrie, Sebree, Hawesville
- **Ohio River Valley** (KY/IN/OH/WV): 30 facilities
  - Barge access for ingot/scrap imports, finished product distribution
- **Southeast** (AL/TN/MS): 11 facilities
  - Novelis Bay Minette, Aluminum Dynamics Columbus, Constellium Muscle Shoals
- **Northeast** (NY/PA): 7 facilities
  - Novelis Oswego, Arconic Lancaster, Alcoa Massena

### 🚢 **Trade Flows & Section 232**

**US Aluminum Consumption:** ~5.5 million metric tons/year (2024)

**Domestic Primary Production:** ~848 kt/year operating + ~515 kt idled capacity

**Import Gap:** ~4.7 million metric tons/year (85% import dependency)

**Top Import Origins (HS 7601 unwrought aluminum):**
1. **Canada** — 65% of imports (USMCA exempt from Section 232)
2. **UAE** — 8% of imports (10% tariff)
3. **Russia** — 5% of imports (200% tariff as of 2024)
4. **Bahrain** — 4% of imports (10% tariff)
5. **Argentina, India, Oman** — 15% combined (10% tariff)
6. **China** — <1% (antidumping duties + 10% Section 232)

**Section 232 Impact (March 2018):**
- 10% tariff on aluminum imports (with country-specific exemptions and quotas)
- Canada and Mexico exempt (USMCA)
- Russia tariffs increased to 200% (2024) following invasion of Ukraine
- Reduced Russian import share from 10% (2017) to <1% (2024)

### 🏗️ **End User Segments**

**Major Aluminum-Consuming Sectors:**

| Sector | Consumption (kt/yr) | Key Products | Major End Users |
|--------|---------------------|--------------|-----------------|
| **Packaging** | 1,980 (36%) | Beverage cans, foil, food containers | Ball, Crown, Ardagh, Silgan |
| **Automotive** | 1,265 (23%) | Body panels, structural, engine blocks | GM, Ford, Stellantis, Tesla, Toyota |
| **Building/Construction** | 770 (14%) | Windows, doors, siding, roofing | Alcoa Building Products, extruders |
| **Electrical** | 495 (9%) | Transmission wire, bus bars | Southwire, General Cable |
| **Aerospace/Defense** | 440 (8%) | Airframe, structural, plate | Boeing, Lockheed, Northrop Grumman |
| **Consumer/Industrial** | 550 (10%) | Machinery, appliances, equipment | Various |

---

## Data Sources

### Primary Production Data

**Industry Compilation** (`market_intelligence/supply_landscape/`)
- 68 facilities mapped with precise capacity, equipment, capabilities
- Primary smelters, integrated mills, rolling mills, secondary smelters, billet casters
- Logistics attributes: port-adjacent, barge access, water access, rail-served

**Facility Breakdown:**
```
68 total facilities:
├── 67 United States
└── 1 Canada (Matalco Brampton)

Capacity by process:
├── Primary smelters: 1,863 kt/yr (7 facilities: 848 kt operating, 515 kt idled, 500 kt planned)
├── Integrated mills: 5,080 kt/yr (11 facilities: 3,830 kt operating, 1,250 kt construction)
├── Rolling mills: 1,480 kt/yr (16 facilities)
├── Secondary smelters: 1,005 kt/yr (27 facilities)
└── Billet casters: 888 kt/yr (8 facilities)

Logistics:
├── Port-adjacent: 3 facilities (Novelis Oswego, Century Mt. Holly, Novelis Bay Minette construction)
├── Water access: 11 facilities (Ohio River, Mississippi River, Great Lakes, St. Lawrence)
└── Barge access: 9 facilities (critical for ingot/scrap imports, finished coil distribution)
```

### Data Source Documentation

**USGS Mineral Commodity Summaries 2024-2025** — Aluminum chapter
- National production, consumption, trade statistics
- Primary smelter operating status
- Import/export origins and volumes

**CRS Report R47294** — U.S. Aluminum Manufacturing: Industry Trends and Sustainability
- Industry structure analysis
- Policy impacts (Section 232, IRA, CHIPS Act)
- Decarbonization pathways

**The Aluminum Association** — "Powering Up American Aluminum" white paper (May 2025)
- Industry advocacy for primary smelter restarts
- Clean energy smelting projects (Century Green Aluminum)
- Recycling infrastructure expansion

**Company Sources:**
- Novelis, Arconic, Constellium, Kaiser, Century, Alcoa, Matalco, Real Alloy, SDI SEC filings
- Press releases, investor presentations, facility announcements
- Light Metal Age Magazine facility reports (2016-2025)

**Trade Publications:**
- Fastmarkets aluminum pricing and market intelligence
- S&P Global Platts metals reporting
- Recycling Today Secondary Aluminum Producers directory (2015)

### Supplementary Data Sources

**EPA FRS** — Aluminum facility environmental compliance
- NAICS 331315 (Aluminum Sheet, Plate, and Foil Manufacturing)
- NAICS 331318 (Other Aluminum Rolling, Drawing, and Extruding)
- NAICS 331314 (Secondary Smelting and Alloying of Aluminum)

**SCRS Rail Data** — Rail-served aluminum facilities (from `01_DATA_SOURCES/federal_rail/scrs_facility_data/`)

**Panjiva Import Manifests** — HS 7601 (unwrought aluminum) imports (from `01_DATA_SOURCES/federal_trade/panjiva_imports/`)

---

## Module Structure

```
aluminum/
├── README.md                          ← This file
├── config.yaml                        ← Aluminum-specific configuration
├── naics_hts_codes.json              ← Aluminum NAICS/HTS classification
├── data_sources.json                  ← Data source catalog
│
├── market_intelligence/               ← Aluminum market data and analysis
│   ├── supply_landscape/              ← Production facilities
│   │   ├── us_aluminum_facilities.csv      ← 68 facilities (all types)
│   │   ├── us_aluminum_facilities.geojson  ← GeoJSON for mapping
│   │   ├── us_aluminum_facilities.py       ← Python dataclass module
│   │   ├── us_aluminum_facilities_README.md ← Facility data documentation
│   │   ├── primary_smelters.json           ← Primary electrolytic smelters
│   │   ├── integrated_mills.json           ← Casthouse + hot/cold rolling
│   │   ├── rolling_mills.json              ← Standalone rolling mills
│   │   ├── secondary_smelters.json         ← Scrap remelters
│   │   └── billet_casters.json             ← Extrusion billet producers
│   │
│   ├── demand_analysis/               ← End-user consumption
│   │   ├── end_user_segments.json     ← Packaging, automotive, aerospace, etc.
│   │   ├── can_sheet_producers.json   ← Beverage can stock supply chain
│   │   └── regional_consumption.json  ← State/metro area consumption
│   │
│   ├── trade_flows/                   ← Import/export analysis
│   │   ├── import_origins.json        ← Canada, UAE, Russia, Bahrain, etc.
│   │   ├── section_232_impacts.json   ← 10% tariff effects by country
│   │   ├── russian_tariff_impacts.json ← 200% tariff on Russian aluminum (2024)
│   │   └── landed_cost_models/        ← CIF + tariff + handling
│   │
│   └── epa_analysis/                  ← Environmental compliance
│       └── aluminum_facilities_frs.csv ← EPA FRS aluminum facilities (NAICS 3313xx)
│
├── supply_chain_models/               ← Aluminum-specific transport analysis
│   ├── rail_routes/
│   │   ├── aluminum_rail_origins.json    ← Mill/smelter rail loadout capabilities
│   │   ├── rail_cost_scenarios.json      ← Pre-computed rail freight costs
│   │   └── scrs_aluminum_facilities.csv  ← Rail-served aluminum facilities (from SCRS)
│   │
│   ├── barge_routes/
│   │   └── aluminum_coil_barge_moves.json ← Barge movements (Ohio River, Miss River)
│   │
│   └── port_operations/
│       └── aluminum_import_terminals.json ← Port discharge rates, storage, handling
│
└── reports/                           ← Generated aluminum reports
    ├── templates/
    ├── drafts/
    └── published/
```

---

## NAICS/HTS Codes

### NAICS Codes (Aluminum Production & Processing)

```json
{
  "primary_production": {
    "331313": "Alumina Refining and Primary Aluminum Production"
  },
  "secondary_production": {
    "331314": "Secondary Smelting and Alloying of Aluminum"
  },
  "rolling_drawing": {
    "331315": "Aluminum Sheet, Plate, and Foil Manufacturing",
    "331318": "Other Aluminum Rolling, Drawing, and Extruding"
  },
  "foundries": {
    "331524": "Aluminum Foundries (except Die-Casting)",
    "331523": "Nonferrous Metal Die-Casting Foundries"
  },
  "end_users_automotive": {
    "336111": "Automobile Manufacturing",
    "336112": "Light Truck and Utility Vehicle Manufacturing",
    "336370": "Motor Vehicle Metal Stamping"
  },
  "end_users_packaging": {
    "332439": "Other Metal Container Manufacturing"
  },
  "end_users_aerospace": {
    "336411": "Aircraft Manufacturing",
    "336412": "Aircraft Engine and Engine Parts Manufacturing"
  }
}
```

### HTS Codes (Aluminum Imports)

```json
{
  "unwrought_aluminum": {
    "7601.10": "Aluminum, not alloyed, unwrought",
    "7601.20": "Aluminum alloys, unwrought"
  },
  "aluminum_waste_scrap": {
    "7602.00": "Aluminum waste and scrap"
  },
  "aluminum_powders_flakes": {
    "7603.10": "Aluminum powders of non-lamellar structure",
    "7603.20": "Aluminum powders of lamellar structure; flakes"
  },
  "aluminum_bars_rods_profiles": {
    "7604.10": "Aluminum, not alloyed, bars, rods and profiles",
    "7604.21": "Aluminum alloy, hollow profiles",
    "7604.29": "Aluminum alloy, other bars, rods and profiles"
  },
  "aluminum_wire": {
    "7605.11": "Aluminum, not alloyed, wire, maximum cross-sectional dimension >7mm",
    "7605.19": "Aluminum, not alloyed, wire, other",
    "7605.21": "Aluminum alloy, wire, maximum cross-sectional dimension >7mm",
    "7605.29": "Aluminum alloy, wire, other"
  },
  "aluminum_plate_sheet_strip": {
    "7606.11": "Aluminum, not alloyed, rectangular plates, sheets and strip, thickness >0.2mm",
    "7606.12": "Aluminum alloy, rectangular plates, sheets and strip, thickness >0.2mm",
    "7606.91": "Aluminum, not alloyed, other plates, sheets and strip, thickness >0.2mm",
    "7606.92": "Aluminum alloy, other plates, sheets and strip, thickness >0.2mm"
  },
  "aluminum_foil": {
    "7607.11": "Aluminum, not alloyed, foil, thickness ≤0.2mm, not backed",
    "7607.19": "Aluminum alloy, foil, thickness ≤0.2mm, not backed",
    "7607.20": "Aluminum foil, thickness ≤0.2mm, backed"
  }
}
```

---

## Integration with Core Toolsets

### 🚂 Rail Intelligence & Cost Modeling

**SCRS Integration:**
- Cross-reference aluminum facilities with SCRS rail-served facility database
- Identify rail origins for aluminum coil/ingot/billet movements
- Calculate rail freight costs using STB URCS methodology

**Example Query:**
```python
# Find rail-served aluminum mills in Ohio River region
from report_platform.toolsets.rail_intelligence import find_rail_facilities

aluminum_mills_rail = find_rail_facilities(
    naics_prefix='331315',
    state=['KY', 'IN', 'OH', 'WV'],
    commodity='aluminum_coil'
)
```

### 🚛 Barge Cost Model

**Waterway-Accessible Aluminum Facilities:**
- 9 facilities with barge access (Ohio River, Mississippi River, Great Lakes, St. Lawrence)
  - Arconic Davenport IA (Mississippi River)
  - Constellium Ravenswood WV (Ohio River)
  - Tri-Arrows Louisville KY, Novelis Lewisport KY, Commonwealth Lewisport KY (Ohio River)
  - Kaiser Warrick IN, Alcoa Warrick IN (Ohio River)
  - Audubon Metals Henderson KY (Ohio River)
  - Aluminum Dynamics Columbus MS (Tenn-Tom Waterway)
- Barge movements: ingot/scrap imports from Gulf ports, finished coil distribution

### 🏭 Facility Registry (EPA FRS)

**Aluminum Facility Analysis:**
- Query EPA FRS for NAICS 331313 (primary aluminum), 331314 (secondary), 331315 (sheet/plate)
- Cross-reference with facility database for validation
- Environmental compliance tracking (air quality permits, wastewater discharge)

**Example Query:**
```python
from report_platform.toolsets.facility_registry import search_facilities

aluminum_facilities = search_facilities(
    naics_prefix='3313',
    state='KY',
    facility_type='production'
)
```

### 🚢 Vessel Intelligence

**Aluminum Import Manifest Processing:**
- HS 7601 (unwrought aluminum — ingot, T-bar, sow, billet, slab)
- Port-level import volumes by origin country (Canada, UAE, Russia, Bahrain)
- Consignee analysis (rolling mills, billet casters, secondary smelters)
- Section 232 tariff impact tracking (10% base, 200% Russian)

---

## Use Cases

### 1. **Aluminum Production Capacity Analysis**

Map all aluminum facilities by type, capacity, ownership, and logistics:
- Primary smelters: Operating vs. idled vs. planned capacity
- Integrated mills: Can stock vs. auto sheet vs. aerospace plate
- Secondary smelters: Automotive die casting alloy supply
- Billet casters: Extrusion billet supply to building products industry

### 2. **Section 232 & Russian Tariff Impact Assessment**

Analyze import volume shifts pre/post Section 232 and Russian 200% tariff:
- Country-level import trends (Canada dominance, Russian collapse)
- Port-level discharge patterns (New Orleans, Houston, Savannah, Mobile)
- Domestic primary smelter restart economics (Century Hawesville, Magnitude 7 New Madrid)

### 3. **Automotive Aluminum Supply Chain**

Map aluminum flow from smelters/mills → automotive OEMs:
- Ingot → casthouse → hot rolling → cold rolling → automotive body sheet
- Novelis Oswego/Bay Minette, Arconic Tennessee, Constellium Muscle Shoals
- Just-in-time delivery to Michigan/Ohio automotive corridor

### 4. **Beverage Can Stock Supply Chain**

Identify can stock producers and UBC recycling infrastructure:
- Major producers: Novelis (Oswego, Bay Minette, Logan), Kaiser Warrick, Tri-Arrows Louisville
- UBC recycling capacity: 340 kt at Constellium Muscle Shoals, major operations at Novelis/Tri-Arrows
- Supply to Ball, Crown, Ardagh can manufacturing plants

### 5. **Decarbonization Pathway Analysis**

Track primary smelter electrification and secondary aluminum growth:
- Century Green Aluminum (Inola OK) — 100% renewable/nuclear power, 500 kt planned 2031
- Secondary smelter expansion (Real Alloy DOE $67M grant for low-waste recycling)
- UBC-to-can closed-loop recycling (95% energy savings vs. primary)

---

## Recent Industry Developments

### Major M&A Activity (2020-2024)

**Novelis Acquisitions:**
- **Aleris Corporation** (Apr 2020) — $2.6B
  - Added Lewisport KY, Uhrichsville OH, Guthrie KY, Richmond VA, Berea KY facilities
  - Made Novelis the world's largest aluminum recycler
  - DOJ required divestiture of Lewisport (sold to American Industrial Partners)

**UAE Investment in US Aluminum:**
- **Spectro Alloys Rosemount MN** — Acquired by EGA (Emirates Global Aluminium) affiliate Sep 2024
  - 110 kt/year secondary smelter capacity

### Greenfield Capacity Additions

**Novelis Bay Minette, Alabama** (Construction)
- 600-1,000 kt/year integrated mill (Danieli 1+4 hot strip mill)
- $2.5B investment
- Startup: H2 2026
- Focus: Can stock and automotive body sheet
- 51km from Port of Mobile for imports

**Aluminum Dynamics Columbus, Mississippi** (Operational mid-2025)
- 650 kt/year integrated mill (SMS 1+4 hot strip mill)
- $1.9B investment (Steel Dynamics' first aluminum mill)
- Adjacent to SDI Columbus steel mill for logistics synergy
- Tenn-Tom Waterway barge access

**Century Green Aluminum Smelter, Inola, Oklahoma** (Planned 2031)
- 500 kt/year primary smelting capacity
- $5B investment
- DOE $500M grant (Office of Clean Energy Demonstrations)
- 100% renewable/nuclear power target
- First new US primary smelter in ~45 years

### Primary Smelter Curtailments

**Magnitude 7 New Madrid, Missouri** — Full shutdown Jan 2024
- 263 kt/year capacity (previously ~250 kt actual production)
- Mississippi River barge access
- Originally Noranda, acquired by ARG International 2016
- No scheduled restart

**Century Hawesville, Kentucky** — Idled since 2022
- 252 kt/year capacity
- 5 potlines, 560 cells
- Restart contingent on competitive long-term power contract

---

## Next Steps

### Planned Enhancements

1. **EPA FRS Aluminum Facility Analysis**
   - Query all NAICS 3313xx facilities
   - Cross-reference with facility database for validation
   - Add environmental compliance tracking (air permits, hazardous waste)

2. **SCRS Rail Integration**
   - Match aluminum facilities to SCRS rail-served facility database
   - Identify rail origins for coil/ingot/billet movements
   - Rail vs. barge vs. truck transport cost modeling

3. **Panjiva Import Analysis**
   - HS 7601 (unwrought aluminum) import volumes by port
   - Consignee matching to rolling mills, billet casters, secondary smelters
   - Section 232 and Russian 200% tariff impact quantification

4. **Can Stock Supply Chain Deep Dive**
   - Map UBC (used beverage can) collection and recycling infrastructure
   - Novelis/Tri-Arrows/Kaiser/Constellium production capacity and customer base
   - Ball/Crown/Ardagh can manufacturing plant proximity analysis

5. **Regional Demand Modeling**
   - State-level aluminum consumption estimates by end-use sector
   - Automotive corridor (MI/OH/KY/TN/AL) sheet/extrusion demand
   - Building products demand by construction activity

---

## Data Refresh Schedule

| Data Source | Current Vintage | Refresh Cadence | Next Update |
|-------------|-----------------|-----------------|-------------|
| Facility Database | 2026-02 | Semi-annual | 2026-08 |
| EPA FRS | 2024-Q4 | Quarterly | 2025-Q1 available |
| SCRS Rail Facilities | 2024 | Annual | Static reference |
| Panjiva Imports (HS 7601) | 2023-2025 | Real-time | Continuous (subscription) |
| USGS Minerals | 2024 | Annual | 2025 prelim available Q2 |
| Aluminum Association | 2025 | Annual | 2026 expected Q3 |

---

**Module Status:** ✅ Production Landscape Complete | 📅 Trade Flows Planned | 📅 End User Analysis Planned

**Last Updated:** 2026-02-24

**Maintained by:** William S. Davis III
