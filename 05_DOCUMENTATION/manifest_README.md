
## Latest Version: v3.6.0 (2026-01-14)

**Major Release: 218 new user-edited rules with refined keyword strategy**

- [OK] 668 total rules (+95 from v3.4.0)
- [OK] 100% classification rate on 15K test sample
- [OK] Break-Bulk group eliminated (improved from 82% vague to 95.7% Dry Bulk)
- [OK] Comprehensive coverage: Crude Oil, Steel, Chemicals, Metals, Fertilizers
- [OK] Refined keyword strategy: Key_Phrases, Primary_Keywords, Match_Strategy

**Quick Links:**
- [Version History](05_DOCUMENTATION/DICTIONARY_VERSION_HISTORY.md)
- [v3.6.0 Summary](user_notes/DICTIONARY_V3.6.0_SUMMARY.md)
- [v3.6.0 Test Results](user_notes/DICTIONARY_V3.6.0_TEST_RESULTS.md)
- [Dictionary File](03_DICTIONARIES/03.01_cargo_classification/cargo_classification_dictionary_v3.6.0_20260114_1830.csv)
## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Results](#results)
- [USACE Data Integration](#usace-data-integration)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Repository Structure](#repository-structure)
- [Classification Rules](#classification-rules)
- [Next Steps](#next-steps)
- [Contributing](#contributing)

---

## 🎯 Overview

This system processes raw Panjiva import data through a multi-phase classification pipeline that assigns cargo to a 4-level taxonomy:

```
Group → Commodity → Cargo → Cargo_Detail
```

**Example Classification**:
```
Group:         Liquid Bulk
Commodity:     Petroleum
Cargo:         Crude Oil
Cargo_Detail:  Crude Oil - Basrah Heavy
```

### Dataset

- **Source**: Panjiva U.S. Import Data
- **Coverage**: 2023-2025 (3 years)
- **Records**: 854,870 shipments (deduplicated)
- **Total Tonnage**: 1.35 billion metric tons
- **Note**: v2.1.0 preprocessing includes automatic deduplication (447,376 duplicates removed)

---

## ✨ Key Features

### 🎯 High-Performance Classification

- **560,091 records classified** (65.5% of total)
- **1.34 billion tons captured** (99.3% of total tonnage)
- **294,779 records excluded** (34.5% - cruise lines, freight forwarders, white noise)
- **100% classification achieved** on clean deduplicated data
- **133+ classification rules** across 7 processing stages
- **5-tier rule hierarchy** (carrier locks → package types → HS codes → tonnage → keywords)

### 📊 Interactive Dashboards

- **Pipeline Dashboard**: 3-year trends, top commodities, phase progression
- **Technical Data Flow**: Column schema evolution, rule execution matrix
- **Landing Page**: Centralized access to all documentation and data

### 📚 Comprehensive Dictionaries

- **Cargo Classification**: 4-level taxonomy with 400+ entries
- **HS Code Lookups**: Complete HS2/HS4/HS6 hierarchy (7.6 MB)
- **Port Dictionary**: U.S. ports with ACE codes
- **Ship Registry**: 5.4 MB vessel database with IMO numbers
- **Trade Codes**: Schedule B, SITC, NAICS, SIC classifications

### 🔧 Production Features

- **Checkpoint System**: Resume from any processing stage
- **Comprehensive Logging**: Detailed execution logs and audit trails
- **Version Control**: Git-tracked with proper large file exclusions
- **Modular Design**: Independent phase scripts for maintenance

---

## 🏗️ Architecture

### Processing Pipeline

```
00. Raw Data (170 files)
    ↓
01. Preprocessing (Stage 00)
    - Deduplication
    - Column removal/renaming
    - Date validation
    - HS code extraction
    ↓
02. Classification (Phases 1-10)
    - Carrier-based locks
    - Package type rules
    - HS code + keyword matching
    - Tonnage overrides
    - User refinements
    ↓
03. Output
    - Classified CSVs by year
    - Pivot summaries
    - Interactive dashboards
```

### 5-Tier Rule Hierarchy

| Tier | Type | Accuracy | Example |
|------|------|----------|---------|
| 1 | Carrier Locks | 100% | NGL carriers → LNG/LPG |
| 2 | Package Types | 98% | LBK (Liquid Bulk) → 501M tons |
| 3 | HS Code + Keywords | 85-95% | HS 2709 + "CRUDE" → Crude Oil |
| 4 | Tonnage Overrides | 90-95% | >1000 tons + keyword → Reclassify |
| 5 | User Refinements | 75-90% | "SALT" → Salt (simplified rule) |

---

## 📊 Results

### Overall Performance (2023-2025 Combined)

| Metric | Value |
|--------|-------|
| **Total Records** | 1,302,246 |
| **Classified Records** | 786,674 (60.4%) |
| **Total Tonnage** | 2.07B tons |
| **Classified Tonnage** | 1.47B tons (71.3%) |
| **Processing Time** | ~40 minutes |

### Year-by-Year Breakdown

| Year | Records | Classified % | Tonnage Captured |
|------|---------|--------------|------------------|
| **2023** | 454,266 | 80.2% | 49.3% |
| **2024** | 449,233 | 52.5% | 84.0% |
| **2025** | 398,747 | 55.9% | 82.8% |

### Top 3 Rules by Tonnage Impact

| Rank | Rule | Tonnage Captured | Description |
|------|------|------------------|-------------|
| 🥇 | LBK Package | 501M tons | Liquid bulk package type indicator |
| 🥈 | Crude Oil Variants | 79M tons | Specific grades (BASRAH, KIRKUK, LIZA, TUPI) |
| 🥉 | Simplified Salt | 32.9M tons | "Salt is just salt" - keyword matching |

---

## 🏢 Party Harmonization System

**NEW: Entity-Based Classification (2026-02-09)**

In addition to commodity classification, the system now includes **party name harmonization** to standardize raw shipper/consignee/notify party names into canonical entities.

### Overview

- **Purpose**: Standardize messy party names → clean entities for firm-based cargo rules
- **Dictionary**: 163 entities across 11 sectors
- **Version**: v1.3.0
- **Status**: Tested and ready for production deployment

### Key Features

**High Tonnage Capture**:
- January 2024 test (25,399 records, 45.7M tons):
  - Shipper: 5.9% records matched → **32.5% tonnage captured**
  - Consignee: 6.7% records matched → **53.3% tonnage captured**
  - Notify Party: 3.5% records matched → 43.3% tonnage captured
- **Key Insight**: Low record match but HIGH tonnage capture (harmonizes big players)

**Match Strategies**:
- EXACT: Direct name match (100% confidence)
- Contains: Keyword appears in party name (95% confidence)
- Contains_All: All required keywords present (90% confidence)
- FUZZY: 75%+ word overlap (85% confidence)

**Entity Categories** (163 total):
- Cement: 23 entities (Nuh Cimento, Cemex, Argos, etc.)
- Steel: 31 entities (ArcelorMittal, Ternium, NLMK, etc.)
- Petroleum: 42 entities (Chevron, Ecopetrol, Vale, etc.)
- Chemicals: 18 entities (Celanese, Dow, BASF, etc.)
- Aggregates: 11 entities (Vulcan, Martin Marietta, etc.)
- [+ 6 more sectors]

### Controlled Refinement Architecture

**Two-Tier Classification**:
1. **Stable High-Level** (Group/Commodity/Cargo) - rarely changes
2. **Progressive Detail** (Cargo_Detail) - controlled refinement over time

**Task Registry System**:
- Explicit overwrite permissions per refinement task
- Prevents "drift" - no random modifications
- Full audit trail of all changes
- Example: "Cement NOS" → "Cement - Turkish Import (Nuh Cimento)"

**Active Refinement Tasks**:
- CEMENT_ORIGIN_v1.0: Add origin detail to cement shipments
- SCM_PRODUCTS_v1.0: Identify GGBFS, fly ash, natural pozzolan
- AGGREGATES_DETAIL_v1.0: Distinguish crushed stone, sand, gravel
- CONSTRUCTION_TRADE_LANES_v1.0: Tag market segments for analysis

### Files

**Scripts**: `05_TASKS/05.01_party_harmonization/`
- `harmonize_party_names_v1.0.0.py` - Main harmonization
- `infer_parties_from_trade_lanes_v1.0.0.py` - Infer missing parties
- `refine_cement_with_entities_v1.0.0.py` - Cement refinement
- `validate_harmonization_v1.0.0.py` - Validation reports

**Dictionary**: `01_DICTIONARIES/01.06_parties/`
- `party_harmonization_master_v1.3.0.csv` (163 entities)
- Top 200 profiling files for shippers/consignees

**Documentation**:
- `05_TASKS/05.01_party_harmonization/README.md` - Complete system documentation
- `SESSION_HANDOFF_20260209.md` - Development history and next steps

**Integration Status**: NOT yet integrated with main cargo classification pipeline

---

## 🚢 USACE Data Integration

**NEW: USACE Vessel Movement Data (2026-01-15)**

In addition to Panjiva cargo classification, this system now processes USACE (U.S. Army Corps of Engineers) vessel entrance and clearance data.

### Dataset

- **Source**: USACE Waterborne Commerce Statistics
- **Year**: 2023
- **Records**: 165,683 vessel movements
  - 82,343 entrances (inbound/imports)
  - 83,340 clearances (outbound/exports)
- **Output**: 37-column standardized schema

### Key Features

**Port Mapping (100% accuracy)**:
- Discovered USACE uses proprietary port/waterway codes (NOT Census Sked D)
- Built authoritative dictionary from source data (528 unique codes)

**Vessel Enrichment (85.7% match rate)**:
- Two-tier matching: IMO number (primary) + vessel name (secondary)
- Added specifications: Type, DWT, Grain capacity, TPC, draft data

**Draft Analysis (84.3% coverage)**:
- Calculate actual draft as % of max DWT draft
- Forecast vessel activity: >50% = Discharge (laden), ≤50% = Load (ballast)
- Results: 81% Discharge, 3% Load

**Cargo Classification (100% coverage)**:
- Maps ICST vessel type to cargo Group and Commodity
- 45.3% Dry Bulk, 23.8% Other, 18.7% Liquid Bulk

### Files

**Scripts**:
- `04_SCRIPTS/transform_usace_entrance_data_v2.0.0.py`
- `04_SCRIPTS/transform_usace_clearance_data_v2.0.0.py`

**Dictionaries**:
- `01.01_dictionary/usace_port_codes_from_data.csv` (528 USACE codes)
- `01.01_dictionary/usace_sked_k_foreign_ports.csv` (1,907 foreign ports)
- `01.01_dictionary/usace_cargoclass.csv` (40 cargo classifications)

**Documentation**:
- [USACE Data Transformation Guide](05_DOCUMENTATION/USACE_DATA_TRANSFORMATION_v2.0.0.md)

**Output**:
- `02_STAGE02_CLASSIFICATION/usace_2023_inbound_entrance_transformed_v2.1.0.csv`
- `02_STAGE02_CLASSIFICATION/usace_2023_outbound_clearance_transformed_v2.1.0.csv`

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Pandas, NumPy
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/theshipsagent/panjiva-classification-system.git
cd panjiva-classification-system

# Install dependencies
pip install pandas numpy

# View documentation
open build_documentation/INDEX.html
```

### Running Classification

```bash
# Run full classification pipeline (example - scripts in C:\Users\wsd3\)
python classification_phase10_high_value.py 2024

# Output: classified CSV + pivot summary
```

**Note**: Large data files (raw data, processed CSVs) are NOT in this repository. They remain in Google Drive at `G:\My Drive\LLM\project_manifest\`.

---

## 📖 Documentation

### Interactive Dashboards

- **[INDEX.html](build_documentation/INDEX.html)** - Main landing page
- **[Pipeline Dashboard](build_documentation/classification_pipeline_dashboard.html)** - Charts & metrics
- **[Technical Data Flow](build_documentation/classification_technical_dataflow.html)** - Architecture diagrams

### Documentation Files

- **[Master Pipeline Plan](build_documentation/PIPELINE_MASTER_PLAN_UPDATED.md)** - Complete system reference
- **[Phase 10 Summary](build_documentation/classification_phase10_final_summary.md)** - Latest phase results
- **[3-Year Comparison](build_documentation/classification_3year_comparison.md)** - Cross-year analysis
- **[Git Setup Guide](GIT_SETUP_GUIDE.md)** - Version control workflow
- **[Folder Organization](FOLDER_REORGANIZATION_SUMMARY.md)** - Project structure

### Reference Dictionaries

- **[Cargo Dictionary](01.01_dictionary/01_cargo_dictionary_harmonized_v20260111_2313.csv)** - Latest taxonomy
- **[HS Code Lookups](01.01_dictionary/)** - Complete HS hierarchy
- **[Port Dictionary](01.01_dictionary/01_us_port_dictionary.csv)** - U.S. ports
- **[Ship Registry](01.01_dictionary/01_ships_register.csv)** - Vessel database

---

## 📁 Repository Structure

```
panjiva-classification-system/
│
├── 📂 build_documentation/          # Final outputs & dashboards
│   ├── INDEX.html                   # Main landing page ⭐
│   ├── classification_pipeline_dashboard.html
│   ├── classification_technical_dataflow.html
│   ├── PIPELINE_MASTER_PLAN_UPDATED.md
│   ├── classification_phase10_final_summary.md
│   ├── classification_3year_comparison.md
│   └── classification_full_20XX/   # Empty (CSVs excluded)
│
├── 📂 01.01_dictionary/             # Reference dictionaries
│   ├── 01_cargo_dictionary_harmonized_v20260111_2313.csv
│   ├── hs_code_lookup.json         # 7.6 MB HS hierarchy
│   ├── 01_us_port_dictionary.csv
│   ├── 01_ships_register.csv       # 5.4 MB vessel registry
│   ├── sked_b_import_codes.csv     # Trade codes
│   └── [40+ reference files]
│
├── 📂 .github/workflows/            # GitHub Actions
│   └── backup.yml                   # Automated backups
│
├── .gitignore                       # Excludes large data files
├── README.md                        # This file ⭐
├── GIT_SETUP_GUIDE.md              # Git workflow guide
└── FOLDER_REORGANIZATION_SUMMARY.md # Project cleanup log
```

**Large Data Files (NOT in repository)**:
- `00_raw_data/` - 170 raw Panjiva files (~330 MB)
- `01_step_one/` - Processed CSVs (1 GB)
- `classification_full_*/` - Classified outputs (1 GB+)
- `_archive/` - Old versions (13 GB)

---

## 🎯 Classification Rules

### Phase Overview

| Phase | Focus | Rules | Key Achievement |
|-------|-------|-------|-----------------|
| **1-2** | Bulk Commodities | 8 | Crude oil, grain, coal, salt |
| **3** | General Cargo | 6 | Steel, containers, vehicles |
| **4** | Tonnage Override | 4 | Misclassified bulk shipments |
| **5** | Final Push | 5 | Remaining high-value items |
| **6** | Orchestrator Fixes | 3 | Ferrochrome, aggregates |
| **7** | Major Tonnages | 5 | LBK package rule (501M tons!) |
| **8** | High Confidence | 8 | Precision rules |
| **9** | User Refinements | 5 | Simplified salt rule |
| **10** | High Value | 15 | 106M tons added |

### Rule Examples

**Tier 1 - Carrier Lock** (100% accuracy):
```python
# Excelerate Energy → LNG classification
carrier_lock = (df['Shipper'].str.contains('EXCELERATE', na=False))
df.loc[carrier_lock, 'Commodity'] = 'LNG'
```

**Tier 2 - Package Type** (98% accuracy):
```python
# LBK package → Liquid Bulk
lbk_mask = (df['Pckg'] == 'LBK')
df.loc[lbk_mask, 'Group'] = 'Liquid Bulk'
# Result: 501M tons classified!
```

**Tier 3 - HS Code + Keyword** (85-95% accuracy):
```python
# HS 2709 + "CRUDE" → Crude Oil
crude_mask = (
    (df['HS2'] == '27') &
    (df['Goods Shipped'].str.contains('CRUDE', na=False)) &
    (df['Tons'] > 100)
)
df.loc[crude_mask, 'Cargo'] = 'Crude Oil'
```

---

## 🔄 Next Steps

### Recommended Enhancements

1. **Monthly Updates**
   - Process ~37K new records/month
   - Runtime: 2-3 minutes
   - Incremental classification

2. **ML Pattern Discovery**
   - Use 786K classified records as training set
   - Automated rule refinement
   - Pattern mining for new commodities

3. **Granularity Refinement**
   - "Steel NOS" → "Cold Rolled Coils"
   - "Grain NOS" → "Hard Red Winter Wheat"
   - Higher analytical value

4. **Cross-Year Trend Analysis**
   - Commodity flow patterns
   - Port specialization evolution
   - Trade route changes

---

## 🤝 Contributing

### Development Workflow

1. **Clone & Branch**:
   ```bash
   git clone https://github.com/theshipsagent/panjiva-classification-system.git
   git checkout -b feature-new-commodity
   ```

2. **Make Changes**:
   - Update dictionaries in `01.01_dictionary/`
   - Modify documentation in `build_documentation/`
   - Add new rules (scripts in local environment)

3. **Commit & Push**:
   ```bash
   git add .
   git commit -m "Add: new commodity classification for XYZ"
   git push origin feature-new-commodity
   ```

4. **Create Pull Request** on GitHub

### Coding Standards

- **Commit Messages**: Use descriptive, imperative mood ("Add", "Fix", "Update")
- **Documentation**: Update relevant markdown files
- **Testing**: Verify classification accuracy on sample data
- **Large Files**: Never commit CSVs >10 MB (use `.gitignore`)

---

## 📊 Performance Metrics

### Classification Quality

- **Precision**: 95%+ for Tier 1-2 rules
- **Recall**: 71.3% tonnage capture
- **False Positives**: <2% for high-confidence rules

### Processing Speed

- **Stage 00 Preprocessing**: ~30 minutes (1.3M records)
- **Phase 1-9 Classification**: ~8 minutes per year
- **Phase 10 High Value**: ~2 minutes per year
- **Total Pipeline**: ~40 minutes end-to-end

### Storage

- **Repository Size**: 6.72 MB (version-controlled)
- **Full Project**: ~22 GB (Google Drive)
- **Classified Data**: ~1 GB (3 years of output CSVs)

---

## 🔒 Data Privacy

This repository contains:
- ✅ Public reference data (HS codes, port codes, trade classifications)
- ✅ Classification rules and algorithms
- ✅ Documentation and dashboards
- ❌ No proprietary raw Panjiva data
- ❌ No company-specific information
- ❌ No classified output files

**Large data files remain in Google Drive** and are excluded via `.gitignore`.

---

## 📝 License

This project is proprietary and confidential. Unauthorized use, reproduction, or distribution is prohibited.

**Copyright © 2026 The Ships Agent**

---

## 📧 Contact

**Project Maintainer**: The Ships Agent
**Email**: takoradiautomations@gmail.com
**GitHub**: [@theshipsagent](https://github.com/theshipsagent)

---

## 🎉 Acknowledgments

- **Panjiva** - Source data provider
- **Claude AI** - Development assistance
- **USACE** - Port and waterway references
- **Census Bureau** - HS code classifications

---

## 📈 Project Timeline

- **2025 Q4**: Initial development and rule creation
- **2026 Q1**: Phase 1-9 completion (786K records classified)
- **2026-01-13**: Phase 10 completion, folder reorganization, git setup
- **Current Status**: Production-ready, ML-ready training set

---

**⭐ Star this repository** if you find it useful!

**📖 View Full Documentation**: [build_documentation/INDEX.html](build_documentation/INDEX.html)
