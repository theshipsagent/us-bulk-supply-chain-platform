"""
Cost calculation API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from src.engines.cost_engine import CostEngine
from src.engines.routing_engine import RoutingEngine
from src.models.route import RouteConstraints, RouteCost

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize engines
routing_engine = RoutingEngine()
cost_engine = CostEngine()


class CostRequest(BaseModel):
    """Request model for cost calculation."""
    origin_node: int = Field(..., description="Origin node ID")
    destination_node: int = Field(..., description="Destination node ID")
    vessel_dwt: int = Field(..., description="Vessel deadweight tonnage", ge=100, le=200000)
    crew_size: int = Field(5, description="Number of crew members", ge=1, le=50)
    vessel_beam_m: Optional[float] = Field(None, description="Vessel beam in meters")
    vessel_draft_m: Optional[float] = Field(None, description="Vessel draft in meters")
    include_terminals: bool = Field(True, description="Include terminal costs")


class CostCompareRequest(BaseModel):
    """Request model for comparing costs across different routes."""
    routes: list[dict] = Field(..., description="List of routes to compare")
    vessel_dwt: int = Field(..., ge=100, le=200000)
    crew_size: int = Field(5, ge=1, le=50)


@router.post("/costs/calculate", response_model=RouteCost)
async def calculate_route_cost(request: CostRequest):
    """
    Calculate total cost for a route.

    Includes:
    - Fuel costs (based on distance and vessel size)
    - Crew costs (wages for transit time)
    - Lock fees (per lock passage)
    - Terminal costs (origin and destination)
    """
    try:
        # First, find the route
        constraints = RouteConstraints(
            max_beam_m=request.vessel_beam_m,
            min_draft_m=request.vessel_draft_m
        )

        route = routing_engine.find_route(
            origin_node=request.origin_node,
            dest_node=request.destination_node,
            constraints=constraints,
            algorithm="dijkstra"
        )

        if not route:
            raise HTTPException(
                status_code=404,
                detail="No route found between specified nodes"
            )

        # Calculate costs
        route_cost = cost_engine.calculate_route_cost(
            route=route,
            vessel_dwt=request.vessel_dwt,
            crew_size=request.crew_size,
            include_terminals=request.include_terminals
        )

        return route_cost

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cost calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cost calculation failed")


@router.post("/costs/compare")
async def compare_route_costs(request: CostCompareRequest):
    """
    Compare costs across multiple routes.

    Useful for analyzing trade-offs between different paths.
    """
    try:
        results = []

        for route_data in request.routes:
            origin = route_data.get("origin_node")
            destination = route_data.get("destination_node")

            if not origin or not destination:
                continue

            # Find route
            route = routing_engine.find_route(
                origin_node=origin,
                dest_node=destination,
                constraints=RouteConstraints(),
                algorithm="dijkstra"
            )

            if route:
                # Calculate cost
                cost = cost_engine.calculate_route_cost(
                    route=route,
                    vessel_dwt=request.vessel_dwt,
                    crew_size=request.crew_size,
                    include_terminals=True
                )

                results.append({
                    "origin_node": origin,
                    "destination_node": destination,
                    "route": route,
                    "cost": cost
                })

        # Sort by total cost
        results.sort(key=lambda x: x["cost"].total_cost_usd)

        return {
            "vessel_dwt": request.vessel_dwt,
            "crew_size": request.crew_size,
            "routes_compared": len(results),
            "results": results,
            "cheapest": results[0] if results else None,
            "most_expensive": results[-1] if results else None
        }

    except Exception as e:
        logger.error(f"Cost comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cost comparison failed")


@router.get("/costs/fuel-rate")
async def get_fuel_rate():
    """Get current fuel price per gallon used in calculations."""
    return {
        "fuel_price_usd_per_gallon": cost_engine.fuel_price_usd_per_gallon,
        "note": "Fuel consumption calculated based on vessel DWT and transit time"
    }


@router.get("/costs/crew-rate")
async def get_crew_rate():
    """Get current crew hourly rate used in calculations."""
    return {
        "crew_hourly_rate_usd": cost_engine.crew_hourly_rate_usd,
        "note": "Multiplied by crew size and total transit time (including lock delays)"
    }


@router.get("/costs/lock-fee")
async def get_lock_fee():
    """Get standard lock passage fee used in calculations."""
    return {
        "lock_fee_usd": cost_engine.lock_fee_usd,
        "note": "Flat fee per lock passage"
    }
