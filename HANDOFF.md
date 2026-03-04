# HANDOFF — project_master_reporting
**Last updated:** 2026-03-03 (Session — Grain v3 dark maps + full-year FGIS + section reorder)
**Owner:** William S. Davis III

---

## SESSION RESTORE
Say **"read handoff"** at the start of any new session to restore context instantly.

---

## WHAT WAS COMPLETED THIS SESSION

### Grain Module — Lower Miss River Elevator Guide v3 (refinement)

**Build script:** `03_COMMODITY_MODULES/grain/src/build_lower_miss_report_v3.py`
**Output:** `04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3.html` (~2,017 KB)
**Run:** `python3 src/build_lower_miss_report_v3.py` from `03_COMMODITY_MODULES/grain/`

#### Changes made this session:

1. **FGIS data corrected** — `southport_ingest.py` parser fixed for Q4 2025:
   - Two-pass sheet detection: `FGISyyyyDATA` preferred, `FGISyyyy` fallback
   - Dynamic header row scanning (4-row title block in Q4 sheets)
   - Expanded column aliases (`vessel`, `metric tons`, `foriegn matter` [sic])
   - Dedup by `serial_no` preferring rows with test_weight
   - True 2025 MISS R. total: **64.48 MMT** (was 864.5M — cumulative file artifact)
   - All 12 months now in DB

2. **Grade-quality restored** — 18 rows; stow factor uses USDA reference weights (Corn 56, SYB 60, WHT 60, Sorghum 56 lb/bu) when cert lacks test_weight

3. **Top-10 ships table** — Elevator column added via CTE join with `grain_southport_lineup`

4. **Monthly YoY chart** — 2025 (Jan–Sep real, Oct–Dec null/spanGaps:false) + 2022/2023/2024 dashed comparison lines

5. **All 3 maps — OceanDatum dark style:**
   - CartoDB DarkMatter, fig_bg=#08090d, grain mint=#64ffb4, 4-layer river glow
   - River map, World trade flow map, Barge corridor map all matching

6. **Section reorder** — Trade flows + market intel at top; terminals + supply chain at end:
   Cover → Trade Flows → Commodity Intelligence → Quality → Rankings → Vessel Analytics → River Map → Terminal Profiles → Anchorage → River Conditions → Barge Origins

7. **Web post prompt written** — `08_USER_NOTES/grain_web_post_prompt.md`

---

## WHAT'S NEXT

### Grain Module — v3 Refinements
- [ ] Verify SOYBEANS grade rows — check alias `SOYBEANS` vs `SYB` in FGIS data
- [ ] Terminal profiles: verify ADM WOOD BUOYS and BUNGE DESTREHAN coordinates (currently approximate)
- [ ] Seasonal narrative: US harvest calendar → barge fleet buildout → vessel queue
- [ ] 2024 vs 2025 volume comparison at terminal level
- [ ] Report archiving: analyze all versions across project, move superseded to 06_ARCHIVE/

### Coal Module (from previous session — 8ba1139)
- [ ] Web session: post coal 2025 Year in Review (prompt at `08_USER_NOTES/coal_web_post_prompt.md`)
- [ ] Rebuild with `--og-image-url` once coalmine1.jpeg hosted

### Platform Priorities
- [ ] Port Expenses: build `01_towage`, `02_pilotage`, `03_terminals`
- [ ] Wire `11_hold_cleaning` into `10_proforma_calculator`

---

## KEY FILE PATHS

```
03_COMMODITY_MODULES/grain/src/build_lower_miss_report_v3.py           ← active grain build script
03_COMMODITY_MODULES/grain/src/southport_ingest.py                      ← FGIS parser (Q4 2025 fixed)
04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3.html  ← main report (~2,017 KB)
04_REPORTS/presentations/lower_miss_grain_elevator_guide_2025_v3_INTERNAL.html
08_USER_NOTES/grain_web_post_prompt.md                                  ← web session prompt (grain)
08_USER_NOTES/coal_web_post_prompt.md                                   ← web session prompt (coal)
data/analytics.duckdb                                                   ← grain_fgis_certs 105,833 rows
03_COMMODITY_MODULES/coal/src/build_coal_export_report.py               ← coal build script
04_REPORTS/coal_export_report/output/usec_coal_2025_year_in_review_20260303.html
```

---

## DATA FACTS — GRAIN

- `grain_fgis_certs` — 105,833 rows, deduplicated by serial_no
- 2025 MISS R. certified volume: **64.48 MMT** (Corn 37.1, Soybeans 23.4, Wheat 4.0)
- `grain_southport_lineup` — column is `status_type` NOT `status`
- FGIS Q4 2025: sheet = `FGIS2025` (no DATA suffix), 4-row title block before headers
- MRTIS real zones: 9 Mile Anch, 12 Mile Anch, Lwr Kenner Bend Anch, Belle Chasse Anch, AMA Anch, Burnside Anch, Davant Anch, Baton Rouge Gen Anch

## DATA FACTS — COAL

- `coal_analytics.duckdb` — 5,116 vessel calls, Oct 2021–Jan 2026
- 42% NULL metric_tons — Format 1 PDF structural artifact (not a bug)
- Top shippers 2025: JAVELIN, ALPHA, XCOAL, CONSOL / Core Natural Resources
- Top destinations 2025: India, Brazil, Netherlands, China

---

## WEB DEMO NOTE

Web session = OceanDatum.ai (`theshipsagent.github.io/`) — completely separate repo.
NEVER read or modify from this session.
- Grain post prompt: `08_USER_NOTES/grain_web_post_prompt.md`
- Coal post prompt: `08_USER_NOTES/coal_web_post_prompt.md`
Both are standalone demos — no link to production drafts here.
