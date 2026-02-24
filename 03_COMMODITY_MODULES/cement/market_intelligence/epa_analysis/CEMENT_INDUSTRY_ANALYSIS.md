# Cement Industry Analysis - EPA FRS Data

**Analysis Date:** 2026-02-07
**Data Source:** EPA ECHO FRS Database
**Total Facilities Analyzed:** 15,741

---

## Executive Summary

This analysis covers the complete cement industry supply chain in the United States, from primary manufacturing through end-use products and distribution.

### Industry Segments Analyzed

| NAICS Code | Category | Facilities | States Present |
|------------|----------|------------|----------------|
| **327310** | **Cement Manufacturing (Portland, Hydraulic)** | **437** | **50** |
| **327320** | **Ready-Mix Concrete Manufacturing** | **11,977** | **55** |
| **327331** | **Concrete Block and Brick Manufacturing** | **1,139** | **52** |
| **327332** | **Concrete Pipe Manufacturing** | **459** | **43** |
| **327390** | **Other Concrete Products (Precast, etc.)** | **1,321** | **47** |
| **423320** | **Cement/Concrete Terminals & Distributors** | **408** | **42** |

---

## Key Findings

### 1. Industry Structure
- **Ready-mix concrete** dominates with 76% of all facilities (11,977 plants)
- **Cement manufacturing** (primary production) has only 437 plants serving the entire nation
- **End-use products** (block, brick, pipe, precast) total 2,919 facilities
- **Distribution terminals** number 408, serving as bulk cement transfer points

### 2. Geographic Distribution

**Top 10 States by Total Cement Industry Facilities:**

| State | Total | Cement Mfg | Ready-Mix | Block/Brick | Precast | Terminals |
|-------|-------|------------|-----------|-------------|---------|-----------|
| **FL** | 1,403 | 24 | 1,012 | 165 | 230 | 24 |
| **CA** | 1,392 | 70 | 731 | 93 | 116 | 58 |
| **IL** | 1,205 | 11 | 1,026 | 45 | 86 | 37 |
| **TX** | 858 | 21 | 682 | 34 | 68 | 9 |
| **MO** | 795 | 22 | 622 | 34 | 13 | 6 |
| **CO** | 735 | 18 | 603 | 40 | 55 | 8 |
| **NC** | 728 | 9 | 554 | 42 | 34 | 7 |
| **KS** | 717 | 10 | 662 | 14 | 19 | 3 |
| **VA** | 664 | 6 | 539 | 52 | 53 | 34 |
| **SC** | 522 | 7 | 417 | 37 | 9 | 16 |

### 3. Market Characteristics

**Cement Manufacturing (Primary Production):**
- **437 plants** nationwide producing Portland and hydraulic cement
- High concentration in **California (70 plants)**, **Florida (24)**, **Missouri (22)**, **Tennessee (21)**, **Texas (21)**
- Capital-intensive, serving regional markets due to transportation costs
- Present in all 50 states

**Ready-Mix Concrete:**
- **11,977 plants** - the largest segment
- Highly distributed due to short shelf-life (60-90 minutes)
- **Illinois leads (1,026 plants)**, followed by **Florida (1,012)** and **California (731)**
- Serves construction sites directly with perishable product

**Block & Brick Manufacturing:**
- **1,139 facilities** producing concrete masonry units (CMU)
- **Florida leads (165 plants)**, **California (93)**, **Virginia (52)**
- Regional production serving construction markets

**Precast Concrete Products:**
- **1,321 facilities** producing structural elements, architectural panels, septic tanks, etc.
- **Florida dominates (230 plants)**, **California (116)**, **Illinois (86)**
- Includes specialized products requiring curing facilities

**Terminals & Distributors:**
- **408 facilities** handling bulk cement storage and distribution
- **California (58 terminals)**, **Illinois (37)**, **Virginia (34)**, **Ohio (33)**
- Critical infrastructure linking manufacturing to ready-mix plants

---

## Regional Analysis

### EPA Regions with Highest Cement Activity:
- **Region 4** (Southeast): Florida, Georgia, Alabama, Tennessee, North Carolina, South Carolina
- **Region 9** (Southwest): California, Arizona, Nevada
- **Region 7** (Central): Missouri, Kansas, Iowa, Nebraska
- **Region 6** (South Central): Texas, Louisiana, New Mexico
- **Region 3** (Mid-Atlantic): Virginia, Pennsylvania

---

## Supply Chain Flow

```
Cement Manufacturing (437 plants)
        ↓
Terminals/Distributors (408 facilities)
        ↓
    ┌───┴───┬─────────┬──────────┐
    ↓       ↓         ↓          ↓
Ready-Mix  Block/   Precast   Concrete
(11,977)   Brick    Products  Pipe
          (1,139)   (1,321)   (459)
```

---

## Data Files Exported

All facilities have been exported with the following data fields:
- **registry_id** - EPA unique identifier
- **fac_name** - Facility name
- **fac_street** - Street address
- **fac_city** - City
- **fac_state** - State
- **fac_zip** - ZIP code
- **fac_county** - County
- **fac_epa_region** - EPA region number
- **latitude/longitude** - Coordinates (where available)
- **naics_code** - 6-digit NAICS code

### Files Created:
1. **cement_manufacturing_plants.csv** (437 records)
2. **ready_mix_concrete_plants.csv** (11,960 records)
3. **concrete_block_brick_plants.csv** (1,137 records)
4. **precast_concrete_products.csv** (1,318 records)
5. **cement_terminals_distributors.csv** (407 records)
6. **cement_industry_all_facilities.csv** (17,670 records - master file)

---

## Industry Insights

### Market Concentration
- **Ready-mix** is highly fragmented with many local operators
- **Cement manufacturing** shows regional concentration (few large plants per state)
- **Florida and California** are dominant markets across all segments

### Geographic Patterns
- **Sunbelt states** (FL, TX, CA, AZ) show high activity due to population growth
- **Midwest states** (IL, MO, KS) have extensive ready-mix networks
- **Coastal states** show higher terminal density for import/export operations

### Infrastructure Implications
- 437 cement plants support nearly 12,000 ready-mix operations (1:27 ratio)
- 408 terminals indicate significant bulk cement distribution infrastructure
- End-use product facilities (2,919 total) represent value-added manufacturing

---

## Bulk Cement End Users Summary

**Direct Consumers of Bulk Cement:**
1. **Ready-Mix Concrete Plants** (11,977) - Largest consumer
2. **Block & Brick Manufacturers** (1,139) - CMU production
3. **Precast Product Manufacturers** (1,321) - Structural elements
4. **Concrete Pipe Manufacturers** (459) - Infrastructure products
5. **Terminals/Distributors** (408) - Storage and redistribution

**Total Bulk Cement Consumption Points:** ~15,300+ facilities

---

## Data Quality Notes

- Some facilities may have incomplete address data
- Latitude/longitude coordinates available for most facilities
- NAICS codes from EPA program linkages (facilities may have multiple codes)
- Data current as of EPA ECHO download date

---

## Recommended Next Steps

1. **Geographic Analysis** - Map facility density by market
2. **Market Size Analysis** - Estimate consumption by state/region
3. **Competitive Analysis** - Identify major operators by region
4. **Logistics Optimization** - Analyze terminal coverage vs demand
5. **Regulatory Compliance** - Cross-reference with EPA program data (NPDES, RCRA, etc.)

---

## Query Examples

To explore this data further using the EPA FRS Analytics Tool:

```bash
# All cement manufacturing in California
python cli.py query facilities --naics 327310 --state CA

# Ready-mix plants in Florida
python cli.py query facilities --naics 327320 --state FL

# Terminals in Virginia
python cli.py query facilities --naics 423320 --state VA

# Precast manufacturers nationwide
python cli.py query facilities --naics 327390

# Get EPA program linkages for a facility
python cli.py query programs <REGISTRY_ID>
```

---

## Data Source

**EPA Enforcement and Compliance History Online (ECHO)**
FRS Facilities and Linkages Database
Downloaded: 2026-02-07
https://echo.epa.gov/tools/data-downloads

---

*Analysis prepared using EPA FRS Analytics Tool*
