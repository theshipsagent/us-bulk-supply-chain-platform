# Port Call Merge Strategy Plan

## Overview
Merge ENTRANCE (inbound) and CLEARANCE (outbound) records to create complete port call records.

**Concept**: A complete port call = Vessel arrives (entrance) + Vessel departs (clearance)

---

## Column Analysis

### UNIQUE to ENTRANCE (2 columns)
- `Arrival_Date` - Date vessel entered US port
- `Arrival_Port_Name` - Arrival port name

### UNIQUE to CLEARANCE (2 columns)
- `Clearance_Date` - Date vessel departed US port
- `Clearance_Port_Name` - Clearance port name

### UNIVERSAL (55 columns - present in both)
**Core Identifiers:**
- `IMO` - Unique vessel identifier (PRIMARY MATCH KEY)
- `Vessel` - Vessel name
- `PORT` - USACE port code (PRIMARY MATCH KEY)
- `RECID` - Original record ID (for traceability)

**Port Details:**
- `US_Port_USACE`, `Port_Consolidated`, `Port_Coast`, `Port_Region`
- `PWW_IND` - Port/Waterway indicator

**Vessel Specifications:**
- `RIG_DESC`, `ICST_DESC`, `FLAG_CTRY`
- `NRT`, `GRT`, `DRAFT_FT`, `DRAFT_IN`
- `Ships_Type`, `Ships_DWT`, `Ships_Draft`, `Ships_Grain`, `Ships_TPC`, `Ships_LOA`, `Ships_Beam`, `Ships_GT`
- `Vessel_Type`, `Vessel_DWT`, `Vessel_Grain`, `Vessel_TPC`, `Vessel_Dwt_Draft_m`, `Vessel_Dwt_Draft_ft`
- `Ships_Match`, `Vessel_Match_Method`

**Draft Analysis:**
- `Draft_Pct_of_Max` - Draft percentage
- `Forecasted_Activity` - Load/Discharge

**Previous/Next Port (meaning differs):**
- `WHERE_IND` - Foreign/Coastwise
  - ENTRANCE: Where vessel CAME FROM
  - CLEARANCE: Where vessel is GOING TO
- `WHERE_PORT` - Domestic port code
- `WHERE_SCHEDK` - Foreign port code
- `WHERE_NAME` - Port name
- `WHERE_CTRY` - Country
- `Previous_US_Port_USACE` - US port name
- `Previous_Foreign_Port` - Foreign port name
- `Previous_Foreign_Country` - Foreign country

**Cargo & Fees:**
- `Group`, `Commodity`, `Carrier_Name`, `Tons`
- `Fee_Base`, `Fee_Adj`, `Fee_Class` - **ONE FEE PER PORT CALL** (from entrance)
- `Agency_Fee`, `Agency_Fee_Adj`

**Other:**
- `TYPEDOC` - Imports (entrance) / Exports (clearance)
- `CONTAINER` - Container indicator
- `Count` - Always 1

---

## Matching Logic

### Match Keys
1. **IMO** (vessel identifier)
2. **PORT** (USACE port code)
3. **Date sequence**: Clearance_Date > Arrival_Date

### Matching Algorithm
```
FOR EACH unique IMO + PORT combination:
  1. Get all ENTRANCES sorted by Arrival_Date (ascending)
  2. Get all CLEARANCES sorted by Clearance_Date (ascending)
  3. FOR EACH entrance:
       Find NEXT clearance where Clearance_Date > Arrival_Date
       IF found:
         CREATE port_call record (entrance + clearance)
         Mark both as MATCHED
       ELSE:
         Flag entrance as UNMATCHED (vessel still in port / year-end / data issue)
  4. Flag any remaining unmatched clearances (entered previous year / data issue)
```

### Edge Cases
1. **Entrance with no matching clearance**
   - Vessel still in port at year-end (Dec 31, 2023)
   - Data quality issue (clearance not reported)
   - Keep as entrance-only record, flag for review

2. **Clearance with no matching entrance**
   - Vessel entered in previous year (Dec 2022)
   - Data quality issue (entrance not reported)
   - Keep as clearance-only record, flag for review

3. **Multiple entrances before single clearance**
   - Unusual but possible (vessel repositioning within port)
   - Match clearance to LAST entrance before clearance date

4. **Multiple clearances after single entrance**
   - Unusual but possible
   - Match entrance to FIRST clearance after arrival date

---

## Merged Record Structure

### New Port Call Schema (60+ columns)

#### Port Call Identification (4 columns)
- `Port_Call_ID` - **NEW**: Sequential port call ID (1, 2, 3...)
- `Entrance_RECID` - **NEW**: Original entrance record ID (traceability)
- `Clearance_RECID` - **NEW**: Original clearance record ID (traceability)
- `Match_Status` - **NEW**: 'COMPLETE', 'ENTRANCE_ONLY', 'CLEARANCE_ONLY'

#### Port Call Timing (3 columns)
- `Arrival_Date` - From entrance record
- `Clearance_Date` - From clearance record (NULL if entrance-only)
- `Days_in_Port` - **NEW**: Clearance_Date - Arrival_Date (NULL if incomplete)

#### US Port (from entrance - authoritative)
- `PORT` - USACE port code
- `Port_Name` - Port name
- `US_Port_USACE` - USACE port name
- `Port_Consolidated` - Census consolidated port
- `Port_Coast` - Coast region
- `Port_Region` - Geographic region
- `PWW_IND` - Port/Waterway

#### Vessel (from entrance - authoritative)
- `IMO` - Vessel identifier
- `Vessel` - Vessel name
- `FLAG_CTRY` - Flag country
- `RIG_DESC` - Vessel rig
- `ICST_DESC` - ICST vessel type
- `NRT`, `GRT` - Tonnage
- `DRAFT_FT`, `DRAFT_IN` - Draft
- `CONTAINER` - Container indicator

#### Vessel Specifications (from entrance)
- `Ships_Type`, `Ships_DWT`, `Ships_Draft`, `Ships_Grain`, `Ships_TPC`
- `Ships_LOA`, `Ships_Beam`, `Ships_GT`, `Ships_Match`
- `Vessel_Type`, `Vessel_DWT`, `Vessel_Grain`, `Vessel_TPC`
- `Vessel_Dwt_Draft_m`, `Vessel_Dwt_Draft_ft`, `Vessel_Match_Method`

#### Draft Analysis (from entrance)
- `Draft_Pct_of_Max` - Arrival draft percentage
- `Forecasted_Activity` - Load/Discharge forecast

#### Origin Port (WHERE came FROM - from entrance)
- `Origin_IND` - **RENAMED** from entrance WHERE_IND
- `Origin_PORT` - **RENAMED** from entrance WHERE_PORT
- `Origin_SCHEDK` - **RENAMED** from entrance WHERE_SCHEDK
- `Origin_Name` - **RENAMED** from entrance WHERE_NAME
- `Origin_Country` - **RENAMED** from entrance WHERE_CTRY
- `Origin_US_Port_USACE` - **RENAMED** from entrance Previous_US_Port_USACE
- `Origin_Foreign_Port` - **RENAMED** from entrance Previous_Foreign_Port
- `Origin_Foreign_Country` - **RENAMED** from entrance Previous_Foreign_Country

#### Destination Port (WHERE going TO - from clearance)
- `Destination_IND` - **RENAMED** from clearance WHERE_IND
- `Destination_PORT` - **RENAMED** from clearance WHERE_PORT
- `Destination_SCHEDK` - **RENAMED** from clearance WHERE_SCHEDK
- `Destination_Name` - **RENAMED** from clearance WHERE_NAME
- `Destination_Country` - **RENAMED** from clearance WHERE_CTRY
- `Destination_US_Port_USACE` - **RENAMED** from clearance Previous_US_Port_USACE
- `Destination_Foreign_Port` - **RENAMED** from clearance Previous_Foreign_Port
- `Destination_Foreign_Country` - **RENAMED** from clearance Previous_Foreign_Country

#### Cargo & Fees (from entrance - authoritative)
- `Group` - Cargo group
- `Commodity` - Commodity type
- `Carrier_Name` - Carrier
- `Tons` - Tonnage
- **`Fee_Base`** - Base agency fee (ONE PER PORT CALL)
- **`Fee_Adj`** - Adjusted fee
- **`Fee_Class`** - Fee classification
- `Agency_Fee`, `Agency_Fee_Adj`

#### Quality Flags (NEW)
- `Match_Status` - COMPLETE / ENTRANCE_ONLY / CLEARANCE_ONLY
- `Match_Confidence` - HIGH / MEDIUM / LOW
  - HIGH: Standard match (1 entrance → 1 clearance, reasonable time gap)
  - MEDIUM: Multiple visits, unusual timing
  - LOW: Data quality concerns
- `Data_Quality_Notes` - Any issues or observations

---

## Implementation Steps

### Phase 1: Data Preparation
1. Parse dates correctly (MMYDD format → YYYY-MM-DD)
2. Add parsed date columns to both entrance and clearance datasets
3. Validate date parsing (all dates in 2023)

### Phase 2: Matching
1. Group by IMO + PORT
2. Sort each group: entrance by Arrival_Date, clearance by Clearance_Date
3. Apply matching algorithm
4. Calculate Days_in_Port for complete port calls
5. Assign Match_Status and Match_Confidence

### Phase 3: Merge
1. Create merged records with proper column naming:
   - Origin_* (from entrance WHERE_*)
   - Destination_* (from clearance WHERE_*)
2. Add Port_Call_ID, Entrance_RECID, Clearance_RECID
3. Add quality flags

### Phase 4: Validation
1. Check match statistics:
   - % of complete port calls
   - % entrance-only (expected: ~small, year-end effect)
   - % clearance-only (expected: ~small, year-start carryover)
2. Validate Days_in_Port distribution (expected: 1-7 days typical, >30 days unusual)
3. Review unmatched records for patterns

### Phase 5: Output
1. Generate three files:
   - **port_calls_COMPLETE_v4.0.0.csv** - Matched port calls
   - **port_calls_ENTRANCE_ONLY_v4.0.0.csv** - Unmatched entrances
   - **port_calls_CLEARANCE_ONLY_v4.0.0.csv** - Unmatched clearances
2. Generate summary statistics report
3. Update documentation

---

## Expected Outcomes

### Match Rate Estimates
- **Complete port calls**: ~85-95% (most vessels arrive and depart within same year)
- **Entrance-only**: ~3-8% (vessels in port at Dec 31, 2023)
- **Clearance-only**: ~3-8% (vessels that entered in Dec 2022)

### Benefits of Merged Data
1. **Complete voyage picture**: Origin → US Port → Destination
2. **Accurate port stay duration**: Days_in_Port
3. **Single fee per port call**: No double-counting
4. **Better analytics**: Full supply chain visibility
5. **Traceability**: Can trace back to original entrance/clearance records via RECID fields

---

## Fee Handling

**CRITICAL**: Only ONE fee per port call
- Use `Fee_Base` and `Fee_Adj` from **ENTRANCE record** (authoritative)
- Do NOT add fees from both entrance and clearance
- Fee represents the port call event, not each transaction type

**Rationale**:
- Entrance determines the fee assessment
- Clearance is administrative departure record
- Billing is per port call, not per document

---

## Questions for User Confirmation

1. ✓ Use entrance WHERE_* as Origin, clearance WHERE_* as Destination?
2. ✓ Take fee from entrance record only (not clearance)?
3. ✓ Create three output files (complete, entrance-only, clearance-only)?
4. ✓ Use Entrance_RECID and Clearance_RECID for traceability?
5. Any specific Days_in_Port thresholds for flagging unusual port stays?
6. Should we create a separate "data quality" output for review?

---

**Author**: WSD3 / Claude Code
**Date**: 2026-02-05
**Version**: 1.0.0
