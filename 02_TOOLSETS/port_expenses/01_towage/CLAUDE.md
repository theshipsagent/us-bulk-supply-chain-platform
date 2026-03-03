# CLAUDE.md — Towage Sub-Module
**Module:** `02_TOOLSETS/port_expenses/01_towage/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a tug cost calculator that returns the estimated towage cost for a vessel port call given vessel parameters and port.

---

## WHAT TO BUILD

### 1. Rate Data (`towage_rates.parquet`)
Populate a rate table with columns:
`port | vessel_loa_min | vessel_loa_max | tugs_required | rate_per_move_usd | callout_fee_usd | night_surcharge_pct | weekend_surcharge_pct | source | year`

Seed with benchmark data for: New Orleans, Baton Rouge, Houston, Savannah, Baltimore, Norfolk, Tampa, Mobile.

### 2. Calculator (`src/towage_calculator.py`)
```python
def calculate_towage(
    port: str,
    vessel_loa: float,
    vessel_grt: int,
    moves: int = 2,          # dock + undock
    night_ops: bool = False,
    weekend: bool = False,
) -> dict:
    ...
```

Returns dict with all output fields defined in `README.md`.

### 3. CLI hook
Wire into parent proforma calculator — no standalone CLI needed for this sub-module.

---

## DATA SOURCES TO CHECK

1. `09_user_notes/` — William's empirical towage rate benchmarks (check first)
2. Port authority websites for published tug tariffs
3. Tug operator rate cards: Moran, Seabulk, McAllister, Bouchard

---

## ACCEPTANCE CRITERIA

- Returns correct tug count for LOA inputs per `config.yaml` defaults
- Applies night/weekend surcharge correctly
- Returns `confidence: high` when tariff sourced, `medium` for benchmarks
- All output fields populated (no nulls in total)
