# 02 — Pilotage Sub-Module

**Sub-module:** `02_TOOLSETS/port_expenses/02_pilotage/`
**Status:** Active Build — Data Collection Phase | **Created:** 2026-03-02 | **Updated:** 2026-03-02

---

## Purpose

Calculates compulsory pilotage costs for inbound and outbound vessel movements at US ports.
Pilotage is legally compulsory for most foreign-flagged vessels at US ports. Rates are set by
state pilotage commissions, approved by legislature, and published as regulated tariff schedules.

This module provides:
- Rate lookup by port + vessel GRT tier
- Mississippi River segment logic (NOBRA multi-segment billing)
- Multi-movement support (arrival, departure, shifting)
- Confidence flagging (published tariff vs. benchmark estimate)

---

## Calculation Basis

| Parameter | Notes |
|---|---|
| Primary rate driver | GRT (Gross Registered Tons) — most associations |
| Secondary driver | LOA (Length Overall) — some Gulf associations |
| Movements | 2 per standard port call (arrival + departure) |
| River transits | Billed per segment or per river mile (Mississippi) |
| Rate authority | State pilotage commission — rates are regulated/mandatory |

---

## Priority Pilot Associations

### Gulf Coast
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| NOBRA | New Orleans, Baton Rouge, Head of Passes | GRT + river segment | Target |
| Houston Pilots | Houston Ship Channel, Galveston | GRT | Target |
| Sabine Pilots | Port Arthur, Beaumont, Orange | GRT | Target |
| Galveston-Texas City Pilots | Galveston, Texas City | GRT | Target |
| Corpus Christi Pilots | Corpus Christi | GRT | Target |
| Port of Lake Charles Pilots | Lake Charles | GRT | Target |
| Mobile Bar Pilots | Mobile | GRT | Target |
| Panama City Pilots | Panama City FL | GRT | Target |

### East Coast — South
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| Tampa Bay Pilots | Tampa | GRT | Target |
| Port Canaveral Pilots | Port Canaveral | GRT | Target |
| Jacksonville Pilots | Jacksonville (JAXPORT) | GRT | Target |
| Savannah Bar Pilots | Savannah | GRT | Target |
| Charleston Pilots | Charleston | GRT | Target |
| Wilmington Pilots (NC) | Wilmington NC | GRT | Target |
| Cape Fear Pilots | Morehead City NC | GRT | Target |

### East Coast — Mid-Atlantic
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| Virginia Pilots | Norfolk, Hampton Roads, Richmond | GRT | Target |
| Maryland Pilots | Baltimore | GRT | Target |
| Chesapeake Bay Pilots | Chesapeake Bay transits | GRT | Target |
| Delaware Bay & River Pilots | Philadelphia, Wilmington DE | GRT | Target |

### East Coast — Northeast
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| New York & New Jersey Pilots | New York harbor, Newark | GRT | Target |
| Boston Pilots | Boston, Mystic | GRT | Target |
| Portland Pilots | Portland ME | GRT | Target |
| Providence & Bristol Pilots | Providence RI | GRT | Target |

### Pacific Coast
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| Puget Sound Pilots | Seattle, Tacoma, Olympia | GRT | Target |
| Columbia River Pilots | Portland OR, Longview | GRT | Target |
| San Francisco Bar Pilots | San Francisco Bay, Richmond, Stockton | GRT | Target |
| Los Angeles Pilots | Los Angeles, Long Beach | GRT | Target |
| San Diego Pilots | San Diego | GRT | Target |

### Great Lakes
| Association | Ports Covered | Rate Basis | Status |
|---|---|---|---|
| Great Lakes Pilotage | All GL ports (federal — USCG regulated) | GRT + district | Target |

---

## Mississippi River Special Logic

NOBRA bills the Lower Mississippi in named segments, each with its own rate:

| Segment | From | To | Billing |
|---|---|---|---|
| Passes | Head of Passes | Pilots Station | Per GRT (entry) |
| Lower River | Pilots Station | New Orleans | Per GRT |
| Upper River | New Orleans | Baton Rouge | Per GRT (per 100 GRT, per mile or segment) |
| Tributaries | New Orleans | Other bayou/river destinations | Per GRT + location surcharge |

Implementation: segment lookup table keyed to `(origin_zone, destination_zone)`.

---

## Data Files

| File | Description | Status |
|---|---|---|
| `data/pilot_associations.json` | Master directory — name, ports, URL, rate basis, contact | Building |
| `data/pilotage_tariffs.parquet` | Port × GRT tier rate table | Pending |
| `data/river_segments.json` | Mississippi segment rate structure | Pending |
| `data/raw_tariffs/` | Downloaded PDFs and HTML source pages | Collecting |
| `src/pilotage_calculator.py` | Calculator engine | Pending |

---

## Calculator Interface

```python
from pilotage_calculator import calculate_pilotage

result = calculate_pilotage(
    port="New Orleans",
    vessel_grt=35000,
    vessel_loa=225.0,
    movements=2,            # inbound + outbound
    river_miles=0.0,        # Mississippi river transit miles (NOBRA only)
)

# Returns:
{
    "pilotage_movements": 2,
    "pilotage_rate_per_movement": 8540.00,
    "pilotage_river_surcharge": 0.00,
    "pilotage_total": 17080.00,
    "pilotage_basis": "GRT — NOBRA tariff schedule 2024",
    "pilotage_source": "nobra.com",
    "pilotage_confidence": "high"
}
```

---

## Output Fields

| Field | Type | Description |
|---|---|---|
| `pilotage_movements` | int | Number of movements billed |
| `pilotage_rate_per_movement` | float USD | Rate applied per movement |
| `pilotage_river_surcharge` | float USD | Mississippi/river segment surcharge |
| `pilotage_total` | float USD | Total pilotage cost |
| `pilotage_basis` | str | Rate tier description |
| `pilotage_source` | str | Source URL or document |
| `pilotage_confidence` | str | `high` / `medium` / `estimate` |

---

## Build Phases

- [x] Phase 1 — Module scaffolded, CLAUDE.md, README.md
- [ ] Phase 2 — Web research: collect tariff schedules from all target associations
- [ ] Phase 3 — Parse and normalize tariffs into `pilotage_tariffs.parquet`
- [ ] Phase 4 — Build `pilotage_calculator.py` with full port coverage
- [ ] Phase 5 — Mississippi river segment logic (NOBRA)
- [ ] Phase 6 — CLI integration into `report-platform port-expenses`
- [ ] Phase 7 — Validation against William's empirical benchmarks

---

## Integration

- Feeds into: `10_proforma_calculator/` (line item in PDA)
- CLI: `report-platform port-expenses --port "New Orleans" --grt 35000 --loa 225`
- Supersedes: pilotage stub in `02_TOOLSETS/port_cost_model/`
