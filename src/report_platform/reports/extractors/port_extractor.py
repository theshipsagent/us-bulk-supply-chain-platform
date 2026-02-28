"""Port cost model data extractor — proforma port cost benchmarks."""

import logging
import sys
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class PortExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "port"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        toolsets_dir = str(get_project_root() / "02_TOOLSETS")
        if toolsets_dir not in sys.path:
            sys.path.insert(0, toolsets_dir)

        try:
            from port_cost_model.src.proforma_generator import generate_proforma

            # Benchmark ports for bulk cargo
            benchmark_ports = [
                {"port": "new_orleans", "label": "New Orleans"},
                {"port": "houston", "label": "Houston"},
                {"port": "tampa", "label": "Tampa"},
                {"port": "mobile", "label": "Mobile"},
            ]

            port_benchmarks = []
            for bp in benchmark_ports:
                try:
                    pf = generate_proforma(
                        vessel_name="Benchmark Vessel",
                        port=bp["port"],
                        cargo_type="cement",
                        cargo_tons=30000,
                        vessel_loa_feet=590,
                        vessel_draft_feet=38.5,
                        vessel_gt=32000,
                        vessel_dwt=55000,
                        days_alongside=3,
                    )
                    port_benchmarks.append({
                        "port": bp["label"],
                        "total_cost": pf.get("total_cost", 0),
                        "cost_per_ton": pf.get("cost_per_ton", 0),
                        "pilotage": pf.get("pilotage_total", 0),
                        "dockage": pf.get("dockage", 0),
                    })
                except Exception as e:
                    logger.debug("Port benchmark for %s failed: %s", bp["label"], e)

            data["port_benchmarks"] = port_benchmarks
            data["port_data_loaded"] = True

        except ImportError:
            logger.warning("port_cost_model not importable — skipping port data")
            data["port_data_loaded"] = False
        except Exception as e:
            logger.warning("Port extractor error: %s", e)
            data["port_data_loaded"] = False

        return data
