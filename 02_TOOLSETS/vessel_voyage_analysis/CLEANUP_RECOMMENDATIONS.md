# Zone Report File Analysis - Cleanup Recommendations

## Summary
Analysis completed on 34 zone report files spanning 2018-2026. Each year should have exactly 4 files representing:
1. **ANCHORAGE** - 12 Mile Anchorage zone
2. **CROSS IN** - SWP Cross entries
3. **CROSS OUT** - SWP Cross exits
4. **TERMINAL** - 133 Buoys or 110 Buoys terminal zones

## Current Status by Year

### ✓ 2019 - COMPLETE (4 files, all zones present)
- Zone Report 01-01-19 - 12-31-19.csv → ANCHORAGE
- Zone Report 01-01-19 - 12-31-19 (1).csv → CROSS IN
- Zone Report 01-01-19 - 12-31-19 (2).csv → CROSS OUT
- Zone Report 01-01-19 - 12-31-19 (3).csv → TERMINAL

### ✓ 2020 - COMPLETE (4 files, all zones present)
- Zone Report 01-01-20 - 12-31-20 (3).csv → ANCHORAGE
- Zone Report 01-01-20 - 12-31-20 (2).csv → CROSS IN
- Zone Report 01-01-20 - 12-31-20 (1).csv → CROSS OUT
- Zone Report 01-01-20 - 12-31-20.csv → TERMINAL

### ✓ 2026 - COMPLETE (4 files, all zones present)
- Zone Report 01-01-26 - 01-28-26 (3).csv → ANCHORAGE
- Zone Report 01-01-26 - 01-28-26 (2).csv → CROSS IN
- Zone Report 01-01-26 - 01-28-26 (1).csv → CROSS OUT
- Zone Report 01-01-26 - 01-28-26.csv → TERMINAL

---

## Issues Requiring Action

### 2018 - MISSING 3 ZONES
**Current:** Only 1 file (TERMINAL)
**Missing:** ANCHORAGE, CROSS IN, CROSS OUT
**Action:** Need to obtain the missing 3 zone reports for 2018

---

### 2021 - DUPLICATE TERMINAL + MISSING 2 ZONES
**Issue:** 2 identical TERMINAL files (exact duplicates)
**Current files:**
- Zone Report 01-01-21 - 12-31-21.csv → CROSS OUT
- Zone Report 01-01-21 - 12-31-21 (1).csv → TERMINAL
- Zone Report 01-01-21 - 12-31-21 (2).csv → TERMINAL (EXACT DUPLICATE)

**Action Required:**
1. **DELETE:** Zone Report 01-01-21 - 12-31-21 (2).csv (duplicate TERMINAL)
2. **OBTAIN:** ANCHORAGE and CROSS IN reports for 2021

---

### 2022 - DUPLICATE CROSS OUT + MISSING TERMINAL
**Issue:** 2 identical CROSS OUT files (exact duplicates)
**Current files:**
- Zone Report 01-01-22 - 12-31-22.csv → ANCHORAGE
- Zone Report 01-01-22 - 12-31-22 (1).csv → CROSS IN
- Zone Report 01-01-22 - 12-31-22 (2).csv → CROSS OUT
- Zone Report 01-01-22 - 12-31-22 (3).csv → CROSS OUT (EXACT DUPLICATE)

**Action Required:**
1. **DELETE:** Zone Report 01-01-22 - 12-31-22 (3).csv (duplicate CROSS OUT)
2. **OBTAIN:** TERMINAL report for 2022

---

### 2023 - DUPLICATE ANCHORAGE + MISSING TERMINAL
**Issue:** 2 ANCHORAGE files with slightly different sizes (NOT exact duplicates - may contain different data)
**Current files:**
- Zone Report 01-01-23 - 12-31-23 (1).csv → ANCHORAGE (1181.7K)
- Zone Report 01-01-23 - 12-31-23 (3).csv → ANCHORAGE (1187.2K)
- Zone Report 01-01-23 - 12-31-23 (2).csv → CROSS IN
- Zone Report 01-01-23 - 12-31-23.csv → CROSS OUT

**Action Required:**
1. **INVESTIGATE:** Compare the two ANCHORAGE files to determine which is correct
   - File (1): 1181.7K
   - File (3): 1187.2K (5.5K larger)
2. **DELETE:** One of the ANCHORAGE files after investigation
3. **OBTAIN:** TERMINAL report for 2023

---

### 2024 - DUPLICATE CROSS OUT (5 files total)
**Issue:** 2 identical CROSS OUT files (exact duplicates)
**Current files:**
- Zone Report 01-01-24 - 12-31-24 (1).csv → ANCHORAGE
- Zone Report 01-01-24 - 12-31-24.csv → CROSS IN
- Zone Report 01-01-24 - 12-31-24 (2).csv → CROSS OUT
- Zone Report 01-01-24 - 12-31-24 (4).csv → CROSS OUT (EXACT DUPLICATE)
- Zone Report 01-01-24 - 12-31-24 (3).csv → TERMINAL

**Action Required:**
1. **DELETE:** Zone Report 01-01-24 - 12-31-24 (4).csv (duplicate CROSS OUT)

**Result:** Will have all 4 zones after deletion

---

### 2025 - DUPLICATE CROSS IN (5 files total)
**Issue:** 2 CROSS IN files with slightly different sizes (NOT exact duplicates - may contain different data)
**Current files:**
- Zone Report 01-01-25 - 12-31-25 (3).csv → ANCHORAGE
- Zone Report 01-01-25 - 12-31-25 (2).csv → CROSS IN (401.8K)
- Zone Report 01-01-25 - 12-31-25 (4).csv → CROSS IN (402.0K)
- Zone Report 01-01-25 - 12-31-25 (1).csv → CROSS OUT
- Zone Report 01-01-25 - 12-31-25.csv → TERMINAL

**Action Required:**
1. **INVESTIGATE:** Compare the two CROSS IN files to determine which is correct
   - File (2): 401.8K
   - File (4): 402.0K (slightly larger)
2. **DELETE:** One of the CROSS IN files after investigation

**Result:** Will have all 4 zones after deletion

---

## Immediate Actions - Safe Deletions

These files are exact duplicates and can be safely deleted immediately:

```bash
# 2021 - Delete duplicate TERMINAL
rm "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-21 - 12-31-21 (2).csv"

# 2022 - Delete duplicate CROSS OUT
rm "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-22 - 12-31-22 (3).csv"

# 2024 - Delete duplicate CROSS OUT
rm "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-24 - 12-31-24 (4).csv"
```

---

## Files Requiring Investigation Before Deletion

### 2023 ANCHORAGE - Not exact duplicates (different sizes)
Compare these files to determine which is correct:
- Zone Report 01-01-23 - 12-31-23 (1).csv → 1181.7K
- Zone Report 01-01-23 - 12-31-23 (3).csv → 1187.2K

### 2025 CROSS IN - Not exact duplicates (different sizes)
Compare these files to determine which is correct:
- Zone Report 01-01-25 - 12-31-25 (2).csv → 401.8K
- Zone Report 01-01-25 - 12-31-25 (4).csv → 402.0K

---

## Missing Files to Obtain

| Year | Missing Zones |
|------|--------------|
| 2018 | ANCHORAGE, CROSS IN, CROSS OUT |
| 2021 | ANCHORAGE, CROSS IN |
| 2022 | TERMINAL |
| 2023 | TERMINAL |

---

## Final State After Cleanup

After completing all actions above:
- **2019, 2020, 2024, 2026:** Complete with 4 unique zone files each ✓
- **2018:** Will have 1/4 files (need to obtain 3 more)
- **2021:** Will have 2/4 files (need to obtain 2 more)
- **2022:** Will have 3/4 files (need to obtain 1 more)
- **2023:** Will have 3/4 files (need to obtain 1 more)
- **2025:** Complete with 4 unique zone files ✓

---

## Zone Identification Reference

For future reference, here's how to identify each zone:

| Zone Type | Identifying Characteristics |
|-----------|---------------------------|
| ANCHORAGE | Zone column contains "12 Mile Anch" |
| CROSS IN | Zone column contains "SWP Cross" AND Action = "Enter" only |
| CROSS OUT | Zone column contains "SWP Cross" AND Action = "Exit" only |
| TERMINAL | Zone column contains "133 Buoys" or "110 Buoys" |
