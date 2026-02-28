# ArcGIS Online Story Map Implementation Guide
## Florida Cement Market Intelligence

---

## Overview

This guide provides instructions for creating interactive maps and Story Maps using the GeoJSON layers created for the Florida Cement Market Intelligence Report.

---

## GeoJSON Layer Package

### Layer Inventory

| File | Type | Records | Purpose |
|------|------|---------|---------|
| `cement_plants_florida_gulf.geojson` | Points | 13 | Cement plants with capacity data |
| `import_terminals_florida.geojson` | Points | 7 | Florida port terminals |
| `caribbean_markets.geojson` | Points | 19 | Export market opportunities |
| `shipping_routes.geojson` | Lines | 9 | Trade routes |
| `import_origins.geojson` | Points | 10 | Source country locations |
| `us_states_cement.geojson` | Points | 12 | State-level summary data |

---

## Color Scheme (Green/Blue Sustainability Palette)

### Primary Colors (Green)
- `#1B5E20` - Dark Green (primary-dark)
- `#2E7D32` - Green (primary)
- `#4CAF50` - Light Green (primary-light)
- `#81C784` - Lighter Green

### Secondary Colors (Blue)
- `#0D47A1` - Dark Blue (secondary-dark)
- `#1976D2` - Blue (secondary)
- `#42A5F5` - Light Blue

### Accent Colors (Teal)
- `#00ACC1` - Cyan (accent)
- `#00897B` - Teal (accent-dark)

### Status Colors
- `#FF5722` - Warning/Competitor (orange-red)

---

## Uploading to ArcGIS Online

### Step 1: Add GeoJSON as Hosted Feature Layer

1. Log in to ArcGIS Online
2. Go to **Content** > **New Item** > **Your device**
3. Select a `.geojson` file
4. Choose **Add [filename] and create a hosted feature layer**
5. Enter title and tags
6. Click **Save**

### Step 2: Style Layers

**For Point Layers (Plants, Terminals, Markets):**

1. Open the layer in Map Viewer
2. Click **Styles** (paint brush icon)
3. Choose **Types (unique symbols)** or **Counts and Amounts (size)**
4. For capacity-based sizing:
   - Field: `capacity_mt` or `symbol_size`
   - Size range: 8-40 px
5. For opportunity scoring:
   - Field: `opportunity_score`
   - Use color ramp: Green (#1B5E20) to Light (#E8F5E9)

**For Line Layers (Shipping Routes):**

1. Open in Map Viewer
2. Click **Styles**
3. Choose **Types (unique symbols)** based on `route_type`
4. Set colors:
   - Import routes: `#0D47A1` (blue)
   - Export routes: `#1B5E20` (green)
5. Use `line_weight` field for width proportional to volume

---

## Symbology Recommendations

### Cement Plants Layer
```
Symbol: Circle
Size: Based on capacity_mt (proportional)
Color: By owner or state
  - Florida plants: #2E7D32 (green)
  - Texas plants: #0D47A1 (blue)
  - Alabama plants: #1976D2 (light blue)
Outline: White, 1px
```

### Import Terminals Layer
```
Symbol: Square or Diamond
Size: Based on volume_mt (proportional)
Color: #00ACC1 (teal)
Highlight Port Redwing (new): #2E7D32 (green)
```

### Caribbean Markets Layer
```
Symbol: Circle
Size: Based on opportunity_score
Color Ramp by opportunity_label:
  - VERY HIGH: #1B5E20
  - HIGH: #2E7D32
  - MODERATE: #4CAF50
  - LOW: #81C784
  - COMPETITOR: #FF5722
```

### Shipping Routes Layer
```
Symbol: Solid line
Width: Based on line_weight (2-8 px)
Color by route_type:
  - Import: #0D47A1 (blue)
  - Export: #1B5E20 (green)
Arrow: Add at endpoint for direction
```

---

## Pop-up Configuration

### Cement Plants Pop-up
```html
<b>{name}</b><br>
Owner: {owner}<br>
Location: {city}, {state}<br>
Capacity: {capacity_label}<br>
Products: {products}<br>
Status: {status}
```

### Caribbean Markets Pop-up
```html
<b>{name}</b><br>
Opportunity: <b>{opportunity_label}</b><br>
Import Dependency: {import_dependency}%<br>
Transit from Tampa: {transit_days_tampa} days<br>
Products: {products}<br>
<i>{key_driver}</i>
```

### Import Origins Pop-up
```html
<b>{name}</b><br>
Volume: {volume_label} ({share_label} market share)<br>
Tariff: {tariff_rate}<br>
YoY Change: {yoy_change}<br>
Key Suppliers: {key_suppliers}
```

---

## Creating a Story Map

### Recommended Structure

**1. Cover Page**
- Title: "Florida Cement Market Intelligence"
- Subtitle: "Tampa Bay Region | Supply, Demand & Export Opportunities"
- Background: Map of Florida Gulf region

**2. Executive Summary (Sidecar)**
- Key statistics as infographics
- Market positioning statement

**3. Supply Analysis (Map Tour)**
- Florida cement plants with capacity
- Tampa area terminals
- Zoom to each facility with details

**4. Import Analysis (Express Map)**
- Global map showing import origins
- Shipping routes overlay
- Volume-weighted flows

**5. Export Opportunities (Map Tour)**
- Caribbean and Central America markets
- Color by opportunity score
- Transit times from Tampa

**6. Market Segments (Slideshow)**
- Customer breakdown charts
- Gray vs white cement segments

**7. Conclusions (Sidecar)**
- Strategic recommendations
- Call to action

---

## Express Map Configurations

### Map 1: Florida Supply Infrastructure
```
Layers:
1. cement_plants_florida_gulf (points, capacity-sized)
2. import_terminals_florida (points, volume-sized)

Extent: Florida peninsula
Basemap: Light Gray Canvas or Navigation
```

### Map 2: US Import Origins
```
Layers:
1. import_origins (points, volume-sized)
2. shipping_routes (lines, import routes only)

Extent: World (Atlantic focus)
Basemap: Oceans
```

### Map 3: Caribbean Export Opportunities
```
Layers:
1. caribbean_markets (points, opportunity-colored)
2. shipping_routes (lines, export routes only)

Extent: Caribbean basin
Basemap: Navigation (Night) for contrast
```

### Map 4: Full Trade Network
```
Layers:
1. import_origins
2. cement_plants_florida_gulf
3. import_terminals_florida
4. caribbean_markets
5. shipping_routes (all)

Extent: Americas / Atlantic
Basemap: Light Gray Canvas
```

---

## Heat Map Configuration

For **caribbean_markets** layer as heat map:

1. In Map Viewer, add the layer
2. Click **Styles**
3. Choose **Heat Map**
4. Field: `opportunity_score`
5. Adjust:
   - Radius: 50-75 miles
   - Intensity: Medium
   - Color ramp: Green (#1B5E20 to #E8F5E9)

---

## Web App Builder Option

If preferred over Story Maps, create a Web App with:

1. **Dashboard** template for analytics view
2. Widgets:
   - Legend
   - Layer List (toggle layers)
   - Chart (from layer attributes)
   - Filter (by state, opportunity level)
   - Bookmark (preset views)

---

## File Locations

```
G:\My Drive\LLM\project_cement\
├── geospatial\
│   ├── cement_plants_florida_gulf.geojson
│   ├── import_terminals_florida.geojson
│   ├── caribbean_markets.geojson
│   ├── shipping_routes.geojson
│   ├── import_origins.geojson
│   └── us_states_cement.geojson
├── reports\
│   ├── CEMENT_MARKET_INTELLIGENCE_REPORT.html
│   └── STORYMAP_GUIDE.md
└── drafts\
    └── FLORIDA_CEMENT_MARKET_REPORT.md
```

---

## Sharing Settings

For distribution to external parties:

1. Set layer sharing to **Public** or **Organization**
2. In Story Map settings:
   - Enable **Publicly accessible**
   - Disable editing
3. Copy share URL for distribution
4. Optional: Enable **Embed** for website integration

---

## Notes

- All GeoJSON files use WGS84 (EPSG:4326) projection
- Coordinates are [longitude, latitude] format
- Each feature includes styling hints in properties (`color`, `symbol_size`)
- Properties are ready for pop-up templates

---

**Created:** December 2025
**Format:** ArcGIS Online compatible GeoJSON
