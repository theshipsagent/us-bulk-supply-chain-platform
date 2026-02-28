"""Rail cost model data extractor."""

import logging
import sys
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class RailExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "rail"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        toolsets_dir = str(get_project_root() / "02_TOOLSETS")
        if toolsets_dir not in sys.path:
            sys.path.insert(0, toolsets_dir)

        try:
            from rail_cost_model.src.costing.route_costing import RouteCostCalculator
            calc = RouteCostCalculator()

            # Benchmark corridors at different distances
            benchmarks = [
                {"label": "Short haul (200 mi)", "miles": 200, "tons": 5000, "cars": 50},
                {"label": "Medium haul (500 mi)", "miles": 500, "tons": 5000, "cars": 50},
                {"label": "Long haul (1000 mi)", "miles": 1000, "tons": 5000, "cars": 50},
                {"label": "Unit train (1000 mi)", "miles": 1000, "tons": 11000, "cars": 110},
            ]

            rail_benchmarks = []
            for bm in benchmarks:
                try:
                    result = calc.calculate_route_cost(
                        route_miles=bm["miles"],
                        commodity_tons=bm["tons"],
                        num_cars=bm["cars"],
                    )
                    rail_benchmarks.append({
                        "label": bm["label"],
                        "miles": bm["miles"],
                        "cost_per_ton": result["cost_per_ton"],
                        "cost_per_mile": result["cost_per_mile"],
                        "total_cost": result["total_variable_cost"],
                    })
                except Exception as e:
                    logger.debug("Rail benchmark %s failed: %s", bm["label"], e)

            data["rail_benchmarks"] = rail_benchmarks
            data["rail_data_loaded"] = True

        except ImportError:
            logger.warning("rail_cost_model not importable — skipping rail data")
            data["rail_data_loaded"] = False
        except Exception as e:
            logger.warning("Rail extractor error: %s", e)
            data["rail_data_loaded"] = False

        return data
