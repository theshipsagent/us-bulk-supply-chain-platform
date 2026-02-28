#!/usr/bin/env python3
"""Verify ATLAS installation and data load."""

import sys
from pathlib import Path

def check_structure():
    """Check directory structure."""
    print("\n" + "="*70)
    print("CHECKING DIRECTORY STRUCTURE")
    print("="*70)
    
    required_dirs = [
        "config", "data", "data/work_product_archive",
        "src", "src/etl", "src/harmonize", "src/analytics", "src/utils"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        status = "[OK]" if path.exists() else "[MISSING]"
        print(f"  {status} {dir_path}/")
    
    required_files = [
        "config/settings.yaml",
        "config/naics_cement.yaml",
        "config/target_companies.yaml",
        "src/utils/db.py",
        "src/etl/epa_frs.py",
        "src/harmonize/entity_resolver.py",
        "src/analytics/supply.py",
        "cli.py",
        "README.md",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        status = "[OK]" if path.exists() else "[MISSING]"
        print(f"  {status} {file_path}")

def check_database():
    """Check database and data."""
    print("\n" + "="*70)
    print("CHECKING DATABASE")
    print("="*70)
    
    try:
        from src.utils.db import get_atlas_connection
        
        db_path = Path("../data/atlas.duckdb")
        if not db_path.exists():
            print("  [MISSING] Database file not found")
            return
        
        print(f"  [OK] Database file exists ({db_path.stat().st_size / 1024 / 1024:.1f} MB)")
        
        con = get_atlas_connection(read_only=True)
        
        # Check tables
        tables = con.execute("SHOW TABLES").fetchall()
        print(f"  [OK] Found {len(tables)} tables")
        
        # Check record counts
        fac_count = con.execute("SELECT COUNT(*) FROM frs_facilities").fetchone()[0]
        print(f"  [OK] Facilities: {fac_count:,}")
        
        state_count = con.execute("SELECT COUNT(DISTINCT state) FROM frs_facilities").fetchone()[0]
        print(f"  [OK] States covered: {state_count}")
        
        con.close()
        
    except Exception as e:
        print(f"  [ERROR] {e}")

def check_imports():
    """Check Python imports."""
    print("\n" + "="*70)
    print("CHECKING PYTHON IMPORTS")
    print("="*70)
    
    modules = [
        'duckdb', 'pandas', 'yaml', 'click', 
        'rapidfuzz', 'openpyxl', 'tabulate'
    ]
    
    for mod in modules:
        try:
            __import__(mod)
            print(f"  [OK] {mod}")
        except ImportError:
            print(f"  [MISSING] {mod} - run: pip install {mod}")

def main():
    print("="*70)
    print("ATLAS INSTALLATION VERIFICATION")
    print("="*70)
    
    check_structure()
    check_imports()
    check_database()
    
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Install missing dependencies: pip install -r requirements.txt")
    print("  2. Load data (if not done): python cli.py refresh")
    print("  3. Query facilities: python cli.py query --state TX")
    print("  4. View statistics: python cli.py stats")

if __name__ == "__main__":
    main()
