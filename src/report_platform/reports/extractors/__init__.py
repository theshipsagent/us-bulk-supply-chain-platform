"""Extractor registry — maps extractor names to classes."""

import logging
from typing import Any

from report_platform.reports.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

# Lazy registry: name -> module.ClassName
_EXTRACTOR_MAP: dict[str, tuple[str, str]] = {
    "barge": ("report_platform.reports.extractors.barge_extractor", "BargeExtractor"),
    "rail": ("report_platform.reports.extractors.rail_extractor", "RailExtractor"),
    "facility": ("report_platform.reports.extractors.facility_extractor", "FacilityExtractor"),
    "policy": ("report_platform.reports.extractors.policy_extractor", "PolicyExtractor"),
    "port": ("report_platform.reports.extractors.port_extractor", "PortExtractor"),
    "vessel": ("report_platform.reports.extractors.vessel_extractor", "VesselExtractor"),
    "commodity": ("report_platform.reports.extractors.commodity_extractor", "CommodityExtractor"),
}


def get_extractor(name: str) -> BaseExtractor:
    """Get an extractor instance by name."""
    if name not in _EXTRACTOR_MAP:
        raise ValueError(f"Unknown extractor: {name!r}. Available: {list(_EXTRACTOR_MAP)}")

    module_path, class_name = _EXTRACTOR_MAP[name]
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


def run_extractors(extractor_names: list[str]) -> dict[str, Any]:
    """Run multiple extractors and merge their data contexts.

    Each extractor returns a dict. All dicts are merged into one flat namespace.
    If an extractor fails, its data is skipped with a warning.
    """
    context: dict[str, Any] = {}

    for name in extractor_names:
        try:
            extractor = get_extractor(name)
            data = extractor.extract()
            context.update(data)
            logger.info("Extractor '%s' returned %d keys", name, len(data))
        except Exception as e:
            logger.warning("Extractor '%s' failed: %s — skipping", name, e)

    return context
