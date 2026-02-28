# Data Gaps & Access Issues — Knowledge Bank Documentation

**Created:** 2026-02-23

---

## Overview

This document identifies information that could not be fetched from carrier websites due to access restrictions, URL changes, dynamic content, or data not publicly available. It also notes areas requiring manual follow-up or direct carrier inquiry.

## URL Access Issues

### Union Pacific (UP)
**Issue:** WebFetch tool blocked by network restrictions or enterprise security policies
**Error:** "Unable to verify if domain www.up.com is safe to fetch"
**Workaround:** Used WebSearch to gather information from search results and industry sources
**Impact:** Could not fetch directly from UP commodity pages
**Alternative Data Sources:** Web search results, industry publications, Wikipedia

**UP Attempted URLs:**
- https://www.up.com/customers/agriculture/
- https://www.up.com/customers/automotive/
- https://www.up.com/customers/chemicals/
- https://www.up.com/customers/coal/
- https://www.up.com/customers/intermodal/
- https://www.up.com/customers/industrial/metals/
- https://www.up.com/customers/industrial/minerals/
- https://www.up.com/customers/industrial/lumber/
- https://www.up.com/customers/industrial/construction/

**URL Structure Changes:** UP appears to have migrated some pages to `/shipping/[commodity]/` from `/customers/[commodity]/`

---

### CSX Transportation
**Issue:** Website returned 403 Forbidden errors
**Error:** "Request failed with status code 403"
**Workaround:** Used existing files from previous session, supplemented with general knowledge
**Impact:** Could not fetch CSX maps or additional commodity details

**CSX Attempted URLs:**
- https://www.csx.com/index.cfm/customers/maps/
- Port connection pages

---

### Norfolk Southern
**Issue:** Domain redirect and WebFetch permission denied
**Error:** Domain redirected from nscorp.com to norfolksouthern.com, then WebFetch denied
**Original URLs:** http://www.nscorp.com/content/nscorp/en/shipping-options/...
**New Domain:** https://www.norfolksouthern.com/
**Workaround:** Used WebSearch extensively to gather NS information
**Impact:** Could not fetch directly from NS commodity pages

**NS URL Changes:**
- Old: nscorp.com/content/nscorp/en/shipping-options/
- New: norfolksouthern.com/en/ship-by-rail/industry/

---

### BNSF Railway
**Issue:** URL structure changed from specific commodity pages to index pages
**Error:** 404 errors on commodity-specific URLs
**Workaround:** Fetched broader category pages (agricultural-products/index.page, energy/index.page, etc.)
**Impact:** Less granular commodity detail than expected

**BNSF Old URL Pattern (404):**
- /ship-with-bnsf/agricultural-products/grain.html
- /ship-with-bnsf/industrial-products/cement.html

**BNSF New URL Pattern (Working):**
- /ship-with-bnsf/agricultural-products/index.page
- /ship-with-bnsf/industrial-products/index.page

---

### Canadian National (CN) & CPKC
**Issue:** Limited WebFetch attempts due to earlier access issues
**Workaround:** Relied entirely on WebSearch for information
**Impact:** General commodity information rather than detailed facility-level data

---

## Information Gaps by Category

### Facility-Level Detail

**Missing Information:**
- Exact street addresses for most terminals, transload facilities, reload centers
- Facility capacity (annual throughput, car spots, storage capacity)
- Operating hours and contact information
- Specific equipment types at each facility

**Available:** General facility counts, major terminal names, city-level locations

**Example:** "NS serves 15 cement facilities" (count known) but specific addresses not public

---

### Volume Statistics

**Missing Information:**
- Annual carload counts by commodity
- Revenue per commodity segment (some carriers provide percentages, not all)
- Specific customer volumes
- Interchange traffic volumes by gateway

**Available:** General commodity revenue percentages (CN, CPKC provided 2024 percentages), network-wide statistics

**Example:** "BNSF moves grain from Great Plains to PNW" (route known) but annual carloads not disclosed

---

### Pricing & Rates

**Missing Information (Proprietary):**
- Freight rates for any commodity
- Accessorial charges (switching, demurrage, storage)
- Contract terms and volume discounts
- Transit time guarantees

**Note:** All pricing information is commercially sensitive and not publicly available. Customers must request quotes directly from carriers.

---

### Customer Names

**Missing Information (Proprietary):**
- Specific steel service center customers
- Grain elevator names and locations (some directories available, not comprehensive)
- Chemical plant customers
- Automotive assembly plant details (general locations known, specific customers often confidential)

**Available:** Some carriers publish grain customer directories (NS provides one), but most customer information is proprietary

---

### Equipment Fleet Data

**Missing Information:**
- Total railcar counts by type (covered hoppers, tank cars, autoracks, etc.)
- Locomotive fleet size and types
- Specialized equipment availability (Schnabel cars, heavy-duty flatcars)

**Available:** General equipment descriptions (e.g., "NS uses bi-level and tri-level autoracks") but not counts

**Example:** "BNSF operates centerbeam flatcars for lumber" (equipment type known) but fleet size not disclosed

---

### Operational Metrics

**Missing Information:**
- Average train velocity (speed)
- Terminal dwell time
- On-time performance percentages
- Service reliability metrics
- Equipment cycle time

**Available:** General service characteristics (e.g., "unit train service for coal") but not operational KPIs

---

## Dynamic Content & Interactive Tools

### Issues with Web-Based Tools

**Interactive Maps:**
- CSX system map (interactive, did not render in WebFetch)
- NS NSites industrial development tool (login-required or dynamic)
- BNSF Strategic Programs Map (interactive, not fetched)

**Port Schedules & Service Grids:**
- CN terminal-to-port service grids (referenced but not fully captured)
- CPKC Lazaro Cardenas port schedule (PDF, not fetched)

**Equipment Guides:**
- Detailed railcar specifications (some carriers have interactive equipment guides)

**Workaround:** Noted that these resources exist and described general content based on surrounding text

---

## Login-Required Content

### Customer Portals

**Examples:**
- BNSF: customer2.bnsf.com (rate quotes, tracking, account management)
- UP: Similar customer portal
- All carriers have login-required sections for shippers

**Content Behind Login:**
- Real-time car tracking
- Rate quotes
- Invoices and billing
- Historical shipping data
- Service performance dashboards

**Note:** This content is intended for customers only and not accessible for public knowledge bank compilation

---

## PDF Maps & Documents

### System Maps

**Not Fetched:**
- BNSF Rail Network Map (PDF download)
- UP System Map (PDF)
- CSX System Map (PDF)
- NS System Map (PDF)
- CN Network Map (PDF)
- CPKC Network Map (PDF)

**Note:** These maps exist and are referenced in network_overview.md and routes_corridors.md files, but the actual PDFs were not downloaded or parsed. They contain detailed route information, subdivision names, milepost data, and junction points.

---

## Recommended Follow-Up Actions

### For More Detailed Information

1. **Direct Carrier Contact:**
   - Sales representatives can provide facility-specific information
   - Customer service for shipping inquiries
   - Industrial development teams for site location data

2. **Request Public Documents:**
   - Annual reports (investor relations)
   - SEC filings (detailed operational and financial data)
   - Service guides (may be available upon request)

3. **Industry Publications:**
   - Trains Magazine, Railway Age, Progressive Railroading
   - Trade associations (AAR, ASLRRA)
   - STB regulatory filings (public dockets)

4. **Alternative Research Methods:**
   - Direct website access via browser (avoid WebFetch restrictions)
   - VPN or different network (bypass enterprise security blocks)
   - LinkedIn outreach to carrier personnel
   - Industry conferences and trade shows

---

## Data Quality Assessment

### High Confidence Information
- Network statistics (route miles, states served)
- Major facility locations (cities where terminals exist)
- Major corridors (Crescent Corridor, Northern Transcon, etc.)
- Commodity categories handled
- Interchange points (major gateways)
- Port access (cities and port names)

### Medium Confidence Information
- Facility counts (based on marketing materials, may not be comprehensive)
- Service characteristics (general descriptions, not contractual)
- Equipment types (general descriptions, not detailed specs)
- Commodity revenue percentages (where disclosed by carrier)

### Low Confidence / Uncertain
- Specific facility addresses (not verified)
- Volume statistics (estimates or not available)
- Customer names (proprietary, limited disclosure)
- Operational metrics (not publicly disclosed)

---

## Carrier-Specific Data Gaps

### BNSF
- Specific commodity page URLs changed to index pages (lost granularity)
- Logistics parks interactive map not accessed
- Coal Mine Guide referenced but not fetched

### Union Pacific
- Entire website access blocked by WebFetch
- Relied on web search and secondary sources
- URL structure migration noted but not fully explored

### CSX
- 403 errors on maps and some commodity pages
- Port information compiled from general knowledge
- TRANSFLO terminals referenced but details limited

### Norfolk Southern
- Domain redirect caused access issues
- Extensive web search used as alternative
- Some facility details limited

### Canadian National
- Limited direct website access attempted
- Revenue percentages available (2024 financial data)
- Specific Canadian facility details limited

### CPKC
- Newly formed company (2023 merger)
- Some Mexico facility details limited
- Lazaro Cardenas expansion plans noted but detailed info limited

---

## Conclusion

Despite access restrictions and data availability limitations, the knowledge bank contains substantial information on all six Class I carriers, covering:
- Network overviews
- Major commodities
- Routes and corridors
- Facilities (major terminals)
- Interchanges
- Port connections

For detailed, customer-specific information (facility addresses, pricing, service commitments), direct carrier contact is required. The knowledge bank provides a strong foundation for understanding Class I railroad operations, commodity markets, and network connectivity.
