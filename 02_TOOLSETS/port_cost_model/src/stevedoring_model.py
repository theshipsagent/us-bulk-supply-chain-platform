"""Stevedoring and cargo handling cost model.

Models the cost of loading/discharging cargo at US port terminals.
Rates depend on cargo type, handling method, and commodity-specific
equipment requirements.

Key cost drivers:
- Cargo type (bulk, breakbulk, containerised, liquid)
- Handling method (crane, conveyor, pneumatic, grab)
- Discharge/loading rate (tons per hour)
- Labour hours (gang size x hours)
- Equipment rental (cranes, forklifts, bobcats)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StevedoringRate:
    """Rate structure for a specific cargo/handling combination."""
    cargo_type: str
    handling_method: str
    rate_per_ton: float                 # $/short ton for stevedoring labour
    equipment_per_hour: float = 0.0     # crane/equipment hire $/hr
    discharge_rate_tph: float = 500.0   # tons per hour (typical throughput)
    min_charge: float = 0.0
    overtime_pct: float = 50.0          # OT surcharge percentage
    notes: str = ""


# ---------------------------------------------------------------------------
# Reference stevedoring rates (approximate 2024/2025 Gulf Coast)
# ---------------------------------------------------------------------------

STEVEDORING_RATES: dict[str, StevedoringRate] = {
    # Dry bulk
    "cement_pneumatic": StevedoringRate(
        cargo_type="cement",
        handling_method="pneumatic",
        rate_per_ton=3.50,
        equipment_per_hour=350.0,
        discharge_rate_tph=400,
        notes="Pneumatic unloader to silo, cement-specific",
    ),
    "cement_grab": StevedoringRate(
        cargo_type="cement",
        handling_method="grab_crane",
        rate_per_ton=4.25,
        equipment_per_hour=500.0,
        discharge_rate_tph=300,
        notes="Grab crane to hopper, then conveyor to silo",
    ),
    "grain_elevator": StevedoringRate(
        cargo_type="grain",
        handling_method="elevator",
        rate_per_ton=2.50,
        equipment_per_hour=200.0,
        discharge_rate_tph=1_500,
        notes="Grain elevator loading, high throughput",
    ),
    "coal_grab": StevedoringRate(
        cargo_type="coal",
        handling_method="grab_crane",
        rate_per_ton=3.00,
        equipment_per_hour=450.0,
        discharge_rate_tph=800,
    ),
    "bulk_dry_general": StevedoringRate(
        cargo_type="bulk_dry",
        handling_method="grab_crane",
        rate_per_ton=4.00,
        equipment_per_hour=500.0,
        discharge_rate_tph=400,
    ),
    # Breakbulk
    "steel_coils": StevedoringRate(
        cargo_type="steel",
        handling_method="shore_crane",
        rate_per_ton=8.50,
        equipment_per_hour=650.0,
        discharge_rate_tph=150,
        notes="Coil cradles, shore crane discharge",
    ),
    "steel_plate": StevedoringRate(
        cargo_type="steel",
        handling_method="shore_crane",
        rate_per_ton=7.50,
        equipment_per_hour=600.0,
        discharge_rate_tph=180,
    ),
    "breakbulk_general": StevedoringRate(
        cargo_type="breakbulk",
        handling_method="ship_gear",
        rate_per_ton=9.00,
        equipment_per_hour=400.0,
        discharge_rate_tph=120,
        notes="Ship's gear or mobile crane, general breakbulk",
    ),
    "project_cargo": StevedoringRate(
        cargo_type="project",
        handling_method="heavy_lift",
        rate_per_ton=15.00,
        equipment_per_hour=1_200.0,
        discharge_rate_tph=50,
        notes="Heavy lift crane, engineered rigging plans",
    ),
    # Liquid bulk
    "liquid_bulk": StevedoringRate(
        cargo_type="liquid",
        handling_method="pipeline",
        rate_per_ton=1.80,
        equipment_per_hour=0.0,
        discharge_rate_tph=1_000,
        notes="Shore manifold connection, pumping charges separate",
    ),
    # Containers (per TEU basis converted to per-ton estimate)
    "containers": StevedoringRate(
        cargo_type="containers",
        handling_method="gantry_crane",
        rate_per_ton=12.00,
        equipment_per_hour=800.0,
        discharge_rate_tph=200,
        notes="Container rate ~$200/TEU, assumes ~16 tons/TEU",
    ),
}


@dataclass
class StevedoringEstimate:
    """Itemised stevedoring cost estimate."""
    cargo_type: str
    handling_method: str
    cargo_tons: float
    labour_cost: float
    equipment_cost: float
    overtime_surcharge: float
    total: float
    estimated_hours: float
    rate_per_ton: float
    details: dict[str, Any] = field(default_factory=dict)


def calculate_stevedoring(
    cargo_type: str,
    cargo_tons: float,
    handling_method: str | None = None,
    overtime_hours: float = 0.0,
    custom_rate_per_ton: float | None = None,
) -> StevedoringEstimate:
    """Calculate stevedoring / cargo handling costs.

    Parameters
    ----------
    cargo_type : str
        Cargo type key (e.g. ``"cement"``, ``"steel"``, ``"breakbulk"``).
    cargo_tons : float
        Cargo quantity in short tons.
    handling_method : str, optional
        Specific handling method. If None, picks default for cargo type.
    overtime_hours : float
        Hours of overtime labour (weekend, night, holiday work).
    custom_rate_per_ton : float, optional
        Override the reference rate with a custom $/ton rate.
    """
    # Find matching rate
    rate_obj = _find_rate(cargo_type, handling_method)
    if rate_obj is None:
        available = ", ".join(sorted(STEVEDORING_RATES.keys()))
        raise ValueError(
            f"No stevedoring rate for cargo='{cargo_type}', method='{handling_method}'. "
            f"Available keys: {available}"
        )

    r_per_ton = custom_rate_per_ton if custom_rate_per_ton is not None else rate_obj.rate_per_ton
    estimated_hours = cargo_tons / rate_obj.discharge_rate_tph if rate_obj.discharge_rate_tph > 0 else 0

    labour = r_per_ton * cargo_tons
    labour = max(labour, rate_obj.min_charge)

    equipment = rate_obj.equipment_per_hour * estimated_hours

    ot_surcharge = 0.0
    if overtime_hours > 0:
        ot_hourly_rate = (labour / max(estimated_hours, 1)) * (rate_obj.overtime_pct / 100.0)
        ot_surcharge = ot_hourly_rate * overtime_hours

    total = labour + equipment + ot_surcharge

    return StevedoringEstimate(
        cargo_type=rate_obj.cargo_type,
        handling_method=rate_obj.handling_method,
        cargo_tons=cargo_tons,
        labour_cost=round(labour, 2),
        equipment_cost=round(equipment, 2),
        overtime_surcharge=round(ot_surcharge, 2),
        total=round(total, 2),
        estimated_hours=round(estimated_hours, 1),
        rate_per_ton=r_per_ton,
    )


def _find_rate(cargo_type: str, handling_method: str | None) -> StevedoringRate | None:
    """Find a matching stevedoring rate."""
    cargo_lc = cargo_type.lower()

    # Exact key match
    if handling_method:
        key = f"{cargo_lc}_{handling_method.lower()}"
        if key in STEVEDORING_RATES:
            return STEVEDORING_RATES[key]

    # Find first match for cargo type
    for key, rate in STEVEDORING_RATES.items():
        if rate.cargo_type.lower() == cargo_lc:
            return rate

    # General fallback
    if "bulk_dry_general" in STEVEDORING_RATES:
        return STEVEDORING_RATES["bulk_dry_general"]

    return None


def list_rates() -> list[dict[str, Any]]:
    """Return all stevedoring rates as summary dicts."""
    return [
        {
            "key": key,
            "cargo_type": r.cargo_type,
            "handling_method": r.handling_method,
            "rate_per_ton": r.rate_per_ton,
            "throughput_tph": r.discharge_rate_tph,
        }
        for key, r in sorted(STEVEDORING_RATES.items())
    ]
