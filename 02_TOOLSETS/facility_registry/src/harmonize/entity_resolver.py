"""Entity resolution and parent company harmonization."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process
import yaml

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


def load_parent_mapping() -> Dict[str, str]:
    """Load manual parent company mappings from JSON."""
    mapping_path = Path("config/parent_mapping.json")
    with open(mapping_path, "r") as f:
        data = json.load(f)
        return data.get("mappings", {})


def save_parent_mapping(mappings: Dict[str, str]) -> None:
    """Save parent company mappings to JSON."""
    mapping_path = Path("config/parent_mapping.json")
    data = {
        "_comment": "Curated parent corporation entity rollup mappings",
        "_format": "normalized_name -> parent_company_name",
        "mappings": mappings
    }
    with open(mapping_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(mappings)} parent mappings to {mapping_path}")


def normalize_org_name(name: str) -> str:
    """
    Normalize organization name for matching.

    Removes common suffixes, standardizes spacing, converts to uppercase.

    Args:
        name: Original organization name

    Returns:
        Normalized name
    """
    if not name or pd.isna(name):
        return ""

    # Convert to uppercase
    normalized = str(name).upper().strip()

    # Remove common business entity suffixes
    suffixes = [
        r'\bINCORPORATED\b',
        r'\bINC\.?\b',
        r'\bCORPORATION\b',
        r'\bCORP\.?\b',
        r'\bCOMPANY\b',
        r'\bCO\.?\b',
        r'\bLIMITED\b',
        r'\bLTD\.?\b',
        r'\bL\.L\.C\.?\b',
        r'\bLLC\.?\b',
        r'\bLLC\b',
        r'\bL\.P\.?\b',
        r'\bLLP\.?\b',
        r'\bPLLC\.?\b',
        r'\bP\.C\.?\b',
        r'\bLIMITED LIABILITY COMPANY\b',
        r'\bLIMITED LIABILITY CORPORATION\b',
        r'\bLIMITED PARTNERSHIP\b',
        r'\bPROFESSIONAL CORPORATION\b',
    ]

    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)

    # Remove location-specific terms
    location_terms = [
        r'\bFLORIDA\b',
        r'\bCALIFORNIA\b',
        r'\bTEXAS\b',
        r'\bPACIFIC\b',
        r'\bSOUTH\b',
        r'\bNORTH\b',
        r'\bEAST\b',
        r'\bWEST\b',
        r'\bMIDWEST\b',
        r'\bILLINOIS\b',
        r'\bOHIO\b',
        r'\bMICHIGAN\b',
        r'\bVIRGINIA\b',
        r'\bGEORGIA\b',
    ]

    for term in location_terms:
        normalized = re.sub(term, '', normalized)

    # Remove operation/product-specific terms
    operation_terms = [
        r'\bREADY MIX\b',
        r'\bREADY-MIX\b',
        r'\bREADYMIX\b',
        r'\bCONCRETE\b',
        r'\bCEMENT\b',
        r'\bPRECAST\b',
        r'\bCONSTRUCTION MATERIALS\b',
        r'\bMATERIALS\b',
        r'\bPRODUCTS\b',
        r'\bINDUSTRIES\b',
        r'\bMANUFACTURING\b',
        r'\bPLANT\b',
        r'\bFACILITY\b',
        r'\bDIVISION\b',
        r'\bOPERATIONS\b',
    ]

    for term in operation_terms:
        normalized = re.sub(term, '', normalized)

    # Clean up extra whitespace and punctuation
    normalized = re.sub(r'[,\.\-\(\)]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()

    return normalized


def extract_base_company_name(name: str) -> str:
    """
    Extract the base company name from a facility name.

    This is more aggressive than normalize - tries to get core brand.

    Args:
        name: Facility name

    Returns:
        Base company name
    """
    normalized = normalize_org_name(name)

    # If empty after normalization, return original
    if not normalized:
        return str(name).upper().strip()

    # Split into words and take first 1-3 significant words
    words = normalized.split()

    # Filter out common filler words
    filler_words = {'THE', 'A', 'AN', 'OF', 'AND', 'OR', 'IN', 'ON', 'AT', 'TO',
                   'FOR', 'BY', 'WITH', 'FROM', 'AS', 'GROUP', 'COMPANIES'}

    significant_words = [w for w in words if w not in filler_words]

    # Take first 1-2 words as base name
    if len(significant_words) >= 2:
        base = ' '.join(significant_words[:2])
    elif len(significant_words) == 1:
        base = significant_words[0]
    else:
        # Fallback to first word of normalized
        base = words[0] if words else normalized

    return base


def suggest_parent_companies(
    conn: duckdb.DuckDBPyConnection,
    min_facilities: int = 3,
    similarity_threshold: int = 85
) -> pd.DataFrame:
    """
    Analyze facility names and suggest parent company rollups.

    Args:
        conn: DuckDB connection
        min_facilities: Minimum facilities to consider a company
        similarity_threshold: Fuzzy match threshold (0-100)

    Returns:
        DataFrame with suggested parent companies
    """
    # Get all facility names
    query = """
        SELECT DISTINCT
            fac_name,
            COUNT(*) as facility_count
        FROM facilities
        WHERE fac_name IS NOT NULL
        GROUP BY fac_name
        HAVING COUNT(*) >= ?
        ORDER BY facility_count DESC
    """

    df = conn.execute(query, [min_facilities]).df()

    logger.info(f"Analyzing {len(df)} facility name groups...")

    # Extract base names
    df['normalized_name'] = df['fac_name'].apply(normalize_org_name)
    df['base_company'] = df['fac_name'].apply(extract_base_company_name)

    # Group by base company
    grouped = df.groupby('base_company').agg({
        'fac_name': list,
        'facility_count': 'sum',
        'normalized_name': list
    }).reset_index()

    # Filter to companies with multiple variations
    grouped = grouped[grouped['fac_name'].apply(len) > 1]
    grouped = grouped.sort_values('facility_count', ascending=False)

    logger.info(f"Found {len(grouped)} parent companies with multiple facility names")

    return grouped


def create_parent_company_table(
    conn: duckdb.DuckDBPyConnection,
    manual_mappings: Optional[Dict[str, str]] = None
) -> None:
    """
    Create a parent_company lookup table in DuckDB.

    Args:
        conn: DuckDB connection
        manual_mappings: Optional manual parent company mappings
    """
    # Load existing manual mappings if not provided
    if manual_mappings is None:
        manual_mappings = load_parent_mapping()

    # Get all facility names
    query = """
        SELECT DISTINCT fac_name
        FROM facilities
        WHERE fac_name IS NOT NULL
    """

    df = conn.execute(query).df()
    logger.info(f"Processing {len(df)} unique facility names...")

    # Create parent company assignments
    results = []

    for fac_name in df['fac_name']:
        normalized = normalize_org_name(fac_name)

        # Check manual mappings first
        if normalized in manual_mappings:
            parent = manual_mappings[normalized]
        else:
            # Use base company extraction
            parent = extract_base_company_name(fac_name)

        results.append({
            'fac_name_original': fac_name,
            'fac_name_normalized': normalized,
            'parent_company': parent
        })

    parent_df = pd.DataFrame(results)

    # Create table in DuckDB
    conn.execute("DROP TABLE IF EXISTS parent_company_lookup")
    conn.execute("""
        CREATE TABLE parent_company_lookup (
            fac_name_original VARCHAR,
            fac_name_normalized VARCHAR,
            parent_company VARCHAR
        )
    """)

    conn.execute("INSERT INTO parent_company_lookup SELECT * FROM parent_df")

    logger.info(f"Created parent_company_lookup table with {len(parent_df)} entries")

    # Print summary
    summary = parent_df.groupby('parent_company').size().sort_values(ascending=False).head(20)
    print("\nTop 20 Parent Companies by Facility Count:")
    print("="*80)
    for parent, count in summary.items():
        print(f"  {parent:40s}: {count:5d} facilities")


def export_facilities_with_parent(
    conn: duckdb.DuckDBPyConnection,
    naics_filter: Optional[str] = None,
    output_file: str = "facilities_with_parent_company.csv"
) -> pd.DataFrame:
    """
    Export facilities with parent company rollup.

    Args:
        conn: DuckDB connection
        naics_filter: Optional NAICS code filter (e.g., '3273%')
        output_file: Output CSV filename

    Returns:
        DataFrame with facilities and parent companies
    """
    naics_clause = ""
    if naics_filter:
        naics_clause = f"AND n.naics_code LIKE '{naics_filter}'"

    query = f"""
        SELECT DISTINCT
            f.registry_id,
            f.fac_name as facility_name_original,
            p.parent_company,
            f.fac_street,
            f.fac_city,
            f.fac_state,
            f.fac_zip,
            f.fac_county,
            f.fac_epa_region,
            f.latitude,
            f.longitude,
            n.naics_code
        FROM facilities f
        LEFT JOIN parent_company_lookup p ON f.fac_name = p.fac_name_original
        LEFT JOIN naics_codes n ON f.registry_id = n.registry_id
        WHERE 1=1 {naics_clause}
        ORDER BY p.parent_company, f.fac_state, f.fac_city
    """

    df = conn.execute(query).df()
    df.to_csv(output_file, index=False)

    logger.info(f"Exported {len(df)} facilities to {output_file}")

    return df


def analyze_parent_company_coverage(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Analyze parent company assignments and coverage.

    Args:
        conn: DuckDB connection

    Returns:
        DataFrame with parent company statistics
    """
    query = """
        SELECT
            p.parent_company,
            COUNT(DISTINCT f.fac_name) as unique_facility_names,
            COUNT(DISTINCT f.registry_id) as total_facilities,
            COUNT(DISTINCT f.fac_state) as states_present,
            STRING_AGG(DISTINCT f.fac_state, ', ') as states
        FROM facilities f
        LEFT JOIN parent_company_lookup p ON f.fac_name = p.fac_name_original
        WHERE p.parent_company IS NOT NULL
        GROUP BY p.parent_company
        HAVING total_facilities >= 5
        ORDER BY total_facilities DESC
    """

    df = conn.execute(query).df()

    print("\nParent Company Coverage Analysis")
    print("="*120)
    print(f"Total parent companies: {len(df)}")
    print(f"Total facilities covered: {df['total_facilities'].sum():,}")

    return df
