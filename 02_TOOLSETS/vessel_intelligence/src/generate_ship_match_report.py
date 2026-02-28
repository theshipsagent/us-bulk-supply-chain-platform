#!/usr/bin/env python3
"""Generate ship matching statistics and report after processing voyages."""

import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def generate_ship_match_report(event_log_path: str, output_path: str = "ship_match_report.txt"):
    """
    Generate comprehensive ship matching statistics from event log.

    Args:
        event_log_path: Path to event_log.csv
        output_path: Path to write report
    """
    logger.info("=" * 80)
    logger.info("SHIP REGISTER MATCHING STATISTICS REPORT")
    logger.info("=" * 80)

    try:
        # Load event log
        logger.info(f"\nLoading event log from: {event_log_path}")
        df = pd.read_csv(event_log_path)
        logger.info(f"Loaded {len(df)} events")

        # Initialize report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SHIP REGISTER INTEGRATION - MATCHING STATISTICS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Report File: {output_path}\n")

        # Overall Statistics
        report_lines.append("OVERALL STATISTICS")
        report_lines.append("-" * 80)
        total_events = len(df)
        report_lines.append(f"Total Events Processed:           {total_events:>10,}")

        # Match method breakdown
        if 'ShipMatchMethod' in df.columns:
            match_counts = df['ShipMatchMethod'].value_counts(dropna=False)
            imo_matches = match_counts.get('imo', 0)
            name_matches = match_counts.get('name', 0)
            no_matches = match_counts.get(None, 0) + match_counts.get('', 0)

            total_matched = imo_matches + name_matches
            match_rate = (total_matched / total_events * 100) if total_events > 0 else 0

            report_lines.append(f"Events Matched by IMO:           {imo_matches:>10,} ({imo_matches/total_events*100:>6.2f}%)")
            report_lines.append(f"Events Matched by Name:          {name_matches:>10,} ({name_matches/total_events*100:>6.2f}%)")
            report_lines.append(f"Events with No Match:            {no_matches:>10,} ({no_matches/total_events*100:>6.2f}%)")
            report_lines.append(f"Total Match Rate:                {match_rate:>10.2f}%\n")

        # Ship Type Distribution (from matches only)
        report_lines.append("SHIP TYPE DISTRIBUTION (Matched Records Only)")
        report_lines.append("-" * 80)
        if 'ShipType_Register' in df.columns:
            df_matched = df[df['ShipMatchMethod'].isin(['imo', 'name'])]
            ship_types = df_matched['ShipType_Register'].value_counts()

            if len(ship_types) > 0:
                for ship_type, count in ship_types.items():
                    pct = (count / len(df_matched) * 100) if len(df_matched) > 0 else 0
                    report_lines.append(f"  {str(ship_type):<30} {count:>10,} ({pct:>6.2f}%)")
                report_lines.append(f"  {'Ships with blank type':<30} {(len(df_matched) - ship_types.sum()):>10,}")
            else:
                report_lines.append("  No ship type data available")

        report_lines.append("")

        # DWT Statistics
        report_lines.append("DEADWEIGHT TONNAGE (DWT) STATISTICS")
        report_lines.append("-" * 80)
        if 'DWT' in df.columns:
            dwt_data = pd.to_numeric(df['DWT'], errors='coerce')
            dwt_valid = dwt_data.dropna()

            if len(dwt_valid) > 0:
                report_lines.append(f"Events with DWT Data:            {len(dwt_valid):>10,} ({len(dwt_valid)/total_events*100:>6.2f}%)")
                report_lines.append(f"Minimum DWT:                     {dwt_valid.min():>10.0f} tons")
                report_lines.append(f"Maximum DWT:                     {dwt_valid.max():>10.0f} tons")
                report_lines.append(f"Average DWT:                     {dwt_valid.mean():>10.0f} tons")
                report_lines.append(f"Median DWT:                      {dwt_valid.median():>10.0f} tons")
                report_lines.append(f"Std Dev:                         {dwt_valid.std():>10.0f} tons")

                # DWT Distribution
                report_lines.append("\n  DWT Range Distribution:")
                ranges = [
                    (0, 10000, "0-10K"),
                    (10000, 30000, "10K-30K"),
                    (30000, 50000, "30K-50K"),
                    (50000, 100000, "50K-100K"),
                    (100000, float('inf'), "100K+")
                ]
                for min_dwt, max_dwt, label in ranges:
                    count = ((dwt_valid >= min_dwt) & (dwt_valid < max_dwt)).sum()
                    pct = (count / len(dwt_valid) * 100) if len(dwt_valid) > 0 else 0
                    report_lines.append(f"    {label:<15} {count:>10,} ({pct:>6.2f}%)")
            else:
                report_lines.append("No DWT data available")

        report_lines.append("")

        # Draft Statistics
        report_lines.append("DRAFT STATISTICS (RegisterDraft_m)")
        report_lines.append("-" * 80)
        if 'RegisterDraft_m' in df.columns:
            draft_data = pd.to_numeric(df['RegisterDraft_m'], errors='coerce')
            draft_valid = draft_data.dropna()

            if len(draft_valid) > 0:
                report_lines.append(f"Events with Draft Data:          {len(draft_valid):>10,} ({len(draft_valid)/total_events*100:>6.2f}%)")
                report_lines.append(f"Minimum Draft:                   {draft_valid.min():>10.2f} m")
                report_lines.append(f"Maximum Draft:                   {draft_valid.max():>10.2f} m")
                report_lines.append(f"Average Draft:                   {draft_valid.mean():>10.2f} m")
                report_lines.append(f"Median Draft:                    {draft_valid.median():>10.2f} m")

                # Draft Distribution
                report_lines.append("\n  Draft Range Distribution:")
                draft_ranges = [
                    (0, 5, "0-5m"),
                    (5, 10, "5-10m"),
                    (10, 15, "10-15m"),
                    (15, 20, "15-20m"),
                    (20, float('inf'), "20m+")
                ]
                for min_draft, max_draft, label in draft_ranges:
                    count = ((draft_valid >= min_draft) & (draft_valid < max_draft)).sum()
                    pct = (count / len(draft_valid) * 100) if len(draft_valid) > 0 else 0
                    report_lines.append(f"    {label:<15} {count:>10,} ({pct:>6.2f}%)")
            else:
                report_lines.append("No draft data available")

        report_lines.append("")

        # Top Vessels
        report_lines.append("TOP 20 VESSELS BY EVENT FREQUENCY")
        report_lines.append("-" * 80)
        if 'VesselName' in df.columns:
            vessel_counts = df['VesselName'].value_counts().head(20)
            for idx, (vessel, count) in enumerate(vessel_counts.items(), 1):
                pct = (count / total_events * 100) if total_events > 0 else 0
                report_lines.append(f"{idx:>2}. {vessel:<40} {count:>10,} ({pct:>6.2f}%)")

        report_lines.append("")

        # Vessels by DWT (Top 10 matched)
        report_lines.append("TOP 10 VESSELS BY DWT (Matched Only)")
        report_lines.append("-" * 80)
        if 'VesselName' in df.columns and 'DWT' in df.columns:
            df_matched_dwt = df[df['ShipMatchMethod'].isin(['imo', 'name'])].copy()
            df_matched_dwt['DWT_numeric'] = pd.to_numeric(df_matched_dwt['DWT'], errors='coerce')
            df_matched_dwt = df_matched_dwt.dropna(subset=['DWT_numeric'])

            if len(df_matched_dwt) > 0:
                top_vessels = df_matched_dwt.drop_duplicates('VesselName').nlargest(10, 'DWT_numeric')
                for idx, row in enumerate(top_vessels.itertuples(), 1):
                    report_lines.append(f"{idx:>2}. {row.VesselName:<40} {row.DWT_numeric:>10.0f} tons")
            else:
                report_lines.append("No DWT data available")

        report_lines.append("")

        # Data Quality Summary
        report_lines.append("DATA QUALITY SUMMARY")
        report_lines.append("-" * 80)
        if 'ShipMatchMethod' in df.columns:
            matched_events = df[df['ShipMatchMethod'].isin(['imo', 'name'])]
            report_lines.append(f"Events Successfully Matched:     {len(matched_events):>10,} ({len(matched_events)/total_events*100:>6.2f}%)")

            # Characteristics coverage
            if 'ShipType_Register' in df.columns:
                ship_type_coverage = matched_events['ShipType_Register'].notna().sum()
                report_lines.append(f"  - With Ship Type:              {ship_type_coverage:>10,} ({ship_type_coverage/len(matched_events)*100:>6.2f}% of matched)")

            if 'DWT' in df.columns:
                dwt_coverage = pd.to_numeric(matched_events['DWT'], errors='coerce').notna().sum()
                report_lines.append(f"  - With DWT:                    {dwt_coverage:>10,} ({dwt_coverage/len(matched_events)*100:>6.2f}% of matched)")

            if 'RegisterDraft_m' in df.columns:
                draft_coverage = pd.to_numeric(matched_events['RegisterDraft_m'], errors='coerce').notna().sum()
                report_lines.append(f"  - With Draft:                  {draft_coverage:>10,} ({draft_coverage/len(matched_events)*100:>6.2f}% of matched)")

            if 'TPC' in df.columns:
                tpc_coverage = pd.to_numeric(matched_events['TPC'], errors='coerce').notna().sum()
                report_lines.append(f"  - With TPC:                    {tpc_coverage:>10,} ({tpc_coverage/len(matched_events)*100:>6.2f}% of matched)")

        report_lines.append("")
        report_lines.append("=" * 80)

        # Write report
        report_text = "\n".join(report_lines)
        print(report_text)

        with open(output_path, 'w') as f:
            f.write(report_text + "\n")

        logger.info(f"\nReport written to: {output_path}")
        return report_text

    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        event_log = sys.argv[1]
    else:
        # Try common location
        event_log = "event_log.csv"

    if not Path(event_log).exists():
        logger.error(f"Event log not found: {event_log}")
        return 1

    try:
        generate_ship_match_report(event_log)
        return 0
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
