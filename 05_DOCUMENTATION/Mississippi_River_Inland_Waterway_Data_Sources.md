# Mississippi River & Inland Waterway Transportation Data Sources

**Compiled:** January 29, 2026
**Focus:** Mississippi River inland barge transport, national waterways, locks, tonnage, commodity flows, and navigation datasets

---

## 📊 Executive Summary

This document catalogs **249 total data sources** with **specialized focus on inland waterway transportation**. Key highlights:
- **USACE (U.S. Army Corps of Engineers)** datasets for lock operations, waterway networks, and commodity flows
- **BTS (Bureau of Transportation Statistics)** comprehensive navigation facilities and tonnage data
- **NOAA** navigational charts and real-time maritime data
- **Local geospatial files** with detailed waterway infrastructure

---

## 🚢 CRITICAL USACE NAVIGATION & COMMERCE DATA SOURCES

### **1. Waterborne Commerce Statistics Center (WCSC)**
**Source:** USACE Institute for Water Resources
**URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/
**Data Portal:** https://ndc.ops.usace.army.mil/wcsc/webpub/
**Description:** Comprehensive waterborne commerce data including vessel trips and cargo data collected within the Oracle Waterborne System and Lock Performance Monitoring System. Provides downloadable data for:
- Port, lock and waterway facility characteristics
- Vessel characteristics
- Commodity movement across the nation
- Monthly indicators and annual reports on waterborne commerce statistics

**Update Status:** Ongoing collection with annual reports
**Data Sources:** U.S. Customs and Border Protection, U.S. Census Bureau, Port Import Export Reporting Service
**Formats:** Oracle Database, W-DAPP tool (Waterborne Data Analyzer and Pre-Processor), Downloadable datasets

---

### **2. Lock Performance Monitoring System (LPMS)**
**Source:** USACE Navigation and Civil Works Decision Support Center (NDC)
**URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/NDC-Navigation-and-Civil-Works-Decision-Support/NDC-Locks/
**Data Portal:** https://ndc.ops.usace.army.mil/ords/f?p=108:1::::::
**CISA Reference:** https://www.cisa.gov/mts-resilience-resources/lock-performance-monitoring-system-lpms
**Description:** Web-based system collecting and reporting data on vessels traversing through Corps-owned or operated locks in **near real-time**. Includes:
- Lock performance metrics
- Hourly lock performance data
- Vessel-specific information
- Navigation decision support

**Update Status:** Near real-time data collection and reporting
**Dataset ID:** DS-238 (Chrome Bookmarks)

---

### **3. Foreign Traffic Vessel Entrances and Clearances**
**Source:** USACE Navigation Data Center (NDC) Library
**URL:** https://ndclibrary.sec.usace.army.mil/searchResults?series=Foreign%20Traffic%20Vessel%20Entrances%20Clearances
**Description:** Dataset series documenting foreign trade vessel movements including:
- Vessel entrance and clearance dates
- Customs district and port codes
- Vessel manifest numbers
- Vessel names and IMO numbers

**Data Sources:** U.S. Customs and Border Protection, U.S. Census Bureau, Port Import Export Reporting Service
**Update Status:** Historical compilation maintained by ERDC team

---

### **4. Schedule K - Foreign Port Codes**
**Source:** USACE Waterborne Commerce Statistics Center (WCSC)
**URL:** https://ndclibrary.sec.usace.army.mil/searchResults?series=Schedule%20K%20Foreign%20Port%20Codes
**CBP Resource:** https://www.cbp.gov/document/guidance/ace-ocean-camir-appendix-f-schedule-k
**Description:** Geographic coding scheme identifying seaports worldwide that handle waterborne shipments involved in foreign trade with the U.S.
- Five-digit numeric identifiers for major seaports
- Used by carriers on electronic vessel manifests
- Used by importers/customs brokers in entry filings

**Update Status:** Regularly updated (Recent: February 2025, August 2024)
**Dataset ID:** DS-249

---

### **5. Dredging Information System (DIS) - NDC Dredges Database**
**Source:** USACE Navigation and Civil Works Decision Support Center (NDC)
**URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/NDC-Navigation-and-Civil-Works-Decision-Support/NDC-Dredges/
**Data Portal:** https://ndc.ops.usace.army.mil/dis/
**Description:** Full lifecycle database capturing USACE dredging work including:
- In-house operations and contracted work
- Bid schedules and contract locations
- Dredge types and cubic yards
- Comprehensive dredging contract activities

**Update Status:** Ongoing collection with district staff data input

---

### **6. Notice to Navigation Interests (NTNI)**
**Source:** USACE Navigation and Civil Works Decision Support Center (NDC)
**URL:** https://www.iwr.usace.army.mil/About/Technical-Centers/NDC-Navigation-and-Civil-Works-Decision-Support/NDC-Navigation-Notices/
**Data Portal:** https://ndc.ops.usace.army.mil/ords/f?p=107:1::::::
**Description:** Centralized access for mariners to find notices of:
- Maintenance projects
- Hazards, closures, or restrictions
- Real-time waterway conditions
- Official USACE navigation status information

**Update Status:** Real-time updates as conditions change

---

### **7. Navigation and Civil Works Decision Support (NDC) Library**
**Source:** USACE Institute for Water Resources
**URL:** https://ndclibrary.sec.usace.army.mil/
**Commodity Data:** https://ndclibrary.sec.usace.army.mil/searchResults?series=Commodity%20Monthly%20Indicators
**Waterborne Cargo:** https://ndclibrary.sec.usace.army.mil/searchResults?series=Waterborne%20Foreign%20Cargo
**Description:** Central library with multiple data series including:
- Commodity Monthly Indicators
- Waterborne Foreign Cargo
- Vessel Company Summaries
- Historical navigation data

**Update Status:** Ongoing updates
**Dataset IDs:** DS-246, DS-247, DS-248

---

## 🗺️ BTS (BUREAU OF TRANSPORTATION STATISTICS) WATERWAY DATASETS

### **8. Navigable Waterway Network Lines**
**Source:** Federal Geographic Data Committee / USACE / BTS
**URL:** https://catalog.data.gov/dataset/navigable-waterway-network-lines-129e0
**Description:** Periodically updated waterway network lines dataset
**Formats:** XML, JSON, RSS, HTML, ArcGIS GeoServices REST API, CSV, ZIP, GeoJSON, KML, TEXT, XLS, GPKG, GDB
**Dataset ID:** DS-123
**Update Status:** Periodically updated by USACE

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\09_bts_waterway_networks\`
- Formats: GeoJSON (38.3 MB), CSV, TXT, GPKG (30.9 MB), KMZ, Geodatabase, ZIP
- File count: 9+ files with complete network data

---

### **9. Navigable Waterway Network Nodes**
**Source:** Federal Geographic Data Committee / USACE / BTS
**URL:** https://catalog.data.gov/dataset/navigable-waterway-network-nodes-47f75
**Catalog:** https://catalog.data.gov/dataset/navigable-waterway-network-nodes
**Description:** Node points for navigable waterway network
**Formats:** XML, JSON, RSS, HTML, ArcGIS GeoServices REST API, CSV, ZIP, GeoJSON, KML, TEXT, XLS, GPKG, GDB
**Dataset ID:** DS-135, DS-216
**Update Status:** Periodically updated by USACE

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\10_bts_waterway_nodes\`

---

### **10. Waterway Locks**
**Source:** Federal Geographic Data Committee / USACE / BTS
**URL:** https://catalog.data.gov/dataset/waterway-locks-ddc5f
**Catalog:** https://catalog.data.gov/dataset/waterway-locks1
**Description:** Complete dataset of waterway locks across U.S. inland waterway system
**Formats:** XML, JSON, RSS, HTML, ArcGIS GeoServices REST API, CSV, ZIP, GeoJSON, KML, TEXT, XLS, GPKG, GDB
**Dataset ID:** DS-125, DS-213
**Update Status:** Periodically updated by USACE

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\04_bts_locks\`
- Formats: CSV (66.8 KB), GeoJSON (203 KB), TXT (219 KB), GPKG (204 KB), KMZ, Geodatabase, ZIP, XLSX
- File count: 9 files with complete lock infrastructure data

---

### **11. Link Tonnages**
**Source:** Department of Transportation - USACE / BTS
**URL:** https://catalog.data.gov/dataset/total-tonnage-foreign-and-domestic-of-commodites-carried-on-commercial-waterways
**Description:** Tonnage data on transportation links for supply chain analysis. Total tonnage (foreign and domestic) of commodities carried on commercial waterways
**Formats:** HTML/Geospatial, CSV, XLSX, KMZ, Geodatabase, GPKG, ZIP
**Dataset ID:** DS-010, DS-207
**Update Status:** Updated August 2025

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\03_bts_link_tons\`
- Formats: CSV (332 KB), XLSX (319 KB), TXT (2.2 MB), GPKG (1.1 MB), Geodatabase (1.0 MB), KMZ, ZIP
- File count: 8 comprehensive tonnage files

---

### **12. Navigation Facilities (Docks)**
**Source:** Federal Geographic Data Committee / USACE / BTS
**URL:** https://catalog.data.gov/dataset/docks-cc874
**Description:** Navigation facilities dataset including docks, fleeting areas, marinas, anchorages, and other waterway facilities
**Formats:** XML, JSON, RSS, HTML, ArcGIS GeoServices REST API, CSV, ZIP, GeoJSON, KML, TEXT, XLS, GPKG, GDB
**Dataset ID:** DS-131
**Update Status:** Periodically updated by USACE

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\05_bts_navigation_fac\`
- Organized by:
  - **Port Category:** Inland Ports, Ocean Ports, Great Lakes, Alaska/US Islands, Unknown
  - **Facility Type:** Dock, Fleeting Area, Lock and/or Dam, Lock Chamber, Anchorage, Marina, Milepoint, Junction, Bridge, Tie-Off, Open Water, Virtual Dock, Virtual Marina
- Archive includes complete facility and berth data with port category dictionary

---

### **13. Docks (BTS)**
**Source:** Bureau of Transportation Statistics
**Description:** Standalone docks dataset
**Dataset ID:** DS-131
**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\01_bts_docks\`
- Multiple formats available

---

### **14. Intermodal Freight Facilities - Marine Roll-on/Roll-off**
**Source:** Department of Transportation - BTS
**URL:** https://catalog.data.gov
**Description:** Intermodal freight facilities for marine roll-on/roll-off operations
**Formats:** HTML/Geospatial
**Dataset ID:** DS-008
**Update Status:** Updated July 2022

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\02_bts_intermodal_roro\`

---

### **15. Principal Ports**
**Source:** Department of Transportation - USACE / BTS
**URL:** https://catalog.data.gov
**Description:** Principal ports dataset for maritime shipping and cargo operations
**Formats:** HTML/Geospatial
**Dataset ID:** DS-005
**Update Status:** Periodically Updated

**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\08_bts_principal_ports\`

---

### **16. Port Areas**
**Source:** Bureau of Transportation Statistics
**Description:** Port area boundaries and characteristics
**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\06_bts_port_area\`

---

### **17. Port Statistical Areas**
**Source:** Bureau of Transportation Statistics
**Description:** Statistical areas for port analysis
**Local Files Available:**
- Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\07_bts_port_stat_areas\`

---

### **18. Intermodal Freight Facilities - Pipeline Terminals**
**Source:** Bureau of Transportation Statistics (BTS)
**URL:** https://catalog.data.gov/dataset/intermodal-freight-facilities
**Description:** Pipeline terminal facilities with truck/rail/water mode connections and commodity data
**Formats:** ESRI Geodatabase, Shapefile
**Dataset ID:** DS-025
**Category:** Freight & Supply Chain
**Update Status:** Current

---

## 🌊 MARINE HIGHWAYS & SHIPPING

### **19. Marine Highways**
**Source:** Department of Transportation - MARAD
**URL:** https://catalog.data.gov
**Description:** Marine highway system for coastal and inland waterway shipping
**Formats:** HTML/Geospatial
**Dataset ID:** DS-009
**Update Status:** Updated September 2025

---

### **20. Shipping Fairways, Lanes, and Zones for US Waters**
**Source:** NOAA - National Oceanic and Atmospheric Administration, Office of Coast Survey
**URL:** https://catalog.data.gov/dataset/shipping-fairways-lanes-and-zones-for-us-waters1
**Description:** Documents various shipping zones that delineate activities and regulations for marine vessel traffic including:
- Traffic lanes
- Separation zones
- Precautionary navigation areas
- Safety fairways
- Recommended shipping routes
- Seasonal speed-reduction zones (North Atlantic Right Whales)
- Particularly Sensitive Sea Areas
- Areas to be avoided

**Formats:** ZIP, Esri REST Services, ISO-19139 Metadata
**Geographic Coverage:** U.S. waters from 179.46°W to 174.6°E longitude and 9.31°N to 60.98°N latitude
**Update Status:** Weekly updates (Last: May 20, 2025)
**Contact:** patrick.keown@noaa.gov
**Note:** Not for navigation - intended for coastal and ocean planning purposes only

---

### **21. Shipping Fairways (HIFLD)**
**Source:** HIFLD - Bureau of Transportation Statistics
**URL:** https://hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::shipping-fairways
**Description:** Defined shipping fairways and marine traffic corridors for coastal planning
**Formats:** ESRI REST, Shapefile
**Dataset ID:** DS-029
**Update Status:** Current

---

### **22. Deepwater Ship Channels**
**Source:** USACE / State Agencies
**URL:** https://catalog.data.gov
**Description:** Polygon features of deepwater ship channels in critical waterways
**Formats:** GIS Polygon Features
**Dataset ID:** DS-033
**Update Status:** Current

---

### **23. Shipping Lanes - Gulf of Mexico**
**Source:** NOAA / BOEM
**URL:** https://catalog.data.gov
**Description:** Polygon data for all major shipping lanes in Gulf of Mexico
**Formats:** GIS Polygon Features
**Dataset ID:** DS-031
**Update Status:** Current

---

## 🛰️ VESSEL TRACKING & REAL-TIME DATA

### **24. Automatic Identification System (AIS) Vessel Tracking**
**Source:** NOAA / Maritime Safety
**URL:** https://catalog.data.gov
**Description:** Real-time location and characteristics of vessels tracked via navigation devices
**Formats:** Real-time Data
**Dataset ID:** DS-032
**Update Status:** Real-time

---

### **25. Physical Oceanographic Real-Time System (PORTS)**
**Source:** NOAA - National Ocean Service (NOS)
**URL:** https://tidesandcurrents.noaa.gov/ports.html
**Description:** Decision support system measuring and disseminating real-time observations and predictions:
- Water levels
- Currents
- Salinity
- Meteorological parameters (winds, atmospheric pressure, air/water temperatures)

Integrates real-time environmental observations with forecasts and geospatial information to improve safety and efficiency of maritime commerce.

**Formats:** Internet/Web platforms, Telephone voice response, PUFFF (PORTS Uniform Flat File Format), Numerical circulation model forecasts
**Geographic Coverage:** Various U.S. ports including Delaware River, Alaska, and other coastal locations
**Update Status:** Real-time continuous data collection

---

## 🗺️ NAVIGATION CHARTS & COASTAL DATA

### **26. NOAA Electronic Navigational Charts (ENCs)**
**Source:** NOAA - National Oceanic and Atmospheric Administration
**URL:** https://catalog.data.gov
**Catalog:** https://catalog.data.gov/dataset/noaa-electronic-navigational-charts-enc1
**Description:** Marine transportation infrastructure and coastal management charts
**Formats:** NOAA Standard Formats
**Dataset ID:** DS-036, DS-231
**Update Status:** Current

---

### **27. MarineCadastre.gov**
**Source:** NOAA - Department of Commerce
**URL:** https://marinecadastre.gov
**Description:** Marine information system with ocean data and offshore planning tools
**Formats:** Multiple
**Dataset ID:** DS-015
**Category:** Ports & Shipping - Environmental
**Update Status:** Current

---

### **28. Vessel Routing Measures**
**Source:** NOAA / MarineCadastre
**URL:** https://hub.arcgis.com/datasets/noaa::vessel-routing-measures/about
**Description:** Designated traffic lanes, precautionary areas, and shipping safety fairways
**Formats:** Feature Service
**Dataset ID:** Not in main catalog
**Update Status:** Current

---

## 🏗️ PORT & TERMINAL FACILITIES

### **29. Major U.S. Port Facilities**
**Source:** Bureau of Transportation Statistics (BTS) / HIFLD
**URL:** https://hifld-geoplatform.opendata.arcgis.com/datasets/major-us-port-facilities
**Description:** Comprehensive locations and characteristics of major U.S. port facilities
**Formats:** ESRI REST Services, Shapefile
**Dataset ID:** DS-028
**Update Status:** Current

---

### **30. Intermodal Freight Facilities - Liquid Bulk (BETA)**
**Source:** Bureau of Transportation Statistics (BTS)
**URL:** https://hub.arcgis.com/datasets/usdot::beta-intermodal-freight-facilities-liquid-bulk/about
**Description:** Liquid bulk transfer facilities including pipeline terminals and tank farms
**Formats:** Feature Service
**Dataset ID:** Not in main catalog
**Category:** Freight & Supply Chain
**Update Status:** Beta / Current

---

### **31. Pilot Boarding Areas**
**Source:** NOAA
**URL:** https://hub.arcgis.com/datasets/noaa::pilot-boarding-areas/about
**Description:** Locations where pilots board vessels for port entry and navigation
**Formats:** Feature Layer
**Dataset ID:** Not in main catalog
**Update Status:** Current

---

## 📦 COMMODITY & TRADE DATA

### **32. Product Commodity Class Hierarchy**
**Source:** USDA Agricultural Marketing Service
**URL:** https://fgisonline.ams.usda.gov/G_APS/G_APS_ComClassHierarchy.aspx?pEM=D
**Description:** Commodity classification hierarchy for agricultural products
**Dataset ID:** DS-239
**Update Status:** Current

---

### **33. Open Ag Transport Data**
**Source:** USDA
**URL:** https://agtransport.usda.gov/
**Description:** Agricultural transportation data including modal movements
**Dataset ID:** Chrome bookmarks collection
**Category:** Government - State/Local
**Update Status:** Current

---

### **34. Freight Analysis Framework (FAF5) Highway Network Assignments**
**Source:** Department of Transportation - BTS
**URL:** https://catalog.data.gov
**Description:** Freight flow data and highway network assignments for supply chain analysis based on 2017 base year
**Formats:** HTML/Geospatial
**Dataset ID:** DS-007
**Update Status:** Updated April 2022

---

## 🏭 INFRASTRUCTURE & FACILITIES

### **33. Federal Dams / National Inventory of Dams (NID)**
**Source:** Department of Transportation / USACE
**URL:** https://catalog.data.gov
**Description:** Inventory of dams with operational and structural characteristics
**Formats:** HTML/Geospatial
**Dataset ID:** DS-013
**Update Status:** Current

---

### **34. National Bridge Inventory**
**Source:** Department of Transportation - FHWA
**URL:** https://catalog.data.gov
**Description:** Bridge conditions and engineering data across U.S. highway system
**Formats:** HTML/Geospatial
**Dataset ID:** DS-012
**Update Status:** Updated June 2025

---

### **35. USGS National Structures Dataset**
**Source:** Department of the Interior - USGS
**URL:** https://catalog.data.gov
**Description:** Structures including facilities, dams, and operational infrastructure
**Formats:** XML
**Dataset ID:** DS-011
**Update Status:** Current

---

## 🌍 GEOSPATIAL & MAPPING RESOURCES

### **36. U.S. Energy Mapping System**
**Source:** U.S. Energy Information Administration
**URL:** https://catalog.data.gov/dataset/u-s-energy-mapping-system
**Description:** Map data for energy production and consumption in geospatial format
**Formats:** SHP, HTML
**Dataset ID:** DS-099
**Update Status:** Current

---

### **37. US Energy Atlas**
**Source:** Energy Information Administration (EIA)
**URL:** https://atlas.eia.gov
**Description:** Comprehensive energy infrastructure dataset with multiple download formats
**Formats:** CSV, KML, Zip, GeoJSON, GeoTIFF, WMS, WFS
**Dataset ID:** DS-034
**Category:** Infrastructure Transformation
**Update Status:** Current

---

## 📚 ADDITIONAL FEDERAL DATA RESOURCES

### **38. International Trade Data Main Page**
**Source:** U.S. Census Bureau
**URL:** https://www.census.gov/foreign-trade/data/index.html
**Description:** International trade statistics including waterborne commerce
**Dataset ID:** Chrome bookmarks collection
**Category:** Government - Federal Data

---

### **39. Surface Transportation Board**
**Source:** STB
**URL:** https://www.stb.gov/reports-data/
**Description:** Reports and data on surface transportation including rail and water carriers
**Dataset ID:** Chrome bookmarks collection
**Category:** Government - State/Local

---

### **40. Minerals Yearbook**
**Source:** USGS National Minerals Information Center
**URL:** https://www.usgs.gov/centers/national-minerals-information-center/minerals-yearbook-metals-and-minerals
**Description:** Annual data on mineral commodity production including transportation
**Dataset ID:** Chrome bookmarks collection
**Category:** Government - Federal Data

---

## 🛠️ TECHNICAL TOOLS & PORTALS

### **41. Corps Locks - Home (LPMS Portal)**
**Source:** USACE Navigation Data Center
**URL:** https://ndc.ops.usace.army.mil/ords/f?p=108:1::::::
**Description:** Interactive portal for Lock Performance Monitoring System data
**Dataset ID:** DS-243
**Category:** Government - Maritime/Waterways

---

### **42. IWR Project Assistance Library**
**Source:** USACE Institute for Water Resources
**URL:** https://publibrary.sec.usace.army.mil/
**Example:** https://publibrary.sec.usace.army.mil/resource?title=2023%20Vessel%20Company%20Summary&documentId=116a2b60-c10b-460e-fe60-6f74ac607dd9
**Description:** Library with vessel company summaries and waterborne commerce documents
**Dataset ID:** DS-246
**Category:** Government - Maritime/Waterways

---

## 📁 LOCAL GEOSPATIAL FILE INVENTORY

### **Complete BTS Navigation Dataset Collection**

Location: `G:\My Drive\LLM\sources_data_maps\01_geospatial\`

**Directory Structure:**
```
01_geospatial/
├── 01_bts_docks/                      - Dock facility data
├── 02_bts_intermodal_roro/            - Roll-on/Roll-off facilities
├── 03_bts_link_tons/                  - Link tonnage data (8 files, ~6.6 MB total)
├── 04_bts_locks/                      - Waterway locks (9 files, ~1.4 MB total)
├── 05_bts_navigation_fac/             - Navigation facilities (extensive archive)
│   ├── split_by_type/                 - Organized by facility type
│   │   ├── by_fac_type/
│   │   │   ├── Alaska_US_Islands/
│   │   │   ├── Great_Lakes/
│   │   │   ├── Inland_Ports/          - Mississippi River region data
│   │   │   ├── Ocean_Ports/
│   │   │   └── Unknown/
│   └── ARCHIVE_COMPLETE_20260109_1229/
│       ├── by_port_category/
│       └── by_fac_type/
├── 06_bts_port_area/                  - Port area boundaries
├── 07_bts_port_stat_areas/            - Port statistical areas
├── 08_bts_principal_ports/            - Principal ports
├── 09_bts_waterway_networks/          - Waterway networks (9 files, ~215 MB total)
└── 10_bts_waterway_nodes/             - Waterway network nodes
```

**Total Local Files:** 100+ geospatial files in multiple formats
**Total Size:** ~250+ MB of waterway infrastructure data

---

## 🎯 MISSISSIPPI RIVER SPECIFIC DATASETS

### **Inland Ports Navigation Facilities**
**Location:** `01_geospatial\05_bts_navigation_fac\ARCHIVE_COMPLETE_20260109_1229\by_fac_type\Inland_Ports\`

**Available Facility Types for Inland Waterways:**
- Docks (primary cargo transfer points)
- Fleeting Areas (barge staging)
- Lock and/or Dam facilities
- Lock Chambers
- Anchorages
- Marinas
- Milepoints (river mile markers)
- Junctions (waterway intersections)
- Bridges
- Tie-Off locations
- Open Water designations

**File Format:** CSV with complete facility details, geographic coordinates, and operational characteristics

---

## 📊 RECOMMENDED DATA WORKFLOW FOR MISSISSIPPI RIVER ANALYSIS

### **Step 1: Waterway Infrastructure**
1. **Waterway Networks** (DS-123) - Load base waterway geometry
2. **Waterway Nodes** (DS-135) - Add network connection points
3. **Locks** (DS-125) - Overlay lock locations and characteristics
4. **Navigation Facilities** (DS-131) - Add docks, fleeting areas, terminals

### **Step 2: Commodity Flows**
1. **Link Tonnages** (DS-010, DS-207) - Analyze commodity volumes by waterway segment
2. **WCSC Data** - Deep dive into vessel trips and cargo movements
3. **Commodity Monthly Indicators** (NDC Library) - Track temporal patterns

### **Step 3: Operational Data**
1. **Lock Performance Monitoring System** (LPMS) - Real-time lock operations
2. **Notice to Navigation Interests** (NTNI) - Current restrictions/hazards
3. **Dredging Information System** (DIS) - Channel maintenance activities

### **Step 4: Trade & Economic Analysis**
1. **Waterborne Commerce Statistics** - Annual trade volumes
2. **Foreign Traffic Vessel Data** - International cargo movements
3. **Vessel Company Summaries** - Commercial operator analysis

---

## 🔗 KEY DATA PORTALS (Quick Access)

| Portal | URL | Primary Use |
|--------|-----|-------------|
| **USACE NDC Operations Portal** | https://ndc.ops.usace.army.mil/ | Lock performance, dredging, notices |
| **WCSC Web Publisher** | https://ndc.ops.usace.army.mil/wcsc/webpub/ | Waterborne commerce statistics |
| **NDC Library** | https://ndclibrary.sec.usace.army.mil/ | Historical data, reports, commodity indicators |
| **Lock Performance System** | https://ndc.ops.usace.army.mil/ords/f?p=108:1:::::: | Real-time lock operations |
| **Navigation Notices** | https://ndc.ops.usace.army.mil/ords/f?p=107:1:::::: | Current waterway conditions |
| **Dredging System** | https://ndc.ops.usace.army.mil/dis/ | Channel maintenance data |
| **Data.gov Catalog** | https://catalog.data.gov | Federal dataset discovery |
| **MarineCadastre** | https://marinecadastre.gov | Ocean/coastal planning data |
| **NOAA Tides & Currents** | https://tidesandcurrents.noaa.gov/ports.html | Real-time PORTS data |

---

## 📖 DOCUMENTATION & METADATA

### **Facility State File Documentation**
**Location:** `G:\My Drive\LLM\sources_data_maps\qgis\Facility State File Documentation 11132012_new.pdf`
**Description:** Technical documentation for navigation facility data structure and coding

### **Master Inventory**
**Location:** `G:\My Drive\LLM\sources_data_maps\_build_documents\sources_inventory.csv`
**Records:** 249 datasets with complete metadata
**Columns:** SOURCE_ID, Name, Type, Source, Category, Description, URL, Update_Status

### **Interactive Dashboard**
**Location:** `G:\My Drive\LLM\sources_data_maps\_html_web_files\data_sources_index.html`
**Features:** Search, filter, sort, export capabilities for all 249 datasets

---

## 🎓 DATASET CATEGORIES SUMMARY

| Category | Count | Key Datasets |
|----------|-------|--------------|
| **Waterway Navigation** | 15+ | Networks, Nodes, Locks, Facilities, Charts |
| **Commodity Flows** | 8+ | Link Tonnages, WCSC, Monthly Indicators |
| **Port Operations** | 12+ | Principal Ports, Terminals, Anchorages |
| **Real-Time Data** | 5+ | AIS Tracking, PORTS, LPMS, NTNI |
| **Infrastructure** | 10+ | Dams, Bridges, Dredging, Channels |
| **Trade Statistics** | 8+ | Foreign Traffic, Customs, Commerce |

**Total Relevant Datasets:** 60+ specifically applicable to inland waterway transportation
**Total Dataset Collection:** 249 datasets covering all transportation modes and energy infrastructure

---

## 📞 KEY CONTACTS & RESOURCES

### **USACE - Institute for Water Resources**
- **Waterborne Commerce Statistics Center:** Direct contact through IWR website
- **Navigation and Civil Works Decision Support:** Technical support for NDC systems

### **NOAA - National Ocean Service**
- **PORTS Program:** https://tidesandcurrents.noaa.gov/ports.html
- **Coast Survey:** patrick.keown@noaa.gov (Shipping Fairways data)

### **Bureau of Transportation Statistics**
- **Data Portal:** https://catalog.data.gov (search by agency)

---

## ⚠️ IMPORTANT NOTES

1. **Data Currency:** Most datasets updated 2024-2025, some real-time
2. **Multiple Formats:** Most datasets available in CSV, GeoJSON, Shapefile, Geodatabase, KML
3. **Local Files:** Extensive local cache in `01_geospatial/` directory
4. **Access:** Most data is publicly available; some portals may require registration
5. **Navigation Use:** Many datasets explicitly state "not for navigation" - intended for planning/analysis only
6. **Coordination:** USACE datasets often sourced from multiple agencies (CBP, Census, etc.)

---

## 🚀 GETTING STARTED

### **For Mississippi River Barge Analysis:**
1. Start with **Waterway Networks** (local file or DS-123) for base geography
2. Add **Locks** dataset (DS-125) to identify choke points
3. Overlay **Link Tonnages** (DS-010) for commodity volumes
4. Access **LPMS** for operational performance data
5. Use **Navigation Facilities** (DS-131) for terminal/dock locations

### **For Commodity Flow Analysis:**
1. Primary: **WCSC Data Portal** - comprehensive commerce statistics
2. Secondary: **Link Tonnages** - segment-specific volumes
3. Tertiary: **NDC Library Commodity Indicators** - temporal trends
4. Supporting: **Vessel Company Summaries** - operator-level detail

### **For Real-Time Operations:**
1. **LPMS** - Current lock performance and delays
2. **NTNI** - Navigation hazards and restrictions
3. **PORTS** - Environmental conditions affecting operations
4. **AIS** - Vessel positions and movements

---

## 📄 ADDITIONAL REFERENCE DOCUMENTS

1. **PROJECT_SESSION_SUMMARY.md** - Complete project overview
2. **INDEX_OF_DOCUMENTATION.md** - Full documentation index
3. **QUICK_START_GUIDE.md** - Fast reference for common tasks
4. **chrome_bookmarks_analysis_report.txt** - Detailed bookmark analysis
5. **FGDC_Datasets_Catalog.md** - Federal Geographic Data Committee datasets

---

**Document Version:** 1.0
**Last Updated:** January 29, 2026
**Next Dataset ID Available:** DS-250
**Compilation Status:** ✅ Complete

---

*This document represents a comprehensive compilation of federal, state, and commercial data sources specifically relevant to Mississippi River inland barge transportation, national waterway systems, lock operations, commodity flows, and navigation datasets.*
