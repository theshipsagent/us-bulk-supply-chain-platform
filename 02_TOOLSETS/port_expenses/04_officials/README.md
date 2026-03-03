# 04 — Officials

**Sub-module:** `02_TOOLSETS/port_expenses/04_officials/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Calculates fees charged for mandatory government and port authority boarding visits on arrival and departure.

## Agencies and Fees

| Agency | Abbreviation | Trigger | Basis |
|---|---|---|---|
| US Customs & Border Protection | CBP | All international arrivals | Fixed visit fee |
| US Coast Guard | USCG | Safety inspection (spot or scheduled) | Fixed fee |
| USDA APHIS | APHIS | Grain/agricultural cargo | Fixed fee |
| Port Health Authority | PHA | Vessel arriving from foreign port | Fixed fee |
| Immigration (crew documentation) | CBP-IMM | All international arrivals | Per crew member or fixed |
| Fumigation authority | — | Required for certain cargoes/origins | Variable |

## Notes

- Fees are largely fixed and port-specific
- Some ports bundle CBP + immigration into a single fee
- APHIS inspection is mandatory for grain imports; can also apply to vessel holds
- Night/weekend boarding surcharges apply at some ports

## Data Files (to be created)

| File | Description |
|---|---|
| `officials_fees.parquet` | Port × agency fee table |
| `agency_directory.csv` | Agency contacts by port |

## Output Fields

```
officials_cbp_fee           float (USD)
officials_uscg_fee          float (USD)
officials_aphis_fee         float (USD)
officials_health_fee        float (USD)
officials_immigration_fee   float (USD)
officials_other_fees        float (USD)
officials_total             float (USD)
officials_basis             str
officials_source            str
officials_confidence        str
```
