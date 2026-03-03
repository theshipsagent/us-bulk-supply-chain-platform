# Methodology — Port Expenses Toolset

**Toolset:** `02_TOOLSETS/port_expenses/`
**Owner:** William S. Davis III
**Version:** 1.0.0 | Created: 2026-03-02

---

## Overview

A **Proforma Disbursement Account (PDA)** is the standard maritime instrument used to estimate all costs incurred during a vessel's port call, prior to arrival. This toolset calculates each expense category independently, then aggregates into a full PDA.

Vessel parameters drive most calculations:

| Parameter | Abbreviation | Typical Basis For |
|---|---|---|
| Length Overall | LOA | Towage, berth fees |
| Gross Registered Tons | GRT | Pilotage, official fees, agency |
| Deadweight Tons | DWT | Some terminal fees |
| Net Registered Tons | NRT | Light dues, canal fees |
| Cargo Quantity | MT/ST | Stevedoring, terminal handling |

---

## Expense Categories and Calculation Methods

### 01 — Towage
Tug services for moving a vessel within port limits (docking, undocking, shifting).

**Basis:** LOA (most common), GRT, or horsepower-hour
**Structure:**
- Fixed call-out fee per tug
- Variable rate per tug per move (docking = 1 move, undocking = 1 move)
- Number of tugs required scales with vessel LOA:
  - LOA < 150m → 1 tug
  - LOA 150–200m → 2 tugs
  - LOA > 200m → 3+ tugs (port-specific)
- Night/weekend surcharges apply at most ports

---

### 02 — Pilotage
Compulsory or voluntary pilot services for harbor navigation.

**Basis:** GRT or LOA, per movement (inbound + outbound = 2 movements)
**Structure:** Regulated tariff schedules published by pilot associations
**Key associations:**
- NOBRA (New Orleans Bar Pilots) — Mississippi River
- Savannah Bar Pilots — Port of Savannah
- Tampa Bay Pilots — Tampa
- Houston Pilots — Houston Ship Channel

---

### 03 — Terminals
Cargo handling and berth-related charges.

**Sub-components:**
- **Stevedoring:** Labor + equipment cost per ton of cargo worked
- **Wharfage:** Fee charged per ton of cargo crossing the wharf
- **Dockage:** Berth rental fee (per linear foot per day, or per GRT per day)
- **Terminal Handling Charge (THC):** Bundled rate at some terminals

---

### 04 — Officials
Boarding fees for government and port authority representatives.

**Basis:** Fixed per-visit fees per agency
**Typical categories:**
- US Customs and Border Protection (CBP)
- US Coast Guard (USCG) inspection
- USDA APHIS (agriculture/fumigation inspection)
- Port Health Authority
- Immigration (USCBP — crew documentation)

---

### 05 — Surveyors
Professional fees for marine and cargo survey attendance.

**Basis:** Per survey / per day / per shift
**Typical categories:**
- Draft survey (cargo quantity verification)
- Condition survey (vessel or cargo condition)
- P&I club correspondent attendance
- Classification society (ABS, Lloyd's, DNV) fee

---

### 06 — Launches
Boat hire for transporting personnel and goods to/from vessel.

**Basis:** Per trip or per day charter
**Typical uses:**
- Delivering officials, pilots, surveyors to anchorage
- Crew change transportation
- Ship's stores/provisions delivery
- Mooring lines, ropes at anchorage

---

### 07 — Agents
Ship agent (husbanding agent) fees and communication costs.

**Basis:** Fixed fee + percentage of total disbursements, or flat fee by vessel GRT
**Includes:**
- Basic agency fee
- Crew documentation handling
- Correspondence and communication charges
- Port clearance documentation
- Pre-arrival / post-departure services

---

### 08 — Disbursements
Miscellaneous port costs not captured in the above categories.

**Examples:**
- Fresh water supply
- Garbage removal
- Fumigation certificates
- Medical fees
- Overtime charges (weekends, holidays)
- Bank transfer charges
- Advance commission

---

### 09 — User Notes
William's reference data, empirical rate observations, and port-specific intelligence.
Not a calculator — a structured knowledge repository.

---

### 10 — Proforma Calculator
Aggregation engine that:
1. Calls each sub-module calculator with shared vessel/cargo parameters
2. Returns itemized PDA as dict, DataFrame, Excel, or PDF
3. Supports comparison across ports ("least-cost port analysis")
4. Flags items as "estimated" vs. "confirmed tariff"

---

### 11 — Hold Cleaning
Vessel hold preparation costs before and after cargo loading.

**Basis:** Per hold or per vessel, based on hold count and cleanliness standard required
**Typical operations:**
- Sweeping and washing holds after discharge
- Fumigation of holds prior to loading
- Hold inspection (grain-grade cleanliness, CSO certification)
- Drying and ventilation
- Scale/rust removal if required

**Key standard:** USDA FGIS requires holds to be "grain-tight" and free of live insects for grain loading. This drives significant hold cleaning costs on vessels previously carrying other bulk cargoes.

---

## Aggregation and Output

```
PDA TOTAL = Towage + Pilotage + Terminals + Officials +
            Surveyors + Launches + Agents + Disbursements + Hold Cleaning
```

All line items returned with:
- `amount_usd` — calculated estimate
- `basis` — how calculated (tariff, benchmark, estimate)
- `confidence` — high / medium / low
- `source` — tariff schedule, empirical, benchmark
- `notes` — any port-specific caveats
