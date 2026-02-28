"""
Analyze high-concentration commodities in 3-month sample
Identify lockable rules with 90%+ confidence for priority classification

Target commodities with >60% concentration:
1. Perishables (100% concentration)
2. Refrigerated (100% concentration)
3. Metals (80% port, 92% HS)
4. Carbon Products (71% port, 71% HS)
5. Forestry (68% port, 77% origin)
6. Ferrous Raw Materials (58% port, 75% origin, 88% HS)
7. Non-Ferrous Raw Materials (58% port, 70% HS)
8. Fertilizer (46% port, 77% party, 86% HS)
"""

import pandas as pd
from pathlib import Path
import sys

# Set UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Load data
input_file = Path(__file__).resolve().parent / "sample_2023_sep_oct_nov.csv"
df = pd.read_csv(input_file, low_memory=False)

print(f"Total records: {len(df):,}")
print(f"Total tons: {df['Tons'].sum():,.0f}")
print(f"\nColumns: {list(df.columns)}\n")

# Target commodities
target_commodities = [
    'Perishables',
    'Refrigerated',
    'Metals',
    'Carbon Products',
    'Forestry',
    'Ferrous Raw Materials',
    'Non-Ferrous Raw Materials',
    'Fertilizer'
]

# Filter to classified cargo only
df_classified = df[df['Group'].notna() & (df['Group'] != 'EXCLUDED')].copy()
print(f"Classified records: {len(df_classified):,} ({len(df_classified)/len(df)*100:.1f}%)")
print(f"Classified tons: {df_classified['Tons'].sum():,.0f}\n")

# Create port pair field
df_classified['Port_Pair'] = df_classified['Port of Loading (F)'].astype(str) + ' TO ' + df_classified['Port of Discharge (D)'].astype(str)

# Analysis results
results = []

for commodity in target_commodities:
    print("="*100)
    print(f"\nANALYZING: {commodity}")
    print("="*100)

    # Filter to commodity
    df_comm = df_classified[df_classified['Commodity'] == commodity].copy()

    if len(df_comm) == 0:
        print(f"No records found for {commodity}")
        continue

    total_tons = df_comm['Tons'].sum()
    total_records = len(df_comm)

    print(f"\nTotal Records: {total_records:,}")
    print(f"Total Tons: {total_tons:,.0f}")

    # ==================================================================================
    # 1. PORT PAIR ANALYSIS
    # ==================================================================================
    print(f"\n{'-'*100}")
    print("PORT PAIR CONCENTRATION")
    print('-'*100)

    port_pair_stats = df_comm.groupby('Port_Pair').agg({
        'Tons': 'sum',
        'REC_ID': 'count'
    }).round(0)
    port_pair_stats.columns = ['Tons', 'Records']
    port_pair_stats = port_pair_stats.sort_values('Tons', ascending=False)
    port_pair_stats['Tons_Pct'] = (port_pair_stats['Tons'] / total_tons * 100).round(1)
    port_pair_stats['Cumulative_Pct'] = port_pair_stats['Tons_Pct'].cumsum().round(1)

    # Show top 10 port pairs
    print(f"\nTop 10 Port Pairs (covering {port_pair_stats.head(10)['Cumulative_Pct'].iloc[-1]:.1f}% of tons):")
    print(port_pair_stats.head(10).to_string())

    # ==================================================================================
    # 2. HS CODE ANALYSIS
    # ==================================================================================
    print(f"\n{'-'*100}")
    print("HS CODE CONCENTRATION")
    print('-'*100)

    hs4_stats = df_comm.groupby('HS4').agg({
        'Tons': 'sum',
        'REC_ID': 'count'
    }).round(0)
    hs4_stats.columns = ['Tons', 'Records']
    hs4_stats = hs4_stats.sort_values('Tons', ascending=False)
    hs4_stats['Tons_Pct'] = (hs4_stats['Tons'] / total_tons * 100).round(1)
    hs4_stats['Cumulative_Pct'] = hs4_stats['Tons_Pct'].cumsum().round(1)

    print(f"\nTop 10 HS4 Codes (covering {hs4_stats.head(10)['Cumulative_Pct'].iloc[-1]:.1f}% of tons):")
    print(hs4_stats.head(10).to_string())

    # ==================================================================================
    # 3. PARTY ANALYSIS (Consignee)
    # ==================================================================================
    print(f"\n{'-'*100}")
    print("CONSIGNEE CONCENTRATION")
    print('-'*100)

    party_stats = df_comm.groupby('Consignee').agg({
        'Tons': 'sum',
        'REC_ID': 'count'
    }).round(0)
    party_stats.columns = ['Tons', 'Records']
    party_stats = party_stats.sort_values('Tons', ascending=False)
    party_stats['Tons_Pct'] = (party_stats['Tons'] / total_tons * 100).round(1)
    party_stats['Cumulative_Pct'] = party_stats['Tons_Pct'].cumsum().round(1)

    print(f"\nTop 10 Consignees (covering {party_stats.head(10)['Cumulative_Pct'].iloc[-1]:.1f}% of tons):")
    print(party_stats.head(10).to_string())

    # ==================================================================================
    # 4. LOCKABLE RULES - Port Pair + HS4
    # ==================================================================================
    print(f"\n{'-'*100}")
    print("LOCKABLE RULES: Port_Pair + HS4 Combinations")
    print('-'*100)

    # Group by Port_Pair + HS4
    rule_stats = df_comm.groupby(['Port_Pair', 'HS4', 'Commodity']).agg({
        'Tons': 'sum',
        'REC_ID': 'count'
    }).reset_index()
    rule_stats.columns = ['Port_Pair', 'HS4', 'Commodity', 'Tons', 'Records']
    rule_stats = rule_stats.sort_values('Tons', ascending=False)
    rule_stats['Tons_Pct'] = (rule_stats['Tons'] / total_tons * 100).round(1)
    rule_stats['Cumulative_Pct'] = rule_stats['Tons_Pct'].cumsum().round(1)

    # Show top 20 rules
    print(f"\nTop 20 Rules (Port_Pair + HS4):")
    print(rule_stats.head(20).to_string(index=False))

    # ==================================================================================
    # 5. HIGH-CONFIDENCE RULE IDENTIFICATION (90%+ threshold)
    # ==================================================================================
    print(f"\n{'-'*100}")
    print("HIGH-CONFIDENCE RULES (90%+ of commodity tons)")
    print('-'*100)

    # Filter rules covering >= 90% cumulative tons
    high_conf_rules = rule_stats[rule_stats['Cumulative_Pct'] <= 90.0].copy()

    if len(high_conf_rules) > 0:
        lockable_tons = high_conf_rules['Tons'].sum()
        lockable_pct = lockable_tons / total_tons * 100

        print(f"\nLOCKABLE TONS: {lockable_tons:,.0f} ({lockable_pct:.1f}% of {commodity})")
        print(f"Number of rules needed: {len(high_conf_rules)}")
        print(f"\nRule formats:")

        for idx, row in high_conf_rules.head(10).iterrows():
            print(f"  IF Port_Pair='{row['Port_Pair']}' AND HS4={row['HS4']} THEN Commodity='{row['Commodity']}' (confidence: {row['Tons_Pct']:.1f}%)")
    else:
        lockable_tons = 0
        lockable_pct = 0
        print(f"No rules meet 90%+ threshold")

    # ==================================================================================
    # 6. SUMMARY STATISTICS
    # ==================================================================================
    results.append({
        'Commodity': commodity,
        'Total_Tons': total_tons,
        'Total_Records': total_records,
        'Top_Port_Pair_Pct': port_pair_stats['Tons_Pct'].iloc[0] if len(port_pair_stats) > 0 else 0,
        'Top_HS4_Pct': hs4_stats['Tons_Pct'].iloc[0] if len(hs4_stats) > 0 else 0,
        'Top_Party_Pct': party_stats['Tons_Pct'].iloc[0] if len(party_stats) > 0 else 0,
        'Lockable_Tons_90pct': lockable_tons,
        'Lockable_Pct_90pct': lockable_pct,
        'Rules_Needed_90pct': len(high_conf_rules)
    })

# ==================================================================================
# FINAL SUMMARY TABLE
# ==================================================================================
print("\n" + "="*100)
print("SUMMARY: HIGH-CONFIDENCE LOCKABLE RULES (90%+ threshold)")
print("="*100)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Lockable_Pct_90pct', ascending=False)

print("\nCommodities ranked by % lockable with deterministic rules:\n")
for idx, row in results_df.iterrows():
    print(f"{row['Commodity']:30s} | {row['Lockable_Pct_90pct']:6.1f}% lockable | {row['Rules_Needed_90pct']:4.0f} rules needed | {row['Lockable_Tons_90pct']:12,.0f} tons")

# Save to CSV
output_file = Path(__file__).resolve().parent / "high_concentration_analysis.csv"
results_df.to_csv(output_file, index=False)
print(f"\n✓ Detailed results saved to: {output_file}")

print("\n" + "="*100)
print("ANALYSIS COMPLETE")
print("="*100)
