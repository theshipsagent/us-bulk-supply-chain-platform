"""
Match FGIS Grain Data to USACE Clearances v1.0.0

Adds grain export information to USACE clearance records.

Match criteria: Vessel + Port + Date (±1 day tolerance)

Adds columns:
- Grain: Y/N (grain data found)
- Grain_Countries: Destination countries
- Grain_Tons: Metric tons
- Grain_Grades: Grain grades

Author: WSD3 / Claude Code
Date: 2026-02-06
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from usace_to_fgis_port_mapping import map_usace_to_fgis_port

def normalize_vessel_name(name):
    """Normalize vessel name for matching"""
    if pd.isna(name) or not name:
        return ''
    return str(name).strip().upper()

def normalize_port_name_fgis(port):
    """Normalize FGIS port name for matching"""
    if pd.isna(port) or not port:
        return ''
    return str(port).strip().upper()

def match_grain_to_clearances(clearance_file, grain_file, output_dir):
    """Match FGIS grain data to USACE clearances"""

    print("=" * 80)
    print("USACE-FGIS Grain Matching v1.0.0")
    print("=" * 80)
    print()

    # Read USACE clearance data
    print(f"Reading USACE clearances: {clearance_file.name}")
    df_usace = pd.read_csv(clearance_file, dtype=str)
    print(f"  Loaded {len(df_usace):,} clearance records")
    print()

    # Read FGIS grain voyages
    print(f"Reading FGIS grain voyages: {grain_file.name}")
    df_grain = pd.read_csv(grain_file, dtype=str)
    print(f"  Loaded {len(df_grain):,} grain voyage records")
    print()

    # Parse dates
    print("Parsing dates...")
    df_usace['Clearance_Date_dt'] = pd.to_datetime(df_usace['Clearance_Date'], errors='coerce')
    df_grain['Cert_Date_dt'] = pd.to_datetime(df_grain['Cert_Date'], errors='coerce')
    print()

    # Normalize vessel names and map regions
    print("Normalizing vessel names and mapping regions...")
    df_usace['Vessel_Match'] = df_usace['Vessel'].apply(normalize_vessel_name)

    # Map USACE region to FGIS grain region
    # FGIS grain regions: MISSISSIPPI R., N. TEXAS, S. TEXAS, COLUMBIA R., PUGET SOUND, S. ATLANTIC, EAST GULF, LAKES
    def map_usace_region_to_fgis(port_region, port_coast):
        """Map USACE region to FGIS grain export region"""
        region_str = str(port_region).upper() if port_region else ''
        coast_str = str(port_coast).upper() if port_coast else ''

        # Gulf Coast regions
        if 'TEXAS' in region_str:
            if 'NORTH TEXAS' in region_str:
                return 'N. TEXAS'
            elif 'SOUTH TEXAS' in region_str:
                return 'S. TEXAS'
            return 'N. TEXAS'  # Default Texas to North

        # Louisiana/Mississippi River
        if 'GULF EAST' in region_str or 'LOUISIANA' in region_str:
            return 'MISSISSIPPI R.'

        # East Gulf (Alabama, Florida panhandle)
        if 'ALABAMA' in region_str or 'MOBILE' in region_str:
            return 'EAST GULF'

        # Pacific Northwest
        if 'PACIFIC NORTHWEST' in region_str or 'WASHINGTON' in region_str or 'OREGON' in region_str:
            return 'COLUMBIA R.'  # Most PNW grain goes through Columbia River

        # California
        if 'CALIFORNIA' in region_str:
            return 'CALIFORNIA'

        # Atlantic regions
        if 'SOUTH ATLANTIC' in region_str or 'MID-ATLANTIC' in region_str or 'VIRGINIA' in region_str:
            return 'S. ATLANTIC'
        if 'NORTH ATLANTIC' in region_str:
            return 'N. ATLANTIC'

        # Great Lakes
        if 'GREAT LAKES' in region_str or 'LAKES' in coast_str:
            return 'LAKES'

        return None

    df_usace['Region_Match'] = df_usace.apply(
        lambda row: map_usace_region_to_fgis(row.get('Port_Region'), row.get('Port_Coast')), axis=1
    )

    df_grain['Vessel_Match'] = df_grain['Vessel_Norm']  # Already normalized
    df_grain['Region_Match'] = df_grain['Port_Norm']  # FGIS port is actually a region
    print()

    # Initialize grain columns
    df_usace['Grain'] = 'N'
    df_usace['Grain_Countries'] = ''
    df_usace['Grain_Tons'] = ''
    df_usace['Grain_Grades'] = ''
    df_usace['Grain_Cert_Date'] = ''

    # Matching process
    print("=" * 80)
    print("MATCHING CLEARANCES TO GRAIN DATA")
    print("=" * 80)
    print()
    print("Match criteria: Vessel + Region + Date (±1 day)")
    print()

    matched_count = 0
    multiple_matches = 0
    no_region_match = 0

    for idx, usace_row in df_usace.iterrows():
        vessel = usace_row['Vessel_Match']
        region = usace_row['Region_Match']
        clearance_date = usace_row['Clearance_Date_dt']

        if pd.isna(clearance_date) or not vessel:
            continue

        if not region:
            no_region_match += 1
            continue

        # Find grain records matching vessel + region
        grain_matches = df_grain[
            (df_grain['Vessel_Match'] == vessel) &
            (df_grain['Region_Match'] == region)
        ].copy()

        if len(grain_matches) == 0:
            continue

        # Check date tolerance (±1 day)
        grain_matches['Date_Diff'] = abs((grain_matches['Cert_Date_dt'] - clearance_date).dt.days)
        grain_matches = grain_matches[grain_matches['Date_Diff'] <= 1]

        if len(grain_matches) == 0:
            continue

        # If multiple matches, take the closest date
        if len(grain_matches) > 1:
            multiple_matches += 1
            grain_matches = grain_matches.nsmallest(1, 'Date_Diff')

        # Get the matched grain record
        grain_row = grain_matches.iloc[0]

        # Update USACE record with grain data
        df_usace.at[idx, 'Grain'] = 'Y'
        df_usace.at[idx, 'Grain_Countries'] = grain_row['Grain_Countries']
        df_usace.at[idx, 'Grain_Tons'] = grain_row['Grain_Tons']
        df_usace.at[idx, 'Grain_Grades'] = grain_row['Grain_Grades']
        df_usace.at[idx, 'Grain_Cert_Date'] = grain_row['Cert_Date']

        matched_count += 1

    # Summary statistics
    print("=" * 80)
    print("MATCHING SUMMARY")
    print("=" * 80)
    print()

    print(f"USACE clearance records: {len(df_usace):,}")
    print(f"  With grain data: {matched_count:,} ({matched_count/len(df_usace)*100:.1f}%)")
    print(f"  No grain data: {len(df_usace) - matched_count:,} ({(len(df_usace) - matched_count)/len(df_usace)*100:.1f}%)")
    print()

    if no_region_match > 0:
        print(f"No region mapping (non-grain ports): {no_region_match:,}")
        print()

    if multiple_matches > 0:
        print(f"Multiple matches (used closest date): {multiple_matches:,}")
        print()

    # Grain tonnage statistics
    df_with_grain = df_usace[df_usace['Grain'] == 'Y'].copy()
    if len(df_with_grain) > 0:
        total_grain_tons = pd.to_numeric(df_with_grain['Grain_Tons'], errors='coerce').sum()
        print(f"Total grain tons matched: {total_grain_tons:,.0f} MT")
        print()

        # Top destination countries
        print("Top 10 grain destination countries:")
        all_countries = []
        for countries_str in df_with_grain['Grain_Countries']:
            if countries_str:
                all_countries.extend([c.strip() for c in str(countries_str).split(',')])

        from collections import Counter
        country_counts = Counter(all_countries)
        for country, count in country_counts.most_common(10):
            print(f"  {country:20s}: {count:4d} shipments")
        print()

    # Save output
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_version = "v4.1.0"

    output_file = output_dir / f"usace_clearances_with_grain_{base_version}_{timestamp}.csv"

    print(f"Saving to: {output_file.name}")
    df_usace.to_csv(output_file, index=False)
    print(f"  Saved {len(df_usace):,} records")
    print()

    print("=" * 80)
    print()

    return df_usace, output_file

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "00_DATA" / "00.02_PROCESSED"

    print("\n\n")
    print("#" * 80)
    print("# MATCH GRAIN DATA TO USACE CLEARANCES")
    print("#" * 80)
    print("\n")

    # Find most recent files
    clearance_files = sorted(data_dir.glob("*port_calls_COMPLETE_*.csv"), reverse=True)
    grain_files = sorted(data_dir.glob("fgis_grain_voyages_*.csv"), reverse=True)

    if not clearance_files:
        print("ERROR: No USACE clearance files found")
        print("Please run merge_port_calls.py first")
        return

    if not grain_files:
        print("ERROR: No FGIS grain voyage files found")
        print("Please run aggregate_fgis_grain_data.py first")
        return

    clearance_file = clearance_files[0]
    grain_file = grain_files[0]

    print(f"Input files:")
    print(f"  USACE: {clearance_file.name}")
    print(f"  FGIS:  {grain_file.name}")
    print()

    # Match
    df_result, output_file = match_grain_to_clearances(clearance_file, grain_file, data_dir)

    print("=" * 80)
    print("GRAIN MATCHING COMPLETE")
    print("=" * 80)
    print()
    print(f"Output: {output_file}")
    print()

if __name__ == "__main__":
    main()
