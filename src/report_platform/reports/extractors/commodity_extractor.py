"""Commodity module data extractor — pulls from commodity-specific databases."""

import logging
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class CommodityExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "commodity"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()
        modules_dir = root / "03_COMMODITY_MODULES"

        if not modules_dir.exists():
            data["commodity_data_loaded"] = False
            return data

        # Discover active commodity modules
        active_modules = []
        for mod_dir in sorted(modules_dir.iterdir()):
            if mod_dir.is_dir() and not mod_dir.name.startswith("."):
                config_file = mod_dir / "config.yaml"
                if config_file.exists() or any(mod_dir.rglob("*.duckdb")):
                    active_modules.append(mod_dir.name)

        data["commodity_active_modules"] = active_modules

        # Cement-specific data (primary commodity module)
        cement_dir = modules_dir / "cement"
        if cement_dir.exists():
            data.update(self._extract_cement(cement_dir))

        data["commodity_data_loaded"] = bool(active_modules)
        return data

    def _extract_cement(self, cement_dir) -> dict[str, Any]:
        """Extract cement module data."""
        data: dict[str, Any] = {}

        # Look for DuckDB databases in cement module
        duckdb_files = list(cement_dir.rglob("*.duckdb"))
        if not duckdb_files:
            logger.info("No cement DuckDB found")
            return data

        try:
            import duckdb

            for db_path in duckdb_files:
                try:
                    conn = duckdb.connect(str(db_path), read_only=True)
                    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

                    for table in tables:
                        count = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()
                        data[f"cement_{table}_count"] = count[0] if count else 0

                    data["cement_db_tables"] = tables
                    conn.close()
                except Exception as e:
                    logger.debug("Cement DB %s error: %s", db_path.name, e)

        except ImportError:
            logger.warning("duckdb not available for cement data")

        # Count report/analysis files
        data["cement_report_count"] = len(list(cement_dir.rglob("*.md")))
        data["cement_data_files"] = len(list(cement_dir.rglob("*.csv"))) + len(list(cement_dir.rglob("*.parquet")))

        return data
