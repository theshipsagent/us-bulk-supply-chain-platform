"""Zone classification lookup from terminal dictionary."""
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ZoneLookup:
    """Loads and provides zone classification lookups from terminal dictionary."""

    def __init__(self, dict_path: str = "terminal_zone_dictionary.csv"):
        """
        Initialize the ZoneLookup with a terminal zone dictionary.

        Args:
            dict_path: Path to the terminal_zone_dictionary.csv file
        """
        self.zone_dict = {}
        self._load_dictionary(dict_path)

    def _load_dictionary(self, dict_path: str):
        """
        Load terminal zone dictionary from CSV.

        Creates lookup dict: {zone_name: {facility, vessel_types, activity, cargoes}}

        Args:
            dict_path: Path to the terminal_zone_dictionary.csv file
        """
        try:
            # Try to load the CSV file
            dict_file = Path(dict_path)
            if not dict_file.exists():
                # Try looking in common locations
                common_paths = [
                    Path(dict_path),
                    Path(__file__).parent.parent.parent / dict_path,
                    Path.cwd() / dict_path
                ]

                for path in common_paths:
                    if path.exists():
                        dict_file = path
                        break

            if not dict_file.exists():
                logger.warning(f"Zone dictionary not found at {dict_path}. Using empty lookup.")
                return

            # Load CSV
            df = pd.read_csv(dict_file, encoding='utf-8')

            # Validate required columns
            required_cols = ['Zone', 'Facility', 'Vessel Types', 'Activity', 'Cargoes']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                logger.warning(f"Missing columns in zone dictionary: {missing_cols}")
                return

            # Build lookup dictionary
            for _, row in df.iterrows():
                zone_name = str(row['Zone']).strip()

                self.zone_dict[zone_name] = {
                    'facility': str(row['Facility']).strip() if pd.notna(row['Facility']) else zone_name,
                    'vessel_types': str(row['Vessel Types']).strip() if pd.notna(row['Vessel Types']) else None,
                    'activity': str(row['Activity']).strip() if pd.notna(row['Activity']) else None,
                    'cargoes': str(row['Cargoes']).strip() if pd.notna(row['Cargoes']) else None
                }

            logger.info(f"Loaded {len(self.zone_dict)} zone classifications from {dict_file}")

        except Exception as e:
            logger.error(f"Error loading zone dictionary from {dict_path}: {e}")

    def get_classification(self, zone: str) -> dict:
        """
        Get all classifications for a zone.

        Args:
            zone: Zone name to look up

        Returns:
            Dictionary with keys: facility, vessel_types, activity, cargoes
            If zone not found, returns default with zone name as facility
        """
        zone_str = str(zone).strip() if zone else ''

        if zone_str in self.zone_dict:
            return self.zone_dict[zone_str].copy()

        # Default return if not found
        return {
            'facility': zone_str,
            'vessel_types': None,
            'activity': None,
            'cargoes': None
        }

    def has_classification(self, zone: str) -> bool:
        """Check if a zone has a classification in the dictionary."""
        zone_str = str(zone).strip() if zone else ''
        return zone_str in self.zone_dict

    def get_all_zones(self) -> list:
        """Get all zone names in the dictionary."""
        return list(self.zone_dict.keys())

    def get_stats(self) -> dict:
        """Get statistics about the loaded dictionary."""
        return {
            'total_zones': len(self.zone_dict),
            'zones_with_vessel_types': sum(1 for z in self.zone_dict.values() if z['vessel_types']),
            'zones_with_activity': sum(1 for z in self.zone_dict.values() if z['activity']),
            'zones_with_cargoes': sum(1 for z in self.zone_dict.values() if z['cargoes'])
        }
