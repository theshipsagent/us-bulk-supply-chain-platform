# CLAUDE.md — Proforma Calculator Sub-Module
**Module:** `02_TOOLSETS/port_expenses/10_proforma_calculator/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — build LAST (depends on 01–09, 11) | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build the aggregation engine that combines all sub-module calculators into a complete Proforma Disbursement Account (PDA). This is the capstone of the port_expenses toolset.

**Build this sub-module AFTER all others are operational.**

---

## WHAT TO BUILD

### 1. Core Class (`src/proforma.py`)

```python
class ProformaCalculator:
    def __init__(self, port, vessel_loa, vessel_grt, vessel_dwt,
                 commodity, cargo_tonnes, arrival_date, **kwargs):
        ...

    def estimate(self) -> dict:
        """Run all sub-module calculators, return full PDA dict."""
        ...

    def to_dataframe(self) -> pd.DataFrame:
        """Itemized PDA as DataFrame."""
        ...

    def to_excel(self, filepath: str) -> None:
        """Write formatted PDA to Excel using template."""
        ...

    def to_text(self) -> str:
        """Return formatted PDA as plain text."""
        ...

    def compare_ports(self, ports: list[str]) -> pd.DataFrame:
        """Run same spec across multiple ports — least-cost analysis."""
        ...
```

### 2. Port Resolver (`src/port_resolver.py`)
Translates port name or UNLOCODE → config parameters for each sub-module.

### 3. Excel Template (`templates/pda_excel.xlsx`)
Formatted PDA template with:
- Header block (port, vessel, cargo, date, prepared by)
- Line items by category (01–11)
- Totals row
- Confidence flags column
- Source citations column
- Notes section

### 4. CLI Integration
```bash
report-platform port-expenses \
  --port "New Orleans" \
  --vessel-loa 225 \
  --vessel-grt 38500 \
  --vessel-dwt 63000 \
  --commodity grain \
  --cargo-tonnes 55000 \
  --output pda_output.xlsx
```

### 5. Multi-Port Comparison Output
```
PORT COST COMPARISON — Panamax Grain, 55,000 ST
================================================
Category          New Orleans    Houston    Savannah
------------------------------------------------
Towage              $28,400      $24,100     $19,800
Pilotage            $12,800      $10,500      $8,200
Terminals          $385,000     $368,000    $352,000
...
TOTAL              $472,400     $438,200    $416,000
================================================
```

---

## DEPENDENCIES

All of the following must be working before building this module:
- `01_towage/src/towage_calculator.py`
- `02_pilotage/src/pilotage_calculator.py`
- `03_terminals/src/terminal_calculator.py`
- `04_officials/src/officials_calculator.py`
- `05_surveyors/src/surveyors_calculator.py`
- `06_launches/src/launches_calculator.py`
- `07_agents/src/agents_calculator.py`
- `08_disbursements/src/disbursements_calculator.py`
- `11_hold_cleaning/src/hold_cleaning_calculator.py`

---

## ACCEPTANCE CRITERIA

- All 11 expense categories represented in output
- Excel output matches PDA template format
- Multi-port comparison works for 2+ ports in single call
- CLI command functional end-to-end
- Confidence flags propagated from sub-modules to summary
