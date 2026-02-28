# Maritime Voyage Analysis - Data Dictionary & Exclusion List

Generated: 2026-01-29

---

## 📋 PART 1: TERMINAL ZONE DICTIONARY

**Purpose:** Roll-up classification for 217 unique zone names

**File:** `terminal_zone_dictionary.csv`

### Top Terminal/Anchorage Zones by Activity

| Zone Name | Records | Zone Type | Suggested Roll-Up Category |
|-----------|---------|-----------|---------------------------|
| SWP Cross | 81,647 | CROSS_IN/OUT | **Port Boundary** |
| 12 Mile Anch | 9,608 | ANCHORAGE | **Lower River Anchorage** |
| 9 Mile Anch | 9,459 | ANCHORAGE | **Lower River Anchorage** |
| Belle Chasse Anch | 7,888 | ANCHORAGE | **Mid River Anchorage** |
| AMA Anch | 7,230 | ANCHORAGE | **Upper River Anchorage** |
| Lwr Kenner Bend Anch | 7,217 | ANCHORAGE | **Upper River Anchorage** |
| Nashville Ave B C | 5,955 | TERMINAL | **New Orleans Terminals** |
| Burnside Anch | 5,551 | ANCHORAGE | **Upper River Anchorage** |
| ADM Destrehan | 2,509 | TERMINAL | **Grain Terminals** |
| ADM AMA | 2,461 | TERMINAL | **Grain Terminals** |
| Zen-Noh Grain | 2,416 | TERMINAL | **Grain Terminals** |
| Stolthaven 3 | 1,889 | TERMINAL | **Chemical/Petroleum** |
| Exxon Baton Rouge | 1,878 | TERMINAL | **Chemical/Petroleum** |
| Cenex Harvest States | 1,770 | TERMINAL | **Grain Terminals** |
| Bunge Destrehan | 1,669 | TERMINAL | **Grain Terminals** |

### Suggested Roll-Up Categories

1. **Port Boundary**
   - SWP Cross (entry/exit point)

2. **Lower River Anchorage** (Mile 0-30)
   - 9 Mile Anch, 12 Mile Anch, Pilottown Anch, Boothville Anch, Davant Anch, etc.

3. **Mid River Anchorage** (Mile 30-70)
   - Belle Chasse Anch, Pt Celeste Anch, General Anch, Chalmette area anchorages

4. **Upper River Anchorage** (Mile 70+)
   - AMA Anch, Kenner Bend Anch, Bonnet Carre Anch, Burnside Anch, Baton Rouge anchorages

5. **Grain Terminals**
   - ADM (Destrehan, AMA, Reserve), Zen-Noh, Bunge, Cargill, Cenex Harvest States

6. **Chemical/Petroleum Terminals**
   - Stolthaven, Exxon, Shell, Valero, Marathon, PBF, IMTT facilities

7. **Container/General Cargo Terminals**
   - Nashville Ave, Erato St, Julia St

8. **Bulk Terminals**
   - United Bulk, Drax Biomass, Nucor Steel

9. **Buoy Locations**
   - 110 Buoys, 136 Buoys, 158 Buoys, 175 Buoys, 179 Buoys, etc.

**Full List:** See `terminal_zone_dictionary.csv` (217 zones)

---

## 🚫 PART 2: VESSEL EXCLUSION LIST (Dredges & Service Vessels)

**Purpose:** Identify and exclude vessels that create "white noise" (non-cargo operations)

**File:** `vessels_no_imo_exclude_list.csv`

### Vessels Recommended for EXCLUSION (>100 events, no IMO)

| Vessel Name | Event Count | % of Dataset | Likely Type |
|-------------|-------------|--------------|-------------|
| **Allisonk** | 6,028 | 1.89% | Dredge |
| **Allins K** | 1,671 | 0.52% | Dredge (same as above?) |
| **Keeneland** | 709 | 0.22% | Service vessel |
| **Chesapeake Bay** | 375 | 0.12% | Service vessel |
| **Jadwin Discharge** | 250 | 0.08% | Dredge |
| **Dixie Raider** | 167 | 0.05% | Service vessel |

**Total to Exclude:** 9,200 events (2.89% of dataset)

### Vessels Recommended for REVIEW (50-100 events)

| Vessel Name | Event Count | Notes |
|-------------|-------------|-------|
| Jesse A Mollineaux | 99 | Review activity pattern |
| Gol Warrior | 92 | Review activity pattern |
| Amy Clemons Mccall | 61 | Review activity pattern |

### Vessels to KEEP (<50 events)

- 46 additional vessels with low activity
- Likely occasional service vessels or one-time visits
- Total: 550 events across all low-activity vessels

---

## 📊 IMPACT ANALYSIS

### Current Dataset (With Dredges)
```
Total events:              304,765
Total voyages:             41,156
Complete voyages:          40,491 (98.4%)
Incomplete voyages:        665 (1.6%)
Orphaned events:           33,058 (10.8%)
Quality issues:            3,658
```

### Expected After Exclusions
```
Total events:              ~295,565 (-9,200)
Total voyages:             ~41,150 (minimal change)
Complete voyages:          ~40,490 (minimal change)
Orphaned events:           ~23,858 (-9,200, -28%)
Expected completeness:     ~98.4% (same)
Expected quality issues:   ~3,650 (minimal change)
```

### Why This Helps

1. **Reduced Noise:** Removes 9,200 orphaned events from dredges that never connect to voyages
2. **Cleaner Reports:** 28% fewer orphaned events to investigate
3. **Better Matching:** Improves the signal-to-noise ratio for actual cargo vessels
4. **Minimal Impact:** Only 2.89% of data removed, preserves all legitimate voyages

---

## 🔧 IMPLEMENTATION

### Option 1: Add Vessel Filter to Loader

Modify `src/data/loader.py` to exclude vessels without IMO:

```python
# After loading DataFrame
exclude_vessels = ['Allisonk', 'Allins K', 'Keeneland',
                   'Chesapeake Bay', 'Jadwin Discharge', 'Dixie Raider']

df_combined = df_combined[~df_combined['Name'].isin(exclude_vessels)]
logger.info(f"Excluded {len(exclude_vessels)} dredge/service vessels")
```

### Option 2: Add CLI Flag

Add optional `--exclude-no-imo` flag to voyage_analyzer.py:

```bash
python voyage_analyzer.py -i 00_source_files/ -o results/ --exclude-no-imo
```

### Option 3: Pre-filter Source Data

Create cleaned CSV files with dredges already removed.

---

## 📝 NEXT STEPS

### For Terminal Classification:

1. **Review `terminal_zone_dictionary.csv`**
   - 217 unique zones with record counts
   - Classify each zone into roll-up categories
   - Create `zone_rollup_mapping.csv` with columns: Zone, RollUpCategory

2. **Common Roll-Ups:**
   - **By River Mile:** Lower (0-30), Mid (30-70), Upper (70+)
   - **By Terminal Type:** Grain, Chemical, Container, Bulk, Anchorage
   - **By Operator:** ADM facilities, IMTT facilities, Shell facilities, etc.
   - **By Function:** Loading, Unloading, Anchorage, Buoys

3. **Apply Classifications:**
   - Add RollUpCategory column to event_log.csv
   - Aggregate metrics by category in voyage_summary.csv

### For Vessel Exclusions:

1. **Review `vessels_no_imo_exclude_list.csv`**
   - 6 vessels recommended for exclusion (>100 events)
   - 3 vessels for manual review (50-100 events)
   - 46 low-activity vessels (keep)

2. **Decision Points:**
   - **Exclude all 6:** Removes 9,200 events (2.89%)
   - **Exclude 6 + Review 3:** Removes 9,452 events (2.97%)
   - **Custom list:** Pick specific vessels to exclude

3. **Implementation:**
   - Add exclusion logic to data loader
   - OR create cleaned source CSV files
   - OR add CLI flag for flexible filtering

---

## 📈 EXPECTED IMPROVEMENTS

After implementing exclusions:

✅ **~9,200 fewer orphaned events** (-28%)
✅ **Cleaner quality reports** with less noise
✅ **Faster processing** (2.89% fewer records)
✅ **Same voyage completeness** (98.4%)
✅ **Better focus** on actual cargo operations

---

## 📁 FILES GENERATED

1. **terminal_zone_dictionary.csv** (217 zones)
   - Zone name, record count, zone type
   - Ready for roll-up classification

2. **vessels_no_imo_exclude_list.csv** (55 vessels)
   - Vessel name, event count, recommendation
   - Sorted by event count (highest first)

3. **This document** (DATA_DICTIONARY_AND_EXCLUSIONS.md)
   - Analysis and recommendations
   - Implementation guidance

---

## 🎯 RECOMMENDATIONS

### Priority 1: Vessel Exclusions
**Action:** Exclude 6 dredges/service vessels
**Impact:** Immediate -28% reduction in orphaned events
**Effort:** Low (simple name filter)
**Risk:** None (vessels have no valid voyages anyway)

### Priority 2: Terminal Roll-Ups
**Action:** Create zone classification scheme
**Impact:** Better reporting and aggregation
**Effort:** Medium (manual classification needed)
**Risk:** None (additive enhancement)

### Priority 3: Enhanced Filtering
**Action:** Add CLI options for exclusions
**Impact:** Flexible analysis capabilities
**Effort:** Low (CLI flag addition)
**Risk:** None (optional feature)

---

**Generated by:** Maritime Voyage Analysis System v1.0
**Date:** 2026-01-29
**Dataset:** 318,809 source records (2018-2026)
