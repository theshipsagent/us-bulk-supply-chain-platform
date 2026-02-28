"""Mississippi River pilotage cost calculator.

Models the multi-association pilotage system on the Lower Mississippi River
and other US Gulf/Atlantic pilot jurisdictions. Pilotage in the US is
compulsory for foreign-flag vessels and is regulated at the state level.

Key associations modeled:
- Associated Branch Pilots (Bar to Head of Passes)
- Crescent River Port Pilots (Head of Passes to New Orleans)
- New Orleans–Baton Rouge Steamship Pilots (NOLA to Baton Rouge)
- Associated Federal Pilots (Lake Charles, other federal channels)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PilotageZone:
    """A pilotage jurisdiction zone."""
    zone_id: str
    name: str
    association: str
    base_rate_per_foot: float          # $/foot of draft
    min_charge: float = 0.0
    surcharge_pct: float = 0.0         # fuel/general surcharge %
    detention_rate_per_hour: float = 0.0
    cancellation_fee: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# Reference rate data (approximate 2024/2025 tariff card rates)
# ---------------------------------------------------------------------------

PILOTAGE_ZONES: dict[str, PilotageZone] = {
    "bar_to_hop": PilotageZone(
        zone_id="bar_to_hop",
        name="Bar to Head of Passes",
        association="Associated Branch Pilots",
        base_rate_per_foot=135.0,
        min_charge=3_800.0,
        surcharge_pct=15.0,
        detention_rate_per_hour=450.0,
        cancellation_fee=2_500.0,
    ),
    "hop_to_nola": PilotageZone(
        zone_id="hop_to_nola",
        name="Head of Passes to New Orleans",
        association="Crescent River Port Pilots",
        base_rate_per_foot=155.0,
        min_charge=4_200.0,
        surcharge_pct=12.0,
        detention_rate_per_hour=500.0,
        cancellation_fee=2_800.0,
    ),
    "nola_to_br": PilotageZone(
        zone_id="nola_to_br",
        name="New Orleans to Baton Rouge",
        association="New Orleans-Baton Rouge Steamship Pilots",
        base_rate_per_foot=165.0,
        min_charge=4_500.0,
        surcharge_pct=10.0,
        detention_rate_per_hour=525.0,
        cancellation_fee=3_000.0,
    ),
    "br_to_plantation": PilotageZone(
        zone_id="br_to_plantation",
        name="Baton Rouge to Plantation (above BR)",
        association="New Orleans-Baton Rouge Steamship Pilots",
        base_rate_per_foot=180.0,
        min_charge=4_800.0,
        surcharge_pct=10.0,
        detention_rate_per_hour=550.0,
    ),
    "lake_charles": PilotageZone(
        zone_id="lake_charles",
        name="Lake Charles Ship Channel",
        association="Lake Charles Pilots",
        base_rate_per_foot=110.0,
        min_charge=3_200.0,
        surcharge_pct=8.0,
        detention_rate_per_hour=400.0,
    ),
    "houston_ship_channel": PilotageZone(
        zone_id="houston_ship_channel",
        name="Houston Ship Channel",
        association="Houston Pilots",
        base_rate_per_foot=125.0,
        min_charge=3_500.0,
        surcharge_pct=10.0,
        detention_rate_per_hour=450.0,
    ),
    "mobile": PilotageZone(
        zone_id="mobile",
        name="Mobile Bay and Ship Channel",
        association="Mobile Bar Pilots",
        base_rate_per_foot=100.0,
        min_charge=2_800.0,
        surcharge_pct=8.0,
        detention_rate_per_hour=350.0,
    ),
    "tampa": PilotageZone(
        zone_id="tampa",
        name="Tampa Bay",
        association="Tampa Bay Pilots",
        base_rate_per_foot=95.0,
        min_charge=2_600.0,
        surcharge_pct=7.0,
        detention_rate_per_hour=325.0,
    ),
    "norfolk": PilotageZone(
        zone_id="norfolk",
        name="Hampton Roads / Norfolk",
        association="Virginia Pilots Association",
        base_rate_per_foot=90.0,
        min_charge=2_500.0,
        surcharge_pct=6.0,
        detention_rate_per_hour=300.0,
    ),
}


# ---------------------------------------------------------------------------
# Common Lower Mississippi route templates
# ---------------------------------------------------------------------------

ROUTE_TEMPLATES: dict[str, list[str]] = {
    "sea_to_nola": ["bar_to_hop", "hop_to_nola"],
    "sea_to_br": ["bar_to_hop", "hop_to_nola", "nola_to_br"],
    "sea_to_above_br": ["bar_to_hop", "hop_to_nola", "nola_to_br", "br_to_plantation"],
    "nola_to_br": ["nola_to_br"],
    "sea_to_houston": ["houston_ship_channel"],
    "sea_to_lake_charles": ["lake_charles"],
    "sea_to_mobile": ["mobile"],
    "sea_to_tampa": ["tampa"],
    "sea_to_norfolk": ["norfolk"],
}


@dataclass
class PilotageCharge:
    """Itemised pilotage charge for a single zone transit."""
    zone: PilotageZone
    draft_feet: float
    gross_charge: float
    surcharge: float
    total: float
    detention_hours: float = 0.0
    detention_charge: float = 0.0


@dataclass
class PilotageEstimate:
    """Full pilotage estimate across all zones for a voyage."""
    route_name: str
    vessel_draft_feet: float
    zone_charges: list[PilotageCharge] = field(default_factory=list)
    total_pilotage: float = 0.0
    direction: str = "inbound"  # inbound / outbound / both


def calculate_zone_pilotage(
    zone: PilotageZone,
    draft_feet: float,
    detention_hours: float = 0.0,
) -> PilotageCharge:
    """Calculate pilotage cost for a single zone."""
    gross = max(zone.base_rate_per_foot * draft_feet, zone.min_charge)
    surcharge = gross * (zone.surcharge_pct / 100.0)
    detention = detention_hours * zone.detention_rate_per_hour
    total = gross + surcharge + detention
    return PilotageCharge(
        zone=zone,
        draft_feet=draft_feet,
        gross_charge=round(gross, 2),
        surcharge=round(surcharge, 2),
        total=round(total, 2),
        detention_hours=detention_hours,
        detention_charge=round(detention, 2),
    )


def calculate_route_pilotage(
    route_name: str,
    draft_feet: float,
    direction: str = "both",
    detention_hours_per_zone: float = 0.0,
) -> PilotageEstimate:
    """Calculate total pilotage for a named route.

    Parameters
    ----------
    route_name : str
        Key from ``ROUTE_TEMPLATES`` or a comma-separated list of zone IDs.
    draft_feet : float
        Maximum vessel draft in feet.
    direction : str
        ``"inbound"``, ``"outbound"``, or ``"both"`` (doubles the charge).
    detention_hours_per_zone : float
        Pilot detention hours per zone (waiting time).
    """
    if route_name in ROUTE_TEMPLATES:
        zone_ids = ROUTE_TEMPLATES[route_name]
    else:
        zone_ids = [z.strip() for z in route_name.split(",")]

    multiplier = 2.0 if direction == "both" else 1.0
    charges: list[PilotageCharge] = []
    total = 0.0

    for zid in zone_ids:
        zone = PILOTAGE_ZONES.get(zid)
        if zone is None:
            continue
        charge = calculate_zone_pilotage(zone, draft_feet, detention_hours_per_zone)
        charges.append(charge)
        total += charge.total

    total *= multiplier

    return PilotageEstimate(
        route_name=route_name,
        vessel_draft_feet=draft_feet,
        zone_charges=charges,
        total_pilotage=round(total, 2),
        direction=direction,
    )


def list_zones() -> list[dict[str, Any]]:
    """Return all pilotage zones as dicts."""
    return [
        {
            "zone_id": z.zone_id,
            "name": z.name,
            "association": z.association,
            "rate_per_foot": z.base_rate_per_foot,
            "min_charge": z.min_charge,
            "surcharge_pct": z.surcharge_pct,
        }
        for z in PILOTAGE_ZONES.values()
    ]


def list_routes() -> list[dict[str, Any]]:
    """Return all route templates as dicts."""
    return [
        {"route": name, "zones": zones}
        for name, zones in ROUTE_TEMPLATES.items()
    ]
