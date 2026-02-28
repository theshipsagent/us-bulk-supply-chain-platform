"""Base connector interface and SourceRecord dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceRecord:
    """Normalized record from any upstream source.

    Every connector emits these so the matching engine has
    a uniform interface regardless of origin.
    """
    source_system: str          # e.g. 'steel_csv', 'aluminum_csv', 'epa_frs'
    source_record_id: str       # original PK in the source
    name: str
    city: str = ""
    state: str = ""
    county: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parent_company: str = ""
    facility_types: str = ""    # comma-separated
    naics_codes: str = ""       # comma-separated
    sic_codes: str = ""
    commodity_sector: str = ""
    capacity_kt_year: Optional[float] = None
    rail_served: bool = False
    barge_access: bool = False
    water_access: bool = False
    port_adjacent: bool = False
    status: str = "active"
    raw_attributes: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract base for all source connectors."""

    @abstractmethod
    def source_system_name(self) -> str:
        """Return canonical source system identifier."""
        ...

    @abstractmethod
    def fetch_records(self, **filters) -> list[SourceRecord]:
        """Return all records from this source, optionally filtered."""
        ...
