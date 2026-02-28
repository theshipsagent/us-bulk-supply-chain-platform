"""
Load waterway network data from BTS CSV into PostgreSQL.
Builds NetworkX graph for routing engine.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import networkx as nx
import pickle
from sqlalchemy import text
from tqdm import tqdm

from src.config.settings import settings, DATA_FILES
from src.config.database import get_db_session


def clean_value(value, value_type='str'):
    """Clean and convert CSV values, handling nulls and clamping to NUMERIC(12,6) range."""
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
            # Clamp to NUMERIC(12, 6) range: -999999.999999 to 999999.999999
            if result > 999999.999999:
                return 999999.999999
            elif result < -999999.999999:
                return -999999.999999
            return result
        except (ValueError, TypeError):
            return None
    else:  # string
        return str(value).strip() if value else None


def load_waterway_networks():
    """Load waterway networks from CSV to PostgreSQL and build NetworkX graph."""

    print("=" * 80)
    print("WATERWAY NETWORK LOADER")
    print("=" * 80)

    # 1. Read CSV (handle BOM)
    print("\n[1/4] Reading waterway networks CSV...")
    csv_path = DATA_FILES["waterway_networks"]
    print(f"File: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df):,} records from CSV")
    print(f"  Columns: {', '.join(df.columns[:10])}...")

    # 2. Build NetworkX graph
    print("\n[2/4] Building routing graph...")
    G = nx.DiGraph()

    edges_added = 0
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Building graph"):
        anode = clean_value(row['ANODE'], 'int')
        bnode = clean_value(row['BNODE'], 'int')

        if anode and bnode:
            G.add_edge(
                anode,
                bnode,
                linknum=clean_value(row['LINKNUM'], 'int'),
                length=clean_value(row['LENGTH'], 'float'),
                rivername=clean_value(row['RIVERNAME']),
                state=clean_value(row['STATE'])
            )
            edges_added += 1

    print(f"✓ Graph built: {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")

    # 3. Insert to database (batch insert)
    print("\n[3/4] Inserting to PostgreSQL...")

    with get_db_session() as db:
        # Clear existing data
        print("  Truncating waterway_links table...")
        db.execute(text("TRUNCATE TABLE waterway_links RESTART IDENTITY CASCADE;"))

        # Batch insert (1000 at a time)
        batch_size = 1000
        total_inserted = 0

        for i in tqdm(range(0, len(df), batch_size), desc="Inserting batches"):
            batch = df.iloc[i:i+batch_size]
            records = []

            for _, row in batch.iterrows():
                # Skip records with missing required fields
                anode = clean_value(row['ANODE'], 'int')
                bnode = clean_value(row['BNODE'], 'int')
                linknum = clean_value(row['LINKNUM'], 'int')

                if anode is None or bnode is None or linknum is None:
                    continue  # Skip invalid records

                record = {
                    'objectid': clean_value(row['OBJECTID'], 'int'),
                    'id': clean_value(row.get('ID'), 'int'),
                    'length_miles': clean_value(row.get('LENGTH'), 'float'),
                    'dir': clean_value(row.get('DIR'), 'int'),
                    'linknum': linknum,
                    'anode': anode,
                    'bnode': bnode,
                    'linkname': clean_value(row.get('LINKNAME')),
                    'rivername': clean_value(row.get('RIVERNAME')),
                    'amile': clean_value(row.get('AMILE'), 'float'),
                    'bmile': clean_value(row.get('BMILE'), 'float'),
                    'length1': clean_value(row.get('LENGTH1'), 'float'),
                    'length_src': clean_value(row.get('LENGTH_SRC')),
                    'shape_src': clean_value(row.get('SHAPE_SRC')),
                    'linktype': clean_value(row.get('LINKTYPE')),
                    'waterway': clean_value(row.get('WATERWAY')),
                    'geo_class': clean_value(row.get('GEO_CLASS')),
                    'func_class': clean_value(row.get('FUNC_CLASS')),
                    'wtwy_type': clean_value(row.get('WTWY_TYPE')),
                    'chart_id': clean_value(row.get('CHART_ID')),
                    'num_pairs': clean_value(row.get('NUM_PAIRS'), 'int'),
                    'who_mod': clean_value(row.get('WHO_MOD')),
                    'date_mod': clean_value(row.get('DATE_MOD')),
                    'heading': clean_value(row.get('HEADING')),
                    'state': clean_value(row.get('STATE')),
                    'fips': clean_value(row.get('FIPS')),
                    'fips2': clean_value(row.get('FIPS2')),
                    'non_us': clean_value(row.get('NON_US')),
                    'key_id': clean_value(row.get('KEY_ID')),
                    'waterway_unique': clean_value(row.get('WATERWAY_Unique')),
                    'min_meas': clean_value(row.get('MIN_MEAS'), 'float'),
                    'max_meas': clean_value(row.get('MAX_MEAS'), 'float'),
                    'shape_length': clean_value(row.get('Shape__Length'), 'float'),
                }
                records.append(record)

            # Insert batch
            db.execute(text("""
                INSERT INTO waterway_links (
                    objectid, id, length_miles, dir, linknum, anode, bnode,
                    linkname, rivername, amile, bmile, length1, length_src,
                    shape_src, linktype, waterway, geo_class, func_class,
                    wtwy_type, chart_id, num_pairs, who_mod, date_mod,
                    heading, state, fips, fips2, non_us, key_id,
                    waterway_unique, min_meas, max_meas, shape_length
                ) VALUES (
                    :objectid, :id, :length_miles, :dir, :linknum, :anode, :bnode,
                    :linkname, :rivername, :amile, :bmile, :length1, :length_src,
                    :shape_src, :linktype, :waterway, :geo_class, :func_class,
                    :wtwy_type, :chart_id, :num_pairs, :who_mod, :date_mod,
                    :heading, :state, :fips, :fips2, :non_us, :key_id,
                    :waterway_unique, :min_meas, :max_meas, :shape_length
                )
            """), records)

            total_inserted += len(records)

        db.commit()

    print(f"✓ Inserted {total_inserted:,} records to database")

    # 4. Save graph for routing engine
    print("\n[4/4] Saving graph cache...")
    models_dir = settings.MODELS_DIR
    models_dir.mkdir(exist_ok=True)

    graph_file = models_dir / 'waterway_graph.pkl'
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)

    print(f"✓ Saved graph to {graph_file}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"CSV Records:        {len(df):,}")
    print(f"Database Records:   {total_inserted:,}")
    print(f"Graph Nodes:        {len(G.nodes()):,}")
    print(f"Graph Edges:        {len(G.edges()):,}")
    print(f"Unique Rivers:      {df['RIVERNAME'].nunique():,}")
    print(f"Unique States:      {df['STATE'].nunique():,}")
    print(f"Total Length:       {df['LENGTH'].sum():,.2f} miles")
    print("=" * 80)
    print("✓ Waterway network loading complete!")
    print("=" * 80)

    return G


if __name__ == "__main__":
    try:
        load_waterway_networks()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
