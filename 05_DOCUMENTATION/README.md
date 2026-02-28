# Documentation — US Bulk Supply Chain Reporting Platform

**Last Updated:** 2026-02-25
**Purpose:** Central documentation hub for the entire platform

---

## Quick Navigation

### Core Platform Documentation (Start Here)

| Document | Purpose | Priority |
|---|---|:---:|
| **[CLAUDE.md](../CLAUDE.md)** | **Project directives (condensed, 247 lines)** | 🔴 Critical |
| **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)** | **Complete directory tree with descriptions** | 🔴 Critical |
| **[MIGRATION_STATUS.md](MIGRATION_STATUS.md)** | **Project migration tracking (8 of 12 complete)** | 🟡 High |
| **[TECHNICAL_STANDARDS.md](TECHNICAL_STANDARDS.md)** | **Code style, data standards, file naming** | 🟡 High |
| **[NAICS_HTS_CODES.md](NAICS_HTS_CODES.md)** | **Classification codes by commodity** | 🟢 Medium |

### Specialized Documentation

#### Barge & Waterway Research
| Document | Purpose |
|---|---|
| [Inland_Barge_Transportation_Economics_Research_Compendium.md](Inland_Barge_Transportation_Economics_Research_Compendium.md) | Research compendium (711 lines) |
| [Mississippi_River_Inland_Waterway_Data_Sources.md](Mississippi_River_Inland_Waterway_Data_Sources.md) | Waterway data sources (759 lines) |
| [Access_Guide_Barge_Research.md](Access_Guide_Barge_Research.md) | Barge research access guide (373 lines) |
| [Complete_Access_Guide_Wetzstein_Dissertation.md](Complete_Access_Guide_Wetzstein_Dissertation.md) | Wetzstein dissertation guide (464 lines) |
| [miss_river_grain_barge_pricing_claude_chat.md](miss_river_grain_barge_pricing_claude_chat.md) | Grain barge pricing notes (95 lines) |

#### USACE Data Sources
| Document | Purpose |
|---|---|
| [USACE_README.md](USACE_README.md) | USACE overview (340 lines) |
| [USACE_QUICKSTART.md](USACE_QUICKSTART.md) | Quick start guide (167 lines) |
| [USACE_HISTORICAL_GUIDE.md](USACE_HISTORICAL_GUIDE.md) | Historical data guide (444 lines) |

#### Vessel & Trade Intelligence
| Document | Purpose |
|---|---|
| [manifest_README.md](manifest_README.md) | Panjiva manifest processing (566 lines) |
| [manifest_CLAUDE.md](manifest_CLAUDE.md) | Manifest directives (237 lines) |
| [PIPELINE_RULES.md](PIPELINE_RULES.md) | Classification pipeline rules (608 lines) |

#### Rail Intelligence
| Document | Purpose |
|---|---|
| [rail_reference/README.md](rail_reference/README.md) | Rail reference overview (163 lines) |
| [rail_reference/SESCO_RAIL/trinity/TRINITY_RAILCAR_LEASE_SUMMARY.md](rail_reference/SESCO_RAIL/trinity/TRINITY_RAILCAR_LEASE_SUMMARY.md) | Trinity railcar lease summary (611 lines) |

#### Implementation & Technical Reports
| Document | Purpose |
|---|---|
| [Implementation_Toolkit_Code_Templates.md](Implementation_Toolkit_Code_Templates.md) | Code templates (627 lines) |
| [TECHNICAL_REPORT_SUMMARY.md](TECHNICAL_REPORT_SUMMARY.md) | Technical summary (470 lines) |
| [RESEARCH_SUMMARY_QuickStart.md](RESEARCH_SUMMARY_QuickStart.md) | Research quickstart (313 lines) |
| [project_summary_report.md](project_summary_report.md) | Project summary (611 lines) |

#### Master Indexes
| Document | Purpose |
|---|---|
| [INDEX_MASTER.md](INDEX_MASTER.md) | Master index (313 lines) |
| [architecture.md](architecture.md) | System architecture (39 lines) |
| [changelog.md](changelog.md) | Change log (10 lines) |

---

## Documentation Organization

### By Use Case

**"I'm new to this project"** → Start here:
1. Read [CLAUDE.md](../CLAUDE.md) (project directives)
2. Read [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) (understand structure)
3. Read [MIGRATION_STATUS.md](MIGRATION_STATUS.md) (see current state)

**"I need to write code"** → Read:
1. [TECHNICAL_STANDARDS.md](TECHNICAL_STANDARDS.md) (code style, data formats)
2. [Implementation_Toolkit_Code_Templates.md](Implementation_Toolkit_Code_Templates.md) (code templates)

**"I need to find facilities/classify industries"** → Read:
1. [NAICS_HTS_CODES.md](NAICS_HTS_CODES.md) (classification codes)
2. `02_TOOLSETS/facility_registry/METHODOLOGY.md` (EPA FRS usage)

**"I need to analyze barge economics"** → Read:
1. [Inland_Barge_Transportation_Economics_Research_Compendium.md](Inland_Barge_Transportation_Economics_Research_Compendium.md)
2. `02_TOOLSETS/barge_cost_model/METHODOLOGY.md`

**"I need USACE data"** → Read:
1. [USACE_QUICKSTART.md](USACE_QUICKSTART.md) (quick start)
2. [Mississippi_River_Inland_Waterway_Data_Sources.md](Mississippi_River_Inland_Waterway_Data_Sources.md) (comprehensive)

**"I need to classify vessel cargo"** → Read:
1. [manifest_README.md](manifest_README.md) (Panjiva processing)
2. [PIPELINE_RULES.md](PIPELINE_RULES.md) (classification rules)
3. `02_TOOLSETS/vessel_intelligence/METHODOLOGY.md`

**"I need rail data/analysis"** → Read:
1. [rail_reference/README.md](rail_reference/README.md)
2. `02_TOOLSETS/rail_cost_model/METHODOLOGY.md`
3. `02_TOOLSETS/rail_intelligence/README.md`

---

## Document Categories

### Platform Documentation (Essential)
- CLAUDE.md (project directives) — 247 lines
- DIRECTORY_STRUCTURE.md (complete tree) — 300+ lines
- MIGRATION_STATUS.md (tracking) — 350+ lines
- TECHNICAL_STANDARDS.md (code/data standards) — 600+ lines
- NAICS_HTS_CODES.md (classification codes) — 450+ lines

### Research Compendia (Deep Background)
- Inland barge economics — 711 lines
- Mississippi River data sources — 759 lines
- Wetzstein dissertation — 464 lines
- USACE historical guide — 444 lines

### Toolset-Specific (Methodology)
- See `02_TOOLSETS/{toolset}/METHODOLOGY.md` for each toolset
- vessel_intelligence: 13,000 words
- barge_cost_model: 223 lines
- rail_cost_model: TBD

### Implementation Guides (How-To)
- Implementation toolkit — 627 lines
- Code templates — embedded in Implementation_Toolkit
- USACE quickstart — 167 lines
- Research quickstart — 313 lines

### Reference Material
- Master index — 313 lines
- Technical report summary — 470 lines
- Project summary — 611 lines
- Architecture — 39 lines

---

## File Naming Conventions

**UPPERCASE.md** — Top-level essential docs (CLAUDE.md, DIRECTORY_STRUCTURE.md, MIGRATION_STATUS.md)
**Title_Case.md** — Research compendia, guides, toolkits
**lowercase.md** — Architecture, changelog, index files

---

## Maintenance

### When to Update This Documentation

**CLAUDE.md** — Only for critical directive changes (keep under 300 lines)
**DIRECTORY_STRUCTURE.md** — When major folders/toolsets are added
**MIGRATION_STATUS.md** — After each project migration or toolset completion
**TECHNICAL_STANDARDS.md** — When standards change (rare)
**NAICS_HTS_CODES.md** — When new commodity modules are added

### Document Owners

**Platform Documentation:**
- Maintained by: Claude Code (automated updates during sessions)
- Review frequency: After major milestones

**Research Compendia:**
- Maintained by: William S. Davis III (domain knowledge)
- Review frequency: Annual or when new research emerges

**Toolset Methodology:**
- Maintained by: Individual toolset developers
- Review frequency: When methodology changes

---

## Quick Reference Card

```
📁 project_master_reporting/
├── CLAUDE.md                          ← START HERE (project directives)
├── 01_DATA_SOURCES/                   ← Raw data
├── 02_TOOLSETS/                       ← Analysis engines
│   └── {toolset}/METHODOLOGY.md       ← How each toolset works
├── 03_COMMODITY_MODULES/              ← Commodity verticals
├── 04_REPORTS/                        ← Generated reports
└── 05_DOCUMENTATION/                  ← YOU ARE HERE
    ├── DIRECTORY_STRUCTURE.md         ← Full directory tree
    ├── MIGRATION_STATUS.md            ← What's done/in progress
    ├── TECHNICAL_STANDARDS.md         ← Code/data standards
    ├── NAICS_HTS_CODES.md             ← Classification codes
    └── README.md                      ← This file
```

---

## Need Help?

- **General platform questions:** Read CLAUDE.md first
- **Can't find something:** Check DIRECTORY_STRUCTURE.md
- **Want to know progress:** Check MIGRATION_STATUS.md
- **Need to write code:** Check TECHNICAL_STANDARDS.md
- **Need classification codes:** Check NAICS_HTS_CODES.md
- **Deep research:** Browse research compendia in this folder

For specific toolset usage, always check `02_TOOLSETS/{toolset}/README.md` first.
