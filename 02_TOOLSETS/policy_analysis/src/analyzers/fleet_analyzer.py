"""
Fleet Analyzer - Overall US Flag Fleet Statistics
Computes comprehensive statistics across the entire US flag vessel fleet
"""
import logging
from typing import Dict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FleetAnalyzer:
    """Analyzes overall US flag fleet statistics"""

    def __init__(self, vessel_df: pd.DataFrame):
        """
        Initialize fleet analyzer

        Args:
            vessel_df: Master vessel dataset
        """
        self.vessel_df = vessel_df
        self.current_year = 2026
        logger.info(f"Initialized FleetAnalyzer with {len(vessel_df)} vessels")

    def analyze(self) -> Dict:
        """
        Run complete fleet analysis

        Returns:
            Dictionary of analysis results
        """
        logger.info("Starting fleet analysis")

        results = {
            'overview': self._analyze_overview(),
            'vessel_types': self._analyze_vessel_types(),
            'tonnage': self._analyze_tonnage(),
            'demographics': self._analyze_demographics(),
            'operators': self._analyze_operators(),
            'geography': self._analyze_geography(),
            'categories': self._analyze_categories()
        }

        logger.info("Fleet analysis complete")
        return results

    def _analyze_overview(self) -> Dict:
        """Overall fleet statistics"""
        return {
            'total_vessels': len(self.vessel_df),
            'unique_operators': self.vessel_df['Operator'].nunique(),
            'unique_types': self.vessel_df['Vessel Type'].nunique(),
            'unique_ports': self.vessel_df['Home Port'].nunique(),
            'avg_age': (self.current_year - self.vessel_df['Build Year'].mean()) if 'Build Year' in self.vessel_df.columns else None,
            'avg_tonnage': self.vessel_df['Gross Tonnage'].mean() if 'Gross Tonnage' in self.vessel_df.columns else None
        }

    def _analyze_vessel_types(self) -> Dict:
        """Vessel type distribution"""
        type_counts = self.vessel_df['Vessel Type'].value_counts()
        return {
            'distribution': type_counts.to_dict(),
            'top_5': type_counts.head(5).to_dict(),
            'categories': {
                'container': len(self.vessel_df[self.vessel_df['Vessel Type'].str.contains('Container', na=False)]),
                'tanker': len(self.vessel_df[self.vessel_df['Vessel Type'].str.contains('Tanker|Oiler', na=False)]),
                'bulk': len(self.vessel_df[self.vessel_df['Vessel Type'].str.contains('Bulk', na=False)]),
                'roro': len(self.vessel_df[self.vessel_df['Vessel Type'].str.contains('RoRo|Roll', case=False, na=False)]),
                'msc': len(self.vessel_df[self.vessel_df['Vessel Name'].str.contains('USNS', na=False)])
            }
        }

    def _analyze_tonnage(self) -> Dict:
        """Tonnage statistics"""
        if 'Gross Tonnage' not in self.vessel_df.columns:
            return {}

        tonnage = self.vessel_df['Gross Tonnage'].dropna()
        return {
            'total_gt': float(tonnage.sum()),
            'mean_gt': float(tonnage.mean()),
            'median_gt': float(tonnage.median()),
            'min_gt': float(tonnage.min()),
            'max_gt': float(tonnage.max()),
            'by_category': self.vessel_df.groupby('Vessel Type')['Gross Tonnage'].sum().to_dict()
        }

    def _analyze_demographics(self) -> Dict:
        """Fleet age and build demographics"""
        if 'Build Year' not in self.vessel_df.columns:
            return {}

        ages = self.current_year - self.vessel_df['Build Year'].dropna()

        # Build decade distribution
        decades = (self.vessel_df['Build Year'] // 10 * 10).value_counts().sort_index()
        decade_dist = {f"{int(d)}s": int(count) for d, count in decades.items() if not pd.isna(d)}

        return {
            'avg_age': float(ages.mean()),
            'median_age': float(ages.median()),
            'min_age': float(ages.min()),
            'max_age': float(ages.max()),
            'oldest_vessel': int(self.vessel_df['Build Year'].min()),
            'newest_vessel': int(self.vessel_df['Build Year'].max()),
            'by_decade': decade_dist,
            'modern_fleet': len(self.vessel_df[self.vessel_df['Build Year'] >= 2010]),  # Built since 2010
            'legacy_fleet': len(self.vessel_df[self.vessel_df['Build Year'] < 1990])   # Built before 1990
        }

    def _analyze_operators(self) -> Dict:
        """Operator analysis"""
        operator_counts = self.vessel_df['Operator'].value_counts()

        # Identify MSC vs commercial operators
        msc_operators = ['Military Sealift Command', 'Maersk Line Limited', 'Crowley Maritime Corporation',
                        'American Steamship Company', 'Intrepid Ship Management', 'OSG Ship Management']

        msc_vessels = self.vessel_df[self.vessel_df['Operator'].isin(msc_operators)]
        commercial_vessels = self.vessel_df[~self.vessel_df['Operator'].isin(msc_operators)]

        return {
            'top_10': operator_counts.head(10).to_dict(),
            'total_operators': len(operator_counts),
            'msc_contractor_vessels': len(msc_vessels),
            'pure_commercial_vessels': len(commercial_vessels),
            'concentration': {
                'top_3_share': (operator_counts.head(3).sum() / len(self.vessel_df) * 100),
                'top_5_share': (operator_counts.head(5).sum() / len(self.vessel_df) * 100)
            }
        }

    def _analyze_geography(self) -> Dict:
        """Geographic distribution"""
        port_counts = self.vessel_df['Home Port'].value_counts()

        # Regional grouping (simplified)
        regions = {
            'East Coast': ['Norfolk', 'Baltimore', 'Charleston', 'Savannah', 'Jacksonville', 'New York', 'Philadelphia', 'Miami'],
            'Gulf Coast': ['Houston', 'New Orleans', 'Mobile', 'Tampa', 'Beaumont'],
            'West Coast': ['Los Angeles', 'Long Beach', 'Oakland', 'Seattle', 'Tacoma', 'San Diego', 'San Francisco'],
            'Pacific': ['Honolulu', 'Anchorage'],
            'Great Lakes': ['Duluth', 'Cleveland', 'Detroit', 'Chicago', 'Superior']
        }

        regional_dist = {}
        for region, ports in regions.items():
            regional_dist[region] = len(self.vessel_df[self.vessel_df['Home Port'].isin(ports)])

        return {
            'top_10_ports': port_counts.head(10).to_dict(),
            'regional_distribution': regional_dist,
            'norfolk_vessels': len(self.vessel_df[self.vessel_df['Home Port'] == 'Norfolk']),
            'norfolk_percentage': (len(self.vessel_df[self.vessel_df['Home Port'] == 'Norfolk']) / len(self.vessel_df) * 100)
        }

    def _analyze_categories(self) -> Dict:
        """Analyze by fleet category (commercial, MSC, RRF)"""
        # Identify categories based on vessel characteristics
        usns_vessels = self.vessel_df[self.vessel_df['Vessel Name'].str.contains('USNS', na=False)]
        rrf_vessels = self.vessel_df[self.vessel_df['Vessel Type'].str.contains('Reserve', na=False)]
        commercial_vessels = self.vessel_df[~self.vessel_df['Vessel Name'].str.contains('USNS|SS CAPE', na=False)]

        return {
            'msc_total': len(usns_vessels),
            'rrf_total': len(rrf_vessels),
            'commercial_total': len(commercial_vessels),
            'percentages': {
                'msc': len(usns_vessels) / len(self.vessel_df) * 100,
                'rrf': len(rrf_vessels) / len(self.vessel_df) * 100,
                'commercial': len(commercial_vessels) / len(self.vessel_df) * 100
            }
        }
