"""Rail cost model data extractor — reads cement analytics CSVs from disk."""

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

_REPORTS_DIR = "02_TOOLSETS/rail_cost_model/analytics/reports"


class RailExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "rail"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()
        reports = root / _REPORTS_DIR

        if not reports.exists():
            logger.warning("Rail reports directory not found: %s", reports)
            data["rail_data_loaded"] = False
            return data

        # Cement origin BEAs (top shipping origins)
        origins_path = reports / "cement_origins.csv"
        origin_rows = load_csv_records(origins_path, limit=15)
        if origin_rows:
            data["rail_cement_origins"] = [
                {
                    "origin": row.get("origin", row.get("origin_bea", "")),
                    "states": row.get("states", ""),
                    "tons_M": _round(row.get("tons_M"), 2),
                    "rev_M": _round(row.get("rev_M"), 1),
                    "rev_per_ton": _round(row.get("rev_per_ton"), 2),
                    "avg_miles": _round(row.get("avg_miles"), 0),
                    "num_dests": row.get("num_dests", ""),
                }
                for row in origin_rows
                if row.get("origin")  # skip rows without origin name
            ]

        # Cement destination BEAs (top receiving markets)
        dest_path = reports / "cement_destinations.csv"
        dest_rows = load_csv_records(dest_path, limit=15)
        if dest_rows:
            data["rail_cement_destinations"] = [
                {
                    "destination": row.get("destination", ""),
                    "states": row.get("states", ""),
                    "tons_M": _round(row.get("tons_M"), 2),
                    "rev_M": _round(row.get("rev_M"), 1),
                    "num_origins": row.get("num_origins", ""),
                }
                for row in dest_rows
                if row.get("destination")
            ]

        # Cement O-D flows (top origin-destination pairs)
        od_path = reports / "cement_od_flows.csv"
        od_rows = load_csv_records(od_path, limit=15)
        if od_rows:
            data["rail_cement_od_flows"] = [
                {
                    "origin": row.get("origin", ""),
                    "destination": row.get("destination", ""),
                    "tons_M": _round(row.get("tons_M"), 3),
                    "miles": _round(row.get("miles"), 0),
                    "rate": _round(row.get("rate"), 2),
                }
                for row in od_rows
                if row.get("origin") and row.get("destination")
            ]

        # Summary stats
        data["rail_total_od_flows"] = csv_row_count(od_path)
        data["rail_total_origins"] = csv_row_count(origins_path)
        data["rail_total_destinations"] = csv_row_count(dest_path)
        data["rail_results_updated"] = file_modified(origins_path)
        data["rail_data_loaded"] = bool(origin_rows or od_rows)

        if data["rail_data_loaded"]:
            logger.info(
                "Rail extractor loaded %d origins, %d OD flows",
                len(origin_rows),
                len(od_rows),
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
