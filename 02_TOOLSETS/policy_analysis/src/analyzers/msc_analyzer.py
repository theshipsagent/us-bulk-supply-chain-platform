"""
Military Sealift Command Analyzer
Analyzes MSC fleet composition, status, and Norfolk port disposition
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


class MSCAnalyzer:
    """Analyzes Military Sealift Command vessel data"""

    def __init__(self, config: dict):
        """
        Initialize MSC analyzer

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.norfolk_config = config['locations']['norfolk']
        self.msc_status_definitions = config['msc_status']

        # MSC vessel type categories
        self.msc_vessel_types = {
            'combat_logistics': [
                'Fast Combat Support Ship',
                'Fleet Replenishment Oiler',
                'Dry Cargo Ship',
                'Ammunition Ship'
            ],
            'strategic_sealift': [
                'Large Medium-Speed Roll-on/Roll-off',
                'Fast Sealift Ship',
                'Ready Reserve Force',
                'Bob Hope Class',
                'Watson Class'
            ],
            'special_mission': [
                'Hospital Ship',
                'Command Ship',
                'Submarine Tender',
                'Surveillance Ship',
                'Oceanographic Survey Ship'
            ],
            'prepositioning': [
                'Maritime Prepositioning Ship',
                'Afloat Prepositioning',
                'MPS'
            ],
            'tankers': [
                'Fleet Oiler',
                'Tanker',
                'Oiler'
            ],
            'support': [
                'Tug',
                'Salvage',
                'Cable Ship',
                'Crane Ship'
            ]
        }

        logger.info("Initialized MSC analyzer")

    def analyze(self, vessel_df: pd.DataFrame) -> Dict:
        """
        Perform comprehensive MSC fleet analysis

        Args:
            vessel_df: Vessel data DataFrame

        Returns:
            Analysis results dictionary
        """
        logger.info("Starting MSC fleet analysis")

        # Filter for MSC vessels
        msc_vessels = self.identify_msc_vessels(vessel_df)

        logger.info(f"Identified {len(msc_vessels)} MSC vessels")

        # Analyze fleet composition
        composition = self.analyze_fleet_composition(msc_vessels)

        # Analyze by status
        status_analysis = self.analyze_by_status(msc_vessels)

        # Analyze Norfolk vessels
        norfolk_analysis = self.analyze_norfolk_vessels(msc_vessels)

        # Analyze operators
        operator_analysis = self.analyze_operators(msc_vessels)

        # Generate summary statistics
        summary = self.generate_summary(msc_vessels)

        results = {
            'summary': summary,
            'fleet_composition': composition,
            'status_analysis': status_analysis,
            'norfolk_analysis': norfolk_analysis,
            'operator_analysis': operator_analysis,
            'vessel_data': msc_vessels
        }

        logger.info("MSC analysis complete")

        return results

    def identify_msc_vessels(self, vessel_df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify MSC vessels from vessel data

        Args:
            vessel_df: All vessel data

        Returns:
            MSC vessels only
        """
        logger.info("Identifying MSC vessels")

        # Multiple methods to identify MSC vessels
        msc_mask = pd.Series([False] * len(vessel_df), index=vessel_df.index)

        # Method 1: Check operator field
        if 'operator' in vessel_df.columns:
            msc_mask |= vessel_df['operator'].str.contains(
                'MSC|Military Sealift|Sealift Command',
                case=False, na=False
            )

        # Method 2: Check vessel name (USNS prefix)
        if 'vessel_name' in vessel_df.columns:
            msc_mask |= vessel_df['vessel_name'].str.contains(
                'USNS|T-A|T-AO|T-AKE|T-ACS|T-EPF',
                case=False, na=False
            )

        # Method 3: Check MSC-specific fields
        if 'msc_category' in vessel_df.columns:
            msc_mask |= vessel_df['msc_category'].notna()

        if 'msc_status' in vessel_df.columns:
            msc_mask |= vessel_df['msc_status'].notna()

        # Method 4: Check vessel type for MSC-specific types
        if 'vessel_type' in vessel_df.columns:
            msc_type_keywords = [
                'replenishment', 'prepositioning', 'sealift',
                'combat support', 'hospital ship', 'command ship'
            ]
            msc_mask |= vessel_df['vessel_type'].str.contains(
                '|'.join(msc_type_keywords),
                case=False, na=False
            )

        msc_vessels = vessel_df[msc_mask].copy()

        # Categorize MSC vessels
        msc_vessels['msc_category'] = msc_vessels.apply(
            self._categorize_msc_vessel, axis=1
        )

        return msc_vessels

    def analyze_fleet_composition(self, msc_vessels: pd.DataFrame) -> Dict:
        """
        Analyze MSC fleet composition by type

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Composition analysis
        """
        logger.info("Analyzing fleet composition")

        composition = {
            'total_vessels': len(msc_vessels),
            'by_category': {},
            'by_type': {},
            'by_build_decade': {},
            'size_distribution': {}
        }

        # By MSC category
        if 'msc_category' in msc_vessels.columns:
            composition['by_category'] = msc_vessels['msc_category'].value_counts().to_dict()

        # By vessel type
        if 'vessel_type' in msc_vessels.columns:
            composition['by_type'] = msc_vessels['vessel_type'].value_counts().to_dict()

        # By build year
        if 'build_year' in msc_vessels.columns:
            decades = (msc_vessels['build_year'] // 10 * 10).value_counts().sort_index()
            composition['by_build_decade'] = {
                f"{int(decade)}s": count for decade, count in decades.items()
                if not pd.isna(decade)
            }

        # Size distribution
        if 'gross_tonnage' in msc_vessels.columns:
            tonnage = msc_vessels['gross_tonnage'].dropna()
            composition['size_distribution'] = {
                'mean_tonnage': float(tonnage.mean()),
                'median_tonnage': float(tonnage.median()),
                'min_tonnage': float(tonnage.min()),
                'max_tonnage': float(tonnage.max())
            }

        return composition

    def analyze_by_status(self, msc_vessels: pd.DataFrame) -> Dict:
        """
        Analyze vessels by operational status

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Status analysis
        """
        logger.info("Analyzing by status")

        status_analysis = {
            'by_status': {},
            'by_readiness': {},
            'deployment_ready': 0,
            'maintenance': 0,
            'reserve': 0
        }

        # Standardize status
        msc_vessels['status_standardized'] = msc_vessels.apply(
            self._standardize_status, axis=1
        )

        # Count by status
        status_counts = msc_vessels['status_standardized'].value_counts()
        status_analysis['by_status'] = status_counts.to_dict()

        # Categorize readiness
        for status in ['operational', 'ready', 'ready_reserve']:
            count = len(msc_vessels[msc_vessels['status_standardized'] == status])
            status_analysis['by_readiness'][status] = count
            status_analysis['deployment_ready'] += count

        # Maintenance and reserve
        status_analysis['maintenance'] = len(
            msc_vessels[msc_vessels['status_standardized'] == 'maintenance']
        )
        status_analysis['reserve'] = len(
            msc_vessels[msc_vessels['status_standardized'].isin(['ready_reserve', 'ros'])]
        )

        return status_analysis

    def analyze_norfolk_vessels(self, msc_vessels: pd.DataFrame) -> Dict:
        """
        Analyze MSC vessels at Norfolk, VA

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Norfolk analysis
        """
        logger.info("Analyzing Norfolk vessels")

        # Identify Norfolk vessels
        norfolk_mask = self._identify_norfolk_vessels(msc_vessels)
        norfolk_vessels = msc_vessels[norfolk_mask].copy()

        logger.info(f"Found {len(norfolk_vessels)} MSC vessels at Norfolk")

        analysis = {
            'total_norfolk_vessels': len(norfolk_vessels),
            'by_status': {},
            'by_category': {},
            'by_operator': {},
            'vessels': []
        }

        # By status
        if 'status_standardized' in norfolk_vessels.columns:
            analysis['by_status'] = norfolk_vessels['status_standardized'].value_counts().to_dict()

        # By category
        if 'msc_category' in norfolk_vessels.columns:
            analysis['by_category'] = norfolk_vessels['msc_category'].value_counts().to_dict()

        # By operator
        if 'primary_operator' in norfolk_vessels.columns:
            analysis['by_operator'] = norfolk_vessels['primary_operator'].value_counts().to_dict()

        # Detailed vessel list
        vessel_fields = ['vessel_name', 'vessel_type', 'status_standardized',
                        'primary_operator', 'gross_tonnage', 'build_year']

        for _, row in norfolk_vessels.iterrows():
            vessel_info = {
                field: row.get(field, 'N/A')
                for field in vessel_fields if field in row
            }
            analysis['vessels'].append(vessel_info)

        return analysis

    def analyze_operators(self, msc_vessels: pd.DataFrame) -> Dict:
        """
        Analyze civilian operators of MSC vessels

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Operator analysis
        """
        logger.info("Analyzing MSC operators")

        # Filter for civilian-operated vessels
        civilian_operated = msc_vessels[
            msc_vessels.get('is_civilian_operated', False) == True
        ].copy() if 'is_civilian_operated' in msc_vessels.columns else pd.DataFrame()

        analysis = {
            'total_civilian_operated': len(civilian_operated),
            'civilian_percentage': (len(civilian_operated) / len(msc_vessels) * 100)
                if len(msc_vessels) > 0 else 0,
            'by_operator': {},
            'operator_vessel_types': {}
        }

        if not civilian_operated.empty and 'primary_operator' in civilian_operated.columns:
            # Count by operator
            analysis['by_operator'] = civilian_operated['primary_operator'].value_counts().to_dict()

            # Vessel types by operator
            for operator in civilian_operated['primary_operator'].unique():
                if pd.notna(operator):
                    operator_vessels = civilian_operated[
                        civilian_operated['primary_operator'] == operator
                    ]
                    if 'vessel_type' in operator_vessels.columns:
                        types = operator_vessels['vessel_type'].value_counts().to_dict()
                        analysis['operator_vessel_types'][operator] = types

        return analysis

    def generate_summary(self, msc_vessels: pd.DataFrame) -> Dict:
        """
        Generate summary statistics

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Summary statistics
        """
        summary = {
            'total_msc_vessels': len(msc_vessels),
            'us_flag_vessels': len(msc_vessels[msc_vessels.get('is_us_flag', False) == True])
                if 'is_us_flag' in msc_vessels.columns else len(msc_vessels),
            'unique_operators': msc_vessels['primary_operator'].nunique()
                if 'primary_operator' in msc_vessels.columns else 0,
            'unique_types': msc_vessels['vessel_type'].nunique()
                if 'vessel_type' in msc_vessels.columns else 0,
        }

        # Age statistics
        if 'build_year' in msc_vessels.columns:
            current_year = pd.Timestamp.now().year
            ages = current_year - msc_vessels['build_year'].dropna()
            summary['average_age'] = float(ages.mean())
            summary['oldest_vessel'] = int(msc_vessels['build_year'].min())
            summary['newest_vessel'] = int(msc_vessels['build_year'].max())

        # Total tonnage
        if 'gross_tonnage' in msc_vessels.columns:
            summary['total_gross_tonnage'] = float(
                msc_vessels['gross_tonnage'].sum()
            )

        return summary

    def _categorize_msc_vessel(self, row: pd.Series) -> str:
        """
        Categorize MSC vessel by type

        Args:
            row: Vessel data row

        Returns:
            MSC category
        """
        # Check existing category
        if 'msc_category' in row and pd.notna(row['msc_category']):
            return row['msc_category']

        # Determine from vessel type
        vessel_type = str(row.get('vessel_type', '')).lower()
        vessel_name = str(row.get('vessel_name', '')).lower()

        for category, type_list in self.msc_vessel_types.items():
            for vtype in type_list:
                if vtype.lower() in vessel_type or vtype.lower() in vessel_name:
                    return category

        return 'other'

    def _standardize_status(self, row: pd.Series) -> str:
        """
        Standardize vessel status

        Args:
            row: Vessel data row

        Returns:
            Standardized status
        """
        # Check MSC-specific status field
        if 'msc_status' in row and pd.notna(row['msc_status']):
            status_str = str(row['msc_status']).lower()
        elif 'status' in row and pd.notna(row['status']):
            status_str = str(row['status']).lower()
        else:
            return 'unknown'

        # Map to standard statuses
        status_map = {
            'operational': ['operational', 'active', 'deployed', 'in service'],
            'ready': ['ready', 'available', 'standby'],
            'ready_reserve': ['ready reserve', 'rrf', 'reserve'],
            'ros': ['reduced operating', 'ros', 'reduced crew'],
            'activation': ['activation', 'activating', 'mobilizing'],
            'maintenance': ['maintenance', 'repair', 'overhaul', 'drydock']
        }

        for standard_status, keywords in status_map.items():
            if any(keyword in status_str for keyword in keywords):
                return standard_status

        return 'unknown'

    def _identify_norfolk_vessels(self, msc_vessels: pd.DataFrame) -> pd.Series:
        """
        Identify vessels at Norfolk, VA

        Args:
            msc_vessels: MSC vessel data

        Returns:
            Boolean mask for Norfolk vessels
        """
        mask = pd.Series([False] * len(msc_vessels), index=msc_vessels.index)

        # Method 1: Check home port
        if 'home_port' in msc_vessels.columns:
            norfolk_ports = self.norfolk_config['ports']
            mask |= msc_vessels['home_port'].str.contains(
                '|'.join(norfolk_ports),
                case=False, na=False
            )

        # Method 2: Check current location
        if 'current_location' in msc_vessels.columns:
            norfolk_ports = self.norfolk_config['ports']
            mask |= msc_vessels['current_location'].str.contains(
                '|'.join(norfolk_ports),
                case=False, na=False
            )

        # Method 3: Check coordinates (if available)
        if 'latitude' in msc_vessels.columns and 'longitude' in msc_vessels.columns:
            norfolk_lat = self.norfolk_config['latitude']
            norfolk_lon = self.norfolk_config['longitude']
            radius_km = self.norfolk_config['radius_km']

            # Simple distance calculation (not accounting for Earth curvature)
            lat_diff = abs(msc_vessels['latitude'] - norfolk_lat)
            lon_diff = abs(msc_vessels['longitude'] - norfolk_lon)

            # Rough km per degree (at Norfolk latitude)
            mask |= ((lat_diff < radius_km / 111) & (lon_diff < radius_km / 85))

        return mask

    def export_analysis(self, analysis: Dict, output_dir: Path):
        """
        Export analysis results to files

        Args:
            analysis: Analysis results
            output_dir: Output directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export vessel data
        if 'vessel_data' in analysis:
            vessel_path = output_dir / 'msc_vessels.csv'
            analysis['vessel_data'].to_csv(vessel_path, index=False)
            logger.info(f"Exported MSC vessels to: {vessel_path}")

        # Export Norfolk vessels
        if 'norfolk_analysis' in analysis and analysis['norfolk_analysis']['vessels']:
            norfolk_df = pd.DataFrame(analysis['norfolk_analysis']['vessels'])
            norfolk_path = output_dir / 'norfolk_vessels.csv'
            norfolk_df.to_csv(norfolk_path, index=False)
            logger.info(f"Exported Norfolk vessels to: {norfolk_path}")

        logger.info("Analysis export complete")
