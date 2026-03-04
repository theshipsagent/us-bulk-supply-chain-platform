# HANDOFF — project_master_reporting
**Last updated:** 2026-03-03 (Session — Grain v3 refinement + dark maps + data correction)
**Owner:** William S. Davis III

---

## SESSION RESTORE
Say **"read handoff"** at the start of any new session to restore context instantly.

---

## WHAT WAS COMPLETED THIS SESSION

### Grain Module — Lower Miss River Elevator Guide v3

**Build script:** `03_COMMODITY_MODULES/grain/src/build_lower_miss_report_v3.py`
**Output:** `04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3.html` (~2,017 KB, self-contained)
**Run:** `python3 src/build_lower_miss_report_v3.py` from `03_COMMODITY_MODULES/grain/`

#### Changes made this session:

1. **FGIS data corrected** — `southport_ingest.py` parser fixed:
   - Q4 2025 files use `FGIS2025` sheet (no DATA suffix) — two-pass sheet detection added
   - Dynamic header row scanning (Q4 sheets have 4-row title block before headers)
   - Expanded column aliases for FGIS2025 schema (`vessel`, `metric tons`, `foriegn matter` [sic])
   - Dedup: prefer rows with test_weight IS NOT NULL over recap rows
   - True 2025 MISS R. total: **64.48 MMT** (was 864.5M — cumulative file duplicate artifact)
   - All 12 months now present in DB

2. **Grade-quality section restored** — 18 rows; stow factor uses USDA reference weights (Corn 56 lb/bu, SYB 60, WHT 60, Sorghum 56) when cert lacks test_weight

3. **Top-10 ships table** — Elevator column added via CTE join with `grain_southport_lineup`

4. **Monthly YoY chart** — 2025 (Jan–Sep real, Oct–Dec null) + 2022/2023/2024 dashed comparison lines

5. **All 3 maps rewritten in OceanDatum dark style:**
   - CartoDB DarkMatter basemap, fig_bg=#08090d, grain mint=#64ffb4, river glow 4-layer
   - Barge corridor map: 3-layer glow per corridor, mint destination star, dark legend with mint border

6. **Section reorder:** trade flows/market at top; terminals/supply chain at end
   - New order: Cover → Trade Flows → Commodity → Quality → Rankings → Vessel Analytics → River Map → Terminal Profiles → Anchorage → River Conditions → Barge Origins

---

## CURRENT STATE

| Item | Status |
|---|---|
| v3 build script | ✅ Operational |
| All 3 dark maps (river, world, barge) | ✅ OceanDatum style |
| FGIS data — full year 2025 | ✅ 105,833 rows, 12 months |
| Grade-quality table | ✅ 18 rows, stow factors |
| Top-10 ships + elevator | ✅ Done |
| Monthly YoY chart | ✅ Done |
| Section order | ✅ Trade flows first |
| Web demo | ✅ Web session has standalone copy (no link here) |

---

## WHAT'S NEXT

### Grain Module — v3 Refinements
- [ ] Verify SOYBEANS grade rows — check alias `SOYBEANS` vs `SYB` in FGIS data
- [ ] Terminal profiles: verify ADM WOOD BUOYS and BUNGE DESTREHAN coordinates (currently approximate)
- [ ] Seasonal narrative page: US harvest calendar → barge fleet buildout → vessel queue
- [ ] 2024 vs 2025 volume comparison at terminal level

### Platform Priorities
- [ ] Port Expenses: build `01_towage`, `02_pilotage`, `03_terminals`; wire `11_hold_cleaning` into `10_proforma_calculator`
- [ ] Wire `report-platform data download/ingest` to per-source downloaders
- [ ] End-to-end cement module integration test

---

## KEY FILE PATHS

```
03_COMMODITY_MODULES/grain/src/build_lower_miss_report_v3.py         ← active build script
03_COMMODITY_MODULES/grain/src/southport_ingest.py                    ← FGIS ingest (Q4 2025 fixed)
04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3.html ← main report (~2,017 KB)
04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3_INTERNAL.html
data/analytics.duckdb                                                  ← grain_fgis_certs 105,833 rows
```

---

## DATA FACTS

- `grain_fgis_certs` — 105,833 rows, deduplicated by serial_no
- 2025 MISS R. certified volume: **64.48 MMT** (Corn 37.1, Soybeans 23.4, Wheat 4.0)
- `grain_southport_lineup` — column is `status_type` NOT `status`
- FGIS Q4 2025: sheet = `FGIS2025` (no DATA suffix), 4-row title block before headers
- MRTIS real anchorage zones (confirmed): 9 Mile Anch, 12 Mile Anch, Lwr Kenner Bend Anch, Belle Chasse Anch, AMA Anch, Burnside Anch, Davant Anch, Baton Rouge Gen Anch

---

## WEB DEMO NOTE

Web session holds a standalone demo copy on OceanDatum.ai — completely separate, no links.
This env = production draft (keep improving). Web = demo snapshot (update manually when ready).
NEVER read or modify `theshipsagent.github.io/` from this session.
