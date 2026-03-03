# CLAUDE.md — Port Expenses Toolset
**Toolset:** `02_TOOLSETS/port_expenses/`
**Parent project:** `CLAUDE.md` at project root (read that first for full platform context)
**Version:** 1.1.0 | Created: 2026-03-02 | Last Updated: 2026-03-02

---

## SESSION BRIEF

You are building the **Port Expenses Toolset** — a structured system for estimating, benchmarking, and validating the cost of a vessel port call at any US bulk commodity port.

The end deliverable is a **Proforma Disbursement Account (PDA)**: the standard maritime pre-arrival cost estimate used by shipowners, charterers, and operators to forecast port costs. A PDA is broken into 8 standard expense categories, each handled by its own sub-module.

William has 30+ years of maritime consulting experience. He knows the domain deeply. Translate his intent into working code without second-guessing domain logic.

---

## TOOLSET STRUCTURE

```
02_TOOLSETS/port_expenses/
├── CLAUDE.md                    ← THIS FILE
├── README.md                    ← Toolset overview
├── METHODOLOGY.md               ← Calculation methodology
├── config.yaml                  ← Tariff tables, port settings
├── 01_towage/                   ← Tug services
├── 02_pilotage/                 ← Pilot services
├── 03_terminals/                ← Stevedoring, wharfage, dockage
├── 04_officials/                ← Port authority, customs, immigration fees
├── 05_surveyors/                ← Marine/cargo surveyor fees
├── 06_launches/                 ← Launch/boat hire
├── 07_agents/                   ← Ship agency fees
├── 08_disbursements/            ← Miscellaneous sundry charges
├── 09_user_notes/               ← William's domain notes and reference data
└── 10_proforma_calculator/      ← Rolls up all categories into full PDA
```

Each sub-module has its own `CLAUDE.md` for focused build sessions.

---

## MODULE STATUS

| Module | Status | Notes |
|---|---|---|
| `01_towage` | ⏳ Scaffolded | Not yet built |
| `02_pilotage` | ⏳ Scaffolded | Not yet built |
| `03_terminals` | ⏳ Scaffolded | Not yet built |
| `04_officials` | ⏳ Scaffolded | Not yet built |
| `05_surveyors` | ⏳ Scaffolded | Not yet built |
| `06_launches` | ⏳ Scaffolded | Not yet built |
| `07_agents` | ⏳ Scaffolded | Not yet built |
| `08_disbursements` | ⏳ Scaffolded | Not yet built |
| `09_user_notes` | ⏳ Scaffolded | Populate as modules are built |
| `10_proforma_calculator` | ⏳ Scaffolded | Aggregate engine — build last |
| `11_hold_cleaning` | ✅ **OPERATIONAL v1.1.0** | PDA calculator, intelligence module, HoldIntel CLI, KB (50 sources), 55-transition matrix, vendor DB, HTML intelligence report. See `11_hold_cleaning/README.md`. |

## BUILD SEQUENCE

Build sub-modules in order — each feeds into `10_proforma_calculator`:

1. `01_towage` → rate calculator (LOA/GRT/HP basis, per tug, per move)
2. `02_pilotage` → regulated tariff lookup by port + vessel parameters
3. `03_terminals` → stevedoring rate × cargo tonnage + wharfage/dockage
4. `04_officials` → fixed visit fees per agency per port
5. `05_surveyors` → daily/per-survey rates, optional items
6. `06_launches` → per-trip or daily charter rates
7. `07_agents` → agency fee schedules (flat + percentage structures)
8. `08_disbursements` → catch-all with user-configurable line items
9. `09_user_notes` → populate with reference data as you build each module
10. `10_proforma_calculator` → aggregate engine + Excel/PDF output
11. `11_hold_cleaning` → ✅ DONE — wire into 10_proforma_calculator as optional line item

---

## TECHNICAL STANDARDS

Follow root `CLAUDE.md` tech standards:
- Python 3.11+, type hints, Click CLI
- DuckDB for tariff/rate data storage
- Parquet for intermediate data
- Output: Excel (openpyxl), JSON, optionally PDF

Input parameters for all calculators:
- `port` (string — US port name or UNLOCODE)
- `vessel_loa` (float — meters)
- `vessel_grt` (int — gross registered tons)
- `vessel_dwt` (int — deadweight tons)
- `commodity` (string — NAICS or commodity name)
- `cargo_tonnes` (float — short tons)
- `arrival_date` (ISO 8601 date)

---

## DATA SOURCES TO USE

- Port authority published tariff schedules (PDF/web — source manually)
- Pilot association published tariffs (NOBRA, Savannah, Tampa Bay, etc.)
- Tug operator rate cards (Moran, Bouchard, Seabulk, McAllister)
- AAPA port statistics for benchmark validation
- William's `09_user_notes/` for empirical adjustments

---

## INTEGRATION TARGETS

- CLI: `report-platform port-expenses --port "New Orleans" --vessel-loa 225 --grt 35000 --cargo-tonnes 50000`
- Feeds into: commodity module supply chain cost models
- Supersedes: `02_TOOLSETS/port_cost_model/` (legacy, to be merged/retired)
