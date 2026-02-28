"""
Operator Linker
Links vessels to their contracted operators and builds operator directory
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


logger = logging.getLogger(__name__)


class OperatorLinker:
    """Links vessels to operators and manages operator directory"""

    def __init__(self, config: dict):
        """
        Initialize operator linker

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Known MSC civilian operators (can be expanded from data)
        self.known_operators = {
            'MATSON': 'Matson Navigation Company',
            'MAERSK': 'Maersk Line, Limited',
            'OSG': 'Overseas Shipholding Group',
            'KEYSTONE': 'Keystone Shipping Company',
            'CROWLEY': 'Crowley Maritime Corporation',
            'INTREPID': 'Intrepid Ship Management',
            'PASHA': 'Pasha Hawaii',
            'APL': 'American President Lines',
            'TOTE': 'TOTE Maritime',
            'AMSEA': 'American Steamship Company'
        }

        logger.info("Initialized operator linker")

    def link_operators(self, vessel_df: pd.DataFrame) -> pd.DataFrame:
        """
        Link vessels to operators

        Args:
            vessel_df: Vessel data DataFrame

        Returns:
            DataFrame with operator information
        """
        logger.info("Linking vessels to operators")

        # Standardize operator names
        if 'operator' in vessel_df.columns:
            vessel_df['operator_standardized'] = vessel_df['operator'].apply(
                self._standardize_operator_name
            )

        if 'contract_operator' in vessel_df.columns:
            vessel_df['contract_operator_standardized'] = vessel_df['contract_operator'].apply(
                self._standardize_operator_name
            )

        # Extract operator information from vessel names (some have operator codes)
        vessel_df['operator_from_name'] = vessel_df['vessel_name'].apply(
            self._extract_operator_from_name
        )

        # Consolidate operator information
        vessel_df['primary_operator'] = vessel_df.apply(
            self._determine_primary_operator, axis=1
        )

        # Identify civilian vs military operated
        vessel_df['is_civilian_operated'] = vessel_df['primary_operator'].apply(
            self._is_civilian_operator
        )

        logger.info(f"Linked {vessel_df['primary_operator'].notna().sum()} vessels to operators")

        return vessel_df

    def build_operator_directory(self, vessel_df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
        """
        Build operator directory from vessel data

        Args:
            vessel_df: Vessel data with operator links
            output_path: Path to save operator directory

        Returns:
            Operator directory DataFrame
        """
        logger.info("Building operator directory")

        operators = []

        # Get unique operators
        operator_columns = [
            'operator', 'contract_operator', 'operator_standardized',
            'contract_operator_standardized', 'primary_operator'
        ]

        # Filter to only columns that exist
        existing_operator_columns = [col for col in operator_columns if col in vessel_df.columns]

        all_operators = set()
        for col in existing_operator_columns:
            all_operators.update(vessel_df[col].dropna().unique())

        # Build directory entries
        for operator in all_operators:
            if operator and str(operator).strip():
                # Get vessels operated by this operator
                if existing_operator_columns:
                    vessels = vessel_df[
                        vessel_df[existing_operator_columns].apply(
                            lambda row: operator in row.values, axis=1
                        )
                    ]
                else:
                    vessels = pd.DataFrame()  # No operator columns exist

                operator_info = {
                    'operator_name': operator,
                    'operator_standardized': self._standardize_operator_name(operator),
                    'vessel_count': len(vessels),
                    'vessel_types': ', '.join(vessels['vessel_type'].dropna().unique())
                        if 'vessel_type' in vessels.columns else '',
                    'is_civilian': self._is_civilian_operator(operator),
                    'vessels': ', '.join(vessels['vessel_name'].dropna().head(10))
                        if 'vessel_name' in vessels.columns else ''
                }

                # Calculate aggregate statistics
                if 'gross_tonnage' in vessels.columns:
                    operator_info['total_tonnage'] = vessels['gross_tonnage'].sum()

                if 'status' in vessels.columns:
                    operator_info['operational_vessels'] = len(
                        vessels[vessels['status'].str.contains(
                            'operational|active', case=False, na=False
                        )]
                    )

                operators.append(operator_info)

        operator_df = pd.DataFrame(operators)

        # Sort by vessel count
        operator_df = operator_df.sort_values('vessel_count', ascending=False)

        # Save operator directory
        operator_df.to_csv(output_path, index=False)
        logger.info(f"Saved operator directory: {output_path} ({len(operator_df)} operators)")

        return operator_df

    def _standardize_operator_name(self, operator: str) -> Optional[str]:
        """
        Standardize operator name

        Args:
            operator: Raw operator name

        Returns:
            Standardized name or None
        """
        if pd.isna(operator) or not str(operator).strip():
            return None

        operator_str = str(operator).strip().upper()

        # Check known operators
        for code, full_name in self.known_operators.items():
            if code in operator_str:
                return full_name

        # Remove common prefixes/suffixes
        operator_str = re.sub(r'\b(INC|LLC|LTD|CORP|COMPANY|CO)\b', '', operator_str)
        operator_str = re.sub(r'\s+', ' ', operator_str).strip()

        return operator_str if operator_str else None

    def _extract_operator_from_name(self, vessel_name: str) -> Optional[str]:
        """
        Try to extract operator from vessel name

        Args:
            vessel_name: Vessel name

        Returns:
            Operator name or None
        """
        if pd.isna(vessel_name):
            return None

        name_upper = str(vessel_name).upper()

        # Check for operator codes in vessel names
        for code, full_name in self.known_operators.items():
            if code in name_upper:
                return full_name

        # Common patterns
        patterns = [
            r'(USNS)\s+(.+)',  # US Naval Ship
            r'(MV|SS|MSC)\s+(.+)',  # Merchant vessels
        ]

        for pattern in patterns:
            match = re.search(pattern, name_upper)
            if match:
                return match.group(2).strip()

        return None

    def _determine_primary_operator(self, row: pd.Series) -> Optional[str]:
        """
        Determine primary operator from available fields

        Args:
            row: DataFrame row

        Returns:
            Primary operator name
        """
        # Priority order
        fields = [
            'contract_operator_standardized',
            'operator_standardized',
            'contract_operator',
            'operator',
            'operator_from_name'
        ]

        for field in fields:
            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                return row[field]

        return None

    def _is_civilian_operator(self, operator: str) -> bool:
        """
        Check if operator is civilian (vs military)

        Args:
            operator: Operator name

        Returns:
            True if civilian operator
        """
        if pd.isna(operator):
            return False

        operator_upper = str(operator).upper()

        # Military indicators
        military_keywords = [
            'NAVY', 'USN', 'NAVAL', 'MILITARY',
            'USNS', 'MSC OPERATED', 'GOVERNMENT'
        ]

        is_military = any(keyword in operator_upper for keyword in military_keywords)

        # Civilian indicators
        civilian_keywords = [
            'MARITIME', 'SHIPPING', 'NAVIGATION',
            'STEAMSHIP', 'LINES', 'CORPORATION'
        ]

        is_civilian = any(keyword in operator_upper for keyword in civilian_keywords)

        # Check known civilian operators
        is_known_civilian = any(
            code in operator_upper
            for code in self.known_operators.keys()
        )

        return (is_civilian or is_known_civilian) and not is_military

    def get_operator_statistics(self, operator_df: pd.DataFrame) -> Dict:
        """
        Generate operator statistics

        Args:
            operator_df: Operator directory DataFrame

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_operators': len(operator_df),
            'civilian_operators': len(operator_df[operator_df['is_civilian'] == True])
                if 'is_civilian' in operator_df.columns else 0,
            'military_operators': len(operator_df[operator_df['is_civilian'] == False])
                if 'is_civilian' in operator_df.columns else 0,
        }

        if 'vessel_count' in operator_df.columns:
            stats['total_vessels_operated'] = operator_df['vessel_count'].sum()
            stats['avg_vessels_per_operator'] = operator_df['vessel_count'].mean()
            stats['top_operators'] = operator_df.nlargest(5, 'vessel_count')[
                ['operator_name', 'vessel_count']
            ].to_dict('records')

        if 'total_tonnage' in operator_df.columns:
            stats['total_tonnage_operated'] = operator_df['total_tonnage'].sum()

        return stats

    def add_operator(self, name: str, is_civilian: bool = True, details: Dict = None) -> Dict:
        """
        Manually add operator to known operators

        Args:
            name: Operator name
            is_civilian: Whether civilian operator
            details: Additional details

        Returns:
            Operator info dict
        """
        code = name.split()[0].upper()
        self.known_operators[code] = name

        logger.info(f"Added operator: {name} ({code})")

        operator_info = {
            'name': name,
            'code': code,
            'is_civilian': is_civilian
        }

        if details:
            operator_info.update(details)

        return operator_info
