"""
Pydantic models for route planning and computed routes.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field


class RouteSegment(BaseModel):
    """Individual segment of a route."""

    linknum: int = Field(..., description="Waterway link number")
    anode: int = Field(..., description="Start node")
    bnode: int = Field(..., description="End node")
    length_miles: float = Field(..., ge=0, description="Segment length in miles")
    rivername: Optional[str] = None
    has_lock: bool = Field(default=False, description="Whether this segment has a lock")
    lock_name: Optional[str] = None


class RouteCost(BaseModel):
    """Detailed cost breakdown for a route."""

    # Fuel costs
    fuel_gallons: float = Field(..., ge=0, description="Total fuel consumption in gallons")
    fuel_cost_usd: float = Field(..., ge=0, description="Total fuel cost")

    # Crew costs
    crew_days: float = Field(..., ge=0, description="Crew time in days")
    crew_cost_usd: float = Field(..., ge=0, description="Total crew cost")

    # Lock costs
    num_locks: int = Field(..., ge=0, description="Number of locks passed")
    lock_fees_usd: float = Field(..., ge=0, description="Total lock passage fees")
    lock_delay_hours: float = Field(default=0, ge=0, description="Total lock delay time")

    # Terminal costs
    origin_terminal_fee_usd: float = Field(default=0, ge=0)
    dest_terminal_fee_usd: float = Field(default=0, ge=0)

    # Totals
    @computed_field
    @property
    def total_cost_usd(self) -> float:
        """Calculate total route cost."""
        return (
            self.fuel_cost_usd +
            self.crew_cost_usd +
            self.lock_fees_usd +
            self.origin_terminal_fee_usd +
            self.dest_terminal_fee_usd
        )

    @computed_field
    @property
    def cost_per_mile_usd(self) -> Optional[float]:
        """Cost per mile (requires distance from parent route)."""
        return None  # Calculated by parent Route object


class RouteConstraints(BaseModel):
    """Constraints that must be satisfied for a route."""

    vessel_beam_m: Optional[float] = Field(None, ge=0, description="Vessel beam in meters")
    vessel_draft_m: Optional[float] = Field(None, ge=0, description="Vessel draft in meters")
    vessel_length_m: Optional[float] = Field(None, ge=0, description="Vessel length in meters")

    max_lock_wait_hours: float = Field(default=24, ge=0, description="Maximum acceptable lock wait time")
    min_channel_depth_m: float = Field(default=2.7, ge=0, description="Minimum channel depth required")

    # Safety margins
    beam_safety_margin_m: float = Field(default=0.5, ge=0, description="Lock width safety margin")
    draft_safety_margin_m: float = Field(default=1.5, ge=0, description="Under-keel clearance")

    def check_lock_compatibility(self, lock_width_m: float, lock_length_m: float) -> bool:
        """Check if vessel can pass through a lock."""
        if self.vessel_beam_m and lock_width_m:
            if self.vessel_beam_m + self.beam_safety_margin_m > lock_width_m:
                return False

        if self.vessel_length_m and lock_length_m:
            if self.vessel_length_m + self.beam_safety_margin_m > lock_length_m:
                return False

        return True


class ComputedRoute(BaseModel):
    """Complete computed route with all metrics."""

    model_config = ConfigDict(from_attributes=True)

    # Route identification
    route_id: Optional[int] = None
    origin_node: int = Field(..., description="Starting node")
    dest_node: int = Field(..., description="Destination node")
    origin_dock_name: Optional[str] = None
    dest_dock_name: Optional[str] = None

    # Vessel information
    vessel_imo: Optional[str] = None
    vessel_name: Optional[str] = None

    # Route path
    node_path: List[int] = Field(..., description="Sequence of nodes in route")
    segments: List[RouteSegment] = Field(..., description="Detailed route segments")

    # Distance and time metrics
    total_distance_miles: float = Field(..., ge=0)
    total_distance_km: Optional[float] = None
    transit_time_hours: float = Field(..., ge=0)
    transit_time_days: Optional[float] = None

    # Lock information
    num_locks: int = Field(default=0, ge=0)
    lock_names: List[str] = Field(default_factory=list)
    total_lock_delay_hours: float = Field(default=0, ge=0)

    # Cost breakdown
    cost: Optional[RouteCost] = None

    # Metadata
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    algorithm_used: str = Field(default="dijkstra", description="Routing algorithm used")
    constraints_applied: Optional[RouteConstraints] = None
    is_feasible: bool = Field(default=True, description="Whether route satisfies all constraints")
    feasibility_notes: Optional[str] = None

    created_at: Optional[datetime] = None

    @computed_field
    @property
    def total_time_hours(self) -> float:
        """Total time including transit and lock delays."""
        return self.transit_time_hours + self.total_lock_delay_hours

    @computed_field
    @property
    def average_speed_mph(self) -> float:
        """Calculate average speed (not including lock delays)."""
        if self.transit_time_hours == 0:
            return 0
        return self.total_distance_miles / self.transit_time_hours

    @computed_field
    @property
    def cost_per_mile(self) -> Optional[float]:
        """Calculate cost per mile."""
        if self.cost and self.total_distance_miles > 0:
            return self.cost.total_cost_usd / self.total_distance_miles
        return None

    def to_geojson(self) -> dict:
        """
        Convert route to GeoJSON format for mapping.

        Note: Requires actual geographic coordinates from database.
        This is a placeholder structure.
        """
        return {
            "type": "Feature",
            "properties": {
                "route_id": self.route_id,
                "origin": self.origin_dock_name,
                "destination": self.dest_dock_name,
                "distance_miles": self.total_distance_miles,
                "transit_hours": self.transit_time_hours,
                "num_locks": self.num_locks,
                "total_cost": self.cost.total_cost_usd if self.cost else None,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": []  # Would be populated from segment coordinates
            }
        }

    def get_summary(self) -> dict:
        """Get route summary for display."""
        summary = {
            "origin": self.origin_dock_name or f"Node {self.origin_node}",
            "destination": self.dest_dock_name or f"Node {self.dest_node}",
            "distance": f"{self.total_distance_miles:.1f} miles ({self.total_distance_miles * 1.60934:.1f} km)",
            "transit_time": f"{self.transit_time_hours:.1f} hours ({self.transit_time_hours / 24:.1f} days)",
            "num_locks": self.num_locks,
            "total_time": f"{self.total_time_hours:.1f} hours (including lock delays)",
            "avg_speed": f"{self.average_speed_mph:.1f} mph",
            "feasible": "Yes" if self.is_feasible else "No",
        }

        if self.cost:
            summary.update({
                "total_cost": f"${self.cost.total_cost_usd:,.2f}",
                "cost_per_mile": f"${self.cost_per_mile:,.2f}/mile" if self.cost_per_mile else "N/A",
                "fuel_cost": f"${self.cost.fuel_cost_usd:,.2f}",
                "crew_cost": f"${self.cost.crew_cost_usd:,.2f}",
                "lock_fees": f"${self.cost.lock_fees_usd:,.2f}",
            })

        return summary


class RouteRequest(BaseModel):
    """Request for route computation."""

    origin_node: Optional[int] = None
    origin_dock_id: Optional[int] = None
    dest_node: Optional[int] = None
    dest_dock_id: Optional[int] = None

    vessel_imo: Optional[str] = None
    vessel_beam_m: Optional[float] = Field(None, ge=0)
    vessel_draft_m: Optional[float] = Field(None, ge=0)
    vessel_length_m: Optional[float] = Field(None, ge=0)

    algorithm: str = Field(default="dijkstra", description="Routing algorithm (dijkstra, astar)")
    apply_constraints: bool = Field(default=True, description="Whether to apply vessel constraints")
    include_cost: bool = Field(default=True, description="Whether to compute costs")


class RouteComparison(BaseModel):
    """Comparison of multiple routes."""

    routes: List[ComputedRoute] = Field(..., min_length=2, description="Routes to compare")

    @computed_field
    @property
    def shortest_distance_route(self) -> ComputedRoute:
        """Get route with shortest distance."""
        return min(self.routes, key=lambda r: r.total_distance_miles)

    @computed_field
    @property
    def fastest_route(self) -> ComputedRoute:
        """Get route with shortest total time."""
        return min(self.routes, key=lambda r: r.total_time_hours)

    @computed_field
    @property
    def cheapest_route(self) -> Optional[ComputedRoute]:
        """Get route with lowest cost."""
        routes_with_cost = [r for r in self.routes if r.cost]
        if not routes_with_cost:
            return None
        return min(routes_with_cost, key=lambda r: r.cost.total_cost_usd)

    def get_comparison_table(self) -> dict:
        """Get comparison data in tabular format."""
        return {
            "routes": [
                {
                    "route": f"{r.origin_dock_name} → {r.dest_dock_name}",
                    "distance_miles": r.total_distance_miles,
                    "time_hours": r.total_time_hours,
                    "locks": r.num_locks,
                    "cost_usd": r.cost.total_cost_usd if r.cost else None,
                    "feasible": r.is_feasible,
                }
                for r in self.routes
            ],
            "recommended": {
                "shortest": self.shortest_distance_route.route_id,
                "fastest": self.fastest_route.route_id,
                "cheapest": self.cheapest_route.route_id if self.cheapest_route else None,
            }
        }
