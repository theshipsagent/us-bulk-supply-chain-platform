"""
Vessel Data Processor
Parses and standardizes vessel data from various sources
"""
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

import pandas as pd
import openpyxl
import pdfplumber
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class VesselProcessor:
    """Process and standardize vessel data from multiple sources"""

    def __init__(self, config: dict):
        """
        Initialize vessel processor

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.required_fields = config['processing']['required_fields']
        self.date_formats = config['processing']['date_formats']
        self.imo_validation = config['processing']['imo_validation']

        # Standardized column names
        self.column_mapping = {
            # Vessel identification
            'vessel_name': ['vessel name', 'ship name', 'name', 'vessel', 'ship'],
            'imo_number': ['imo', 'imo number', 'imo no', 'imo_no'],
            'mmsi': ['mmsi', 'mmsi number'],
            'call_sign': ['call sign', 'callsign', 'call_sign'],

            # Vessel classification
            'vessel_type': ['vessel type', 'ship type', 'type', 'vessel_class'],
            'flag': ['flag', 'flag state', 'registry', 'country'],
            'classification': ['classification', 'class', 'vessel_classification'],

            # Physical characteristics
            'length': ['length', 'loa', 'length overall', 'length_overall'],
            'beam': ['beam', 'width', 'breadth'],
            'draft': ['draft', 'draught', 'depth'],
            'gross_tonnage': ['gt', 'gross tonnage', 'gross_tonnage', 'grt'],
            'deadweight': ['dwt', 'deadweight', 'dead weight tonnage', 'deadweight_tonnage'],
            'displacement': ['displacement', 'displ'],

            # Build information
            'build_year': ['year built', 'build year', 'built', 'year_built'],
            'builder': ['builder', 'shipyard', 'built_by'],
            'build_location': ['build location', 'built at', 'build_yard'],

            # Operational status
            'status': ['status', 'vessel status', 'operational status'],
            'operator': ['operator', 'operated by', 'managed by', 'manager'],
            'owner': ['owner', 'owned by'],
            'home_port': ['home port', 'homeport', 'port of registry', 'home_port'],

            # Location
            'current_location': ['location', 'current location', 'current_port'],
            'latitude': ['latitude', 'lat'],
            'longitude': ['longitude', 'lon', 'long'],

            # MSC-specific
            'msc_category': ['msc category', 'service category', 'mission'],
            'msc_status': ['msc status', 'readiness', 'service status'],
            'contract_operator': ['contract operator', 'civilian operator', 'contractor']
        }

        logger.info("Initialized vessel processor")

    def process_directory(self, input_dir: Path, output_path: Path) -> pd.DataFrame:
        """
        Process all files in a directory

        Args:
            input_dir: Directory containing raw data files
            output_path: Path to save processed data

        Returns:
            Combined DataFrame
        """
        logger.info(f"Processing files in: {input_dir}")

        all_data = []

        for file_path in input_dir.rglob('*'):
            if file_path.is_file():
                try:
                    df = self.process_file(file_path)
                    if df is not None and not df.empty:
                        df['source_file'] = file_path.name
                        all_data.append(df)
                        logger.info(f"Processed {file_path.name}: {len(df)} records")
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        if not all_data:
            logger.warning("No data processed")
            return pd.DataFrame()

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined data: {len(combined_df)} total records")

        # Standardize and clean
        combined_df = self.standardize_data(combined_df)

        # Deduplicate if configured
        if self.config['processing']['deduplicate']:
            combined_df = self.deduplicate(combined_df)

        # Save processed data
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to: {output_path}")

        return combined_df

    def process_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Process a single file based on its extension

        Args:
            file_path: Path to file

        Returns:
            DataFrame or None
        """
        ext = file_path.suffix.lower()

        try:
            if ext in ['.xlsx', '.xls']:
                return self._process_excel(file_path)
            elif ext == '.csv':
                return self._process_csv(file_path)
            elif ext == '.pdf':
                return self._process_pdf(file_path)
            elif ext == '.html':
                return self._process_html(file_path)
            else:
                logger.debug(f"Unsupported file type: {ext}")
                return None

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None

    def _process_excel(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process Excel file"""
        try:
            # Try reading all sheets
            excel_file = pd.ExcelFile(file_path)
            dfs = []

            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if not df.empty and self._looks_like_vessel_data(df):
                        df['sheet_name'] = sheet_name
                        dfs.append(df)
                        logger.debug(f"Loaded sheet: {sheet_name}")
                except Exception as e:
                    logger.debug(f"Could not read sheet {sheet_name}: {e}")

            if dfs:
                return pd.concat(dfs, ignore_index=True)
            return None

        except Exception as e:
            logger.error(f"Failed to read Excel file {file_path}: {e}")
            return None

    def _process_csv(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process CSV file"""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    if self._looks_like_vessel_data(df):
                        return df
                except UnicodeDecodeError:
                    continue

            logger.warning(f"Could not decode CSV: {file_path}")
            return None

        except Exception as e:
            logger.error(f"Failed to read CSV {file_path}: {e}")
            return None

    def _process_pdf(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process PDF file"""
        try:
            with pdfplumber.open(file_path) as pdf:
                all_tables = []

                for page in pdf.pages:
                    tables = page.extract_tables()
                    all_tables.extend(tables)

                if not all_tables:
                    logger.debug(f"No tables found in PDF: {file_path}")
                    return None

                # Convert tables to DataFrames
                dfs = []
                for i, table in enumerate(all_tables):
                    if len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        if self._looks_like_vessel_data(df):
                            dfs.append(df)

                if dfs:
                    return pd.concat(dfs, ignore_index=True)

            return None

        except Exception as e:
            logger.error(f"Failed to read PDF {file_path}: {e}")
            return None

    def _process_html(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find tables
            tables = soup.find_all('table')

            dfs = []
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    if self._looks_like_vessel_data(df):
                        dfs.append(df)
                except Exception as e:
                    logger.debug(f"Could not parse table: {e}")

            if dfs:
                return pd.concat(dfs, ignore_index=True)

            return None

        except Exception as e:
            logger.error(f"Failed to read HTML {file_path}: {e}")
            return None

    def _looks_like_vessel_data(self, df: pd.DataFrame) -> bool:
        """
        Check if DataFrame looks like vessel data

        Args:
            df: DataFrame to check

        Returns:
            True if it looks like vessel data
        """
        if df.empty or len(df.columns) < 3:
            return False

        # Convert columns to lowercase for matching
        columns_lower = [str(col).lower() for col in df.columns]

        # Look for vessel-related keywords
        vessel_keywords = [
            'vessel', 'ship', 'name', 'imo', 'flag',
            'type', 'tonnage', 'operator', 'built'
        ]

        matches = sum(
            any(keyword in col for keyword in vessel_keywords)
            for col in columns_lower
        )

        return matches >= 2

    def standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names and data formats

        Args:
            df: Input DataFrame

        Returns:
            Standardized DataFrame
        """
        logger.info("Standardizing vessel data")

        # Standardize column names
        df = self._standardize_columns(df)

        # Clean and format data
        if 'vessel_name' in df.columns:
            try:
                df.loc[:, 'vessel_name'] = df['vessel_name'].astype(str).str.strip().str.upper()
            except Exception as e:
                logger.warning(f"Could not standardize vessel_name: {e}")

        if 'flag' in df.columns:
            try:
                df.loc[:, 'flag'] = df['flag'].astype(str).str.strip().str.upper()
                # Focus on US flag vessels
                df.loc[:, 'is_us_flag'] = df['flag'].str.contains('US|USA|UNITED STATES', na=False, regex=True)
            except Exception as e:
                logger.warning(f"Could not standardize flag: {e}")

        if 'imo_number' in df.columns and self.imo_validation:
            df['imo_valid'] = df['imo_number'].apply(self._validate_imo)

        # Standardize dates
        if 'build_year' in df.columns:
            df['build_year'] = pd.to_numeric(df['build_year'], errors='coerce')

        # Standardize numeric fields
        numeric_fields = ['length', 'beam', 'draft', 'gross_tonnage', 'deadweight']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')

        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names using mapping

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with standardized columns
        """
        columns_lower = {col: str(col).lower() for col in df.columns}
        new_columns = {}

        for col in df.columns:
            col_lower = columns_lower[col]

            # Find matching standard name
            for standard_name, variations in self.column_mapping.items():
                if any(var in col_lower for var in variations):
                    new_columns[col] = standard_name
                    break

            # Keep original if no match
            if col not in new_columns:
                new_columns[col] = col

        df = df.rename(columns=new_columns)

        # Remove duplicate columns if they exist
        df = df.loc[:, ~df.columns.duplicated()]

        return df

    def _validate_imo(self, imo: Union[str, int, float]) -> bool:
        """
        Validate IMO number using check digit algorithm

        Args:
            imo: IMO number

        Returns:
            True if valid
        """
        try:
            imo_str = str(imo).replace('IMO', '').strip()
            if not imo_str.isdigit() or len(imo_str) != 7:
                return False

            # Check digit calculation
            check_sum = sum(int(imo_str[i]) * (7 - i) for i in range(6))
            check_digit = check_sum % 10

            return check_digit == int(imo_str[6])

        except Exception:
            return False

    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate vessel records

        Args:
            df: Input DataFrame

        Returns:
            Deduplicated DataFrame
        """
        logger.info("Deduplicating vessel records")

        initial_count = len(df)

        # Deduplicate by IMO number (most reliable)
        if 'imo_number' in df.columns:
            df = df.drop_duplicates(subset=['imo_number'], keep='first')

        # Deduplicate by vessel name and flag
        if 'vessel_name' in df.columns and 'flag' in df.columns:
            df = df.drop_duplicates(subset=['vessel_name', 'flag'], keep='first')

        final_count = len(df)
        removed = initial_count - final_count

        logger.info(f"Removed {removed} duplicate records")

        return df

    def filter_us_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter for US flag vessels only

        Args:
            df: Input DataFrame

        Returns:
            Filtered DataFrame
        """
        if 'is_us_flag' in df.columns:
            filtered = df[df['is_us_flag'] == True].copy()
        elif 'flag' in df.columns:
            filtered = df[df['flag'].str.contains('US|USA|UNITED STATES', na=False)].copy()
        else:
            logger.warning("Cannot filter by US flag - no flag column")
            return df

        logger.info(f"Filtered to {len(filtered)} US flag vessels")
        return filtered

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics

        Args:
            df: Input DataFrame

        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_vessels': len(df),
            'unique_operators': df['operator'].nunique() if 'operator' in df.columns else 0,
            'unique_types': df['vessel_type'].nunique() if 'vessel_type' in df.columns else 0,
        }

        if 'vessel_type' in df.columns:
            stats['vessels_by_type'] = df['vessel_type'].value_counts().to_dict()

        if 'status' in df.columns:
            stats['vessels_by_status'] = df['status'].value_counts().to_dict()

        if 'operator' in df.columns:
            stats['vessels_by_operator'] = df['operator'].value_counts().head(10).to_dict()

        return stats
