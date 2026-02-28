"""
Bake parent company harmonization into facilities table.

SAFETY: This script adds a column but does NOT modify original data.

Steps:
1. Verify parent_company_lookup table exists
2. Check current facilities table schema
3. Backup database (if not already done)
4. Add parent_company column to facilities table
5. Update parent_company values from lookup table
6. Verify no data loss
7. Print summary
"""

import duckdb
from pathlib import Path
import sys

print("="*100)
print("BAKING PARENT COMPANY HARMONIZATION INTO DATABASE")
print("="*100)

# Connect to database
db_path = Path("data/frs.duckdb")
if not db_path.exists():
    print(f"Error: Database not found at {db_path}")
    sys.exit(1)

conn = duckdb.connect(str(db_path))

# Step 1: Verify parent_company_lookup exists
print("\n[Step 1] Verifying parent_company_lookup table...")
tables = conn.execute("SHOW TABLES").df()
if 'parent_company_lookup' not in tables['name'].values:
    print("❌ Error: parent_company_lookup table not found!")
    print("Run: python cli.py harmonize create-parent-table")
    sys.exit(1)

lookup_count = conn.execute("SELECT COUNT(*) FROM parent_company_lookup").fetchone()[0]
print(f"[OK] parent_company_lookup table exists with {lookup_count:,} entries")

# Step 2: Check current facilities schema
print("\n[Step 2] Checking facilities table schema...")
schema = conn.execute("DESCRIBE facilities").df()
print(schema)

original_count = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
print(f"\n[OK] Facilities table has {original_count:,} rows")

# Check if parent_company column already exists
if 'parent_company' in schema['column_name'].values:
    print("\n⚠️  parent_company column already exists!")
    response = input("Recreate it? This will reset all parent company values (yes/no): ")
    if response.lower() == 'yes':
        print("Dropping parent_company column...")
        conn.execute("ALTER TABLE facilities DROP COLUMN parent_company")
        print("[OK] Column dropped")
    else:
        print("Skipping column creation.")
        sys.exit(0)

# Step 3: Create backup reminder
print("\n[Step 3] Backup check...")
backup_dir = Path("data/backups")
if backup_dir.exists():
    backups = list(backup_dir.glob("*.duckdb*"))
    if backups:
        latest = max(backups, key=lambda p: p.stat().st_mtime)
        print(f"[OK] Latest backup found: {latest.name}")
    else:
        print("⚠️  No backups found!")
else:
    print("⚠️  No backups found!")

response = input("\nHave you created a backup? (yes/no): ")
if response.lower() != 'yes':
    print("\n⚠️  Please create a backup first:")
    print("  python scripts/backup_database.py")
    sys.exit(1)

# Step 4: Add parent_company column
print("\n[Step 4] Adding parent_company column to facilities table...")
try:
    conn.execute("ALTER TABLE facilities ADD COLUMN parent_company VARCHAR")
    print("[OK] Column added successfully")
except Exception as e:
    print(f"❌ Error adding column: {e}")
    sys.exit(1)

# Step 5: Update parent_company values
print("\n[Step 5] Updating parent_company values from lookup table...")
print("This may take a few minutes for 3M+ rows...")

try:
    # Update using JOIN with lookup table
    update_query = """
        UPDATE facilities
        SET parent_company = (
            SELECT p.parent_company
            FROM parent_company_lookup p
            WHERE p.fac_name_original = facilities.fac_name
        )
    """
    conn.execute(update_query)
    print("[OK] Parent company values updated")
except Exception as e:
    print(f"❌ Error updating values: {e}")
    print("\nAttempting to restore...")
    print("Run: python scripts/restore_database.py frs.duckdb.backup_before_harmonization_bake")
    sys.exit(1)

# Step 6: Verify no data loss
print("\n[Step 6] Verifying data integrity...")

new_count = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
print(f"Original row count: {original_count:,}")
print(f"New row count:      {new_count:,}")

if original_count != new_count:
    print("❌ ERROR: Row count mismatch! Data loss detected!")
    sys.exit(1)

print("[OK] No data loss - row counts match")

# Check how many facilities got parent companies
with_parent = conn.execute("SELECT COUNT(*) FROM facilities WHERE parent_company IS NOT NULL").fetchone()[0]
without_parent = conn.execute("SELECT COUNT(*) FROM facilities WHERE parent_company IS NULL").fetchone()[0]

print(f"\nParent company coverage:")
print(f"  With parent company:    {with_parent:,} ({with_parent/new_count*100:.1f}%)")
print(f"  Without parent company: {without_parent:,} ({without_parent/new_count*100:.1f}%)")

# Step 7: Print summary
print("\n[Step 7] Summary")
print("="*100)

# Show top parent companies
top_parents = conn.execute("""
    SELECT parent_company, COUNT(*) as count
    FROM facilities
    WHERE parent_company IS NOT NULL
    GROUP BY parent_company
    ORDER BY count DESC
    LIMIT 10
""").df()

print("\nTop 10 Parent Companies:")
for idx, row in top_parents.iterrows():
    print(f"  {row['parent_company']:40s}: {row['count']:,} facilities")

# Sample data to verify original names preserved
print("\nSample data (verifying original names preserved):")
sample = conn.execute("""
    SELECT registry_id, fac_name, parent_company, fac_state
    FROM facilities
    WHERE parent_company IS NOT NULL
    LIMIT 5
""").df()
print(sample.to_string(index=False))

print("\n" + "="*100)
print("[SUCCESS] HARMONIZATION SUCCESSFULLY BAKED INTO DATABASE!")
print("="*100)

print("\nDatabase schema updated:")
print("  • parent_company column added to facilities table")
print("  • Original fac_name column UNCHANGED")
print("  • All original data PRESERVED")
print(f"  • {with_parent:,} facilities now have parent company assigned")

print("\nNext steps:")
print("  1. Update PROJECT_STATUS.md")
print("  2. Test queries with parent_company")
print("  3. Update query_engine.py to include parent_company in results")

conn.close()
