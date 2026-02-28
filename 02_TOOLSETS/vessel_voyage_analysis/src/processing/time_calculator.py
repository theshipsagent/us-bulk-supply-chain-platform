"""Time interval calculations for voyage metrics."""

from typing import List, Optional, Tuple
import logging
from ..models.voyage import Voyage
from ..models.event import Event
from ..models.quality_issue import QualityIssue, IssueType, Severity

logger = logging.getLogger(__name__)


class TimeCalculator:
    """Calculates time metrics for voyages."""

    def __init__(self):
        self.voyages_processed = 0
        self.calculation_errors = 0

    def calculate_voyage_metrics(self, voyage: Voyage) -> None:
        """
        Calculate all time metrics for a voyage (modifies voyage in place).

        Calculates:
        1. Total Port Time = Cross Out - Cross In (if complete)
        2. Transit Time = Sum of segments between locations
        3. Anchor Time = Sum of paired (Arrive Anchor → Depart Anchor)
        4. Terminal Time = Sum of paired (Arrive Terminal → Depart Terminal)

        Args:
            voyage: Voyage object to calculate metrics for
        """
        try:
            # Calculate total port time (only if complete)
            if voyage.is_complete and voyage.cross_out_event:
                duration = voyage.cross_out_event.timestamp - voyage.cross_in_event.timestamp
                voyage.total_port_time_hours = duration.total_seconds() / 3600.0

            # Calculate anchor time and count
            anchor_time, anchor_count, anchor_issues = self._calculate_stop_time(
                voyage.events, 'ANCHORAGE'
            )
            voyage.total_anchor_time_hours = anchor_time
            voyage.num_anchor_stops = anchor_count
            for issue in anchor_issues:
                voyage.add_quality_issue(issue)

            # Calculate terminal time and count
            terminal_time, terminal_count, terminal_issues = self._calculate_stop_time(
                voyage.events, 'TERMINAL'
            )
            voyage.total_terminal_time_hours = terminal_time
            voyage.num_terminal_stops = terminal_count
            for issue in terminal_issues:
                voyage.add_quality_issue(issue)

            # Calculate transit time
            transit_time = self._calculate_transit_time(voyage)
            voyage.total_transit_time_hours = transit_time

            self.voyages_processed += 1

        except Exception as e:
            logger.error(f"Error calculating metrics for voyage {voyage.voyage_id}: {e}")
            self.calculation_errors += 1

    def _calculate_stop_time(
        self,
        events: List[Event],
        zone_type: str
    ) -> Tuple[float, int, List[QualityIssue]]:
        """
        Calculate total time spent at stops (anchor or terminal).

        Args:
            events: List of events in chronological order
            zone_type: 'ANCHORAGE' or 'TERMINAL'

        Returns:
            Tuple of (total_hours, stop_count, quality_issues)
        """
        total_hours = 0.0
        stop_count = 0
        issues = []

        i = 0
        while i < len(events):
            event = events[i]

            # Look for arrival at this zone type
            if event.zone_type == zone_type and event.is_arrival():
                # Find matching departure
                departure_event = self._find_matching_departure(events, i, zone_type)

                if departure_event:
                    # Calculate duration
                    duration = departure_event.timestamp - event.timestamp
                    hours = duration.total_seconds() / 3600.0

                    if hours < 0:
                        # Negative duration - quality issue
                        issue = QualityIssue(
                            issue_type=IssueType.NEGATIVE_DURATION,
                            severity=Severity.ERROR,
                            voyage_id=events[0].imo,  # Will be updated by voyage
                            imo=event.imo,
                            vessel_name=event.vessel_name,
                            timestamp=event.timestamp,
                            description=f"Negative duration: {hours:.2f} hours at {event.zone}",
                            affected_events=[event, departure_event]
                        )
                        issues.append(issue)
                    else:
                        total_hours += hours
                        stop_count += 1

                else:
                    # Orphaned arrival - no matching departure
                    issue = QualityIssue(
                        issue_type=IssueType.ORPHANED_ARRIVAL,
                        severity=Severity.WARNING,
                        voyage_id=events[0].imo,
                        imo=event.imo,
                        vessel_name=event.vessel_name,
                        timestamp=event.timestamp,
                        description=f"Arrival at {event.zone} without matching departure",
                        affected_events=[event]
                    )
                    issues.append(issue)

            i += 1

        return total_hours, stop_count, issues

    def _find_matching_departure(
        self,
        events: List[Event],
        arrival_idx: int,
        zone_type: str
    ) -> Optional[Event]:
        """
        Find the next departure event matching an arrival.

        Args:
            events: List of all events
            arrival_idx: Index of arrival event
            zone_type: Zone type to match

        Returns:
            Matching departure event or None
        """
        arrival_event = events[arrival_idx]

        # Search forward for matching departure
        for i in range(arrival_idx + 1, len(events)):
            event = events[i]

            # Stop if we hit another arrival at the same zone type
            if event.zone_type == zone_type and event.is_arrival():
                return None

            # Found matching departure
            if event.zone_type == zone_type and event.is_departure():
                return event

            # Stop if we hit voyage end
            if event.is_voyage_end():
                return None

        return None

    def _calculate_transit_time(self, voyage: Voyage) -> float:
        """
        Calculate total transit time (time moving between locations).

        Transit segments:
        - Cross In → First Arrive
        - Depart → Next Arrive (for all stops)
        - Last Depart → Cross Out

        Args:
            voyage: Voyage object

        Returns:
            Total transit time in hours
        """
        total_hours = 0.0
        events = voyage.events

        # Find all arrival and departure events (excluding Cross In/Out)
        stops = []
        for event in events:
            if event.is_arrival() or event.is_departure():
                stops.append(event)

        if not stops:
            # No stops - entire voyage is transit
            if voyage.is_complete:
                duration = voyage.cross_out_event.timestamp - voyage.cross_in_event.timestamp
                return duration.total_seconds() / 3600.0
            return 0.0

        # Segment 1: Cross In → First Arrive
        first_arrive = stops[0] if stops and stops[0].is_arrival() else None
        if first_arrive:
            duration = first_arrive.timestamp - voyage.cross_in_event.timestamp
            total_hours += duration.total_seconds() / 3600.0

        # Segments 2-N: Depart → Next Arrive
        for i in range(len(stops) - 1):
            if stops[i].is_departure() and stops[i + 1].is_arrival():
                duration = stops[i + 1].timestamp - stops[i].timestamp
                total_hours += duration.total_seconds() / 3600.0

        # Final segment: Last Depart → Cross Out
        if voyage.is_complete and stops:
            last_depart = stops[-1] if stops[-1].is_departure() else None
            if last_depart:
                duration = voyage.cross_out_event.timestamp - last_depart.timestamp
                total_hours += duration.total_seconds() / 3600.0

        return total_hours

    def get_stats(self) -> dict:
        """Get calculation statistics."""
        return {
            'voyages_processed': self.voyages_processed,
            'calculation_errors': self.calculation_errors
        }
