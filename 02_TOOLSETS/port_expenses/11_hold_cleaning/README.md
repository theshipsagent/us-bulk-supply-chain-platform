# 11 — Hold Cleaning
**Sub-module:** `02_TOOLSETS/port_expenses/11_hold_cleaning/`
**Status:** Operational | **Version:** 1.1.0 | **Created:** 2026-03-02 | **Last Updated:** 2026-03-02

---

## Purpose

Estimates the cost of preparing vessel cargo holds before loading, including cleaning operations, fumigation, and mandatory USDA FGIS / NCB inspection. This is a required PDA line item whenever a vessel is transitioning between incompatible cargo types or loading any US grain export cargo.

Hold cleaning is often underestimated in quick PDAs but can be the largest single expense item — a Panamax transitioning from coal to grain may spend $40,000–$80,000 in cleaning, inspection, and lost off-hire time.

---

## Directory Structure

```
11_hold_cleaning/
├── CLAUDE.md                          ← Build session directives
├── README.md                          ← This file
├── METHODOLOGY.md                     ← Full calculation methodology
├── CLAUDE.md                          ← Build session directives
├── README.md                          ← This file
├── METHODOLOGY.md                     ← Full calculation methodology
├── knowledge_base/
│   └── hold_cleaning_kb.json          ← Master knowledge base (50+ authoritative sources; v1.1.0)
├── cli/
│   └── holdintel.py                   ← HoldIntel CLI (lookup, checklist, marpol, report, search)
├── src/
│   ├── hold_cleaning_calculator.py    ← PDA cost calculator (main module)
│   └── hold_cleaning_module.py        ← Full intelligence reporting module
├── data/
│   ├── hold_cleaning_rates.csv        ← Port × operation rate table (7 ports, crew + shore gang)
│   ├── cargo_compatibility_matrix.csv ← Previous → next cargo cleaning matrix (55 transitions)
│   ├── fgis_inspection_fees.csv       ← USDA FGIS / NCB regulated fee schedule (2024)
│   ├── vendors_us_gulf.csv            ← US Gulf hold cleaning vendor directory (12 entries)
│   ├── sources/                       ← Downloaded P&I circulars, USCG documents
│   ├── downloads/                     ← holdintel download output
│   └── cache/                         ← Download logs and cache
├── generate_intelligence_report.py    ← Generates hold_cleaning_intelligence_report.html
├── hold_cleaning_intelligence_report.html ← Comprehensive HTML intelligence briefing
├── sample_report.py                   ← Generates PDA cost scenario report (sample_report.html)
└── 09_user_notes/                     ← William's empirical port notes
```

---

## Quick Start

### PDA Calculator

```python
from src.hold_cleaning_calculator import calculate_hold_cleaning, format_pda_summary

# Coal → Grain transition, 7-hold Panamax, Hampton Roads
result = calculate_hold_cleaning(
    port="Hampton Roads",
    hold_count=7,
    commodity_loading="grain",
    previous_cargo="coal",
    vessel_dwt=75000,
)

print(format_pda_summary(result))
# → PDA line items: sweep, wash, FGIS/NCB, days lost, warnings
```

### HoldIntel CLI

```bash
# Look up cargo requirements
python cli/holdintel.py lookup --cargo "soda ash"
python cli/holdintel.py lookup --standard "grain clean"

# Generate cleaning checklist
python cli/holdintel.py checklist --cargo grain --previous-cargo coal --vessel-type panamax

# Full readiness report
python cli/holdintel.py report --cargo grain --previous coal --vessel-type panamax --port "Hampton Roads"

# MARPOL compliance check
python cli/holdintel.py marpol --cargo "soda ash" --position "36N 075W"

# List all authoritative sources
python cli/holdintel.py sources --type pi_club

# Download P&I circulars and USCG documents
python cli/holdintel.py download --source ukpi
python cli/holdintel.py download --source all

# Search knowledge base
python cli/holdintel.py search "loose rust scale grain"
```

### Intelligence Module

```python
from src.hold_cleaning_module import HoldCleaningModule

mod = HoldCleaningModule()

# Full cargo transition analysis
report = mod.cargo_transition_report(
    previous_cargo="coal",
    next_cargo="grain",
    vessel_type="Panamax",
    load_port="Hampton Roads, VA",
    ballast_days=3.5,
    vessel_dwt=75000,
)
print(report.text_summary())

# Get cleanliness standard for any cargo
info = mod.get_standard_for_cargo("soda ash")
# → {"required_standard": "hospital clean", "rank": 1, ...}

# MARPOL quick check
check = mod.marpol_quick_check("fertilizer", inside_special_area=False)
```

---

## Cleanliness Standards

| Rank | Standard | Required For |
|---|---|---|
| 1 | **Hospital Clean** | Soda ash, kaolin, mineral sands, rice, high-grade wood pulp |
| 2 | **Grain Clean** | All grains, soya, alumina, sulphur, cement, fertilizers |
| 3 | **Normal Clean** | General bulk (no CP specification) |
| 4 | **Shovel Clean** | Coal, iron ore, ores |
| 5 | **Load on Top** | Same commodity COA trades |

---

## Cargo Compatibility (Previous → Next) Risk Matrix

| Previous Cargo | Next Cargo | Risk | Chemical Wash | Days Lost |
|---|---|---|---|---|
| Grain | Grain | Low | No | 0.5 |
| Iron ore | Grain | Low | No | 1.0 |
| Coal | Grain | **High** | Yes | 2.5 |
| Petcoke | Grain | **High** | Yes | 3.0 |
| Cement | Grain | **High** | No (portable pump) | 2.0 |
| Sulphur | Grain | Medium | No (PPE critical) | 1.5 |
| Fertilizer | Grain | Medium | No | 1.5 |
| Fishmeal | Grain | **High** | Yes (enzymatic) | 2.5 |
| Coal | Soda ash | **Very High** | Yes + fresh water only | 3.5 |
| Petcoke | Soda ash | **Very High** | Yes + fresh water only | 4.0 |

Full matrix: `data/cargo_compatibility_matrix.csv`

---

## FGIS Mandatory Inspection (US Grain Exports)

All US grain export shipments require:
1. **USDA FGIS Stowage Examination** — vessel cleanliness certification ($417–$1,067 by DWT)
2. **NCB Grain Certificate of Readiness** — structure, bilges, stability ($750–$1,850 by DWT)
3. **USDA Per-Hold Cleanliness Certificates** — ($260/hold)
4. **Reinspection** reserve for high-risk previous cargoes (+$250)

Total FGIS/NCB burden for a Panamax (75,000 DWT): ~$4,000–$6,000 before cleaning costs.

Full fee schedule: `data/fgis_inspection_fees.csv`

---

## Output Fields (PDA Schema)

```
hold_cleaning_sweep             float (USD) — sweeping cost
hold_cleaning_wash              float (USD) — all washing operations
hold_cleaning_fumigation        float (USD) — fumigation if infestation
hold_cleaning_fgis_inspection   float (USD) — FGIS + NCB fees (grain)
hold_cleaning_days_lost         float (days) — vessel delay estimate
hold_cleaning_total             float (USD)
hold_cleaning_previous_cargo    str
hold_cleaning_risk_level        str (low/medium/high/very_high)
hold_cleaning_basis             str — parameters used
hold_cleaning_source            str — data file references
hold_cleaning_confidence        str (estimated/indicative)
hold_cleaning_warnings          list[str] — protocol warnings
hold_cleaning_operations        list[str] — line-by-line breakdown
hold_cleaning_regulatory_flags  list[str] — regulatory compliance checklist
```

---

## MARPOL Annex V Compliance

All wash water discharge is regulated under MARPOL Annex V (2013 amendment):
- **HME cargoes**: discharge PROHIBITED — port reception facility mandatory
- **Non-HME outside Special Areas**: vessel en route, min. 12nm from land
- **Gulf of Mexico / Caribbean**: MARPOL Special Area — stricter rules apply

The calculator flags MARPOL compliance requirements whenever chemical wash is applied.

---

## Data Sources

| File | Source |
|---|---|
| `hold_cleaning_rates.csv` | Industry benchmarks, William S. Davis III empirical rates (7 ports) |
| `cargo_compatibility_matrix.csv` | UK P&I Club, Skuld, Swedish Club, IMSBC Code, USDA FGIS, Isbester (55 transitions) |
| `fgis_inspection_fees.csv` | 7 CFR Part 800 / USDA FGIS / NCB tariff schedule (2024) |
| `vendors_us_gulf.csv` | Web research 2026 — US Gulf hold cleaning vendors by type (12 entries) |
| `knowledge_base/hold_cleaning_kb.json` | 50+ authoritative sources: P&I clubs, IMO, USCG, NCB, Wilhelmsen, Isbester, MARPOL 2022 |

**Full methodology:** See `METHODOLOGY.md`

---

## Session History

### Session 1 — 2026-03-02 (Initial Build)
- Scaffolded full module structure
- Built PDA calculator (`src/hold_cleaning_calculator.py`) and intelligence module (`src/hold_cleaning_module.py`)
- Built HoldIntel CLI (`cli/holdintel.py`) — lookup, checklist, marpol, report, search commands
- Populated rate tables (7 ports), compatibility matrix (51 initial transitions), FGIS fee schedule
- Built initial knowledge base v1.0.0 (45 sources): UK P&I, Skuld, Swedish Club, IMSBC, MARPOL, USDA FGIS, NCB

### Session 2 — 2026-03-02 (KB Cross-Reference + Intelligence Report)
- Read and cross-referenced 6 Zotero PDFs: Isbester *Bulk Carrier Practice* Ch.5, IMSBC Code (full), MARPOL 2022, Marine Cargo Operations, Carrying Solid Bulk Cargoes Safely, IMO CSS Code
- Updated KB to v1.1.0 (50 sources): added Isbester textbook, limewash recipe, copper concentrate CRITICAL warning, coal fine dual IMSBC classification, time benchmarks, 3 washing methods, port restriction warning, 24-item hold prep checklist
- Added 4 new rows to compatibility matrix (copper concentrate × 2, salt, coal_fine) → 55 transitions total
- Ran Supramax cargo pattern analysis: 41,156 USACE MRTIS voyage records → confirmed import pattern (steel/fertilizer/cement → grain export via Lower Mississippi grain elevators)
- Built US Gulf vendor database (`data/vendors_us_gulf.csv`) — 12 entries across shore gangs, shipyards, robotic, chemical suppliers
- Generated comprehensive HTML intelligence report (`hold_cleaning_intelligence_report.html`) — 12 sections, 109 KB
- Generated PDA cost scenario report (`sample_report.html`) — 10 scenarios, Supramax basis

### Next Session — Pending Work
- LinkedIn / vendor research: Arc Marine LLC (NOLA), Gulf Ship Services (George Stratikis profile found) — verify and add to vendor database
- Add cleaning material/chemical suppliers (specific US distributors, not just Drew/Wilhelmsen global)
- Add launch hire companies (separate vendor type, William to provide names)
- Verify "Intership" vendor — no US Gulf hold cleaning match found; may be a local subcontractor name
- Verify "Bertucci" scope of hold cleaning services (confirmed as Bertucci Contracting Co., Jefferson LA — primarily marine construction/dredging)
- Wire hold cleaning into `10_proforma_calculator/` PDA aggregate engine
- CLI integration: `report-platform port-expenses --include-hold-cleaning` flag
