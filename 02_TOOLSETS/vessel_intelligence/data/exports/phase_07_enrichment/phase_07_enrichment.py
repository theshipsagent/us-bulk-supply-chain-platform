"""
Phase 07: Vessel & Port Enrichment
====================================
Final enrichment after cargo classification complete.

Simple exact matching:
- Vessel: Match IMO -> return ship data
- Port: Match port code -> return consolidation data

Input:  phase_06_output.csv (from phase_06_final_catchall/)
Output: phase_07_output.csv  <- FINAL PIPELINE OUTPUT

Author: WSD3 / Claude Code
Date: 2026-02-08
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

SHIPS_REGISTER = PROJECT_ROOT / "DICTIONARIES" / "ships_register.csv"
PORT_MASTER = PROJECT_ROOT / "DICTIONARIES" / "ports_master.csv"
INPUT_FILE = PIPELINE_DIR / "phase_06_final_catchall" / "phase_06_output.csv"
OUTPUT_FILE = SCRIPT_DIR / "phase_07_output.csv"

def stamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def enrich_vessels_and_ports():
    """Enrich with vessel and port data via exact matching"""

    stamp("="*80)
    stamp("PHASE 07: VESSEL & PORT ENRICHMENT")
    stamp("="*80)
    start = datetime.now()

    # Load data
    stamp("\n1. Loading classified data...")
    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    stamp(f"   Total records: {len(df):,}")
    stamp(f"   Columns: {len(df.columns)}")

    # Load dictionaries
    stamp("\n2. Loading dictionaries...")

    stamp("   Loading ships register...")
    ships = pd.read_csv(SHIPS_REGISTER, dtype=str)
    stamp(f"   Ships in register: {len(ships):,}")

    stamp("   Loading port dictionary...")
    ports = pd.read_csv(PORT_MASTER, dtype=str)
    stamp(f"   Ports in dictionary: {len(ports):,}")

    # Vessel enrichment
    stamp("\n3. Enriching vessel data (IMO exact match)...")

    vessel_cols = ['IMO', 'Type', 'DWT', 'LOA', 'Beam', 'Depth(m)', 'GT', 'NRT', 'Grain', 'TPC', 'Dwt_Draft(m)']
    ships_subset = ships[vessel_cols].copy()

    vessels_before = df['Type'].notna().sum() if 'Type' in df.columns else 0

    df = df.merge(ships_subset, on='IMO', how='left', suffixes=('_old', ''))

    old_cols = [c for c in df.columns if c.endswith('_old')]
    if old_cols:
        df = df.drop(columns=old_cols)

    vessels_after = df['Type'].notna().sum()
    vessels_matched = vessels_after - vessels_before
    match_rate = (vessels_matched / len(df) * 100) if len(df) > 0 else 0

    stamp(f"   Vessels matched: {vessels_matched:,} ({match_rate:.1f}%)")

    # Port enrichment
    stamp("\n4. Enriching port data (exact match on port name)...")

    port_col = 'Port of Discharge (D)'

    if port_col in df.columns:
        stamp(f"   Using port column: {port_col}")

        ports_before = df['Port_Consolidated'].notna().sum() if 'Port_Consolidated' in df.columns else 0

        df = df.merge(ports, on=port_col, how='left', suffixes=('_old', ''))

        old_cols = [c for c in df.columns if c.endswith('_old')]
        if old_cols:
            df = df.drop(columns=old_cols)

        ports_after = df['Port_Consolidated'].notna().sum()
        ports_matched = ports_after - ports_before
        match_rate = (ports_matched / len(df) * 100) if len(df) > 0 else 0

        stamp(f"   Ports matched: {ports_matched:,} ({match_rate:.1f}%)")
    else:
        stamp("   WARNING: Port column not found")

    # Save
    stamp("\n" + "="*80)
    stamp("5. SAVING FINAL OUTPUT")
    stamp("="*80)

    df.to_csv(OUTPUT_FILE, index=False)
    stamp(f"   Saved: {OUTPUT_FILE.name}")
    stamp(f"   Records: {len(df):,}")
    stamp(f"   Columns: {len(df.columns)}")

    duration = (datetime.now() - start).total_seconds() / 60
    stamp(f"\n" + "="*80)
    stamp(f"PHASE 07 COMPLETE - Duration: {duration:.1f} minutes")
    stamp(f"FINAL PIPELINE OUTPUT: {OUTPUT_FILE}")
    stamp("="*80)

if __name__ == "__main__":
    enrich_vessels_and_ports()
