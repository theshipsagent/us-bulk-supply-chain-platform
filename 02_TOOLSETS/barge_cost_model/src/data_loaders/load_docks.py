"""
Load navigation facilities (docks) data from BTS CSV into PostgreSQL.
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


def load_docks():
    """Load navigation facilities from CSV to PostgreSQL."""

    print("=" * 80)
    print("DOCKS LOADER")
    print("=" * 80)

    # 1. Read CSV (handle BOM)
    print("\n[1/2] Reading docks CSV...")
    csv_path = DATA_FILES["docks"]
    print(f"File: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df):,} records from CSV")
    print(f"  Columns: {', '.join(df.columns[:15])}...")

    # 2. Insert to database (batch insert for large dataset)
    print("\n[2/2] Inserting to PostgreSQL...")

    with get_db_session() as db:
        # Clear existing data
        print("  Truncating docks table...")
        db.execute(text("TRUNCATE TABLE docks RESTART IDENTITY CASCADE;"))

        # Batch insert (1000 at a time)
        batch_size = 1000
        total_inserted = 0

        for i in tqdm(range(0, len(df), batch_size), desc="Inserting batches"):
            batch = df.iloc[i:i+batch_size]
            records = []

            for _, row in batch.iterrows():
                record = {
                    'objectid': clean_value(row['ObjectID'], 'int'),
                    'latitude': clean_value(row.get('LATITUDE'), 'float'),
                    'longitude': clean_value(row.get('LONGITUDE'), 'float'),
                    'loc_dock': clean_value(row.get('LOC_DOCK'), max_length=50),
                    'nav_unit_id': clean_value(row.get('NAV_UNIT_ID'), max_length=50),
                    'nav_unit_guid': clean_value(row.get('NAV_UNIT_GUID'), max_length=50),
                    'unlocode': clean_value(row.get('UNLOCODE'), max_length=50),
                    'nav_unit_name': clean_value(row.get('NAV_UNIT_NAME'), max_length=255),
                    'fac_type': clean_value(row.get('FAC_TYPE'), max_length=100),
                    'data_record_status': clean_value(row.get('DATA_RECORD_STATUS'), max_length=50),
                    'location_description': clean_value(row.get('LOCATION_DESCRIPTION')),
                    'street_address': clean_value(row.get('STREET_ADDRESS'), max_length=255),
                    'city_or_town': clean_value(row.get('CITY_OR_TOWN'), max_length=100),
                    'state': clean_value(row.get('STATE'), max_length=2),
                    'zipcode': clean_value(row.get('ZIPCODE'), max_length=20),
                    'county_name': clean_value(row.get('COUNTY_NAME'), max_length=100),
                    'county_fips_code': clean_value(row.get('COUNTY_FIPS_CODE'), max_length=10),
                    'congress': clean_value(row.get('CONGRESS'), max_length=50),
                    'congress_fips': clean_value(row.get('CONGRESS_FIPS'), max_length=10),
                    'tows_link_num': clean_value(row.get('TOWS_LINK_NUM'), 'int'),
                    'tows_mile': clean_value(row.get('TOWS_MILE'), 'float'),
                    'wtwy': clean_value(row.get('WTWY'), max_length=50),
                    'wtwy_name': clean_value(row.get('WTWY_NAME'), max_length=255),
                    'port': clean_value(row.get('PORT'), max_length=50),
                    'port_name': clean_value(row.get('PORT_NAME'), max_length=255),
                    'psa': clean_value(row.get('PSA'), max_length=50),
                    'psa_name': clean_value(row.get('PSA_NAME'), max_length=255),
                    'mile': clean_value(row.get('MILE'), 'float'),
                    'bank': clean_value(row.get('BANK'), max_length=10),
                    'operators': clean_value(row.get('OPERATORS')),
                    'owners': clean_value(row.get('OWNERS')),
                    'purpose': clean_value(row.get('PURPOSE')),
                    'highway_note': clean_value(row.get('HIGHWAY_NOTE')),
                    'railway_note': clean_value(row.get('RAILWAY_NOTE')),
                    'commodities': clean_value(row.get('COMMODITIES')),
                    'construction': clean_value(row.get('CONSTRUCTION')),
                    'mechanical_handling': clean_value(row.get('MECHANICAL_HANDLING')),
                    'remarks': clean_value(row.get('REMARKS')),
                    'vertical_datum': clean_value(row.get('VERTICAL_DATUM'), max_length=50),
                    'depth_min': clean_value(row.get('DEPTH_MIN'), 'float'),
                    'depth_max': clean_value(row.get('DEPTH_MAX'), 'float'),
                    'berthing_largest': clean_value(row.get('BERTHING_LARGEST'), 'float'),
                    'berthing_total': clean_value(row.get('BERTHING_TOTAL'), 'float'),
                    'deck_height_min': clean_value(row.get('DECK_HEIGHT_MIN'), 'float'),
                    'deck_height_max': clean_value(row.get('DECK_HEIGHT_MAX'), 'float'),
                    'parent_or_child': clean_value(row.get('PARENT_OR_CHILD'), max_length=50),
                    'service_initiation_date': clean_value(row.get('SERVICE_INITIATION_DATE'), max_length=50),
                    'x': clean_value(row.get('x'), 'float'),
                    'y': clean_value(row.get('y'), 'float'),
                }
                records.append(record)

            # Insert batch
            db.execute(text("""
                INSERT INTO docks (
                    objectid, latitude, longitude, loc_dock, nav_unit_id, nav_unit_guid,
                    unlocode, nav_unit_name, fac_type, data_record_status,
                    location_description, street_address, city_or_town, state, zipcode,
                    county_name, county_fips_code, congress, congress_fips,
                    tows_link_num, tows_mile, wtwy, wtwy_name, port, port_name,
                    psa, psa_name, mile, bank, operators, owners, purpose,
                    highway_note, railway_note, commodities, construction,
                    mechanical_handling, remarks, vertical_datum, depth_min, depth_max,
                    berthing_largest, berthing_total, deck_height_min, deck_height_max,
                    parent_or_child, service_initiation_date, x, y
                ) VALUES (
                    :objectid, :latitude, :longitude, :loc_dock, :nav_unit_id, :nav_unit_guid,
                    :unlocode, :nav_unit_name, :fac_type, :data_record_status,
                    :location_description, :street_address, :city_or_town, :state, :zipcode,
                    :county_name, :county_fips_code, :congress, :congress_fips,
                    :tows_link_num, :tows_mile, :wtwy, :wtwy_name, :port, :port_name,
                    :psa, :psa_name, :mile, :bank, :operators, :owners, :purpose,
                    :highway_note, :railway_note, :commodities, :construction,
                    :mechanical_handling, :remarks, :vertical_datum, :depth_min, :depth_max,
                    :berthing_largest, :berthing_total, :deck_height_min, :deck_height_max,
                    :parent_or_child, :service_initiation_date, :x, :y
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
    print(f"Unique States:      {df['STATE'].nunique():,}")
    print(f"Unique Ports:       {df['PORT_NAME'].nunique():,}")
    print(f"Facility Types:     {df['FAC_TYPE'].nunique():,}")
    print(f"Avg Depth Min:      {df['DEPTH_MIN'].mean():.2f} feet")
    print("=" * 80)
    print("✓ Docks loading complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        load_docks()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
