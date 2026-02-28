#!/usr/bin/env python3
"""
Entity Resolution Module — Natural Pozzolan
==============================================
Performs fuzzy matching of pozzolan producer and processor names using rapidfuzz.
Matches EPA FRS facility names against known producers from target_companies.yaml.
"""

import duckdb
import pandas as pd
import yaml
from rapidfuzz import fuzz, process
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EntityResolver:
    """Handles fuzzy matching and entity resolution for pozzolan producer names."""

    def __init__(self, config_path: str, fuzzy_threshold: int = 65):
        self.config_path = config_path
        self.fuzzy_threshold = fuzzy_threshold
        self.target_companies = self._load_target_companies()

    def _load_target_companies(self) -> List[str]:
        """Load target company patterns from YAML config file."""
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
        facility_name_col: str = 'facility_name',
        limit: int = 50
    ) -> pd.DataFrame:
        """Fuzzy match facility names against target company list."""
        if not self.target_companies:
            logger.warning("No target companies loaded, skipping fuzzy matching")
            return pd.DataFrame()

        logger.info("Starting fuzzy matching against target company list...")

        facility_names = df[facility_name_col].dropna().unique().tolist()

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

        match_df = pd.DataFrame(matches)
        match_df = match_df.sort_values('match_score', ascending=False).drop_duplicates(
            subset='matched_facility_name', keep='first'
        )

        logger.info(f"Fuzzy matches found: {len(match_df):,} unique facility names")

        logger.info("Top matched companies:")
        for target, count in match_df['target_company'].value_counts().head(20).items():
            logger.info(f"  {target}: {count:,} matches")

        return match_df

    def resolve_entities(
        self,
        df: pd.DataFrame,
        facility_name_col: str = 'facility_name'
    ) -> pd.DataFrame:
        """Apply entity resolution to facilities."""
        matched = self.fuzzy_match_companies(df, facility_name_col)

        if matched.empty:
            df = df.copy()
            df['resolved_company'] = None
            df['match_score'] = None
            return df

        df = df.merge(
            matched[['matched_facility_name', 'target_company', 'match_score']],
            left_on=facility_name_col,
            right_on='matched_facility_name',
            how='left'
        )
        df = df.drop(columns=['matched_facility_name'], errors='ignore')
        df = df.rename(columns={'target_company': 'resolved_company'})

        matched_count = df['resolved_company'].notna().sum()
        logger.info(
            f"Entity resolution complete: {matched_count:,} of {len(df):,} "
            f"facilities matched to known companies"
        )

        return df

    def save_resolved(self, df: pd.DataFrame, atlas_db_path: str) -> None:
        """Save entity-resolved facilities to ATLAS database."""
        con = duckdb.connect(atlas_db_path)
        try:
            con.execute("CREATE OR REPLACE TABLE frs_facilities_resolved AS SELECT * FROM df")

            row_count = con.execute("SELECT COUNT(*) FROM frs_facilities_resolved").fetchone()[0]
            resolved_count = con.execute(
                "SELECT COUNT(*) FROM frs_facilities_resolved WHERE resolved_company IS NOT NULL"
            ).fetchone()[0]

            logger.info(
                f"Saved {row_count:,} facilities to frs_facilities_resolved "
                f"({resolved_count:,} with company match)"
            )
        finally:
            con.close()

    def get_match_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate summary statistics of entity resolution results."""
        if 'resolved_company' not in df.columns:
            return pd.DataFrame()

        summary = df[df['resolved_company'].notna()].groupby('resolved_company').agg(
            facility_count=('registry_id', 'nunique'),
            avg_score=('match_score', 'mean'),
            min_score=('match_score', 'min'),
            max_score=('match_score', 'max'),
            states=('state', 'nunique')
        ).reset_index()

        return summary.sort_values('facility_count', ascending=False)


# Convenience functions
def load_target_companies(config_path: str) -> List[str]:
    resolver = EntityResolver(config_path)
    return resolver.target_companies


def fuzzy_match_facilities(df: pd.DataFrame, config_path: str, threshold: int = 65,
                           facility_name_col: str = 'facility_name') -> pd.DataFrame:
    resolver = EntityResolver(config_path, threshold)
    return resolver.fuzzy_match_companies(df, facility_name_col)


def resolve_facility_entities(df: pd.DataFrame, config_path: str, threshold: int = 65,
                              facility_name_col: str = 'facility_name') -> pd.DataFrame:
    resolver = EntityResolver(config_path, threshold)
    return resolver.resolve_entities(df, facility_name_col)


def get_company_categories(config_path: str) -> Dict[str, List[str]]:
    if not Path(config_path).exists():
        return {}
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return {k: v for k, v in config.items() if isinstance(v, list)}
