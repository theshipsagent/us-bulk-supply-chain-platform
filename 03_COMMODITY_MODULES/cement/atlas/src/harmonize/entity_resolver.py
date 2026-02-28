#!/usr/bin/env python3
"""
Entity Resolution Module
=========================
Performs fuzzy matching of company names using rapidfuzz library.
Loads target companies from YAML configuration.

Functions:
    - load_target_companies: Load company patterns from YAML config
    - fuzzy_match_companies: Match facility names against target companies
    - resolve_entities: Apply entity resolution to facilities
"""

import pandas as pd
import yaml
from rapidfuzz import fuzz, process
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class EntityResolver:
    """Handles fuzzy matching and entity resolution for company names."""

    def __init__(self, config_path: str, fuzzy_threshold: int = 65):
        """
        Initialize Entity Resolver.

        Args:
            config_path: Path to target companies YAML configuration
            fuzzy_threshold: Minimum match score (0-100) to consider a match
        """
        self.config_path = config_path
        self.fuzzy_threshold = fuzzy_threshold
        self.target_companies = self._load_target_companies()

    def _load_target_companies(self) -> List[str]:
        """
        Load target company patterns from YAML config file.

        Returns:
            List of company name patterns for fuzzy matching
        """
        if not Path(self.config_path).exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return []

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        companies = []
        for category, company_list in config.items():
            if isinstance(company_list, list):
                companies.extend(company_list)

        logger.info(f"Loaded {len(companies)} target company patterns from {self.config_path}")
        return companies

    def fuzzy_match_companies(
        self,
        df: pd.DataFrame,
        facility_name_col: str = 'FACILITY_NAME',
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Fuzzy match facility names against target company list.

        Args:
            df: DataFrame with facility records
            facility_name_col: Column name containing facility names
            limit: Maximum number of matches to return per target company

        Returns:
            DataFrame with matched facilities and match scores
        """
        if self.target_companies is None or len(self.target_companies) == 0:
            logger.warning("No target companies loaded, skipping fuzzy matching")
            return pd.DataFrame()

        logger.info("Starting fuzzy matching against target company list...")

        # Deduplicate to facility level for matching
        fac_df = df.drop_duplicates(subset='REGISTRY_ID').copy()
        facility_names = fac_df[facility_name_col].dropna().unique().tolist()

        logger.info(
            f"Matching {len(facility_names):,} unique facility names against "
            f"{len(self.target_companies)} target patterns..."
        )

        matches = []
        for target in self.target_companies:
            results = process.extract(
                target,
                facility_names,
                scorer=fuzz.token_set_ratio,
                limit=limit,
                score_cutoff=self.fuzzy_threshold
            )
            for match_name, score, idx in results:
                matches.append({
                    'target_company': target,
                    'matched_facility_name': match_name,
                    'match_score': score
                })

        if not matches:
            logger.warning("No fuzzy matches found above threshold")
            return pd.DataFrame()

        match_df = pd.DataFrame(matches).drop_duplicates(subset='matched_facility_name')

        # Merge back to get full facility records
        enriched = df.merge(
            match_df,
            left_on=facility_name_col,
            right_on='matched_facility_name',
            how='inner'
        )

        logger.info(f"Fuzzy matches found: {len(match_df):,} unique facility names")
        logger.info(f"Enriched records: {len(enriched):,}")
        logger.info(f"Unique matched facilities: {enriched['REGISTRY_ID'].nunique():,}")

        # Show match distribution
        logger.info("Top matched companies:")
        for target, count in enriched['target_company'].value_counts().head(20).items():
            logger.info(f"  {target}: {count:,} records")

        return enriched

    def resolve_entities(
        self,
        df: pd.DataFrame,
        facility_name_col: str = 'FACILITY_NAME'
    ) -> pd.DataFrame:
        """
        Apply entity resolution to facilities, adding company matches.

        Args:
            df: DataFrame with facility records
            facility_name_col: Column name containing facility names

        Returns:
            DataFrame with company resolution columns added
        """
        matched = self.fuzzy_match_companies(df, facility_name_col)

        if matched.empty:
            # Return original dataframe with empty resolution columns
            df['resolved_company'] = None
            df['match_score'] = None
            return df

        # For facilities with matches, use resolved company
        # For facilities without matches, keep original
        df = df.merge(
            matched[['REGISTRY_ID', 'target_company', 'match_score']].drop_duplicates('REGISTRY_ID'),
            on='REGISTRY_ID',
            how='left'
        )
        df = df.rename(columns={'target_company': 'resolved_company'})

        matched_count = df['resolved_company'].notna().sum()
        logger.info(
            f"Entity resolution complete: {matched_count:,} of {len(df):,} "
            f"facilities matched to known companies"
        )

        return df

    def get_match_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary statistics of entity resolution results.

        Args:
            df: DataFrame with resolved entities

        Returns:
            DataFrame with match summary by company
        """
        if 'resolved_company' not in df.columns:
            logger.warning("No resolved_company column found")
            return pd.DataFrame()

        summary = df[df['resolved_company'].notna()].groupby('resolved_company').agg({
            'REGISTRY_ID': 'nunique',
            'match_score': ['mean', 'min', 'max']
        }).reset_index()

        summary.columns = [
            'company', 'facility_count', 'avg_score', 'min_score', 'max_score'
        ]
        summary = summary.sort_values('facility_count', ascending=False)

        return summary


# Convenience functions for direct usage
def load_target_companies(config_path: str) -> List[str]:
    """
    Load target company patterns from YAML config.

    Args:
        config_path: Path to target companies YAML file

    Returns:
        List of company name patterns
    """
    resolver = EntityResolver(config_path)
    return resolver.target_companies


def fuzzy_match_facilities(
    df: pd.DataFrame,
    config_path: str,
    threshold: int = 65,
    facility_name_col: str = 'FACILITY_NAME'
) -> pd.DataFrame:
    """
    Convenience function to perform fuzzy matching on facilities.

    Args:
        df: DataFrame with facility records
        config_path: Path to target companies YAML file
        threshold: Minimum match score (0-100)
        facility_name_col: Column name containing facility names

    Returns:
        DataFrame with matched facilities
    """
    resolver = EntityResolver(config_path, threshold)
    return resolver.fuzzy_match_companies(df, facility_name_col)


def resolve_facility_entities(
    df: pd.DataFrame,
    config_path: str,
    threshold: int = 65,
    facility_name_col: str = 'FACILITY_NAME'
) -> pd.DataFrame:
    """
    Convenience function to resolve entities in facility dataframe.

    Args:
        df: DataFrame with facility records
        config_path: Path to target companies YAML file
        threshold: Minimum match score (0-100)
        facility_name_col: Column name containing facility names

    Returns:
        DataFrame with entity resolution columns added
    """
    resolver = EntityResolver(config_path, threshold)
    return resolver.resolve_entities(df, facility_name_col)


def get_company_categories(config_path: str) -> Dict[str, List[str]]:
    """
    Load company categories from YAML config.

    Args:
        config_path: Path to target companies YAML file

    Returns:
        Dictionary mapping category names to lists of companies
    """
    if not Path(config_path).exists():
        return {}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return {k: v for k, v in config.items() if isinstance(v, list)}
