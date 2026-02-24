Three new commodity dossier modules have been built and are ready for integration into the master reporting platform. Each follows the same HTML/CSS template as the fly ash dossier and includes BUILD_NOTES.md (with NAICS/HTS codes for tool integration) and HANDOFF.md (with cross-project integration plans).

## New Modules to Integrate

1. **Aggregates**: G:/My Drive/LLM/project_master_reporting/aggregate/
   - AGGREGATES_COMPREHENSIVE_DOSSIER.html (~35KB, 13 sections)
   - BUILD_NOTES.md, HANDOFF.md
   - Key: 2.38 Bt production, $39B market, limestone 70% of crushed stone (~1.05 Bt feeds cement)

2. **Slag/GGBFS**: G:/My Drive/LLM/project_master_reporting/slag/
   - SLAG_COMPREHENSIVE_DOSSIER.html (~45KB, 15 sections)
   - BUILD_NOTES.md, HANDOFF.md
   - Key: GGBFS supply-constrained (<3% of slag tonnage = 80% of $600M value), EAF transition existential risk, ~2 Mt imported (Japan 52%, China 23%)

3. **Natural Pozzolans**: G:/My Drive/LLM/project_master_reporting/natural_pozzolan/
   - NATURAL_POZZOLAN_COMPREHENSIVE_DOSSIER.html (~50KB, 15 sections)
   - BUILD_NOTES.md, HANDOFF.md
   - Key: 2.5 Mt shipped 2024, only SCM with growing supply, price crossover with fly ash ($115 vs $118), LC3 emerging ($1.6B DOE investment)

## Reference Dossier

4. **Fly Ash** (pre-existing): G:/My Drive/LLM/project_flyash/FLY_ASH_COMPREHENSIVE_DOSSIER_v2.html
   - Original template all three modules are modeled after
   - Key: 14.7 Mt to concrete, declining from coal plant closures (-64% since 2007 peak)

## What to Do

Start by reading each module's HANDOFF.md — they contain detailed integration plans mapping existing tools (EPA FRS, Panjiva manifests, rail model, barge model, GIS data) to commodity-specific NAICS and HTS codes.

Priority actions:
1. Review HANDOFF.md files in aggregate/, slag/, and natural_pozzolan/
2. Integrate into 03_COMMODITY_MODULES/ per the master reporting architecture in CLAUDE.md
3. The HANDOFFs propose a combined "US SCM Supply Outlook 2025-2030" merging all four dossiers — this is the logical next deliverable
4. Each BUILD_NOTES.md has NAICS codes for EPA FRS queries and HTS codes for Panjiva manifest queries ready to run

## Combined SCM Supply Picture (2024 → 2028-2030)

- Fly Ash: 14.7 Mt → ~10 Mt (declining — coal closures)
- GGBFS: ~3-5 Mt → ~3 Mt (constrained — EAF shift)
- Natural Pozzolans: 2.5 Mt → 3.5-4 Mt (GROWING — independent mineral reserves)
- LC3: TBD (DOE demos → commercial scale)
- Total SCM to concrete: >20 Mt today, structural deficit emerging
