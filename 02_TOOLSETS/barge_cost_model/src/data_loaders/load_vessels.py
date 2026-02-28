"""
Load vessel registry data from CSV into PostgreSQL.
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
        return None

    if value_type == 'int':
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    elif value_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    else:  # string
        return str(value).strip() if value else None


def load_vessels():
    """Load vessel registry from CSV to PostgreSQL."""

    print("=" * 80)
    print("VESSELS LOADER")
    print("=" * 80)

    # 1. Read CSV (handle BOM)
    print("\n[1/2] Reading vessels CSV...")
    csv_path = DATA_FILES["vessels"]
    print(f"File: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df):,} records from CSV")
    print(f"  Columns: {', '.join(df.columns)}")

    # 2. Insert to database (batch insert for large dataset)
    print("\n[2/2] Inserting to PostgreSQL...")

    with get_db_session() as db:
        # Clear existing data
        print("  Truncating vessels table...")
        db.execute(text("TRUNCATE TABLE vessels RESTART IDENTITY CASCADE;"))

        # Batch insert (1000 at a time)
        batch_size = 1000
        total_inserted = 0
        skipped = 0

        for i in tqdm(range(0, len(df), batch_size), desc="Inserting batches"):
            batch = df.iloc[i:i+batch_size]
            records = []

            for _, row in batch.iterrows():
                # Skip rows without IMO (primary key)
                imo = clean_value(row.get('IMO'))
                if not imo:
                    skipped += 1
                    continue

                record = {
                    'imo': imo,
                    'vessel_name': clean_value(row.get('Vessel')),
                    'design': clean_value(row.get('Design')),
                    'vessel_type': clean_value(row.get('Type')),
                    'dwt': clean_value(row.get('DWT'), 'int'),
                    'loa': clean_value(row.get('LOA'), 'float'),
                    'beam': clean_value(row.get('Beam'), 'float'),
                    'depth_m': clean_value(row.get('Depth(m)'), 'float'),
                    'gt': clean_value(row.get('GT'), 'int'),
                    'nrt': clean_value(row.get('NRT'), 'int'),
                    'grain': clean_value(row.get('Grain'), 'int'),
                    'tpc': clean_value(row.get('TPC'), 'float'),
                    'dwt_draft_m': clean_value(row.get('Dwt_Draft(m)'), 'float'),
                    'source_file': clean_value(row.get('Source_File')),
                }
                records.append(record)

            # Insert batch
            if records:
                db.execute(text("""
                    INSERT INTO vessels (
                        imo, vessel_name, design, vessel_type, dwt, loa, beam,
                        depth_m, gt, nrt, grain, tpc, dwt_draft_m, source_file
                    ) VALUES (
                        :imo, :vessel_name, :design, :vessel_type, :dwt, :loa, :beam,
                        :depth_m, :gt, :nrt, :grain, :tpc, :dwt_draft_m, :source_file
                    )
                """), records)

                total_inserted += len(records)

        db.commit()

    print(f"✓ Inserted {total_inserted:,} records to database")
    if skipped > 0:
        print(f"  (Skipped {skipped:,} records without IMO)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"CSV Records:        {len(df):,}")
    print(f"Database Records:   {total_inserted:,}")
    print(f"Skipped:            {skipped:,}")
    print(f"Unique Types:       {df['Type'].nunique():,}")
    print(f"Unique Designs:     {df['Design'].nunique():,}")
    print(f"Avg Beam:           {df['Beam'].mean():.2f} m")
    print(f"Avg Draft:          {df['Depth(m)'].mean():.2f} m")
    print(f"Avg DWT:            {df['DWT'].mean():.0f} tons")
    print("=" * 80)
    print("✓ Vessels loading complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        load_vessels()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
