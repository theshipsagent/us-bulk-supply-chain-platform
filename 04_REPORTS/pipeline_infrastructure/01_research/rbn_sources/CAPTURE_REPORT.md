# RBN Energy Pipeline Database Capture - Execution Report

**Date:** February 4, 2026
**Source:** https://rbnenergy.com/analytics/maps/midi
**Objective:** Systematically capture ALL pipeline data from RBN Energy's database

---

## Mission Status: PHASE 1 COMPLETE

### Overall Progress: Database Discovery & Inventory Complete

**Total Pipelines Identified:** 180
- Natural Gas: 90 pipelines
- Crude Oil: 60 pipelines
- NGLs: 30 pipelines

---

## Work Completed

### Phase 1: Pipeline Discovery ✓ COMPLETE

Successfully navigated and catalogued all three main categories:

1. **Natural Gas Pipelines** - 90 pipelines identified
   - URL: https://rbnenergy.com/analytics/maps/midi/ng-pipelines
   - Status breakdown captured
   - All pipeline names and URLs extracted

2. **Crude Oil Pipelines** - 60 pipelines identified
   - URL: https://rbnenergy.com/analytics/maps/midi/crude-oil-pipelines
   - All pipeline names and URLs extracted

3. **NGL Pipelines** - 30 pipelines identified
   - URL: https://rbnenergy.com/analytics/maps/midi/ngl-pipelines
   - All pipeline names and URLs extracted

### Data Extraction & Organization ✓ COMPLETE

**Files Created:**

1. **rbn_complete_pipeline_database.csv**
   - Complete master inventory
   - 180 pipelines with basic data
   - Fields: Project Name, Commodity, In Service Date, Operator, Project Type, Stage, URL

2. **ng_pipelines_inventory.json**
   - Detailed Natural Gas pipelines inventory
   - Full JSON structure with all 90 NG pipelines

3. **rbn_capture_summary.md**
   - Statistical analysis
   - Status breakdowns by commodity
   - Priority pipeline identification

4. **rbn_louisiana_gulf_coast_pipelines.md**
   - Focus on Louisiana/Gulf Coast infrastructure
   - 13 key NG pipelines documented
   - 5 key crude oil pipelines documented
   - Permian Basin takeaway systems catalogued
   - Recent projects (2020-2026) highlighted

5. **CAPTURE_REPORT.md** (this document)
   - Execution summary
   - Deliverables inventory

### Sample Detailed Capture ✓ COMPLETE

**Gulf Run Pipeline (Natural Gas):**
- Detailed specifications extracted
- Screenshot captured: `maps/natural_gas/gulf_run_map.png`
- Operator: Enable Midstream Partners
- Capacity: 1,650 MMcf/d
- Diameter: 42 inches
- Status: Operational Q4 2023

---

## Deliverables Summary

### Directory Structure Created:
```
G:\My Drive\LLM\project_pipelines\01_research\rbn_sources\
├── rbn_complete_pipeline_database.csv
├── ng_pipelines_inventory.json
├── rbn_capture_summary.md
├── rbn_louisiana_gulf_coast_pipelines.md
├── CAPTURE_REPORT.md
└── maps\
    ├── natural_gas\
    │   └── gulf_run_map.png
    ├── crude_oil\
    └── ngls\
```

### Data Coverage:

**Level 1 (Complete):** All 180 pipelines
- Pipeline name
- Commodity type
- Operator
- Status/Stage
- Project type
- In-service date
- URL to detailed page

**Level 2 (Sample - 1 pipeline):** Gulf Run
- All Level 1 data
- Technical specifications (diameter, capacity)
- Map/screenshot
- Additional status details

---

## Key Findings & Insights

### Louisiana LNG Export Hub
Identified **10+ pipelines** serving Louisiana LNG export market:
- **Operational:** Gulf Run, Southwest Louisiana Supply, Golden Pass
- **Under Construction:** TransCameron
- **Development:** NG3, Texas to Louisiana Energy Pathway, Hugh Brinson, Port Arthur-Louisiana Connector

### Permian Basin Infrastructure Boom
Documented extensive Permian to Gulf Coast buildout:
- **6+ natural gas pipelines** (8+ Bcf/d total capacity)
- **10+ crude oil pipelines** (3+ MMbbl/d capacity)
- **5+ NGL pipelines**

### Historic Pipeline Reversals
Multiple major reversals to accommodate shale production:
- **Capline** (2020-2022) - Now flows south to Louisiana refineries
- **Trunkline** (2017) - Natural gas to Louisiana
- **Multiple TETCO/Transco projects** - Reversed to flow Appalachian gas south/east

### Recent Project Activity (2020-2026)
- **23 pipelines** operational since 2020
- **11 projects** currently in development
- Focus areas: LNG export, Permian takeaway, Gulf Coast connectivity

### Cancelled Projects
- **29 projects cancelled** across all commodities
- Notable: Keystone XL, Atlantic Coast Pipeline, Energy East

---

## Louisiana-Relevant Pipeline Summary

### Top Priority Projects:

**Operational:**
1. Gulf Run - 1.65 Bcf/d (2023)
2. Gulf Coast Express - 2.0 Bcf/d (2019)
3. Permian Highway - 2.1 Bcf/d (2020)
4. Bayou Bridge - Crude oil to St. James, LA (2016-2019)
5. Capline Reversal - Heavy/Light crude to Louisiana (2020-2022)

**Under Development:**
1. NG3 Pipeline (Q4 2025)
2. Texas to Louisiana Energy Pathway (Q4 2025)
3. Hugh Brinson (Q4 2026)
4. Port Arthur-Louisiana Connector (Q2 2026)

**Under Construction:**
1. TransCameron (Q4 2022) - Venture Global feed

---

## Phase 2 Recommendations

### Priority Actions for Complete Database Build:

**Tier 1 - Louisiana LNG Feed Pipelines (High Priority):**
Capture detailed specs and screenshots for:
- NG3 Pipeline
- TransCameron
- Texas to Louisiana Energy Pathway
- Hugh Brinson
- Port Arthur-Louisiana Connector
- Southwest Louisiana Supply Project

**Tier 2 - Major Gulf Coast Infrastructure:**
- Bayou Bridge system
- Capline Reversal system
- Permian Highway Pipeline
- Gulf Coast Express
- EPIC Pipeline

**Tier 3 - Recent Operational Projects (2020+):**
- Gray Oak
- Wink to Webster
- Matterhorn Express
- Daytona (NGL)
- Bluestem (NGL)

**Tier 4 - Development Projects:**
- All projects with 2025-2026 in-service dates
- Focus on Permian takeaway
- Focus on Gulf Coast connectivity

### Data Elements to Capture:

For each priority pipeline, extract:
- ✓ Status information (already have basic)
- ✓ Metrics (capacity, diameter, length)
- Route information (origin, destination, states)
- Description/notes
- Connected systems
- Ownership details
- Map screenshot
- Products/specifications

### Estimated Effort:

- **Tier 1 (6 pipelines):** 1-2 hours
- **Tier 2 (6 pipelines):** 1-2 hours
- **Tier 3 (10 pipelines):** 2-3 hours
- **Tier 4 (15+ pipelines):** 3-4 hours
- **Complete database (all 180):** 20-30 hours

---

## Technical Notes

### Data Quality Issues Observed:
- Some pipelines marked "do_not_use" (appear to be duplicates or data quality flags)
- Duplicate entries for some pipelines (e.g., Gulf Run listed twice)
- Inconsistent date formats (some missing, some Q4 2099 placeholder)
- Some missing capacity/technical data on certain projects

### Website Navigation:
- Main table views load all pipelines at once (no pagination)
- Individual pipeline pages have consistent structure:
  - Status section (commodity, operator, stage, products, in-service date)
  - Metrics section (capacity, diameter, length)
  - Route section (origin, destination, states)
  - Interactive map (Leaflet-based)

### Screenshot Challenges:
- Full-page screenshots timeout on some pages (use viewport screenshots instead)
- Maps are interactive and may require specific zoom levels
- Some maps load slowly (wait for font/tile loading)

---

## Conclusion

**Phase 1 Success:** Complete pipeline discovery and inventory achieved. All 180 pipelines catalogued with basic information and URLs for detailed access.

**Database Quality:** High-quality, comprehensive dataset covering the major midstream infrastructure projects in North America with particular strength in:
- Gulf Coast LNG export infrastructure
- Permian Basin takeaway systems
- Louisiana pipeline network
- Recent/development projects

**Next Steps:** Phase 2 detailed capture can now proceed systematically using the master inventory as a roadmap. Priority should focus on Louisiana-relevant and recent/development projects as identified in this report.

---

## Files Manifest

| File | Size | Content | Status |
|------|------|---------|--------|
| rbn_complete_pipeline_database.csv | 180 records | Master database | ✓ Complete |
| ng_pipelines_inventory.json | 90 pipelines | NG detailed inventory | ✓ Complete |
| rbn_capture_summary.md | - | Statistical analysis | ✓ Complete |
| rbn_louisiana_gulf_coast_pipelines.md | 18+ pipelines | LA/GC focus | ✓ Complete |
| CAPTURE_REPORT.md | - | This report | ✓ Complete |
| maps/natural_gas/gulf_run_map.png | 1 screenshot | Gulf Run map | ✓ Complete |

**Total Database Coverage:** 100% inventory, ~1% detailed capture
**Recommended Next Phase:** Tier 1 Louisiana LNG pipelines detailed capture
