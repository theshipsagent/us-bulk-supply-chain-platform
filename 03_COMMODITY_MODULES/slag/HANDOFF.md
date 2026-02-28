# HANDOFF — Slag/GGBFS Module for Master Reporting Platform
# From: project_master_reporting/slag/ (standalone dossier session)
# To: project_master_reporting (master session with full toolset access)
# Date: 2026-02-18

---

## WHAT WAS BUILT

A comprehensive HTML dossier on slag in construction and cement, with primary focus on GGBFS as an SCM. Modeled after the fly ash dossier format (`project_flyash/FLY_ASH_COMPREHENSIVE_DOSSIER_v2.html`) and sibling to the aggregates dossier (`aggregate/AGGREGATES_COMPREHENSIVE_DOSSIER.html`).

### Key Findings

- **Supply-constrained market**: All US GGBFS (~3-5 Mt) consumed; market defined by supply, not demand
- **EAF transition = existential risk**: EAFs now ~70% of US steelmaking and rising; EAF slag CANNOT substitute for GGBFS; only ~1% of steel slag used as cement admixture
- **Value concentration**: GGBFS is <3% of slag tonnage but ~80% of $600M value
- **Import dependence**: ~2 Mt imported annually; Japan 52%, China 23%, Brazil 11%
- **Carbon advantage**: 93-96% lower embodied CO2 than OPC (35-67 vs 844-967 kg CO2e/t)
- **Dual SCM crisis**: Both fly ash AND GGBFS face structural supply declines from unrelated industrial transitions
- **Gary Works anchor**: Nippon Steel $3.1B investment to reline 4 BFs through 2030 — key supply stabilizer
- **Pricing**: GGBFS delivered $100-140+/ton; GBS unground $48-60/ton; OPC $163/ton; Fly ash $118/ton

### Files Delivered

```
project_master_reporting/slag/
├── SLAG_COMPREHENSIVE_DOSSIER.html   (~45 KB, 15 sections, SVG charts)
├── BUILD_NOTES.md                     (sources, NAICS/HTS codes, methodology)
└── HANDOFF.md                         (THIS FILE)
```

---

## INTEGRATION WITH EXISTING TOOLS

### 1. EPA FRS Facility Registry (`task_epa_frs/`)
**Action for Slag**:
```
Query NAICS codes:
  331110 - Iron and Steel Mills and Ferroalloy Manufacturing
  331111 - Iron and Steel Mills (integrated BF-BOF — GGBFS source)
  331112 - Electrometallurgical Ferroalloy Product Manufacturing (EAF — NO GGBFS)
  327310 - Cement Manufacturing (slag cement consumers)
  327320 - Ready-Mix Concrete Manufacturing (GGBFS end users)
```
This identifies every steel mill, cement plant, and ready-mix facility. Cross-reference 331111 (integrated) vs 331112 (EAF) to map GGBFS source vs non-source steelmaking.

### 2. Panjiva Import Manifests (`project_manifest/`)
**Action for Slag**:
```
Query HTS codes:
  2618.00.0000 - Granulated slag (slag sand) from iron/steel — PRIMARY
  2619 - Non-granulated slag, dross from iron/steel
  2523 - Portland cement, slag cement (blended products)
```
This maps import trade flows — vessel names, ports of entry, origin countries, shippers (Nippon Steel, Chinese mills, Brazilian suppliers), consignees (Heidelberg, Holcim, Charah, SATHI). Critical for understanding the growing import dependency.

### 3. Rail Network & Cost Model (`project_rail/`)
**Action for Slag**:
- Map rail routes from Great Lakes integrated mills (Gary IN, Burns Harbor IN, Cleveland OH, East Chicago IN) to demand centers
- Calculate rail distribution costs for GGBFS to Southeast, Texas, and East Coast markets
- SCRS data already has steel facilities classified — cross-reference with BF-BOF identification

### 4. Barge Cost Model (`project_barge/`)
**Action for Slag**:
- Great Lakes waterway distribution from Gary/Indiana mills
- Ohio River distribution from Cleveland/East Chicago
- Mississippi system for downstream distribution
- Compare barge vs rail cost for GGBFS to Gulf Coast terminals

### 5. Fly Ash Dossier (`project_flyash/`)
**Action — Cross-Reference**:
- Both SCMs face structural supply declines from different industrial transitions
- Fly ash: coal plant closures (-48% capacity since 2011)
- GGBFS: EAF shift (70% of steelmaking, no GGBFS produced)
- Combined SCM supply outlook is critical for cement industry planning
- Import economics differ: fly ash $16-27/Mt FOB Asia vs GGBFS $48-60/Mt wholesale

### 6. Aggregates Dossier (`aggregate/`)
**Action — Cross-Reference**:
- Limestone (70% of crushed stone, ~1.05 Bt) feeds cement manufacturing
- Cement manufacturing (84 Mt) is the primary consumer of GGBFS as SCM
- Supply chain: Quarry → Cement Plant (+ GGBFS) → Ready-Mix → Construction
- Air-cooled BFS and steel slag compete with natural aggregates for road base/fill

### 7. Cement Markets (`project_cement_markets/`)
**Action — Cross-Reference**:
- Cement demand is the demand driver for GGBFS
- PLC (Portland-Limestone Cement) adoption at 58% of shipments changes the SCM equation
- Type IS (slag cement) adoption trends
- Cement plant locations vs GGBFS supply points

### 8. Geospatial Data (`sources_data_maps/`)
**Action**:
- Map integrated steel mills (BF-BOF) with GGBFS production potential
- Overlay import terminal locations
- Map GGBFS distribution radius from each supply point (rail/truck/barge)
- Identify demand centers (cement plants, ready-mix) outside distribution radius — import opportunity zones

---

## RECOMMENDED INTEGRATION PLAN

### Phase 1: Data Assembly
1. Copy `slag/` contents into `03_COMMODITY_MODULES/slag/` in master_reporting structure
2. Run EPA FRS queries for NAICS 331110/331111 — map integrated mills
3. Run Panjiva queries for HTS 2618 — map GGBFS import trade flows
4. Cross-reference with fly ash and aggregates dossiers

### Phase 2: Supply Chain Mapping
5. Map domestic GGBFS supply points (7 integrated mills with granulation status)
6. Map import terminals (Houston, Norfolk, Cape Canaveral, Gulf Coast)
7. Calculate distribution costs from each supply point to top 50 cement/ready-mix clusters
8. Identify supply gaps — demand centers outside economical GGBFS distribution radius

### Phase 3: Market Intelligence
9. Entity resolution: Match steel mill operators → slag processors → cement consumers
10. Track EAF-to-BF ratio by company and facility — forward supply projection
11. Model GGBFS supply scenario: base case vs accelerated BF closures vs Gary Works maintained

### Phase 4: Integrated SCM Report
12. Combine fly ash + GGBFS + natural pozzolan + LC3 supply outlooks
13. Map total SCM supply vs cement industry demand by region
14. Identify regions most vulnerable to SCM shortage
15. Generate combined dossier: "US Supplementary Cementitious Materials Supply Outlook"

---

## CROSS-PROJECT REFERENCES

| Resource | Location | Relevance to Slag Module |
|----------|----------|--------------------------|
| Fly Ash Dossier | `project_flyash/FLY_ASH_COMPREHENSIVE_DOSSIER_v2.html` | Parallel SCM supply crisis; template format |
| Aggregates Dossier | `project_master_reporting/aggregate/` | Limestone → cement → GGBFS supply chain |
| Master Spec | `project_master_reporting/CLAUDE.md` | Architecture, data standards, phase roadmap |
| EPA FRS Tool | `task_epa_frs/` | Steel mill and cement facility registry |
| Rail Cost Model | `project_rail/` | Great Lakes mill distribution costing |
| Barge Cost Model | `project_barge/` | Waterway distribution from mill locations |
| Manifest Pipeline | `project_manifest/` | HTS 2618 import trade flow analysis |
| Cement Markets | `project_cement_markets/` | Demand-side context; competitive landscape |
| GIS Datasets | `sources_data_maps/` | Facility mapping, transport network overlay |

---

## KEY COMMODITY LINKAGES

This slag module connects to a chain of related commodity modules in the master reporting platform:

```
LIMESTONE QUARRY (aggregate module)
    ↓ crushed limestone
CEMENT PLANT (cement_markets module)
    + GGBFS (slag module) ← Import terminals ← Japan/China/Brazil
    + Fly Ash (flyash module) ← Coal plants (declining)
    + Natural Pozzolans (future module)
    ↓ blended cement
READY-MIX CONCRETE
    + Aggregates (aggregate module)
    ↓ delivered concrete
CONSTRUCTION SITE
```

---

## OPEN QUESTIONS FOR MASTER SESSION

1. **Module hierarchy**: Should slag be a standalone commodity module or a sub-module of cement? It's both a by-product (of steelmaking) and an input (to cement/concrete).
2. **SCM rollup report**: Should we create a combined "US SCM Supply Outlook" that merges fly ash + GGBFS + natural pozzolan + LC3 analysis?
3. **Import terminal deep-dive**: The Heidelberg Houston facility, Titan Norfolk dome, and Charah Greens Port operations warrant individual terminal profiles — build as part of slag module or port_cost_model?
4. **EAF slag research**: Should we track emerging research on processing EAF slag into viable SCMs? This could change the supply outlook long-term.
5. **Trade policy risk**: Chinese slag imports (23% share) face potential tariff escalation. Should we model tariff scenarios?

---

*Handoff prepared by Claude Code session, 2026-02-18. All files in `project_master_reporting/slag/` are ready for integration into the master reporting platform.*
