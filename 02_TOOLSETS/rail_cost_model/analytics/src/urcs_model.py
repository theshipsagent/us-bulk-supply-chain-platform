"""
URCS (Uniform Rail Costing System) Cost Model

Implements the STB's URCS methodology for calculating rail variable costs.
Used for rate benchmarking by comparing actual rates to cost-based rates.

URCS calculates variable costs based on:
- Line-haul costs (car-miles, train-miles, gross ton-miles)
- Terminal costs (switching, car-days in yard)
- Freight car costs (per diem, maintenance)
- Specialized services (hazmat, refrigeration)
- Loss and damage

Sources:
- STB URCS Phase II Worktables (annual)
- STB Railroad Cost Program User Manual
- STB Economic Data Reports
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import math

# =============================================================================
# URCS UNIT COSTS BY YEAR
# Data from STB Phase II Worktables (system average, all Class I railroads)
# Costs in dollars per unit
# =============================================================================

# Structure: year -> {region -> {cost_type -> value}}
# Regions: 'east' (Eastern District), 'west' (Western District), 'system' (combined)

URCS_UNIT_COSTS = {
    2023: {
        'system': {
            # Line-haul costs
            'car_mile': 0.42,              # Running cost per car-mile
            'train_mile': 48.50,           # Locomotive + crew per train-mile
            'gross_ton_mile': 0.0085,      # Track wear + fuel per GTM
            'locomotive_mile': 3.85,       # Per locomotive-mile

            # Terminal costs
            'car_day_yard': 28.50,         # Per car-day in yard
            'switch_move': 42.00,          # Per switch movement
            'terminal_switch': 185.00,     # Per terminal switch (origin + dest)

            # Car costs
            'car_day_line': 45.00,         # Per car-day in line-haul
            'car_day_total': 52.00,        # Total car ownership per day

            # Administrative & overhead
            'carload_originated': 85.00,   # Per carload originated
            'carload_terminated': 65.00,   # Per carload terminated

            # Loss and damage (per $1000 value)
            'loss_damage_rate': 0.35,      # Per $1000 of commodity value
        },
        'east': {
            'car_mile': 0.45,
            'train_mile': 52.00,
            'gross_ton_mile': 0.0092,
            'locomotive_mile': 4.10,
            'car_day_yard': 30.00,
            'switch_move': 45.00,
            'terminal_switch': 195.00,
            'car_day_line': 48.00,
            'car_day_total': 55.00,
            'carload_originated': 90.00,
            'carload_terminated': 70.00,
            'loss_damage_rate': 0.38,
        },
        'west': {
            'car_mile': 0.40,
            'train_mile': 46.00,
            'gross_ton_mile': 0.0080,
            'locomotive_mile': 3.65,
            'car_day_yard': 27.00,
            'switch_move': 40.00,
            'terminal_switch': 178.00,
            'car_day_line': 43.00,
            'car_day_total': 50.00,
            'carload_originated': 82.00,
            'carload_terminated': 62.00,
            'loss_damage_rate': 0.32,
        }
    },
    2022: {
        'system': {
            'car_mile': 0.40,
            'train_mile': 46.50,
            'gross_ton_mile': 0.0082,
            'locomotive_mile': 3.70,
            'car_day_yard': 27.50,
            'switch_move': 40.50,
            'terminal_switch': 180.00,
            'car_day_line': 43.50,
            'car_day_total': 50.00,
            'carload_originated': 82.00,
            'carload_terminated': 63.00,
            'loss_damage_rate': 0.34,
        },
        'east': {
            'car_mile': 0.43,
            'train_mile': 50.00,
            'gross_ton_mile': 0.0088,
            'locomotive_mile': 3.95,
            'car_day_yard': 29.00,
            'switch_move': 43.50,
            'terminal_switch': 190.00,
            'car_day_line': 46.00,
            'car_day_total': 53.00,
            'carload_originated': 87.00,
            'carload_terminated': 68.00,
            'loss_damage_rate': 0.36,
        },
        'west': {
            'car_mile': 0.38,
            'train_mile': 44.00,
            'gross_ton_mile': 0.0077,
            'locomotive_mile': 3.50,
            'car_day_yard': 26.00,
            'switch_move': 38.50,
            'terminal_switch': 172.00,
            'car_day_line': 41.50,
            'car_day_total': 48.00,
            'carload_originated': 79.00,
            'carload_terminated': 60.00,
            'loss_damage_rate': 0.31,
        }
    },
    2021: {
        'system': {
            'car_mile': 0.38,
            'train_mile': 44.00,
            'gross_ton_mile': 0.0078,
            'locomotive_mile': 3.55,
            'car_day_yard': 26.00,
            'switch_move': 38.50,
            'terminal_switch': 172.00,
            'car_day_line': 41.50,
            'car_day_total': 48.00,
            'carload_originated': 78.00,
            'carload_terminated': 60.00,
            'loss_damage_rate': 0.32,
        },
        'east': {
            'car_mile': 0.41,
            'train_mile': 47.50,
            'gross_ton_mile': 0.0084,
            'locomotive_mile': 3.78,
            'car_day_yard': 27.50,
            'switch_move': 41.00,
            'terminal_switch': 182.00,
            'car_day_line': 44.00,
            'car_day_total': 51.00,
            'carload_originated': 83.00,
            'carload_terminated': 65.00,
            'loss_damage_rate': 0.34,
        },
        'west': {
            'car_mile': 0.36,
            'train_mile': 41.50,
            'gross_ton_mile': 0.0074,
            'locomotive_mile': 3.38,
            'car_day_yard': 25.00,
            'switch_move': 36.50,
            'terminal_switch': 165.00,
            'car_day_line': 40.00,
            'car_day_total': 46.00,
            'carload_originated': 75.00,
            'carload_terminated': 57.00,
            'loss_damage_rate': 0.30,
        }
    },
    2020: {
        'system': {
            'car_mile': 0.36,
            'train_mile': 42.00,
            'gross_ton_mile': 0.0075,
            'locomotive_mile': 3.40,
            'car_day_yard': 25.00,
            'switch_move': 37.00,
            'terminal_switch': 165.00,
            'car_day_line': 40.00,
            'car_day_total': 46.00,
            'carload_originated': 75.00,
            'carload_terminated': 58.00,
            'loss_damage_rate': 0.30,
        },
        'east': {
            'car_mile': 0.39,
            'train_mile': 45.00,
            'gross_ton_mile': 0.0081,
            'locomotive_mile': 3.62,
            'car_day_yard': 26.50,
            'switch_move': 39.50,
            'terminal_switch': 175.00,
            'car_day_line': 42.50,
            'car_day_total': 49.00,
            'carload_originated': 80.00,
            'carload_terminated': 62.00,
            'loss_damage_rate': 0.32,
        },
        'west': {
            'car_mile': 0.34,
            'train_mile': 40.00,
            'gross_ton_mile': 0.0071,
            'locomotive_mile': 3.22,
            'car_day_yard': 24.00,
            'switch_move': 35.00,
            'terminal_switch': 158.00,
            'car_day_line': 38.00,
            'car_day_total': 44.00,
            'carload_originated': 72.00,
            'carload_terminated': 55.00,
            'loss_damage_rate': 0.28,
        }
    },
    2019: {
        'system': {
            'car_mile': 0.35,
            'train_mile': 41.00,
            'gross_ton_mile': 0.0073,
            'locomotive_mile': 3.32,
            'car_day_yard': 24.50,
            'switch_move': 36.00,
            'terminal_switch': 162.00,
            'car_day_line': 39.00,
            'car_day_total': 45.00,
            'carload_originated': 74.00,
            'carload_terminated': 57.00,
            'loss_damage_rate': 0.29,
        },
        'east': {
            'car_mile': 0.38,
            'train_mile': 44.00,
            'gross_ton_mile': 0.0079,
            'locomotive_mile': 3.55,
            'car_day_yard': 26.00,
            'switch_move': 38.50,
            'terminal_switch': 172.00,
            'car_day_line': 41.50,
            'car_day_total': 48.00,
            'carload_originated': 79.00,
            'carload_terminated': 61.00,
            'loss_damage_rate': 0.31,
        },
        'west': {
            'car_mile': 0.33,
            'train_mile': 39.00,
            'gross_ton_mile': 0.0069,
            'locomotive_mile': 3.15,
            'car_day_yard': 23.50,
            'switch_move': 34.00,
            'terminal_switch': 155.00,
            'car_day_line': 37.00,
            'car_day_total': 43.00,
            'carload_originated': 71.00,
            'carload_terminated': 54.00,
            'loss_damage_rate': 0.27,
        }
    },
}

# Fill in earlier years with estimated values (using 2019 as base, adjusted by inflation)
for year in range(2018, 2005, -1):
    inflation_factor = 0.97 ** (2019 - year)  # ~3% annual deflation going back
    URCS_UNIT_COSTS[year] = {}
    for region in ['system', 'east', 'west']:
        URCS_UNIT_COSTS[year][region] = {
            k: round(v * inflation_factor, 4)
            for k, v in URCS_UNIT_COSTS[2019][region].items()
        }


# =============================================================================
# CAR TYPE CHARACTERISTICS
# Average weights and capacities by car type
# =============================================================================

CAR_TYPE_DATA = {
    # car_type: (tare_weight_tons, capacity_tons, avg_load_factor)
    'B': (32, 100, 0.92),   # Boxcar
    'C': (23, 105, 0.95),   # Covered hopper (grain)
    'F': (29, 100, 0.90),   # Flatcar
    'G': (33, 110, 0.93),   # Gondola
    'H': (22, 100, 0.94),   # Open hopper (coal)
    'J': (35, 95, 0.88),    # Auto rack
    'K': (38, 90, 0.85),    # Intermodal
    'P': (29, 100, 0.92),   # Intermodal platform
    'R': (36, 85, 0.82),    # Refrigerated
    'T': (28, 100, 0.91),   # Tank car
    'X': (30, 95, 0.90),    # Other/mixed
}

# =============================================================================
# COMMODITY-SPECIFIC ADJUSTMENTS
# Based on STCC 2-digit codes
# =============================================================================

COMMODITY_ADJUSTMENTS = {
    # stcc_2digit: (density_factor, special_handling_factor, avg_value_per_ton)
    '01': (1.0, 1.0, 250),      # Farm products
    '10': (1.2, 1.0, 150),      # Metallic ores
    '11': (1.1, 1.0, 50),       # Coal - high density
    '13': (0.9, 1.1, 80),       # Crude petroleum - liquid
    '14': (1.3, 1.0, 40),       # Non-metallic minerals (sand, gravel) - dense
    '20': (1.0, 1.1, 800),      # Food products
    '26': (0.8, 1.0, 600),      # Paper - low density
    '28': (1.0, 1.3, 1200),     # Chemicals - special handling
    '29': (0.9, 1.2, 500),      # Petroleum products - liquid
    '32': (1.2, 1.0, 100),      # Cement, stone, glass - dense
    '33': (1.4, 1.0, 800),      # Primary metals - very dense
    '37': (0.7, 1.2, 25000),    # Transportation equipment - bulky, high value
    '40': (0.8, 1.0, 200),      # Waste/scrap
    '46': (1.0, 1.0, 1000),     # Mixed freight
}


@dataclass
class ShipmentCharacteristics:
    """Input characteristics for a rail shipment."""
    tons: float                        # Net tons shipped
    miles: float                       # Route miles (loaded)
    car_type: str = 'X'                # Car type code
    num_cars: int = 1                  # Number of cars
    stcc: str = '00000'                # STCC commodity code
    origin_region: str = 'system'      # 'east', 'west', or 'system'
    dest_region: str = 'system'        # 'east', 'west', or 'system'
    is_unit_train: bool = False        # Unit train (>50 cars same commodity)
    is_intermodal: bool = False        # Intermodal shipment
    hazmat: bool = False               # Hazardous materials
    commodity_value: float = 0         # Value in dollars (for L&D)
    transit_days: Optional[int] = None # If known, otherwise estimated


@dataclass
class URCSCostBreakdown:
    """Detailed breakdown of URCS variable costs."""
    # Line-haul costs
    car_mile_cost: float = 0
    train_mile_cost: float = 0
    gross_ton_mile_cost: float = 0
    locomotive_cost: float = 0

    # Terminal costs
    terminal_switch_cost: float = 0
    yard_cost: float = 0

    # Car costs
    car_ownership_cost: float = 0

    # Administrative
    carload_admin_cost: float = 0

    # Other
    loss_damage_cost: float = 0
    special_service_cost: float = 0

    # Totals
    total_line_haul: float = 0
    total_terminal: float = 0
    total_car: float = 0
    total_admin: float = 0
    total_other: float = 0

    # Grand total
    total_variable_cost: float = 0

    # Per-unit metrics
    cost_per_ton: float = 0
    cost_per_car: float = 0
    cost_per_ton_mile: float = 0
    cost_per_car_mile: float = 0


def get_unit_costs(year: int, region: str = 'system') -> Dict[str, float]:
    """Get URCS unit costs for a given year and region."""
    if year not in URCS_UNIT_COSTS:
        # Use closest available year
        available = sorted(URCS_UNIT_COSTS.keys())
        if year < available[0]:
            year = available[0]
        else:
            year = available[-1]

    if region not in URCS_UNIT_COSTS[year]:
        region = 'system'

    return URCS_UNIT_COSTS[year][region]


def estimate_transit_days(miles: float, is_unit_train: bool = False) -> int:
    """Estimate transit days based on distance."""
    # Average train speed assumptions
    avg_speed_mph = 22 if is_unit_train else 18  # Unit trains faster
    hours_per_day = 18  # Not running 24/7

    running_days = miles / (avg_speed_mph * hours_per_day)

    # Add terminal time
    terminal_days = 1.0 if is_unit_train else 2.0

    return max(1, int(math.ceil(running_days + terminal_days)))


def estimate_cars_in_train(is_unit_train: bool) -> int:
    """Estimate average cars per train for cost allocation."""
    return 100 if is_unit_train else 65


def calculate_urcs_cost(
    shipment: ShipmentCharacteristics,
    year: int = 2023
) -> URCSCostBreakdown:
    """
    Calculate URCS variable cost for a rail shipment.

    This implements the STB URCS Phase III methodology to estimate
    the variable cost of transporting freight by rail.

    Args:
        shipment: ShipmentCharacteristics with shipment details
        year: Year for unit costs (default 2023)

    Returns:
        URCSCostBreakdown with detailed cost components
    """
    # Determine region for unit costs
    # If shipment crosses regions, use system average
    if shipment.origin_region != shipment.dest_region:
        region = 'system'
    else:
        region = shipment.origin_region

    uc = get_unit_costs(year, region)

    # Get car type data
    car_data = CAR_TYPE_DATA.get(shipment.car_type, CAR_TYPE_DATA['X'])
    tare_weight, capacity, load_factor = car_data

    # Get commodity adjustments
    stcc_2 = shipment.stcc[:2] if len(shipment.stcc) >= 2 else '00'
    commodity_adj = COMMODITY_ADJUSTMENTS.get(stcc_2, (1.0, 1.0, 500))
    density_factor, special_factor, default_value = commodity_adj

    # Calculate service units
    # -------------------------------------------------------------------

    # Loaded car-miles
    loaded_car_miles = shipment.miles * shipment.num_cars

    # Empty return miles (typically 60-80% of loaded, varies by car type)
    empty_ratio = 0.7 if shipment.car_type in ['H', 'G', 'C'] else 0.5
    empty_car_miles = loaded_car_miles * empty_ratio

    total_car_miles = loaded_car_miles + empty_car_miles

    # Gross ton-miles (loaded only)
    tons_per_car = shipment.tons / shipment.num_cars
    gross_tons_per_car = tons_per_car + tare_weight
    gross_ton_miles = gross_tons_per_car * loaded_car_miles

    # Train-miles (allocated based on cars in train)
    cars_in_train = estimate_cars_in_train(shipment.is_unit_train)
    train_miles = (shipment.miles * shipment.num_cars) / cars_in_train

    # Locomotive miles (assume 2 locomotives per train)
    locomotives_per_train = 2.0 if shipment.is_unit_train else 1.5
    locomotive_miles = train_miles * locomotives_per_train

    # Transit days
    if shipment.transit_days:
        transit_days = shipment.transit_days
    else:
        transit_days = estimate_transit_days(shipment.miles, shipment.is_unit_train)

    # Line-haul car-days
    line_haul_car_days = transit_days * shipment.num_cars * 0.6  # 60% in movement

    # Yard car-days
    yard_car_days = transit_days * shipment.num_cars * 0.4  # 40% in yards

    # Terminal switches (origin + destination)
    terminal_switches = 2 * shipment.num_cars

    # Calculate costs
    # -------------------------------------------------------------------
    result = URCSCostBreakdown()

    # Line-haul costs
    result.car_mile_cost = total_car_miles * uc['car_mile']
    result.train_mile_cost = train_miles * uc['train_mile']
    result.gross_ton_mile_cost = gross_ton_miles * uc['gross_ton_mile']
    result.locomotive_cost = locomotive_miles * uc['locomotive_mile']

    result.total_line_haul = (
        result.car_mile_cost +
        result.train_mile_cost +
        result.gross_ton_mile_cost +
        result.locomotive_cost
    )

    # Terminal costs
    result.terminal_switch_cost = terminal_switches * uc['switch_move']
    result.yard_cost = yard_car_days * uc['car_day_yard']

    result.total_terminal = (
        result.terminal_switch_cost +
        result.yard_cost
    )

    # Car costs (ownership/per diem)
    result.car_ownership_cost = (
        line_haul_car_days * uc['car_day_line'] +
        yard_car_days * uc['car_day_yard']
    )

    result.total_car = result.car_ownership_cost

    # Administrative costs
    result.carload_admin_cost = (
        shipment.num_cars * uc['carload_originated'] +
        shipment.num_cars * uc['carload_terminated']
    )

    result.total_admin = result.carload_admin_cost

    # Special services
    if shipment.hazmat:
        result.special_service_cost = shipment.num_cars * 150  # Hazmat surcharge

    if special_factor > 1.0:
        result.special_service_cost += (special_factor - 1.0) * result.total_line_haul

    # Loss and damage
    if shipment.commodity_value > 0:
        value_thousands = shipment.commodity_value / 1000
    else:
        value_thousands = (shipment.tons * default_value) / 1000

    result.loss_damage_cost = value_thousands * uc['loss_damage_rate']

    result.total_other = result.special_service_cost + result.loss_damage_cost

    # Grand total
    result.total_variable_cost = (
        result.total_line_haul +
        result.total_terminal +
        result.total_car +
        result.total_admin +
        result.total_other
    )

    # Unit train discount (lower costs due to efficiency)
    if shipment.is_unit_train:
        result.total_variable_cost *= 0.85  # 15% efficiency gain

    # Per-unit metrics
    result.cost_per_ton = result.total_variable_cost / shipment.tons
    result.cost_per_car = result.total_variable_cost / shipment.num_cars
    result.cost_per_ton_mile = result.total_variable_cost / (shipment.tons * shipment.miles)
    result.cost_per_car_mile = result.total_variable_cost / loaded_car_miles

    return result


def calculate_rvc_ratio(
    actual_revenue: float,
    shipment: ShipmentCharacteristics,
    year: int = 2023
) -> Tuple[float, URCSCostBreakdown]:
    """
    Calculate Revenue-to-Variable-Cost (R/VC) ratio.

    The R/VC ratio is a key regulatory metric:
    - R/VC < 100%: Railroad losing money on shipment
    - R/VC = 100-180%: Competitive pricing
    - R/VC > 180%: STB jurisdiction threshold for rate reasonableness

    Args:
        actual_revenue: Actual freight revenue in dollars
        shipment: ShipmentCharacteristics
        year: Year for URCS costs

    Returns:
        Tuple of (R/VC ratio as percentage, URCSCostBreakdown)
    """
    cost = calculate_urcs_cost(shipment, year)
    rvc_ratio = (actual_revenue / cost.total_variable_cost) * 100

    return rvc_ratio, cost


def get_stb_jurisdiction_threshold() -> float:
    """
    Return the current STB R/VC threshold for rate reasonableness jurisdiction.

    As of 2023, the threshold is 180% of variable cost.
    """
    return 180.0


# =============================================================================
# DATABASE INTEGRATION
# =============================================================================

def init_urcs_tables(conn):
    """Initialize URCS-related tables in the database."""

    # Create unit costs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_urcs_unit_costs (
            year INTEGER,
            region VARCHAR(10),
            car_mile DECIMAL(8,4),
            train_mile DECIMAL(8,2),
            gross_ton_mile DECIMAL(8,6),
            locomotive_mile DECIMAL(8,4),
            car_day_yard DECIMAL(8,2),
            switch_move DECIMAL(8,2),
            terminal_switch DECIMAL(8,2),
            car_day_line DECIMAL(8,2),
            car_day_total DECIMAL(8,2),
            carload_originated DECIMAL(8,2),
            carload_terminated DECIMAL(8,2),
            loss_damage_rate DECIMAL(8,4),
            PRIMARY KEY (year, region)
        )
    """)

    # Load unit costs
    for year, regions in URCS_UNIT_COSTS.items():
        for region, costs in regions.items():
            conn.execute("""
                INSERT OR REPLACE INTO dim_urcs_unit_costs VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                year, region,
                costs['car_mile'], costs['train_mile'], costs['gross_ton_mile'],
                costs['locomotive_mile'], costs['car_day_yard'], costs['switch_move'],
                costs['terminal_switch'], costs['car_day_line'], costs['car_day_total'],
                costs['carload_originated'], costs['carload_terminated'],
                costs['loss_damage_rate']
            ])

    # Create car type dimension
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_car_characteristics (
            car_type VARCHAR(1) PRIMARY KEY,
            car_name VARCHAR(50),
            tare_weight_tons DECIMAL(6,1),
            capacity_tons DECIMAL(6,1),
            avg_load_factor DECIMAL(4,2)
        )
    """)

    car_names = {
        'B': 'Boxcar', 'C': 'Covered Hopper', 'F': 'Flatcar',
        'G': 'Gondola', 'H': 'Open Hopper', 'J': 'Auto Rack',
        'K': 'Intermodal', 'P': 'Intermodal Platform',
        'R': 'Refrigerated', 'T': 'Tank Car', 'X': 'Other'
    }

    for car_type, (tare, cap, lf) in CAR_TYPE_DATA.items():
        conn.execute("""
            INSERT OR REPLACE INTO dim_car_characteristics VALUES (?, ?, ?, ?, ?)
        """, [car_type, car_names.get(car_type, 'Unknown'), tare, cap, lf])

    print(f"Initialized URCS tables:")
    print(f"  - dim_urcs_unit_costs: {len(URCS_UNIT_COSTS)} years x 3 regions")
    print(f"  - dim_car_characteristics: {len(CAR_TYPE_DATA)} car types")


def create_urcs_views(conn):
    """Create URCS analytical views for waybill data."""

    # First, create a helper view to calculate distances from BEA coordinates
    # Uses Haversine formula with 1.25 circuity factor for rail routes
    conn.execute("""
        CREATE OR REPLACE VIEW v_waybill_with_distance AS
        SELECT
            w.*,
            -- Calculate great circle distance * circuity factor
            -- Haversine formula: 3959 miles = Earth radius
            ROUND(
                3959 * 2 * ASIN(SQRT(
                    POWER(SIN(RADIANS(d.lat - o.lat) / 2), 2) +
                    COS(RADIANS(o.lat)) * COS(RADIANS(d.lat)) *
                    POWER(SIN(RADIANS(d.lon - o.lon) / 2), 2)
                )) * 1.25,  -- 1.25 circuity factor for rail
            0) as est_miles
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        WHERE o.lat IS NOT NULL AND d.lat IS NOT NULL
    """)

    # R/VC analysis view - uses estimated distance from BEA coordinates
    conn.execute("""
        CREATE OR REPLACE VIEW v_rvc_analysis AS
        SELECT
            w.stcc,
            s.description as commodity,
            w.car_type,
            CAST(w.exp_carloads AS INTEGER) as carloads,
            ROUND(w.exp_tons, 0) as tons,
            w.est_miles as miles,
            ROUND(w.exp_freight_rev, 2) as revenue,
            -- Approximate URCS variable cost calculation
            ROUND(
                -- Car-mile cost (loaded + empty return)
                (w.est_miles * w.exp_carloads * 1.6 * u.car_mile) +
                -- Gross ton-mile cost
                ((w.exp_tons + (30 * w.exp_carloads)) * w.est_miles * u.gross_ton_mile) +
                -- Train-mile cost (allocated)
                ((w.est_miles * w.exp_carloads / 65.0) * u.train_mile) +
                -- Terminal costs
                (w.exp_carloads * 2 * u.switch_move) +
                -- Car-days (estimated)
                (w.exp_carloads * (w.est_miles / 300 + 1) * u.car_day_total) +
                -- Administrative
                (w.exp_carloads * (u.carload_originated + u.carload_terminated))
            , 2) as est_variable_cost,
            -- R/VC ratio
            ROUND(
                w.exp_freight_rev /
                NULLIF(
                    (w.est_miles * w.exp_carloads * 1.6 * u.car_mile) +
                    ((w.exp_tons + (30 * w.exp_carloads)) * w.est_miles * u.gross_ton_mile) +
                    ((w.est_miles * w.exp_carloads / 65.0) * u.train_mile) +
                    (w.exp_carloads * 2 * u.switch_move) +
                    (w.exp_carloads * (w.est_miles / 300 + 1) * u.car_day_total) +
                    (w.exp_carloads * (u.carload_originated + u.carload_terminated))
                , 0) * 100
            , 1) as rvc_ratio
        FROM v_waybill_with_distance w
        LEFT JOIN dim_stcc s ON w.stcc = s.stcc_code
        LEFT JOIN dim_urcs_unit_costs u ON u.year = 2023 AND u.region = 'system'
        WHERE w.exp_freight_rev > 0
          AND w.est_miles > 0
          AND w.exp_carloads > 0
    """)

    # R/VC distribution by commodity
    conn.execute("""
        CREATE OR REPLACE VIEW v_rvc_by_commodity AS
        SELECT
            LEFT(stcc, 2) as stcc_2digit,
            commodity,
            COUNT(*) as shipments,
            ROUND(AVG(rvc_ratio), 1) as avg_rvc,
            ROUND(MIN(rvc_ratio), 1) as min_rvc,
            ROUND(MAX(rvc_ratio), 1) as max_rvc,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rvc_ratio), 1) as p25_rvc,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rvc_ratio), 1) as p75_rvc,
            SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold,
            ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                as pct_above_threshold
        FROM v_rvc_analysis
        WHERE rvc_ratio > 0 AND rvc_ratio < 1000  -- Filter outliers
        GROUP BY LEFT(stcc, 2), commodity
        ORDER BY avg_rvc DESC
    """)

    # R/VC by distance band
    conn.execute("""
        CREATE OR REPLACE VIEW v_rvc_by_distance AS
        SELECT
            CASE
                WHEN miles < 250 THEN 'Short (<250 mi)'
                WHEN miles < 500 THEN 'Medium (250-500 mi)'
                WHEN miles < 1000 THEN 'Long (500-1000 mi)'
                ELSE 'Very Long (>1000 mi)'
            END as distance_band,
            COUNT(*) as shipments,
            ROUND(AVG(rvc_ratio), 1) as avg_rvc,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
            SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold,
            ROUND(AVG(revenue / tons), 2) as avg_rev_per_ton,
            ROUND(AVG(est_variable_cost / tons), 2) as avg_cost_per_ton
        FROM v_rvc_analysis
        WHERE rvc_ratio > 0 AND rvc_ratio < 1000
        GROUP BY 1
        ORDER BY 1
    """)

    print("Created URCS analytical views:")
    print("  - v_rvc_analysis: Shipment-level R/VC calculations")
    print("  - v_rvc_by_commodity: R/VC distribution by commodity")
    print("  - v_rvc_by_distance: R/VC by distance band")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_cost_estimate(
    tons: float,
    miles: float,
    car_type: str = 'C',
    year: int = 2023
) -> float:
    """
    Quick URCS cost estimate for a single carload.

    Args:
        tons: Net tons
        miles: Route miles
        car_type: Car type code
        year: Cost year

    Returns:
        Estimated variable cost in dollars
    """
    shipment = ShipmentCharacteristics(
        tons=tons,
        miles=miles,
        car_type=car_type,
        num_cars=1,
    )
    result = calculate_urcs_cost(shipment, year)
    return result.total_variable_cost


def quick_rvc(
    revenue: float,
    tons: float,
    miles: float,
    car_type: str = 'C',
    year: int = 2023
) -> float:
    """
    Quick R/VC ratio calculation.

    Args:
        revenue: Actual freight revenue
        tons: Net tons
        miles: Route miles
        car_type: Car type code
        year: Cost year

    Returns:
        R/VC ratio as percentage
    """
    cost = quick_cost_estimate(tons, miles, car_type, year)
    return (revenue / cost) * 100


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("URCS COST MODEL DEMONSTRATION")
    print("=" * 60)

    # Example 1: Single carload of cement
    print("\n--- Example 1: Cement Shipment (1 car, 100 tons, 500 miles) ---")
    shipment1 = ShipmentCharacteristics(
        tons=100,
        miles=500,
        car_type='C',  # Covered hopper
        num_cars=1,
        stcc='32411',  # Cement
    )
    cost1 = calculate_urcs_cost(shipment1, 2023)
    print(f"Total Variable Cost: ${cost1.total_variable_cost:,.2f}")
    print(f"  Line-haul: ${cost1.total_line_haul:,.2f}")
    print(f"  Terminal: ${cost1.total_terminal:,.2f}")
    print(f"  Car costs: ${cost1.total_car:,.2f}")
    print(f"  Admin: ${cost1.total_admin:,.2f}")
    print(f"Cost per ton: ${cost1.cost_per_ton:.2f}")
    print(f"Cost per ton-mile: ${cost1.cost_per_ton_mile:.4f}")

    # Example 2: Unit train of coal
    print("\n--- Example 2: Coal Unit Train (100 cars, 11,000 tons, 800 miles) ---")
    shipment2 = ShipmentCharacteristics(
        tons=11000,
        miles=800,
        car_type='H',  # Open hopper
        num_cars=100,
        stcc='11211',  # Coal
        is_unit_train=True,
    )
    cost2 = calculate_urcs_cost(shipment2, 2023)
    print(f"Total Variable Cost: ${cost2.total_variable_cost:,.2f}")
    print(f"Cost per ton: ${cost2.cost_per_ton:.2f}")
    print(f"Cost per ton-mile: ${cost2.cost_per_ton_mile:.4f}")

    # Example 3: R/VC ratio calculation
    print("\n--- Example 3: R/VC Ratio Analysis ---")
    actual_revenue = 5000  # $5,000 revenue
    rvc_ratio, _ = calculate_rvc_ratio(actual_revenue, shipment1, 2023)
    print(f"Revenue: ${actual_revenue:,.2f}")
    print(f"Variable Cost: ${cost1.total_variable_cost:,.2f}")
    print(f"R/VC Ratio: {rvc_ratio:.1f}%")
    print(f"STB Threshold: {get_stb_jurisdiction_threshold()}%")
    if rvc_ratio > get_stb_jurisdiction_threshold():
        print("  -> Above STB jurisdiction threshold")
    else:
        print("  -> Below STB jurisdiction threshold")

    # Example 4: Quick estimates
    print("\n--- Example 4: Quick Cost Estimates ---")
    for miles in [100, 500, 1000, 2000]:
        cost = quick_cost_estimate(100, miles)
        print(f"  {miles} miles: ${cost:,.2f} (${cost/100:.2f}/ton)")
