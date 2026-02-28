"""Efficiency metrics calculator for voyage segments."""

from typing import List, Dict, Optional
from collections import defaultdict
import logging
from ..models.voyage_segment import VoyageSegment

logger = logging.getLogger(__name__)


class EfficiencyCalculator:
    """
    Calculates efficiency and utilization metrics for voyage segments.

    Metrics calculated:
    - Vessel utilization (terminal time / total port time)
    - Port idle time
    - Cargo tonnage estimates (using TPC)
    - Aggregate statistics by vessel
    """

    def __init__(self):
        """Initialize the efficiency calculator."""
        self.segments_processed = 0
        self.segments_with_utilization = 0
        self.segments_with_cargo_estimate = 0

    def calculate_efficiency(
        self,
        segments: List[VoyageSegment],
        ship_register: Optional[Dict[str, Dict]] = None
    ) -> List[VoyageSegment]:
        """
        Calculate efficiency metrics for all segments.

        Args:
            segments: List of VoyageSegment objects
            ship_register: Optional dict of ship characteristics (IMO -> data)
                          Used for TPC-based cargo estimation

        Returns:
            Same list of segments with efficiency metrics populated
        """
        logger.info(f"Calculating efficiency metrics for {len(segments)} segments")

        for segment in segments:
            self._calculate_segment_efficiency(segment, ship_register)
            self.segments_processed += 1

        logger.info(
            f"Processed {self.segments_processed} segments "
            f"({self.segments_with_utilization} with utilization, "
            f"{self.segments_with_cargo_estimate} with cargo estimates)"
        )

        return segments

    def _calculate_segment_efficiency(
        self,
        segment: VoyageSegment,
        ship_register: Optional[Dict[str, Dict]]
    ) -> None:
        """Calculate efficiency metrics for a single segment."""

        # Calculate vessel utilization (terminal time / total port time)
        self._calculate_vessel_utilization(segment)

        # Calculate port idle time (approximation: port_duration)
        # In the future, could subtract actual loading/unloading activity time
        if segment.port_duration_hours is not None:
            segment.port_idle_time_hours = segment.port_duration_hours

        # Calculate cargo tonnage estimate using TPC (if ship register available)
        if ship_register:
            self._calculate_cargo_tonnage(segment, ship_register)

        # Note: Inbound/Outbound efficiency (hours per mile) would require
        # mile data tracking per segment, which is not currently available.
        # This would be a future enhancement if mile markers are tracked.

    def _calculate_vessel_utilization(self, segment: VoyageSegment) -> None:
        """
        Calculate vessel utilization percentage.

        Formula: (port_duration / total_port_time) * 100

        High utilization = vessel spent most time at terminal (efficient)
        Low utilization = vessel spent lots of time anchored/transiting (inefficient)
        """
        if (segment.port_duration_hours is not None and
            segment.total_port_time_hours is not None and
            segment.total_port_time_hours > 0):

            segment.vessel_utilization_pct = (
                segment.port_duration_hours / segment.total_port_time_hours * 100
            )
            self.segments_with_utilization += 1

    def _calculate_cargo_tonnage(
        self,
        segment: VoyageSegment,
        ship_register: Dict[str, Dict]
    ) -> None:
        """
        Calculate estimated cargo tonnage using TPC (Tonnes Per Centimeter).

        Formula:
        - draft_delta_ft converted to meters
        - draft_delta_m converted to centimeters
        - cargo_tonnes = draft_delta_cm * TPC

        Args:
            segment: Segment to calculate cargo for
            ship_register: Dict with IMO as key, ship data as value
        """
        # Check if we have draft delta
        if segment.draft_delta_ft is None:
            return

        # Look up ship in register
        ship_data = ship_register.get(segment.imo)
        if not ship_data:
            return

        # Get TPC from ship register
        tpc = ship_data.get('tpc')
        if tpc is None:
            return

        # Convert draft delta from feet to centimeters
        # 1 foot = 30.48 cm
        draft_delta_cm = segment.draft_delta_ft * 30.48

        # Calculate cargo tonnage
        # Positive draft delta = loaded cargo outbound
        # Negative draft delta = loaded cargo inbound (delivered)
        segment.estimated_cargo_tonnes = abs(draft_delta_cm * tpc)
        self.segments_with_cargo_estimate += 1

    def calculate_aggregate_metrics(
        self,
        segments: List[VoyageSegment]
    ) -> Dict[str, Dict]:
        """
        Calculate aggregate metrics across all segments.

        Groups by vessel (IMO) and calculates:
        - Total voyages
        - Average durations (inbound, outbound, port)
        - Average utilization
        - Most frequent discharge terminal
        - Total cargo estimate

        Args:
            segments: List of VoyageSegment objects

        Returns:
            Dict with IMO as key, aggregate metrics as value
        """
        logger.info(f"Calculating aggregate metrics for {len(segments)} segments")

        # Group segments by vessel (IMO)
        segments_by_vessel = defaultdict(list)
        for segment in segments:
            segments_by_vessel[segment.imo].append(segment)

        # Calculate aggregates for each vessel
        aggregates = {}
        for imo, vessel_segments in segments_by_vessel.items():
            aggregates[imo] = self._calculate_vessel_aggregates(vessel_segments)

        logger.info(f"Generated aggregate metrics for {len(aggregates)} vessels")

        return aggregates

    def _calculate_vessel_aggregates(
        self,
        segments: List[VoyageSegment]
    ) -> Dict:
        """
        Calculate aggregate metrics for a single vessel.

        Args:
            segments: List of segments for this vessel

        Returns:
            Dict of aggregate metrics
        """
        # Get vessel name (same for all segments)
        vessel_name = segments[0].vessel_name if segments else "Unknown"

        # Filter to complete segments only for accurate averages
        complete_segments = [s for s in segments if s.is_complete]

        # Collect metrics
        inbound_durations = [s.inbound_duration_hours for s in complete_segments
                            if s.inbound_duration_hours is not None]
        outbound_durations = [s.outbound_duration_hours for s in complete_segments
                             if s.outbound_duration_hours is not None]
        port_durations = [s.port_duration_hours for s in complete_segments
                         if s.port_duration_hours is not None]
        utilizations = [s.vessel_utilization_pct for s in complete_segments
                       if s.vessel_utilization_pct is not None]
        cargo_estimates = [s.estimated_cargo_tonnes for s in complete_segments
                          if s.estimated_cargo_tonnes is not None]

        # Find most frequent discharge terminal
        terminals = [s.discharge_terminal_facility for s in segments
                    if s.discharge_terminal_facility is not None]
        most_frequent_terminal = self._get_most_frequent(terminals)

        # Calculate averages
        return {
            'vessel_name': vessel_name,
            'total_voyages': len(segments),
            'complete_voyages': len(complete_segments),
            'avg_inbound_duration_hours': self._safe_avg(inbound_durations),
            'avg_outbound_duration_hours': self._safe_avg(outbound_durations),
            'avg_port_duration_hours': self._safe_avg(port_durations),
            'avg_vessel_utilization_pct': self._safe_avg(utilizations),
            'most_frequent_discharge_terminal': most_frequent_terminal,
            'total_cargo_estimate_tonnes': sum(cargo_estimates) if cargo_estimates else None,
            'avg_cargo_per_voyage_tonnes': self._safe_avg(cargo_estimates)
        }

    def _safe_avg(self, values: List[float]) -> Optional[float]:
        """Calculate average, returning None if list is empty."""
        if not values:
            return None
        return sum(values) / len(values)

    def _get_most_frequent(self, items: List[str]) -> Optional[str]:
        """Get most frequent item from list."""
        if not items:
            return None

        counts = defaultdict(int)
        for item in items:
            counts[item] += 1

        return max(counts.items(), key=lambda x: x[1])[0]

    def get_stats(self) -> dict:
        """Get calculation statistics."""
        return {
            'segments_processed': self.segments_processed,
            'segments_with_utilization': self.segments_with_utilization,
            'segments_with_cargo_estimate': self.segments_with_cargo_estimate,
            'utilization_coverage': (
                self.segments_with_utilization / self.segments_processed * 100
                if self.segments_processed > 0 else 0
            ),
            'cargo_estimate_coverage': (
                self.segments_with_cargo_estimate / self.segments_processed * 100
                if self.segments_processed > 0 else 0
            )
        }
