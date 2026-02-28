"""
Generate US Flag Fleet Analysis DOCX Report
Orchestrates analysis and report generation
"""
import sys
import logging
from pathlib import Path

import pandas as pd
import yaml

# Add src to path
sys.path.insert(0, 'src')

from analyzers.fleet_analyzer import FleetAnalyzer
from report.intelligence_report_builder import IntelligenceReportBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("US FLAG FLEET ANALYSIS - DOCX REPORT GENERATION")
    logger.info("=" * 60)

    # Load configuration
    logger.info("Loading configuration...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Load vessel data
    logger.info("Loading vessel data...")
    vessel_df = pd.read_csv('data/processed/us_flag_fleet_master.csv')
    logger.info(f"Loaded {len(vessel_df)} vessels")

    # Run fleet analysis
    logger.info("Running fleet analysis...")
    fleet_analyzer = FleetAnalyzer(vessel_df)
    fleet_results = fleet_analyzer.analyze()

    # Combine analysis results
    analysis_results = {
        'fleet': fleet_results
    }

    # Log key findings
    logger.info("=" * 60)
    logger.info("ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total vessels: {fleet_results['overview']['total_vessels']}")
    logger.info(f"Commercial: {fleet_results['categories']['commercial_total']} "
                f"({fleet_results['categories']['percentages']['commercial']:.1f}%)")
    logger.info(f"MSC: {fleet_results['categories']['msc_total']} "
                f"({fleet_results['categories']['percentages']['msc']:.1f}%)")
    logger.info(f"RRF: {fleet_results['categories']['rrf_total']} "
                f"({fleet_results['categories']['percentages']['rrf']:.1f}%)")
    logger.info(f"Norfolk vessels: {fleet_results['geography']['norfolk_vessels']} "
                f"({fleet_results['geography']['norfolk_percentage']:.1f}%)")

    # Generate Intelligence Brief
    logger.info("=" * 60)
    logger.info("GENERATING INTELLIGENCE BRIEF")
    logger.info("=" * 60)

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    report_builder = IntelligenceReportBuilder(config, output_dir)
    report_path = report_builder.generate_report(
        vessel_df,
        analysis_results
    )

    logger.info("=" * 60)
    logger.info("REPORT GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Report saved to: {report_path}")
    logger.info(f"File size: {report_path.stat().st_size / 1024:.1f} KB")

    # Report structure
    logger.info("\nIntelligence Brief Structure:")
    logger.info("  • Executive Summary (1 page, bullets)")
    logger.info("  • MSC Fleet Intelligence (vessel-by-vessel, programs)")
    logger.info("  • Norfolk Operations (operator breakdown)")
    logger.info("  • Commercial Fleet Summary")
    logger.info("  • Operator Intelligence")
    logger.info("  • Complete Vessel Inventory")

    print(f"\nSUCCESS! Intelligence brief generated: {report_path}")
    print(f"File size: {report_path.stat().st_size / 1024:.1f} KB")
    print(f"\nData-dense format. No fluff.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
