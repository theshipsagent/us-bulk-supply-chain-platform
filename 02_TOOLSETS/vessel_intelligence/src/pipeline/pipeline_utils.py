"""
Pipeline Utilities - Shared Functions for Classification Phases
================================================================
Common functions used across phase_00 through phase_07 scripts.

Eliminates code duplication and ensures consistent behavior.

Functions:
- stamp(): Timestamped logging
- load_phase_data(): Load CSV with standard preprocessing
- apply_classification(): Apply rule to matching records
- print_phase_results(): Standard results section
- get_statistics(): Calculate classification statistics

Author: WSD3 / Claude Code
Date: 2026-02-09
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Base directory - can be overridden via environment variable
BASE_DIR = Path(os.getenv('PANJIVA_BASE', r"G:\My Drive\LLM\project_manifest"))

# Standard paths
PIPELINE_DIR = BASE_DIR / "PIPELINE"
DICTIONARIES_DIR = BASE_DIR / "DICTIONARIES"
RAW_DATA_DIR = BASE_DIR / "RAW_DATA"


# ============================================================================
# LOGGING
# ============================================================================

def stamp(msg: str):
    """
    Print message with timestamp.

    Used consistently across all phase scripts for uniform output.

    Args:
        msg: Message to print
    """
    logger.info(msg)


# ============================================================================
# DATA LOADING
# ============================================================================

def load_phase_data(
    input_file: Path,
    add_tons_numeric: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    Load phase data with standard preprocessing.

    Args:
        input_file: Path to input CSV
        add_tons_numeric: Whether to add Tons_Numeric column

    Returns:
        Tuple of (dataframe, initial_stats dict)

    Example:
        df, stats = load_phase_data(INPUT_FILE)
        print(f"Loaded {stats['total_records']:,} records")
    """
    stamp(f"Loading data: {input_file.name}")

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    stamp(f"  Total records: {len(df):,}")

    stats = {
        'total_records': len(df),
        'total_columns': len(df.columns),
    }

    if add_tons_numeric:
        df['Tons_Numeric'] = pd.to_numeric(df['Tons'], errors='coerce').fillna(0)
        stats['total_tons'] = df['Tons_Numeric'].sum()

    # Calculate initial classification state
    stats['unclassified_records'] = df['Group'].isna().sum()
    stats['excluded_records'] = (df['Group'] == 'EXCLUDED').sum()
    stats['classified_records'] = ((df['Group'].notna()) & (df['Group'] != 'EXCLUDED')).sum()

    if add_tons_numeric:
        stats['unclassified_tons'] = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
        stats['excluded_tons'] = df.loc[df['Group'] == 'EXCLUDED', 'Tons_Numeric'].sum()
        stats['classified_tons'] = df.loc[(df['Group'].notna()) & (df['Group'] != 'EXCLUDED'), 'Tons_Numeric'].sum()

    stamp(f"  Unclassified: {stats['unclassified_records']:,} records" +
          (f", {stats['unclassified_tons']:,.0f} tons" if add_tons_numeric else ""))

    return df, stats


def save_phase_data(df: pd.DataFrame, output_file: Path, drop_temp_cols: bool = True):
    """
    Save phase data with cleanup.

    Args:
        df: DataFrame to save
        output_file: Path to output CSV
        drop_temp_cols: Whether to drop temporary columns like Tons_Numeric
    """
    if drop_temp_cols and 'Tons_Numeric' in df.columns:
        df = df.drop(columns=['Tons_Numeric'])

    stamp(f"Saving: {output_file.name}")
    df.to_csv(output_file, index=False)
    stamp(f"  Saved {len(df):,} records")


# ============================================================================
# CLASSIFICATION HELPERS
# ============================================================================

def apply_classification(
    df: pd.DataFrame,
    mask: pd.Series,
    rule: Dict,
    rule_id: str,
    classification_source: str = None
) -> Tuple[int, float]:
    """
    Apply classification rule to matching records.

    Args:
        df: DataFrame to modify (modified in place)
        mask: Boolean mask of records to classify
        rule: Rule dictionary with Group, Commodity, Cargo, Cargo_Detail
        rule_id: Rule identifier for tracking
        classification_source: Override for Classified_By_Rule column

    Returns:
        Tuple of (records_classified, tons_classified)
    """
    match_count = mask.sum()
    if match_count == 0:
        return 0, 0.0

    # Calculate tonnage before applying
    match_tons = df.loc[mask, 'Tons_Numeric'].sum() if 'Tons_Numeric' in df.columns else 0.0

    # Apply classification
    df.loc[mask, 'Group'] = rule.get('Group', rule.get('group'))
    df.loc[mask, 'Commodity'] = rule.get('Commodity', rule.get('commodity'))
    df.loc[mask, 'Cargo'] = rule.get('Cargo', rule.get('cargo'))

    # Handle Cargo_Detail with fallback to Cargo
    cargo_detail = rule.get('Cargo_Detail', rule.get('CargoDetail', rule.get('cargo_detail')))
    if pd.isna(cargo_detail) or cargo_detail is None:
        cargo_detail = rule.get('Cargo', rule.get('cargo'))
    df.loc[mask, 'Cargo_Detail'] = cargo_detail

    # Track which rule classified this record
    df.loc[mask, 'Classified_By_Rule'] = classification_source or f'Rule_{rule_id}'

    return match_count, match_tons


# ============================================================================
# STATISTICS
# ============================================================================

def get_statistics(df: pd.DataFrame) -> Dict:
    """
    Calculate classification statistics.

    Args:
        df: DataFrame with classification columns

    Returns:
        Dictionary with classification stats
    """
    total_records = len(df)
    has_tons = 'Tons_Numeric' in df.columns

    if has_tons:
        total_tons = df['Tons_Numeric'].sum()
    else:
        total_tons = 0

    # Record counts
    unclassified = df['Group'].isna().sum()
    excluded = (df['Group'] == 'EXCLUDED').sum()
    classified = total_records - unclassified - excluded

    stats = {
        'total_records': total_records,
        'classified_records': classified,
        'excluded_records': excluded,
        'unclassified_records': unclassified,
        'classified_pct': (classified / total_records * 100) if total_records > 0 else 0,
        'excluded_pct': (excluded / total_records * 100) if total_records > 0 else 0,
        'unclassified_pct': (unclassified / total_records * 100) if total_records > 0 else 0,
    }

    if has_tons:
        # Tonnage calculations
        unclassified_tons = df.loc[df['Group'].isna(), 'Tons_Numeric'].sum()
        excluded_tons = df.loc[df['Group'] == 'EXCLUDED', 'Tons_Numeric'].sum()
        classified_tons = total_tons - unclassified_tons - excluded_tons

        stats.update({
            'total_tons': total_tons,
            'classified_tons': classified_tons,
            'excluded_tons': excluded_tons,
            'unclassified_tons': unclassified_tons,
            'classified_tons_pct': (classified_tons / total_tons * 100) if total_tons > 0 else 0,
            'excluded_tons_pct': (excluded_tons / total_tons * 100) if total_tons > 0 else 0,
            'unclassified_tons_pct': (unclassified_tons / total_tons * 100) if total_tons > 0 else 0,
        })

    return stats


def print_phase_results(
    df: pd.DataFrame,
    phase_name: str,
    stats_before: Dict,
    captured_records: int,
    captured_tons: float,
    by_category: Dict = None
):
    """
    Print standard results section for a phase.

    Args:
        df: DataFrame after processing
        phase_name: Name of phase (e.g., "Phase 4")
        stats_before: Statistics dict from before processing
        captured_records: Records classified in this phase
        captured_tons: Tons classified in this phase
        by_category: Optional breakdown by commodity/cargo
    """
    stamp("\n" + "=" * 80)
    stamp(f"RESULTS - {phase_name}")
    stamp("=" * 80)

    # Before/After comparison
    stats_after = get_statistics(df)

    stamp(f"\nBEFORE:")
    stamp(f"  Unclassified: {stats_before['unclassified_records']:,} records" +
          (f", {stats_before.get('unclassified_tons', 0):,.0f} tons" if 'unclassified_tons' in stats_before else ""))

    stamp(f"\nCAPTURED ({phase_name}):")
    stamp(f"  Total: {captured_records:,} records, {captured_tons:,.0f} tons")

    stamp(f"\nAFTER:")
    stamp(f"  Unclassified: {stats_after['unclassified_records']:,} records" +
          (f", {stats_after.get('unclassified_tons', 0):,.0f} tons" if 'unclassified_tons' in stats_after else ""))

    # Category breakdown if provided
    if by_category:
        stamp(f"\nBY CATEGORY (top 10):")
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1].get('tons', x[1].get('records', 0)), reverse=True)[:10]
        for cat, stats in sorted_cats:
            cat_display = cat[:40] if len(cat) > 40 else cat
            stamp(f"  {cat_display:40s}: {stats['records']:>6,} records, {stats.get('tons', 0):>12,.0f} tons")

    # Overall status
    stamp(f"\nOVERALL STATUS:")
    stamp(f"  Classified:   {stats_after['classified_records']:,} records ({stats_after['classified_pct']:.1f}%)" +
          (f", {stats_after.get('classified_tons', 0):,.0f} tons ({stats_after.get('classified_tons_pct', 0):.1f}%)" if 'classified_tons' in stats_after else ""))
    stamp(f"  Excluded:     {stats_after['excluded_records']:,} records ({stats_after['excluded_pct']:.1f}%)" +
          (f", {stats_after.get('excluded_tons', 0):,.0f} tons ({stats_after.get('excluded_tons_pct', 0):.1f}%)" if 'excluded_tons' in stats_after else ""))
    stamp(f"  Unclassified: {stats_after['unclassified_records']:,} records ({stats_after['unclassified_pct']:.1f}%)" +
          (f", {stats_after.get('unclassified_tons', 0):,.0f} tons ({stats_after.get('unclassified_tons_pct', 0):.1f}%)" if 'unclassified_tons' in stats_after else ""))


# ============================================================================
# DURATION TRACKING
# ============================================================================

class PhaseTimer:
    """
    Simple timer for tracking phase duration.

    Example:
        timer = PhaseTimer("Phase 4")
        # ... processing ...
        timer.complete()
    """

    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.start_time = datetime.now()
        stamp(f"\n{'=' * 80}")
        stamp(f"{phase_name} STARTED")
        stamp(f"{'=' * 80}")

    def elapsed(self) -> float:
        """Return elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def complete(self, records_processed: int = None):
        """Print completion message with duration"""
        duration = self.elapsed()

        stamp(f"\n{'=' * 80}")
        stamp(f"{self.phase_name} COMPLETE")
        stamp(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        if records_processed:
            rate = records_processed / duration if duration > 0 else 0
            stamp(f"  Processing rate: {rate:.0f} records/second")

        stamp(f"{'=' * 80}")


# ============================================================================
# DICTIONARY HELPERS
# ============================================================================

def load_dictionary(dict_path: Path, required_columns: list = None) -> pd.DataFrame:
    """
    Load and validate a dictionary file.

    Args:
        dict_path: Path to dictionary CSV
        required_columns: List of required column names

    Returns:
        DataFrame with dictionary contents

    Raises:
        FileNotFoundError: If dictionary doesn't exist
        ValueError: If required columns missing
    """
    if not dict_path.exists():
        raise FileNotFoundError(f"Dictionary not found: {dict_path}")

    stamp(f"Loading dictionary: {dict_path.name}")
    df = pd.read_csv(dict_path, dtype=str)
    stamp(f"  Loaded {len(df)} entries")

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Dictionary missing required columns: {missing}")

    return df


def validate_input_file(input_file: Path) -> bool:
    """
    Validate that input file exists and is readable.

    Args:
        input_file: Path to check

    Returns:
        True if valid, False otherwise
    """
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    if input_file.stat().st_size == 0:
        logger.error(f"Input file is empty: {input_file}")
        return False

    return True


# ============================================================================
# CONVENIENCE EXPORTS
# ============================================================================

__all__ = [
    'BASE_DIR',
    'PIPELINE_DIR',
    'DICTIONARIES_DIR',
    'RAW_DATA_DIR',
    'stamp',
    'load_phase_data',
    'save_phase_data',
    'apply_classification',
    'get_statistics',
    'print_phase_results',
    'PhaseTimer',
    'validate_input_file',
    'load_dictionary',
]
