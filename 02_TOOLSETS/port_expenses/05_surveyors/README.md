# 05 — Surveyors

**Sub-module:** `02_TOOLSETS/port_expenses/05_surveyors/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Estimates professional fees for marine and cargo surveyors attending the vessel during a port call. Survey costs depend on cargo type, charter party requirements, and the parties involved (owners, charterers, receivers, insurers).

## Survey Types

| Survey Type | Trigger | Typical Basis |
|---|---|---|
| Draft survey | Cargo quantity verification (load/discharge) | Per survey (in + out = 2) |
| Condition survey (hold) | Pre-load hold inspection | Per hold or per vessel |
| On-hire / off-hire survey | Charter party changeover | Per survey |
| Cargo damage survey | Claim investigation | Per survey + report |
| P&I correspondent attendance | Club representation | Daily rate |
| Classification society (ABS, Lloyd's, DNV) | Statutory or class survey | Per survey |
| Grain inspection (FGIS/USDA) | Federal grain sampling | Per shipment |

## Notes

- Draft surveys are routine for bulk cargoes — almost always included
- FGIS (Federal Grain Inspection Service) fees are federally regulated and non-negotiable for grain exports
- P&I club correspondents billed at daily rates; often optional
- Charter party may specify which party pays for which surveys

## Data Files (to be created)

| File | Description |
|---|---|
| `surveyor_rates.parquet` | Survey type × port rate table |
| `fgis_fee_schedule.csv` | FGIS regulated inspection fees |
| `classification_society_fees.csv` | ABS, Lloyd's, DNV fee schedules |

## Output Fields

```
surveyors_draft_survey          float (USD)
surveyors_condition_survey      float (USD)
surveyors_pi_attendance         float (USD)
surveyors_fgis_fees             float (USD)
surveyors_class_society_fees    float (USD)
surveyors_other                 float (USD)
surveyors_total                 float (USD)
surveyors_basis                 str
surveyors_source                str
surveyors_confidence            str
```
