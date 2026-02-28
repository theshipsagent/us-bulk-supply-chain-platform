"""
Excel file loader for USACE vessel data.
Reads the 9 Excel files and standardizes column names.
"""
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ExcelLoader:
    """Loads USACE Excel files into pandas DataFrames."""

    def __init__(self, raw_data_dir):
        """
        Initialize loader.

        Args:
            raw_data_dir: Path to directory containing raw Excel files
        """
        self.raw_data_dir = Path(raw_data_dir)

    def _standardize_columns(self, df):
        """
        Standardize column names.
        Remove leading/trailing whitespace and convert to lowercase with underscores.

        Args:
            df: DataFrame

        Returns:
            DataFrame with standardized columns
        """
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Drop unnamed columns (empty columns from Excel)
        df = df.loc[:, ~df.columns.str.contains('^unnamed', na=False)]

        # Fix common typos
        df.columns = df.columns.str.replace('equp1', 'equip1')
        df.columns = df.columns.str.replace('equp2', 'equip2')

        return df

    def load_operators(self, filename=None):
        """
        Load operators file (TS OP file).

        Args:
            filename: Optional specific filename. If None, auto-detects from directory.

        Returns:
            DataFrame with operators
        """
        try:
            if filename is None:
                # Auto-detect TS OP file using glob pattern
                files = list(self.raw_data_dir.glob("*TS*OP*.xlsx"))
                if not files:
                    raise FileNotFoundError(f"No TS OP file found in {self.raw_data_dir}")
                file_path = files[0]
                logger.info(f"Auto-detected operators file: {file_path.name}")
            else:
                file_path = self.raw_data_dir / filename

            logger.info(f"Loading operators from: {file_path}")

            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Standardize column names
            df = self._standardize_columns(df)

            logger.info(f"Loaded {len(df)} operators")
            return df

        except Exception as e:
            logger.error(f"Failed to load operators: {e}")
            raise

    def load_vessels_master(self, filename=None):
        """
        Load master vessel file (TS VS file).
        Contains all vessels for the year.

        Args:
            filename: Optional specific filename. If None, auto-detects from directory.

        Returns:
            DataFrame with all vessels
        """
        try:
            if filename is None:
                # Auto-detect TS VS file using glob pattern
                files = list(self.raw_data_dir.glob("*TS*VS*.xlsx"))
                if not files:
                    raise FileNotFoundError(f"No TS VS file found in {self.raw_data_dir}")
                file_path = files[0]
                logger.info(f"Auto-detected vessels file: {file_path.name}")
            else:
                file_path = self.raw_data_dir / filename

            logger.info(f"Loading master vessel file from: {file_path}")

            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Standardize column names
            df = self._standardize_columns(df)

            logger.info(f"Loaded {len(df)} vessels from master file")
            return df

        except Exception as e:
            logger.error(f"Failed to load master vessel file: {e}")
            raise

    def load_all_vessel_files(self):
        """
        Load all 7 individual vessel type files.
        These are subsets of the master file, useful for validation.

        Returns:
            Dict of DataFrames keyed by vessel type
        """
        vessel_files = {
            'self_propelled': "2023 Self Propelled Vessels selfpr23.xlsx",
            'deck_barges': "2023 Deck Barges deck23.xlsx",
            'dry_covered': "2023 Dry Covered Barge drycv23.xlsx",
            'dry_open': "2023 Dry Open Barge dryop23.xlsx",
            'tank_barges': "2023 Tank Barges tankb23.xlsx",
            'tow_boats': "2023 Toe Boats towb23.xlsx",
            'other_barges': "2023 Other Dry Barges otdbrg23.xlsx"
        }

        vessel_data = {}

        for vessel_type, filename in vessel_files.items():
            try:
                file_path = self.raw_data_dir / filename
                logger.info(f"Loading {vessel_type} from: {filename}")

                df = pd.read_excel(file_path, sheet_name=0)
                df = self._standardize_columns(df)

                vessel_data[vessel_type] = df
                logger.info(f"  Loaded {len(df)} {vessel_type} vessels")

            except Exception as e:
                logger.warning(f"Failed to load {vessel_type}: {e}")
                vessel_data[vessel_type] = pd.DataFrame()

        return vessel_data

    def validate_data_integrity(self, operators_df, vessels_df):
        """
        Validate data integrity between operators and vessels.

        Args:
            operators_df: Operators DataFrame
            vessels_df: Vessels DataFrame

        Returns:
            Dict with validation results
        """
        results = {
            'total_operators': len(operators_df),
            'total_vessels': len(vessels_df),
            'unique_operators_in_vessels': vessels_df['ts_oper'].nunique(),
            'orphan_vessels': 0,
            'duplicate_vessels': 0
        }

        # Check for orphan vessels (vessel with ts_oper not in operators table)
        operator_ids = set(operators_df['ts_oper'].values)
        vessel_operators = set(vessels_df['ts_oper'].dropna().values)
        orphans = vessel_operators - operator_ids

        results['orphan_vessels'] = len(orphans)
        if orphans:
            logger.warning(f"Found {len(orphans)} vessels with missing operators")

        # Check for duplicate vessel IDs
        duplicates = vessels_df['vessel'].duplicated().sum()
        results['duplicate_vessels'] = duplicates
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate vessel IDs")

        logger.info(f"Data validation complete: {results}")
        return results
