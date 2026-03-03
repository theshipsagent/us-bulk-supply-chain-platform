# METHODOLOGY — Hold Cleaning Cost Calculator
**Module:** `02_TOOLSETS/port_expenses/11_hold_cleaning/`
**Version:** 1.1.0 | **Created:** 2026-03-02 | **Last Updated:** 2026-03-02

---

## Purpose

The hold cleaning module estimates the cost of preparing vessel cargo holds before loading, including cleaning operations, fumigation, and mandatory regulatory inspections. This is a required line item in any Proforma Disbursement Account (PDA) where:

1. A vessel is transitioning between incompatible cargo types
2. The next cargo requires a defined cleanliness standard (grain clean, hospital clean)
3. USDA FGIS/NCB inspection is mandatory (all US grain exports)

---

## Cleanliness Standards Hierarchy

| Rank | Standard | Key Cargoes | Rust Tolerance |
|---|---|---|---|
| 1 | **Hospital Clean** | Soda ash, kaolin, mineral sands, rice | Zero — 100% intact paint |
| 2 | **Grain Clean** | All grains, alumina, sulphur, cement, fertilizers | No loose scale; oxidation OK |
| 3 | **Normal Clean** | General bulk (no CP specification) | Standard |
| 4 | **Shovel Clean** | Coal, iron ore, ores | Minimum |
| 5 | **Load on Top** | Same commodity COA trades | N/A |

---

## Calculation Methodology

### Step 1: Determine Cleaning Requirement

Lookup `cargo_compatibility_matrix.csv` using `(previous_cargo, next_cargo)` key.

Returns:
- `cleaning_requirement` — operations required (sweep, seawater wash, fresh water rinse, chemical wash)
- `risk_level` — LOW / MEDIUM / HIGH / VERY_HIGH
- `fgis_concern` — whether the previous cargo creates elevated FGIS survey risk
- `chemical_wash_required` — boolean
- `days_lost_estimate` — expected vessel delay days for severe cases

If no matrix match: apply conservative defaults (seawater + freshwater rinse, MEDIUM risk).

### Step 2: Rate Lookup

Rates sourced from `hold_cleaning_rates.csv`:
- Port × operation × cleaning type (crew vs. shore gang)
- Three columns: `rate_usd_low`, `rate_usd_mid`, `rate_usd_high`
- Calculator uses `rate_usd_mid` for PDA estimates
- Falls back to `DEFAULT` row if specific port not in table

**Operations priced:**

| Operation | When Applied |
|---|---|
| `sweep_per_hold` | Always (baseline) — crew rates only |
| `wash_saltwater_per_hold` | Always (grain clean and above) |
| `wash_freshwater_per_hold` | Always (grain clean and above) — removes chlorides |
| `chemical_wash_per_hold` | When `chemical_wash_required = True` from matrix |
| `fumigation_per_hold` | When `include_fumigation = True` (infestation present) |
| `scale_removal_per_hold` | Manual input only — not auto-applied |
| `enzymatic_wash_per_hold` | Post-fishmeal/organic — keyed from matrix |

**Note on Fresh Water Rinse:** Always included for grain-clean-or-above standard. Removing salt residues from seawater wash is mandatory — failure to rinse results in silver nitrate chloride test failure and survey rejection.

### Step 3: FGIS / NCB Inspection Fees

Auto-triggered when `commodity_loading` matches grain commodities:
- wheat, corn, maize, barley, oats, rye, soybeans, soya, rapeseed, canola, milo, sorghum, sunflower seed

**Fees applied:**
1. **FGIS Stowage Examination** — scaled by vessel DWT (7 CFR Part 800)
2. **NCB Grain Certificate of Readiness** — scaled by vessel DWT
3. **NCB Stability Review** — included when previous cargo is HIGH or VERY_HIGH risk
4. **USDA Per-Hold Cleanliness Certificates** — per hold count
5. **Reinspection Reserve** — included when risk level is HIGH/VERY_HIGH

All FGIS/NCB fees are federally regulated. See `data/fgis_inspection_fees.csv` for current schedule.

### Step 4: Aggregation

```
hold_cleaning_total = sweep + wash + fumigation + fgis_inspection
```

Days lost estimate flows directly from `cargo_compatibility_matrix.csv` — this is the expected vessel delay for severe transitions (coal→grain on Post-Panamax requires 48-72 hours, potentially off-hire).

---

## MARPOL Annex V Compliance Notes

All wash water discharge is subject to MARPOL Annex V (amended January 1, 2013):

- **Default rule:** Discharge of garbage/cargo residues at sea is PROHIBITED
- **HME (Harmful to Marine Environment)** cargoes: NEVER discharged at sea — port reception facility mandatory
- **Non-HME, outside Special Areas:** May discharge if vessel is en route, minimum 12nm from land
- **Special Areas** (Med, Baltic, Gulf of Mexico/Caribbean, etc.): Generally PROHIBITED even for non-HME

**Key MARPOL trigger:** When `chemical_wash_required = True`, the module flags a MARPOL warning requiring confirmation that the cleaning agent is non-HME. Wilhelmsen Unitor CargoClean HD is confirmed non-HME; products containing sodium hypochlorite may be HME.

---

## Data Sources

| File | Source | Notes |
|---|---|---|
| `hold_cleaning_rates.csv` | Industry benchmarks / William S. Davis III empirical rates | Mid-point rates from 30+ years maritime practice |
| `cargo_compatibility_matrix.csv` | UK P&I Club, Skuld P&I, Swedish Club, IMSBC Code, USDA FGIS | Derived from authoritative industry sources |
| `fgis_inspection_fees.csv` | 7 CFR Part 800 / USDA FGIS / NCB Tariff Schedule | Regulated federal fees — verify annually for updates |
| `knowledge_base/hold_cleaning_kb.json` | P&I Clubs, IMO, USCG, NCB, Wilhelmsen, BulkcarrierGuide | Full source index in KB metadata |

---

## Authoritative Sources

**P&I Clubs:**
- UK P&I Club — FAQ Hold Preparation and Cleaning (2021); Carefully to Carry 2023 Ch.17
- Skuld P&I — Preparing Cargo Holds and Loading Solid Bulk Cargoes
- West of England P&I — Cargo Hold Cleaning LP Bulletin
- Swedish Club — Practical Guide: Hold Cleaning of Bulk Vessels (2023, with CWA International)

**Regulatory:**
- IMO — MARPOL Annex V; International Grain Code; IMSBC Code
- USCG — NVIC 5-94 (Grain Code), NVIC 3-97, FFVE Manual
- USDA FGIS — Stowage Examination Services Directive Section 7
- NCB (National Cargo Bureau) — Grain Certificate of Readiness

**Technical:**
- Wilhelmsen Ships Service (Unitor/Navadan product guidance)
- Bulkcarrierguide.com; BulkersGuide; HandyBulk; Safety4Sea

Full source catalog with URLs: `knowledge_base/hold_cleaning_kb.json` → `authoritative_sources`

---

## Limitations and Confidence Notes

- Rates are **benchmarks** — actual quotes from ship chandlers, shore cleaning contractors, and fumigation companies must be obtained for live PDAs
- FGIS fees are from the published 2024 fee schedule — verify against current 7 CFR Part 800 for updated tariffs
- NCB fees are estimates based on published tariff schedules; actual quotes may vary
- Days lost estimates are conservative midpoints — actual cleaning time depends on vessel condition, crew size, weather, and port constraints
- "Hospital clean" after heavily contaminated previous cargo (coal, petcoke, fishmeal) may require shore gang; crew-only rates should be treated as lower bound only
