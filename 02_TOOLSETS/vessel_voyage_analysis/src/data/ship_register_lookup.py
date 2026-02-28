"""Ship characteristics lookup from ships register."""
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ShipRegisterLookup:
    """Loads and provides ship characteristics lookups from the ships register."""

    def __init__(self, register_path: str = "ships_register_dictionary.csv"):
        """
        Initialize the ship register lookup.

        Args:
            register_path: Path to the ships_register_dictionary.csv file
        """
        self.ship_dict_imo = {}  # {imo_clean: {ship_type, dwt, draft_m, tpc, vessel_name}}
        self.ship_dict_name = {}  # {vessel_name_upper: [(imo, characteristics)]} for secondary matching
        self.register_size = 0
        self._load_register(register_path)

    def _load_register(self, register_path: str) -> None:
        """
        Load ships register dictionary with cleaned IMOs.

        Args:
            register_path: Path to the CSV file
        """
        try:
            register_file = Path(register_path)

            if not register_file.exists():
                logger.warning(f"Ships register file not found at {register_path}")
                return

            # Load CSV
            df = pd.read_csv(register_file, dtype={
                'IMO_Clean': str,
                'IMO_Original': str,
                'VesselName': str,
                'ShipType': str,
                'DWT': 'float64',
                'Draft_m': 'float64',
                'TPC': 'float64',
                'MatchQuality': str
            })

            logger.info(f"Loaded {len(df)} records from ships register")

            # Build IMO lookup dict (primary key)
            for idx, row in df.iterrows():
                imo_clean = str(row['IMO_Clean']).strip()

                characteristics = {
                    'ship_type': str(row['ShipType']).strip() if pd.notna(row['ShipType']) else None,
                    'dwt': float(row['DWT']) if pd.notna(row['DWT']) and float(row['DWT']) > 0 else None,
                    'draft_m': float(row['Draft_m']) if pd.notna(row['Draft_m']) and float(row['Draft_m']) > 0 else None,
                    'tpc': float(row['TPC']) if pd.notna(row['TPC']) and float(row['TPC']) > 0 else None,
                    'vessel_name': str(row['VesselName']).strip() if pd.notna(row['VesselName']) else None,
                    'match_quality': str(row['MatchQuality']).strip() if pd.notna(row['MatchQuality']) else 'Unknown'
                }

                # Only add if we have at least one characteristic
                if any([characteristics['ship_type'], characteristics['dwt'],
                        characteristics['draft_m'], characteristics['tpc']]):
                    self.ship_dict_imo[imo_clean] = characteristics

                    # Build name lookup for secondary matching
                    vessel_name_upper = characteristics['vessel_name'].upper() if characteristics['vessel_name'] else None
                    if vessel_name_upper:
                        if vessel_name_upper not in self.ship_dict_name:
                            self.ship_dict_name[vessel_name_upper] = []
                        self.ship_dict_name[vessel_name_upper].append((imo_clean, characteristics))

            self.register_size = len(self.ship_dict_imo)
            logger.info(f"Built IMO lookup index with {self.register_size} unique IMOs")
            logger.info(f"Built name lookup index with {len(self.ship_dict_name)} unique vessel names")

        except Exception as e:
            logger.error(f"Error loading ships register from {register_path}: {e}")
            raise

    def get_ship_characteristics(self, imo: str, vessel_name: str) -> Dict:
        """
        Get ship characteristics by IMO (primary) or name (secondary).

        Tries IMO first (recommended as more reliable), then falls back to vessel name.

        Args:
            imo: IMO number (will be cleaned to 7 digits)
            vessel_name: Vessel name (for secondary matching)

        Returns:
            Dictionary with:
            - ship_type: Vessel type from register (str or None)
            - dwt: Deadweight tonnage (float or None)
            - draft_m: Draft in meters from register (float or None)
            - tpc: Tonnes per centimeter (float or None)
            - match_method: 'imo', 'name', or None
            - vessel_name_matched: Name from register (for verification)
        """
        result = {
            'ship_type': None,
            'dwt': None,
            'draft_m': None,
            'tpc': None,
            'match_method': None,
            'vessel_name_matched': None
        }

        # Try IMO match first (clean the IMO)
        imo_clean = self._clean_imo_for_lookup(imo)
        if imo_clean and imo_clean in self.ship_dict_imo:
            char = self.ship_dict_imo[imo_clean]
            result['ship_type'] = char.get('ship_type')
            result['dwt'] = char.get('dwt')
            result['draft_m'] = char.get('draft_m')
            result['tpc'] = char.get('tpc')
            result['match_method'] = 'imo'
            result['vessel_name_matched'] = char.get('vessel_name')
            return result

        # If no IMO match, try vessel name match
        if vessel_name:
            vessel_name_upper = str(vessel_name).strip().upper()
            if vessel_name_upper in self.ship_dict_name:
                # Get the first match by IMO (best quality)
                imo_matched, char = self.ship_dict_name[vessel_name_upper][0]
                result['ship_type'] = char.get('ship_type')
                result['dwt'] = char.get('dwt')
                result['draft_m'] = char.get('draft_m')
                result['tpc'] = char.get('tpc')
                result['match_method'] = 'name'
                result['vessel_name_matched'] = char.get('vessel_name')
                return result

        # No match found
        return result

    @staticmethod
    def _clean_imo_for_lookup(imo_value) -> Optional[str]:
        """
        Clean IMO for lookup (standardize to 7-digit format).

        Args:
            imo_value: IMO value (any type)

        Returns:
            Cleaned 7-digit IMO string or None if invalid
        """
        if not imo_value or pd.isna(imo_value):
            return None

        imo_str = str(imo_value).strip()

        # Remove leading zeros, then pad to 7 digits
        try:
            imo_int = int(imo_str)
            if imo_int <= 0:
                return None
            return str(imo_int).zfill(7)
        except (ValueError, TypeError):
            return None

    def get_lookup_stats(self) -> Dict:
        """Get statistics about the loaded register."""
        return {
            'total_unique_imos': self.register_size,
            'total_unique_names': len(self.ship_dict_name),
            'lookup_initialized': self.register_size > 0
        }
