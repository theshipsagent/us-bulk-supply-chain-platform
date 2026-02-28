"""Policy analysis data extractor — Section 301, tariffs, regulatory tracker."""

import logging
import sys
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class PolicyExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "policy"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        toolsets_dir = str(get_project_root() / "02_TOOLSETS")
        if toolsets_dir not in sys.path:
            sys.path.insert(0, toolsets_dir)

        # Section 301 fee schedule
        try:
            from policy_analysis.src.section_301_model import assess_section_301, compare_phases

            # Representative bulk carrier assessment
            phases = []
            for phase in [1, 2, 3]:
                result = assess_section_301(
                    vessel_name="Representative Bulk Carrier",
                    vessel_nrt=20000,
                    vessel_type="bulk",
                    category="chinese_built",
                    phase=phase,
                    cargo_tons=30000,
                )
                phases.append({
                    "phase": phase,
                    "fee": result.applied_fee,
                    "fee_per_ton": result.fee_per_ton_cargo,
                    "fee_type": result.fee_type,
                })

            data["section_301_phases"] = phases
            data["section_301_loaded"] = True

        except ImportError:
            logger.warning("policy_analysis not importable — skipping Section 301 data")
            data["section_301_loaded"] = False
        except Exception as e:
            logger.warning("Section 301 extractor error: %s", e)
            data["section_301_loaded"] = False

        # Landed cost example (Turkish cement)
        try:
            from policy_analysis.src.tariff_impact import calculate_landed_cost

            lc = calculate_landed_cost(
                commodity="cement",
                hts_code="2523.29",
                origin_country="Turkey",
                cargo_tons=30000,
                fob_price_per_ton=55.0,
                ocean_freight_per_ton=25.0,
            )
            data["landed_cost_example"] = {
                "origin": "Turkey",
                "fob": lc.fob_price_per_ton,
                "cif": lc.cif_per_ton,
                "duty_pct": lc.general_duty_pct,
                "landed_per_ton": lc.total_landed_per_ton,
                "total_landed": lc.total_landed_cost,
            }
            data["landed_cost_loaded"] = True

        except ImportError:
            data["landed_cost_loaded"] = False
        except Exception as e:
            logger.warning("Landed cost extractor error: %s", e)
            data["landed_cost_loaded"] = False

        # Regulatory tracker
        try:
            from policy_analysis.src.regulatory_tracker import get_active_actions
            actions = get_active_actions()
            data["regulatory_action_count"] = len(actions)
            data["regulatory_actions"] = [
                {
                    "id": a.action_id,
                    "agency": a.agency,
                    "title": a.title,
                    "status": a.status,
                }
                for a in actions[:10]
            ]
            data["regulatory_loaded"] = True
        except ImportError:
            data["regulatory_loaded"] = False
        except Exception as e:
            logger.warning("Regulatory extractor error: %s", e)
            data["regulatory_loaded"] = False

        return data
