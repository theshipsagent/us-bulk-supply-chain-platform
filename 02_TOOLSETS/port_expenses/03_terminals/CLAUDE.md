# CLAUDE.md — Terminals Sub-Module
**Module:** `02_TOOLSETS/port_expenses/03_terminals/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** OPERATIONAL — calculator + data files built | **Created:** 2026-03-02 | **Updated:** 2026-03-02

---

## SESSION OBJECTIVE

Build a terminal cost calculator covering stevedoring, wharfage, and dockage — the largest expense category in any bulk cargo PDA.

---

## WHAT TO BUILD

### 1. Rate Data (`terminal_rates.parquet`)
Columns: `port | terminal_name | commodity | stevedoring_per_st | wharfage_per_st | dockage_basis | dockage_rate | source | year`

Seed with benchmark rates for major bulk terminals at:
- New Orleans / Baton Rouge (grain elevators: ADM, Bunge, Louis Dreyfus, Cargill)
- Houston (bulk terminals)
- Savannah, Baltimore, Norfolk, Tampa, Mobile

### 2. Terminal Directory (`terminal_directory.csv`)
Columns: `port | terminal_name | operator | commodities_handled | latitude | longitude | max_vessel_loa | max_vessel_dwt`

Cross-reference with `02_TOOLSETS/facility_registry/` for existing terminal data.

### 3. Calculator (`src/terminal_calculator.py`)
```python
def calculate_terminal_costs(
    port: str,
    commodity: str,
    cargo_tonnes: float,        # short tons
    days_in_berth: float = 2.0,
    vessel_loa: float = None,
    vessel_grt: int = None,
    terminal_name: str = None,  # optional — use port default if None
) -> dict:
    ...
```

---

## DATA SOURCES

1. `09_user_notes/` — William's empirical stevedoring rate benchmarks (primary calibration)
2. Port authority published wharfage schedules
3. AAPA port statistics for benchmark validation
4. Individual terminal published tariffs (where available publicly)

---

## ACCEPTANCE CRITERIA

- Returns stevedoring, wharfage, dockage as separate line items
- Commodity-specific rates applied correctly
- Falls back to port-level benchmark when terminal-specific rate not available
- `confidence: high` for published tariff, `medium` for benchmark, `low` for estimate
