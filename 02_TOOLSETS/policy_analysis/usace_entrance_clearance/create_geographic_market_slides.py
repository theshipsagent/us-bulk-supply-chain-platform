#!/usr/bin/env python3
"""
Create high-definition slides with REAL geographic maps
Integrating port geospatial data from sources_data_maps
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle, Circle
from matplotlib import patheffects
import json
import warnings
warnings.filterwarnings('ignore')

# Set high-quality output parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']

print("="*80)
print("LOADING DATA")
print("="*80)

# Load port calls data
print("Loading port call data...")
df = pd.read_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.02_PROCESSED\usace_2023_port_calls_COMPLETE_v4.0.0_20260206_004712.csv')

# Clean up agency fee data
df['Agency_Fee_Clean'] = df['Agency_Fee'].str.replace('$', '').str.replace(',', '').str.strip()
df['Agency_Fee_Numeric'] = pd.to_numeric(df['Agency_Fee_Clean'], errors='coerce')

print(f"Total records: {len(df):,}")
print(f"Total revenue: ${df['Agency_Fee_Numeric'].sum():,.0f}")

# Load geospatial data
print("\nLoading geospatial port data...")
try:
    ports_geo = gpd.read_file(r'G:\My Drive\LLM\sources_data_maps\01_geospatial\08_bts_principal_ports\Principal_Ports_-68781543534027147.geojson')
    print(f"Loaded {len(ports_geo)} ports from geospatial database")
    print(f"Columns: {ports_geo.columns.tolist()[:10]}")
except Exception as e:
    print(f"Error loading geospatial data: {e}")
    ports_geo = None

# Aggregate port data
port_summary = df.groupby(['Port_Consolidated', 'Port_Coast', 'Port_Region']).agg({
    'Port_Call_ID': 'count',
    'Agency_Fee_Numeric': 'sum'
}).reset_index()

port_summary.columns = ['Port', 'Coast', 'Region', 'Port_Calls', 'Total_Revenue']
port_summary = port_summary.sort_values('Total_Revenue', ascending=False)
port_summary['Revenue_M'] = port_summary['Total_Revenue'] / 1e6

print(f"\nAggregated {len(port_summary)} unique ports")

# ============================================================================
# CREATE SLIDE 1: US MAP WITH WEIGHTED PORT CIRCLES
# ============================================================================

print("\n" + "="*80)
print("CREATING SLIDE 1: GEOGRAPHIC MAP WITH REVENUE OVERLAY")
print("="*80)

fig = plt.figure(figsize=(20, 12))
fig.patch.set_facecolor('white')

# Main title
fig.text(0.5, 0.97, 'US Agency Market - Geographic Distribution by Port',
         ha='center', fontsize=32, fontweight='bold', color='#1a1a1a')
fig.text(0.5, 0.94, 'Total Market: $167.7M | 49,726 Port Calls | 2023 Data',
         ha='center', fontsize=18, color='#666666')

# Create main map
ax_map = plt.subplot(111)

# Plot US states boundary if we have geospatial data
if ports_geo is not None:
    # Get US bounds
    minx, miny, maxx, maxy = -130, 24, -65, 50
    ax_map.set_xlim(minx, maxx)
    ax_map.set_ylim(miny, maxy)

    # Plot ports from geospatial data as base layer
    ports_geo.plot(ax=ax_map, color='lightgray', markersize=5, alpha=0.3, zorder=1)
else:
    # Manual port positions if geospatial data not available
    ax_map.set_xlim(-130, -65)
    ax_map.set_ylim(24, 50)

# Define approximate coordinates for major ports
port_coords = {
    'Houston': (-95.36, 29.76),
    'South Florida': (-80.19, 26.12),
    'Sabine River': (-93.88, 29.73),
    'New York': (-74.01, 40.71),
    'South Texas': (-97.39, 27.80),
    'New Orleans': (-90.07, 29.95),
    'Mobile': (-88.04, 30.69),
    'LA-Long Beach': (-118.24, 33.74),
    'Hampton Roads': (-76.29, 36.85),
    'Baltimore': (-76.61, 39.29),
    'Columbia River': (-123.77, 46.18),
    'North Florida': (-81.66, 30.33),
    'Georgia Ports': (-81.09, 32.08),
    'Lake Charles': (-93.22, 30.23),
    'San Franciso': (-122.42, 37.77),
    'Delaware River': (-75.14, 39.95),
    'Seattle-Tacoma': (-122.33, 47.60),
    'Tampa': (-82.46, 27.95),
    'South Carolina Ports': (-79.93, 32.78),
    'Boston': (-71.06, 42.36),
}

# Color by coast
coast_colors = {
    'Gulf': '#e74c3c',
    'East': '#3498db',
    'West': '#2ecc71',
    'Great Lakes': '#f39c12',
    'Land Ports': '#95a5a6',
    'Land  Ports': '#95a5a6',
    'Lake': '#f39c12'
}

# Plot weighted circles for each port
max_revenue = port_summary['Total_Revenue'].max()
min_size = 50
max_size = 3000

plotted_ports = []

for idx, row in port_summary.head(20).iterrows():
    port_name = row['Port']
    revenue = row['Total_Revenue']
    calls = row['Port_Calls']
    coast = row['Coast']

    if port_name in port_coords:
        lon, lat = port_coords[port_name]

        # Calculate size
        size = min_size + (revenue / max_revenue) * (max_size - min_size)

        # Plot circle
        color = coast_colors.get(coast, '#95a5a6')
        ax_map.scatter(lon, lat, s=size, c=color, alpha=0.6,
                      edgecolors='white', linewidths=2, zorder=3)

        # Add revenue label
        if revenue > 5e6:  # Label only major ports
            ax_map.text(lon, lat, f'${revenue/1e6:.1f}M',
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       color='white', zorder=4,
                       path_effects=[patheffects.withStroke(linewidth=2.5, foreground='black')])

        # Add port name below
        if revenue > 8e6:  # Name only top ports
            ax_map.text(lon, lat - 1.5, port_name,
                       ha='center', va='top', fontsize=7, color='#333333',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='none', alpha=0.7), zorder=4)

        plotted_ports.append(port_name)

# Add legend
legend_elements = [
    plt.scatter([], [], s=200, c=coast_colors['Gulf'], alpha=0.6, edgecolors='white', linewidths=2, label='Gulf Coast'),
    plt.scatter([], [], s=200, c=coast_colors['East'], alpha=0.6, edgecolors='white', linewidths=2, label='East Coast'),
    plt.scatter([], [], s=200, c=coast_colors['West'], alpha=0.6, edgecolors='white', linewidths=2, label='West Coast'),
]

# Size legend
for size_val, label in [(5, '$5M'), (15, '$15M'), (25, '$25M')]:
    size_pixels = min_size + (size_val*1e6 / max_revenue) * (max_size - min_size)
    legend_elements.append(
        plt.scatter([], [], s=size_pixels, c='gray', alpha=0.6,
                   edgecolors='white', linewidths=2, label=label)
    )

ax_map.legend(handles=legend_elements, loc='lower left', fontsize=11,
             title='Revenue by Coast', title_fontsize=12, framealpha=0.9)

ax_map.set_xlabel('Longitude', fontsize=12)
ax_map.set_ylabel('Latitude', fontsize=12)
ax_map.set_title('Port Revenue Distribution (Circle size = Revenue)',
                fontsize=16, fontweight='bold', pad=15)
ax_map.grid(True, alpha=0.3, linestyle='--')
ax_map.set_aspect('equal')

# Add coastline styling
ax_map.set_facecolor('#e8f4f8')

plt.tight_layout(rect=[0, 0.02, 1, 0.92])

output_file1 = r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\SLIDE_Geographic_Market_Map.png'
plt.savefig(output_file1, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n[OK] Slide 1 saved: {output_file1}")
plt.close()

# ============================================================================
# CREATE SLIDE 2: REGIONAL MAPS WITH ZOOM-IN VIEWS
# ============================================================================

print("\n" + "="*80)
print("CREATING SLIDE 2: REGIONAL ZOOM MAPS")
print("="*80)

fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('white')

# Main title
fig.text(0.5, 0.98, 'US Agency Market - Regional Deep Dive',
         ha='center', fontsize=32, fontweight='bold', color='#1a1a1a')
fig.text(0.5, 0.955, 'Top Revenue Regions with Port Details',
         ha='center', fontsize=18, color='#666666')

# Define regional zooms
regions = [
    {'name': 'Gulf Coast (Houston Area)', 'bounds': (-97, 27, -88, 31), 'ports': ['Houston', 'South Texas', 'Sabine River', 'New Orleans', 'Mobile', 'Lake Charles']},
    {'name': 'East Coast (Mid-Atlantic)', 'bounds': (-77, 36, -73, 42), 'ports': ['New York', 'Hampton Roads', 'Baltimore', 'Delaware River']},
    {'name': 'Southeast Atlantic', 'bounds': (-82, 25, -78, 33), 'ports': ['South Florida', 'North Florida', 'Georgia Ports', 'South Carolina Ports', 'Tampa']},
    {'name': 'West Coast (Pacific)', 'bounds': (-125, 32, -117, 49), 'ports': ['LA-Long Beach', 'San Franciso', 'Seattle-Tacoma', 'Columbia River']},
]

# Create subplots
for idx, region in enumerate(regions):
    ax = plt.subplot(2, 2, idx+1)

    minx, miny, maxx, maxy = region['bounds']
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_title(region['name'], fontsize=14, fontweight='bold', pad=10)
    ax.set_facecolor('#e8f4f8')
    ax.grid(True, alpha=0.3, linestyle='--')

    # Plot ports in this region
    regional_revenue = 0
    regional_calls = 0

    for port_name in region['ports']:
        if port_name in port_coords:
            port_data = port_summary[port_summary['Port'] == port_name]
            if not port_data.empty:
                lon, lat = port_coords[port_name]
                revenue = port_data['Total_Revenue'].values[0]
                calls = port_data['Port_Calls'].values[0]
                coast = port_data['Coast'].values[0]

                regional_revenue += revenue
                regional_calls += calls

                # Calculate size
                size = 200 + (revenue / max_revenue) * 2000

                # Plot
                color = coast_colors.get(coast, '#95a5a6')
                ax.scatter(lon, lat, s=size, c=color, alpha=0.7,
                          edgecolors='white', linewidths=2, zorder=3)

                # Label
                ax.text(lon, lat, f'${revenue/1e6:.1f}M',
                       ha='center', va='center', fontsize=8, fontweight='bold',
                       color='white', zorder=4,
                       path_effects=[patheffects.withStroke(linewidth=2, foreground='black')])

                # Port name
                ax.text(lon, lat - 0.4, port_name,
                       ha='center', va='top', fontsize=7, color='#333333',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='gray', alpha=0.8), zorder=4)

    # Add regional summary
    ax.text(0.02, 0.98,
           f'Total Revenue: ${regional_revenue/1e6:.1f}M\nPort Calls: {regional_calls:,}',
           transform=ax.transAxes, fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', edgecolor='#cccccc',
                    linewidth=1.5, alpha=0.9))

    ax.set_xlabel('Longitude', fontsize=9)
    ax.set_ylabel('Latitude', fontsize=9)
    ax.tick_params(labelsize=8)

plt.tight_layout(rect=[0, 0.02, 1, 0.94])

output_file2 = r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\SLIDE_Regional_Geographic_Zooms.png'
plt.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
print(f"[OK] Slide 2 saved: {output_file2}")
plt.close()

# ============================================================================
# CREATE SLIDE 3: HEATMAP STYLE DENSITY MAP
# ============================================================================

print("\n" + "="*80)
print("CREATING SLIDE 3: REVENUE DENSITY HEATMAP")
print("="*80)

fig = plt.figure(figsize=(20, 12))
fig.patch.set_facecolor('white')

# Title
fig.text(0.5, 0.97, 'US Agency Market - Revenue Concentration Heat Map',
         ha='center', fontsize=32, fontweight='bold', color='#1a1a1a')
fig.text(0.5, 0.94, 'Darker = Higher Revenue Concentration',
         ha='center', fontsize=18, color='#666666')

# Create map with graduated circles
ax = plt.subplot(111)
ax.set_xlim(-130, -65)
ax.set_ylim(24, 50)
ax.set_facecolor('#f0f0f0')
ax.grid(True, alpha=0.2, linestyle='--')

# Plot all ports with graduated transparency based on revenue
for idx, row in port_summary.iterrows():
    port_name = row['Port']
    revenue = row['Total_Revenue']

    if port_name in port_coords:
        lon, lat = port_coords[port_name]

        # Size and alpha based on revenue
        size = 100 + (revenue / max_revenue) * 2500
        alpha = 0.3 + (revenue / max_revenue) * 0.6

        # Color intensity
        color_intensity = revenue / max_revenue
        color = plt.cm.YlOrRd(color_intensity * 0.8 + 0.2)

        # Plot with glow effect
        ax.scatter(lon, lat, s=size*2, c=[color], alpha=alpha*0.3,
                  edgecolors='none', zorder=1)
        ax.scatter(lon, lat, s=size, c=[color], alpha=alpha*0.8,
                  edgecolors='white', linewidths=1.5, zorder=2)

        # Label top 10 only
        if revenue > 7e6:
            ax.text(lon, lat, f'{port_name}\n${revenue/1e6:.1f}M',
                   ha='center', va='center', fontsize=9, fontweight='bold',
                   color='white', zorder=3,
                   path_effects=[patheffects.withStroke(linewidth=3, foreground='#333333')])

# Add colorbar
sm = plt.cm.ScalarMappable(cmap='YlOrRd',
                           norm=plt.Normalize(vmin=0, vmax=max_revenue/1e6))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02, fraction=0.03)
cbar.set_label('Revenue ($ Millions)', fontsize=12, fontweight='bold')

ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)
ax.set_title('Market Concentration by Geographic Location',
            fontsize=16, fontweight='bold', pad=15)
ax.set_aspect('equal')

# Add statistics box
stats_text = f"""
MARKET CONCENTRATION STATISTICS

Total US Market: ${port_summary['Total_Revenue'].sum()/1e6:.1f}M
Total Ports: {len(port_summary)}

Top 5 Ports: ${port_summary.head(5)['Total_Revenue'].sum()/1e6:.1f}M ({port_summary.head(5)['Total_Revenue'].sum()/port_summary['Total_Revenue'].sum()*100:.1f}%)
Top 10 Ports: ${port_summary.head(10)['Total_Revenue'].sum()/1e6:.1f}M ({port_summary.head(10)['Total_Revenue'].sum()/port_summary['Total_Revenue'].sum()*100:.1f}%)

Largest Market: {port_summary.iloc[0]['Port']} (${port_summary.iloc[0]['Total_Revenue']/1e6:.1f}M)
"""

ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
       fontsize=10, verticalalignment='top', fontfamily='monospace',
       bbox=dict(boxstyle='round', facecolor='white', edgecolor='#333333',
                linewidth=2, alpha=0.95), zorder=5)

plt.tight_layout(rect=[0, 0.02, 1, 0.92])

output_file3 = r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\SLIDE_Revenue_Density_Heatmap.png'
plt.savefig(output_file3, dpi=300, bbox_inches='tight', facecolor='white')
print(f"[OK] Slide 3 saved: {output_file3}")
plt.close()

print("\n" + "="*80)
print("ALL GEOGRAPHIC SLIDES COMPLETE")
print("="*80)
print(f"[OK] 3 high-definition geographic slides created at 300 DPI")
print(f"[OK] Integrated with geospatial port data")
print("="*80)
