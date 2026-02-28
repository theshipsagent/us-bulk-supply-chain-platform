"""
Aggregate FGIS Grain Export Data to Voyage Level v1.0.0

Rolls up multiple inspection records per vessel into single voyage records.

Aggregation:
- Group by: Vessel + Port + Date (±1 day tolerance)
- Countries: Comma-separated unique destinations
- Grades: Comma-separated unique grades
- Metric Tons: SUM total

Author: WSD3 / Claude Code
Date: 2026-02-06
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def parse_cert_date(cert_date_str):
    """Parse FGIS Cert Date from YYYYMMDD to datetime"""
    try:
        s = str(cert_date_str).strip()
        if len(s) == 8:
            return datetime.strptime(s, '%Y%m%d')
        return None
    except:
        return None

def aggregate_fgis_voyages(fgis_file, output_dir):
    """Aggregate FGIS grain export records to voyage level"""

    print("=" * 80)
    print("FGIS Grain Export Aggregation v1.0.0")
    print("=" * 80)
    print()

    # Read FGIS data
    print(f"Reading FGIS data: {fgis_file.name}")
    df = pd.read_csv(fgis_file, dtype=str)
    print(f"  Total records: {len(df):,}")
    print()

    # Filter to Type Carrier = 1 (ocean vessels only)
    print("Filtering to ocean vessels (Type Carrier = 1)...")
    df_vessels = df[df['Type Carrier'] == '1'].copy()
    print(f"  Ocean vessel records: {len(df_vessels):,}")
    print()

    # Select only needed columns
    keep_columns = ['Cert Date', 'Carrier Name', 'Field Office', 'Port',
                    'Grade', 'Destination', 'Metric Ton']
    df_vessels = df_vessels[keep_columns].copy()

    # Parse dates
    print("Parsing certification dates...")
    df_vessels['Cert_Date_Parsed'] = df_vessels['Cert Date'].apply(parse_cert_date)
    df_vessels = df_vessels[df_vessels['Cert_Date_Parsed'].notna()].copy()
    print(f"  Valid dates: {len(df_vessels):,}")
    print()

    # Convert metric tons to numeric
    df_vessels['Metric_Ton_Num'] = pd.to_numeric(df_vessels['Metric Ton'], errors='coerce').fillna(0)

    # Normalize vessel names and ports for matching
    df_vessels['Vessel_Norm'] = df_vessels['Carrier Name'].str.strip().str.upper()
    df_vessels['Port_Norm'] = df_vessels['Port'].str.strip().str.upper()

    # Aggregate to voyage level
    print("Aggregating to voyage level...")
    print("  Grouping by: Vessel + Port + Date")
    print()

    aggregated = []

    # Group by vessel + port + date
    grouped = df_vessels.groupby(['Vessel_Norm', 'Port_Norm', 'Cert_Date_Parsed'])

    for (vessel, port, cert_date), group in grouped:
        # Get original (non-normalized) values
        vessel_name = group['Carrier Name'].iloc[0]
        port_name = group['Port'].iloc[0]
        field_office = group['Field Office'].iloc[0]

        # Aggregate destinations (unique, comma-separated)
        destinations = group['Destination'].dropna().unique()
        destinations = [d.strip() for d in destinations if d and str(d).strip()]
        dest_str = ', '.join(sorted(set(destinations)))

        # Aggregate grades (unique, comma-separated)
        grades = group['Grade'].dropna().unique()
        grades = [g.strip() for g in grades if g and str(g).strip()]
        grade_str = ', '.join(sorted(set(grades)))

        # Sum metric tons
        total_tons = group['Metric_Ton_Num'].sum()

        # Count inspection records
        inspection_count = len(group)

        aggregated.append({
            'Cert_Date': cert_date.strftime('%Y-%m-%d'),
            'Vessel': vessel_name,
            'Port': port_name,
            'Field_Office': field_office,
            'Grain_Countries': dest_str,
            'Grain_Grades': grade_str,
            'Grain_Tons': round(total_tons, 2),
            'Inspection_Count': inspection_count,
            'Vessel_Norm': vessel,
            'Port_Norm': port
        })

    df_voyages = pd.DataFrame(aggregated)

    # Summary statistics
    print("=" * 80)
    print("AGGREGATION SUMMARY")
    print("=" * 80)
    print()

    print(f"Input inspection records: {len(df_vessels):,}")
    print(f"Output voyage records: {len(df_voyages):,}")
    print(f"Reduction ratio: {len(df_vessels)/len(df_voyages):.1f}:1")
    print()

    print("Inspection records per voyage:")
    print(f"  Average: {df_voyages['Inspection_Count'].mean():.1f}")
    print(f"  Median: {df_voyages['Inspection_Count'].median():.0f}")
    print(f"  Max: {df_voyages['Inspection_Count'].max():.0f}")
    print()

    print(f"Unique vessels: {df_voyages['Vessel'].nunique():,}")
    print(f"Unique ports: {df_voyages['Port'].nunique():,}")
    print(f"Total grain tons: {df_voyages['Grain_Tons'].sum():,.0f} MT")
    print()

    # Top vessels by voyage count
    print("Top 10 vessels by voyage count:")
    top_vessels = df_voyages['Vessel'].value_counts().head(10)
    for vessel, count in top_vessels.items():
        print(f"  {vessel[:40]:40s}: {count:3d} voyages")
    print()

    # Save output
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"fgis_grain_voyages_2023_{timestamp}.csv"

    print(f"Saving to: {output_file.name}")
    df_voyages.to_csv(output_file, index=False)
    print(f"  Saved {len(df_voyages):,} voyage records")
    print()

    print("=" * 80)
    print()

    return df_voyages, output_file

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent

    # Input file path
    fgis_file = Path(r"G:\My Drive\Downloads\CY2023 (2).csv")
    output_dir = project_root / "00_DATA" / "00.02_PROCESSED"

    if not fgis_file.exists():
        print(f"ERROR: FGIS file not found: {fgis_file}")
        return

    print("\n\n")
    print("#" * 80)
    print("# FGIS GRAIN EXPORT AGGREGATION")
    print("#" * 80)
    print("\n")

    df_voyages, output_file = aggregate_fgis_voyages(fgis_file, output_dir)

    print("=" * 80)
    print("FGIS AGGREGATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Output: {output_file}")
    print()

if __name__ == "__main__":
    main()
