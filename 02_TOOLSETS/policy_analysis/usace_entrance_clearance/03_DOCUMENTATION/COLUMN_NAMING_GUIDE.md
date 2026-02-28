# Column Naming Guide - Laymen-Friendly Names

## Purpose
Rename technical source columns to human-readable, self-explanatory names for final output.

---

## Port Call Identification

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Port_Call_ID | Port_Call_ID | ✓ Already clear |
| TYPEDOC | Record_Type | 0=Entrance Only, 1=Clearance Only, 2=Complete Port Call |
| Entrance_RECID | Entrance_Record_ID | Original entrance record identifier |
| Clearance_RECID | Clearance_Record_ID | Original clearance record identifier |

---

## Port Call Timing

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Arrival_Date | Arrival_Date | ✓ Already clear |
| Clearance_Date | Departure_Date | More intuitive than "clearance" |
| Days_in_Port | Days_in_Port | ✓ Already clear |

---

## US Port Information

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| PORT | Port_Code | USACE 4-digit port code |
| US_Port_USACE | Port_Name | Primary port name |
| Port_Consolidated | Port_Metro_Area | Census consolidated metropolitan port |
| Port_Coast | Coast_Region | Atlantic/Pacific/Gulf/Great Lakes |
| Port_Region | Geographic_Region | Detailed regional classification |
| PWW_IND | Entry_Type | Port or Waterway entry |

---

## Vessel Identification

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Vessel | Vessel_Name | ✓ Already clear |
| IMO | IMO_Number | International Maritime Organization number |
| FLAG_CTRY | Flag_Country | Vessel flag of registry |

---

## Vessel Classification & Size

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| RIG_DESC | Propulsion_Type | Motor/Steam/Towed/etc |
| ICST_DESC | Ship_Type_ICST | ICST vessel classification |
| Ships_Type | Ship_Type_Detail | Detailed vessel type (e.g., "Tanker-VLCC") |
| CONTAINER | Container_Vessel | Y/N indicator |

---

## Vessel Measurements - Tonnage

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| NRT | Net_Registered_Tons | Net registered tonnage |
| GRT | Gross_Registered_Tons | Gross registered tonnage |
| Ships_GT | Gross_Tonnage | Gross tonnage (from registry) |
| Ships_DWT | Deadweight_Tonnage | Deadweight tonnage |
| Vessel_DWT | Deadweight_Tonnage | **DUPLICATE - Remove** |

---

## Vessel Measurements - Physical Dimensions

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Ships_LOA | Length_Overall_Meters | Length overall (meters) |
| Ships_Beam | Beam_Width_Meters | Beam width (meters) |
| Ships_Draft | Max_Draft_Meters | Maximum draft at DWT (meters) |
| Vessel_Dwt_Draft_m | Max_Draft_Meters | **DUPLICATE - Remove** |
| Vessel_Dwt_Draft_ft | Max_Draft_Feet | **DUPLICATE - Remove** |

---

## Vessel Measurements - Draft (Actual)

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| DRAFT_FT | Actual_Draft_Feet | Actual draft at arrival (feet) |
| DRAFT_IN | Actual_Draft_Inches | Inches above feet |
| Draft_Pct_of_Max | Draft_Percent_Capacity | Draft as % of maximum (load indicator) |
| Forecasted_Activity | Load_Status | Load or Discharge (based on draft) |

---

## Vessel Measurements - Capacity

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Ships_Grain | Grain_Capacity_Cubic_Meters | Grain cargo capacity (m³) |
| Vessel_Grain | Grain_Capacity_Cubic_Meters | **DUPLICATE - Remove** |
| Ships_TPC | Tonnes_Per_Centimeter | Weight per cm of draft |
| Vessel_TPC | Tonnes_Per_Centimeter | **DUPLICATE - Remove** |

---

## Vessel Match Quality

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Ships_Match | Vessel_Registry_Match | YES/NO - matched to ship registry |
| Vessel_Match_Method | Match_Method | IMO or Name match |
| Ships_Vessel | Registry_Vessel_Name | Vessel name from registry |
| Vessel_Type | Vessel_Type_Registry | **DUPLICATE - Remove** |

---

## Origin Port (Where vessel CAME FROM)

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Origin_IND | Origin_Type | Foreign or Coastwise (domestic) |
| Origin_PORT | Origin_Port_Code | US port code (if coastwise) |
| Origin_SCHEDK | Origin_Foreign_Code | Foreign port code (Schedule K) |
| Origin_Name | Origin_Port_Name | Port name |
| Origin_Country | Origin_Country | Country name |
| Origin_US_Port_USACE | Origin_US_Port | US port name (if coastwise) |
| Origin_Foreign_Port | Origin_Foreign_Port | ✓ Already clear |
| Origin_Foreign_Country | Origin_Foreign_Country | ✓ Already clear (remove if duplicate) |

---

## Destination Port (Where vessel is GOING TO)

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Destination_IND | Destination_Type | Foreign or Coastwise (domestic) |
| Destination_PORT | Destination_Port_Code | US port code (if coastwise) |
| Destination_SCHEDK | Destination_Foreign_Code | Foreign port code (Schedule K) |
| Destination_Name | Destination_Port_Name | Port name |
| Destination_Country | Destination_Country | ✓ Already clear |
| Destination_US_Port_USACE | Destination_US_Port | US port name (if coastwise) |
| Destination_Foreign_Port | Destination_Foreign_Port | ✓ Already clear |
| Destination_Foreign_Country | Destination_Foreign_Country | ✓ Already clear (remove if duplicate) |

---

## Cargo Information

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Group | Cargo_Group | Liquid Bulk/Dry Bulk/Container/etc |
| Commodity | Commodity_Type | Specific commodity classification |
| Carrier_Name | Carrier_Name | ✓ Already clear |
| Tons | Cargo_Tons | Tonnage of cargo |

---

## Fees & Charges

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Fee_Base | Base_Fee_Amount | Base agency fee (dollars) |
| Fee_Adj | Adjusted_Fee_Amount | Adjusted fee after regional factors |
| Fee_Class | Fee_Category | Fee classification (container/bulk/etc) |
| Agency_Fee | Agency_Fee_Formatted | Fee as formatted currency string |
| Agency_Fee_Adj | Agency_Fee_Adjusted_Formatted | Adjusted fee formatted |

---

## Administrative

| Current Name | Suggested Name | Description |
|--------------|----------------|-------------|
| Count | Record_Count | Always 1 (for aggregation purposes) |

---

## Summary of Changes

### Clear Improvements (33 renames)
- PORT → Port_Code
- TYPEDOC → Record_Type
- IMO → IMO_Number
- RIG_DESC → Propulsion_Type
- ICST_DESC → Ship_Type_ICST
- Ships_Type → Ship_Type_Detail
- FLAG_CTRY → Flag_Country
- NRT → Net_Registered_Tons
- GRT → Gross_Registered_Tons
- DRAFT_FT → Actual_Draft_Feet
- DRAFT_IN → Actual_Draft_Inches
- PWW_IND → Entry_Type
- Ships_GT → Gross_Tonnage
- Ships_DWT → Deadweight_Tonnage
- Ships_LOA → Length_Overall_Meters
- Ships_Beam → Beam_Width_Meters
- Ships_Draft → Max_Draft_Meters
- Ships_Grain → Grain_Capacity_Cubic_Meters
- Ships_TPC → Tonnes_Per_Centimeter
- Ships_Match → Vessel_Registry_Match
- Ships_Vessel → Registry_Vessel_Name
- Clearance_Date → Departure_Date
- US_Port_USACE → Port_Name
- Port_Consolidated → Port_Metro_Area
- Port_Coast → Coast_Region
- Port_Region → Geographic_Region
- Draft_Pct_of_Max → Draft_Percent_Capacity
- Forecasted_Activity → Load_Status
- Fee_Base → Base_Fee_Amount
- Fee_Adj → Adjusted_Fee_Amount
- Fee_Class → Fee_Category
- Group → Cargo_Group
- Tons → Cargo_Tons

### Duplicates to Remove (4 columns)
- Vessel_DWT (use Deadweight_Tonnage)
- Vessel_Dwt_Draft_m (use Max_Draft_Meters)
- Vessel_Dwt_Draft_ft (use Max_Draft_Feet)
- Vessel_Grain (use Grain_Capacity_Cubic_Meters)
- Vessel_TPC (use Tonnes_Per_Centimeter)
- Vessel_Type (use Ship_Type_Detail)

### Keep As-Is (already clear - 15 columns)
- Port_Call_ID
- Arrival_Date
- Days_in_Port
- Vessel_Name
- Container_Vessel
- Carrier_Name
- Origin/Destination fields (most already clear)
- Vessel_Match_Method

---

## Implementation

Apply these renames in the final merge script to produce user-friendly output.

**Total Columns**: ~55-60 (after removing duplicates)
**Renamed**: ~33 columns
**Removed**: ~6 duplicate columns
**Unchanged**: ~15 columns

---

**Author**: WSD3 / Claude Code
**Date**: 2026-02-05
**Version**: 1.0.0
