#!/usr/bin/env python3
"""
EPA FRS Data Loader Module
===========================
Extracts cement-relevant facilities from EPA FRS database and loads to ATLAS.
Adapted from enrich_cement_facilities_from_frs.py

Functions:
    - discover_schema: Auto-discover DuckDB table and column names
    - map_columns: Map expected columns to actual column names
    - extract_cement_facilities: Query facilities by NAICS codes
    - load_to_atlas: Load extracted data to ATLAS database
"""

import duckdb
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EPAFRSLoader:
    """Handles extraction and loading of EPA FRS data."""

    def __init__(self, frs_db_path: str, atlas_db_path: str, config_path: str = None):
        """
        Initialize EPA FRS Loader.

        Args:
            frs_db_path: Path to EPA FRS DuckDB database
            atlas_db_path: Path to ATLAS DuckDB database
            config_path: Path to NAICS configuration YAML (optional)
        """
        self.frs_db_path = frs_db_path
        self.atlas_db_path = atlas_db_path
        self.config_path = config_path
        self.naics_codes = self._load_naics_codes()

    def _load_naics_codes(self) -> List[str]:
        """Load NAICS codes from config file or use defaults."""
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                codes = []
                for category, items in config.items():
                    if category == 'broad_prefixes':
                        codes.extend(items)
                    elif isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'code' in item:
                                codes.append(item['code'])
                return codes
        else:
            # Default cement-relevant NAICS codes
            return [
                "3273", "327310", "327320", "327331", "327332", "327390",
                "327410", "327999", "324121", "324122", "325520", "325510",
                "327120", "238110", "238910", "237310", "213112", "327910",
                "238340", "238310", "423320", "423390", "444190"
            ]

    def discover_schema(self, con: duckdb.DuckDBPyConnection) -> Dict[str, List[Tuple[str, str]]]:
        """
        Auto-discover table and column names in the DuckDB.

        Args:
            con: DuckDB connection

        Returns:
            Dictionary mapping table names to list of (column_name, column_type) tuples
        """
        logger.info("Discovering database schema...")
        tables = con.execute("SHOW TABLES").fetchall()
        schema = {}

        for (tname,) in tables:
            cols = con.execute(f"DESCRIBE {tname}").fetchall()
            schema[tname] = [(c[0], c[1]) for c in cols]
            row_count = con.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            logger.info(f"  Table: {tname} ({row_count:,} rows)")
            for cname, ctype in schema[tname]:
                logger.debug(f"    {cname:<40} {ctype}")

        return schema

    def map_columns(self, schema: Dict[str, List[Tuple[str, str]]]) -> Dict[str, str]:
        """
        Map expected columns to actual column names in the DB.

        Args:
            schema: Database schema from discover_schema

        Returns:
            Dictionary mapping logical table names to actual table names
        """
        mapping = {}

        # Auto-detect based on column presence
        for tname, cols in schema.items():
            col_names = [c[0].upper() for c in cols]

            # Facilities table
            if 'REGISTRY_ID' in col_names and any('NAME' in c for c in col_names):
                if any('STREET' in c or 'ADDRESS' in c or 'LOCATION' in c for c in col_names):
                    mapping['facilities'] = tname

            # NAICS table
            if any('NAICS' in c for c in col_names) and 'REGISTRY_ID' in col_names:
                mapping['naics'] = tname

            # Organizations table
            if any('ORG' in c for c in col_names) and 'REGISTRY_ID' in col_names:
                mapping['organizations'] = tname

        logger.info(f"Detected table mapping: {mapping}")
        return mapping

    def extract_cement_facilities(
        self,
        con: duckdb.DuckDBPyConnection,
        schema: Dict[str, List[Tuple[str, str]]],
        table_map: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Extract facilities with cement-relevant NAICS codes.

        Args:
            con: DuckDB connection
            schema: Database schema
            table_map: Table name mappings

        Returns:
            DataFrame with facility records and NAICS codes
        """
        logger.info("Extracting cement-relevant facilities by NAICS codes...")

        fac_table = table_map.get('facilities')
        naics_table = table_map.get('naics')

        if not fac_table or not naics_table:
            raise ValueError(
                f"Could not identify facilities or NAICS tables. "
                f"Available tables: {list(schema.keys())}"
            )

        # Build column name references dynamically
        fac_cols = {c[0].upper(): c[0] for c in schema[fac_table]}
        naics_cols = {c[0].upper(): c[0] for c in schema[naics_table]}

        # Find actual column names
        reg_id_fac = next((fac_cols[k] for k in fac_cols if 'REGISTRY' in k), None)
        fac_name = next(
            (fac_cols[k] for k in fac_cols if 'FAC' in k and 'NAME' in k),
            next((fac_cols[k] for k in fac_cols if 'NAME' in k and 'REGISTRY' not in k), None)
        )
        street = next(
            (fac_cols[k] for k in fac_cols if 'STREET' in k or ('LOCATION' in k and 'ADDRESS' in k)),
            None
        )
        city = next((fac_cols[k] for k in fac_cols if 'CITY' in k), None)
        state = next(
            (fac_cols[k] for k in fac_cols if 'STATE' in k and 'CODE' not in k and 'NAME' not in k),
            next((fac_cols[k] for k in fac_cols if 'STATE' in k), None)
        )
        zipcode = next((fac_cols[k] for k in fac_cols if 'ZIP' in k or 'POSTAL' in k), None)
        county = next((fac_cols[k] for k in fac_cols if 'COUNTY' in k), None)
        lat = next((fac_cols[k] for k in fac_cols if 'LAT' in k), None)
        lon = next(
            (fac_cols[k] for k in fac_cols if 'LON' in k or 'LNG' in k or 'LONG' in k),
            None
        )

        reg_id_naics = next((naics_cols[k] for k in naics_cols if 'REGISTRY' in k), None)
        naics_code = next(
            (naics_cols[k] for k in naics_cols if 'NAICS' in k and 'CODE' in k),
            next((naics_cols[k] for k in naics_cols if 'NAICS' in k), None)
        )

        logger.info(f"Facilities table: {fac_table}")
        logger.info(f"  Registry ID: {reg_id_fac}, Name: {fac_name}")
        logger.info(f"  Location: {street}, {city}, {state}, {zipcode}")
        logger.info(f"  Coordinates: {lat}, {lon}")
        logger.info(f"NAICS table: {naics_table}")
        logger.info(f"  Registry ID: {reg_id_naics}, NAICS code: {naics_code}")

        # Build NAICS filter
        naics_conditions = " OR ".join([
            f"CAST(n.{naics_code} AS VARCHAR) LIKE '{prefix}%'"
            for prefix in self.naics_codes
        ])

        # Select columns that exist
        select_cols = []
        for alias, col in [
            ("REGISTRY_ID", reg_id_fac), ("FACILITY_NAME", fac_name),
            ("STREET_ADDRESS", street), ("CITY", city), ("STATE", state),
            ("ZIP", zipcode), ("COUNTY", county), ("LATITUDE", lat), ("LONGITUDE", lon)
        ]:
            if col:
                select_cols.append(f"f.{col} AS {alias}")

        query = f"""
        SELECT DISTINCT
            {', '.join(select_cols)},
            CAST(n.{naics_code} AS VARCHAR) AS NAICS_CODE
        FROM {fac_table} f
        INNER JOIN {naics_table} n ON f.{reg_id_fac} = n.{reg_id_naics}
        WHERE ({naics_conditions})
        ORDER BY f.{state}, f.{fac_name}
        """

        df = con.execute(query).fetchdf()
        logger.info(f"Found {len(df):,} facility-NAICS records")
        logger.info(f"Unique facilities: {df['REGISTRY_ID'].nunique():,}")
        logger.info(f"States represented: {df['STATE'].nunique()}")

        # Show NAICS distribution
        logger.info("NAICS Code Distribution (top 15):")
        naics_dist = df['NAICS_CODE'].value_counts().head(15)
        for code, count in naics_dist.items():
            logger.info(f"  {code}: {count:,} facilities")

        return df

    def load_to_atlas(self, df: pd.DataFrame) -> None:
        """
        Load extracted facilities to ATLAS database.

        Args:
            df: DataFrame with facility records
        """
        logger.info(f"Loading {len(df):,} records to ATLAS database...")

        # Connect to ATLAS database
        con = duckdb.connect(self.atlas_db_path)

        try:
            # Create facilities table if not exists
            con.execute("""
            CREATE TABLE IF NOT EXISTS frs_facilities (
                registry_id VARCHAR PRIMARY KEY,
                facility_name VARCHAR,
                street_address VARCHAR,
                city VARCHAR,
                state VARCHAR,
                zip VARCHAR,
                county VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                naics_codes VARCHAR,
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Aggregate NAICS codes per facility
            fac_df = df.drop_duplicates(subset='REGISTRY_ID').copy()
            naics_agg = df.groupby('REGISTRY_ID')['NAICS_CODE'].apply(
                lambda x: '; '.join(sorted(set(x.dropna().astype(str))))
            ).reset_index()
            naics_agg.columns = ['REGISTRY_ID', 'ALL_NAICS_CODES']

            fac_df = fac_df.drop(columns=['NAICS_CODE'], errors='ignore').merge(
                naics_agg, on='REGISTRY_ID', how='left'
            )

            # Rename columns to match table schema (only those that exist)
            rename_map = {}
            for old_col, new_col in [
                ('REGISTRY_ID', 'registry_id'),
                ('FACILITY_NAME', 'facility_name'),
                ('STREET_ADDRESS', 'street_address'),
                ('CITY', 'city'),
                ('STATE', 'state'),
                ('ZIP', 'zip'),
                ('COUNTY', 'county'),
                ('LATITUDE', 'latitude'),
                ('LONGITUDE', 'longitude'),
                ('ALL_NAICS_CODES', 'naics_codes')
            ]:
                if old_col in fac_df.columns:
                    rename_map[old_col] = new_col

            fac_df = fac_df.rename(columns=rename_map)

            # Add missing columns with NULL values
            for col in ['latitude', 'longitude']:
                if col not in fac_df.columns:
                    fac_df[col] = None

            # Ensure columns are in correct order
            column_order = ['registry_id', 'facility_name', 'street_address', 'city',
                           'state', 'zip', 'county', 'latitude', 'longitude', 'naics_codes']
            fac_df = fac_df[[c for c in column_order if c in fac_df.columns]]

            # Insert or replace records
            con.execute("DELETE FROM frs_facilities")  # Clear existing data
            con.execute("INSERT INTO frs_facilities SELECT *, CURRENT_TIMESTAMP FROM fac_df")

            row_count = con.execute("SELECT COUNT(*) FROM frs_facilities").fetchone()[0]
            logger.info(f"Successfully loaded {row_count:,} facilities to ATLAS")

        finally:
            con.close()

    def refresh(self) -> None:
        """Execute full ETL pipeline: extract from FRS and load to ATLAS."""
        logger.info("Starting EPA FRS data refresh...")

        # Connect to FRS database (read-only)
        con = duckdb.connect(self.frs_db_path, read_only=True)

        try:
            # Discover schema
            schema = self.discover_schema(con)

            # Map tables
            table_map = self.map_columns(schema)

            if not table_map.get('facilities'):
                raise ValueError(
                    f"Could not auto-detect facilities table. "
                    f"Available tables: {list(schema.keys())}"
                )

            # Extract facilities
            df = self.extract_cement_facilities(con, schema, table_map)

            if df.empty:
                logger.warning("No facilities found with cement-relevant NAICS codes")
                return

            # Load to ATLAS
            self.load_to_atlas(df)

            logger.info("EPA FRS data refresh complete")

        finally:
            con.close()


# Convenience functions for direct usage
def refresh_frs_data(frs_db_path: str, atlas_db_path: str, config_path: str = None) -> None:
    """
    Convenience function to refresh FRS data in ATLAS.

    Args:
        frs_db_path: Path to EPA FRS DuckDB database
        atlas_db_path: Path to ATLAS DuckDB database
        config_path: Path to NAICS configuration YAML (optional)
    """
    loader = EPAFRSLoader(frs_db_path, atlas_db_path, config_path)
    loader.refresh()


def extract_frs_facilities(frs_db_path: str, config_path: str = None) -> pd.DataFrame:
    """
    Extract facilities from FRS database without loading to ATLAS.

    Args:
        frs_db_path: Path to EPA FRS DuckDB database
        config_path: Path to NAICS configuration YAML (optional)

    Returns:
        DataFrame with facility records
    """
    loader = EPAFRSLoader(frs_db_path, "", config_path)
    con = duckdb.connect(frs_db_path, read_only=True)

    try:
        schema = loader.discover_schema(con)
        table_map = loader.map_columns(schema)
        df = loader.extract_cement_facilities(con, schema, table_map)
        return df
    finally:
        con.close()
