"""
Upriver Cement Barge Distribution Routing Model

Models barge distribution of cement on the Mississippi River system,
including route selection, cost estimation, and multimodal comparison
(barge vs. rail). Covers the primary inland waterway corridors:

    - Lower Mississippi (NOLA to Cairo, IL)
    - Middle Mississippi (Cairo to St. Louis, MO)
    - Upper Mississippi (St. Louis to Minneapolis, MN)
    - Ohio River (Cairo to Pittsburgh, PA)
    - Illinois Waterway (Grafton, IL to Chicago, IL)
    - Tennessee River (Paducah, KY to Knoxville, TN)

Cost model is based on 2025 industry benchmarks for towboat fuel,
crew, lock fees, terminal handling, and insurance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Route definitions: (origin, destination) -> route details
# ---------------------------------------------------------------------------
CEMENT_ROUTES: dict[str, dict] = {
    # --- Lower Mississippi (no locks) ---
    "nola_to_memphis": {
        "origin": "New Orleans, LA",
        "destination": "Memphis, TN",
        "waterway": "Lower Mississippi River",
        "distance_miles": 741,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 7,
        "transit_days_downstream": 4,
        "max_tow_size": 15,
        "notes": "Open river, no locks. Strong current (3-4 mph average).",
    },
    "nola_to_baton_rouge": {
        "origin": "New Orleans, LA",
        "destination": "Baton Rouge, LA",
        "waterway": "Lower Mississippi River",
        "distance_miles": 135,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 1.5,
        "transit_days_downstream": 1,
        "max_tow_size": 15,
        "notes": "Short run between major cement terminals.",
    },
    "nola_to_vicksburg": {
        "origin": "New Orleans, LA",
        "destination": "Vicksburg, MS",
        "waterway": "Lower Mississippi River",
        "distance_miles": 440,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 4.5,
        "transit_days_downstream": 2.5,
        "max_tow_size": 15,
        "notes": "Mid-point on Lower Miss.",
    },
    "nola_to_cairo": {
        "origin": "New Orleans, LA",
        "destination": "Cairo, IL",
        "waterway": "Lower Mississippi River",
        "distance_miles": 953,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 9,
        "transit_days_downstream": 5,
        "max_tow_size": 15,
        "notes": "Ohio River confluence. Key junction for barge traffic routing.",
    },
    "memphis_to_cairo": {
        "origin": "Memphis, TN",
        "destination": "Cairo, IL",
        "waterway": "Lower Mississippi River",
        "distance_miles": 212,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 2,
        "transit_days_downstream": 1.5,
        "max_tow_size": 15,
        "notes": "Short segment, open river.",
    },
    # --- Middle Mississippi (Cairo to St. Louis) ---
    "cairo_to_st_louis": {
        "origin": "Cairo, IL",
        "destination": "St. Louis, MO",
        "waterway": "Middle Mississippi River",
        "distance_miles": 180,
        "locks": 2,
        "lock_names": ["Lock 27 (Chain of Rocks)", "Mel Price Lock"],
        "transit_days_upstream": 2.5,
        "transit_days_downstream": 1.5,
        "max_tow_size": 15,
        "notes": "Two locks above Cairo for St. Louis harbor access.",
    },
    "nola_to_st_louis": {
        "origin": "New Orleans, LA",
        "destination": "St. Louis, MO",
        "waterway": "Lower + Middle Mississippi River",
        "distance_miles": 1070,
        "locks": 2,
        "lock_names": ["Lock 27 (Chain of Rocks)", "Mel Price Lock"],
        "transit_days_upstream": 10,
        "transit_days_downstream": 6,
        "max_tow_size": 15,
        "notes": "Full Lower Miss transit plus 2 locks at St. Louis.",
    },
    "nola_to_ste_genevieve": {
        "origin": "New Orleans, LA",
        "destination": "Ste. Genevieve, MO",
        "waterway": "Lower + Middle Mississippi River",
        "distance_miles": 950,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 9,
        "transit_days_downstream": 5.5,
        "max_tow_size": 15,
        "notes": "No locks required. Ste. Genevieve below Chain of Rocks Lock.",
    },
    # --- Ohio River ---
    "cairo_to_cincinnati": {
        "origin": "Cairo, IL",
        "destination": "Cincinnati, OH",
        "waterway": "Ohio River",
        "distance_miles": 580,
        "locks": 9,
        "lock_names": [
            "Olmsted Lock", "Smithland Lock", "John T. Myers Lock",
            "Newburgh Lock", "Cannelton Lock", "McAlpine Lock",
            "Markland Lock", "Meldahl Lock", "Greenup Lock",
        ],
        "transit_days_upstream": 7,
        "transit_days_downstream": 5,
        "max_tow_size": 15,
        "notes": "Heavily locked. Double-locking at 600-ft chambers adds delays.",
    },
    "cairo_to_louisville": {
        "origin": "Cairo, IL",
        "destination": "Louisville, KY",
        "waterway": "Ohio River",
        "distance_miles": 365,
        "locks": 6,
        "lock_names": [
            "Olmsted Lock", "Smithland Lock", "John T. Myers Lock",
            "Newburgh Lock", "Cannelton Lock", "McAlpine Lock",
        ],
        "transit_days_upstream": 5,
        "transit_days_downstream": 3.5,
        "max_tow_size": 15,
        "notes": "McAlpine Lock at Louisville Falls of the Ohio.",
    },
    "cairo_to_pittsburgh": {
        "origin": "Cairo, IL",
        "destination": "Pittsburgh, PA",
        "waterway": "Ohio River",
        "distance_miles": 981,
        "locks": 20,
        "lock_names": [
            "Olmsted", "Smithland", "John T. Myers", "Newburgh",
            "Cannelton", "McAlpine", "Markland", "Meldahl",
            "Greenup", "R.C. Byrd", "Belleville", "Racine",
            "Willow Island", "Hannibal", "Pike Island",
            "New Cumberland", "Montgomery", "Dashields",
            "Emsworth", "Point of Rocks (Allegheny confluence)",
        ],
        "transit_days_upstream": 14,
        "transit_days_downstream": 10,
        "max_tow_size": 12,
        "notes": "Upper Ohio limited to 12 barges or fewer. Very lock-intensive.",
    },
    "nola_to_cincinnati": {
        "origin": "New Orleans, LA",
        "destination": "Cincinnati, OH",
        "waterway": "Lower Mississippi + Ohio River",
        "distance_miles": 1200,
        "locks": 9,
        "lock_names": [
            "Olmsted Lock", "Smithland Lock", "John T. Myers Lock",
            "Newburgh Lock", "Cannelton Lock", "McAlpine Lock",
            "Markland Lock", "Meldahl Lock", "Greenup Lock",
        ],
        "transit_days_upstream": 12,
        "transit_days_downstream": 8,
        "max_tow_size": 15,
        "notes": "Combined Lower Miss (no locks) + Ohio River (9 locks).",
    },
    # --- Illinois Waterway ---
    "nola_to_chicago": {
        "origin": "New Orleans, LA",
        "destination": "Chicago, IL",
        "waterway": "Lower Mississippi + Illinois Waterway",
        "distance_miles": 1415,
        "locks": 8,
        "lock_names": [
            "LaGrange Lock", "Peoria Lock", "Starved Rock Lock",
            "Marseilles Lock", "Dresden Island Lock", "Brandon Road Lock",
            "Lockport Lock", "T.J. O'Brien Lock",
        ],
        "transit_days_upstream": 14,
        "transit_days_downstream": 9,
        "max_tow_size": 15,
        "notes": "15-barge tow on Lower Miss; reduced to 6-9 on upper Illinois.",
    },
    "st_louis_to_chicago": {
        "origin": "St. Louis, MO",
        "destination": "Chicago, IL",
        "waterway": "Illinois Waterway (via Grafton)",
        "distance_miles": 327,
        "locks": 8,
        "lock_names": [
            "LaGrange Lock", "Peoria Lock", "Starved Rock Lock",
            "Marseilles Lock", "Dresden Island Lock", "Brandon Road Lock",
            "Lockport Lock", "T.J. O'Brien Lock",
        ],
        "transit_days_upstream": 5,
        "transit_days_downstream": 3.5,
        "max_tow_size": 9,
        "notes": "Illinois Waterway locks limit tow to 6-9 barges.",
    },
    # --- Tennessee River ---
    "cairo_to_chattanooga": {
        "origin": "Cairo, IL (via Paducah, KY)",
        "destination": "Chattanooga, TN",
        "waterway": "Tennessee River (via Ohio River to Paducah)",
        "distance_miles": 650,
        "locks": 9,
        "lock_names": [
            "Olmsted Lock (Ohio)", "Kentucky Lock (Tennessee River)",
            "Pickwick Lock", "Wilson Lock", "Wheeler Lock",
            "Guntersville Lock", "Nickajack Lock", "Chickamauga Lock",
            "Watts Bar Lock",
        ],
        "transit_days_upstream": 8,
        "transit_days_downstream": 6,
        "max_tow_size": 9,
        "notes": "Tennessee River access via Ohio River at Paducah.",
    },
    # --- Houston/ICW ---
    "houston_to_nola": {
        "origin": "Houston, TX",
        "destination": "New Orleans, LA",
        "waterway": "Gulf Intracoastal Waterway (GIWW)",
        "distance_miles": 367,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 5,
        "transit_days_downstream": 4,
        "max_tow_size": 6,
        "notes": "GIWW tow limited to 6 barges (2-wide x 3-long).",
    },
    "houston_to_memphis": {
        "origin": "Houston, TX",
        "destination": "Memphis, TN",
        "waterway": "GIWW + Lower Mississippi River",
        "distance_miles": 1108,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 11,
        "transit_days_downstream": 7,
        "max_tow_size": 6,
        "notes": "6-barge ICW tow; may reconfigure at NOLA for larger Miss River tow.",
    },
    "baton_rouge_to_memphis": {
        "origin": "Baton Rouge, LA",
        "destination": "Memphis, TN",
        "waterway": "Lower Mississippi River",
        "distance_miles": 540,
        "locks": 0,
        "lock_names": [],
        "transit_days_upstream": 5,
        "transit_days_downstream": 3,
        "max_tow_size": 15,
        "notes": "Full 15-barge tow. Open river transit.",
    },
}

# ---------------------------------------------------------------------------
# Cost parameters (2025 basis)
# ---------------------------------------------------------------------------

@dataclass
class BargeCostParams:
    """Operating cost parameters for towboat/barge operations."""
    # Fuel
    fuel_price_per_gallon: float = 3.50
    fuel_consumption_gph_loaded: float = 100.0   # gallons per hour, loaded upriver
    fuel_consumption_gph_empty: float = 70.0     # gallons per hour, empty return
    fuel_consumption_gph_idling: float = 15.0    # at lock or waiting

    # Crew
    crew_daily_cost: float = 8500.0              # full crew wages/benefits per day
    crew_size: int = 10                          # typical towboat crew

    # Lock fees (per lockage)
    lock_fee_per_lockage: float = 0.0            # USACE locks are toll-free
    lock_delay_hours_avg: float = 4.0            # average wait + transit per lock

    # Terminal
    fleeting_cost_per_barge_per_day: float = 150.0
    terminal_handling_per_ton: float = 2.50      # load/unload at destination
    barge_cleaning_per_barge: float = 500.0      # cement residue cleaning

    # Insurance / overhead
    insurance_per_ton: float = 0.50
    overhead_pct: float = 0.10                   # 10% overhead on operating costs

    # Barge
    barge_capacity_tons: float = 1500.0
    barge_lease_per_day: float = 250.0           # daily charter rate per barge


DEFAULT_COST_PARAMS = BargeCostParams()

# ---------------------------------------------------------------------------
# Rail cost parameters for comparison
# ---------------------------------------------------------------------------
RAIL_COST_PER_TON_MILE: float = 0.035
RAIL_FIXED_COST_PER_CAR: float = 1200.0         # switching, terminal, car hire
RAIL_TONS_PER_CAR: float = 100.0
RAIL_AVG_SPEED_MPH: float = 25.0                # railroad average including dwell

# Truck cost parameters
TRUCK_COST_PER_TON_MILE: float = 0.12
TRUCK_CAPACITY_TONS: float = 25.0
TRUCK_AVG_SPEED_MPH: float = 45.0


def get_available_routes(
    origin: str,
    destination: str,
) -> list[dict]:
    """Find available barge routes between an origin and destination.

    Performs a case-insensitive search of route origins and destinations
    to find matching routes. Returns all routes where both origin and
    destination match (partial matching on city name).

    Args:
        origin: Origin location name or partial name (e.g. 'New Orleans', 'NOLA').
        destination: Destination location name or partial name (e.g. 'Memphis').

    Returns:
        List of route dictionaries with keys: route_key, origin, destination,
        distance_miles, locks, transit_days_upstream, transit_days_downstream,
        max_tow_size, waterway, notes.
    """
    # Normalize common abbreviations
    _aliases: dict[str, list[str]] = {
        "new orleans": ["nola", "new orleans"],
        "st. louis": ["st. louis", "st louis", "saint louis"],
        "ste. genevieve": ["ste. genevieve", "ste genevieve", "sainte genevieve"],
    }

    def _normalize(name: str) -> str:
        lower = name.lower().strip()
        for canonical, aliases in _aliases.items():
            if lower in aliases:
                return canonical
        return lower

    origin_norm = _normalize(origin)
    dest_norm = _normalize(destination)

    results = []
    for route_key, route in CEMENT_ROUTES.items():
        route_origin_norm = route["origin"].lower()
        route_dest_norm = route["destination"].lower()

        origin_match = origin_norm in route_origin_norm
        dest_match = dest_norm in route_dest_norm

        if origin_match and dest_match:
            results.append({
                "route_key": route_key,
                "origin": route["origin"],
                "destination": route["destination"],
                "waterway": route["waterway"],
                "distance_miles": route["distance_miles"],
                "locks": route["locks"],
                "lock_names": route["lock_names"],
                "transit_days_upstream": route["transit_days_upstream"],
                "transit_days_downstream": route["transit_days_downstream"],
                "max_tow_size": route["max_tow_size"],
                "notes": route["notes"],
            })

    return results


def calculate_upriver_cost(
    origin: str,
    destination: str,
    cargo_tons: float,
    tow_size: Optional[int] = None,
    params: Optional[BargeCostParams] = None,
    route_key: Optional[str] = None,
) -> dict:
    """Calculate the full cost of moving cement upriver by barge.

    Args:
        origin: Origin location (e.g. 'New Orleans, LA').
        destination: Destination location (e.g. 'Memphis, TN').
        cargo_tons: Total cargo in metric tons.
        tow_size: Number of barges in tow. If None, computed from cargo_tons
            and route max_tow_size.
        params: Cost parameters. If None, uses DEFAULT_COST_PARAMS.
        route_key: Specific route key to use. If None, finds the best
            matching route.

    Returns:
        Dictionary with fuel_cost, crew_cost, lock_fees, terminal_fees,
        barge_lease_cost, insurance_cost, overhead, total_cost,
        cost_per_ton, and supporting details.

    Raises:
        ValueError: If no matching route is found.
    """
    if params is None:
        params = DEFAULT_COST_PARAMS

    # Find route
    if route_key and route_key in CEMENT_ROUTES:
        route = CEMENT_ROUTES[route_key]
    else:
        routes = get_available_routes(origin, destination)
        if not routes:
            raise ValueError(
                f"No route found from '{origin}' to '{destination}'. "
                f"Available routes: {list(CEMENT_ROUTES.keys())}"
            )
        route = CEMENT_ROUTES[routes[0]["route_key"]]

    # Determine tow size
    num_barges = tow_size or min(
        math.ceil(cargo_tons / params.barge_capacity_tons),
        route["max_tow_size"],
    )
    actual_cargo = min(cargo_tons, num_barges * params.barge_capacity_tons)

    # Transit time
    transit_days = route["transit_days_upstream"]

    # --- Fuel cost ---
    transit_hours = transit_days * 24
    lock_hours = route["locks"] * params.lock_delay_hours_avg
    running_hours = transit_hours - lock_hours
    fuel_gallons = (
        running_hours * params.fuel_consumption_gph_loaded
        + lock_hours * params.fuel_consumption_gph_idling
    )
    fuel_cost = fuel_gallons * params.fuel_price_per_gallon

    # --- Crew cost ---
    crew_cost = transit_days * params.crew_daily_cost

    # --- Lock fees ---
    # USACE inland waterway locks are toll-free; fuel tax funds the
    # Inland Waterways Trust Fund instead. Lock cost is in delay time (fuel/crew).
    lock_fees = route["locks"] * params.lock_fee_per_lockage  # typically $0

    # --- Terminal / handling fees ---
    terminal_handling = actual_cargo * params.terminal_handling_per_ton
    barge_cleaning = num_barges * params.barge_cleaning_per_barge
    fleeting_days = 2  # assembly + destination
    fleeting_cost = num_barges * params.fleeting_cost_per_barge_per_day * fleeting_days
    terminal_fees = terminal_handling + barge_cleaning + fleeting_cost

    # --- Barge lease ---
    total_barge_days = transit_days + fleeting_days + 2  # +2 for turnaround
    barge_lease_cost = num_barges * params.barge_lease_per_day * total_barge_days

    # --- Insurance ---
    insurance_cost = actual_cargo * params.insurance_per_ton

    # --- Subtotal and overhead ---
    subtotal = fuel_cost + crew_cost + lock_fees + terminal_fees + barge_lease_cost + insurance_cost
    overhead = subtotal * params.overhead_pct
    total_cost = subtotal + overhead

    cost_per_ton = total_cost / actual_cargo if actual_cargo > 0 else 0.0

    return {
        "route": {
            "origin": route["origin"],
            "destination": route["destination"],
            "waterway": route["waterway"],
            "distance_miles": route["distance_miles"],
            "locks": route["locks"],
            "transit_days": transit_days,
        },
        "tow": {
            "num_barges": num_barges,
            "max_tow_size": route["max_tow_size"],
            "cargo_tons": actual_cargo,
            "barge_capacity_tons": params.barge_capacity_tons,
        },
        "cost_breakdown": {
            "fuel_cost": round(fuel_cost, 2),
            "crew_cost": round(crew_cost, 2),
            "lock_fees": round(lock_fees, 2),
            "terminal_fees": round(terminal_fees, 2),
            "barge_lease_cost": round(barge_lease_cost, 2),
            "insurance_cost": round(insurance_cost, 2),
            "overhead": round(overhead, 2),
        },
        "total_cost": round(total_cost, 2),
        "cost_per_ton": round(cost_per_ton, 2),
        "fuel_gallons": round(fuel_gallons, 0),
    }


def compare_barge_vs_rail(
    origin: str,
    destination: str,
    cargo_tons: float,
    rail_distance_miles: Optional[float] = None,
    params: Optional[BargeCostParams] = None,
) -> dict:
    """Compare barge and rail transportation costs for cement.

    Args:
        origin: Origin location name.
        destination: Destination location name.
        cargo_tons: Total cargo in metric tons.
        rail_distance_miles: Rail distance (usually shorter than barge).
            If None, estimated as 70% of barge distance (typical ratio).
        params: Barge cost parameters.

    Returns:
        Dictionary with barge and rail cost comparisons including
        total_cost, cost_per_ton, transit_days, advantage, and
        savings for each mode.

    Raises:
        ValueError: If no barge route is found.
    """
    # Barge cost
    barge_result = calculate_upriver_cost(origin, destination, cargo_tons, params=params)

    barge_distance = barge_result["route"]["distance_miles"]

    # Rail distance estimate
    if rail_distance_miles is None:
        rail_distance_miles = barge_distance * 0.70  # rail routes ~30% shorter

    # Rail cost
    num_cars = math.ceil(cargo_tons / RAIL_TONS_PER_CAR)
    rail_variable_cost = cargo_tons * RAIL_COST_PER_TON_MILE * rail_distance_miles
    rail_fixed_cost = num_cars * RAIL_FIXED_COST_PER_CAR
    rail_total_cost = rail_variable_cost + rail_fixed_cost
    rail_cost_per_ton = rail_total_cost / cargo_tons if cargo_tons > 0 else 0.0

    # Rail transit time (days)
    rail_transit_days = (rail_distance_miles / RAIL_AVG_SPEED_MPH / 24) + 2  # +2 for dwell/switching

    # Comparison
    barge_cost_per_ton = barge_result["cost_per_ton"]
    savings_per_ton = rail_cost_per_ton - barge_cost_per_ton
    cheaper_mode = "barge" if savings_per_ton > 0 else "rail"
    pct_savings = abs(savings_per_ton) / max(barge_cost_per_ton, rail_cost_per_ton) * 100

    return {
        "barge": {
            "distance_miles": barge_distance,
            "total_cost": barge_result["total_cost"],
            "cost_per_ton": round(barge_cost_per_ton, 2),
            "transit_days": barge_result["route"]["transit_days"],
            "locks": barge_result["route"]["locks"],
            "num_barges": barge_result["tow"]["num_barges"],
        },
        "rail": {
            "distance_miles": round(rail_distance_miles, 0),
            "total_cost": round(rail_total_cost, 2),
            "cost_per_ton": round(rail_cost_per_ton, 2),
            "transit_days": round(rail_transit_days, 1),
            "num_cars": num_cars,
        },
        "comparison": {
            "cheaper_mode": cheaper_mode,
            "savings_per_ton": round(abs(savings_per_ton), 2),
            "savings_pct": round(pct_savings, 1),
            "total_savings": round(abs(savings_per_ton) * cargo_tons, 2),
            "time_advantage_mode": "rail" if rail_transit_days < barge_result["route"]["transit_days"] else "barge",
            "time_difference_days": round(
                abs(barge_result["route"]["transit_days"] - rail_transit_days), 1
            ),
        },
        "notes": [
            "Barge costs include fuel, crew, terminal handling, barge lease, insurance, and overhead.",
            "Rail costs include variable (ton-mile) and fixed (car switching/terminal) components.",
            f"Rail distance estimated at {rail_distance_miles:.0f} miles "
            f"({rail_distance_miles / barge_distance * 100:.0f}% of barge distance)."
            if rail_distance_miles
            else "",
            "Barge is typically cheaper for high-volume, long-distance, time-insensitive moves.",
            "Rail advantage increases for destinations far from waterway or requiring rapid delivery.",
        ],
    }


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AVAILABLE ROUTES: New Orleans to Memphis")
    print("=" * 70)
    routes = get_available_routes("New Orleans", "Memphis")
    for r in routes:
        print(f"  {r['route_key']}: {r['distance_miles']} mi, "
              f"{r['locks']} locks, {r['transit_days_upstream']} days up")

    print()
    print("=" * 70)
    print("UPRIVER COST: NOLA → Memphis, 22,500 tons")
    print("=" * 70)
    cost = calculate_upriver_cost("New Orleans", "Memphis", 22500)
    for key, val in cost["cost_breakdown"].items():
        label = key.replace("_", " ").title()
        print(f"  {label:.<35s} ${val:>12,.2f}")
    print(f"  {'Total':.<35s} ${cost['total_cost']:>12,.2f}")
    print(f"  Cost per ton: ${cost['cost_per_ton']:.2f}")

    print()
    print("=" * 70)
    print("BARGE vs RAIL: NOLA → Memphis, 22,500 tons")
    print("=" * 70)
    comp = compare_barge_vs_rail("New Orleans", "Memphis", 22500)
    print(f"  Barge: ${comp['barge']['cost_per_ton']:.2f}/ton "
          f"({comp['barge']['transit_days']} days)")
    print(f"  Rail:  ${comp['rail']['cost_per_ton']:.2f}/ton "
          f"({comp['rail']['transit_days']} days)")
    print(f"  Cheaper: {comp['comparison']['cheaper_mode']} "
          f"(saves ${comp['comparison']['savings_per_ton']:.2f}/ton, "
          f"{comp['comparison']['savings_pct']:.1f}%)")
