# CLAUDE.md — Surveyors Sub-Module
**Module:** `02_TOOLSETS/port_expenses/05_surveyors/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a surveyor fee calculator. Survey requirements depend on cargo type, charter party terms, and the parties involved (owners, charterers, receivers, P&I clubs).

---

## WHAT TO BUILD

### 1. Rate Data (`surveyor_rates.parquet`)
Columns: `port | survey_type | rate_usd | rate_basis | source | year`

Survey types: draft_survey, condition_survey, on_hire, pi_attendance, class_society, fgis

### 2. FGIS Fee Schedule (`fgis_fee_schedule.csv`)
Federally regulated — obtain from USDA FGIS published schedule.
Columns: `service | quantity_min_bu | quantity_max_bu | fee_usd | fee_per_cwt`

### 3. Calculator (`src/surveyors_calculator.py`)
```python
def calculate_surveyors(
    port: str,
    commodity: str,
    cargo_tonnes: float,
    operations: list,           # ['load', 'discharge']
    include_draft_survey: bool = True,
    include_pi_attendance: bool = False,
    include_class_survey: bool = False,
    charter_party_type: str = "voyage",
) -> dict:
    ...
```

### 4. Logic Rules
- Draft survey: always included for bulk cargoes (2 surveys for load = before + after)
- FGIS inspection: triggered automatically for grain (wheat, corn, soybeans, sorghum)
- P&I attendance: optional toggle, billed at daily rate

---

## DATA SOURCES

1. USDA FGIS published fee schedule (federally regulated, publicly available)
2. `09_user_notes/` — William's surveyor rate benchmarks by port
3. ABS, Lloyd's, DNV published fee schedules

---

## ACCEPTANCE CRITERIA

- FGIS fees correctly calculated from federal schedule for grain tonnage
- Draft surveys included by default, correctly counted per operation
- All survey types as separate line items in output
