"""
US Flag Vessel Analysis - Main Orchestration Script
Coordinates data collection, processing, analysis, and report generation
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import yaml

# Import project modules
from src.scrapers.usace_scraper import USACEScraper
from src.scrapers.marad_scraper import MARADScraper
from src.scrapers.gov_sources import GovSourcesScraper
from src.processors.vessel_processor import VesselProcessor
from src.processors.operator_linker import OperatorLinker
from src.analyzers.msc_analyzer import MSCAnalyzer
from src.report_generator import ReportGenerator


def setup_logging(config: dict):
    """
    Setup logging configuration

    Args:
        config: Configuration dictionary
    """
    log_config = config['logging']
    log_dir = Path(config['directories']['logs'])
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters and handlers
    log_format = log_config['format']
    log_level = getattr(logging, log_config['level'])

    # File handler
    log_file = log_dir / f"vessel_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)

    if log_config['console']:
        root_logger.addHandler(console_handler)

    logging.info("Logging initialized")
    logging.info(f"Log file: {log_file}")


def load_config(config_path: str = 'config.yaml') -> dict:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    logging.info(f"Configuration loaded from {config_path}")
    return config


def scrape_data(config: dict) -> bool:
    """
    Run data collection scrapers

    Args:
        config: Configuration dictionary

    Returns:
        True if successful
    """
    logging.info("=" * 60)
    logging.info("PHASE 1: DATA COLLECTION")
    logging.info("=" * 60)

    try:
        # USACE scraper
        logging.info("Starting USACE scraper...")
        usace_scraper = USACEScraper(
            config,
            output_dir=f"{config['directories']['raw_data']}/usace"
        )
        usace_files = usace_scraper.scrape()
        logging.info(f"USACE: Downloaded {len(usace_files)} files")

        # MARAD scraper
        logging.info("Starting MARAD scraper...")
        marad_scraper = MARADScraper(
            config,
            output_dir=f"{config['directories']['raw_data']}/marad"
        )
        marad_files = marad_scraper.scrape()
        logging.info(f"MARAD: Downloaded {len(marad_files)} files")

        # Government sources scraper
        logging.info("Starting government sources scraper...")
        gov_scraper = GovSourcesScraper(
            config,
            output_dir=f"{config['directories']['raw_data']}/other_sources"
        )
        gov_files = gov_scraper.scrape()
        logging.info(f"Gov Sources: Downloaded {len(gov_files)} files")

        total_files = len(usace_files) + len(marad_files) + len(gov_files)
        logging.info(f"Data collection complete: {total_files} total files")

        return True

    except Exception as e:
        logging.error(f"Data collection failed: {e}", exc_info=True)
        return False


def process_data(config: dict) -> tuple:
    """
    Process raw data files

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (vessel_df, operator_df) or (None, None) on failure
    """
    logging.info("=" * 60)
    logging.info("PHASE 2: DATA PROCESSING")
    logging.info("=" * 60)

    try:
        # Initialize processors
        vessel_processor = VesselProcessor(config)
        operator_linker = OperatorLinker(config)

        # Process vessel data
        logging.info("Processing vessel data...")
        raw_data_dir = Path(config['directories']['raw_data'])
        processed_dir = Path(config['directories']['processed_data'])
        processed_dir.mkdir(parents=True, exist_ok=True)

        vessel_output = processed_dir / 'vessel_inventory.csv'
        vessel_df = vessel_processor.process_directory(raw_data_dir, vessel_output)

        if vessel_df.empty:
            logging.warning("No vessel data processed")
            return None, None

        # Filter US flag vessels
        vessel_df = vessel_processor.filter_us_flag(vessel_df)
        logging.info(f"Processed {len(vessel_df)} US flag vessels")

        # Link operators
        logging.info("Linking operators to vessels...")
        vessel_df = operator_linker.link_operators(vessel_df)

        # Build operator directory
        logging.info("Building operator directory...")
        operator_output = processed_dir / 'operator_directory.csv'
        operator_df = operator_linker.build_operator_directory(vessel_df, operator_output)

        # Save updated vessel data
        vessel_df.to_csv(vessel_output, index=False)
        logging.info(f"Updated vessel data saved to {vessel_output}")

        # Print summary statistics
        stats = vessel_processor.get_summary_statistics(vessel_df)
        logging.info(f"Summary Statistics:")
        logging.info(f"  Total vessels: {stats['total_vessels']}")
        logging.info(f"  Unique operators: {stats['unique_operators']}")
        logging.info(f"  Unique types: {stats['unique_types']}")

        return vessel_df, operator_df

    except Exception as e:
        logging.error(f"Data processing failed: {e}", exc_info=True)
        return None, None


def analyze_msc(config: dict, vessel_df, operator_df) -> dict:
    """
    Perform MSC-specific analysis

    Args:
        config: Configuration dictionary
        vessel_df: Vessel data DataFrame
        operator_df: Operator directory DataFrame

    Returns:
        Analysis results dictionary or None on failure
    """
    logging.info("=" * 60)
    logging.info("PHASE 3: MSC ANALYSIS")
    logging.info("=" * 60)

    try:
        # Initialize analyzer
        msc_analyzer = MSCAnalyzer(config)

        # Run analysis
        logging.info("Analyzing MSC fleet...")
        analysis = msc_analyzer.analyze(vessel_df)

        # Log key findings
        summary = analysis['summary']
        logging.info(f"MSC Analysis Results:")
        logging.info(f"  Total MSC vessels: {summary['total_msc_vessels']}")
        logging.info(f"  US flag vessels: {summary.get('us_flag_vessels', 0)}")
        logging.info(f"  Unique operators: {summary.get('unique_operators', 0)}")

        norfolk = analysis['norfolk_analysis']
        logging.info(f"  Norfolk vessels: {norfolk['total_norfolk_vessels']}")

        # Export analysis results
        processed_dir = Path(config['directories']['processed_data'])
        msc_analyzer.export_analysis(analysis, processed_dir)

        return analysis

    except Exception as e:
        logging.error(f"MSC analysis failed: {e}", exc_info=True)
        return None


def generate_report(config: dict, analysis: dict, vessel_df, operator_df) -> bool:
    """
    Generate PDF report

    Args:
        config: Configuration dictionary
        analysis: Analysis results
        vessel_df: Vessel data DataFrame
        operator_df: Operator directory DataFrame

    Returns:
        True if successful
    """
    logging.info("=" * 60)
    logging.info("PHASE 4: REPORT GENERATION")
    logging.info("=" * 60)

    try:
        # Initialize report generator
        report_dir = config['directories']['reports']
        report_generator = ReportGenerator(config, report_dir)

        # Generate report
        logging.info("Generating PDF report...")
        report_path = report_generator.generate_report(analysis, vessel_df, operator_df)

        logging.info(f"Report generated successfully: {report_path}")
        logging.info(f"Report size: {report_path.stat().st_size / 1024:.1f} KB")

        return True

    except Exception as e:
        logging.error(f"Report generation failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='US Flag Vessel Analysis - MSC Fleet Report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --all              Run complete pipeline
  python main.py --scrape           Collect data only
  python main.py --process          Process existing data
  python main.py --analyze          Analyze processed data
  python main.py --report           Generate report from existing analysis
        """
    )

    # Operation modes
    parser.add_argument('--all', action='store_true',
                       help='Run complete pipeline')
    parser.add_argument('--scrape', action='store_true',
                       help='Run data collection scrapers')
    parser.add_argument('--process', action='store_true',
                       help='Process raw data files')
    parser.add_argument('--analyze', action='store_true',
                       help='Run MSC analysis')
    parser.add_argument('--report', action='store_true',
                       help='Generate PDF report')

    # Options
    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--skip-cache', action='store_true',
                       help='Skip cached data and re-scrape')

    args = parser.parse_args()

    # Default to --all if no options specified
    if not any([args.all, args.scrape, args.process, args.analyze, args.report]):
        args.all = True

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Setup logging
    setup_logging(config)

    logging.info("=" * 60)
    logging.info("US FLAG VESSEL ANALYSIS - MSC FLEET REPORT")
    logging.info("=" * 60)
    logging.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    vessel_df = None
    operator_df = None
    analysis = None

    try:
        # Phase 1: Data Collection
        if args.all or args.scrape:
            success = scrape_data(config)
            if not success and not args.all:
                return 1

        # Phase 2: Data Processing
        if args.all or args.process or args.analyze or args.report:
            vessel_df, operator_df = process_data(config)
            if vessel_df is None and (args.all or args.process):
                logging.error("Cannot proceed without processed data")
                return 1

        # Phase 3: MSC Analysis
        if args.all or args.analyze or args.report:
            if vessel_df is None:
                # Try loading processed data
                processed_dir = Path(config['directories']['processed_data'])
                vessel_file = processed_dir / 'vessel_inventory.csv'
                operator_file = processed_dir / 'operator_directory.csv'

                if vessel_file.exists():
                    import pandas as pd
                    vessel_df = pd.read_csv(vessel_file)
                    operator_df = pd.read_csv(operator_file) if operator_file.exists() else None
                    logging.info("Loaded processed data from files")
                else:
                    logging.error("No processed data available. Run --process first.")
                    return 1

            analysis = analyze_msc(config, vessel_df, operator_df)
            if analysis is None and (args.all or args.analyze):
                return 1

        # Phase 4: Report Generation
        if args.all or args.report:
            if analysis is None:
                logging.error("No analysis results available. Run --analyze first.")
                return 1

            success = generate_report(config, analysis, vessel_df, operator_df)
            if not success:
                return 1

        logging.info("=" * 60)
        logging.info("PIPELINE COMPLETE")
        logging.info("=" * 60)
        logging.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except KeyboardInterrupt:
        logging.warning("Process interrupted by user")
        return 130

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
