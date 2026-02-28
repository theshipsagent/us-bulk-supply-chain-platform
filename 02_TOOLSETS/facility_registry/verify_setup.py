"""Quick setup verification script."""

import sys
from pathlib import Path

print("Verifying EPA FRS Analytics Tool setup...")
print("="*80)

# Check Python version
print(f"\nPython version: {sys.version}")
if sys.version_info < (3, 11):
    print("[!] Warning: Python 3.11+ recommended")
else:
    print("[OK] Python version OK")

# Check required directories
dirs = [
    "config",
    "data/raw",
    "data/processed",
    "src/etl",
    "src/analyze",
    "src/harmonize",
    "src/geo",
    "src/export"
]

print("\nChecking directories:")
for d in dirs:
    if Path(d).exists():
        print(f"[OK] {d}")
    else:
        print(f"[MISS] {d} missing")

# Check key files
files = [
    "requirements.txt",
    "config/settings.yaml",
    "cli.py",
    "src/etl/download.py",
    "src/etl/ingest.py",
    "src/analyze/query_engine.py",
    "src/analyze/stats.py"
]

print("\nChecking key files:")
for f in files:
    if Path(f).exists():
        print(f"[OK] {f}")
    else:
        print(f"[MISS] {f} missing")

# Try importing dependencies
print("\nChecking dependencies:")
dependencies = {
    'click': 'Click',
    'duckdb': 'DuckDB',
    'pandas': 'Pandas',
    'yaml': 'PyYAML',
    'requests': 'Requests',
    'tqdm': 'tqdm',
    'tabulate': 'tabulate'
}

missing = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"[OK] {name}")
    except ImportError:
        print(f"[MISS] {name} - not installed")
        missing.append(name)

if missing:
    print(f"\n[!] Missing dependencies. Install with:")
    print("   pip install -r requirements.txt")
else:
    print("\n[OK] All dependencies installed!")

print("\n" + "="*80)
print("Setup verification complete!")
print("\nNext steps:")
print("1. python cli.py download echo")
print("2. python cli.py ingest echo")
print("3. python cli.py query facilities --state VA")
