#!/usr/bin/env python3
"""
USGS Cement Data ETL Module
============================
Loads USGS cement industry data from Monthly Industry Surveys (MIS) and
Minerals Yearbook (MYB) Excel files into ATLAS database.

Data Sources:
    - MIS: Monthly Industry Surveys with regional shipments, production, imports
    - MYB: Annual Minerals Yearbook with national statistics

Tables Created:
    - usgs_monthly_shipments: State-level cement shipments
    - usgs_monthly_production: District-level cement/clinker production
    - usgs_monthly_imports: Port/country-level imports
    - usgs_annual_stats: Annual national statistics
"""

import duckdb
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}


def parse_value(val: Any) -> Optional[float]:
    """
    Parse a numeric value that may contain formatting or markers.

    Handles:
        - Numbers with commas: '466,143'
        - Values with revision markers: '466,143 r' or '85,836e'
        - Withheld data: 'W' or '--' or '(D)'
        - Empty/NaN values

    Args:
        val: Raw value from Excel cell

    Returns:
        Float value or None if withheld/missing
    """
    if pd.isna(val) or val is None:
        return None

    # Handle numeric types directly
    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip()

    # Handle withheld/missing data markers
    if val_str.upper() in ('W', '--', '(D)', 'NA', 'N/A', ''):
        return None

    # Remove trailing revision markers (e, r, p) with possible space
    val_str = re.sub(r'\s*[erp]$', '', val_str, flags=re.IGNORECASE)

    # Remove commas (thousand separators)
    val_str = val_str.replace(',', '')

    # Remove any remaining whitespace
    val_str = val_str.strip()

    if not val_str:
        return None

    try:
        return float(val_str)
    except (ValueError, TypeError):
        return None


def extract_year_month_from_filename(filename: str) -> Tuple[int, int]:
    """
    Extract year and month from MIS filename pattern.

    Args:
        filename: Filename like 'mis-202401-cemen.xlsx'

    Returns:
        Tuple of (year, month)
    """
    # Pattern: mis-YYYYMM-cemen*.xlsx
    match = re.search(r'mis-(\d{4})(\d{2})', filename, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))

    raise ValueError(f"Cannot extract year/month from filename: {filename}")


def extract_year_from_myb_filename(filename: str) -> int:
    """
    Extract year from MYB filename pattern.

    Args:
        filename: Filename like 'myb1-2023-cemen-ERT.xlsx'

    Returns:
        Year as integer
    """
    # Pattern: myb1-YYYY-cemen*.xlsx
    match = re.search(r'myb1-(\d{4})', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))

    raise ValueError(f"Cannot extract year from filename: {filename}")


class USGSCementLoader:
    """Handles loading and processing of USGS cement industry data."""

    def __init__(self, usgs_data_dir: str, atlas_db_path: str):
        """
        Initialize USGS Cement Loader.

        Args:
            usgs_data_dir: Path to USGS data directory (containing mis/ and myb/)
            atlas_db_path: Path to ATLAS DuckDB database
        """
        self.usgs_data_dir = Path(usgs_data_dir)
        self.atlas_db_path = atlas_db_path
        self.mis_dir = self.usgs_data_dir / 'mis'
        self.myb_dir = self.usgs_data_dir / 'myb'

    def _create_tables(self, con: duckdb.DuckDBPyConnection) -> None:
        """Create database tables for USGS data."""
        logger.info("Creating USGS tables...")

        # Monthly shipments by state destination
        con.execute("""
        CREATE TABLE IF NOT EXISTS usgs_monthly_shipments (
            year INTEGER,
            month INTEGER,
            state VARCHAR,
            shipments_short_tons DOUBLE,
            data_source VARCHAR,
            load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (year, month, state)
        )
        """)

        # Monthly production by district
        con.execute("""
        CREATE TABLE IF NOT EXISTS usgs_monthly_production (
            year INTEGER,
            month INTEGER,
            district VARCHAR,
            cement_shipments_short_tons DOUBLE,
            clinker_production_short_tons DOUBLE,
            data_source VARCHAR,
            load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (year, month, district)
        )
        """)

        # Monthly imports by country and port
        con.execute("""
        CREATE TABLE IF NOT EXISTS usgs_monthly_imports (
            year INTEGER,
            month INTEGER,
            customs_district VARCHAR,
            country VARCHAR,
            imports_metric_tons DOUBLE,
            data_source VARCHAR,
            load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (year, month, customs_district, country)
        )
        """)

        # Annual national statistics
        con.execute("""
        CREATE TABLE IF NOT EXISTS usgs_annual_stats (
            year INTEGER PRIMARY KEY,
            cement_production_kt DOUBLE,
            clinker_production_kt DOUBLE,
            shipments_kt DOUBLE,
            imports_kt DOUBLE,
            exports_kt DOUBLE,
            consumption_kt DOUBLE,
            data_source VARCHAR,
            load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        logger.info("USGS tables created successfully")

    def _create_summary_views(self, con: duckdb.DuckDBPyConnection) -> None:
        """Create summary views for easy querying."""
        logger.info("Creating USGS summary views...")

        # Annual shipments by state
        con.execute("""
        CREATE OR REPLACE VIEW usgs_annual_shipments_by_state AS
        SELECT
            year,
            state,
            SUM(shipments_short_tons) as total_shipments_short_tons,
            COUNT(*) as months_reported
        FROM usgs_monthly_shipments
        GROUP BY year, state
        ORDER BY year DESC, total_shipments_short_tons DESC
        """)

        # Monthly total shipments
        con.execute("""
        CREATE OR REPLACE VIEW usgs_monthly_total_shipments AS
        SELECT
            year,
            month,
            SUM(shipments_short_tons) as total_shipments_short_tons,
            COUNT(DISTINCT state) as states_reported
        FROM usgs_monthly_shipments
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        """)

        # Annual production by district
        con.execute("""
        CREATE OR REPLACE VIEW usgs_annual_production_by_district AS
        SELECT
            year,
            district,
            SUM(cement_shipments_short_tons) as total_cement_short_tons,
            SUM(clinker_production_short_tons) as total_clinker_short_tons,
            COUNT(*) as months_reported
        FROM usgs_monthly_production
        GROUP BY year, district
        ORDER BY year DESC, total_cement_short_tons DESC NULLS LAST
        """)

        # Annual imports by country
        con.execute("""
        CREATE OR REPLACE VIEW usgs_annual_imports_by_country AS
        SELECT
            year,
            country,
            SUM(imports_metric_tons) as total_imports_metric_tons,
            COUNT(DISTINCT customs_district) as entry_points,
            COUNT(*) as months_reported
        FROM usgs_monthly_imports
        GROUP BY year, country
        ORDER BY year DESC, total_imports_metric_tons DESC
        """)

        # Annual imports by port
        con.execute("""
        CREATE OR REPLACE VIEW usgs_annual_imports_by_port AS
        SELECT
            year,
            customs_district,
            SUM(imports_metric_tons) as total_imports_metric_tons,
            COUNT(DISTINCT country) as source_countries,
            COUNT(*) as months_reported
        FROM usgs_monthly_imports
        GROUP BY year, customs_district
        ORDER BY year DESC, total_imports_metric_tons DESC
        """)

        logger.info("USGS summary views created")

    def _parse_mis_state_shipments(self, file_path: Path) -> pd.DataFrame:
        """
        Parse state shipments from MIS file (T2AP1, T2AP2, T2AP3 sheets).

        Args:
            file_path: Path to MIS Excel file

        Returns:
            DataFrame with columns: year, month, state, shipments_short_tons
        """
        logger.info(f"Parsing state shipments from: {file_path.name}")

        records = []
        file_year, file_month = extract_year_month_from_filename(file_path.name)

        # Try to read each continuation sheet
        xlsx = pd.ExcelFile(file_path)
        sheet_names = [s for s in xlsx.sheet_names if s.startswith('T2A')]

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

                if len(df) < 5:
                    continue

                # Find year row (row 2) and month row (row 3)
                year_row = df.iloc[2]
                month_row = df.iloc[3]

                # Determine which years and months are in which columns
                col_info = []  # List of (col_idx, year, month)

                current_year = None
                for col_idx in range(1, len(df.columns)):
                    # Check if this column has a year
                    year_val = year_row.iloc[col_idx]
                    if pd.notna(year_val):
                        try:
                            current_year = int(year_val)
                        except (ValueError, TypeError):
                            pass

                    # Check month name
                    month_val = month_row.iloc[col_idx]
                    if pd.notna(month_val):
                        month_str = str(month_val).lower().strip()
                        # Handle annual total column
                        if 'december' in month_str or 'total' in month_str or 'annual' in month_str:
                            continue  # Skip annual totals

                        # Extract month
                        for month_name, month_num in MONTH_MAP.items():
                            if month_str.startswith(month_name):
                                if current_year:
                                    col_info.append((col_idx, current_year, month_num))
                                break

                # Parse state data rows (starting from row 4)
                for row_idx in range(4, len(df)):
                    row = df.iloc[row_idx]
                    state = row.iloc[0]

                    if pd.isna(state):
                        continue

                    state_str = str(state).strip()

                    # Skip subtotals, totals, footnotes
                    if any(skip in state_str.lower() for skip in
                           ['subtotal', 'total', 'footnote', 'note', 'source', 'table']):
                        continue

                    # Skip empty or numeric-only rows
                    if not state_str or state_str.replace('.', '').isdigit():
                        continue

                    # Clean state name (remove footnote markers)
                    state_clean = re.sub(r'[\d,\s]+$', '', state_str).strip()
                    state_clean = re.sub(r'\s*[erp]$', '', state_clean, flags=re.IGNORECASE).strip()

                    if not state_clean:
                        continue

                    # Extract values for each month column
                    for col_idx, year, month in col_info:
                        if col_idx < len(row):
                            val = parse_value(row.iloc[col_idx])
                            if val is not None:
                                # Convert metric tons to short tons (1 metric ton = 1.10231 short tons)
                                val_short_tons = val * 1.10231
                                records.append({
                                    'year': year,
                                    'month': month,
                                    'state': state_clean,
                                    'shipments_short_tons': val_short_tons
                                })

            except Exception as e:
                logger.warning(f"Error parsing sheet {sheet_name} in {file_path.name}: {e}")
                continue

        logger.info(f"Parsed {len(records)} state shipment records from {file_path.name}")
        return pd.DataFrame(records)

    def _parse_mis_district_production(self, file_path: Path) -> pd.DataFrame:
        """
        Parse district production from MIS file (T1A for shipments, T4 for clinker).

        Args:
            file_path: Path to MIS Excel file

        Returns:
            DataFrame with production data by district
        """
        logger.info(f"Parsing district production from: {file_path.name}")

        records = {}  # Key: (year, month, district)
        file_year, file_month = extract_year_month_from_filename(file_path.name)

        xlsx = pd.ExcelFile(file_path)

        # Parse T1A sheets for cement shipments
        t1a_sheets = [s for s in xlsx.sheet_names if s.startswith('T1A')]
        for sheet_name in t1a_sheets:
            self._parse_district_sheet(file_path, sheet_name, records, 'cement_shipments_short_tons')

        # Parse T4 sheets for clinker production
        t4_sheets = [s for s in xlsx.sheet_names if s.startswith('T4')]
        for sheet_name in t4_sheets:
            self._parse_district_sheet(file_path, sheet_name, records, 'clinker_production_short_tons')

        # Convert to DataFrame
        result_records = []
        for (year, month, district), data in records.items():
            result_records.append({
                'year': year,
                'month': month,
                'district': district,
                'cement_shipments_short_tons': data.get('cement_shipments_short_tons'),
                'clinker_production_short_tons': data.get('clinker_production_short_tons')
            })

        logger.info(f"Parsed {len(result_records)} district production records from {file_path.name}")
        return pd.DataFrame(result_records)

    def _parse_district_sheet(self, file_path: Path, sheet_name: str,
                              records: Dict, value_field: str) -> None:
        """Parse a single district sheet and update records dict."""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

            if len(df) < 5:
                return

            # Find year and month columns
            year_row = df.iloc[2]
            month_row = df.iloc[3]

            col_info = []
            current_year = None

            for col_idx in range(1, len(df.columns)):
                year_val = year_row.iloc[col_idx]
                if pd.notna(year_val):
                    try:
                        current_year = int(year_val)
                    except (ValueError, TypeError):
                        pass

                month_val = month_row.iloc[col_idx]
                if pd.notna(month_val):
                    month_str = str(month_val).lower().strip()
                    if 'december' in month_str or 'total' in month_str:
                        continue

                    for month_name, month_num in MONTH_MAP.items():
                        if month_str.startswith(month_name):
                            if current_year:
                                col_info.append((col_idx, current_year, month_num))
                            break

            # Parse district rows
            for row_idx in range(4, len(df)):
                row = df.iloc[row_idx]
                district = row.iloc[0]

                if pd.isna(district):
                    continue

                district_str = str(district).strip()

                # Skip headers, subtotals, totals
                if any(skip in district_str.lower() for skip in
                       ['subtotal', 'total', 'footnote', 'note', 'source', 'table',
                        'east north central', 'west north central', 'south atlantic',
                        'new england', 'middle atlantic']):
                    continue

                # Skip empty or section headers (all uppercase without numbers)
                if not district_str or district_str.isupper():
                    continue

                # Clean district name
                district_clean = re.sub(r'[\d]+$', '', district_str).strip()

                if not district_clean:
                    continue

                # Extract values
                for col_idx, year, month in col_info:
                    if col_idx < len(row):
                        val = parse_value(row.iloc[col_idx])
                        if val is not None:
                            # Convert metric tons to short tons
                            val_short_tons = val * 1.10231
                            key = (year, month, district_clean)
                            if key not in records:
                                records[key] = {}
                            records[key][value_field] = val_short_tons

        except Exception as e:
            logger.warning(f"Error parsing sheet {sheet_name}: {e}")

    def _parse_mis_imports(self, file_path: Path) -> pd.DataFrame:
        """
        Parse imports from MIS file (T5P1-T5P5 sheets).

        Args:
            file_path: Path to MIS Excel file

        Returns:
            DataFrame with import data by customs district and country
        """
        logger.info(f"Parsing imports from: {file_path.name}")

        records = []
        file_year, file_month = extract_year_month_from_filename(file_path.name)

        xlsx = pd.ExcelFile(file_path)
        t5_sheets = [s for s in xlsx.sheet_names if s.startswith('T5')]

        for sheet_name in t5_sheets:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

                if len(df) < 4:
                    continue

                # Row 2 has country names
                country_row = df.iloc[2]

                # Get countries from header (skip first column which is customs district)
                countries = []
                for col_idx in range(1, len(df.columns)):
                    country = country_row.iloc[col_idx]
                    if pd.notna(country):
                        country_str = str(country).strip()
                        # Skip 'Total' and similar aggregate columns
                        if country_str.lower() not in ('total', 'value', 'quantity'):
                            countries.append((col_idx, country_str))

                # Parse data rows (starting from row 3)
                for row_idx in range(3, len(df)):
                    row = df.iloc[row_idx]
                    customs_district = row.iloc[0]

                    if pd.isna(customs_district):
                        continue

                    district_str = str(customs_district).strip()

                    # Skip totals, footnotes
                    if any(skip in district_str.lower() for skip in
                           ['total', 'footnote', 'note', 'source', 'table']):
                        continue

                    if not district_str:
                        continue

                    # Clean district name (remove footnote markers)
                    district_clean = re.sub(r'[\d]+$', '', district_str).strip()

                    # Extract values for each country
                    for col_idx, country in countries:
                        if col_idx < len(row):
                            val = parse_value(row.iloc[col_idx])
                            if val is not None and val > 0:
                                records.append({
                                    'year': file_year,
                                    'month': file_month,
                                    'customs_district': district_clean,
                                    'country': country,
                                    'imports_metric_tons': val
                                })

            except Exception as e:
                logger.warning(f"Error parsing sheet {sheet_name} in {file_path.name}: {e}")
                continue

        logger.info(f"Parsed {len(records)} import records from {file_path.name}")
        return pd.DataFrame(records)

    def _parse_myb_annual_stats(self, file_path: Path) -> pd.DataFrame:
        """
        Parse annual statistics from MYB file (T1 sheet).

        Args:
            file_path: Path to MYB Excel file

        Returns:
            DataFrame with annual national statistics
        """
        logger.info(f"Parsing annual stats from: {file_path.name}")

        try:
            df = pd.read_excel(file_path, sheet_name='T1', header=None)
        except Exception as e:
            logger.warning(f"Error reading T1 sheet from {file_path.name}: {e}")
            return pd.DataFrame()

        # Find the year row (contains years like 2019, 2020, etc.)
        year_row_idx = None
        years = []
        year_cols = []

        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            row_years = []
            row_cols = []
            for col_idx in range(len(row)):
                val = row.iloc[col_idx]
                if pd.notna(val):
                    try:
                        year = int(float(val))
                        if 2000 <= year <= 2030:
                            row_years.append(year)
                            row_cols.append(col_idx)
                    except (ValueError, TypeError):
                        pass

            if len(row_years) >= 3:  # Found year row
                year_row_idx = idx
                years = row_years
                year_cols = row_cols
                break

        if not years:
            logger.warning(f"Could not find year row in {file_path.name}")
            return pd.DataFrame()

        logger.info(f"Found years: {years} at columns {year_cols}")

        # Track context for multi-row labels
        context = None  # 'production', 'imports', 'shipments', etc.

        # Initialize stats for each year
        year_stats = {}
        for year in years:
            year_stats[year] = {
                'year': year,
                'cement_production_kt': None,
                'clinker_production_kt': None,
                'shipments_kt': None,
                'imports_kt': None,
                'exports_kt': None,
                'consumption_kt': None
            }

        # Parse data rows
        for row_idx in range(year_row_idx + 1, min(len(df), year_row_idx + 30)):
            row_label = df.iloc[row_idx, 0]
            if pd.isna(row_label):
                continue

            label = str(row_label).lower().strip()

            # Skip footnotes
            if label.startswith('r') and len(label) < 3:
                continue
            if label.startswith('1') or label.startswith('2') or label.startswith('source'):
                break

            # Update context based on section headers
            if 'production:' in label or 'production' in label:
                context = 'production'
                continue
            elif 'shipment' in label:
                context = 'shipments'
                continue
            elif 'import' in label:
                context = 'imports'
                continue
            elif 'stock' in label:
                context = 'stocks'
                continue

            # Extract values for each year
            for year, col_idx in zip(years, year_cols):
                # Handle potential 'r' markers in adjacent columns
                val = None
                for offset in [0, 1]:
                    check_col = col_idx + offset
                    if check_col < len(df.columns):
                        cell_val = df.iloc[row_idx, check_col]
                        if pd.notna(cell_val):
                            parsed = parse_value(cell_val)
                            if parsed is not None:
                                val = parsed
                                break

                if val is None:
                    continue

                # Match to appropriate field based on label and context
                stats = year_stats[year]

                if label.startswith('cement') and context == 'production':
                    if stats['cement_production_kt'] is None:
                        stats['cement_production_kt'] = val
                elif label.startswith('clinker') and context == 'production':
                    if stats['clinker_production_kt'] is None:
                        stats['clinker_production_kt'] = val
                elif 'quantity' in label and context == 'shipments':
                    if stats['shipments_kt'] is None:
                        stats['shipments_kt'] = val
                elif 'export' in label and 'import' not in label:
                    if stats['exports_kt'] is None:
                        stats['exports_kt'] = val
                elif 'total' in label and context == 'imports':
                    if stats['imports_kt'] is None:
                        stats['imports_kt'] = val
                elif 'consumption' in label and 'apparent' in label:
                    if stats['consumption_kt'] is None:
                        stats['consumption_kt'] = val

        records = list(year_stats.values())
        result_df = pd.DataFrame(records)
        logger.info(f"Parsed {len(result_df)} annual statistics records from {file_path.name}")
        return result_df

    def load_mis_files(self) -> Dict[str, int]:
        """
        Load all MIS files from the data directory.

        Returns:
            Dictionary with counts of loaded records by type
        """
        if not self.mis_dir.exists():
            logger.warning(f"MIS directory not found: {self.mis_dir}")
            return {}

        mis_files = list(self.mis_dir.glob('mis-*.xlsx'))
        logger.info(f"Found {len(mis_files)} MIS files")

        all_shipments = []
        all_production = []
        all_imports = []

        for file_path in sorted(mis_files):
            try:
                # Parse state shipments
                shipments_df = self._parse_mis_state_shipments(file_path)
                if not shipments_df.empty:
                    all_shipments.append(shipments_df)

                # Parse district production
                production_df = self._parse_mis_district_production(file_path)
                if not production_df.empty:
                    all_production.append(production_df)

                # Parse imports
                imports_df = self._parse_mis_imports(file_path)
                if not imports_df.empty:
                    all_imports.append(imports_df)

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                continue

        # Combine all data
        counts = {}

        if all_shipments:
            combined_shipments = pd.concat(all_shipments, ignore_index=True)
            # Deduplicate, keeping latest
            combined_shipments = combined_shipments.drop_duplicates(
                subset=['year', 'month', 'state'], keep='last'
            )
            counts['shipments'] = len(combined_shipments)
            self._load_dataframe(combined_shipments, 'usgs_monthly_shipments', 'mis')

        if all_production:
            combined_production = pd.concat(all_production, ignore_index=True)
            combined_production = combined_production.drop_duplicates(
                subset=['year', 'month', 'district'], keep='last'
            )
            counts['production'] = len(combined_production)
            self._load_dataframe(combined_production, 'usgs_monthly_production', 'mis')

        if all_imports:
            combined_imports = pd.concat(all_imports, ignore_index=True)
            # Aggregate duplicate entries (same port/country/month)
            combined_imports = combined_imports.groupby(
                ['year', 'month', 'customs_district', 'country']
            ).agg({'imports_metric_tons': 'sum'}).reset_index()
            counts['imports'] = len(combined_imports)
            self._load_dataframe(combined_imports, 'usgs_monthly_imports', 'mis')

        return counts

    def load_myb_files(self) -> int:
        """
        Load all MYB files from the data directory.

        Returns:
            Count of loaded annual statistics records
        """
        if not self.myb_dir.exists():
            logger.warning(f"MYB directory not found: {self.myb_dir}")
            return 0

        myb_files = list(self.myb_dir.glob('myb1-*.xlsx'))
        logger.info(f"Found {len(myb_files)} MYB files")

        all_stats = []

        for file_path in sorted(myb_files):
            try:
                stats_df = self._parse_myb_annual_stats(file_path)
                if not stats_df.empty:
                    all_stats.append(stats_df)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                continue

        if all_stats:
            combined_stats = pd.concat(all_stats, ignore_index=True)
            # Deduplicate by year, keeping most recent file's data
            combined_stats = combined_stats.drop_duplicates(subset=['year'], keep='last')
            self._load_dataframe(combined_stats, 'usgs_annual_stats', 'myb')
            return len(combined_stats)

        return 0

    def _load_dataframe(self, df: pd.DataFrame, table_name: str, source: str) -> None:
        """Load a DataFrame into the database table."""
        con = duckdb.connect(self.atlas_db_path)

        try:
            # Add metadata columns
            df = df.copy()
            df['data_source'] = source
            df['load_timestamp'] = datetime.now()

            # Clear existing data and insert new
            con.execute(f"DELETE FROM {table_name}")

            # Handle column ordering based on table
            if table_name == 'usgs_monthly_shipments':
                cols = ['year', 'month', 'state', 'shipments_short_tons',
                        'data_source', 'load_timestamp']
            elif table_name == 'usgs_monthly_production':
                cols = ['year', 'month', 'district', 'cement_shipments_short_tons',
                        'clinker_production_short_tons', 'data_source', 'load_timestamp']
            elif table_name == 'usgs_monthly_imports':
                cols = ['year', 'month', 'customs_district', 'country',
                        'imports_metric_tons', 'data_source', 'load_timestamp']
            elif table_name == 'usgs_annual_stats':
                cols = ['year', 'cement_production_kt', 'clinker_production_kt',
                        'shipments_kt', 'imports_kt', 'exports_kt', 'consumption_kt',
                        'data_source', 'load_timestamp']
            else:
                cols = list(df.columns)

            # Ensure all columns exist
            for col in cols:
                if col not in df.columns:
                    df[col] = None

            df = df[cols]

            # Insert data
            con.execute(f"INSERT INTO {table_name} SELECT * FROM df")

            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"Loaded {count} records to {table_name}")

        finally:
            con.close()

    def refresh(self) -> Dict[str, Any]:
        """
        Execute full ETL pipeline for USGS data.

        Returns:
            Dictionary with load statistics
        """
        logger.info("Starting USGS Cement data refresh...")

        con = duckdb.connect(self.atlas_db_path)
        try:
            self._create_tables(con)
        finally:
            con.close()

        results = {}

        # Load MIS files
        mis_counts = self.load_mis_files()
        results['mis'] = mis_counts

        # Load MYB files
        myb_count = self.load_myb_files()
        results['myb'] = {'annual_stats': myb_count}

        # Create summary views
        con = duckdb.connect(self.atlas_db_path)
        try:
            self._create_summary_views(con)
        finally:
            con.close()

        logger.info("USGS Cement data refresh complete")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded USGS data.

        Returns:
            Dictionary with data statistics
        """
        con = duckdb.connect(self.atlas_db_path, read_only=True)

        try:
            stats = {}

            # Monthly shipments stats
            try:
                result = con.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT state) as states,
                        MIN(year) as min_year,
                        MAX(year) as max_year,
                        SUM(shipments_short_tons) as total_shipments
                    FROM usgs_monthly_shipments
                """).fetchone()
                stats['shipments'] = {
                    'total_records': result[0],
                    'states': result[1],
                    'year_range': f"{result[2]}-{result[3]}" if result[2] else None,
                    'total_short_tons': result[4]
                }
            except Exception:
                stats['shipments'] = None

            # Monthly production stats
            try:
                result = con.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT district) as districts,
                        MIN(year) as min_year,
                        MAX(year) as max_year
                    FROM usgs_monthly_production
                """).fetchone()
                stats['production'] = {
                    'total_records': result[0],
                    'districts': result[1],
                    'year_range': f"{result[2]}-{result[3]}" if result[2] else None
                }
            except Exception:
                stats['production'] = None

            # Monthly imports stats
            try:
                result = con.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT customs_district) as ports,
                        COUNT(DISTINCT country) as countries,
                        MIN(year) as min_year,
                        MAX(year) as max_year,
                        SUM(imports_metric_tons) as total_imports
                    FROM usgs_monthly_imports
                """).fetchone()
                stats['imports'] = {
                    'total_records': result[0],
                    'ports': result[1],
                    'countries': result[2],
                    'year_range': f"{result[3]}-{result[4]}" if result[3] else None,
                    'total_metric_tons': result[5]
                }
            except Exception:
                stats['imports'] = None

            # Annual stats
            try:
                result = con.execute("""
                    SELECT
                        COUNT(*) as total_years,
                        MIN(year) as min_year,
                        MAX(year) as max_year
                    FROM usgs_annual_stats
                """).fetchone()
                stats['annual'] = {
                    'total_years': result[0],
                    'year_range': f"{result[1]}-{result[2]}" if result[1] else None
                }
            except Exception:
                stats['annual'] = None

            # Top states by shipments
            try:
                top_states = con.execute("""
                    SELECT state, SUM(shipments_short_tons) as total
                    FROM usgs_monthly_shipments
                    GROUP BY state
                    ORDER BY total DESC
                    LIMIT 10
                """).fetchdf()
                stats['top_states'] = top_states.to_dict('records')
            except Exception:
                stats['top_states'] = []

            # Top import countries
            try:
                top_countries = con.execute("""
                    SELECT country, SUM(imports_metric_tons) as total
                    FROM usgs_monthly_imports
                    GROUP BY country
                    ORDER BY total DESC
                    LIMIT 10
                """).fetchdf()
                stats['top_import_countries'] = top_countries.to_dict('records')
            except Exception:
                stats['top_import_countries'] = []

            return stats

        except Exception as e:
            logger.warning(f"Error getting USGS stats: {e}")
            return {}
        finally:
            con.close()


# Convenience functions
def refresh_usgs_data(usgs_data_dir: str, atlas_db_path: str) -> Dict[str, Any]:
    """
    Convenience function to refresh USGS data in ATLAS.

    Args:
        usgs_data_dir: Path to USGS data directory
        atlas_db_path: Path to ATLAS DuckDB database

    Returns:
        Dictionary with load statistics
    """
    loader = USGSCementLoader(usgs_data_dir, atlas_db_path)
    return loader.refresh()


def get_usgs_stats(atlas_db_path: str) -> Dict[str, Any]:
    """
    Get statistics about USGS data in ATLAS.

    Args:
        atlas_db_path: Path to ATLAS DuckDB database

    Returns:
        Dictionary with USGS statistics
    """
    loader = USGSCementLoader("", atlas_db_path)
    return loader.get_stats()


def query_shipments_by_state(atlas_db_path: str, state: str,
                              year: Optional[int] = None) -> pd.DataFrame:
    """
    Query shipments by state.

    Args:
        atlas_db_path: Path to ATLAS database
        state: State name to query
        year: Optional year filter

    Returns:
        DataFrame with shipment data
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
            SELECT year, month, state, shipments_short_tons
            FROM usgs_monthly_shipments
            WHERE UPPER(state) LIKE UPPER(?)
        """
        params = [f"%{state}%"]

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY year DESC, month DESC"

        return con.execute(query, params).fetchdf()
    finally:
        con.close()


def query_imports_by_country(atlas_db_path: str, country: str,
                              year: Optional[int] = None) -> pd.DataFrame:
    """
    Query imports by country.

    Args:
        atlas_db_path: Path to ATLAS database
        country: Country name to query
        year: Optional year filter

    Returns:
        DataFrame with import data
    """
    con = duckdb.connect(atlas_db_path, read_only=True)
    try:
        query = """
            SELECT year, month, customs_district, country, imports_metric_tons
            FROM usgs_monthly_imports
            WHERE UPPER(country) LIKE UPPER(?)
        """
        params = [f"%{country}%"]

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY year DESC, month DESC"

        return con.execute(query, params).fetchdf()
    finally:
        con.close()
