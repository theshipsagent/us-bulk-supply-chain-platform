# Claude Code Prompt — Econometric Model Technical White Paper

## INSTRUCTION

You are tasked with producing a comprehensive technical white paper documenting the econometric models, data architecture, and system requirements across three interrelated project directories. This is a deep technical audit and documentation exercise — not a summary. Read everything first, then write.

---

## PHASE 1: DISCOVERY (Read Before Writing)

Recursively read and catalog ALL files in the following three directories:

```
G:\My Drive\LLM\project_rail
G:\My Drive\LLM\project_barge
G:\My Drive\LLM\project_port_nickle
```

For each directory:
1. List every file with its path, type, and size
2. Read every `.py`, `.ipynb`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.csv` (headers only for CSVs), `.xlsx` (sheet names and headers), and any requirements/setup files
3. Identify all `import` statements across all Python files
4. Identify all configuration files, environment variables, API keys referenced (names only, not values)
5. Identify all data source URLs, file paths, and external API endpoints referenced in code or documentation
6. Map function-to-function dependencies within and across projects

Do NOT begin writing the report until all three directories have been fully read and cataloged.

---

## PHASE 2: ANALYSIS

After completing Phase 1, analyze and classify the following for each project:

### A. Econometric / Mathematical Models
- Identify every formula, equation, regression specification, optimization function, cost function, index calculation, deflator, elasticity, multiplier, or statistical model used
- Document each model with: (a) the exact formula as implemented in code, (b) variable definitions and units, (c) the source or theoretical basis for the model (e.g., BEA I-O tables, IMPLAN multipliers, Army Corps waterway data, STB waybill data, etc.), (d) any calibration parameters or hardcoded constants and their provenance

### B. Data Pipeline Architecture
- Map the full data flow: raw source → ingestion → transformation → model input → model output → visualization/export
- Identify every external data source by name, URL, update frequency, and format
- Document any data harmonization, entity resolution, or classification logic (e.g., commodity codes, port codes, carrier harmonization)

### C. System Dependencies
- Catalog every Python package imported across all three projects
- Identify system-level dependencies (e.g., wkhtmltopdf, poppler, GDAL, database drivers)
- Note any API dependencies and authentication requirements
- Flag any version-specific requirements or known compatibility issues found in code comments or config files

---

## PHASE 3: WRITE THE WHITE PAPER

Create the output directory:
```
G:\My Drive\LLM\econometric_model_documentation
```

Generate a single PDF file named:
```
Econometric_Model_Technical_Documentation_YYYY-MM-DD.pdf
```

Use the current date for YYYY-MM-DD.

### Document Structure

**COVER PAGE**
- Title: "Econometric Model Technical Documentation — Barge, Rail, and Port Economic Impact Systems"
- Subtitle: "Architecture, Methodology, Data Sources, and System Requirements"
- Author: William S. Davis III
- Date: [current date]
- Version: 1.0 — Initial Technical Audit

**TABLE OF CONTENTS**
- Auto-generated with page numbers covering all sections and subsections below

---

**SECTION 1: EXECUTIVE OVERVIEW** (1–2 pages)
- Purpose of this document
- Summary of the three model systems and their interrelationships
- Current development status of each (operational, in-progress, prototype, planned)

---

**SECTION 2: BARGE COST MODEL** (`project_barge`)

2.1 — Model Purpose and Scope
- What the model calculates, for whom, and covering what geography/commodities

2.2 — Econometric Methodology
- Every formula and cost function, written out in standard mathematical notation AND as implemented in code
- Variable definitions table (variable name, description, unit, source)
- Regression specifications if any (dependent variable, independent variables, estimation method)
- Any index calculations, deflators, or normalization methods

2.3 — Data Sources and Inputs
- Complete inventory of every data source: name, provider, URL/access method, format, update frequency, date range available
- Sample data structures (column headers, key fields)

2.4 — Data Pipeline and Processing Logic
- Step-by-step data flow from raw ingestion to model output
- Any entity harmonization, commodity classification, or geographic mapping logic
- Error handling and data validation rules

2.5 — Outputs and Deliverables
- What the model produces (tables, charts, reports, exports)
- Output formats and destinations

2.6 — Current Status and Known Limitations
- What works, what's incomplete, what needs improvement
- Any hardcoded values that should be parameterized
- Data gaps or quality issues identified

---

**SECTION 3: RAIL COST MODEL** (`project_rail`)

Same subsection structure as Section 2 (3.1 through 3.6), fully detailed for the rail model. Include:
- Rail-specific cost components (line-haul, switching, demurrage, fuel surcharge, etc.)
- Any STB waybill data processing
- Network/routing logic if present
- Rate benchmarking methodology

---

**SECTION 4: PORT ECONOMIC IMPACT MODEL** (`project_port_nickle`)

Same subsection structure as Section 2 (4.1 through 4.6), fully detailed. Include:
- BEA Input-Output methodology and tables used
- IMPLAN or IMPLAN-equivalent multiplier logic
- Workforce impact calculations (direct, indirect, induced)
- Economic impact metrics (GDP contribution, employment, tax revenue, etc.)
- Any regional economic modeling (RIMS II, custom multipliers)
- Capital investment and operational expenditure modeling

---

**SECTION 5: CROSS-MODEL INTEGRATION**

5.1 — Shared Data Sources and Common Infrastructure
- Data sources used by multiple models
- Shared utility functions or libraries
- Common data schemas or classification systems

5.2 — Model Interdependencies
- How outputs from one model feed into another
- Opportunities for further integration

---

**SECTION 6: SYSTEM ARCHITECTURE OVERVIEW**

6.1 — Technology Stack Summary
- Python version requirements
- Key framework choices (pandas, numpy, scipy, statsmodels, etc.)
- Visualization libraries
- PDF/report generation tools
- Any database or storage dependencies

6.2 — Directory and File Structure
- Tree diagram of each project directory with file descriptions

---

**ANNEX A: CONSOLIDATED PYTHON PACKAGE REQUIREMENTS**

A single consolidated list in `pip install` format, organized by category:
- Core scientific computing (numpy, pandas, scipy, etc.)
- Econometrics and statistics (statsmodels, linearmodels, etc.)
- Data ingestion and web scraping (requests, selenium, beautifulsoup4, etc.)
- Visualization (matplotlib, plotly, seaborn, etc.)
- PDF/document generation (reportlab, fpdf, weasyprint, etc.)
- Geospatial (if any)
- API clients (if any)
- Utilities (if any)

For each package, include: package name, version constraint if specified in any project file, and which project(s) use it.

Also provide the complete `requirements.txt` content that would install everything needed to run all three projects.

---

**ANNEX B: EXTERNAL DATA SOURCE REGISTRY**

Master table of all external data sources across all three projects:
| Source Name | Provider | URL/Access Method | Format | Update Frequency | Used By (Project) | Data Fields Used | Notes |

---

**ANNEX C: FORMULA AND MODEL REFERENCE**

Consolidated quick-reference of every formula, equation, and model specification documented in Sections 2–4, numbered sequentially (Eq. 1, Eq. 2, etc.) with cross-references back to the relevant section.

---

**ANNEX D: SYSTEM PREREQUISITES AND ENVIRONMENT SETUP**

Step-by-step instructions to recreate the development environment from scratch:
1. Python version and installation
2. Virtual environment setup
3. System-level dependencies (OS packages, drivers, tools)
4. pip install sequence (with the consolidated requirements.txt from Annex A)
5. Environment variables and configuration files needed
6. API keys or credentials required (by name/purpose only)
7. Data directory structure to create
8. Any initial data downloads or setup scripts to run

---

## FORMATTING REQUIREMENTS

- Clean, professional typography — no colored backgrounds, no decorative elements
- Use consistent heading hierarchy (Section → Subsection → Sub-subsection)
- Formulas in clean mathematical notation where possible, with code implementation shown separately
- Tables for structured data (variable definitions, data sources, package lists)
- Monospace font for code snippets, file paths, and package names
- Page numbers on every page except cover
- Headers with section name on each page
- Reasonable margins and line spacing for readability
- Target length: as long as needed to be thorough — do not truncate or summarize to save space

---

## CRITICAL INSTRUCTIONS

1. **Read everything before writing anything.** Do not start the report after reading only one directory.
2. **Document what EXISTS in the code, not what you think should exist.** If a formula is implemented differently than textbook, document the actual implementation and note the discrepancy.
3. **If a model component is incomplete or placeholder, say so explicitly.** Do not fill gaps with assumptions.
4. **Every formula must show both the mathematical form AND the Python implementation** with line references to the source file.
5. **Every data source must be traceable** — if a CSV is loaded, document where that CSV comes from originally.
6. **The Annexes are as important as the body.** The requirements annex must be complete enough that someone could rebuild the environment from scratch.
7. Save the final PDF to: `G:\My Drive\LLM\econometric_model_documentation\`
8. Also save a copy of the consolidated `requirements.txt` as a separate file in the same output directory.
