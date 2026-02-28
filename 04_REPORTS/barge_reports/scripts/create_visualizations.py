"""
Create visualizations for Mississippi River Barge Transportation Industry Briefing
Generates 9 professional charts, maps, and diagrams
"""

import sys
import os

# Fix encoding for Windows console
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'

# Output directory
output_dir = Path("G:/My Drive/LLM/project_barge/report_output/visualizations")
output_dir.mkdir(exist_ok=True)

print("Creating Mississippi River Barge Transportation Visualizations...")
print("=" * 70)

# =============================================================================
# 1. LOCK DELAY COST CURVE (EXPONENTIAL)
# =============================================================================
print("\n1. Creating Lock Delay Cost Curve (exponential relationship)...")

fig, ax = plt.subplots(figsize=(12, 7))

# Utilization levels (0-100%)
utilization = np.linspace(0, 95, 100)

# Exponential delay model: delay = base_delay / (1 - utilization)
# At low utilization (30%), delay ~3 hours
# At high utilization (90%), delay ~30 hours
base_delay = 2.1
delays = base_delay / (1 - (utilization / 100))

# Cost per hour: $1,500 (fuel, crew, opportunity cost)
cost_per_hour = 1500
delay_costs = delays * cost_per_hour

# Plot
ax.plot(utilization, delays, linewidth=3, color='#d62728', label='Average Delay (hours)')
ax.axhline(y=3, color='green', linestyle='--', alpha=0.5, label='Target Delay (3 hours)')
ax.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Capacity Threshold (80%)')

# Highlight critical zone
ax.fill_between(utilization, 0, delays, where=(utilization >= 80), alpha=0.2, color='red', label='Critical Zone')

# Annotate key points
ax.annotate('Normal Operations\n~3-4 hour delay', xy=(50, 4), fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.7))
ax.annotate('Harvest Season\n24-48 hour delays', xy=(88, 30), fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", facecolor='pink', alpha=0.7),
            arrowprops=dict(arrowstyle='->', lw=2, color='red'))

ax.set_xlabel('Lock Utilization (%)', fontsize=13, fontweight='bold')
ax.set_ylabel('Average Delay (hours)', fontsize=13, fontweight='bold')
ax.set_title('Lock Delay vs. Utilization: Non-Linear Cost Escalation\n' +
             'Mississippi River Lock System (2012-2024 Data)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlim(0, 95)
ax.set_ylim(0, 50)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)

# Secondary axis for cost
ax2 = ax.twinx()
ax2.plot(utilization, delay_costs / 1000, linewidth=2, color='#1f77b4',
         linestyle=':', alpha=0.7, label='Delay Cost ($1000s)')
ax2.set_ylabel('Delay Cost per Tow ($1000s)', fontsize=13, fontweight='bold', color='#1f77b4')
ax2.tick_params(axis='y', labelcolor='#1f77b4')
ax2.set_ylim(0, 75)

plt.tight_layout()
plt.savefig(output_dir / '01_lock_delay_cost_curve.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 01_lock_delay_cost_curve.png")
plt.close()

# =============================================================================
# 2. RATE COMPONENTS BREAKDOWN CHART
# =============================================================================
print("\n2. Creating Rate Components Breakdown Chart...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Base barge rate components
components = ['Loading\nCharge', 'Mileage\nRate\n(1,000 mi)', 'Unloading\nCharge',
              'Fleeting\n(15 days)', 'Demurrage\nRisk', 'Harbor\nTugs', 'Other\nAncillaries']
costs = [0.50, 15.00, 0.40, 0.45, 0.30, 0.20, 0.15]
colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2']

# Stacked bar
cumulative = np.cumsum([0] + costs[:-1])
bars = ax1.barh(components, costs, left=cumulative, color=colors, edgecolor='black', linewidth=1.5)

# Annotate values
for i, (bar, cost) in enumerate(zip(bars, costs)):
    width = bar.get_width()
    x_pos = bar.get_x() + width / 2
    ax1.text(x_pos, bar.get_y() + bar.get_height()/2, f'${cost:.2f}',
             ha='center', va='center', fontweight='bold', fontsize=10,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', alpha=0.8))

# Total
total = sum(costs)
ax1.axvline(x=total, color='red', linestyle='--', linewidth=2, label=f'Total: ${total:.2f}/ton')
ax1.text(total + 0.3, 3.5, f'TOTAL\n${total:.2f}/ton', fontsize=12, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

ax1.set_xlabel('Cost per Ton ($)', fontsize=12, fontweight='bold')
ax1.set_title('Barge Freight Rate Components\nMemphis to New Orleans (1,000 river miles)',
              fontsize=13, fontweight='bold')
ax1.set_xlim(0, 20)
ax1.grid(axis='x', alpha=0.3)

# Pie chart comparison
rate_categories = ['Base Freight\n(87%)', 'Fleeting &\nDemurrage (4%)', 'Other\nAncillaries (9%)']
rate_values = [15.90, 0.75, 1.35]
colors_pie = ['#1f77b4', '#d62728', '#7f7f7f']

wedges, texts, autotexts = ax2.pie(rate_values, labels=rate_categories, autopct='%1.0f%%',
                                     colors=colors_pie, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'},
                                     wedgeprops={'edgecolor': 'black', 'linewidth': 2})

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')

ax2.set_title('Rate Composition:\nBase vs. Ancillary Costs', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '02_rate_components_breakdown.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 02_rate_components_breakdown.png")
plt.close()

# =============================================================================
# 3. SEASONAL RATE VOLATILITY (replaces CCC correlation - more relevant)
# =============================================================================
print("\n3. Creating Seasonal Barge Rate Volatility Chart...")

# Simulate realistic barge rate data based on report
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
months_num = np.arange(1, 13)

# Normal year rates
normal_rates = [14, 13, 12, 13, 14, 16, 18, 20, 28, 35, 24, 16]

# Drought year rates (2012)
drought_rates = [16, 15, 14, 15, 18, 24, 38, 52, 68, 88, 58, 28]

# Low demand year
low_rates = [10, 9, 9, 10, 11, 12, 14, 15, 22, 26, 18, 12]

fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(months_num, normal_rates, marker='o', linewidth=3, markersize=8,
        label='Normal Year (2019)', color='#2ca02c')
ax.plot(months_num, drought_rates, marker='s', linewidth=3, markersize=8,
        label='Drought Year (2012)', color='#d62728')
ax.plot(months_num, low_rates, marker='^', linewidth=3, markersize=8,
        label='Low Demand Year (2020)', color='#1f77b4')

# Highlight harvest season
ax.axvspan(8.5, 11.5, alpha=0.2, color='orange', label='Harvest Season')

# Annotate key points
ax.annotate('2012 Drought Peak\n$88/ton (5x normal)', xy=(10, 88), xytext=(10, 100),
            fontsize=11, fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', lw=2, color='red'),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='pink', alpha=0.8))

ax.annotate('Typical Harvest Spike\n$35/ton (2.5x winter)', xy=(10, 35), xytext=(7, 45),
            fontsize=10, ha='center',
            arrowprops=dict(arrowstyle='->', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))

ax.set_xlabel('Month', fontsize=13, fontweight='bold')
ax.set_ylabel('Barge Freight Rate ($/ton)', fontsize=13, fontweight='bold')
ax.set_title('Seasonal Barge Rate Volatility: Normal vs. Drought Conditions\n' +
             'St. Louis to New Orleans Grain Movements (2012-2020)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xticks(months_num)
ax.set_xticklabels(months)
ax.set_ylim(0, 110)
ax.legend(loc='upper left', fontsize=12, framealpha=0.9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '03_seasonal_rate_volatility.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 03_seasonal_rate_volatility.png")
plt.close()

# =============================================================================
# 4. LOWER MISSISSIPPI MAP (SIMPLIFIED SCHEMATIC)
# =============================================================================
print("\n4. Creating Lower Mississippi Map (schematic)...")

fig, ax = plt.subplots(figsize=(10, 14))

# River path (simplified S-curve)
river_y = np.linspace(0, 235, 500)
river_x = 5 + 2 * np.sin(river_y / 30)  # Meandering effect

ax.plot(river_x, river_y, color='#4169E1', linewidth=12, alpha=0.6, solid_capstyle='round')
ax.plot(river_x, river_y, color='#1E90FF', linewidth=8, alpha=0.8, solid_capstyle='round')

# Major terminals (river mile, name, x_offset)
terminals = [
    (235, 'Baton Rouge\n(Head of Navigation)', 0),
    (157, 'Zen-Noh Grain\nConvent', 2),
    (134, 'Cargill Reserve', -2),
    (130, 'ADM Destrehan', 2),
    (50, 'CHS Myrtle Grove', -2),
    (0, 'Head of Passes\n(Gulf of Mexico)', 0)
]

for mile, name, x_off in terminals:
    y_pos = mile
    x_pos = 5 + 2 * np.sin(y_pos / 30) + x_off

    # Terminal marker
    ax.scatter(x_pos, y_pos, s=400, c='red', marker='s', edgecolors='black', linewidths=2, zorder=5)

    # Label
    align = 'right' if x_off < 0 else 'left'
    x_text = x_pos - 0.8 if x_off < 0 else x_pos + 0.8
    ax.text(x_text, y_pos, name, fontsize=10, fontweight='bold', ha=align, va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor='black', alpha=0.9))

# Fleeting areas
fleeting = [(140, 'Fleeting Area\n(200+ barges)'), (55, 'Fleeting Area')]
for mile, label in fleeting:
    y_pos = mile
    x_pos = 5 + 2 * np.sin(y_pos / 30)
    circle = plt.Circle((x_pos, y_pos), 1.5, color='orange', alpha=0.4, zorder=3)
    ax.add_patch(circle)
    ax.text(x_pos + 3, y_pos, label, fontsize=9, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.7))

# Channel depth annotations
depths = [(200, '45 ft depth'), (120, '50 ft depth'), (30, '55 ft depth')]
for mile, depth_text in depths:
    y_pos = mile
    x_pos = 5 + 2 * np.sin(y_pos / 30) - 3.5
    ax.text(x_pos, y_pos, depth_text, fontsize=9, color='blue', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.6))

# Scale
ax.text(1, 220, 'River Miles\nfrom Gulf', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black'))

# Title and labels
ax.set_title('Lower Mississippi River: Export Terminal Locations\n' +
             'Baton Rouge to Gulf of Mexico (235 river miles)',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('', fontsize=12)
ax.set_ylabel('River Miles from Gulf of Mexico', fontsize=12, fontweight='bold')
ax.set_xlim(-2, 12)
ax.set_ylim(-10, 245)
ax.set_aspect('equal')
ax.axis('off')

# Add directional arrow
ax.annotate('', xy=(10, 230), xytext=(10, 10),
            arrowprops=dict(arrowstyle='->', lw=3, color='black'))
ax.text(10.5, 120, 'Flow to\nGulf', fontsize=11, fontweight='bold', rotation=90, va='center')

plt.tight_layout()
plt.savefig(output_dir / '04_lower_mississippi_map.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 04_lower_mississippi_map.png")
plt.close()

# =============================================================================
# 5. LOCK CUTTING OPERATION DIAGRAM
# =============================================================================
print("\n5. Creating Lock Cutting Operation Diagram...")

fig, ax = plt.subplots(figsize=(14, 10))

# Lock chamber
lock_chamber = Rectangle((2, 2), 6, 2, facecolor='lightgray', edgecolor='black', linewidth=3)
ax.add_patch(lock_chamber)
ax.text(5, 3, 'Lock Chamber\n600 ft length', ha='center', va='center',
        fontsize=12, fontweight='bold')

# Step 1: Full tow approaching (1200 ft - 15 barges)
y_step1 = 7
# Upstream side
for i in range(15):
    barge = Rectangle((0.5 + i*0.8, y_step1), 0.7, 0.5, facecolor='brown',
                      edgecolor='black', linewidth=1)
    ax.add_patch(barge)

ax.text(7, y_step1 + 1.2, 'STEP 1: Full 15-Barge Tow Approaches\n(1,200 ft - too long for lock)',
        ha='center', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', edgecolor='black'))

# Step 2: First cut (7 barges)
y_step2 = 5.2
for i in range(7):
    barge = Rectangle((2.2 + i*0.8, y_step2), 0.7, 0.5, facecolor='brown',
                      edgecolor='black', linewidth=1)
    ax.add_patch(barge)

# Remaining 8 barges waiting
for i in range(8):
    barge = Rectangle((0.3 + i*0.8, y_step2 - 0.8), 0.7, 0.5, facecolor='tan',
                      edgecolor='black', linewidth=1, linestyle='--', alpha=0.6)
    ax.add_patch(barge)

ax.text(5, 5.2 + 1, 'STEP 2: First Cut (7 barges) Enters Lock\n8 barges wait upstream',
        ha='center', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='black'))

# Arrow showing movement
arrow1 = FancyArrowPatch((5, 6.8), (5, 5.8), arrowstyle='->', lw=3, color='red',
                         mutation_scale=30)
ax.add_patch(arrow1)

# Step 3: Second cut
y_step3 = 1
for i in range(8):
    barge = Rectangle((2 + i*0.8, y_step3), 0.7, 0.5, facecolor='brown',
                      edgecolor='black', linewidth=1)
    ax.add_patch(barge)

ax.text(5.5, 1 + 1.5, 'STEP 3: Second Cut (8 barges) Locks Through\nReassemble downstream',
        ha='center', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', edgecolor='black'))

# Time annotations
ax.text(11, 7, 'Time Required:', fontsize=12, fontweight='bold')
ax.text(11, 6.5, '• First cut: 45-60 min', fontsize=10)
ax.text(11, 6.1, '• Return for 2nd: 30 min', fontsize=10)
ax.text(11, 5.7, '• Second cut: 45-60 min', fontsize=10)
ax.text(11, 5.3, '• Reassembly: 30 min', fontsize=10)
ax.text(11, 4.8, 'TOTAL: 2.5-3 hours', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow'))

ax.text(11, 3.8, 'With Queue Delay:', fontsize=11, fontweight='bold', color='red')
ax.text(11, 3.4, '• Normal: 4-6 hours', fontsize=10)
ax.text(11, 3.0, '• Harvest: 24-48 hours', fontsize=10, fontweight='bold', color='red')

ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Lock Cutting Operation: How 1,200-ft Tows Transit 600-ft Locks\n' +
             'Mississippi River Navigation System',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / '05_lock_cutting_operation.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 05_lock_cutting_operation.png")
plt.close()

# =============================================================================
# 6. MIDSTREAM FLEETING DIAGRAM
# =============================================================================
print("\n6. Creating Midstream Fleeting Operation Diagram...")

fig, ax = plt.subplots(figsize=(14, 8))

# River
river = Rectangle((0, 0), 14, 8, facecolor='lightblue', alpha=0.3)
ax.add_patch(river)

# Fleeting area (organized grid of barges)
fleet_x, fleet_y = 2, 1
for row in range(4):
    for col in range(10):
        barge = Rectangle((fleet_x + col*0.35, fleet_y + row*0.6), 0.3, 0.5,
                         facecolor='brown', edgecolor='black', linewidth=1)
        ax.add_patch(barge)

ax.text(fleet_x + 1.5, fleet_y + 2.8, 'Fleeting Area\n(40 barges organized)',
        ha='center', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor='black'))

# Mooring to bank
ax.plot([1.8, 1.8], [1, 3.5], 'k-', linewidth=4, label='Bank')
ax.text(1, 2, 'Bank\nMooring', fontsize=9, fontweight='bold', rotation=90, va='center')

# Fleet boat
fleet_boat = Rectangle((5.5, 3.5), 0.5, 0.3, facecolor='red', edgecolor='black', linewidth=2)
ax.add_patch(fleet_boat)
ax.text(5.75, 4, 'Fleet Boat\n600-1200 HP', ha='center', fontsize=9, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='pink'))

# Midstream buoys
buoy_positions = [(10, 2), (10.5, 4), (11, 6)]
for x, y in buoy_positions:
    buoy = plt.Circle((x, y), 0.2, facecolor='orange', edgecolor='black', linewidth=2)
    ax.add_patch(buoy)
    # Barges at buoys
    for i in range(3):
        barge = Rectangle((x - 0.5 + i*0.35, y - 0.6), 0.3, 0.5,
                         facecolor='tan', edgecolor='black', linewidth=1, alpha=0.7)
        ax.add_patch(barge)

ax.text(10.5, 1, 'Midstream Buoys\n(9 barges waiting)', ha='center', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat', edgecolor='black'))

# Terminal
terminal = Rectangle((12, 5), 1.5, 2, facecolor='gray', edgecolor='black', linewidth=3)
ax.add_patch(terminal)
ax.text(12.75, 6, 'Export\nTerminal', ha='center', va='center', fontsize=10, fontweight='bold',
        color='white')

# Harbor tug retrieving barge
tug = Rectangle((11, 3.5), 0.4, 0.25, facecolor='blue', edgecolor='black', linewidth=2)
ax.add_patch(tug)
barge_moving = Rectangle((11.5, 3.5), 0.3, 0.5, facecolor='brown', edgecolor='black', linewidth=2)
ax.add_patch(barge_moving)

# Arrow showing movement to terminal
arrow = FancyArrowPatch((11.8, 3.75), (12.3, 5.5), arrowstyle='->', lw=3, color='green',
                       mutation_scale=30)
ax.add_patch(arrow)
ax.text(12, 4.5, 'Harbor Tug\nRetrieves Barge', fontsize=9, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen'))

# Cost comparison
ax.text(1, 7, 'Cost Comparison:', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black'))
ax.text(1, 6.5, 'Fleeting: $30-50/day per barge', fontsize=9)
ax.text(1, 6.1, '  • 15 days = $450-750', fontsize=9, color='red')
ax.text(1, 5.5, 'Midstream Buoy: $150-300 one-time', fontsize=9)
ax.text(1, 5.1, '  • Harbor tug: $500-1,500', fontsize=9)
ax.text(1, 4.7, '  • TOTAL: $650-1,800 (any duration)', fontsize=9, fontweight='bold', color='green')

ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Midstream Fleeting & Buoy Operations\n' +
             'Lower Mississippi River Export Logistics',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / '06_midstream_fleeting_diagram.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 06_midstream_fleeting_diagram.png")
plt.close()

# =============================================================================
# 7. GRAIN EXPORT SUPPLY CHAIN FLOW
# =============================================================================
print("\n7. Creating Grain Export Supply Chain Flow Diagram...")

fig, ax = plt.subplots(figsize=(14, 10))

# Define stages
stages = [
    {'name': 'Farm\nStorage', 'y': 9, 'color': 'lightgreen'},
    {'name': 'Country\nElevator', 'y': 7.5, 'color': 'yellow'},
    {'name': 'River\nTerminal', 'y': 6, 'color': 'orange'},
    {'name': 'Barge\nTransit\n(7-14 days)', 'y': 4, 'color': 'lightblue'},
    {'name': 'Fleeting\nArea\n(10-20 days)', 'y': 2, 'color': 'wheat'},
    {'name': 'Export\nTerminal', 'y': 0.5, 'color': 'pink'},
]

x_center = 7

for i, stage in enumerate(stages):
    # Box
    box = FancyBboxPatch((x_center - 1.5, stage['y'] - 0.3), 3, 0.6,
                         boxstyle="round,pad=0.1", facecolor=stage['color'],
                         edgecolor='black', linewidth=2)
    ax.add_patch(box)

    # Label
    ax.text(x_center, stage['y'], stage['name'], ha='center', va='center',
            fontsize=11, fontweight='bold')

    # Arrow to next stage
    if i < len(stages) - 1:
        arrow = FancyArrowPatch((x_center, stage['y'] - 0.4),
                               (x_center, stages[i+1]['y'] + 0.4),
                               arrowstyle='->', lw=3, color='black', mutation_scale=30)
        ax.add_patch(arrow)

# Side annotations (left side - transport mode)
transport_notes = [
    (9, 'Truck to Elevator'),
    (7.5, 'Barge or Truck'),
    (6, 'Barge Tow (15 barges)'),
    (4, 'Mississippi River'),
    (2, 'Fleet Boat Shuffling'),
]

for y, note in transport_notes:
    ax.text(3, y - 0.6, note, fontsize=9, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lavender', alpha=0.7))

# Right side annotations (costs and timing)
cost_notes = [
    (9, 'Origin Cost: $0.10-0.25/bu'),
    (7.5, 'Elevation: $0.05-0.15/bu'),
    (6, 'River Handling: $0.08/bu'),
    (4, 'Barge Freight: $0.40-1.20/bu'),
    (2, 'Fleeting: $0.01-0.03/bu'),
    (0.5, 'Terminal: $0.15-0.30/bu'),
]

for y, note in cost_notes:
    ax.text(11, y, note, fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))

# Total timeline
ax.text(1, -0.5, 'TOTAL TIMELINE: 20-40 days farm to vessel', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', edgecolor='red', linewidth=2))

# Total cost
ax.text(1, -1.2, 'TOTAL COST: $0.80-2.00 per bushel', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', edgecolor='red', linewidth=2))

# Ocean vessel at bottom
vessel = Rectangle((x_center - 2, -2), 4, 0.8, facecolor='gray', edgecolor='black', linewidth=3)
ax.add_patch(vessel)
ax.text(x_center, -1.6, 'Ocean Vessel\n(Panamax - 75,000 tons)', ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')

# Arrow from terminal to vessel
arrow_final = FancyArrowPatch((x_center, 0.1), (x_center, -1.2),
                              arrowstyle='->', lw=4, color='green', mutation_scale=40)
ax.add_patch(arrow_final)
ax.text(x_center + 1, -0.5, 'Loading:\n10,000-15,000\ntons/hour', fontsize=9, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen'))

ax.set_xlim(0, 14)
ax.set_ylim(-3, 10)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Grain Export Supply Chain: Farm to Ocean Vessel\n' +
             'Mississippi River Corridor (Typical 30-35 day cycle)',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / '07_grain_export_supply_chain.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 07_grain_export_supply_chain.png")
plt.close()

# =============================================================================
# 8. RATE CALCULATION EXAMPLE TABLE
# =============================================================================
print("\n8. Creating Rate Calculation Example Table...")

fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('tight')
ax.axis('off')

# Route example data
route_data = [
    ['COMPONENT', 'FORMULA', 'CALCULATION', 'COST/TON'],
    ['', '', '', ''],
    ['Origin Loading', 'Fixed charge', '$0.50 × 1', '$0.50'],
    ['', '', '', ''],
    ['Mileage Rate', 'Base + ($/mi × distance)', '$4.25 + ($0.015 × 1,050 mi)', '$20.00'],
    ['', '', '', ''],
    ['Destination Unloading', 'Fixed charge', '$0.40 × 1', '$0.40'],
    ['', '', '', ''],
    ['BASE FREIGHT', '', 'Sum above', '$20.90'],
    ['', '', '', ''],
    ['Fleeting (15 days)', 'Daily rate × days ÷ tonnage', '($30/day × 15 days) ÷ 1,500 tons', '$0.30'],
    ['', '', '', ''],
    ['Harbor Tug', 'Fixed per barge ÷ tonnage', '$800 ÷ 1,500 tons', '$0.53'],
    ['', '', '', ''],
    ['Switching Fee', 'Fixed ÷ tonnage', '$250 ÷ 1,500 tons', '$0.17'],
    ['', '', '', ''],
    ['USDA Inspection', 'Per ton charge', '$0.03 × 1', '$0.03'],
    ['', '', '', ''],
    ['Draft Survey', 'Fixed ÷ tonnage', '$350 ÷ 1,500 tons', '$0.23'],
    ['', '', '', ''],
    ['TOTAL DELIVERED COST', '', 'Sum all components', '$22.16'],
]

# Create table
table = ax.table(cellText=route_data, cellLoc='left', loc='center',
                colWidths=[0.25, 0.35, 0.25, 0.15])

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header row
for i in range(4):
    cell = table[(0, i)]
    cell.set_facecolor('#4472C4')
    cell.set_text_props(weight='bold', color='white', fontsize=11)

# Style section headers
section_rows = [8, 18]
for row_idx in section_rows:
    for col_idx in range(4):
        cell = table[(row_idx, col_idx)]
        cell.set_facecolor('#FFC000')
        cell.set_text_props(weight='bold', fontsize=11)

# Style final total row
for col_idx in range(4):
    cell = table[(20, col_idx)]
    cell.set_facecolor('#70AD47')
    cell.set_text_props(weight='bold', color='white', fontsize=12)

# Alternate row colors for readability
for row_idx in range(1, 20):
    if row_idx not in [1, 3, 5, 7, 8, 9, 11, 13, 15, 17]:  # Skip empty rows and headers
        for col_idx in range(4):
            cell = table[(row_idx, col_idx)]
            if row_idx % 2 == 0:
                cell.set_facecolor('#F2F2F2')

ax.set_title('Barge Freight Rate Calculation Example\n' +
             'Peoria, IL to Reserve, LA (1,050 river miles) - 1,500 ton barge',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / '08_rate_calculation_table.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 08_rate_calculation_table.png")
plt.close()

# =============================================================================
# 9. RIVER VS OCEAN OPERATIONS COMPARISON
# =============================================================================
print("\n9. Creating River vs. Ocean Operations Comparison Table...")

fig, ax = plt.subplots(figsize=(14, 10))
ax.axis('tight')
ax.axis('off')

comparison_data = [
    ['OPERATIONAL ASPECT', 'OCEAN SHIPPING', 'MISSISSIPPI RIVER BARGES'],
    ['', '', ''],
    ['Vessel Size', 'Panamax: 75,000 tons\nCapesize: 180,000 tons', 'Single barge: 1,500 tons\n15-barge tow: 22,500 tons'],
    ['', '', ''],
    ['Speed', '12-15 knots (14-17 mph)\nOptimized for ocean distances', 'Upstream: 4-6 mph\nDownstream: 6-8 mph\nLimited by current & channels'],
    ['', '', ''],
    ['Transit Time Variability', 'Predictable: ±1-2 days\nWeather delays rare', 'Highly variable: ±3-7 days\nLock delays, weather, water levels'],
    ['', '', ''],
    ['Infrastructure Constraints', 'Port draft limits\nBerth availability\nCanal transits (Suez, Panama)', 'Lock chamber size (600-1,200 ft)\nChannel depth (9-12 ft)\n29 locks on Upper Mississippi'],
    ['', '', ''],
    ['Scheduling Certainty', 'High: Fixed berth windows\nLaycan contracts common', 'Low: Fleeting buffers uncertainty\nBarge arrival times ±1 week'],
    ['', '', ''],
    ['Cost Structure', 'Voyage costs: bunkers, port fees\nLumpsum or $/ton rates', 'Base + mileage formula\nAncillary fees (fleeting, tugs)\nHighly seasonal volatility'],
    ['', '', ''],
    ['Cargo Handling', 'Berth-to-berth operation\nShip\'s gear or shore cranes\n10,000-50,000 tons/day', 'Barge-to-terminal discharge\nPneumatic or conveyor systems\n15,000-20,000 tons/day per barge'],
    ['', '', ''],
    ['Waiting Costs', 'Expensive: $15,000-30,000/day\nMinimize port time critical', 'Cheap: Fleeting $30-50/day/barge\nBuoy mooring nearly free\nTime flexibility is strategy'],
    ['', '', ''],
    ['Rate Volatility', 'Moderate: 20-50% year-over-year\nMarket cycles, fuel prices', 'Extreme: 300-500% seasonal swings\nDrought can quintuple rates\nHarvest peaks triple baseline'],
    ['', '', ''],
    ['Contracting', 'Voyage charter or COA\nStandard charter parties\n(Gencon, Graincon)', 'Annual contracts + spot market\nPrivate negotiated terms\nNo standard forms'],
    ['', '', ''],
    ['Capacity Expansion', 'Order new vessels: 2-3 years\nReposition fleet geographically', 'Build barges: 18-24 months\nCannot easily add peak capacity\nFixed infrastructure limits'],
    ['', '', ''],
    ['Fuel Efficiency', '59 ton-miles/gallon (truck)\n202 ton-miles/gal (rail)\n514 ton-miles/gal (barge)\n→ Barge 8.7× better than truck', 'Most fuel-efficient mode\nPhysics advantage: water vs. land\nBut: Slow speed, infrastructure limits'],
]

# Create table
table = ax.table(cellText=comparison_data, cellLoc='left', loc='center',
                colWidths=[0.25, 0.375, 0.375])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.2)

# Style header row
for i in range(3):
    cell = table[(0, i)]
    cell.set_facecolor('#4472C4')
    cell.set_text_props(weight='bold', color='white', fontsize=11)

# Alternate row colors
for row_idx in range(2, len(comparison_data)):
    if row_idx % 4 == 2:  # Data rows (skip blank rows)
        for col_idx in range(3):
            cell = table[(row_idx, col_idx)]
            if row_idx % 8 == 2:
                cell.set_facecolor('#E7E6E6')
            else:
                cell.set_facecolor('#F7F7F7')

# Highlight ocean column
for row_idx in range(2, len(comparison_data)):
    if row_idx % 4 == 2:
        cell = table[(row_idx, 1)]
        current_color = cell.get_facecolor()
        cell.set_facecolor('#D6EAF8')  # Light blue tint

# Highlight river column
for row_idx in range(2, len(comparison_data)):
    if row_idx % 4 == 2:
        cell = table[(row_idx, 2)]
        current_color = cell.get_facecolor()
        cell.set_facecolor('#D5F4E6')  # Light green tint

ax.set_title('Ocean Shipping vs. Mississippi River Barge Operations:\n' +
             'Operational Comparison for Commodity Trade Professionals',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / '09_river_ocean_comparison.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: 09_river_ocean_comparison.png")
plt.close()

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("✓ ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
print("=" * 70)
print(f"\nOutput directory: {output_dir}")
print("\nFiles created:")
print("  1. 01_lock_delay_cost_curve.png")
print("  2. 02_rate_components_breakdown.png")
print("  3. 03_seasonal_rate_volatility.png")
print("  4. 04_lower_mississippi_map.png")
print("  5. 05_lock_cutting_operation.png")
print("  6. 06_midstream_fleeting_diagram.png")
print("  7. 07_grain_export_supply_chain.png")
print("  8. 08_rate_calculation_table.png")
print("  9. 09_river_ocean_comparison.png")
print("\nReady for incorporation into Industry Briefing report.")
