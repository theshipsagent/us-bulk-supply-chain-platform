# CLAUDE.md — Hold Cleaning Sub-Module
**Module:** `02_TOOLSETS/port_expenses/11_hold_cleaning/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a hold cleaning cost calculator that estimates the cost to prepare vessel cargo holds before loading, including cleaning operations, fumigation, and mandatory FGIS inspection for grain cargoes.

---

## WHAT TO BUILD

### 1. Rate Data (`hold_cleaning_rates.parquet`)
Columns: `port | operation | rate_usd | rate_basis | source | year`

Operations: sweep_per_hold, wash_saltwater_per_hold, wash_freshwater_per_hold, fumigation_per_hold, scale_removal_per_hold

### 2. Cargo Compatibility Matrix (`cargo_compatibility_matrix.csv`)
Columns: `previous_cargo | cleaning_requirement | risk_level | fgis_concern | notes`

This is the key intelligence table — what cleaning is needed based on what was previously carried.

Key entries:
- grain → grain: sweep only, low risk
- fertilizer → grain: thorough wash + fumigation, high risk, FGIS concern
- coal/petcoke → grain: thorough wash + possible rejection, very high risk
- cement → grain: wash, medium risk, dust residue
- sulfur → grain: very high risk, chemical contamination concern
- steel → grain: sweep only, low risk

### 3. FGIS Inspection Fees (`fgis_inspection_fees.csv`)
Federally regulated. Obtain from USDA FGIS published fee schedule.
Columns: `service | vessel_size | fee_usd | notes`

### 4. Calculator (`src/hold_cleaning_calculator.py`)
```python
def calculate_hold_cleaning(
    port: str,
    hold_count: int,
    commodity_loading: str,       # what is being loaded
    previous_cargo: str = None,   # what vessel previously carried
    vessel_grt: int = None,
    include_fgis_inspection: bool = None,  # auto-detect from commodity
) -> dict:
    ...
```

### 5. Logic Rules
- Auto-detect FGIS inspection requirement when `commodity_loading` is grain
- Cleaning requirement auto-populated from `cargo_compatibility_matrix`
- If `previous_cargo` is None: assume same commodity, minimum cleaning
- Flag high-risk previous cargo combinations with a warning in output
- Include `days_lost` estimate for severe cleaning situations (vessel delay risk)

---

## DATA SOURCES

1. USDA FGIS published inspection fee schedule
2. `09_user_notes/` — William's empirical hold cleaning cost benchmarks
3. Port authority / ship chandler cleaning rate schedules

---

## ACCEPTANCE CRITERIA

- FGIS inspection fee auto-triggered for grain loading
- Cargo compatibility matrix correctly determines cleaning operations required
- `risk_level` and warning flags returned in output for incompatible previous cargoes
- `hold_cleaning_days_lost` populated when cleaning estimated to exceed 12 hours
