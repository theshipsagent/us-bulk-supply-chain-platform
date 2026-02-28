"""Data cleaning and Event object creation."""

import pandas as pd
import re
from typing import List
import logging
from ..models.event import Event
from .zone_classifier import ZoneClassifier
from .zone_lookup import ZoneLookup
from .ship_register_lookup import ShipRegisterLookup

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocesses raw CSV data and creates Event objects."""

    def __init__(self, dict_path: str = "terminal_zone_dictionary.csv",
                 ship_register_path: str = "ships_register_dictionary.csv"):
        """
        Initialize the preprocessor with zone classifier, lookup, and ship register.

        Args:
            dict_path: Path to the terminal zone dictionary CSV file
            ship_register_path: Path to the ships register dictionary CSV file
        """
        self.zone_classifier = ZoneClassifier()
        self.zone_lookup = ZoneLookup(dict_path)
        self.ship_register = ShipRegisterLookup(ship_register_path)
        self.events_created = 0
        self.parse_errors = 0
        self.ships_matched_imo = 0
        self.ships_matched_name = 0
        self.ships_not_matched = 0

    def process_dataframe(self, df: pd.DataFrame) -> List[Event]:
        """
        Process DataFrame and create Event objects.

        Args:
            df: DataFrame with columns: IMO, Name, Action, Time, Zone, Agent, Type, Draft, Mile, parsed_time, source_file

        Returns:
            List of Event objects sorted by IMO and timestamp
        """
        events = []

        for idx, row in df.iterrows():
            try:
                event = self._create_event_from_row(row)
                if event:
                    events.append(event)
                    self.events_created += 1
            except Exception as e:
                logger.error(f"Error creating event at row {idx}: {e}")
                self.parse_errors += 1
                continue

        logger.info(f"Created {self.events_created} Event objects ({self.parse_errors} errors)")

        # Sort events by IMO and timestamp
        events.sort(key=lambda e: (e.imo, e.timestamp))

        return events

    def _create_event_from_row(self, row: pd.Series) -> Event:
        """Create an Event object from a DataFrame row."""
        # Parse draft
        draft = self._parse_draft(row.get('Draft'))

        # Classify zone type
        zone = str(row['Zone']) if pd.notna(row['Zone']) else ''
        action = str(row['Action']) if pd.notna(row['Action']) else ''
        zone_type = self.zone_classifier.classify_event(zone, action)

        # Handle missing values
        agent = str(row['Agent']) if pd.notna(row['Agent']) else None
        vessel_type = str(row['Type']) if pd.notna(row['Type']) else None
        mile = str(row['Mile']) if pd.notna(row['Mile']) else None

        # Lookup zone classifications from terminal dictionary
        zone_classification = self.zone_lookup.get_classification(zone)

        # Lookup ship characteristics from ships register
        imo_str = str(row['IMO']).strip()
        vessel_name_str = str(row['Name']).strip()
        ship_characteristics = self.ship_register.get_ship_characteristics(imo_str, vessel_name_str)

        # Track matching statistics
        if ship_characteristics['match_method'] == 'imo':
            self.ships_matched_imo += 1
        elif ship_characteristics['match_method'] == 'name':
            self.ships_matched_name += 1
        else:
            self.ships_not_matched += 1

        event = Event(
            imo=imo_str,
            vessel_name=vessel_name_str,
            action=action,
            timestamp=row['parsed_time'],
            zone=zone,
            zone_type=zone_type,
            agent=agent,
            vessel_type=vessel_type,
            draft=draft,
            mile=mile,
            raw_time=str(row['Time']),
            source_file=str(row['source_file']),
            facility=zone_classification.get('facility'),
            vessel_types=zone_classification.get('vessel_types'),
            activity=zone_classification.get('activity'),
            cargoes=zone_classification.get('cargoes'),
            ship_type_register=ship_characteristics.get('ship_type'),
            dwt=ship_characteristics.get('dwt'),
            register_draft_m=ship_characteristics.get('draft_m'),
            tpc=ship_characteristics.get('tpc'),
            ship_match_method=ship_characteristics.get('match_method')
        )

        return event

    @staticmethod
    def _parse_draft(draft_str) -> float | None:
        """
        Parse draft from string format like '38ft' to float.

        Args:
            draft_str: Draft string (e.g., '38ft', '42.5ft')

        Returns:
            Float value or None if parsing fails
        """
        if pd.isna(draft_str):
            return None

        draft_str = str(draft_str).strip()
        if not draft_str:
            return None

        # Extract numeric value
        match = re.match(r'([\d.]+)', draft_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def get_stats(self) -> dict:
        """Get preprocessing statistics."""
        total_processed = self.events_created + self.parse_errors
        match_rate = (self.ships_matched_imo + self.ships_matched_name) / total_processed * 100 if total_processed > 0 else 0

        return {
            'events_created': self.events_created,
            'parse_errors': self.parse_errors,
            'ships_matched_imo': self.ships_matched_imo,
            'ships_matched_name': self.ships_matched_name,
            'ships_not_matched': self.ships_not_matched,
            'ship_match_rate_percent': f"{match_rate:.2f}",
            'register_stats': self.ship_register.get_lookup_stats()
        }
