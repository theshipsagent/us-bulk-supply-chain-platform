# Panjiva Commodity Trends Charts - Quick Start Guide

## What You Have

**📊 Interactive HTML Presentation:** 11 professional slides with charts and data tables

**📁 File Location:**
```
G:/My Drive/LLM/project_master_reporting/Panjiva_Commodity_Trends_Charts.html
```

**📈 File Size:** 1.1 MB (all charts embedded, no external dependencies)

---

## How to View

### Method 1: Double-Click (Easiest)
1. Navigate to `G:/My Drive/LLM/project_master_reporting/`
2. Double-click `Panjiva_Commodity_Trends_Charts.html`
3. Opens automatically in your default browser

### Method 2: Right-Click (Choose Browser)
1. Right-click `Panjiva_Commodity_Trends_Charts.html`
2. Select "Open with..."
3. Choose Chrome, Edge, Firefox, or Safari

---

## Navigation Controls

| Key/Action | Function |
|---|---|
| **→ Right Arrow** | Next slide |
| **← Left Arrow** | Previous slide |
| **Space Bar** | Next slide |
| **Esc** | Slide overview (grid view) |
| **F** | Fullscreen mode |
| **S** | Speaker notes (if available) |
| **Home** | First slide |
| **End** | Last slide |
| **Click** | Advance to next slide |

---

## Slide Contents

### Slide 1: Title
- Presentation title and metadata
- Analysis date: February 24, 2026

### Slides 2-3: Year-over-Year Overview
- **Chart:** 4-panel dashboard showing total tonnage, growth rates, value, and shipments
- **Table:** Summary statistics with YoY growth percentages

### Slides 4-5: Top Commodities
- **Chart:** Horizontal bar chart + grouped comparison of top commodities
- **Table:** Detailed tonnage breakdown by commodity and year

### Slides 6-7: Commodity Growth Rates
- **Chart:** Growth rate comparison + trend lines for top 5 commodities
- **Table:** Percentage growth by period

### Slides 8-9: Port-Level Trends
- **Chart:** Top 10 ports + commodity specialization by port
- **Table:** Port tonnage summary

### Slides 10-11: Country of Origin
- **Chart:** Top 10 origin countries + commodity mix by country
- **Table:** Country tonnage summary

### Slide 12: Executive Summary
- Key findings and applications

---

## Data Highlights

**📦 Records Analyzed:** 854,870 import shipments
**📅 Time Period:** 2023-2025 (3 years)
**⚖️ Total Tonnage:** 1.35 billion tons
**🚢 Data Source:** Panjiva Phase 07 Enrichment

---

## Chart Features

✅ **Professional Design**
- Clean, modern styling
- Color-coded for easy interpretation
- Grid lines for readability
- Data labels on all bars/points

✅ **High Resolution**
- 150 DPI embedded PNG images
- Crisp text and graphics
- Suitable for printing or projection

✅ **Comprehensive**
- Multiple view types (bar, line, grouped, horizontal)
- Year-over-year comparisons
- Growth rate analysis
- Geographic breakdowns

✅ **Self-Contained**
- No internet required after initial load
- All images embedded as base64
- Reveal.js loaded from CDN

---

## Sharing & Exporting

### Share the Presentation
- **Email:** Attach the HTML file (1.1 MB)
- **Cloud:** Upload to Google Drive, Dropbox, OneDrive
- **USB:** Copy file to USB drive
- **Network:** Place on shared drive

### Export Individual Slides
- **Screenshot:** Use Windows Snipping Tool or browser screenshot
- **Print to PDF:** Use browser's Print > Save as PDF
- **Full Deck PDF:** Print entire presentation to PDF

### Extract Charts
- Right-click on any chart in the HTML
- Select "Save image as..."
- Charts are high-resolution PNGs

---

## Regeneration & Updates

### When to Regenerate
- New data becomes available
- Additional years added to dataset
- Phase 07 enrichment updated
- Filter criteria changed

### How to Regenerate
```bash
cd "G:/My Drive/LLM/project_master_reporting"
python analyze_panjiva_trends.py
```

**Runtime:** ~2-3 minutes
**Output:** Overwrites existing HTML file

---

## Presentation Tips

### For Meetings
1. Open presentation before meeting starts
2. Use **F** key for fullscreen
3. Navigate with arrow keys or click
4. Press **Esc** to show slide overview
5. Use tables slides for detailed Q&A

### For Reports
1. Print to PDF for distribution
2. Extract individual charts for Word/PowerPoint
3. Reference data tables for specific metrics
4. Cite as "Panjiva Phase 07 Analysis (2023-2025)"

### For Analysis
1. Use slide overview (Esc) to compare charts
2. Reference tables for exact values
3. Cross-check trends across multiple slides
4. Use growth rate slides for YoY comparisons

---

## Troubleshooting

### Slides Not Advancing
- Ensure JavaScript is enabled in browser
- Try refreshing the page (F5)
- Check browser console for errors (F12)

### Images Not Displaying
- Images are embedded—should always work
- If blank, file may be corrupted—regenerate
- Try different browser (Chrome recommended)

### Layout Issues
- Presentation optimized for 1400x900 resolution
- Use fullscreen mode (F) for best experience
- Zoom in/out with Ctrl+Plus/Minus if needed

### Performance Issues
- File is 1.1 MB—may load slowly on slow connections
- Once loaded, all navigation is instant
- Close other browser tabs if sluggish

---

## Technical Details

**Framework:** Reveal.js 4.5.0
**Charts:** Matplotlib + Seaborn styling
**Data Processing:** Pandas
**Image Format:** Base64-encoded PNG
**Browser Compatibility:** Chrome, Edge, Firefox, Safari (latest versions)

---

## Support Files

| File | Location | Purpose |
|---|---|---|
| **Presentation** | `Panjiva_Commodity_Trends_Charts.html` | Main slides |
| **Analysis Script** | `analyze_panjiva_trends.py` | Regeneration script |
| **Summary** | `PANJIVA_ANALYSIS_SUMMARY.md` | Detailed documentation |
| **Quick Start** | `PANJIVA_CHARTS_QUICKSTART.md` | This guide |
| **Source Data** | `02_TOOLSETS/vessel_intelligence/.../phase_07_output.csv` | Raw data |

---

## Next Steps

1. **View the presentation** → Double-click the HTML file
2. **Review the summary** → Read `PANJIVA_ANALYSIS_SUMMARY.md` for full context
3. **Share with stakeholders** → Email or upload to shared location
4. **Use in reporting** → Extract charts for reports/presentations
5. **Regenerate as needed** → Run Python script when data updates

---

**Questions?** Check `PANJIVA_ANALYSIS_SUMMARY.md` for detailed documentation.

**Ready to view?** → Double-click `Panjiva_Commodity_Trends_Charts.html`

---

*Last Updated: February 24, 2026*
