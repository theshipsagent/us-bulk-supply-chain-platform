"""
Load locks facility data from BTS CSV into PostgreSQL.
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


def clean_value(value, value_type='str', max_length=None):
    """Clean and convert CSV values, handling nulls and truncating strings."""
    if pd.isna(value):
        return None

    if value_type == 'int':
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    elif value_type == 'float':
        try:
            result = float(value)
            # Clamp to NUMERIC(12, 6) range
            if result > 999999.999999:
                return 999999.999999
            elif result < -999999.999999:
                return -999999.999999
            return result
        except (ValueError, TypeError):
            return None
    else:  # string
        result = str(value).strip() if value else None
        if result and max_length:
            result = result[:max_length]
        return result


def load_locks():
    """Load locks from CSV to PostgreSQL."""

    print("=" * 80)
    print("LOCKS LOADER")
    print("=" * 80)

    # 1. Read CSV (handle BOM)
    print("\n[1/2] Reading locks CSV...")
    csv_path = DATA_FILES["locks"]
    print(f"File: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df):,} records from CSV")
    print(f"  Columns: {', '.join(df.columns[:15])}...")

    # 2. Insert to database
    print("\n[2/2] Inserting to PostgreSQL...")

    with get_db_session() as db:
        # Clear existing data
        print("  Truncating locks table...")
        db.execute(text("TRUNCATE TABLE locks RESTART IDENTITY CASCADE;"))

        # Prepare records
        records = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing records"):
            record = {
                'objectid': clean_value(row['OBJECTID'], 'int'),
                'id': clean_value(row.get('ID'), 'int'),
                'ndccode': clean_value(row.get('NDCCODE'), max_length=50),
                'region': clean_value(row.get('REGION'), max_length=10),
                'rivercd': clean_value(row.get('RIVERCD'), max_length=10),
                'lockcd': clean_value(row.get('LOCKCD'), max_length=10),
                'chmbcd': clean_value(row.get('CHMBCD'), max_length=10),
                'nochmb': clean_value(row.get('NOCHMB'), 'int'),
                'pmsdata': clean_value(row.get('PMSDATA'), max_length=5),
                'navstr': clean_value(row.get('NAVSTR'), max_length=100),
                'chambn': clean_value(row.get('CHAMBN'), max_length=50),
                'chb1': clean_value(row.get('CHB1'), max_length=10),
                'str1': clean_value(row.get('STR1'), max_length=10),
                'pmsname': clean_value(row.get('PMSNAME'), max_length=100),
                'status': clean_value(row.get('STATUS'), max_length=50),
                'river': clean_value(row.get('RIVER'), max_length=100),
                'rivermi': clean_value(row.get('RIVERMI'), 'float'),
                'bank': clean_value(row.get('BANK'), max_length=10),
                'lift': clean_value(row.get('LIFT'), 'float'),
                'length': clean_value(row.get('LENGTH'), 'float'),
                'chmbul': clean_value(row.get('CHMBUL'), 'float'),
                'width': clean_value(row.get('WIDTH'), 'float'),
                'chmbuw': clean_value(row.get('CHMBUW'), 'float'),
                'audpa': clean_value(row.get('AUDPA'), 'float'),
                'audpb': clean_value(row.get('AUDPB'), 'float'),
                'updpthms': clean_value(row.get('UPDPTHMS'), 'float'),
                'lwdpthms': clean_value(row.get('LWDPTHMS'), 'float'),
                'yearopen': clean_value(row.get('YEAROPEN'), 'int'),
                'gatetype': clean_value(row.get('GATETYPE'), max_length=50),
                'gate': clean_value(row.get('GATE'), max_length=50),
                'chnlgth': clean_value(row.get('CHNLGTH'), 'float'),
                'chndptha': clean_value(row.get('CHNDPTHA'), 'float'),
                'chndpthb': clean_value(row.get('CHNDPTHB'), 'float'),
                'chnwdtha': clean_value(row.get('CHNWDTHA'), 'float'),
                'chnwdthb': clean_value(row.get('CHNWDTHB'), 'float'),
                'wwprjct': clean_value(row.get('WWPRJCT'), max_length=100),
                'mooring': clean_value(row.get('MOORING'), max_length=10),
                'multi': clean_value(row.get('MULTI'), max_length=10),
                'division': clean_value(row.get('DIVISION'), max_length=50),
                'district': clean_value(row.get('DISTRICT'), max_length=50),
                'state': clean_value(row.get('STATE'), max_length=2),
                'maint1': clean_value(row.get('MAINT1'), max_length=50),
                'oper1': clean_value(row.get('OPER1'), max_length=50),
                'owner1': clean_value(row.get('OWNER1'), max_length=50),
                'town': clean_value(row.get('TOWN'), max_length=100),
                'county1': clean_value(row.get('COUNTY1'), max_length=100),
                'mooring_r': clean_value(row.get('MOORING_R'), max_length=50),
                'x': clean_value(row.get('x'), 'float'),
                'y': clean_value(row.get('y'), 'float'),
            }
            records.append(record)

        # Insert all records
        db.execute(text("""
            INSERT INTO locks (
                objectid, id, ndccode, region, rivercd, lockcd, chmbcd, nochmb,
                pmsdata, navstr, chambn, chb1, str1, pmsname, status, river,
                rivermi, bank, lift, length, chmbul, width, chmbuw, audpa, audpb,
                updpthms, lwdpthms, yearopen, gatetype, gate, chnlgth, chndptha,
                chndpthb, chnwdtha, chnwdthb, wwprjct, mooring, multi, division,
                district, state, maint1, oper1, owner1, town, county1, mooring_r,
                x, y
            ) VALUES (
                :objectid, :id, :ndccode, :region, :rivercd, :lockcd, :chmbcd, :nochmb,
                :pmsdata, :navstr, :chambn, :chb1, :str1, :pmsname, :status, :river,
                :rivermi, :bank, :lift, :length, :chmbul, :width, :chmbuw, :audpa, :audpb,
                :updpthms, :lwdpthms, :yearopen, :gatetype, :gate, :chnlgth, :chndptha,
                :chndpthb, :chnwdtha, :chnwdthb, :wwprjct, :mooring, :multi, :division,
                :district, :state, :maint1, :oper1, :owner1, :town, :county1, :mooring_r,
                :x, :y
            )
        """), records)

        db.commit()

    print(f"✓ Inserted {len(records):,} records to database")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"CSV Records:        {len(df):,}")
    print(f"Database Records:   {len(records):,}")
    print(f"Unique Rivers:      {df['RIVER'].nunique():,}")
    print(f"Unique States:      {df['STATE'].nunique():,}")
    print(f"Avg Lock Length:    {df['LENGTH'].mean():.2f} feet")
    print(f"Avg Lock Width:     {df['WIDTH'].mean():.2f} feet")
    print("=" * 80)
    print("✓ Locks loading complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        load_locks()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
