#!/usr/bin/env python3
"""
GEM Cement Tracker Data Loader Module
======================================
Loads Global Cement and Concrete Tracker data from Excel into ATLAS.

The GEM (Global Energy Monitor) Cement Tracker contains ~3,515 plants
across 167 countries with production capacity, ownership, and status data.

Functions:
    - parse_coordinates: Parse "lat, lon" string format
    - parse_owner: Parse "Owner Name [XX.X%]" format
    - load_gem_data: Load Excel file and create database tables
    - create_summary_views: Create country and parent company views
"""

import duckdb
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GEMCementLoader:
    """Handles loading and processing of GEM Global Cement Tracker data."""

    def __init__(self, gem_excel_path: str, atlas_db_path: str):
        """
        Initialize GEM Cement Loader.

        Args:
            gem_excel_path: Path to GEM Cement Tracker Excel file
            atlas_db_path: Path to ATLAS DuckDB database
        """
        self.gem_excel_path = gem_excel_path
        self.atlas_db_path = atlas_db_path

    @staticmethod
    def parse_coordinates(coord_str: Any) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse coordinate string in "lat, lon" format.

        Args:
            coord_str: String like "29.611942, -98.374994"

        Returns:
            Tuple of (latitude, longitude) as floats, or (None, None) if invalid
        """
        if pd.isna(coord_str) or not coord_str:
            return None, None

        try:
            coord_str = str(coord_str).strip()
            # Handle various separators
            if ',' in coord_str:
                parts = coord_str.split(',')
            elif ';' in coord_str:
                parts = coord_str.split(';')
            else:
                return None, None

            if len(parts) >= 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Validate reasonable coordinate ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
        except (ValueError, TypeError):
            pass

        return None, None

    @staticmethod
    def parse_owner(owner_str: Any) -> List[Dict[str, Any]]:
        """
        Parse owner string to extract company names and ownership percentages.

        Args:
            owner_str: String like "Holcim (US) Inc [100.0%]" or
                      "Company A [50.0%]; Company B [50.0%]"

        Returns:
            List of dicts with 'name' and 'percentage' keys
        """
        if pd.isna(owner_str) or not owner_str:
            return []

        owners = []
        owner_str = str(owner_str).strip()

        # Split on semicolons for multiple owners
        owner_parts = [p.strip() for p in owner_str.split(';') if p.strip()]

        for part in owner_parts:
            # Pattern: "Company Name [XX.X%]" or "Company Name (XX.X%)"
            match = re.match(r'^(.+?)\s*[\[\(](\d+\.?\d*)\s*%[\]\)]$', part.strip())
            if match:
                name = match.group(1).strip()
                try:
                    percentage = float(match.group(2))
                except ValueError:
                    percentage = None
                owners.append({'name': name, 'percentage': percentage})
            else:
                # No percentage found, treat entire string as name
                owners.append({'name': part.strip(), 'percentage': None})

        return owners

    @staticmethod
    def extract_primary_owner(owner_str: Any) -> Tuple[Optional[str], Optional[float]]:
        """
        Extract the primary (first/largest) owner from owner string.

        Args:
            owner_str: Owner string in GEM format

        Returns:
            Tuple of (owner_name, ownership_percentage)
        """
        owners = GEMCementLoader.parse_owner(owner_str)
        if not owners:
            return None, None

        # Return first owner (typically the largest or primary)
        primary = owners[0]
        return primary.get('name'), primary.get('percentage')

    def discover_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-discover column mappings from GEM Excel file.

        Args:
            df: DataFrame loaded from Excel

        Returns:
            Dictionary mapping logical names to actual column names
        """
        columns = {c.upper(): c for c in df.columns}
        mapping = {}

        # Plant identification - prioritize 'Asset name' over just 'Plant'
        for key in ['ASSET NAME', 'PLANT NAME', 'FACILITY NAME', 'NAME']:
            for col_upper, col in columns.items():
                if key in col_upper and 'PARENT' not in col_upper and 'OWNER' not in col_upper:
                    if 'plant_name' not in mapping:
                        mapping['plant_name'] = col
                    break
            if 'plant_name' in mapping:
                break

        # GEM Plant ID
        for col_upper, col in columns.items():
            if 'GEM' in col_upper and 'ID' in col_upper:
                mapping['plant_id'] = col
                break

        # Country - be specific to avoid matching 'Subnational'
        for key in ['COUNTRY/AREA', 'COUNTRY', 'NATION']:
            for col_upper, col in columns.items():
                if key in col_upper and 'SUB' not in col_upper:
                    mapping['country'] = col
                    break
            if 'country' in mapping:
                break

        # Region/State
        for key in ['SUBNATIONAL', 'REGION', 'STATE', 'PROVINCE']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    mapping['region'] = col
                    break
            if 'region' in mapping:
                break

        # Coordinates
        for key in ['COORDINATES', 'COORD', 'LAT/LONG', 'LOCATION']:
            for col_upper, col in columns.items():
                if key in col_upper and 'ACCURACY' not in col_upper:
                    mapping['coordinates'] = col
                    break

        # Separate lat/lon if available
        for col_upper, col in columns.items():
            if 'LATITUDE' in col_upper or col_upper == 'LAT':
                mapping['latitude'] = col
            if 'LONGITUDE' in col_upper or col_upper == 'LON' or col_upper == 'LONG':
                mapping['longitude'] = col

        # Capacity
        for key in ['CAPACITY', 'PRODUCTION']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'capacity' not in mapping:
                        mapping['capacity'] = col
                    break

        # Status
        for key in ['STATUS', 'OPERATING STATUS']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    mapping['status'] = col
                    break

        # Owner/Parent
        for key in ['OWNER', 'PARENT', 'COMPANY']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'owner' not in mapping:
                        mapping['owner'] = col
                    break

        # Start year
        for key in ['START', 'COMMENCED', 'OPENED', 'YEAR']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'start_year' not in mapping:
                        mapping['start_year'] = col
                    break

        # Plant type
        for key in ['TYPE', 'PLANT TYPE', 'FACILITY TYPE']:
            for col_upper, col in columns.items():
                if key in col_upper and 'PRODUCT' not in col_upper:
                    if 'plant_type' not in mapping:
                        mapping['plant_type'] = col
                    break

        # Product type
        for key in ['PRODUCT', 'OUTPUT']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'product_type' not in mapping:
                        mapping['product_type'] = col
                    break

        # Unique ID if present
        for key in ['ID', 'TRACKER ID', 'PLANT ID', 'UID']:
            for col_upper, col in columns.items():
                if col_upper == key or col_upper.endswith(' ID'):
                    if 'plant_id' not in mapping:
                        mapping['plant_id'] = col
                    break

        logger.info(f"Discovered column mappings: {mapping}")
        return mapping

    def load_excel(self) -> pd.DataFrame:
        """
        Load GEM Cement Tracker Excel file.

        Returns:
            DataFrame with raw GEM data
        """
        logger.info(f"Loading GEM Cement Tracker from: {self.gem_excel_path}")

        if not Path(self.gem_excel_path).exists():
            raise FileNotFoundError(f"GEM Excel file not found: {self.gem_excel_path}")

        # Try to find the main data sheet
        xlsx = pd.ExcelFile(self.gem_excel_path)
        sheet_names = xlsx.sheet_names

        logger.info(f"Available sheets: {sheet_names}")

        # Look for the main data sheet (prioritize 'Plant Data' over 'Metadata')
        main_sheet = None
        priority_patterns = ['plant data', 'plant', 'tracker', 'facilities', 'cement']
        for pattern in priority_patterns:
            for name in sheet_names:
                name_lower = name.lower()
                if pattern in name_lower and 'meta' not in name_lower and 'about' not in name_lower:
                    main_sheet = name
                    break
            if main_sheet:
                break

        if not main_sheet:
            # Use first sheet if no obvious match
            main_sheet = sheet_names[0]

        logger.info(f"Using sheet: {main_sheet}")
        df = pd.read_excel(self.gem_excel_path, sheet_name=main_sheet)

        logger.info(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform GEM data to standardized format.

        Args:
            df: Raw DataFrame from Excel

        Returns:
            Transformed DataFrame ready for database loading
        """
        logger.info("Transforming GEM data...")

        col_map = self.discover_columns(df)

        # Build standardized DataFrame
        records = []
        for idx, row in df.iterrows():
            record = {
                'gem_id': None,
                'plant_name': None,
                'country': None,
                'region': None,
                'latitude': None,
                'longitude': None,
                'capacity_mtpa': None,
                'status': None,
                'owner_raw': None,
                'owner_name': None,
                'owner_percentage': None,
                'start_year': None,
                'plant_type': None,
                'product_type': None,
            }

            # Map columns
            if 'plant_id' in col_map:
                record['gem_id'] = row.get(col_map['plant_id'])
            else:
                # Generate ID from index
                record['gem_id'] = f"GEM_{idx + 1:05d}"

            if 'plant_name' in col_map:
                record['plant_name'] = row.get(col_map['plant_name'])

            if 'country' in col_map:
                record['country'] = row.get(col_map['country'])

            if 'region' in col_map:
                record['region'] = row.get(col_map['region'])

            # Handle coordinates
            if 'coordinates' in col_map:
                lat, lon = self.parse_coordinates(row.get(col_map['coordinates']))
                record['latitude'] = lat
                record['longitude'] = lon
            elif 'latitude' in col_map and 'longitude' in col_map:
                try:
                    record['latitude'] = float(row.get(col_map['latitude']))
                    record['longitude'] = float(row.get(col_map['longitude']))
                except (ValueError, TypeError):
                    pass

            if 'capacity' in col_map:
                try:
                    cap = row.get(col_map['capacity'])
                    if pd.notna(cap):
                        record['capacity_mtpa'] = float(cap)
                except (ValueError, TypeError):
                    pass

            if 'status' in col_map:
                record['status'] = row.get(col_map['status'])

            if 'owner' in col_map:
                owner_raw = row.get(col_map['owner'])
                record['owner_raw'] = owner_raw
                name, pct = self.extract_primary_owner(owner_raw)
                record['owner_name'] = name
                record['owner_percentage'] = pct

            if 'start_year' in col_map:
                try:
                    yr = row.get(col_map['start_year'])
                    if pd.notna(yr):
                        record['start_year'] = int(yr)
                except (ValueError, TypeError):
                    pass

            if 'plant_type' in col_map:
                record['plant_type'] = row.get(col_map['plant_type'])

            if 'product_type' in col_map:
                record['product_type'] = row.get(col_map['product_type'])

            records.append(record)

        result_df = pd.DataFrame(records)

        # Clean string columns
        for col in ['plant_name', 'country', 'region', 'status', 'owner_raw',
                    'owner_name', 'plant_type', 'product_type']:
            if col in result_df.columns:
                result_df[col] = result_df[col].apply(
                    lambda x: str(x).strip() if pd.notna(x) else None
                )

        logger.info(f"Transformed {len(result_df):,} plant records")
        logger.info(f"Countries: {result_df['country'].nunique()}")
        logger.info(f"Plants with coordinates: {result_df['latitude'].notna().sum():,}")
        logger.info(f"Plants with owner data: {result_df['owner_name'].notna().sum():,}")

        return result_df

    def load_to_atlas(self, df: pd.DataFrame) -> None:
        """
        Load transformed GEM data to ATLAS database.

        Args:
            df: Transformed DataFrame with GEM plant data
        """
        logger.info(f"Loading {len(df):,} GEM plants to ATLAS database...")

        con = duckdb.connect(self.atlas_db_path)

        try:
            # Create GEM plants table
            con.execute("""
            CREATE TABLE IF NOT EXISTS gem_cement_plants (
                gem_id VARCHAR PRIMARY KEY,
                plant_name VARCHAR,
                country VARCHAR,
                region VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                capacity_mtpa DOUBLE,
                status VARCHAR,
                owner_raw VARCHAR,
                owner_name VARCHAR,
                owner_percentage DOUBLE,
                start_year INTEGER,
                plant_type VARCHAR,
                product_type VARCHAR,
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Clear existing data and insert new
            con.execute("DELETE FROM gem_cement_plants")
            con.execute("INSERT INTO gem_cement_plants SELECT *, CURRENT_TIMESTAMP FROM df")

            row_count = con.execute("SELECT COUNT(*) FROM gem_cement_plants").fetchone()[0]
            logger.info(f"Successfully loaded {row_count:,} GEM plants to ATLAS")

            # Create summary views
            self._create_summary_views(con)

        finally:
            con.close()

    def _create_summary_views(self, con: duckdb.DuckDBPyConnection) -> None:
        """
        Create summary views for country and parent company analysis.

        Args:
            con: Active DuckDB connection
        """
        logger.info("Creating summary views...")

        # Country summary view
        con.execute("""
        CREATE OR REPLACE VIEW gem_country_summary AS
        SELECT
            country,
            COUNT(*) as plant_count,
            SUM(capacity_mtpa) as total_capacity_mtpa,
            AVG(capacity_mtpa) as avg_capacity_mtpa,
            COUNT(CASE WHEN status = 'operating' OR status = 'Operating' THEN 1 END) as operating_count,
            COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as geocoded_count,
            MIN(start_year) as earliest_plant_year,
            MAX(start_year) as latest_plant_year
        FROM gem_cement_plants
        GROUP BY country
        ORDER BY total_capacity_mtpa DESC NULLS LAST
        """)

        # Parent company summary view
        con.execute("""
        CREATE OR REPLACE VIEW gem_parent_summary AS
        SELECT
            owner_name as parent_company,
            COUNT(*) as plant_count,
            COUNT(DISTINCT country) as country_count,
            SUM(capacity_mtpa) as total_capacity_mtpa,
            AVG(capacity_mtpa) as avg_capacity_mtpa,
            AVG(owner_percentage) as avg_ownership_pct,
            STRING_AGG(DISTINCT country, ', ' ORDER BY country) as countries
        FROM gem_cement_plants
        WHERE owner_name IS NOT NULL
        GROUP BY owner_name
        ORDER BY total_capacity_mtpa DESC NULLS LAST
        """)

        # Status summary view
        con.execute("""
        CREATE OR REPLACE VIEW gem_status_summary AS
        SELECT
            status,
            COUNT(*) as plant_count,
            SUM(capacity_mtpa) as total_capacity_mtpa,
            COUNT(DISTINCT country) as country_count
        FROM gem_cement_plants
        GROUP BY status
        ORDER BY plant_count DESC
        """)

        logger.info("Summary views created: gem_country_summary, gem_parent_summary, gem_status_summary")

    def refresh(self) -> None:
        """Execute full ETL pipeline: load Excel and create database tables."""
        logger.info("Starting GEM Cement Tracker data refresh...")

        # Load Excel
        df = self.load_excel()

        # Transform
        df_transformed = self.transform_data(df)

        if df_transformed.empty:
            logger.warning("No GEM plants found after transformation")
            return

        # Load to ATLAS
        self.load_to_atlas(df_transformed)

        logger.info("GEM Cement Tracker data refresh complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded GEM data.

        Returns:
            Dictionary with GEM data statistics
        """
        con = duckdb.connect(self.atlas_db_path, read_only=True)

        try:
            stats = {}

            # Total plants
            stats['total_plants'] = con.execute(
                "SELECT COUNT(*) FROM gem_cement_plants"
            ).fetchone()[0]

            # Countries
            stats['total_countries'] = con.execute(
                "SELECT COUNT(DISTINCT country) FROM gem_cement_plants WHERE country IS NOT NULL"
            ).fetchone()[0]

            # Total capacity
            result = con.execute(
                "SELECT SUM(capacity_mtpa) FROM gem_cement_plants"
            ).fetchone()[0]
            stats['total_capacity_mtpa'] = result if result else 0

            # Plants with coordinates
            stats['geocoded_plants'] = con.execute(
                "SELECT COUNT(*) FROM gem_cement_plants WHERE latitude IS NOT NULL"
            ).fetchone()[0]

            # Unique parent companies
            stats['unique_parents'] = con.execute(
                "SELECT COUNT(DISTINCT owner_name) FROM gem_cement_plants WHERE owner_name IS NOT NULL"
            ).fetchone()[0]

            # Top countries by capacity
            top_countries = con.execute("""
                SELECT country, plant_count, total_capacity_mtpa
                FROM gem_country_summary
                LIMIT 10
            """).fetchdf()
            stats['top_countries'] = top_countries.to_dict('records')

            # Top parent companies by capacity
            top_parents = con.execute("""
                SELECT parent_company, plant_count, total_capacity_mtpa, country_count
                FROM gem_parent_summary
                LIMIT 10
            """).fetchdf()
            stats['top_parents'] = top_parents.to_dict('records')

            return stats

        except Exception as e:
            logger.warning(f"Error getting GEM stats: {e}")
            return {}
        finally:
            con.close()


# Convenience functions for direct usage
def refresh_gem_data(gem_excel_path: str, atlas_db_path: str) -> None:
    """
    Convenience function to refresh GEM data in ATLAS.

    Args:
        gem_excel_path: Path to GEM Cement Tracker Excel file
        atlas_db_path: Path to ATLAS DuckDB database
    """
    loader = GEMCementLoader(gem_excel_path, atlas_db_path)
    loader.refresh()


def get_gem_stats(atlas_db_path: str) -> Dict[str, Any]:
    """
    Get statistics about GEM data in ATLAS.

    Args:
        atlas_db_path: Path to ATLAS DuckDB database

    Returns:
        Dictionary with GEM statistics
    """
    loader = GEMCementLoader("", atlas_db_path)
    return loader.get_stats()


def query_gem_by_country(atlas_db_path: str, country: str) -> pd.DataFrame:
    """
    Query GEM plants by country.

    Args:
        atlas_db_path: Path to ATLAS database
        country: Country name to query

    Returns:
        DataFrame with matching plants
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
        SELECT *
        FROM gem_cement_plants
        WHERE UPPER(country) = UPPER(?)
        ORDER BY capacity_mtpa DESC NULLS LAST
        """
        return con.execute(query, [country]).fetchdf()
    finally:
        con.close()


def query_gem_by_parent(atlas_db_path: str, parent: str) -> pd.DataFrame:
    """
    Query GEM plants by parent company.

    Args:
        atlas_db_path: Path to ATLAS database
        parent: Parent company name to query (fuzzy match)

    Returns:
        DataFrame with matching plants
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
        SELECT *
        FROM gem_cement_plants
        WHERE UPPER(owner_name) LIKE UPPER(?)
        ORDER BY capacity_mtpa DESC NULLS LAST
        """
        return con.execute(query, [f"%{parent}%"]).fetchdf()
    finally:
        con.close()
