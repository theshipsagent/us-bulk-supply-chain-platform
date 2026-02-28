# USACE Port Clearance Market Study - HTML Report (REVISED)

## Overview
Interactive HTML market study report analyzing US port clearance patterns focused on **vessel types** and **trade patterns** across port regions, with dynamic charts and visualizations.

## ✅ Implementation Complete

### Key Revision: Focus Changed
**Previous Focus:** Individual vessel names as "operators"
**New Focus:** Vessel types and trade patterns across port regions

**Why the Change:**
- Individual vessel names are not relevant metrics for market analysis
- Focus shifted to analyzing vessel TYPE distribution and trade PATTERNS
- Analysis now examines how different vessel types operate across classified port regions
- Emphasis on cargo flows, regional specialization, and trade routes

---

## Generated Files

### Scripts Created (HTML Version)
1. **`market_analysis_html.py`** - Data analysis focused on vessel types and trade patterns
2. **`html_visualizations.py`** - Interactive plotly visualizations
3. **`generate_html_report.py`** - HTML report assembly with embedded charts
4. **`run_market_study_html.py`** - Main orchestrator

### Report Output
- **Location:** `G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\`
- **File:** `usace_market_study_2023_20260206_100942.html`
- **Size:** 145 KB
- **Format:** Interactive HTML with Plotly charts

---

## Report Structure

### 1. Executive Summary
- Total market statistics
- Key findings focused on vessel types and regional trade
- Market characteristics overview

### 2. Market Overview
- Total revenue: $169.1M
- Total clearances: 49,726
- Interactive metrics dashboard
- 61 vessel types across 11 regions

### 3. Vessel Type Analysis
**Focus:** Distribution and performance of different vessel types

**Interactive Charts:**
- Top 15 vessel types by revenue (bar chart)
- Cargo class distribution (treemap)
- Vessel type performance matrix (scatter plot)

**Key Findings:**
- 61 distinct vessel types
- Bulk Carrier-Supra/Ultramax leads with $26.8M
- Clear specialization by cargo type

### 4. Regional Trade Patterns
**Focus:** How trade patterns vary across port regions

**Interactive Charts:**
- Revenue by port region (bar chart)
- Coast distribution (sunburst chart)
- Regional market share comparison (radar chart)

**Key Findings:**
- 11 distinct port regions
- North Texas leads with $35.2M (20.8%)
- Clear geographic specialization

### 5. Vessel Type × Region Analysis
**Focus:** Intersection of vessel types and regional operations

**Interactive Charts:**
- Revenue heatmap: Top 10 vessel types × Top 10 regions

**Key Insights:**
- Regional vessel type preferences
- Infrastructure-driven specialization
- Trade route optimization patterns

### 6. Cargo Flows & Trade Patterns
**Focus:** Origin-destination trade lanes through US ports

**Interactive Charts:**
- Top 15 origin countries
- Top 15 destination countries
- Trade lane flows (Sankey diagram: Origin → Region → Destination)

**Key Insights:**
- Major trade lanes identified
- Regional nodes in global supply chains
- Container vs. bulk commodity routes

### 7. Grain Export Analysis
**Focus:** Strategic grain export segment

**Interactive Charts:**
- Grain shipments by region
- Grain export destinations (pie chart)
- Grain vessel types

**Statistics:**
- 409 grain shipments (0.8% of total)
- 17.4M MT exported
- $4.9M in revenue

### 8. Conclusions & Strategic Insights
- Vessel type diversity implications
- Regional specialization patterns
- Trade concentration analysis
- Infrastructure impact
- Growth opportunities

---

## Interactive Features

### Dynamic Charts (Plotly)
All charts are interactive with:
- **Hover tooltips** - detailed data on hover
- **Zoom/pan** - explore data ranges
- **Click legends** - show/hide data series
- **Export** - download charts as PNG
- **Responsive** - adapts to screen size

### Navigation
- **Sticky navigation bar** - quick section access
- **Smooth scrolling** - to section anchors
- **Visual hierarchy** - clear section organization

### Visual Design
- **Professional styling** - modern color scheme
- **Gradient headers** - eye-catching section breaks
- **Stat cards** - animated metric displays
- **Insight boxes** - highlighted key findings
- **Responsive grid** - mobile-friendly layout

---

## Key Analysis Focus Areas

### 1. Vessel Type Distribution
- **61 distinct vessel types** analyzed
- Revenue contribution by type
- Clearance frequency patterns
- Average vessel characteristics (DWT, LOA, beam, draft)

### 2. Regional Trade Patterns
- **11 port regions** classified
- Revenue and clearance distribution
- Regional vessel type preferences
- Coastal vs. inland patterns

### 3. Cargo Flows
- Origin country analysis
- Destination country analysis
- Trade lane mapping (origin → region → destination)
- Commodity group distribution

### 4. Type × Region Interactions
- Which vessel types dominate which regions
- Regional infrastructure capabilities
- Trade route optimization
- Specialization patterns

### 5. Grain Exports
- Strategic agricultural exports
- Regional concentration
- Destination markets
- Vessel type requirements

---

## Data Metrics

### Overall Market
- **Total Revenue:** $169.1M
- **Total Clearances:** 49,726
- **Average Fee:** $3,401
- **Vessel Types:** 61
- **Port Regions:** 11
- **Cargo Classes:** 20

### Top Performers
- **Top Vessel Type:** Bulk Carrier-Supra/Ultramax ($26.8M)
- **Top Region:** North Texas ($35.2M, 20.8%)
- **Top Cargo Class:** Varies by revenue metric

### Grain Segment
- **Clearances:** 409 (0.8%)
- **Tonnage:** 17.4M MT
- **Revenue:** $4.9M

---

## Usage

### Viewing the Report

#### Option 1: Direct Open
```bash
# Open in default browser
start "G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\usace_market_study_2023_20260206_100942.html"

# Or on Mac/Linux
open "path/to/usace_market_study_2023_20260206_100942.html"
```

#### Option 2: Regenerate Report
```bash
cd "G:\My Drive\LLM\task_usace_entrance_clearance\02_SCRIPTS"
python run_market_study_html.py
```

### Requirements
```python
pandas>=1.3.0
numpy>=1.21.0
plotly>=5.0.0
```

Install with:
```bash
pip install pandas numpy plotly
```

---

## Technical Implementation

### Analysis Module (`market_analysis_html.py`)

**Functions:**
1. `load_and_prepare_data()` - Load and clean CSV data
2. `calculate_market_metrics()` - Overall market statistics
3. `analyze_vessel_types()` - Vessel type revenue and characteristics
4. `analyze_regional_trade_patterns()` - Regional distribution analysis
5. `analyze_cargo_flows()` - Origin-destination trade lanes
6. `analyze_vessel_type_by_region()` - Type × region interaction
7. `analyze_grain_shipments()` - Grain export subset

### Visualization Module (`html_visualizations.py`)

**Chart Types:**
- **Bar charts** - Revenue by type/region
- **Heatmaps** - Type × region revenue matrix
- **Treemaps** - Cargo class hierarchy
- **Scatter plots** - Performance metrics
- **Sunburst charts** - Hierarchical distributions
- **Radar charts** - Multi-metric comparisons
- **Sankey diagrams** - Trade flow visualization
- **Pie charts** - Proportional distributions

All charts use **Plotly** for interactivity.

### HTML Report Generator (`generate_html_report.py`)

**Features:**
- Responsive CSS grid layout
- Embedded Plotly charts (CDN)
- Professional color scheme
- Section navigation
- Mobile-friendly design
- Print-optimized styling

---

## Comparison: PDF vs HTML Versions

| Feature | PDF Version | HTML Version |
|---------|-------------|--------------|
| **Format** | Static PDF | Interactive HTML |
| **Charts** | Matplotlib (static) | Plotly (interactive) |
| **File Size** | 304 KB | 145 KB |
| **Navigation** | Page-based | Section links |
| **Interactivity** | None | Hover, zoom, filter |
| **Focus** | Individual vessels | Vessel types & trade |
| **Sharing** | Easy (email) | Easy (web/email) |
| **Printing** | Excellent | Good |
| **Analysis Depth** | 8 sections | 8 sections |
| **Charts** | 17 static | 14 interactive |

---

## Key Insights from Analysis

### 1. Vessel Type Diversity (61 Types)
- Reflects specialized cargo requirements
- Trade route optimization
- Infrastructure constraints
- Bulk carriers dominate revenue

### 2. Regional Specialization
- North Texas: 20.8% of market
- Clear geographic advantages
- Infrastructure-driven patterns
- Trade route positioning

### 3. Trade Pattern Concentration
- Established origin-destination pairs
- Container vs. bulk commodity differentiation
- Seasonal patterns (grain exports)
- Supply chain optimization

### 4. Growth Opportunities
- Underserved vessel types
- Regional capacity expansion
- Trade lane diversification
- Infrastructure investments

---

## File Structure

```
02_SCRIPTS/
├── market_analysis_html.py         # Analysis (vessel types & trade)
├── html_visualizations.py          # Interactive Plotly charts
├── generate_html_report.py         # HTML assembly
├── run_market_study_html.py        # Main orchestrator
└── README_HTML_REPORT.md           # This file

00_DATA/
└── 00.03_REPORTS/
    ├── usace_market_study_2023_20260206_030652.pdf   # PDF version (static)
    └── usace_market_study_2023_20260206_100942.html  # HTML version (interactive)
```

---

## Future Enhancements

### Potential Additions
1. **Time-series analysis** - Multi-year trends (if 2024+ data available)
2. **Seasonal patterns** - Monthly/quarterly breakdowns
3. **Geographic maps** - US choropleth and bubble maps
4. **Commodity deep-dive** - Detailed cargo type analysis
5. **Port-level details** - Individual port performance
6. **Vessel size analysis** - DWT/LOA distribution patterns
7. **Trade route maps** - Visual flow lines
8. **Benchmarking** - YoY comparisons

### Interactive Enhancements
- Dropdown filters (region, vessel type, date range)
- Real-time data updates (if connected to database)
- User-configurable views
- Export data tables to Excel
- Annotation capabilities

---

## Success Criteria - All Met ✅

- ✅ HTML report generated successfully
- ✅ Interactive charts with Plotly
- ✅ Focus on vessel types (not individual vessels)
- ✅ Trade pattern analysis across regions
- ✅ Regional specialization visualized
- ✅ Cargo flow Sankey diagrams
- ✅ Professional responsive design
- ✅ Mobile-friendly layout
- ✅ File size: 145 KB (lightweight)
- ✅ All 8 sections with interactive content
- ✅ Clear navigation and visual hierarchy

---

## Report Generation Details

**Generated:** February 6, 2026, 10:09:42 AM
**Runtime:** ~30 seconds
**Interactive Charts:** 14 (Plotly)
**Data Points:** 49,726 clearances
**Analysis Focus:** Vessel types & trade patterns

---

## Summary

This HTML version provides a **modern, interactive approach** to market analysis, focusing on the **vessel types and trade patterns** that actually drive the port clearance market. The interactive charts allow stakeholders to explore data dynamically, while the responsive design ensures accessibility across devices.

**Key Advantage:** Viewers can interact with charts, filter data visually, and gain deeper insights through exploration rather than static presentation.

---

*Report successfully implements vessel type and trade pattern analysis with interactive HTML visualizations.*
