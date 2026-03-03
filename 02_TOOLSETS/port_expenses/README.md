# Port Expenses Toolset

**Toolset:** `02_TOOLSETS/port_expenses/`
**Owner:** William S. Davis III
**Status:** Scaffolded — sub-modules under active development
**Last Updated:** 2026-03-02

---

## Purpose

Estimates, benchmarks, and validates port call costs for bulk commodity vessels across US ports. Produces a **Proforma Disbursement Account (PDA)** — the standard maritime pre-arrival cost estimate — broken down by expense category.

Applies to any commodity and any vessel size. Designed to feed into:
- `barge_cost_model` (inland leg costs)
- `port_cost_model` (legacy calculator, to be superseded or merged)
- Commodity module supply chain cost analyses

---

## Sub-Modules

| # | Sub-Module | Description | Status |
|---|---|---|---|
| 01 | `01_towage/` | Tug services — docking, undocking, shifting; rates by LOA/GRT/HP | Scaffolded |
| 02 | `02_pilotage/` | Compulsory and voluntary pilotage; regulated tariff schedules by port | Scaffolded |
| 03 | `03_terminals/` | Stevedoring, wharfage, dockage, terminal handling charges | Scaffolded |
| 04 | `04_officials/` | Port authority, customs, immigration, health/quarantine visit fees | Scaffolded |
| 05 | `05_surveyors/` | Marine and cargo surveyors, classification society attendance fees | Scaffolded |
| 06 | `06_launches/` | Launch/boat hire for crew change, officials, cargo samples | Scaffolded |
| 07 | `07_agents/` | Ship agency/husbanding fees, communications, correspondence | Scaffolded |
| 08 | `08_disbursements/` | Miscellaneous sundry charges not captured in above categories | Scaffolded |
| 09 | `09_user_notes/` | William's domain notes, reference tariffs, port-specific intelligence | Active |
| 10 | `10_proforma_calculator/` | Rolls up all categories into a full PDA output | Scaffolded |
| 11 | `11_hold_cleaning/` | Hold cleaning, fumigation, FGIS inspection — pre-load preparation costs | Scaffolded |

---

## Data Sources

- Port authority tariff schedules (collected manually per port)
- US Coast Pilot, NOAA port guides
- AAPA (American Association of Port Authorities) port statistics
- Pilot association published tariffs (e.g., NOBRA, Savannah Bar Pilots)
- Tug operator rate cards (Moran, Bouchard, Seabulk, etc.)
- Agent fee benchmarks from William's consulting experience

---

## Output Format

Primary output: **Proforma Disbursement Account (PDA)**

```
PORT: [Port Name]               VESSEL: [Name / Type / LOA / GRT / DWT]
DATE: [Expected arrival]        COMMODITY: [Cargo / Qty]

ITEM                            ESTIMATED COST (USD)
------------------------------------------------------
01  Towage                      $XX,XXX
02  Pilotage                    $X,XXX
03  Terminal / Stevedoring      $XXX,XXX
04  Officials                   $X,XXX
05  Surveyors                   $X,XXX
06  Launches                    $X,XXX
07  Agency Fees                 $X,XXX
08  Disbursements (misc)        $X,XXX
11  Hold Cleaning               $X,XXX
------------------------------------------------------
    TOTAL ESTIMATED PORT COST   $XXX,XXX
```

---

## Integration

```python
from port_expenses import ProformaCalculator

pda = ProformaCalculator(
    port="New Orleans",
    vessel_loa=225,        # meters
    vessel_grt=35000,
    vessel_dwt=58000,
    commodity="grain",
    cargo_tonnes=50000,
    arrival_date="2026-04-15"
)

pda.estimate()
pda.to_dict()
pda.to_excel("pda_new_orleans_20260415.xlsx")
```

---

## Related Toolsets

- `02_TOOLSETS/port_cost_model/` — legacy port cost calculator (to be merged/superseded)
- `02_TOOLSETS/barge_cost_model/` — inland waterway leg costs
- `02_TOOLSETS/vessel_voyage_analysis/` — voyage cost context
