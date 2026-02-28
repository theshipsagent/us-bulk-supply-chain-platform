#!/usr/bin/env python3
"""
Quick market analysis by vessel class and anticipated revenue
Analyzes 2023 USACE port call data with agency fees
"""

import pandas as pd
import numpy as np

# Read the port calls data
print("Loading port call data...")
df = pd.read_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.02_PROCESSED\usace_2023_port_calls_COMPLETE_v4.0.0_20260206_004712.csv')

print(f"Total records: {len(df):,}")
print(f"\nColumns available: {df.columns.tolist()}\n")

# Clean up agency fee data - remove dollar signs and commas, convert to numeric
df['Agency_Fee_Clean'] = df['Agency_Fee'].str.replace('$', '').str.replace(',', '').str.strip()
df['Agency_Fee_Numeric'] = pd.to_numeric(df['Agency_Fee_Clean'], errors='coerce')

# Group by vessel class (ICST_DESC)
print("="*80)
print("US AGENCY MARKET SUMMARY BY VESSEL CLASS - 2023")
print("="*80)

vessel_summary = df.groupby('ICST_DESC').agg({
    'Port_Call_ID': 'count',  # Number of port calls
    'Agency_Fee_Numeric': 'sum',  # Total revenue
    'NRT': 'mean',  # Average NRT
    'GRT': 'mean',  # Average GRT
    'Ships_DWT': 'mean'  # Average DWT
}).round(0)

vessel_summary.columns = ['Port_Calls', 'Total_Revenue', 'Avg_NRT', 'Avg_GRT', 'Avg_DWT']
vessel_summary = vessel_summary.sort_values('Total_Revenue', ascending=False)

# Add percentage of total revenue
total_revenue = vessel_summary['Total_Revenue'].sum()
vessel_summary['Pct_Revenue'] = (vessel_summary['Total_Revenue'] / total_revenue * 100).round(1)

# Add percentage of total calls
total_calls = vessel_summary['Port_Calls'].sum()
vessel_summary['Pct_Calls'] = (vessel_summary['Port_Calls'] / total_calls * 100).round(1)

# Format for display
vessel_summary['Total_Revenue'] = vessel_summary['Total_Revenue'].apply(lambda x: f"${x:,.0f}")
vessel_summary['Port_Calls'] = vessel_summary['Port_Calls'].astype(int)
vessel_summary['Avg_NRT'] = vessel_summary['Avg_NRT'].astype(int)
vessel_summary['Avg_GRT'] = vessel_summary['Avg_GRT'].astype(int)
vessel_summary['Avg_DWT'] = vessel_summary['Avg_DWT'].astype(int)

print("\n")
print(vessel_summary.to_string())
print("\n")
print("="*80)
print(f"TOTAL PORT CALLS: {total_calls:,}")
print(f"TOTAL REVENUE: ${total_revenue:,.0f}")
print("="*80)

# Top 10 vessel classes by revenue
print("\n\nTOP 10 VESSEL CLASSES BY REVENUE:")
print("-"*80)
top10 = vessel_summary.head(10)[['Port_Calls', 'Total_Revenue', 'Pct_Revenue', 'Pct_Calls']]
print(top10.to_string())

# Group into major categories for executive summary
print("\n\n")
print("="*80)
print("EXECUTIVE SUMMARY - VESSEL CATEGORIES")
print("="*80)

# Categorize vessel types
def categorize_vessel(icst_desc):
    icst_desc = str(icst_desc).upper()
    if 'CONTAINER' in icst_desc:
        return 'CONTAINER'
    elif 'BULK' in icst_desc and 'TANKER' not in icst_desc:
        return 'BULK CARRIER'
    elif 'TANKER' in icst_desc or 'OIL' in icst_desc or 'CRUDE' in icst_desc:
        return 'TANKER (Oil/Crude)'
    elif 'CHEMICAL' in icst_desc:
        return 'CHEMICAL TANKER'
    elif 'LNG' in icst_desc or 'LPG' in icst_desc or 'GAS' in icst_desc:
        return 'GAS CARRIER'
    elif 'REEFER' in icst_desc:
        return 'REEFER'
    elif 'RO-RO' in icst_desc or 'VEHICLE' in icst_desc:
        return 'RO-RO/VEHICLE'
    elif 'CRUISE' in icst_desc or 'PASSENGER' in icst_desc:
        return 'PASSENGER/CRUISE'
    elif 'TUG' in icst_desc or 'PUSH' in icst_desc:
        return 'TUG/PUSH'
    elif 'BARGE' in icst_desc:
        return 'BARGE'
    elif 'GENERAL CARGO' in icst_desc:
        return 'GENERAL CARGO'
    else:
        return 'OTHER'

# Re-read for clean analysis
df2 = pd.read_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.02_PROCESSED\usace_2023_port_calls_COMPLETE_v4.0.0_20260206_004712.csv')
df2['Agency_Fee_Clean'] = df2['Agency_Fee'].str.replace('$', '').str.replace(',', '').str.strip()
df2['Agency_Fee_Numeric'] = pd.to_numeric(df2['Agency_Fee_Clean'], errors='coerce')
df2['Vessel_Category'] = df2['ICST_DESC'].apply(categorize_vessel)

category_summary = df2.groupby('Vessel_Category').agg({
    'Port_Call_ID': 'count',
    'Agency_Fee_Numeric': 'sum'
}).round(0)

category_summary.columns = ['Port_Calls', 'Total_Revenue']
category_summary = category_summary.sort_values('Total_Revenue', ascending=False)
category_summary['Pct_Revenue'] = (category_summary['Total_Revenue'] / category_summary['Total_Revenue'].sum() * 100).round(1)
category_summary['Pct_Calls'] = (category_summary['Port_Calls'] / category_summary['Port_Calls'].sum() * 100).round(1)

print("\n")
print(category_summary.to_string())

print("\n\nKEY INSIGHTS:")
print("-"*80)
print(f"• Total US Agency Market (2023): ${total_revenue:,.0f}")
print(f"• Total Port Calls: {total_calls:,}")
print(f"• Average Fee per Call: ${total_revenue/total_calls:,.0f}")

# Find top revenue generators
top_cat = category_summary.head(1).index[0]
top_cat_rev = category_summary.head(1)['Total_Revenue'].values[0]
top_cat_pct = category_summary.head(1)['Pct_Revenue'].values[0]
print(f"• Largest Category: {top_cat} (${top_cat_rev:,.0f}, {top_cat_pct}% of revenue)")

# Export summary to CSV
vessel_summary.to_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\vessel_class_revenue_summary.csv')
category_summary.to_csv(r'G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.03_REPORTS\vessel_category_revenue_summary.csv')

print("\n✓ Summary files exported to 00_DATA/00.03_REPORTS/")
print("="*80)
