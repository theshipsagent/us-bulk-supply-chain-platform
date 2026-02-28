"""Database connection utilities."""
import duckdb
from pathlib import Path
import yaml
from typing import Optional


def get_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_epa_frs_connection() -> duckdb.DuckDBPyConnection:
    """Get read-only connection to EPA FRS database."""
    config = get_config()
    db_path = Path(__file__).parent.parent.parent / config['data']['epa_frs']['path']
    
    if not db_path.exists():
        raise FileNotFoundError(
            f"EPA FRS database not found at {db_path}. "
            f"Please check the path in config/settings.yaml"
        )
    
    return duckdb.connect(str(db_path), read_only=True)


def get_atlas_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Get connection to ATLAS database (read-write by default)."""
    config = get_config()
    db_path = Path(__file__).parent.parent.parent / config['data']['atlas']['path']
    
    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return duckdb.connect(str(db_path), read_only=read_only)


def init_atlas_db() -> None:
    """Initialize ATLAS database with schema."""
    con = get_atlas_connection()
    
    try:
        # Core facilities table (from EPA FRS)
        con.execute("""
            CREATE TABLE IF NOT EXISTS facilities (
                registry_id VARCHAR PRIMARY KEY,
                facility_name VARCHAR,
                street_address VARCHAR,
                city VARCHAR,
                state VARCHAR(2),
                zip VARCHAR,
                county VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # NAICS codes per facility
        con.execute("""
            CREATE TABLE IF NOT EXISTS facility_naics (
                registry_id VARCHAR,
                naics_code VARCHAR,
                naics_description VARCHAR,
                naics_category VARCHAR,
                PRIMARY KEY (registry_id, naics_code),
                FOREIGN KEY (registry_id) REFERENCES facilities(registry_id)
            )
        """)
        
        # Parent company resolution
        con.execute("""
            CREATE TABLE IF NOT EXISTS parent_companies (
                raw_name VARCHAR PRIMARY KEY,
                resolved_parent VARCHAR,
                match_score DECIMAL,
                method VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Facility to parent company link
        con.execute("""
            CREATE TABLE IF NOT EXISTS facility_companies (
                registry_id VARCHAR,
                raw_name VARCHAR,
                resolved_parent VARCHAR,
                match_score DECIMAL,
                PRIMARY KEY (registry_id, raw_name),
                FOREIGN KEY (registry_id) REFERENCES facilities(registry_id)
            )
        """)
        
        print("ATLAS database schema initialized successfully")
        
    finally:
        con.close()


def get_db_info() -> dict:
    """Get database statistics and info."""
    con = get_atlas_connection(read_only=True)
    
    try:
        info = {}
        
        # Get record counts
        tables = ['facilities', 'facility_naics', 'parent_companies', 'facility_companies']
        for table in tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                info[table] = count
            except:
                info[table] = 0
        
        # Get last updated timestamp
        try:
            last_updated = con.execute(
                "SELECT MAX(created_at) FROM facilities"
            ).fetchone()[0]
            info['last_updated'] = last_updated
        except:
            info['last_updated'] = None
        
        return info
        
    finally:
        con.close()
