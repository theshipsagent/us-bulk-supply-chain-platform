# Session State — Coal Module
Last updated: 2026-03-03 ~21:00

## Current Goal
USEC Coal Exports — 2025 Year in Review report, publishable quality for OceanDatum.ai

## Completed This Session

- **Rebuilt report as narrative-first "Year in Review"** — no Chart.js, clean prose sections
- **Photo embedded** — `coalmine1.jpeg` (Lee Dorsey "Working in the Coal Mine" album cover)
  - Float: top-left, text wraps right — blog post layout
  - Caption fixed: *Working in the Coal Mine* — Lee Dorsey, 1966
  - Standalone copy written to output dir alongside HTML
- **OG / social sharing meta tags added**
  - `og:title`, `og:description`, `og:site_name`, `og:type`, `article:author`
  - `twitter:card: summary_large_image`
  - `--og-image-url` CLI option — set to hosted URL when deploying to OceanDatum.ai
- **Build script:** `src/build_coal_export_report.py` (59 KB)
- **Output:** `04_REPORTS/coal_export_report/output/usec_coal_2025_year_in_review_20260303.html` (75 KB)

## Report Sections (current)
1. Cover / hero + stat cards
2. Where the Coal Went (markets, destinations, world map)
3. The Infrastructure Behind It (terminals, shippers, origins map)
4. What It Costs to Move Coal to Water (rail corridors, FOB pricing, freight)
5. What 2025 Tells Us (outlook narrative)

## Next Steps
- [ ] Web session: post unlinked copy to OceanDatum.ai (use prompt in `08_USER_NOTES/coal_web_post_prompt.md`)
- [ ] Rebuild with `--og-image-url` once hosted URL is known
- [ ] Consider: add a "About this data" footer note (methodology, data sources cited)
- [ ] Port Expenses: build `01_towage`, `02_pilotage`, `03_terminals`

## Key Files
```
03_COMMODITY_MODULES/coal/src/build_coal_export_report.py   ← main build script
03_COMMODITY_MODULES/coal/src/build_coal_trade_map.py       ← Leaflet maps (inline)
04_REPORTS/coal_export_report/output/
  usec_coal_2025_year_in_review_20260303.html               ← main report (75 KB)
  coalmine1.jpeg                                            ← cover photo (standalone)
/Users/wsd/Downloads/coalmine1.jpeg                         ← source photo
```

## Data Facts
- `coal_analytics.duckdb` — 5,116 vessel calls, Oct 2021–Jan 2026
- 42% NULL metric_tons in Format 1 PDFs (structural, not a bug)
- Top shippers: JAVELIN (398 calls), ALPHA (396), XCOAL (220), CONSOL (215)
- Top destinations 2025: India, Brazil, Netherlands, China
- Hampton Roads ~80% of USEC volume; ~75% met coal
