"""Connector for SCRS (Switching and Reciprocal Switching) rail facility data.

Reads the integration-ready CSV (bulk commodity subset, 8,555 records).
SCRS has no coordinates — matching is by facility name + city + state.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .base_connector import BaseConnector, SourceRecord

logger = logging.getLogger(__name__)

SCRS_CSV = (
    "01_DATA_SOURCES/federal_rail/stb_economic_data"
    "/integrated/scrs_integration_ready.csv"
)


class ScrsConnector(BaseConnector):
    """Read SCRS rail facility data."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def source_system_name(self) -> str:
        return "scrs_rail"

    def fetch_records(self, **filters) -> list[SourceRecord]:
        if not self.csv_path.exists():
            logger.warning(f"SCRS CSV not found: {self.csv_path}")
            return []

        records: list[SourceRecord] = []
        with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = self._row_to_record(row)
                if rec:
                    records.append(rec)

        logger.info(f"[scrs_rail] Loaded {len(records)} records from {self.csv_path.name}")
        return records

    def fetch_indexed_by_state_city(self) -> dict[str, list[SourceRecord]]:
        """Return records indexed by 'STATE:CITY' for fast lookup."""
        records = self.fetch_records()
        index: dict[str, list[SourceRecord]] = defaultdict(list)
        for rec in records:
            key = f"{rec.state}:{rec.city}".upper()
            index[key].append(rec)
        return index

    @staticmethod
    def _row_to_record(row: dict) -> Optional[SourceRecord]:
        name = (row.get("FACILITY_NAME") or "").strip()
        state = (row.get("STATE") or "").strip().upper()
        if not name or not state:
            return None

        city = (row.get("CITY") or "").strip()
        carrier = (row.get("SERVING_CARRIER") or "").strip()
        status = (row.get("SWITCHING_STATUS") or "").strip()
        source_id = (row.get("SOURCE_ID") or row.get("CIF_NUMBER") or "").strip()

        raw = {
            "serving_carrier": carrier,
            "switching_status": status,
            "station_name": (row.get("STATION_NAME") or "").strip(),
            "commodity_focus": (row.get("COMMODITY_FOCUS") or "").strip(),
            "parent_company": (row.get("PARENT_COMPANY") or "").strip(),
            "full_address": (row.get("FULL_ADDRESS") or "").strip(),
        }

        return SourceRecord(
            source_system="scrs_rail",
            source_record_id=source_id or f"scrs_{name}_{state}",
            name=name,
            city=city,
            state=state,
            parent_company=(row.get("PARENT_COMPANY") or "").strip(),
            rail_served=True,  # All SCRS facilities are rail-served by definition
            naics_codes=(row.get("NAICS") or "").strip(),
            commodity_sector=(row.get("COMMODITY_FOCUS") or "").strip().lower(),
            raw_attributes={k: v for k, v in raw.items() if v},
        )
