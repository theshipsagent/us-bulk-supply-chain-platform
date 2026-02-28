# INVENTORY: 12 Existing Projects — High-Level Assessment
**Date**: 2026-02-23
**Purpose**: Understand what exists, what works, what state each project is in BEFORE reorganization
**Approach**: NON-DESTRUCTIVE - inventory only, no changes

---

## INVENTORY METHODOLOGY

For each project, document:
1. **Size** - Disk space used
2. **Last Modified** - When was it last worked on?
3. **Key Contents** - What files/folders exist?
4. **Working Status** - Does it work? Experimental? Abandoned?
5. **Dependencies** - What does it depend on?
6. **Value Assessment** - Keep, migrate, archive, or discard?

---

## PROJECT #1: project_barge

**Path**: `G:/My Drive/LLM/project_barge/`
**Last Modified**: Feb 19, 2026
**Status**: 🟢 ACTIVE - recently updated

### Contents (preliminary scan):
- USDA GTR rate data
- Lock performance data
- Barge fleet statistics
- Forecasting models (VAR, Prophet)
- Python scripts for rate analysis

### Known Working Components:
- Need to verify specific scripts/databases

### Assessment:
- **Recently active** (Feb 19)
- **High value** - core platform toolset
- **Already partially migrated** to `02_TOOLSETS/barge_cost_model/` in master_reporting
- **Action**: Verify what's in old folder vs. new location; consolidate

---

## PROJECT #2: project_cement_markets

**Path**: `G:/My Drive/LLM/project_cement_markets/`
**Last Modified**: Feb 12, 2026
**Status**: 🟢 ACTIVE

### Contents (preliminary scan):
- Cement market analysis
- SCM data (slag, fly ash, pozzolans)
- Tariff analysis
- SESCO competitive intelligence

### Known Working Components:
- Need to verify

### Assessment:
- **Recently active** (Feb 12)
- **High value** - SESCO client work
- **Already partially migrated** to `03_COMMODITY_MODULES/cement/` in master_reporting
- **Action**: Verify migration completeness

---

## PROJECT #3: project_rail

**Path**: `G:/My Drive/LLM/project_rail/`
**Last Modified**: Feb 23, 2026
**Status**: 🟢 ACTIVE - updated TODAY

### Contents (preliminary scan):
- NTAD/NARN rail network shapefiles
- STB URCS cost tables
- NetworkX routing scripts
- Rail cost modeling code

### Known Working Components:
- Need to verify

### Assessment:
- **VERY recently active** (TODAY)
- **High value** - core platform toolset
- **Already partially migrated** to `02_TOOLSETS/rail_cost_model/` in master_reporting
- **Action**: User may be actively working here - DO NOT DISRUPT

---

## PROJECT #4: task_epa_frs

**Path**: `G:/My Drive/LLM/task_epa_frs/`
**Last Modified**: Feb 9, 2026
**Status**: 🟢 ACTIVE

### Contents (preliminary scan):
- EPA FRS national database (DuckDB, 732 MB)
- Python ETL scripts
- NAICS lookups
- Entity resolution patterns

### Known Working Components:
- DuckDB database (confirmed working)
- ETL pipeline (download, ingest, query)

### Assessment:
- **Recently active** (Feb 9)
- **HIGH VALUE** - foundation for facility intelligence
- **Already partially migrated** to `02_TOOLSETS/facility_registry/` in master_reporting
- **Action**: This is critical - verify DuckDB location and scripts work

---

## PROJECT #5: project_manifest

**Path**: `G:/My Drive/LLM/project_manifest/`
**Last Modified**: Feb 23, 2026
**Status**: 🟢 ACTIVE - updated TODAY

### Contents (preliminary scan):
- Panjiva import records (800K+ records, 4.5 GB)
- Master data dictionary
- Vessel tracking analysis
- HTS code lookups

### Known Working Components:
- Need to verify

### Assessment:
- **VERY recently active** (TODAY)
- **HIGH VALUE** - trade flow analysis foundation
- **Already partially migrated** to `02_TOOLSETS/vessel_intelligence/` in master_reporting
- **Action**: User may be actively working here - DO NOT DISRUPT

---

## PROJECT #6: sources_data_maps

**Path**: `G:/My Drive/LLM/sources_data_maps/`
**Last Modified**: Feb 22, 2026
**Status**: 🟢 ACTIVE - updated YESTERDAY

### Contents (known):
- **PROVEN FACILITY REGISTER** - 167 facilities, 7,999 dataset links ✅
- `master_facilities.csv` - WORKS
- `facility_dataset_links.csv` - WORKS
- `FACILITY_ENTITY_RESOLUTION_EXAMPLES.md` - detailed documentation
- GIS layers, shapefiles, base maps

### Known Working Components:
- ✅ Facility entity resolution (PROVEN)
- ✅ Master facilities registry (167 Lower Miss River facilities)
- ✅ Multi-source data linking (EPA, BTS, Rail, Refineries, etc.)

### Assessment:
- **VERY recently active** (YESTERDAY)
- **HIGHEST VALUE** - contains the working facility register prototype!
- **CRITICAL** - This is the model for Master Facility Register
- **Action**: PRESERVE THIS - it's the gold standard; migrate carefully

---

## PROJECT #7: project_pipelines

**Path**: `G:/My Drive/LLM/project_pipelines/`
**Last Modified**: Feb 5, 2026
**Status**: 🟡 DORMANT (2+ weeks)

### Contents (preliminary scan):
- Pipeline route shapefiles
- Terminal location data

### Assessment:
- **Not recently active**
- **Medium value** - pipeline infrastructure data
- **Action**: Low priority for migration; can wait

---

## PROJECT #8: project_us_flag

**Path**: `G:/My Drive/LLM/project_us_flag/`
**Last Modified**: Feb 13, 2026
**Status**: 🟢 ACTIVE

### Contents (preliminary scan):
- Section 301 analysis
- Jones Act research
- US flag fleet data

### Known Working Components:
- Need to verify

### Assessment:
- **Recently active** (Feb 13)
- **High value** - maritime policy analysis
- **Already partially migrated** to `02_TOOLSETS/policy_analysis/` in master_reporting
- **Action**: Verify migration completeness

---

## PROJECT #9: task_usace_entrance_clearance

**Path**: `G:/My Drive/LLM/task_usace_entrance_clearance/`
**Last Modified**: Feb 7, 2026
**Status**: 🟡 DORMANT (2+ weeks)

### Contents (preliminary scan):
- USACE vessel entrance/clearance records

### Assessment:
- **Not recently active**
- **Medium value** - vessel call data
- **Action**: Lower priority for migration

---

## PROJECT #10: project_mrtis

**Path**: `G:/My Drive/LLM/project_mrtis/`
**Last Modified**: Feb 19, 2026
**Status**: 🟢 ACTIVE

### Contents (preliminary scan):
- USACE MRTIS waterborne commerce exports

### Assessment:
- **Recently active** (Feb 19)
- **High value** - waterborne commerce statistics
- **Action**: Important for barge/waterway analysis

---

## PROJECT #11: project_port_nickle

**Path**: `G:/My Drive/LLM/project_port_nickle/`
**Last Modified**: Feb 5, 2026
**Status**: 🟡 DORMANT (2+ weeks)

### Contents (preliminary scan):
- Plaquemines Parish 11-chapter study
- Port Sulphur economic analysis

### Assessment:
- **Not recently active**
- **Medium value** - regional study
- **Action**: Archive as completed work; extract reusable patterns for port development toolset

---

## PROJECT #12: project_Miss_river

**Path**: `G:/My Drive/LLM/project_Miss_river/` (if exists)
**Status**: NEED TO VERIFY EXISTS

### Contents (expected):
- Lower Mississippi River chapters
- Navigation data
- Hydrology data

### Assessment:
- **Action**: Verify this project exists and assess

---

## SUMMARY FINDINGS

### Active Projects (Recently Updated):
🟢 **HIGH PRIORITY - DO NOT DISRUPT:**
1. **project_rail** (TODAY) - user may be working
2. **project_manifest** (TODAY) - user may be working
3. **sources_data_maps** (YESTERDAY) - **CONTAINS WORKING FACILITY REGISTER**
4. **project_barge** (Feb 19)
5. **project_mrtis** (Feb 19)
6. **project_us_flag** (Feb 13)
7. **project_cement_markets** (Feb 12)
8. **task_epa_frs** (Feb 9)

### Dormant Projects (2+ weeks):
🟡 **LOWER PRIORITY:**
9. **project_pipelines** (Feb 5)
10. **project_port_nickle** (Feb 5) - completed study, can archive
11. **task_usace_entrance_clearance** (Feb 7)

### Already Partially Migrated:
✅ These have content in `project_master_reporting`:
- project_barge → `02_TOOLSETS/barge_cost_model/`
- project_rail → `02_TOOLSETS/rail_cost_model/`
- project_cement_markets → `03_COMMODITY_MODULES/cement/`
- task_epa_frs → `02_TOOLSETS/facility_registry/`
- project_manifest → `02_TOOLSETS/vessel_intelligence/`
- project_us_flag → `02_TOOLSETS/policy_analysis/`

### Critical Finding:
⭐ **sources_data_maps** contains the **WORKING FACILITY REGISTER PROTOTYPE**:
- 167 facilities (master registry)
- 7,999 dataset links
- Proven entity resolution algorithm
- **This is the model** for Master Facility Register nationwide expansion

---

## NEXT STEPS (PROPOSED)

### Step 1: DETAILED INVENTORY (Choose Priority Projects)
Pick 3-5 most critical projects for detailed inventory:
1. **sources_data_maps** (highest priority - working facility register)
2. **task_epa_frs** (facility intelligence foundation)
3. **project_rail** (active TODAY - be careful)
4. **project_manifest** (active TODAY - be careful)
5. ??

### Step 2: VERIFY What's Already Migrated
For each project that's "partially migrated":
- Compare old folder vs. new location
- What's in old that's NOT in new?
- What's working in old that might be broken in new?
- Are scripts pointing to old paths?

### Step 3: SIMPLE CONSOLIDATION PLAN
- Copy (don't move) working pieces
- Update paths
- Test
- Archive original

### Step 4: NO NEW BUILDING
- Stop creating new schemas/databases from scratch
- Use what exists and works
- Reorganize, don't recreate

---

## QUESTIONS FOR USER

1. **Which projects are you actively working in RIGHT NOW?**
   - project_rail (updated today)?
   - project_manifest (updated today)?

2. **Which projects should I inventory in detail first?**
   - Recommend: sources_data_maps (working facility register)
   - Then: task_epa_frs, project_mrtis, project_barge?

3. **Any projects that are abandoned/can be archived immediately?**

4. **Do you want me to verify what's already migrated to project_master_reporting?**
   - Check if old folders have content that new location doesn't

---

**Status**: HIGH-LEVEL INVENTORY COMPLETE
**Next**: Awaiting user direction on which projects to detail inventory first
**Critical Finding**: sources_data_maps has working facility register (167 facilities, 7,999 links)
