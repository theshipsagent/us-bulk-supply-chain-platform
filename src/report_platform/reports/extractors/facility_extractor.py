"""EPA FRS facility registry data extractor."""

import logging
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

# Key NAICS codes for bulk commodities
NAICS_QUERIES = {
    "cement_plants": ("327310", "Cement Manufacturing"),
    "ready_mix": ("327320", "Ready-Mix Concrete"),
    "steel_mills": ("331110", "Iron and Steel Mills"),
    "grain_elevators": ("493130", "Farm Product Warehousing"),
    "petroleum_refineries": ("324110", "Petroleum Refineries"),
    "fertilizer_mfg": ("325311", "Nitrogenous Fertilizer Manufacturing"),
}


class FacilityExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "facility"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()
        db_path = root / "02_TOOLSETS" / "facility_registry" / "data" / "frs.duckdb"

        if not db_path.exists():
            logger.warning("FRS database not found at %s — skipping", db_path)
            data["facility_data_loaded"] = False
            return data

        try:
            import duckdb
            conn = duckdb.connect(str(db_path), read_only=True)

            # Count facilities by NAICS
            facility_counts = {}
            for key, (naics, label) in NAICS_QUERIES.items():
                try:
                    result = conn.execute(
                        """
                        SELECT COUNT(DISTINCT f.registry_id)
                        FROM facilities f
                        WHERE f.registry_id IN (
                            SELECT DISTINCT registry_id
                            FROM naics_codes
                            WHERE naics_code LIKE ?
                        )
                        """,
                        [f"{naics}%"],
                    ).fetchone()
                    facility_counts[key] = {
                        "naics": naics,
                        "label": label,
                        "count": result[0] if result else 0,
                    }
                except Exception as e:
                    logger.debug("Facility count for %s failed: %s", key, e)

            data["facility_counts"] = facility_counts

            # Total facilities in database
            total = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()
            data["facility_total_count"] = total[0] if total else 0

            # Top states for cement manufacturing
            cement_by_state = conn.execute(
                """
                SELECT f.fac_state, COUNT(DISTINCT f.registry_id) as cnt
                FROM facilities f
                WHERE f.registry_id IN (
                    SELECT DISTINCT registry_id FROM naics_codes
                    WHERE naics_code LIKE '3273%'
                )
                GROUP BY f.fac_state
                ORDER BY cnt DESC
                LIMIT 10
                """,
            ).fetchall()
            data["cement_facilities_by_state"] = [
                {"state": row[0], "count": row[1]} for row in cement_by_state
            ]

            conn.close()
            data["facility_data_loaded"] = True

        except ImportError:
            logger.warning("duckdb not available — skipping facility data")
            data["facility_data_loaded"] = False
        except Exception as e:
            logger.warning("Facility extractor error: %s", e)
            data["facility_data_loaded"] = False

        return data
