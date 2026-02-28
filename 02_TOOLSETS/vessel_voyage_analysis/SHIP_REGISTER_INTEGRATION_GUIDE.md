# Ship Register Integration Guide

## Overview

The Maritime Voyage Analysis System now integrates ship characteristics from the ships register. This allows analysis of vessel properties such as deadweight tonnage (DWT), ship type, and draft specifications.

## Architecture

### Components Added

#### 1. ShipRegisterLookup Module
**File**: `src/data/ship_register_lookup.py`

Provides lookups of ship characteristics by:
- **Primary Match**: IMO (International Maritime Organization) number
- **Secondary Match**: Vessel name (if IMO not found)

**Key Features**:
- Loads ships_register_dictionary.csv (52,034 unique vessels)
- Builds efficient lookup dictionaries (IMO → characteristics, Name → IMO)
- Cleans IMO numbers to 7-digit standardized format
- Returns match method for tracking lookup success

**Usage**:
```python
from src.data.ship_register_lookup import ShipRegisterLookup

lookup = ShipRegisterLookup("ships_register_dictionary.csv")
characteristics = lookup.get_ship_characteristics(imo="1004156", vessel_name="SUMURUN")

# Returns:
{
    'ship_type': 'Bulk',
    'dwt': 30000.0,
    'draft_m': 9.5,
    'tpc': 45.2,
    'match_method': 'imo',
    'vessel_name_matched': 'SUMURUN'
}
```

#### 2. Event Model Updates
**File**: `src/models/event.py`

Added 5 new fields to the Event dataclass:
- `ship_type_register`: Vessel type from ships register (e.g., "Bulk", "Tank", "Container")
- `dwt`: Deadweight tonnage in metric tonnes (float)
- `register_draft_m`: Draft from ships register in meters (float)
- `tpc`: Tonnes per centimeter (float)
- `ship_match_method`: How the ship was matched ('imo', 'name', or None)

#### 3. DataPreprocessor Updates
**File**: `src/data/preprocessor.py`

- Initializes ShipRegisterLookup on instantiation
- Calls lookup for every event during preprocessing
- Tracks matching statistics:
  - `ships_matched_imo`: Events where IMO matched
  - `ships_matched_name`: Events where vessel name matched
  - `ships_not_matched`: Events with no match found
- Reports match rate in statistics

#### 4. CSV Writer Updates
**File**: `src/output/csv_writer.py`

Added 5 new columns to event_log.csv:
- `ShipType_Register`: Ship type from register
- `DWT`: Deadweight tonnage
- `RegisterDraft_m`: Draft from register
- `TPC`: Tonnes per centimeter
- `ShipMatchMethod`: Match method used

## Data Flow

```
Raw Event Data
    ↓
DataPreprocessor._create_event_from_row()
    ├→ Zone Classification (existing)
    ├→ Terminal Dictionary Lookup (existing)
    └→ [NEW] ShipRegisterLookup.get_ship_characteristics()
         ├→ Try IMO match first (most reliable)
         └→ Fall back to vessel name match
    ↓
Event object with ship characteristics
    ↓
CSVWriter.write_event_log()
    └→ Includes new ship register columns
```

## IMO Cleaning Process

IMO numbers are standardized to a 7-digit format:

```python
# Examples
1004156 → 1004156 (already 7 digits)
4156    → 0004156 (padded with leading zeros)
01004156 → 1004156 (leading zeros removed, then standardized)
```

**Why**: Some systems record IMOs differently (with/without leading zeros). Standardization ensures consistent matching.

## Matching Logic

### Primary: IMO Matching
1. Clean the IMO from the event (remove zeros, pad to 7 digits)
2. Look up in ship_dict_imo dictionary
3. If found, return characteristics and set match_method='imo'

### Secondary: Name Matching
If IMO doesn't match:
1. Convert vessel name to uppercase
2. Look up in ship_dict_name dictionary
3. If found, return characteristics and set match_method='name'

### No Match
If neither works, return all None values with match_method=None

## Ships Register Dictionary Structure

**File**: `ships_register_dictionary.csv`

| Column | Type | Description |
|--------|------|-------------|
| IMO_Clean | str | Standardized 7-digit IMO |
| IMO_Original | str | Original IMO from source |
| VesselName | str | Vessel name |
| ShipType | str | Vessel type (Bulk, Tank, Container, etc.) |
| DWT | float | Deadweight tonnage in metric tonnes |
| Draft_m | float | Draft in meters |
| TPC | float | Tonnes per centimeter |
| MatchQuality | str | Quality indicator (Exact, Partial, etc.) |

**Size**: 52,034 records covering major maritime vessels in US ports

## Output Columns

### New Event Log Columns

```csv
VoyageID,IMO,VesselName,...,ShipType_Register,DWT,RegisterDraft_m,TPC,ShipMatchMethod
V001,1004156,SUMURUN,...,Bulk,30000.0,9.5,45.2,imo
V002,1005678,UNKNOWN,...,,,,name
V003,1006789,UNMATCHED,...,,,,
```

**Column Descriptions**:
- **ShipType_Register**: Type from register (empty if no match)
- **DWT**: Deadweight tonnage in metric tonnes (empty if not matched or zero)
- **RegisterDraft_m**: Draft specification from register (empty if not matched or zero)
- **TPC**: Tonnes per centimeter displacement (empty if not matched or zero)
- **ShipMatchMethod**: How the record was matched:
  - `imo`: Matched by IMO number (most reliable)
  - `name`: Matched by vessel name (secondary)
  - (empty): No match found

## Statistics & Reporting

After processing, the preprocessor provides matching statistics:

```python
stats = preprocessor.get_stats()

{
    'events_created': 125432,
    'parse_errors': 45,
    'ships_matched_imo': 98765,          # 78.7% by IMO
    'ships_matched_name': 18934,          # 15.1% by name
    'ships_not_matched': 7733,            # 6.2% with no match
    'ship_match_rate_percent': '93.8',
    'register_stats': {
        'total_unique_imos': 52034,
        'total_unique_names': 48567,
        'lookup_initialized': True
    }
}
```

## Use Cases

### 1. Analyzing Port Capacity by Ship Type
```sql
SELECT ShipType_Register, COUNT(*), AVG(DWT)
FROM event_log
WHERE ShipMatchMethod IS NOT NULL
GROUP BY ShipType_Register
ORDER BY COUNT(*) DESC
```

### 2. Draft Requirements Analysis
```sql
SELECT RegisterDraft_m, COUNT(*) as NumVessels
FROM event_log
WHERE RegisterDraft_m IS NOT NULL
GROUP BY ROUND(RegisterDraft_m, 1)
ORDER BY RegisterDraft_m
```

### 3. Displacement Analysis
```sql
SELECT
    VesselName,
    DWT,
    RegisterDraft_m,
    TPC,
    COUNT(*) as NumEvents
FROM event_log
WHERE ShipMatchMethod = 'imo'
GROUP BY VesselName
ORDER BY DWT DESC
```

## Updating the Ships Register

To update with new vessels:

1. **Data Source**: Use the ships_register_012926_1530/01_ships_register.csv
2. **Processing**: Run the ships register dictionary creator (see parallel agent)
3. **Output**: Generates ships_register_dictionary.csv with:
   - Cleaned IMO numbers
   - Duplicate consolidation
   - Quality metrics
4. **Deployment**: Place in project root directory
5. **Reload**: Preprocessor automatically loads on next run

## Troubleshooting

### Low Match Rates (<80%)
- Check if IMO data quality is poor in source
- Verify ships register is current
- Enable secondary matching by ensuring vessel names are standardized

### Missing Ship Types
- Some small vessels may not be in commercial register
- Private vessels may lack type information
- Consider filtering for commercial vessel types only

### Draft Discrepancies
- Register draft (Dwt_Draft) is design draft
- Actual event draft depends on cargo/ballast
- Use register draft for vessel specifications only

## Performance Considerations

- **Memory**: Lookup dictionaries (~200 MB for 52K vessels)
- **Speed**: O(1) lookup time, < 1ms per event
- **Initialization**: ~5 seconds to load and build indices

## File Locations

| File | Purpose |
|------|---------|
| `ships_register_dictionary.csv` | Master lookup file (project root) |
| `src/data/ship_register_lookup.py` | Lookup module |
| `src/models/event.py` | Event model with ship fields |
| `src/data/preprocessor.py` | Integration in preprocessing |
| `src/output/csv_writer.py` | Output with new columns |

## Version History

- **v1.0** (Jan 29, 2026): Initial integration
  - IMO and name-based matching
  - 4 ship characteristics (type, DWT, draft, TPC)
  - Statistics reporting

## Future Enhancements

- Fuzzy matching for vessel names with typos
- Additional characteristics (LOA, Beam, GT, NRT)
- Historical register lookups (ship age, previous names)
- Match confidence scoring
- Integration with real-time AIS vessel data
