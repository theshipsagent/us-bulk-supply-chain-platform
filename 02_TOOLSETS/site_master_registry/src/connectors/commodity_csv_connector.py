"""Connector for commodity module CSV files (steel, aluminum, copper).

Reads curated facility CSVs from 03_COMMODITY_MODULES/ and emits
SourceRecord objects with normalized fields.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from .base_connector import BaseConnector, SourceRecord

logger = logging.getLogger(__name__)

# Column mappings per commodity — maps CSV column name to SourceRecord field
_COMMON_FIELDS = {
    "name": "name",
    "company": "parent_company",
    "city": "city",
    "state": "state",
    "lat": "latitude",
    "lon": "longitude",
    "facility_types": "facility_types",
    "port_adjacent": "port_adjacent",
    "rail_served": "rail_served",
    "barge_access": "barge_access",
    "water_access": "water_access",
    "status": "status",
}

# Capacity column varies
_CAPACITY_COLS = {"capacity_kt_year", "capacity_kt"}


def _parse_bool(val: str) -> bool:
    """Parse CSV boolean — handles TRUE/FALSE/Yes/No/1/0/empty."""
    if not val:
        return False
    return val.strip().upper() in ("TRUE", "YES", "1", "Y")


def _parse_float(val: str) -> Optional[float]:
    if not val or val.strip() == "":
        return None
    try:
        return float(val.strip())
    except ValueError:
        return None


class CommodityCsvConnector(BaseConnector):
    """Read a single commodity CSV and yield SourceRecords."""

    def __init__(self, csv_path: str, commodity_sector: str, naics_prefixes: list[str]):
        self.csv_path = Path(csv_path)
        self.commodity_sector = commodity_sector
        self.naics_prefixes = naics_prefixes
        self._system_name = f"{commodity_sector}_csv"

    def source_system_name(self) -> str:
        return self._system_name

    def fetch_records(self, **filters) -> list[SourceRecord]:
        if not self.csv_path.exists():
            logger.warning(f"CSV not found: {self.csv_path}")
            return []

        records: list[SourceRecord] = []
        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                rec = self._row_to_record(row, idx)
                if rec:
                    records.append(rec)

        logger.info(f"[{self._system_name}] Loaded {len(records)} records from {self.csv_path.name}")
        return records

    def _row_to_record(self, row: dict, idx: int) -> Optional[SourceRecord]:
        name = (row.get("name") or "").strip()
        if not name:
            return None

        state = (row.get("state") or "").strip().upper()
        if not state:
            return None

        # Parse capacity — try both column name variants
        capacity = None
        for col in _CAPACITY_COLS:
            if col in row:
                capacity = _parse_float(row[col])
                break

        # Build a stable record ID: {sector}_{index}_{state}
        record_id = f"{self.commodity_sector}_{idx:04d}_{state}"

        # Collect all raw attributes for provenance
        raw_attrs = {k: v for k, v in row.items() if v}

        return SourceRecord(
            source_system=self._system_name,
            source_record_id=record_id,
            name=name,
            city=(row.get("city") or "").strip(),
            state=state,
            latitude=_parse_float(row.get("lat", "")),
            longitude=_parse_float(row.get("lon", "")),
            parent_company=(row.get("company") or "").strip(),
            facility_types=(row.get("facility_types") or "").strip(),
            naics_codes=",".join(self.naics_prefixes),
            commodity_sector=self.commodity_sector,
            capacity_kt_year=capacity,
            rail_served=_parse_bool(row.get("rail_served", "")),
            barge_access=_parse_bool(row.get("barge_access", "")),
            water_access=_parse_bool(row.get("water_access", "")),
            port_adjacent=_parse_bool(row.get("port_adjacent", "")),
            status=(row.get("status") or "active").strip().lower(),
            raw_attributes=raw_attrs,
        )
