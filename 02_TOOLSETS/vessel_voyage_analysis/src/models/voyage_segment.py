"""Voyage segment data model for inbound/outbound analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VoyageSegment:
    """
    Represents inbound and outbound segments of a voyage.

    A voyage is split at the discharge terminal (first terminal arrival):
    - Inbound: Cross In → First Terminal Arrival
    - Outbound: First Terminal Departure → Cross Out
    """

    # Identifiers
    voyage_id: str              # Reference to parent Voyage
    imo: str
    vessel_name: str
    segment_id: str             # {voyage_id}_SEGMENT

    # Inbound Segment (Cross In → First Terminal Arrival)
    cross_in_time: datetime
    cross_in_draft: Optional[float] = None  # Draft in feet
    first_terminal_arrival_time: Optional[datetime] = None
    first_terminal_arrival_draft: Optional[float] = None  # Draft in feet
    discharge_terminal_zone: Optional[str] = None
    discharge_terminal_facility: Optional[str] = None
    inbound_duration_hours: Optional[float] = None
    inbound_transit_hours: float = 0.0
    inbound_anchor_hours: float = 0.0

    # Outbound Segment (First Terminal Departure → Cross Out)
    first_terminal_departure_time: Optional[datetime] = None
    first_terminal_departure_draft: Optional[float] = None  # Draft in feet
    cross_out_time: Optional[datetime] = None
    cross_out_draft: Optional[float] = None  # Draft in feet
    outbound_duration_hours: Optional[float] = None
    outbound_transit_hours: float = 0.0
    outbound_anchor_hours: float = 0.0

    # Port Operations Metrics
    port_duration_hours: Optional[float] = None  # Time at discharge terminal
    total_port_time_hours: Optional[float] = None  # Cross In to Cross Out

    # Draft Analysis (Cargo Indicators)
    draft_delta_ft: Optional[float] = None  # Outbound - Inbound (positive = loaded outbound)
    estimated_cargo_tonnes: Optional[float] = None  # Using TPC if available
    cargo_status: Optional[str] = None  # "Laden Inbound", "Laden Outbound", "Ballast", "Unknown"

    # Efficiency Metrics
    inbound_efficiency: Optional[float] = None  # Hours per mile (if mile data available)
    outbound_efficiency: Optional[float] = None  # Hours per mile (if mile data available)
    port_idle_time_hours: Optional[float] = None  # Time at port not actively working
    vessel_utilization_pct: Optional[float] = None  # Terminal time / Total port time * 100

    # Quality and Completeness
    has_discharge_terminal: bool = False  # True if voyage has at least one terminal stop
    is_complete: bool = False  # True if all required segments have valid times
    quality_notes: Optional[str] = None  # Human-readable quality issues

    def calculate_total_time(self) -> Optional[float]:
        """
        Calculate total port time from inbound + port + outbound.
        Returns None if any segment is missing.
        """
        if (self.inbound_duration_hours is not None and
            self.port_duration_hours is not None and
            self.outbound_duration_hours is not None):
            return (self.inbound_duration_hours +
                    self.port_duration_hours +
                    self.outbound_duration_hours)
        return None

    def get_cargo_status_description(self) -> str:
        """Get human-readable cargo status."""
        if self.cargo_status:
            return self.cargo_status
        if self.draft_delta_ft is None:
            return "Unknown (no draft data)"
        return "Unknown"

    def get_utilization_grade(self) -> str:
        """
        Get utilization grade based on percentage.
        A: >80%, B: 60-80%, C: 40-60%, D: 20-40%, F: <20%
        """
        if self.vessel_utilization_pct is None:
            return "N/A"
        pct = self.vessel_utilization_pct
        if pct >= 80:
            return "A"
        elif pct >= 60:
            return "B"
        elif pct >= 40:
            return "C"
        elif pct >= 20:
            return "D"
        else:
            return "F"

    def validate_segment_times(self) -> bool:
        """
        Validate that segment times are consistent.
        Returns True if times are valid and sum correctly.
        """
        if not self.is_complete:
            return False

        # Check that calculated total matches expected total (within 1% tolerance)
        calculated = self.calculate_total_time()
        if calculated is None or self.total_port_time_hours is None:
            return False

        difference = abs(calculated - self.total_port_time_hours)
        tolerance = self.total_port_time_hours * 0.01  # 1% tolerance
        return difference <= tolerance

    def __str__(self) -> str:
        """Human-readable segment representation."""
        status = "Complete" if self.is_complete else "Incomplete"
        terminal = self.discharge_terminal_facility or "No Terminal"
        return f"Segment {self.segment_id}: {self.vessel_name} via {terminal} ({status})"
