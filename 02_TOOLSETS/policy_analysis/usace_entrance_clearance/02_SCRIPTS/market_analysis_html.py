"""
USACE Market Study - Data Analysis Module (HTML Version)
Focuses on vessel types and trade patterns across port regions
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
    df['Tons'] = pd.to_numeric(df['Tons'], errors='coerce')

    # Fill nulls in key fields
    df['Ships_Type'] = df['Ships_Type'].fillna('Unknown')
    df['ICST_DESC'] = df['ICST_DESC'].fillna('Unknown')
    df['Port_Region'] = df['Port_Region'].fillna('Unknown')
    df['Port_Coast'] = df['Port_Coast'].fillna('Unknown')
    df['Grain'] = df['Grain'].fillna('N')

    # Origin/Destination
    df['Origin_Country'] = df['Origin_Country'].fillna('Unknown')
    df['Destination_Country'] = df['Destination_Country'].fillna('Unknown')

    print(f"Revenue sum: ${df['Fee_Adj'].sum():,.0f}")
    print(f"Vessel types: {df['Ships_Type'].nunique():,}")
    print(f"Regions: {df['Port_Region'].nunique():,}")
    print(f"Cargo classes: {df['ICST_DESC'].nunique():,}")

    return df


def calculate_market_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate overall market metrics."""
    print("Calculating market metrics...")

    total_revenue = df['Fee_Adj'].sum()
    total_clearances = len(df)
    avg_fee = df['Fee_Adj'].mean()
    total_tonnage = df['Tons'].sum()

    # Vessel type counts
    vessel_type_counts = df['Ships_Type'].value_counts()

    # Cargo class distribution
    cargo_class_counts = df['ICST_DESC'].value_counts()

    # Regional distribution
    region_counts = df['Port_Region'].value_counts()

    results = {
        'total_revenue': total_revenue,
        'total_clearances': total_clearances,
        'avg_fee': avg_fee,
        'total_tonnage': total_tonnage,
        'vessel_type_counts': vessel_type_counts,
        'cargo_class_counts': cargo_class_counts,
        'region_counts': region_counts,
        'total_vessel_types': df['Ships_Type'].nunique(),
        'total_cargo_classes': df['ICST_DESC'].nunique(),
        'total_regions': df['Port_Region'].nunique()
    }

    print(f"  Total Revenue: ${total_revenue:,.0f}")
    print(f"  Total Clearances: {total_clearances:,}")
    print(f"  Average Fee: ${avg_fee:,.0f}")
    print(f"  Total Tonnage: {total_tonnage:,.0f} tons")

    return results


def analyze_vessel_types(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze vessel types and their characteristics."""
    print("Analyzing vessel types...")

    # Revenue and clearances by vessel type
    type_stats = df.groupby('Ships_Type').agg({
        'Fee_Adj': ['sum', 'mean', 'count'],
        'Tons': 'sum',
        'Ships_DWT': 'mean',
        'Ships_LOA': 'mean'
    })
    type_stats.columns = ['Total_Revenue', 'Avg_Fee', 'Clearances', 'Total_Tons', 'Avg_DWT', 'Avg_LOA']
    type_stats['Revenue_Pct'] = (type_stats['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    type_stats['Clearance_Pct'] = (type_stats['Clearances'] / len(df)) * 100
    type_stats = type_stats.sort_values('Total_Revenue', ascending=False)

    # Cargo class by vessel type
    cargo_revenue = df.groupby('ICST_DESC').agg({
        'Fee_Adj': ['sum', 'count'],
        'Tons': 'sum'
    })
    cargo_revenue.columns = ['Total_Revenue', 'Clearances', 'Total_Tons']
    cargo_revenue['Revenue_Pct'] = (cargo_revenue['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    cargo_revenue = cargo_revenue.sort_values('Total_Revenue', ascending=False)

    results = {
        'type_stats_df': type_stats.reset_index(),
        'cargo_revenue_df': cargo_revenue.reset_index(),
        'total_types': len(type_stats)
    }

    print(f"  Total vessel types: {results['total_types']}")
    print(f"  Top type by revenue: {type_stats.index[0]} (${type_stats.iloc[0]['Total_Revenue']:,.0f})")

    return results


def analyze_regional_trade_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze trade patterns across port regions."""
    print("Analyzing regional trade patterns...")

    # Revenue and activity by region
    region_stats = df.groupby('Port_Region').agg({
        'Fee_Adj': ['sum', 'mean', 'count'],
        'Tons': 'sum',
        'Ships_DWT': 'mean'
    })
    region_stats.columns = ['Total_Revenue', 'Avg_Fee', 'Clearances', 'Total_Tons', 'Avg_Vessel_Size']
    region_stats['Revenue_Pct'] = (region_stats['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    region_stats['Clearance_Pct'] = (region_stats['Clearances'] / len(df)) * 100
    region_stats = region_stats.sort_values('Total_Revenue', ascending=False)

    # Coast distribution
    coast_stats = df.groupby('Port_Coast').agg({
        'Fee_Adj': ['sum', 'count'],
        'Tons': 'sum'
    })
    coast_stats.columns = ['Total_Revenue', 'Clearances', 'Total_Tons']
    coast_stats['Revenue_Pct'] = (coast_stats['Total_Revenue'] / df['Fee_Adj'].sum()) * 100
    coast_stats = coast_stats.sort_values('Total_Revenue', ascending=False)

    # Region x Vessel Type matrix
    region_type = df.groupby(['Port_Region', 'Ships_Type'])['Fee_Adj'].sum().reset_index()
    region_type_pivot = region_type.pivot_table(
        index='Port_Region',
        columns='Ships_Type',
        values='Fee_Adj',
        fill_value=0
    )

    # Top vessel types by region
    top_types_by_region = df.groupby(['Port_Region', 'Ships_Type']).agg({
        'Fee_Adj': 'sum',
        'Clearance_RECID': 'count'
    }).reset_index()
    top_types_by_region.columns = ['Port_Region', 'Ships_Type', 'Revenue', 'Clearances']
    top_types_by_region = top_types_by_region.sort_values(['Port_Region', 'Revenue'], ascending=[True, False])

    results = {
        'region_stats_df': region_stats.reset_index(),
        'coast_stats_df': coast_stats.reset_index(),
        'region_type_matrix': region_type_pivot,
        'region_type_df': region_type,
        'top_types_by_region_df': top_types_by_region
    }

    print(f"  Total regions: {len(region_stats)}")
    print(f"  Top region: {region_stats.index[0]} (${region_stats.iloc[0]['Total_Revenue']:,.0f})")

    return results


def analyze_cargo_flows(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze cargo flows and trade routes."""
    print("Analyzing cargo flows...")

    # Origin countries
    origin_stats = df[df['Origin_Country'] != 'Unknown'].groupby('Origin_Country').agg({
        'Fee_Adj': 'count',
        'Tons': 'sum'
    }).sort_values('Fee_Adj', ascending=False).head(20)
    origin_stats.columns = ['Clearances', 'Total_Tons']

    # Destination countries
    dest_stats = df[df['Destination_Country'] != 'Unknown'].groupby('Destination_Country').agg({
        'Fee_Adj': 'count',
        'Tons': 'sum'
    }).sort_values('Fee_Adj', ascending=False).head(20)
    dest_stats.columns = ['Clearances', 'Total_Tons']

    # Trade lanes (Origin -> Destination via Region)
    trade_lanes = df[(df['Origin_Country'] != 'Unknown') &
                     (df['Destination_Country'] != 'Unknown')].groupby(
        ['Origin_Country', 'Destination_Country', 'Port_Region']
    ).agg({
        'Fee_Adj': 'count',
        'Tons': 'sum'
    }).reset_index()
    trade_lanes.columns = ['Origin', 'Destination', 'Region', 'Clearances', 'Tons']
    trade_lanes = trade_lanes.sort_values('Clearances', ascending=False).head(50)

    # Commodity groups
    commodity_stats = df.groupby('ICST_DESC').agg({
        'Fee_Adj': ['count', 'sum'],
        'Tons': 'sum'
    })
    commodity_stats.columns = ['Clearances', 'Revenue', 'Total_Tons']
    commodity_stats = commodity_stats.sort_values('Revenue', ascending=False)

    results = {
        'origin_stats_df': origin_stats.reset_index(),
        'dest_stats_df': dest_stats.reset_index(),
        'trade_lanes_df': trade_lanes,
        'commodity_stats_df': commodity_stats.reset_index()
    }

    print(f"  Top origin: {origin_stats.index[0] if len(origin_stats) > 0 else 'N/A'}")
    print(f"  Top destination: {dest_stats.index[0] if len(dest_stats) > 0 else 'N/A'}")
    print(f"  Total trade lanes analyzed: {len(trade_lanes)}")

    return results


def analyze_vessel_type_by_region(df: pd.DataFrame) -> Dict[str, Any]:
    """Detailed analysis of vessel type preferences by region."""
    print("Analyzing vessel type preferences by region...")

    # For each region, get top 5 vessel types
    region_top_types = {}
    for region in df['Port_Region'].unique():
        region_df = df[df['Port_Region'] == region]
        top_5 = region_df.groupby('Ships_Type').agg({
            'Fee_Adj': ['sum', 'count']
        }).reset_index()
        top_5.columns = ['Ships_Type', 'Revenue', 'Clearances']
        top_5 = top_5.sort_values('Revenue', ascending=False).head(5)
        region_top_types[region] = top_5

    # Vessel type diversity by region (how many different types operate)
    type_diversity = df.groupby('Port_Region')['Ships_Type'].nunique().sort_values(ascending=False)

    # Average vessel characteristics by region
    vessel_chars = df.groupby('Port_Region').agg({
        'Ships_DWT': 'mean',
        'Ships_LOA': 'mean',
        'Ships_Beam': 'mean',
        'Ships_Draft': 'mean'
    })

    results = {
        'region_top_types': region_top_types,
        'type_diversity_df': type_diversity.reset_index(),
        'vessel_chars_df': vessel_chars.reset_index()
    }

    print(f"  Vessel type diversity calculated for {len(type_diversity)} regions")

    return results


def analyze_grain_shipments(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze grain shipment subset."""
    print("Analyzing grain shipments...")

    grain_df = df[df['Grain'] == 'Y'].copy()

    if len(grain_df) == 0:
        return {'grain_clearances': 0, 'grain_revenue': 0, 'grain_tonnage': 0}

    grain_clearances = len(grain_df)
    grain_revenue = grain_df['Fee_Adj'].sum()
    grain_tonnage = grain_df['Grain_Tons'].sum() if 'Grain_Tons' in grain_df.columns else 0

    # Grain by region
    grain_by_region = grain_df.groupby('Port_Region').agg({
        'Fee_Adj': 'count',
        'Grain_Tons': 'sum' if 'Grain_Tons' in grain_df.columns else 'count'
    }).sort_values('Fee_Adj', ascending=False)
    grain_by_region.columns = ['Clearances', 'Tonnage']

    # Grain destinations
    if 'Destination_Country' in grain_df.columns:
        grain_dest = grain_df.groupby('Destination_Country').agg({
            'Fee_Adj': 'count',
            'Grain_Tons': 'sum' if 'Grain_Tons' in grain_df.columns else 'count'
        }).sort_values('Fee_Adj', ascending=False)
        grain_dest.columns = ['Shipments', 'Tonnage']
    else:
        grain_dest = pd.DataFrame()

    # Grain vessel types
    grain_types = grain_df.groupby('Ships_Type').agg({
        'Fee_Adj': ['count', 'sum']
    })
    grain_types.columns = ['Clearances', 'Revenue']
    grain_types = grain_types.sort_values('Clearances', ascending=False)

    results = {
        'grain_clearances': grain_clearances,
        'grain_revenue': grain_revenue,
        'grain_tonnage': grain_tonnage,
        'grain_pct': (grain_clearances / len(df)) * 100,
        'grain_by_region_df': grain_by_region.reset_index(),
        'grain_dest_df': grain_dest.reset_index() if len(grain_dest) > 0 else pd.DataFrame(),
        'grain_types_df': grain_types.reset_index()
    }

    print(f"  Grain clearances: {grain_clearances:,} ({results['grain_pct']:.1f}%)")
    print(f"  Grain tonnage: {grain_tonnage:,.0f} MT")

    return results


def run_all_analysis(data_file: str) -> Dict[str, Any]:
    """Run all analysis modules focused on vessel types and trade patterns."""
    print("\n" + "="*60)
    print("USACE Market Study - Vessel Type & Trade Pattern Analysis")
    print("="*60 + "\n")

    # Load data
    df = load_and_prepare_data(data_file)

    # Run all analyses
    results = {
        'market': calculate_market_metrics(df),
        'vessel_types': analyze_vessel_types(df),
        'regional_trade': analyze_regional_trade_patterns(df),
        'cargo_flows': analyze_cargo_flows(df),
        'vessel_type_by_region': analyze_vessel_type_by_region(df),
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
