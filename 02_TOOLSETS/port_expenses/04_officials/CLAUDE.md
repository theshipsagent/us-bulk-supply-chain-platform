# CLAUDE.md — Officials Sub-Module
**Module:** `02_TOOLSETS/port_expenses/04_officials/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a government officials fee calculator — fixed boarding fees charged by federal and port agencies on vessel arrival and departure.

---

## WHAT TO BUILD

### 1. Fee Data (`officials_fees.parquet`)
Columns: `port | agency | fee_usd | trigger | night_surcharge_pct | source | year`

Agencies: CBP, USCG, APHIS, Port Health, Immigration (CBP-IMM), Fumigation authority

### 2. Calculator (`src/officials_calculator.py`)
```python
def calculate_officials(
    port: str,
    vessel_flag: str,           # ISO flag state — determines international vs. domestic
    commodity: str,             # triggers APHIS if agricultural
    crew_count: int = 25,
    arriving_international: bool = True,
    night_arrival: bool = False,
) -> dict:
    ...
```

### 3. Logic Rules
- CBP + Immigration: triggered for all international arrivals (non-US flag or foreign port last call)
- APHIS: triggered when commodity is grain, feed, or any agricultural product
- USCG: triggered probabilistically (spot inspections) — use port-specific inspection rate
- Port Health: triggered on international arrivals from restricted ports (build toggle)

---

## DATA SOURCES

1. CBP published boarding fees (Title 19 CFR)
2. USDA APHIS inspection fee schedules (publicly published)
3. `09_user_notes/` — William's port-specific fee observations

---

## ACCEPTANCE CRITERIA

- Correct agency fees triggered based on vessel flag and commodity
- Night surcharges applied correctly
- APHIS fee included automatically for grain/agricultural cargoes
- Clear itemization — each agency as separate output field
