# Steel & Metals Commodity Module

**US Steel Production, Trade Flows, and Supply Chain Intelligence**

---

## Overview

The **Steel & Metals Module** provides comprehensive analysis of the US steel industry, covering flat-rolled production, trade flows, and end-user consumption patterns. Integrates production facility data (AIST), import manifests (Panjiva), rail-served facilities (SCRS), and environmental compliance (EPA FRS).

### Scope

- **68 steel production facilities** (AIST 2021 Directory)
  - 31 hot strip mills (87,180 kt/year capacity)
  - 65 galvanizing lines at 44 sites (26,052 kt/year)
  - 25 electric arc furnaces (37,846 kt/year)
  - 12 plate mills (17,750 kt/year)
- **53 major steel end users** (service centers, fabricators, automotive, construction)
- **Trade flow analysis** (imports, Section 232 tariffs, country-specific impacts)
- **Rail-served steel facilities** (SCRS integration)

---

## Key Features

### 🏭 **Production Landscape**

**Top 5 Producers by Hot Strip Mill Capacity:**

| Company | HSM Capacity (kt/yr) | Major Facilities | Ownership Notes |
|---------|----------------------|------------------|-----------------|
| **United States Steel** | 21,600 | Gary IN, Granite City IL, Big River AR (x2) | Acquired Big River Steel 2020 |
| **Cleveland-Cliffs** | 19,400 | Burns Harbor IN, Indiana Harbor IN, Middletown OH | Acquired ArcelorMittal USA 2020 |
| **Nucor Corporation** | 13,300 | Arkansas, Berkeley SC, Decatur AL, Gallatin KY | Largest mini-mill operator |
| **Steel Dynamics Inc.** | 8,800 | Butler IN, Columbus MS, Sinton TX | EAF-based flat-rolled |
| **AM/NS Calvert** | 5,400 | Calvert AL | ArcelorMittal/Nippon Steel JV |

**Total US Flat-Rolled Capacity:** ~87 million tons/year (HSM basis)

### 📊 **Industry Structure**

**Integrated vs. Mini-Mill:**
- **Integrated Mills**: Blast furnace → BOF → continuous caster → hot strip mill
  - US Steel Gary, Cleveland-Cliffs Burns Harbor, AM/NS Calvert
- **Mini-Mills**: EAF → continuous caster → hot strip mill
  - Nucor, Steel Dynamics, Big River Steel (now USS)

**Geographic Concentration:**
- **Great Lakes Region** (IN, OH, IL, MI): 40% of capacity
- **Southern Tier** (AL, AR, MS, TX, SC): 35% of capacity
- **Mid-Atlantic** (PA, WV): 10% of capacity
- **West Coast** (CA): 5% of capacity

### 🚢 **Trade Flows & Section 232**

**US Steel Consumption:** ~96 million tons/year (2024)

**Domestic Production:** ~87 million tons/year

**Import Gap:** ~20-25 million tons/year

**Top Import Origins (pre-Section 232):**
1. **Canada** — 30% of imports (exempt from Section 232)
2. **Mexico** — 20% of imports (exempt from Section 232)
3. **Brazil** — 10% of imports (25% tariff)
4. **South Korea** — 10% of imports (25% tariff)
5. **Germany, Japan, Taiwan** — 15% combined (25% tariff)
6. **China** — <5% (antidumping/countervailing duties + 25% tariff)

**Section 232 Impact (March 2018):**
- 25% tariff on steel imports (with country-specific exemptions)
- Canada & Mexico exempt (USMCA)
- Reduced import penetration from 26% (2017) to 19% (2024)

### 🏗️ **End User Segments**

**Major Steel-Consuming Sectors:**

| Sector | Consumption (kt/yr) | Key Products | Major End Users |
|--------|---------------------|--------------|-----------------|
| **Automotive** | 15,000 | Body panels, structural, chassis | GM, Ford, Stellantis, Tesla, Toyota, Honda |
| **Construction** | 35,000 | Structural, rebar, plate, sheet pile | Commercial buildings, infrastructure |
| **Energy/Pipeline** | 8,000 | Line pipe, OCTG, structural | Oil & gas, wind turbines, transmission towers |
| **Appliances** | 3,500 | Sheet, coated products | Whirlpool, GE, Electrolux |
| **Containers** | 2,500 | Tinplate, TFS | Food & beverage packaging |
| **Service Centers** | 25,000 | Distribution, processing | Ryerson, Reliance, Olympic Steel |

---

## Data Sources

### Primary Production Data

**AIST 2021 Directory** (`market_intelligence/supply_landscape/`)
- 68 facilities mapped with precise capacity, equipment, capabilities
- Hot strip mills, plate mills, galvanizing lines, electric arc furnaces
- Logistics attributes: port-adjacent, barge access, rail-served

**Facility Breakdown:**
```
68 total facilities:
├── 65 United States
└── 3 Canada

Capacity by process:
├── Hot strip mills: 87,180 kt/year (31 mills)
├── Galvanizing lines: 26,052 kt/year (65 lines at 44 sites)
├── Electric arc furnaces: 37,846 kt/year (25 facilities)
└── Plate mills: 17,750 kt/year (12 mills)

Logistics:
├── Port-adjacent: 14 facilities
├── Water access: 30 facilities
└── Barge access: 9 facilities
```

### Supplementary Data Sources

**EPA FRS** — Steel facility environmental compliance
- NAICS 331110 (Iron & Steel Mills)
- NAICS 331210 (Iron & Steel Pipe & Tube Manufacturing)

**SCRS Rail Data** — Rail-served steel facilities (from `01_DATA_SOURCES/federal_rail/scrs_facility_data/`)

**Panjiva Import Manifests** — HS 7208-7212 steel imports (from `01_DATA_SOURCES/federal_trade/panjiva_imports/`)

**USGS Mineral Commodity Summaries** — Production, consumption, trade statistics

---

## Module Structure

```
steel_metals/
├── README.md                          ← This file
├── config.yaml                        ← Steel-specific configuration
├── naics_hts_codes.json              ← Steel NAICS/HTS classification
├── data_sources.json                  ← Data source catalog
│
├── market_intelligence/               ← Steel market data and analysis
│   ├── supply_landscape/              ← Production facilities
│   │   ├── aist_steel_plants.csv      ← 68 facilities (AIST 2021)
│   │   ├── aist_steel_plants.geojson  ← GeoJSON for mapping
│   │   ├── aist_steel_plants_geospatial.py ← Python dataclass module
│   │   ├── aist_steel_plants_README.md ← AIST data documentation
│   │   ├── integrated_mills.json      ← Blast furnace/BOF mills
│   │   ├── mini_mills.json            ← EAF-based mills
│   │   └── capacity_ownership.json    ← Ownership consolidation
│   │
│   ├── demand_analysis/               ← End-user consumption
│   │   ├── end_user_segments.json     ← Automotive, construction, energy, etc.
│   │   ├── service_centers.json       ← Steel service center locations
│   │   └── regional_consumption.json  ← State/metro area consumption
│   │
│   ├── trade_flows/                   ← Import/export analysis
│   │   ├── import_origins.json        ← Canada, Mexico, Brazil, S. Korea, etc.
│   │   ├── section_232_impacts.json   ← 25% tariff effects by country
│   │   ├── antidumping_orders.json    ← Country-product specific AD/CVD
│   │   └── landed_cost_models/        ← CIF + tariff + handling
│   │
│   └── epa_analysis/                  ← Environmental compliance
│       └── steel_facilities_frs.csv   ← EPA FRS steel facilities (NAICS 331110)
│
├── supply_chain_models/               ← Steel-specific transport analysis
│   ├── rail_routes/
│   │   ├── steel_rail_origins.json    ← Mill rail loadout capabilities
│   │   ├── rail_cost_scenarios.json   ← Pre-computed rail freight costs
│   │   └── scrs_steel_facilities.csv  ← Rail-served steel facilities (from SCRS)
│   │
│   ├── barge_routes/
│   │   └── steel_coil_barge_moves.json ← Barge movements (Great Lakes, Mississippi, ICW)
│   │
│   └── port_operations/
│       └── steel_import_terminals.json ← Port discharge rates, storage, handling
│
└── reports/                           ← Generated steel reports
    ├── templates/
    ├── drafts/
    └── published/
```

---

## NAICS/HTS Codes

### NAICS Codes (Steel Production & Processing)

```json
{
  "steel_production": {
    "331110": "Iron and Steel Mills and Ferroalloy Manufacturing",
    "331210": "Iron and Steel Pipe and Tube Manufacturing from Purchased Steel",
    "331221": "Rolled Steel Shape Manufacturing",
    "331222": "Steel Wire Drawing"
  },
  "steel_finishing": {
    "332111": "Iron and Steel Forging",
    "332112": "Nonferrous Forging",
    "332114": "Custom Roll Forming",
    "332119": "Metal Crown, Closure, and Other Metal Stamping (except Automotive)",
    "332710": "Machine Shops",
    "332812": "Metal Coating, Engraving (except Jewelry and Silverware), and Allied Services to Manufacturers"
  },
  "steel_service_centers": {
    "423510": "Metal Service Centers and Other Metal Merchant Wholesalers"
  },
  "steel_end_users_automotive": {
    "336111": "Automobile Manufacturing",
    "336112": "Light Truck and Utility Vehicle Manufacturing",
    "336211": "Motor Vehicle Body Manufacturing",
    "336370": "Motor Vehicle Metal Stamping"
  },
  "steel_end_users_construction": {
    "332312": "Fabricated Structural Metal Manufacturing",
    "332313": "Plate Work Manufacturing",
    "332323": "Ornamental and Architectural Metal Work Manufacturing"
  },
  "steel_end_users_energy": {
    "332996": "Fabricated Pipe and Pipe Fitting Manufacturing",
    "333132": "Oil and Gas Field Machinery and Equipment Manufacturing"
  }
}
```

### HTS Codes (Steel Imports - Flat-Rolled)

```json
{
  "flat_rolled_carbon_hot": {
    "7208.10": "Hot-rolled, in coils, pickled",
    "7208.25": "Hot-rolled, in coils, pickled, thickness ≥4.75mm",
    "7208.26": "Hot-rolled, in coils, pickled, 3mm ≤ thickness <4.75mm",
    "7208.27": "Hot-rolled, in coils, pickled, thickness <3mm",
    "7208.36": "Hot-rolled, in coils, thickness >10mm",
    "7208.37": "Hot-rolled, in coils, 4.75mm ≤ thickness ≤10mm",
    "7208.38": "Hot-rolled, in coils, 3mm ≤ thickness <4.75mm",
    "7208.39": "Hot-rolled, in coils, thickness <3mm",
    "7208.40": "Hot-rolled, not in coils, width ≥600mm"
  },
  "flat_rolled_carbon_cold": {
    "7209.15": "Cold-rolled, in coils, thickness ≥3mm",
    "7209.16": "Cold-rolled, in coils, 1mm ≤ thickness <3mm",
    "7209.17": "Cold-rolled, in coils, 0.5mm ≤ thickness <1mm",
    "7209.18": "Cold-rolled, in coils, thickness <0.5mm"
  },
  "coated_galvanized": {
    "7210.30": "Electrolytically plated or coated with zinc",
    "7210.41": "Corrugated",
    "7210.49": "Other (galvanized, galvannealed)",
    "7210.61": "Plated or coated with aluminum-zinc alloys",
    "7210.70": "Painted, varnished or coated with plastics"
  },
  "plate": {
    "7208.51": "Flat-rolled, not in coils, thickness >10mm",
    "7208.52": "Flat-rolled, not in coils, 4.75mm ≤ thickness ≤10mm"
  }
}
```

---

## Integration with Core Toolsets

### 🚂 Rail Intelligence & Cost Modeling

**SCRS Integration:**
- Cross-reference AIST steel plants with SCRS rail-served facilities
- Identify rail origins for steel coil/plate movements
- Calculate rail freight costs using STB URCS methodology

**Example Query:**
```python
# Find rail-served steel mills in Great Lakes region
from report_platform.toolsets.rail_intelligence import find_rail_facilities

steel_mills_rail = find_rail_facilities(
    naics_prefix='331110',
    state=['IN', 'OH', 'IL', 'MI'],
    commodity='steel_coil'
)
```

### 🚛 Barge Cost Model

**Waterway-Accessible Steel Mills:**
- 9 facilities with barge access (Mississippi River, Great Lakes, ICW)
- Barge movements: coils from mills to service centers, imports to end users

### 🏭 Facility Registry (EPA FRS)

**Steel Facility Analysis:**
- Query EPA FRS for NAICS 331110 (steel mills)
- Cross-reference with AIST data for facility validation
- Environmental compliance tracking

**Example Query:**
```python
from report_platform.toolsets.facility_registry import search_facilities

steel_facilities = search_facilities(
    naics_prefix='331110',
    state='IN',
    facility_type='production'
)
```

### 🚢 Vessel Intelligence

**Steel Import Manifest Processing:**
- HS 7208-7212 (flat-rolled steel products)
- Port-level import volumes by origin country
- Consignee analysis (service centers, OEMs, toll processors)

---

## Use Cases

### 1. **Steel Mill Competitive Analysis**

Map all steel mills by capacity, ownership, product mix, and logistics access:
- Identify integrated vs. mini-mill competition
- Analyze regional capacity clusters (Great Lakes, Southern Tier)
- Assess rail/barge/port logistics advantages

### 2. **Section 232 Tariff Impact Assessment**

Analyze import volume shifts pre/post Section 232:
- Country-level import trends (Canada, Mexico, Brazil, S. Korea)
- Port-level discharge patterns
- Domestic mill utilization response

### 3. **Automotive Steel Supply Chain**

Map steel flow from mills → service centers → automotive OEMs:
- Hot-rolled coil → cold-rolled → galvanized → automotive stamping
- Just-in-time delivery radius analysis
- Rail vs. truck transport economics

### 4. **Service Center Location Optimization**

Identify optimal service center locations based on:
- Proximity to steel mills (rail freight cost)
- Proximity to end users (truck delivery radius)
- Regional demand density

### 5. **Decarbonization Pathway Analysis**

Track EAF capacity growth vs. blast furnace shutdowns:
- Scrap-based EAF expansion (Nucor, SDI, Big River)
- DRI-based EAF projects (Cleveland-Cliffs HBI)
- Carbon intensity by production route

---

## Recent Industry Developments

### Major M&A Activity (2020-2024)

**Cleveland-Cliffs Acquisitions:**
- **ArcelorMittal USA** (Dec 2020) — $1.4B
  - Added Burns Harbor, Indiana Harbor, Cleveland, Riverdale facilities
  - Made Cliffs the largest flat-rolled producer in North America
- **AK Steel** (Mar 2020) — $1.1B
  - Added Middletown, Ashland, Dearborn facilities

**US Steel Acquisitions:**
- **Big River Steel** (Jan 2021) — $1.4B
  - Arkansas facility (3.3 million tons flexible HSM)
  - Big River Steel 2 under construction (another 3.0 million tons)

### Greenfield Capacity Additions

**Nucor West Virginia** (Construction)
- 3.0 million ton flex mill (galvanizing, advanced high-strength steel)
- Startup: 2026
- Total investment: $2.7 billion

**SDI Sinton, Texas** (Operational 2022)
- 3.0 million ton flat-rolled capacity
- Focus: heavy-gauge, electrical steel

---

## Next Steps

### Planned Enhancements

1. **EPA FRS Steel Facility Analysis**
   - Query all NAICS 331110 facilities
   - Cross-reference with AIST for validation
   - Add environmental compliance tracking

2. **SCRS Rail Integration**
   - Match AIST plants to SCRS rail-served facility database
   - Identify rail origins for steel movements

3. **Panjiva Import Analysis**
   - HS 7208-7212 import volumes by port
   - Consignee matching to service centers/end users
   - Section 232 impact quantification

4. **Service Center Database**
   - Import 53-facility end-user database
   - Map steel flow from mills → service centers → fabricators

5. **Regional Demand Modeling**
   - State-level steel consumption estimates
   - End-user segment breakdown (automotive, construction, energy)

---

## Data Refresh Schedule

| Data Source | Current Vintage | Refresh Cadence | Next Update |
|-------------|-----------------|-----------------|-------------|
| AIST Directory | 2021 | Annual | 2025 edition expected Q2 |
| EPA FRS | 2024-Q4 | Quarterly | 2025-Q1 available |
| SCRS Rail Facilities | 2024 | Annual | Static reference |
| Panjiva Imports | 2023-2025 | Real-time | Continuous (subscription) |
| USGS Minerals | 2024 | Annual | 2025 prelim available Q2 |

---

**Module Status:** ✅ Production Landscape Complete | 🚧 Trade Flows In Progress | 📅 End User Analysis Planned

**Last Updated:** 2026-02-24

**Maintained by:** William S. Davis III
