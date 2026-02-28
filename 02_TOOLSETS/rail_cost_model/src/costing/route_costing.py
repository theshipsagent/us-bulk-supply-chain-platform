"""
Route Costing Module
Applies URCS-style variable costs to routes on the network

Cost components:
1. Running costs (distance-based)
   - Train-mile costs
   - Car-mile costs  
   - Gross ton-mile costs

2. Terminal/Switching costs
   - Per car switched
   - Per interchange

3. Equipment costs
   - Car-days (time in transit)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class RouteCostCalculator:
    """Calculate variable costs for rail routes."""
    
    # Default URCS-style unit costs (approximate, for illustration)
    # Actual values should come from URCS Phase II workbooks
    DEFAULT_UNIT_COSTS = {
        'car_mile': 0.35,           # $ per car-mile
        'gross_ton_mile': 0.008,    # $ per gross ton-mile
        'train_mile': 25.00,        # $ per train-mile
        'car_switched': 150.00,     # $ per car classification event
        'interchange': 75.00,       # $ per carrier interchange
        'car_day': 45.00,           # $ per car-day (equipment cost)
    }
    
    # Average car characteristics
    CAR_DEFAULTS = {
        'tare_weight_tons': 30,     # Empty car weight
        'avg_lading_tons': 100,     # Average payload
        'cars_per_train': 100,      # Average train length
    }
    
    def __init__(self, unit_costs: Optional[Dict] = None, car_params: Optional[Dict] = None):
        self.unit_costs = unit_costs or self.DEFAULT_UNIT_COSTS.copy()
        self.car_params = car_params or self.CAR_DEFAULTS.copy()
        
    def calculate_route_cost(
        self,
        route_miles: float,
        commodity_tons: float,
        num_cars: int = 1,
        num_interchanges: int = 0,
        num_classifications: int = 1,
        transit_days: float = None
    ) -> Dict:
        """
        Calculate total variable cost for a route.
        
        Args:
            route_miles: Total route distance in miles
            commodity_tons: Net tons of commodity being shipped
            num_cars: Number of rail cars
            num_interchanges: Number of carrier interchanges
            num_classifications: Number of yard classification events
            transit_days: Days in transit (estimated if None)
            
        Returns:
            Dictionary with cost breakdown
        """
        # Calculate gross tons (commodity + car tare weight)
        gross_tons_per_car = self.car_params['tare_weight_tons'] + (commodity_tons / num_cars)
        total_gross_tons = gross_tons_per_car * num_cars
        
        # Running costs
        car_mile_cost = route_miles * num_cars * self.unit_costs['car_mile']
        gtm_cost = route_miles * total_gross_tons * self.unit_costs['gross_ton_mile']
        
        # Allocate train-mile cost across cars
        train_miles = route_miles  # Simplified: 1 train for shipment
        train_mile_cost = train_miles * self.unit_costs['train_mile'] * (num_cars / self.car_params['cars_per_train'])
        
        # Terminal costs
        switching_cost = num_classifications * num_cars * self.unit_costs['car_switched']
        interchange_cost = num_interchanges * num_cars * self.unit_costs['interchange']
        
        # Equipment costs
        if transit_days is None:
            # Estimate: ~400 miles/day average
            transit_days = max(1, route_miles / 400)
        equipment_cost = transit_days * num_cars * self.unit_costs['car_day']
        
        # Total
        total_cost = (
            car_mile_cost + 
            gtm_cost + 
            train_mile_cost + 
            switching_cost + 
            interchange_cost + 
            equipment_cost
        )
        
        return {
            'total_variable_cost': round(total_cost, 2),
            'cost_per_ton': round(total_cost / commodity_tons, 4) if commodity_tons > 0 else 0,
            'cost_per_car': round(total_cost / num_cars, 2),
            'cost_per_mile': round(total_cost / route_miles, 4) if route_miles > 0 else 0,
            'breakdown': {
                'line_haul': {
                    'car_mile': round(car_mile_cost, 2),
                    'gross_ton_mile': round(gtm_cost, 2),
                    'train_mile': round(train_mile_cost, 2),
                },
                'terminal': {
                    'switching': round(switching_cost, 2),
                    'interchange': round(interchange_cost, 2),
                },
                'equipment': round(equipment_cost, 2),
            },
            'parameters': {
                'route_miles': route_miles,
                'commodity_tons': commodity_tons,
                'num_cars': num_cars,
                'gross_tons': total_gross_tons,
                'transit_days': round(transit_days, 1),
            }
        }

    def cost_network_path(
        self,
        graph,
        path: List[int],
        commodity_tons: float,
        num_cars: int = 1
    ) -> Dict:
        """
        Calculate cost for a path through the network.
        
        Tracks carrier changes for interchange costs.
        """
        if not path or len(path) < 2:
            return {'error': 'Invalid path'}
        
        # Calculate total miles and track carrier changes
        total_miles = 0
        carriers = set()
        current_carrier = None
        num_interchanges = 0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            
            # Get edge data (take first edge if multigraph)
            edge_data = list(graph.get_edge_data(u, v).values())[0]
            
            total_miles += edge_data.get('miles', 0)
            
            # Track carrier
            carrier = edge_data.get('owner', 'UNKNOWN')
            carriers.add(carrier)
            
            if current_carrier and carrier != current_carrier:
                num_interchanges += 1
            current_carrier = carrier
        
        # Estimate classifications (simplified: 1 + interchanges)
        num_classifications = 1 + num_interchanges
        
        # Calculate cost
        cost = self.calculate_route_cost(
            route_miles=total_miles,
            commodity_tons=commodity_tons,
            num_cars=num_cars,
            num_interchanges=num_interchanges,
            num_classifications=num_classifications
        )
        
        cost['route_info'] = {
            'path_nodes': path,
            'carriers': list(carriers),
            'num_interchanges': num_interchanges,
        }
        
        return cost
