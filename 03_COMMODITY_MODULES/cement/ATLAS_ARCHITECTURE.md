# U.S. Cement Market Intelligence System — Architecture Blueprint

## Project Codename: ATLAS
### Analytical Tool for Logistics, Assets, Trade & Supply

---

## 1. SYSTEM PHILOSOPHY

This is **not** a RAG project with some data bolted on. This is a **hybrid intelligence platform** with three distinct engines that serve different purposes:

| Engine | Purpose | Data Types | Technology |
|--------|---------|------------|------------|
| **Structured Analytics** | Quantitative analysis, joins, aggregation, time-series, spatial | EPA FRS, USGS minerals, ocean manifests, HTS trade, Census/BTS | DuckDB + Python |
| **Document Intelligence (RAG)** | Narrative search, contextual retrieval, qualitative insights | Industry reports, SEC filings, Federal Register, trade press, earnings calls | ChromaDB + sentence-transformers |
| **Synthesis Engine** | Combines structured + RAG outputs into reports and dashboards | Structured query results + RAG retrievals | Claude API + Jinja2 templates |

The key insight: **RAG replaces an analyst's file cabinet, not their spreadsheet.** Structured data stays in SQL. Documents go in vectors. The synthesis layer is where the magic happens — Claude takes both inputs and produces the deliverable.

---

## 2. DATA SOURCE INVENTORY

### Phase 1: Domestic Supply/Demand Mapping

| Source | Type | Update Freq | Access Method | Key Fields |
|--------|------|-------------|---------------|------------|
| **EPA FRS** (already built) | Structured | Weekly | Local DuckDB | REGISTRY_ID, facility name, address, lat/lon, NAICS, org |
| **USGS Mineral Commodity Summaries** | Semi-structured | Annual (Jan) | PDF + data tables | Production, consumption, imports, exports, prices by commodity |
| **USGS Minerals Yearbook — Cement** | Semi-structured | Annual (lag 18mo) | PDF chapters + Excel tables | Plant-level production, state data, company rankings |
| **USGS Cement Statistics** | Structured | Monthly | data.usgs.gov API + Excel | Monthly shipments, clinker production, stocks, by state |
| **Portland Cement Association (PCA)** | Semi-structured | Quarterly | Reports (subscription) | Regional demand forecasts, end-use breakdowns |
| **Census Bureau — Manufacturers' Shipments** | Structured | Monthly/Annual | census.gov API | MA325D (concrete products), value of shipments |
| **EPA GHGRP** (Greenhouse Gas) | Structured | Annual | data.epa.gov | Cement plant emissions → proxy for production volume |

### Phase 2: Import/Export Trade Flows

| Source | Type | Update Freq | Access Method | Key Fields |
|--------|------|-------------|---------------|------------|
| **CBP AMS Ocean Manifests** | Structured | Daily | OpenJICA / AMS bulk | BOL, shipper, consignee, commodity, port, vessel, weight |
| **USITC/Census HTS Trade Data** | Structured | Monthly | dataweb.usitc.gov | HTS 2523.xx (Portland cement), quantity, value, country, port district |
| **Section 232/301 Tariff Actions** | Semi-structured | As issued | Federal Register + USTR | Duty rates, exclusions, country scope |
| **Vessel Tracking (AIS)** | Structured | Real-time | MarineTraffic API / bulk | Vessel movements, port calls, draft readings |

### Phase 3: Full Integration + Qualitative Layer

| Source | Type | Storage | Purpose |
|--------|------|---------|---------|
| **SEC EDGAR filings** (10-K, 10-Q) | Documents → RAG | ChromaDB | Company financials, capacity plans, risk factors |
| **Earnings call transcripts** | Documents → RAG | ChromaDB | Forward guidance, pricing commentary, demand signals |
| **Trade press** (CemNet, Global Cement, Cement Americas) | Documents → RAG | ChromaDB | Market intelligence, project announcements |
| **Federal Register notices** | Documents → RAG | ChromaDB | Regulatory changes, AD/CVD actions, environmental rules |
| **CBP rulings / CROSS database** | Documents → RAG | ChromaDB | Classification precedents, tariff treatment |

---

## 3. SYSTEM ARCHITECTURE

```
atlas/
├── config/
│   ├── settings.yaml                 # All paths, API keys, DB locations
│   ├── naics_sectors.yaml            # Cement industry NAICS groupings
│   ├── hts_codes.yaml                # Cement HTS classification tree
│   ├── parent_mapping.json           # Corporate entity rollup rules
│   └── report_templates/             # Jinja2 templates for client reports
│       ├── market_overview.md.j2
│       ├── facility_profile.md.j2
│       ├── trade_flow_brief.md.j2
│       └── executive_dashboard.md.j2
│
├── data/
│   ├── raw/                          # Downloaded source files (gitignored)
│   │   ├── epa_frs/                  # → symlink to task_epa_frs/data/
│   │   ├── usgs/                     # Mineral commodity data
│   │   ├── trade/                    # HTS, AMS manifests
│   │   └── documents/                # PDFs, filings for RAG ingest
│   ├── processed/                    # Cleaned Parquet intermediates
│   └── atlas.duckdb                  # Master analytical database
│
├── src/
│   ├── __init__.py
│   │
│   ├── etl/                          # Extract-Transform-Load pipelines
│   │   ├── __init__.py
│   │   ├── epa_frs.py                # EPA FRS loader (reads from existing frs.duckdb)
│   │   ├── usgs_minerals.py          # USGS data fetcher + parser
│   │   ├── usgs_cement_stats.py      # Monthly cement statistics
│   │   ├── trade_hts.py              # HTS import/export data loader
│   │   ├── ocean_manifests.py        # AMS/OpenJICA manifest parser
│   │   ├── ghgrp.py                  # EPA Greenhouse Gas loader (production proxy)
│   │   ├── census_shipments.py       # Census manufacturers' shipments
│   │   └── refresh.py                # Orchestrator: refresh all sources
│   │
│   ├── harmonize/                    # Entity resolution & normalization
│   │   ├── __init__.py
│   │   ├── entity_resolver.py        # Fuzzy company name matching + parent rollup
│   │   ├── facility_linker.py        # Cross-source facility dedup (FRS ↔ GHGRP ↔ USGS)
│   │   ├── naics_grouper.py          # NAICS hierarchy with cement-specific sectors
│   │   └── hts_classifier.py         # HTS code normalization + cement product mapping
│   │
│   ├── analytics/                    # Structured data analysis
│   │   ├── __init__.py
│   │   ├── supply.py                 # Domestic production capacity, plant utilization
│   │   ├── demand.py                 # End-use consumption modeling by segment
│   │   ├── trade_flows.py            # Import/export volume, value, origin/destination
│   │   ├── pricing.py                # Price indices, freight-adjusted delivered cost
│   │   ├── spatial.py                # Facility clustering, market radius, logistics
│   │   └── timeseries.py             # Trend analysis, seasonality, forecasting
│   │
│   ├── rag/                          # Document intelligence layer
│   │   ├── __init__.py
│   │   ├── ingest.py                 # PDF/text → chunks → embeddings → ChromaDB
│   │   ├── retriever.py              # Semantic search with metadata filtering
│   │   ├── extractors/               # Source-specific content extractors
│   │   │   ├── sec_edgar.py          # 10-K/10-Q section parser
│   │   │   ├── usgs_yearbook.py      # USGS chapter table extraction
│   │   │   ├── federal_register.py   # FR notice parser
│   │   │   └── trade_press.py        # Article scraper/cleaner
│   │   └── chunking.py               # Smart chunking (respect section boundaries)
│   │
│   ├── synthesis/                    # Report generation engine
│   │   ├── __init__.py
│   │   ├── report_builder.py         # Orchestrates data pull → RAG retrieval → Claude
│   │   ├── templates.py              # Template loader + Jinja2 rendering
│   │   ├── charts.py                 # Matplotlib/Plotly chart generation
│   │   ├── maps.py                   # Folium/GeoPandas facility maps
│   │   └── export.py                 # → DOCX, PDF, XLSX, HTML dashboard
│   │
│   └── dashboard/                    # Live query interface
│       ├── __init__.py
│       ├── app.py                    # Streamlit or Panel dashboard
│       ├── pages/
│       │   ├── market_overview.py    # National supply/demand snapshot
│       │   ├── facility_explorer.py  # Interactive facility map + details
│       │   ├── trade_monitor.py      # Import/export flow visualization
│       │   └── company_profiles.py   # Corporate footprint analysis
│       └── widgets.py                # Reusable dashboard components
│
├── cli.py                            # Master CLI entry point
├── requirements.txt
├── .env                              # API keys (gitignored)
└── README.md
```

---

## 4. DATABASE SCHEMA (atlas.duckdb)

### Core Tables (Phase 1)

```sql
-- Facilities: master record from EPA FRS (read from existing frs.duckdb)
CREATE TABLE facilities AS
SELECT * FROM read_parquet('data/processed/facilities.parquet');
-- Key: registry_id | name, street, city, state, zip, county, lat, lon

-- NAICS codes per facility
CREATE TABLE facility_naics AS ...
-- Key: registry_id + naics_code | description, sector_group

-- Organizations / parent companies
CREATE TABLE organizations AS ...
-- Key: registry_id | org_name, duns, org_type, resolved_parent

-- USGS cement plant data (annual production)
CREATE TABLE usgs_cement_plants (
    plant_id VARCHAR PRIMARY KEY,
    company VARCHAR,
    plant_name VARCHAR,
    city VARCHAR, state VARCHAR,
    type VARCHAR,           -- 'portland', 'masonry', 'white', 'oil_well'
    capacity_tons DECIMAL,
    production_tons DECIMAL,
    year INTEGER,
    registry_id VARCHAR,    -- FK to facilities (cross-linked)
    lat DOUBLE, lon DOUBLE
);

-- USGS monthly cement statistics
CREATE TABLE usgs_cement_monthly (
    year INTEGER, month INTEGER,
    metric VARCHAR,         -- 'clinker_production', 'cement_shipments', 'stocks'
    state VARCHAR,
    value DECIMAL,
    unit VARCHAR
);

-- EPA GHGRP emissions (production proxy)
CREATE TABLE ghgrp_cement (
    facility_id VARCHAR,
    year INTEGER,
    co2_emissions_tons DECIMAL,
    subpart VARCHAR,        -- 'H' = cement
    registry_id VARCHAR,    -- FK to facilities
    PRIMARY KEY (facility_id, year)
);

-- Parent company resolution table
CREATE TABLE parent_companies (
    raw_name VARCHAR,
    resolved_parent VARCHAR,
    confidence DECIMAL,
    method VARCHAR,         -- 'exact', 'fuzzy', 'manual', 'sec_cik'
    sec_cik VARCHAR,
    ticker VARCHAR
);
```

### Trade Tables (Phase 2)

```sql
-- HTS import/export data
CREATE TABLE hts_trade (
    year INTEGER, month INTEGER,
    direction VARCHAR,      -- 'import', 'export'
    hts_code VARCHAR,       -- e.g., '2523.29.0000'
    hts_description VARCHAR,
    country VARCHAR,
    customs_district VARCHAR,
    port_code VARCHAR,
    quantity DECIMAL, quantity_unit VARCHAR,
    value_usd DECIMAL,
    duty_rate DECIMAL
);

-- Ocean manifest records
CREATE TABLE ocean_manifests (
    bol_number VARCHAR,
    vessel_name VARCHAR, voyage_number VARCHAR,
    carrier_code VARCHAR,
    shipper_name VARCHAR, shipper_country VARCHAR,
    consignee_name VARCHAR, consignee_address VARCHAR,
    notify_party VARCHAR,
    commodity_description VARCHAR,
    container_count INTEGER, weight_kg DECIMAL,
    port_of_loading VARCHAR, port_of_discharge VARCHAR,
    arrival_date DATE,
    -- Resolved fields
    resolved_shipper_parent VARCHAR,
    resolved_consignee_parent VARCHAR,
    product_category VARCHAR   -- 'portland_cement', 'white_cement', 'clinker', etc.
);

-- Tariff/duty schedule
CREATE TABLE tariff_schedule (
    hts_code VARCHAR,
    description VARCHAR,
    general_rate DECIMAL,
    special_rate VARCHAR,
    column2_rate DECIMAL,
    effective_date DATE,
    notes VARCHAR            -- Section 232, AD/CVD, etc.
);
```

### RAG Metadata Table (Phase 3)

```sql
-- Document registry (metadata for RAG corpus)
CREATE TABLE documents (
    doc_id VARCHAR PRIMARY KEY,
    source VARCHAR,         -- 'sec_10k', 'usgs_yearbook', 'trade_press', etc.
    title VARCHAR,
    company VARCHAR,        -- if company-specific
    date DATE,
    url VARCHAR,
    file_path VARCHAR,
    chunk_count INTEGER,
    last_indexed TIMESTAMP
);
```

---

## 5. RAG DESIGN (Scoped to Where It Adds Value)

### What Goes Into RAG

Only **unstructured narrative content** that you'd otherwise have to read manually:
- USGS Minerals Yearbook narrative chapters (NOT the data tables — those go to DuckDB)
- SEC 10-K sections: Business, Risk Factors, MD&A, Properties
- Earnings call transcripts (capacity expansion signals, pricing guidance)
- Trade press articles (project announcements, M&A, market shifts)
- Federal Register notices (AD/CVD, Section 232 modifications)
- CBP rulings from CROSS database

### What Does NOT Go Into RAG

- EPA FRS data → DuckDB (structured, relational)
- USGS statistics → DuckDB (time-series, numeric)
- HTS trade data → DuckDB (tabular, aggregatable)
- Ocean manifests → DuckDB (structured, high-volume)
- Any data you need to SUM, JOIN, GROUP BY, or plot on a chart

### Chunking Strategy

```python
# Smart chunking that respects document structure
CHUNK_CONFIG = {
    'sec_10k': {
        'method': 'section_boundary',  # Split at Item headers
        'max_tokens': 1000,
        'overlap': 100,
        'metadata': ['company', 'cik', 'filing_date', 'section', 'fiscal_year']
    },
    'usgs_yearbook': {
        'method': 'heading_boundary',  # Split at H2/H3 headings
        'max_tokens': 800,
        'overlap': 50,
        'metadata': ['commodity', 'year', 'section_title', 'chapter']
    },
    'trade_press': {
        'method': 'paragraph',         # Natural paragraph breaks
        'max_tokens': 600,
        'overlap': 75,
        'metadata': ['source', 'date', 'title', 'companies_mentioned', 'topic']
    },
    'federal_register': {
        'method': 'section_boundary',
        'max_tokens': 1000,
        'overlap': 100,
        'metadata': ['fr_number', 'agency', 'action_type', 'effective_date', 'hts_codes']
    }
}
```

### Embedding Model

```python
# sentence-transformers for local embedding (no API cost)
# all-MiniLM-L6-v2 for speed, or all-mpnet-base-v2 for accuracy
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
```

### Vector Store

```python
# ChromaDB: lightweight, persistent, good metadata filtering
import chromadb
client = chromadb.PersistentClient(path="data/chromadb")
collection = client.get_or_create_collection(
    name="cement_intelligence",
    metadata={"hnsw:space": "cosine"}
)
```

---

## 6. SYNTHESIS ENGINE (The Secret Weapon)

This is where structured analytics and RAG converge. The synthesis engine:

1. **Receives a report request** (e.g., "Q4 2025 Cement Market Overview")
2. **Runs structured queries** against DuckDB (production stats, trade volumes, facility counts)
3. **Retrieves relevant documents** from ChromaDB (earnings commentary, USGS analysis, trade press)
4. **Constructs a Claude prompt** with structured data as tables/facts and RAG results as context
5. **Generates the report** using Claude API with a Jinja2 template structure
6. **Exports** to DOCX, PDF, or dashboard

```python
# Synthesis flow pseudocode
class ReportBuilder:
    def generate(self, report_type, params):
        # 1. Structured data queries
        data = {}
        data['production'] = self.analytics.supply.get_production(params)
        data['imports'] = self.analytics.trade_flows.get_imports(params)
        data['facility_count'] = self.analytics.supply.count_by_state(params)
        data['charts'] = self.charts.generate(data)

        # 2. RAG retrieval
        context = {}
        context['market_commentary'] = self.rag.retrieve(
            query=f"cement market conditions {params['quarter']} {params['year']}",
            filters={'date': {'$gte': params['start_date']}},
            top_k=10
        )
        context['company_guidance'] = self.rag.retrieve(
            query=f"cement capacity expansion investment plans",
            filters={'source': 'sec_10k', 'date': {'$gte': params['start_date']}},
            top_k=8
        )

        # 3. Claude synthesis
        prompt = self.templates.render(report_type, data=data, context=context)
        report = claude_api.complete(prompt, model="claude-sonnet-4-5-20250929")

        # 4. Export
        return self.export.to_docx(report, charts=data['charts'])
```

---

## 7. CLI INTERFACE

```bash
# Data management
atlas refresh --all                    # Refresh all data sources
atlas refresh --source epa_frs         # Refresh specific source
atlas refresh --source usgs --year 2025
atlas refresh --source trade --months 6

# Analytics
atlas query facilities --naics 3273 --state TX
atlas query trade --hts 2523 --direction import --year 2025
atlas stats production --commodity cement --by state
atlas stats imports --by country --top 10

# RAG management
atlas rag ingest --source sec_10k --company "CRH"
atlas rag ingest --source usgs_yearbook --year 2024
atlas rag search "cement capacity expansion plans Southeast"

# Report generation
atlas report market-overview --quarter Q4 --year 2025
atlas report facility-profile --company "CEMEX" --output docx
atlas report trade-brief --commodity "portland cement" --period "2025"
atlas report custom --template my_template.md.j2 --params params.yaml

# Dashboard
atlas dashboard serve --port 8501      # Launch Streamlit dashboard

# Entity resolution
atlas harmonize suggest --threshold 80
atlas harmonize apply
atlas harmonize export-mapping
```

---

## 8. BUILD SEQUENCE (Claude Code Phases)

### Phase 1A: Foundation (Session 1-2)
**Goal:** Master DuckDB with EPA FRS integrated, USGS data loaded, basic queries working.

```
Build:
- Project scaffolding (full directory structure, config files, requirements.txt)
- src/etl/epa_frs.py → Read from existing frs.duckdb into atlas.duckdb
- src/etl/usgs_minerals.py → Download + parse USGS Mineral Commodity Summaries
- src/etl/usgs_cement_stats.py → Monthly cement statistics
- src/etl/ghgrp.py → EPA Greenhouse Gas cement plant data
- src/harmonize/entity_resolver.py → Fuzzy matching + parent_mapping.json
- src/harmonize/facility_linker.py → Cross-reference FRS ↔ USGS ↔ GHGRP
- src/analytics/supply.py → Production capacity, utilization, state distribution
- cli.py → Core commands (refresh, query, stats)
- Basic test suite
```

**Deliverable:** Can answer "How much cement does each company produce, at which plants, in which states?"

### Phase 1B: Demand Modeling (Session 3)
**Goal:** End-use consumption breakdown, facility-level demand estimation.

```
Build:
- src/analytics/demand.py → Segment consumption model (precast, highway, masonry, etc.)
- src/analytics/spatial.py → Market radius analysis, logistics optimization
- src/analytics/timeseries.py → Seasonal patterns, trend decomposition
- Census shipments integration
- Demand heatmap generation
```

**Deliverable:** Can answer "What are the top cement-consuming metros, and which segments drive demand?"

### Phase 2A: Trade Intelligence (Session 4-5)
**Goal:** Import/export flows fully mapped, ocean manifest analysis operational.

```
Build:
- src/etl/trade_hts.py → HTS import/export data loader from USITC
- src/etl/ocean_manifests.py → AMS/OpenJICA parser
- src/harmonize/hts_classifier.py → Cement product category mapping
- src/analytics/trade_flows.py → Volume/value by origin, destination, port
- Shipper/consignee entity resolution against parent_companies
- Tariff schedule integration (Section 232, AD/CVD)
```

**Deliverable:** Can answer "Who is importing cement from Turkey into Gulf ports, at what volume, and what duty applies?"

### Phase 2B: Trade + Domestic Integration (Session 6)
**Goal:** Domestic production + imports = total supply picture.

```
Build:
- Supply/demand balance model (production + imports - exports = apparent consumption)
- Port-to-terminal-to-market logistics mapping
- Import penetration by region
- Price arbitrage analysis (import landed cost vs domestic)
```

**Deliverable:** Can answer "Which regions are import-dependent, and what's the landed cost advantage?"

### Phase 3A: RAG Layer (Session 7-8)
**Goal:** Document intelligence operational for qualitative enrichment.

```
Build:
- src/rag/ingest.py → PDF/text chunking + embedding pipeline
- src/rag/retriever.py → Semantic search with metadata filtering
- src/rag/extractors/ → Source-specific parsers (SEC, USGS, FR, press)
- ChromaDB setup + initial corpus ingest
- RAG quality testing
```

**Deliverable:** Can answer "What did CRH say about Southeast capacity in their last 10-K?"

### Phase 3B: Synthesis + Reports (Session 9-10)
**Goal:** Automated report generation combining structured data + RAG.

```
Build:
- src/synthesis/report_builder.py → Orchestration engine
- src/synthesis/templates.py → Jinja2 template system
- src/synthesis/charts.py → Auto-generated charts
- src/synthesis/maps.py → Facility maps for reports
- src/synthesis/export.py → DOCX, PDF, XLSX output
- Report templates (market overview, facility profile, trade brief)
```

**Deliverable:** One command generates a 20-page market overview with charts, maps, and narrative.

### Phase 4: Dashboard (Session 11-12)
**Goal:** Live interactive dashboard for ongoing intelligence.

```
Build:
- src/dashboard/app.py → Streamlit application
- Market overview page (national snapshot with KPIs)
- Facility explorer (interactive map, click for details)
- Trade monitor (import/export trends, vessel tracking)
- Company profiles (corporate footprint, financials, compliance)
```

**Deliverable:** Browser-based dashboard you can use daily and show clients.

---

## 9. KEY DESIGN DECISIONS

### Why DuckDB as the Core (Not Postgres/SQLite)

- Columnar storage = 10-100x faster analytics on wide tables
- Native Parquet/CSV ingestion (no ETL boilerplate)
- Spatial extension for geospatial queries
- Zero-config, single-file database (portable, no server)
- Already proven in your EPA FRS project

### Why ChromaDB for RAG (Not Pinecone/Weaviate)

- Local/persistent (no cloud dependency or API costs)
- Good metadata filtering (critical for source/date/company scoping)
- Python-native, lightweight
- Sufficient for corpus size (<100K chunks)

### Why Sentence-Transformers (Not OpenAI Embeddings)

- No API cost (runs locally)
- No rate limits or data privacy concerns
- all-mpnet-base-v2 is competitive quality for domain-specific retrieval
- Consistent, reproducible results

### Why Claude API for Synthesis (Not Local LLM)

- Report quality matters for client deliverables
- Claude handles complex multi-source synthesis better than local models
- Structured data + narrative context requires large context window
- Cost is minimal for report generation (not high-volume inference)

---

## 10. DEPENDENCIES

```
# requirements.txt
# Core
duckdb>=1.1
pandas>=2.1
pyarrow>=14.0
click>=8.1
pyyaml>=6.0
python-dotenv>=1.0

# Entity Resolution
rapidfuzz>=3.5

# Geospatial
geopandas>=0.14
folium>=0.15
shapely>=2.0

# RAG
chromadb>=0.4
sentence-transformers>=2.2
pypdf2>=3.0
beautifulsoup4>=4.12

# Synthesis
anthropic>=0.28
jinja2>=3.1

# Visualization
matplotlib>=3.8
plotly>=5.18
seaborn>=0.13

# Dashboard
streamlit>=1.30
streamlit-folium>=0.15

# ETL
requests>=2.31
tqdm>=4.66
openpyxl>=3.1

# Report Export
python-docx>=1.1
weasyprint>=60.0     # HTML → PDF
```

---

## 11. CLAUDE CODE KICKOFF PROMPT (Phase 1A)

Save this and hand it to Claude Code when ready:

```
# ATLAS Phase 1A — Foundation Build

## Context
I'm building a cement market intelligence system called ATLAS. The architecture 
blueprint is at: G:\My Drive\LLM\atlas\ARCHITECTURE.md

An EPA FRS DuckDB database already exists at:
G:\My Drive\LLM\task_epa_frs\data\frs.duckdb

## This Session: Build Phase 1A

1. Create the full project scaffolding at G:\My Drive\LLM\atlas\ 
   following the directory structure in the architecture doc.

2. Create config/settings.yaml with all paths, URLs, and NAICS groupings.

3. Build src/etl/epa_frs.py:
   - Connect to existing frs.duckdb (READ ONLY)
   - Auto-discover schema (table/column names)
   - Extract facilities, naics_codes, organizations tables
   - Write to atlas.duckdb with standardized schema
   - Cross-reference with cement NAICS prefixes (3273xx, 3241xx, etc.)

4. Build src/etl/usgs_minerals.py:
   - Download USGS Mineral Commodity Summaries (cement chapter)
   - Parse production, consumption, import, export tables
   - Load into atlas.duckdb usgs_cement_plants and usgs_cement_monthly

5. Build src/etl/ghgrp.py:
   - Download EPA GHGRP Subpart H (cement) data from data.epa.gov
   - Parse facility-level CO2 emissions as production proxy
   - Cross-link to FRS registry_ids
   - Load into atlas.duckdb ghgrp_cement table

6. Build src/harmonize/entity_resolver.py:
   - Fuzzy company name matching using rapidfuzz
   - Organization name normalization (strip LLC/Inc/Corp)
   - parent_mapping.json for curated overrides
   - Function: resolve_parent(raw_name) → resolved_parent

7. Build src/harmonize/facility_linker.py:
   - Cross-reference FRS facilities ↔ USGS plant list ↔ GHGRP facilities
   - Match by name + state + proximity (within 5 miles)
   - Output: unified facility record with all source IDs

8. Build src/analytics/supply.py:
   - Production by company, by state, by plant
   - Capacity utilization estimates
   - Market share calculation
   - State-level supply concentration (HHI)

9. Build cli.py with Click:
   - atlas refresh [--source SOURCE] [--all]
   - atlas query facilities [--naics PREFIX] [--state ST] [--name PATTERN]
   - atlas stats production [--by state|company|plant] [--year YEAR]
   - atlas stats supply-summary

10. requirements.txt and README.md

## Important Notes
- DuckDB is the single analytical engine. All queries go through SQL.
- The existing frs.duckdb must NOT be modified. Read-only access.
- atlas.duckdb is the new master database for this project.
- Use Parquet as intermediate format between download and DuckDB load.
- Print clear progress messages during ETL operations.
- Handle network failures gracefully (retry logic for downloads).
- All paths should be configurable via settings.yaml.
```
