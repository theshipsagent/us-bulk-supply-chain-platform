"""
Pydantic data models for the Interactive Barge Dashboard.

This package contains type-safe models for all database entities and business logic.
"""

from src.models.waterway import (
    WaterwayLink,
    WaterwayNode,
    Lock,
    Dock,
)

from src.models.cargo import (
    LinkTonnage,
    CommodityType,
    COMMODITY_TYPES,
)

from src.models.vessel import (
    Vessel,
    VesselType,
    VESSEL_TYPES,
)

from src.models.route import (
    RouteSegment,
    RouteCost,
    RouteConstraints,
    ComputedRoute,
    RouteRequest,
    RouteComparison,
)

__all__ = [
    # Waterway models
    'WaterwayLink',
    'WaterwayNode',
    'Lock',
    'Dock',

    # Cargo models
    'LinkTonnage',
    'CommodityType',
    'COMMODITY_TYPES',

    # Vessel models
    'Vessel',
    'VesselType',
    'VESSEL_TYPES',

    # Route models
    'RouteSegment',
    'RouteCost',
    'RouteConstraints',
    'ComputedRoute',
    'RouteRequest',
    'RouteComparison',
]
