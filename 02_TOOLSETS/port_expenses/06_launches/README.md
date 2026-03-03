# 06 — Launches

**Sub-module:** `02_TOOLSETS/port_expenses/06_launches/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Estimates launch and boat hire costs — the chartered small vessels used to transport personnel, supplies, and equipment between shore and the ship, particularly when the vessel is at anchor or in a roadstead.

## Use Cases

| Purpose | Notes |
|---|---|
| Pilot boarding/disembarking | Inbound + outbound at pilot station |
| Official boarding | CBP, USCG, APHIS, health officers |
| Crew change | Joining/signing-off crew at anchorage |
| Ship's stores delivery | Provisions, spare parts, lubricants |
| Cargo samples | Delivering pre-load samples to vessel |
| Mooring ropes at anchorage | Mooring buoy operations |
| Survey attendance | Getting surveyors aboard at anchorage |

## Rate Structure

- **Per trip:** Single transit shore-to-ship (most common for officials/pilot)
- **Daily charter:** Full day hire for vessel on standby (crew change operations)
- **Night/weekend surcharge:** 25–50% premium common

## Data Files (to be created)

| File | Description |
|---|---|
| `launch_rates.parquet` | Port × service type rate table |
| `launch_operators.csv` | Operator directory by port |

## Output Fields

```
launches_pilot_trips            int
launches_official_trips         int
launches_crew_change_trips      int
launches_stores_trips           int
launches_rate_per_trip          float (USD)
launches_surcharges             float (USD)
launches_total                  float (USD)
launches_basis                  str
launches_source                 str
launches_confidence             str
```
