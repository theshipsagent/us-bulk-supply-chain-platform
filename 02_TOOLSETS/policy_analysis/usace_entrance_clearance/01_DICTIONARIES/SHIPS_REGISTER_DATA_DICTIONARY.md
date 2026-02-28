# Ships Register Data Dictionary
**File:** `01_ships_register.csv`
**Location:** `01_DICTIONARIES/01.03_vessels/`
**Version:** Current (as of 2026-01-29)

---

## Overview

This file contains a comprehensive registry of commercial vessels with technical specifications and classification data.

**Records:** 52,034 vessels
**Columns:** 14
**Primary Key:** IMO (International Maritime Organization number)

---

## File Format

- **Format:** CSV (Comma-Separated Values)
- **Encoding:** UTF-8
- **Delimiter:** Comma (`,`)
- **Header Row:** Yes (Row 1)
- **Data Starts:** Row 2

---

## Column Specifications

### 1. IMO
**International Maritime Organization Number**

- **Type:** String (numeric)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 52,034 (all unique)
- **Format:** 7-digit number
- **Primary Key:** Yes
- **Example Values:** `1004156`, `1004338`, `1006025`

**Description:**
Unique identifier assigned by the International Maritime Organization. This is the global standard for vessel identification and remains with the vessel for its lifetime, regardless of ownership or flag changes.

**Usage:**
Use this field to uniquely identify vessels and join with other datasets (e.g., Panjiva imports, USACE port calls).

---

### 2. Vessel
**Vessel Name**

- **Type:** String
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 49,562 (some vessels share names)
- **Format:** Free text, uppercase
- **Example Values:** `SUMURUN`, `MAKAI`, `ARRIVEDERCI IV`

**Description:**
Current registered name of the vessel. Names can change over time when vessels are sold or reflagged.

**Note:**
Not unique - 2,472 vessels share names with other vessels in the registry. Always use IMO for unique identification.

---

### 3. Design
**Vessel Design Class**

- **Type:** String
- **Population:** 19,483 / 52,034 (37.4%)
- **Unique Values:** 1,610 distinct designs
- **Format:** Design series name
- **Example Values:** `CIMC ORIC 11500`, `Imabari 211`, `I-Star 63 New`

**Description:**
Shipyard design series or class. Indicates the standard design template used for construction. Vessels of the same design typically have identical or very similar specifications.

**Note:**
Missing (blank) for 62.6% of vessels - primarily smaller or older vessels.

**Common Designs:**
- `Imabari 40` - Handymax bulk carrier design
- `I-Star 63 New` - Supramax/Ultramax bulk carrier
- `CIMC ORIC 11500` - Sub-Panamax containership

---

### 4. Type
**Vessel Type Classification**

- **Type:** String
- **Population:** 40,094 / 52,034 (77.1%)
- **Unique Values:** 78 distinct types
- **Format:** Category-Subcategory
- **Example Values:** `Containership-Sub New Panamax`, `Tanker-MR2`, `Bulk Carrier-Capesize`

**Description:**
Detailed vessel classification combining vessel category and size/capacity class.

**Missing:** 11,940 vessels (22.9%) have no type classification.

**Top 20 Vessel Types:**

| Type | Count | % of Total |
|------|-------|------------|
| Bulk Carrier-Supra/Ultramax | 3,662 | 7.0% |
| Bulk Carrier-Pmax/Kamsarmax | 2,317 | 4.5% |
| Bulk Carrier-Large Handy | 2,150 | 4.1% |
| Tanker-MR2 | 2,027 | 3.9% |
| Tanker-<=4,999dwt | 2,009 | 3.9% |
| General Cargo <=4,999 dwt | 1,775 | 3.4% |
| Tanker-Handy | 1,769 | 3.4% |
| General Cargo 5,000-9,999 dwt | 1,746 | 3.4% |
| Containership-Regional Feeder | 1,293 | 2.5% |
| Tanker-5,000-7,499dwt | 1,242 | 2.4% |
| Bulk Carrier-Capesize | 1,126 | 2.2% |
| Tanker-VLCC | 886 | 1.7% |
| General Cargo 10,000-14,999dwt | 857 | 1.6% |
| Containership-Post-Panamax | 842 | 1.6% |
| Bulk Carrier-Handymax | 806 | 1.5% |
| PCC/PCTC => 4,000 cars | 704 | 1.4% |
| General Cargo =>30,000dwt | 698 | 1.3% |
| Containership-Feedermax | 668 | 1.3% |
| Containership-New Panamax | 662 | 1.3% |
| Tanker-Aframax | 654 | 1.3% |

**Categories Include:**
- **Bulk Carriers:** Capesize, Newcastlemax, Panamax, Supramax, Handymax, Handysize
- **Tankers:** VLCC, Suezmax, Aframax, LR1/LR2, MR1/MR2, Handy, Small
- **Containerships:** Post-Panamax, New Panamax, Panamax, Feedermax, Regional Feeder
- **General Cargo:** Size ranges from <=4,999 dwt to >=30,000 dwt
- **Ro-Ro:** Car carriers (PCC/PCTC), General Ro-Ro
- **Gas Carriers:** LNG, LPG (various sizes)
- **Specialized:** Reefers, Chemical tankers, Product tankers

---

### 5. DWT
**Deadweight Tonnage**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 27,886
- **Format:** Integer (metric tons)
- **Range:** 0 to 440,000+ MT
- **Example Values:** `0`, `66`, `5026`, `139000`, `210125`

**Description:**
Total weight a vessel can safely carry, including cargo, fuel, fresh water, ballast water, provisions, passengers, and crew.

**Note:**
Many records show `0` - indicates data not available or not applicable (e.g., yachts, service vessels).

**Common Ranges:**
- **Handysize Bulk:** 20,000 - 40,000 MT
- **Supramax/Ultramax:** 50,000 - 65,000 MT
- **Panamax:** 65,000 - 90,000 MT
- **Capesize:** 100,000 - 200,000 MT
- **VLCC Tanker:** 200,000 - 320,000 MT

---

### 6. LOA
**Length Overall**

- **Type:** Numeric (stored as string)
- **Population:** 52,008 / 52,034 (100.0%)
- **Unique Values:** 7,532
- **Format:** Decimal (meters)
- **Range:** 0 to 400+ meters
- **Example Values:** `0`, `35.28`, `97.55`, `244.009`, `296.02`

**Description:**
Total length of the vessel from the foremost point to the aftermost point, measured in meters.

**Note:**
26 records missing LOA. Many records show `0` indicating data not available.

**Typical Ranges:**
- **Small vessels:** < 50m
- **Handysize:** 150-200m
- **Panamax:** 200-250m
- **Capesize/VLCC:** 250-350m
- **Ultra-large:** > 350m

---

### 7. Beam
**Vessel Beam (Width)**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 3,265
- **Format:** Decimal (meters)
- **Range:** 0 to 60+ meters
- **Example Values:** `5.06`, `8`, `32.292`, `45.038`

**Description:**
Maximum width of the vessel at its widest point, measured in meters.

**Note:**
Beam determines canal/lock compatibility (e.g., Panama Canal max ~49m, Suez Canal ~77m).

**Typical Ranges:**
- **Handysize:** 20-30m
- **Panamax:** 32.2m (Panama Canal limit)
- **Post-Panamax:** 32.3-49m
- **Capesize:** 40-60m

---

### 8. Depth(m)
**Molded Depth**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 2,019
- **Format:** Decimal (meters)
- **Range:** 0 to 35+ meters
- **Example Values:** `2.3`, `7.4`, `15`, `25`

**Description:**
Vertical distance from the keel to the main deck, measured at the ship's side amidships.

**Note:**
Different from draft (depth of water needed to float the vessel).

---

### 9. GT
**Gross Tonnage**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 16,884
- **Format:** Integer
- **Range:** 0 to 250,000+
- **Example Values:** `50`, `4903`, `36278`, `107062`

**Description:**
Volumetric measure of the overall internal volume of a vessel. Used for regulatory and statistical purposes.

**Note:**
GT is NOT a measure of weight - it's a dimensionless index calculated from total enclosed volume.

**Formula:**
GT = K₁ × V
Where V = total volume of enclosed spaces (m³) and K₁ = 0.2 + 0.02 × log₁₀(V)

---

### 10. NRT
**Net Registered Tonnage**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 12,451
- **Format:** Integer
- **Range:** 0 to 150,000+
- **Example Values:** `35`, `2465`, `21173`, `64177`

**Description:**
Volumetric measure of cargo-earning capacity. Represents the volume available for cargo and passengers.

**Calculation:**
NRT = K₂ × Vc
Where Vc = cargo hold volume (m³) and K₂ = 0.2 + 0.02 × log₁₀(Vc)

**Note:**
Many records show `0` - indicates data not available or vessel type doesn't report NRT.

---

### 11. Grain
**Grain Cubic Capacity**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 4,036
- **Format:** Integer (cubic meters or cubic feet)
- **Range:** 0 to 250,000+
- **Example Values:** `0`, `6800`, `50207`, `81198`, `222146`

**Description:**
Total volumetric capacity for carrying grain cargo. Relevant primarily for bulk carriers and general cargo vessels.

**Note:**
Most non-bulk-carrier vessels show `0`. Critical specification for grain trade.

---

### 12. TPC
**Tonnes Per Centimeter Immersion**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 1,409
- **Format:** Decimal
- **Range:** 0 to 120+
- **Example Values:** `0`, `17.5`, `53.6`, `99.9`

**Description:**
Weight (in metric tons) required to change the vessel's draft by 1 centimeter at a given waterline. Used for loading calculations.

**Formula:**
TPC = (Waterplane Area × Density of Water) / 100

**Note:**
Many records show `0` - indicates data not available.

---

### 13. Dwt_Draft(m)
**Draft at Deadweight**

- **Type:** Numeric (stored as string)
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 5,761
- **Format:** Decimal (meters)
- **Range:** 0 to 25+ meters
- **Example Values:** `1.52`, `4.1`, `10.483`, `18.246`

**Description:**
Depth of the vessel in the water when loaded to maximum deadweight capacity.

**Importance:**
Determines which ports and channels the vessel can access when fully loaded.

**Typical Ranges:**
- **Small vessels:** < 5m
- **Handysize:** 8-12m
- **Panamax:** 12-15m (Panama Canal limit: 15.2m)
- **Capesize:** 16-20m
- **VLCC:** 20-25m

**Note:**
`0` values indicate data not available.

---

### 14. Source_File
**Data Source**

- **Type:** String
- **Population:** 52,034 / 52,034 (100%)
- **Unique Values:** 57 distinct source files
- **Format:** Filename (Excel workbook)
- **Example Values:** `Ship Results (61).xlsx`, `Ship Results (44).xlsx`, `Ship Results.xlsx`

**Description:**
Original Excel file from which the vessel data was extracted. Used for data lineage and troubleshooting.

**Common Sources:**
- `Ship Results.xlsx` - Base file
- `Ship Results (1).xlsx` through `Ship Results (61).xlsx` - Numbered extracts

**Note:**
Indicates data was compiled from 57+ separate Excel workbooks, likely from multiple data collection efforts.

---

## Data Quality Notes

### Completeness

| Column | Populated | Missing | Notes |
|--------|-----------|---------|-------|
| IMO | 100% | 0% | Primary key - always present |
| Vessel | 100% | 0% | Always present |
| Design | 37.4% | 62.6% | Optional field |
| Type | 77.1% | 22.9% | Missing for smaller/older vessels |
| DWT | 100% | 0% | Present but many `0` values |
| LOA | 100% | 0.05% | 26 records missing |
| Beam | 100% | 0% | Present but many `0` values |
| Depth(m) | 100% | 0% | Present but many `0` values |
| GT | 100% | 0% | Present but many `0` values |
| NRT | 100% | 0% | Present but many `0` values |
| Grain | 100% | 0% | Relevant only for bulk carriers |
| TPC | 100% | 0% | Present but many `0` values |
| Dwt_Draft(m) | 100% | 0% | Present but many `0` values |
| Source_File | 100% | 0% | Always present |

### Zero Values

Many numeric columns contain `0` values, which typically indicate:
- Data not available from source
- Not applicable for vessel type
- Measurement not taken

**Fields with significant `0` values:**
- DWT, LOA, Beam, Depth, GT, NRT, Grain, TPC, Dwt_Draft

**Recommendation:**
Treat `0` as "unknown" or "not applicable" rather than literal zero.

---

## Common Use Cases

### 1. Vessel Enrichment
**Join with Panjiva/USACE data to add vessel specifications**

```python
# Match on vessel name (fuzzy matching recommended)
import pandas as pd

ships = pd.read_csv('01_ships_register.csv', dtype=str)
panjiva = pd.read_csv('panjiva_imports.csv', dtype=str)

# Enrich with Type and DWT
enriched = panjiva.merge(
    ships[['Vessel', 'Type', 'DWT', 'Beam', 'Dwt_Draft(m)']],
    on='Vessel',
    how='left'
)
```

### 2. Vessel Type Mapping
**Map detailed Type to simplified categories**

```python
def simplify_vessel_type(vessel_type):
    if pd.isna(vessel_type) or vessel_type == '':
        return ''

    vessel_type = str(vessel_type).upper()

    if 'BULK CARRIER' in vessel_type:
        return 'Bulk Carrier'
    elif 'TANKER' in vessel_type:
        return 'Tanker'
    elif 'CONTAINER' in vessel_type:
        return 'Container'
    elif 'GENERAL CARGO' in vessel_type:
        return 'General Cargo'
    elif 'RO-RO' in vessel_type or 'PCC' in vessel_type or 'PCTC' in vessel_type:
        return 'RoRo'
    elif 'LNG' in vessel_type or 'LPG' in vessel_type:
        return 'LPG/LNG Carrier'
    else:
        return 'Other'

ships['Vessel_Type_Simple'] = ships['Type'].apply(simplify_vessel_type)
```

### 3. Size Classification
**Classify vessels by DWT**

```python
def classify_by_dwt(dwt):
    try:
        dwt_val = float(dwt)
    except:
        return 'Unknown'

    if dwt_val == 0:
        return 'Unknown'
    elif dwt_val < 10000:
        return 'Small'
    elif dwt_val < 50000:
        return 'Medium'
    elif dwt_val < 100000:
        return 'Large'
    else:
        return 'Very Large'

ships['Size_Class'] = ships['DWT'].apply(classify_by_dwt)
```

### 4. Port Compatibility Check
**Check if vessel can access port based on draft**

```python
def can_access_port(vessel_draft, port_depth):
    """Check if vessel can access port (with safety margin)"""
    safety_margin = 1.5  # meters

    try:
        draft = float(vessel_draft)
        depth = float(port_depth)
    except:
        return False

    return (draft + safety_margin) <= depth

# Example: Check Panama Canal compatibility
panama_draft_limit = 15.2  # meters
ships['Panama_Compatible'] = ships['Dwt_Draft(m)'].apply(
    lambda x: can_access_port(x, panama_draft_limit)
)
```

---

## Data Lineage

**Original Source:** 57 Excel workbooks (`Ship Results.xlsx` series)
**Consolidation Method:** Compiled into single CSV
**Last Updated:** Unknown (check file modification date)
**Maintained By:** Project team

**Update Frequency:** Unknown - likely static reference data

---

## Related Files

**In same directory (`01_DICTIONARIES/01.03_vessels/`):**
- US Flag vessel inventory files (9 Excel workbooks)
- Additional vessel reference data

**Related dictionaries:**
- `01_DICTIONARIES/01.04_carriers/` - Carrier SCAC mappings
- `01_DICTIONARIES/01.02_ports/` - Port codes and names

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| Current | 2026-01-29 | Active version (52,034 vessels) |

---

## Contact

For questions about this data dictionary or the ships register file, refer to project documentation or data steward.

---

**Document Version:** 1.0.0
**Created:** 2026-01-29
**Format:** Markdown
**Filename:** `SHIPS_REGISTER_DATA_DICTIONARY.md`
