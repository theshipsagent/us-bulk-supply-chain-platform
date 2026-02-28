# task_census — Project Rules

## Port Reference Architecture

The **single source of truth** for all US port lookups is:

    data/reference/port_reference.csv

This file is IMMUTABLE in code. It is only modified by explicit human edit.
After any manual edit, run `fix_zero_padding.py` to restore 4-digit zero-padded port_codes,
then the file is automatically copied to `project_manifest/DICTIONARIES/port_reference.csv`.

### Primary Key

The 4-digit zero-padded port code (TEXT, e.g. "0123") is the absolute primary key.
It is the same code across Census Schedule D, CBP Appendix E, and all trade data files.
Everything maps FROM the 4-digit code, never TO it by guessing from text.

### port_reference.csv Columns

| Column | Source | Description |
|--------|--------|-------------|
| port_code | Census Schedule D | 4-digit zero-padded TEXT primary key |
| sked_d_name | Census Schedule D | Official Census port name (ALL CAPS) |
| cbp_appendix_e_name | CBP Appendix E | CBP port name (Title Case, full state) |
| district_code | Census | First 2 digits of port_code |
| district_name | Census | District headquarters name |
| state | Derived | 2-letter state abbreviation |
| port_consolidated | Our classification | Grouping for reporting |
| port_coast | Our classification | East/West/Gulf/Great Lakes/Inland/Islands/Land Ports/N/A |
| port_region | Our classification | Sub-region for reporting |
| port_type | Our classification | seaport/airport/land_border/inland/courier/administrative/ftz |

### File Locations (must stay in sync)

| Path | Purpose |
|------|---------|
| `task_census/data/reference/port_reference.csv` | Working copy (549 codes) |
| `project_manifest/DICTIONARIES/port_reference.csv` | Manifest copy (identical) |
| `project_manifest/DICTIONARIES/ports_master.csv` | Panjiva text-to-code crosswalk (160 rows) |
| `task_census/data/port_dictionary.json` | Runtime dictionary with trade volumes |

### Build Chain

If you need to rebuild from scratch (you shouldn't — the CSV is the source):

```
parse_schedule_d.py        -> data/reference/census_schedule_d.csv
parse_appendix_e.py        -> data/reference/cbp_appendix_e_ports.csv
build_port_classifications.py -> data/reference/port_classifications.csv
build_unified_port_reference.py -> data/reference/port_reference.csv
```

After port_reference.csv exists, these consume it:

```
fix_zero_padding.py   -> restores zero-padding + copies to project_manifest
fix_ports_master.py   -> rebuilds ports_master.csv from port_reference.csv
build_port_dict.py    -> rebuilds port_dictionary.json from port_reference.csv + trade data
```

### Rules

1. NEVER modify port_reference.csv in code. Only human edits.
2. NEVER guess a port code from text. Look it up in port_reference.csv.
3. After editing port_reference.csv, always run fix_zero_padding.py.
4. The port_code column must always be 4-digit zero-padded TEXT ("0101" not "101").
5. For statistics, only port_type="seaport" matters (176 codes). Others are reference.
6. All runtime code loads from port_reference.csv via `load_port_reference()`.

### Python API

```python
from census_trade.config.port_codes import load_port_reference, DISTRICTS, LOWER_MISS_PORTS, get_district
ref = load_port_reference()  # dict keyed by port_code
```

## Country Reference Architecture

The **single source of truth** for all country lookups is:

    data/reference/country_reference.csv

### Primary Key

The 4-digit zero-padded country code (TEXT, e.g. "1220") is the absolute primary key.
It is the Census Schedule C code, used in `cty_code` across ALL trade data files.

### country_reference.csv Columns

| Column | Source | Description |
|--------|--------|-------------|
| cty_code | Census Schedule C | 4-digit zero-padded TEXT primary key |
| cty_name | Census Schedule C | Full country name (from country3.txt) |
| cty_abbrev | Census COUNTRY.TXT | 7-char abbreviation from Census data |
| iso_alpha2 | Census Schedule C | 2-letter ISO 3166-1 code |
| region | Our classification | Geographic region (11 regions) |
| sub_region | Our classification | Sub-region for reporting |

### File Locations (must stay in sync)

| Path | Purpose |
|------|---------|
| `task_census/data/reference/country_reference.csv` | Working copy (243 codes) |
| `project_manifest/DICTIONARIES/country_reference.csv` | Manifest copy (identical) |

### Build Chain

```
parse_schedule_c.py  -> data/reference/country_reference.csv + copies to manifest
```

### Rules

1. The cty_code column must always be 4-digit zero-padded TEXT ("1220" not "1220").
2. NEVER guess a country code from text. Look it up in country_reference.csv.
3. All runtime code loads from country_reference.csv via `load_country_reference()`.

### Python API

```python
from census_trade.config.country_codes import load_country_reference, REGIONS, get_region
ref = load_country_reference()  # dict keyed by cty_code
```

## Foreign Port Reference Architecture

The **single source of truth** for foreign port lookups is:

    data/reference/foreign_port_reference.csv

### Primary Key

The 5-digit zero-padded port code (TEXT, e.g. "35705") is the primary key.
These are CBP Schedule K codes from Appendix F.

### foreign_port_reference.csv Columns

| Column | Source | Description |
|--------|--------|-------------|
| port_code | Schedule K | 5-digit zero-padded TEXT primary key |
| port_name | CBP Appendix F | Port name from CBP |
| country | Derived | Country name as listed in Appendix F |
| cty_code | Cross-reference | Schedule C 4-digit country code |
| region | Our classification | Geographic region |

### File Locations (must stay in sync)

| Path | Purpose |
|------|---------|
| `task_census/data/reference/foreign_port_reference.csv` | Working copy (2,136 codes) |
| `project_manifest/DICTIONARIES/foreign_port_reference.csv` | Manifest copy (identical) |

### Build Chain

```
parse_schedule_k.py  -> data/reference/foreign_port_reference.csv + copies to manifest
```

### Note

Foreign port codes are **reference-only** — no field in current Census record layouts uses
Schedule K codes. They are needed for future port-call matching with vessel tracking data.

## Cargo HS6 Reference Architecture

The **single source of truth** for cargo classification is:

    data/cargo_hs6_dictionary.json  (built by build_cargo_dict.py)

The **upstream source** (human-edited) is:

    data/us_hs6_dictionary_sep_nov_2025_user.xlsx

### Primary Key

The 6-digit HS6 code (TEXT, e.g. "270900") is the primary key.
These are Harmonized System codes at the 6-digit level used in Census PORTHS6 trade data.

### cargo_hs6_dictionary.json Structure

The JSON has three top-level sections:

| Section | Description |
|---------|-------------|
| `_metadata` | Build info, counts, period |
| `hierarchy` | group → commodity → [cargo] nested tree |
| `cargo_to_hs6` | cargo name → {group, commodity, hs6_codes[], total_mt} |
| `hs6_lookup` | **Main lookup**: hs6_code → {description, group, commodity, cargo, cargo_detail, export_ves_mt, import_ves_mt, total_mt, mapping_source} |

### 3-Tier Mapping

Every HS6 code is classified via layered mapping:

| Tier | Source | Count | Description |
|------|--------|-------|-------------|
| 1 | `manual` | 2,788 | William's hand-classified codes (from Excel) |
| 2 | `heading` | 450 | Inherited from manual codes in same 4-digit HS heading |
| 3 | `chapter` | 2,353 | Broad default by HS chapter (built-in table in build script) |

Total: 5,591 codes, 0 unmapped. The `mapping_source` field on each entry records which tier.

### Cargo Groups (top-level)

5 groups: Dry Bulk, Liquid Bulk, Liquid Gas, Containerized, Dry

### Build Chain

```
build_cargo_dict.py  -> data/cargo_hs6_dictionary.json  (from Excel, 3-tier mapping)
```

After the JSON exists, these consume it:

```
census_trade/config/cargo_codes.py  -> API module (load_cargo_reference, get_cargo, get_group)
query_miss_river.py                 -> uses cargo_codes API for trade queries
generate_sample_report.py           -> HTML report at data/sample_cargo_report.html
```

### File Locations

| Path | Purpose |
|------|---------|
| `data/us_hs6_dictionary_sep_nov_2025_user.xlsx` | Excel source (William's mappings) |
| `data/cargo_hs6_dictionary.json` | Runtime dictionary (gitignored, rebuild with build_cargo_dict.py) |
| `build_cargo_dict.py` | Build script with 3-tier mapping logic + chapter default table |
| `census_trade/config/cargo_codes.py` | API module |
| `generate_sample_report.py` | HTML report generator |

### Rules

1. The Excel file is the upstream source. Manual mapping changes go there.
2. After editing the Excel, run `python build_cargo_dict.py` to rebuild the JSON.
3. The JSON is gitignored — it is a build artifact.
4. NEVER guess an HS6 classification from text. Look it up via the API.
5. All runtime code loads via `load_cargo_reference()` from cargo_codes.py.
6. Chapter default table lives in build_cargo_dict.py (CHAPTER_DEFAULTS dict).

### Python API

```python
from census_trade.config.cargo_codes import load_cargo_reference, CARGO_GROUPS, get_cargo, get_group
ref = load_cargo_reference()   # dict keyed by HS6 code
info = get_cargo('270900')     # {'group': 'Liquid Bulk', 'commodity': 'Petroleum Products', 'cargo': 'Crude Oil', 'cargo_detail': 'Crude Oil'}
grp = get_group('270900')      # 'Liquid Bulk'
```
