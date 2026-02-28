"""
Cost calculation engine for waterway transportation.

Calculates comprehensive costs including fuel, crew, locks, terminals, and delays.
Based on formulas from BargeTariffCalculator in knowledge base.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
import logging

from src.config.settings import settings, COST_CONSTANTS
from src.models.route import ComputedRoute, RouteCost

logger = logging.getLogger(__name__)


class CostEngine:
    """
    Waterway transportation cost calculator.

    Calculates costs based on:
    - Fuel consumption (gallons/day × fuel price)
    - Crew costs (crew size × daily rate × days)
    - Lock passage fees (per lock)
    - Terminal fees (origin + destination)
    - Time-based costs (delays, waiting)
    """

    def __init__(self, cost_constants: Optional[dict] = None):
        """
        Initialize cost engine.

        Args:
            cost_constants: Optional custom cost constants (defaults to settings.COST_CONSTANTS)
        """
        self.constants = cost_constants or COST_CONSTANTS

    def calculate_fuel_cost(
        self,
        transit_time_hours: float,
        vessel_dwt: Optional[int] = None
    ) -> tuple[float, float]:
        """
        Calculate fuel consumption and cost.

        Args:
            transit_time_hours: Total transit time in hours
            vessel_dwt: Vessel deadweight tonnage (optional, for size adjustment)

        Returns:
            Tuple of (gallons consumed, total cost in USD)
        """
        # Base consumption rate (gallons per day)
        base_consumption = self.constants['fuel_consumption_gallons_per_day']

        # Adjust for vessel size if provided
        if vessel_dwt:
            # Larger vessels use more fuel (rough approximation)
            size_factor = max(1.0, vessel_dwt / 10000)  # Normalize around 10k DWT
            consumption_rate = base_consumption * size_factor
        else:
            consumption_rate = base_consumption

        # Calculate total consumption
        transit_days = transit_time_hours / 24
        total_gallons = consumption_rate * transit_days

        # Calculate cost
        fuel_price = self.constants['fuel_price_per_gallon_usd']
        total_cost = total_gallons * fuel_price

        return total_gallons, total_cost

    def calculate_crew_cost(
        self,
        transit_time_hours: float,
        lock_delay_hours: float = 0.0,
        crew_size: Optional[int] = None
    ) -> float:
        """
        Calculate crew costs.

        Args:
            transit_time_hours: Transit time in hours
            lock_delay_hours: Additional time at locks in hours
            crew_size: Number of crew members (defaults to settings value)

        Returns:
            Total crew cost in USD
        """
        # Total time including delays
        total_hours = transit_time_hours + lock_delay_hours
        total_days = total_hours / 24

        # Crew parameters
        crew = crew_size or self.constants['crew_size']
        daily_cost_per_person = self.constants['crew_cost_per_day_usd']

        # Calculate total crew cost
        total_cost = crew * daily_cost_per_person * total_days

        return total_cost

    def calculate_lock_costs(
        self,
        num_locks: int,
        avg_delay_per_lock_hours: float = 2.0
    ) -> tuple[float, float]:
        """
        Calculate lock passage fees and delay costs.

        Args:
            num_locks: Number of locks to pass
            avg_delay_per_lock_hours: Average delay time per lock

        Returns:
            Tuple of (lock fees USD, total delay hours)
        """
        # Lock passage fees
        fee_per_lock = self.constants['lock_fee_usd']
        total_fees = num_locks * fee_per_lock

        # Total delay time
        total_delay_hours = num_locks * avg_delay_per_lock_hours

        return total_fees, total_delay_hours

    def calculate_terminal_fees(
        self,
        include_origin: bool = True,
        include_destination: bool = True
    ) -> tuple[float, float]:
        """
        Calculate terminal handling fees.

        Args:
            include_origin: Include origin terminal fee
            include_destination: Include destination terminal fee

        Returns:
            Tuple of (origin fee USD, destination fee USD)
        """
        terminal_fee = self.constants['terminal_fee_usd']

        origin_fee = terminal_fee if include_origin else 0.0
        dest_fee = terminal_fee if include_destination else 0.0

        return origin_fee, dest_fee

    def calculate_route_cost(
        self,
        route: ComputedRoute,
        vessel_dwt: Optional[int] = None,
        crew_size: Optional[int] = None,
        include_terminals: bool = True
    ) -> RouteCost:
        """
        Calculate comprehensive costs for a complete route.

        Args:
            route: ComputedRoute object with distance and time metrics
            vessel_dwt: Vessel deadweight tonnage (for fuel adjustment)
            crew_size: Crew size (defaults to settings)
            include_terminals: Whether to include terminal fees

        Returns:
            RouteCost object with itemized breakdown
        """
        # Fuel costs
        fuel_gallons, fuel_cost = self.calculate_fuel_cost(
            transit_time_hours=route.transit_time_hours,
            vessel_dwt=vessel_dwt
        )

        # Crew costs
        crew_cost = self.calculate_crew_cost(
            transit_time_hours=route.transit_time_hours,
            lock_delay_hours=route.total_lock_delay_hours,
            crew_size=crew_size
        )

        # Lock costs
        lock_fees, lock_delay_hours = self.calculate_lock_costs(
            num_locks=route.num_locks
        )

        # Terminal fees
        if include_terminals:
            origin_fee, dest_fee = self.calculate_terminal_fees()
        else:
            origin_fee, dest_fee = 0.0, 0.0

        # Build cost object
        cost = RouteCost(
            fuel_gallons=fuel_gallons,
            fuel_cost_usd=fuel_cost,
            crew_days=route.total_time_hours / 24,
            crew_cost_usd=crew_cost,
            num_locks=route.num_locks,
            lock_fees_usd=lock_fees,
            lock_delay_hours=lock_delay_hours,
            origin_terminal_fee_usd=origin_fee,
            dest_terminal_fee_usd=dest_fee
        )

        return cost

    def calculate_cost_per_ton(
        self,
        total_cost_usd: float,
        cargo_tons: int
    ) -> float:
        """
        Calculate cost per ton of cargo.

        Args:
            total_cost_usd: Total transportation cost
            cargo_tons: Cargo tonnage

        Returns:
            Cost per ton in USD
        """
        if cargo_tons <= 0:
            return 0.0

        return total_cost_usd / cargo_tons

    def calculate_cost_per_ton_mile(
        self,
        total_cost_usd: float,
        cargo_tons: int,
        distance_miles: float
    ) -> float:
        """
        Calculate cost per ton-mile (standard freight metric).

        Args:
            total_cost_usd: Total transportation cost
            cargo_tons: Cargo tonnage
            distance_miles: Distance traveled

        Returns:
            Cost per ton-mile in USD
        """
        if cargo_tons <= 0 or distance_miles <= 0:
            return 0.0

        ton_miles = cargo_tons * distance_miles
        return total_cost_usd / ton_miles

    def estimate_trip_profitability(
        self,
        total_cost_usd: float,
        cargo_tons: int,
        revenue_per_ton_usd: float
    ) -> dict:
        """
        Estimate trip profitability.

        Args:
            total_cost_usd: Total trip cost
            cargo_tons: Cargo tonnage
            revenue_per_ton_usd: Revenue earned per ton

        Returns:
            Dictionary with revenue, cost, profit, and margin
        """
        total_revenue = cargo_tons * revenue_per_ton_usd
        profit = total_revenue - total_cost_usd
        margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            'revenue_usd': total_revenue,
            'cost_usd': total_cost_usd,
            'profit_usd': profit,
            'margin_percent': margin,
            'profitable': profit > 0
        }

    def compare_routes(
        self,
        routes: list[ComputedRoute],
        vessel_dwt: Optional[int] = None
    ) -> dict:
        """
        Compare costs across multiple routes.

        Args:
            routes: List of ComputedRoute objects
            vessel_dwt: Vessel deadweight tonnage

        Returns:
            Comparison dictionary with best options
        """
        route_costs = []

        for route in routes:
            cost = self.calculate_route_cost(route, vessel_dwt=vessel_dwt)
            route.cost = cost  # Attach cost to route

            route_costs.append({
                'route': route,
                'total_cost': cost.total_cost_usd,
                'cost_per_mile': cost.total_cost_usd / route.total_distance_miles if route.total_distance_miles > 0 else 0,
                'time_hours': route.total_time_hours,
            })

        # Find best options
        cheapest = min(route_costs, key=lambda x: x['total_cost']) if route_costs else None
        fastest = min(route_costs, key=lambda x: x['time_hours']) if route_costs else None

        return {
            'routes': route_costs,
            'cheapest': cheapest,
            'fastest': fastest,
            'num_compared': len(routes)
        }


# Convenience function
def calculate_cost(
    route: ComputedRoute,
    vessel_dwt: Optional[int] = None,
    crew_size: Optional[int] = None,
    include_terminals: bool = True
) -> RouteCost:
    """
    Quick cost calculation for a route.

    Args:
        route: Route to calculate costs for
        vessel_dwt: Vessel deadweight tonnage
        crew_size: Crew size
        include_terminals: Include terminal fees

    Returns:
        RouteCost object
    """
    engine = CostEngine()
    return engine.calculate_route_cost(
        route=route,
        vessel_dwt=vessel_dwt,
        crew_size=crew_size,
        include_terminals=include_terminals
    )


if __name__ == "__main__":
    """Test cost engine."""
    print("=" * 80)
    print("COST ENGINE TEST")
    print("=" * 80)

    engine = CostEngine()

    # Display cost constants
    print("\nCost Constants:")
    for key, value in engine.constants.items():
        print(f"  {key}: {value}")

    # Test 1: Fuel cost
    print("\n[1/4] Fuel Cost Calculation")
    gallons, cost = engine.calculate_fuel_cost(transit_time_hours=48.0, vessel_dwt=15000)
    print(f"  48 hours @ 15k DWT: {gallons:.1f} gallons, ${cost:,.2f}")

    # Test 2: Crew cost
    print("\n[2/4] Crew Cost Calculation")
    crew_cost = engine.calculate_crew_cost(transit_time_hours=48.0, lock_delay_hours=8.0)
    print(f"  48hr transit + 8hr delay: ${crew_cost:,.2f}")

    # Test 3: Lock costs
    print("\n[3/4] Lock Costs")
    lock_fees, delay_hours = engine.calculate_lock_costs(num_locks=5)
    print(f"  5 locks: ${lock_fees:,.2f} fees, {delay_hours:.1f} hours delay")

    # Test 4: Terminal fees
    print("\n[4/4] Terminal Fees")
    origin_fee, dest_fee = engine.calculate_terminal_fees()
    print(f"  Origin: ${origin_fee:,.2f}, Destination: ${dest_fee:,.2f}")

    total_example = cost + crew_cost + lock_fees + origin_fee + dest_fee
    print(f"\n  Example Total Cost: ${total_example:,.2f}")

    print("\n" + "=" * 80)
    print("✓ Cost engine initialized successfully")
    print("=" * 80)
