# Panjiva Import Manifest Analysis - Year-over-Year Commodity Trends

## Executive Summary

**Analysis Date:** February 24, 2026
**Data Source:** Panjiva Phase 07 Enrichment Output
**File Location:** `G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/vessel_intelligence/src/pipeline/phase_07_enrichment/phase_07_output.csv`

**Output File:** `G:/My Drive/LLM/project_master_reporting/Panjiva_Commodity_Trends_Charts.html`
**File Size:** 1.1 MB
**Format:** HTML5 with Reveal.js presentation framework

---

## Dataset Overview

- **Total Records Analyzed:** 854,870 import shipments
- **Time Period:** 2023-2025 (3 years)
- **Total Tonnage:** 1,351,610,685 tons (1.35 billion tons)
- **Scope:** US import flows excluding white noise/spurious records

---

## Analysis Components

### 1. Year-over-Year Total Volume Overview
**Slides 1-2**

**Visualizations:**
- Total tonnage by year (bar chart)
- YoY growth rates for tonnage and value (grouped bar chart)
- Total import value by year (bar chart)
- Shipment count by year (bar chart)

**Data Table Includes:**
- Total tonnage (million tons)
- Total value (billion USD)
- Shipment count (thousands)
- Tonnage growth rate (%)
- Value growth rate (%)

**Key Metrics:**
- Multi-year trend comparison
- Growth rate analysis
- Volume vs. value dynamics
- Shipment frequency trends

---

### 2. Top 10 Commodities by Import Volume
**Slides 3-4**

**Visualizations:**
- Horizontal stacked bar chart showing all years for top 10 commodities
- Grouped bar chart comparing top 5 commodities year-over-year

**Data Table Includes:**
- Commodity name
- Tonnage by year (2023, 2024, 2025)
- Total tonnage across all years

**Analysis Focus:**
- Dominant commodity categories
- Shifts in commodity mix over time
- Relative market share by commodity
- Commodity concentration patterns

---

### 3. Commodity Growth Rate Analysis
**Slides 5-6**

**Visualizations:**
- Horizontal bar chart showing growth rates by period (2023-2024, 2024-2025)
- Line chart showing trend lines for top 5 commodities
- Color-coded positive/negative growth indicators

**Data Table Includes:**
- Commodity name
- Growth rate 2023-2024 (%)
- Growth rate 2024-2025 (%)

**Analysis Focus:**
- Fastest-growing commodity categories
- Declining commodity categories
- Momentum and volatility indicators
- Market expansion/contraction patterns

---

### 4. Port-Level Import Trends
**Slides 7-8**

**Visualizations:**
- Top 10 ports by import volume (grouped horizontal bar chart)
- Top commodities by top 3 ports (grouped vertical bar chart)

**Data Table Includes:**
- Port name
- Tonnage by year (2023, 2024, 2025)
- Total tonnage

**Analysis Focus:**
- Critical gateway ports for US imports
- Port-commodity specialization patterns
- Geographic distribution of import infrastructure
- Port capacity utilization trends

---

### 5. Country of Origin Analysis
**Slides 9-10**

**Visualizations:**
- Top 10 origin countries by import volume (grouped horizontal bar chart)
- Top commodities by top 3 origin countries (grouped vertical bar chart)

**Data Table Includes:**
- Country name
- Tonnage by year (2023, 2024, 2025)
- Total tonnage

**Analysis Focus:**
- Global supply chain dependencies
- Country-commodity specialization
- Trade relationship evolution
- Geographic sourcing patterns

---

## Technical Specifications

### Chart Design Standards
- **Style:** Professional with grid lines for readability
- **Colors:** 10-color palette for consistency
- **Labels:** Data point labels on all major charts
- **Fonts:** Clear, bold labels with hierarchical sizing
- **Format:** High-resolution PNG embedded as base64

### Data Processing
- **Library:** Pandas for data manipulation
- **Visualization:** Matplotlib with seaborn styling
- **Memory Optimization:** Selective column loading for 5.4M row dataset
- **Data Cleaning:** Filtered white noise, handled missing values

### Presentation Framework
- **Framework:** Reveal.js 4.5.0
- **Theme:** White (professional)
- **Dimensions:** 1400x900 (16:9 ratio optimized)
- **Navigation:** Arrow keys, click, or touch
- **Features:** Slide numbers, progress bar, keyboard shortcuts

---

## Key Applications

1. **Strategic Market Intelligence**
   - Identify emerging commodity trends
   - Track market share shifts
   - Monitor competitive dynamics

2. **Port Infrastructure Planning**
   - Capacity requirements forecasting
   - Commodity specialization analysis
   - Gateway port prioritization

3. **Trade Policy Impact Assessment**
   - Country-of-origin dependency analysis
   - Tariff impact modeling
   - Supply chain risk assessment

4. **Competitive Landscape Monitoring**
   - Market concentration analysis
   - Growth opportunity identification
   - Commodity vertical prioritization

---

## Data Quality Notes

- **White Noise Filtering:** Applied to exclude spurious records
- **Tonnage Data:** Direct from Panjiva manifest records
- **Classification:** Phase 07 enrichment includes full commodity taxonomy
- **Geographic Standardization:** Port names consolidated for consistency
- **Country Attribution:** Based on "Country of Origin (F)" field

---

## Usage Instructions

### Opening the Presentation
1. Navigate to: `G:/My Drive/LLM/project_master_reporting/`
2. Double-click `Panjiva_Commodity_Trends_Charts.html`
3. Opens in default web browser

### Navigation
- **Arrow Keys:** Left/Right to navigate slides
- **Space Bar:** Next slide
- **Escape:** Slide overview mode
- **F:** Fullscreen mode

### Slide Structure
- **11 Total Slides:**
  - 1 title slide
  - 10 content slides (5 chart slides + 5 data table slides)
  - 1 executive summary slide

---

## File Locations

### Input Data
```
G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/vessel_intelligence/src/pipeline/phase_07_enrichment/phase_07_output.csv
```

### Analysis Script
```
G:/My Drive/LLM/project_master_reporting/analyze_panjiva_trends.py
```

### Output Presentation
```
G:/My Drive/LLM/project_master_reporting/Panjiva_Commodity_Trends_Charts.html
```

### This Summary
```
G:/My Drive/LLM/project_master_reporting/PANJIVA_ANALYSIS_SUMMARY.md
```

---

## Regeneration Instructions

To regenerate the analysis with updated data:

```bash
cd "G:/My Drive/LLM/project_master_reporting"
python analyze_panjiva_trends.py
```

**Runtime:** ~2-3 minutes for 854K records
**Requirements:** pandas, matplotlib, numpy

---

## Future Enhancements

### Potential Additions
1. **Quarterly Breakdown:** Add quarterly trends within each year
2. **Vessel Type Analysis:** Break down by vessel types (tanker, bulk carrier, container, etc.)
3. **Value per Ton Analysis:** Track commodity pricing trends
4. **Regional Analysis:** Port region clustering (Gulf, East Coast, West Coast)
5. **Shipper/Consignee Analysis:** Top importers and exporters
6. **HS Code Deep Dive:** 6-digit HS code level analysis
7. **Seasonal Patterns:** Month-over-month seasonality analysis

### Interactive Features
1. **Drill-Down Capability:** Click charts to filter data
2. **Export Buttons:** Download charts as PNG/PDF
3. **Data Export:** Download tables as CSV/Excel
4. **Filter Controls:** Toggle years, commodities, ports dynamically

---

## Contact & Credits

**Analysis Platform:** US Bulk Supply Chain Reporting Platform
**Project Root:** `G:/My Drive/LLM/project_master_reporting`
**Data Pipeline:** Vessel Intelligence Toolset (Phase 07 Enrichment)
**Visualization:** Python + Matplotlib + Reveal.js
**Analysis Date:** February 24, 2026

---

## Appendix: Chart Types Used

| Chart Type | Use Case | Slides |
|---|---|---|
| Bar Chart | Year comparison, absolute values | 1, 3, 7, 9 |
| Grouped Bar Chart | Multi-series comparison | 1, 3, 5, 7, 9 |
| Horizontal Bar Chart | Ranking display | 3, 5, 7, 9 |
| Line Chart | Trend visualization | 5 |
| Data Table | Detailed statistics | 2, 4, 6, 8, 10 |

---

**End of Summary**
