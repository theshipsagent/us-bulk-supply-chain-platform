# FINAL Zone Report Cleanup Plan

## Current Status Summary

| Year | Total Files | ANCHORAGE | CROSS IN | CROSS OUT | TERMINAL | Status |
|------|-------------|-----------|----------|-----------|----------|--------|
| 2018 | 5 | ✓ | ✓ | ✓ | ✓ + 1 DUP | Extra duplicate |
| 2019 | 4 | ✓ | ✓ | ✓ | ✓ | ✅ **COMPLETE** |
| 2020 | 4 | ✓ | ✓ | ✓ | ✓ | ✅ **COMPLETE** |
| 2021 | 5 | ✓ | ✓ | ✓ | ✓ + 1 DUP | Extra duplicate |
| 2022 | 5 | ✓ | ✓ | ✓ + 1 DUP | ✓ | Extra duplicate |
| 2023 | 6 | ✓ + 1 DUP | ✓ | ✓ | ✓ + 1 DUP | 2 extra duplicates |
| 2024 | 5 | ✓ | ✓ | ✓ + 1 DUP | ✓ | Extra duplicate |
| 2025 | 5 | ✓ | ✓ + 1 DUP | ✓ | ✓ | Extra duplicate |
| 2026 | 4 | ✓ | ✓ | ✓ | ✓ | ✅ **COMPLETE** |

---

## FILES TO DELETE (7 duplicates)

### 2018 - Delete 1 file
**Issue:** Exact duplicate TERMINAL files
- **DELETE:** `Zone Report 01-01-18 - 12-31-18.csv` (778.1K)
- **KEEP:** `Zone Report 01-01-18 - 12-31-18 (3).csv` (778.1K)
- **Reason:** Exact duplicates (same hash: c9e0c61350fc...)

### 2021 - Delete 1 file
**Issue:** Exact duplicate TERMINAL files
- **DELETE:** `Zone Report 01-01-21 - 12-31-21 (2).csv` (1112.9K)
- **KEEP:** `Zone Report 01-01-21 - 12-31-21 (1).csv` (1112.9K)
- **Reason:** Exact duplicates (same hash: 7140ed142688...)

### 2022 - Delete 1 file
**Issue:** Exact duplicate CROSS OUT files
- **DELETE:** `Zone Report 01-01-22 - 12-31-22 (3).csv` (402.4K)
- **KEEP:** `Zone Report 01-01-22 - 12-31-22 (2).csv` (402.4K)
- **Reason:** Exact duplicates (same hash: f850030a4552...)

### 2023 - Delete 2 files
**Issue 1:** ANCHORAGE files with different record counts
- **DELETE:** `Zone Report 01-01-23 - 12-31-23 (1).csv` (1181.7K - 15,194 rows)
- **KEEP:** `Zone Report 01-01-23 - 12-31-23 (3).csv` (1187.2K - 15,269 rows)
- **Reason:** File (3) has 75 MORE records

**Issue 2:** Exact duplicate TERMINAL files (NOTE: weird filename date "01-01-22" but it's 2023 data)
- **DELETE:** `Zone Report 01-01-22 - 01-31-23.csv` (1216.2K)
- **KEEP:** `Zone Report 01-01-22 - 01-31-23 (1).csv` (1216.2K)
- **Reason:** Exact duplicates (same hash: f7ed46a3ff38...)

### 2024 - Delete 1 file
**Issue:** Exact duplicate CROSS OUT files
- **DELETE:** `Zone Report 01-01-24 - 12-31-24 (4).csv` (407.4K)
- **KEEP:** `Zone Report 01-01-24 - 12-31-24 (2).csv` (407.4K)
- **Reason:** Exact duplicates (same hash: d343e0316830...)

### 2025 - Delete 1 file
**Issue:** CROSS IN files with different record counts
- **DELETE:** `Zone Report 01-01-25 - 12-31-25 (2).csv` (401.8K - 5,516 rows)
- **KEEP:** `Zone Report 01-01-25 - 12-31-25 (4).csv` (402.0K - 5,518 rows)
- **Reason:** File (4) has 2 MORE records

### 2026 - No deletions needed
**Status:** Already complete with 4 unique files ✅

---

## DELETE COMMANDS

Copy and paste these commands in Command Prompt:

```batch
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-18 - 12-31-18.csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-21 - 12-31-21 (2).csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-22 - 12-31-22 (3).csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-23 - 12-31-23 (1).csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-22 - 01-31-23.csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-24 - 12-31-24 (4).csv"
del "G:\My Drive\LLM\project_mrtis\00_source_files\Zone Report 01-01-25 - 12-31-25 (2).csv"
```

---

## AFTER CLEANUP - EXPECTED STATE

All years will have exactly 4 unique zone files:

| Year | Files | Status |
|------|-------|--------|
| 2018 | 4 | ✅ COMPLETE |
| 2019 | 4 | ✅ COMPLETE |
| 2020 | 4 | ✅ COMPLETE |
| 2021 | 4 | ✅ COMPLETE |
| 2022 | 4 | ✅ COMPLETE |
| 2023 | 4 | ✅ COMPLETE |
| 2024 | 4 | ✅ COMPLETE |
| 2025 | 4 | ✅ COMPLETE |
| 2026 | 4 | ✅ COMPLETE |

**Total:** 36 files across 9 years, all complete! 🎉

---

## COMPLETE FILE MAPPING (After Cleanup)

### 2018 ✅
- `Zone Report 01-01-18 - 12-31-18 (4).csv` → ANCHORAGE (737.4K)
- `Zone Report 01-01-18 - 12-31-18 (1).csv` → CROSS IN (255.4K)
- `Zone Report 01-01-18 - 12-31-18 (2).csv` → CROSS OUT (248.7K)
- `Zone Report 01-01-18 - 12-31-18 (3).csv` → TERMINAL (778.1K)

### 2019 ✅
- `Zone Report 01-01-19 - 12-31-19.csv` → ANCHORAGE (1503.0K)
- `Zone Report 01-01-19 - 12-31-19 (1).csv` → CROSS IN (401.3K)
- `Zone Report 01-01-19 - 12-31-19 (2).csv` → CROSS OUT (401.3K)
- `Zone Report 01-01-19 - 12-31-19 (3).csv` → TERMINAL (1275.4K)

### 2020 ✅
- `Zone Report 01-01-20 - 12-31-20 (3).csv` → ANCHORAGE (1255.3K)
- `Zone Report 01-01-20 - 12-31-20 (2).csv` → CROSS IN (384.2K)
- `Zone Report 01-01-20 - 12-31-20 (1).csv` → CROSS OUT (399.5K)
- `Zone Report 01-01-20 - 12-31-20.csv` → TERMINAL (1122.6K)

### 2021 ✅
- `Zone Report 01-01-21 - 12-31-21 (4).csv` → ANCHORAGE (1291.7K)
- `Zone Report 01-01-21 - 12-31-21 (3).csv` → CROSS IN (373.2K)
- `Zone Report 01-01-21 - 12-31-21.csv` → CROSS OUT (385.7K)
- `Zone Report 01-01-21 - 12-31-21 (1).csv` → TERMINAL (1112.9K)

### 2022 ✅
- `Zone Report 01-01-22 - 12-31-22.csv` → ANCHORAGE (1219.2K)
- `Zone Report 01-01-22 - 12-31-22 (1).csv` → CROSS IN (385.4K)
- `Zone Report 01-01-22 - 12-31-22 (2).csv` → CROSS OUT (402.4K)
- `Zone Report 01-01-22 - 12-31-22 (4).csv` → TERMINAL (1114.2K)

### 2023 ✅
- `Zone Report 01-01-23 - 12-31-23 (3).csv` → ANCHORAGE (1187.2K, 15,269 rows)
- `Zone Report 01-01-23 - 12-31-23 (2).csv` → CROSS IN (379.7K)
- `Zone Report 01-01-23 - 12-31-23.csv` → CROSS OUT (392.2K)
- `Zone Report 01-01-22 - 01-31-23 (1).csv` → TERMINAL (1216.2K)

### 2024 ✅
- `Zone Report 01-01-24 - 12-31-24 (1).csv` → ANCHORAGE (1245.1K)
- `Zone Report 01-01-24 - 12-31-24.csv` → CROSS IN (391.5K)
- `Zone Report 01-01-24 - 12-31-24 (2).csv` → CROSS OUT (407.4K)
- `Zone Report 01-01-24 - 12-31-24 (3).csv` → TERMINAL (1246.6K)

### 2025 ✅
- `Zone Report 01-01-25 - 12-31-25 (3).csv` → ANCHORAGE (1181.5K)
- `Zone Report 01-01-25 - 12-31-25 (4).csv` → CROSS IN (402.0K, 5,518 rows)
- `Zone Report 01-01-25 - 12-31-25 (1).csv` → CROSS OUT (417.7K)
- `Zone Report 01-01-25 - 12-31-25.csv` → TERMINAL (1175.7K)

### 2026 ✅
- `Zone Report 01-01-26 - 01-28-26 (3).csv` → ANCHORAGE (89.6K)
- `Zone Report 01-01-26 - 01-28-26 (2).csv` → CROSS IN (31.2K)
- `Zone Report 01-01-26 - 01-28-26 (1).csv` → CROSS OUT (32.4K)
- `Zone Report 01-01-26 - 01-28-26.csv` → TERMINAL (106.8K)

---

## Zone Identification Rules (Updated)

| Zone Type | Action Column | Zone Column Characteristics |
|-----------|---------------|----------------------------|
| **ANCHORAGE** | `Arrive` or `Depart` | Zone names contain "Anch" (e.g., "12 Mile Anch", "Gramercy Anch", "Gramercy Lower Anch") |
| **CROSS IN** | `Enter` only | Zone = "SWP Cross" |
| **CROSS OUT** | `Exit` only | Zone = "SWP Cross" |
| **TERMINAL** | `Arrive` or `Depart` | Zone names contain "Buoys" (e.g., "133 Buoys", "110 Buoys") or dock/terminal names without "Anch" |

---

## Summary

- **Current files:** 43 files
- **Duplicates to delete:** 7 files (5 exact duplicates + 2 files with fewer records)
- **Files after cleanup:** 36 files (9 years × 4 zones)
- **Complete years:** 9 years (2018-2026)
- **All 4 zones present:** ✅ YES (after cleanup)

Once you run the delete commands, all years will be complete with exactly 4 unique zone files each!
