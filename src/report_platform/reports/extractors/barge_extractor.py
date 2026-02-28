"""Barge cost model data extractor — reads forecast results from disk."""

import logging
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor
from report_platform.reports.extractors.file_loader import (
    load_csv_records,
    load_json,
    file_exists,
    file_modified,
)

logger = logging.getLogger(__name__)

# Base path relative to project root
_RESULTS_DIR = "02_TOOLSETS/barge_cost_model/forecasting/results"


class BargeExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "barge"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()
        results = root / _RESULTS_DIR

        if not results.exists():
            logger.warning("Barge results directory not found: %s", results)
            data["barge_data_loaded"] = False
            return data

        # Forecast accuracy comparison (VAR vs SpVAR vs Naive)
        accuracy_rows = load_csv_records(results / "forecast_accuracy_comparison.csv")
        if accuracy_rows:
            data["barge_forecast_accuracy"] = [
                {
                    "segment": row.get("segment", ""),
                    "naive_mape": _round(row.get("naive_mape"), 1),
                    "var_mape": _round(row.get("var_mape"), 1),
                    "spvar_mape": _round(row.get("spvar_mape"), 1),
                    "var_r2": _round(row.get("var_r2"), 3),
                    "var_improvement_pct": _round(row.get("var_improvement_pct"), 1),
                }
                for row in accuracy_rows
            ]

        # Forecast comparison summary (model-level stats)
        summary = load_json(results / "forecast_comparison_summary.json")
        if summary:
            data["barge_forecast_summary"] = {
                "models_compared": summary.get("models_compared", []),
                "test_periods": summary.get("test_periods", 0),
                "segments": summary.get("segments", 0),
                "naive_avg_mape": _round(
                    summary.get("naive_baseline", {}).get("avg_mape"), 1
                ),
                "var_avg_mape": _round(
                    summary.get("var_model", {}).get("avg_mape"), 1
                ),
                "spvar_avg_mape": _round(
                    summary.get("spvar_model", {}).get("avg_mape"), 1
                ),
                "var_avg_r2": _round(
                    summary.get("var_model", {}).get("avg_r2"), 3
                ),
            }

        # Economic impact analysis
        impact_rows = load_csv_records(results / "economic_impact_analysis.csv")
        if impact_rows:
            data["barge_economic_impact"] = [
                {
                    "shipper_type": row.get("shipper_type", ""),
                    "annual_volume": _round(row.get("annual_volume"), 0),
                    "annual_savings": _round(row.get("annual_savings"), 0),
                }
                for row in impact_rows
            ]

        # Diebold-Mariano statistical tests
        dm_rows = load_csv_records(results / "diebold_mariano_tests.csv")
        if dm_rows:
            data["barge_dm_tests"] = dm_rows

        # VAR model results
        var_summary = load_json(results / "var_results_summary.json")
        if var_summary:
            data["barge_var_model"] = {
                "lag_order": var_summary.get("lag_order", ""),
                "training_obs": var_summary.get("training_observations", 0),
                "test_obs": var_summary.get("test_observations", 0),
                "segment_count": len(var_summary.get("segments", [])),
            }

        data["barge_results_updated"] = file_modified(
            results / "forecast_comparison_summary.json"
        )
        data["barge_data_loaded"] = bool(accuracy_rows or summary)

        if data["barge_data_loaded"]:
            logger.info(
                "Barge extractor loaded %d accuracy rows, summary=%s",
                len(accuracy_rows),
                bool(summary),
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
