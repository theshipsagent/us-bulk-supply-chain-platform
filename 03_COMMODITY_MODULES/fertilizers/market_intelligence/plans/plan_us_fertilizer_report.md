# US FERTILIZERS MARKET REPORT - PROJECT PLAN

**Report Type:** Comprehensive Market Intelligence Package
**Geographic Focus:** United States (National + Regional Deep-Dives)
**Primary Commodities:** Nitrogen (Ammonia, Urea, UAN), Phosphate, Potash
**Delivery Format:** HTML Report Suite + Interactive GeoJSON Maps + ArcGIS StoryMaps
**Visual Style:** Noir aesthetic matching theshipsagent.com branding

---

## I. PROJECT SCOPE & OBJECTIVES

### Primary Objectives
1. **Map the complete US fertilizer supply chain** - from production facilities to import terminals to distribution networks
2. **Identify major market participants** and their competitive positioning
3. **Analyze import/export flows** by commodity type, port, and origin country
4. **Visualize transportation infrastructure** critical to fertilizer logistics (Mississippi River system, Class I rail, marine highways, key ports)
5. **Provide actionable market intelligence** for fertilizer traders, importers, distributors, and infrastructure investors

### Geographic Coverage
- **National Overview:** All 50 states production and consumption patterns
- **Regional Deep-Dives:**
  - Gulf Coast (Houston, New Orleans, Tampa, Mobile) - Primary import gateway
  - Mississippi River Corridor - Barge transportation network
  - Pacific Northwest (Portland, Longview) - Potash imports from Canada
  - Great Lakes (Toledo, Chicago) - Canadian imports via lake shipping
  - East Coast (Savannah, Charleston, Norfolk) - Atlantic import terminals

### Commodity Coverage
- **Nitrogen Fertilizers:**
  - Anhydrous Ammonia (NH3)
  - Urea (46-0-0)
  - UAN Solutions (28-0-0, 32-0-0)
  - Ammonium Nitrate
  - Ammonium Sulfate
- **Phosphate Fertilizers:**
  - DAP (18-46-0)
  - MAP (11-52-0)
  - TSP (0-46-0)
  - Phosphoric Acid
- **Potash:**
  - MOP (Muriate of Potash, 0-0-60)
  - SOP (Sulfate of Potash, 0-0-50)

---

## II. DATA SOURCES TO GATHER

### Government & Statistical Sources

#### USDA Economic Research Service (ERS)
- **URL:** https://www.ers.usda.gov/topics/farm-economy/fertilizer-use-and-price/
- **Data Needed:**
  - National fertilizer consumption by nutrient (N, P, K)
  - State-level fertilizer use statistics
  - Fertilizer price indices by commodity
  - Farm input cost trends
- **Format:** Excel downloads, CSV, API access via USDA QuickStats

#### USGS Mineral Commodity Summaries
- **URL:** https://www.usgs.gov/centers/national-minerals-information-center/fertilizer-statistics-and-information
- **Data Needed:**
  - US production capacity by facility
  - Import/export volumes by commodity
  - Domestic consumption estimates
  - Global production context
- **Format:** Annual PDF reports + Excel data tables

#### US Census Bureau - USA Trade Online
- **URL:** https://usatrade.census.gov/
- **Data Needed:**
  - HTS Codes: 3102 (Mineral/chemical fertilizers, nitrogenous), 3103 (phosphatic), 3104 (potassic), 3105 (mixed)
  - Monthly import/export data by port, country, commodity
  - Value and volume statistics
- **Format:** Excel downloads, query-based system

#### USACE (US Army Corps of Engineers)
- **URL:** https://www.iwr.usace.army.mil/NDC/
- **Navigation Data Center:** Waterborne commerce statistics
- **Data Needed:**
  - Lock performance data (fertilizer tonnages through Mississippi River locks)
  - Inland waterway fertilizer movements
  - Port commodity statistics
- **Format:** Excel, PDF reports

#### USDA GIPSA (Grain Inspection)
- **URL:** https://www.ams.usda.gov/services/fgis
- **Data Needed:**
  - Export inspection data (shows grain export volumes correlated with fertilizer demand)
  - Terminal dwell time data
- **Format:** Weekly CSV reports, API access

### Commercial Trade Intelligence

#### Panjiva / S&P Global Market Intelligence
- **Data Type:** Bill of lading manifests for ocean shipments
- **Coverage Period:** 2023-2025 (minimum 36 months)
- **Key Fields:**
  - Consignee (importer)
  - Shipper (exporter)
  - Port of unlading
  - Commodity description
  - Weight (metric tons)
  - Country of origin
- **Search Terms:**
  - Fertilizer, Urea, Ammonia, Phosphate, Potash, DAP, MAP, UAN
  - HTS Codes: 3102, 3103, 3104, 3105
- **Output:** Aggregated Excel with ~15,000-25,000 records expected

#### Clarksons Shipping Intelligence
- **URL:** https://sin.clarksons.net/
- **Data Needed:**
  - Dry bulk freight rates (Handysize, Supramax, Panamax for fertilizer routes)
  - Fertilizer trade flow routes
  - Shipping time estimates
- **Key Routes:**
  - Middle East → US Gulf (Ammonia, Urea)
  - Russia/Baltic → US East Coast (Urea, Potash)
  - Canada → US (Rail and lake shipping)
  - Morocco → US Gulf (Phosphate rock)

#### IHS Markit / Fertilizer Week
- **Data Type:** Fertilizer market pricing and analysis
- **Data Needed:**
  - Weekly spot prices by commodity and location
  - Production capacity database
  - Trade flow statistics
- **Format:** Subscription reports, Excel data

### Industry & Company Sources

#### The Fertilizer Institute (TFI)
- **URL:** https://www.tfi.org/
- **Data Needed:**
  - Production statistics
  - Industry member directory
  - Safety and regulatory information

#### Major Producer Websites & Annual Reports
- **CF Industries** - Largest US nitrogen producer (Port Neal, Donaldsonville, Yazoo City)
- **Mosaic** - Phosphate and potash (Florida phosphate mines, Carlsbad NM potash)
- **Nutrien** - Potash and nitrogen (Canadian operations serving US)
- **Koch Fertilizer** - Nitrogen terminals and production
- **Yara** - International nitrogen supplier
- **OCP Group (Morocco)** - Phosphate rock imports

### Geospatial Data Sources

#### Global Energy Monitor - Fertilizer Plants Database
- **URL:** https://globalenergymonitor.org/
- **Data Needed:**
  - Fertilizer plant locations (lat/lon)
  - Capacity by commodity
  - Ownership
  - Operating status
- **Format:** Excel download, convert to GeoJSON

#### BTS National Transportation Atlas Database (NTAD)
- **URL:** https://geodata.bts.gov/
- **Layers Needed:**
  - Class I Railroad Network (shapefile)
  - Navigable Waterways (shapefile)
  - Ports (point layer)
  - Intermodal facilities
- **Format:** Shapefiles, convert to GeoJSON

#### USDA NASS CropScape
- **URL:** https://nassgeodata.gmu.edu/CropScape/
- **Data Needed:**
  - Cropland layer (shows fertilizer demand zones)
  - State agricultural statistics
- **Format:** Raster/vector, can create fertilizer demand heatmap

---

## III. GEOSPATIAL DELIVERABLES

### Map 1: US Fertilizer Production Facilities
**File:** `us_fertilizer_plants.geojson`

**Features to Include:**
- All nitrogen production plants (ammonia, urea, UAN)
- Phosphate mines and processing plants (Florida, North Carolina, Idaho)
- Potash mines (New Mexico, Utah)
- Major blending/formulation facilities

**Attributes:**
```json
{
  "plant_name": "CF Industries Donaldsonville",
  "owner": "CF Industries",
  "location": "Donaldsonville, LA",
  "state": "Louisiana",
  "latitude": 30.1,
  "longitude": -90.9,
  "commodity_type": "Nitrogen",
  "products": ["Ammonia", "Urea", "UAN"],
  "capacity_mt_year": 3200000,
  "status": "Operating",
  "employees": 450,
  "rail_served": true,
  "barge_served": true,
  "pipeline_connection": true
}
```

**Styling:**
- Color by commodity type:
  - Nitrogen: Blue (#1976D2)
  - Phosphate: Orange (#FF9800)
  - Potash: Purple (#9C27B0)
  - Multi-nutrient: Green (#4CAF50)
- Size by capacity (larger circles = higher capacity)

---

### Map 2: Fertilizer Import Ports (Weighted by Volume)
**File:** `us_fertilizer_import_ports.geojson`

**Features to Include:**
- Top 25 ports by fertilizer import tonnage
- Bubble size proportional to annual volume
- Breakdown by commodity type

**Attributes:**
```json
{
  "port_name": "Houston, TX",
  "total_import_mt": 5717149,
  "nitrogen_mt": 3200000,
  "phosphate_mt": 1800000,
  "potash_mt": 717149,
  "shipments_count": 342,
  "top_origins": ["Trinidad", "Russia", "Canada", "Morocco"],
  "primary_commodities": ["Ammonia", "Urea", "DAP"],
  "latitude": 29.72,
  "longitude": -95.05
}
```

**Styling:**
- Red bubbles (#E53935), size by total volume
- Popup shows commodity breakdown chart
- Highlight top 5 ports

---

### Map 3: Mississippi River Fertilizer Transportation Network
**File:** `mississippi_river_fertilizer_system.geojson`

**Features to Include:**
- Mississippi River mainline (Cairo IL to New Orleans)
- Major tributaries (Ohio River, Illinois River, Arkansas River, Tennessee River)
- USACE locks with fertilizer tonnage data
- River terminals handling fertilizer

**Attributes for Locks:**
```json
{
  "lock_name": "Lock & Dam 27",
  "river_mile": 185.5,
  "location": "Granite City, IL",
  "fertilizer_tons_2024": 1250000,
  "commodity_breakdown": {
    "nitrogen": 750000,
    "phosphate": 350000,
    "potash": 150000
  },
  "lockages_per_year": 1247,
  "avg_delay_hours": 2.3,
  "infrastructure_condition": "Fair - Rehabilitation planned 2026"
}
```

**Styling:**
- River lines: Blue gradient by tonnage
- Locks: Yellow/Orange markers sized by volume
- Terminals: Green squares

---

### Map 4: Class I Railroad Fertilizer Routes
**File:** `class1_rail_fertilizer_routes.geojson`

**Features to Include:**
- Major rail lines serving fertilizer facilities
- Intermodal transfer points
- Rail-to-barge terminals
- Rail-to-truck transload facilities

**Key Rail Corridors:**
- BNSF: Potash from Canada (Saskatchewan) to Gulf ports
- CN/CP: Canadian imports to Midwest
- UP/BNSF: Fertilizer distribution throughout Corn Belt
- CSX/NS: East Coast import distribution

**Styling:**
- Brown lines (#795548)
- Highlight high-volume fertilizer corridors (thicker lines)

---

### Map 5: US Agricultural Fertilizer Demand Zones
**File:** `us_fertilizer_demand_heatmap.geojson`

**Features to Include:**
- County-level fertilizer consumption estimates
- Crop type distribution (corn, soybeans, wheat, cotton)
- Chloropleth map showing fertilizer intensity

**Data Calculation:**
- Use USDA NASS crop acreage data
- Apply standard application rates per crop
- Calculate total nutrient demand (N, P, K) by county

**Styling:**
- Green gradient (light = low, dark = high)
- Corn Belt should be darkest (Iowa, Illinois, Indiana, eastern Nebraska)

---

### Map 6: Global Fertilizer Trade Flows to US
**File:** `global_fertilizer_trade_flows.geojson`

**Features to Include:**
- Arc lines from major supplier countries to US ports
- Line thickness proportional to tonnage
- Color by commodity type

**Major Trade Routes:**
- Trinidad & Tobago → US Gulf (Ammonia)
- Russia/Baltic → US East Coast (Urea, Potash)
- Canada → US (Potash, Ammonia via rail and ship)
- Morocco → US Gulf (Phosphate rock)
- Middle East → US Gulf (Urea, Ammonia)
- China → US Pacific Northwest (Limited, declining)

**Styling:**
- Curved geodesic arcs
- Animated flow (if using Mapbox/Leaflet plugins)
- Tooltip shows origin, destination, commodity, annual tonnage

---

## IV. REPORT SECTIONS (HTML Deliverables)

Following the Tampa Bay Cement Report model, create these HTML documents:

### Report Hub: INDEX.html
**Template:** G:\My Drive\LLM\project_cement\reports\INDEX.html

**Structure:**
```
Header: "US Fertilizer Market Intelligence Package"
Subtitle: "Production, Imports, Distribution & Infrastructure Analysis"
Date: "2025 | National & Regional Market Report"

Quick Stats (4 stat boxes):
- 16.79M MT - Total US Fertilizer Imports (2023-2025)
- 5.72M MT - Houston Port Share (#1 Import Gateway)
- 152 - Production Facilities (Nitrogen, Phosphate, Potash)
- 3,500 miles - Mississippi River System

Section 1: Start Here
  - Executive Summary (2-page overview)
  - Full Market Report (comprehensive analysis)

Section 2: Interactive Maps
  - US Fertilizer Production Facilities Map
  - Import Ports Map (weighted bubbles)
  - Mississippi River Transportation Network
  - Railroad Fertilizer Routes
  - Agricultural Demand Zones (heatmap)
  - Global Trade Flows to US

Section 3: Market Intelligence
  - Commodity Market Dashboards (Nitrogen, Phosphate, Potash)
  - Regional Market Analysis (Gulf Coast, Midwest, Pacific NW)
  - Supplier Country Profiles
  - Transportation Cost Analysis

Section 4: Presentations
  - Market Pitch Deck
  - Investor Overview
```

**Color Scheme (Noir Aesthetic):**
- Primary Dark: #0D1B2A (deep navy)
- Primary: #1B263B (slate blue)
- Accent 1: #415A77 (steel blue)
- Accent 2: #778DA9 (powder blue)
- Highlight: #E0E1DD (off-white for text/backgrounds)

---

### Executive Summary: FERTILIZER_MARKET_EXECUTIVE_SUMMARY.html

**Length:** 2-3 pages (printable)

**Content Blocks:**

**1. Market Overview**
- US fertilizer market size: ~$50B annually
- Domestic production vs import dependency
- Key commodity breakdown (nitrogen 60%, phosphate 25%, potash 15%)

**2. Supply Infrastructure Snapshot**
- 152 production facilities across 35 states
- 60% of nitrogen production in Gulf Coast (cheap natural gas)
- Florida phosphate rock: 75% of US production
- 100% potash import-dependent (Canada supplies 85%)

**3. Import Statistics (2023-2025 Average)**
- Total imports: 16.79M MT annually
- Top ports: Houston (5.72M), New Orleans (2.1M), Portland OR (1.8M)
- Top suppliers: Canada (35%), Russia (18%), Morocco (12%), Trinidad (9%)
- Import tariffs: Generally 0% (free trade), except countervailing duties on specific origins

**4. Transportation Infrastructure**
- Mississippi River system: 45% of domestic fertilizer movements
- Class I railroads: 35% of movements (especially potash)
- Trucking: 15% (last-mile delivery)
- Ocean shipping: 5% (coastal/Great Lakes)

**5. Market Trends**
- Declining Russian imports due to sanctions (down 40% since 2022)
- Increased North African imports (Morocco, Egypt, Algeria)
- US nitrogen production expansion (CF Industries, Koch)
- Climate impacts on river transportation (2022-2023 droughts)

**6. Strategic Recommendations**
- Diversify import sources away from Russia
- Invest in Mississippi River lock modernization
- Expand Gulf Coast import terminal capacity
- Develop domestic potash production (reduce Canadian dependency)

---

### Full Market Report: US_FERTILIZER_MARKET_REPORT.html

**Template:** Similar to FLORIDA_CEMENT_MARKET_REPORT.html

**Structure:**

#### Part 1: Supply Side Analysis

**1.1 US Fertilizer Production Landscape**

*Nitrogen Production (Ammonia/Urea/UAN)*
- Total US capacity: ~25M MT nitrogen nutrient annually
- Major producers:
  - **CF Industries** (40% market share) - Donaldsonville LA, Port Neal IA, Yazoo City MS, Verdigris OK
  - **Koch Fertilizer** (15%) - Enid OK, Beatrice NE, Fort Dodge IA
  - **Nutrien** (12%) - Lima OH, Borger TX
  - **Yara** (8%) - Belle Chasse LA, New Orleans LA
  - **CVR Partners** (5%) - Coffeyville KS, East Dubuque IL

*Technology:*
- Natural gas-based Haber-Bosch ammonia synthesis
- US advantage: Low natural gas prices vs global (Henry Hub ~$2.50/MMBtu)
- Capacity utilization: ~80% (cyclical based on crop prices)

*Geographic Concentration:*
- Gulf Coast: 60% of capacity (Louisiana, Texas)
- Midwest: 30% (Iowa, Kansas, Oklahoma)
- Other: 10% (scattered)

**Table: Top 15 US Nitrogen Plants**
| Plant Name | Owner | Location | Capacity (MT NH3/yr) | Products | Status |
|------------|-------|----------|---------------------|----------|--------|
| CF Donaldsonville | CF Industries | Donaldsonville, LA | 3,200,000 | NH3, Urea, UAN | Operating |
| CF Port Neal | CF Industries | Sergeant Bluff, IA | 1,100,000 | NH3, Urea, UAN | Operating |
| ... (15 total) |

*Phosphate Production*
- Total capacity: ~12M MT P2O5 annually
- Geographic concentration: Florida (75%), North Carolina (15%), Idaho (10%)
- Major producers:
  - **Mosaic** (60% market share) - FL mines + processing
  - **Nutrien** (20%)
  - **Simplot** (15%) - Idaho operations
  - **PotashCorp** (5%)

**Table: US Phosphate Mines & Processing Plants**
| Facility | Company | State | Type | Capacity | Products |
|----------|---------|-------|------|----------|----------|
| Mosaic Four Corners | Mosaic | Florida | Mine + Plant | 3.5M MT rock | Phosphate rock, DAP, MAP |
| ... |

*Potash Production*
- **US has only 2 operating potash mines** (New Mexico, Utah)
- Domestic capacity: ~1M MT K2O/year
- Import dependency: 90% (Canada supplies 85%)

**Table: US Potash Operations**
| Mine | Company | Location | Capacity | Type |
|------|---------|----------|----------|------|
| Intrepid Potash Carlsbad | Intrepid | Carlsbad, NM | 500K MT | Underground |
| Intrepid Potash Moab | Intrepid | Moab, UT | 300K MT | Solution mining |

---

**1.2 Import Terminals & Ports**

**Gulf Coast Ports (68% of US fertilizer imports)**

*Houston, TX - #1 US Fertilizer Import Port*
- Total volume: 5.72M MT (2023-2025 avg)
- Commodities: Ammonia (40%), Urea (35%), DAP/MAP (20%), Potash (5%)
- Major terminals:
  - **Kinder Morgan Pasadena** - Ammonia refrigerated storage (75K MT)
  - **Trafigura Houston** - Urea/DAP terminal
  - **Enterprise Products Houston Ship Channel** - Ammonia pipeline terminal
  - **Trammo Houston** - Multi-commodity terminal
- Primary suppliers: Trinidad (ammonia), Russia/Middle East (urea), Morocco (phosphate)
- Rail connections: UP, BNSF (distribute to Midwest)

*New Orleans/Louisiana Ports Complex*
- Total volume: 2.1M MT
- Ports: New Orleans, Gramercy, Burnside, Geismar
- Commodities: Potash (45%), Urea (30%), DAP/MAP (25%)
- River distribution via Mississippi River system
- Major terminals:
  - **International Marine Terminals** - Potash specialty
  - **Cooper/T. Smith** - Multi-commodity
  - **Nustar Terminals** - Ammonia/UAN

*Tampa, FL*
- Volume: 890K MT (primarily phosphate exports, some nitrogen imports)
- **Mosaic terminals** - export phosphate from Florida mines
- Import: Nitrogen fertilizers for Florida agriculture

*Mobile, AL*
- Volume: 620K MT
- Commodities: Potash (60%), Urea (40%)
- **McDuffie Coal Terminal** - handles fertilizer
- Mississippi River barge access

**Pacific Northwest Ports (15% of imports)**

*Portland, OR / Longview, WA*
- Volume: 1.8M MT combined
- Commodity: 90% Potash from Canada (rail from Saskatchewan)
- **Columbia Grain Terminal** - potash specialty
- River barge distribution up Columbia/Snake to Idaho

**East Coast Ports (12% of imports)**

*Savannah, GA / Charleston, SC*
- Volume: 1.2M MT combined
- Commodities: Urea, DAP/MAP
- Suppliers: Morocco, Middle East, Russia (declining)

*Norfolk, VA / Baltimore, MD*
- Volume: 800K MT combined
- Potash imports via Saint Lawrence Seaway

**Great Lakes (5% of imports)**

*Toledo, OH / Chicago, IL*
- Volume: 400K MT
- Canadian potash via lake shipping (seasonal, May-November)

---

#### Part 2: Demand Side Analysis

**2.1 US Agricultural Fertilizer Demand**

**Total US Fertilizer Consumption:**
- Nitrogen (N): 13.5M MT nutrient
- Phosphate (P2O5): 4.2M MT nutrient
- Potash (K2O): 5.8M MT nutrient

**Demand by Crop Type:**

*Corn (40% of total fertilizer use)*
- Acreage: 90M acres
- Nitrogen application: 150 lbs/acre average
- Total N demand: 6.8M MT
- States: Iowa, Illinois, Nebraska, Minnesota, Indiana

*Soybeans (20%)*
- Acreage: 87M acres
- Lower N demand (legume fixation), high P/K
- Phosphate: 60 lbs/acre
- Potash: 90 lbs/acre

*Wheat (15%)*
- Acreage: 45M acres
- Nitrogen: 80 lbs/acre
- States: Kansas, North Dakota, Montana, Washington

*Cotton (8%)*
- Acreage: 12M acres
- Intensive fertilization (all nutrients)
- States: Texas, Georgia, Mississippi, Arkansas

**Geographic Demand Concentration:**

*Corn Belt (55% of total demand)*
- Iowa: #1 state (2.1M MT total nutrients)
- Illinois: #2 (1.9M MT)
- Nebraska: #3 (1.6M MT)
- Minnesota, Indiana: #4-5

*Great Plains (20%)*
- Kansas, North Dakota, South Dakota
- Wheat and corn

*Southeast (12%)*
- Cotton, peanuts, vegetables
- Georgia, Alabama, Mississippi, Arkansas

*Other (13%)*
- California specialty crops, Pacific NW wheat, etc.

---

**2.2 Customer Segments**

**Retail Distribution (Farm Supply Cooperatives & Dealers) - 70% of market**
- **Nutrien Ag Solutions** - Largest retail network, 1,700+ locations
- **CHS Inc.** - Farmer cooperative, 1,000+ locations
- **Growmark** - Regional cooperative (Midwest)
- **Southern States Cooperative** - Southeast
- Independent dealers - 5,000+ locations nationwide

**Direct-to-Farm (Large Growers) - 15%**
- Mega-farms purchasing directly from producers/importers
- Custom application services

**Industrial/Commercial - 10%**
- Golf courses, landscaping, turf management
- Municipal applications

**Export - 5%**
- Re-export of imported fertilizers to Latin America (limited)

---

#### Part 3: Transportation Infrastructure Deep-Dive

**3.1 Mississippi River Transportation System**

**System Overview:**
- 3,500 navigable miles (Cairo, IL to Gulf of Mexico)
- 29 locks on Upper Mississippi
- 45% of US fertilizer moves by barge at some point

**Cost Advantage:**
- Barge: $0.01-0.02 per ton-mile
- Rail: $0.03-0.05 per ton-mile
- Truck: $0.10-0.15 per ton-mile
- Example: New Orleans to St. Louis (700 miles)
  - Barge: $7-14 per ton
  - Rail: $21-35 per ton
  - Truck: $70-105 per ton

**Major Fertilizer Movements:**
- Northbound: Imported fertilizers from Gulf (urea, potash, DAP) to Midwest
- Southbound: Domestic nitrogen (from Midwest plants) to Gulf for blending/export

**Critical Locks for Fertilizer (Ranked by Tonnage):**

1. **Locks 27** (Granite City, IL) - 1.25M MT fertilizer annually
2. **Locks & Dam 26** (Alton, IL) - 1.18M MT
3. **Melvin Price L&D** (Alton, IL) - 1.15M MT
4. **LaGrange Lock** (LaGrange, IL) - 980K MT
5. **Peoria Lock** (Peoria, IL) - 890K MT

**Table: Mississippi River Lock System - Fertilizer Tonnages**
| Lock Name | River Mile | Location | Fertilizer Tons (2024) | Avg Delay (hrs) | Condition |
|-----------|------------|----------|----------------------|----------------|-----------|
| L&D 27 | 185.5 | Granite City, IL | 1,250,000 | 2.3 | Fair |
| ... (29 locks total) |

**Infrastructure Challenges:**
- Aging lock infrastructure (most built 1930s-1950s)
- 600-foot lock chambers (too small for modern 15-barge tows, must break tow and double-lock)
- Winter ice closures (December-February, Upper Mississippi)
- Drought impacts (2022-2023: River levels critically low, reduced tow sizes)

**USACE Modernization Program:**
- $8.7B allocated for lock replacements
- Priority: Locks 20-25 (LaGrange to Saverton)
- Timeline: 2025-2035

---

**3.2 Railroad Fertilizer Transportation**

**Class I Railroads Serving Fertilizer Market:**

*BNSF Railway*
- **Primary corridor:** Saskatchewan potash to Gulf ports (Texas, Louisiana)
- **Route:** Regina → Galveston/Houston (2,100 miles, 5-7 days)
- **Volume:** 3.5M MT potash annually
- **Also:** Fertilizer distribution throughout Corn Belt

*Union Pacific*
- **Primary corridors:**
  - Gulf Coast imports → Midwest distribution
  - California imports → Interior West
- **Volume:** 2.8M MT annually
- **Unit trains:** 110-car potash trains from Vancouver, BC to California

*Canadian National (CN) / Canadian Pacific (CP)*
- **Primary:** Canadian potash/nitrogen to US Midwest
- **Routes:** Saskatchewan → Duluth/Superior, Chicago, Toledo (lake ports)
- **Volume:** 2.2M MT annually

*CSX / Norfolk Southern*
- **Primary:** East Coast import distribution
- **Volume:** 1.5M MT annually (smaller share, truck-competitive in shorter hauls)

**Rail-to-Barge Transload Facilities:**
- Critical nodes connecting Canadian rail to Mississippi River system
- Locations: St. Louis, Memphis, Cairo IL

---

**3.3 Trucking (Last-Mile Delivery)**

- Fertilizer retailers typically within 50 miles of rail siding or river terminal
- Truck delivery to farm averages 20-30 miles
- Peak season: March-May (spring planting), September-October (fall application)
- Average load: 25 tons (pneumatic tankers for dry fertilizer, liquid tankers for UAN/ammonia)

---

#### Part 4: Supplier Country Analysis

**4.1 Canada - #1 US Fertilizer Supplier (35% of imports)**

**Potash:**
- Saskatchewan: World's largest potash reserves (Mosaic, Nutrien mines)
- US imports: 5.5M MT/year (85% of US potash supply)
- Transportation: Unit trains (110 cars) via BNSF, CN, CP
- Destinations: Gulf ports (export terminals), Pacific NW ports, Midwest direct

**Nitrogen:**
- Alberta ammonia/urea production
- US imports: 800K MT/year
- Transport: Pipeline (ammonia), rail (urea)

**Trade Status:**
- USMCA (formerly NAFTA): Tariff-free
- Highly integrated supply chain

---

**4.2 Russia - #2 Supplier (18%, declining due to sanctions)**

**Historical Position (pre-2022):**
- Urea: 2.5M MT/year to US
- Potash: 1.2M MT/year
- Ammonia: 500K MT/year

**Post-Sanctions (2023-2025):**
- Urea: Down 40% to 1.5M MT/year
- Potash: Down 60% to 480K MT/year
- Ammonia: Down 80% to 100K MT/year

**Trading Networks (from existing research):**
- **EuroChem** (Andrey Melnichenko) - Trading via Swiss entities
- **PhosAgro** (Guryev family) - Limited US access post-sanctions
- **Uralkali** - Minimal US trade (focused on China/India)

**US Ports Receiving Russian Fertilizer:**
- New Orleans (potash via Baltic ports)
- Houston (urea via Middle East transshipment)
- Savannah, Charleston (urea direct)

**Sanction Evasion:**
- Fertilizers technically exempt from sanctions (food security)
- But: Banking restrictions, shipping insurance issues limit trade
- Transshipment via Turkey, UAE (re-labeling)

---

**4.3 Morocco - #3 Phosphate Supplier (12%)**

**OCP Group:**
- World's largest phosphate rock exporter
- US imports: 1.8M MT phosphate rock/year
- Destinations: Gulf Coast (Louisiana, Florida processing plants)
- Products: Phosphate rock → processed to DAP/MAP in US

**Trade Status:**
- US-Morocco Free Trade Agreement (2006): Tariff-free

---

**4.4 Trinidad & Tobago - #4 Ammonia Supplier (9%)**

**Production:**
- Methanol Holdings Trinidad (MHTL)
- Point Lisas Industrial Estate
- US imports: 1.5M MT ammonia/year

**Transportation:**
- Refrigerated ammonia tankers
- Houston terminals (primary destination)
- Pipeline distribution to US Gulf nitrogen plants

**Strategic Importance:**
- Reliable Western Hemisphere supplier
- Natural gas-based production (Trinidad gas reserves)

---

**4.5 Middle East - Growing Share (8%)**

**Saudi Arabia (SABIC, Ma'aden):**
- Urea, DAP, ammonia
- US imports: 600K MT/year (growing)

**Qatar (Qafco):**
- Urea
- US imports: 400K MT/year

**UAE:**
- Urea, ammonia
- Transshipment hub (some Russian fertilizer re-labeled)

---

#### Part 5: Market Trends & Strategic Outlook

**5.1 Supply Chain Vulnerabilities**

**Potash Import Dependency:**
- 90% of US potash imported (mostly Canada)
- **Risk:** Canadian rail strikes, port congestion (Vancouver)
- **Mitigation:** Develop US potash (exploration in Michigan, North Dakota Williston Basin)

**Russian Sanctions Impact:**
- 2.5M MT annual import shortfall (replaced by Morocco, Middle East, Egypt)
- Price volatility (2022 spike: Urea $900/MT, now ~$350/MT)

**Mississippi River Climate Risk:**
- 2022-2023 drought: River levels at historic lows
- Reduced barge capacity (40-50% of normal)
- Transportation cost spike (barge rates tripled)
- **Mitigation:** Lock system upgrades, alternative rail routes

**Geopolitical Risk:**
- China fertilizer export bans (2021-2022): Limited US impact (China not major US supplier)
- Ukraine war: Disrupted Black Sea potash/urea (Russia, Belarus)

---

**5.2 Technology Trends**

**Precision Agriculture:**
- Variable-rate application (VRA) technology
- Reduces fertilizer use 10-20% vs broadcast
- Soil testing, satellite imagery, yield mapping

**Enhanced Efficiency Fertilizers (EEF):**
- Slow-release coatings (polymer-coated urea)
- Nitrification inhibitors (reduce N loss)
- Premium pricing: 20-30% above commodity fertilizer

**Sustainable Nitrogen Production:**
- Green ammonia (electrolysis + renewable energy)
- CF Industries: Blue ammonia pilot (carbon capture)
- Timeline: Commercial scale 2030+

---

**5.3 Regulatory Environment**

**EPA Nutrient Management:**
- Chesapeake Bay TMDL (Total Maximum Daily Load) - Phosphorus/Nitrogen runoff limits
- Impact: Reduced fertilizer rates in Maryland, Virginia, Pennsylvania

**State-Level Regulations:**
- Iowa Nutrient Reduction Strategy (voluntary)
- Minnesota Buffer Law (fertilizer-free zones near water)

**USDA Conservation Programs:**
- EQIP (Environmental Quality Incentives Program) - Cost-share for precision ag, cover crops
- Reduces fertilizer demand via improved efficiency

---

## V. TECHNICAL REQUIREMENTS

### GeoJSON Layer Specifications

**Coordinate System:** WGS84 (EPSG:4326)
**File Format:** GeoJSON (RFC 7946 compliant)
**Validation:** Use geojsonlint.com before publishing

**Naming Convention:**
- `us_fertilizer_plants.geojson`
- `us_fertilizer_import_ports_weighted.geojson`
- `mississippi_river_fertilizer_system.geojson`
- `class1_rail_fertilizer_routes.geojson`
- `us_fertilizer_demand_zones.geojson`
- `global_fertilizer_trade_flows.geojson`

**File Size Management:**
- Rail network: Simplify geometry (tolerate 100m positional error for web display)
- Large shapefiles: Use mapshaper.org to reduce vertices by 50%
- Target: <5MB per GeoJSON file for web performance

---

### ArcGIS Online Integration

**Account:** Use existing theshipsagent.com ArcGIS Online organization account

**Upload Process:**
1. Upload each GeoJSON to "My Content"
2. Publish as hosted feature layer
3. Configure popup templates with HTML formatting
4. Set symbology (graduated symbols, heatmaps, categorical colors)
5. Share: Public or Organization-only (client preference)

**Web Map Creation:**
- **Basemap:** Dark Gray Canvas (noir aesthetic) or Light Gray Canvas
- **Layer Order:**
  1. Demand heatmap (bottom, semi-transparent)
  2. Rail/River lines
  3. Trade flow arcs
  4. Plant points
  5. Port bubbles (top, most interactive)

**StoryMap Configuration:**
- ArcGIS StoryMaps template (Sidecar or Map Tour)
- Embed web maps at key narrative points
- Side-by-side text and map views

---

### HTML Report Styling (Noir Aesthetic)

**Color Palette:**
```css
:root {
    --primary-dark: #0D1B2A;    /* Deep navy - headers, backgrounds */
    --primary: #1B263B;          /* Slate blue - section backgrounds */
    --secondary: #415A77;        /* Steel blue - accents, buttons */
    --secondary-light: #778DA9;  /* Powder blue - charts, highlights */
    --neutral-light: #E0E1DD;    /* Off-white - text backgrounds */
    --text-dark: #0D1B2A;        /* Primary text */
    --text-light: #E0E1DD;       /* Light text on dark backgrounds */
    --accent-green: #52796F;     /* Muted green - success states */
    --accent-orange: #C77A4B;    /* Muted orange - warnings */
}
```

**Typography:**
- Headings: `font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;`
- Body: Same, `line-height: 1.6`
- Code/Data: `font-family: 'Courier New', monospace;`

**Layout:**
- Max-width: 1400px for reports, 900px for index
- Responsive grid: CSS Grid for stat cards, tables
- Print-friendly: `@media print` styles (remove nav, optimize spacing)

**Chart Library:**
- Chart.js (same as cement reports)
- Color scheme: Use --secondary-light for primary data series
- Background: Semi-transparent --primary for chart backgrounds

---

## VI. ESTIMATED DELIVERABLES LIST

### HTML Reports (10 files)
1. `INDEX.html` - Report hub/landing page
2. `FERTILIZER_MARKET_EXECUTIVE_SUMMARY.html` - 2-page summary
3. `US_FERTILIZER_MARKET_REPORT.html` - Full comprehensive report
4. `NITROGEN_MARKET_DASHBOARD.html` - Nitrogen commodity focus
5. `PHOSPHATE_MARKET_DASHBOARD.html` - Phosphate commodity focus
6. `POTASH_MARKET_DASHBOARD.html` - Potash commodity focus
7. `GULF_COAST_REGIONAL_REPORT.html` - Gulf Coast deep-dive
8. `MIDWEST_REGIONAL_REPORT.html` - Corn Belt analysis
9. `FERTILIZER_MARKET_PITCH_DECK.html` - Presentation slides
10. `FERTILIZER_INFRASTRUCTURE_MAP.html` - Standalone interactive map page

### GeoJSON Map Layers (6 files)
1. `us_fertilizer_plants.geojson`
2. `us_fertilizer_import_ports_weighted.geojson`
3. `mississippi_river_fertilizer_system.geojson`
4. `class1_rail_fertilizer_routes.geojson`
5. `us_fertilizer_demand_zones.geojson`
6. `global_fertilizer_trade_flows.geojson`

### Supporting Data Files (3 files)
1. `fertilizer_import_data_2023_2025.xlsx` - Panjiva aggregated data
2. `fertilizer_production_facilities.xlsx` - Plant database
3. `fertilizer_trade_statistics.xlsx` - USDA/USGS/Census compiled data

### ArcGIS Online Content
- 6 hosted feature layers (from GeoJSON uploads)
- 3 web maps (Production, Imports, Transportation)
- 1 StoryMap (narrative combining all maps)

---

## VII. PROJECT TIMELINE (Estimated)

**Phase 1: Data Collection (2-3 weeks)**
- Week 1: Government data (USDA, USGS, Census, USACE)
- Week 2: Commercial data (Panjiva query, Clarksons subscription)
- Week 3: Geospatial data (BTS NTAD, GEM database, cleanup)

**Phase 2: Data Processing & Analysis (2 weeks)**
- Panjiva aggregation (by port, commodity, origin)
- GeoJSON creation and validation
- Statistical analysis (trends, market shares)

**Phase 3: Report Writing (2 weeks)**
- Executive Summary
- Full Market Report (4 parts)
- Commodity dashboards (3)
- Regional reports (2)

**Phase 4: Visualization & Mapping (1-2 weeks)**
- Chart.js charts embedded in HTML
- GeoJSON styling and testing
- ArcGIS Online publishing
- StoryMap creation

**Phase 5: Review & Finalization (1 week)**
- Proofreading, fact-checking
- Link testing, cross-browser compatibility
- Client review and revisions

**Total: 8-10 weeks**

---

## VIII. SUCCESS CRITERIA

A successful US Fertilizer Market Report will:

1. **Provide Comprehensive Coverage** - All major fertilizer commodities (N, P, K), all major ports, all major suppliers
2. **Actionable Intelligence** - Traders can identify supply chain opportunities, investors can identify infrastructure gaps
3. **Visual Excellence** - Interactive maps that are publication-quality, shareable
4. **Data Integrity** - All statistics sourced and cited, reproducible analysis
5. **User-Friendly Navigation** - INDEX.html as central hub, clear report hierarchy
6. **Mobile-Responsive** - Reports render properly on tablets/phones
7. **Print-Optimized** - Executive Summary and reports print cleanly (CSS @media print)
8. **Brand Consistency** - Matches theshipsagent.com noir aesthetic (dark blues, clean typography)

---

## IX. NOTES & ASSUMPTIONS

**Data Limitations:**
- Fertilizer trade data often aggregated (hard to separate urea vs UAN in some datasets)
- Domestic barge movements on Mississippi not comprehensively tracked (use USACE lock data as proxy)
- Customer-level data (who buys from whom) is proprietary - can infer from Panjiva consignees

**Comparison to Cement Report:**
- Fertilizer market is more commodity-driven (less brand differentiation than cement)
- Transportation analysis is MORE critical (fertilizer margins thin, logistics cost = competitive advantage)
- Fertilizer has stronger seasonality (spring/fall application seasons)

**Potential Enhancements (Future Phases):**
- Real-time pricing dashboard (Fertilizer Week subscription data)
- Futures market analysis (CME fertilizer contracts)
- Carbon footprint analysis (green ammonia opportunities)
- Water quality impact modeling (nutrient runoff)

---

## X. DATA SOURCE URLS (REFERENCE)

- USDA ERS Fertilizer: https://www.ers.usda.gov/topics/farm-economy/fertilizer-use-and-price/
- USGS Minerals: https://www.usgs.gov/centers/national-minerals-information-center/fertilizer-statistics-and-information
- US Census Trade: https://usatrade.census.gov/
- USACE Navigation: https://www.iwr.usace.army.mil/NDC/
- BTS Geospatial: https://geodata.bts.gov/
- Global Energy Monitor: https://globalenergymonitor.org/
- Panjiva: https://panjiva.com/ (subscription)
- Clarksons: https://sin.clarksons.net/ (subscription)
- The Fertilizer Institute: https://www.tfi.org/
- CF Industries: https://www.cfindustries.com/
- Mosaic Company: https://www.mosaicco.com/
- Nutrien: https://www.nutrien.com/

---

**END OF US FERTILIZER MARKET REPORT PLAN**
