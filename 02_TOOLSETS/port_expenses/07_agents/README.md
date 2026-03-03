# 07 — Agents

**Sub-module:** `02_TOOLSETS/port_expenses/07_agents/`
**Status:** Scaffolded | **Created:** 2026-03-02

---

## Purpose

Estimates ship agency (husbanding agent) fees and associated administrative costs. The agent is the vessel's local representative — arranging all port services, liaising with authorities, and managing disbursements on behalf of owners/operators.

## Fee Structure

Agency fees are typically quoted as one of:
- **Flat fee** by vessel GRT tier (most common in US ports)
- **Percentage of total disbursements** (less common, typical 2–5%)
- **Itemized:** Base fee + per-service charges

## Standard Services Included

| Service | Notes |
|---|---|
| Basic agency fee | Core husbanding service |
| Port clearance documentation | Arrival/departure paperwork |
| Crew documentation | Crew lists, crew visas, sign-on/off |
| Customs and immigration liaison | CBP coordination |
| Advance / guarantee to port authority | Float for disbursements |
| Communications | Phone, fax, courier (often itemized) |
| Pre-arrival / post-departure services | Vessel scheduling, berth bookings |

## Key US Bulk Port Agents (to populate)

- GAC Shipping (multiple US ports)
- Inchcape Shipping Services
- Wilhelmsen Ships Service
- Local independent agents (William's reference list)

## Data Files (to be created)

| File | Description |
|---|---|
| `agency_fees.parquet` | Port × GRT tier fee table |
| `agent_directory.csv` | Agent contact directory by port |

## Output Fields

```
agents_base_fee                 float (USD)
agents_documentation_fee        float (USD)
agents_communications_fee       float (USD)
agents_other_fees               float (USD)
agents_total                    float (USD)
agents_basis                    str
agents_source                   str
agents_confidence               str
```
