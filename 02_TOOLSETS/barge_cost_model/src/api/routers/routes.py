"""
Routing API endpoints for pathfinding and route comparison.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from src.engines.routing_engine import RoutingEngine
from src.models.route import RouteConstraints, ComputedRoute

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize routing engine
routing_engine = RoutingEngine()


class RouteRequest(BaseModel):
    """Request model for route calculation."""
    origin_node: int = Field(..., description="Origin node ID (ANODE/BNODE)")
    destination_node: int = Field(..., description="Destination node ID (ANODE/BNODE)")
    vessel_beam_m: Optional[float] = Field(None, description="Vessel beam in meters")
    vessel_draft_m: Optional[float] = Field(None, description="Vessel draft in meters")
    algorithm: str = Field("dijkstra", description="Algorithm: dijkstra or astar")


class RouteCompareRequest(BaseModel):
    """Request model for comparing multiple routes."""
    origin_node: int
    destination_node: int
    vessel_beam_m: Optional[float] = None
    vessel_draft_m: Optional[float] = None


@router.post("/routes/calculate", response_model=ComputedRoute)
async def calculate_route(request: RouteRequest):
    """
    Calculate optimal route between two nodes.

    - **origin_node**: Starting waterway node
    - **destination_node**: Ending waterway node
    - **vessel_beam_m**: Vessel beam width (for lock clearance)
    - **vessel_draft_m**: Vessel draft depth (for channel clearance)
    - **algorithm**: Pathfinding algorithm (dijkstra or astar)
    """
    try:
        # Build constraints
        constraints = RouteConstraints(
            max_beam_m=request.vessel_beam_m,
            min_draft_m=request.vessel_draft_m
        )

        # Find route
        route = routing_engine.find_route(
            origin_node=request.origin_node,
            dest_node=request.destination_node,
            constraints=constraints,
            algorithm=request.algorithm
        )

        if not route:
            raise HTTPException(
                status_code=404,
                detail="No route found between specified nodes"
            )

        return route

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Route calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Route calculation failed")


@router.post("/routes/compare")
async def compare_routes(request: RouteCompareRequest):
    """
    Compare different routing algorithms for the same origin/destination.

    Returns routes calculated with both Dijkstra and A* algorithms for comparison.
    """
    try:
        constraints = RouteConstraints(
            max_beam_m=request.vessel_beam_m,
            min_draft_m=request.vessel_draft_m
        )

        # Calculate with both algorithms
        dijkstra_route = routing_engine.find_route(
            origin_node=request.origin_node,
            dest_node=request.destination_node,
            constraints=constraints,
            algorithm="dijkstra"
        )

        astar_route = routing_engine.find_route(
            origin_node=request.origin_node,
            dest_node=request.destination_node,
            constraints=constraints,
            algorithm="astar"
        )

        return {
            "origin_node": request.origin_node,
            "destination_node": request.destination_node,
            "dijkstra": dijkstra_route,
            "astar": astar_route,
            "comparison": {
                "distance_difference_mi": abs(
                    dijkstra_route.total_distance_mi - astar_route.total_distance_mi
                ) if dijkstra_route and astar_route else None,
                "time_difference_hours": abs(
                    dijkstra_route.transit_time_hours - astar_route.transit_time_hours
                ) if dijkstra_route and astar_route else None
            }
        }

    except Exception as e:
        logger.error(f"Route comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Route comparison failed")


@router.get("/routes/nodes")
async def get_available_nodes(
    river_name: Optional[str] = Query(None, description="Filter by river name"),
    state: Optional[str] = Query(None, description="Filter by state code"),
    limit: int = Query(100, ge=1, le=1000, description="Max results")
):
    """
    Get available waterway nodes for routing.

    Useful for finding valid origin/destination nodes.
    """
    try:
        nodes = routing_engine.get_available_nodes(
            river_name=river_name,
            state=state,
            limit=limit
        )

        return {
            "count": len(nodes),
            "nodes": nodes
        }

    except Exception as e:
        logger.error(f"Error fetching nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch nodes")
