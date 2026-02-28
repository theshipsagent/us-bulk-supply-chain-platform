#!/usr/bin/env python3
"""Reorganize old project_cement files into ATLAS knowledge base."""

import shutil
from pathlib import Path

OLD = Path("G:/My Drive/LLM/project_cement")
NEW = Path("G:/My Drive/LLM/project_cement_markets")
ATLAS = NEW / "atlas"

# === 1. GEOSPATIAL FILES ===
geo_src = OLD / "geospatial"
geo_dst = ATLAS / "data" / "geospatial"

# Facilities
facilities = {
    "cement_plants_florida_gulf.geojson",
    "north_american_cement_plants.geojson",
    "us_cement_plants_national.geojson",
    "import_terminals_florida.geojson",
    "florida_readymix_plants.geojson",
    "florida_readymix_compact.json",
    "gulf_coast_readymix_plants.geojson",
    "gulf_non_fl_compact.json",
    "global_cement_producers.geojson",
}

trade_flows = {
    "import_origins.geojson",
    "global_trade_flows_detailed.geojson",
    "trade_flows_weighted.geojson",
    "shipping_routes.geojson",
    "us_ports_cement_imports.geojson",
    "us_cement_import_ports_weighted.geojson",
    "caribbean_markets.geojson",
}

transport = {
    "class1_rail_part1.geojson",
    "us_marine_highways.geojson",
    "port_redwing_trucking_radius.geojson",
}

demand = {
    "florida_counties_demand.geojson",
    "us_states_cement.geojson",
}

print("=== GEOSPATIAL FILES ===")
for category, files, subdir in [
    ("facilities", facilities, "facilities"),
    ("trade_flows", trade_flows, "trade_flows"),
    ("transport", transport, "transport"),
    ("demand", demand, "demand"),
]:
    dst = geo_dst / subdir
    dst.mkdir(parents=True, exist_ok=True)
    for f in files:
        src_file = geo_src / f
        if src_file.exists():
            shutil.copy2(src_file, dst / f)
            print(f"  Copied {f} -> geospatial/{subdir}/")
        else:
            print(f"  SKIP {f} (not found)")

# Copy metadata
meta = geo_src / "GEOJSON_METADATA.md"
if meta.exists():
    shutil.copy2(meta, geo_dst / "GEOJSON_METADATA.md")
    print("  Copied GEOJSON_METADATA.md -> geospatial/")

# === 2. RESEARCH DOCUMENTS ===
print("\n=== RESEARCH DOCUMENTS ===")
research_dst = ATLAS / "data" / "reference" / "research"
research_dst.mkdir(parents=True, exist_ok=True)

research_src = OLD / "research"
if research_src.exists():
    for f in research_src.glob("*.md"):
        if f.name != "desktop.ini":
            shutil.copy2(f, research_dst / f.name)
            print(f"  Copied {f.name} -> reference/research/")

# === 3. FLORIDA/TAMPA REPORTS ===
print("\n=== FLORIDA/TAMPA REPORTS ===")
reports_dst = ATLAS / "data" / "reference" / "reports" / "tampa_study"
reports_dst.mkdir(parents=True, exist_ok=True)

# Drafts
drafts_src = OLD / "drafts"
if drafts_src.exists():
    for f in drafts_src.glob("*.md"):
        shutil.copy2(f, reports_dst / f.name)
        print(f"  Copied {f.name} -> reference/reports/tampa_study/")

# Key HTML reports
reports_src = OLD / "reports"
if reports_src.exists():
    key_reports = [
        "FLORIDA_CEMENT_MARKET_REPORT.html",
        "FLORIDA_CEMENT_EXECUTIVE_SUMMARY.html",
        "TAMPA_CEMENT_MARKET_STUDY.md",
        "TAMPA_MARKET_COMPREHENSIVE_REPORT.html",
        "CEMENT_MARKET_INTELLIGENCE_REPORT.html",
        "CEMENT_MARKET_NATIONAL_DASHBOARD.html",
        "CEMENT_INFRASTRUCTURE_MAP.html",
        "GLOBAL_TRADE_FLOW_MAP.html",
        "READYMIX_CUSTOMER_MAP.html",
        "PHASE_1_CRITICAL_REVIEW_AND_NEXT_STEPS.html",
        "INDEX.html",
    ]
    for name in key_reports:
        f = reports_src / name
        if f.exists():
            shutil.copy2(f, reports_dst / name)
            print(f"  Copied {name} -> reference/reports/tampa_study/")
        else:
            print(f"  SKIP {name} (not found)")

# Root PDFs
for pdf_name in [
    "Tampa Bay Cement Market Study - Comprehensive Analysis.pdf",
    "Tampa Bay Cement Market Study - SESCO Cement Corp.pdf",
]:
    pdf = OLD / pdf_name
    if pdf.exists():
        shutil.copy2(pdf, reports_dst / pdf_name)
        print(f"  Copied {pdf_name} -> reference/reports/tampa_study/")

# === 4. PANJIVA EXPORTS (we don't have this yet) ===
print("\n=== TRADE DATA ===")
trade_dst = ATLAS / "data" / "source" / "trade" / "panjiva"
trade_dst.mkdir(parents=True, exist_ok=True)

exports = OLD / "data" / "panjiva_cement_exports.csv"
if exports.exists():
    shutil.copy2(exports, trade_dst / "panjiva_cement_exports.csv")
    print(f"  Copied panjiva_cement_exports.csv -> source/trade/panjiva/")

# Panjiva trade metadata
trade_md = OLD / "data" / "panjiva_cement_trade.md"
if trade_md.exists():
    shutil.copy2(trade_md, trade_dst / "panjiva_cement_trade.md")
    print(f"  Copied panjiva_cement_trade.md -> source/trade/panjiva/")

# === 5. SCRIPTS ===
print("\n=== SCRIPTS ===")
scripts_src = OLD / "scripts" / "upload_to_arcgis.py"
if scripts_src.exists():
    scripts_dst = ATLAS / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scripts_src, scripts_dst / "upload_to_arcgis.py")
    print(f"  Copied upload_to_arcgis.py -> scripts/")

# === 6. SESSION HANDOVER ===
print("\n=== PROJECT NOTES ===")
handover = OLD / "SESSION_HANDOVER.md"
if handover.exists():
    shutil.copy2(handover, reports_dst / "SESSION_HANDOVER.md")
    print(f"  Copied SESSION_HANDOVER.md -> reference/reports/tampa_study/")

geojson_meta = OLD / "geojsonmetadata.md"
if geojson_meta.exists():
    shutil.copy2(geojson_meta, geo_dst / "geojsonmetadata_detailed.md")
    print(f"  Copied geojsonmetadata.md -> geospatial/")

cementreport = OLD / "cementreport.md"
if cementreport.exists():
    shutil.copy2(cementreport, reports_dst / "cementreport_initial.md")
    print(f"  Copied cementreport.md -> reference/reports/tampa_study/")

print("\n=== DONE ===")
print("All valuable files integrated into ATLAS knowledge base.")
