"""Jones Act (Merchant Marine Act of 1920) analysis engine.

The Jones Act requires that goods shipped between US ports be
transported on vessels that are:
  1. US-built
  2. US-owned
  3. US-flagged
  4. US-crewed

This module analyses the impact on domestic shipping costs, fleet
availability, and competitive dynamics for bulk commodity transport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JonesActVessel:
    """A Jones Act qualified vessel."""
    vessel_name: str
    vessel_type: str            # barge, tanker, container, tug, bulker
    dwt: int = 0
    year_built: int = 0
    owner: str = ""
    operator: str = ""
    flag: str = "US"
    trade_route: str = ""       # typical route
    cargo_capacity_tons: float = 0.0


# ---------------------------------------------------------------------------
# US domestic fleet summary data (MARAD / USCG registry based)
# ---------------------------------------------------------------------------

US_DOMESTIC_FLEET: dict[str, dict[str, Any]] = {
    "inland_barges": {
        "count": 27_000,
        "avg_capacity_tons": 1_500,
        "primary_cargoes": ["coal", "grain", "petroleum", "chemicals", "aggregates", "cement"],
        "operating_regions": ["Mississippi River System", "Ohio River", "Gulf ICW"],
        "avg_age_years": 18,
    },
    "coastal_tankers": {
        "count": 95,
        "avg_capacity_dwt": 42_000,
        "primary_cargoes": ["crude_oil", "refined_products", "chemicals"],
        "operating_regions": ["Gulf Coast", "Atlantic Coast", "Pacific Coast"],
        "avg_age_years": 12,
    },
    "ocean_bulkers": {
        "count": 5,
        "avg_capacity_dwt": 35_000,
        "primary_cargoes": ["grain", "coal", "aggregates"],
        "operating_regions": ["Hawaii", "Puerto Rico", "Alaska"],
        "notes": "Very limited fleet — major constraint for Jones Act bulk",
    },
    "container_ships": {
        "count": 65,
        "avg_capacity_teu": 2_800,
        "primary_cargoes": ["containers"],
        "operating_regions": ["Hawaii", "Puerto Rico", "Alaska", "Guam"],
        "avg_age_years": 15,
    },
    "tugs_towboats": {
        "count": 5_200,
        "avg_hp": 3_500,
        "operating_regions": ["Mississippi River System", "coastal", "harbour"],
    },
}


@dataclass
class JonesActCostAnalysis:
    """Cost comparison: Jones Act domestic vs. foreign-flag hypothetical."""
    route: str
    commodity: str
    cargo_tons: float

    # Jones Act (actual) costs
    ja_vessel_day_rate: float
    ja_transit_days: float
    ja_vessel_cost: float
    ja_fuel_cost: float
    ja_crew_cost: float
    ja_total: float
    ja_per_ton: float

    # Foreign-flag hypothetical
    ff_vessel_day_rate: float
    ff_transit_days: float
    ff_vessel_cost: float
    ff_fuel_cost: float
    ff_crew_cost: float
    ff_total: float
    ff_per_ton: float

    # Premium
    premium_total: float
    premium_per_ton: float
    premium_pct: float


# ---------------------------------------------------------------------------
# Cost benchmarks for domestic vs foreign-flag comparison
# ---------------------------------------------------------------------------

_COST_BENCHMARKS: dict[str, dict[str, float]] = {
    # Jones Act vessel daily costs (higher due to US-build, US-crew requirements)
    "ja_tanker_day_rate": 35_000,
    "ja_bulker_day_rate": 28_000,
    "ja_container_day_rate": 32_000,
    "ja_barge_day_rate": 2_500,  # per barge

    # Foreign-flag equivalent costs
    "ff_tanker_day_rate": 18_000,
    "ff_bulker_day_rate": 14_000,
    "ff_container_day_rate": 16_000,

    # Common parameters
    "fuel_cost_per_day": 8_000,  # approximate
    "ja_crew_cost_per_day": 5_000,
    "ff_crew_cost_per_day": 1_500,
}


def analyze_jones_act_premium(
    route: str,
    commodity: str,
    cargo_tons: float,
    vessel_type: str = "bulker",
    transit_days: float = 5.0,
) -> JonesActCostAnalysis:
    """Calculate the Jones Act cost premium for a domestic voyage.

    Compares actual Jones Act vessel costs to hypothetical foreign-flag costs.

    Parameters
    ----------
    route : str
        Description of the route (e.g., "Houston to Tampa").
    commodity : str
        Cargo type.
    cargo_tons : float
        Cargo quantity in tons.
    vessel_type : str
        "tanker", "bulker", or "container".
    transit_days : float
        One-way transit time in days (round trip = 2x).
    """
    rt_days = transit_days * 2  # round trip

    # Jones Act costs
    ja_day_rate = _COST_BENCHMARKS.get(f"ja_{vessel_type}_day_rate", 28_000)
    ja_vessel = ja_day_rate * rt_days
    ja_fuel = _COST_BENCHMARKS["fuel_cost_per_day"] * rt_days
    ja_crew = _COST_BENCHMARKS["ja_crew_cost_per_day"] * rt_days
    ja_total = ja_vessel + ja_fuel + ja_crew
    ja_per_ton = ja_total / cargo_tons if cargo_tons > 0 else 0

    # Foreign-flag hypothetical
    ff_day_rate = _COST_BENCHMARKS.get(f"ff_{vessel_type}_day_rate", 14_000)
    ff_vessel = ff_day_rate * rt_days
    ff_fuel = _COST_BENCHMARKS["fuel_cost_per_day"] * rt_days
    ff_crew = _COST_BENCHMARKS["ff_crew_cost_per_day"] * rt_days
    ff_total = ff_vessel + ff_fuel + ff_crew
    ff_per_ton = ff_total / cargo_tons if cargo_tons > 0 else 0

    premium_total = ja_total - ff_total
    premium_per_ton = ja_per_ton - ff_per_ton
    premium_pct = (premium_total / ff_total * 100) if ff_total > 0 else 0

    return JonesActCostAnalysis(
        route=route,
        commodity=commodity,
        cargo_tons=cargo_tons,
        ja_vessel_day_rate=ja_day_rate,
        ja_transit_days=rt_days,
        ja_vessel_cost=round(ja_vessel, 2),
        ja_fuel_cost=round(ja_fuel, 2),
        ja_crew_cost=round(ja_crew, 2),
        ja_total=round(ja_total, 2),
        ja_per_ton=round(ja_per_ton, 2),
        ff_vessel_day_rate=ff_day_rate,
        ff_transit_days=rt_days,
        ff_vessel_cost=round(ff_vessel, 2),
        ff_fuel_cost=round(ff_fuel, 2),
        ff_crew_cost=round(ff_crew, 2),
        ff_total=round(ff_total, 2),
        ff_per_ton=round(ff_per_ton, 2),
        premium_total=round(premium_total, 2),
        premium_per_ton=round(premium_per_ton, 2),
        premium_pct=round(premium_pct, 1),
    )


def check_jones_act_applicability(
    origin_port: str,
    destination_port: str,
    is_origin_us: bool = True,
    is_destination_us: bool = True,
) -> dict[str, Any]:
    """Determine if a shipment falls under Jones Act requirements."""
    applies = is_origin_us and is_destination_us

    return {
        "origin": origin_port,
        "destination": destination_port,
        "jones_act_applies": applies,
        "reason": (
            "Both ports are US domestic — Jones Act requires US-built, "
            "US-flagged, US-owned, US-crewed vessel."
            if applies
            else "International voyage — Jones Act does not apply."
        ),
        "exemptions_to_check": [
            "US territory (Puerto Rico, USVI, Guam) — JA applies",
            "Non-contiguous states (Hawaii, Alaska) — JA applies",
            "Foreign Trade Zone cargo — may be exempt",
            "Military/government cargo — may have waiver",
        ] if applies else [],
    }


def get_fleet_summary() -> dict[str, Any]:
    """Return the US domestic Jones Act fleet summary."""
    return US_DOMESTIC_FLEET
