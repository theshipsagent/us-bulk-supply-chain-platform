# RESTORE POINT — 2026-02-17

## What This Project Is

Census Foreign Trade data platform (`task_census`). Parses fixed-width Census Bureau trade files (imports/exports by port, commodity, country) and joins them to hand-built cargo and port classification dictionaries.

**Location**: `G:\My Drive\LLM\task_census`

---

## Current State: WORKING / ALL TESTS PASS

```
13 passed in 145s (5 end-to-end + 8 supply chain)
Run: python -m pytest tests/ -v
```

---

## Architecture

```
task_census/
├── census_trade/                  # Python package — parsers, clients, config
│   ├── config/
│   │   ├── record_layouts.py      # Fixed-width layouts for all Census file types
│   │   ├── eits_codes.py          # Economic Indicators Time Series codes
│   │   ├── country_codes.py       # load_country_reference() from CSV
│   │   ├── port_codes.py          # Port code utilities
│   │   └── url_patterns.py        # Census download URLs
│   ├── parsers/
│   │   ├── fixed_width.py         # Generic fixed-width file parser
│   │   ├── ports.py               # PortParser class (PORTHS6 files)
│   │   ├── merchandise.py         # Merchandise trade parser
│   │   └── concordance.py         # HS/NAICS/SITC concordance parser
│   ├── clients/
│   │   ├── downloader.py          # File download client
│   │   ├── trade_api.py           # Census API client
│   │   └── econ_indicators.py     # EITS API client
│   └── tools/
│       ├── port_analysis.py       # Port trade analysis tools
│       ├── merchandise_trade.py   # Merchandise analysis tools
│       ├── state_trade.py         # State-level trade tools
│       └── supply_chain.py        # Supply chain indicator tools
│
├── data/
│   ├── extracted/                 # Raw Census fixed-width files (large)
│   │   ├── EXDB2501/              # Jan 2025 export database + lookups
│   │   ├── PORTHS6MM2509-2511/    # Port import HS6 (Sep-Nov 2025)
│   │   └── PORTHS6XM2509-2511/    # Port export HS6 (Sep-Nov 2025)
│   │
│   ├── reference/                 # Canonical reference CSVs (SOURCE OF TRUTH)
│   │   ├── port_reference.csv     # 549 US port codes, 4-digit text PK
│   │   ├── country_reference.csv  # 243 country codes, 4-digit text PK
│   │   └── foreign_port_reference.csv  # 2,136 foreign port codes, 5-digit text PK
│   │
│   ├── cargo_hs6_dictionary.json  # 5,591 HS6 codes → cargo classification (built from user Excel)
│   ├── port_dictionary.json       # 403 US port codes → consolidation hierarchy
│   ├── miss_river_annual_trade_by_cargo_country.csv  # Query output
│   ├── lower_miss_river_ports_hs6_2025_ytd.csv       # Query output
│   └── us_hs6_dictionary_sep_nov_2025_user.xlsx      # William's cargo mapping (input)
│
├── tests/
│   ├── test_end_to_end.py         # 5 tests — URL builder, layouts, parsing
│   └── test_supply_chain.py       # 8 tests — EITS API, supply chain pipeline
│
├── build_port_dict.py             # Builds port_dictionary.json FROM port_reference.csv
├── build_port_classifications.py  # Port classification builder
├── build_unified_port_reference.py # Merges Schedule D + CBP Appendix E → port_reference.csv
├── fix_ports_master.py            # Syncs ports_master.csv to port_reference.csv
├── fix_zero_padding.py            # Restores 4-digit zero-padding after Excel edits
├── parse_appendix_e.py            # Parses CBP Appendix E PDF
├── parse_schedule_c.py            # Parses Census Schedule C → country_reference.csv
├── parse_schedule_d.py            # Parses Census Schedule D port codes
├── parse_schedule_k.py            # Parses CBP Appendix F → foreign_port_reference.csv
└── query_miss_river.py            # Mississippi River trade query
```

---

## Key Dictionaries (3 built this session)

### 1. cargo_hs6_dictionary.json
- **Source**: `us_hs6_dictionary_sep_nov_2025_user.xlsx` (William's manual HS6→cargo mapping)
- **5,591 HS6 codes**, 2,788 mapped to 90 cargo types, 2,803 unmapped ("x")
- **Hierarchy**: Group → Commodity → Cargo → Cargo_Detail
- **Lookups**: `hs6_lookup` (by code), `cargo_to_hs6` (reverse), `hierarchy` (tree)
- **Rebuild**: Just reload the Excel, script was inline

### 2. port_dictionary.json
- **Source**: `data/reference/port_reference.csv` (single source of truth)
- **403 port codes** with trade volumes from Sep-Nov 2025
- **77 consolidated groups**, Coast/Region hierarchy
- **Key grouping**: "Lower Miss River" = ports 2002 (New Orleans) + 2004 (Baton Rouge) + 2010 (Gramercy)
- **Rebuild**: `python build_port_dict.py`

### 3. country_reference.csv + foreign_port_reference.csv (new this session)
- **243 countries** with ISO codes, regions, sub-regions
- **2,136 foreign ports** with country cross-reference
- **Canonical copies in**: `project_manifest/DICTIONARIES/` AND `task_census/data/reference/`
- **Must stay in sync** — byte-identical

---

## DICTIONARIES Sync Rule

These files exist in TWO locations and must be identical:

| Manifest (canonical)                                          | Working copy                                    |
|---------------------------------------------------------------|------------------------------------------------|
| `project_manifest/DICTIONARIES/port_reference.csv`            | `task_census/data/reference/port_reference.csv` |
| `project_manifest/DICTIONARIES/country_reference.csv`         | `task_census/data/reference/country_reference.csv` |
| `project_manifest/DICTIONARIES/foreign_port_reference.csv`    | `task_census/data/reference/foreign_port_reference.csv` |
| `project_manifest/DICTIONARIES/ports_master.csv`              | (read-only, Panjiva text crosswalk)             |

**Never edit reference CSVs with code.** Human edit only, then run `fix_zero_padding.py`.

---

## Mississippi River Query Results (Jan-Nov 2025 YTD)

Last run: `python query_miss_river.py`

- Covers all District 20 ports (14 ports)
- "Lower Miss River" = 2002 + 2004 + 2010 (grouped)
- All others standalone (Lake Charles, Morgan City, Memphis, Nashville, etc.)
- **Imports**: 45.2M MT / $30.8B — top: Crude Oil, Dirty Products, Fertilizer, Cement (1.9M MT)
- **Exports**: 174.5M MT / $73.2B — top: Grain (71.3M), LNG (35.9M), Dirty Products (21.6M)
- Output: `data/miss_river_annual_trade_by_cargo_country.csv` (3,299 rows)

---

## To Resume Work

```bash
cd "G:/My Drive/LLM/task_census"

# Verify everything works
python -m pytest tests/ -v

# Rebuild port dictionary (if port_reference.csv changed)
python build_port_dict.py

# Rerun Mississippi River query
python query_miss_river.py

# Key imports for ad-hoc work
python -c "
import json
with open('data/port_dictionary.json') as f: ports = json.load(f)
with open('data/cargo_hs6_dictionary.json') as f: cargo = json.load(f)
print(f'Ports: {len(ports[\"port_lookup\"])}  Cargos: {len(cargo[\"hs6_lookup\"])}')
"
```

---

## Related Projects

- `G:\My Drive\LLM\project_manifest\` — Panjiva import manifest data, DICTIONARIES folder
- `G:\My Drive\LLM\project_master_reporting\` — Master project (CLAUDE.md has full architecture)
- `G:\My Drive\LLM\project_master_reporting\CLAUDE.md` — Read this for full project context
