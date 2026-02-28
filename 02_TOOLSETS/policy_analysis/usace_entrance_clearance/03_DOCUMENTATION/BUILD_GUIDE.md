# USACE Entrance & Clearance Processing - Build Guide

**Complete Documentation for Building and Running the USACE Data Processing Pipeline**

---

## Table of Contents

1. [Overview](#overview)
2. [Project Purpose](#project-purpose)
3. [Architecture](#architecture)
4. [Directory Structure](#directory-structure)
5. [Dictionary Files](#dictionary-files)
6. [Processing Pipeline](#processing-pipeline)
7. [Data Flow](#data-flow)
8. [Script Details](#script-details)
9. [Output Schema](#output-schema)
10. [Troubleshooting](#troubleshooting)
11. [Master Project Reference](#master-project-reference)

---

## Overview

This is an **isolated, standalone project** for processing USACE (U.S. Army Corps of Engineers) Entrance and Clearance data. It was bifurcated from the master maritime cargo classification system to provide a focused, self-contained environment for USACE data transformation.

**Version**: v3.0.0
**Date**: 2026-02-05
**Status**: Production Ready

---

## Project Purpose

### What This Project Does

Transforms raw USACE port arrival and departure records into enriched datasets suitable for:

- **Port call analysis** - Understanding vessel movements through U.S. ports
- **Cargo flow analysis** - Tracking import/export patterns
- **Vessel utilization studies** - Analyzing vessel capacity and activity
- **Maritime transportation research** - Academic and policy research

### Why This Was Bifurcated

The master project (`G:\My Drive\LLM\project_manifest`) is a comprehensive maritime cargo classification system processing 1.3M+ Panjiva shipment records. The USACE entrance/clearance processing is a distinct workflow that:

1. **Uses different source data** - USACE port records vs. Panjiva customs records
2. **Has different objectives** - Port activity tracking vs. cargo classification
3. **Stands alone** - Can operate independently without Panjiva data
4. **Benefits from isolation** - Cleaner testing and development environment

---

## Architecture

### High-Level Flow

```
Raw Excel File
    ↓
[Step 1: Split Excel to CSV]
    ↓
Inbound CSV     Outbound CSV
    ↓                ↓
[Step 2: Transform] [Step 3: Transform]
    ↓                ↓
Enriched Entrance   Enriched Clearance
    Records             Records
```

### Key Design Principles

1. **Dictionary-Driven** - All reference data externalized to CSV files
2. **Portable Paths** - Scripts auto-detect project root for flexibility
3. **Modular Design** - Each step can run independently
4. **Verbose Logging** - Detailed progress and statistics output
5. **Idempotent** - Safe to re-run without side effects

---

## Directory Structure

```
task_usace_entrance_clearance/
│
├── 00_DATA/
│   ├── 00.01_RAW/                    # Raw input files
│   │   ├── Entrances_Clearances_2023.xlsx          # Original Excel file
│   │   ├── Entrances_Clearances_2023_2023_Inbound.csv    # Inbound records
│   │   ├── Entrances_Clearances_2023_2023_Outbound.csv   # Outbound records
│   │   └── Entrances_Clearances_2023_Definition.csv      # Field definitions
│   │
│   └── 00.02_PROCESSED/              # Transformed output files
│       ├── usace_2023_inbound_entrance_transformed_v3.0.0.csv
│       └── usace_2023_outbound_clearance_transformed_v3.0.0.csv
│
├── 01_DICTIONARIES/                   # All reference data
│   ├── 01_ships_register.csv         # 50K+ vessel specs (5.4 MB)
│   ├── agency_fee_by_icst.csv        # Agency fees by vessel type
│   ├── icst_vessel_codes.md          # ICST documentation
│   ├── usace_cargoclass.csv          # Cargo classification rules
│   ├── usace_port_codes_from_data.csv # USACE port codes
│   ├── usace_sked_k_foreign_ports.csv # Foreign ports (Schedule K)
│   └── usace_to_census_port_mapping.csv # Port mapping table
│
├── 02_SCRIPTS/                        # Processing scripts
│   ├── split_excel_to_csv.py         # Step 1: Excel → CSV
│   ├── transform_usace_entrance_data.py # Step 2: Entrance transformation
│   ├── transform_usace_clearance_data.py # Step 3: Clearance transformation
│   └── run_usace_pipeline.py         # Master orchestrator
│
├── 03_DOCUMENTATION/                  # Documentation
│   └── BUILD_GUIDE.md                # This file
│
├── logs/                              # Processing logs (empty initially)
├── previous_build/                    # Original files from master project
├── requirements.txt                   # Python dependencies
└── README.md                          # Quick start guide
```

---

## Dictionary Files

### 1. `01_ships_register.csv` (5.4 MB)

**Purpose**: International vessel registry with specifications

**Key Columns**:
- `IMO` - International Maritime Organization number (unique vessel ID)
- `Vessel` - Vessel name
- `Type` - Vessel type (Bulk Carrier, Tanker, Container, etc.)
- `DWT` - Deadweight tonnage
- `Grain` - Grain capacity (cubic meters)
- `TPC` - Tonnes per centimeter immersion
- `Dwt_Draft(m)` - Draft at maximum DWT (meters)

**Usage**: Matched by IMO number (primary) or vessel name (fallback) to enrich USACE records with vessel specifications.

---

### 2. `usace_port_codes_from_data.csv` (15 KB)

**Purpose**: USACE-specific port codes and names

**Columns**:
- `Port_Code` - USACE 4-digit port code (e.g., "4301" for New Orleans)
- `Port_Name` - Port name (e.g., "NEW ORLEANS, LA")

**Usage**: Converts USACE PORT codes to human-readable port names. Extracted directly from USACE data to ensure complete coverage.

**Example**:
```csv
Port_Code,Port_Name
4301,NEW ORLEANS, LA
1401,NEW YORK, NY
2704,HOUSTON, TX
```

---

### 3. `usace_to_census_port_mapping.csv` (27 KB)

**Purpose**: Maps USACE ports to Census Bureau statistical port categories

**Key Columns**:
- `USACE_PORT` - USACE port name
- `Match_Type` - Quality of match (EXACT, PARTIAL, NO MATCH)
- `Census_Code` - Census Bureau port code
- `Census_Sked_D_E` - Census Schedule D/E port name
- `Port_Consolidated` - Consolidated port name for rollups
- `Port_Coast` - Coast (Gulf Coast, Atlantic, Pacific, Great Lakes)
- `Port_Region` - Geographic region

**Coverage**: 44.3% of USACE ports have matching Census statistical categories

**Usage**: Enables aggregation to Census Bureau port groupings for statistical analysis.

---

### 4. `usace_sked_k_foreign_ports.csv` (109 KB)

**Purpose**: Foreign port codes from USACE Schedule K

**Columns**:
- `FORPORT_CD` - Foreign port code
- `FORPORT_NAME` - Foreign port name
- `CTRY_NAME` - Country name

**Usage**: Converts WHERE_SCHEDK codes (last foreign port of call) to port names and countries.

**Example**:
```csv
FORPORT_CD,FORPORT_NAME,CTRY_NAME
0101,AMSTERDAM,NETHERLANDS
0201,ANTWERP,BELGIUM
```

---

### 5. `usace_cargoclass.csv` (1.3 KB)

**Purpose**: Cargo classification rules based on ICST vessel type

**Columns**:
- `icst type` - ICST vessel type description (uppercase)
- `Group` - Cargo group (e.g., "Dry Bulk", "Liquid Bulk")
- `Commodity` - Specific commodity (e.g., "Grains", "Petroleum")

**Usage**: Assigns cargo type based on vessel type (ICST_DESC field).

**Example**:
```csv
icst type,Group,Commodity
BULK CARRIER,Dry Bulk,General Dry Bulk
OIL TANKER,Liquid Bulk,Petroleum
CONTAINER SHIP,Containerized,General Cargo
```

---

### 6. `agency_fee_by_icst.csv` (1.0 KB)

**Purpose**: Agency fee schedule by vessel type

**Columns**:
- `ICST_DESC` - ICST vessel type description
- `Agency_Fee` - Fee amount or category

**Usage**: Assigns agency fees based on vessel type.

---

### 7. `icst_vessel_codes.md` (2.6 KB)

**Purpose**: Documentation of ICST (International Classification of Ships by Type) codes

**Format**: Markdown reference document

**Usage**: Human reference for understanding ICST vessel type codes used in USACE data.

---

## Processing Pipeline

### Complete Pipeline (Recommended)

```bash
python 02_SCRIPTS/run_usace_pipeline.py
```

This runs all three steps in sequence:

1. **Split Excel** → Separate Inbound and Outbound CSVs
2. **Transform Entrance** → Enriched entrance records
3. **Transform Clearance** → Enriched clearance records

**Runtime**: ~10-15 minutes for 2023 data (127K records total)

---

### Individual Steps

#### Step 1: Split Excel to CSV

```bash
python 02_SCRIPTS/split_excel_to_csv.py
```

**What it does**:
- Reads multi-worksheet Excel file
- Extracts each worksheet to separate CSV
- Preserves all data types and formatting

**Input**: `00_DATA/00.01_RAW/Entrances_Clearances_2023.xlsx`

**Output**:
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Inbound.csv`
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Outbound.csv`
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_Definition.csv`

**Runtime**: ~30 seconds

---

#### Step 2: Transform Entrance Data

```bash
python 02_SCRIPTS/transform_usace_entrance_data.py
```

**What it does**:
- Loads 6 dictionary files
- Converts numeric codes to descriptive text
- Maps ports to names and statistical categories
- Matches vessels to specs (IMO/name lookup)
- Calculates draft percentage and forecasts activity
- Classifies cargo by vessel type
- Assigns agency fees

**Input**: `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Inbound.csv`

**Output**: `00_DATA/00.02_PROCESSED/usace_2023_inbound_entrance_transformed_v3.0.0.csv`

**Runtime**: ~5-7 minutes

**Expected Statistics**:
- USACE Port Mapping: 100%
- Census Port Categories: 44.3%
- Vessel Specs (IMO/Name): 70-80%
- Draft % Calculated: 60-70%
- Cargo Classification: 90-95%
- Agency Fees: 90-95%

---

#### Step 3: Transform Clearance Data

```bash
python 02_SCRIPTS/transform_usace_clearance_data.py
```

**What it does**: Same as Step 2, but for outbound/export records

**Input**: `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Outbound.csv`

**Output**: `00_DATA/00.02_PROCESSED/usace_2023_outbound_clearance_transformed_v3.0.0.csv`

**Runtime**: ~5-7 minutes

---

## Data Flow

### Input Schema (Raw USACE Data)

| Field | Description | Example |
|-------|-------------|---------|
| TYPEDOC | Type document (0=Import, 1=Export) | 0 |
| ECDATE | Entrance/clearance date (MMDDYY) | 010523 |
| PORT | US port code (4 digits) | 4301 |
| PWW_IND | Port/Waterway indicator (P/W) | P |
| PORT_NAME | Port name | NEW ORLEANS, LA |
| VESSNAME | Vessel name | NORD VENUS |
| RIG | Vessel rig code | 2 |
| RIG_DESC | Vessel rig description | SELF PROPELLED |
| ICST | ICST code | 31 |
| ICST_DESC | ICST description | BULK CARRIER |
| FLAG | Flag code | US |
| FLAG_CTRY | Flag country | UNITED STATES |
| WHERE_IND | Domestic/Foreign indicator (D/F) | F |
| WHERE_PORT | Previous domestic port code | |
| WHERE_SCHEDK | Previous foreign port code | 4801 |
| WHERE_NAME | Previous port name | TAMPICO |
| WHERE_CTRY | Previous port country | MEXICO |
| NRT | Net registered tonnage | 35162 |
| GRT | Gross registered tonnage | 58052 |
| DRAFT_FT | Draft feet | 36 |
| DRAFT_IN | Draft inches | 3 |
| CONTAINER | Container indicator | N |
| IMO | IMO vessel number | 9304880 |

---

### Output Schema (Transformed Data)

**Total Columns**: 53

#### Core Identification (4 columns)
- `RECID` - Sequential record ID (1 to N)
- `Count` - Always 1 (for aggregation)
- `TYPEDOC` - Imports/Exports (transformed from 0/1)
- `Arrival_Date` or `Clearance_Date` - Date (renamed from ECDATE)

#### US Port Arrival/Clearance (7 columns)
- `PORT` - USACE port code
- `Arrival_Port_Name` / `Clearance_Port_Name` - Port name
- `US_Port_USACE` - USACE port name (from dictionary)
- `Port_Consolidated` - Census consolidated port
- `Port_Coast` - Coast (Gulf/Atlantic/Pacific/Great Lakes)
- `Port_Region` - Geographic region
- `PWW_IND` - Port/Waterway (transformed from P/W)

#### Vessel (10 columns)
- `Vessel` - Vessel name
- `IMO` - IMO number
- `RIG_DESC` - Self-propelled/Towed
- `ICST_DESC` - ICST vessel type
- `FLAG_CTRY` - Flag country
- `NRT` - Net registered tonnage
- `GRT` - Gross registered tonnage
- `DRAFT_FT` - Draft feet
- `DRAFT_IN` - Draft inches
- `CONTAINER` - Container indicator

#### Vessel Specifications (7 columns)
- `Vessel_Type` - Type from registry
- `Vessel_DWT` - Deadweight tonnage
- `Vessel_Grain` - Grain capacity (m³)
- `Vessel_TPC` - Tonnes per centimeter
- `Vessel_Dwt_Draft_m` - Max draft (meters)
- `Vessel_Dwt_Draft_ft` - Max draft (feet, calculated)
- `Vessel_Match_Method` - IMO/Name

#### Draft Analysis (2 columns)
- `Draft_Pct_of_Max` - Draft as % of max (e.g., "78.3")
- `Forecasted_Activity` - Load/Discharge (>50% = Discharge)

#### Previous Port (8 columns)
- `WHERE_IND` - Foreign/Coastwise (transformed from F/D)
- `WHERE_PORT` - Previous domestic port code
- `Previous_US_Port_USACE` - Previous US port name
- `WHERE_SCHEDK` - Previous foreign port code
- `Previous_Foreign_Port` - Previous foreign port name
- `Previous_Foreign_Country` - Previous foreign country
- `WHERE_NAME` - Previous port name (original)
- `WHERE_CTRY` - Previous country (original)

#### Cargo Classification (2 columns)
- `Group` - Cargo group (from ICST)
- `Commodity` - Commodity (from ICST)

#### Tonnage & Carrier (2 columns)
- `Tons` - Placeholder (empty)
- `Carrier_Name` - Placeholder (empty)

#### Agency Fees (2 columns)
- `Agency_Fee` - Fee (from ICST)
- `Agency_Fee_Adj` - Placeholder (empty)

---

## Script Details

### `split_excel_to_csv.py`

**Purpose**: Splits multi-worksheet Excel file into separate CSVs

**Dependencies**: pandas, openpyxl

**Key Functions**:
- `split_excel_to_csv(excel_file)` - Main processing function

**Logic**:
1. Read Excel file with `pd.read_excel(..., sheet_name=None)`
2. Iterate through worksheets
3. Save each as CSV with worksheet name in filename
4. Report rows and columns for each

**Customization**: Change input/output paths in `main()` function

---

### `transform_usace_entrance_data.py`

**Purpose**: Transform entrance (inbound/imports) records

**Dependencies**: pandas, numpy, re

**Key Functions**:
- `transform_entrance_data(input_file, output_file, dict_path, test_mode)` - Main transformation
- `normalize_name(name)` - Vessel name normalization for fuzzy matching

**Logic Flow**:
1. **Load Dictionaries** (6 files)
   - USACE port codes
   - Port-to-Census mapping
   - Foreign ports (Schedule K)
   - Ships register (IMO and name lookups)
   - Cargo classification
   - Agency fees

2. **Read Input Data**
   - Full file or first 100 rows (test_mode)
   - Convert numeric codes to clean text

3. **Apply Transformations**
   - TYPEDOC: 0→Imports, 1→Exports
   - PWW_IND: P→Port, W→Waterway
   - WHERE_IND: F→Foreign, D→Coastwise

4. **Map Ports**
   - USACE port codes → port names
   - USACE ports → Census categories
   - Domestic previous ports
   - Foreign previous ports (Schedule K)

5. **Match Vessels**
   - Try IMO match first (exact)
   - Fall back to normalized name match
   - Extract specs: Type, DWT, Grain, TPC, Draft

6. **Calculate Draft Analysis**
   - Actual draft = DRAFT_FT + (DRAFT_IN / 12)
   - Draft % = (Actual / Max) × 100
   - Forecast: >50% = Discharge, ≤50% = Load

7. **Classify Cargo**
   - Match ICST_DESC to cargo dictionary
   - Assign Group and Commodity

8. **Assign Agency Fees**
   - Match ICST_DESC to fee schedule

9. **Add Placeholders**
   - Tons, Carrier_Name, Agency_Fee_Adj

10. **Finalize**
    - Add Count (1) and RECID (sequential)
    - Rename columns
    - Select final column set
    - Save output

**Customization**: Paths are auto-detected from script location using `Path(__file__).parent.parent`

---

### `transform_usace_clearance_data.py`

**Purpose**: Transform clearance (outbound/exports) records

**Notes**: Identical logic to `transform_usace_entrance_data.py`, but:
- Uses different input file (Outbound.csv)
- Renames `ECDATE` to `Clearance_Date` instead of `Arrival_Date`
- Renames `PORT_NAME` to `Clearance_Port_Name` instead of `Arrival_Port_Name`

---

### `run_usace_pipeline.py`

**Purpose**: Orchestrate complete pipeline execution

**Dependencies**: subprocess, pathlib, datetime

**Key Functions**:
- `run_script(script_path, script_name)` - Execute Python script
- `print_header(message)` - Formatted section headers
- `print_step(step_num, message)` - Formatted step messages

**Logic**:
1. **Setup**
   - Detect project root
   - Create output directories
   - Record start time

2. **Step 1: Split Excel**
   - Check if CSVs already exist → skip
   - Check if Excel exists → run split script
   - If neither → abort with error

3. **Step 2: Transform Entrance**
   - Check if Inbound CSV exists
   - Run transform script
   - Track success/failure

4. **Step 3: Transform Clearance**
   - Check if Outbound CSV exists
   - Run transform script
   - Track success/failure

5. **Summary**
   - Report status of all steps
   - Calculate total runtime
   - List output files
   - Exit with success/failure code

**Features**:
- Skips unnecessary steps (CSVs already exist)
- Continues on non-fatal errors
- Comprehensive logging
- Clear success/failure indicators

---

## Troubleshooting

### Issue: "File not found" errors

**Cause**: Google Drive File Stream not mounted or files missing

**Solution**:
```bash
# Check Drive mounting
ls "G:\My Drive"

# Check project files
ls "G:\My Drive\LLM\task_usace_entrance_clearance"

# Check raw data
ls "G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.01_RAW"
```

---

### Issue: Low vessel match rates (<50%)

**Cause**: `01_ships_register.csv` corrupted or incomplete

**Solution**:
```bash
# Check file size
ls -lh "01_DICTIONARIES/01_ships_register.csv"
# Expected: ~5.4 MB

# Check record count
python -c "import pandas as pd; df = pd.read_csv('01_DICTIONARIES/01_ships_register.csv'); print(f'{len(df):,} vessels')"
# Expected: 50,000+ vessels

# Re-copy from master project if needed
cp "G:\My Drive\LLM\project_manifest\01_DICTIONARIES\01.03_vessels\01_ships_register.csv" "01_DICTIONARIES/"
```

---

### Issue: Port mapping rates lower than expected

**Cause**: Dictionary file version mismatch

**Solution**: Re-copy dictionaries from master project:
```bash
cp "G:\My Drive\LLM\project_manifest\01_DICTIONARIES\01.02_ports\usace_to_census_port_mapping.csv" "01_DICTIONARIES/"
```

---

### Issue: Script hangs or takes too long

**Cause**: Large dataset causing memory issues

**Solution**: Enable test mode to process first 100 rows only:

```python
# In transform_usace_entrance_data.py, line 538:
df_final = transform_entrance_data(INPUT_FILE, OUTPUT_FILE, DICT_PATH, test_mode=True)
```

---

### Issue: Unicode or encoding errors

**Cause**: Special characters in vessel names or port names

**Solution**: Scripts use UTF-8 by default. If issues persist:
```python
# Add encoding parameter to read_csv
df = pd.read_csv(input_file, encoding='utf-8-sig')
```

---

## Master Project Reference

### Relationship to Master Project

This isolated project was extracted from:

**Master Project Path**: `G:\My Drive\LLM\project_manifest`

**Original Script Locations**:
- `02_SCRIPTS/02.01_preprocessing/split_excel_to_csv.py`
- `02_SCRIPTS/02.01_preprocessing/transform_usace_entrance_data.py`
- `02_SCRIPTS/02.01_preprocessing/transform_usace_clearance_data.py`

**Original Dictionary Locations**:
- `01_DICTIONARIES/01.02_ports/` - Port dictionaries
- `01_DICTIONARIES/01.03_vessels/` - Vessel registry
- `_archive/2026-01-16_pre_reorganization/01.01_dictionary/` - USACE-specific dictionaries

---

### Key Master Project Documents

#### `00_START_HERE.md`
- Overview of full classification system
- v2.0.0 classification results
- Quick start commands

#### `CLAUDE.md`
- Complete technical guide
- Pipeline architecture
- Dictionary-driven design principles
- Lock system for classification rules

#### `CLASSIFICATION_3YEAR_COMPARISON_v2.0.0.md`
- Results from classifying 862,980 Panjiva records
- Phase-by-phase breakdown
- Vessel enrichment statistics

---

### Differences from Master Project

| Aspect | Master Project | Isolated Project |
|--------|---------------|------------------|
| **Data Source** | Panjiva customs data | USACE entrance/clearance |
| **Scope** | 1.3M+ shipment records | 127K port calls (2023) |
| **Primary Goal** | Cargo classification | Port activity tracking |
| **Dictionary Size** | 668 classification rules | 6 reference tables |
| **Processing Time** | 13-15 hours (full year) | 10-15 minutes |
| **Dependencies** | Requires Panjiva data | Self-contained |

---

### Integration Path

To integrate USACE transformed data back into master project:

1. **Match USACE entrance records to Panjiva imports**:
   - Script: `02_SCRIPTS/02.02_matching/match_entrance_to_imports_SIMPLE.py`
   - Keys: Vessel + Date + Port

2. **Match USACE clearance records to Panjiva exports**:
   - Script: `02_SCRIPTS/02.02_matching/match_clearance_to_exports_SIMPLE.py`
   - Keys: Vessel + Date + Port

3. **Create port call master**:
   - Script: `02_SCRIPTS/02.02_matching/marry_entrance_clearance_SIMPLE.py`
   - Combines entrance + clearance + Panjiva matches

---

## Appendix

### Sample Output Record (Entrance)

```csv
RECID,Count,TYPEDOC,Arrival_Date,PORT,Arrival_Port_Name,US_Port_USACE,Port_Consolidated,Port_Coast,Port_Region,PWW_IND,Vessel,IMO,RIG_DESC,ICST_DESC,FLAG_CTRY,NRT,GRT,DRAFT_FT,DRAFT_IN,CONTAINER,Vessel_Type,Vessel_DWT,Vessel_Grain,Vessel_TPC,Vessel_Dwt_Draft_m,Vessel_Dwt_Draft_ft,Vessel_Match_Method,Draft_Pct_of_Max,Forecasted_Activity,WHERE_IND,WHERE_PORT,Previous_US_Port_USACE,WHERE_SCHEDK,Previous_Foreign_Port,Previous_Foreign_Country,WHERE_NAME,WHERE_CTRY,Group,Commodity,Tons,Carrier_Name,Agency_Fee,Agency_Fee_Adj
1,1,Imports,010523,4301,NEW ORLEANS,NEW ORLEANS LA,New Orleans,Gulf Coast,South Central,Port,NORD VENUS,9304880,SELF PROPELLED,BULK CARRIER,LIBERIA,35162,58052,36,3,,Bulk Carrier,82545,105872,138.56,13.81,45.31,IMO,80.3,Discharge,Foreign,,,,TAMPICO,MEXICO,TAMPICO,MEXICO,Dry Bulk,General Dry Bulk,,,1250,
```

### Common Data Issues

1. **Missing IMO numbers** - Older vessels or domestic barges may lack IMO
2. **Inconsistent vessel names** - "M/V NORD VENUS" vs "NORD VENUS"
3. **Multiple port codes for same port** - Houston has 7 different USACE codes
4. **Draft values of 0** - Ballast voyages or data entry errors
5. **Foreign port codes evolve** - Schedule K updated periodically

---

**Document Version**: 1.0.0
**Created**: 2026-02-05
**Last Updated**: 2026-02-05
**Status**: Current - Production Ready
