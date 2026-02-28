"""
USACE Market Study - HTML Report Orchestrator
Coordinates analysis and HTML report generation focused on vessel types and trade patterns
"""

import sys
from pathlib import Path
from datetime import datetime

# Import analysis and visualization modules
from market_analysis_html import run_all_analysis
from html_visualizations import create_all_visualizations
from generate_html_report import create_html_report


def main():
    """Main orchestrator function."""
    print("\n" + "="*70)
    print(" "*10 + "USACE PORT CLEARANCE MARKET STUDY - HTML VERSION")
    print(" "*15 + "Vessel Type & Trade Pattern Analysis")
    print("="*70 + "\n")

    # Define file paths
    base_dir = Path(r"G:\My Drive\LLM\task_usace_entrance_clearance")
    data_file = base_dir / "00_DATA" / "00.02_PROCESSED" / "usace_clearances_with_grain_v4.1.1_20260206_014715.csv"

    # Create output directory
    output_dir = base_dir / "00_DATA" / "00.03_REPORTS"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"usace_market_study_2023_{timestamp}.html"

    print(f"Data file: {data_file}")
    print(f"Output directory: {output_dir}")
    print(f"Output file: {output_file.name}\n")

    # Verify data file exists
    if not data_file.exists():
        print(f"ERROR: Data file not found at {data_file}")
        print("Please verify the file path and try again.")
        sys.exit(1)

    try:
        # Phase 1: Data Analysis (focused on vessel types and trade patterns)
        print("PHASE 1: Data Analysis - Vessel Types & Trade Patterns")
        print("-" * 70)
        results = run_all_analysis(str(data_file))

        # Phase 2: Create Interactive HTML Visualizations
        print("\nPHASE 2: Create Interactive HTML Visualizations")
        print("-" * 70)
        figures = create_all_visualizations(results)

        # Phase 3: Generate HTML Report
        print("\nPHASE 3: Generate HTML Report")
        print("-" * 70)
        final_report = create_html_report(results, figures, str(output_file))

        # Success message
        print("\n" + "="*70)
        print(" "*20 + "REPORT GENERATION COMPLETE")
        print("="*70)
        print(f"\nHTML Report saved to: {final_report}")
        print(f"\nOpen in browser to view interactive charts")
        print(f"\nSummary:")
        print(f"  - Total Revenue: ${results['market']['total_revenue']/1e6:.1f}M")
        print(f"  - Total Clearances: {results['market']['total_clearances']:,}")
        print(f"  - Vessel Types: {results['vessel_types']['total_types']}")
        print(f"  - Port Regions: {results['regional_trade']['region_stats_df'].shape[0]}")
        print(f"  - Cargo Classes: {results['vessel_types']['cargo_revenue_df'].shape[0]}")
        print(f"  - Grain Shipments: {results['grain']['grain_clearances']:,}")
        print("\n" + "="*70 + "\n")

        # Open in browser
        try:
            import webbrowser
            webbrowser.open(f'file:///{final_report}')
            print("Opening report in default browser...")
        except Exception as e:
            print(f"Note: Could not auto-open browser: {e}")
            print(f"Please manually open: {final_report}")

        return final_report

    except Exception as e:
        print("\n" + "="*70)
        print(" "*25 + "ERROR OCCURRED")
        print("="*70)
        print(f"\nError: {str(e)}")
        print("\nPlease check the error message above and try again.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
