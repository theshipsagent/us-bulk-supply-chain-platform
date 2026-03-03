# 01 — Towage

**Sub-module:** `02_TOOLSETS/port_expenses/01_towage/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Calculates tug boat service costs for a vessel port call — docking, undocking, and any shifting moves within port limits.

## Calculation Basis

- **Rate driver:** Vessel LOA (primary), GRT (secondary)
- **Structure:** Fixed call-out fee per tug + variable per-move rate
- **Moves:** Minimum 2 (dock + undock); shifts add additional moves
- **Tug count:** Scales with LOA (see `config.yaml` defaults; port rules override)
- **Surcharges:** Night, weekend, public holiday premiums (typically 25–50%)

## Key Rate Sources (to populate)

- Port authority published tug tariffs
- Moran Towing, Seabulk Towing, McAllister Towing rate cards
- Bouchard Transportation (Gulf Coast)
- NOBRA-area tug operators (New Orleans/Baton Rouge)

## Data Files (to be created)

| File | Description |
|---|---|
| `towage_rates.parquet` | Port × vessel tier rate table |
| `tug_operators.csv` | Operator directory by port |
| `surcharge_schedules.json` | Night/weekend/holiday multipliers by port |

## Output Fields

```
towage_tugs_required    int
towage_moves            int
towage_rate_per_move    float (USD)
towage_call_out_fee     float (USD)
towage_surcharge        float (USD)
towage_total            float (USD)
towage_basis            str
towage_source           str
towage_confidence       str (high/medium/low)
```
