# NAICS & HTS Codes — Commodity Module Reference

**Last Updated:** 2026-02-24
**Purpose:** Classification codes for facility queries and trade flow analysis

---

## Overview

This document provides NAICS (North American Industry Classification System) and HTS (Harmonized Tariff Schedule) codes relevant to each commodity module.

**Usage:**
- **NAICS codes** → EPA FRS facility queries, SCRS rail-served facility filters
- **HTS codes** → Panjiva/CBP import manifest classification, trade flow analysis

---

## Cement & Cementitious Materials

### NAICS Codes

#### Core Cement Manufacturing
| NAICS | Description | Use Case |
|---|---|---|
| 327310 | Cement Manufacturing | Portland cement plants, clinker production |
| 327320 | Ready-Mix Concrete Manufacturing | Ready-mix plants, concrete batching |
| 327331 | Concrete Block and Brick Manufacturing | Precast concrete products |
| 327332 | Concrete Pipe Manufacturing | Concrete pipe plants |
| 327390 | Other Concrete Product Manufacturing | Misc. concrete products |

#### Related Manufacturing
| NAICS | Description | Use Case |
|---|---|---|
| 327410 | Lime Manufacturing | Lime plants (sometimes co-located with cement) |
| 327420 | Gypsum Product Manufacturing | Wallboard, plaster |
| 327910 | Abrasive Product Manufacturing | Industrial minerals |
| 327999 | All Other Nonmetallic Mineral Product Manufacturing | Specialty materials |

#### SCM Sources
| NAICS | Description | Use Case |
|---|---|---|
| 221112 | Fossil Fuel Electric Power Generation | Coal plants (fly ash source) |
| 331110 | Iron and Steel Mills and Ferroalloy Manufacturing | Integrated steel mills (blast furnace slag) |
| 331210 | Iron and Steel Pipe and Tube Manufacturing | Steel manufacturing (slag) |
| 212312 | Crushed and Broken Limestone Mining | Limestone quarries (aggregate, raw material) |
| 212319 | Other Crushed and Broken Stone Mining | Natural pozzolan sources |

#### Distribution
| NAICS | Description | Use Case |
|---|---|---|
| 423320 | Brick, Stone, and Related Construction Material Merchant Wholesalers | Cement/concrete wholesalers |
| 424690 | Other Chemical and Allied Products Merchant Wholesalers | Fly ash, slag wholesalers |

### HTS Codes

#### Portland Cement
| HTS | Description | Tariff Rate (2024) |
|---|---|---:|
| 2523.10 | Cement clinkers | Varies by country |
| 2523.21 | White Portland cement | Varies by country |
| 2523.29 | Other Portland cement | Varies by country |
| 2523.30 | Aluminous cement | Varies by country |
| 2523.90 | Other hydraulic cements | Varies by country |

#### Supplementary Cementitious Materials (SCM)
| HTS | Description | Tariff Rate (2024) |
|---|---|---:|
| 2618.00 | Granulated slag (slag sand) from iron/steel manufacture | Free (typically) |
| 2619.00 | Slag, dross (other than granulated slag) | Free (typically) |
| 2621.00 | Slag wool, rock wool (mineral wools) | Varies |
| 2620.60 | Ash and residues containing arsenic, metals, compounds | Varies |
| 3824.90 | Prepared binders for foundry molds; chemical products (pozzolans) | Varies |

**Note:** Tariff rates vary by country of origin. See `02_TOOLSETS/policy_analysis/data/hts_cement_tariff_rates.json` for detailed rates.

---

## Steel & Iron Products

### NAICS Codes

#### Primary Steel Production
| NAICS | Description | Use Case |
|---|---|---|
| 331110 | Iron and Steel Mills and Ferroalloy Manufacturing | Integrated mills, mini-mills, EAF |
| 331210 | Iron and Steel Pipe and Tube Manufacturing | Seamless/welded pipe and tube |
| 331221 | Rolled Steel Shape Manufacturing | Structural shapes (I-beams, channels) |
| 331222 | Steel Wire Drawing | Wire rod, wire products |

#### Secondary Steel Processing
| NAICS | Description | Use Case |
|---|---|---|
| 332111 | Iron and Steel Forging | Forged steel products |
| 332312 | Fabricated Structural Metal Manufacturing | Steel fabrication shops |
| 332313 | Plate Work Manufacturing | Pressure vessels, tanks |

### HTS Codes

#### Iron & Steel Products
| HTS | Description |
|---|---|
| 7206 | Iron and non-alloy steel in ingots or other primary forms |
| 7207 | Semi-finished products of iron or non-alloy steel |
| 7208 | Flat-rolled products of iron or non-alloy steel, in coils, hot-rolled |
| 7209 | Flat-rolled products of iron or non-alloy steel, in coils, cold-rolled |
| 7210 | Flat-rolled products of iron or non-alloy steel, clad, plated, or coated |
| 7211 | Flat-rolled products of iron or non-alloy steel, not in coils |
| 7212 | Flat-rolled products of iron or non-alloy steel, clad, plated, or coated |
| 7213 | Bars and rods, hot-rolled, in irregularly wound coils |
| 7214 | Bars and rods of iron or non-alloy steel |
| 7215 | Other bars and rods of iron or non-alloy steel |

---

## Aluminum Products

### NAICS Codes

#### Primary Aluminum Production
| NAICS | Description | Use Case |
|---|---|---|
| 331313 | Alumina Refining and Primary Aluminum Production | Primary smelters, alumina refineries |
| 331314 | Secondary Smelting and Alloying of Aluminum | Secondary aluminum production |
| 331315 | Aluminum Sheet, Plate, and Foil Manufacturing | Rolling mills |
| 331318 | Other Aluminum Rolling, Drawing, and Extruding | Extrusion plants, drawn products |

### HTS Codes

#### Aluminum Products
| HTS | Description |
|---|---|
| 7601 | Unwrought aluminum |
| 7603 | Aluminum powders and flakes |
| 7604 | Aluminum bars, rods, and profiles |
| 7605 | Aluminum wire |
| 7606 | Aluminum plates, sheets, and strip (thickness > 0.2 mm) |
| 7607 | Aluminum foil |
| 7608 | Aluminum tubes and pipes |

---

## Copper & Brass Products

### NAICS Codes

#### Primary Copper Production
| NAICS | Description | Use Case |
|---|---|---|
| 212234 | Copper Ore and Nickel Ore Mining | Copper mines |
| 331410 | Nonferrous Metal (except Aluminum) Smelting and Refining | Copper smelters, refineries |
| 331420 | Copper Rolling, Drawing, Extruding, and Alloying | Copper mills, brass mills |

### HTS Codes

#### Copper Products
| HTS | Description |
|---|---|
| 7402 | Unrefined copper; copper anodes for electrolytic refining |
| 7403 | Refined copper and copper alloys, unwrought |
| 7404 | Copper waste and scrap |
| 7405 | Master alloys of copper |
| 7407 | Copper bars, rods, and profiles |
| 7408 | Copper wire |
| 7409 | Copper plates, sheets, and strip (thickness > 0.15 mm) |
| 7411 | Copper tubes and pipes |

---

## Grain & Oilseeds

### NAICS Codes

#### Grain Production & Handling
| NAICS | Description | Use Case |
|---|---|---|
| 111110 | Soybean Farming | Soybean production |
| 111120 | Oilseed (except Soybean) Farming | Canola, sunflower, etc. |
| 111130 | Dry Pea and Bean Farming | Pulses |
| 111140 | Wheat Farming | Wheat production |
| 111150 | Corn Farming | Corn production |
| 111160 | Rice Farming | Rice production |
| 111191 | Oilseed and Grain Combination Farming | Mixed grain farms |
| 111199 | All Other Grain Farming | Barley, oats, etc. |

#### Grain Storage & Processing
| NAICS | Description | Use Case |
|---|---|---|
| 424510 | Grain and Field Bean Merchant Wholesalers | Grain elevators, wholesalers |
| 311211 | Flour Milling | Flour mills |
| 311212 | Rice Milling | Rice mills |
| 311213 | Malt Manufacturing | Malt houses |
| 311221 | Wet Corn Milling | Corn processors |
| 311224 | Soybean and Other Oilseed Processing | Soybean crush plants |

### HTS Codes

#### Grains
| HTS | Description |
|---|---|
| 1001 | Wheat and meslin |
| 1002 | Rye |
| 1003 | Barley |
| 1004 | Oats |
| 1005 | Corn (maize) |
| 1006 | Rice |
| 1007 | Grain sorghum |
| 1008 | Buckwheat, millet, and other cereals |

#### Oilseeds
| HTS | Description |
|---|---|
| 1201 | Soybeans |
| 1204 | Linseed (flax seed) |
| 1205 | Rape or colza seeds (canola) |
| 1206 | Sunflower seeds |
| 1207 | Other oil seeds and oleaginous fruits |

---

## Fertilizers

### NAICS Codes

#### Fertilizer Manufacturing
| NAICS | Description | Use Case |
|---|---|---|
| 325311 | Nitrogenous Fertilizer Manufacturing | Ammonia, urea, ammonium nitrate |
| 325312 | Phosphatic Fertilizer Manufacturing | Phosphate fertilizers, DAP, MAP |
| 325314 | Fertilizer (Mixing Only) Manufacturing | Blended fertilizers |
| 325320 | Pesticide and Other Agricultural Chemical Manufacturing | Crop protection chemicals |

#### Fertilizer Distribution
| NAICS | Description | Use Case |
|---|---|---|
| 424910 | Farm Supplies Merchant Wholesalers | Fertilizer wholesalers |
| 444220 | Nursery, Garden Center, and Farm Supply Stores | Retail farm supply |

### HTS Codes

#### Fertilizers
| HTS | Description |
|---|---|
| 3102 | Mineral or chemical fertilizers, nitrogenous |
| 3103 | Mineral or chemical fertilizers, phosphatic |
| 3104 | Mineral or chemical fertilizers, potassic |
| 3105 | Mineral or chemical fertilizers containing two or three elements (N, P, K) |

#### Fertilizer Ingredients
| HTS | Description |
|---|---|
| 2510 | Natural calcium phosphates, natural aluminum calcium phosphates |
| 2814 | Ammonia, anhydrous or in aqueous solution |
| 2834 | Nitrites; nitrates |

---

## Petroleum & Petroleum Coke

### NAICS Codes

#### Petroleum Refining
| NAICS | Description | Use Case |
|---|---|---|
| 324110 | Petroleum Refineries | Crude oil refining |
| 324121 | Asphalt Paving Mixture and Block Manufacturing | Asphalt plants |
| 324122 | Asphalt Shingle and Coating Materials Manufacturing | Roofing materials |
| 324191 | Petroleum Lubricating Oil and Grease Manufacturing | Lubricant blending |
| 324199 | All Other Petroleum and Coal Products Manufacturing | Petroleum coke, specialty products |

#### Petroleum Distribution
| NAICS | Description | Use Case |
|---|---|---|
| 424710 | Petroleum Bulk Stations and Terminals | Fuel terminals |
| 424720 | Petroleum and Petroleum Products Merchant Wholesalers | Fuel wholesalers |
| 486110 | Pipeline Transportation of Crude Oil | Crude pipelines |
| 486910 | Pipeline Transportation of Refined Petroleum Products | Product pipelines |

### HTS Codes

#### Crude Oil & Refined Products
| HTS | Description |
|---|---|
| 2709 | Petroleum oils and oils from bituminous minerals, crude |
| 2710 | Petroleum oils and oils from bituminous minerals (not crude) |
| 2711 | Petroleum gases and other gaseous hydrocarbons |
| 2712 | Petroleum jelly, paraffin wax, microcrystalline wax |
| 2713 | Petroleum coke, petroleum bitumen |

---

## Chemicals (General)

### NAICS Codes

#### Basic Chemicals
| NAICS | Description | Use Case |
|---|---|---|
| 325110 | Petrochemical Manufacturing | Ethylene, propylene, aromatics |
| 325120 | Industrial Gas Manufacturing | Oxygen, nitrogen, hydrogen |
| 325180 | Other Basic Inorganic Chemical Manufacturing | Acids, alkalis, salts |
| 325190 | Other Basic Organic Chemical Manufacturing | Organic chemicals |

#### Specialty Chemicals
| NAICS | Description | Use Case |
|---|---|---|
| 325211 | Plastics Material and Resin Manufacturing | Polymers, resins |
| 325220 | Artificial and Synthetic Fibers and Filaments Manufacturing | Synthetic fibers |
| 325311 | Nitrogenous Fertilizer Manufacturing | Ammonia, urea |
| 325312 | Phosphatic Fertilizer Manufacturing | Phosphate fertilizers |

### HTS Codes

#### Inorganic Chemicals
| HTS | Description |
|---|---|
| 28 | Inorganic chemicals; organic or inorganic compounds of precious metals, rare-earth metals, radioactive elements, or isotopes |

#### Organic Chemicals
| HTS | Description |
|---|---|
| 29 | Organic chemicals |

---

## Coal

### NAICS Codes

#### Coal Mining
| NAICS | Description | Use Case |
|---|---|---|
| 212111 | Bituminous Coal and Lignite Surface Mining | Surface coal mines |
| 212112 | Bituminous Coal Underground Mining | Underground coal mines |
| 212113 | Anthracite Mining | Anthracite mines |

#### Coal Distribution
| NAICS | Description | Use Case |
|---|---|---|
| 424520 | Coal and Other Mineral and Ore Merchant Wholesalers | Coal terminals, wholesalers |

### HTS Codes

#### Coal
| HTS | Description |
|---|---|
| 2701 | Coal; briquettes, ovoids and similar solid fuels manufactured from coal |
| 2702 | Lignite, whether or not agglomerated, excluding jet |
| 2703 | Peat (including peat litter), whether or not agglomerated |
| 2704 | Coke and semi-coke of coal, of lignite or of peat |

---

## Forestry & Wood Products

### NAICS Codes

#### Logging & Sawmills
| NAICS | Description | Use Case |
|---|---|---|
| 113110 | Timber Tract Operations | Timberland management |
| 113310 | Logging | Logging operations |
| 321113 | Sawmills | Lumber production |
| 321114 | Wood Preservation | Treated lumber |

#### Wood Products Manufacturing
| NAICS | Description | Use Case |
|---|---|---|
| 321211 | Hardwood Veneer and Plywood Manufacturing | Plywood mills |
| 321212 | Softwood Veneer and Plywood Manufacturing | Softwood plywood |
| 321213 | Engineered Wood Member Manufacturing | I-joists, LVL |
| 321214 | Truss Manufacturing | Roof/floor trusses |
| 321219 | Reconstituted Wood Product Manufacturing | Particleboard, MDF, OSB |

#### Pulp & Paper
| NAICS | Description | Use Case |
|---|---|---|
| 322110 | Pulp Mills | Pulp production |
| 322121 | Paper (except Newsprint) Mills | Paper mills |
| 322122 | Newsprint Mills | Newsprint production |
| 322130 | Paperboard Mills | Paperboard/containerboard |

### HTS Codes

#### Wood & Wood Products
| HTS | Description |
|---|---|
| 44 | Wood and articles of wood; wood charcoal |
| 4401 | Fuel wood, in logs, billets, twigs, faggots, or similar forms |
| 4403 | Wood in the rough |
| 4407 | Wood sawn or chipped lengthwise, sliced or peeled |
| 4408 | Sheets for veneering |
| 4409 | Wood continuously shaped |
| 4410 | Particle board, oriented strand board (OSB) |
| 4411 | Fibreboard of wood or other ligneous materials |
| 4412 | Plywood, veneered panels, and similar laminated wood |

#### Pulp & Paper
| HTS | Description |
|---|---|
| 47 | Pulp of wood or of other fibrous cellulosic material |
| 48 | Paper and paperboard; articles of paper pulp, paper or paperboard |

---

## Usage Examples

### EPA FRS Facility Query (Cement)

```python
import duckdb

con = duckdb.connect('02_TOOLSETS/facility_registry/data/frs.duckdb')

# Query all cement-related facilities in Louisiana
query = """
SELECT
    registry_id,
    facility_name,
    naics_code,
    latitude,
    longitude,
    city,
    state_code
FROM epa_frs_facilities
WHERE state_code = 'LA'
  AND naics_code IN ('327310', '327320', '327331', '327332', '327390')
ORDER BY facility_name
"""

facilities = con.execute(query).fetch_df()
print(f"Found {len(facilities)} cement facilities in Louisiana")
```

### Panjiva Trade Flow Filter (Cement)

```python
import pandas as pd

# Load Panjiva import data
panjiva = pd.read_parquet('01_DATA_SOURCES/federal_trade/panjiva_imports/panjiva_master.parquet')

# Filter for cement imports
cement_codes = ['2523.10', '2523.21', '2523.29', '2523.30', '2523.90']
cement_imports = panjiva[panjiva['hts_code'].isin(cement_codes)]

# Analyze by origin country
by_country = cement_imports.groupby('country_of_origin').agg({
    'quantity_metric_tons': 'sum',
    'customs_value_usd': 'sum'
}).sort_values('quantity_metric_tons', ascending=False)

print(by_country.head(10))
```

---

## References

- **NAICS:** https://www.census.gov/naics/
- **HTS:** https://hts.usitc.gov/
- **USITC Tariff Database:** https://dataweb.usitc.gov/

For commodity-specific code lists, see `03_COMMODITY_MODULES/{commodity}/naics_hts_codes.json`
