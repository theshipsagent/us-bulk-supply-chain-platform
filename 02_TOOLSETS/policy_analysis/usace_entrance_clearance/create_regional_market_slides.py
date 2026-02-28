#!/usr/bin/env python3
"""
Create high-definition slides with weighted maps showing regional market strengths
US Agency Market Analysis - Regional Distribution
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches
from matplotlib import patheffects
import warnings
warnings.filterwarnings('ignore')

# Set high-quality output parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']

# Read the port calls data
print("Loading port call data...")
df = pd.read_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.02_PROCESSED\usace_2023_port_calls_COMPLETE_v4.0.0_20260206_004712.csv')

# Clean up agency fee data
df['Agency_Fee_Clean'] = df['Agency_Fee'].str.replace('$', '').str.replace(',', '').str.strip()
df['Agency_Fee_Numeric'] = pd.to_numeric(df['Agency_Fee_Clean'], errors='coerce')

print(f"Total records: {len(df):,}")
print(f"Total revenue: ${df['Agency_Fee_Numeric'].sum():,.0f}")

# ============================================================================
# REGIONAL ANALYSIS
# ============================================================================

# Analyze by Region
regional_summary = df.groupby('Port_Region').agg({
    'Port_Call_ID': 'count',
    'Agency_Fee_Numeric': 'sum'
}).round(0)

regional_summary.columns = ['Port_Calls', 'Total_Revenue']
regional_summary = regional_summary.sort_values('Total_Revenue', ascending=False)
regional_summary['Pct_Revenue'] = (regional_summary['Total_Revenue'] / regional_summary['Total_Revenue'].sum() * 100).round(1)
regional_summary['Pct_Calls'] = (regional_summary['Port_Calls'] / regional_summary['Port_Calls'].sum() * 100).round(1)

print("\n" + "="*80)
print("REGIONAL MARKET SUMMARY")
print("="*80)
print(regional_summary)

# Analyze by Coast
coast_summary = df.groupby('Port_Coast').agg({
    'Port_Call_ID': 'count',
    'Agency_Fee_Numeric': 'sum'
}).round(0)

coast_summary.columns = ['Port_Calls', 'Total_Revenue']
coast_summary = coast_summary.sort_values('Total_Revenue', ascending=False)
coast_summary['Pct_Revenue'] = (coast_summary['Total_Revenue'] / coast_summary['Total_Revenue'].sum() * 100).round(1)
coast_summary['Pct_Calls'] = (coast_summary['Port_Calls'] / coast_summary['Port_Calls'].sum() * 100).round(1)

print("\n" + "="*80)
print("COAST MARKET SUMMARY")
print("="*80)
print(coast_summary)

# Top ports analysis
port_summary = df.groupby('Port_Consolidated').agg({
    'Port_Call_ID': 'count',
    'Agency_Fee_Numeric': 'sum'
}).round(0)

port_summary.columns = ['Port_Calls', 'Total_Revenue']
port_summary = port_summary.sort_values('Total_Revenue', ascending=False)
port_summary['Pct_Revenue'] = (port_summary['Total_Revenue'] / port_summary['Total_Revenue'].sum() * 100).round(1)

print("\n" + "="*80)
print("TOP 20 PORTS BY REVENUE")
print("="*80)
print(port_summary.head(20))

# ============================================================================
# CREATE SLIDE 1: REGIONAL MARKET OVERVIEW WITH WEIGHTED MAP
# ============================================================================

fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('white')

# Title
fig.text(0.5, 0.95, 'US Agency Market by Region - 2023',
         ha='center', fontsize=28, fontweight='bold', color='#1a1a1a')
fig.text(0.5, 0.915, 'Total Market: $167.7M | 49,726 Port Calls',
         ha='center', fontsize=16, color='#666666')

# Define regional positions for map visualization (approximate US map layout)
region_positions = {
    'North Atlantic': (0.75, 0.65),
    'Mid-Atlantic': (0.73, 0.55),
    'South Atlantic': (0.72, 0.40),
    'Gulf East': (0.60, 0.25),
    'North Texas': (0.50, 0.30),
    'California': (0.20, 0.45),
    'Pacific NW': (0.18, 0.70),
    'Alaska': (0.10, 0.85),
    'Great Lakes': (0.60, 0.70),
}

# Create map subplot
ax_map = plt.subplot2grid((3, 3), (0, 0), colspan=2, rowspan=2, fig=fig)
ax_map.set_xlim(0, 1)
ax_map.set_ylim(0, 1)
ax_map.axis('off')
ax_map.set_title('Revenue Distribution by Region (Bubble size = Revenue)',
                  fontsize=14, fontweight='bold', pad=10)

# Calculate bubble sizes based on revenue
max_revenue = regional_summary['Total_Revenue'].max()
min_bubble = 0.03
max_bubble = 0.12

# Draw regional bubbles
colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(regional_summary)))

for idx, (region, row) in enumerate(regional_summary.iterrows()):
    if region in region_positions:
        x, y = region_positions[region]
        revenue = row['Total_Revenue']
        calls = row['Port_Calls']
        pct_rev = row['Pct_Revenue']

        # Calculate bubble size
        bubble_size = min_bubble + (revenue / max_revenue) * (max_bubble - min_bubble)

        # Draw bubble
        circle = plt.Circle((x, y), bubble_size, color=colors[idx], alpha=0.7,
                           edgecolor='white', linewidth=2, zorder=2)
        ax_map.add_patch(circle)

        # Add revenue text
        ax_map.text(x, y + 0.005, f'${revenue/1e6:.1f}M',
                   ha='center', va='center', fontsize=11, fontweight='bold',
                   color='white', zorder=3,
                   path_effects=[patheffects.withStroke(linewidth=2, foreground='black')])

        # Add region name below
        ax_map.text(x, y - bubble_size - 0.03, region.replace(' ', '\n'),
                   ha='center', va='top', fontsize=8, color='#333333')

        # Add percentage
        ax_map.text(x, y - 0.015, f'{pct_rev}%',
                   ha='center', va='center', fontsize=8,
                   color='white', fontweight='bold', zorder=3,
                   path_effects=[patheffects.withStroke(linewidth=1.5, foreground='black')])

# ============================================================================
# Regional breakdown table
# ============================================================================
ax_table = plt.subplot2grid((3, 3), (0, 2), rowspan=2, fig=fig)
ax_table.axis('off')
ax_table.set_title('Regional Breakdown', fontsize=12, fontweight='bold', pad=10)

# Create table data
table_data = []
for region, row in regional_summary.iterrows():
    table_data.append([
        region,
        f"{int(row['Port_Calls']):,}",
        f"${row['Total_Revenue']/1e6:.1f}M",
        f"{row['Pct_Revenue']:.1f}%"
    ])

table = ax_table.table(cellText=table_data,
                       colLabels=['Region', 'Calls', 'Revenue', '% Rev'],
                       cellLoc='left',
                       loc='upper left',
                       bbox=[0, 0, 1, 1])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.8)

# Style table
for i in range(len(table_data) + 1):
    for j in range(4):
        cell = table[(i, j)]
        if i == 0:
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(weight='bold', color='white')
        else:
            if i % 2 == 0:
                cell.set_facecolor('#f8f9fa')
            else:
                cell.set_facecolor('white')
            cell.set_text_props(color='#333333')

# ============================================================================
# Coast breakdown pie chart
# ============================================================================
ax_pie = plt.subplot2grid((3, 3), (2, 0), colspan=1, fig=fig)
ax_pie.set_title('Revenue by Coast', fontsize=12, fontweight='bold', pad=10)

coast_data = coast_summary['Total_Revenue'].values
coast_labels = [f"{idx}\n${val/1e6:.1f}M\n({coast_summary.loc[idx, 'Pct_Revenue']:.1f}%)"
                for idx, val in zip(coast_summary.index, coast_data)]

colors_coast = ['#3498db', '#e74c3c', '#2ecc71']
wedges, texts = ax_pie.pie(coast_data, labels=coast_labels, colors=colors_coast,
                            startangle=90, textprops={'fontsize': 9, 'weight': 'bold'})

# ============================================================================
# Vessel class by region heatmap
# ============================================================================
ax_heat = plt.subplot2grid((3, 3), (2, 1), colspan=2, fig=fig)
ax_heat.set_title('Top Vessel Classes by Region', fontsize=12, fontweight='bold', pad=10)

# Get top 5 vessel classes
top_vessel_classes = df.groupby('ICST_DESC')['Agency_Fee_Numeric'].sum().nlargest(5).index

# Create pivot for heatmap
heatmap_data = df[df['ICST_DESC'].isin(top_vessel_classes)].groupby(['Port_Region', 'ICST_DESC'])['Agency_Fee_Numeric'].sum().unstack(fill_value=0)

# Filter to regions with data
heatmap_data = heatmap_data.loc[heatmap_data.sum(axis=1) > 0]

# Normalize by row for better visualization
heatmap_data_norm = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100

# Plot heatmap
sns.heatmap(heatmap_data_norm, annot=True, fmt='.0f', cmap='YlOrRd',
            ax=ax_heat, cbar_kws={'label': '% of Regional Revenue'},
            linewidths=0.5, linecolor='white')
ax_heat.set_xlabel('')
ax_heat.set_ylabel('')
ax_heat.tick_params(labelsize=8)

plt.tight_layout(rect=[0, 0.03, 1, 0.9])

# Save slide
output_file = r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\SLIDE_Regional_Market_Analysis.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n[OK] Slide 1 saved: {output_file}")
plt.close()

# ============================================================================
# CREATE SLIDE 2: TOP PORTS WITH GEOGRAPHIC DISTRIBUTION
# ============================================================================

fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('white')

# Title
fig.text(0.5, 0.95, 'Top US Agency Markets by Port - 2023',
         ha='center', fontsize=28, fontweight='bold', color='#1a1a1a')

# Top 15 ports bar chart
ax1 = plt.subplot2grid((2, 2), (0, 0), colspan=2, fig=fig)

top15_ports = port_summary.head(15)
colors_bar = plt.cm.viridis(np.linspace(0.3, 0.9, len(top15_ports)))

bars = ax1.barh(range(len(top15_ports)), top15_ports['Total_Revenue']/1e6, color=colors_bar)
ax1.set_yticks(range(len(top15_ports)))
ax1.set_yticklabels(top15_ports.index, fontsize=10)
ax1.set_xlabel('Revenue ($ Millions)', fontsize=12, fontweight='bold')
ax1.set_title('Top 15 Ports by Agency Fee Revenue', fontsize=14, fontweight='bold', pad=15)
ax1.invert_yaxis()
ax1.grid(axis='x', alpha=0.3, linestyle='--')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, top15_ports['Total_Revenue'])):
    ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f'${val/1e6:.1f}M', va='center', fontsize=9, fontweight='bold')

# Port concentration metrics
ax2 = plt.subplot2grid((2, 2), (1, 0), fig=fig)
ax2.axis('off')

# Calculate concentration
top5_pct = port_summary.head(5)['Total_Revenue'].sum() / port_summary['Total_Revenue'].sum() * 100
top10_pct = port_summary.head(10)['Total_Revenue'].sum() / port_summary['Total_Revenue'].sum() * 100
top20_pct = port_summary.head(20)['Total_Revenue'].sum() / port_summary['Total_Revenue'].sum() * 100

metrics_text = f"""
PORT CONCENTRATION METRICS

• Top 5 Ports: {top5_pct:.1f}% of total revenue
• Top 10 Ports: {top10_pct:.1f}% of total revenue
• Top 20 Ports: {top20_pct:.1f}% of total revenue

Total Ports with Activity: {len(port_summary)}

REGIONAL LEADERS
"""

for region, row in regional_summary.head(5).iterrows():
    top_port = df[df['Port_Region'] == region].groupby('Port_Consolidated')['Agency_Fee_Numeric'].sum().idxmax()
    metrics_text += f"\n• {region}: {top_port}"

ax2.text(0.05, 0.95, metrics_text, transform=ax2.transAxes,
         fontsize=10, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#cccccc', linewidth=2))

# Vessel mix by top ports
ax3 = plt.subplot2grid((2, 2), (1, 1), fig=fig)
ax3.set_title('Vessel Mix - Top 5 Ports', fontsize=12, fontweight='bold', pad=10)

# Get top 5 ports and their vessel mix
top5_ports_list = port_summary.head(5).index.tolist()

vessel_mix_data = df[df['Port_Consolidated'].isin(top5_ports_list)].groupby(['Port_Consolidated', 'ICST_DESC'])['Port_Call_ID'].count().unstack(fill_value=0)

# Get top 6 vessel types
top_vessel_cols = vessel_mix_data.sum().nlargest(6).index
vessel_mix_data = vessel_mix_data[top_vessel_cols]

# Create stacked bar
vessel_mix_data.plot(kind='bar', stacked=True, ax=ax3, colormap='tab10', legend=True)
ax3.set_ylabel('Number of Port Calls', fontsize=10)
ax3.set_xlabel('')
ax3.tick_params(axis='x', rotation=45, labelsize=8)
ax3.legend(title='Vessel Type', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
ax3.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout(rect=[0, 0.03, 1, 0.92])

output_file2 = r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\SLIDE_Top_Ports_Analysis.png'
plt.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
print(f"[OK] Slide 2 saved: {output_file2}")
plt.close()

# ============================================================================
# Export data summaries
# ============================================================================

regional_summary.to_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\regional_market_summary.csv')
coast_summary.to_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\coast_market_summary.csv')
port_summary.to_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\port_market_summary.csv')

print("\n" + "="*80)
print("SLIDES AND DATA EXPORTS COMPLETE")
print("="*80)
print(f"[OK] High-definition slides created at 300 DPI")
print(f"[OK] Regional, coast, and port summaries exported")
print("="*80)
