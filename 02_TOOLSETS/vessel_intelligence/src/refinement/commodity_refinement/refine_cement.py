"""
Cement Origin Refinement Task - v1.0
=====================================
Refine Cargo_Detail for cement shipments with origin-specific detail.

**Controlled Overwrite**: Only modifies generic "Cement NOS" values
**Permission**: Registered in task_registry.py as CEMENT_ORIGIN_v1.0

Author: WSD3 / Claude Code
Date: 2026-02-09
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from task_registry import validate_overwrite, log_refinement_change

# Paths
TASK_NAME = "CEMENT_ORIGIN_v1.0"
TASK_DIR = Path(__file__).parent.parent
AUDIT_LOG = TASK_DIR / f"audit_{TASK_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# ============================================================================
# CEMENT ORIGIN PATTERNS
# ============================================================================

# Known cement-producing entities by country
CEMENT_ENTITIES_BY_ORIGIN = {
    "TURKEY": [
        "NUH-CIMENTO-001",
        "AKCANSA-001",
        "CEMTECH-001"
    ],
    "VIETNAM": [
        "VISSAI-001"
    ],
    "MEXICO": [
        "CEMEX-001"
    ],
    "COLOMBIA": [
        "ZONA-FRANCA-ARGOS-001",
        "ARGOS-001"
    ],
    "UAE": [
        "LAFARGE-EMIRATES-001"
    ],
    "SAUDI ARABIA": [
        "SAUDI-CEMENT-001"
    ]
}

# Trade lane patterns (port + origin)
CEMENT_TRADE_LANES = {
    ("Tampa", "TURKEY"): {
        "market": "US_FLORIDA_TURKISH_CEMENT",
        "typical_grade": "Type I Portland Cement"
    },
    ("Tampa", "VIETNAM"): {
        "market": "US_FLORIDA_VIETNAMESE_CEMENT",
        "typical_grade": "Type I Portland Cement"
    },
    ("Houston", "MEXICO"): {
        "market": "US_GULF_MEXICAN_CEMENT",
        "typical_grade": "Oil Well Cement / Type I"
    },
    ("Mobile", "TURKEY"): {
        "market": "US_GULF_TURKISH_CEMENT",
        "typical_grade": "Type I Portland Cement"
    }
}


def refine_cement_origin(record):
    """
    Determine cement origin refinement for a record.

    Args:
        record: DataFrame row

    Returns:
        dict or None: Refinement details if applicable
    """
    # Only refine cement records
    if record.get('Commodity') != 'Cement':
        return None

    # Only refine if current value is generic
    current_detail = record.get('Cargo_Detail', '')
    if current_detail not in ['Cement NOS', 'Cement', 'Cement - Imported']:
        return None

    # Get origin and shipper
    origin = str(record.get('Origin_Country', '')).upper()
    shipper_entity = record.get('Shipper_Entity_ID', '')
    port = record.get('Port', '')

    # Strategy 1: Entity-based (highest confidence)
    if shipper_entity:
        for country, entities in CEMENT_ENTITIES_BY_ORIGIN.items():
            if shipper_entity in entities:
                shipper_name = record.get('Shipper_Harmonized', origin)
                return {
                    'new_value': f"Cement - {country.title()} Import ({shipper_name})",
                    'confidence': 95,
                    'method': 'Entity_Match',
                    'market_segment': f"CEMENT_US_{country.replace(' ', '_')}",
                    'trade_lane_id': f"{country}_TO_US_{port.upper().replace(' ', '_')}"
                }

    # Strategy 2: Trade lane pattern (high confidence)
    trade_lane_key = (port, origin)
    if trade_lane_key in CEMENT_TRADE_LANES:
        lane = CEMENT_TRADE_LANES[trade_lane_key]
        return {
            'new_value': f"Cement - {origin.title()} Import",
            'confidence': 85,
            'method': 'Trade_Lane_Pattern',
            'market_segment': lane['market'],
            'trade_lane_id': f"{origin}_TO_US_{port.upper().replace(' ', '_')}"
        }

    # Strategy 3: Origin-only (medium confidence)
    if origin and origin not in ['UNKNOWN', 'US', 'UNITED STATES']:
        return {
            'new_value': f"Cement - {origin.title()} Import",
            'confidence': 75,
            'method': 'Origin_Only',
            'market_segment': f"CEMENT_US_{origin.replace(' ', '_')}",
            'trade_lane_id': f"{origin}_TO_US"
        }

    return None


def apply_cement_refinement(df):
    """
    Apply cement origin refinement to dataframe.

    Args:
        df: Input dataframe

    Returns:
        DataFrame: Modified dataframe with audit trail
    """
    print(f"\n{'='*80}")
    print(f"CEMENT ORIGIN REFINEMENT - {TASK_NAME}")
    print(f"{'='*80}")

    # Initialize new columns if needed
    if 'Cargo_Detail_Original' not in df.columns:
        df['Cargo_Detail_Original'] = None
    if 'Refinement_Task' not in df.columns:
        df['Refinement_Task'] = None
    if 'Refinement_Date' not in df.columns:
        df['Refinement_Date'] = None
    if 'Refinement_Confidence' not in df.columns:
        df['Refinement_Confidence'] = None
    if 'Market_Segment' not in df.columns:
        df['Market_Segment'] = None
    if 'Trade_Lane_ID' not in df.columns:
        df['Trade_Lane_ID'] = None

    # Track changes
    changes_log = []
    overwrite_count = 0
    prevented_count = 0
    not_applicable_count = 0

    # Process cement records only
    cement_records = df[df['Commodity'] == 'Cement']
    print(f"\nProcessing {len(cement_records):,} cement records...")

    for idx, row in cement_records.iterrows():
        # Get refinement suggestion
        refinement = refine_cement_origin(row)

        if refinement is None:
            not_applicable_count += 1
            continue

        # Validate overwrite permission
        allowed, reason = validate_overwrite(
            row,
            TASK_NAME,
            'Cargo_Detail',
            refinement['new_value']
        )

        if allowed:
            # Log change
            change = {
                'REC_ID': row['REC_ID'],
                'Field': 'Cargo_Detail',
                'Old_Value': row['Cargo_Detail'],
                'New_Value': refinement['new_value'],
                'Task': TASK_NAME,
                'Method': refinement['method'],
                'Confidence': refinement['confidence'],
                'Timestamp': datetime.now().isoformat()
            }
            changes_log.append(change)

            # Apply overwrite
            df.at[idx, 'Cargo_Detail_Original'] = row['Cargo_Detail']
            df.at[idx, 'Cargo_Detail'] = refinement['new_value']
            df.at[idx, 'Refinement_Task'] = TASK_NAME
            df.at[idx, 'Refinement_Date'] = datetime.now()
            df.at[idx, 'Refinement_Confidence'] = refinement['confidence']

            # Set market segment and trade lane if provided
            if 'market_segment' in refinement:
                df.at[idx, 'Market_Segment'] = refinement['market_segment']
            if 'trade_lane_id' in refinement:
                df.at[idx, 'Trade_Lane_ID'] = refinement['trade_lane_id']

            overwrite_count += 1
        else:
            prevented_count += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"REFINEMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Cement records processed: {len(cement_records):,}")
    print(f"  Overwrites applied: {overwrite_count:,}")
    print(f"  Overwrites prevented: {prevented_count:,}")
    print(f"  Not applicable: {not_applicable_count:,}")

    # Save audit log
    if changes_log:
        log_df = pd.DataFrame(changes_log)
        log_df.to_csv(AUDIT_LOG, index=False)
        print(f"\nAudit log saved: {AUDIT_LOG.name}")

        # Summary by method
        print(f"\nRefinements by method:")
        for method, count in log_df['Method'].value_counts().items():
            avg_conf = log_df[log_df['Method'] == method]['Confidence'].mean()
            print(f"  {method}: {count:,} ({avg_conf:.0f}% avg confidence)")

    return df


def main():
    """Test cement refinement on harmonized sample"""
    import argparse

    parser = argparse.ArgumentParser(description='Refine cement cargo detail with origin')
    parser.add_argument('--input', required=True, help='Input harmonized CSV file')
    parser.add_argument('--output', required=True, help='Output refined CSV file')

    args = parser.parse_args()

    # Load data
    print(f"\nLoading: {args.input}")
    df = pd.read_csv(args.input, encoding='utf-8-sig', low_memory=False)
    print(f"  Loaded {len(df):,} records")

    # Apply refinement
    df = apply_cement_refinement(df)

    # Save output
    print(f"\nSaving: {args.output}")
    df.to_csv(args.output, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(df):,} records")

    print(f"\n{'='*80}")
    print("CEMENT REFINEMENT COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
