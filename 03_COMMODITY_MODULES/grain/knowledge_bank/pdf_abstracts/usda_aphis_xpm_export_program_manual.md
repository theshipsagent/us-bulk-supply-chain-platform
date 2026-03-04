# USDA APHIS Export Program Manual (XPM)

**Last Updated:** 2026-03-01
**Citation:** USDA Animal and Plant Health Inspection Service (APHIS), Plant Protection and Quarantine (PPQ). *Export Program Manual.* New edition 2024, updated 11/25/2025.
**File:** `xpm.pdf`
**Type:** Federal agency operational manual; authoritative reference for agricultural export certification

---

## Overview

The Export Program Manual (XPM) is the authoritative USDA-APHIS-PPQ reference for inspecting and certifying commodities offered for export from the United States. It covers phytosanitary certification procedures, special programs, and the regulatory framework for U.S. agricultural export certification.

**Important note:** USDA-APHIS-PPQ does **NOT** regulate the exportation of commodities. It provides certification services as a convenience to exporters who need to meet foreign phytosanitary import requirements.

---

## Legal and Regulatory Framework

| Authority | Description |
|---|---|
| Plant Protection Act, Section 418 | Grants APHIS authority to issue export certificates |
| 7 CFR Part 353 | Export Certification regulations |
| 7 CFR Part 354.3 | User fees for international services |
| IPPC Standards (ISPMs) | International Plant Protection Convention phytosanitary standards |
| NAPPO Standards (RSPMs) | North American Plant Protection Organization regional standards |

---

## Key Forms and Certificates

| Form | Purpose |
|---|---|
| PPQ Form 572 | Application for Inspection and Certification (submitted by exporter) |
| PPQ Form 577 | Phytosanitary Certificate (standard export) |
| PPQ Form 579 | Phytosanitary Certificate for Reexport |
| PPQ Form 578 | Export Certificate for Processed Plant Products |
| FGIS Form 921-2 | Inspection Report — Insects in Grain (grain-specific) |
| AMS Form SC-66 | Report of Inspection |

---

## Systems Referenced

| System | Purpose |
|---|---|
| PExD (Phytosanitary Export Database) | Database of foreign countries' plant import requirements |
| PCIT (Phytosanitary Certificate Issuance & Tracking) | Automates phytosanitary certificate issuance and tracking |

---

## Grain-Specific Provisions (Chapter 4 — Special Procedures)

**Table 4-1:** Species that FGIS Can Inspect (grain-specific list)

**Table 4-2:** Determine Action to Take on Grain Inspected by FGIS

**Key provision:** For bulk grain exports, USDA FGIS (Federal Grain Inspection Service) conducts the official inspection. APHIS-PPQ uses the FGIS certificate as the basis for issuing PPQ Form 577 or 579.

**Table 4-3:** Determine Whether to Issue PPQ Form 577 or 579
**Table 4-4:** Completion of PPQ Forms 577 or 579 for Grain Products
**Table 4-5:** Determine Whether to Use FGIS Certificate to Issue PPQ Form 577 or 579

---

## Certification Process (General Flow)

```
Exporter → submits PPQ Form 572 (application)
         → ACO inspects commodity
         → ACO verifies against PExD (destination country requirements)
         → ACO issues PPQ Form 577 (or 579 for reexport)

For grain: FGIS conducts official inspection → issues FGIS certificate
         → ACO uses FGIS certificate to issue PPQ 577/579
```

---

## Phytosanitary Certification Eligibility

**Table 3-5:** Determine Eligibility Based on Origin and Destination
**Table 3-6:** Determine Eligibility Based on CITES and ESA Status

**Table 3-7:** Common Import Requirements (varies by destination country — use PExD)

---

## Special Programs (Chapter 5)

Relevant to forestry/wood commodities more than grain, but includes:
- Kiln-dried lumber treatment certificates
- Heat treatment certificates
- Mill certification programs
- MOUs for industry-issued certificates (ISPM 15 treatment mark)

---

## Key Value for Platform

**Primary use:** Regulatory compliance reference for grain export certification; understanding the FGIS-APHIS interface; phytosanitary certification process for export grain

**Relevance to grain module:**
- Export documentation requirements for `knowledge_bank/supply_chain_flows/`
- FGIS inspection requirement at export elevators — connects to Tier 4 elevator taxonomy
- PPQ Form 577 is required for most grain exports to countries with phytosanitary requirements (Japan, Korea, EU, etc.)
- PExD database is a reference tool for destination-country import requirements

**Cross-reference:**
- FGIS export inspection data is a data source in `data_sources.json` (Tier 1)
- FGIS vessel inspection records are used by `vessel_voyage_analysis` toolset for cargo classification

---

## Notes

- The XPM covers ALL plant and plant product exports, not just grain — grain is a subset via Chapter 4
- Most U.S. bulk grain exports require FGIS official inspection; phytosanitary certificate is then a downstream step
- The manual is updated continuously — check APHIS website for current version
- PExD database is publicly accessible and useful for destination-country import requirement research
- APHIS does NOT set grades or standards for grain — that is USDA FGIS/AMS function
