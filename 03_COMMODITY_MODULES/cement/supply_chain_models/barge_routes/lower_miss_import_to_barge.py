"""
Lower Mississippi Import-to-Barge Cement Transfer Model

Models the vessel-to-barge transloading process for imported cement arriving
at Lower Mississippi River terminals (New Orleans to Baton Rouge corridor).
Covers discharge from ocean vessels, terminal storage/handling, and loading
onto inland barges for upriver distribution.

Typical flow:
    Ocean Vessel → Terminal Discharge → Silo Storage → Barge Loading → Upriver Tow

Key terminals modeled:
    - New Orleans (Mississippi River Mile 95-105)
    - Baton Rouge (Mississippi River Mile 228-235)
    - Port Allen (Mississippi River Mile 228, west bank)
    - Burnside / Gramercy (Mississippi River Mile 165-175)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class HandlingMethod(Enum):
    """Cement discharge method from ocean vessel."""
    PNEUMATIC = "pneumatic"
    GRAB_CRANE = "grab_crane"
    SHIPS_GEAR = "ships_gear"


class VesselType(Enum):
    """Ocean vessel types carrying cement or clinker."""
    HANDYSIZE = "handysize"
    SUPRAMAX = "supramax"
    PANAMAX = "panamax"
    HANDY_BULKER = "handy_bulker"


# ---------------------------------------------------------------------------
# Discharge rate parameters (tons per hour) by handling method
# ---------------------------------------------------------------------------
DISCHARGE_RATES_TPH: dict[str, float] = {
    HandlingMethod.PNEUMATIC.value: 400.0,
    HandlingMethod.GRAB_CRANE.value: 300.0,
    HandlingMethod.SHIPS_GEAR.value: 200.0,
}

# ---------------------------------------------------------------------------
# Stevedoring / handling cost per ton by method (USD, 2025 basis)
# ---------------------------------------------------------------------------
STEVEDORING_COST_PER_TON: dict[str, float] = {
    HandlingMethod.PNEUMATIC.value: 5.50,
    HandlingMethod.GRAB_CRANE.value: 4.25,
    HandlingMethod.SHIPS_GEAR.value: 6.00,
}

# ---------------------------------------------------------------------------
# Terminal profiles on the Lower Mississippi
# ---------------------------------------------------------------------------
TERMINAL_PROFILES: dict[str, dict] = {
    "new_orleans_nashville_wharf": {
        "name": "Nashville Avenue Wharf (New Orleans)",
        "river_mile": 97.0,
        "bank": "east",
        "max_vessel_loa_ft": 750,
        "max_draft_ft": 45,
        "silo_capacity_tons": 60000,
        "barge_loading_rate_tph": 500,
        "dock_fee_per_vessel": 15000,
        "wharfage_per_ton": 1.25,
        "has_pneumatic_unloader": True,
        "has_grab_crane": True,
    },
    "new_orleans_ternium": {
        "name": "New Orleans Terminal (Ternium/SESCO)",
        "river_mile": 100.5,
        "bank": "east",
        "max_vessel_loa_ft": 700,
        "max_draft_ft": 45,
        "silo_capacity_tons": 45000,
        "barge_loading_rate_tph": 400,
        "dock_fee_per_vessel": 12000,
        "wharfage_per_ton": 1.10,
        "has_pneumatic_unloader": True,
        "has_grab_crane": False,
    },
    "baton_rouge_giant": {
        "name": "Giant Cement / Heidelberg (Baton Rouge)",
        "river_mile": 230.0,
        "bank": "east",
        "max_vessel_loa_ft": 700,
        "max_draft_ft": 45,
        "silo_capacity_tons": 80000,
        "barge_loading_rate_tph": 450,
        "dock_fee_per_vessel": 12000,
        "wharfage_per_ton": 1.15,
        "has_pneumatic_unloader": True,
        "has_grab_crane": True,
    },
    "burnside_terminal": {
        "name": "Burnside Marine Terminal",
        "river_mile": 167.0,
        "bank": "east",
        "max_vessel_loa_ft": 750,
        "max_draft_ft": 45,
        "silo_capacity_tons": 50000,
        "barge_loading_rate_tph": 400,
        "dock_fee_per_vessel": 11000,
        "wharfage_per_ton": 1.05,
        "has_pneumatic_unloader": True,
        "has_grab_crane": True,
    },
    "port_allen_terminal": {
        "name": "Port Allen Terminal (West Bank)",
        "river_mile": 228.0,
        "bank": "west",
        "max_vessel_loa_ft": 600,
        "max_draft_ft": 40,
        "silo_capacity_tons": 30000,
        "barge_loading_rate_tph": 350,
        "dock_fee_per_vessel": 10000,
        "wharfage_per_ton": 1.00,
        "has_pneumatic_unloader": True,
        "has_grab_crane": False,
    },
}

# ---------------------------------------------------------------------------
# Vessel size parameters (DWT ranges)
# ---------------------------------------------------------------------------
VESSEL_DWT_RANGES: dict[str, tuple[int, int]] = {
    VesselType.HANDYSIZE.value: (15000, 35000),
    VesselType.SUPRAMAX.value: (35000, 60000),
    VesselType.PANAMAX.value: (60000, 80000),
    VesselType.HANDY_BULKER.value: (10000, 15000),
}

# ---------------------------------------------------------------------------
# Barge parameters for inland distribution
# ---------------------------------------------------------------------------
BARGE_CAPACITY_TONS: float = 1500.0
BARGE_LOADING_COST_PER_TON: float = 1.75
FLEETING_COST_PER_BARGE_PER_DAY: float = 150.0

# ---------------------------------------------------------------------------
# Import origin freight rate benchmarks (ocean freight $/ton to US Gulf)
# ---------------------------------------------------------------------------
OCEAN_FREIGHT_BENCHMARKS: dict[str, float] = {
    "turkey": 18.00,
    "greece": 20.00,
    "spain": 19.50,
    "china": 28.00,
    "vietnam": 30.00,
    "mexico": 12.00,
    "colombia": 14.00,
    "egypt": 22.00,
    "japan": 32.00,
    "south_korea": 30.00,
    "thailand": 29.00,
}


@dataclass
class CementTransloadScenario:
    """Represents a complete vessel-to-barge cement transload scenario.

    Captures all parameters and computed costs for a single import-to-barge
    transfer operation at a Lower Mississippi River terminal.
    """

    # --- Vessel parameters ---
    origin_country: str
    vessel_type: str
    vessel_dwt: int
    cargo_tons: float

    # --- Terminal parameters ---
    terminal_key: str
    terminal_name: str = ""
    handling_method: str = HandlingMethod.PNEUMATIC.value

    # --- Discharge parameters ---
    discharge_rate_tph: float = 0.0
    discharge_hours: float = 0.0
    discharge_weather_delay_hours: float = 4.0
    discharge_total_hours: float = 0.0

    # --- Cost components ($/ton) ---
    ocean_freight_per_ton: float = 0.0
    stevedoring_per_ton: float = 0.0
    wharfage_per_ton: float = 0.0
    dock_fee_per_ton: float = 0.0
    barge_loading_per_ton: float = 0.0
    fleeting_per_ton: float = 0.0
    total_transload_per_ton: float = 0.0

    # --- Barge loading parameters ---
    num_barges_required: int = 0
    barge_loading_hours: float = 0.0

    # --- Barge destination ---
    barge_destination: str = ""
    barge_freight_per_ton: float = 0.0

    # --- Total delivered cost ---
    total_delivered_per_ton: float = 0.0

    # --- Notes ---
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Populate terminal name from key if not set."""
        if not self.terminal_name and self.terminal_key in TERMINAL_PROFILES:
            self.terminal_name = TERMINAL_PROFILES[self.terminal_key]["name"]


def calculate_transload_cost(
    vessel_size_dwt: int,
    cargo_tons: float,
    terminal: str,
    handling_method: str = "pneumatic",
) -> dict:
    """Calculate the cost of transloading cement from vessel to barge at a
    Lower Mississippi terminal.

    Args:
        vessel_size_dwt: Deadweight tonnage of the arriving vessel.
        cargo_tons: Actual cement cargo in metric tons to be discharged.
        terminal: Terminal key from TERMINAL_PROFILES (e.g., 'new_orleans_nashville_wharf').
        handling_method: One of 'pneumatic', 'grab_crane', or 'ships_gear'.

    Returns:
        Dictionary with cost breakdown including stevedoring_per_ton,
        barge_loading_per_ton, wharfage_per_ton, dock_fee_per_ton,
        total_transload_per_ton, and supporting details.

    Raises:
        ValueError: If terminal key or handling method is not recognized.
    """
    if terminal not in TERMINAL_PROFILES:
        raise ValueError(
            f"Unknown terminal '{terminal}'. "
            f"Available: {list(TERMINAL_PROFILES.keys())}"
        )

    if handling_method not in DISCHARGE_RATES_TPH:
        raise ValueError(
            f"Unknown handling method '{handling_method}'. "
            f"Available: {list(DISCHARGE_RATES_TPH.keys())}"
        )

    profile = TERMINAL_PROFILES[terminal]

    # Check terminal supports the handling method
    if handling_method == HandlingMethod.PNEUMATIC.value and not profile["has_pneumatic_unloader"]:
        raise ValueError(
            f"Terminal '{terminal}' does not have a pneumatic unloader."
        )
    if handling_method == HandlingMethod.GRAB_CRANE.value and not profile["has_grab_crane"]:
        raise ValueError(
            f"Terminal '{terminal}' does not have a grab crane."
        )

    stevedoring = STEVEDORING_COST_PER_TON[handling_method]
    wharfage = profile["wharfage_per_ton"]
    dock_fee_per_ton = profile["dock_fee_per_vessel"] / cargo_tons if cargo_tons > 0 else 0.0
    barge_loading = BARGE_LOADING_COST_PER_TON

    num_barges = math.ceil(cargo_tons / BARGE_CAPACITY_TONS)
    fleeting_days = 2  # typical fleeting time while assembling tow
    fleeting_total = num_barges * FLEETING_COST_PER_BARGE_PER_DAY * fleeting_days
    fleeting_per_ton = fleeting_total / cargo_tons if cargo_tons > 0 else 0.0

    total_transload = stevedoring + wharfage + dock_fee_per_ton + barge_loading + fleeting_per_ton

    return {
        "vessel_size_dwt": vessel_size_dwt,
        "cargo_tons": cargo_tons,
        "terminal": profile["name"],
        "handling_method": handling_method,
        "stevedoring_per_ton": round(stevedoring, 2),
        "wharfage_per_ton": round(wharfage, 2),
        "dock_fee_per_ton": round(dock_fee_per_ton, 2),
        "barge_loading_per_ton": round(barge_loading, 2),
        "fleeting_per_ton": round(fleeting_per_ton, 2),
        "num_barges_required": num_barges,
        "total_transload_per_ton": round(total_transload, 2),
        "total_transload_cost": round(total_transload * cargo_tons, 2),
    }


def estimate_barge_loading_time(
    cargo_tons: float,
    handling_rate_tph: float = 400.0,
    num_barges: Optional[int] = None,
) -> float:
    """Estimate total time to load barges from terminal silos.

    Args:
        cargo_tons: Total cement tonnage to load onto barges.
        handling_rate_tph: Terminal barge-loading rate in tons per hour.
            Defaults to 400 TPH (typical pneumatic loading).
        num_barges: Number of barges to load. If None, calculated from
            cargo_tons / BARGE_CAPACITY_TONS.

    Returns:
        Total estimated loading time in hours, including barge-positioning
        overhead (0.5 hours per barge swap).
    """
    if num_barges is None:
        num_barges = math.ceil(cargo_tons / BARGE_CAPACITY_TONS)

    # Pure loading time
    loading_hours = cargo_tons / handling_rate_tph

    # Barge swap / positioning overhead (0.5 hours per barge change)
    swap_overhead = max(0, (num_barges - 1)) * 0.5

    total_hours = loading_hours + swap_overhead
    return round(total_hours, 1)


def model_import_to_barge_chain(
    origin_country: str,
    vessel_type: str,
    discharge_port: str,
    barge_destination: str,
    cargo_tons: Optional[float] = None,
    handling_method: str = "pneumatic",
    barge_freight_per_ton: Optional[float] = None,
) -> dict:
    """Model the complete import-to-barge supply chain for cement.

    Produces a full cost-chain from ocean vessel loading through inland
    barge delivery, including ocean freight, terminal transloading,
    and barge freight components.

    Args:
        origin_country: Country of origin (key in OCEAN_FREIGHT_BENCHMARKS,
            e.g. 'turkey', 'greece', 'china').
        vessel_type: Vessel class ('handysize', 'supramax', 'panamax', 'handy_bulker').
        discharge_port: Terminal key from TERMINAL_PROFILES.
        barge_destination: Description of barge destination (e.g. 'Memphis, TN').
        cargo_tons: Cargo volume in metric tons. If None, defaults to 75% of
            vessel DWT midpoint.
        handling_method: Discharge method ('pneumatic', 'grab_crane', 'ships_gear').
        barge_freight_per_ton: Barge freight rate to destination. If None,
            a default estimate is used.

    Returns:
        Dictionary with complete cost chain including ocean_freight, transload
        costs, barge freight, and total delivered cost per ton.

    Raises:
        ValueError: If origin_country, vessel_type, or discharge_port is invalid.
    """
    # Validate origin country
    origin_key = origin_country.lower().replace(" ", "_")
    if origin_key not in OCEAN_FREIGHT_BENCHMARKS:
        raise ValueError(
            f"Unknown origin country '{origin_country}'. "
            f"Available: {list(OCEAN_FREIGHT_BENCHMARKS.keys())}"
        )

    # Validate vessel type
    vessel_key = vessel_type.lower().replace(" ", "_")
    if vessel_key not in VESSEL_DWT_RANGES:
        raise ValueError(
            f"Unknown vessel type '{vessel_type}'. "
            f"Available: {list(VESSEL_DWT_RANGES.keys())}"
        )

    # Determine cargo volume
    dwt_low, dwt_high = VESSEL_DWT_RANGES[vessel_key]
    dwt_midpoint = (dwt_low + dwt_high) // 2
    if cargo_tons is None:
        cargo_tons = dwt_midpoint * 0.75  # typical utilization

    # Ocean freight
    ocean_freight = OCEAN_FREIGHT_BENCHMARKS[origin_key]

    # Transload costs
    transload = calculate_transload_cost(
        vessel_size_dwt=dwt_midpoint,
        cargo_tons=cargo_tons,
        terminal=discharge_port,
        handling_method=handling_method,
    )

    # Barge freight estimate
    if barge_freight_per_ton is None:
        # Default estimates by destination keyword
        _barge_defaults: dict[str, float] = {
            "memphis": 8.75,
            "st. louis": 10.50,
            "st louis": 10.50,
            "cincinnati": 13.25,
            "chicago": 14.75,
            "baton rouge": 3.50,
            "cairo": 7.50,
        }
        dest_lower = barge_destination.lower()
        barge_freight_per_ton = next(
            (v for k, v in _barge_defaults.items() if k in dest_lower),
            10.00,  # fallback default
        )

    # Discharge time
    discharge_rate = DISCHARGE_RATES_TPH[handling_method]
    discharge_hours = cargo_tons / discharge_rate
    weather_delay = 4.0  # typical allowance
    total_discharge_hours = discharge_hours + weather_delay

    # Barge loading time
    num_barges = math.ceil(cargo_tons / BARGE_CAPACITY_TONS)
    terminal_profile = TERMINAL_PROFILES[discharge_port]
    barge_loading_hours = estimate_barge_loading_time(
        cargo_tons=cargo_tons,
        handling_rate_tph=terminal_profile["barge_loading_rate_tph"],
        num_barges=num_barges,
    )

    # Total delivered cost
    total_delivered = (
        ocean_freight
        + transload["total_transload_per_ton"]
        + barge_freight_per_ton
    )

    # Build scenario dataclass
    scenario = CementTransloadScenario(
        origin_country=origin_country,
        vessel_type=vessel_type,
        vessel_dwt=dwt_midpoint,
        cargo_tons=cargo_tons,
        terminal_key=discharge_port,
        terminal_name=terminal_profile["name"],
        handling_method=handling_method,
        discharge_rate_tph=discharge_rate,
        discharge_hours=round(discharge_hours, 1),
        discharge_weather_delay_hours=weather_delay,
        discharge_total_hours=round(total_discharge_hours, 1),
        ocean_freight_per_ton=round(ocean_freight, 2),
        stevedoring_per_ton=transload["stevedoring_per_ton"],
        wharfage_per_ton=transload["wharfage_per_ton"],
        dock_fee_per_ton=transload["dock_fee_per_ton"],
        barge_loading_per_ton=transload["barge_loading_per_ton"],
        fleeting_per_ton=transload["fleeting_per_ton"],
        total_transload_per_ton=transload["total_transload_per_ton"],
        num_barges_required=num_barges,
        barge_loading_hours=barge_loading_hours,
        barge_destination=barge_destination,
        barge_freight_per_ton=round(barge_freight_per_ton, 2),
        total_delivered_per_ton=round(total_delivered, 2),
    )

    return {
        "scenario_summary": {
            "origin": f"{origin_country.title()} → {terminal_profile['name']} → {barge_destination}",
            "vessel": f"{vessel_type.title()} ({dwt_midpoint:,} DWT)",
            "cargo_tons": cargo_tons,
            "num_barges": num_barges,
        },
        "cost_chain": {
            "ocean_freight_per_ton": scenario.ocean_freight_per_ton,
            "stevedoring_per_ton": scenario.stevedoring_per_ton,
            "wharfage_per_ton": scenario.wharfage_per_ton,
            "dock_fee_per_ton": scenario.dock_fee_per_ton,
            "barge_loading_per_ton": scenario.barge_loading_per_ton,
            "fleeting_per_ton": scenario.fleeting_per_ton,
            "total_transload_per_ton": scenario.total_transload_per_ton,
            "barge_freight_per_ton": scenario.barge_freight_per_ton,
            "total_delivered_per_ton": scenario.total_delivered_per_ton,
        },
        "timing": {
            "discharge_rate_tph": scenario.discharge_rate_tph,
            "discharge_hours": scenario.discharge_hours,
            "weather_delay_hours": scenario.discharge_weather_delay_hours,
            "total_discharge_hours": scenario.discharge_total_hours,
            "barge_loading_hours": scenario.barge_loading_hours,
        },
        "total_cost": round(scenario.total_delivered_per_ton * cargo_tons, 2),
        "scenario": scenario,
    }


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example: Turkish cement import via New Orleans to Memphis
    result = model_import_to_barge_chain(
        origin_country="turkey",
        vessel_type="supramax",
        discharge_port="new_orleans_nashville_wharf",
        barge_destination="Memphis, TN",
        cargo_tons=35000,
    )

    print("=" * 70)
    print("CEMENT IMPORT-TO-BARGE COST CHAIN")
    print("=" * 70)
    print(f"Route: {result['scenario_summary']['origin']}")
    print(f"Vessel: {result['scenario_summary']['vessel']}")
    print(f"Cargo: {result['scenario_summary']['cargo_tons']:,.0f} tons")
    print(f"Barges: {result['scenario_summary']['num_barges']}")
    print("-" * 70)
    print("COST BREAKDOWN ($/ton):")
    for key, val in result["cost_chain"].items():
        label = key.replace("_", " ").replace(" per ton", "").title()
        print(f"  {label:.<40s} ${val:>8.2f}")
    print("-" * 70)
    print(f"TOTAL COST: ${result['total_cost']:>12,.2f}")
    print(f"Discharge time: {result['timing']['total_discharge_hours']:.1f} hours")
    print(f"Barge loading time: {result['timing']['barge_loading_hours']:.1f} hours")
