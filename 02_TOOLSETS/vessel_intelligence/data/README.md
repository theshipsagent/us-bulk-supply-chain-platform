# DICTIONARIES

Authoritative reference files for the project. Each CSV uses a fixed code as its primary key.

## Port Code Files

### port_reference.csv (Single Source of Truth)

549 US port codes from Census Schedule D + CBP Appendix E, with our classifications.

- **Primary key**: `port_code` (4-digit zero-padded TEXT, e.g. "0101")
- **Sources**: Census Schedule D (sked_d_name), CBP Appendix E (cbp_appendix_e_name)
- **Our classifications**: port_consolidated, port_coast, port_region, port_type
- **Built by**: `task_census/build_unified_port_reference.py`
- **Maintained by**: Human edit only, then run `task_census/fix_zero_padding.py`
- **176 seaports** (used for statistics), rest kept as reference

### ports_master.csv (Panjiva Text Crosswalk)

160 Panjiva discharge text strings mapped to Census port codes.

- **Purpose**: Match raw Panjiva "Port of Discharge" text to the correct 4-digit port_code
- **Port_Code validated against**: port_reference.csv (zero orphans)
- **Consolidated/Coast/Region pulled from**: port_reference.csv
- **Rebuilt by**: `task_census/fix_ports_master.py`

## Country Code Files

### country_reference.csv (Single Source of Truth)

243 country/territory codes from Census Schedule C, with our region classifications.

- **Primary key**: `cty_code` (4-digit zero-padded TEXT, e.g. "1220" = Canada)
- **Sources**: Census COUNTRY.TXT (cty_abbrev), Census country3.txt (cty_name, iso_alpha2)
- **Our classifications**: region, sub_region
- **Built by**: `task_census/parse_schedule_c.py`
- **Validated against**: All `cty_code` values in Census trade data (zero orphans)

### foreign_port_reference.csv (Reference Only)

2,136 foreign port codes from CBP Appendix F (Schedule K).

- **Primary key**: `port_code` (5-digit zero-padded TEXT, e.g. "35705" = Buenos Aires)
- **Source**: CBP Appendix F PDF (Schedule K foreign port codes)
- **Cross-reference**: `cty_code` links to country_reference.csv
- **Built by**: `task_census/parse_schedule_k.py`
- **Status**: Reference-only (not in current Census record layouts)

## Other Dictionaries

| File | Description |
|------|-------------|
| cargo_classification.csv | Cargo type classification rules |
| carrier_scac.csv | SCAC carrier codes |
| carrier_exclusions.csv | Carriers to exclude |
| carrier_classification_rules.csv | Carrier classification rules |
| white_noise_filter.csv | Noise filtering rules |
| ships_register.csv | Vessel registry |
| hs4_alignment.csv | HS4 code alignment |
| hs_codes/ | HS code lookups (hs2, hs4, hs6) |

## Rules

1. port_reference.csv is NEVER modified by code. Only explicit human edits.
2. After any edit to port_reference.csv, run `task_census/fix_zero_padding.py` to restore zero-padding.
3. The copy here must always match `task_census/data/reference/port_reference.csv`.
4. All port_code values are 4-digit zero-padded TEXT. Never numeric.
5. country_reference.csv and foreign_port_reference.csv copies must match `task_census/data/reference/`.
