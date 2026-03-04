# Grain Commodity Module
**Module Version:** 1.0.0 | **Status:** Active — Data Ingestion Phase
**Owner:** William S. Davis III
**Last Updated:** 2026-03-02

---

## Overview

The grain commodity module provides end-to-end supply chain intelligence for U.S. bulk grain
and oilseed exports. It covers ten commodities across the full chain — from field production
through country elevators, river/rail transport, export terminals, and ocean vessel loading —
integrating with the platform's core barge, rail, vessel, and port toolsets.

**Commodities in Scope:**

| Commodity | HS Chapter | NAICS Primary |
|---|---|---|
| Corn | 1005 | 115114 / 311221 |
| Soybeans | 1201 | 115114 / 311224 |
| Wheat | 1001 | 115114 / 311211 |
| Grain Sorghum | 1007 | 115114 |
| Barley | 1003 | 115114 |
| Oats | 1004 | 115114 |
| Rice | 1006 | 111160 / 311212 |
| DDGS / Corn Gluten | 2302-2303 | 311221 |
| Soybean Meal | 2304 | 311224 |
| Soybean Oil | 1507 | 311225 |

---

## U.S. Grain Supply Chain Structure

```
Producer (farm)
    ↓ [truck — typically <50 miles]
Country Elevator
(grain receiving, cleaning, drying, short-term storage)
    ↓ [truck or short-line rail]
Sub-Terminal Elevator
(large-scale accumulation, shuttle train loading)
    ↓ [Class I rail  —OR—  barge via river port]
Export Terminal / Export Elevator
(seaport grain handling, ship loading)
    ↓ [ocean bulk vessel — Panamax/Supramax/Handymax]
Destination Country
(China, Mexico, Japan, Egypt, EU, Southeast Asia, etc.)
```

**Domestic Processing Chain (parallel to export):**
```
Country Elevator → [truck/rail] → Processor
  Processors: flour mill | ethanol plant | soy crusher |
              feed mill | wet corn mill | rice mill
```

---

## Modal Economics Summary

| Market | Truck | Rail | Barge | Key Driver |
|---|---|---|---|---|
| Domestic (2014) | ~53% | ~28% | ~19% | Growing domestic processing demand |
| Export (2014) | ~7% | ~38% | ~55% | Long-distance corridors to Gulf/PNW ports |
| Gulf corn export | ~10% | ~0% | ~90% | UMR-IWW barge system proximity |
| PNW wheat export | ~0% | ~60% | ~28% | Distance from waterways in plains |

**Modal cost crossover distances (approximate):**
- Truck → Rail: ~250 miles
- Rail → Barge: ~700 miles (where waterway available)

**Source:** USDA AMS Modal Share Analysis 1978-2014 (Oct 2017), CRS RL32720

---

## Data Sources — 26 Catalogued

### Tier 1: Live Federal APIs
1. **USDA FAS ESR** — Weekly export sales by commodity + country
2. **USDA FAS PSD** — Monthly global supply/demand balances (WASDE)
3. **USDA NASS QuickStats** — Production, acreage, stocks, prices
4. **U.S. Census Trade API** — Monthly exports by HS-10, port, state
5. **USDA ERS FATUS** — Annual/monthly trade aggregations

### Tier 2: Supplemental Downloads
6. **USDA AMS GTR** — Weekly freight rates (barge, rail, ocean, truck)
7. **USDA FGIS** — Export grain inspection & weighing data
8. **WASDE Report** — Monthly global supply/demand (machine-readable)
9. **USDA GAIN Reports** — Country-specific intelligence from attachés
10. **USDA ERS Baseline** — 10-year supply/demand projections
11. **Cornell ESMIS** — Historical USDA publication archive

### Tier 3: Trade Organizations
12. **NAEGA** — GOMAI trade access indexes; export policy
13. **USSEC** — Soybean export volumes; SSAP sustainability
14. **USGC / Grains Council** — GIAF portal; corn/DDGS export data
15. **USW** — Wheat market data; port basis; inspection reports
16. **GAFTA** — International grain contract standards
17. **NGFA** — Domestic trade rules; rail performance data

### Tier 4: Market Prices & Futures
18. **CME/CBOT** — ZC/ZW/ZS/ZM/ZL/ZO/ZR futures (paid or yfinance)
19. **USDA AMS Market News** — Daily elevator bids, basis levels

### Tier 5: Geospatial & Infrastructure
20. **USDA CDL** — 30-meter cropland data layer (production geography)
21. **USACE Waterborne Commerce** — Annual barge tonnage by commodity/waterway
22. **STB Rail Waybill** — Rail O-D shipments by grain STCC code
23. **EIA Ethanol** — Corn demand: ethanol production/exports
24. **data.gov** — Federal ag dataset catalog
25. **USDA NASS Crop Progress** — Weekly crop condition reports
26. **AMS AgTransport Platform** — Integrated freight visualization

Full catalog with endpoints: see `data_sources.json`

---

## Module Components

```
grain/
├── README.md                          ← This file
├── config.yaml                        ← Module parameters, API settings, port registry
├── naics_hts_codes.json              ← Complete commodity classification codes
├── data_sources.json                  ← All 26+ sources with endpoints/metadata
├── knowledge_bank/                    ← Reference intelligence from research PDFs
│   ├── pdf_abstracts/                 ← Structured summaries of key reference documents
│   ├── modal_economics/               ← Transport cost benchmarks by mode/commodity
│   ├── facility_taxonomy/             ← Grain elevator types and operations
│   └── supply_chain_flows/            ← Supply chain structure and flow diagrams
├── market_intelligence/
│   ├── supply_landscape/              ← Production facilities, capacity data
│   ├── demand_analysis/               ← Domestic consumption patterns
│   ├── trade_flows/                   ← Import/export analysis by destination
│   └── pricing/                       ← Market pricing, basis, futures
├── supply_chain_models/
│   ├── barge_routes/                  ← Inland waterway routing models
│   ├── rail_routes/                   ← Rail rate and routing analysis
│   └── terminal_operations/           ← Export terminal capacity and costs
├── src/                               ← Data ingestion and analysis scripts
│   ├── ingest_grain_data.py           ← Main ingestion pipeline
│   ├── fetch_fas_esr.py               ← FAS export sales
│   ├── fetch_fas_psd.py               ← FAS supply/demand
│   ├── fetch_nass.py                  ← NASS QuickStats
│   ├── fetch_census_trade.py          ← Census trade API
│   ├── fetch_ams_gtr.py               ← AMS freight datasets
│   └── validate_grain_data.py         ← Cross-source validation
├── data/                              ← Raw and processed data (gitignored)
│   ├── raw/                           ← Downloaded source files
│   └── processed/                     ← Normalized parquet outputs
└── reports/                           ← Client deliverables
    ├── templates/
    ├── drafts/
    └── published/
```

---

## Quick Start

```bash
# 1. Set API keys
export USDA_API_KEY="your_key_here"    # Register: https://api.data.gov/signup/
export CENSUS_API_KEY="your_key_here"  # Register: https://api.census.gov/data/key_signup.html

# 2. Install dependencies
pip install requests pandas openpyxl pyarrow python-dotenv aiohttp

# 3. Run full ingestion (recommended execution order)
python src/ingest_grain_data.py --step production   # NASS supply data
python src/ingest_grain_data.py --step psd          # FAS global S&D
python src/ingest_grain_data.py --step esr          # FAS weekly exports
python src/ingest_grain_data.py --step census       # Census trade
python src/ingest_grain_data.py --step gtr          # AMS freight rates
python src/ingest_grain_data.py --step fgis         # Inspection volumes

# 4. Validate cross-source consistency
python src/validate_grain_data.py
```

---

## Platform Integration

| Toolset | Integration |
|---|---|
| `barge_cost_model` | UMR-IWW corridor routing; grain USACE commodity codes 14/15/17 |
| `rail_cost_model` | STCC 01112/31/41/55; shuttle vs carload rate benchmarking |
| `vessel_voyage_analysis` | FGIS inspection → vessel matching; grain bulk carrier identification |
| `vessel_intelligence` | HS 10-digit export manifest classification |
| `facility_registry` | Grain elevator NAICS 115114, 493130, 424510 |
| `port_cost_model` | Export elevator handling charges at Gulf/PNW terminals |
| `census_trade` | Monthly HS-10 flows by port district and country |

---

*Primary sources: USDA FAS, ERS, NASS, AMS, FGIS; U.S. Census Bureau; USACE; STB; CME Group*
*Knowledge bank PDFs: CRS RL32720, USDA AMS Modal Share 1978-2014, Jaller 2022, EPA AP-42 §9.9.1, USDA AMS Rail Study 2013*
