"""Query engine for EPA FRS data analysis."""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from tabulate import tabulate

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_db_connection() -> duckdb.DuckDBPyConnection:
    """Get DuckDB connection."""
    config = load_config()
    db_path = config['database']['path']
    return duckdb.connect(db_path, read_only=False)


def query_facilities(
    state: Optional[str] = None,
    naics_prefix: Optional[str] = None,
    name_pattern: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 100,
    output_format: str = "table"
) -> pd.DataFrame:
    """
    Query facilities with flexible filters.

    Args:
        state: State code filter (e.g., 'VA')
        naics_prefix: NAICS code prefix filter (e.g., '325' for chemicals)
        name_pattern: Facility name pattern (SQL LIKE pattern)
        city: City name filter
        limit: Maximum rows to return
        output_format: 'table' for formatted output, 'csv' for CSV, 'dataframe' for raw

    Returns:
        Query results as DataFrame
    """
    conn = get_db_connection()

    # Build query dynamically
    query = """
        SELECT DISTINCT
            f.registry_id,
            f.fac_name,
            f.fac_street,
            f.fac_city,
            f.fac_state,
            f.fac_zip,
            f.fac_county,
            f.fac_epa_region
        FROM facilities f
        WHERE 1=1
    """

    params = []

    if state:
        query += " AND f.fac_state = ?"
        params.append(state.upper())

    if city:
        query += " AND LOWER(f.fac_city) LIKE LOWER(?)"
        params.append(f"%{city}%")

    if name_pattern:
        query += " AND LOWER(f.fac_name) LIKE LOWER(?)"
        params.append(f"%{name_pattern}%")

    if naics_prefix:
        query += """
            AND f.registry_id IN (
                SELECT DISTINCT registry_id
                FROM naics_codes
                WHERE naics_code LIKE ?
            )
        """
        params.append(f"{naics_prefix}%")

    query += f" LIMIT {limit}"

    logger.info(f"Executing query with filters: state={state}, naics={naics_prefix}, name={name_pattern}, city={city}")

    df = conn.execute(query, params).df()

    if output_format == "table":
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def query_facility_programs(registry_id: str, output_format: str = "table") -> pd.DataFrame:
    """
    Get all program linkages for a specific facility.

    Args:
        registry_id: Facility registry ID
        output_format: Output format ('table', 'csv', or 'dataframe')

    Returns:
        Query results as DataFrame
    """
    conn = get_db_connection()

    query = """
        SELECT
            p.pgm_sys_acrnm,
            p.pgm_sys_id,
            p.primary_name,
            p.location_address,
            p.city_name,
            p.state_code,
            p.site_type_name
        FROM program_links p
        WHERE p.registry_id = ?
    """

    df = conn.execute(query, [registry_id]).df()

    if output_format == "table":
        print(f"\nProgram Links for Registry ID: {registry_id}")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def query_facility_naics(registry_id: str, output_format: str = "table") -> pd.DataFrame:
    """
    Get all NAICS codes for a specific facility.

    Args:
        registry_id: Facility registry ID
        output_format: Output format ('table', 'csv', or 'dataframe')

    Returns:
        Query results as DataFrame
    """
    conn = get_db_connection()

    query = """
        SELECT
            n.naics_code,
            n.pgm_sys_acrnm,
            n.naics_primary_indicator,
            l.description
        FROM naics_codes n
        LEFT JOIN naics_lookup l ON SUBSTRING(n.naics_code, 1, 2) = l.naics_code
        WHERE n.registry_id = ?
    """

    df = conn.execute(query, [registry_id]).df()

    if output_format == "table":
        print(f"\nNAICS Codes for Registry ID: {registry_id}")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def get_naics_distribution(
    state: Optional[str] = None,
    digit_level: int = 2,
    top_n: int = 20,
    output_format: str = "table"
) -> pd.DataFrame:
    """
    Get distribution of NAICS codes.

    Args:
        state: Optional state filter
        digit_level: NAICS digit level (2, 3, 4, or 6)
        top_n: Number of top codes to return
        output_format: Output format

    Returns:
        DataFrame with NAICS distribution
    """
    conn = get_db_connection()

    state_filter = ""
    params = [digit_level]

    if state:
        state_filter = """
            AND n.registry_id IN (
                SELECT registry_id FROM facilities WHERE state_code = ?
            )
        """
        params.append(state.upper())

    query = f"""
        SELECT
            SUBSTRING(n.naics_code, 1, ?) as naics_code,
            l.description,
            COUNT(DISTINCT n.registry_id) as facility_count,
            COUNT(*) as total_records
        FROM naics_codes n
        LEFT JOIN naics_lookup l ON SUBSTRING(n.naics_code, 1, 2) = l.naics_code
        WHERE n.naics_code IS NOT NULL
        {state_filter}
        GROUP BY SUBSTRING(n.naics_code, 1, ?), l.description
        ORDER BY facility_count DESC
        LIMIT {top_n}
    """

    # Add digit_level parameter again for the GROUP BY
    params.insert(1, digit_level)

    df = conn.execute(query, params).df()

    if output_format == "table":
        print(f"\nTop {top_n} NAICS Codes ({digit_level}-digit level)")
        if state:
            print(f"State: {state}")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def get_facility_count_by_state(output_format: str = "table") -> pd.DataFrame:
    """
    Get facility count by state.

    Args:
        output_format: Output format

    Returns:
        DataFrame with state counts
    """
    conn = get_db_connection()

    query = """
        SELECT
            fac_state as state_code,
            COUNT(*) as facility_count
        FROM facilities
        WHERE fac_state IS NOT NULL
        GROUP BY fac_state
        ORDER BY facility_count DESC
    """

    df = conn.execute(query).df()

    if output_format == "table":
        print("\nFacility Count by State")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def get_facility_count_by_epa_region(output_format: str = "table") -> pd.DataFrame:
    """
    Get facility count by EPA region.

    Args:
        output_format: Output format

    Returns:
        DataFrame with EPA region counts
    """
    conn = get_db_connection()

    query = """
        SELECT
            fac_epa_region as epa_region_code,
            COUNT(*) as facility_count
        FROM facilities
        WHERE fac_epa_region IS NOT NULL
        GROUP BY fac_epa_region
        ORDER BY fac_epa_region
    """

    df = conn.execute(query).df()

    if output_format == "table":
        print("\nFacility Count by EPA Region")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df


def get_program_summary(output_format: str = "table") -> pd.DataFrame:
    """
    Get summary of program linkages.

    Args:
        output_format: Output format

    Returns:
        DataFrame with program summary
    """
    conn = get_db_connection()

    query = """
        SELECT
            pgm_sys_acrnm,
            COUNT(DISTINCT registry_id) as facility_count,
            COUNT(*) as total_links
        FROM program_links
        WHERE pgm_sys_acrnm IS NOT NULL
        GROUP BY pgm_sys_acrnm
        ORDER BY facility_count DESC
    """

    df = conn.execute(query).df()

    if output_format == "table":
        print("\nProgram System Summary")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    elif output_format == "csv":
        print(df.to_csv(index=False))

    return df
