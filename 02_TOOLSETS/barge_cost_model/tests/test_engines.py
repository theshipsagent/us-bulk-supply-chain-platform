"""
Unit tests for routing and cost engines.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, patch
import networkx as nx

from src.models.route import ComputedRoute, RouteConstraints, RouteCost, RouteSegment


class TestRoutingEngine:
    """Test routing engine functionality."""

    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing."""
        G = nx.DiGraph()
        G.add_edge(1, 2, linknum=100, length=10.0, rivername='River A')
        G.add_edge(2, 3, linknum=101, length=15.0, rivername='River A')
        G.add_edge(3, 4, linknum=102, length=20.0, rivername='River B')
        G.add_edge(1, 3, linknum=103, length=30.0, rivername='River B')  # Alternative route
        return G

    def test_graph_creation(self, sample_graph):
        """Test graph structure."""
        assert len(sample_graph.nodes()) == 4
        assert len(sample_graph.edges()) == 4
        assert sample_graph.has_edge(1, 2)

    def test_shortest_path(self, sample_graph):
        """Test Dijkstra's shortest path."""
        path = nx.dijkstra_path(sample_graph, 1, 4, weight='length')
        assert path == [1, 2, 3, 4]  # Shortest by length

    def test_path_length(self, sample_graph):
        """Test path length calculation."""
        path = nx.dijkstra_path(sample_graph, 1, 4, weight='length')
        length = sum(
            sample_graph[path[i]][path[i+1]]['length']
            for i in range(len(path) - 1)
        )
        assert length == 45.0  # 10 + 15 + 20

    def test_alternative_path(self, sample_graph):
        """Test finding multiple paths."""
        paths = list(nx.shortest_simple_paths(sample_graph, 1, 4, weight='length'))
        assert len(paths) >= 2  # At least 2 paths exist
        assert paths[0] == [1, 2, 3, 4]  # Shortest
        assert paths[1] == [1, 3, 4]  # Alternative


class TestCostEngine:
    """Test cost calculation engine."""

    @pytest.fixture
    def sample_route(self):
        """Create a sample route for testing."""
        segments = [
            RouteSegment(linknum=100, anode=1, bnode=2, length_miles=10.0, rivername='River A'),
            RouteSegment(linknum=101, anode=2, bnode=3, length_miles=15.0, rivername='River A'),
        ]

        return ComputedRoute(
            origin_node=1,
            dest_node=3,
            node_path=[1, 2, 3],
            segments=segments,
            total_distance_miles=25.0,
            total_distance_km=40.2,
            transit_time_hours=5.0,  # 25 miles / 5 mph
            transit_time_days=0.208,
            num_locks=2,
            lock_names=['Lock A', 'Lock B'],
            total_lock_delay_hours=4.0,
        )

    def test_fuel_cost_calculation(self):
        """Test fuel cost calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        gallons, cost = engine.calculate_fuel_cost(transit_time_hours=24.0)

        assert gallons > 0
        assert cost > 0
        assert cost == gallons * engine.constants['fuel_price_per_gallon_usd']

    def test_crew_cost_calculation(self):
        """Test crew cost calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        cost = engine.calculate_crew_cost(
            transit_time_hours=24.0,
            lock_delay_hours=4.0
        )

        expected_days = 28.0 / 24  # (24 + 4) / 24
        expected_cost = engine.constants['crew_size'] * engine.constants['crew_cost_per_day_usd'] * expected_days

        assert cost == expected_cost

    def test_lock_costs(self):
        """Test lock passage costs."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        fees, delay = engine.calculate_lock_costs(num_locks=3)

        assert fees == 3 * engine.constants['lock_fee_usd']
        assert delay == 3 * 2.0  # Default 2 hours per lock

    def test_terminal_fees(self):
        """Test terminal fee calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        origin_fee, dest_fee = engine.calculate_terminal_fees()

        assert origin_fee == engine.constants['terminal_fee_usd']
        assert dest_fee == engine.constants['terminal_fee_usd']

    def test_total_route_cost(self, sample_route):
        """Test complete route cost calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        cost = engine.calculate_route_cost(sample_route)

        assert isinstance(cost, RouteCost)
        assert cost.total_cost_usd > 0
        assert cost.fuel_cost_usd > 0
        assert cost.crew_cost_usd > 0
        assert cost.lock_fees_usd > 0

    def test_cost_per_ton(self):
        """Test cost per ton calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        cost_per_ton = engine.calculate_cost_per_ton(
            total_cost_usd=5000.0,
            cargo_tons=1000
        )

        assert cost_per_ton == 5.0  # $5 per ton

    def test_cost_per_ton_mile(self):
        """Test cost per ton-mile calculation."""
        from src.engines.cost_engine import CostEngine

        engine = CostEngine()
        cost_per_ton_mile = engine.calculate_cost_per_ton_mile(
            total_cost_usd=5000.0,
            cargo_tons=1000,
            distance_miles=100
        )

        assert cost_per_ton_mile == 0.05  # $0.05 per ton-mile


class TestRouteConstraints:
    """Test route constraint checking."""

    def test_lock_compatibility(self):
        """Test vessel lock compatibility check."""
        constraints = RouteConstraints(
            vessel_beam_m=10.0,
            vessel_length_m=60.0,
            beam_safety_margin_m=0.5
        )

        # Lock that's too narrow
        assert not constraints.check_lock_compatibility(
            lock_width_m=10.0,  # Too narrow (10.0 < 10.5 with margin)
            lock_length_m=100.0
        )

        # Lock that fits
        assert constraints.check_lock_compatibility(
            lock_width_m=15.0,  # Wide enough
            lock_length_m=100.0  # Long enough
        )

    def test_vessel_constraint_methods(self):
        """Test vessel model constraint methods."""
        from src.models.vessel import Vessel

        vessel = Vessel(
            imo='1234567',
            beam=10.0,
            depth_m=3.0,
            loa=60.0
        )

        # Test lock passage
        assert vessel.can_pass_lock(lock_width_feet=40.0, lock_length_feet=200.0)  # Fits
        assert not vessel.can_pass_lock(lock_width_feet=20.0, lock_length_feet=200.0)  # Too narrow

        # Test channel navigation
        assert vessel.can_navigate_channel(channel_depth_m=5.0)  # Enough depth
        assert not vessel.can_navigate_channel(channel_depth_m=3.0)  # Too shallow


class TestRouteComparison:
    """Test route comparison functionality."""

    @pytest.fixture
    def sample_routes(self):
        """Create sample routes for comparison."""
        route1 = ComputedRoute(
            origin_node=1,
            dest_node=3,
            node_path=[1, 2, 3],
            segments=[],
            total_distance_miles=25.0,
            transit_time_hours=5.0,
            num_locks=1,
            cost=RouteCost(
                fuel_gallons=50.0,
                fuel_cost_usd=175.0,
                crew_days=0.5,
                crew_cost_usd=400.0,
                num_locks=1,
                lock_fees_usd=50.0,
                origin_terminal_fee_usd=750.0,
                dest_terminal_fee_usd=750.0
            )
        )

        route2 = ComputedRoute(
            origin_node=1,
            dest_node=3,
            node_path=[1, 4, 3],
            segments=[],
            total_distance_miles=30.0,
            transit_time_hours=6.0,
            num_locks=0,
            cost=RouteCost(
                fuel_gallons=60.0,
                fuel_cost_usd=210.0,
                crew_days=0.6,
                crew_cost_usd=480.0,
                num_locks=0,
                lock_fees_usd=0.0,
                origin_terminal_fee_usd=750.0,
                dest_terminal_fee_usd=750.0
            )
        )

        return [route1, route2]

    def test_route_comparison(self, sample_routes):
        """Test route comparison logic."""
        from src.models.route import RouteComparison

        comparison = RouteComparison(routes=sample_routes)

        # Shortest distance
        shortest = comparison.shortest_distance_route
        assert shortest.total_distance_miles == 25.0

        # Fastest route
        fastest = comparison.fastest_route
        assert fastest.total_time_hours == 5.0

        # Cheapest route
        cheapest = comparison.cheapest_route
        assert cheapest is not None


if __name__ == "__main__":
    """Run tests."""
    pytest.main([__file__, '-v'])
