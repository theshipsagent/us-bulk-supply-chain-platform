"""Backup the DuckDB database before making changes."""

import shutil
from pathlib import Path
from datetime import datetime

# Database path
db_path = Path("data/frs.duckdb")
backup_dir = Path("data/backups")

# Create backups directory
backup_dir.mkdir(exist_ok=True)

# Create timestamped backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = backup_dir / f"frs.duckdb.backup_{timestamp}"

print(f"Creating backup: {backup_path}")
print(f"Source: {db_path}")
print(f"Size: {db_path.stat().st_size / (1024**3):.2f} GB")

# Copy database
shutil.copy2(db_path, backup_path)

print(f"[OK] Backup created successfully!")
print(f"\nTo restore:")
print(f'  python scripts/restore_database.py {backup_path.name}')

# Also create named backup for current phase
phase_backup = backup_dir / "frs.duckdb.backup_before_harmonization_bake"
shutil.copy2(db_path, phase_backup)
print(f"\n[OK] Phase backup: {phase_backup.name}")
