"""
Grouped Vessel Category Market Share Analysis
Groups all vessels into major categories: Bulkers, General Cargo, Tankers, RoRo, Containers, Cruise, Others
Compares ship count vs revenue market share
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path


def categorize_vessel(vessel_type: str) -> str:
    """Categorize vessel into major groups."""
    vessel_lower = vessel_type.lower()

    # Bulkers
    if 'bulk' in vessel_lower:
        return 'Bulkers'

    # Tankers
    if 'tanker' in vessel_lower or 'chemical' in vessel_lower:
        return 'Tankers'

    # General Cargo
    if 'general cargo' in vessel_lower or 'cargo' in vessel_lower:
        return 'General Cargo'

    # RoRo (Roll-on/Roll-off, vehicle carriers, car carriers)
    if any(x in vessel_lower for x in ['roro', 'ro-ro', 'pcc', 'pctc', 'vehicle', 'car carrier']):
        return 'RoRo'

    # Containers
    if 'container' in vessel_lower:
        return 'Containers'

    # Cruise
    if 'cruise' in vessel_lower or 'passenger' in vessel_lower:
        return 'Cruise'

    # All others (LNG, LPG, specialized, etc.)
    return 'Others'


def analyze_grouped_vessels(data_file: str):
    """Analyze vessel market share by major categories."""
    print("\n" + "="*70)
    print("GROUPED VESSEL CATEGORY MARKET SHARE ANALYSIS")
    print("Ship Count vs Revenue - Major Vessel Categories")
    print("="*70 + "\n")

    # Load data
    print("Loading data...")
    df = pd.read_csv(data_file)
    df['Fee_Adj'] = pd.to_numeric(df['Fee_Adj'], errors='coerce')
    df['Ships_Type'] = df['Ships_Type'].fillna('')
    df['ICST_DESC'] = df['ICST_DESC'].fillna('Unknown')

    # Create unified vessel type field with fallback logic
    def get_vessel_type(row):
        ships_type = str(row['Ships_Type']).strip()
        if ships_type and ships_type not in ['', 'Unknown', 'nan', 'None']:
            return ships_type
        else:
            return row['ICST_DESC']

    df['Vessel_Type_Unified'] = df.apply(get_vessel_type, axis=1)

    # Apply categorization
    df['Vessel_Category'] = df['Vessel_Type_Unified'].apply(categorize_vessel)

    total_clearances = len(df)
    total_revenue = df['Fee_Adj'].sum()

    print(f"Total clearances: {total_clearances:,}")
    print(f"Total revenue: ${total_revenue:,.0f}\n")

    # Calculate market share by clearances
    clearance_share = df.groupby('Vessel_Category').size().reset_index(name='Clearance_Count')
    clearance_share['Clearance_Pct'] = (clearance_share['Clearance_Count'] / total_clearances) * 100

    # Calculate market share by revenue
    revenue_share = df.groupby('Vessel_Category')['Fee_Adj'].sum().reset_index()
    revenue_share.columns = ['Vessel_Category', 'Total_Revenue']
    revenue_share['Revenue_Pct'] = (revenue_share['Total_Revenue'] / total_revenue) * 100

    # Merge
    market_share = pd.merge(clearance_share, revenue_share, on='Vessel_Category')

    # Calculate ratio and average fee
    market_share['Ratio'] = market_share['Revenue_Pct'] / market_share['Clearance_Pct']
    market_share['Avg_Fee'] = market_share['Total_Revenue'] / market_share['Clearance_Count']

    # Sort by revenue descending
    market_share = market_share.sort_values('Revenue_Pct', ascending=False)

    # Print summary
    print("="*70)
    print("MARKET SHARE BY MAJOR VESSEL CATEGORY")
    print("="*70)
    print(f"{'Category':<15} {'Ships':>10} {'Ship %':>10} {'Revenue':>15} {'Rev %':>10} {'Ratio':>8} {'Avg Fee':>12}")
    print("-" * 70)

    for _, row in market_share.iterrows():
        print(f"{row['Vessel_Category']:<15} "
              f"{row['Clearance_Count']:>10,} "
              f"{row['Clearance_Pct']:>9.1f}% "
              f"${row['Total_Revenue']:>13,.0f} "
              f"{row['Revenue_Pct']:>9.1f}% "
              f"{row['Ratio']:>7.2f}x "
              f"${row['Avg_Fee']:>10,.0f}")

    print("-" * 70)
    print(f"{'TOTAL':<15} {total_clearances:>10,} {'100.0%':>10} ${total_revenue:>13,.0f} {'100.0%':>10}")
    print("="*70)

    # Get detailed breakdown for each category
    print("\n" + "="*70)
    print("DETAILED BREAKDOWN BY CATEGORY")
    print("="*70)

    category_details = {}
    for category in market_share['Vessel_Category']:
        cat_df = df[df['Vessel_Category'] == category]
        type_breakdown = cat_df.groupby('Vessel_Type_Unified').agg({
            'Fee_Adj': ['count', 'sum']
        }).reset_index()
        type_breakdown.columns = ['Vessel_Type', 'Count', 'Revenue']
        type_breakdown = type_breakdown.sort_values('Revenue', ascending=False)
        category_details[category] = type_breakdown

        print(f"\n{category.upper()} - Top 5 Types:")
        print(f"{'  Type':<45} {'Count':>8} {'Revenue':>15}")
        print("  " + "-" * 68)
        for _, row in type_breakdown.head(5).iterrows():
            type_name = row['Vessel_Type'][:42] + "..." if len(row['Vessel_Type']) > 42 else row['Vessel_Type']
            print(f"  {type_name:<45} {row['Count']:>8,} ${row['Revenue']:>13,.0f}")

    return market_share, category_details


def create_grouped_comparison_chart(market_share: pd.DataFrame, output_file: str):
    """Create comparison chart for grouped categories."""
    print("\n\nCreating grouped comparison chart...")

    # Sort by revenue for better visualization
    market_share_sorted = market_share.sort_values('Revenue_Pct', ascending=True)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Ship Count Market Share', 'Revenue Market Share'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Ship count
    fig.add_trace(
        go.Bar(
            y=market_share_sorted['Vessel_Category'],
            x=market_share_sorted['Clearance_Pct'],
            orientation='h',
            name='Ship Count %',
            text=market_share_sorted['Clearance_Pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker=dict(color='lightblue'),
            hovertemplate='<b>%{y}</b><br>Ship Count: %{x:.1f}%<br>Clearances: %{customdata:,}<extra></extra>',
            customdata=market_share_sorted['Clearance_Count']
        ),
        row=1, col=1
    )

    # Revenue
    fig.add_trace(
        go.Bar(
            y=market_share_sorted['Vessel_Category'],
            x=market_share_sorted['Revenue_Pct'],
            orientation='h',
            name='Revenue %',
            text=market_share_sorted['Revenue_Pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker=dict(color='darkgreen'),
            hovertemplate='<b>%{y}</b><br>Revenue: %{x:.1f}%<br>Amount: $%{customdata:,.0f}<extra></extra>',
            customdata=market_share_sorted['Total_Revenue']
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Market Share (%)", row=1, col=1)
    fig.update_xaxes(title_text="Market Share (%)", row=1, col=2)

    fig.update_layout(
        title_text="Vessel Category Market Share: Ship Count vs Revenue<br><sub>Comparing fleet representation with revenue generation</sub>",
        height=600,
        showlegend=False
    )

    # Create full HTML
    html_content = fig.to_html(include_plotlyjs='cdn', div_id='grouped_comparison')

    # Build complete HTML page
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Grouped Vessel Category Market Share Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #1e3c72;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #2a5298;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 1.2em;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        }}
        .stat-card h3 {{
            font-size: 2.5em;
            margin: 0 0 10px 0;
            color: white;
        }}
        .stat-card p {{
            margin: 0;
            opacity: 0.95;
            font-size: 1em;
        }}
        .insight {{
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            padding: 25px;
            border-left: 6px solid #4caf50;
            margin: 25px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .insight h3 {{
            color: #2e7d32;
            margin-top: 0;
            font-size: 1.4em;
        }}
        .insight ul {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        .insight li {{
            margin: 10px 0;
            line-height: 1.6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #e3f2fd;
            transition: background 0.2s;
        }}
        .highlight {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            font-weight: bold;
        }}
        .high-ratio {{
            color: #2e7d32;
            font-weight: bold;
        }}
        .low-ratio {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .chart-container {{
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚢 Vessel Category Market Share Analysis</h1>
        <p class="subtitle">Major Categories: Ship Count vs Revenue Comparison</p>

        <div class="stats-grid">
"""

    # Add stat cards for each category
    for _, row in market_share.iterrows():
        color_class = 'high-ratio' if row['Ratio'] > 1.5 else ('low-ratio' if row['Ratio'] < 0.8 else '')
        full_html += f"""
            <div class="stat-card">
                <h3>{row['Revenue_Pct']:.1f}%</h3>
                <p><strong>{row['Vessel_Category']}</strong></p>
                <p style="font-size: 0.9em; margin-top: 10px;">
                    {row['Clearance_Count']:,} ships ({row['Clearance_Pct']:.1f}%)<br>
                    Ratio: {row['Ratio']:.2f}x
                </p>
            </div>
"""

    full_html += f"""
        </div>

        <div class="insight">
            <h3>📊 Key Insights</h3>
            <ul>
                <li><strong>Bulkers dominate revenue:</strong> Despite being only {market_share[market_share['Vessel_Category']=='Bulkers']['Clearance_Pct'].iloc[0]:.1f}% of ships,
                they generate {market_share[market_share['Vessel_Category']=='Bulkers']['Revenue_Pct'].iloc[0]:.1f}% of revenue
                ({market_share[market_share['Vessel_Category']=='Bulkers']['Ratio'].iloc[0]:.2f}x ratio)</li>

                <li><strong>Volume vs. Value:</strong> Containers and cruise ships represent high ship counts but lower revenue per vessel</li>

                <li><strong>Market balance:</strong> Seven major categories cover the entire $169M clearance market</li>

                <li><strong>Average fees vary widely:</strong> From ${market_share['Avg_Fee'].min():,.0f} to ${market_share['Avg_Fee'].max():,.0f} per clearance</li>
            </ul>
        </div>

        <div class="chart-container">
            {html_content}
        </div>

        <h2>Detailed Market Share Data</h2>
        <table>
            <thead>
                <tr>
                    <th>Vessel Category</th>
                    <th>Clearances</th>
                    <th>Ship Count %</th>
                    <th>Total Revenue</th>
                    <th>Revenue %</th>
                    <th>Ratio</th>
                    <th>Avg Fee</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add table rows
    for _, row in market_share.iterrows():
        ratio_class = 'high-ratio' if row['Ratio'] > 1.5 else ('low-ratio' if row['Ratio'] < 0.8 else '')
        full_html += f"""
                <tr>
                    <td><strong>{row['Vessel_Category']}</strong></td>
                    <td>{row['Clearance_Count']:,}</td>
                    <td>{row['Clearance_Pct']:.1f}%</td>
                    <td>${row['Total_Revenue']:,.0f}</td>
                    <td>{row['Revenue_Pct']:.1f}%</td>
                    <td class="{ratio_class}">{row['Ratio']:.2f}x</td>
                    <td>${row['Avg_Fee']:,.0f}</td>
                </tr>
"""

    full_html += f"""
            </tbody>
            <tfoot style="background: #f0f0f0; font-weight: bold;">
                <tr>
                    <td>TOTAL</td>
                    <td>{market_share['Clearance_Count'].sum():,}</td>
                    <td>100.0%</td>
                    <td>${market_share['Total_Revenue'].sum():,.0f}</td>
                    <td>100.0%</td>
                    <td>-</td>
                    <td>${market_share['Total_Revenue'].sum() / market_share['Clearance_Count'].sum():,.0f}</td>
                </tr>
            </tfoot>
        </table>

        <div class="insight">
            <h3>💡 Understanding the Ratios</h3>
            <ul>
                <li><strong>Ratio > 1.0:</strong> Category generates MORE revenue per clearance than average (revenue efficient)</li>
                <li><strong>Ratio = 1.0:</strong> Category revenue proportional to ship count representation</li>
                <li><strong>Ratio < 1.0:</strong> Category generates LESS revenue per clearance than average (volume business)</li>
            </ul>
            <p><strong>Example:</strong> Bulkers with {market_share[market_share['Vessel_Category']=='Bulkers']['Ratio'].iloc[0]:.2f}x ratio
            generate nearly {market_share[market_share['Vessel_Category']=='Bulkers']['Ratio'].iloc[0]:.0f} times more revenue per clearance
            than their representation in the fleet would suggest.</p>
        </div>

        <p style="text-align: center; color: #666; margin-top: 40px; padding-top: 20px; border-top: 2px solid #e0e0e0;">
            <strong>Report Generated:</strong> {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}<br>
            USACE Port Clearance Market Analysis
        </p>
    </div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    file_size = Path(output_file).stat().st_size / 1024
    print(f"Chart saved to: {output_file}")
    print(f"File size: {file_size:.2f} KB")


def create_ratio_comparison_chart(market_share: pd.DataFrame, output_file: str):
    """Create ratio comparison chart."""
    print("Creating ratio comparison chart...")

    market_share_sorted = market_share.sort_values('Ratio', ascending=True)

    fig = go.Figure()

    colors = ['#d32f2f' if x < 0.8 else '#4caf50' if x > 1.5 else '#2196f3'
              for x in market_share_sorted['Ratio']]

    fig.add_trace(go.Bar(
        y=market_share_sorted['Vessel_Category'],
        x=market_share_sorted['Ratio'],
        orientation='h',
        text=market_share_sorted['Ratio'].apply(lambda x: f"{x:.2f}x"),
        textposition='outside',
        marker=dict(color=colors),
        hovertemplate='<b>%{y}</b><br>Ratio: %{x:.2f}x<br>Revenue %: %{customdata[0]:.1f}%<br>Ship Count %: %{customdata[1]:.1f}%<br>Avg Fee: $%{customdata[2]:,.0f}<extra></extra>',
        customdata=market_share_sorted[['Revenue_Pct', 'Clearance_Pct', 'Avg_Fee']].values
    ))

    # Add reference line at 1.0
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray", line_width=2,
                  annotation_text="Equal Representation (1.0x)",
                  annotation_position="top right")

    fig.update_layout(
        title={
            'text': 'Revenue Efficiency by Vessel Category<br><sub>Revenue % / Ship Count % Ratio | Values > 1.0 = Revenue Efficient | < 1.0 = Volume Business</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Revenue/Ship Count Ratio",
        yaxis_title="Vessel Category",
        height=500,
        showlegend=False
    )

    fig.write_html(output_file, include_plotlyjs='cdn')
    print(f"Ratio chart saved to: {output_file}")


def main():
    """Main execution function."""
    # File paths
    base_dir = Path(r"G:\My Drive\LLM\task_usace_entrance_clearance")
    data_file = base_dir / "00_DATA" / "00.02_PROCESSED" / "usace_clearances_with_grain_v4.1.1_20260206_014715.csv"
    output_dir = base_dir / "00_DATA" / "00.03_REPORTS"
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_file = output_dir / "grouped_vessel_comparison.html"
    ratio_file = output_dir / "grouped_vessel_ratio.html"

    # Run analysis
    market_share, category_details = analyze_grouped_vessels(str(data_file))

    # Create charts
    create_grouped_comparison_chart(market_share, str(comparison_file))
    create_ratio_comparison_chart(market_share, str(ratio_file))

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nComparison chart: {comparison_file}")
    print(f"Ratio chart: {ratio_file}")
    print("\nOpen these files in your browser to view the interactive charts.")

    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file:///{comparison_file}')
        print("\nOpening comparison chart in browser...")
    except:
        pass


if __name__ == '__main__':
    main()
