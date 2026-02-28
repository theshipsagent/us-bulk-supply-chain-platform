"""Maritime Voyage Analysis System - Main CLI Entry Point."""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.processing.voyage_detector import VoyageDetector
from src.processing.time_calculator import TimeCalculator
from src.processing.quality_analyzer import QualityAnalyzer
from src.processing.voyage_segmenter import VoyageSegmenter
from src.processing.efficiency_calculator import EfficiencyCalculator
from src.output.csv_writer import CSVWriter
from src.output.report_writer import ReportWriter


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Maritime Voyage Analysis System - Analyze vessel voyages and calculate KPIs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Phase 1: Basic voyage analysis (default)
  python voyage_analyzer.py -i 00_source_files/ -o results/

  # Phase 1: Filter by vessel or date range
  python voyage_analyzer.py -i 00_source_files/ -o results/ -v "Yellow Fin"
  python voyage_analyzer.py -i 00_source_files/ -o results/ -s 2026-01-01 -e 2026-01-31

  # Phase 2: Voyage segmentation and efficiency analysis
  python voyage_analyzer.py -i 00_source_files/ -o results_phase2/ --phase 2

  # Phase 2: Custom draft threshold
  python voyage_analyzer.py -i 00_source_files/ -o results_phase2/ --phase 2 --draft-threshold 2.0
        """
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input CSV file or directory containing CSV files'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory for results'
    )

    parser.add_argument(
        '-v', '--vessel',
        help='Filter by vessel name or IMO (partial match)'
    )

    parser.add_argument(
        '-s', '--start-date',
        help='Start date filter (YYYY-MM-DD)'
    )

    parser.add_argument(
        '-e', '--end-date',
        help='End date filter (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--phase',
        type=int,
        choices=[1, 2],
        default=1,
        help='Analysis phase: 1=voyage analysis (default), 2=voyage segmentation & efficiency'
    )

    parser.add_argument(
        '--draft-threshold',
        type=float,
        default=1.5,
        help='Draft threshold in feet for cargo status determination (default: 1.5)'
    )

    return parser.parse_args()


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def main():
    """Main entry point."""
    args = parse_arguments()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("MARITIME VOYAGE ANALYSIS SYSTEM")
    logger.info("=" * 80)

    try:
        # Parse date filters
        start_date = parse_date(args.start_date) if args.start_date else None
        end_date = parse_date(args.end_date) if args.end_date else None

        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir.absolute()}")

        # Stage 1: Load Data
        logger.info("\n[Stage 1/6] Loading CSV data...")
        loader = DataLoader()
        df = loader.load_data(
            args.input,
            start_date=start_date,
            end_date=end_date,
            vessel_filter=args.vessel
        )
        logger.info(f"Loaded {len(df)} records")

        # Stage 2: Preprocess Data
        logger.info("\n[Stage 2/6] Preprocessing data and creating events...")
        preprocessor = DataPreprocessor()
        events = preprocessor.process_dataframe(df)
        logger.info(f"Created {len(events)} event objects")

        # Stage 3: Detect Voyages
        logger.info("\n[Stage 3/6] Detecting voyage boundaries...")
        detector = VoyageDetector()
        voyages = detector.detect_voyages(events)
        logger.info(f"Detected {len(voyages)} voyages")

        # Stage 4: Calculate Time Metrics
        logger.info("\n[Stage 4/6] Calculating voyage metrics...")
        calculator = TimeCalculator()
        for voyage in voyages:
            calculator.calculate_voyage_metrics(voyage)
        logger.info(f"Calculated metrics for {len(voyages)} voyages")

        # Stage 5: Analyze Quality
        logger.info("\n[Stage 5/6] Analyzing data quality...")
        analyzer = QualityAnalyzer()
        quality_stats = analyzer.analyze_quality(voyages)
        logger.info(
            f"Quality analysis complete: "
            f"{quality_stats['total_issues']} issues found"
        )

        # Phase 2: Voyage Segmentation (if requested)
        segments = None
        aggregates = None
        if args.phase == 2:
            logger.info("\n[Phase 2 - Stage 1/2] Segmenting voyages...")
            segmenter = VoyageSegmenter(draft_threshold=args.draft_threshold)
            segments = segmenter.segment_voyages(voyages)
            logger.info(f"Created {len(segments)} voyage segments")

            logger.info("\n[Phase 2 - Stage 2/2] Calculating efficiency metrics...")
            calculator = EfficiencyCalculator()
            segments = calculator.calculate_efficiency(segments)
            aggregates = calculator.calculate_aggregate_metrics(segments)
            logger.info(f"Calculated efficiency metrics for {len(aggregates)} vessels")

        # Stage 6: Generate Output
        logger.info("\n[Stage 6/6] Generating output files...")

        writer = CSVWriter()

        # Write Phase 1 outputs (always generated)
        voyage_summary_path = output_dir / 'voyage_summary.csv'
        writer.write_voyage_summary(voyages, str(voyage_summary_path))

        event_log_path = output_dir / 'event_log.csv'
        writer.write_event_log(voyages, str(event_log_path))

        report_writer = ReportWriter()
        quality_report_path = output_dir / 'quality_report.txt'
        report_writer.write_quality_report(
            voyages,
            quality_stats,
            str(quality_report_path)
        )

        # Write Phase 2 outputs (if Phase 2 was run)
        voyage_segments_path = None
        efficiency_metrics_path = None
        if args.phase == 2 and segments:
            voyage_segments_path = output_dir / 'voyage_segments.csv'
            writer.write_voyage_segments(segments, str(voyage_segments_path))

            efficiency_metrics_path = output_dir / 'efficiency_metrics.csv'
            writer.write_efficiency_metrics(aggregates, str(efficiency_metrics_path))

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info(f"PROCESSING COMPLETE - PHASE {args.phase}")
        logger.info("=" * 80)
        logger.info(f"Input files:         {loader.files_loaded}")
        if loader.excluded_vessels > 0:
            logger.info(f"Excluded vessels:    {loader.excluded_vessels} events (dredges/service vessels)")
        logger.info(f"Total events:        {len(events)}")
        logger.info(f"Total voyages:       {len(voyages)}")
        logger.info(f"Complete voyages:    {quality_stats['complete_voyages']}")
        logger.info(f"Completeness rate:   {quality_stats['completeness_percentage']:.1f}%")
        logger.info(f"Quality issues:      {quality_stats['total_issues']}")

        if args.phase == 2 and segments:
            logger.info("")
            logger.info("Phase 2 Statistics:")
            logger.info(f"Voyage segments:     {len(segments)}")
            logger.info(f"Vessels analyzed:    {len(aggregates)}")
            logger.info(f"Draft threshold:     {args.draft_threshold} ft")

        logger.info("")
        logger.info("Output files:")
        logger.info(f"  - {voyage_summary_path}")
        logger.info(f"  - {event_log_path}")
        logger.info(f"  - {quality_report_path}")

        if args.phase == 2:
            if voyage_segments_path:
                logger.info(f"  - {voyage_segments_path}")
            if efficiency_metrics_path:
                logger.info(f"  - {efficiency_metrics_path}")

        logger.info("=" * 80)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
