# Port Cost Model — Technical Methodology

## 1. Overview

The Port Cost Model generates proforma port cost estimates for vessel port calls at US ports. The model aggregates five cost components — pilotage, towage, port authority charges, stevedoring, and ancillary costs — into a standardised proforma format used in ship agency, chartering, and supply chain cost analysis.

**Platform Path:** `02_TOOLSETS/port_cost_model/`
**Primary Output:** Itemised proforma port cost estimate ($/call and $/ton)
**Key Dependencies:** Python dataclasses (no external libraries required for core calculation)

## 2. Cost Components

### 2.1 Pilotage

Pilotage is compulsory for foreign-flag vessels at all US ports. The Mississippi River system uses a multi-association pilotage structure:

| Zone | Association | Route | Base Rate |
|---|---|---|---|
| Bar to Head of Passes | Associated Branch Pilots | Sea buoy to HOP | $135/ft draft |
| Head of Passes to NOLA | Crescent River Port Pilots | HOP to New Orleans | $155/ft draft |
| NOLA to Baton Rouge | NOLA-BR Steamship Pilots | New Orleans to BR | $165/ft draft |
| Above Baton Rouge | NOLA-BR Steamship Pilots | BR to Plantation | $180/ft draft |
| Houston Ship Channel | Houston Pilots | Galveston to Houston | $125/ft draft |
| Lake Charles | Lake Charles Pilots | Calcasieu Ship Channel | $110/ft draft |
| Mobile | Mobile Bar Pilots | Mobile Bay | $100/ft draft |
| Tampa | Tampa Bay Pilots | Tampa Bay | $95/ft draft |
| Norfolk | Virginia Pilots Association | Hampton Roads | $90/ft draft |

**Calculation method:**

```
Pilotage = max(Rate_per_foot × Draft_feet, Minimum_charge)
         + Surcharge (fuel/general, typically 6-15%)
         + Detention (if applicable, $300-550/hour)

For round-trip (inbound + outbound): multiply by 2
```

**Route templates:** Pre-defined zone sequences for common voyages (e.g., "sea_to_nola" = Bar→HOP + HOP→NOLA).

### 2.2 Towage (Harbour Tugs)

Harbour towage covers assist tugs for docking and undocking operations:

**Rate structure:** Rates are based on vessel GT (gross tonnage) brackets and vary by port:

| GT Bracket | New Orleans | Houston | Mobile | Tampa |
|---|---|---|---|---|
| 0–10,000 | $4,500/tug | $5,000/tug | $3,800/tug | $3,500/tug |
| 10,001–25,000 | $6,800/tug | $7,500/tug | $5,800/tug | $5,500/tug |
| 25,001–50,000 | $9,200/tug | $10,000/tug | $8,000/tug | $7,800/tug |
| 50,001–80,000 | $12,500/tug | $13,500/tug | $10,800/tug | $10,200/tug |
| 80,001+ | $16,000/tug | $17,000/tug | $13,500/tug | $13,000/tug |

**Calculation method:**

```
Towage = Rate_per_tug × Number_of_tugs × Movements (typically 2: dock + undock)
       + Overtime surcharge (50% for nights/weekends/holidays)
       + Standby charges (if applicable)

Number of tugs: determined by GT bracket (min 1, max 4)
```

### 2.3 Port Authority Charges

Port authority charges consist of three components:

**Dockage:** Charged per foot of vessel LOA per 24-hour period.
```
Dockage = Rate_per_foot_day × LOA_feet × ⌈Days_alongside⌉
Minimum charge applies (typically $700–$1,500)
```

**Wharfage:** Charged per ton of cargo crossing the wharf.
```
Wharfage = Rate_per_ton × Cargo_tons

Rates vary by cargo type:
  Bulk dry (cement, grain): $0.80–1.40/ton
  Bulk liquid: $0.80–1.25/ton
  Steel/metals: $1.50–2.35/ton
  Containers: $1.90–2.20/ton
  General/breakbulk: $1.30–2.15/ton
```

**Harbour dues:** Flat or GT-based entry fee.
```
Harbour Dues = max(Rate_per_GT × Vessel_GT, Minimum_charge)
Typical: $0.04–0.075/GT, minimum $250–600
```

**Additional port charges:** Line handling ($1,500–3,000), security fee ($350–850), fresh water ($12–20/ton).

### 2.4 Stevedoring (Cargo Handling)

Stevedoring covers the cost of loading or discharging cargo:

| Cargo Type | Handling Method | Rate ($/ton) | Throughput (TPH) |
|---|---|---|---|
| Cement (pneumatic) | Pneumatic unloader | $3.50 | 400 |
| Cement (grab) | Grab crane to hopper | $4.25 | 300 |
| Grain (elevator) | Grain elevator | $2.50 | 1,500 |
| Coal | Grab crane | $3.00 | 800 |
| Steel coils | Shore crane | $8.50 | 150 |
| Steel plate | Shore crane | $7.50 | 180 |
| Breakbulk general | Ship gear | $9.00 | 120 |
| Project cargo | Heavy lift crane | $15.00 | 50 |
| Liquid bulk | Pipeline/manifold | $1.80 | 1,000 |

**Calculation method:**

```
Stevedoring = Labour_cost + Equipment_cost + Overtime_surcharge

Labour_cost = max(Rate_per_ton × Cargo_tons, Minimum_charge)
Equipment_cost = Equipment_rate_per_hour × Estimated_hours
Estimated_hours = Cargo_tons / Discharge_rate_TPH
Overtime = (Labour hourly rate × OT% × OT hours)
```

### 2.5 Ancillary Costs

Standard ancillary costs included in every proforma:

| Item | Typical Cost | Notes |
|---|---|---|
| Agency fee | $3,500 | Ship agent disbursement fee |
| Customs clearance | $750 | CBP entry processing |
| Immigration | $250 | Crew documentation |
| Quarantine | $200 | CDC/CBP health clearance |
| Surveyor fees | $1,500 | Draft/cargo survey |
| Communications | $300 | Port communications |
| Garbage removal | $400 | Waste disposal |
| Launch service | $500 | Crew/stores transfer |
| Miscellaneous | $500 | Contingency |
| **Total ancillary** | **~$7,900** | |

## 3. Proforma Assembly

The proforma generator aggregates all components:

```
Total Port Cost = Pilotage + Towage + Port_Charges + Stevedoring + Ancillary

Cost_per_ton = Total_Port_Cost / Cargo_tons
```

### 3.1 Sample Proforma: Supramax at New Orleans

**Vessel:** MV TBN | Flag: Foreign | LOA: 590 ft | Draft: 38.5 ft | GT: 32,000 | DWT: 55,000
**Cargo:** 30,000 tons cement | Days alongside: 4

| Component | Amount |
|---|---|
| Pilotage (Bar-HOP-NOLA, both ways) | $25,321 |
| Towage (2 tugs × 2 movements) | $36,800 |
| Port charges (dockage + wharfage + harbour + line + security) | $67,750 |
| Stevedoring (cement pneumatic, 75 hrs) | $131,250 |
| Ancillary | $7,900 |
| **TOTAL** | **$269,021** |
| **Cost per ton** | **$8.97** |

### 3.2 Sample Proforma: Supramax at Houston

**Vessel:** MV TBN | LOA: 625 ft | Draft: 40 ft | GT: 38,000 | DWT: 65,000
**Cargo:** 45,000 tons cement | Days alongside: 5

| Component | Amount |
|---|---|
| Pilotage (Houston Ship Channel, both ways) | $11,000 |
| Towage (2 tugs × 2 movements) | $40,000 |
| Port charges | $107,075 |
| Stevedoring (cement pneumatic, 112.5 hrs) | $196,875 |
| Ancillary | $7,900 |
| **TOTAL** | **$362,850** |
| **Cost per ton** | **$8.06** |

## 4. Validation

### 4.1 Rate Validation Sources

- Published port authority tariff books (available on port authority websites)
- Pilot association rate cards (filed with state regulatory bodies)
- Tug operator published rates
- Stevedoring company quotations
- Historical ship agency disbursement accounts

### 4.2 Accuracy Assessment

The model is calibrated to produce estimates within ±10–15% of actual disbursement accounts for standard bulk cargo port calls. Variance sources:
- Terminal-specific surcharges not captured in generic tariffs
- Seasonal rate adjustments (holiday overtime, peak season surcharges)
- Negotiated contract rates vs. published tariff rates

## 5. Limitations

1. **Tariff currency:** Reference rates are approximate 2024/2025 figures; port tariffs are updated annually
2. **Terminal-specific rates:** Some terminals have proprietary handling rates not captured in published tariffs
3. **Overtime estimation:** The model uses average overtime hours; actual overtime depends on vessel arrival time, cargo stowage, and weather
4. **Canal transits:** Panama/Suez canal costs are not included in the standard proforma
5. **Bunker delivery:** Fuel delivery charges are excluded from the standard ancillary template
6. **Agency fee variation:** Ship agency fees vary by port and agent; the default is a Gulf Coast average

## 6. Port Coverage

The model currently covers 8 US ports with full tariff data:

| Port | Pilotage | Towage | Tariff | Stevedoring |
|---|---|---|---|---|
| New Orleans | ✓ (3 zones) | ✓ | ✓ | ✓ |
| Houston | ✓ | ✓ | ✓ | ✓ |
| Baton Rouge | ✓ (1 zone) | ✓ | ✓ | ✓ |
| Mobile | ✓ | ✓ | ✓ | ✓ |
| Tampa | ✓ | ✓ | ✓ | ✓ |
| Norfolk | ✓ | ✓ | ✓ | ✓ |
| Lake Charles | ✓ | ✓ | ✓ | ✓ |
| Memphis | — | — | ✓ | ✓ |

Additional ports can be added by extending the tariff data files.

## 7. References

1. Port of New Orleans. *Public Tariff.* https://portnola.com/
2. Port Houston. *General Tariff.* https://porthouston.com/
3. Associated Branch Pilots of the Port of New Orleans. *Rate Schedule.*
4. Crescent River Port Pilots Association. *Pilotage Tariff.*
5. New Orleans–Baton Rouge Steamship Pilots Association. *Rate Schedule.*
6. BIMCO. *Port Cost Handbook.* Annual publication.
7. Drewry Shipping Consultants. *Port Cost Comparisons.* Annual.

---

*US Bulk Supply Chain Reporting Platform v1.0.0 | OceanDatum.ai*
