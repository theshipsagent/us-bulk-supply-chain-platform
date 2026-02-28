#!/usr/bin/env python3
"""Move analysis scripts to organized locations."""

import shutil
from pathlib import Path

ATLAS = Path("G:/My Drive/LLM/project_cement_markets/atlas")

# Create analysis directory
analysis = ATLAS / "scripts" / "analysis"
analysis.mkdir(parents=True, exist_ok=True)

# Move analysis scripts
analysis_scripts = [
    "analyze_nc_va_market.py",
    "analyze_port_markets.py",
    "canada_analysis.py",
    "check_nc_ports.py",
    "query_frs_cement.py",
]

for name in analysis_scripts:
    src = ATLAS / name
    if src.exists():
        shutil.move(str(src), str(analysis / name))
        print(f"  Moved {name} -> scripts/analysis/")

# Move utility scripts
utility = ATLAS / "scripts" / "utility"
utility.mkdir(parents=True, exist_ok=True)

utility_scripts = [
    "cleanup_project.py",
    "reorganize_files.py",
]

for name in utility_scripts:
    src = ATLAS / name
    if src.exists():
        shutil.move(str(src), str(utility / name))
        print(f"  Moved {name} -> scripts/utility/")

# Keep in atlas root (main tools):
# - cli.py (main CLI)
# - extract_report_data.py (report pipeline)
# - generate_market_report.py (report pipeline)
# - verify_installation.py (setup tool)

print("\nKept in atlas root: cli.py, extract_report_data.py, generate_market_report.py, verify_installation.py")
print("Done!")
