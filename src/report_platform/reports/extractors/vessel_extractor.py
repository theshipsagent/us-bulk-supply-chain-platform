"""Vessel voyage analysis data extractor — reads CSV results from disk."""

import logging
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor
from report_platform.reports.extractors.file_loader import (
    load_csv_records,
    csv_row_count,
    file_exists,
    file_modified,
)

logger = logging.getLogger(__name__)

_RESULTS_DIR = "02_TOOLSETS/vessel_voyage_analysis/results_phase2_full"


class VesselExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "vessel"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()
        results = root / _RESULTS_DIR

        if not results.exists():
            logger.warning("Vessel results directory not found: %s", results)
            data["vessel_data_loaded"] = False
            return data

        # Voyage summary
        voyage_path = results / "voyage_summary.csv"
        voyage_rows = load_csv_records(voyage_path)
        if voyage_rows:
            data["vessel_voyage_count"] = len(voyage_rows)
            complete = sum(
                1 for r in voyage_rows if r.get("IsComplete", "").lower() == "yes"
            )
            data["vessel_complete_voyages"] = complete
            unique_vessels = {r.get("IMO") for r in voyage_rows if r.get("IMO")}
            data["vessel_unique_count"] = len(unique_vessels)

            # Average port time
            port_times = []
            for r in voyage_rows:
                try:
                    pt = float(r.get("TotalPortTimeHours", 0))
                    if pt > 0:
                        port_times.append(pt)
                except (TypeError, ValueError):
                    pass
            if port_times:
                data["vessel_avg_port_time_hours"] = round(
                    sum(port_times) / len(port_times), 1
                )

        # Efficiency metrics
        eff_path = results / "efficiency_metrics.csv"
        eff_rows = load_csv_records(eff_path, limit=20)
        if eff_rows:
            data["vessel_efficiency_metrics"] = [
                {
                    "vessel": row.get("VesselName", ""),
                    "total_voyages": row.get("TotalVoyages", ""),
                    "avg_port_hours": _round(row.get("AvgPortDurationHours"), 1),
                    "utilization_pct": _round(row.get("AvgVesselUtilizationPct"), 1),
                    "frequent_terminal": row.get("MostFrequentDischargeTerminal", ""),
                }
                for row in eff_rows
                if row.get("VesselName")
            ]
            data["vessel_efficiency_count"] = len(eff_rows)

        # Event log stats
        event_path = results / "event_log.csv"
        data["vessel_event_count"] = csv_row_count(event_path)

        # Voyage segments
        segments_path = results / "voyage_segments.csv"
        data["vessel_segment_count"] = csv_row_count(segments_path)

        data["vessel_results_updated"] = file_modified(voyage_path)
        data["vessel_data_loaded"] = bool(voyage_rows or eff_rows)

        if data["vessel_data_loaded"]:
            logger.info(
                "Vessel extractor: %d voyages, %d efficiency records",
                len(voyage_rows),
                len(eff_rows),
            )

        return data


def _round(val, decimals: int):
    """Safely round a string or numeric value."""
    if val is None:
        return None
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return val
