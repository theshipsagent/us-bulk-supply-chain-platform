# Master Facility Register (MFR) - Concept Design
**Created**: 2026-02-23
**Purpose**: Unified facility intelligence layer integrating fragmented data sources

---

## THE PROBLEM

A single industrial facility (e.g., ArcelorMittal Burns Harbor steel mill) appears in **10+ different databases** with:
- Different names ("ArcelorMittal Burns Harbor", "ARCELORMITTAL BURNS HARBOR LLC", "Burns Harbor Works")
- Different identifiers (EPA FRS ID, Rail SCRS code, Port UNLOC, BLS establishment ID)
- Different coordinates (facility centroid, rail yard, dock, stack emissions point)
- Different levels of detail (EPA has 50+ attributes, rail has 5)

**Current State**: Each data source exists in isolation. No master key links them.

**Consequence**:
- To analyze one steel mill, you must manually search 10 databases
- Name fuzzy matching is unreliable ("U.S. Steel Gary Works" vs "United States Steel Corporation Gary Plant")
- Can't answer: "Show me ALL data for this facility across ALL sources"

---

## THE SOLUTION: Master Facility Register (MFR)

### Concept

A **Master Facility Register** is a:
1. **Canonical Facility Inventory** - One authoritative list of every major industrial facility in the US
2. **Cross-Database Linking Table** - Maps facility master ID → EPA FRS ID, Rail code, Port code, etc.
3. **Geospatial Fusion Layer** - Consolidates multiple coordinate systems into one master boundary
4. **Attribute Aggregation Engine** - Collects all known data about each facility into one unified profile

### Architecture

```
07_KNOWLEDGE_BANK/master_facility_register/
│
├── facility_master.duckdb           ← Master database (core table: facilities)
│
├── src/
│   ├── entity_resolution.py         ← Name harmonization engine
│   ├── geospatial_fusion.py         ← Coordinate consolidation
│   ├── cross_reference_builder.py   ← Build ID linkage tables
│   ├── attribute_enrichment.py      ← Aggregate attributes from all sources
│   └── facility_profile_generator.py ← Generate unified facility cards
│
├── crosswalks/                      ← ID mapping tables
│   ├── epa_frs_to_master.csv        ← EPA FRS ID → MFR Master ID
│   ├── rail_scrs_to_master.csv      ← Rail SCRS code → MFR Master ID
│   ├── port_unloc_to_master.csv     ← Port UNLOC → MFR Master ID
│   ├── panjiva_consignee_to_master.csv ← Import consignee → MFR Master ID
│   ├── eia_generator_to_master.csv  ← Power plant ID → MFR Master ID
│   └── bls_establishment_to_master.csv ← BLS establishment → MFR Master ID
│
├── geometries/                      ← Facility boundary polygons
│   ├── facility_boundaries.geojson  ← Property boundaries (from county parcels)
│   ├── rail_infrastructure.geojson  ← Rail spurs, yards, loading docks
│   ├── waterfront_infrastructure.geojson ← Docks, berths, material handling
│   └── emission_points.geojson      ← EPA stack locations, outfall pipes
│
├── profiles/                        ← Generated facility intelligence cards
│   └── [facility_master_id].json    ← One file per facility (all data consolidated)
│
└── METHODOLOGY.md
```

---

## DATA SCHEMA

### Core Table: `facilities` (Master Facility Register)

```sql
CREATE TABLE facilities (
    -- Master identifiers
    facility_master_id VARCHAR PRIMARY KEY,  -- e.g., "MFR_00012345"
    canonical_name VARCHAR NOT NULL,         -- "ArcelorMittal Burns Harbor"
    facility_type VARCHAR,                   -- "steel_mill", "cement_plant", "power_plant"
    naics_primary INT,                       -- Primary NAICS code

    -- Location (master coordinates - weighted centroid of all sub-facilities)
    latitude DOUBLE,
    longitude DOUBLE,
    state VARCHAR(2),
    county VARCHAR,
    city VARCHAR,
    zip_code VARCHAR(10),

    -- Geospatial
    boundary_geom GEOMETRY,                  -- Facility property boundary polygon

    -- Operational status
    status VARCHAR,                          -- "active", "idle", "closed", "under_construction"
    first_observed_date DATE,                -- Earliest date in any data source
    closure_date DATE,                       -- If closed

    -- Capacity & Scale
    annual_capacity_tons DOUBLE,             -- Production capacity (if applicable)
    employment_count INT,                    -- From BLS or company reports
    land_area_acres DOUBLE,                  -- From county parcel data

    -- Ownership
    parent_company_id VARCHAR,               -- Link to company_master in Knowledge Bank
    operator_company_id VARCHAR,             -- May differ from owner

    -- Data provenance
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    data_quality_score DOUBLE                -- Confidence in entity resolution (0-1)
);
```

### Cross-Reference Table: `facility_external_ids`

```sql
CREATE TABLE facility_external_ids (
    facility_master_id VARCHAR REFERENCES facilities(facility_master_id),
    source_system VARCHAR,                   -- "epa_frs", "rail_scrs", "port_unloc", "panjiva"
    external_id VARCHAR,                     -- ID from source system
    external_name VARCHAR,                   -- Name as it appears in source system
    match_confidence DOUBLE,                 -- How confident is this link? (0-1)
    verified_by VARCHAR,                     -- "automated" or "manual_review"
    PRIMARY KEY (facility_master_id, source_system, external_id)
);
```

**Example rows:**
```
facility_master_id | source_system | external_id       | external_name                      | match_confidence
-------------------|---------------|-------------------|------------------------------------|-----------------
MFR_00012345       | epa_frs       | FIN000004359      | ARCELORMITTAL BURNS HARBOR         | 0.98
MFR_00012345       | rail_scrs     | 045802            | Burns Harbor Works                 | 0.95
MFR_00012345       | usace_port    | USBUR             | Port of Indiana-Burns Harbor       | 0.92
MFR_00012345       | panjiva       | (fuzzy)           | ARCELORMITTAL BURNS HARBOR LLC     | 0.87
MFR_00012345       | eia           | 50000             | Burns Harbor Energy Center         | 1.00 (verified)
```

### Attribute Table: `facility_attributes`

```sql
CREATE TABLE facility_attributes (
    facility_master_id VARCHAR REFERENCES facilities(facility_master_id),
    attribute_category VARCHAR,              -- "environmental", "rail", "port", "employment"
    attribute_key VARCHAR,                   -- "air_permit_number", "rail_connections", "berth_count"
    attribute_value VARCHAR,                 -- The actual value
    source_system VARCHAR,                   -- Where this data came from
    as_of_date DATE,                         -- When this was true
    PRIMARY KEY (facility_master_id, attribute_category, attribute_key, source_system)
);
```

**Example rows:**
```
facility_master_id | attribute_category | attribute_key          | attribute_value        | source_system | as_of_date
-------------------|--------------------|-----------------------|------------------------|---------------|------------
MFR_00012345       | environmental      | air_permit_number     | IN0000451              | epa_frs       | 2025-01-15
MFR_00012345       | rail               | rail_connections      | CN, CSX, NS            | rail_scrs     | 2024-06-01
MFR_00012345       | rail               | car_storage_capacity  | 1200                   | rail_scrs     | 2024-06-01
MFR_00012345       | port               | berth_count           | 3                      | usace         | 2023-12-01
MFR_00012345       | port               | max_vessel_loa_ft     | 1000                   | usace         | 2023-12-01
MFR_00012345       | employment         | employees             | 3800                   | bls           | 2024-03-01
MFR_00012345       | production         | annual_steel_tons     | 5000000                | company       | 2024-01-01
```

---

## DATA SOURCES TO INTEGRATE

### 1. **EPA Facility Registry Service (FRS)**
- **What it provides**: Environmental compliance, permits, inspections
- **Key identifier**: `REGISTRY_ID` (e.g., FIN000004359)
- **Attributes**: Air/water permits, NAICS, lat/lon, facility name, parent company
- **Challenges**: Name variations, multiple entries per site (different permit types)

### 2. **Rail: SCRS (Standard Carrier Railroad Stations)**
- **What it provides**: Rail connections, spur locations, car capacity
- **Key identifier**: SCRS code (5-6 digit numeric)
- **Attributes**: Serving railroads, yard capacity, lat/lon
- **Challenges**: Not all facilities have SCRS codes; coordinates may be rail yard, not facility centroid

### 3. **USACE Waterborne Commerce / Port Directories**
- **What it provides**: Vessel calls, tonnage, berth specs
- **Key identifier**: UNLOC code (5-character alpha) or port name
- **Attributes**: Berth depth, LOA limits, throughput statistics
- **Challenges**: Port-level data (not facility-specific); multiple facilities per port

### 4. **Panjiva / S&P Global Import Manifests**
- **What it provides**: Import volumes, origins, commodity descriptions
- **Key identifier**: Consignee name (free text, highly variable)
- **Attributes**: HTS codes, shipper, vessel, tonnage, arrival date
- **Challenges**: No structured ID; heavy name fuzzy matching required

### 5. **EIA Electric Generator Inventory (EIA-860)**
- **What it provides**: Power plant capacity, fuel type, ownership
- **Key identifier**: Plant Code (numeric, 4-6 digits)
- **Attributes**: Generator capacity (MW), fuel type, prime mover, lat/lon
- **Challenges**: Only covers power generation facilities; some industrials have on-site cogeneration

### 6. **BLS Quarterly Census of Employment & Wages (QCEW)**
- **What it provides**: Employment counts, wage data
- **Key identifier**: Establishment ID (long alphanumeric)
- **Attributes**: NAICS, employment count, total wages
- **Challenges**: Confidentiality suppression for small establishments; not publicly geocoded

### 7. **State Environmental Permits**
- **What it provides**: State-level air/water/waste permits
- **Key identifier**: State-specific permit numbers
- **Attributes**: Permit type, issue/expiration dates, compliance status
- **Challenges**: 50 different state systems; no standardization

### 8. **County Tax Assessor / Parcel Data**
- **What it provides**: Property boundaries, land area, ownership
- **Key identifier**: Assessor Parcel Number (APN)
- **Attributes**: Parcel polygon, acreage, assessed value, owner of record
- **Challenges**: County-by-county data; must geocode and match to facilities

### 9. **DOT National Transportation Atlas Database (NTAD)**
- **What it provides**: Rail network, intermodal terminals, ports
- **Key identifier**: Feature ID (varies by layer)
- **Attributes**: Lat/lon, network topology
- **Challenges**: Network-level data; not always facility-specific

### 10. **Company-Reported Data**
- **What it provides**: Capacity, production, strategic plans
- **Key identifier**: Company name + site name
- **Attributes**: Annual capacity, recent capex, closure announcements
- **Challenges**: Unstructured (earnings calls, press releases); must extract and verify

---

## ENTITY RESOLUTION WORKFLOW

### Step 1: Seed from Authoritative Source (EPA FRS)

EPA FRS is the most comprehensive starting point:
- 4M+ facilities nationwide
- Structured NAICS codes
- Standardized lat/lon
- Parent company linkages

**Process:**
1. Load all EPA FRS facilities for target NAICS codes (e.g., 327310 Cement, 331110 Steel)
2. Create initial `facility_master_id` for each FRS entry
3. Set `canonical_name` = EPA FRS facility name (clean and Title Case)

### Step 2: Fuzzy Match to Rail Data

For each FRS facility:
1. Buffer 1 mile around FRS lat/lon
2. Find all Rail SCRS stations within buffer
3. Fuzzy match FRS facility name to SCRS station name (using RapidFuzz)
4. If match confidence > 0.85, link SCRS code to facility_master_id
5. If multiple SCRS matches, take closest geographically

### Step 3: Fuzzy Match to Panjiva Consignees

For each FRS facility:
1. Extract all Panjiva consignee names containing city/county/state of FRS facility
2. Fuzzy match FRS facility name + parent company name to consignee name
3. If match confidence > 0.80, link consignee name to facility_master_id
4. Review low-confidence matches (0.70-0.80) manually

### Step 4: Link to EIA Power Plants (if applicable)

For NAICS codes with power generation (221112, some industrials):
1. Buffer 0.5 miles around FRS lat/lon
2. Find all EIA plant codes within buffer
3. If plant name matches FRS facility name (or parent company), link
4. Store EIA Plant Code in `facility_external_ids`

### Step 5: Enrich with County Parcel Boundaries

For each facility lat/lon:
1. Reverse geocode to county
2. Load county parcel shapefile
3. Perform point-in-polygon to find parcel containing facility
4. Extract parcel boundary polygon → store as `boundary_geom`
5. Calculate land area → store as `land_area_acres`

### Step 6: Manual Review & Quality Control

1. Flag facilities with:
   - Low match confidence (<0.85)
   - Conflicting data (e.g., FRS says "active", EIA says "retired")
   - Missing critical attributes (no NAICS, no lat/lon)
2. Manual research to verify/correct
3. Update `data_quality_score` (0.0 = unreliable, 1.0 = verified)

---

## USE CASES

### Use Case 1: "Show me everything about ArcelorMittal Burns Harbor"

**Query:**
```python
from report_platform.knowledge_bank import get_facility_profile

profile = get_facility_profile(
    facility_name="ArcelorMittal Burns Harbor",
    state="IN"
)
```

**Returns:**
```json
{
  "facility_master_id": "MFR_00012345",
  "canonical_name": "ArcelorMittal Burns Harbor",
  "facility_type": "steel_mill",
  "naics_primary": 331110,
  "location": {
    "latitude": 41.6289,
    "longitude": -87.1347,
    "city": "Portage",
    "county": "Porter County",
    "state": "IN",
    "boundary_acres": 850
  },
  "operational_status": "active",
  "capacity": {
    "annual_steel_production_tons": 5000000,
    "employment": 3800
  },
  "ownership": {
    "parent_company": "ArcelorMittal S.A. (Luxembourg)",
    "operator": "ArcelorMittal USA LLC"
  },
  "external_ids": {
    "epa_frs": "FIN000004359",
    "rail_scrs": "045802",
    "port_unloc": "USBUR",
    "eia_plant": "50000"
  },
  "infrastructure": {
    "rail": {
      "serving_railroads": ["Canadian National", "CSX", "Norfolk Southern"],
      "car_storage_capacity": 1200,
      "spurs": 12
    },
    "port": {
      "berth_count": 3,
      "max_vessel_loa_ft": 1000,
      "annual_tonnage_handled": 8500000,
      "commodities": ["iron_ore", "coal", "limestone", "steel_products"]
    },
    "power": {
      "on_site_generation_mw": 450,
      "fuel_type": "natural_gas_cogeneration"
    }
  },
  "environmental": {
    "air_permit": "IN0000451",
    "water_permit": "IN0026174",
    "major_source": true,
    "recent_violations": []
  },
  "trade": {
    "imports_2024": {
      "iron_ore_tons": 2400000,
      "top_origins": ["Canada", "Brazil", "Sweden"]
    },
    "exports_2024": {
      "steel_products_tons": 850000,
      "top_destinations": ["Canada", "Mexico"]
    }
  },
  "data_quality_score": 0.96,
  "last_updated": "2026-02-15"
}
```

### Use Case 2: "Find all steel mills within 100 miles of Chicago with rail access"

**Query:**
```python
from report_platform.knowledge_bank import search_facilities

results = search_facilities(
    facility_type="steel_mill",
    naics_codes=[331110, 331210],
    near_city="Chicago, IL",
    radius_miles=100,
    filters={"has_rail": True}
)
```

**Returns:** List of facilities matching criteria, ranked by distance.

### Use Case 3: "Map all slag sources for SESCO Houston terminal import strategy"

**Query:**
```python
from report_platform.knowledge_bank import search_facilities

slag_sources = search_facilities(
    naics_codes=[331110],  # Steel mills (GGBFS source)
    status="active",
    filters={"has_port_access": True}  # Can ship via vessel
)

# Returns all integrated steel mills (blast furnace) with port access
# for import of GGBFS to Houston
```

---

## IMPLEMENTATION PLAN

### Phase 1: Proof of Concept (Cement/Steel Only)

1. Build DuckDB schema (`facility_master.duckdb`)
2. Load EPA FRS data for NAICS 327310 (cement) and 331110 (steel)
3. Link to Rail SCRS data (fuzzy match within 1-mile buffer)
4. Link to Panjiva consignees (fuzzy match by name + location)
5. Generate 50 facility profiles manually to validate

### Phase 2: Automated Entity Resolution Pipeline

1. Build automated fuzzy matching pipeline (`src/entity_resolution.py`)
2. Implement geospatial fusion (consolidate multiple coordinates)
3. Build cross-reference tables for all data sources
4. Run full pipeline for all NAICS codes in scope
5. Quality control: manual review of low-confidence matches

### Phase 3: API & Integration

1. Build facility profile generator (`src/facility_profile_generator.py`)
2. Expose Knowledge Bank API for commodity modules to query
3. Integrate with CLI: `report-platform facility-search --name "Burns Harbor"`
4. Generate facility intelligence cards (JSON + HTML)

### Phase 4: Continuous Maintenance

1. Build data refresh scheduler (quarterly EPA FRS updates)
2. Monitor for new facilities (construction permits, news)
3. Track closures (retirement announcements, EPA deactivations)
4. Update ownership changes (M&A tracker feeds company linkages)

---

## EXAMPLE: Facility Intelligence Card (HTML Output)

```html
<!DOCTYPE html>
<html>
<head>
    <title>ArcelorMittal Burns Harbor - Facility Intelligence Card</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: auto; }
        .header { background: #1a365d; color: white; padding: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .map { height: 400px; width: 100%; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ArcelorMittal Burns Harbor</h1>
        <p>Integrated Steel Mill | Portage, Indiana | NAICS 331110</p>
    </div>

    <div class="section">
        <h2>Location & Boundaries</h2>
        <div id="map" class="map"></div>
        <!-- Folium map showing facility boundary, rail spurs, dock locations -->
    </div>

    <div class="section">
        <h2>Operational Profile</h2>
        <table>
            <tr><th>Annual Capacity</th><td>5,000,000 tons steel</td></tr>
            <tr><th>Employment</th><td>3,800 workers</td></tr>
            <tr><th>Land Area</th><td>850 acres</td></tr>
            <tr><th>Status</th><td>Active</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Infrastructure</h2>
        <h3>Rail</h3>
        <ul>
            <li>Served by CN, CSX, Norfolk Southern</li>
            <li>12 rail spurs, 1,200 car storage capacity</li>
        </ul>
        <h3>Port</h3>
        <ul>
            <li>3 berths, max vessel LOA 1,000 ft</li>
            <li>8.5M tons annual throughput (iron ore, coal, limestone inbound; steel products outbound)</li>
        </ul>
    </div>

    <div class="section">
        <h2>Data Sources</h2>
        <ul>
            <li><strong>EPA FRS</strong>: FIN000004359</li>
            <li><strong>Rail SCRS</strong>: 045802</li>
            <li><strong>Port UNLOC</strong>: USBUR</li>
            <li><strong>EIA Plant</strong>: 50000</li>
            <li><strong>Panjiva</strong>: Import consignee records (2020-2025)</li>
        </ul>
    </div>

    <div class="section">
        <h2>Environmental & Compliance</h2>
        <ul>
            <li>Air Permit: IN0000451 (Major Source)</li>
            <li>Water Permit: IN0026174</li>
            <li>No recent violations (last 24 months)</li>
        </ul>
    </div>

    <footer style="text-align: center; padding: 20px; color: #666;">
        <p>Generated by Master Facility Register | Data as of 2026-02-15 | Quality Score: 0.96</p>
    </footer>
</body>
</html>
```

---

## BENEFITS

### For Commodity Modules:
- **One-stop shop**: Query one system to get all data about a facility
- **No duplicate work**: Entity resolution done once, reused everywhere
- **Higher accuracy**: Manual QC ensures high-confidence facility matches

### For Supply Chain Analysis:
- **Complete infrastructure picture**: Rail + port + road access in one view
- **Competitive intelligence**: See ALL facilities for a parent company
- **Geospatial analysis**: Buffer analysis, proximity queries, catchment areas

### For Client Reports:
- **Rich facility profiles**: Generate detailed facility intelligence cards
- **Interactive maps**: Folium maps showing all infrastructure layers
- **Traceability**: Every data point linked back to authoritative source

---

## NEXT STEPS

1. **Review & Refine** this concept with William
2. **Prioritize data sources** (start with EPA FRS + Rail + Panjiva?)
3. **Build proof-of-concept** for 50 cement/steel facilities
4. **Validate** entity resolution accuracy
5. **Scale** to full NAICS scope if POC succeeds

---

**Author**: Claude Sonnet 4.5
**For**: William Davis, OceanDatum.ai
**Project**: US Bulk Supply Chain Reporting Platform
