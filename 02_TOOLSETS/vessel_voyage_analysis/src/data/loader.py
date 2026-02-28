"""CSV data loading and consolidation."""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and consolidates maritime event data from CSV files."""

    EXPECTED_COLUMNS = ['IMO', 'Name', 'Action', 'Time', 'Zone', 'Agent', 'Type', 'Draft', 'Mile']

    # Vessels to exclude (dredges and service vessels without IMO)
    EXCLUDE_VESSELS = [
        'Allisonk',
        'Allins K',
        'Keeneland',
        'Chesapeake Bay',
        'Jadwin Discharge',
        'Dixie Raider'
    ]

    def __init__(self):
        self.files_loaded = 0
        self.total_rows = 0
        self.duplicates_removed = 0
        self.excluded_vessels = 0

    def load_data(
        self,
        input_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        vessel_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load CSV data from file or directory.

        Args:
            input_path: Path to CSV file or directory containing CSV files
            start_date: Optional start date filter
            end_date: Optional end date filter
            vessel_filter: Optional vessel name/IMO filter (partial match)

        Returns:
            Consolidated DataFrame sorted by IMO and timestamp
        """
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {input_path}")

        # Collect CSV files
        if path.is_file():
            csv_files = [path]
        else:
            csv_files = sorted(path.glob('*.csv'))

        if not csv_files:
            raise ValueError(f"No CSV files found in: {input_path}")

        logger.info(f"Found {len(csv_files)} CSV file(s) to process")

        # Load all CSV files
        dataframes = []
        for csv_file in csv_files:
            try:
                df = self._load_single_csv(csv_file)
                if df is not None and not df.empty:
                    dataframes.append(df)
                    self.files_loaded += 1
            except Exception as e:
                logger.error(f"Error loading {csv_file.name}: {e}")
                continue

        if not dataframes:
            raise ValueError("No valid data loaded from CSV files")

        # Concatenate all dataframes
        df_combined = pd.concat(dataframes, ignore_index=True)
        self.total_rows = len(df_combined)
        logger.info(f"Loaded {self.total_rows} total rows from {self.files_loaded} files")

        # Parse timestamps
        df_combined['parsed_time'] = pd.to_datetime(
            df_combined['Time'],
            format='%m/%d/%Y %H:%M',
            errors='coerce'
        )

        # Remove rows with invalid timestamps
        invalid_times = df_combined['parsed_time'].isna().sum()
        if invalid_times > 0:
            logger.warning(f"Removing {invalid_times} rows with invalid timestamps")
            df_combined = df_combined.dropna(subset=['parsed_time'])

        # Apply date range filter
        if start_date:
            df_combined = df_combined[df_combined['parsed_time'] >= start_date]
            logger.info(f"Applied start date filter: {start_date.date()}")

        if end_date:
            df_combined = df_combined[df_combined['parsed_time'] <= end_date]
            logger.info(f"Applied end date filter: {end_date.date()}")

        # Apply vessel filter
        if vessel_filter:
            vessel_filter_upper = vessel_filter.upper()
            mask = (
                df_combined['Name'].str.upper().str.contains(vessel_filter_upper, na=False) |
                df_combined['IMO'].str.upper().str.contains(vessel_filter_upper, na=False)
            )
            df_combined = df_combined[mask]
            logger.info(f"Applied vessel filter '{vessel_filter}': {len(df_combined)} rows remaining")

        # Exclude dredges and service vessels (vessels without IMO in exclusion list)
        initial_count = len(df_combined)
        exclude_mask = (
            (df_combined['IMO'].isna() | (df_combined['IMO'] == '')) &
            df_combined['Name'].isin(self.EXCLUDE_VESSELS)
        )
        df_combined = df_combined[~exclude_mask]
        self.excluded_vessels = initial_count - len(df_combined)

        if self.excluded_vessels > 0:
            logger.info(f"Excluded {self.excluded_vessels} dredge/service vessel events")

        # Sort by IMO and timestamp
        df_combined = df_combined.sort_values(['IMO', 'parsed_time'])

        # Detect and remove duplicates
        df_combined['composite_key'] = (
            df_combined['IMO'].astype(str) + '_' +
            df_combined['parsed_time'].astype(str)
        )
        initial_count = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset='composite_key', keep='first')
        self.duplicates_removed = initial_count - len(df_combined)

        if self.duplicates_removed > 0:
            logger.info(f"Removed {self.duplicates_removed} duplicate events")

        logger.info(f"Final dataset: {len(df_combined)} rows")

        return df_combined

    def _load_single_csv(self, csv_file: Path) -> Optional[pd.DataFrame]:
        """Load a single CSV file with validation."""
        try:
            df = pd.read_csv(csv_file, dtype=str)

            # Validate columns
            missing_cols = set(self.EXPECTED_COLUMNS) - set(df.columns)
            if missing_cols:
                logger.warning(f"{csv_file.name}: Missing columns {missing_cols}")
                return None

            # Add source file column
            df['source_file'] = csv_file.name

            logger.debug(f"Loaded {len(df)} rows from {csv_file.name}")
            return df

        except Exception as e:
            logger.error(f"Error reading {csv_file.name}: {e}")
            return None

    def get_stats(self) -> dict:
        """Get loading statistics."""
        return {
            'files_loaded': self.files_loaded,
            'total_rows': self.total_rows,
            'duplicates_removed': self.duplicates_removed,
            'excluded_vessels': self.excluded_vessels,
            'final_rows': self.total_rows - self.duplicates_removed - self.excluded_vessels
        }
