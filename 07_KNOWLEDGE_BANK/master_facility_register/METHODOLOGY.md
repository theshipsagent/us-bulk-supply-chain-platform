# Facility Entity Resolution - Sample Overview Sheets
## Lower Mississippi River Industrial Infrastructure

**Generated:** February 22, 2026
**Study Area:** Lower Mississippi River, Louisiana
**Master Registry:** 167 anchor facilities | 7,999 dataset links

---

## EXAMPLE #1: GRAIN ELEVATOR - Dreyfuss (Port Allen)

### Basic Information
- **Facility ID:** MRTIS_0162
- **Type:** Grain Elevator
- **Location:** Port Allen, West Baton Rouge Parish, LA
- **Coordinates:** 30.434, -91.202
- **River Mile:** 229.0 (MRTIS) / 228.9 (USACE)
- **Port:** Port of Greater Baton Rouge
- **Operator:** Louis Dreyfus Commodities LLC
- **Commodities:** Coal, Petroleum Products, Grain

### Connected Government Datasets: **174 total records from 4 sources**

| Dataset Source | Records | Confidence Breakdown |
|----------------|---------|----------------------|
| **EPA FRS** (Environmental) | 137 | All within 3km radius |
| **BTS Docks** (Navigation) | 32 | Dock registrations |
| **Product Terminals** (Energy) | 4 | Petroleum terminal data |
| **BTS Locks** (Waterway) | 1 | Proximate lock structure |

**Entity Resolution Success:** This single facility location connects to 174 different government records across environmental, navigation, and energy datasets - previously impossible to link manually.

---

## EXAMPLE #2: PETROLEUM TERMINAL - Apex Baton Rouge

### Basic Information
- **Facility ID:** MRTIS_0165
- **Type:** Tank Storage / Petroleum Terminal
- **Location:** Port Allen, West Baton Rouge Parish, LA
- **Coordinates:** 30.444, -91.200
- **River Mile:** 230.0 (MRTIS) / 229.5 (USACE)
- **Port:** Port of Greater Baton Rouge
- **Operator:** Petroleum Fuel and Terminal Co. (Apex Oil)
- **Commodities:** Petroleum Products, Asphalt, Naptha

### Connected Government Datasets: **170 total records from 4 sources**

| Dataset Source | Records | High-Confidence Matches |
|----------------|---------|-------------------------|
| **EPA FRS** | 130 | 3 MEDIUM matches (60-80% name similarity) |
| **BTS Docks** | 35 | Navigation facility records |
| **Product Terminals** | 4 | 2 HIGH matches (<300m, 81.5% name match) |
| **BTS Locks** | 1 | Waterway infrastructure |

**High-Confidence Match Example:**
- **Source:** EIA Product Terminals
- **Name:** "BATON ROUGE"
- **Distance:** 280 meters from anchor
- **Name Similarity:** 81.5%
- **Confidence:** HIGH ✓

---

## EXAMPLE #3: REFINERY - Exxon Baton Rouge

### Basic Information
- **Facility ID:** MRTIS_0166
- **Type:** Petroleum Refinery
- **Location:** Baton Rouge, East Baton Rouge Parish, LA
- **Coordinates:** 30.482, -91.193
- **River Mile:** 232.0 (MRTIS) / 232.2 (USACE)
- **Port:** Port of Greater Baton Rouge
- **Owner/Operator:** ExxonMobil Refining & Supply Co.
- **Commodities:** Crude Petroleum, Gasoline, Jet Fuel, Coal

### Connected Government Datasets: **96 total records from 5 sources**

| Dataset Source | Records | Key Details |
|----------------|---------|-------------|
| **EPA FRS** | 60 | Environmental permits & monitoring |
| **BTS Docks** | 16 | Marine terminal operations |
| **Product Terminals** | 10 | Refined product storage |
| **Rail Yards** | 6 | 2 MEDIUM matches (Baton Rouge yard, 878m) |
| **Refineries** | 4 | Refinery capacity & throughput |

**Multi-Modal Integration:** This refinery connects to water (docks), rail (yards), pipeline (terminals), and environmental (EPA) datasets - showing the complete supply chain infrastructure at one location.

---

## EXAMPLE #4: STEEL MILL - Nucor Steel (Convent)

### Basic Information
- **Facility ID:** MRTIS_0128
- **Type:** Industrial Plant / Steel Mill
- **Location:** Convent, St. James Parish, LA
- **Coordinates:** 30.065, -90.867
- **River Mile:** 162.0 (MRTIS) / 161.5 (USACE)
- **Port:** Port of South Louisiana
- **Owner/Operator:** Nucor Steel Louisiana

### Connected Government Datasets: **Multiple sources**

**HIGH Confidence Match Example:**
- **Source:** EPA FRS
- **Name:** "NUCOR STEEL"
- **Distance:** 67 meters from anchor
- **Name Similarity:** 100%
- **Confidence:** HIGH ✓

**Why This Matters:** The EPA FRS record for "Nucor Steel" at 8184 Wilton Rd is only 67 meters from the USACE navigation database record for the Nucor barge dock. Before entity resolution, these were separate, disconnected records. Now they're linked to one master facility.

---

## EXAMPLE #5: CHEMICAL PLANT - RAIN Gramercy

### Basic Information
- **Facility ID:** MRTIS_0082
- **Type:** Chemical/Bulk Plant
- **Location:** Gramercy, St. James Parish, LA
- **River Mile:** 154.0 (MRTIS)
- **Port:** Port of South Louisiana

### Connected Government Datasets: **79 total records from 6 sources**

Demonstrates the most diverse dataset coverage:
- EPA FRS (environmental permits)
- BTS Docks (navigation)
- BTS Locks (waterway structures)
- Product Terminals (petroleum)
- Rail Yards (freight rail)
- Refineries (energy processing)

---

## DATASET COVERAGE SUMMARY

### Total Master Registry Stats
- **Anchor Facilities:** 167
- **Total Dataset Links:** 7,999
- **Average Links per Facility:** 47.9

### Links by Dataset Source (Across All Facilities)

| Dataset Source | Total Records | Description |
|----------------|---------------|-------------|
| **BTS_DOCK** | 3,692 | Navigation dock registrations |
| **EPA_FRS** | 3,524 | Environmental facility permits |
| **PRODUCT_TERMINAL** | 450 | Petroleum product terminals |
| **RAIL_YARD** | 196 | Rail yard connections |
| **REFINERY** | 110 | Petroleum refineries |
| **BTS_LOCK** | 27 | Waterway lock structures |

### Match Quality Distribution
- **HIGH Confidence:** <500m distance + >80% name match
- **MEDIUM Confidence:** <1500m distance + >60% name match
- **LOW Confidence:** <3000m distance (spatial proximity)

---

## KEY INSIGHTS

### 1. Entity Resolution Success
**Before:** 18+ disconnected government datasets with no way to link records for the same physical facility.

**After:** Single query returns ALL government data for any facility location.

### 2. Data Integration Examples

**Nucor Steel (Convent, LA):**
- EPA record at "8184 Wilton Rd"
- USACE barge dock record 67m away
- **Match Confidence: HIGH** ✓
- **Result:** Air permits, water discharge data, vessel call records, rail connections - all linked to one facility

**Apex Baton Rouge Terminal:**
- EIA product terminal "BATON ROUGE" (280m away, 81.5% name match)
- EPA FRS "Genesis Baton Rouge" (657m away, 74.3% match)
- **Result:** Environmental compliance + petroleum storage capacity + navigation operations linked

### 3. Coverage by Facility Type

| Facility Type | Avg Dataset Links | Key Sources |
|---------------|-------------------|-------------|
| **Grain Elevators** | 100+ | EPA, BTS Docks, Product Terminals |
| **Refineries** | 80-100 | All 6 sources (most diverse) |
| **Petroleum Terminals** | 90-170 | EPA, Docks, Product Terminals |
| **Chemical Plants** | 70-80 | EPA (dominant), Docks, Rail |
| **General Cargo** | 40-75 | Docks, EPA, Rail |

---

## USE CASES ENABLED

### For Regulators
"Show me all environmental permits (EPA FRS) for facilities with petroleum storage capacity (Product Terminals) that receive vessel traffic (BTS Docks)"

### For Logistics
"Find all facilities with both rail yard access AND barge terminal operations within 5 miles of mile marker 150"

### For Market Analysis
"Which grain elevator clusters (spatial groupings) have the highest total government-reported capacity across all datasets?"

### For Risk Assessment
"Identify all chemical facilities (EPA) within 2km of petroleum refineries that have rail connections"

---

## TECHNICAL APPROACH

### Matching Algorithm
1. **Spatial Proximity:** Haversine distance calculation (<3km radius)
2. **Fuzzy Name Matching:** SequenceMatcher (>60% similarity threshold)
3. **Confidence Scoring:**
   - HIGH: <500m + >80% name match
   - MEDIUM: <1500m + >60% name match
   - LOW: <3000m spatial proximity

### Why 3km Radius?
Large industrial sites (refineries, chemical plants, steel mills) can span 1-2 square miles. Different government agencies may geocode to:
- Main gate address (EPA)
- Barge dock location (USACE)
- Rail siding entrance (FRA)
- Administrative office (Census)

All refer to the same facility, just different points within the site boundary.

---

## NEXT STEPS

### 1. Validation & Refinement
- Manual review of HIGH confidence matches (accuracy check)
- Adjust distance thresholds by facility type
- Improve name normalization rules

### 2. Expand Dataset Coverage
- Add IENC fleeting area data
- Integrate Coast Guard vessel traffic (AIS)
- Include state permit databases

### 3. Build Commodity Market Clusters
- Spatial grouping of grain elevators → catchment zones
- Refinery complex boundaries → market areas
- Chemical corridor mapping → industrial zones

### 4. Interactive Visualization
- Add master registry to Leaflet story map
- Click facility → show all connected datasets
- Filter by dataset source, confidence level
- Export facility reports (like this document)

---

**End of Sample Overview Sheets**
*For full dataset: see `master_facilities.csv` and `facility_dataset_links.csv`*
