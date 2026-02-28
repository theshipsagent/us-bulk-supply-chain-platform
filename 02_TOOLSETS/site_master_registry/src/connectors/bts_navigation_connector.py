"""Connector for BTS Navigation Facilities (docks, locks, ports).

Reads the BTS docks CSV (29,644 records with lat/lon).
Matching to master_sites is by spatial proximity.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from .base_connector import BaseConnector, SourceRecord

logger = logging.getLogger(__name__)

BTS_DOCKS_CSV = (
    "01_DATA_SOURCES/geospatial/base_layers"
    "/05_bts_navigation_fac/Docks_8605051818000540974.csv"
)


def _parse_float(val: str) -> Optional[float]:
    if not val or val.strip() == "":
        return None
    try:
        return float(val.strip())
    except ValueError:
        return None


class BtsNavigationConnector(BaseConnector):
    """Read BTS docks/navigation facility data."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def source_system_name(self) -> str:
        return "bts_navigation"

    def fetch_records(self, **filters) -> list[SourceRecord]:
        if not self.csv_path.exists():
            logger.warning(f"BTS CSV not found: {self.csv_path}")
            return []

        fac_types = filters.get("fac_types")  # e.g. {"Dock", "Lock"}

        records: list[SourceRecord] = []
        with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = self._row_to_record(row)
                if rec is None:
                    continue
                if fac_types and rec.raw_attributes.get("fac_type") not in fac_types:
                    continue
                records.append(rec)

        logger.info(f"[bts_navigation] Loaded {len(records)} records from {self.csv_path.name}")
        return records

    @staticmethod
    def _row_to_record(row: dict) -> Optional[SourceRecord]:
        name = (row.get("NAV_UNIT_NAME") or "").strip()
        state = (row.get("STATE") or "").strip().upper()
        if not name or not state:
            return None

        lat = _parse_float(row.get("LATITUDE", ""))
        lon = _parse_float(row.get("LONGITUDE", ""))
        if lat is None or lon is None:
            return None

        obj_id = (row.get("\ufeffObjectID") or row.get("ObjectID") or "").strip()
        nav_id = (row.get("NAV_UNIT_ID") or "").strip()
        source_id = nav_id or obj_id or f"bts_{name}_{state}"

        fac_type = (row.get("FAC_TYPE") or "").strip()
        has_rail = bool(row.get("RAILWAY_NOTE", "").strip())

        raw = {
            "fac_type": fac_type,
            "nav_unit_id": nav_id,
            "unlocode": (row.get("UNLOCODE") or "").strip(),
            "waterway_name": (row.get("WTWY_NAME") or "").strip(),
            "port_name": (row.get("PORT_NAME") or "").strip(),
            "commodities": (row.get("COMMODITIES") or "").strip(),
            "operators": (row.get("OPERATORS") or "").strip(),
            "owners": (row.get("OWNERS") or "").strip(),
            "purpose": (row.get("PURPOSE") or "").strip(),
            "railway_note": (row.get("RAILWAY_NOTE") or "").strip(),
        }

        return SourceRecord(
            source_system="bts_navigation",
            source_record_id=source_id,
            name=name,
            city=(row.get("CITY_OR_TOWN") or "").strip(),
            state=state,
            county=(row.get("COUNTY_NAME") or "").strip(),
            latitude=lat,
            longitude=lon,
            water_access=True,
            barge_access=True,
            port_adjacent=(fac_type.lower() in ("dock", "port", "terminal")),
            rail_served=has_rail,
            facility_types=fac_type,
            raw_attributes={k: v for k, v in raw.items() if v},
        )
