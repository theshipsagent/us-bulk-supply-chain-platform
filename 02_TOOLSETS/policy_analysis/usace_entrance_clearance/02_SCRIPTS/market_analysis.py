"""
USACE Market Study - Data Analysis Module
Analyzes port clearance data for market study report
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any


def load_and_prepare_data(data_file: str) -> pd.DataFrame:
    """Load CSV and prepare data for analysis."""
    print(f"Loading data from {data_file}...")

    df = pd.read_csv(data_file)
    print(f"Loaded {len(df):,} records")

    # Convert fees to numeric
    df['Fee_Adj'] = pd.to_numeric(df['Fee_Adj'], errors='coerce')

    # Fill nulls in key fields
    df['Ships_Type'] = df['Ships_Type'].fillna('Unknown')
    df['ICST_DESC'] = df['ICST_DESC'].fillna('Unknown')
    df['Port_Region'] = df['Port_Region'].fillna('Unknown')
    df['Grain'] = df['Grain'].fillna('N')

    # Create vessel identifier
    df['Vessel_ID'] = df['Vessel'].fillna('Unknown')

    print(f"Revenue sum: ${df['Fee_Adj'].sum():,.0f}")
    print(f"Unique vessels: {df['Vessel_ID'].nunique():,}")
    print(f"Vessel types: {df['Ships_Type'].nunique():,}")
    print(f"Regions: {df['Port_Region'].nunique():,}")

    return df


def calculate_market_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate overall market metrics."""
    print("Calculating market metrics...")

    total_revenue = df['Fee_Adj'].sum()
    total_clearances = len(df)
    avg_fee = df['Fee_Adj'].mean()
    unique_vessels = df['Vessel_ID'].nunique()

    # Top vessels by revenue
    vessel_revenue = df.groupby('Vessel_ID').agg({
        'Fee_Adj': 'sum',
        'Vessel_ID': 'count'
    }).rename(columns={'Vessel_ID': 'Clearances'})
    vessel_revenue = vessel_revenue.sort_values('Fee_Adj', ascending=False)

    # Market concentration
    top_10_revenue = vessel_revenue.head(10)['Fee_Adj'].sum()
    top_25_revenue = vessel_revenue.head(25)['Fee_Adj'].sum()
    top_50_revenue = vessel_revenue.head(50)['Fee_Adj'].sum()

    # Calculate HHI (Herfindahl-Hirschman Index)
    vessel_revenue['market_share'] = vessel_revenue['Fee_Adj'] / total_revenue
    hhi = (vessel_revenue['market_share'] ** 2).sum() * 10000

    # Multi-visit vessels
    multi_visit = (vessel_revenue['Clearances'] > 1).sum()
    single_visit = (vessel_revenue['Clearances'] == 1).sum()

    results = {
        'total_revenue': total_revenue,
        'total_clearances': total_clearances,
        'avg_fee': avg_fee,
        'unique_vessels': unique_vessels,
        'top_10_pct': (top_10_revenue / total_revenue) * 100,
        'top_25_pct': (top_25_revenue / total_revenue) * 100,
        'top_50_pct': (top_50_revenue / total_revenue) * 100,
        'hhi': hhi,
        'multi_visit_vessels': multi_visit,
        'single_visit_vessels': single_visit,
        'vessel_revenue_df': vessel_revenue.reset_index(),
        'top_50_vessels': vessel_revenue.head(50).reset_index()
    }

    print(f"  Total Revenue: ${total_revenue:,.0f}")
    print(f"  Total Clearances: {total_clearances:,}")
    print(f"  Average Fee: ${avg_fee:,.0f}")
    print(f"  Top 10 vessels: {results['top_10_pct']:.1f}%")
    print(f"  Top 50 vessels: {results['top_50_pct']:.1f}%")
    print(f"  HHI: {hhi:.0f}")

    return results


def analyze_vessel_types(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze revenue by vessel type."""
    print("Analyzing vessel types...")

    # Revenue by Ships_Type
    type_revenue = df.groupby('Ships_Type').agg({
        'Fee_Adj': ['sum', 'mean', 'count', 'std', 'min', 'max']
    })
    type_revenue.columns = ['Total_Revenue', 'Avg_Fee', 'Count', 'Std_Dev', 'Min_Fee', 'Max_Fee']
    type_revenue['Revenue_Pct'] = (type_revenue['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    type_revenue = type_revenue.sort_values('Total_Revenue', ascending=False)

    # Revenue by ICST_DESC (cargo class)
    cargo_revenue = df.groupby('ICST_DESC').agg({
        'Fee_Adj': ['sum', 'mean', 'count']
    })
    cargo_revenue.columns = ['Total_Revenue', 'Avg_Fee', 'Count']
    cargo_revenue['Revenue_Pct'] = (cargo_revenue['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    cargo_revenue = cargo_revenue.sort_values('Total_Revenue', ascending=False)

    # Revenue disparity metrics
    disparity = {
        'highest_type': type_revenue.index[0],
        'highest_revenue': type_revenue.iloc[0]['Total_Revenue'],
        'lowest_type': type_revenue.index[-1],
        'lowest_revenue': type_revenue.iloc[-1]['Total_Revenue'],
        'revenue_ratio': type_revenue.iloc[0]['Total_Revenue'] / type_revenue.iloc[-1]['Total_Revenue'],
        'avg_fee_highest': type_revenue.iloc[0]['Avg_Fee'],
        'avg_fee_lowest': type_revenue.iloc[-1]['Avg_Fee']
    }

    results = {
        'type_revenue_df': type_revenue.reset_index(),
        'cargo_revenue_df': cargo_revenue.reset_index(),
        'disparity': disparity,
        'total_types': len(type_revenue),
        'total_cargo_classes': len(cargo_revenue)
    }

    print(f"  Total vessel types: {results['total_types']}")
    print(f"  Highest revenue type: {disparity['highest_type']} (${disparity['highest_revenue']:,.0f})")
    print(f"  Revenue disparity ratio: {disparity['revenue_ratio']:.1f}x")

    return results


def analyze_regions(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze revenue by region."""
    print("Analyzing regions...")

    # Revenue by region
    region_revenue = df.groupby('Port_Region').agg({
        'Fee_Adj': ['sum', 'mean', 'count']
    })
    region_revenue.columns = ['Total_Revenue', 'Avg_Fee', 'Clearances']
    region_revenue['Revenue_Pct'] = (region_revenue['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    region_revenue = region_revenue.sort_values('Total_Revenue', ascending=False)

    # Dominant vessel types by region
    region_type_revenue = df.groupby(['Port_Region', 'Ships_Type'])['Fee_Adj'].sum().reset_index()
    dominant_types = region_type_revenue.loc[
        region_type_revenue.groupby('Port_Region')['Fee_Adj'].idxmax()
    ][['Port_Region', 'Ships_Type', 'Fee_Adj']]
    dominant_types.columns = ['Region', 'Dominant_Type', 'Type_Revenue']

    # Region-Type matrix for heatmap
    region_type_matrix = df.pivot_table(
        index='Port_Region',
        columns='Ships_Type',
        values='Fee_Adj',
        aggfunc='sum',
        fill_value=0
    )

    results = {
        'region_revenue_df': region_revenue.reset_index(),
        'dominant_types_df': dominant_types,
        'region_type_matrix': region_type_matrix,
        'total_regions': len(region_revenue)
    }

    print(f"  Total regions: {results['total_regions']}")
    print(f"  Top region: {region_revenue.index[0]} (${region_revenue.iloc[0]['Total_Revenue']:,.0f})")

    return results


def analyze_revenue_per_ship(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze average revenue per ship."""
    print("Analyzing revenue per ship...")

    # Revenue per vessel
    vessel_stats = df.groupby('Vessel_ID').agg({
        'Fee_Adj': 'sum',
        'Vessel_ID': 'count'
    }).rename(columns={'Vessel_ID': 'Visits', 'Fee_Adj': 'Total_Revenue'})

    vessel_stats['Avg_Revenue_Per_Visit'] = vessel_stats['Total_Revenue'] / vessel_stats['Visits']

    # Overall average
    total_vessels = len(vessel_stats)
    total_revenue = vessel_stats['Total_Revenue'].sum()
    avg_revenue_per_ship = total_revenue / total_vessels

    # Percentiles
    percentiles = vessel_stats['Total_Revenue'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict()

    # Revenue per ship by vessel type
    vessel_type_map = df[['Vessel_ID', 'Ships_Type']].drop_duplicates().set_index('Vessel_ID')
    vessel_stats_with_type = vessel_stats.join(vessel_type_map)

    type_ship_revenue = vessel_stats_with_type.groupby('Ships_Type')['Total_Revenue'].agg([
        'mean', 'median', 'count', 'sum'
    ]).sort_values('mean', ascending=False)

    results = {
        'vessel_stats_df': vessel_stats.reset_index().sort_values('Total_Revenue', ascending=False),
        'avg_revenue_per_ship': avg_revenue_per_ship,
        'percentiles': percentiles,
        'type_ship_revenue_df': type_ship_revenue.reset_index(),
        'total_vessels': total_vessels
    }

    print(f"  Average revenue per ship: ${avg_revenue_per_ship:,.0f}")
    print(f"  Median revenue per ship: ${percentiles[0.5]:,.0f}")

    return results


def analyze_grain_shipments(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze grain shipment subset."""
    print("Analyzing grain shipments...")

    grain_df = df[df['Grain'] == 'Y'].copy()

    if len(grain_df) == 0:
        print("  No grain shipments found")
        return {
            'grain_clearances': 0,
            'grain_revenue': 0,
            'grain_tonnage': 0
        }

    grain_clearances = len(grain_df)
    grain_revenue = grain_df['Fee_Adj'].sum()
    grain_tonnage = grain_df['Grain_Tons'].sum() if 'Grain_Tons' in grain_df.columns else 0

    # Top destinations
    if 'Destination_Country' in grain_df.columns:
        destinations = grain_df.groupby('Destination_Country').agg({
            'Fee_Adj': 'count',
            'Grain_Tons': 'sum' if 'Grain_Tons' in grain_df.columns else 'count'
        }).sort_values('Fee_Adj', ascending=False)
        destinations.columns = ['Shipments', 'Tonnage']
    else:
        destinations = pd.DataFrame()

    # Grain vessel types
    grain_types = grain_df.groupby('Ships_Type').agg({
        'Fee_Adj': ['count', 'sum']
    })
    grain_types.columns = ['Count', 'Revenue']
    grain_types = grain_types.sort_values('Count', ascending=False)

    # Top grain vessels
    grain_vessels = grain_df.groupby('Vessel_ID').agg({
        'Fee_Adj': 'count',
        'Grain_Tons': 'sum' if 'Grain_Tons' in grain_df.columns else 'count'
    }).sort_values('Fee_Adj', ascending=False).head(20)
    grain_vessels.columns = ['Shipments', 'Tonnage']

    results = {
        'grain_clearances': grain_clearances,
        'grain_revenue': grain_revenue,
        'grain_tonnage': grain_tonnage,
        'grain_pct': (grain_clearances / len(df)) * 100,
        'destinations_df': destinations.reset_index() if len(destinations) > 0 else pd.DataFrame(),
        'grain_types_df': grain_types.reset_index(),
        'grain_vessels_df': grain_vessels.reset_index()
    }

    print(f"  Grain clearances: {grain_clearances:,} ({results['grain_pct']:.1f}%)")
    print(f"  Grain revenue: ${grain_revenue:,.0f}")
    print(f"  Grain tonnage: {grain_tonnage:,.0f} MT")

    return results


def run_all_analysis(data_file: str) -> Dict[str, Any]:
    """Run all analysis modules and return results."""
    print("\n" + "="*60)
    print("USACE Market Study - Data Analysis")
    print("="*60 + "\n")

    # Load data
    df = load_and_prepare_data(data_file)

    # Run all analyses
    results = {
        'market': calculate_market_metrics(df),
        'vessel_types': analyze_vessel_types(df),
        'regions': analyze_regions(df),
        'per_ship': analyze_revenue_per_ship(df),
        'grain': analyze_grain_shipments(df),
        'df': df  # Include full dataframe for visualizations
    }

    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60 + "\n")

    return results


if __name__ == '__main__':
    # Test the analysis
    data_file = r"G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.02_PROCESSED\usace_clearances_with_grain_v4.1.1_20260206_014715.csv"
    results = run_all_analysis(data_file)
    print("\nAnalysis results keys:", list(results.keys()))
