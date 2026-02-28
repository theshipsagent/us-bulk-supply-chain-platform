"""
FAF5 (Freight Analysis Framework) Data Loader
Processes FAF5 commodity flow databases
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FAFLoader:
    """Load and process FAF5 data."""
    
    def __init__(self, config: dict, data_dir: Path):
        self.config = config
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw" / "faf"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
    
    def load_faf5_flows(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        """
        Load FAF5 commodity flow database.
        
        Key fields:
        - Origin/Destination zones
        - SCTG commodity code
        - Mode (rail, truck, water, etc.)
        - Tons, value
        - Years (2018-2050 forecasts)
        """
        if filepath is None:
            filepath = self.raw_dir / "FAF5_regional_flows.csv"
        
        if not filepath.exists():
            logger.warning(f"FAF5 file not found: {filepath}")
            logger.info("Download from: https://www.bts.gov/faf")
            return pd.DataFrame()
        
        logger.info(f"Loading FAF5 flows: {filepath}")
        df = pd.read_csv(filepath)
        
        return df
    
    def filter_rail_flows(self, flows_df: pd.DataFrame) -> pd.DataFrame:
        """Filter to rail-only flows."""
        if 'dms_mode' in flows_df.columns:
            rail_df = flows_df[flows_df['dms_mode'].isin(['Rail', 'rail', 'RAIL', 1])]
        elif 'mode' in flows_df.columns:
            rail_df = flows_df[flows_df['mode'].str.contains('rail', case=False, na=False)]
        else:
            logger.warning("Could not identify mode column")
            rail_df = flows_df
        
        logger.info(f"  Filtered to {len(rail_df)} rail flow records")
        return rail_df
