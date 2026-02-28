"""
Panjiva Import Manifest Data Analysis - Year-over-Year Commodity Trends
Generates HTML slides with interactive charts using reveal.js
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
import base64
from io import BytesIO
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for professional charts
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# Color palette
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E',
          '#BC4B51', '#8B5A3C', '#4A5859', '#D4A373', '#7209B7']

def load_data(file_path):
    """Load and preprocess Panjiva data"""
    print("Loading Panjiva data...")

    # Read with specific columns to optimize memory
    cols_needed = [
        'Arrival Date', 'Tons', 'Kilos', 'Value',
        'Group', 'Commodity', 'Cargo', 'Cargo_Detail',
        'Port_Consolidated', 'Port_Region', 'Country of Origin (F)',
        'Vessel_Type_Simple', 'Consignee', 'Filter'
    ]

    df = pd.read_csv(file_path, usecols=cols_needed, low_memory=False)

    # Convert Arrival Date to datetime
    df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

    # Extract year
    df['Year'] = df['Arrival Date'].dt.year

    # Filter for 2023-2025 and exclude white noise
    df = df[
        (df['Year'].isin([2023, 2024, 2025])) &
        (df['Filter'] != 'White_Noise_Filter')
    ].copy()

    # Convert numeric columns
    df['Tons'] = pd.to_numeric(df['Tons'], errors='coerce')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

    # Fill NaN values
    df['Tons'] = df['Tons'].fillna(0)
    df['Value'] = df['Value'].fillna(0)

    print(f"Loaded {len(df):,} records from 2023-2025")
    print(f"Years: {sorted(df['Year'].unique())}")
    print(f"Total tonnage: {df['Tons'].sum():,.0f} tons")

    return df

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def create_yoy_total_volume_chart(df):
    """Chart 1: Total import volumes by year"""
    print("Creating YoY total volume chart...")

    # Aggregate by year
    yearly = df.groupby('Year').agg({
        'Tons': 'sum',
        'Value': 'sum',
        'Arrival Date': 'count'
    }).reset_index()
    yearly.columns = ['Year', 'Total_Tons', 'Total_Value', 'Shipment_Count']

    # Calculate YoY growth
    yearly['Tonnage_Growth'] = yearly['Total_Tons'].pct_change() * 100
    yearly['Value_Growth'] = yearly['Total_Value'].pct_change() * 100

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Chart 1: Total tonnage by year
    ax1 = fig.add_subplot(gs[0, 0])
    bars1 = ax1.bar(yearly['Year'], yearly['Total_Tons'] / 1e6,
                     color=COLORS[0], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Year', fontweight='bold')
    ax1.set_ylabel('Total Tonnage (Million Tons)', fontweight='bold')
    ax1.set_title('Total Import Volume by Year', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}M',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Chart 2: YoY growth rates
    ax2 = fig.add_subplot(gs[0, 1])
    x = np.arange(len(yearly[yearly['Tonnage_Growth'].notna()]))
    width = 0.35

    growth_data = yearly[yearly['Tonnage_Growth'].notna()]
    bars2a = ax2.bar(x - width/2, growth_data['Tonnage_Growth'], width,
                     label='Tonnage Growth', color=COLORS[1], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2b = ax2.bar(x + width/2, growth_data['Value_Growth'], width,
                     label='Value Growth', color=COLORS[2], alpha=0.8, edgecolor='black', linewidth=1.5)

    ax2.set_xlabel('Year', fontweight='bold')
    ax2.set_ylabel('YoY Growth (%)', fontweight='bold')
    ax2.set_title('Year-over-Year Growth Rates', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(growth_data['Year'])
    ax2.legend(loc='upper left')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels
    for bars in [bars2a, bars2b]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom' if height >= 0 else 'top',
                    fontweight='bold', fontsize=9)

    # Chart 3: Total value by year
    ax3 = fig.add_subplot(gs[1, 0])
    bars3 = ax3.bar(yearly['Year'], yearly['Total_Value'] / 1e9,
                    color=COLORS[3], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_xlabel('Year', fontweight='bold')
    ax3.set_ylabel('Total Value (Billion USD)', fontweight='bold')
    ax3.set_title('Total Import Value by Year', fontsize=14, fontweight='bold', pad=15)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')

    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}B',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Chart 4: Shipment count by year
    ax4 = fig.add_subplot(gs[1, 1])
    bars4 = ax4.bar(yearly['Year'], yearly['Shipment_Count'] / 1000,
                    color=COLORS[4], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_xlabel('Year', fontweight='bold')
    ax4.set_ylabel('Shipment Count (Thousands)', fontweight='bold')
    ax4.set_title('Total Shipments by Year', fontsize=14, fontweight='bold', pad=15)
    ax4.grid(axis='y', alpha=0.3, linestyle='--')

    for bar in bars4:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}K',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    fig.suptitle('Panjiva Import Data: Year-over-Year Overview (2023-2025)',
                 fontsize=16, fontweight='bold', y=0.98)

    # Create summary table
    table_data = yearly[['Year', 'Total_Tons', 'Total_Value', 'Shipment_Count',
                          'Tonnage_Growth', 'Value_Growth']].copy()
    table_data['Total_Tons'] = table_data['Total_Tons'].apply(lambda x: f'{x/1e6:.2f}M')
    table_data['Total_Value'] = table_data['Total_Value'].apply(lambda x: f'${x/1e9:.2f}B')
    table_data['Shipment_Count'] = table_data['Shipment_Count'].apply(lambda x: f'{x/1000:.1f}K')
    table_data['Tonnage_Growth'] = table_data['Tonnage_Growth'].apply(
        lambda x: f'{x:.1f}%' if pd.notna(x) else 'N/A')
    table_data['Value_Growth'] = table_data['Value_Growth'].apply(
        lambda x: f'{x:.1f}%' if pd.notna(x) else 'N/A')

    return fig_to_base64(fig), table_data.to_html(index=False, classes='data-table')

def create_top_commodities_chart(df):
    """Chart 2: Top 10 commodities by volume"""
    print("Creating top commodities chart...")

    # Aggregate by commodity and year
    commodity_yearly = df.groupby(['Cargo_Detail', 'Year']).agg({
        'Tons': 'sum',
        'Value': 'sum',
        'Arrival Date': 'count'
    }).reset_index()

    # Get top 10 commodities by total tonnage
    top_commodities = commodity_yearly.groupby('Cargo_Detail')['Tons'].sum().nlargest(10).index

    # Filter for top commodities
    top_data = commodity_yearly[commodity_yearly['Cargo_Detail'].isin(top_commodities)]

    # Create pivot for stacked bar chart
    pivot = top_data.pivot(index='Cargo_Detail', columns='Year', values='Tons').fillna(0)
    pivot = pivot.div(1e6)  # Convert to millions

    # Sort by total
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=True)
    pivot = pivot.drop('Total', axis=1)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))

    # Chart 1: Stacked horizontal bar chart
    pivot.plot(kind='barh', stacked=False, ax=ax1,
               color=COLORS[:3], alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_xlabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Commodity', fontweight='bold', fontsize=12)
    ax1.set_title('Top 10 Commodities by Import Volume', fontsize=14, fontweight='bold', pad=15)
    ax1.legend(title='Year', loc='lower right', framealpha=0.9)
    ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # Chart 2: YoY comparison for top 5
    top_5 = pivot.tail(5)
    x = np.arange(len(top_5))
    width = 0.25

    for i, year in enumerate([2023, 2024, 2025]):
        if year in top_5.columns:
            offset = width * (i - 1)
            bars = ax2.bar(x + offset, top_5[year], width,
                          label=str(year), color=COLORS[i], alpha=0.8,
                          edgecolor='black', linewidth=1)

            # Add value labels
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.1f}',
                            ha='center', va='bottom', fontsize=8, rotation=0)

    ax2.set_xlabel('Commodity', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax2.set_title('Top 5 Commodities: Year-over-Year Comparison',
                  fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(top_5.index, rotation=45, ha='right')
    ax2.legend(title='Year', loc='upper left')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    fig.suptitle('Top Commodities Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Create summary table
    table_data = top_data.pivot_table(
        index='Cargo_Detail',
        columns='Year',
        values='Tons',
        aggfunc='sum'
    ).fillna(0)

    table_data['Total'] = table_data.sum(axis=1)
    table_data = table_data.sort_values('Total', ascending=False)

    for col in table_data.columns:
        if col != 'Total':
            table_data[col] = table_data[col].apply(lambda x: f'{x/1e6:.2f}M tons')
        else:
            table_data[col] = table_data[col].apply(lambda x: f'{x/1e6:.2f}M tons')

    table_data = table_data.reset_index()
    table_data.columns = ['Commodity'] + [str(c) for c in table_data.columns[1:]]

    return fig_to_base64(fig), table_data.to_html(index=False, classes='data-table')

def create_commodity_growth_chart(df):
    """Chart 3: Commodity growth rates"""
    print("Creating commodity growth chart...")

    # Aggregate by commodity and year
    commodity_yearly = df.groupby(['Cargo_Detail', 'Year'])['Tons'].sum().reset_index()

    # Get top 15 commodities
    top_commodities = commodity_yearly.groupby('Cargo_Detail')['Tons'].sum().nlargest(15).index

    # Filter and pivot
    growth_data = commodity_yearly[commodity_yearly['Cargo_Detail'].isin(top_commodities)]
    pivot = growth_data.pivot(index='Cargo_Detail', columns='Year', values='Tons').fillna(0)

    # Calculate growth rates
    if 2023 in pivot.columns and 2024 in pivot.columns:
        pivot['2023-2024 Growth'] = ((pivot[2024] - pivot[2023]) / pivot[2023].replace(0, np.nan) * 100)
    if 2024 in pivot.columns and 2025 in pivot.columns:
        pivot['2024-2025 Growth'] = ((pivot[2025] - pivot[2024]) / pivot[2024].replace(0, np.nan) * 100)

    # Filter for commodities with data
    growth_cols = [col for col in pivot.columns if 'Growth' in str(col)]
    pivot_clean = pivot[pivot[growth_cols].notna().any(axis=1)]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))

    # Chart 1: Growth rates heatmap style
    if len(growth_cols) > 0:
        growth_only = pivot_clean[growth_cols].sort_values(growth_cols[0], ascending=True)

        x = np.arange(len(growth_only))
        width = 0.35

        for i, col in enumerate(growth_cols):
            offset = width * (i - len(growth_cols)/2 + 0.5)
            colors = [COLORS[1] if v >= 0 else COLORS[3] for v in growth_only[col]]
            bars = ax1.barh(x + offset, growth_only[col], width,
                           label=col, color=colors, alpha=0.8, edgecolor='black', linewidth=1)

            # Add value labels
            for idx, (bar, val) in enumerate(zip(bars, growth_only[col])):
                if pd.notna(val) and abs(val) > 5:  # Only show labels for significant changes
                    ax1.text(val, bar.get_y() + bar.get_height()/2,
                            f'{val:.0f}%',
                            ha='left' if val >= 0 else 'right',
                            va='center', fontsize=8, fontweight='bold')

        ax1.set_yticks(x)
        ax1.set_yticklabels(growth_only.index, fontsize=9)
        ax1.set_xlabel('Growth Rate (%)', fontweight='bold', fontsize=12)
        ax1.set_title('Commodity Growth Rates by Period', fontsize=14, fontweight='bold', pad=15)
        ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax1.legend(loc='best')
        ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # Chart 2: Line chart showing trends
    top_5_for_trend = pivot_clean.iloc[:, :3].sum(axis=1).nlargest(5).index
    trend_data = pivot.loc[top_5_for_trend, [col for col in pivot.columns if col in [2023, 2024, 2025]]]

    for commodity in trend_data.index:
        years = [y for y in [2023, 2024, 2025] if y in trend_data.columns]
        values = [trend_data.loc[commodity, y] / 1e6 for y in years]
        ax2.plot(years, values, marker='o', linewidth=2.5, markersize=8,
                label=commodity, alpha=0.8)

        # Add value labels
        for year, value in zip(years, values):
            ax2.text(year, value, f'{value:.1f}M',
                    fontsize=8, ha='center', va='bottom')

    ax2.set_xlabel('Year', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax2.set_title('Top 5 Commodities: Trend Lines', fontsize=14, fontweight='bold', pad=15)
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xticks([2023, 2024, 2025])

    fig.suptitle('Commodity Growth Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Create summary table
    table_data = pivot_clean[growth_cols].copy()
    table_data = table_data.round(1)
    for col in table_data.columns:
        table_data[col] = table_data[col].apply(lambda x: f'{x:.1f}%' if pd.notna(x) else 'N/A')
    table_data = table_data.reset_index()
    table_data.columns = ['Commodity'] + list(table_data.columns[1:])

    return fig_to_base64(fig), table_data.to_html(index=False, classes='data-table')

def create_port_trends_chart(df):
    """Chart 4: Port-level trends by commodity"""
    print("Creating port trends chart...")

    # Aggregate by port and year
    port_yearly = df.groupby(['Port_Consolidated', 'Year'])['Tons'].sum().reset_index()

    # Get top 10 ports
    top_ports = port_yearly.groupby('Port_Consolidated')['Tons'].sum().nlargest(10).index

    # Filter for top ports
    port_data = port_yearly[port_yearly['Port_Consolidated'].isin(top_ports)]

    # Pivot
    pivot = port_data.pivot(index='Port_Consolidated', columns='Year', values='Tons').fillna(0)
    pivot = pivot.div(1e6)  # Convert to millions

    # Sort by total
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=True)
    pivot = pivot.drop('Total', axis=1)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))

    # Chart 1: Stacked bar chart
    pivot.plot(kind='barh', stacked=False, ax=ax1,
               color=COLORS[:3], alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_xlabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Port', fontweight='bold', fontsize=12)
    ax1.set_title('Top 10 Ports by Import Volume', fontsize=14, fontweight='bold', pad=15)
    ax1.legend(title='Year', loc='lower right')
    ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # Chart 2: Top commodities by top 3 ports
    top_3_ports = pivot.tail(3).index

    port_commodity = df[df['Port_Consolidated'].isin(top_3_ports)].groupby(
        ['Port_Consolidated', 'Cargo_Detail']
    )['Tons'].sum().reset_index()

    # Get top 5 commodities per port
    top_port_commodities = []
    for port in top_3_ports:
        port_top = port_commodity[port_commodity['Port_Consolidated'] == port].nlargest(5, 'Tons')
        top_port_commodities.append(port_top)

    combined = pd.concat(top_port_commodities)
    combined['Tons'] = combined['Tons'] / 1e6

    # Create grouped bar chart
    ports_list = combined['Port_Consolidated'].unique()
    x = np.arange(len(ports_list))
    width = 0.15

    commodities_per_port = {}
    for port in ports_list:
        commodities_per_port[port] = combined[combined['Port_Consolidated'] == port]['Cargo_Detail'].tolist()

    all_commodities = list(set([c for comms in commodities_per_port.values() for c in comms]))

    for i, commodity in enumerate(all_commodities[:5]):  # Limit to 5 for readability
        values = []
        for port in ports_list:
            port_data = combined[(combined['Port_Consolidated'] == port) &
                                (combined['Cargo_Detail'] == commodity)]
            values.append(port_data['Tons'].sum() if len(port_data) > 0 else 0)

        offset = width * (i - 2)
        ax2.bar(x + offset, values, width, label=commodity[:30],
               color=COLORS[i % len(COLORS)], alpha=0.8, edgecolor='black', linewidth=1)

    ax2.set_xlabel('Port', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax2.set_title('Top Commodities by Top 3 Ports', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(ports_list, rotation=45, ha='right', fontsize=10)
    ax2.legend(loc='upper left', fontsize=8, ncol=1)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    fig.suptitle('Port-Level Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Create summary table
    table_data = port_yearly[port_yearly['Port_Consolidated'].isin(top_ports)].pivot_table(
        index='Port_Consolidated',
        columns='Year',
        values='Tons',
        aggfunc='sum'
    ).fillna(0)

    table_data['Total'] = table_data.sum(axis=1)
    table_data = table_data.sort_values('Total', ascending=False)

    for col in table_data.columns:
        table_data[col] = table_data[col].apply(lambda x: f'{x/1e6:.2f}M tons')

    table_data = table_data.reset_index()
    table_data.columns = ['Port'] + [str(c) for c in table_data.columns[1:]]

    return fig_to_base64(fig), table_data.to_html(index=False, classes='data-table')

def create_origin_trends_chart(df):
    """Chart 5: Country of origin trends by commodity"""
    print("Creating country of origin trends chart...")

    # Aggregate by country and year
    country_yearly = df.groupby(['Country of Origin (F)', 'Year'])['Tons'].sum().reset_index()

    # Get top 10 countries
    top_countries = country_yearly.groupby('Country of Origin (F)')['Tons'].sum().nlargest(10).index

    # Filter for top countries
    country_data = country_yearly[country_yearly['Country of Origin (F)'].isin(top_countries)]

    # Pivot
    pivot = country_data.pivot(index='Country of Origin (F)', columns='Year', values='Tons').fillna(0)
    pivot = pivot.div(1e6)  # Convert to millions

    # Sort by total
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=True)
    pivot = pivot.drop('Total', axis=1)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))

    # Chart 1: Grouped bar chart
    pivot.plot(kind='barh', stacked=False, ax=ax1,
               color=COLORS[:3], alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_xlabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Country of Origin', fontweight='bold', fontsize=12)
    ax1.set_title('Top 10 Countries by Import Volume', fontsize=14, fontweight='bold', pad=15)
    ax1.legend(title='Year', loc='lower right')
    ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # Chart 2: Top commodities by top 3 countries
    top_3_countries = pivot.tail(3).index

    country_commodity = df[df['Country of Origin (F)'].isin(top_3_countries)].groupby(
        ['Country of Origin (F)', 'Cargo_Detail']
    )['Tons'].sum().reset_index()

    # Get top 5 commodities per country
    top_country_commodities = []
    for country in top_3_countries:
        country_top = country_commodity[country_commodity['Country of Origin (F)'] == country].nlargest(5, 'Tons')
        top_country_commodities.append(country_top)

    combined = pd.concat(top_country_commodities)
    combined['Tons'] = combined['Tons'] / 1e6

    # Create grouped bar chart
    countries_list = combined['Country of Origin (F)'].unique()
    x = np.arange(len(countries_list))
    width = 0.15

    commodities_per_country = {}
    for country in countries_list:
        commodities_per_country[country] = combined[combined['Country of Origin (F)'] == country]['Cargo_Detail'].tolist()

    all_commodities = list(set([c for comms in commodities_per_country.values() for c in comms]))

    for i, commodity in enumerate(all_commodities[:5]):  # Limit to 5 for readability
        values = []
        for country in countries_list:
            country_data = combined[(combined['Country of Origin (F)'] == country) &
                                   (combined['Cargo_Detail'] == commodity)]
            values.append(country_data['Tons'].sum() if len(country_data) > 0 else 0)

        offset = width * (i - 2)
        ax2.bar(x + offset, values, width, label=commodity[:30],
               color=COLORS[i % len(COLORS)], alpha=0.8, edgecolor='black', linewidth=1)

    ax2.set_xlabel('Country', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Tonnage (Million Tons)', fontweight='bold', fontsize=12)
    ax2.set_title('Top Commodities by Top 3 Origin Countries', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(countries_list, rotation=45, ha='right', fontsize=10)
    ax2.legend(loc='upper left', fontsize=8, ncol=1)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    fig.suptitle('Country of Origin Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Create summary table
    table_data = country_yearly[country_yearly['Country of Origin (F)'].isin(top_countries)].pivot_table(
        index='Country of Origin (F)',
        columns='Year',
        values='Tons',
        aggfunc='sum'
    ).fillna(0)

    table_data['Total'] = table_data.sum(axis=1)
    table_data = table_data.sort_values('Total', ascending=False)

    for col in table_data.columns:
        table_data[col] = table_data[col].apply(lambda x: f'{x/1e6:.2f}M tons')

    table_data = table_data.reset_index()
    table_data.columns = ['Country'] + [str(c) for c in table_data.columns[1:]]

    return fig_to_base64(fig), table_data.to_html(index=False, classes='data-table')

def generate_html_slides(charts_data):
    """Generate HTML slides with reveal.js"""
    print("Generating HTML slides...")

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panjiva Commodity Trends Analysis (2023-2025)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/white.css">
    <style>
        .reveal h1 {
            font-size: 2.5em;
            color: #2E86AB;
            margin-bottom: 0.5em;
            text-transform: none;
        }
        .reveal h2 {
            font-size: 2em;
            color: #2E86AB;
            margin-bottom: 0.5em;
            text-transform: none;
        }
        .reveal h3 {
            font-size: 1.5em;
            color: #A23B72;
            text-transform: none;
        }
        .reveal p {
            font-size: 1.2em;
            line-height: 1.6;
        }
        .reveal img {
            max-width: 100%;
            height: auto;
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .data-table {
            font-size: 0.85em;
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th {
            background-color: #2E86AB;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        .data-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .data-table tr:hover {
            background-color: #f5f5f5;
        }
        .data-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .slide-footer {
            position: absolute;
            bottom: 20px;
            left: 20px;
            font-size: 0.7em;
            color: #666;
        }
        .key-insights {
            background-color: #f0f8ff;
            border-left: 4px solid #2E86AB;
            padding: 15px;
            margin: 20px 0;
            font-size: 1em;
        }
        .key-insights ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .key-insights li {
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">

            <!-- Title Slide -->
            <section>
                <h1>Panjiva Import Manifest Analysis</h1>
                <h2>Year-over-Year Commodity Trends</h2>
                <h3>2023 - 2025</h3>
                <p style="margin-top: 40px; font-size: 1em; color: #666;">
                    Analysis Date: ''' + datetime.now().strftime('%B %d, %Y') + '''
                </p>
                <p style="font-size: 0.9em; color: #666;">
                    Data Source: Panjiva Import Manifest Database (Phase 07 Enrichment)
                </p>
            </section>

            <!-- Slide 1: YoY Total Volume -->
            <section>
                <h2>Year-over-Year Import Volume Overview</h2>
                <img src="data:image/png;base64,''' + charts_data['yoy_total']['chart'] + '''" alt="YoY Total Volume">
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <section>
                <h2>Year-over-Year Summary Statistics</h2>
                ''' + charts_data['yoy_total']['table'] + '''
                <div class="key-insights">
                    <strong>Key Insights:</strong>
                    <ul>
                        <li>Comprehensive overview of import volumes, values, and shipment counts</li>
                        <li>Growth rate analysis reveals year-over-year trends</li>
                        <li>Multiple metrics provide context for market dynamics</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <!-- Slide 2: Top Commodities -->
            <section>
                <h2>Top 10 Commodities by Import Volume</h2>
                <img src="data:image/png;base64,''' + charts_data['top_commodities']['chart'] + '''" alt="Top Commodities">
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <section>
                <h2>Top Commodities - Detailed Breakdown</h2>
                ''' + charts_data['top_commodities']['table'] + '''
                <div class="key-insights">
                    <strong>Key Insights:</strong>
                    <ul>
                        <li>Identifies dominant commodity categories in US imports</li>
                        <li>Reveals shifts in commodity mix over time</li>
                        <li>Provides basis for focused commodity analysis</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <!-- Slide 3: Commodity Growth Rates -->
            <section>
                <h2>Commodity Growth Rate Analysis</h2>
                <img src="data:image/png;base64,''' + charts_data['commodity_growth']['chart'] + '''" alt="Commodity Growth">
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <section>
                <h2>Commodity Growth Rates - Data Table</h2>
                ''' + charts_data['commodity_growth']['table'] + '''
                <div class="key-insights">
                    <strong>Key Insights:</strong>
                    <ul>
                        <li>Highlights fastest-growing and declining commodity categories</li>
                        <li>Trend lines reveal momentum and volatility</li>
                        <li>Growth rate comparison enables strategic planning</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <!-- Slide 4: Port-Level Trends -->
            <section>
                <h2>Port-Level Import Trends</h2>
                <img src="data:image/png;base64,''' + charts_data['port_trends']['chart'] + '''" alt="Port Trends">
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <section>
                <h2>Top Ports - Volume Summary</h2>
                ''' + charts_data['port_trends']['table'] + '''
                <div class="key-insights">
                    <strong>Key Insights:</strong>
                    <ul>
                        <li>Identifies critical gateway ports for US imports</li>
                        <li>Port-commodity relationships reveal specialization</li>
                        <li>Geographic distribution of import infrastructure</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <!-- Slide 5: Country of Origin -->
            <section>
                <h2>Country of Origin Analysis</h2>
                <img src="data:image/png;base64,''' + charts_data['origin_trends']['chart'] + '''" alt="Origin Trends">
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <section>
                <h2>Top Origin Countries - Volume Summary</h2>
                ''' + charts_data['origin_trends']['table'] + '''
                <div class="key-insights">
                    <strong>Key Insights:</strong>
                    <ul>
                        <li>Maps global supply chain dependencies</li>
                        <li>Country-commodity specialization patterns</li>
                        <li>Trade relationship evolution over time</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

            <!-- Conclusion Slide -->
            <section>
                <h2>Executive Summary</h2>
                <div class="key-insights">
                    <strong>Analysis Overview:</strong>
                    <ul>
                        <li><strong>Dataset:</strong> Panjiva Import Manifest Database (Phase 07 Enrichment)</li>
                        <li><strong>Time Period:</strong> 2023-2025 (3 years)</li>
                        <li><strong>Scope:</strong> US import flows by commodity, port, and origin country</li>
                        <li><strong>Methodology:</strong> Year-over-year comparative analysis with growth rate calculations</li>
                    </ul>
                    <br>
                    <strong>Key Applications:</strong>
                    <ul>
                        <li>Strategic market intelligence for commodity supply chains</li>
                        <li>Port infrastructure planning and capacity analysis</li>
                        <li>Trade policy impact assessment</li>
                        <li>Competitive landscape monitoring</li>
                    </ul>
                </div>
                <div class="slide-footer">Source: Panjiva Phase 07 Output | Analysis: 2023-2025</div>
            </section>

        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            controls: true,
            progress: true,
            center: true,
            transition: 'slide',
            width: 1400,
            height: 900,
            margin: 0.04,
            slideNumber: 'c/t'
        });
    </script>
</body>
</html>
'''

    return html_template

def main():
    """Main execution function"""
    print("=" * 80)
    print("PANJIVA COMMODITY TRENDS ANALYSIS")
    print("=" * 80)

    # File paths
    data_file = "G:/My Drive/LLM/project_master_reporting/02_TOOLSETS/vessel_intelligence/src/pipeline/phase_07_enrichment/phase_07_output.csv"
    output_file = "G:/My Drive/LLM/project_master_reporting/Panjiva_Commodity_Trends_Charts.html"

    # Load data
    df = load_data(data_file)

    # Generate all charts
    charts_data = {}

    print("\n" + "=" * 80)
    charts_data['yoy_total'] = {
        'chart': create_yoy_total_volume_chart(df)[0],
        'table': create_yoy_total_volume_chart(df)[1]
    }

    print("=" * 80)
    charts_data['top_commodities'] = {
        'chart': create_top_commodities_chart(df)[0],
        'table': create_top_commodities_chart(df)[1]
    }

    print("=" * 80)
    charts_data['commodity_growth'] = {
        'chart': create_commodity_growth_chart(df)[0],
        'table': create_commodity_growth_chart(df)[1]
    }

    print("=" * 80)
    charts_data['port_trends'] = {
        'chart': create_port_trends_chart(df)[0],
        'table': create_port_trends_chart(df)[1]
    }

    print("=" * 80)
    charts_data['origin_trends'] = {
        'chart': create_origin_trends_chart(df)[0],
        'table': create_origin_trends_chart(df)[1]
    }

    # Generate HTML
    print("=" * 80)
    html_content = generate_html_slides(charts_data)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n{'=' * 80}")
    print(f"SUCCESS: HTML slides saved to:")
    print(f"{output_file}")
    print(f"{'=' * 80}\n")

    print("Open the file in a web browser to view the presentation.")
    print("Use arrow keys or click to navigate between slides.")

if __name__ == "__main__":
    main()
