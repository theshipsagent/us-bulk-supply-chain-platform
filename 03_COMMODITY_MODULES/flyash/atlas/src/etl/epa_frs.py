#!/usr/bin/env python3
"""
EPA FRS Data Loader Module — Fly Ash / CCP
=============================================
Extracts fly-ash-relevant facilities from EPA FRS database and loads to ATLAS.
Adapted from slag/atlas/src/etl/epa_frs.py for fly ash NAICS codes.

Key distinction: categorizes facilities as Coal Power (fly ash source),
Ash Processing/Harvesting, Cement/Concrete End Users, and Distribution.
"""

import duckdb
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# NAICS category mapping for fly ash supply chain
NAICS_CATEGORIES = {
    "221112": "Coal Power (Fly Ash Source)",
    "562998": "Ash Processing/Harvesting",
    "562910": "Ash Processing/Harvesting",
    "212399": "Ash Processing/Harvesting",
    "327310": "Cement/Concrete End User",
    "327320": "Cement/Concrete End User",
    "327390": "Cement/Concrete End User",
    "424690": "Distribution",
}


class EPAFRSLoader:
    """Handles extraction and loading of EPA FRS data for fly ash/CCP facilities."""

    def __init__(self, frs_db_path: str, atlas_db_path: str, config_path: str = None):
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
            return [
                "2211",    # Broad: Utilities (coal power)
                "3273",    # Broad: Cement and Concrete
                "221112",  # Fossil Fuel Electric Power Generation
                "562998",  # Waste Management Services (ash management)
                "562910",  # Remediation Services (ash pond remediation)
                "212399",  # Nonmetallic Mineral Mining (ash harvesting)
                "327310", "327320", "327390",
                "424690",  # Distribution
            ]

    def discover_schema(self, con: duckdb.DuckDBPyConnection) -> Dict[str, List[Tuple[str, str]]]:
        """Auto-discover table and column names in the DuckDB."""
        logger.info("Discovering database schema...")
        tables = con.execute("SHOW TABLES").fetchall()
        schema = {}

        for (tname,) in tables:
            cols = con.execute(f"DESCRIBE {tname}").fetchall()
            schema[tname] = [(c[0], c[1]) for c in cols]
            row_count = con.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            logger.info(f"  Table: {tname} ({row_count:,} rows)")

        return schema

    def map_columns(self, schema: Dict[str, List[Tuple[str, str]]]) -> Dict[str, str]:
        """Map expected columns to actual column names in the DB."""
        mapping = {}
        facilities_candidates = []

        for tname, cols in schema.items():
            col_names = [c[0].upper() for c in cols]

            if 'REGISTRY_ID' in col_names and any('NAME' in c for c in col_names):
                if any('STREET' in c or 'ADDRESS' in c or 'LOCATION' in c for c in col_names):
                    has_coords = any('LAT' in c for c in col_names)
                    facilities_candidates.append((tname, has_coords))

            if any('NAICS' in c for c in col_names) and 'REGISTRY_ID' in col_names:
                mapping['naics'] = tname

            if any('ORG' in c for c in col_names) and 'REGISTRY_ID' in col_names:
                mapping['organizations'] = tname

        # Prefer facilities table with coordinates
        if facilities_candidates:
            with_coords = [t for t, has in facilities_candidates if has]
            if with_coords:
                mapping['facilities'] = with_coords[0]
            else:
                mapping['facilities'] = facilities_candidates[0][0]

        logger.info(f"Detected table mapping: {mapping}")
        return mapping

    def extract_facilities(
        self,
        con: duckdb.DuckDBPyConnection,
        schema: Dict[str, List[Tuple[str, str]]],
        table_map: Dict[str, str]
    ) -> pd.DataFrame:
        """Extract facilities with fly-ash-relevant NAICS codes."""
        logger.info("Extracting fly-ash-relevant facilities by NAICS codes...")

        fac_table = table_map.get('facilities')
        naics_table = table_map.get('naics')

        if not fac_table or not naics_table:
            raise ValueError(
                f"Could not identify facilities or NAICS tables. "
                f"Available tables: {list(schema.keys())}"
            )

        fac_cols = {c[0].upper(): c[0] for c in schema[fac_table]}
        naics_cols = {c[0].upper(): c[0] for c in schema[naics_table]}

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
        logger.info(f"  Coordinates: {lat}, {lon}")

        naics_conditions = " OR ".join([
            f"CAST(n.{naics_code} AS VARCHAR) LIKE '{prefix}%'"
            for prefix in self.naics_codes
        ])

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

        # NAICS distribution
        logger.info("NAICS Code Distribution (top 15):")
        for code, count in df['NAICS_CODE'].value_counts().head(15).items():
            logger.info(f"  {code}: {count:,} facilities")

        return df

    def _categorize_naics(self, naics_codes_str: str) -> str:
        """
        Determine facility category from NAICS codes.
        Priority: Coal Power > Ash Processing > Cement/Concrete > Distribution > Other
        """
        if not naics_codes_str:
            return "Unknown"

        codes = [c.strip() for c in naics_codes_str.split(';')]
        categories = set()

        for code in codes:
            if code in NAICS_CATEGORIES:
                categories.add(NAICS_CATEGORIES[code])
            else:
                for naics, cat in NAICS_CATEGORIES.items():
                    if code.startswith(naics[:4]):
                        categories.add(cat)

        for priority in [
            "Coal Power (Fly Ash Source)",
            "Ash Processing/Harvesting",
            "Cement/Concrete End User",
            "Distribution",
        ]:
            if priority in categories:
                return priority

        return "Other"

    def load_to_atlas(self, df: pd.DataFrame) -> None:
        """Load extracted facilities to ATLAS Fly Ash database."""
        logger.info(f"Loading {len(df):,} records to ATLAS Fly Ash database...")

        con = duckdb.connect(self.atlas_db_path)

        try:
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
                naics_category VARCHAR,
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            fac_df = df.drop_duplicates(subset='REGISTRY_ID').copy()
            naics_agg = df.groupby('REGISTRY_ID')['NAICS_CODE'].apply(
                lambda x: '; '.join(sorted(set(x.dropna().astype(str))))
            ).reset_index()
            naics_agg.columns = ['REGISTRY_ID', 'ALL_NAICS_CODES']

            fac_df = fac_df.drop(columns=['NAICS_CODE'], errors='ignore').merge(
                naics_agg, on='REGISTRY_ID', how='left'
            )

            fac_df['NAICS_CATEGORY'] = fac_df['ALL_NAICS_CODES'].apply(self._categorize_naics)

            rename_map = {
                'REGISTRY_ID': 'registry_id', 'FACILITY_NAME': 'facility_name',
                'STREET_ADDRESS': 'street_address', 'CITY': 'city', 'STATE': 'state',
                'ZIP': 'zip', 'COUNTY': 'county', 'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude', 'ALL_NAICS_CODES': 'naics_codes',
                'NAICS_CATEGORY': 'naics_category'
            }
            fac_df = fac_df.rename(columns={k: v for k, v in rename_map.items() if k in fac_df.columns})

            for col in ['latitude', 'longitude']:
                if col not in fac_df.columns:
                    fac_df[col] = None

            column_order = ['registry_id', 'facility_name', 'street_address', 'city',
                           'state', 'zip', 'county', 'latitude', 'longitude',
                           'naics_codes', 'naics_category']
            fac_df = fac_df[[c for c in column_order if c in fac_df.columns]]

            con.execute("DELETE FROM frs_facilities")
            con.execute("INSERT INTO frs_facilities SELECT *, CURRENT_TIMESTAMP FROM fac_df")

            row_count = con.execute("SELECT COUNT(*) FROM frs_facilities").fetchone()[0]
            logger.info(f"Successfully loaded {row_count:,} facilities to ATLAS Fly Ash")

            cat_dist = con.execute("""
                SELECT naics_category, COUNT(*) as cnt
                FROM frs_facilities GROUP BY naics_category ORDER BY cnt DESC
            """).fetchdf()
            for _, row in cat_dist.iterrows():
                logger.info(f"  {row['naics_category']}: {row['cnt']:,}")

        finally:
            con.close()

    def refresh(self) -> None:
        """Execute full ETL pipeline."""
        logger.info("Starting EPA FRS data refresh for fly ash/CCP...")

        con = duckdb.connect(self.frs_db_path, read_only=True)
        try:
            schema = self.discover_schema(con)
            table_map = self.map_columns(schema)

            if not table_map.get('facilities'):
                raise ValueError(f"Could not auto-detect facilities table. Tables: {list(schema.keys())}")

            df = self.extract_facilities(con, schema, table_map)

            if df.empty:
                logger.warning("No facilities found with fly-ash-relevant NAICS codes")
                return

            self.load_to_atlas(df)
            logger.info("EPA FRS data refresh complete for fly ash")
        finally:
            con.close()


def refresh_frs_data(frs_db_path: str, atlas_db_path: str, config_path: str = None) -> None:
    """Refresh FRS data in ATLAS Fly Ash database."""
    loader = EPAFRSLoader(frs_db_path, atlas_db_path, config_path)
    loader.refresh()


def extract_frs_facilities(frs_db_path: str, config_path: str = None) -> pd.DataFrame:
    """Extract facilities from FRS database without loading to ATLAS."""
    loader = EPAFRSLoader(frs_db_path, "", config_path)
    con = duckdb.connect(frs_db_path, read_only=True)
    try:
        schema = loader.discover_schema(con)
        table_map = loader.map_columns(schema)
        return loader.extract_facilities(con, schema, table_map)
    finally:
        con.close()
