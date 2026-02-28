"""Barge cost model data extractor."""

import logging
import sys
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class BargeExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "barge"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        # Ensure toolsets are importable
        toolsets_dir = str(get_project_root() / "02_TOOLSETS")
        if toolsets_dir not in sys.path:
            sys.path.insert(0, toolsets_dir)

        try:
            from barge_cost_model.barge_cost_calculator import BargeCostCalculator
            calc = BargeCostCalculator()
            status = calc.load_data()

            # Reference corridors for cost benchmarking
            corridors = [
                ("Minneapolis", "MISSISSIPPI RIVER", 858.0, "MISSISSIPPI RIVER", 0.0),
                ("St. Louis", "MISSISSIPPI RIVER", 185.0, "MISSISSIPPI RIVER", 0.0),
                ("Cincinnati", "OHIO RIVER", 470.0, "MISSISSIPPI RIVER", 0.0),
                ("Pittsburgh", "OHIO RIVER", 0.0, "MISSISSIPPI RIVER", 0.0),
                ("Chicago", "ILLINOIS RIVER", 327.0, "MISSISSIPPI RIVER", 0.0),
            ]

            corridor_rates = []
            for name, o_river, o_mile, d_river, d_mile in corridors:
                try:
                    result = calc.calculate_route_cost(
                        origin_river=o_river, origin_mile=o_mile,
                        dest_river=d_river, dest_mile=d_mile,
                    )
                    corridor_rates.append({
                        "origin": name,
                        "destination": "New Orleans",
                        "miles": result.get("route_miles", 0),
                        "cost_per_ton": result.get("cost_per_ton", 0),
                        "total_cost": result.get("total_variable_cost", 0),
                    })
                except Exception as e:
                    logger.debug("Barge corridor %s failed: %s", name, e)

            data["barge_corridor_rates"] = corridor_rates
            data["barge_network_nodes"] = status.get("nodes", "N/A")
            data["barge_data_loaded"] = True

            # Rate forecast
            try:
                forecast_df = calc.get_rate_forecast(weeks_ahead=4)
                if not forecast_df.empty:
                    data["barge_rate_forecast"] = forecast_df.to_dict("records")
            except Exception:
                pass

        except ImportError:
            logger.warning("barge_cost_model not importable — skipping barge data")
            data["barge_data_loaded"] = False
        except Exception as e:
            logger.warning("Barge extractor error: %s", e)
            data["barge_data_loaded"] = False

        return data
