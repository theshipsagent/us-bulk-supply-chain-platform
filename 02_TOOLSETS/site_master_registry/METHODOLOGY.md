# Site Master Registry — Methodology

## Purpose

Creates **one master record per physical industrial site** with a stable `facility_uid` that bridges all upstream data sources. Solves the core identity resolution problem: the same facility appears in EPA FRS, commodity directories, rail databases, and navigation data under different names, coordinates, and IDs.

## Architecture

- **Input:** Commodity CSVs (steel/aluminum/copper), EPA FRS DuckDB, SCRS Rail, BTS Navigation
- **Output:** `site_master.duckdb` with 4 tables (master_sites, source_links, match_candidates, build_log)
- **Does not modify** upstream sources — read-only consumption

## Matching Strategy

Priority order:

1. **Manual overrides** — `config/manual_overrides.json` (bypass algorithms)
2. **Name + State + NAICS** — Normalized names via entity_resolver patterns, `rapidfuzz.fuzz.token_sort_ratio()`, require state match + NAICS overlap
3. **Spatial + Fuzzy Name** — Haversine proximity within configurable radius, composite scoring
4. **Parent Company Bridge** — Boosts confidence when parent_company matches (confirmation signal)

## Confidence Scoring

Weighted composite: name (0.45) + spatial (0.35) + NAICS (0.15) + parent (0.05).

- **HIGH** (≥0.75): Accepted as confirmed link, enriches master site
- **MEDIUM** (≥0.50): Accepted as probable link, enriches master site
- **LOW** (<0.50): Queued for manual review in `match_candidates`

Strong-name override: ≥90% name similarity automatically bumps to ≥0.80 confidence (FRS geocodes differ significantly from curated data).

## UID Generation

Deterministic UUID v5 from `{state}:{city_normalized}:{name_normalized}`. Same physical site always gets the same UID regardless of build timing.

## Build Phases

1. **Seed + FRS Match** — 179 curated commodity facilities → match to EPA FRS
2. **FRS Industrial Expansion** — Add major FRS facilities by NAICS anchor codes
3. **SCRS Rail + Navigation Links** — Enrich with rail-served and water-access flags
4. **Exports, Maps, CLI** — Interactive maps, CLI commands, report integration

## Data Sources

| Source | Records | Key Strength |
|--------|---------|-------------|
| Steel (AIST CSV) | 68 | Curated capacity, logistics flags |
| Aluminum (CSV) | 68 | Same quality as steel |
| Copper (CSV) | 43 | Same quality as steel |
| EPA FRS (DuckDB) | 3.2M | Universal coverage, NAICS codes |
| SCRS Rail (CSV) | 39,936 | Rail-served flag, serving carriers |
| BTS Navigation (GeoJSON) | 4,600+ | Docks, locks, ports |
