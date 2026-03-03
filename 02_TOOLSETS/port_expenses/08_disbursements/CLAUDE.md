# CLAUDE.md — Disbursements Sub-Module
**Module:** `02_TOOLSETS/port_expenses/08_disbursements/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a miscellaneous disbursements calculator with configurable line items. This is the catch-all category — items that don't fit elsewhere in the PDA.

---

## WHAT TO BUILD

### 1. Item Rate Data (`disbursement_items.parquet`)
Columns: `port | item_name | rate_usd | rate_basis | applies_to | source | year`

`applies_to`: international_arrivals | all_calls | optional | grain_cargo | etc.

### 2. Light Dues Schedule (`light_dues_schedule.csv`)
US light dues are federally set. Fetch from USCG or CBP published schedule.
Columns: `district | vessel_type | grt_min | grt_max | rate_per_grt | max_fee_usd`

### 3. Calculator (`src/disbursements_calculator.py`)
```python
def calculate_disbursements(
    port: str,
    vessel_grt: int,
    arriving_international: bool = True,
    cargo_type: str = "bulk",
    days_in_port: float = 2.0,
    fresh_water_needed: bool = False,
    fresh_water_tonnes: float = 0,
    overtime_hours: float = 0,
    custom_items: list[dict] = None,  # user-defined additional items
) -> dict:
    ...
```

### 4. Toggle Logic
- Light dues: triggered for international arrivals in US waters
- ISPS security fee: triggered for all port calls
- Garbage removal: triggered for calls > 1 day
- Fresh water: optional, user-specifies quantity
- Custom items: allow user to add any line item with description + amount

---

## DATA SOURCES

1. `09_user_notes/` — William's empirical disbursement observations
2. USCG/CBP light dues schedules (publicly available)
3. Port authority miscellaneous fee schedules

---

## ACCEPTANCE CRITERIA

- ISPS fee and light dues triggered automatically for international calls
- `custom_items` parameter allows arbitrary additions without code changes
- All items returned as separate fields AND as `disbursements_total`
