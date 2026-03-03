# 10 — Proforma Calculator

**Sub-module:** `02_TOOLSETS/port_expenses/10_proforma_calculator/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

The Proforma Calculator is the capstone of the port_expenses toolset. It accepts vessel and cargo parameters, calls each sub-module calculator, and produces a complete **Proforma Disbursement Account (PDA)** — the standard maritime pre-arrival cost document.

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `port` | str | US port name or UNLOCODE |
| `vessel_name` | str | Vessel name (optional) |
| `vessel_type` | str | bulk_carrier, tanker, general_cargo |
| `vessel_loa` | float | Length overall (meters) |
| `vessel_grt` | int | Gross registered tons |
| `vessel_dwt` | int | Deadweight tons |
| `vessel_flag` | str | ISO flag state code |
| `commodity` | str | Cargo commodity name or NAICS |
| `cargo_tonnes` | float | Cargo quantity (short tons) |
| `arrival_date` | str | ISO 8601 expected arrival |
| `operations` | list | [load, discharge, both] |
| `at_anchor` | bool | Whether vessel anchors before berth |
| `crew_change` | bool | Whether crew change planned |

## Outputs

### Standard PDA Format

```
================================================
         PROFORMA DISBURSEMENT ACCOUNT
================================================
PORT:         New Orleans, LA (USMSY)
VESSEL:       MV Example / Bulk Carrier
              LOA: 225m | GRT: 38,500 | DWT: 63,000
COMMODITY:    Grain (Soybeans) — 55,000 ST
ARRIVAL:      2026-04-15 (estimated)
PREPARED BY:  William S. Davis III
DATE:         2026-03-02
================================================

01  TOWAGE                         $  28,400
02  PILOTAGE                       $  12,800
03  TERMINALS / STEVEDORING        $ 385,000
04  OFFICIALS                      $   4,200
05  SURVEYORS                      $   6,500
06  LAUNCHES                       $   3,800
07  AGENTS                         $   8,500
08  DISBURSEMENTS (MISC)           $   5,200
11  HOLD CLEANING                  $  18,000
------------------------------------------------
    TOTAL ESTIMATED PORT COST      $ 472,400
================================================
All figures in USD. Estimates based on published
tariffs and benchmark rates. Subject to revision
upon confirmed vessel nomination.
================================================
```

## Output Formats

- `dict` — machine-readable, for pipeline integration
- `DataFrame` — tabular, for further analysis
- `Excel (.xlsx)` — formatted PDA for client delivery
- `JSON` — API response format

## Multi-Port Comparison

The calculator supports running the same vessel/cargo spec across multiple ports to identify the least-cost port option — a standard analysis in bulk commodity sourcing decisions.

## Data Files (to be created)

| File | Description |
|---|---|
| `src/proforma.py` | Main PDA aggregation class |
| `src/port_resolver.py` | Resolves port name to config + sub-module params |
| `templates/pda_excel.xlsx` | Excel output template |
| `templates/pda_text.jinja2` | Text/PDF output template |
