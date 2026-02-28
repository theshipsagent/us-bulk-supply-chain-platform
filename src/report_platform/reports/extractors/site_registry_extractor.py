"""Report extractor for the Site Master Registry.

Provides template variables for report chapters:
  - site_registry_summary: total sites, rail/water counts, multimodal
  - site_registry_sectors: sector breakdown with logistics flags
  - site_registry_top_multimodal: top 20 sites with both rail + water
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class SiteRegistryExtractor(BaseExtractor):

    @property
    def name(self) -> str:
        return "site_registry"

    def extract(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        root = get_project_root()

        db_path = root / "02_TOOLSETS" / "site_master_registry" / "data" / "site_master.duckdb"
        if not db_path.exists():
            logger.warning("site_master.duckdb not found — run build first")
            data["site_registry_loaded"] = False
            return data

        # Add toolset to path
        toolset_path = str(root / "02_TOOLSETS" / "site_master_registry")
        if toolset_path not in sys.path:
            sys.path.insert(0, toolset_path)

        from src.query import SiteRegistryQuery

        query = SiteRegistryQuery(str(db_path))

        try:
            summary = query.summary()
            data["site_registry_summary"] = summary

            # Sector details
            sectors = []
            for sector_name, count in summary.get("sectors", {}).items():
                detail = query.sector_summary(sector_name)
                sectors.append(detail)
            data["site_registry_sectors"] = sectors

            # Top multimodal sites (both rail + water)
            multimodal = query.search(rail_served=True, water_access=True, limit=20)
            data["site_registry_top_multimodal"] = multimodal

            data["site_registry_loaded"] = True
        except Exception as e:
            logger.warning("Site registry extraction failed: %s", e)
            data["site_registry_loaded"] = False
        finally:
            query.close()

        return data
