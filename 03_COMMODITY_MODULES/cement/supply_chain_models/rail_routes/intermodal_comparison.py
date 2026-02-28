"""
Intermodal Transportation Comparison for Cement

Compares rail, barge, and truck transportation modes for bulk cement
deliveries across the United States. Provides cost modeling, breakeven
analysis, and optimal mode selection for origin-destination pairs.

Cost basis (2025 benchmarks):
    - Truck:  ~$0.12/ton-mile (25-ton loads, includes driver, fuel, insurance)
    - Rail:   ~$0.035/ton-mile (100-ton cars, unit train rates, includes car hire)
    - Barge:  ~$0.012/ton-mile (1,500-ton barges, 15-barge tow, includes fuel/crew)

These are mid-range estimates. Actual costs vary with fuel prices, distance,
lane density, contract terms, and seasonal factors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Mode cost parameters
# ---------------------------------------------------------------------------

@dataclass
class TruckParams:
    """Cost parameters for truck (pneumatic tanker) cement transport."""
    cost_per_ton_mile: float = 0.12
    fixed_cost_per_load: float = 250.0     # lumper, fuel surcharge base, detention
    capacity_tons: float = 25.0
    avg_speed_mph: float = 45.0
    max_daily_miles: float = 500.0
    loading_time_hours: float = 0.5
    unloading_time_hours: float = 0.75
    driver_hours_per_day: float = 11.0     # HOS regulation

    @property
    def min_loads_for_railcar_equivalent(self) -> int:
        """Number of truck loads to match one railcar (100 tons)."""
        return math.ceil(100.0 / self.capacity_tons)


@dataclass
class RailParams:
    """Cost parameters for rail (covered hopper) cement transport."""
    cost_per_ton_mile: float = 0.035
    fixed_cost_per_car: float = 1200.0     # switching, terminal handling, car hire
    capacity_tons_per_car: float = 100.0
    avg_speed_mph: float = 25.0            # includes dwell time
    min_cars_unit_train: int = 25          # unit train threshold for rate discount
    unit_train_discount_pct: float = 0.15  # discount for unit train vs manifest
    transit_time_base_days: float = 2.0    # base dwell/switching time
    stcc_code: str = "3241110"

    def effective_cost_per_ton_mile(self, cars: int) -> float:
        """Return cost per ton-mile adjusted for unit train discount."""
        if cars >= self.min_cars_unit_train:
            return self.cost_per_ton_mile * (1 - self.unit_train_discount_pct)
        return self.cost_per_ton_mile


@dataclass
class BargeParams:
    """Cost parameters for barge (covered hopper barge) cement transport."""
    cost_per_ton_mile: float = 0.012
    fixed_cost_per_barge: float = 800.0    # fleeting, cleaning, positioning
    capacity_tons_per_barge: float = 1500.0
    max_tow_open_river: int = 15           # 5-wide x 3-long
    max_tow_icw: int = 6                   # 2-wide x 3-long
    max_tow_locked_river: int = 15         # most 1200-ft locks
    avg_speed_upstream_mph: float = 5.0
    avg_speed_downstream_mph: float = 8.0
    lock_delay_hours: float = 4.0          # per lock average
    transit_time_base_days: float = 1.0    # mobilization/demobilization

    def effective_cost_per_ton_mile(self, num_locks: int, distance_miles: float) -> float:
        """Adjust cost per ton-mile for lock delays (adds effective distance)."""
        if distance_miles <= 0:
            return self.cost_per_ton_mile
        # Lock delays add equivalent cost as if traveling extra miles
        lock_delay_equivalent_miles = num_locks * 15  # ~15 miles worth of cost per lock
        effective_distance = distance_miles + lock_delay_equivalent_miles
        return self.cost_per_ton_mile * (effective_distance / distance_miles)


# Default parameter instances
DEFAULT_TRUCK = TruckParams()
DEFAULT_RAIL = RailParams()
DEFAULT_BARGE = BargeParams()


# ---------------------------------------------------------------------------
# Waterway accessibility lookup
# Indicates whether a location has barge access and approximate river mile
# ---------------------------------------------------------------------------
WATERWAY_ACCESS: dict[str, dict] = {
    "new orleans": {"has_barge": True, "river": "Lower Mississippi", "mile": 100},
    "baton rouge": {"has_barge": True, "river": "Lower Mississippi", "mile": 230},
    "memphis": {"has_barge": True, "river": "Lower Mississippi", "mile": 735},
    "st. louis": {"has_barge": True, "river": "Middle Mississippi", "mile": 180},
    "cairo": {"has_barge": True, "river": "Lower Mississippi/Ohio", "mile": 953},
    "cincinnati": {"has_barge": True, "river": "Ohio River", "mile": 470},
    "louisville": {"has_barge": True, "river": "Ohio River", "mile": 607},
    "pittsburgh": {"has_barge": True, "river": "Ohio River", "mile": 0},
    "chicago": {"has_barge": True, "river": "Illinois Waterway", "mile": 327},
    "houston": {"has_barge": True, "river": "GIWW/Ship Channel", "mile": 0},
    "kansas city": {"has_barge": False, "river": "Missouri River (limited)", "mile": 0},
    "dallas": {"has_barge": False, "river": None, "mile": 0},
    "atlanta": {"has_barge": False, "river": None, "mile": 0},
    "denver": {"has_barge": False, "river": None, "mile": 0},
    "los angeles": {"has_barge": False, "river": None, "mile": 0},
    "phoenix": {"has_barge": False, "river": None, "mile": 0},
    "san antonio": {"has_barge": False, "river": None, "mile": 0},
    "indianapolis": {"has_barge": False, "river": None, "mile": 0},
    "milwaukee": {"has_barge": False, "river": None, "mile": 0},
    "nashville": {"has_barge": True, "river": "Cumberland River", "mile": 190},
    "chattanooga": {"has_barge": True, "river": "Tennessee River", "mile": 465},
    "paducah": {"has_barge": True, "river": "Ohio/Tennessee confluence", "mile": 0},
    "peoria": {"has_barge": True, "river": "Illinois River", "mile": 158},
}


# ---------------------------------------------------------------------------
# Distance estimation between common cement origins and destinations
# Uses straight-line distance with road/rail/waterway multipliers
# ---------------------------------------------------------------------------

def _estimate_road_distance(origin: str, destination: str) -> float:
    """Estimate road distance between two locations.

    Uses a simplified lookup of approximate distances. Returns 0 if
    pair is not found (caller should provide explicit distance).
    """
    # Common cement lane distances (approximate road miles)
    _distances: dict[tuple[str, str], float] = {
        ("midlothian", "houston"): 250,
        ("midlothian", "dallas"): 35,
        ("midlothian", "san antonio"): 270,
        ("midlothian", "oklahoma city"): 210,
        ("houston", "dallas"): 240,
        ("houston", "san antonio"): 200,
        ("houston", "memphis"): 560,
        ("new orleans", "memphis"): 390,
        ("new orleans", "baton rouge"): 80,
        ("new orleans", "houston"): 350,
        ("ste. genevieve", "st. louis"): 65,
        ("ste. genevieve", "chicago"): 330,
        ("ste. genevieve", "memphis"): 280,
        ("ste. genevieve", "kansas city"): 300,
        ("ste. genevieve", "indianapolis"): 280,
        ("mitchell", "cincinnati"): 165,
        ("mitchell", "indianapolis"): 85,
        ("lasalle", "chicago"): 95,
        ("lasalle", "milwaukee"): 140,
        ("hagerstown", "washington dc"): 75,
        ("nazareth", "new york"): 90,
        ("holly hill", "atlanta"): 310,
        ("pueblo", "denver"): 110,
        ("roberta", "atlanta"): 155,
        ("tampa", "orlando"): 85,
        ("cairo", "st. louis"): 155,
        ("baton rouge", "memphis"): 375,
    }

    o = origin.lower().strip()
    d = destination.lower().strip()

    # Check both directions
    dist = _distances.get((o, d)) or _distances.get((d, o))
    return dist or 0.0


def compare_modes(
    origin: str,
    destination: str,
    cargo_tons: float,
    road_distance_miles: Optional[float] = None,
    rail_distance_miles: Optional[float] = None,
    barge_distance_miles: Optional[float] = None,
    num_locks: int = 0,
    truck_params: Optional[TruckParams] = None,
    rail_params: Optional[RailParams] = None,
    barge_params: Optional[BargeParams] = None,
) -> dict:
    """Compare truck, rail, and barge transport costs for a cement shipment.

    Args:
        origin: Origin city/location name.
        destination: Destination city/location name.
        cargo_tons: Total shipment volume in metric tons.
        road_distance_miles: Highway distance. If None, estimated from lookup.
        rail_distance_miles: Rail distance. If None, estimated as 1.1x road distance.
        barge_distance_miles: Waterway distance. If None, estimated or set to 0
            if destination has no barge access.
        num_locks: Number of navigation locks on barge route.
        truck_params: Truck cost parameters. Defaults to DEFAULT_TRUCK.
        rail_params: Rail cost parameters. Defaults to DEFAULT_RAIL.
        barge_params: Barge cost parameters. Defaults to DEFAULT_BARGE.

    Returns:
        Dictionary with cost, time, and capacity comparison for each mode.
        Barge entry is None if destination has no waterway access.
    """
    tp = truck_params or DEFAULT_TRUCK
    rp = rail_params or DEFAULT_RAIL
    bp = barge_params or DEFAULT_BARGE

    # Estimate distances
    if road_distance_miles is None:
        road_distance_miles = _estimate_road_distance(origin, destination)
    if rail_distance_miles is None:
        rail_distance_miles = road_distance_miles * 1.10  # rail typically ~10% longer
    if road_distance_miles == 0:
        return {"error": f"No distance data for {origin} -> {destination}. Provide distances explicitly."}

    # --- Truck ---
    num_trucks = math.ceil(cargo_tons / tp.capacity_tons)
    truck_variable = cargo_tons * tp.cost_per_ton_mile * road_distance_miles
    truck_fixed = num_trucks * tp.fixed_cost_per_load
    truck_total = truck_variable + truck_fixed
    truck_per_ton = truck_total / cargo_tons if cargo_tons > 0 else 0
    truck_transit_hours = road_distance_miles / tp.avg_speed_mph + tp.loading_time_hours + tp.unloading_time_hours
    truck_transit_days = truck_transit_hours / 24

    truck_result = {
        "mode": "truck",
        "distance_miles": road_distance_miles,
        "total_cost": round(truck_total, 2),
        "cost_per_ton": round(truck_per_ton, 2),
        "cost_per_ton_mile": tp.cost_per_ton_mile,
        "transit_days": round(truck_transit_days, 1),
        "num_units": num_trucks,
        "unit_capacity_tons": tp.capacity_tons,
        "notes": f"{num_trucks} truck loads at {tp.capacity_tons} tons each",
    }

    # --- Rail ---
    num_cars = math.ceil(cargo_tons / rp.capacity_tons_per_car)
    eff_rate = rp.effective_cost_per_ton_mile(num_cars)
    rail_variable = cargo_tons * eff_rate * rail_distance_miles
    rail_fixed = num_cars * rp.fixed_cost_per_car
    rail_total = rail_variable + rail_fixed
    rail_per_ton = rail_total / cargo_tons if cargo_tons > 0 else 0
    rail_transit_days = (rail_distance_miles / rp.avg_speed_mph / 24) + rp.transit_time_base_days
    is_unit_train = num_cars >= rp.min_cars_unit_train

    rail_result = {
        "mode": "rail",
        "distance_miles": rail_distance_miles,
        "total_cost": round(rail_total, 2),
        "cost_per_ton": round(rail_per_ton, 2),
        "cost_per_ton_mile": round(eff_rate, 4),
        "transit_days": round(rail_transit_days, 1),
        "num_units": num_cars,
        "unit_capacity_tons": rp.capacity_tons_per_car,
        "is_unit_train": is_unit_train,
        "notes": f"{num_cars} cars {'(unit train rate)' if is_unit_train else '(manifest rate)'}",
    }

    # --- Barge ---
    dest_lower = destination.lower().strip()
    dest_access = WATERWAY_ACCESS.get(dest_lower, {"has_barge": False})

    barge_result: Optional[dict] = None
    if dest_access["has_barge"] and (barge_distance_miles is None or barge_distance_miles > 0):
        if barge_distance_miles is None:
            # Rough estimate: waterway distance ~1.5x road distance for river routes
            barge_distance_miles = road_distance_miles * 1.5

        num_barges = math.ceil(cargo_tons / bp.capacity_tons_per_barge)
        eff_barge_rate = bp.effective_cost_per_ton_mile(num_locks, barge_distance_miles)
        barge_variable = cargo_tons * eff_barge_rate * barge_distance_miles
        barge_fixed = num_barges * bp.fixed_cost_per_barge
        barge_total = barge_variable + barge_fixed
        barge_per_ton = barge_total / cargo_tons if cargo_tons > 0 else 0

        # Transit time
        barge_running_hours = barge_distance_miles / bp.avg_speed_upstream_mph
        lock_hours = num_locks * bp.lock_delay_hours
        barge_transit_days = (barge_running_hours + lock_hours) / 24 + bp.transit_time_base_days

        barge_result = {
            "mode": "barge",
            "distance_miles": barge_distance_miles,
            "total_cost": round(barge_total, 2),
            "cost_per_ton": round(barge_per_ton, 2),
            "cost_per_ton_mile": round(eff_barge_rate, 4),
            "transit_days": round(barge_transit_days, 1),
            "num_units": num_barges,
            "unit_capacity_tons": bp.capacity_tons_per_barge,
            "num_locks": num_locks,
            "notes": f"{num_barges} barges, {num_locks} locks",
        }

    # --- Determine cheapest mode ---
    modes = {"truck": truck_result, "rail": rail_result}
    if barge_result:
        modes["barge"] = barge_result

    cheapest = min(modes.values(), key=lambda m: m["cost_per_ton"])
    fastest = min(modes.values(), key=lambda m: m["transit_days"])

    return {
        "origin": origin,
        "destination": destination,
        "cargo_tons": cargo_tons,
        "truck": truck_result,
        "rail": rail_result,
        "barge": barge_result,
        "cheapest_mode": cheapest["mode"],
        "fastest_mode": fastest["mode"],
        "summary": {
            "cheapest": f"{cheapest['mode']} at ${cheapest['cost_per_ton']:.2f}/ton",
            "fastest": f"{fastest['mode']} at {fastest['transit_days']:.1f} days",
        },
    }


def calculate_breakeven_distance(
    mode_a: str,
    mode_b: str,
    cargo_tons: float,
    truck_params: Optional[TruckParams] = None,
    rail_params: Optional[RailParams] = None,
    barge_params: Optional[BargeParams] = None,
) -> float:
    """Calculate the distance at which two transportation modes have equal cost.

    Uses the simplified linear cost model: Total = (rate * tons * miles) + fixed.
    Solves for the mileage where total cost of mode_a equals mode_b.

    Args:
        mode_a: First mode ('truck', 'rail', or 'barge').
        mode_b: Second mode ('truck', 'rail', or 'barge').
        cargo_tons: Shipment size in metric tons.
        truck_params: Truck cost parameters.
        rail_params: Rail cost parameters.
        barge_params: Barge cost parameters.

    Returns:
        Breakeven distance in miles. Returns float('inf') if the modes
        never cross (one is always cheaper). Returns 0.0 if mode parameters
        are identical.

    Raises:
        ValueError: If mode name is not recognized.
    """
    tp = truck_params or DEFAULT_TRUCK
    rp = rail_params or DEFAULT_RAIL
    bp = barge_params or DEFAULT_BARGE

    def _get_params(mode: str) -> tuple[float, float]:
        """Return (variable_rate_per_ton_mile, fixed_cost_total) for a mode."""
        if mode == "truck":
            num_units = math.ceil(cargo_tons / tp.capacity_tons)
            return tp.cost_per_ton_mile, num_units * tp.fixed_cost_per_load
        elif mode == "rail":
            num_units = math.ceil(cargo_tons / rp.capacity_tons_per_car)
            rate = rp.effective_cost_per_ton_mile(num_units)
            return rate, num_units * rp.fixed_cost_per_car
        elif mode == "barge":
            num_units = math.ceil(cargo_tons / bp.capacity_tons_per_barge)
            return bp.cost_per_ton_mile, num_units * bp.fixed_cost_per_barge
        else:
            raise ValueError(f"Unknown mode '{mode}'. Use 'truck', 'rail', or 'barge'.")

    rate_a, fixed_a = _get_params(mode_a)
    rate_b, fixed_b = _get_params(mode_b)

    # Total_a = rate_a * cargo_tons * D + fixed_a
    # Total_b = rate_b * cargo_tons * D + fixed_b
    # Breakeven: rate_a * cargo_tons * D + fixed_a = rate_b * cargo_tons * D + fixed_b
    # D * cargo_tons * (rate_a - rate_b) = fixed_b - fixed_a
    # D = (fixed_b - fixed_a) / (cargo_tons * (rate_a - rate_b))

    rate_diff = rate_a - rate_b
    if abs(rate_diff) < 1e-10:
        # Same rate per ton-mile -- breakeven only if fixed costs differ
        return 0.0 if abs(fixed_a - fixed_b) < 1e-10 else float("inf")

    breakeven_miles = (fixed_b - fixed_a) / (cargo_tons * rate_diff)

    if breakeven_miles < 0:
        # Negative means one mode is always cheaper at all distances
        return float("inf")

    return round(breakeven_miles, 1)


def optimal_mode_map(
    origin: str,
    destinations_list: list[str],
    cargo_tons: float,
    road_distances: Optional[dict[str, float]] = None,
    rail_distances: Optional[dict[str, float]] = None,
    barge_distances: Optional[dict[str, float]] = None,
    locks_by_dest: Optional[dict[str, int]] = None,
) -> dict[str, dict]:
    """Determine the cheapest transportation mode for each destination.

    Args:
        origin: Origin city/location.
        destinations_list: List of destination city/location names.
        cargo_tons: Shipment volume in metric tons.
        road_distances: Optional dict mapping destination -> road miles.
        rail_distances: Optional dict mapping destination -> rail miles.
        barge_distances: Optional dict mapping destination -> waterway miles.
        locks_by_dest: Optional dict mapping destination -> number of locks.

    Returns:
        Dictionary mapping each destination to a dict with 'cheapest_mode',
        'cost_per_ton', 'transit_days', and 'all_modes' comparison.
    """
    road_distances = road_distances or {}
    rail_distances = rail_distances or {}
    barge_distances = barge_distances or {}
    locks_by_dest = locks_by_dest or {}

    results: dict[str, dict] = {}

    for dest in destinations_list:
        comparison = compare_modes(
            origin=origin,
            destination=dest,
            cargo_tons=cargo_tons,
            road_distance_miles=road_distances.get(dest),
            rail_distance_miles=rail_distances.get(dest),
            barge_distance_miles=barge_distances.get(dest),
            num_locks=locks_by_dest.get(dest, 0),
        )

        if "error" in comparison:
            results[dest] = {"error": comparison["error"]}
            continue

        cheapest_mode = comparison["cheapest_mode"]
        cheapest_data = comparison[cheapest_mode]

        results[dest] = {
            "cheapest_mode": cheapest_mode,
            "cost_per_ton": cheapest_data["cost_per_ton"],
            "transit_days": cheapest_data["transit_days"],
            "all_modes": {
                "truck": {
                    "cost_per_ton": comparison["truck"]["cost_per_ton"],
                    "transit_days": comparison["truck"]["transit_days"],
                },
                "rail": {
                    "cost_per_ton": comparison["rail"]["cost_per_ton"],
                    "transit_days": comparison["rail"]["transit_days"],
                },
                "barge": {
                    "cost_per_ton": comparison["barge"]["cost_per_ton"],
                    "transit_days": comparison["barge"]["transit_days"],
                } if comparison["barge"] else None,
            },
        }

    return results


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("INTERMODAL COMPARISON: Ste. Genevieve MO -> Chicago IL (2,600 tons)")
    print("=" * 70)

    result = compare_modes(
        origin="Ste. Genevieve",
        destination="Chicago",
        cargo_tons=2600,
        road_distance_miles=330,
        rail_distance_miles=350,
        barge_distance_miles=1415,
        num_locks=8,
    )

    for mode_name in ["truck", "rail", "barge"]:
        m = result[mode_name]
        if m:
            print(f"\n  {mode_name.upper():}")
            print(f"    Distance:    {m['distance_miles']:,.0f} miles")
            print(f"    Cost/ton:    ${m['cost_per_ton']:,.2f}")
            print(f"    Total cost:  ${m['total_cost']:,.2f}")
            print(f"    Transit:     {m['transit_days']:.1f} days")
            print(f"    Units:       {m['num_units']} ({m['notes']})")

    print(f"\n  CHEAPEST: {result['summary']['cheapest']}")
    print(f"  FASTEST:  {result['summary']['fastest']}")

    print("\n" + "=" * 70)
    print("BREAKEVEN DISTANCES (2,600 tons)")
    print("=" * 70)
    for a, b in [("truck", "rail"), ("truck", "barge"), ("rail", "barge")]:
        be = calculate_breakeven_distance(a, b, 2600)
        if be == float("inf"):
            print(f"  {a} vs {b}: no crossover (one is always cheaper)")
        else:
            print(f"  {a} vs {b}: {be:.0f} miles")

    print("\n" + "=" * 70)
    print("OPTIMAL MODE MAP: Ste. Genevieve MO -> Multiple Destinations")
    print("=" * 70)
    destinations = ["Chicago", "Memphis", "St. Louis", "Cincinnati", "Indianapolis", "Dallas"]
    mode_map = optimal_mode_map(
        origin="Ste. Genevieve",
        destinations_list=destinations,
        cargo_tons=2600,
        barge_distances={
            "Chicago": 1415,
            "Memphis": 280,
            "St. Louis": 65,
            "Cincinnati": 580,
        },
        locks_by_dest={
            "Chicago": 8,
            "St. Louis": 2,
            "Cincinnati": 9,
        },
    )
    for dest, info in mode_map.items():
        if "error" in info:
            print(f"  {dest}: {info['error']}")
        else:
            print(f"  {dest}: {info['cheapest_mode']} "
                  f"(${info['cost_per_ton']:.2f}/ton, {info['transit_days']:.1f} days)")
