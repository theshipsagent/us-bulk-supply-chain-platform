# STB Agricultural Contract Summary (ACS) - Parsing Analysis

## Source File
- **File:** `ACS-UP-4Q-11-29-2021.pdf`
- **Railroad:** Union Pacific Railroad Company
- **Quarter:** Q4 2021
- **Received by STB:** November 29, 2021
- **Pages:** 49
- **Contracts found:** 10 (originally identified 11 header markers, but one is a continuation)

## Parsing Results (Validated)

| Metric | Count |
|--------|-------|
| Contracts | 10 |
| Unique carriers | 6 |
| Unique commodities | 21 |
| Unique shippers | 13 |
| Unique origins | 104 |
| Unique destinations | 90 |
| Exhibit (AGS) stations | 953 |

## Database Schema

8 normalized tables created in SQLite:
- `acs_filing` - One row per PDF file
- `acs_contract` - One row per contract summary
- `acs_carrier` - Many carriers per contract
- `acs_commodity` - Many commodities per contract
- `acs_shipper` - 1-2+ shippers per contract
- `acs_origin` - Many origin locations per contract
- `acs_destination` - Many destination locations per contract
- `acs_exhibit` - AGS station definitions (can be 100+ per exhibit)

## Fields Consistently Present

These fields appear in EVERY contract:
- Contract ID (e.g., `STB-UPOTMQ 150381-F`)
- Railroad name
- Issued date / Effective date
- Issuer name, title, address
- At least one participating carrier
- At least one commodity
- At least one shipper
- At least one origin and destination
- Ports (even if "Not Applicable")
- Duration (effective, amendment effective, expiration dates)
- Rail Car Data
- Rates & Charges
- Volume
- Special Features
- Special Notice

## Variable/Optional Fields

- **Exhibit Definitions:** Only present when AGS (Area Group Switching) references are used in origins/destinations. Can contain hundreds of station names.
- **Multiple carriers:** Most contracts have 1 carrier (UP only), but some have 2-5 (e.g., KCSM, Canadian National, Sacramento Valley Railroad, etc.)
- **Amendment markers:** ADDITION, DELETION, EXTENSION markers on individual items (commodities, origins, destinations, carriers)
- **Rates & Charges:** Varies: "Not applicable" (most common), "Subject to increases", or tariff references like "As published in Tariff(s) 4052"

## Contract ID Format

Format: `STB-{PREFIX} {NUMBER}-{SUFFIX}`

Observed prefixes:
- `UPOTMQ` - UP Open Tariff Multi-car Quarterly (?)
- `UPUPCQ` - UP UP Contract Quarterly (?)

Suffixes indicate amendment version: `-F`, `-M`, `-T`, `-CU`, `-AL`, `-W`, `-BW`, `-22`, `-14`

## Parsing Challenges

1. **Page breaks mid-contract:** Contract text spans multiple PDF pages. The contract ID is repeated as a footer/header on each page, which must be filtered out.
2. **Exhibit definitions are massive:** A single AGS exhibit can list 100-200 stations, spanning multiple pages. These repeat the contract ID as page breaks.
3. **Continuation lines in commodities:** Some commodity descriptions wrap to the next line (starts with lowercase or STCC number).
4. **Multi-carrier address parsing:** When multiple carriers are listed, their addresses interleave. Need heuristics to detect address lines vs. carrier name lines.
5. **Multiple shippers per contract:** Some contracts have 2 shippers on separate lines.
6. **Filing received date:** On the cover page, not always consistently formatted.

## Output Files Generated

- `ACS-UP-4Q-11-29-2021_parsed.json` - Full structured JSON
- `ACS-UP-4Q-11-29-2021_parsed.csv` - Flattened one-row-per-contract CSV
- `ACS-UP-4Q-11-29-2021.db` - SQLite database with normalized schema

## STB Archive Availability (Web Research)

### Agricultural Contract Summaries
- **2008-2021 (older archive):** `stb.gov/wp-content/uploads/econdata/ACS/{RR}/{YEAR}/{QTR}/ACS-{RR}-{YEAR}-{QTR}_{DATE}.pdf`
- **2021-2026 (current):** `stb.gov/wp-content/uploads/{RR}-Contract-Summary-{DATE}.pdf`
- **Railroads:** BNSF, CSX, NS, UP, KCS, IAIS, NCRC, IANR
- **Estimated total PDFs:** 2,000-3,000+ across all railroads

### Other Downloadable STB Data
- Public Use Waybill Sample (1996-2023) - ZIP files
- Commodity Revenue Stratification (2002-2023) - XLSX
- Freight Commodity Statistics (2007-2025) - XLSX/PDF
- Form RE&I, CBS, STB-54 - CSV files
- USDA Open Ag Transport portal - API/JSON access

### Key Limitation
Actual dollar rate amounts are confidential. Contract summaries show "Not applicable" or "Subject to increases" for the rates field. Full rate data requires FOIA or formal researcher access.
