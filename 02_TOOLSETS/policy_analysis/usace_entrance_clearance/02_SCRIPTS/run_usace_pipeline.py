"""
USACE Entrance/Clearance Processing Pipeline Orchestrator v1.0.0

Master script to run the complete USACE data processing pipeline:
1. Split Excel file into CSV worksheets (if needed)
2. Transform entrance (inbound/imports) data
3. Transform clearance (outbound/exports) data

Isolated USACE Project
Author: WSD3 / Claude Code
Date: 2026-02-05
Version: 1.0.0
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(message):
    """Print formatted section header"""
    print("\n")
    print("=" * 80)
    print(f"  {message}")
    print("=" * 80)
    print()

def print_step(step_num, message):
    """Print formatted step message"""
    print(f"\n{'─' * 80}")
    print(f"STEP {step_num}: {message}")
    print(f"{'─' * 80}\n")

def run_script(script_path, script_name):
    """Run a Python script and capture output"""
    print(f"Running: {script_name}")
    print()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        print()
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"✗ {script_name} failed with error code {e.returncode}")
        return False
    except Exception as e:
        print()
        print(f"✗ {script_name} failed with error: {str(e)}")
        return False

def main():
    """Main pipeline orchestration"""

    # Get project paths
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "02_SCRIPTS"
    raw_data_dir = project_root / "00_DATA" / "00.01_RAW"
    processed_dir = project_root / "00_DATA" / "00.02_PROCESSED"
    logs_dir = project_root / "logs"

    # Ensure output directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Start time
    start_time = datetime.now()

    print_header("USACE ENTRANCE/CLEARANCE PROCESSING PIPELINE v1.0.0")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {project_root}")
    print()

    # Track results
    results = {
        'split_excel': None,
        'entrance': None,
        'clearance': None
    }

    # ================================================================
    # STEP 1: Split Excel to CSV (if needed)
    # ================================================================
    print_step(1, "Split Excel to CSV Worksheets")

    excel_file = raw_data_dir / "Entrances_Clearances_2023.xlsx"
    inbound_csv = raw_data_dir / "Entrances_Clearances_2023_2023_Inbound.csv"
    outbound_csv = raw_data_dir / "Entrances_Clearances_2023_2023_Outbound.csv"

    if inbound_csv.exists() and outbound_csv.exists():
        print("✓ CSV files already exist - skipping Excel split")
        results['split_excel'] = True
    elif excel_file.exists():
        script_path = scripts_dir / "split_excel_to_csv.py"
        results['split_excel'] = run_script(script_path, "split_excel_to_csv.py")
    else:
        print(f"✗ Excel file not found: {excel_file}")
        print("  Please place the Excel file in 00_DATA/00.01_RAW/")
        results['split_excel'] = False

    if not results['split_excel']:
        print("\nPipeline aborted - Excel split failed or files missing")
        return False

    # ================================================================
    # STEP 2: Transform Entrance (Inbound/Imports) Data
    # ================================================================
    print_step(2, "Transform Entrance (Inbound/Imports) Data")

    if not inbound_csv.exists():
        print(f"✗ Inbound CSV not found: {inbound_csv}")
        results['entrance'] = False
    else:
        script_path = scripts_dir / "transform_usace_entrance_data.py"
        results['entrance'] = run_script(script_path, "transform_usace_entrance_data.py")

    # ================================================================
    # STEP 3: Transform Clearance (Outbound/Exports) Data
    # ================================================================
    print_step(3, "Transform Clearance (Outbound/Exports) Data")

    if not outbound_csv.exists():
        print(f"✗ Outbound CSV not found: {outbound_csv}")
        results['clearance'] = False
    else:
        script_path = scripts_dir / "transform_usace_clearance_data.py"
        results['clearance'] = run_script(script_path, "transform_usace_clearance_data.py")

    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    end_time = datetime.now()
    duration = end_time - start_time

    print_header("PIPELINE EXECUTION SUMMARY")

    print("Results:")
    print(f"  Step 1 - Split Excel:      {'✓ Success' if results['split_excel'] else '✗ Failed'}")
    print(f"  Step 2 - Entrance Data:    {'✓ Success' if results['entrance'] else '✗ Failed'}")
    print(f"  Step 3 - Clearance Data:   {'✓ Success' if results['clearance'] else '✗ Failed'}")
    print()

    print("Timing:")
    print(f"  Start:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  End:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {duration}")
    print()

    print("Output Files:")
    entrance_output = processed_dir / "usace_2023_inbound_entrance_transformed_v3.0.0.csv"
    clearance_output = processed_dir / "usace_2023_outbound_clearance_transformed_v3.0.0.csv"

    if entrance_output.exists():
        print(f"  ✓ Entrance:  {entrance_output}")
    else:
        print(f"  ✗ Entrance:  Not created")

    if clearance_output.exists():
        print(f"  ✓ Clearance: {clearance_output}")
    else:
        print(f"  ✗ Clearance: Not created")

    print()

    # Overall status
    all_success = all(results.values())

    if all_success:
        print("=" * 80)
        print("  ✓ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        return True
    else:
        print("=" * 80)
        print("  ✗ PIPELINE COMPLETED WITH ERRORS")
        print("=" * 80)
        print()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
