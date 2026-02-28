"""Voyage boundary detection and grouping."""

from typing import List, Dict
from collections import defaultdict
import logging
from ..models.event import Event
from ..models.voyage import Voyage
from ..models.quality_issue import QualityIssue, IssueType, Severity

logger = logging.getLogger(__name__)


class VoyageDetector:
    """Detects voyage boundaries and groups events into voyages."""

    def __init__(self):
        self.voyages_created = 0
        self.incomplete_voyages = 0
        self.orphaned_events = 0

    def detect_voyages(self, events: List[Event]) -> List[Voyage]:
        """
        Detect voyages from a list of events.

        Algorithm:
        1. Group events by IMO
        2. For each vessel, scan for Cross In events (voyage start)
        3. Collect all events until next Cross Out (voyage end)
        4. Create Voyage object with collected events
        5. Mark incomplete if Cross Out missing

        Args:
            events: List of Event objects sorted by IMO and timestamp

        Returns:
            List of Voyage objects
        """
        # Group events by IMO
        events_by_imo = self._group_events_by_imo(events)

        logger.info(f"Processing {len(events_by_imo)} vessels")

        # Detect voyages for each vessel
        all_voyages = []
        for imo, vessel_events in events_by_imo.items():
            voyages = self._detect_voyages_for_vessel(imo, vessel_events)
            all_voyages.extend(voyages)

        logger.info(
            f"Detected {self.voyages_created} voyages "
            f"({self.incomplete_voyages} incomplete, {self.orphaned_events} orphaned events)"
        )

        return all_voyages

    def _group_events_by_imo(self, events: List[Event]) -> Dict[str, List[Event]]:
        """Group events by IMO number."""
        events_by_imo = defaultdict(list)
        for event in events:
            events_by_imo[event.imo].append(event)
        return dict(events_by_imo)

    def _detect_voyages_for_vessel(self, imo: str, events: List[Event]) -> List[Voyage]:
        """Detect all voyages for a single vessel."""
        voyages = []
        i = 0

        while i < len(events):
            event = events[i]

            # Look for voyage start (Cross In)
            if event.is_voyage_start():
                voyage, next_index = self._create_voyage_from_cross_in(events, i)
                voyages.append(voyage)
                self.voyages_created += 1
                i = next_index
            else:
                # Orphaned event (no Cross In before this event)
                if not voyages or voyages[-1].is_complete:
                    # This is an orphaned event - create a quality issue
                    logger.warning(
                        f"Orphaned event: {event.imo} {event.vessel_name} "
                        f"{event.action} {event.zone} at {event.timestamp}"
                    )
                    self.orphaned_events += 1
                i += 1

        return voyages

    def _create_voyage_from_cross_in(
        self,
        events: List[Event],
        start_idx: int
    ) -> tuple[Voyage, int]:
        """
        Create a voyage starting from a Cross In event.

        Args:
            events: List of all events for this vessel
            start_idx: Index of the Cross In event

        Returns:
            Tuple of (Voyage object, next index to process)
        """
        cross_in_event = events[start_idx]
        voyage_id = f"{cross_in_event.imo}_{cross_in_event.timestamp.strftime('%Y%m%d_%H%M%S')}"

        voyage_events = [cross_in_event]
        cross_out_event = None
        current_idx = start_idx + 1

        # Collect events until Cross Out or end of list
        while current_idx < len(events):
            event = events[current_idx]

            # Stop if we hit another Cross In (start of next voyage)
            if event.is_voyage_start():
                break

            voyage_events.append(event)

            # Check for Cross Out (end of voyage)
            if event.is_voyage_end():
                cross_out_event = event
                current_idx += 1
                break

            current_idx += 1

        # Create voyage
        voyage = Voyage(
            voyage_id=voyage_id,
            imo=cross_in_event.imo,
            vessel_name=cross_in_event.vessel_name,
            cross_in_event=cross_in_event,
            cross_out_event=cross_out_event,
            events=voyage_events,
            is_complete=(cross_out_event is not None)
        )

        # Add quality issue if incomplete
        if not voyage.is_complete:
            issue = QualityIssue(
                issue_type=IssueType.MISSING_CROSS_OUT,
                severity=Severity.WARNING,
                voyage_id=voyage_id,
                imo=voyage.imo,
                vessel_name=voyage.vessel_name,
                timestamp=cross_in_event.timestamp,
                description=f"Voyage missing Cross Out event (started {cross_in_event.timestamp})",
                affected_events=[cross_in_event]
            )
            voyage.add_quality_issue(issue)
            self.incomplete_voyages += 1

        return voyage, current_idx

    def get_stats(self) -> dict:
        """Get detection statistics."""
        return {
            'voyages_created': self.voyages_created,
            'incomplete_voyages': self.incomplete_voyages,
            'orphaned_events': self.orphaned_events,
            'completion_rate': (
                (self.voyages_created - self.incomplete_voyages) / self.voyages_created * 100
                if self.voyages_created > 0 else 0
            )
        }
