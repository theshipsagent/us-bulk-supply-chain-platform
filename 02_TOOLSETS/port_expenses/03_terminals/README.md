# 03 — Terminals

**Sub-module:** `02_TOOLSETS/port_expenses/03_terminals/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Calculates cargo handling and berth-related charges at the terminal — typically the largest line item in any bulk cargo PDA.

## Sub-Components

| Component | Basis | Notes |
|---|---|---|
| Stevedoring | Per short ton of cargo | Labor + equipment; varies by commodity |
| Wharfage | Per short ton crossing wharf | Port authority levy |
| Dockage | Per LOA-ft per day or GRT/day | Berth rental |
| Terminal Handling (THC) | Bundled per-ton rate | Some terminals quote all-in |

## Commodity-Specific Rates

| Commodity | Typical Range ($/ST) |
|---|---|
| Grain (wheat, corn, soybeans) | $4–8 |
| Fertilizers (bulk) | $6–12 |
| Cement (bulk) | $8–15 |
| Coal | $4–7 |
| Steel products | $15–40 |

## Data Files (to be created)

| File | Description |
|---|---|
| `terminal_rates.parquet` | Port × commodity × component rate table |
| `terminal_directory.csv` | Terminal facilities by port, operator, commodities handled |
| `dockage_schedules.json` | Dockage rate tables by port |

## Output Fields

```
terminal_stevedoring_per_ton    float (USD)
terminal_stevedoring_total      float (USD)
terminal_wharfage_per_ton       float (USD)
terminal_wharfage_total         float (USD)
terminal_dockage_days           float
terminal_dockage_total          float (USD)
terminal_total                  float (USD)
terminal_basis                  str
terminal_source                 str
terminal_confidence             str
```
