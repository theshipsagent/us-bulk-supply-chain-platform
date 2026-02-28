#!/usr/bin/env python3
"""
Facility Master Integration Module
===================================
Creates a unified master_facilities table linking:
- GEM Cement Tracker plants (global production)
- EPA FRS facilities (US downstream/permits)
- Nearest ports (for trade linkage)

Functions:
    - match_gem_to_frs: Match US GEM plants to EPA FRS by name/location
    - calculate_nearest_ports: Find nearest port for each facility
    - create_master_table: Create unified master_facilities table
"""

import duckdb
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import math

logger = logging.getLogger(__name__)


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


def normalize_name(name: str) -> str:
    """
    Normalize facility/company name for matching.

    Args:
        name: Raw facility or company name

    Returns:
        Normalized name for comparison
    """
    if not name or pd.isna(name):
        return ""

    # Convert to uppercase
    name = str(name).upper()

    # Remove common suffixes
    suffixes = [
        r'\s+INC\.?$', r'\s+LLC\.?$', r'\s+LTD\.?$', r'\s+CORP\.?$',
        r'\s+CORPORATION$', r'\s+COMPANY$', r'\s+CO\.?$',
        r'\s+LP$', r'\s+LLP$', r'\s+PLC$', r'\s+SA$', r'\s+AG$',
        r'\s+\(US\)$', r'\s+USA$', r'\s+US$', r'\s+NA$',
        r'\s+PLANT$', r'\s+FACILITY$', r'\s+CEMENT$',
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name)

    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate simple similarity score between two names.

    Uses Jaccard similarity on word sets.

    Args:
        name1: First name
        name2: Second name

    Returns:
        Similarity score from 0 to 100
    """
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    if not norm1 or not norm2:
        return 0.0

    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    jaccard = len(intersection) / len(union) if union else 0.0

    # Bonus for exact match
    if norm1 == norm2:
        return 100.0

    return jaccard * 100


class FacilityMasterBuilder:
    """Handles creation and maintenance of the master facilities table."""

    # Maximum distance (km) to consider for FRS matching
    MAX_MATCH_DISTANCE_KM = 25

    # Minimum name similarity score for matching
    MIN_NAME_SIMILARITY = 40

    def __init__(self, atlas_db_path: str):
        """
        Initialize Facility Master Builder.

        Args:
            atlas_db_path: Path to ATLAS DuckDB database
        """
        self.atlas_db_path = atlas_db_path

    def _connect(self, read_only: bool = False) -> duckdb.DuckDBPyConnection:
        """Create database connection."""
        return duckdb.connect(self.atlas_db_path, read_only=read_only)

    def check_source_tables(self, con: duckdb.DuckDBPyConnection = None) -> Dict[str, bool]:
        """
        Check which source tables are available.

        Args:
            con: Optional existing connection to use

        Returns:
            Dictionary of table names to availability status
        """
        close_con = False
        if con is None:
            con = self._connect(read_only=True)
            close_con = True

        try:
            tables = {
                'gem_cement_plants': False,
                'frs_facilities': False,
                'schedule_k_ports': False,
            }

            result = con.execute("SHOW TABLES").fetchall()
            available_tables = [t[0] for t in result]

            for table in tables:
                tables[table] = table in available_tables

            return tables
        finally:
            if close_con:
                con.close()

    def match_gem_to_frs(self, con: duckdb.DuckDBPyConnection = None) -> pd.DataFrame:
        """
        Match US GEM cement plants to EPA FRS facilities.

        Uses a combination of geographic proximity and name similarity.

        Args:
            con: Optional existing connection to use

        Returns:
            DataFrame with matched GEM-FRS pairs and match scores
        """
        logger.info("Matching US GEM plants to EPA FRS facilities...")

        close_con = False
        if con is None:
            con = self._connect(read_only=True)
            close_con = True

        try:
            # Check if tables exist
            tables = self.check_source_tables(con)
            if not tables['gem_cement_plants']:
                logger.warning("GEM plants table not found - run 'refresh --source gem' first")
                return pd.DataFrame()
            if not tables['frs_facilities']:
                logger.warning("FRS facilities table not found - run 'refresh' first")
                return pd.DataFrame()

            # Get US GEM plants with coordinates
            gem_df = con.execute("""
                SELECT gem_id, plant_name, country, region, latitude, longitude,
                       capacity_mtpa, status, owner_name
                FROM gem_cement_plants
                WHERE country = 'United States' OR country = 'USA' OR country = 'US'
                  AND latitude IS NOT NULL AND longitude IS NOT NULL
            """).fetchdf()

            if gem_df.empty:
                logger.warning("No US GEM plants found with coordinates")
                return pd.DataFrame()

            logger.info(f"Found {len(gem_df)} US GEM plants to match")

            # Get FRS facilities with coordinates
            frs_df = con.execute("""
                SELECT registry_id, facility_name, state, city, latitude, longitude,
                       naics_codes
                FROM frs_facilities
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """).fetchdf()

            if frs_df.empty:
                logger.warning("No FRS facilities found with coordinates")
                return pd.DataFrame()

            logger.info(f"Found {len(frs_df)} FRS facilities with coordinates")

            # Match each GEM plant to nearest FRS facilities
            matches = []
            for _, gem_row in gem_df.iterrows():
                gem_lat = gem_row['latitude']
                gem_lon = gem_row['longitude']
                gem_name = gem_row['plant_name']

                best_match = None
                best_score = 0

                for _, frs_row in frs_df.iterrows():
                    frs_lat = frs_row['latitude']
                    frs_lon = frs_row['longitude']
                    frs_name = frs_row['facility_name']

                    # Calculate distance
                    dist = haversine_distance(gem_lat, gem_lon, frs_lat, frs_lon)

                    if dist > self.MAX_MATCH_DISTANCE_KM:
                        continue

                    # Calculate name similarity
                    name_sim = calculate_name_similarity(gem_name, frs_name)

                    # Combined score: weight distance and name similarity
                    # Distance score: 100 at 0km, 0 at MAX_MATCH_DISTANCE_KM
                    dist_score = max(0, 100 * (1 - dist / self.MAX_MATCH_DISTANCE_KM))

                    # Combined score (weighted average)
                    combined_score = 0.4 * dist_score + 0.6 * name_sim

                    if combined_score > best_score and name_sim >= self.MIN_NAME_SIMILARITY:
                        best_score = combined_score
                        best_match = {
                            'gem_id': gem_row['gem_id'],
                            'gem_name': gem_name,
                            'gem_state': gem_row['region'],
                            'gem_lat': gem_lat,
                            'gem_lon': gem_lon,
                            'frs_registry_id': frs_row['registry_id'],
                            'frs_name': frs_name,
                            'frs_state': frs_row['state'],
                            'frs_city': frs_row['city'],
                            'frs_lat': frs_lat,
                            'frs_lon': frs_lon,
                            'distance_km': dist,
                            'name_similarity': name_sim,
                            'match_score': combined_score,
                        }

                if best_match:
                    matches.append(best_match)

            matches_df = pd.DataFrame(matches)
            logger.info(f"Found {len(matches_df)} GEM-FRS matches")

            return matches_df

        finally:
            if close_con:
                con.close()

    def calculate_nearest_ports(self, facility_type: str = 'gem', con: duckdb.DuckDBPyConnection = None) -> pd.DataFrame:
        """
        Calculate nearest port for each facility.

        Args:
            facility_type: 'gem' for GEM plants or 'frs' for FRS facilities
            con: Optional existing connection to use

        Returns:
            DataFrame with facility-port linkages and distances
        """
        logger.info(f"Calculating nearest ports for {facility_type} facilities...")

        close_con = False
        if con is None:
            con = self._connect(read_only=True)
            close_con = True

        try:
            # Check if ports table exists
            tables = self.check_source_tables(con)
            if not tables['schedule_k_ports']:
                logger.warning("Ports table not found - run 'refresh --source ports' first")
                return pd.DataFrame()

            # Get facilities with coordinates
            if facility_type == 'gem':
                if not tables['gem_cement_plants']:
                    logger.warning("GEM plants table not found")
                    return pd.DataFrame()

                facilities_df = con.execute("""
                    SELECT gem_id as facility_id, plant_name as facility_name,
                           country, latitude, longitude
                    FROM gem_cement_plants
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """).fetchdf()
            else:  # frs
                if not tables['frs_facilities']:
                    logger.warning("FRS facilities table not found")
                    return pd.DataFrame()

                facilities_df = con.execute("""
                    SELECT registry_id as facility_id, facility_name,
                           'United States' as country, latitude, longitude
                    FROM frs_facilities
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """).fetchdf()

            if facilities_df.empty:
                logger.warning(f"No {facility_type} facilities found with coordinates")
                return pd.DataFrame()

            logger.info(f"Processing {len(facilities_df)} facilities")

            # Get all ports with coordinates
            ports_df = con.execute("""
                SELECT schedule_k_code, port_name, country_name, latitude, longitude
                FROM schedule_k_ports
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """).fetchdf()

            if ports_df.empty:
                logger.warning("No ports found with coordinates")
                return pd.DataFrame()

            # Find nearest port for each facility
            results = []
            for idx, fac_row in facilities_df.iterrows():
                fac_lat = fac_row['latitude']
                fac_lon = fac_row['longitude']

                min_dist = float('inf')
                nearest_port = None

                for _, port_row in ports_df.iterrows():
                    dist = haversine_distance(
                        fac_lat, fac_lon,
                        port_row['latitude'], port_row['longitude']
                    )

                    if dist < min_dist:
                        min_dist = dist
                        nearest_port = port_row

                if nearest_port is not None:
                    results.append({
                        'facility_id': fac_row['facility_id'],
                        'facility_name': fac_row['facility_name'],
                        'facility_country': fac_row['country'],
                        'facility_lat': fac_lat,
                        'facility_lon': fac_lon,
                        'nearest_port_code': nearest_port['schedule_k_code'],
                        'nearest_port_name': nearest_port['port_name'],
                        'nearest_port_country': nearest_port['country_name'],
                        'port_distance_km': min_dist,
                    })

                # Log progress for large datasets
                if (idx + 1) % 500 == 0:
                    logger.info(f"  Processed {idx + 1}/{len(facilities_df)} facilities")

            results_df = pd.DataFrame(results)
            logger.info(f"Calculated nearest ports for {len(results_df)} facilities")

            # Summary stats
            if not results_df.empty:
                avg_dist = results_df['port_distance_km'].mean()
                max_dist = results_df['port_distance_km'].max()
                logger.info(f"  Average distance to port: {avg_dist:.1f} km")
                logger.info(f"  Maximum distance to port: {max_dist:.1f} km")

            return results_df

        finally:
            if close_con:
                con.close()

    def create_master_table(self) -> None:
        """
        Create the unified master_facilities table.

        Combines GEM plants, FRS facilities, and port linkages.
        """
        logger.info("Creating master_facilities table...")

        con = self._connect()

        try:
            tables = self.check_source_tables(con)

            # Create the master table
            con.execute("""
            CREATE TABLE IF NOT EXISTS master_facilities (
                facility_id VARCHAR PRIMARY KEY,
                source VARCHAR,
                facility_name VARCHAR,
                country VARCHAR,
                region VARCHAR,
                city VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                -- GEM specific
                gem_id VARCHAR,
                capacity_mtpa DOUBLE,
                status VARCHAR,
                owner_name VARCHAR,
                -- FRS specific
                frs_registry_id VARCHAR,
                naics_codes VARCHAR,
                -- FRS match (for GEM plants)
                matched_frs_id VARCHAR,
                frs_match_score DOUBLE,
                frs_match_distance_km DOUBLE,
                -- Nearest port
                nearest_port_code VARCHAR,
                nearest_port_name VARCHAR,
                nearest_port_distance_km DOUBLE,
                -- Metadata
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Clear existing data
            con.execute("DELETE FROM master_facilities")

            # Load GEM plants if available
            if tables['gem_cement_plants']:
                logger.info("Loading GEM plants into master table...")
                con.execute("""
                INSERT INTO master_facilities (
                    facility_id, source, facility_name, country, region,
                    latitude, longitude, gem_id, capacity_mtpa, status, owner_name
                )
                SELECT
                    'GEM_' || gem_id,
                    'GEM',
                    plant_name,
                    country,
                    region,
                    latitude,
                    longitude,
                    gem_id,
                    capacity_mtpa,
                    status,
                    owner_name
                FROM gem_cement_plants
                """)

                gem_count = con.execute(
                    "SELECT COUNT(*) FROM master_facilities WHERE source = 'GEM'"
                ).fetchone()[0]
                logger.info(f"  Added {gem_count:,} GEM plants")

            # Load FRS facilities if available
            if tables['frs_facilities']:
                logger.info("Loading FRS facilities into master table...")
                con.execute("""
                INSERT INTO master_facilities (
                    facility_id, source, facility_name, country, region, city,
                    latitude, longitude, frs_registry_id, naics_codes
                )
                SELECT
                    'FRS_' || registry_id,
                    'FRS',
                    facility_name,
                    'United States',
                    state,
                    city,
                    latitude,
                    longitude,
                    registry_id,
                    naics_codes
                FROM frs_facilities
                """)

                frs_count = con.execute(
                    "SELECT COUNT(*) FROM master_facilities WHERE source = 'FRS'"
                ).fetchone()[0]
                logger.info(f"  Added {frs_count:,} FRS facilities")

            # Update GEM-FRS matches
            if tables['gem_cement_plants'] and tables['frs_facilities']:
                logger.info("Updating GEM-FRS matches...")
                matches_df = self.match_gem_to_frs(con)

                if not matches_df.empty:
                    # Update master table with matches
                    for _, match in matches_df.iterrows():
                        con.execute("""
                        UPDATE master_facilities
                        SET matched_frs_id = ?,
                            frs_match_score = ?,
                            frs_match_distance_km = ?
                        WHERE facility_id = ?
                        """, [
                            match['frs_registry_id'],
                            match['match_score'],
                            match['distance_km'],
                            f"GEM_{match['gem_id']}"
                        ])

                    logger.info(f"  Updated {len(matches_df)} GEM-FRS matches")

            # Update nearest ports
            if tables['schedule_k_ports']:
                # Process GEM facilities
                if tables['gem_cement_plants']:
                    logger.info("Calculating nearest ports for GEM plants...")
                    gem_ports = self.calculate_nearest_ports('gem', con)

                    if not gem_ports.empty:
                        for _, row in gem_ports.iterrows():
                            con.execute("""
                            UPDATE master_facilities
                            SET nearest_port_code = ?,
                                nearest_port_name = ?,
                                nearest_port_distance_km = ?
                            WHERE facility_id = ?
                            """, [
                                row['nearest_port_code'],
                                row['nearest_port_name'],
                                row['port_distance_km'],
                                f"GEM_{row['facility_id']}"
                            ])

                # Process FRS facilities
                if tables['frs_facilities']:
                    logger.info("Calculating nearest ports for FRS facilities...")
                    frs_ports = self.calculate_nearest_ports('frs', con)

                    if not frs_ports.empty:
                        for _, row in frs_ports.iterrows():
                            con.execute("""
                            UPDATE master_facilities
                            SET nearest_port_code = ?,
                                nearest_port_name = ?,
                                nearest_port_distance_km = ?
                            WHERE facility_id = ?
                            """, [
                                row['nearest_port_code'],
                                row['nearest_port_name'],
                                row['port_distance_km'],
                                f"FRS_{row['facility_id']}"
                            ])

            # Create summary views
            self._create_master_views(con)

            # Final count
            total = con.execute("SELECT COUNT(*) FROM master_facilities").fetchone()[0]
            logger.info(f"Master facilities table created with {total:,} total records")

        finally:
            con.close()

    def _create_master_views(self, con: duckdb.DuckDBPyConnection) -> None:
        """Create useful views on the master table."""

        # Country summary
        con.execute("""
        CREATE OR REPLACE VIEW master_country_summary AS
        SELECT
            country,
            source,
            COUNT(*) as facility_count,
            SUM(capacity_mtpa) as total_capacity_mtpa,
            COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as geocoded_count,
            COUNT(CASE WHEN nearest_port_code IS NOT NULL THEN 1 END) as port_linked_count,
            AVG(nearest_port_distance_km) as avg_port_distance_km
        FROM master_facilities
        GROUP BY country, source
        ORDER BY facility_count DESC
        """)

        # US integrated view (GEM + FRS matched)
        con.execute("""
        CREATE OR REPLACE VIEW us_integrated_facilities AS
        SELECT
            m.*,
            frs.naics_codes as frs_naics,
            frs.facility_name as frs_facility_name
        FROM master_facilities m
        LEFT JOIN frs_facilities frs ON m.matched_frs_id = frs.registry_id
        WHERE m.source = 'GEM' AND m.country IN ('United States', 'USA', 'US')
        ORDER BY m.capacity_mtpa DESC NULLS LAST
        """)

        # Port proximity view
        con.execute("""
        CREATE OR REPLACE VIEW facilities_by_port AS
        SELECT
            nearest_port_code,
            nearest_port_name,
            COUNT(*) as facility_count,
            SUM(capacity_mtpa) as total_capacity_mtpa,
            AVG(nearest_port_distance_km) as avg_distance_km,
            MIN(nearest_port_distance_km) as min_distance_km
        FROM master_facilities
        WHERE nearest_port_code IS NOT NULL
        GROUP BY nearest_port_code, nearest_port_name
        ORDER BY facility_count DESC
        """)

        logger.info("Created views: master_country_summary, us_integrated_facilities, facilities_by_port")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the master facilities table.

        Returns:
            Dictionary with master table statistics
        """
        con = self._connect(read_only=True)

        try:
            stats = {}

            # Total facilities
            stats['total_facilities'] = con.execute(
                "SELECT COUNT(*) FROM master_facilities"
            ).fetchone()[0]

            # By source
            by_source = con.execute("""
                SELECT source, COUNT(*) as count
                FROM master_facilities
                GROUP BY source
            """).fetchdf()
            stats['by_source'] = by_source.to_dict('records')

            # Countries
            stats['total_countries'] = con.execute(
                "SELECT COUNT(DISTINCT country) FROM master_facilities WHERE country IS NOT NULL"
            ).fetchone()[0]

            # GEM-FRS matches
            stats['gem_frs_matches'] = con.execute(
                "SELECT COUNT(*) FROM master_facilities WHERE matched_frs_id IS NOT NULL"
            ).fetchone()[0]

            # Port linkages
            stats['port_linked'] = con.execute(
                "SELECT COUNT(*) FROM master_facilities WHERE nearest_port_code IS NOT NULL"
            ).fetchone()[0]

            return stats

        except Exception as e:
            logger.warning(f"Error getting master stats: {e}")
            return {}
        finally:
            con.close()


# Convenience functions
def build_master_facilities(atlas_db_path: str) -> None:
    """
    Build the master facilities table.

    Args:
        atlas_db_path: Path to ATLAS DuckDB database
    """
    builder = FacilityMasterBuilder(atlas_db_path)
    builder.create_master_table()


def get_master_stats(atlas_db_path: str) -> Dict[str, Any]:
    """
    Get statistics about the master facilities table.

    Args:
        atlas_db_path: Path to ATLAS DuckDB database

    Returns:
        Dictionary with statistics
    """
    builder = FacilityMasterBuilder(atlas_db_path)
    return builder.get_stats()


def query_master_by_country(atlas_db_path: str, country: str) -> pd.DataFrame:
    """
    Query master facilities by country.

    Args:
        atlas_db_path: Path to ATLAS database
        country: Country name to query

    Returns:
        DataFrame with matching facilities
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
        SELECT *
        FROM master_facilities
        WHERE UPPER(country) LIKE UPPER(?)
        ORDER BY capacity_mtpa DESC NULLS LAST
        """
        return con.execute(query, [f"%{country}%"]).fetchdf()
    finally:
        con.close()


def get_gem_frs_matches(atlas_db_path: str) -> pd.DataFrame:
    """
    Get all GEM-FRS facility matches.

    Args:
        atlas_db_path: Path to ATLAS database

    Returns:
        DataFrame with matched facilities
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
        SELECT
            facility_id,
            facility_name,
            gem_id,
            matched_frs_id,
            frs_match_score,
            frs_match_distance_km,
            capacity_mtpa,
            owner_name
        FROM master_facilities
        WHERE matched_frs_id IS NOT NULL
        ORDER BY frs_match_score DESC
        """
        return con.execute(query).fetchdf()
    finally:
        con.close()
