# Commodity Modules

Pluggable commodity verticals that layer on top of the core platform toolsets.

## Active Modules

### Cement & Cementitious Materials (`cement/`)
First module. Covers Portland cement, white cement, slag, fly ash, natural pozzolans, calcined clay.

## Planned Modules
- `grain/` — Grain and oilseeds
- `fertilizer/` — Fertilizer and chemical commodities
- `petroleum/` — Petroleum and liquid bulk
- `metals/` — Metals and minerals

## Adding a New Module

1. Create directory: `03_COMMODITY_MODULES/<commodity_name>/`
2. Copy structure from `cement/` as template
3. Define commodity-specific NAICS codes in `naics_codes.json`
4. Define HTS codes for trade flow filtering
5. Configure commodity-specific routes in `supply_chain_models/`
6. Add report chapters in `reports/`
7. Register in `config.yaml` under `commodity_modules.active`
