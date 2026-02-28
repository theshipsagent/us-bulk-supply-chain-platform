# Terminal Classification Guide

## Overview

The Maritime Voyage Analysis System has been enhanced to integrate terminal roll-up classifications from a comprehensive terminal zone dictionary. This guide documents how these classifications are loaded, applied, and output throughout the system.

## Purpose of Terminal Roll-Up Classifications

Terminal roll-up classifications provide standardized metadata about maritime zones and terminals in the system. Each zone can have the following classification attributes:

- **Facility**: The aggregated facility name or roll-up terminal name
- **Vessel Types**: Restrictions on what vessel types can use this zone (e.g., "Bulk - Only", "Tanker - Only", "All")
- **Activity**: The primary activities allowed at this zone (e.g., "Load", "Discharge", "Anchoring - Only", "All")
- **Cargoes**: Types of cargo that can be handled (e.g., "Dry Bulk, Break Bulk Only", "Liquid Bulk - Only", "All")

These classifications enable:
- **Cargo Matching**: Verify if cargo types match facility capabilities
- **Vessel Screening**: Check if vessel types are permitted at specific terminals
- **Activity Planning**: Understand what operations are available at each location
- **Compliance Analysis**: Ensure vessel activities align with facility constraints

## Data Flow Architecture

### 1. Source Data

**File**: `terminal_zone_dictionary.csv` (Read-Only Reference)

This is the authoritative source containing all terminal classifications:

```
Zone,Facility,Vessel Types,Activity,Cargoes,ZoneType,Note
110 Buoys,110 Buoys,Bulk - Only,Load or Discharge,"Dry Bulk, Break Bulk Only",Mid-Stream,
111 Buoys,111 Buoys,Bulk - Only,Load or Discharge,"Dry Bulk, Break Bulk Only",Mid-Stream,
Burnside Terminal,ABT Burnside ,Bulk - Only,Load or Discharge,"Dry Bulk, Break Bulk Only",Bulk Terminal,
...
```

**Critical**: Source CSV files are NEVER modified during processing. All data operations are in-memory only.

### 2. Zone Lookup Module

**File**: `src/data/zone_lookup.py`

The `ZoneLookup` class manages classification lookups:

```python
from src.data.zone_lookup import ZoneLookup

# Initialize lookup with dictionary file
lookup = ZoneLookup("terminal_zone_dictionary.csv")

# Get classification for a zone
classification = lookup.get_classification("Burnside Terminal")
# Returns: {
#     'facility': 'ABT Burnside',
#     'vessel_types': 'Bulk - Only',
#     'activity': 'Load or Discharge',
#     'cargoes': 'Dry Bulk, Break Bulk Only'
# }

# Check if zone exists in dictionary
has_it = lookup.has_classification("Unknown Zone")  # Returns False

# Get all zones
all_zones = lookup.get_all_zones()

# Get statistics
stats = lookup.get_stats()
# Returns: {
#     'total_zones': 218,
#     'zones_with_vessel_types': 215,
#     'zones_with_activity': 218,
#     'zones_with_cargoes': 218
# }
```

### 3. Event Model Enhancement

**File**: `src/models/event.py`

The `Event` dataclass now includes four new optional fields:

```python
@dataclass
class Event:
    # ... existing fields ...
    facility: Optional[str] = None        # Roll-up facility name
    vessel_types: Optional[str] = None    # Allowed vessel types
    activity: Optional[str] = None        # Activity type
    cargoes: Optional[str] = None         # Cargo types handled
```

These fields are populated during event creation and carry forward to output files.

### 4. Data Preprocessor Integration

**File**: `src/data/preprocessor.py`

The `DataPreprocessor` now:

1. Initializes a `ZoneLookup` instance in `__init__`
2. For each event row, calls `zone_lookup.get_classification(zone)`
3. Populates the Event object with classification attributes

```python
class DataPreprocessor:
    def __init__(self, dict_path: str = "terminal_zone_dictionary.csv"):
        self.zone_classifier = ZoneClassifier()
        self.zone_lookup = ZoneLookup(dict_path)  # NEW
        # ...

    def _create_event_from_row(self, row: pd.Series) -> Event:
        # ... existing code ...

        # NEW: Lookup zone classifications
        zone_classification = self.zone_lookup.get_classification(zone)

        event = Event(
            # ... existing fields ...
            facility=zone_classification.get('facility'),      # NEW
            vessel_types=zone_classification.get('vessel_types'),  # NEW
            activity=zone_classification.get('activity'),      # NEW
            cargoes=zone_classification.get('cargoes')         # NEW
        )
        return event
```

### 5. CSV Output Generation

**File**: `src/output/csv_writer.py`

The CSV output now includes the new classification columns in the event log:

**event_log.csv columns:**

```
VoyageID, IMO, VesselName, EventType, EventTime, Zone,
ZoneType, Action, DurationToNextEventHours, NextEventType,
Draft, VesselType, Facility, VesselTypes, Activity, Cargoes
```

Example output:
```
1,1234567,VESSEL NAME,TERMINAL_ARRIVE,2024-01-15 10:30:00,Burnside Terminal,TERMINAL,Arrive,,TERMINAL_DEPART,38.5,Bulk Carrier,ABT Burnside,Bulk - Only,Load or Discharge,Dry Bulk Break Bulk Only
```

## Processing Pipeline

```
terminal_zone_dictionary.csv (Read-Only)
        ↓
  ZoneLookup
        ↓
  DataPreprocessor (Event Creation)
        ↓
  Event Objects (with classifications)
        ↓
  Voyage Detection & Analysis
        ↓
  CSVWriter (Output)
        ↓
  event_log.csv (with classification columns)
```

## Implementation Details

### How Classifications are Applied

1. **Load Phase**: `ZoneLookup._load_dictionary()` reads `terminal_zone_dictionary.csv`
2. **Index Phase**: Zone names are indexed for O(1) lookup performance
3. **Event Phase**: During event creation, `zone_lookup.get_classification(zone_name)` is called
4. **Default Handling**: If a zone is not in the dictionary:
   - `facility` defaults to the zone name
   - Other fields default to `None`
5. **Output Phase**: All fields are written to CSV, with empty strings for `None` values

### Memory Efficiency

- Dictionary loaded once at initialization
- In-memory lookups are O(1) via Python dict hash table
- No modifications to source data
- Lookup data is garbage collected after analysis

## Handling Unknown Zones

When a zone is encountered that's not in `terminal_zone_dictionary.csv`:

```python
classification = lookup.get_classification("Unknown Zone Name")
# Returns:
# {
#     'facility': 'Unknown Zone Name',  # Defaults to zone name
#     'vessel_types': None,
#     'activity': None,
#     'cargoes': None
# }
```

This ensures the system is resilient to new or typo'd zone names while still providing facility context.

## Testing and Validation

### Check Classifications are Loaded

```python
from src.data.zone_lookup import ZoneLookup

lookup = ZoneLookup("terminal_zone_dictionary.csv")
stats = lookup.get_stats()
print(f"Loaded {stats['total_zones']} zones")
# Output: Loaded 218 zones
```

### Verify Event Classification

```python
from src.data.preprocessor import DataPreprocessor
import pandas as pd

preprocessor = DataPreprocessor("terminal_zone_dictionary.csv")
# Process events...
# Check first event has classification fields populated
events = preprocessor.process_dataframe(df)
first_event = events[0]
print(f"Facility: {first_event.facility}")
print(f"Activity: {first_event.activity}")
```

### Inspect CSV Output

```bash
# Check that new columns are present
head -1 results/event_log.csv
# Should show: ...,Facility,VesselTypes,Activity,Cargoes
```

## Important Notes

### Source Data Integrity

- **NEVER** modify `terminal_zone_dictionary.csv` during processing
- Source CSV is a read-only reference database
- All operations are in-memory transformations only
- Original source data remains unchanged after processing

### Column Order in Output

The event log CSV includes the classification columns at the end:
- Columns 1-12: Core event data (VoyageID through VesselType)
- Columns 13-16: Classification data (Facility, VesselTypes, Activity, Cargoes)

This ordering allows backward compatibility with tools expecting the original column set.

### Null Value Handling

- In Python: Fields are `None` for unclassified attributes
- In CSV output: `None` values become empty strings `""`
- This maintains valid CSV structure while preserving null semantics

## Configuration

The dictionary path can be customized during preprocessor initialization:

```python
preprocessor = DataPreprocessor("path/to/custom_dictionary.csv")
```

The dictionary file must be a CSV with these columns:
- `Zone` (required, used as lookup key)
- `Facility` (used for facility field)
- `Vessel Types` (used for vessel_types field)
- `Activity` (used for activity field)
- `Cargoes` (used for cargoes field)

Additional columns in the CSV are ignored.

## Troubleshooting

### Dictionary Not Loading

```
WARNING Zone dictionary not found at terminal_zone_dictionary.csv. Using empty lookup.
```

**Solution**: Ensure `terminal_zone_dictionary.csv` is in the working directory or provide the correct path to `ZoneLookup()` or `DataPreprocessor()`.

### Missing Classification Columns in Output

**Check**: Verify that `DataPreprocessor` was initialized with the dictionary path and that `Event` objects are being created with the new fields.

### Performance Concerns

- Initial load of 218 zones: < 10ms
- Per-event lookup: O(1) via dict hash
- Memory footprint: < 100KB for entire dictionary

## Version History

- **v1.0** (2024): Initial implementation with ZoneLookup module and CSV enhancement
  - Added 4 new Event fields: facility, vessel_types, activity, cargoes
  - Created ZoneLookup class for dictionary management
  - Enhanced CSV output with classification columns
  - Integrated lookup into DataPreprocessor

## Future Enhancements

Potential improvements to the classification system:

1. **Caching**: Cache lookups in Redis for multi-process systems
2. **Validation**: Validate that vessel_types match vessel data
3. **Compliance Checking**: Flag mismatches between activity and actual events
4. **Analytics**: Generate reports on facility utilization vs. restrictions
5. **Updates**: Support dynamic dictionary updates without restart
6. **Fuzzy Matching**: Handle zone name variations and typos

## Support

For issues with classifications or the zone lookup system:

1. Check `src/data/zone_lookup.py` for implementation details
2. Verify `terminal_zone_dictionary.csv` content
3. Review logging output from `ZoneLookup._load_dictionary()`
4. Inspect Event objects to confirm classification fields are populated
