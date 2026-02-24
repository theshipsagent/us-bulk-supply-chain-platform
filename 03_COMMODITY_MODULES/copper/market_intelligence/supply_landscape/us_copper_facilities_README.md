# US Copper Cathode Supply Chain — Geospatial Facility Database

## Purpose

Maps all major US facilities that produce, consume, or trade refined copper cathode (HS 7403.11) for ocean import consignee matching against Panjiva manifest records. Parallel dataset to the aluminum (HS 7601) and steel AIST databases.

## Scope: 43 Facilities

| Category | Count | Combined Capacity |
|----------|-------|-------------------|
| Primary smelters | 3 (2 operating, 1 idled) | 890 kt concentrate |
| Primary refineries | 3 (2 operating, 1 idled) | 873 kt cathode |
| SX/EW refineries | 12 (11 operating, 1 construction) | 713 kt cathode |
| Secondary smelters/refineries | 4 | 230+ kt scrap throughput |
| Wire rod mills | 8 (incl. 4 integrated w/cable) | 2,051 kt/yr |
| Brass mills | 9 | 635 kt/yr |
| Copper tube mills | 5 | 280 kt/yr |
| Trading/merchants | 3 | n/a |

## Key HS 7403 Consignees (Primary Targets)

The actual **importers of copper cathode** are concentrated among a small number of very large consumers:

1. **Southwire (Carrollton, GA)** — 380+ kt/yr rod capacity. World's largest SCR copper rod mill. #1 US wire & cable producer. Single largest cathode buyer.
2. **Encore Wire/Prysmian (McKinney, TX)** — 200kt rod capacity. Vertically integrated rod + wire. Cathode mostly from AZ. Acquired by Prysmian Jul 2024.
3. **AmRod (Port Newark, NJ)** — 120kt. Independent rod producer at Port Newark — ideal for seaborne cathode imports. Top Panjiva consignee.
4. **Freeport-McMoRan El Paso (TX)** — 408kt refinery + rod mill. Produces cathode from Miami smelter anode but also buys supplemental.
5. **SDI LaFarga Copperworks (New Haven, IN)** — 213kt. Added ETP (cathode-fed) line 2020 alongside scrap-based FRHC.
6. **Wieland/Olin Brass (East Alton, IL)** — 200kt. Largest NA brass mill. Heavy cathode consumer for alloy casting.
7. **Cerro Wire (Hartselle, AL)** — 80kt rod + wire. Marmon/Berkshire Hathaway.
8. **Mueller Industries (Fulton MS, Wynne AR, Clinton TN)** — 200kt combined tube. Largest US copper tube producer.

Trading entities that appear as Panjiva consignees but redistribute to mills:
- **Engelhart CTP US (Stamford, CT)**
- **GT Commodities (Stamford, CT)**  
- **Geo. Wm. Rueff (New Orleans, LA)**

## US Copper Supply-Demand Gap

| | kt/yr |
|---|---:|
| Domestic mine production | 1,100 |
| Domestic cathode production (refinery+SX/EW) | ~1,000 |
| **Domestic consumption** | **~1,800** |
| **Import gap (cathode)** | **~750-800** |

Top cathode import sources: Chile (~40%), Canada, Peru, Mexico, Congo, Zambia

## Supply Chain Structure

```
MINE (AZ 70%, UT, NM, MT, NV)
  └─ Concentrate → PRIMARY SMELTER (Freeport Miami AZ, Kennecott UT)
       └─ Anode → PRIMARY REFINERY (Kennecott UT, FCX El Paso TX)
            └─ CATHODE
  └─ Oxide ore → SX/EW (Morenci, Bagdad, Safford, Ray, Tyrone...)
       └─ CATHODE

IMPORTED CATHODE (750-800kt via ports: Newark, Houston, New Orleans, Savannah)
  └─ WIRE ROD MILL (Southwire, Encore, AmRod, SDI LaFarga, Cerro, Rea)
       └─ Rod → Wire drawing → WIRE & CABLE
  └─ BRASS MILL (Wieland, PMX, Chase, Aurubis, Mueller)
       └─ Cast + roll → Strip / Sheet / Plate / Rod
  └─ TUBE MILL (Mueller Fulton/Wynne/Clinton, Cerro)
       └─ Cast + extrude → Plumbing tube, ACR tube, HVAC

SCRAP (30+ brass mills, 500 foundries consume)
  └─ SECONDARY SMELTER (Aurubis Augusta, Southwire)
       └─ Blister copper → refine to cathode or use directly
```

## Key Differences from Aluminum Database

- **Much more concentrated**: Copper cathode goes to ~15 major facilities vs. aluminum's ~68
- **Two dominant consumers**: Southwire + Encore/Prysmian together consume ~60% of imported cathode
- **Western production, Eastern consumption**: Mines/smelters in AZ/UT, biggest consumers in GA/TX/NJ/IN/IL
- **Port of entry matters**: AmRod at Port Newark is positioned to receive seaborne cathode directly
- **Trading intermediaries**: Engelhart, GT Commodities, Rueff show as Panjiva consignees but are redistributors

## Section 232 Investigation (Active)

BIS initiated Section 232 investigation for copper March 2025. Southwire's public comments argue:
- US copper demand projected to grow 112% by 2035 (2.9M mt)
- Imports of fairly-traded cathode essential to offset domestic supply shortfall  
- Only 2 primary smelters operating (both at capacity); 50% of US concentrate exported
- Last approved US smelter project dates to 1971 (never built)

## Files

| File | Description |
|------|-------------|
| `us_copper_facilities.py` | Python module with dataclasses, GeoJSON/CSV export |
| `us_copper_facilities.geojson` | GeoJSON FeatureCollection (WGS84) |
| `us_copper_facilities.csv` | Flat table for spreadsheet/database import |

## Data Sources

- USGS Mineral Commodity Summaries 2024-2025 (Copper)
- Southwire Section 232 public comments (BIS-2025-0010-0049)
- Freeport-McMoRan operations page, 10-K filings
- Rio Tinto Kennecott operations disclosures
- Aurubis AG press releases (Augusta/Richmond plant)
- Prysmian/Encore Wire investor materials
- Mueller Industries SEC filings and company history
- Wieland Group / Olin Brass product documentation
- SDI LaFarga Copperworks website and SDI disclosures
- CDA (Copper Development Association) recycling data
- Datamyne/Zauba HS 7403 import analysis
- GBR Copper Production reports 2024

## Integration

Combined metals dataset now covers:
- **Copper**: 43 facilities (this database)
- **Aluminum**: 68 facilities (HS 7601)
- **Steel production**: 68 facilities (AIST)
- **Steel end users**: 53 facilities
- **Total: 232 facilities** across the US metals value chain
