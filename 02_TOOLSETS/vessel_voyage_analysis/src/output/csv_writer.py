"""CSV output generation for voyage summaries and event logs."""

import csv
from pathlib import Path
from typing import List, Dict
import logging
from ..models.voyage import Voyage
from ..models.voyage_segment import VoyageSegment

logger = logging.getLogger(__name__)


class CSVWriter:
    """Writes voyage analysis results to CSV files."""

    def write_voyage_summary(self, voyages: List[Voyage], output_path: str) -> None:
        """
        Write voyage summary CSV.

        Columns: VoyageID, IMO, VesselName, CrossInTime, CrossOutTime,
                 TotalPortTimeHours, TransitTimeHours, AnchorTimeHours,
                 TerminalTimeHours, NumAnchorStops, NumTerminalStops,
                 IsComplete, QualityFlags

        Args:
            voyages: List of Voyage objects
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'VoyageID',
                'IMO',
                'VesselName',
                'CrossInTime',
                'CrossOutTime',
                'TotalPortTimeHours',
                'TransitTimeHours',
                'AnchorTimeHours',
                'TerminalTimeHours',
                'NumAnchorStops',
                'NumTerminalStops',
                'IsComplete',
                'QualityFlags'
            ])

            # Write data rows
            for voyage in voyages:
                cross_out_time = (
                    voyage.cross_out_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    if voyage.cross_out_event else ''
                )

                writer.writerow([
                    voyage.voyage_id,
                    voyage.imo,
                    voyage.vessel_name,
                    voyage.cross_in_event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    cross_out_time,
                    f"{voyage.total_port_time_hours:.2f}" if voyage.total_port_time_hours else '',
                    f"{voyage.total_transit_time_hours:.2f}",
                    f"{voyage.total_anchor_time_hours:.2f}",
                    f"{voyage.total_terminal_time_hours:.2f}",
                    voyage.num_anchor_stops,
                    voyage.num_terminal_stops,
                    'Yes' if voyage.is_complete else 'No',
                    voyage.get_quality_flags()
                ])

        logger.info(f"Wrote voyage summary to {output_path} ({len(voyages)} voyages)")

    def write_event_log(self, voyages: List[Voyage], output_path: str) -> None:
        """
        Write event log CSV.

        Columns: VoyageID, IMO, VesselName, EventType, EventTime, Zone,
                 ZoneType, Action, DurationToNextEventHours, NextEventType,
                 Draft, VesselType, Facility, VesselTypes, Activity, Cargoes,
                 ShipType_Register, DWT, RegisterDraft_m, TPC, ShipMatchMethod

        Args:
            voyages: List of Voyage objects
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        total_events = 0

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'VoyageID',
                'IMO',
                'VesselName',
                'EventType',
                'EventTime',
                'Zone',
                'ZoneType',
                'Action',
                'DurationToNextEventHours',
                'NextEventType',
                'Draft',
                'VesselType',
                'Facility',
                'VesselTypes',
                'Activity',
                'Cargoes',
                'ShipType_Register',
                'DWT',
                'RegisterDraft_m',
                'TPC',
                'ShipMatchMethod'
            ])

            # Write data rows
            for voyage in voyages:
                events = voyage.events

                for i, event in enumerate(events):
                    # Calculate duration to next event
                    duration_hours = ''
                    next_event_type = ''

                    if i < len(events) - 1:
                        next_event = events[i + 1]
                        duration = next_event.timestamp - event.timestamp
                        duration_hours = f"{duration.total_seconds() / 3600.0:.2f}"
                        next_event_type = f"{next_event.action} {next_event.zone_type}"

                    # Determine event type
                    event_type = self._get_event_type(event)

                    writer.writerow([
                        voyage.voyage_id,
                        event.imo,
                        event.vessel_name,
                        event_type,
                        event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        event.zone,
                        event.zone_type,
                        event.action,
                        duration_hours,
                        next_event_type,
                        f"{event.draft:.1f}" if event.draft else '',
                        event.vessel_type or '',
                        event.facility or '',
                        event.vessel_types or '',
                        event.activity or '',
                        event.cargoes or '',
                        event.ship_type_register or '',
                        f"{event.dwt:.0f}" if event.dwt else '',
                        f"{event.register_draft_m:.2f}" if event.register_draft_m else '',
                        f"{event.tpc:.2f}" if event.tpc else '',
                        event.ship_match_method or ''
                    ])

                    total_events += 1

        logger.info(f"Wrote event log to {output_path} ({total_events} events)")

    @staticmethod
    def _get_event_type(event) -> str:
        """Determine human-readable event type."""
        if event.is_voyage_start():
            return 'VOYAGE_START'
        elif event.is_voyage_end():
            return 'VOYAGE_END'
        elif event.is_anchor_arrive():
            return 'ANCHOR_ARRIVE'
        elif event.is_anchor_depart():
            return 'ANCHOR_DEPART'
        elif event.is_terminal_arrive():
            return 'TERMINAL_ARRIVE'
        elif event.is_terminal_depart():
            return 'TERMINAL_DEPART'
        else:
            return f"{event.action}_{event.zone_type}"

    def write_voyage_segments(self, segments: List[VoyageSegment], output_path: str) -> None:
        """
        Write voyage segments CSV (Phase 2).

        Columns: VoyageID, SegmentID, IMO, VesselName,
                 CrossInTime, CrossInDraft, FirstTerminalArrivalTime,
                 FirstTerminalArrivalDraft, DischargeTerminalZone,
                 DischargeTerminalFacility, InboundDurationHours,
                 InboundTransitHours, InboundAnchorHours,
                 FirstTerminalDepartureTime, FirstTerminalDepartureDraft,
                 CrossOutTime, CrossOutDraft, OutboundDurationHours,
                 OutboundTransitHours, OutboundAnchorHours,
                 PortDurationHours, TotalPortTimeHours,
                 DraftDeltaFt, EstimatedCargoTonnes, CargoStatus,
                 VesselUtilizationPct, HasDischargeTerminal,
                 IsComplete, QualityNotes

        Args:
            segments: List of VoyageSegment objects
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'VoyageID',
                'SegmentID',
                'IMO',
                'VesselName',
                'CrossInTime',
                'CrossInDraft',
                'FirstTerminalArrivalTime',
                'FirstTerminalArrivalDraft',
                'DischargeTerminalZone',
                'DischargeTerminalFacility',
                'InboundDurationHours',
                'InboundTransitHours',
                'InboundAnchorHours',
                'FirstTerminalDepartureTime',
                'FirstTerminalDepartureDraft',
                'CrossOutTime',
                'CrossOutDraft',
                'OutboundDurationHours',
                'OutboundTransitHours',
                'OutboundAnchorHours',
                'PortDurationHours',
                'TotalPortTimeHours',
                'DraftDeltaFt',
                'EstimatedCargoTonnes',
                'CargoStatus',
                'VesselUtilizationPct',
                'HasDischargeTerminal',
                'IsComplete',
                'QualityNotes'
            ])

            # Write data rows
            for segment in segments:
                writer.writerow([
                    segment.voyage_id,
                    segment.segment_id,
                    segment.imo,
                    segment.vessel_name,
                    segment.cross_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                    f"{segment.cross_in_draft:.1f}" if segment.cross_in_draft else '',
                    segment.first_terminal_arrival_time.strftime('%Y-%m-%d %H:%M:%S')
                        if segment.first_terminal_arrival_time else '',
                    f"{segment.first_terminal_arrival_draft:.1f}"
                        if segment.first_terminal_arrival_draft else '',
                    segment.discharge_terminal_zone or '',
                    segment.discharge_terminal_facility or '',
                    f"{segment.inbound_duration_hours:.2f}"
                        if segment.inbound_duration_hours is not None else '',
                    f"{segment.inbound_transit_hours:.2f}",
                    f"{segment.inbound_anchor_hours:.2f}",
                    segment.first_terminal_departure_time.strftime('%Y-%m-%d %H:%M:%S')
                        if segment.first_terminal_departure_time else '',
                    f"{segment.first_terminal_departure_draft:.1f}"
                        if segment.first_terminal_departure_draft else '',
                    segment.cross_out_time.strftime('%Y-%m-%d %H:%M:%S')
                        if segment.cross_out_time else '',
                    f"{segment.cross_out_draft:.1f}" if segment.cross_out_draft else '',
                    f"{segment.outbound_duration_hours:.2f}"
                        if segment.outbound_duration_hours is not None else '',
                    f"{segment.outbound_transit_hours:.2f}",
                    f"{segment.outbound_anchor_hours:.2f}",
                    f"{segment.port_duration_hours:.2f}"
                        if segment.port_duration_hours is not None else '',
                    f"{segment.total_port_time_hours:.2f}"
                        if segment.total_port_time_hours is not None else '',
                    f"{segment.draft_delta_ft:.2f}" if segment.draft_delta_ft is not None else '',
                    f"{segment.estimated_cargo_tonnes:.0f}"
                        if segment.estimated_cargo_tonnes is not None else '',
                    segment.cargo_status or '',
                    f"{segment.vessel_utilization_pct:.1f}"
                        if segment.vessel_utilization_pct is not None else '',
                    'Yes' if segment.has_discharge_terminal else 'No',
                    'Yes' if segment.is_complete else 'No',
                    segment.quality_notes or ''
                ])

        logger.info(f"Wrote voyage segments to {output_path} ({len(segments)} segments)")

    def write_efficiency_metrics(
        self,
        aggregates: Dict[str, Dict],
        output_path: str
    ) -> None:
        """
        Write efficiency metrics CSV (Phase 2).

        Columns: IMO, VesselName, TotalVoyages, CompleteVoyages,
                 AvgInboundDurationHours, AvgOutboundDurationHours,
                 AvgPortDurationHours, AvgVesselUtilizationPct,
                 MostFrequentDischargeTerminal,
                 TotalCargoEstimateTonnes, AvgCargoPerVoyageTonnes

        Args:
            aggregates: Dict with IMO as key, aggregate metrics as value
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'IMO',
                'VesselName',
                'TotalVoyages',
                'CompleteVoyages',
                'AvgInboundDurationHours',
                'AvgOutboundDurationHours',
                'AvgPortDurationHours',
                'AvgVesselUtilizationPct',
                'MostFrequentDischargeTerminal',
                'TotalCargoEstimateTonnes',
                'AvgCargoPerVoyageTonnes'
            ])

            # Write data rows (sorted by IMO)
            for imo in sorted(aggregates.keys()):
                agg = aggregates[imo]

                writer.writerow([
                    imo,
                    agg['vessel_name'],
                    agg['total_voyages'],
                    agg['complete_voyages'],
                    f"{agg['avg_inbound_duration_hours']:.2f}"
                        if agg['avg_inbound_duration_hours'] is not None else '',
                    f"{agg['avg_outbound_duration_hours']:.2f}"
                        if agg['avg_outbound_duration_hours'] is not None else '',
                    f"{agg['avg_port_duration_hours']:.2f}"
                        if agg['avg_port_duration_hours'] is not None else '',
                    f"{agg['avg_vessel_utilization_pct']:.1f}"
                        if agg['avg_vessel_utilization_pct'] is not None else '',
                    agg['most_frequent_discharge_terminal'] or '',
                    f"{agg['total_cargo_estimate_tonnes']:.0f}"
                        if agg['total_cargo_estimate_tonnes'] is not None else '',
                    f"{agg['avg_cargo_per_voyage_tonnes']:.0f}"
                        if agg['avg_cargo_per_voyage_tonnes'] is not None else ''
                ])

        logger.info(f"Wrote efficiency metrics to {output_path} ({len(aggregates)} vessels)")
