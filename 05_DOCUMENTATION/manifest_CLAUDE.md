# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

This is a **maritime cargo classification system** for U.S. import data. It processes 1.3M+ Panjiva shipment records (2023-2025) through a multi-phase classification pipeline that assigns cargo to a 4-level taxonomy (Group > Commodity > Cargo > Cargo_Detail) using rule-based pattern matching.

**Dataset**: 854,870 records, 1.35 billion tons (deduplicated from 1,302,246 raw records)
**Classification**: 100% complete - 560,091 classified (65.5%), 294,779 excluded (34.5%)

**Working Directory**: `G:\My Drive\LLM\project_manifest\` (Google Drive File Stream on Windows)

---

## Python Environment

- Python 3.8+
- Required packages: `pandas`, `numpy`
- `pip install pandas numpy`

---

## Directory Structure

```
project_manifest/
├── PIPELINE/                         # 8-phase classification pipeline
│   ├── phase_00_preprocessing/       # Raw → preprocessed (dedup, HS codes, vessel enrich)
│   │   ├── phase_00_preprocess.py
│   │   ├── phase_00_output.csv       # Output: preprocessed data
│   │   └── test/
│   ├── phase_01_white_noise/         # Remove junk (ship spares, FROB, <2 tons)
│   │   ├── phase_01_white_noise.py
│   │   ├── phase_00_output.csv       # Copy of input (read-only)
│   │   ├── phase_01_output.csv
│   │   └── test/
│   ├── phase_02_carrier_exclusions/  # Mark cruise/tug/forwarder carriers EXCLUDED
│   │   ├── phase_02_carrier_exclusions.py
│   │   ├── phase_01_output.csv       # Copy of input (read-only)
│   │   ├── phase_02_output.csv
│   │   └── test/
│   ├── phase_03_carrier_classification/  # RoRo, Reefer carrier locks
│   │   ├── phase_03_carrier_classification.py
│   │   ├── phase_02_output.csv
│   │   ├── phase_03_output.csv
│   │   └── test/
│   ├── phase_04_main_classification/ # Keyword + HS code rules from dictionary
│   │   ├── phase_04_main_classification.py
│   │   ├── phase_03_output.csv
│   │   ├── phase_04_output.csv
│   │   └── test/
│   ├── phase_05_hs4_alignment/       # HS4 statistical inference
│   │   ├── phase_05_hs4_alignment.py
│   │   ├── phase_04_output.csv
│   │   ├── phase_05_output.csv
│   │   └── test/
│   ├── phase_06_final_catchall/      # Remaining → General Cargo (100% coverage)
│   │   ├── phase_06_final_catchall.py
│   │   ├── phase_05_output.csv
│   │   ├── phase_06_output.csv
│   │   └── test/
│   ├── phase_07_enrichment/          # Vessel specs + port groupings
│   │   ├── phase_07_enrichment.py
│   │   ├── phase_06_output.csv
│   │   ├── phase_07_output.csv       # ← FINAL PIPELINE OUTPUT
│   │   └── test/
│   └── pipeline_utils.py            # Shared functions
│
├── DICTIONARIES/                     # All reference data (ONE file each, no versions)
│   ├── cargo_classification.csv      # Main classification rules
│   ├── ships_register.csv            # Ship registry (5.4 MB)
│   ├── ports_master.csv              # Port consolidation
│   ├── carrier_scac.csv              # Carrier SCAC mappings
│   ├── carrier_exclusions.csv        # Excluded carriers
│   ├── carrier_classification_rules.csv  # RoRo/Reefer carrier rules
│   ├── white_noise_filter.csv        # White noise keywords
│   ├── hs4_alignment.csv             # HS4 statistical rules
│   └── hs_codes/
│       ├── hs2_lookup.csv
│       ├── hs4_lookup.csv
│       └── hs6_lookup.csv
│
├── RAW_DATA/                         # Untouched source files
│   ├── 00_01_panjiva_imports_raw/    # 170 Panjiva CSV files
│   ├── 00_02_panjiva_exports_raw/
│   ├── 00_03_usace_entrance_clearance_raw/
│   └── 00_04_fgis_raw/
│
├── REFINEMENT/                       # Post-pipeline enrichment (reads phase_07_output.csv)
│   ├── party_harmonization/
│   │   ├── harmonize_parties.py
│   │   ├── party_dictionary.csv
│   │   └── test/
│   ├── commodity_refinement/
│   │   ├── refine_cement.py
│   │   ├── refine_steel.py
│   │   ├── refine_scm_aggregates.py
│   │   └── test/
│   └── analysis/
│       └── voyage_portcall_summary.py
│
├── DOCUMENTATION/
│   ├── ARCHITECTURE.md
│   ├── PIPELINE_RULES.md
│   └── dashboards/                   # HTML dashboards
│
├── _archive/                         # Historical snapshots
│   ├── 2026-01-16_pre_reorganization/
│   └── 2026-02-12_pre_reorg/         # Previous folder structure
│
├── user_notes/                       # User working files
├── CLAUDE.md
├── README.md
├── .gitignore
└── requirements.txt
```

---

## Pipeline Data Flow

Each phase reads the PREVIOUS phase's output. To re-run a phase, delete its output and re-run.

```
RAW_DATA/00_01_panjiva_imports_raw/*.csv
    ↓ phase_00_preprocess.py
phase_00_output.csv  (deduplicated, columns standardized, HS codes extracted)
    ↓ phase_01_white_noise.py
phase_01_output.csv  (ship spares, FROB, <2 tons marked EXCLUDED)
    ↓ phase_02_carrier_exclusions.py
phase_02_output.csv  (cruise/tug/forwarder carriers marked EXCLUDED)
    ↓ phase_03_carrier_classification.py
phase_03_output.csv  (RoRo, Reefer carrier locks applied)
    ↓ phase_04_main_classification.py
phase_04_output.csv  (keyword + HS code rules applied)
    ↓ phase_05_hs4_alignment.py
phase_05_output.csv  (HS4 code refinement)
    ↓ phase_06_final_catchall.py
phase_06_output.csv  (remaining → General Cargo, 100% coverage)
    ↓ phase_07_enrichment.py
phase_07_output.csv  (vessel specs + port groupings) ← FINAL
```

---

## Running the Pipeline

**Test-first workflow** (MANDATORY for every phase):

1. Phase X completes → `phase_x_output.csv` confirmed working
2. Copy `phase_x_output.csv` into `phase_(x+1)/` folder as input
3. Extract 3-month sample → save as `test/test_sample.csv`
4. Run phase_(x+1) script on `test/test_sample.csv` → `test/test_output.csv`
5. Validate test output
6. ONLY THEN run on full data → `phase_(x+1)_output.csv`

**Running a single phase**:
```bash
cd "G:\My Drive\LLM\project_manifest\PIPELINE\phase_04_main_classification"
python phase_04_main_classification.py
```

**Running preprocessing**:
```bash
cd "G:\My Drive\LLM\project_manifest\PIPELINE\phase_00_preprocessing"
python phase_00_preprocess.py              # Full run
python phase_00_preprocess.py --sample 5000  # Test with 5K records
python phase_00_preprocess.py --year 2024    # Single year
```

---

## Dictionary-Driven Classification

**Critical**: Classification rules live in CSV dictionaries, NOT in Python code. Scripts are generic engines that execute dictionary rules.

**Main Dictionary**: `DICTIONARIES/cargo_classification.csv`

**Editing rules**:
1. Edit `DICTIONARIES/cargo_classification.csv` directly
2. Test on a sample before running full pipeline
3. Never add classification logic to Python scripts

**4-Level Taxonomy**: Group > Commodity > Cargo > Cargo_Detail

**Column Name Note**: Dictionary uses `Cargo_Detail` (underscore), but some scripts output `Cargo Detail` (space). Be aware of this inconsistency.

---

## Key Rules

1. **ONE output file per phase** - fixed name, no timestamps, no versions
2. **Re-run overwrites** - re-running phase 4 overwrites `phase_04_output.csv`
3. **Recovery = delete + re-run** - if phase 5 breaks, delete `phase_05_output.csv` and re-run
4. **NO new values without user approval** - never add Commodity/Group values not in the dictionary
5. **Dictionary is the single source of truth** - scripts read rules from CSVs
6. **Never edit rules in Python code** - always edit the CSV dictionary
7. **Test on sample first** - use the `test/` subfolder before running on full data
8. **Large files stay on Google Drive** - never commit CSVs >10 MB to git
9. **Carrier matching is substring** - "SCAC - Name" format requires `SCAC in record_carrier`

---

## Git Workflow

**Large files excluded** via `.gitignore`:
- All CSV data files (pipeline outputs, raw data)
- Archive folder (`_archive/`)
- User working files (`user_notes/`)

**What IS tracked**:
- Pipeline scripts (`PIPELINE/`)
- Dictionary files (`DICTIONARIES/`)
- Documentation (`DOCUMENTATION/`)
- CLAUDE.md, README.md, .gitignore, requirements.txt

---

## Troubleshooting

**Path Not Found**: Verify Google Drive File Stream is mounted at `G:\`. All scripts use `Path(__file__).resolve().parent` for relative paths.

**Column Name Errors**: Some contexts use `Cargo Detail` (space), others `Cargo_Detail` (underscore). Check output column names.

**Classification Issues**: Check dictionary rules (Phase, Active, Keywords columns). Test with sample data first.

---

## Reference

- `DOCUMENTATION/ARCHITECTURE.md` - Complete system reference
- `DOCUMENTATION/PIPELINE_RULES.md` - Pipeline rule mechanics
- `DOCUMENTATION/dashboards/` - Interactive HTML dashboards
- `_archive/2026-02-12_pre_reorg/` - Previous folder structure (complete rollback available)
