#!/usr/bin/env python3
"""
Schedule K Port Data Loader Module
===================================
Loads Schedule K port dictionary from Excel into ATLAS.

Schedule K is the official U.S. Census Bureau listing of ports for
foreign trade statistics, containing ~4,096 ports worldwide.

Functions:
    - load_schedule_k: Load Schedule K Excel file
    - create_port_table: Create ports table in database
    - find_nearest_port: Find nearest port to given coordinates
"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import math

logger = logging.getLogger(__name__)


class ScheduleKLoader:
    """Handles loading and processing of Schedule K port data."""

    def __init__(self, schedule_k_path: str, atlas_db_path: str):
        """
        Initialize Schedule K Loader.

        Args:
            schedule_k_path: Path to Schedule K Excel file
            atlas_db_path: Path to ATLAS DuckDB database
        """
        self.schedule_k_path = schedule_k_path
        self.atlas_db_path = atlas_db_path

    def discover_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-discover column mappings from Schedule K Excel file.

        Args:
            df: DataFrame loaded from Excel

        Returns:
            Dictionary mapping logical names to actual column names
        """
        columns = {c.upper(): c for c in df.columns}
        mapping = {}

        # Schedule K code
        for key in ['SCHEDULE K', 'SCHEDULE_K', 'CODE', 'PORT CODE', 'SK CODE']:
            for col_upper, col in columns.items():
                if key in col_upper or col_upper == 'K':
                    if 'schedule_k_code' not in mapping:
                        mapping['schedule_k_code'] = col
                    break

        # Port name
        for key in ['PORT', 'NAME', 'PORT NAME']:
            for col_upper, col in columns.items():
                if key in col_upper and 'CODE' not in col_upper:
                    if 'port_name' not in mapping:
                        mapping['port_name'] = col
                    break

        # Country code
        for key in ['COUNTRY CODE', 'COUNTRY_CODE', 'CC', 'ISO']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'country_code' not in mapping:
                        mapping['country_code'] = col
                    break

        # Country name
        for key in ['COUNTRY', 'NATION']:
            for col_upper, col in columns.items():
                if key in col_upper and 'CODE' not in col_upper:
                    if 'country_name' not in mapping:
                        mapping['country_name'] = col
                    break

        # Latitude
        for key in ['LATITUDE', 'LAT']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    mapping['latitude'] = col
                    break

        # Longitude
        for key in ['LONGITUDE', 'LON', 'LONG', 'LNG']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    mapping['longitude'] = col
                    break

        # District (if present)
        for key in ['DISTRICT', 'CUSTOMS DISTRICT']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    mapping['district'] = col
                    break

        # State (if present)
        for key in ['STATE', 'PROVINCE', 'REGION']:
            for col_upper, col in columns.items():
                if key in col_upper:
                    if 'state' not in mapping:
                        mapping['state'] = col
                    break

        logger.info(f"Discovered column mappings: {mapping}")
        return mapping

    def load_excel(self) -> pd.DataFrame:
        """
        Load Schedule K Excel file.

        Returns:
            DataFrame with raw port data
        """
        logger.info(f"Loading Schedule K from: {self.schedule_k_path}")

        if not Path(self.schedule_k_path).exists():
            raise FileNotFoundError(f"Schedule K file not found: {self.schedule_k_path}")

        # Try to find the main data sheet
        xlsx = pd.ExcelFile(self.schedule_k_path)
        sheet_names = xlsx.sheet_names

        logger.info(f"Available sheets: {sheet_names}")

        # Look for the main data sheet
        main_sheet = None
        for name in sheet_names:
            name_lower = name.lower()
            if 'port' in name_lower or 'schedule' in name_lower or 'data' in name_lower:
                main_sheet = name
                break

        if not main_sheet:
            # Use first sheet if no obvious match
            main_sheet = sheet_names[0]

        logger.info(f"Using sheet: {main_sheet}")
        df = pd.read_excel(self.schedule_k_path, sheet_name=main_sheet)

        logger.info(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform Schedule K data to standardized format.

        Args:
            df: Raw DataFrame from Excel

        Returns:
            Transformed DataFrame ready for database loading
        """
        logger.info("Transforming Schedule K data...")

        col_map = self.discover_columns(df)

        # Build standardized DataFrame
        records = []
        for idx, row in df.iterrows():
            record = {
                'schedule_k_code': None,
                'port_name': None,
                'country_code': None,
                'country_name': None,
                'state': None,
                'district': None,
                'latitude': None,
                'longitude': None,
            }

            # Map columns
            if 'schedule_k_code' in col_map:
                val = row.get(col_map['schedule_k_code'])
                if pd.notna(val):
                    record['schedule_k_code'] = str(val).strip()

            if 'port_name' in col_map:
                val = row.get(col_map['port_name'])
                if pd.notna(val):
                    record['port_name'] = str(val).strip()

            if 'country_code' in col_map:
                val = row.get(col_map['country_code'])
                if pd.notna(val):
                    record['country_code'] = str(val).strip().upper()

            if 'country_name' in col_map:
                val = row.get(col_map['country_name'])
                if pd.notna(val):
                    record['country_name'] = str(val).strip()

            if 'state' in col_map:
                val = row.get(col_map['state'])
                if pd.notna(val):
                    record['state'] = str(val).strip()

            if 'district' in col_map:
                val = row.get(col_map['district'])
                if pd.notna(val):
                    record['district'] = str(val).strip()

            # Latitude
            if 'latitude' in col_map:
                try:
                    lat = row.get(col_map['latitude'])
                    if pd.notna(lat):
                        lat_float = float(lat)
                        if -90 <= lat_float <= 90:
                            record['latitude'] = lat_float
                except (ValueError, TypeError):
                    pass

            # Longitude
            if 'longitude' in col_map:
                try:
                    lon = row.get(col_map['longitude'])
                    if pd.notna(lon):
                        lon_float = float(lon)
                        if -180 <= lon_float <= 180:
                            record['longitude'] = lon_float
                except (ValueError, TypeError):
                    pass

            # Only include records with at least a code or name
            if record['schedule_k_code'] or record['port_name']:
                records.append(record)

        result_df = pd.DataFrame(records)

        # Drop duplicates based on schedule_k_code if present
        if 'schedule_k_code' in result_df.columns and result_df['schedule_k_code'].notna().any():
            result_df = result_df.drop_duplicates(subset=['schedule_k_code'], keep='first')

        logger.info(f"Transformed {len(result_df):,} port records")
        logger.info(f"Countries: {result_df['country_name'].nunique()}")
        logger.info(f"Ports with coordinates: {result_df['latitude'].notna().sum():,}")

        return result_df

    def load_to_atlas(self, df: pd.DataFrame) -> None:
        """
        Load transformed port data to ATLAS database.

        Args:
            df: Transformed DataFrame with port data
        """
        logger.info(f"Loading {len(df):,} ports to ATLAS database...")

        con = duckdb.connect(self.atlas_db_path)

        try:
            # Create ports table
            con.execute("""
            CREATE TABLE IF NOT EXISTS schedule_k_ports (
                schedule_k_code VARCHAR PRIMARY KEY,
                port_name VARCHAR,
                country_code VARCHAR,
                country_name VARCHAR,
                state VARCHAR,
                district VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Clear existing data and insert new
            con.execute("DELETE FROM schedule_k_ports")
            con.execute("INSERT INTO schedule_k_ports SELECT *, CURRENT_TIMESTAMP FROM df")

            row_count = con.execute("SELECT COUNT(*) FROM schedule_k_ports").fetchone()[0]
            logger.info(f"Successfully loaded {row_count:,} ports to ATLAS")

            # Create index on coordinates for nearest-port queries
            # Note: DuckDB doesn't support partial indexes, so we create a regular index
            con.execute("""
            CREATE INDEX IF NOT EXISTS idx_ports_coords
            ON schedule_k_ports (latitude, longitude)
            """)

            # Create country summary view
            con.execute("""
            CREATE OR REPLACE VIEW port_country_summary AS
            SELECT
                country_name,
                country_code,
                COUNT(*) as port_count,
                COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as geocoded_count
            FROM schedule_k_ports
            GROUP BY country_name, country_code
            ORDER BY port_count DESC
            """)

            logger.info("Created port_country_summary view")

        finally:
            con.close()

    def refresh(self) -> None:
        """Execute full ETL pipeline: load Excel and create database tables."""
        logger.info("Starting Schedule K port data refresh...")

        # Load Excel
        df = self.load_excel()

        # Transform
        df_transformed = self.transform_data(df)

        if df_transformed.empty:
            logger.warning("No ports found after transformation")
            return

        # Load to ATLAS
        self.load_to_atlas(df_transformed)

        logger.info("Schedule K port data refresh complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded port data.

        Returns:
            Dictionary with port statistics
        """
        con = duckdb.connect(self.atlas_db_path, read_only=True)

        try:
            stats = {}

            # Total ports
            stats['total_ports'] = con.execute(
                "SELECT COUNT(*) FROM schedule_k_ports"
            ).fetchone()[0]

            # Countries
            stats['total_countries'] = con.execute(
                "SELECT COUNT(DISTINCT country_name) FROM schedule_k_ports WHERE country_name IS NOT NULL"
            ).fetchone()[0]

            # Ports with coordinates
            stats['geocoded_ports'] = con.execute(
                "SELECT COUNT(*) FROM schedule_k_ports WHERE latitude IS NOT NULL"
            ).fetchone()[0]

            # US ports
            stats['us_ports'] = con.execute(
                "SELECT COUNT(*) FROM schedule_k_ports WHERE country_code = 'US' OR country_name LIKE '%United States%'"
            ).fetchone()[0]

            # Top countries by port count
            top_countries = con.execute("""
                SELECT country_name, port_count
                FROM port_country_summary
                LIMIT 10
            """).fetchdf()
            stats['top_countries'] = top_countries.to_dict('records')

            return stats

        except Exception as e:
            logger.warning(f"Error getting port stats: {e}")
            return {}
        finally:
            con.close()


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points using Haversine formula.

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_nearest_port(
    atlas_db_path: str,
    latitude: float,
    longitude: float,
    country_filter: Optional[str] = None,
    limit: int = 5
) -> pd.DataFrame:
    """
    Find the nearest ports to a given location.

    Args:
        atlas_db_path: Path to ATLAS database
        latitude: Latitude of the location
        longitude: Longitude of the location
        country_filter: Optional country code or name to filter by
        limit: Maximum number of ports to return

    Returns:
        DataFrame with nearest ports and distances
    """
    con = duckdb.connect(atlas_db_path, read_only=True)

    try:
        # Build query with distance calculation
        # Using simplified distance calculation in SQL
        where_clause = "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        if country_filter:
            where_clause += f" AND (UPPER(country_code) = UPPER('{country_filter}') OR UPPER(country_name) LIKE UPPER('%{country_filter}%'))"

        query = f"""
        SELECT
            schedule_k_code,
            port_name,
            country_code,
            country_name,
            latitude,
            longitude,
            -- Approximate distance using Euclidean formula (good enough for sorting)
            SQRT(POWER(latitude - {latitude}, 2) + POWER(longitude - {longitude}, 2)) as approx_dist
        FROM schedule_k_ports
        {where_clause}
        ORDER BY approx_dist
        LIMIT {limit * 3}
        """

        df = con.execute(query).fetchdf()

        # Calculate actual Haversine distances for the top results
        if not df.empty:
            df['distance_km'] = df.apply(
                lambda row: haversine_distance(latitude, longitude, row['latitude'], row['longitude']),
                axis=1
            )
            df = df.sort_values('distance_km').head(limit)
            df = df.drop(columns=['approx_dist'])

        return df

    finally:
        con.close()


# Convenience functions for direct usage
def refresh_port_data(schedule_k_path: str, atlas_db_path: str) -> None:
    """
    Convenience function to refresh port data in ATLAS.

    Args:
        schedule_k_path: Path to Schedule K Excel file
        atlas_db_path: Path to ATLAS DuckDB database
    """
    loader = ScheduleKLoader(schedule_k_path, atlas_db_path)
    loader.refresh()


def get_port_stats(atlas_db_path: str) -> Dict[str, Any]:
    """
    Get statistics about port data in ATLAS.

    Args:
        atlas_db_path: Path to ATLAS DuckDB database

    Returns:
        Dictionary with port statistics
    """
    loader = ScheduleKLoader("", atlas_db_path)
    return loader.get_stats()


def query_ports_by_country(atlas_db_path: str, country: str) -> pd.DataFrame:
    """
    Query ports by country.

    Args:
        atlas_db_path: Path to ATLAS database
        country: Country name or code to query

    Returns:
        DataFrame with matching ports
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
        SELECT *
        FROM schedule_k_ports
        WHERE UPPER(country_code) = UPPER(?)
           OR UPPER(country_name) LIKE UPPER(?)
        ORDER BY port_name
        """
        return con.execute(query, [country, f"%{country}%"]).fetchdf()
    finally:
        con.close()
