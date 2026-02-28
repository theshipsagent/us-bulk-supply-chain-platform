"""Voyage segmentation into inbound and outbound segments."""

from typing import List, Optional, Tuple
from datetime import datetime
import logging
from ..models.voyage import Voyage
from ..models.voyage_segment import VoyageSegment
from ..models.event import Event

logger = logging.getLogger(__name__)


class VoyageSegmenter:
    """
    Segments voyages into inbound and outbound portions.

    Segmentation Point: First Terminal Arrival (discharge terminal)
    - Inbound: Cross In → First Terminal Arrival
    - Outbound: First Terminal Departure → Cross Out
    """

    def __init__(self, draft_threshold: float = 1.5):
        """
        Initialize the voyage segmenter.

        Args:
            draft_threshold: Threshold in feet for cargo status determination (default: 1.5 ft)
        """
        self.draft_threshold = draft_threshold
        self.segments_created = 0
        self.segments_without_terminal = 0
        self.incomplete_segments = 0

    def segment_voyages(self, voyages: List[Voyage]) -> List[VoyageSegment]:
        """
        Segment a list of voyages into inbound/outbound segments.

        Args:
            voyages: List of Voyage objects from Phase 1

        Returns:
            List of VoyageSegment objects
        """
        segments = []

        logger.info(f"Segmenting {len(voyages)} voyages")

        for voyage in voyages:
            segment = self._segment_voyage(voyage)
            if segment:
                segments.append(segment)
                self.segments_created += 1

        logger.info(
            f"Created {self.segments_created} segments "
            f"({self.segments_without_terminal} without terminals, "
            f"{self.incomplete_segments} incomplete)"
        )

        return segments

    def _segment_voyage(self, voyage: Voyage) -> Optional[VoyageSegment]:
        """
        Segment a single voyage.

        Args:
            voyage: Voyage object to segment

        Returns:
            VoyageSegment object or None if voyage cannot be segmented
        """
        # Find first terminal arrival
        first_terminal_event, terminal_depart_event = self._find_terminal_events(voyage)

        # Create segment ID
        segment_id = f"{voyage.voyage_id}_SEGMENT"

        # Extract basic voyage information
        cross_in_event = voyage.cross_in_event
        cross_out_event = voyage.cross_out_event

        # Initialize segment
        segment = VoyageSegment(
            voyage_id=voyage.voyage_id,
            imo=voyage.imo,
            vessel_name=voyage.vessel_name,
            segment_id=segment_id,
            cross_in_time=cross_in_event.timestamp,
            cross_in_draft=cross_in_event.draft,
            cross_out_time=cross_out_event.timestamp if cross_out_event else None,
            cross_out_draft=cross_out_event.draft if cross_out_event else None,
            total_port_time_hours=voyage.total_port_time_hours
        )

        # Case 1: No terminal stops found
        if first_terminal_event is None:
            self._handle_no_terminal(segment, voyage)
            self.segments_without_terminal += 1
            return segment

        # Case 2: Terminal found - perform segmentation
        segment.has_discharge_terminal = True
        segment.discharge_terminal_zone = first_terminal_event.zone
        segment.discharge_terminal_facility = first_terminal_event.facility

        # Calculate inbound segment
        self._calculate_inbound_segment(segment, voyage, first_terminal_event)

        # Calculate outbound segment (if terminal departure exists)
        if terminal_depart_event and cross_out_event:
            self._calculate_outbound_segment(segment, voyage, terminal_depart_event)

        # Calculate port duration (time at discharge terminal)
        if first_terminal_event and terminal_depart_event:
            segment.port_duration_hours = self._calculate_hours(
                first_terminal_event.timestamp,
                terminal_depart_event.timestamp
            )

        # Calculate draft analysis
        self._calculate_draft_analysis(segment)

        # Determine completeness
        segment.is_complete = self._is_segment_complete(segment)
        if not segment.is_complete:
            self.incomplete_segments += 1

        # Add quality notes if needed
        segment.quality_notes = self._generate_quality_notes(segment)

        return segment

    def _find_terminal_events(self, voyage: Voyage) -> Tuple[Optional[Event], Optional[Event]]:
        """
        Find first terminal arrival and corresponding departure events.

        Args:
            voyage: Voyage to search

        Returns:
            Tuple of (first_terminal_arrival, first_terminal_departure) or (None, None)
        """
        # Find all terminal arrivals
        terminal_arrivals = [e for e in voyage.events if e.is_terminal_arrive()]

        if not terminal_arrivals:
            return None, None

        # First terminal arrival is the discharge terminal
        first_arrival = terminal_arrivals[0]

        # Find corresponding departure from same terminal
        # Look for next departure event after this arrival
        arrival_index = voyage.events.index(first_arrival)
        for event in voyage.events[arrival_index + 1:]:
            if event.is_terminal_depart() and event.zone == first_arrival.zone:
                return first_arrival, event

        # No matching departure found
        return first_arrival, None

    def _calculate_inbound_segment(
        self,
        segment: VoyageSegment,
        voyage: Voyage,
        terminal_arrival: Event
    ) -> None:
        """Calculate inbound segment metrics (Cross In → Terminal Arrival)."""
        segment.first_terminal_arrival_time = terminal_arrival.timestamp
        segment.first_terminal_arrival_draft = terminal_arrival.draft

        # Calculate inbound duration
        segment.inbound_duration_hours = self._calculate_hours(
            voyage.cross_in_event.timestamp,
            terminal_arrival.timestamp
        )

        # Calculate inbound transit and anchor times
        inbound_events = self._get_events_before(voyage.events, terminal_arrival)
        segment.inbound_transit_hours, segment.inbound_anchor_hours = \
            self._calculate_transit_and_anchor_times(inbound_events)

    def _calculate_outbound_segment(
        self,
        segment: VoyageSegment,
        voyage: Voyage,
        terminal_departure: Event
    ) -> None:
        """Calculate outbound segment metrics (Terminal Departure → Cross Out)."""
        segment.first_terminal_departure_time = terminal_departure.timestamp
        segment.first_terminal_departure_draft = terminal_departure.draft

        if voyage.cross_out_event:
            # Calculate outbound duration
            segment.outbound_duration_hours = self._calculate_hours(
                terminal_departure.timestamp,
                voyage.cross_out_event.timestamp
            )

            # Calculate outbound transit and anchor times
            outbound_events = self._get_events_after(voyage.events, terminal_departure)
            segment.outbound_transit_hours, segment.outbound_anchor_hours = \
                self._calculate_transit_and_anchor_times(outbound_events)

    def _calculate_draft_analysis(self, segment: VoyageSegment) -> None:
        """
        Calculate draft delta and determine cargo status.

        Cargo Status Logic:
        - draft_delta > threshold: Laden Outbound (picked up cargo)
        - draft_delta < -threshold: Laden Inbound (delivered cargo)
        - |draft_delta| <= threshold: Ballast or Unknown
        """
        inbound_draft = segment.first_terminal_arrival_draft
        outbound_draft = segment.first_terminal_departure_draft

        if inbound_draft is None or outbound_draft is None:
            segment.cargo_status = "Unknown (no draft data)"
            return

        # Calculate draft delta (positive = deeper outbound = loaded cargo outbound)
        segment.draft_delta_ft = outbound_draft - inbound_draft

        # Determine cargo status
        if segment.draft_delta_ft > self.draft_threshold:
            segment.cargo_status = "Laden Outbound"
        elif segment.draft_delta_ft < -self.draft_threshold:
            segment.cargo_status = "Laden Inbound"
        elif abs(segment.draft_delta_ft) <= self.draft_threshold:
            segment.cargo_status = "Ballast"
        else:
            segment.cargo_status = "Unknown"

        # TODO: Estimate cargo tonnage using TPC (if available from ship register)
        # This requires access to ship register data during segmentation
        # For now, leave as None - can be calculated in EfficiencyCalculator

    def _handle_no_terminal(self, segment: VoyageSegment, voyage: Voyage) -> None:
        """
        Handle voyages with no terminal stops.
        Treat entire voyage as inbound segment.
        """
        segment.has_discharge_terminal = False
        segment.inbound_duration_hours = voyage.total_port_time_hours
        segment.inbound_transit_hours = voyage.total_transit_time_hours
        segment.inbound_anchor_hours = voyage.total_anchor_time_hours
        segment.is_complete = voyage.is_complete
        segment.quality_notes = "No terminal stops detected - full voyage treated as inbound"

    def _get_events_before(self, events: List[Event], target: Event) -> List[Event]:
        """Get all events before target event (not including target)."""
        target_index = events.index(target)
        return events[:target_index]

    def _get_events_after(self, events: List[Event], target: Event) -> List[Event]:
        """Get all events after target event (not including target)."""
        target_index = events.index(target)
        return events[target_index + 1:]

    def _calculate_transit_and_anchor_times(
        self,
        events: List[Event]
    ) -> Tuple[float, float]:
        """
        Calculate total transit and anchor times from a list of events.

        Returns:
            Tuple of (transit_hours, anchor_hours)
        """
        transit_hours = 0.0
        anchor_hours = 0.0

        i = 0
        while i < len(events):
            event = events[i]

            # Anchor time: Arrive Anchor → Depart Anchor
            if event.is_anchor_arrive() and i + 1 < len(events):
                next_event = events[i + 1]
                if next_event.is_anchor_depart():
                    anchor_hours += self._calculate_hours(
                        event.timestamp,
                        next_event.timestamp
                    )
                    i += 2  # Skip both events
                    continue

            # Transit time: anything that's not at anchor
            if i + 1 < len(events):
                if not event.is_anchor_arrive():  # Not counting anchor time
                    next_event = events[i + 1]
                    transit_hours += self._calculate_hours(
                        event.timestamp,
                        next_event.timestamp
                    )

            i += 1

        return transit_hours, anchor_hours

    def _calculate_hours(self, start: datetime, end: datetime) -> float:
        """Calculate hours between two timestamps."""
        delta = end - start
        return delta.total_seconds() / 3600.0

    def _is_segment_complete(self, segment: VoyageSegment) -> bool:
        """
        Determine if a segment is complete.

        Complete if:
        - Has Cross In and Cross Out
        - Has valid inbound duration
        - If has terminal, has valid port duration
        """
        if segment.cross_out_time is None:
            return False

        if segment.inbound_duration_hours is None:
            return False

        if segment.has_discharge_terminal and segment.port_duration_hours is None:
            return False

        return True

    def _generate_quality_notes(self, segment: VoyageSegment) -> Optional[str]:
        """Generate quality notes for segment."""
        notes = []

        if not segment.is_complete:
            if segment.cross_out_time is None:
                notes.append("Missing Cross Out event")
            if segment.first_terminal_departure_time is None and segment.has_discharge_terminal:
                notes.append("Missing terminal departure")

        if segment.first_terminal_arrival_draft is None:
            notes.append("No draft data at terminal arrival")

        if segment.first_terminal_departure_draft is None and segment.has_discharge_terminal:
            notes.append("No draft data at terminal departure")

        return "; ".join(notes) if notes else None

    def get_stats(self) -> dict:
        """Get segmentation statistics."""
        return {
            'segments_created': self.segments_created,
            'segments_without_terminal': self.segments_without_terminal,
            'incomplete_segments': self.incomplete_segments,
            'complete_segments': self.segments_created - self.incomplete_segments,
            'completion_rate': (
                (self.segments_created - self.incomplete_segments) / self.segments_created * 100
                if self.segments_created > 0 else 0
            )
        }
