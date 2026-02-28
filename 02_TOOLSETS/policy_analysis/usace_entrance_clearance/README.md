# USACE Entrance & Clearance Data Processing

**Isolated Project for Processing USACE Port Arrival and Departure Records**

---

## 📖 Overview

This is a standalone, isolated project for processing U.S. Army Corps of Engineers (USACE) Entrance and Clearance data. It transforms raw USACE port arrival and departure records into enriched datasets with:

- Vessel specifications (DWT, draft, grain capacity)
- Port mappings (USACE codes to Census statistical categories)
- Cargo classifications by vessel type (ICST codes)
- Draft analysis and forecasted vessel activity (load vs discharge)
- Agency fee assignments

**Relationship to Master Project**: This project is a focused extraction from the larger maritime cargo classification system at `G:\My Drive\LLM\project_manifest`. It provides a clean, standalone environment for USACE data processing without dependencies on the master project's Panjiva classification pipeline.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pandas, numpy, openpyxl

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Complete Pipeline

```bash
cd "G:\My Drive\LLM\task_usace_entrance_clearance"

# Run the complete pipeline (all 3 steps)
python 02_SCRIPTS/run_usace_pipeline.py
```

This will:
1. Split the Excel file into CSV worksheets (if needed)
2. Transform entrance (inbound/imports) data
3. Transform clearance (outbound/exports) data

---

## 📁 Project Structure

```
task_usace_entrance_clearance/
├── 00_DATA/
│   ├── 00.01_RAW/                    # Raw USACE data files
│   │   ├── Entrances_Clearances_2023.xlsx
│   │   ├── Entrances_Clearances_2023_2023_Inbound.csv
│   │   ├── Entrances_Clearances_2023_2023_Outbound.csv
│   │   └── Entrances_Clearances_2023_Definition.csv
│   └── 00.02_PROCESSED/              # Transformed output files
│       ├── usace_2023_inbound_entrance_transformed_v3.0.0.csv
│       └── usace_2023_outbound_clearance_transformed_v3.0.0.csv
│
├── 01_DICTIONARIES/                   # Reference data and lookup tables
│   ├── 01_ships_register.csv         # International vessel registry
│   ├── agency_fee_by_icst.csv        # Agency fees by vessel type
│   ├── icst_vessel_codes.md          # ICST vessel type documentation
│   ├── usace_cargoclass.csv          # Cargo classification by ICST
│   ├── usace_port_codes_from_data.csv # USACE port codes
│   ├── usace_sked_k_foreign_ports.csv # Foreign port codes (Schedule K)
│   └── usace_to_census_port_mapping.csv # USACE to Census port mapping
│
├── 02_SCRIPTS/                        # Processing scripts
│   ├── split_excel_to_csv.py         # Step 1: Split Excel to CSV
│   ├── transform_usace_entrance_data.py # Step 2: Transform entrance data
│   ├── transform_usace_clearance_data.py # Step 3: Transform clearance data
│   └── run_usace_pipeline.py         # Master orchestration script
│
├── 03_DOCUMENTATION/                  # Build guides and documentation
│   └── BUILD_GUIDE.md                # Detailed build documentation
│
├── logs/                              # Processing logs
├── previous_build/                    # Original data from master project
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

---

## 🔧 Individual Script Usage

### Step 1: Split Excel to CSV

```bash
python 02_SCRIPTS/split_excel_to_csv.py
```

Converts the multi-worksheet Excel file into separate CSV files.

**Input:**
- `00_DATA/00.01_RAW/Entrances_Clearances_2023.xlsx`

**Output:**
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Inbound.csv`
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Outbound.csv`

### Step 2: Transform Entrance Data

```bash
python 02_SCRIPTS/transform_usace_entrance_data.py
```

Transforms raw entrance (inbound/imports) records with enrichments.

**Input:**
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Inbound.csv`

**Output:**
- `00_DATA/00.02_PROCESSED/usace_2023_inbound_entrance_transformed_v3.0.0.csv`

### Step 3: Transform Clearance Data

```bash
python 02_SCRIPTS/transform_usace_clearance_data.py
```

Transforms raw clearance (outbound/exports) records with enrichments.

**Input:**
- `00_DATA/00.01_RAW/Entrances_Clearances_2023_2023_Outbound.csv`

**Output:**
- `00_DATA/00.02_PROCESSED/usace_2023_outbound_clearance_transformed_v3.0.0.csv`

---

## 📊 Data Transformations

### Port Mappings
- **USACE Port Codes** → **USACE Port Names**
- **USACE Ports** → **Census Statistical Categories** (Port_Consolidated, Port_Coast, Port_Region)
- **Foreign Port Codes (Schedule K)** → **Foreign Port Names & Countries**

### Vessel Enrichment
- **IMO Number** → Vessel specifications (Type, DWT, Grain, TPC, Draft)
- **Vessel Name** → Vessel specifications (fuzzy name matching)
- **Draft Calculation** → Draft % of maximum + Forecasted Activity (Load/Discharge)

### Cargo Classification
- **ICST Vessel Type** → Cargo Group & Commodity
- **ICST Vessel Type** → Agency Fee

### Code Transformations
- **TYPEDOC**: `0` → `Imports`, `1` → `Exports`
- **PWW_IND**: `P` → `Port`, `W` → `Waterway`
- **WHERE_IND**: `F` → `Foreign`, `D` → `Coastwise`

---

## 📈 Expected Results

### Typical Match Rates (2023 Data)

| Enrichment Type | Expected Coverage |
|----------------|-------------------|
| USACE Port Mapping | 100% |
| Census Statistical Categories | 44.3% |
| Vessel Specs (IMO/Name) | 70-80% |
| Draft Percentage Calculated | 60-70% |
| Cargo Classification | 90-95% |
| Agency Fees | 90-95% |

---

## 📚 Documentation

- **README.md** (this file) - Quick start and overview
- **03_DOCUMENTATION/BUILD_GUIDE.md** - Detailed build documentation
- **00_DATA/00.01_RAW/Entrances_Clearances_2023_Definition.csv** - Field definitions
- **01_DICTIONARIES/icst_vessel_codes.md** - ICST vessel type codes

---

## 🔗 Master Project Reference

This project was extracted from the larger maritime cargo classification system:

**Master Project Location**: `G:\My Drive\LLM\project_manifest`

**Key Master Project Files**:
- `00_START_HERE.md` - Master project overview
- `CLAUDE.md` - Technical guide for the full system
- `CLASSIFICATION_3YEAR_COMPARISON_v2.0.0.md` - Classification results

**Original Scripts** (for reference):
- `02_SCRIPTS/02.01_preprocessing/split_excel_to_csv.py`
- `02_SCRIPTS/02.01_preprocessing/transform_usace_entrance_data.py`
- `02_SCRIPTS/02.01_preprocessing/transform_usace_clearance_data.py`

---

## 🆘 Troubleshooting

### "File not found" errors

Check that Google Drive File Stream is mounted at `G:\` and files exist:

```bash
ls "G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.01_RAW"
```

### "Dictionary not found" errors

Ensure all dictionary files are in `01_DICTIONARIES/`:

```bash
ls "G:\My Drive\LLM\task_usace_entrance_clearance\01_DICTIONARIES"
```

### Low vessel match rates

The `01_ships_register.csv` file should contain vessel specifications. Check file size:

```bash
ls -lh "G:\My Drive\LLM\task_usace_entrance_clearance\01_DICTIONARIES\01_ships_register.csv"
```

Expected: ~5.4 MB with 50,000+ vessels

---

## ✅ Testing

To test the pipeline on a small sample:

```python
# Edit transform scripts to use test_mode=True
# In transform_usace_entrance_data.py or transform_usace_clearance_data.py:

df_final = transform_entrance_data(INPUT_FILE, OUTPUT_FILE, DICT_PATH, test_mode=True)
```

This will process only the first 100 rows for quick validation.

---

## 📝 Version History

- **v3.0.0** (2026-02-05) - Initial isolated project version
  - Adapted from master project v2.2.0
  - Standalone directory structure
  - Portable path detection
  - Master orchestration script added

---

## 📄 License

This project is part of the WSD3 maritime cargo classification system.

---

**Created**: 2026-02-05
**Last Updated**: 2026-02-05
**Status**: Active - Isolated build complete
