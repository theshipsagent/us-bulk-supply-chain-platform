# Historical Port Agency Fee Research - Download Instructions

**Date:** February 6, 2026

This document provides direct download links and instructions for accessing identified historical sources.

---

## IMMEDIATE DOWNLOADS (Free Access)

### 1. "Dues and Charges on Shipping in Foreign Ports" (1910)

**Source:** Internet Archive
**Author:** G.D. Urquhart, British Board of Trade
**Size:** 166.5 MB (1,665 pages)
**Relevance:** Primary source for 1910-era port charges including agency fees

**Direct Download Link:**
https://archive.org/download/dueschargesonsh00urqugoog/dueschargesonsh00urqugoog.pdf

**Alternative formats:**
- https://archive.org/details/dueschargesonsh00urqugoog (main page with multiple formats)
- Full text search available on Internet Archive page

**Expected Content:**
- Port-by-port breakdown of charges worldwide
- Agency fees, pilotage, towage, wharfage rates
- British perspective but covers US ports
- Benchmark for pre-WWI agency compensation

**Action:** Download PDF and search for:
- "Agent" or "ship agent" or "broker"
- "Commission" or "fee"
- US port names (New York, Baltimore, Norfolk, etc.)

---

### 2. Federal Maritime Board Annual Reports (1951-1961)

**Source:** Federal Maritime Commission Digital Library
**Base URL:** https://www.fmc.gov/annual-reports/

**Individual Report Links:**

**1951 Report** (4.7 MB, 112 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1951-Annual-Report.pdf

**1952 Report** (3.8 MB, 96 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1952-Annual-Report.pdf

**1953 Report** (3.2 MB, 88 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1953-Annual-Report.pdf

**1954 Report** (3.5 MB, 92 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1954-Annual-Report.pdf

**1955 Report** (3.1 MB, 84 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1955-Annual-Report.pdf

**1956 Report** (3.4 MB, 90 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1956-Annual-Report.pdf

**1957 Report** (3.6 MB, 94 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1957-Annual-Report.pdf

**1958 Report** (2.8 MB, 76 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1958-Annual-Report.pdf

**1959 Report** (3.0 MB, 82 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1959-Annual-Report.pdf

**1960 Report** (3.3 MB, 88 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1960-Annual-Report.pdf

**1961 Report** (2.3 MB, 68 pages)
https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1961-Annual-Report.pdf

**Expected Content:**
- Rate case decisions
- Conference agreement reviews
- Industry cost studies
- Shipping statistics
- Regulatory actions on tariffs

**Action:** Download all 11 reports and search for:
- "Agency" or "agent"
- "Port charges" or "port costs"
- "Disbursement"
- "Service fees"
- Any cost/rate tables

---

### 3. Research Papers - Freight Rate History

#### A. Dallas Federal Reserve - "From Sail to Steam" (2020)

**Citation:** Jacks, David S. and Martin Stuermer (2020). "From Sail to Steam: The Impact of the Shipping Container on Global Trade."

**Direct Download Link:**
https://www.dallasfed.org/-/media/documents/research/papers/2020/wp2008.pdf

**Size:** ~2 MB, 50+ pages
**Relevance:** Historical freight rates 1850-2020, includes dry bulk indices

**Note:** If PDF doesn't open in browser, right-click and "Save link as..."

**Alternative Access:**
- Federal Reserve IDEAS page: https://ideas.repec.org/p/fip/feddwp/88543.html
- Author's page: Search "David Jacks freight rates" on Google Scholar

**Expected Content:**
- Freight rate indices by decade
- Can use as proxy for agency fee escalation (fees typically 2-3% of freight costs)

---

#### B. Hummels - "Transportation Costs and International Trade" (2007)

**Citation:** Hummels, David (2007). "Transportation Costs and International Trade in the Second Era of Globalization"

**Direct Download Link:**
https://www.aeaweb.org/articles?id=10.1257/jep.21.3.131

**Alternative (if paywall):**
- NBER Working Paper version: https://www.nber.org/papers/w13382
- Author's page: Purdue University - David Hummels faculty page

**Size:** ~1-2 MB
**Relevance:** Shipping cost breakdown, includes port service costs

**Expected Content:**
- Breakdown of total shipping costs
- Port charges as % of total
- Time series data 1950-2000

---

## DOWNLOAD BATCH SCRIPT (OPTIONAL)

If you want to automate downloads using PowerShell:

```powershell
# Create download directory
$downloadDir = "G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.04_ARCHIVAL_SOURCES"
New-Item -ItemType Directory -Force -Path $downloadDir

# Download 1910 book
Invoke-WebRequest -Uri "https://archive.org/download/dueschargesonsh00urqugoog/dueschargesonsh00urqugoog.pdf" -OutFile "$downloadDir\1910_Dues_and_Charges_on_Shipping.pdf"

# Download Federal Maritime Board reports
$years = 1951..1961
foreach ($year in $years) {
    $url = "https://www.fmc.gov/wp-content/uploads/2021/09/FMB-$year-Annual-Report.pdf"
    $outFile = "$downloadDir\FMB_Annual_Report_$year.pdf"
    Invoke-WebRequest -Uri $url -OutFile $outFile
    Write-Host "Downloaded $year report"
}

# Download research papers
Invoke-WebRequest -Uri "https://www.dallasfed.org/-/media/documents/research/papers/2020/wp2008.pdf" -OutFile "$downloadDir\Dallas_Fed_Freight_Rates_2020.pdf"

Write-Host "All downloads complete!"
```

---

## NEXT STEPS AFTER DOWNLOADING

### Phase 1: Initial Review (1-2 hours)

1. **1910 Book**: Search PDF for US ports + "agent" within 5 pages
   - Target ports: New York, Baltimore, Norfolk, New Orleans, San Francisco
   - Look for tables with "Agent's commission" or "Broker's fee"

2. **Federal Maritime Board Reports**:
   - Check index of each report for "agency" or "port costs"
   - Focus on rate case decisions and cost studies
   - Look for appendices with statistical tables

3. **Research Papers**:
   - Extract freight rate data tables
   - Note years covered and geographic scope
   - Calculate ratios for proxy analysis

### Phase 2: Data Extraction (2-4 hours)

Create spreadsheet with columns:
- Year
- Source Document
- Port (if specified)
- Fee Amount (original currency)
- Fee Type (% of freight, flat fee, per ton, etc.)
- Vessel Type (if specified)
- Page Number (for citation)

### Phase 3: Analysis (1-2 hours)

- Convert all fees to 2025 dollars using CPI
- Calculate compound annual growth rate
- Compare to freight rate inflation
- Compare to wage inflation
- Identify trend breaks (if any)

---

## TROUBLESHOOTING

### If PDFs won't download:
- Try different browser (Chrome, Firefox, Edge)
- Disable browser extensions
- Try incognito/private mode
- Use download manager software

### If PDFs are corrupted:
- Re-download from alternative source
- Try opening with different PDF reader (Adobe, Foxit, browser built-in)
- Check file size matches expected size

### If links are broken:
- Use Internet Archive Wayback Machine to find archived versions
- Search document title + "PDF" on Google
- Contact library/repository directly

---

## ESTIMATED TIME

- **Downloads:** 30-60 minutes (depending on connection speed)
- **Initial review:** 1-2 hours
- **Detailed extraction:** 2-4 hours
- **Analysis:** 1-2 hours

**Total:** 4-8 hours of work

---

## STORAGE REQUIREMENTS

- 1910 Book: 166.5 MB
- 11 FMB Reports: ~37 MB total
- Research papers: ~4 MB
- **Total:** ~208 MB

Ensure sufficient disk space before starting batch download.

---

**END OF DOWNLOAD INSTRUCTIONS**

*Last updated: February 6, 2026*
