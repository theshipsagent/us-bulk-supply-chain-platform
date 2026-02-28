"""
Load link tonnages (cargo volumes) data from BTS CSV into PostgreSQL.
Requires waterway_links table to be loaded first (LINKNUM foreign key).
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import text
from tqdm import tqdm

from src.config.settings import settings, DATA_FILES
from src.config.database import get_db_session


def clean_value(value, value_type='str'):
    """Clean and convert CSV values, handling nulls."""
    if pd.isna(value):
        return None if value_type == 'str' else 0  # Default to 0 for numeric

    if value_type == 'int':
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    elif value_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    else:  # string
        return str(value).strip() if value else None


def load_tonnages():
    """Load link tonnages from CSV to PostgreSQL."""

    print("=" * 80)
    print("LINK TONNAGES LOADER")
    print("=" * 80)

    # 1. Read CSV (handle BOM)
    print("\n[1/2] Reading link tonnages CSV...")
    csv_path = DATA_FILES["link_tonnages"]
    print(f"File: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df):,} records from CSV")
    print(f"  Columns: {', '.join(df.columns[:10])}...")

    # 2. Insert to database
    print("\n[2/2] Inserting to PostgreSQL...")

    with get_db_session() as db:
        # Clear existing data
        print("  Truncating link_tonnages table...")
        db.execute(text("TRUNCATE TABLE link_tonnages RESTART IDENTITY CASCADE;"))

        # Batch insert (1000 at a time)
        batch_size = 1000
        total_inserted = 0

        for i in tqdm(range(0, len(df), batch_size), desc="Inserting batches"):
            batch = df.iloc[i:i+batch_size]
            records = []

            for _, row in batch.iterrows():
                record = {
                    'objectid': clean_value(row['OBJECTID'], 'int'),
                    'linknum': clean_value(row['LINKNUM'], 'int'),
                    'totalup': clean_value(row.get('TOTALUP'), 'int'),
                    'totaldown': clean_value(row.get('TOTALDOWN'), 'int'),
                    'coalup': clean_value(row.get('COALUP'), 'int'),
                    'coaldown': clean_value(row.get('COALDOWN'), 'int'),
                    'petrolup': clean_value(row.get('PETROLUP'), 'int'),
                    'petrodown': clean_value(row.get('PETRODOWN'), 'int'),
                    'chemup': clean_value(row.get('CHEMUP'), 'int'),
                    'chemdown': clean_value(row.get('CHEMDOWN'), 'int'),
                    'crmatup': clean_value(row.get('CRMATUP'), 'int'),
                    'crmatdown': clean_value(row.get('CRMATDOWN'), 'int'),
                    'manuup': clean_value(row.get('MANUUP'), 'int'),
                    'manudown': clean_value(row.get('MANUDOWN'), 'int'),
                    'farmup': clean_value(row.get('FARMUP'), 'int'),
                    'farmdown': clean_value(row.get('FARMDOWN'), 'int'),
                    'machup': clean_value(row.get('MACHUP'), 'int'),
                    'machdown': clean_value(row.get('MACHDOWN'), 'int'),
                    'wasteup': clean_value(row.get('WASTEUP'), 'int'),
                    'wastedown': clean_value(row.get('WASTEDOWN'), 'int'),
                    'unkwnup': clean_value(row.get('UNKWNUP'), 'int'),
                    'unkwdown': clean_value(row.get('UNKWDOWN'), 'int'),
                    'shape_length': clean_value(row.get('Shape__Length'), 'float'),
                }
                records.append(record)

            # Insert batch
            db.execute(text("""
                INSERT INTO link_tonnages (
                    objectid, linknum, totalup, totaldown, coalup, coaldown,
                    petrolup, petrodown, chemup, chemdown, crmatup, crmatdown,
                    manuup, manudown, farmup, farmdown, machup, machdown,
                    wasteup, wastedown, unkwnup, unkwdown, shape_length
                ) VALUES (
                    :objectid, :linknum, :totalup, :totaldown, :coalup, :coaldown,
                    :petrolup, :petrodown, :chemup, :chemdown, :crmatup, :crmatdown,
                    :manuup, :manudown, :farmup, :farmdown, :machup, :machdown,
                    :wasteup, :wastedown, :unkwnup, :unkwdown, :shape_length
                )
            """), records)

            total_inserted += len(records)

        db.commit()

    print(f"✓ Inserted {total_inserted:,} records to database")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"CSV Records:        {len(df):,}")
    print(f"Database Records:   {total_inserted:,}")
    print(f"Total Upstream:     {df['TOTALUP'].sum():,.0f} tons")
    print(f"Total Downstream:   {df['TOTALDOWN'].sum():,.0f} tons")
    print(f"Coal Upstream:      {df['COALUP'].sum():,.0f} tons")
    print(f"Coal Downstream:    {df['COALDOWN'].sum():,.0f} tons")
    print(f"Farm Upstream:      {df['FARMUP'].sum():,.0f} tons")
    print(f"Farm Downstream:    {df['FARMDOWN'].sum():,.0f} tons")
    print("=" * 80)
    print("✓ Link tonnages loading complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        load_tonnages()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
