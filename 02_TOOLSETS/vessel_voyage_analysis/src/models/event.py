"""Event data model with classification methods."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """Represents a single maritime event (Enter, Exit, Arrive, Depart)."""

    imo: str
    vessel_name: str
    action: str                # Enter, Exit, Arrive, Depart
    timestamp: datetime
    zone: str
    zone_type: str            # CROSS_IN, CROSS_OUT, ANCHORAGE, TERMINAL, UNKNOWN
    agent: Optional[str]
    vessel_type: Optional[str]
    draft: Optional[float]    # Parsed from "38ft" → 38.0
    mile: Optional[str]
    raw_time: str
    source_file: str
    facility: Optional[str] = None  # Roll-up facility name
    vessel_types: Optional[str] = None  # Allowed vessel types
    activity: Optional[str] = None  # Activity type (Load, Discharge, Anchoring)
    cargoes: Optional[str] = None  # Cargo types handled
    # Ship register characteristics
    ship_type_register: Optional[str] = None  # From ships register
    dwt: Optional[float] = None  # Deadweight tonnage from register
    register_draft_m: Optional[float] = None  # Draft from ships register in meters
    tpc: Optional[float] = None  # Tonnes per centimeter from register
    ship_match_method: Optional[str] = None  # 'imo', 'name', or None

    def is_voyage_start(self) -> bool:
        """Check if this event starts a voyage (CROSS_IN + Enter)."""
        return self.zone_type == 'CROSS_IN' and self.action == 'Enter'

    def is_voyage_end(self) -> bool:
        """Check if this event ends a voyage (CROSS_OUT + Exit)."""
        return self.zone_type == 'CROSS_OUT' and self.action == 'Exit'

    def is_anchor_arrive(self) -> bool:
        """Check if this is an arrival at anchorage."""
        return self.zone_type == 'ANCHORAGE' and self.action == 'Arrive'

    def is_anchor_depart(self) -> bool:
        """Check if this is a departure from anchorage."""
        return self.zone_type == 'ANCHORAGE' and self.action == 'Depart'

    def is_terminal_arrive(self) -> bool:
        """Check if this is an arrival at terminal."""
        return self.zone_type == 'TERMINAL' and self.action == 'Arrive'

    def is_terminal_depart(self) -> bool:
        """Check if this is a departure from terminal."""
        return self.zone_type == 'TERMINAL' and self.action == 'Depart'

    def is_arrival(self) -> bool:
        """Check if this is any arrival event."""
        return self.action == 'Arrive'

    def is_departure(self) -> bool:
        """Check if this is any departure event."""
        return self.action == 'Depart'

    def __str__(self) -> str:
        """Human-readable event representation."""
        return f"{self.imo} {self.vessel_name}: {self.action} {self.zone} at {self.timestamp}"
