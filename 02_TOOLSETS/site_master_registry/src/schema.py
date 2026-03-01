"""DuckDB schema definitions for site_master.duckdb.

Four tables:
  - master_sites:      One row per physical site
  - source_links:      Maps master sites to upstream source records
  - match_candidates:  Review queue for uncertain matches
  - build_log:         Audit trail per build run
"""

import duckdb

DDL_MASTER_SITES = """
CREATE TABLE IF NOT EXISTS master_sites (
    facility_uid        VARCHAR PRIMARY KEY,
    canonical_name      VARCHAR NOT NULL,
    city                VARCHAR,
    state               VARCHAR NOT NULL,
    county              VARCHAR,
    latitude            DOUBLE,
    longitude           DOUBLE,
    parent_company      VARCHAR,
    facility_types      VARCHAR,          -- comma-separated list
    naics_codes         VARCHAR,          -- comma-separated list
    sic_codes           VARCHAR,
    commodity_sectors   VARCHAR,          -- e.g. 'steel,aluminum'
    rail_served         BOOLEAN DEFAULT FALSE,
    barge_access        BOOLEAN DEFAULT FALSE,
    water_access        BOOLEAN DEFAULT FALSE,
    port_adjacent       BOOLEAN DEFAULT FALSE,
    pipeline_access     BOOLEAN DEFAULT FALSE,
    capacity_kt_year    DOUBLE,
    confidence_score    DOUBLE,           -- 0.0 – 1.0
    source_count        INTEGER DEFAULT 1,
    status              VARCHAR DEFAULT 'active',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_SOURCE_LINKS = """
CREATE TABLE IF NOT EXISTS source_links (
    link_id             INTEGER PRIMARY KEY,
    facility_uid        VARCHAR NOT NULL REFERENCES master_sites(facility_uid),
    source_system       VARCHAR NOT NULL,  -- e.g. 'steel_csv', 'epa_frs'
    source_record_id    VARCHAR NOT NULL,  -- original PK in source
    match_method        VARCHAR,           -- 'seed', 'name_state_naics', 'spatial_fuzzy', 'manual'
    match_confidence    DOUBLE,            -- 0.0 – 1.0
    distance_meters     DOUBLE,
    name_similarity     DOUBLE,
    source_attributes   VARCHAR,           -- JSON blob of source-specific fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_MATCH_CANDIDATES = """
CREATE TABLE IF NOT EXISTS match_candidates (
    candidate_id        INTEGER PRIMARY KEY,
    facility_uid        VARCHAR,
    source_system       VARCHAR NOT NULL,
    source_record_id    VARCHAR NOT NULL,
    source_name         VARCHAR,
    source_lat          DOUBLE,
    source_lon          DOUBLE,
    candidate_frs_id    VARCHAR,
    candidate_frs_name  VARCHAR,
    candidate_lat       DOUBLE,
    candidate_lon       DOUBLE,
    distance_meters     DOUBLE,
    name_similarity     DOUBLE,
    confidence_level    VARCHAR,           -- 'HIGH', 'MEDIUM', 'LOW'
    reviewed            BOOLEAN DEFAULT FALSE,
    review_action       VARCHAR,           -- 'accept', 'reject', 'merge'
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_BUILD_LOG = """
CREATE TABLE IF NOT EXISTS build_log (
    run_id              INTEGER PRIMARY KEY,
    phase               VARCHAR NOT NULL,
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at         TIMESTAMP,
    sites_created       INTEGER DEFAULT 0,
    sites_updated       INTEGER DEFAULT 0,
    links_created       INTEGER DEFAULT 0,
    candidates_queued   INTEGER DEFAULT 0,
    notes               VARCHAR
);
"""

ALL_DDL = [DDL_MASTER_SITES, DDL_SOURCE_LINKS, DDL_MATCH_CANDIDATES, DDL_BUILD_LOG]

# Geographic identity columns added by geo_enrichment.py
GEO_COLUMNS = [
    ("latitude_dms",           "VARCHAR"),
    ("longitude_dms",          "VARCHAR"),
    ("fips_state_code",        "VARCHAR"),
    ("fips_county_code",       "VARCHAR"),
    ("census_region",          "VARCHAR"),
    ("census_division",        "VARCHAR"),
    ("bea_region",             "VARCHAR"),
    ("epa_region",             "INTEGER"),
    ("congressional_district", "VARCHAR"),
    ("market_region",          "VARCHAR"),
    ("nearest_port_code",      "VARCHAR"),
    ("nearest_port_name",      "VARCHAR"),
    ("nearest_port_consolidated", "VARCHAR"),
    ("nearest_port_coast",     "VARCHAR"),
    ("nearest_port_region",    "VARCHAR"),
]


def init_database(db_path: str) -> duckdb.DuckDBPyConnection:
    """Create or open site_master.duckdb and ensure all tables exist."""
    conn = duckdb.connect(db_path)
    # Enable autoincrement sequences
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_link_id START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_candidate_id START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_run_id START 1")
    for ddl in ALL_DDL:
        conn.execute(ddl)
    return conn


def migrate_add_geo_columns(conn: duckdb.DuckDBPyConnection) -> int:
    """Add geographic identity columns to master_sites if they don't exist.

    Returns the number of columns actually added (0 if already present).
    """
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'master_sites'"
        ).fetchall()
    }
    added = 0
    for col_name, col_type in GEO_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE master_sites ADD COLUMN {col_name} {col_type}")
            added += 1
    if added:
        print(f"  Schema migration: added {added} geographic columns to master_sites")
    else:
        print(f"  Schema migration: all {len(GEO_COLUMNS)} geographic columns already present")
    return added
