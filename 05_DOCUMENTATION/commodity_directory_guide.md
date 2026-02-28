# Commodity Directory Guide

**Purpose**: Step-by-step instructions for creating new commodity modules in the reporting platform.

---

## When to Create a New Commodity Directory

Create a new commodity directory when you need to:
- Track supply/demand dynamics for a specific bulk commodity
- Analyze trade flows and pricing trends
- Model supply chain economics and transport costs
- Generate commodity-specific market intelligence reports

**Remember**: Commodity directories contain MARKET INTELLIGENCE. Transport analysis belongs in universal modules.

---

## Directory Structure Template

Every commodity follows this standard structure:

```
03_COMMODITY_MODULES/<commodity_name>/
├── README.md                      # Commodity overview and scope
├── config.yaml                    # Commodity-specific configuration
│
├── market_intelligence/           # Industry data and analysis
│   ├── supply_landscape.json      # Producers, capacity, locations
│   ├── demand_analysis.json       # Consumption, end-users, drivers
│   ├── trade_flows.json           # Import/export, origins/destinations
│   └── pricing_trends.json        # Market pricing, forecasts, benchmarks
│
├── supply_chain_models/           # Commodity-specific route modeling
│   ├── key_routes.json            # Common O-D pairs for this commodity
│   └── cost_scenarios.json        # Pre-computed cost estimates
│
├── reports/                       # Generated reports and publications
│   ├── templates/                 # Report templates (markdown, docx)
│   ├── drafts/                    # Work in progress
│   └── published/                 # Final versions
│
├── data_sources.json              # Commodity-specific data sources
└── naics_hts_codes.json          # Relevant NAICS/HTS codes
```

---

## Step-by-Step: Creating a New Commodity Module

### Step 1: Create Directory Structure

```bash
cd "G:/My Drive/LLM/project_master_reporting/03_COMMODITY_MODULES"

# Replace <commodity_name> with your commodity (e.g., coal, grain, steel)
commodity="<commodity_name>"

mkdir -p "$commodity"/{market_intelligence,supply_chain_models,reports/{templates,drafts,published}}
touch "$commodity"/README.md
touch "$commodity"/config.yaml
touch "$commodity"/naics_hts_codes.json
touch "$commodity"/data_sources.json
```

### Step 2: Create README.md

Template:

```markdown
# <Commodity Name> Module

## Overview

Brief description of the commodity, its uses, and market characteristics.

## Scope

What this module covers:
- Supply landscape (producers, terminals, capacity)
- Demand drivers (end-users, consumption patterns)
- Trade flows (imports, exports, domestic movements)
- Pricing dynamics (spot prices, contract structures, benchmarks)

## Key Markets

- **Primary Markets**: List major US regional markets
- **Export Markets**: If applicable, major export destinations
- **Import Sources**: If applicable, major import origins

## Data Sources

See `data_sources.json` for complete catalog.

Primary sources:
- List 3-5 key data sources

## Analysis Tools

This module uses the following universal modules:
- `barge_river` — Inland waterway freight analysis
- `rail` — Railroad freight analysis
- `ocean_vessel` — Trade flow and import tracking
- `epa_facility` — Producer/consumer facility mapping
- `geospatial` — Market area mapping and visualization

## Quick Start

```python
from report_platform.commodities import <commodity_name>
from report_platform.toolsets import barge_river, epa_facility

# Example: Find producers
producers = epa_facility.query_facilities(
    naics_codes=<commodity_name>.NAICS_CODES["producers"],
    states=["XX", "YY"]
)

# Example: Calculate transport cost
cost = barge_river.calculate_cost(
    origin="<origin>",
    destination="<destination>",
    commodity="<commodity_name>",
    tonnage=15000
)
```

## Reports

- [Market Overview](reports/published/market_overview.md)
- [Supply Chain Analysis](reports/published/supply_chain_analysis.md)

## Contact

- **Author**: Your Name
- **Last Updated**: YYYY-MM-DD
```

### Step 3: Create naics_hts_codes.json

This file contains all relevant NAICS and HTS codes for EPA facility searches and trade flow analysis.

**Template**:

```json
{
  "naics": {
    "producers": {
      "primary": ["XXXXXX"],
      "secondary": ["YYYYYY"],
      "description": "Primary production facilities"
    },
    "processors": {
      "primary": ["ZZZZZZ"],
      "description": "Processing and conversion facilities"
    },
    "distributors": {
      "primary": ["AAAAAA"],
      "description": "Wholesale distribution"
    },
    "end_users": {
      "primary": ["BBBBBB", "CCCCCC"],
      "description": "Major consumption sectors"
    }
  },
  "hts": {
    "imports": {
      "primary": ["XXXX.XX", "YYYY.YY"],
      "description": "Primary HTS codes for imports"
    },
    "exports": {
      "primary": ["ZZZZ.ZZ"],
      "description": "Primary HTS codes for exports"
    }
  },
  "stcc": {
    "rail": ["XXXXX"],
    "description": "Standard Transportation Commodity Code for rail freight"
  }
}
```

**How to Find Codes**:

**NAICS Codes** (North American Industry Classification System):
- Search: https://www.census.gov/naics/
- EPA FRS facility search: https://www.epa.gov/frs
- Example: 212100 = Coal Mining

**HTS Codes** (Harmonized Tariff Schedule):
- Search: https://hts.usitc.gov/
- For imports/exports, check Census trade data
- Example: 2523.29 = Other Portland Cement

**STCC Codes** (Standard Transportation Commodity Code):
- Used for rail freight classification
- STB website: https://www.stb.gov/

### Step 4: Create data_sources.json

This file catalogs all commodity-specific data sources.

**Template**:

```json
{
  "federal_government": {
    "source_name": {
      "agency": "Agency Name",
      "url": "https://...",
      "description": "Brief description",
      "data_types": ["production", "consumption", "prices"],
      "frequency": "monthly",
      "coverage": "national",
      "last_accessed": "2026-02-23",
      "notes": "Any special notes about access or format"
    }
  },
  "industry_associations": {
    "source_name": {
      "organization": "Organization Name",
      "url": "https://...",
      "description": "Brief description",
      "data_types": ["capacity", "shipments"],
      "frequency": "annual",
      "access": "public",
      "notes": "Subscription required"
    }
  },
  "market_intelligence": {
    "source_name": {
      "provider": "Provider Name",
      "url": "https://...",
      "description": "Brief description",
      "data_types": ["pricing", "forecasts"],
      "frequency": "daily",
      "access": "subscription",
      "cost": "$X,XXX/year",
      "notes": ""
    }
  }
}
```

**Common Data Source Categories**:
- **Federal Government**: EIA, USDA, USGS, Census Bureau, STB
- **Industry Associations**: Commodity-specific trade groups
- **Market Intelligence**: Platts, Argus, ICIS, CRU, etc.
- **Academic**: University research, USDA ERS
- **Historical**: National Archives, industry archives

### Step 5: Create config.yaml

Commodity-specific configuration settings.

**Template**:

```yaml
commodity:
  name: "<commodity_name>"
  full_name: "<Full Commodity Name>"
  category: "bulk"  # bulk, liquid_bulk, containerized

units:
  weight: "short_tons"  # short_tons, metric_tons, pounds
  volume: "cubic_yards"  # if applicable
  pricing_unit: "$/ton"

default_parameters:
  density_lb_per_cf: 80  # if applicable
  stowage_factor: 50     # cubic feet per ton (maritime)
  moisture_content: 0.05 # if applicable

transport:
  primary_modes:
    - "barge"
    - "rail"
    - "truck"
  typical_shipment_size:
    barge_tons: 15000
    rail_cars: 110
    truck_tons: 25

markets:
  primary_us_regions:
    - "Gulf Coast"
    - "Midwest"
  import_origins:
    - "Country1"
    - "Country2"
  export_destinations:
    - "Country3"
```

### Step 6: Populate market_intelligence/

Create JSON files with actual market data:

**supply_landscape.json**:
```json
{
  "producers": [
    {
      "name": "Company A",
      "location": "City, State",
      "capacity_annual_tons": 1000000,
      "naics": "XXXXXX",
      "lat": 30.0,
      "lon": -90.0,
      "status": "active",
      "notes": "Largest producer in region"
    }
  ],
  "terminals": [
    {
      "name": "Terminal Name",
      "location": "Port, State",
      "type": "import",
      "capacity_tons": 500000,
      "berths": 2
    }
  ]
}
```

**demand_analysis.json**:
```json
{
  "end_use_sectors": [
    {
      "sector": "Sector Name",
      "naics": "YYYYYY",
      "consumption_annual_tons": 5000000,
      "share_of_total": 0.35,
      "growth_rate_cagr": 0.02
    }
  ],
  "regional_consumption": [
    {
      "region": "Gulf Coast",
      "annual_tons": 3000000,
      "major_markets": ["Houston", "New Orleans"]
    }
  ]
}
```

**trade_flows.json**:
```json
{
  "imports": [
    {
      "origin_country": "Turkey",
      "destination_port": "Mobile, AL",
      "annual_tons_2024": 500000,
      "hts_code": "XXXX.XX",
      "tariff_rate": "10%",
      "major_shippers": ["Company X", "Company Y"]
    }
  ],
  "exports": [
    {
      "origin_port": "New Orleans, LA",
      "destination_country": "Brazil",
      "annual_tons_2024": 200000
    }
  ]
}
```

**pricing_trends.json**:
```json
{
  "benchmarks": [
    {
      "index_name": "Benchmark Index Name",
      "unit": "$/ton",
      "frequency": "daily",
      "source": "Platts",
      "latest_price": 150.50,
      "latest_date": "2026-02-20",
      "52_week_high": 175.00,
      "52_week_low": 135.00
    }
  ]
}
```

### Step 7: Create supply_chain_models/key_routes.json

Document common origin-destination pairs for this commodity:

```json
{
  "routes": [
    {
      "id": "route_001",
      "origin": "Production City, State",
      "destination": "Consumption City, State",
      "primary_mode": "barge",
      "typical_tonnage": 15000,
      "frequency": "weekly",
      "notes": "Major supply route"
    },
    {
      "id": "route_002",
      "origin": "Import Terminal, State",
      "destination": "Distribution Hub, State",
      "primary_mode": "rail",
      "typical_carloads": 110,
      "frequency": "monthly"
    }
  ]
}
```

### Step 8: Test Module Integration

Create a test script showing how your commodity module calls universal modules:

**FILE**: `03_COMMODITY_MODULES/<commodity>/tests/test_integration.py`

```python
"""Test commodity module integration with universal modules"""

from report_platform.toolsets import barge_river, rail, epa_facility, geospatial
import json

# Load commodity-specific codes
with open("../naics_hts_codes.json") as f:
    codes = json.load(f)

# Test 1: Find producers
producers = epa_facility.query_facilities(
    naics_codes=codes["naics"]["producers"]["primary"],
    states=["TX", "LA"],
    status="active"
)
print(f"Found {len(producers)} producers")

# Test 2: Calculate transport cost
cost = barge_river.calculate_cost(
    origin="Houston, TX",
    destination="New Orleans, LA",
    commodity="<commodity_name>",
    tonnage=15000
)
print(f"Barge cost: ${cost['total_cost']:,.0f}")

# Test 3: Create facility map
map_obj = geospatial.create_map(center=(30.0, -90.0), zoom=6)
geospatial.add_point_layer(map_obj, producers, "lat", "lon")
print("Map created successfully")
```

---

## Common Commodity Examples

### Example 1: Coal

**NAICS Codes**:
- 212100: Coal Mining
- 221112: Fossil Fuel Electric Power Generation (demand)
- 331110: Iron and Steel Mills (met coal demand)

**HTS Codes**:
- 2701.11: Anthracite coal
- 2701.12: Bituminous coal
- 2701.19: Other coal

**Key Routes**:
- Powder River Basin (WY) → Power plants (rail unit trains)
- Appalachia (WV, KY) → Export terminals (barge)

### Example 2: Grain

**NAICS Codes**:
- 111150: Corn farming
- 111140: Wheat farming
- 424510: Grain and field bean merchant wholesalers

**HTS Codes**:
- 1001: Wheat
- 1005: Corn (maize)
- 1201: Soybeans

**Key Routes**:
- Iowa → Gulf export (barge down Mississippi)
- Kansas → PNW export (rail unit train)

### Example 3: Cement

**NAICS Codes**:
- 327310: Cement manufacturing
- 327320: Ready-mix concrete manufacturing

**HTS Codes**:
- 2523.21: White Portland cement
- 2523.29: Other Portland cement
- 2618.00: Granulated slag

**Key Routes**:
- Import terminals → Distribution (barge/rail/truck)
- Cement plants → Ready-mix (truck)

---

## Best Practices

### ✅ DO:
- Use standardized directory structure
- Document all NAICS/HTS codes comprehensively
- Cite data sources with URLs and access dates
- Store market data in JSON format for programmatic access
- Call universal modules rather than duplicating code
- Include units and metadata in all data files

### ❌ DON'T:
- Hard-code data in Python scripts (use JSON/YAML config files)
- Duplicate transport analysis logic in commodity modules
- Mix different commodities in one directory
- Store raw data files without documentation
- Include proprietary data without proper licensing

---

## Checklist for New Commodity Module

Use this checklist to ensure completeness:

- [ ] Directory structure created
- [ ] README.md with commodity overview
- [ ] config.yaml with commodity-specific settings
- [ ] naics_hts_codes.json with all relevant codes
- [ ] data_sources.json documenting all sources
- [ ] market_intelligence/supply_landscape.json
- [ ] market_intelligence/demand_analysis.json
- [ ] market_intelligence/trade_flows.json
- [ ] market_intelligence/pricing_trends.json
- [ ] supply_chain_models/key_routes.json
- [ ] Test script demonstrating universal module integration
- [ ] At least one example report in reports/templates/

---

## Next Steps After Creating Module

1. **Populate with Real Data**: Replace template JSON with actual market intelligence
2. **Build Analysis Scripts**: Create Python scripts that generate insights using universal modules
3. **Generate Reports**: Use data and universal modules to create commodity-specific reports
4. **Share with Team**: Update master catalog and communicate availability

---

**Related Documentation**:
- [Module Interface Guide](module_interface_guide.md) — How to call universal modules
- [Master Catalog](master_catalog.md) — Full inventory of modules and commodities
