# CLAUDE.md — Agents Sub-Module
**Module:** `02_TOOLSETS/port_expenses/07_agents/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Scaffolded — ready to build | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

Build a ship agency fee calculator. Agency fees follow either a flat GRT-tiered structure or a percentage-of-disbursements structure depending on the port and agent.

---

## WHAT TO BUILD

### 1. Fee Data (`agency_fees.parquet`)
Columns: `port | agent_name | grt_min | grt_max | base_fee_usd | pct_of_disbursements | comms_fee_usd | docs_fee_usd | source | year`

Seed with benchmark fees for key agents at New Orleans, Houston, Savannah, Baltimore, Norfolk, Tampa, Mobile.

### 2. Agent Directory (`agent_directory.csv`)
Columns: `port | agent_name | contact_name | phone | email | website | notes`

Pre-populate with major US bulk port agents:
- GAC Shipping
- Inchcape Shipping Services
- Wilhelmsen Ships Service
- Local independents from William's `09_user_notes/`

### 3. Calculator (`src/agents_calculator.py`)
```python
def calculate_agency_fees(
    port: str,
    vessel_grt: int,
    total_disbursements_usd: float = 0,  # for % structures; 0 = use flat rate
    agent_name: str = None,              # None = use port default
    crew_documentation: bool = True,
    includes_communications: bool = True,
) -> dict:
    ...
```

### 4. Logic Note
Agency fees are typically calculated AFTER all other disbursements are known (because some agents charge a % of total). Build as the last sub-module called before proforma aggregation.

---

## DATA SOURCES

1. `09_user_notes/` — William's agent contacts and fee benchmarks (primary source)
2. Agent websites / published fee schedules
3. BIMCO standard agency appointment letter fee structures

---

## ACCEPTANCE CRITERIA

- Supports both flat (GRT-tiered) and percentage fee structures
- Returns itemized breakdown: base fee + docs + comms
- Falls back to port-level benchmark when agent-specific rate unavailable
