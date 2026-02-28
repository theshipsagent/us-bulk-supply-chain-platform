"""Port authority tariff calculator.

Models dockage, wharfage, and harbour dues charged by port authorities.
US port tariffs are published publicly and vary by vessel size, cargo type,
and duration of berth occupancy.

Dockage: charged per foot of LOA per 24-hour period (vessel occupying berth)
Wharfage: charged per ton of cargo crossing the wharf
Harbour dues: flat or GT-based entry fee
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortTariff:
    """Tariff schedule for a specific port."""
    port: str
    # Dockage (per foot LOA per 24-hr period)
    dockage_rate_per_foot_day: float
    dockage_min_charge: float = 0.0
    # Wharfage (per short ton)
    wharfage_rates: dict[str, float] = field(default_factory=dict)
    wharfage_default: float = 0.0
    # Harbour dues (per GT)
    harbour_dues_per_gt: float = 0.0
    harbour_dues_min: float = 0.0
    # Line handling (per operation)
    line_handling_rate: float = 0.0
    # Fresh water (per ton)
    fresh_water_per_ton: float = 0.0
    # Security surcharge
    security_fee: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# Reference tariffs (approximate 2024/2025 published rates)
# ---------------------------------------------------------------------------

PORT_TARIFFS: dict[str, PortTariff] = {
    "new_orleans": PortTariff(
        port="New Orleans",
        dockage_rate_per_foot_day=9.50,
        dockage_min_charge=1_200.0,
        wharfage_rates={
            "general": 1.85,
            "bulk_dry": 1.25,
            "bulk_liquid": 1.10,
            "cement": 1.25,
            "steel": 2.10,
            "containers": 1.95,
            "breakbulk": 2.00,
            "grain": 0.95,
            "coal": 0.85,
        },
        wharfage_default=1.85,
        harbour_dues_per_gt=0.065,
        harbour_dues_min=500.0,
        line_handling_rate=2_500.0,
        fresh_water_per_ton=18.0,
        security_fee=750.0,
    ),
    "baton_rouge": PortTariff(
        port="Baton Rouge",
        dockage_rate_per_foot_day=8.00,
        dockage_min_charge=1_000.0,
        wharfage_rates={
            "general": 1.65,
            "bulk_dry": 1.10,
            "bulk_liquid": 0.95,
            "cement": 1.10,
            "grain": 0.85,
        },
        wharfage_default=1.65,
        harbour_dues_per_gt=0.055,
        harbour_dues_min=400.0,
        line_handling_rate=2_200.0,
        fresh_water_per_ton=16.0,
        security_fee=600.0,
    ),
    "houston": PortTariff(
        port="Houston",
        dockage_rate_per_foot_day=11.00,
        dockage_min_charge=1_500.0,
        wharfage_rates={
            "general": 2.10,
            "bulk_dry": 1.40,
            "bulk_liquid": 1.25,
            "cement": 1.40,
            "steel": 2.35,
            "containers": 2.20,
            "breakbulk": 2.15,
            "grain": 1.05,
        },
        wharfage_default=2.10,
        harbour_dues_per_gt=0.075,
        harbour_dues_min=600.0,
        line_handling_rate=3_000.0,
        fresh_water_per_ton=20.0,
        security_fee=850.0,
    ),
    "mobile": PortTariff(
        port="Mobile",
        dockage_rate_per_foot_day=7.50,
        dockage_min_charge=900.0,
        wharfage_rates={
            "general": 1.55,
            "bulk_dry": 1.00,
            "bulk_liquid": 0.90,
            "cement": 1.00,
            "steel": 1.80,
            "coal": 0.75,
        },
        wharfage_default=1.55,
        harbour_dues_per_gt=0.050,
        harbour_dues_min=350.0,
        line_handling_rate=2_000.0,
        fresh_water_per_ton=15.0,
        security_fee=500.0,
    ),
    "tampa": PortTariff(
        port="Tampa",
        dockage_rate_per_foot_day=7.00,
        dockage_min_charge=850.0,
        wharfage_rates={
            "general": 1.50,
            "bulk_dry": 0.95,
            "bulk_liquid": 0.85,
            "cement": 0.95,
            "phosphate": 0.80,
        },
        wharfage_default=1.50,
        harbour_dues_per_gt=0.048,
        harbour_dues_min=325.0,
        line_handling_rate=1_800.0,
        fresh_water_per_ton=14.0,
        security_fee=450.0,
    ),
    "norfolk": PortTariff(
        port="Norfolk",
        dockage_rate_per_foot_day=8.50,
        dockage_min_charge=1_100.0,
        wharfage_rates={
            "general": 1.70,
            "bulk_dry": 1.15,
            "bulk_liquid": 1.00,
            "coal": 0.80,
            "containers": 1.90,
        },
        wharfage_default=1.70,
        harbour_dues_per_gt=0.060,
        harbour_dues_min=450.0,
        line_handling_rate=2_400.0,
        fresh_water_per_ton=17.0,
        security_fee=650.0,
    ),
    "lake_charles": PortTariff(
        port="Lake Charles",
        dockage_rate_per_foot_day=7.00,
        dockage_min_charge=850.0,
        wharfage_rates={
            "general": 1.45,
            "bulk_dry": 0.90,
            "bulk_liquid": 0.80,
            "cement": 0.90,
        },
        wharfage_default=1.45,
        harbour_dues_per_gt=0.045,
        harbour_dues_min=300.0,
        line_handling_rate=1_800.0,
        fresh_water_per_ton=14.0,
        security_fee=450.0,
    ),
    "memphis": PortTariff(
        port="Memphis",
        dockage_rate_per_foot_day=6.00,
        dockage_min_charge=700.0,
        wharfage_rates={
            "general": 1.30,
            "bulk_dry": 0.80,
            "cement": 0.80,
            "steel": 1.50,
        },
        wharfage_default=1.30,
        harbour_dues_per_gt=0.040,
        harbour_dues_min=250.0,
        line_handling_rate=1_500.0,
        fresh_water_per_ton=12.0,
        security_fee=350.0,
    ),
}


@dataclass
class PortCharges:
    """Itemised port authority charges."""
    port: str
    dockage: float
    wharfage: float
    harbour_dues: float
    line_handling: float
    fresh_water: float
    security_fee: float
    total: float
    details: dict[str, Any] = field(default_factory=dict)


def calculate_port_charges(
    port: str,
    vessel_loa_feet: float,
    vessel_gt: int,
    cargo_type: str = "general",
    cargo_tons: float = 0.0,
    days_alongside: float = 1.0,
    fresh_water_tons: float = 0.0,
    line_handling_ops: int = 2,
) -> PortCharges:
    """Calculate port authority charges.

    Parameters
    ----------
    port : str
        Port key from ``PORT_TARIFFS``.
    vessel_loa_feet : float
        Vessel length overall in feet.
    vessel_gt : int
        Gross tonnage.
    cargo_type : str
        Cargo type key for wharfage lookup.
    cargo_tons : float
        Metric tons of cargo loaded/discharged.
    days_alongside : float
        Number of 24-hour periods at berth.
    fresh_water_tons : float
        Fresh water delivered (metric tons).
    line_handling_ops : int
        Number of line handling operations (default 2: arrive + depart).
    """
    port_key = port.lower().replace(" ", "_")
    tariff = PORT_TARIFFS.get(port_key)
    if tariff is None:
        available = ", ".join(sorted(PORT_TARIFFS.keys()))
        raise ValueError(
            f"No tariff data for port='{port}'. Available: {available}"
        )

    import math
    days_ceil = math.ceil(days_alongside)

    dockage = max(
        tariff.dockage_rate_per_foot_day * vessel_loa_feet * days_ceil,
        tariff.dockage_min_charge,
    )

    wharfage_rate = tariff.wharfage_rates.get(
        cargo_type.lower(), tariff.wharfage_default
    )
    wharfage = wharfage_rate * cargo_tons

    harbour = max(
        tariff.harbour_dues_per_gt * vessel_gt,
        tariff.harbour_dues_min,
    )

    line_handling = tariff.line_handling_rate * line_handling_ops
    water = tariff.fresh_water_per_ton * fresh_water_tons
    security = tariff.security_fee

    total = dockage + wharfage + harbour + line_handling + water + security

    return PortCharges(
        port=tariff.port,
        dockage=round(dockage, 2),
        wharfage=round(wharfage, 2),
        harbour_dues=round(harbour, 2),
        line_handling=round(line_handling, 2),
        fresh_water=round(water, 2),
        security_fee=round(security, 2),
        total=round(total, 2),
        details={
            "dockage_rate": tariff.dockage_rate_per_foot_day,
            "wharfage_rate": wharfage_rate,
            "harbour_rate": tariff.harbour_dues_per_gt,
            "days_charged": days_ceil,
            "cargo_type": cargo_type,
        },
    )


def list_ports() -> list[dict[str, Any]]:
    """Return available ports with summary tariff info."""
    return [
        {
            "port_key": key,
            "port_name": t.port,
            "dockage_per_ft_day": t.dockage_rate_per_foot_day,
            "wharfage_default": t.wharfage_default,
            "harbour_per_gt": t.harbour_dues_per_gt,
            "cargo_types": list(t.wharfage_rates.keys()),
        }
        for key, t in sorted(PORT_TARIFFS.items())
    ]
