# PILOTAGE COST CALCULATION — AUDIT DOCUMENT

**Document type:** Proforma Disbursement Account — Pilotage Section  

**Generated:** 2026-03-03 01:32 UTC  

**Status:** ⚠ DRAFT — All rates require verification against current published tariffs before use  

**Tariff source:** pilot_associations_catalog.json v0.1.0-draft  

---

## Section 1 — Voyage & Vessel Inputs

These are the parameters fed into the calculation. Each must be confirmed from official vessel documents or voyage instructions before finalising the PDA.



| Parameter                  | Value               | Notes / Source                                               |
| -------------------------- | ------------------- | ------------------------------------------------------------ |
| Vessel GRT                 | Not provided        | ⚠ Required for GRT-tier ports                                |
| Arrival Draft (inbound)    | 39.40 ft  (12.01 m) | Draft at time of inbound movement                            |
| Departure Draft (outbound) | 24.00 ft  (7.32 m)  | Draft at time of outbound movement — may differ from arrival |
| Port                       | New Orleans         | Provided                                                     |
| River Route                | sea_to_nola         | Auto-inferred from port 'New Orleans'                        |
| Direction                  | both                | Inbound + Outbound — each zone/movement billed twice         |
| Arrival datetime           | Not provided        | Night/weekend surcharge NOT evaluated for inbound movement   |
| Departure datetime         | Not provided        | Night/weekend surcharge NOT evaluated for outbound movement  |

---

## Section 2 — Tariff Schedule & Rate Selection

**Applicable rate basis:** Draft per foot (sliding scale with minimum charge floor)  

**Route:** `sea_to_nola` — 2 zone(s), each billed by a separate licensed association  



### Zone: Sea Buoy → Head of Passes

**Association:** Associated Branch Pilots  

**Tariff URL:** https://www.nobra.com/tariff  

**River miles:** -12.0 to 0.0 (AHP miles from Head of Passes)  



**Rate Schedule:**

| Component              | Value      | Explanation                                                                                          |
| ---------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| Rate per foot of draft | $135.00/ft | Applied to actual vessel draft at time of transit                                                    |
| Minimum charge         | $3,800.00  | Floor — applies if vessel draft × $135.00 < $3,800.00  (i.e., draft below 28.1 ft)                   |
| Standing surcharge     | 15%        | ALWAYS APPLIED — general/fuel surcharge built into published tariff. Not conditional on time of day. |
| Detention rate         | $450/hr    | Applies when pilot is waiting (berth not ready, tide, anchorage, etc.)                               |
| Cancellation fee       | $2,500     | Applies if vessel cancels after pilot has boarded                                                    |

**Calculation formula:**

```
  Step 1  Raw charge     =  Draft (ft)  ×  $135.00 per foot
  Step 2  Applied charge  =  max( Raw charge,  $3,800.00 minimum )
  Step 3  Surcharge       =  Applied charge  ×  15.0%   (standing — always)
  Step 4  Detention       =  Hours waiting   ×  $450/hr
  Step 5  Zone total      =  Applied charge  +  Surcharge  +  Detention
```

### Zone: Head of Passes → New Orleans

**Association:** Crescent River Port Pilots  

**Tariff URL:** https://www.crescentpilots.com  

**River miles:** 0.0 to 95.0 (AHP miles from Head of Passes)  



**Rate Schedule:**

| Component              | Value      | Explanation                                                                                          |
| ---------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| Rate per foot of draft | $155.00/ft | Applied to actual vessel draft at time of transit                                                    |
| Minimum charge         | $4,200.00  | Floor — applies if vessel draft × $155.00 < $4,200.00  (i.e., draft below 27.1 ft)                   |
| Standing surcharge     | 12%        | ALWAYS APPLIED — general/fuel surcharge built into published tariff. Not conditional on time of day. |
| Detention rate         | $500/hr    | Applies when pilot is waiting (berth not ready, tide, anchorage, etc.)                               |
| Cancellation fee       | $2,800     | Applies if vessel cancels after pilot has boarded                                                    |

**Calculation formula:**

```
  Step 1  Raw charge     =  Draft (ft)  ×  $155.00 per foot
  Step 2  Applied charge  =  max( Raw charge,  $4,200.00 minimum )
  Step 3  Surcharge       =  Applied charge  ×  12.0%   (standing — always)
  Step 4  Detention       =  Hours waiting   ×  $500/hr
  Step 5  Zone total      =  Applied charge  +  Surcharge  +  Detention
```

---

## Section 3 — Line Item Calculations

Every arithmetic step is shown. Each figure can be verified independently with a hand calculator.



### Line Item 1 — INBOUND:  Associated Branch Pilots

| | |

|---|---|

| **Zone / Service** | Sea Buoy → Head of Passes |

| **Rate type** | Draft per foot (sliding scale) |

| **Direction** | Inbound |

| **Confidence** | medium |

| **Tariff source** | 2024/2025 tariff card — verify at https://www.nobra.com/tariff |



**Step-by-step arithmetic:**

| Step                       | Calculation                                                               |
| -------------------------- | ------------------------------------------------------------------------- |
| Draft (ft)                 | 39.40 ft                                                                  |
| Rate per foot              | $135.00/ft                                                                |
| Raw calculation            | 39.40 ft × $135.00/ft = $5,319.00                                         |
| Minimum charge floor       | $3,800.00                                                                 |
| Min charge applied?        | NO — $5,319.00 > $3,800.00 floor → gross applies                          |
| Charge before surcharge    | $5,319.00                                                                 |
| Surcharge (15%) — standing | $5,319.00 × 15.0% = $797.85  ← always applied (tariff standing surcharge) |
| **Zone total**             | **$5,319.00 + $797.85 surcharge = $6,116.85**                             |

**Line Item 1 Total:  $6,116.85**

---

### Line Item 2 — OUTBOUND:  Associated Branch Pilots

| | |

|---|---|

| **Zone / Service** | Sea Buoy → Head of Passes |

| **Rate type** | Draft per foot (sliding scale) |

| **Direction** | Outbound |

| **Confidence** | medium |

| **Tariff source** | 2024/2025 tariff card — verify at https://www.nobra.com/tariff |



**Step-by-step arithmetic:**

| Step                       | Calculation                                                               |
| -------------------------- | ------------------------------------------------------------------------- |
| Draft (ft)                 | 24.00 ft                                                                  |
| Rate per foot              | $135.00/ft                                                                |
| Raw calculation            | 24.00 ft × $135.00/ft = $3,240.00                                         |
| Minimum charge floor       | $3,800.00                                                                 |
| Min charge applied?        | YES — $3,240.00 < $3,800.00 floor → use $3,800.00                         |
| Charge before surcharge    | $3,800.00                                                                 |
| Surcharge (15%) — standing | $3,800.00 × 15.0% = $570.00  ← always applied (tariff standing surcharge) |
| **Zone total**             | **$3,800.00 + $570.00 surcharge = $4,370.00**                             |

> **⚑ Minimum charge applied.**  The calculated rate (draft × rate/ft) fell below the minimum charge floor.  This occurs when the vessel is in ballast or lightly loaded.  Minimum charge of **$3,800.00** applied instead.



**Line Item 2 Total:  $4,370.00**

---

### Line Item 3 — INBOUND:  Crescent River Port Pilots

| | |

|---|---|

| **Zone / Service** | Head of Passes → New Orleans |

| **Rate type** | Draft per foot (sliding scale) |

| **Direction** | Inbound |

| **Confidence** | medium |

| **Tariff source** | 2024/2025 tariff card — verify at https://www.crescentpilots.com |



**Step-by-step arithmetic:**

| Step                       | Calculation                                                               |
| -------------------------- | ------------------------------------------------------------------------- |
| Draft (ft)                 | 39.40 ft                                                                  |
| Rate per foot              | $155.00/ft                                                                |
| Raw calculation            | 39.40 ft × $155.00/ft = $6,107.00                                         |
| Minimum charge floor       | $4,200.00                                                                 |
| Min charge applied?        | NO — $6,107.00 > $4,200.00 floor → gross applies                          |
| Charge before surcharge    | $6,107.00                                                                 |
| Surcharge (12%) — standing | $6,107.00 × 12.0% = $732.84  ← always applied (tariff standing surcharge) |
| **Zone total**             | **$6,107.00 + $732.84 surcharge = $6,839.84**                             |

**Line Item 3 Total:  $6,839.84**

---

### Line Item 4 — OUTBOUND:  Crescent River Port Pilots

| | |

|---|---|

| **Zone / Service** | Head of Passes → New Orleans |

| **Rate type** | Draft per foot (sliding scale) |

| **Direction** | Outbound |

| **Confidence** | medium |

| **Tariff source** | 2024/2025 tariff card — verify at https://www.crescentpilots.com |



**Step-by-step arithmetic:**

| Step                       | Calculation                                                               |
| -------------------------- | ------------------------------------------------------------------------- |
| Draft (ft)                 | 24.00 ft                                                                  |
| Rate per foot              | $155.00/ft                                                                |
| Raw calculation            | 24.00 ft × $155.00/ft = $3,720.00                                         |
| Minimum charge floor       | $4,200.00                                                                 |
| Min charge applied?        | YES — $3,720.00 < $4,200.00 floor → use $4,200.00                         |
| Charge before surcharge    | $4,200.00                                                                 |
| Surcharge (12%) — standing | $4,200.00 × 12.0% = $504.00  ← always applied (tariff standing surcharge) |
| **Zone total**             | **$4,200.00 + $504.00 surcharge = $4,704.00**                             |

> **⚑ Minimum charge applied.**  The calculated rate (draft × rate/ft) fell below the minimum charge floor.  This occurs when the vessel is in ballast or lightly loaded.  Minimum charge of **$4,200.00** applied instead.



**Line Item 4 Total:  $4,704.00**

---

## Section 4 — Summary & Total

| Association                | Zone / Service               | Direction           | Amount (USD)   |
| -------------------------- | ---------------------------- | ------------------- | -------------- |
| Associated Branch Pilots   | Sea Buoy → Head of Passes    | Inbound             | $6,116.85      |
| Crescent River Port Pilots | Head of Passes → New Orleans | Inbound             | $6,839.84      |
|                            |                              | *Inbound subtotal*  | *$12,956.69*   |
|                            |                              |                     |                |
| Associated Branch Pilots   | Sea Buoy → Head of Passes    | Outbound            | $4,370.00      |
| Crescent River Port Pilots | Head of Passes → New Orleans | Outbound            | $4,704.00      |
|                            |                              | *Outbound subtotal* | *$9,074.00*    |
|                            |                              |                     |                |
|                            |                              | **TOTAL PILOTAGE**  | **$22,030.69** |

Inbound subtotal:   **$12,956.69**  

Outbound subtotal:  **$9,074.00**  

  

## TOTAL PILOTAGE:  $22,030.69

---

## Section 5 — Assumptions & Human Logic Checklist

The following must be confirmed before this estimate is used in a final PDA or presented to a ship owner:



- [ ] **Draft used — INBOUND:** 39.40 ft.  Rule: use the MAXIMUM draft for each direction.  Discharging port → arrival draft is heaviest.  Loading port → departure draft is heaviest.  

- [ ] **Draft used — OUTBOUND:** 24.00 ft.  

- [ ] **Route correct:** `sea_to_nola` — zones: Sea Buoy → Head of Passes → Head of Passes → New Orleans.  Confirm final berth. If berth is above NOLA bridge, add `nola_to_br` zone.  

- [ ] **Standing surcharges** (15%, 12%) are ALWAYS applied — they are built-in tariff surcharges, not night/weekend charges.  

- [ ] **Detention:** Not applied in this estimate. Add if pilot was detained waiting (berth, tide, anchorage, night-at-bar).  

  | Association | Detention rate |

  |---|---|

  | Associated Branch Pilots | $450/hr |

  | Crescent River Port Pilots | $500/hr |



- [ ] **Minimum charge floors:**  

  - Associated Branch Pilots: $3,800.00 (applies if draft < 28.1 ft)  

  - Crescent River Port Pilots: $4,200.00 (applies if draft < 27.1 ft)  

- [ ] **Cancellation fees** (if vessel cancels after pilot boards):  

  - Associated Branch Pilots: $2,500  

  - Crescent River Port Pilots: $2,800  

---

## Warnings

- ⚠ departure_datetime not provided — outbound night/weekend surcharges NOT applied. Provide departure_datetime= for a complete and accurate estimate.

---

*End of document — pilot_associations_catalog.json v0.1.0-draft*
