"""Restore the DuckDB database from a backup."""

import shutil
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python scripts/restore_database.py <backup_filename>")
    print("\nAvailable backups:")
    backup_dir = Path("data/backups")
    if backup_dir.exists():
        for backup in sorted(backup_dir.glob("*.duckdb*")):
            size = backup.stat().st_size / (1024**3)
            print(f"  {backup.name} ({size:.2f} GB)")
    sys.exit(1)

backup_name = sys.argv[1]
backup_path = Path("data/backups") / backup_name
db_path = Path("data/frs.duckdb")

if not backup_path.exists():
    print(f"Error: Backup not found: {backup_path}")
    sys.exit(1)

print(f"⚠️  WARNING: This will overwrite the current database!")
print(f"Source: {backup_path}")
print(f"Target: {db_path}")
response = input("\nContinue? (yes/no): ")

if response.lower() != 'yes':
    print("Restore cancelled.")
    sys.exit(0)

# Restore
shutil.copy2(backup_path, db_path)
print(f"[OK] Database restored from {backup_name}")
