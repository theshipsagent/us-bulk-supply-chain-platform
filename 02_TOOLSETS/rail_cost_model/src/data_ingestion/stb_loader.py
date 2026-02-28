"""
STB Economic Data Loader
Processes URCS costing workbooks and related STB data

URCS Structure:
- Phase II: Unit costs by railroad, cost category
- Phase III: Applies unit costs to specific movements

Key cost categories:
- Line-haul (train-mile, car-mile, gross ton-mile)
- Switching/Terminal
- Loss and damage
- Equipment ownership
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class URCSLoader:
    """Load and process URCS costing data."""
    
    # URCS cost categories and their typical units
    COST_CATEGORIES = {
        "running": {
            "train_mile": "per train-mile",
            "car_mile": "per car-mile", 
            "gross_ton_mile": "per gross ton-mile"
        },
        "switching": {
            "switch_minutes": "per switch-minute",
            "car_switched": "per car switched"
        },
        "equipment": {
            "car_day": "per car-day",
            "loco_unit_mile": "per locomotive unit-mile"
        }
    }
    
    def __init__(self, config: dict, data_dir: Path):
        self.config = config
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw" / "stb"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
    def load_urcs_workbook(self, filepath: Path) -> Dict[str, pd.DataFrame]:
        """
        Load URCS Phase III Excel workbook.
        
        The workbook contains multiple sheets:
        - Instructions
        - Input parameters
        - Unit cost tables
        - Cost calculation worksheets
        """
        logger.info(f"Loading URCS workbook: {filepath}")
        
        # Read all sheets
        sheets = pd.read_excel(filepath, sheet_name=None, engine='openpyxl')
        
        logger.info(f"  Found {len(sheets)} sheets: {list(sheets.keys())}")
        
        return sheets
    
    def extract_unit_costs(self, urcs_sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Extract unit cost tables from URCS workbook.
        
        Returns DataFrame with columns:
        - railroad: Class I railroad code
        - cost_category: Category of cost
        - unit_cost: Cost per unit
        - unit: Unit of measurement
        """
        # This will need to be customized based on actual URCS workbook structure
        # The structure varies by year
        
        unit_costs = []
        
        # Look for sheets containing unit cost data
        for sheet_name, df in urcs_sheets.items():
            if "unit" in sheet_name.lower() or "cost" in sheet_name.lower():
                logger.info(f"  Processing sheet: {sheet_name}")
                # Extract relevant data
                # Structure depends on specific workbook version
                
        return pd.DataFrame(unit_costs)
    
    def load_commodity_stratification(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        """
        Load Commodity Revenue Stratification Report.
        
        Contains revenues, variable costs, tons, carloads by STCC code.
        """
        if filepath is None:
            filepath = self.raw_dir / "CRSR7-2023.xlsx"
            
        if not filepath.exists():
            logger.warning(f"Commodity stratification file not found: {filepath}")
            logger.info("Download from: https://www.stb.gov/wp-content/uploads/CRSR7-2023.xlsx")
            return pd.DataFrame()
        
        logger.info(f"Loading commodity stratification: {filepath}")
        df = pd.read_excel(filepath, engine='openpyxl')
        
        return df


class WaybillLoader:
    """Load and process Public Use Waybill Sample."""
    
    def __init__(self, config: dict, data_dir: Path):
        self.config = config
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw" / "stb"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
    def load_public_waybill(self, year: int) -> pd.DataFrame:
        """
        Load Public Use Waybill Sample for a given year.
        
        Note: Revenue is masked in public version.
        Key fields include:
        - Origin/Destination BEA regions
        - STCC commodity code
        - Carloads, tons
        - Car type
        - Railroad(s) involved
        """
        # Public waybill is typically a fixed-width or CSV file
        # Specific format varies by year
        
        filepath = self.raw_dir / f"waybill_public_{year}.csv"
        
        if not filepath.exists():
            logger.warning(f"Waybill file not found: {filepath}")
            logger.info("Request from STB: https://www.stb.gov/reports-data/waybill/")
            return pd.DataFrame()
        
        logger.info(f"Loading waybill sample: {filepath}")
        df = pd.read_csv(filepath)
        
        return df
