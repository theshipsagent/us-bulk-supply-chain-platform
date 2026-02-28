"""
USACE Market Study - Visualization Module
Creates charts and maps for market study report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def create_revenue_charts(results: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Create revenue and market concentration charts."""
    print("Creating revenue charts...")

    figures = {}
    market = results['market']

    # 1. Top 20 vessels by revenue - Bar chart
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    top_20 = market['top_50_vessels'].head(20)
    bars = ax1.barh(range(len(top_20)), top_20['Fee_Adj'] / 1e6, color='steelblue')
    ax1.set_yticks(range(len(top_20)))
    ax1.set_yticklabels(top_20['Vessel_ID'], fontsize=9)
    ax1.set_xlabel('Revenue ($ Million)', fontsize=11, fontweight='bold')
    ax1.set_title('Top 20 Vessels by Revenue (2023)', fontsize=13, fontweight='bold')
    ax1.invert_yaxis()
    ax1.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    figures['top_20_vessels'] = fig1

    # 2. Market concentration - Pie chart
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    top_10_rev = market['vessel_revenue_df'].head(10)['Fee_Adj'].sum()
    top_25_rev = market['vessel_revenue_df'].head(25)['Fee_Adj'].sum() - top_10_rev
    top_50_rev = market['vessel_revenue_df'].head(50)['Fee_Adj'].sum() - top_10_rev - top_25_rev
    rest_rev = market['total_revenue'] - top_10_rev - top_25_rev - top_50_rev

    sizes = [top_10_rev, top_25_rev, top_50_rev, rest_rev]
    labels = [
        f'Top 10\n${top_10_rev/1e6:.1f}M ({top_10_rev/market["total_revenue"]*100:.1f}%)',
        f'Top 11-25\n${top_25_rev/1e6:.1f}M ({top_25_rev/market["total_revenue"]*100:.1f}%)',
        f'Top 26-50\n${top_50_rev/1e6:.1f}M ({top_50_rev/market["total_revenue"]*100:.1f}%)',
        f'Rest\n${rest_rev/1e6:.1f}M ({rest_rev/market["total_revenue"]*100:.1f}%)'
    ]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors, autopct='',
                                         startangle=90, textprops={'fontsize': 10})
    ax2.set_title('Market Concentration by Top Vessels (2023)', fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    figures['market_concentration'] = fig2

    # 3. Lorenz curve - Revenue concentration
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    vessel_rev_sorted = market['vessel_revenue_df']['Fee_Adj'].sort_values().values
    cumulative_rev = np.cumsum(vessel_rev_sorted)
    cumulative_rev_pct = cumulative_rev / cumulative_rev[-1] * 100
    cumulative_vessels_pct = np.arange(1, len(vessel_rev_sorted) + 1) / len(vessel_rev_sorted) * 100

    ax3.plot(cumulative_vessels_pct, cumulative_rev_pct, linewidth=2, label='Actual Distribution', color='steelblue')
    ax3.plot([0, 100], [0, 100], 'k--', linewidth=1, label='Perfect Equality')
    ax3.fill_between(cumulative_vessels_pct, cumulative_rev_pct, cumulative_vessels_pct, alpha=0.3, color='lightblue')
    ax3.set_xlabel('Cumulative % of Vessels', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Cumulative % of Revenue', fontsize=11, fontweight='bold')
    ax3.set_title('Revenue Concentration (Lorenz Curve)', fontsize=13, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(alpha=0.3)
    plt.tight_layout()
    figures['lorenz_curve'] = fig3

    print(f"  Created {len(figures)} revenue charts")
    return figures


def create_vessel_type_charts(results: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Create vessel type analysis charts."""
    print("Creating vessel type charts...")

    figures = {}
    vessel_types = results['vessel_types']

    # 1. Top 15 vessel types by revenue - Horizontal bar
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    top_15 = vessel_types['type_revenue_df'].head(15)
    bars = ax1.barh(range(len(top_15)), top_15['Total_Revenue'] / 1e6, color='forestgreen')
    ax1.set_yticks(range(len(top_15)))
    ax1.set_yticklabels(top_15['Ships_Type'], fontsize=9)
    ax1.set_xlabel('Revenue ($ Million)', fontsize=11, fontweight='bold')
    ax1.set_title('Top 15 Vessel Types by Revenue (2023)', fontsize=13, fontweight='bold')
    ax1.invert_yaxis()
    ax1.grid(axis='x', alpha=0.3)

    # Add percentage labels
    for i, (idx, row) in enumerate(top_15.iterrows()):
        ax1.text(row['Total_Revenue'] / 1e6 + 1, i, f"{row['Revenue_Pct']:.1f}%",
                va='center', fontsize=9)

    plt.tight_layout()
    figures['type_revenue'] = fig1

    # 2. Revenue by cargo class - Stacked bar
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    cargo = vessel_types['cargo_revenue_df'].head(10)
    bars = ax2.bar(range(len(cargo)), cargo['Total_Revenue'] / 1e6, color='coral')
    ax2.set_xticks(range(len(cargo)))
    ax2.set_xticklabels(cargo['ICST_DESC'], rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('Revenue ($ Million)', fontsize=11, fontweight='bold')
    ax2.set_title('Revenue by Cargo Class (2023)', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    figures['cargo_revenue'] = fig2

    # 3. Fee distribution by vessel type - Box plot (top 10 types)
    fig3, ax3 = plt.subplots(figsize=(14, 8))
    df = results['df']
    top_10_types = vessel_types['type_revenue_df'].head(10)['Ships_Type'].tolist()
    df_top_types = df[df['Ships_Type'].isin(top_10_types)]

    # Create box plot
    type_order = top_10_types
    sns.boxplot(data=df_top_types, y='Ships_Type', x='Fee_Adj', order=type_order,
                palette='Set2', ax=ax3, orient='h')
    ax3.set_xlabel('Fee Amount ($)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Vessel Type', fontsize=11, fontweight='bold')
    ax3.set_title('Fee Distribution by Vessel Type (Top 10 Types)', fontsize=13, fontweight='bold')
    ax3.set_xlim(0, df_top_types['Fee_Adj'].quantile(0.95))  # Limit to 95th percentile for clarity
    plt.tight_layout()
    figures['fee_distribution'] = fig3

    # 4. Vessel type vs region heatmap (top 10 types, all regions)
    fig4, ax4 = plt.subplots(figsize=(14, 10))
    regions = results['regions']
    matrix = regions['region_type_matrix']

    # Select top 10 types
    top_types = vessel_types['type_revenue_df'].head(10)['Ships_Type'].tolist()
    matrix_subset = matrix[top_types]

    # Convert to millions
    matrix_subset = matrix_subset / 1e6

    sns.heatmap(matrix_subset, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax4,
                cbar_kws={'label': 'Revenue ($ Million)'})
    ax4.set_title('Revenue Heatmap: Vessel Type vs Region (Top 10 Types)',
                  fontsize=13, fontweight='bold', pad=15)
    ax4.set_xlabel('Vessel Type', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Region', fontsize=11, fontweight='bold')
    plt.setp(ax4.get_xticklabels(), rotation=45, ha='right', fontsize=9)
    plt.setp(ax4.get_yticklabels(), rotation=0, fontsize=9)
    plt.tight_layout()
    figures['type_region_heatmap'] = fig4

    print(f"  Created {len(figures)} vessel type charts")
    return figures


def create_regional_charts(results: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Create regional analysis charts."""
    print("Creating regional charts...")

    figures = {}
    regions = results['regions']

    # 1. Revenue by region - Bar chart
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    region_df = regions['region_revenue_df'].sort_values('Total_Revenue', ascending=True)
    bars = ax1.barh(range(len(region_df)), region_df['Total_Revenue'] / 1e6, color='purple')
    ax1.set_yticks(range(len(region_df)))
    ax1.set_yticklabels(region_df['Port_Region'], fontsize=10)
    ax1.set_xlabel('Revenue ($ Million)', fontsize=11, fontweight='bold')
    ax1.set_title('Revenue by Region (2023)', fontsize=13, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # Add percentage labels
    for i, (idx, row) in enumerate(region_df.iterrows()):
        ax1.text(row['Total_Revenue'] / 1e6 + 1, i, f"{row['Revenue_Pct']:.1f}%",
                va='center', fontsize=9)

    plt.tight_layout()
    figures['region_revenue'] = fig1

    # 2. Clearances by region
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    region_df_sorted = regions['region_revenue_df'].sort_values('Clearances', ascending=True)
    bars = ax2.barh(range(len(region_df_sorted)), region_df_sorted['Clearances'], color='teal')
    ax2.set_yticks(range(len(region_df_sorted)))
    ax2.set_yticklabels(region_df_sorted['Port_Region'], fontsize=10)
    ax2.set_xlabel('Number of Clearances', fontsize=11, fontweight='bold')
    ax2.set_title('Clearances by Region (2023)', fontsize=13, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    figures['region_clearances'] = fig2

    # 3. Average fee by region
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    region_df_avg = regions['region_revenue_df'].sort_values('Avg_Fee', ascending=True)
    bars = ax3.barh(range(len(region_df_avg)), region_df_avg['Avg_Fee'], color='darkorange')
    ax3.set_yticks(range(len(region_df_avg)))
    ax3.set_yticklabels(region_df_avg['Port_Region'], fontsize=10)
    ax3.set_xlabel('Average Fee ($)', fontsize=11, fontweight='bold')
    ax3.set_title('Average Fee by Region (2023)', fontsize=13, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    figures['region_avg_fee'] = fig3

    print(f"  Created {len(figures)} regional charts")
    return figures


def create_ship_revenue_charts(results: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Create per-ship revenue analysis charts."""
    print("Creating ship revenue charts...")

    figures = {}
    per_ship = results['per_ship']

    # 1. Revenue per ship distribution - Histogram
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    vessel_revenues = per_ship['vessel_stats_df']['Total_Revenue']

    # Use log scale for better visualization
    bins = np.logspace(np.log10(vessel_revenues.min()), np.log10(vessel_revenues.max()), 50)
    ax1.hist(vessel_revenues, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
    ax1.set_xscale('log')
    ax1.set_xlabel('Revenue per Ship ($, log scale)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Ships', fontsize=11, fontweight='bold')
    ax1.set_title('Distribution of Revenue per Ship (2023)', fontsize=13, fontweight='bold')
    ax1.grid(alpha=0.3)

    # Add average line
    avg_rev = per_ship['avg_revenue_per_ship']
    ax1.axvline(avg_rev, color='red', linestyle='--', linewidth=2, label=f'Mean: ${avg_rev:,.0f}')
    ax1.legend(fontsize=10)

    plt.tight_layout()
    figures['revenue_distribution'] = fig1

    # 2. Revenue per ship by vessel type - Box plot (top 10 types)
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    type_ship_rev = per_ship['type_ship_revenue_df'].head(10)

    # Get vessel data for these types
    df = results['df']
    vessel_types = results['vessel_types']
    top_types = vessel_types['type_revenue_df'].head(10)['Ships_Type'].tolist()

    # Get vessel stats by type
    vessel_stats = per_ship['vessel_stats_df']
    vessel_type_map = df[['Vessel_ID', 'Ships_Type']].drop_duplicates()
    vessel_stats_with_type = vessel_stats.merge(vessel_type_map, on='Vessel_ID')
    vessel_stats_top = vessel_stats_with_type[vessel_stats_with_type['Ships_Type'].isin(top_types)]

    sns.boxplot(data=vessel_stats_top, y='Ships_Type', x='Total_Revenue', order=top_types,
                palette='Set3', ax=ax2, orient='h')
    ax2.set_xlabel('Revenue per Ship ($)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Vessel Type', fontsize=11, fontweight='bold')
    ax2.set_title('Revenue per Ship by Vessel Type (Top 10 Types)', fontsize=13, fontweight='bold')
    ax2.set_xlim(0, vessel_stats_top['Total_Revenue'].quantile(0.95))
    plt.tight_layout()
    figures['revenue_by_type'] = fig2

    # 3. Visits vs revenue scatter plot
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    vessel_stats = per_ship['vessel_stats_df']

    # Sample if too many points
    if len(vessel_stats) > 1000:
        vessel_stats_sample = vessel_stats.sample(1000, random_state=42)
    else:
        vessel_stats_sample = vessel_stats

    scatter = ax3.scatter(vessel_stats_sample['Visits'], vessel_stats_sample['Total_Revenue'] / 1000,
                         alpha=0.5, c='navy', s=30)
    ax3.set_xlabel('Number of Visits', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Total Revenue ($1000s)', fontsize=11, fontweight='bold')
    ax3.set_title('Ship Visits vs Total Revenue', fontsize=13, fontweight='bold')
    ax3.grid(alpha=0.3)

    # Add trend line
    z = np.polyfit(vessel_stats['Visits'], vessel_stats['Total_Revenue'] / 1000, 1)
    p = np.poly1d(z)
    x_trend = np.linspace(vessel_stats['Visits'].min(), vessel_stats['Visits'].max(), 100)
    ax3.plot(x_trend, p(x_trend), 'r--', linewidth=2, label='Trend')
    ax3.legend(fontsize=10)

    plt.tight_layout()
    figures['visits_revenue'] = fig3

    print(f"  Created {len(figures)} ship revenue charts")
    return figures


def create_grain_charts(results: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Create grain shipment analysis charts."""
    print("Creating grain charts...")

    figures = {}
    grain = results['grain']

    if grain['grain_clearances'] == 0:
        print("  No grain data to visualize")
        return figures

    # 1. Grain destinations by shipment count
    if len(grain['destinations_df']) > 0:
        fig1, ax1 = plt.subplots(figsize=(12, 8))
        dest_df = grain['destinations_df'].head(15).reset_index()
        bars = ax1.barh(range(len(dest_df)), dest_df['Shipments'], color='gold')
        ax1.set_yticks(range(len(dest_df)))
        ax1.set_yticklabels(dest_df['Destination_Country'], fontsize=10)
        ax1.set_xlabel('Number of Shipments', fontsize=11, fontweight='bold')
        ax1.set_title('Top Grain Destinations by Shipment Count (2023)', fontsize=13, fontweight='bold')
        ax1.invert_yaxis()
        ax1.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        figures['grain_destinations'] = fig1

        # 2. Grain tonnage by destination - Pie chart
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        top_5_dest = grain['destinations_df'].head(5).reset_index()
        other_tonnage = grain['destinations_df']['Tonnage'].iloc[5:].sum() if len(grain['destinations_df']) > 5 else 0

        sizes = list(top_5_dest['Tonnage']) + ([other_tonnage] if other_tonnage > 0 else [])
        labels = list(top_5_dest['Destination_Country']) + (['Other'] if other_tonnage > 0 else [])

        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Grain Tonnage Distribution by Destination (2023)', fontsize=13, fontweight='bold')
        plt.tight_layout()
        figures['grain_tonnage_pie'] = fig2

    # 3. Grain vessel types
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    grain_types = grain['grain_types_df'].head(10)
    bars = ax3.bar(range(len(grain_types)), grain_types['Count'], color='wheat')
    ax3.set_xticks(range(len(grain_types)))
    ax3.set_xticklabels(grain_types['Ships_Type'], rotation=45, ha='right', fontsize=9)
    ax3.set_ylabel('Number of Shipments', fontsize=11, fontweight='bold')
    ax3.set_title('Grain Shipments by Vessel Type (2023)', fontsize=13, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    figures['grain_vessel_types'] = fig3

    print(f"  Created {len(figures)} grain charts")
    return figures


def create_summary_stats_figure(results: Dict[str, Any]) -> plt.Figure:
    """Create a summary statistics figure for executive summary."""
    print("Creating summary statistics figure...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('USACE Market Study 2023 - Key Statistics', fontsize=16, fontweight='bold')

    market = results['market']
    vessel_types = results['vessel_types']
    regions = results['regions']
    per_ship = results['per_ship']
    grain = results['grain']

    # Define stats
    stats = [
        ('Total Revenue', f"${market['total_revenue']/1e6:.1f}M", 'steelblue'),
        ('Total Clearances', f"{market['total_clearances']:,}", 'forestgreen'),
        ('Unique Vessels', f"{market['unique_vessels']:,}", 'coral'),
        ('Avg Fee', f"${market['avg_fee']:,.0f}", 'purple'),
        ('Top 10 Market Share', f"{market['top_10_pct']:.1f}%", 'darkorange'),
        ('Grain Shipments', f"{grain['grain_clearances']:,}", 'gold')
    ]

    for idx, (ax, (title, value, color)) in enumerate(zip(axes.flat, stats)):
        ax.text(0.5, 0.5, value, ha='center', va='center', fontsize=32, fontweight='bold', color=color)
        ax.text(0.5, 0.15, title, ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Add border
        rect = mpatches.Rectangle((0.05, 0.05), 0.9, 0.9, linewidth=2,
                                  edgecolor=color, facecolor='none', transform=ax.transAxes)
        ax.add_patch(rect)

    plt.tight_layout()
    return fig


def create_all_visualizations(results: Dict[str, Any]) -> Dict[str, Any]:
    """Create all visualizations and return figure dictionaries."""
    print("\n" + "="*60)
    print("USACE Market Study - Creating Visualizations")
    print("="*60 + "\n")

    all_figures = {
        'summary': create_summary_stats_figure(results),
        'revenue': create_revenue_charts(results),
        'vessel_types': create_vessel_type_charts(results),
        'regions': create_regional_charts(results),
        'per_ship': create_ship_revenue_charts(results),
        'grain': create_grain_charts(results)
    }

    total_charts = sum(len(v) if isinstance(v, dict) else 1 for v in all_figures.values())
    print("\n" + "="*60)
    print(f"Visualization Complete - {total_charts} charts created")
    print("="*60 + "\n")

    return all_figures


if __name__ == '__main__':
    # Test visualization with dummy data
    print("Visualization module loaded successfully")
    print("Run from main orchestrator to generate charts")
