"""Statistical analysis and summary functions for EPA FRS data."""

import logging
from typing import Optional, Dict, Any
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


def get_summary_stats(
    state: Optional[str] = None,
    naics_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive summary statistics.

    Args:
        state: Optional state filter
        naics_prefix: Optional NAICS prefix filter

    Returns:
        Dictionary of summary statistics
    """
    conn = get_db_connection()

    stats = {}

    # Base filters
    facility_filter = "WHERE 1=1"
    params = []

    if state:
        facility_filter += " AND fac_state = ?"
        params.append(state.upper())

    # Total facility count
    query = f"SELECT COUNT(*) FROM facilities {facility_filter}"
    stats['total_facilities'] = conn.execute(query, params).fetchone()[0]

    # Count with coordinates
    query = f"""
        SELECT COUNT(*)
        FROM facilities f
        LEFT JOIN program_links p ON f.registry_id = p.registry_id
        {facility_filter}
    """
    # Note: Actual lat/lon may be in facilities or require join with geospatial table
    # For ECHO files, coordinates might not be directly in facilities table

    # State count
    if not state:
        query = "SELECT COUNT(DISTINCT fac_state) FROM facilities WHERE fac_state IS NOT NULL"
        stats['unique_states'] = conn.execute(query).fetchone()[0]

    # EPA region count
    query = f"SELECT COUNT(DISTINCT fac_epa_region) FROM facilities {facility_filter} AND fac_epa_region IS NOT NULL"
    stats['unique_epa_regions'] = conn.execute(query, params).fetchone()[0]

    # Program count
    naics_filter = ""
    if naics_prefix:
        naics_filter = " AND registry_id IN (SELECT registry_id FROM naics_codes WHERE naics_code LIKE ?)"
        params.append(f"{naics_prefix}%")

    query = f"""
        SELECT COUNT(DISTINCT pgm_sys_acrnm)
        FROM program_links
        WHERE registry_id IN (
            SELECT registry_id FROM facilities {facility_filter}
        )
        {naics_filter}
    """
    stats['unique_programs'] = conn.execute(query, params).fetchone()[0]

    # NAICS code count
    naics_params = params.copy()
    if naics_prefix and naics_prefix not in naics_params:
        naics_params.append(f"{naics_prefix}%")

    naics_state_filter = ""
    if state:
        naics_state_filter = "AND registry_id IN (SELECT registry_id FROM facilities WHERE fac_state = ?)"

    query = f"""
        SELECT COUNT(DISTINCT naics_code)
        FROM naics_codes
        WHERE naics_code IS NOT NULL
        {naics_state_filter}
        {"AND naics_code LIKE ?" if naics_prefix else ""}
    """
    stats['unique_naics_codes'] = conn.execute(query, naics_params[:1] + ([naics_params[-1]] if naics_prefix else [])).fetchone()[0]

    return stats


def print_summary_stats(
    state: Optional[str] = None,
    naics_prefix: Optional[str] = None
) -> None:
    """
    Print formatted summary statistics.

    Args:
        state: Optional state filter
        naics_prefix: Optional NAICS prefix filter
    """
    stats = get_summary_stats(state, naics_prefix)

    print("\n" + "="*80)
    print("SUMMARY STATISTICS")

    if state:
        print(f"State: {state}")
    if naics_prefix:
        print(f"NAICS Prefix: {naics_prefix}")

    print("="*80)

    for key, value in stats.items():
        label = key.replace('_', ' ').title()
        print(f"{label:30s}: {value:,}")

    print("="*80 + "\n")


def get_null_rate_analysis() -> pd.DataFrame:
    """
    Analyze null rates across key fields in facilities table.

    Returns:
        DataFrame with null rate analysis
    """
    conn = get_db_connection()

    # Get column names from facilities table
    columns = conn.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'facilities'
    """).df()['column_name'].tolist()

    null_rates = []

    for col in columns:
        query = f"""
            SELECT
                '{col}' as column_name,
                COUNT(*) as total_rows,
                SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) as null_count,
                ROUND(100.0 * SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as null_rate_pct
            FROM facilities
        """
        result = conn.execute(query).fetchone()
        null_rates.append(result)

    df = pd.DataFrame(null_rates, columns=['column_name', 'total_rows', 'null_count', 'null_rate_pct'])
    df = df.sort_values('null_rate_pct', ascending=False)

    print("\nNull Rate Analysis - Facilities Table")
    print("="*80)
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

    return df


def get_outlier_detection(
    field: str = 'postal_code',
    table: str = 'facilities'
) -> pd.DataFrame:
    """
    Detect outliers or data quality issues.

    Args:
        field: Field to analyze
        table: Table name

    Returns:
        DataFrame with outlier analysis
    """
    conn = get_db_connection()

    # Example: Find unusual ZIP codes
    if field == 'postal_code' and table == 'facilities':
        query = """
            SELECT
                postal_code,
                COUNT(*) as count,
                LENGTH(postal_code) as zip_length
            FROM facilities
            WHERE postal_code IS NOT NULL
            GROUP BY postal_code, LENGTH(postal_code)
            HAVING LENGTH(postal_code) NOT IN (5, 10)  -- Normal ZIP or ZIP+4
            ORDER BY count DESC
            LIMIT 50
        """
        df = conn.execute(query).df()

        print(f"\nOutlier Detection: {field} in {table}")
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

        return df

    return pd.DataFrame()
