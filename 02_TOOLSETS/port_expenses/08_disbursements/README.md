# 08 — Disbursements

**Sub-module:** `02_TOOLSETS/port_expenses/08_disbursements/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Captures miscellaneous port costs not covered by the named expense categories (01–07, 11). In maritime practice, "disbursements" also refers to the entire PDA document — here it means the sundry remainder line items.

## Common Disbursement Items

| Item | Basis | Notes |
|---|---|---|
| Fresh water supply | Per metric ton | Varies significantly by port |
| Garbage / waste removal | Fixed or per container | MARPOL regulated |
| Fumigation certificate | Fixed fee | Required for some cargoes/origins |
| Medical fees | Per incident | Crew medical ashore |
| Overtime charges | Per person per hour | Weekend/holiday port labor |
| Bank transfer charges | Fixed fee | For advance payments |
| Advance commission | % of advance | Agent's fee for advancing funds |
| Light dues | Per GRT per voyage | Federal levy in some districts |
| ISPS / port security fee | Fixed per call | International Ship and Port Security Code |
| Quarantine fees | Fixed | If vessel from restricted port |

## Data Files (to be created)

| File | Description |
|---|---|
| `disbursement_items.parquet` | Port × item rate table |
| `light_dues_schedule.csv` | US light dues by district |

## Notes

- This category is highly variable — William's empirical data in `09_user_notes/` is the primary calibration source
- Items can be toggled on/off per port call type (domestic vs. international, cargo type, season)

## Output Fields

```
disbursements_fresh_water       float (USD)
disbursements_garbage           float (USD)
disbursements_isps_fee          float (USD)
disbursements_light_dues        float (USD)
disbursements_overtime          float (USD)
disbursements_bank_charges      float (USD)
disbursements_other             float (USD)
disbursements_total             float (USD)
disbursements_basis             str
disbursements_source            str
disbursements_confidence        str
```
