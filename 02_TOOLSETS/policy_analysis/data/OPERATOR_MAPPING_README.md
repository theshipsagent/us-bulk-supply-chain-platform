# Operator Name Standardization Guide

## Overview

The USACE vessel database contains operator names that vary across years and data sources. This can lead to:
- The same operator appearing as multiple different entities
- Inflated operator counts
- Difficulty tracking operator trends over time

This standardization process consolidates variant names into canonical standard names.

## Files Created

### 1. `operator_name_mapping.yaml`
**Location:** `data/operator_name_mapping.yaml`

The master mapping dictionary that defines how variant names should be standardized.

**Format:**
```yaml
"VARIANT NAME": "Canonical Standardized Name"
"ANOTHER VARIANT": "Canonical Standardized Name"
```

**Instructions:**
- Review the pre-populated mappings
- Add new mappings as you identify variants
- Use the most official/current name as the canonical name
- Include common abbreviations and legal entity variations

### 2. Analysis Scripts

#### `scripts/usace/analyze_operator_variants.py`
Analyzes the database to find likely operator name variants.

**Usage:**
```bash
# Stop Streamlit dashboard first
python scripts/usace/analyze_operator_variants.py
```

**Output:**
- Console: Top 50 operators with variants
- File: `data/operator_variants_analysis.txt` (complete list)

#### `scripts/usace/apply_operator_mapping.py`
Applies the mapping to create standardized operator names.

**Usage:**
```bash
# Stop Streamlit dashboard first
python scripts/usace/apply_operator_mapping.py
```

**What it does:**
1. Adds `operator_name_std` column to operators table
2. Applies mappings from `operator_name_mapping.yaml`
3. Updates analytics view to include standardized names
4. Shows statistics on consolidation

## Workflow

### Step 1: Analyze Variants
```bash
# Stop the dashboard
taskkill /PID <streamlit_pid>

# Run analysis
python scripts/usace/analyze_operator_variants.py

# Review output
notepad data/operator_variants_analysis.txt
```

### Step 2: Update Mapping
Edit `data/operator_name_mapping.yaml` to add/modify mappings:

```yaml
# Example: Consolidate ACBL variants
"AMERICAN COMMERCIAL BARGE LINE": "American Commercial Barge Line"
"AMERICAN COMMERCIAL LINES": "American Commercial Barge Line"
"ACBL": "American Commercial Barge Line"
```

### Step 3: Apply Mapping
```bash
python scripts/usace/apply_operator_mapping.py
```

This creates the `operator_name_std` column with standardized names.

### Step 4: Update Dashboard
Modify dashboard queries to use `operator_name_std` instead of `operator_name`:

**Before:**
```python
SELECT operator_name, COUNT(*)
FROM operators
GROUP BY operator_name
```

**After:**
```python
SELECT operator_name_std, COUNT(*)
FROM operators
GROUP BY operator_name_std
```

### Step 5: Restart Dashboard
```bash
cd "G:\My Drive\LLM\project_us_flag"
python -m streamlit run src/usace_db/dashboard/app.py --server.port 8503 --server.headless true
```

## Example Mappings

### Major Operators

**American Commercial Barge Line (ACBL)**
- Variants: "AMERICAN COMMERCIAL LINES", "ACBL", "AMERICAN COMMERCIAL BARGE LINE LLC"
- Canonical: "American Commercial Barge Line"

**Ingram Barge Company**
- Variants: "INGRAM MARINE GROUP", "INGRAM CORP", "INGRAM BARGE CO"
- Canonical: "Ingram Barge Company"

**Kirby Corporation**
- Variants: "KIRBY INLAND MARINE", "KIRBY OFFSHORE MARINE", "KIRBY CORP"
- Canonical: "Kirby Corporation"

### Legal Entity Variations

Common patterns to standardize:
- LLC / L.L.C. / L.L.C
- INC / INC. / INCORPORATED
- CORP / CORP. / CORPORATION
- CO / CO. / COMPANY

## Expected Results

### Before Standardization
- 4,106 unique operator names across all years
- Many duplicates due to naming variations

### After Standardization
- ~3,500 unique standardized operator names
- Cleaner trend analysis
- Accurate operator fleet tracking over time

## Tips

1. **Use Official Names**: Choose the name that appears on:
   - Company website
   - SEC filings
   - MARAD documentation

2. **Check Recent Names**: If a company was renamed, use the current name

3. **Preserve History**: Don't consolidate if companies merged/split
   - Keep separate if ownership changed
   - Use mapping only for naming variants, not corporate restructuring

4. **Validate Changes**: After applying mapping, spot-check a few operators:
   ```sql
   SELECT operator_name, operator_name_std, fleet_year
   FROM operators
   WHERE operator_name_std = 'American Commercial Barge Line'
   ORDER BY fleet_year
   ```

## Maintenance

- **Regular Reviews**: Check for new variants when loading new years
- **Industry Changes**: Update for mergers, acquisitions, rebranding
- **Data Quality**: Add new mappings as you discover inconsistencies

## Support Files

All files are in `G:\My Drive\LLM\project_us_flag\`:

- Mapping dictionary: `data/operator_name_mapping.yaml`
- Analysis script: `scripts/usace/analyze_operator_variants.py`
- Application script: `scripts/usace/apply_operator_mapping.py`
- Analysis output: `data/operator_variants_analysis.txt` (generated)
- This guide: `data/OPERATOR_MAPPING_README.md`
