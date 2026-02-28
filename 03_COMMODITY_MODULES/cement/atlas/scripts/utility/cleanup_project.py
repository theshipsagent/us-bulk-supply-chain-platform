#!/usr/bin/env python3
"""Clean up project_cement_markets root and organize files."""

import shutil
from pathlib import Path

ROOT = Path("G:/My Drive/LLM/project_cement_markets")
ATLAS = ROOT / "atlas"
ARCHIVE = ROOT / "archive"

# === 1. Move loose PDFs to proper locations ===
print("=== MOVING LOOSE REPORTS ===")

reports_src = ATLAS / "data" / "source" / "reports"
cement_weekly = reports_src / "cement_weekly"
cement_weekly.mkdir(parents=True, exist_ok=True)

for f in ROOT.glob("Cement Weekly*.pdf"):
    dst = cement_weekly / f.name
    shutil.move(str(f), str(dst))
    print(f"  Moved {f.name} -> source/reports/cement_weekly/")

for f in ROOT.glob("Construction Materials*.pdf"):
    dst = reports_src / f.name
    try:
        shutil.copy2(str(f), str(dst))
        print(f"  Copied {f.name} -> source/reports/ (original kept - file locked)")
    except Exception as e:
        print(f"  SKIP {f.name}: {e}")

# === 2. Move USACE prompt to reference ===
usace = ROOT / "USACE_LPMS_Local_App_Prompt.md"
if usace.exists():
    ref = ATLAS / "data" / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(usace), str(ref / usace.name))
        print(f"  Moved {usace.name} -> reference/")
    except Exception:
        shutil.copy2(str(usace), str(ref / usace.name))
        print(f"  Copied {usace.name} -> reference/ (original kept)")

# === 3. Remove duplicate PDF (already in data/) ===
dup_pdf = ROOT / "US_Cement_Market_Intelligence_Report.pdf"
if dup_pdf.exists():
    try:
        dup_pdf.unlink()
        print("  Removed duplicate US_Cement_Market_Intelligence_Report.pdf from root")
    except Exception:
        print("  Note: Could not remove duplicate PDF (file locked)")

# === 4. Remove junk pip install file ===
pip_file = ROOT / "pip install duckdb pandas rapidfuzz openpyxl.txt"
if pip_file.exists():
    try:
        pip_file.unlink()
        print("  Removed pip install text file")
    except Exception:
        print("  Note: Could not remove pip file (file locked)")

# === 5. Move read_cement to archive (but skip .venv and .git bloat) ===
print("\n=== ARCHIVING read_cement ===")
read_cement = ROOT / "read_cement"
if read_cement.exists():
    archive_rc = ARCHIVE / "read_cement"
    archive_rc.mkdir(parents=True, exist_ok=True)

    # Copy only valuable files (skip .venv, .git, PythonProject)
    for item in read_cement.iterdir():
        if item.name in ('.venv', '.git', 'PythonProject', 'desktop.ini'):
            continue
        if item.is_file():
            shutil.copy2(str(item), str(archive_rc / item.name))
            print(f"  Archived {item.name}")
        elif item.is_dir():
            if item.name == 'Cement':
                # Copy Cement scripts but skip .venv and .git
                cement_dst = archive_rc / "Cement"
                cement_dst.mkdir(exist_ok=True)
                for sub in item.iterdir():
                    if sub.name in ('.venv', '.git', 'PythonProject', 'desktop.ini'):
                        continue
                    if sub.is_file():
                        shutil.copy2(str(sub), str(cement_dst / sub.name))
                        print(f"  Archived Cement/{sub.name}")
                    elif sub.is_dir() and sub.name == 'Cement':
                        scripts_dst = cement_dst / "Cement"
                        scripts_dst.mkdir(exist_ok=True)
                        for script in sub.glob("*"):
                            if script.name != 'desktop.ini':
                                shutil.copy2(str(script), str(scripts_dst / script.name))
                                print(f"  Archived Cement/Cement/{script.name}")
            elif item.name == 'usgs_minerals':
                # Already have USGS in ATLAS, just note it
                print(f"  Skipped usgs_minerals/ (already in ATLAS)")
            else:
                shutil.copytree(str(item), str(archive_rc / item.name),
                               ignore=shutil.ignore_patterns('.venv', '.git', 'desktop.ini'),
                               dirs_exist_ok=True)
                print(f"  Archived {item.name}/")

    # Now remove the read_cement directory
    print("\n  Removing read_cement/ directory (archived version preserved)...")
    try:
        shutil.rmtree(str(read_cement), ignore_errors=True)
        print("  Done - read_cement removed from root")
    except Exception as e:
        print(f"  Note: Could not fully remove read_cement/: {e}")

# === 6. Move data/ contents to atlas/data/ and remove duplicate ===
print("\n=== CONSOLIDATING data/ DIRECTORY ===")
root_data = ROOT / "data"
if root_data.exists():
    # The report PDF and report_data.json should be in atlas output
    output_dir = ATLAS / "output"
    output_dir.mkdir(exist_ok=True)

    for f in root_data.glob("*"):
        if f.name == 'desktop.ini':
            continue
        if f.name == 'atlas.duckdb':
            print(f"  Skipping duplicate atlas.duckdb in data/ (primary is atlas/data/)")
            continue
        if f.is_dir():
            continue
        try:
            shutil.copy2(str(f), str(output_dir / f.name))
            print(f"  Copied {f.name} -> atlas/output/")
        except Exception as e:
            print(f"  SKIP {f.name}: {e}")

    # Remove duplicate duckdb
    dup_db = root_data / "atlas.duckdb"
    if dup_db.exists():
        dup_db.unlink()
        print("  Removed duplicate atlas.duckdb from data/")

    # Try to remove now-empty data dir
    try:
        remaining = [f for f in root_data.iterdir() if f.name != 'desktop.ini']
        if not remaining:
            shutil.rmtree(str(root_data), ignore_errors=True)
            print("  Removed empty data/ directory")
        else:
            print(f"  data/ still has {len(remaining)} items, keeping")
    except Exception as e:
        print(f"  Note: Could not remove data/: {e}")

# === 7. Move industry_tracker into ATLAS ===
print("\n=== MOVING industry_tracker ===")
tracker = ROOT / "industry_tracker"
if tracker.exists():
    tracker_dst = ATLAS / "data" / "source" / "industry_tracker"
    tracker_dst.mkdir(parents=True, exist_ok=True)
    for f in tracker.iterdir():
        if f.name != 'desktop.ini' and f.is_file():
            shutil.copy2(str(f), str(tracker_dst / f.name))
            print(f"  Copied {f.name} -> source/industry_tracker/")
    shutil.rmtree(str(tracker), ignore_errors=True)
    print("  Removed industry_tracker/ from root")

print("\n=== CLEANUP COMPLETE ===")
print("\nFinal project structure:")
print("  project_cement_markets/")
print("  ├── .claude/                    (workspace config)")
print("  ├── archive/                    (archived old projects)")
print("  │   ├── tampa_study_original/   (full old project_cement)")
print("  │   └── read_cement/            (early scripts/data)")
print("  ├── atlas/                      (ATLAS system - one-stop-shop)")
print("  │   ├── config/                 (settings, NAICS, companies)")
print("  │   ├── data/                   (all data)")
print("  │   │   ├── atlas.duckdb        (master database)")
print("  │   │   ├── geospatial/         (GeoJSON files)")
print("  │   │   ├── reference/          (research, reports, RAG docs)")
print("  │   │   ├── source/             (USGS, trade, rail, reports)")
print("  │   │   ├── processed/          (clean intermediates)")
print("  │   │   └── work_product_archive/")
print("  │   ├── output/                 (generated reports)")
print("  │   ├── scripts/                (utility scripts)")
print("  │   ├── src/                    (ETL, harmonize, analytics)")
print("  │   └── cli.py                  (main CLI interface)")
print("  ├── ATLAS_ARCHITECTURE.md       (system design)")
print("  └── ATLAS_PHASE0_SUMMARY.md     (phase 0 report)")
