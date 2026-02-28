# FGDC Datasets Collection - Summary Report

**Organization:** Federal Geographic Data Committee (FGDC)
**Source:** https://catalog.data.gov/dataset/?organization=fgdc-gov
**Collection Date:** January 16, 2026
**Total Datasets:** 47

---

## Overview

This report documents the complete collection of 47 datasets from the Federal Geographic Data Committee (FGDC) available on data.gov. The FGDC promotes the coordinated development, use, sharing, and dissemination of geospatial data on a national basis.

## Key Findings

### Dataset Categories

The FGDC datasets primarily fall into these categories:

1. **Transportation Infrastructure (24 datasets)**
   - National Bridge Inventory
   - Aviation Facilities and Runways
   - Rail Networks (North American Rail Network Lines & Nodes)
   - Waterway Infrastructure (Navigable Waterways, Locks, Navigation Facilities)
   - Transit Networks (National Transit Map Routes & Stops)
   - Intermodal Freight Facilities

2. **National Geospatial Data Assets (NGDA) Documentation (15 datasets)**
   - NGDA Portfolio Lists and Overview
   - Standards and Implementation Plans
   - Strategic Plans and Communications

3. **Working Groups and Standards (8 datasets)**
   - Federal Trail GIS Data Schema
   - Federal Lands Roads Working Group
   - U.S. Road Specification Working Group
   - Passenger Travel Working Group

### Data Format Availability

All datasets provide metadata in multiple standard formats:

| Format | Number of Datasets |
|--------|-------------------|
| HTML | 46 |
| JSON | 46 |
| RSS | 46 |
| XML | 46 |
| text/json | 46 |
| ArcGIS GeoServices REST API | 24 |
| CSV | 23 |
| GeoJSON | 23 |
| KML | 23 |
| ZIP (Shapefiles) | 23 |
| Excel (XLS) | 22 |
| GeoPackage (GPKG) | 22 |
| Geodatabase (GDB) | 22 |
| TEXT | 22 |

### Update Frequency

- **High Frequency (Every 28 days):** Aviation Facilities, Runways
- **Periodic Updates:** Waterway data, Rail networks
- **Annual/Ad-hoc:** Strategic plans, documentation
- **As of June 2025:** National Bridge Inventory

### Geographic Coverage

Most transportation datasets cover:
- All 50 U.S. States
- U.S. Territories
- Some include cross-border data (North American coverage)

---

## Major Datasets Highlights

### 1. National Bridge Inventory
- **624,000+ bridges** across the United States
- Includes Interstate, State, and local roads
- **Formats:** CSV, Shapefile, GeoJSON, KML, Excel, GeoPackage
- **Last Updated:** December 8, 2025
- **Source:** Federal Highway Administration (FHWA)

### 2. North American Rail Network
- Comprehensive rail lines and nodes database
- Created in 2016, updated September 30, 2025
- **Source:** Federal Railroad Administration (FRA)
- Part of National Transportation Atlas Database (NTAD)

### 3. Aviation Facilities & Runways
- All official and operational aerodromes
- Physical and operational characteristics
- **Updated every 28 days**
- **Source:** Federal Aviation Administration (FAA)

### 4. National Transit Map
- Transit routes and stops nationwide
- Compiled September 2, 2025
- **Source:** Bureau of Transportation Statistics (BTS)

### 5. Waterway Infrastructure
- Navigable waterway networks (lines and nodes)
- Waterway locks with annual statistics
- Navigation facilities
- **Source:** U.S. Army Corps of Engineers (USACE)

### 6. Intermodal Freight Facilities
- Air-to-Truck facilities
- Rail TOFC/COFC terminals
- Marine Roll-on/Roll-off facilities
- Pipeline terminals
- **Source:** Bureau of Transportation Statistics (BTS)

---

## Special Collections

### BETA - Hazard Exposure Series
Three experimental datasets analyzing hazard exposure for:
1. Select North American Rail Network Lines
2. Primary Airport Parcels
3. National Highway System and Bridges
4. Principal Ports

These datasets integrate transportation infrastructure with hazard analysis.

### National Geospatial Data Assets (NGDA) Program
Multiple datasets documenting the NGDA program:
- Portfolio dataset lists
- Theme strategic plans
- Implementation plans
- Standards and specifications
- Working group activities

---

## Data Access Methods

### Primary Access
- **Data.gov Catalog:** https://catalog.data.gov/dataset/?organization=fgdc-gov
- **CKAN API:** https://catalog.data.gov/api/3/action/package_search?fq=organization:fgdc-gov

### ArcGIS Hub
Many datasets are hosted on:
- **NGDA Transportation GeoPlatform:** https://ngda-transportation-geoplatform.hub.arcgis.com/

### Direct Downloads
- CSV, Excel formats for tabular data
- Shapefiles, GeoJSON, KML for GIS applications
- GeoPackage and File Geodatabase for advanced GIS

---

## Data Quality & Standards

### Metadata Standards
All datasets provide metadata in multiple international standards:
- **ISO 19115** - Geographic Information Metadata
- **ISO 19139** - XML Schema Implementation
- **FGDC CSDGM** - Content Standard for Digital Geospatial Metadata
- **INSPIRE** - EU Metadata Directive
- **DCAT** - Data Catalog Vocabulary (1.1, 2.0.1, 2.1.1, 3.0.0)

### Coordinate Systems
Datasets use standard coordinate reference systems appropriate for U.S. national coverage.

---

## Use Cases

### Transportation Planning
- Infrastructure assessment
- Network connectivity analysis
- Freight routing optimization
- Multi-modal transportation planning

### Emergency Management
- Hazard exposure assessment
- Critical infrastructure protection
- Evacuation route planning

### Research & Analysis
- Transportation statistics
- Commodity flow studies
- Infrastructure condition monitoring
- Historical trend analysis

### GIS & Mapping
- Basemap layers
- Infrastructure overlays
- Spatial analysis
- Custom map production

---

## Data Governance

### Organizations Involved
- **Federal Geographic Data Committee (FGDC)** - Coordinating organization
- **Bureau of Transportation Statistics (BTS)** - Primary data provider
- **Federal Highway Administration (FHWA)**
- **Federal Aviation Administration (FAA)**
- **Federal Railroad Administration (FRA)**
- **U.S. Army Corps of Engineers (USACE)**

### Contact Information
- **Email:** ngdateam@fgdc.gov
- **NTAD Geospatial Questions:** NTAD@dot.gov

---

## Files Generated

This collection includes:

1. **fgdc_datasets_complete.json** (374 KB)
   - Complete structured data for all 47 datasets
   - Includes all resources, formats, metadata
   - Machine-readable format for automated processing

2. **FGDC_Datasets_Catalog.md** (76 KB)
   - Human-readable catalog
   - Detailed information for each dataset
   - Clickable links to all resources

3. **FGDC_Summary_Report.md** (This file)
   - Overview and analysis
   - Key statistics and findings
   - Use case guidance

---

## Tags & Keywords

All datasets are tagged with:
- **fgdc** - Federal Geographic Data Committee
- **gda** - Geospatial Data Asset
- **ngda** - National Geospatial Data Asset

Additional specific tags relate to transportation modes, infrastructure types, and geographic regions.

---

## License & Usage

**License:** US Public Domain (us-pd)
- All datasets are intended for public access and use
- No copyright restrictions
- Free to use for any purpose

---

## Recommendations for Data Users

1. **For Transportation Analysts:** Focus on the comprehensive transportation infrastructure datasets (bridges, aviation, rail, waterways)

2. **For GIS Professionals:** Utilize the multiple format options (Shapefile, GeoJSON, GeoPackage) for integration into GIS platforms

3. **For Researchers:** Access the raw CSV and Excel formats for statistical analysis

4. **For API Users:** Leverage the ArcGIS GeoServices REST API for dynamic data access

5. **For Standards Development:** Review the NGDA documentation and working group materials

---

## Updates & Maintenance

- **High-frequency datasets** (aviation) are updated every 28 days
- **Infrastructure datasets** are updated periodically or annually
- **Documentation** is updated as standards and plans evolve
- Monitor the data.gov catalog for update notifications

---

## Conclusion

The FGDC dataset collection represents a comprehensive resource for U.S. transportation infrastructure and geospatial data standards. With 47 datasets covering bridges, aviation, rail, waterways, and transit systems, plus extensive documentation on national geospatial standards, this collection serves as a critical resource for transportation planning, infrastructure management, emergency response, and research.

All datasets are available in multiple formats, conform to international metadata standards, and are freely accessible to the public.

---

**For more information:**
- Visit: https://www.fgdc.gov/
- Email: ngdateam@fgdc.gov
- Catalog: https://catalog.data.gov/dataset/?organization=fgdc-gov
