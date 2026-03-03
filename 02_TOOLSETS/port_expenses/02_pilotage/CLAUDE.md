# CLAUDE.md — Pilotage Sub-Module
**Module:** `02_TOOLSETS/port_expenses/02_pilotage/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Phase 2 — Active Data Collection | **Created:** 2026-03-02 | **Updated:** 2026-03-02

---

## SESSION CONTEXT

You are building the **Pilotage cost calculator** — one of 8 sub-modules that roll up into the
Port Proforma Disbursement Account (PDA) calculator.

Pilotage is **legally compulsory** for most foreign-flagged cargo vessels at US ports. Rates are
set by state pilotage commissions, approved by state legislature, published as regulated tariff
schedules, and updated periodically (typically annually). They are **non-negotiable**.

William S. Davis III has 30+ years maritime consulting experience — trust his domain logic exactly.

---

## CURRENT PHASE: DATA COLLECTION

### What's been done
- Module scaffolded (CLAUDE.md, README.md)
- Web research agent launched to collect tariff schedules from all major US pilot associations
- Target: 25+ associations across Gulf, East Coast, Pacific, Great Lakes
- Output landing in: `data/pilot_associations_research.json`

### What to do next (this session or next)
1. Review `data/pilot_associations_research.json` — verify, fill gaps manually
2. Create `data/raw_tariffs/` — download PDFs from each association where tariff is a PDF
3. Parse tariff data into `data/pilotage_tariffs.parquet` (normalized GRT-tier table)
4. Build `src/pilotage_calculator.py` — rate lookup + NOBRA segment logic
5. Wire into CLI: `report-platform port-expenses --port "New Orleans" --grt 35000`

---

## WHAT TO BUILD

### File: `data/pilot_associations.json`
Master directory of all US pilot associations with tariff metadata.

```json
{
  "associations": [{
    "id": "nobra",
    "name": "New Orleans Bar Pilots (NOBRA)",
    "ports": ["New Orleans", "Baton Rouge"],
    "state": "LA",
    "coast": "Gulf",
    "website": "https://nobra.com",
    "tariff_url": "https://...",
    "rate_basis": "GRT",
    "tariff_year": "2024",
    "grt_tiers": [
      {"grt_min": 0, "grt_max": 5000, "rate_usd": 1200.00}
    ],
    "confidence": "high"
  }]
}
```

### File: `data/pilotage_tariffs.parquet`
Normalized flat table — one row per GRT tier per port per movement type.

Columns: `port | association_id | grt_min | grt_max | rate_usd | movement_type | surcharge_type | surcharge_usd | effective_date | source_url | confidence`

### File: `data/river_segments.json`
Mississippi River / NOBRA segment structure:

```json
{
  "nobra_segments": {
    "passes": {"from": "Head of Passes", "to": "Pilots Station", "rate_per_grt": 0.12},
    "lower_river": {"from": "Pilots Station", "to": "New Orleans", "rate_per_grt": 0.18},
    "upper_river": {"from": "New Orleans", "to": "Baton Rouge", "rate_per_grt": 0.22}
  }
}
```

### File: `src/pilotage_calculator.py`

```python
def calculate_pilotage(
    port: str,
    vessel_grt: int,
    vessel_loa: float,
    movements: int = 2,         # inbound + outbound (default)
    river_miles: float = 0.0,   # Mississippi only
) -> dict:
    """
    Returns pilotage cost estimate for a port call.
    Confidence: 'high' = published tariff, 'medium' = benchmark, 'estimate' = modeled.
    """
```

---

## PRIORITY PILOT ASSOCIATIONS

### Gulf Coast (highest priority — core bulk commodity ports)
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `nobra` | New Orleans Bar Pilots | New Orleans, Baton Rouge, Head of Passes | GRT + segment |
| `houston` | Houston Pilots | Houston Ship Channel | GRT |
| `sabine` | Sabine Pilots | Port Arthur, Beaumont, Orange | GRT |
| `galveston_tc` | Galveston-Texas City Pilots | Galveston, Texas City | GRT |
| `corpus_christi` | Corpus Christi Pilots | Corpus Christi | GRT |
| `lake_charles` | Lake Charles Pilots | Lake Charles | GRT |
| `mobile` | Mobile Bay Pilots | Mobile | GRT |

### Southeast
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `tampa_bay` | Tampa Bay Pilots | Tampa | GRT |
| `savannah` | Savannah Bar Pilots | Savannah | GRT |
| `charleston` | Charleston Pilots | Charleston | GRT |
| `jacksonville` | Jacksonville Pilots | Jacksonville | GRT |
| `wilmington_nc` | Wilmington NC Pilots | Wilmington NC | GRT |

### Mid-Atlantic
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `virginia` | Virginia Pilots | Norfolk/Hampton Roads | GRT |
| `maryland` | Maryland Pilots | Baltimore | GRT |
| `delaware_bay` | Delaware Bay & River Pilots | Philadelphia/Wilmington DE | GRT |

### Northeast
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `ny_nj` | NY & NJ Sandy Hook Pilots | New York Harbor | GRT |
| `boston` | Boston Pilots | Boston | GRT |
| `portland_me` | Portland Pilots | Portland ME | GRT |

### Pacific
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `puget_sound` | Puget Sound Pilots | Seattle, Tacoma | GRT |
| `columbia_river` | Columbia River Pilots | Portland OR, Longview | GRT |
| `sf_bar` | SF Bar Pilots | San Francisco Bay | GRT |
| `la_lb` | LA/Long Beach Pilots | LA, Long Beach | GRT |

### Great Lakes (federal — USCG regulated)
| ID | Association | Ports | Rate Basis |
|---|---|---|---|
| `great_lakes` | Great Lakes Pilotage | All GL ports | GRT + district (46 CFR Part 401) |

---

## MISSISSIPPI RIVER SPECIAL LOGIC

NOBRA bills the Lower Mississippi in named segments. When a vessel transits from Head of Passes
to Baton Rouge, it passes through multiple billing segments:

```
Head of Passes → Pilots Station       (Passes segment)
Pilots Station → New Orleans           (Lower River segment)
New Orleans    → Baton Rouge           (Upper River segment)
```

Each segment has its own rate per GRT. A full river transit bills all segments.

Implementation approach:
1. Define segment zones as lat/lon boundaries or named waypoints
2. Lookup table: `(origin_zone, destination_zone)` → list of segments traversed
3. Sum segment costs: `Σ (segment_rate_per_grt × vessel_grt)` for each segment

---

## DATA SOURCES

1. **NOBRA:** nobra.com — published tariff schedule (Gulf priority #1)
2. **Houston Pilots:** houstonpilots.com
3. **Savannah Bar Pilots:** savannahpilots.com
4. **State pilotage commission filings** — state DOT or maritime agency websites
5. **Great Lakes:** 46 CFR Part 401 — published in CFR, USCG website
6. **`09_user_notes/`** — William's empirical validation data (add here as collected)

---

## ACCEPTANCE CRITERIA

- Correct rate applied per GRT tier per port
- All 25+ target associations cataloged (tariff found OR noted as gap)
- NOBRA segment logic implemented and tested
- Minimum 2 movements default; configurable for shifting
- Confidence flags: `high` (published tariff), `medium` (benchmark), `estimate` (modeled)
- Calculator returns dict matching standard output schema

---

## INTEGRATION TARGETS

- Feeds into: `10_proforma_calculator/` as `pilotage` line item
- CLI command: `report-platform port-expenses --port "New Orleans" --grt 35000 --loa 225 --cargo-tonnes 50000`
- Supersedes: pilotage stub in legacy `02_TOOLSETS/port_cost_model/`

---

## FILES IN THIS MODULE

```
02_pilotage/
├── CLAUDE.md                        ← THIS FILE
├── README.md                        ← User-facing module overview
├── data/
│   ├── pilot_associations_research.json  ← Research agent output (building)
│   ├── pilot_associations.json           ← Curated master directory (pending)
│   ├── pilotage_tariffs.parquet          ← Normalized rate table (pending)
│   ├── river_segments.json               ← NOBRA segment structure (pending)
│   └── raw_tariffs/                      ← Downloaded PDFs/HTML (collecting)
└── src/
    └── pilotage_calculator.py            ← Calculator engine (pending)
```
