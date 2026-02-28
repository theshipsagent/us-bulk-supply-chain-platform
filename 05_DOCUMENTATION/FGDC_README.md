# FGDC (Federal Geographic Data Committee) Datasets Collection

**Date Collected:** January 16, 2026
**Source:** https://catalog.data.gov/dataset/?organization=fgdc-gov
**Total Datasets:** 47

---

## What's Included

This collection contains **ALL 47 datasets** from the Federal Geographic Data Committee (FGDC) organization on data.gov, systematically extracted and documented.

---

## Files in This Collection

### 1. **fgdc_datasets_complete.json** (373.7 KB)
Complete machine-readable dataset catalog in JSON format.

**Contents:**
- All 47 datasets with full metadata
- Title, description, organization
- Publisher information
- Creation and modification dates
- Complete list of all resources (URLs and formats)
- Tags and keywords
- License information

**Use for:**
- Automated processing
- Database imports
- API integration
- Data analysis scripts

---

### 2. **FGDC_Datasets_Catalog.md** (75.3 KB)
Comprehensive human-readable catalog with detailed information for each dataset.

**Contents:**
For each of 47 datasets:
- Dataset name and description
- Publisher and organization
- Creation and last update dates
- All available data formats
- Category/topic tags
- Direct download links
- Dataset URL on data.gov

**Use for:**
- Browsing and discovery
- Quick reference
- Understanding dataset contents
- Finding download links

---

### 3. **FGDC_Summary_Report.md** (8.8 KB)
Executive summary with statistics and analysis.

**Contents:**
- Overview of the collection
- Key findings and statistics
- Major dataset highlights
- Format availability analysis
- Use cases and recommendations
- Data governance information
- Contact information

**Use for:**
- Understanding the collection scope
- Getting an overview of available data
- Planning data usage strategies

---

### 4. **FGDC_README.md** (This file)
Quick start guide and file descriptions.

---

### 5. **fetch_fgdc_datasets.py**
Python script used to extract all datasets from data.gov API.

---

## Dataset Categories

### Transportation Infrastructure (24 datasets)
- **Bridges:** National Bridge Inventory (624,000+ bridges)
- **Aviation:** Aviation Facilities, Runways
- **Rail:** North American Rail Network Lines & Nodes, Rail Mileposts
- **Waterways:** Navigable Waterway Networks, Locks, Navigation Facilities
- **Transit:** National Transit Map Routes & Stops
- **Freight:** Intermodal Freight Facilities (Air, Rail, Marine, Pipeline)

### NGDA Program Documentation (15 datasets)
- NGDA Portfolio Lists
- Strategic Plans
- Implementation Plans
- Standards Documentation

### Working Groups & Standards (8 datasets)
- Federal Trail GIS Data Schema
- Federal Lands Roads Working Group
- U.S. Road Specification Working Group
- Standards and Specifications

---

## Data Formats Available

| Format | Datasets | Description |
|--------|----------|-------------|
| **CSV** | 23 | Comma-separated values (spreadsheet compatible) |
| **GeoJSON** | 23 | Web-friendly geospatial format |
| **Shapefile (ZIP)** | 23 | Standard GIS format |
| **KML** | 23 | Google Earth compatible |
| **Excel (XLS)** | 22 | Microsoft Excel format |
| **GeoPackage (GPKG)** | 22 | Modern open geospatial format |
| **Geodatabase (GDB)** | 22 | ESRI format |
| **ArcGIS REST API** | 24 | Live web service access |
| **JSON** | 46 | Metadata in JSON format |
| **XML** | 46 | Metadata in XML format |

---

## Quick Start Guide

### For Data Analysts
1. Open `FGDC_Datasets_Catalog.md` to browse available datasets
2. Find datasets of interest
3. Download CSV or Excel formats from the provided links
4. Import into your analysis tools (Excel, Python, R, etc.)

### For GIS Professionals
1. Review `FGDC_Datasets_Catalog.md` for geospatial datasets
2. Download Shapefile (ZIP), GeoJSON, or GeoPackage formats
3. Import into QGIS, ArcGIS, or other GIS software
4. Or use the ArcGIS REST API endpoints for live access

### For Developers
1. Use `fgdc_datasets_complete.json` for programmatic access
2. Parse JSON to extract dataset information
3. Automate downloads or integrate with APIs
4. Build custom applications or visualizations

### For Researchers
1. Start with `FGDC_Summary_Report.md` for overview
2. Review `FGDC_Datasets_Catalog.md` for detailed dataset information
3. Access raw data in CSV/Excel formats
4. Reference proper attribution and licenses

---

## Featured Datasets

### National Bridge Inventory
- **624,000+ bridges** across the United States
- Location, description, classification, condition
- **Updated:** December 8, 2025
- **Source:** Federal Highway Administration (FHWA)
- **Formats:** CSV, Shapefile, GeoJSON, KML, Excel

### North American Rail Network
- Comprehensive rail lines and nodes
- Created 2016, updated September 30, 2025
- **Source:** Federal Railroad Administration (FRA)
- **Formats:** All major GIS formats

### Aviation Facilities
- All official and operational aerodromes
- Physical and operational characteristics
- **Updated every 28 days**
- **Source:** Federal Aviation Administration (FAA)

### Waterway Infrastructure
- Navigable waterways, locks, facilities
- **Source:** U.S. Army Corps of Engineers (USACE)
- Critical for shipping and transportation analysis

---

## Data Quality

### Completeness
- **100% extraction rate:** All 47 datasets captured
- All datasets have complete metadata
- All resource links verified and included

### Metadata Standards
All datasets conform to:
- ISO 19115/19139 (Geographic Information Metadata)
- FGDC CSDGM (Content Standard for Digital Geospatial Metadata)
- INSPIRE (EU Metadata Directive)
- DCAT (Data Catalog Vocabulary)

### Update Frequency
- **High-frequency:** Aviation data (every 28 days)
- **Periodic:** Transportation infrastructure (quarterly/annually)
- **Ad-hoc:** Documentation and standards

---

## License & Usage

**License:** US Public Domain (us-pd)
- All datasets are intended for public access and use
- No copyright restrictions
- Free to use for any purpose
- No registration required

---

## Contact & Support

### FGDC Contact
- **Email:** ngdateam@fgdc.gov
- **Website:** https://www.fgdc.gov/

### NTAD (Geospatial Questions)
- **Email:** NTAD@dot.gov

### Data.gov Catalog
- **URL:** https://catalog.data.gov/dataset/?organization=fgdc-gov
- **API:** https://catalog.data.gov/api/3/action/package_search?fq=organization:fgdc-gov

---

## Additional Information

### Use Cases
- **Transportation Planning:** Infrastructure assessment, network analysis
- **Emergency Management:** Hazard exposure, critical infrastructure protection
- **Research:** Transportation statistics, commodity flows, trend analysis
- **GIS Mapping:** Basemap layers, infrastructure overlays, spatial analysis

### Organizations Involved
- Federal Geographic Data Committee (FGDC)
- Bureau of Transportation Statistics (BTS)
- Federal Highway Administration (FHWA)
- Federal Aviation Administration (FAA)
- Federal Railroad Administration (FRA)
- U.S. Army Corps of Engineers (USACE)

---

## How This Collection Was Created

1. **API Access:** Used data.gov CKAN API to systematically query all FGDC datasets
2. **Data Extraction:** Python script (`fetch_fgdc_datasets.py`) extracted all metadata
3. **Verification:** Confirmed 47/47 datasets with 100% completeness
4. **Documentation:** Generated JSON, Markdown catalog, and summary reports
5. **Quality Check:** Verified all links, formats, and metadata

---

## Next Steps

1. **Explore** the catalog to find datasets relevant to your needs
2. **Download** data in your preferred format
3. **Analyze** using your favorite tools
4. **Share** insights with proper attribution
5. **Monitor** data.gov for updates to datasets

---

## Version History

- **v1.0** (January 16, 2026): Initial collection of all 47 FGDC datasets

---

## Questions or Issues?

For questions about:
- **Dataset contents:** Contact the publisher listed in each dataset
- **Technical issues:** Contact data.gov support
- **This collection:** Refer to the contact information provided in your original request

---

**Happy Data Exploring!**
