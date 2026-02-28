"""Vessel intelligence data extractor — trade flow statistics."""

import logging
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class VesselExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "vessel"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()

        # Check for Panjiva DuckDB
        panjiva_dbs = list(
            (root / "01_DATA_SOURCES" / "federal_trade").rglob("*.duckdb")
        ) + list(
            (root / "02_TOOLSETS" / "vessel_intelligence").rglob("*.duckdb")
        )

        if not panjiva_dbs:
            logger.info("No vessel intelligence DuckDB found — skipping")
            data["vessel_data_loaded"] = False
            return data

        try:
            import duckdb
            db_path = panjiva_dbs[0]
            conn = duckdb.connect(str(db_path), read_only=True)

            # Get table names to determine what's available
            tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

            if tables:
                data["vessel_db_tables"] = tables
                data["vessel_db_path"] = str(db_path)
                data["vessel_data_loaded"] = True

                # Try to get record count from first table
                for table in tables:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()
                        data[f"vessel_{table}_count"] = count[0] if count else 0
                    except Exception:
                        pass
            else:
                data["vessel_data_loaded"] = False

            conn.close()

        except ImportError:
            data["vessel_data_loaded"] = False
        except Exception as e:
            logger.warning("Vessel extractor error: %s", e)
            data["vessel_data_loaded"] = False

        return data
