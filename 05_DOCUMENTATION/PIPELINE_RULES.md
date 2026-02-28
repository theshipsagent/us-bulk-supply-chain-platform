# PIPELINE RULES - NEVER BREAK THESE

**Purpose:** Prevent drift, ensure auditability, maintain data integrity
**Status:** MUST FOLLOW - These are not suggestions
**Last Updated:** 2026-01-28

---

## 🚨 CORE PRINCIPLES

### 1. **Every Row Must Be Traceable**
- Every record gets unique `REC_ID` at import
- Can always trace back to original raw file + row number
- Nothing is ever deleted without being saved elsewhere

### 2. **One Script Per Step**
- Step 01 = Preprocessing ONLY
- Step 02 = Classification ONLY
- Step 03 = Matching ONLY
- No ad-hoc scripts outside these 3

### 3. **Test Small Before Big**
- ALWAYS test on 5K sample first
- 5K = 2 minutes, full = 25 hours
- If 5K fails, full WILL fail

### 4. **Version Everything**
- Scripts: `step01_preprocess_v1.0.0.py`
- Data: `panjiva_2024_preprocessed_v1.0.0.csv`
- Dictionary: `dictionary_v3.6.0.csv`
- NO files without version numbers

### 5. **Archive Before Changes**
- Major change = create `_archive/YYYY-MM-DD/` folder
- Copy current state before modifying
- Can always roll back

---

## 📋 RULE SET

### RULE 1: Record ID Assignment

**Requirement:** Every row gets permanent unique ID at data import

**Format:** `REC_ID = {SOURCE}_{FILENAME}_{ROWNUMBER}`

**Examples:**
```
PANV_IMP_FILE001_R000123    (Panjiva import, file 1, row 123)
PANV_IMP_FILE042_R005678    (Panjiva import, file 42, row 5678)
PANV_EXP_FILE003_R000045    (Panjiva export, file 3, row 45)
USAC_ENT_FILE001_R001234    (USACE entrance, file 1, row 1234)
```

**Implementation:**
```python
# Step 01: When reading raw data
def assign_rec_id(df, source_code, file_number):
    """
    Assign unique record IDs
    source_code: PANV_IMP, PANV_EXP, USAC_ENT, USAC_CLR
    file_number: Sequential file number (001, 002, etc.)
    """
    df['REC_ID'] = [
        f"{source_code}_FILE{file_number:03d}_R{i:06d}"
        for i in range(len(df))
    ]
    return df
```

**Storage:**
- `REC_ID` is the LAST column (position 61)
- Once assigned, NEVER changes
- Used for all auditing, tracking, debugging

**Why:** Can always find original row in raw data

---

### RULE 2: Excluded Records Must Be Saved

**Requirement:** Any row excluded from pipeline must be saved with reason

**File:** `03_DATA/00_excluded/excluded_records_YYYY_stepXX_vX.X.X.csv`

**Columns Required:**
- `REC_ID` - Unique record identifier
- `Exclusion_Step` - Which step excluded it (preprocessing, classification, etc.)
- `Exclusion_Reason` - Why excluded (duplicate, invalid data, filter rule, etc.)
- `Exclusion_Date` - When excluded (YYYY-MM-DD HH:MM:SS)
- Original row data (all columns from that step)

**Example:**
```csv
REC_ID,Exclusion_Step,Exclusion_Reason,Exclusion_Date,Bill of Lading Number,Arrival Date,...
PANV_IMP_FILE001_R000123,Step01_Preprocess,Duplicate BOL,2026-01-28 14:32:01,EOFF123456,2024-01-15,...
PANV_IMP_FILE005_R002345,Step01_Preprocess,Missing arrival date,2026-01-28 14:32:05,EOFF789012,,,...
PANV_IMP_FILE012_R004567,Step02_Classify,FROB flag set,2026-01-28 15:45:22,EOFF345678,2024-03-20,...
```

**Why:** Can always bring excluded records back if rules change

---

### RULE 3: Column Transformations (Harmonization Strategy)

**For Shipper and Consignee:**

**APPROVED METHOD:** Overwrite original with harmonized values

```
Shipper (Original Format)  → KEEP (never changes, original value)
Shipper                     → OVERWRITE with harmonized value
Consignee (Original Format) → KEEP (never changes, original value)
Consignee                   → OVERWRITE with harmonized value
```

**Why this is safe:**
- "(Original Format)" columns preserve original values
- Can always audit back to source
- Harmonized values in main columns are easier to work with
- No duplicate "_Harmonized" columns cluttering schema

**Implementation:**
```python
# Step 01: Preprocessing
# First: Copy original to "(Original Format)" columns (already exists)
# Then: Apply harmonization rules to main columns
df['Shipper'] = df['Shipper'].apply(harmonize_shipper_name)
df['Consignee'] = df['Consignee'].apply(harmonize_consignee_name)
# Original Format columns remain untouched
```

**Harmonization Rules (to be documented separately):**
- Standardize capitalization
- Remove extra spaces
- Standardize abbreviations (CORP → Corporation, CO → Company)
- Standardize punctuation
- Merge known aliases to single name

**Why:** Clean data for classification, can always audit back to original

---

### RULE 4: Quantity Split - The ONE Destructive Transform

**Requirement:** Quantity split is the ONLY transformation that destroys original data

**Original Column:** `Quantity` (e.g., "3903 PCS")

**Split Into:**
- `Qty` = 3903 (integer)
- `Pckg` = "PCS" (text)

**Original column is DROPPED after split**

**Why this is safe:**
- Can reconstruct: `Qty + " " + Pckg` → "3903 PCS"
- Split is deterministic (always produces same result)
- Never need original format

**Implementation:**
```python
# Step 01: Preprocessing
import re

def split_quantity(qty_str):
    """Split '3903 PCS' into (3903, 'PCS')"""
    match = re.match(r'([0-9.,]+)\s*([A-Za-z]+.*)', str(qty_str))
    if match:
        qty_num = int(match.group(1).replace(',', ''))
        qty_pckg = match.group(2).strip()
        return qty_num, qty_pckg
    return None, None

df[['Qty', 'Pckg']] = df['Quantity'].apply(
    lambda x: pd.Series(split_quantity(x))
)
df = df.drop(columns=['Quantity'])  # ONLY column we drop
```

**Why:** Split provides more value than original format, can reconstruct if needed

---

### RULE 5: Data Flow is Strictly Linear

**Pipeline Order:**
```
Raw Data (135 cols)
    ↓
Step 01: Preprocessing (61 cols)
    → Outputs: 03_DATA/01_preprocessed/
    → Excluded: 03_DATA/00_excluded/
    ↓
Step 02: Classification (61 cols, values filled)
    → Outputs: 03_DATA/02_classified/
    ↓
Step 03: Matching (TBD cols)
    → Outputs: 03_DATA/03_matched/
```

**Rules:**
- NEVER skip a step
- NEVER run Step 02 without Step 01 output
- NEVER mix steps in same script
- Each step reads from previous step's output folder

**Why:** Clear lineage, easy debugging, can re-run any step

---

### RULE 6: Column Changes = Preprocessing Only

**Where column changes are allowed:**
- ✅ Step 01 (Preprocessing): Drop, rename, add, split, extract
- ❌ Step 02 (Classification): ONLY fill Group/Commodity/Cargo/Cargo Detail
- ❌ Step 03 (Matching): ONLY join tables

**If you need to add a column:**
1. Update Step 01 script
2. Re-run preprocessing on raw data
3. THEN run classification

**DO NOT:**
- Add columns in classification script
- Rename columns after preprocessing
- Drop columns in classification script

**Why:** All schema changes in one place, easy to track

---

### RULE 7: Test on 5K Before Full Run

**Requirement:** NEVER run full year without 5K test

**Process:**
```bash
# 1. Create 5K sample
python step01_preprocess_v1.0.0.py --sample 5000 --year 2024

# 2. Verify output
# - Check row count (should be ~5000)
# - Check column count (should be 61)
# - Check REC_ID uniqueness
# - Check no null values in key columns

# 3. Run classification on 5K
python step02_classify_v1.0.0.py --sample 5000 --year 2024

# 4. Verify results
# - Check classification coverage (%)
# - Check phase distribution
# - Check no errors

# 5. ONLY THEN run full year
python step01_preprocess_v1.0.0.py --year 2024
python step02_classify_v1.0.0.py --year 2024
```

**Why:** 5K = 2 minutes, full = 25 hours. Catch errors early.

---

### RULE 8: Version Control for Scripts

**Format:** `stepXX_name_vMAJOR.MINOR.PATCH.py`

**Versioning:**
- **MAJOR** (1.0.0 → 2.0.0): Breaking change, output schema changes
- **MINOR** (1.0.0 → 1.1.0): New feature, backwards compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fix, no schema change

**Examples:**
```
step01_preprocess_v1.0.0.py      (initial version)
step01_preprocess_v1.0.1.py      (bug fix: fix date parsing)
step01_preprocess_v1.1.0.py      (add: port rollup logic)
step01_preprocess_v2.0.0.py      (breaking: change REC_ID format)
```

**Rules:**
- Always copy to new file when incrementing version
- Never overwrite old version files
- Keep at least last 3 versions
- Archive older versions to `02_SCRIPTS/_archive/`

**Why:** Can roll back if new version breaks something

---

### RULE 9: Output File Naming

**Format:** `{dataset}_{year}_{step}_{version}_{timestamp}.csv`

**Examples:**
```
panjiva_2024_preprocessed_v1.0.0_20260128_1430.csv
panjiva_2024_classified_v1.0.0_20260128_1645.csv
panjiva_2024_matched_v1.0.0_20260128_1830.csv
```

**Timestamp Format:** `YYYYMMDD_HHMM` (sortable)

**ALSO create symlink/copy without timestamp as "CURRENT":**
```
panjiva_2024_preprocessed_CURRENT.csv → panjiva_2024_preprocessed_v1.0.0_20260128_1430.csv
```

**Why:** Timestamp for history, CURRENT for easy reference

---

### RULE 10: Documentation After Every Step

**Requirement:** Update README.md after each major operation

**Format:**
```markdown
## Current Status (YYYY-MM-DD)

### Last Completed Step
- Step: 01_Preprocessing
- Date: 2026-01-28 14:30
- Input: 170 raw files (1.2M records)
- Output: panjiva_2024_preprocessed_v1.0.0_20260128_1430.csv (450K records)
- Excluded: 750K records (reasons: 500K duplicates, 250K FROB)
- Status: ✅ COMPLETE

### Current Step
- Step: 02_Classification
- Date: Started 2026-01-28 16:00
- Status: 🟡 IN PROGRESS (testing 5K sample)

### Next Steps
1. Complete 5K classification test
2. Run full 2024 classification
3. Verify results
4. Run 2023 and 2025
```

**Update:**
- After each script run
- After finding bugs
- After making decisions
- At end of work session

**Why:** Future you needs to know where past you left off

---

### RULE 11: Single Source of Truth

**Reference Data (Never Changes):**
```
00_REFERENCE/
  ├── ship_registry.csv              (TRUTH for vessel specs)
  ├── dictionary_vX.X.X.csv          (TRUTH for classification rules)
  ├── port_dictionary.csv            (TRUTH for port mappings)
  └── harmonization_rules.json       (TRUTH for name harmonization)
```

**Rules:**
- Reference data is READ-ONLY
- Never modify reference files directly
- To update: Create new version, increment version number
- Scripts point to specific version (not "latest")

**Why:** Know exactly what reference data was used for each run

---

### RULE 12: Parallel Runs Must Be Isolated

**If running multiple years in parallel:**

**DO:**
```bash
# Terminal 1
python step01_preprocess_v1.0.0.py --year 2023 --output 03_DATA/01_preprocessed/2023/

# Terminal 2
python step01_preprocess_v1.0.0.py --year 2024 --output 03_DATA/01_preprocessed/2024/

# Terminal 3
python step01_preprocess_v1.0.0.py --year 2025 --output 03_DATA/01_preprocessed/2025/
```

**DON'T:**
```bash
# Will overwrite each other's outputs!
python step01_preprocess_v1.0.0.py --year 2023
python step01_preprocess_v1.0.0.py --year 2024  # OVERWRITES 2023 outputs!
```

**Why:** Prevent race conditions and data corruption

---

### RULE 13: Git Commit Strategy

**When to commit:**
- ✅ After successful 5K test
- ✅ After script version increment
- ✅ After documentation update
- ✅ At end of work session

**What to commit:**
- ✅ Scripts (02_SCRIPTS/)
- ✅ Reference data (00_REFERENCE/)
- ✅ Documentation (*.md files)
- ✅ Column tracker (COLUMN_EVOLUTION_TRACKER.csv)
- ❌ Data files (too large, use .gitignore)
- ❌ Test outputs (temporary)

**Commit message format:**
```
[TYPE] Brief description

TYPE:
- [ADD] New feature/script/file
- [FIX] Bug fix
- [UPDATE] Modify existing
- [DOCS] Documentation only
- [REFACTOR] Code restructure, no logic change
- [TEST] Test results

Examples:
[ADD] step01_preprocess_v1.0.0.py - initial preprocessing script
[FIX] step02_classify_v1.0.1.py - fix column name mismatch bug
[UPDATE] dictionary_v3.7.0.csv - add 25 new crude oil rules
[DOCS] Update README.md with current status
```

**Why:** Clear history, easy to find changes

---

### RULE 14: Error Handling

**Requirement:** All scripts must handle errors gracefully

**Implementation:**
```python
import logging
import sys
from datetime import datetime

# Setup logging
log_file = f"logs/{script_name}_{datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    # Main processing
    df = load_data()
    df = process_data(df)
    save_data(df)
    logging.info("✅ SUCCESS: Processing complete")

except Exception as e:
    logging.error(f"❌ FAILED: {str(e)}")
    logging.error(f"Traceback: {traceback.format_exc()}")

    # Save checkpoint if possible
    if 'df' in locals():
        checkpoint_file = f"03_DATA/99_checkpoints/checkpoint_{datetime.now():%Y%m%d_%H%M%S}.csv"
        df.to_csv(checkpoint_file, index=False)
        logging.info(f"💾 Checkpoint saved: {checkpoint_file}")

    sys.exit(1)
```

**Why:** Can debug failures, recover from crashes

---

### RULE 15: Performance Monitoring

**Requirement:** Log performance metrics for each run

**Metrics to log:**
```python
# At end of script
logging.info("=== PERFORMANCE METRICS ===")
logging.info(f"Input records: {input_count:,}")
logging.info(f"Output records: {output_count:,}")
logging.info(f"Excluded records: {excluded_count:,}")
logging.info(f"Processing time: {elapsed_time:.2f} seconds")
logging.info(f"Records/second: {output_count/elapsed_time:.2f}")
logging.info(f"Memory peak: {peak_memory_mb:.2f} MB")
```

**Why:** Track performance over time, identify bottlenecks

---

## 🎯 DECISION MATRIX

Use this when making decisions:

| Question | Answer | Rule Reference |
|----------|--------|----------------|
| Should I add a column? | Add in Step 01, re-run preprocessing | Rule 6 |
| Should I modify reference data? | Create new version, don't edit current | Rule 11 |
| Can I skip 5K test? | NO - always test small first | Rule 7 |
| Should I delete excluded rows? | NO - save to excluded_records.csv | Rule 2 |
| Can I run without REC_ID? | NO - every row needs unique ID | Rule 1 |
| Should I harmonize in new column? | NO - overwrite original (have Original Format column) | Rule 3 |
| Can I drop Quantity column? | YES - only after splitting to Qty + Pckg | Rule 4 |
| Should I increment MAJOR version? | YES - if output schema changes | Rule 8 |
| Can I commit data files? | NO - only scripts, reference data, docs | Rule 13 |

---

## 🚨 RED FLAGS (Things That Indicate Drift)

If you find yourself doing any of these, STOP:

❌ "Let me just create a quick script to..."
→ Use one of the 3 main scripts

❌ "I'll just manually edit this CSV..."
→ Write code to do it, make it reproducible

❌ "I don't need to test on 5K first..."
→ You DO. Always test small.

❌ "I'll add this column in the classification script..."
→ NO. Add in preprocessing, re-run.

❌ "I'll just delete these rows..."
→ Save to excluded_records.csv first.

❌ "I don't need to version this file..."
→ Version EVERYTHING.

❌ "I'll commit this later..."
→ Commit now, before you forget.

---

## ✅ CHECKLIST: Before Running Full Pipeline

Before running full year processing, verify:

- [ ] Raw data has REC_ID assigned
- [ ] 5K test completed successfully
- [ ] Column count matches expected (61)
- [ ] REC_ID is unique (no duplicates)
- [ ] Vessel enrichment working (>70% match rate)
- [ ] Classification columns initialized (empty)
- [ ] Lock columns initialized (FALSE)
- [ ] Script version incremented if changes made
- [ ] Reference data version documented
- [ ] Output directory exists
- [ ] Excluded records directory exists
- [ ] Logs directory exists
- [ ] Disk space available (5GB minimum)
- [ ] README.md updated with current status
- [ ] Git committed recent changes

**If all checked, proceed. If any unchecked, fix first.**

---

## 📊 FINAL SCHEMA (61 columns after preprocessing)

**Column Order:**
1-31: Core shipment data (BOL, dates, parties, ports, vessel)
32-38: Product data (goods, HS codes, qty/pckg, REC_ID duplicate)
39: Count (aggregation)
40-43: Classification (Group, Commodity, Cargo, Cargo Detail) - EMPTY
44-47: Lock flags (Group_Locked, Commodity_Locked, Cargo_Locked, Cargo_Detail_Locked) - FALSE
48-49: Tracking (Classified_Phase, Last_Rule_ID) - EMPTY
50-55: Reporting (Report_One/Two/Three/Four, Filter, Note) - EMPTY
56-58: Vessel enrichment (Type, DWT, Vessel_Type_Simple) - FROM REGISTRY
59-60: Reserved for future use
61: **REC_ID** - UNIQUE PERMANENT IDENTIFIER ⭐

**Note:** REC_ID appears twice - once near product data (position 38) and once at end (position 61). This is intentional for backwards compatibility with existing code. Position 61 is the authoritative location.

---

## 🎓 SUMMARY

**These rules exist to:**
1. Prevent drift
2. Ensure auditability
3. Make debugging easy
4. Allow rollback
5. Keep you organized

**Follow them strictly. Future you will thank present you.**

---

**Document Version:** 1.0.0
**Created:** 2026-01-28
**Status:** ACTIVE - MUST FOLLOW
