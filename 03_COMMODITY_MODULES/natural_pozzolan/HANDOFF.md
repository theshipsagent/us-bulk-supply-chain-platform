# HANDOFF — Natural Pozzolan Module for Master Reporting Platform
# From: project_master_reporting/natural_pozzolan/ (standalone dossier session)
# To: project_master_reporting (master session with full toolset access)
# Date: 2026-02-18

---

## WHAT WAS BUILT

A comprehensive HTML dossier on natural pozzolans as SCMs in cement and concrete. This is the fourth commodity dossier in the series (fly ash, aggregates, slag, natural pozzolans) — all using the same HTML/CSS template format.

### Key Findings

- **Growth sector**: Only SCM category with expanding supply from independent mineral reserves
- **2.5 Mt shipped** to US concrete in 2024 (NPA data); capacity projected 3.5-4.0 Mt by 2028
- **Price convergence**: Natural pozzolans ~$115/Mt now competitive with fly ash at $118/Mt (first time)
- **Large reserves**: >25 Mt pumice (USGS); Kirkland Mine 39 Mt; massive NV volcanic tuff deposits
- **LC3 emerging**: $1.6B DOE investment in cement decarb; 3 of 6 projects target LC3; 40% CO2 reduction
- **Major company entry**: CRH/Ash Grove acquired Geofortis (Sep 2024); Eco Material >4 Mt/yr capacity
- **Bridge SCM**: Natural volcanic pozzolans serve near-term while LC3 infrastructure builds (3-5 yr)
- **State DOT acceptance expanding**: TX, NY, WA, CA, OH, WI, FL and others accepting or proposing

### Files Delivered

```
project_master_reporting/natural_pozzolan/
├── NATURAL_POZZOLAN_COMPREHENSIVE_DOSSIER.html   (~50 KB, 15 sections, SVG charts)
├── BUILD_NOTES.md                                  (sources, NAICS/HTS codes, methodology)
└── HANDOFF.md                                      (THIS FILE)
```

---

## COMPLETE SCM DOSSIER SERIES

This natural pozzolan module completes the four-dossier SCM coverage:

| Module | Location | Key Supply Dynamic |
|--------|----------|-------------------|
| **Fly Ash** | `project_flyash/` | Declining — coal plant closures (-64% since 2007 peak) |
| **GGBFS/Slag** | `project_master_reporting/slag/` | Constrained — EAF transition (70% of US steel) |
| **Natural Pozzolans** | `project_master_reporting/natural_pozzolan/` | Growing — independent mineral reserves; LC3 emerging |
| **Aggregates** | `project_master_reporting/aggregate/` | Stable — limestone feeds cement (70% of crushed stone) |

### The Combined SCM Supply Picture

```
US SCM Supply to Concrete (2024): >20 Mt total
├── Fly Ash:           14.7 Mt  ████████████████ (declining)
├── GGBFS:             ~8.0 Mt  ████████████     (constrained)
├── Natural Pozzolans:  2.5 Mt  ███              (GROWING)
└── Silica Fume:       <1.0 Mt  █                (niche)

Projected 2028-2030:
├── Fly Ash:           ~10 Mt   ██████████       (further decline)
├── GGBFS:             ~6 Mt    ████████         (BF closures)
├── Natural Pozzolans: 3.5-4 Mt ████████         (mines + LC3)
└── LC3 (commercial):  TBD Mt   ??               (DOE demos → scale)
```

---

## INTEGRATION WITH EXISTING TOOLS

### 1. EPA FRS (`task_epa_frs/`)
```
Query NAICS:
  212399 - Nonmetallic Mineral Mining (pumice, volcanic ash)
  212325 - Clay and Refractory Minerals Mining (kaolin/calcined clay)
  327310 - Cement Manufacturing (pozzolan consumers)
  327320 - Ready-Mix Concrete (end users)
```
Map all pozzolan mining operations, clay mines (for LC3 feedstock), and concrete demand centers.

### 2. Panjiva (`project_manifest/`)
```
Query HTS:
  2513.10 - Pumice (crude and processed)
  2507 - Kaolin and kaolinic clays
  2530.90 - Other mineral substances
```
Map Greek pumice imports to eastern/Gulf ports; kaolin trade flows.

### 3. Rail Cost Model (`project_rail/`)
- Model distribution costs from Western pozzolan sources (ID, NM, AZ, NV, UT) to Eastern demand centers
- Hazen NV project is 9 km from UP rail siding — example of rail-served pozzolan supply
- Compare rail vs truck breakeven distances for lightweight pumice (low density = high-cube challenge)

### 4. Fly Ash Dossier (`project_flyash/`)
- Natural pozzolans are the direct replacement for declining fly ash
- Price crossover ($115 NP vs $118 fly ash) is the key market signal
- Combined analysis: where fly ash supply gaps are largest = where NP demand grows fastest

### 5. Slag Dossier (`slag/`)
- GGBFS constraints create additional demand pull for alternative SCMs
- 22% of US cement producers reported GGBFS shortages — natural pozzolans fill part of this gap
- Both GGBFS ($100-140+) and NP (~$115) compete for the same concrete mix position

### 6. Aggregates Dossier (`aggregate/`)
- Limestone (70% of crushed stone) feeds cement plants that consume pozzolans
- LC3 uses 15% limestone in its formulation — increases limestone demand per ton of cement
- Air-cooled BFS and pumice both serve as lightweight aggregate

---

## RECOMMENDED NEXT STEPS

### Immediate
1. Copy `natural_pozzolan/` into `03_COMMODITY_MODULES/natural_pozzolan/`
2. Create combined **"US SCM Supply Outlook"** report merging fly ash + GGBFS + NP + LC3

### Phase 2: Geospatial Analysis
3. Map all pozzolan deposits (Western US) vs concrete demand centers (national)
4. Calculate rail distribution cost from each pozzolan source to top 50 MSAs
5. Identify "pozzolan deserts" — regions far from both pozzolan and fly ash sources

### Phase 3: LC3 Tracking
6. Monitor DOE demonstration projects (National Cement CA, Roanoke VA, Summit)
7. Track ASTM standards evolution for higher pozzolan/clay replacement limits
8. Map US kaolin/clay deposits suitable for LC3 feedstock

### Phase 4: Market Intelligence
9. Entity resolution: pozzolan producers → cement company relationships
10. Track state DOT acceptance progress (expand from current 9+ states)
11. Monitor EPD publication for natural pozzolan products

---

## CROSS-PROJECT REFERENCES

| Resource | Location | Relevance |
|----------|----------|-----------|
| Fly Ash Dossier | `project_flyash/FLY_ASH_COMPREHENSIVE_DOSSIER_v2.html` | Parallel SCM; declining supply |
| Slag/GGBFS Dossier | `project_master_reporting/slag/` | Parallel SCM; constrained supply |
| Aggregates Dossier | `project_master_reporting/aggregate/` | Limestone for cement + LC3 |
| Master Spec | `project_master_reporting/CLAUDE.md` | Architecture, standards |
| EPA FRS | `task_epa_frs/` | Mining facility locations |
| Manifests | `project_manifest/` | HTS 2513 pumice imports |
| Rail Model | `project_rail/` | W→E distribution costing |
| Barge Model | `project_barge/` | Waterway distribution |
| Cement Markets | `project_cement_markets/` | Demand-side context |
| GIS Data | `sources_data_maps/` | Deposit/facility mapping |

---

## OPEN QUESTIONS FOR MASTER SESSION

1. **Combined SCM report**: Should we build a unified "US SCM Supply Outlook 2025-2030" merging all four dossiers?
2. **LC3 module**: Should LC3 be part of the natural_pozzolan module or a separate commodity module (given its unique cement plant infrastructure requirements)?
3. **Ground glass pozzolan (GGP)**: ASTM C1866 covers this emerging SCM. Should we add a section or separate module?
4. **Pozzolan distribution modeling**: The West-to-East logistics gap is the primary constraint. Should we run full rail/truck cost models from each deposit to demand centers?

---

*Handoff prepared by Claude Code session, 2026-02-18. All files in `project_master_reporting/natural_pozzolan/` are ready for integration.*
