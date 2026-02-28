"""
Extract top lockable rules for Phase 0.5 implementation
Creates a CSV of Port_Pair + HS4 rules covering 90% of high-concentration commodities

Output: priority_rules_phase_05.csv
Format: Phase,Priority,Port_Loading,Port_Discharge,HS4,Group,Commodity,Cargo,Cargo_Detail,Confidence_Pct,Tons,Records,Active
"""

import pandas as pd
from pathlib import Path

# Load data
input_file = Path(__file__).resolve().parent / "sample_2023_sep_oct_nov.csv"
df = pd.read_csv(input_file, low_memory=False)

# Target commodities (from analysis)
target_commodities = [
    'Perishables',
    'Metals',
    'Carbon Products',
    'Forestry',
    'Ferrous Raw Materials',
    'Non-Ferrous Raw Materials',
    'Fertilizer'
]

# Filter to classified cargo only
df_classified = df[df['Group'].notna() & (df['Group'] != 'EXCLUDED')].copy()

# Extract port pairs
df_classified['Port_Loading'] = df_classified['Port of Loading (F)'].astype(str)
df_classified['Port_Discharge'] = df_classified['Port of Discharge (D)'].astype(str)

# Collect all rules
all_rules = []
priority = 1

for commodity in target_commodities:
    # Filter to commodity
    df_comm = df_classified[df_classified['Commodity'] == commodity].copy()

    if len(df_comm) == 0:
        continue

    total_tons = df_comm['Tons'].sum()

    # Group by Port_Pair + HS4 + Group + Commodity + Cargo + Cargo_Detail
    rule_stats = df_comm.groupby([
        'Port_Loading',
        'Port_Discharge',
        'HS4',
        'Group',
        'Commodity',
        'Cargo',
        'Cargo_Detail'
    ]).agg({
        'Tons': 'sum',
        'REC_ID': 'count'
    }).reset_index()

    rule_stats.columns = ['Port_Loading', 'Port_Discharge', 'HS4', 'Group', 'Commodity', 'Cargo', 'Cargo_Detail', 'Tons', 'Records']
    rule_stats = rule_stats.sort_values('Tons', ascending=False)
    rule_stats['Tons_Pct'] = (rule_stats['Tons'] / total_tons * 100).round(1)
    rule_stats['Cumulative_Pct'] = rule_stats['Tons_Pct'].cumsum().round(1)

    # Filter to rules covering up to 90% cumulative
    high_conf_rules = rule_stats[rule_stats['Cumulative_Pct'] <= 90.0].copy()

    # Add metadata
    high_conf_rules['Phase'] = '0.5'
    high_conf_rules['Priority'] = range(priority, priority + len(high_conf_rules))
    high_conf_rules['Confidence_Pct'] = high_conf_rules['Tons_Pct']
    high_conf_rules['Active'] = True

    priority += len(high_conf_rules)

    all_rules.append(high_conf_rules)

# Combine all rules
rules_df = pd.concat(all_rules, ignore_index=True)

# Reorder columns
rules_df = rules_df[[
    'Phase',
    'Priority',
    'Port_Loading',
    'Port_Discharge',
    'HS4',
    'Group',
    'Commodity',
    'Cargo',
    'Cargo_Detail',
    'Confidence_Pct',
    'Tons',
    'Records',
    'Active'
]]

# Sort by priority
rules_df = rules_df.sort_values('Priority')

# Save to CSV
output_file = Path(__file__).resolve().parent / "priority_rules_phase_05.csv"
rules_df.to_csv(output_file, index=False)

print(f"Generated {len(rules_df)} priority rules")
print(f"Total tons covered: {rules_df['Tons'].sum():,.0f}")
print(f"Saved to: {output_file}")

# Summary by commodity
print("\nRules by Commodity:")
summary = rules_df.groupby('Commodity').agg({
    'Priority': 'count',
    'Tons': 'sum'
}).round(0)
summary.columns = ['Rules', 'Tons']
summary = summary.sort_values('Tons', ascending=False)
print(summary.to_string())

# Show sample rules
print("\n" + "="*100)
print("SAMPLE RULES (Top 10):")
print("="*100)
print(rules_df.head(10)[['Priority', 'Port_Loading', 'Port_Discharge', 'HS4', 'Commodity', 'Confidence_Pct', 'Tons']].to_string(index=False))
