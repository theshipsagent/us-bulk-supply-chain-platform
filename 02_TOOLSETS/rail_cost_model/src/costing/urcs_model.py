"""
URCS Cost Model
Unit cost calculations based on STB URCS methodology
"""

import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class URCSCostModel:
    """URCS-based cost calculations."""
    
    # Default unit costs (approximations for demonstration)
    DEFAULT_COSTS = {
        'car_mile': 0.35,
        'gross_ton_mile': 0.008,
        'train_mile': 25.00,
        'car_switched': 150.00,
        'interchange': 75.00,
        'car_day': 45.00
    }
    
    def __init__(self, unit_costs: Optional[Dict] = None):
        self.unit_costs = unit_costs or self.DEFAULT_COSTS.copy()
    
    def calculate_line_haul_cost(
        self,
        miles: float,
        num_cars: int,
        gross_tons: float
    ) -> Dict[str, float]:
        """Calculate line-haul (running) costs."""
        car_mile_cost = miles * num_cars * self.unit_costs['car_mile']
        gtm_cost = miles * gross_tons * self.unit_costs['gross_ton_mile']
        train_mile_cost = miles * self.unit_costs['train_mile'] * (num_cars / 100)
        
        return {
            'car_mile': car_mile_cost,
            'gross_ton_mile': gtm_cost,
            'train_mile': train_mile_cost,
            'total': car_mile_cost + gtm_cost + train_mile_cost
        }
    
    def calculate_terminal_cost(
        self,
        num_cars: int,
        num_classifications: int,
        num_interchanges: int
    ) -> Dict[str, float]:
        """Calculate terminal and switching costs."""
        switching = num_cars * num_classifications * self.unit_costs['car_switched']
        interchange = num_cars * num_interchanges * self.unit_costs['interchange']
        
        return {
            'switching': switching,
            'interchange': interchange,
            'total': switching + interchange
        }
    
    def calculate_equipment_cost(
        self,
        num_cars: int,
        transit_days: float
    ) -> float:
        """Calculate equipment (car ownership) costs."""
        return num_cars * transit_days * self.unit_costs['car_day']
