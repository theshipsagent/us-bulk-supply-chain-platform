# CLAUDE.md — Launches Sub-Module
**Module:** `02_TOOLSETS/port_expenses/06_launches/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a launch/boat hire cost calculator. Relatively small line item but always present — especially when vessel anchors before berthing.

---

## WHAT TO BUILD

### 1. Rate Data (`launch_rates.parquet`)
Columns: `port | service_type | rate_usd | rate_basis | night_surcharge_pct | source | year`

Service types: pilot_trip, officials_trip, crew_change_trip, stores_trip, daily_charter

### 2. Calculator (`src/launches_calculator.py`)
```python
def calculate_launches(
    port: str,
    at_anchor: bool = False,    # if True, more trips needed
    crew_change: bool = False,
    crew_change_count: int = 0,
    stores_delivery: bool = False,
    night_ops: bool = False,
) -> dict:
    ...
```

### 3. Logic Rules
- Pilot trips: always 2 (inbound at pilot station + outbound) if vessel goes to anchor
- Officials trips: bundled (1–2 trips) if vessel at anchor
- If vessel goes directly to berth: pilot boards at berth, launches reduced/eliminated
- Crew change: 1 trip per 5 crew members (van launch capacity ~5 persons)
- Night surcharge: 25–40% (port-specific)

---

## DATA SOURCES

1. `09_user_notes/` — William's launch rate benchmarks by port
2. Port authority published launch tariffs (where available)

---

## ACCEPTANCE CRITERIA

- Zero launch cost when vessel berthed directly (no anchor)
- Crew change trips scale correctly with crew count
- Night surcharges applied when `night_ops=True`
