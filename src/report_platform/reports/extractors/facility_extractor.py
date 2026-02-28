"""EPA FRS facility registry data extractor — reads CSV analysis outputs first, DuckDB fallback."""

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

_CSV_DIR = "02_TOOLSETS/facility_registry/analysis_outputs"

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
        csv_dir = root / _CSV_DIR

        # Try CSV files first (faster, no DuckDB dependency)
        if csv_dir.exists():
            loaded = self._extract_from_csv(csv_dir, data)
            if loaded:
                data["facility_data_loaded"] = True
                data["facility_source"] = "csv"
                return data

        # Fallback to DuckDB
        db_path = root / "02_TOOLSETS" / "facility_registry" / "data" / "frs.duckdb"
        if db_path.exists():
            self._extract_from_duckdb(db_path, data)
        else:
            logger.warning("No facility data source found (CSV or DuckDB)")
            data["facility_data_loaded"] = False

        return data

    def _extract_from_csv(self, csv_dir, data: dict) -> bool:
        """Extract facility data from pre-computed CSV analysis outputs."""
        found_any = False

        # Cement industry by state
        by_state_path = csv_dir / "cement_industry_by_state.csv"
        state_rows = load_csv_records(by_state_path)
        if state_rows:
            found_any = True
            data["cement_facilities_by_state"] = [
                {
                    "state": row.get("state", ""),
                    "cement_manufacturing": int(row.get("cement_manufacturing", 0)),
                    "ready_mix": int(row.get("ready_mix", 0)),
                    "total_facilities": int(row.get("total_facilities", 0)),
                }
                for row in state_rows[:15]
            ]
            # Compute facility counts from state data
            totals = {}
            for row in state_rows:
                for key in ["cement_manufacturing", "ready_mix", "block_brick",
                            "concrete_pipe", "precast_other", "terminals_distributors"]:
                    totals[key] = totals.get(key, 0) + int(row.get(key, 0))
            data["facility_counts"] = {
                "cement_plants": {
                    "label": "Cement Manufacturing",
                    "count": totals.get("cement_manufacturing", 0),
                },
                "ready_mix": {
                    "label": "Ready-Mix Concrete",
                    "count": totals.get("ready_mix", 0),
                },
                "terminals": {
                    "label": "Terminals & Distributors",
                    "count": totals.get("terminals_distributors", 0),
                },
            }
            data["facility_total_count"] = sum(
                int(row.get("total_facilities", 0)) for row in state_rows
            )
            data["facility_state_count"] = len(state_rows)

        # Cement manufacturing plants detail
        plants_path = csv_dir / "cement_manufacturing_plants.csv"
        plant_rows = load_csv_records(plants_path, limit=25)
        if plant_rows:
            found_any = True
            data["cement_manufacturing_plants"] = plant_rows
            data["cement_plant_count"] = csv_row_count(plants_path)

        # Parent companies summary
        parent_path = csv_dir / "cement_parent_companies_summary.csv"
        parent_rows = load_csv_records(parent_path, limit=20)
        if parent_rows:
            found_any = True
            data["cement_parent_companies"] = parent_rows

        data["facility_results_updated"] = file_modified(by_state_path)
        return found_any

    def _extract_from_duckdb(self, db_path, data: dict):
        """Fallback: query FRS DuckDB directly."""
        try:
            import duckdb
            conn = duckdb.connect(str(db_path), read_only=True)

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

            total = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()
            data["facility_total_count"] = total[0] if total else 0

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
            data["facility_source"] = "duckdb"

        except ImportError:
            logger.warning("duckdb not available — skipping facility data")
            data["facility_data_loaded"] = False
        except Exception as e:
            logger.warning("Facility extractor error: %s", e)
            data["facility_data_loaded"] = False
