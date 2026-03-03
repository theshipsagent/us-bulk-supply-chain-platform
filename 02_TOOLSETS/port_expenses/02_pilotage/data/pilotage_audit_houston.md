# PILOTAGE COST CALCULATION — AUDIT DOCUMENT

**Document type:** Proforma Disbursement Account — Pilotage Section  

**Generated:** 2026-03-03 01:32 UTC  

**Status:** ⚠ DRAFT — All rates require verification against current published tariffs before use  

**Tariff source:** pilot_associations_catalog.json v0.1.0-draft  

---

## Section 1 — Voyage & Vessel Inputs

These are the parameters fed into the calculation. Each must be confirmed from official vessel documents or voyage instructions before finalising the PDA.



| Parameter                  | Value                                             | Notes / Source                                                    |
| -------------------------- | ------------------------------------------------- | ----------------------------------------------------------------- |
| Vessel GRT                 | 35,000 GT                                         | Registered Gross Tonnage — from Certificate of Registry. NOT DWT. |
| Arrival Draft (inbound)    | 41.50 ft  (12.65 m)                               | Draft at time of inbound movement                                 |
| Departure Draft (outbound) | 22.00 ft  (6.71 m)                                | Draft at time of outbound movement — may differ from arrival      |
| Port                       | Houston                                           | Provided                                                          |
| Direction                  | both                                              | Inbound + Outbound — each zone/movement billed twice              |
| Arrival datetime           | 2025-03-08 23:00  [NIGHT (after 22:00) + WEEKEND] | Inbound movement                                                  |
| Departure datetime         | 2025-03-10 10:00  [daytime weekday]               | Outbound movement                                                 |

---

## Section 2 — Tariff Schedule & Rate Selection

**Applicable rate basis:** GRT-tier — flat rate per pilotage movement  

The vessel's Registered Gross Tonnage is looked up in the published tariff schedule. The rate for that GRT bracket is a flat fee per movement. Inbound = 1 movement, Outbound = 1 movement.  



### Association: Houston Pilots

*Covers Houston Ship Channel (50-mile dredged channel). Pilots board at Galveston outer bar. Also covers Texas City turning basin and Galveston island wharves.*  

**Website:** https://www.houstonpilots.com  

**Tariff URL:** https://www.houstonpilots.com/tariff-schedule  



**Full Published GRT Rate Schedule** (rate per pilotage movement):

| GRT From   | GRT To     | Rate per Movement (USD) | Selection                            |
| ---------- | ---------- | ----------------------- | ------------------------------------ |
| 0          | 5,000      | $1,050.00               |                                      |
| 5,001      | 10,000     | $2,100.00               |                                      |
| 10,001     | 15,000     | $3,150.00               |                                      |
| 15,001     | 20,000     | $4,200.00               |                                      |
| 20,001     | 25,000     | $5,250.00               |                                      |
| 25,001     | 30,000     | $6,300.00               |                                      |
| **30,001** | **40,000** | **$7,350.00**           | ← **VESSEL FALLS HERE** (GRT 35,000) |
| 40,001     | 50,000     | $8,400.00               |                                      |
| 50,001     | and above  | $9,450.00               |                                      |

**→ Vessel GRT:** 35,000 GT  

**→ Selected bracket:** 30,001 – 40,000 GT  

**→ Rate applied:** $7,350.00 per movement  



**Calculation formula:**

```
  Step 1  Look up GRT in tariff schedule → identify bracket → read flat rate
  Step 2  Movement charge  =  Flat rate (no further scaling)
  Step 3  Detention        =  Hours waiting  ×  detention rate/hr
  Step 4  Movement total   =  Flat rate  +  Detention
  Note:   Surcharges (night, deep draft, etc.) are separate line items below
```

**Applicable Surcharges from Published Tariff:**

| Surcharge Type       | Rate    | Condition / Notes            | How Applied                                                            |
| -------------------- | ------- | ---------------------------- | ---------------------------------------------------------------------- |
| Deep Draft Surcharge | $500.00 | Vessels drawing over 40 feet | Per movement direction — evaluated separately for inbound and outbound |
| Night Pilotage       | $300.00 | Between 2200-0600 local time | Per movement direction — evaluated separately for inbound and outbound |

---

## Section 3 — Line Item Calculations

Every arithmetic step is shown. Each figure can be verified independently with a hand calculator.



### Line Item 1 — INBOUND:  Houston Pilots

| | |

|---|---|

| **Zone / Service** | Houston Pilots — Port Call |

| **Rate type** | GRT-tier (flat rate per movement) |

| **Direction** | Inbound |

| **Confidence** | medium |

| **Tariff source** | https://www.houstonpilots.com |



**Step-by-step arithmetic:**

| Step               | Calculation                              |
| ------------------ | ---------------------------------------- |
| Vessel GRT         | 35,000 GT                                |
| GRT bracket        | 30,001 – 40,000 GT                       |
| Tariff rate        | $7,350.00 per movement (flat — GRT tier) |
| Direction          | inbound                                  |
| **Movement total** | **$7,350.00 (flat rate — no detention)** |

**Line Item 1 Total:  $7,350.00**

---

### Line Item 2 — OUTBOUND:  Houston Pilots

| | |

|---|---|

| **Zone / Service** | Houston Pilots — Port Call |

| **Rate type** | GRT-tier (flat rate per movement) |

| **Direction** | Outbound |

| **Confidence** | medium |

| **Tariff source** | https://www.houstonpilots.com |



**Step-by-step arithmetic:**

| Step               | Calculation                              |
| ------------------ | ---------------------------------------- |
| Vessel GRT         | 35,000 GT                                |
| GRT bracket        | 30,001 – 40,000 GT                       |
| Tariff rate        | $7,350.00 per movement (flat — GRT tier) |
| Direction          | outbound                                 |
| **Movement total** | **$7,350.00 (flat rate — no detention)** |

**Line Item 2 Total:  $7,350.00**

---

### Line Item 3 — INBOUND:  Houston Pilots

| | |

|---|---|

| **Zone / Service** | Deep Draft Surcharge (>40 ft) |

| **Rate type** | Surcharge |

| **Direction** | Inbound |

| **Confidence** | medium |

| **Tariff source** | catalog |



**Step-by-step arithmetic:**

| Step                   | Calculation                     |
| ---------------------- | ------------------------------- |
| Threshold              | 40 ft (per tariff schedule)     |
| Vessel draft (inbound) | 41.5 ft                         |
| Triggered?             | YES — 41.5 ft > 40 ft threshold |
| Rate                   | $500.00 flat per movement       |
| **Total**              | **$500.00**                     |

**Line Item 3 Total:  $500.00**

---

### Line Item 4 — INBOUND:  Houston Pilots

| | |

|---|---|

| **Zone / Service** | Night Pilotage |

| **Rate type** | Surcharge |

| **Direction** | Inbound |

| **Confidence** | medium |

| **Tariff source** | catalog |



**Step-by-step arithmetic:**

| Step       | Calculation                                                 |
| ---------- | ----------------------------------------------------------- |
| Condition  | Night Pilotage — triggers when movement is night or weekend |
| Movement   | INBOUND — arrival 23:00                                     |
| Triggered? | YES — night (23:00 is after 22:00) + weekend (Saturday)     |
| Rate       | $300.00 flat per movement                                   |
| **Total**  | **$300.00**                                                 |

**Line Item 4 Total:  $300.00**

---

## Section 4 — Summary & Total

| Association    | Zone / Service                | Direction           | Amount (USD)   |
| -------------- | ----------------------------- | ------------------- | -------------- |
| Houston Pilots | Houston Pilots — Port Call    | Inbound             | $7,350.00      |
| Houston Pilots | Deep Draft Surcharge (>40 ft) | Inbound             | $500.00        |
| Houston Pilots | Night Pilotage                | Inbound             | $300.00        |
|                |                               | *Inbound subtotal*  | *$8,150.00*    |
|                |                               |                     |                |
| Houston Pilots | Houston Pilots — Port Call    | Outbound            | $7,350.00      |
|                |                               | *Outbound subtotal* | *$7,350.00*    |
|                |                               |                     |                |
|                |                               | **TOTAL PILOTAGE**  | **$15,500.00** |

Inbound subtotal:   **$8,150.00**  

Outbound subtotal:  **$7,350.00**  

  

## TOTAL PILOTAGE:  $15,500.00

---

## Section 5 — Assumptions & Human Logic Checklist

The following must be confirmed before this estimate is used in a final PDA or presented to a ship owner:



- [ ] **GRT confirmed:** 35,000 GT.  Must be Registered Gross Tonnage from Certificate of Registry — NOT DWT.  

- [ ] **Night surcharge window:** 22:00–06:00 local time.  Arrival = 23:00 (inbound).  Departure = 10:00 (outbound).  Each movement evaluated **independently**.  

- [ ] **Deep draft:**  Inbound = 41.5 ft.  Outbound = 22.0 ft.  Surcharge applies only to the direction where draft exceeds the threshold.  

- [ ] **Shifting:** Standard = 2 movements (in + out).  Each shift within port = 1 additional movement.  

- [ ] **GRT below compulsory threshold:** Most US ports compulsory above 300 GT.  Below threshold = voluntary — confirm with port agent.  

---

*End of document — pilot_associations_catalog.json v0.1.0-draft*
