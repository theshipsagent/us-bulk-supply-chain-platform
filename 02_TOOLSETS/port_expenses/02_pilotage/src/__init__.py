"""
US Port Pilotage Calculator Package
=====================================
Compulsory pilotage cost estimation for cargo vessel port calls and river transits.

Modules
-------
vessel_resolver     : Local + web lookup chain for vessel parameters (GRT, draft, LOA)
pilotage_calculator : Rate calculation engine — GRT-tier and draft-per-foot rate types

Quick start
-----------
    from pilotage_calculator import calculate_pilotage

    result = calculate_pilotage(
        port="New Orleans",
        vessel_imo="9123456",          # looks up ship register
        route="sea_to_nola",           # Mississippi route template
    )
    print(result.pilotage_total)
"""

from .pilotage_calculator import calculate_pilotage, list_associations, list_routes
from .vessel_resolver import VesselParams, resolve_vessel

__all__ = [
    "calculate_pilotage",
    "list_associations",
    "list_routes",
    "resolve_vessel",
    "VesselParams",
]
