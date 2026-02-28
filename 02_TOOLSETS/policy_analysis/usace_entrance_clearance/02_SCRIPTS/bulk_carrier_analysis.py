"""
Bulk Carrier Market Share Analysis
Compares ship count vs revenue market share for bulk carrier types
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path


def analyze_bulk_carrier_market_share(data_file: str):
    """Analyze bulk carrier market share by ship count vs revenue."""
    print("\n" + "="*70)
    print("BULK CARRIER MARKET SHARE ANALYSIS")
    print("Ship Count vs Revenue Comparison")
    print("="*70 + "\n")

    # Load data
    print("Loading data...")
    df = pd.read_csv(data_file)
    df['Fee_Adj'] = pd.to_numeric(df['Fee_Adj'], errors='coerce')
    df['Ships_Type'] = df['Ships_Type'].fillna('Unknown')

    total_clearances = len(df)
    total_revenue = df['Fee_Adj'].sum()

    # Define bulk carrier types (based on the actual data)
    bulk_carrier_types = [
        'Bulk Carrier-Supra/Ultramax',
        'Bulk Carrier-Large Handy',
        'Bulk Carrier-Pmax/Kamsarmax',
        'Bulk Carrier-Handymax',
        'Bulk Carrier-Small Handy',
        'Bulk Carrier-Capesize',
        'Bulk Carrier-Post Panamax',
        'Bulk Carrier-Mini Capesize',
        'Bulk Carrier-Newcastlemax',
        'Bulk Carrier-5,000-7,499dwt'
    ]

    # Categorize vessels
    df['Vessel_Category'] = df['Ships_Type'].apply(
        lambda x: x if x in bulk_carrier_types else 'Other Vessel Types'
    )

    # Calculate market share by clearances (ship count)
    clearance_share = df.groupby('Vessel_Category').size().reset_index(name='Clearance_Count')
    clearance_share['Clearance_Pct'] = (clearance_share['Clearance_Count'] / total_clearances) * 100

    # Calculate market share by revenue
    revenue_share = df.groupby('Vessel_Category')['Fee_Adj'].sum().reset_index()
    revenue_share.columns = ['Vessel_Category', 'Total_Revenue']
    revenue_share['Revenue_Pct'] = (revenue_share['Total_Revenue'] / total_revenue) * 100

    # Merge the two
    market_share = pd.merge(clearance_share, revenue_share, on='Vessel_Category')

    # Sort by revenue descending
    market_share = market_share.sort_values('Revenue_Pct', ascending=False)

    # Print summary
    print("\nMARKET SHARE SUMMARY")
    print("-" * 70)
    print(f"{'Vessel Category':<35} {'Ship %':>10} {'Revenue %':>10} {'Ratio':>10}")
    print("-" * 70)

    for _, row in market_share.iterrows():
        ratio = row['Revenue_Pct'] / row['Clearance_Pct'] if row['Clearance_Pct'] > 0 else 0
        print(f"{row['Vessel_Category']:<35} {row['Clearance_Pct']:>9.1f}% {row['Revenue_Pct']:>9.1f}% {ratio:>9.2f}x")

    print("-" * 70)

    # Calculate bulk carrier totals
    bulk_carriers = market_share[market_share['Vessel_Category'] != 'Other Vessel Types']
    total_bulk_clearance_pct = bulk_carriers['Clearance_Pct'].sum()
    total_bulk_revenue_pct = bulk_carriers['Revenue_Pct'].sum()

    print(f"\n{'BULK CARRIERS (TOTAL)':<35} {total_bulk_clearance_pct:>9.1f}% {total_bulk_revenue_pct:>9.1f}% {total_bulk_revenue_pct/total_bulk_clearance_pct:>9.2f}x")
    print(f"{'OTHER VESSEL TYPES':<35} {100-total_bulk_clearance_pct:>9.1f}% {100-total_bulk_revenue_pct:>9.1f}% {(100-total_bulk_revenue_pct)/(100-total_bulk_clearance_pct):>9.2f}x")

    return market_share


def create_comparison_chart(market_share: pd.DataFrame, output_file: str):
    """Create interactive comparison chart."""
    print("\nCreating comparison chart...")

    # Create grouped bar chart
    fig = go.Figure()

    # Add ship count bars
    fig.add_trace(go.Bar(
        name='Ship Count %',
        x=market_share['Vessel_Category'],
        y=market_share['Clearance_Pct'],
        text=market_share['Clearance_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(color='lightblue'),
        hovertemplate='<b>%{x}</b><br>Ship Count: %{y:.1f}%<br>Clearances: %{customdata:,}<extra></extra>',
        customdata=market_share['Clearance_Count']
    ))

    # Add revenue bars
    fig.add_trace(go.Bar(
        name='Revenue %',
        x=market_share['Vessel_Category'],
        y=market_share['Revenue_Pct'],
        text=market_share['Revenue_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(color='darkgreen'),
        hovertemplate='<b>%{x}</b><br>Revenue: %{y:.1f}%<br>Amount: $%{customdata:,.0f}<extra></extra>',
        customdata=market_share['Total_Revenue']
    ))

    fig.update_layout(
        title={
            'text': 'Bulk Carrier Market Share: Ship Count vs Revenue<br><sub>Showing disparity between vessel numbers and revenue generation</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Vessel Type",
        yaxis_title="Market Share (%)",
        barmode='group',
        height=600,
        xaxis={'tickangle': -45},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )

    # Save as HTML
    html_content = fig.to_html(include_plotlyjs='cdn', div_id='bulk_carrier_comparison')

    # Create full HTML page
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bulk Carrier Market Share Analysis</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1e3c72;
            text-align: center;
        }}
        .insight {{
            background: #e8f5e9;
            padding: 20px;
            border-left: 5px solid #4caf50;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .insight h3 {{
            color: #2e7d32;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #2a5298;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{
            background: #f5f5f5;
        }}
        .highlight {{
            background: #fff3e0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚢 Bulk Carrier Market Share Analysis</h1>
        <h2 style="text-align: center; color: #666;">Ship Count vs Revenue Comparison</h2>

        <div class="insight">
            <h3>Key Insight</h3>
            <p><strong>Bulk carriers generate disproportionately high revenue relative to their ship count.</strong></p>
            <p>While bulk carriers represent approximately <strong>{market_share[market_share['Vessel_Category'] != 'Other Vessel Types']['Clearance_Pct'].sum():.1f}%</strong>
            of vessel clearances, they account for <strong>{market_share[market_share['Vessel_Category'] != 'Other Vessel Types']['Revenue_Pct'].sum():.1f}%</strong>
            of total revenue.</p>
        </div>

        {html_content}

        <h2 style="margin-top: 40px;">Detailed Market Share Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Vessel Category</th>
                    <th>Clearances</th>
                    <th>Ship Count %</th>
                    <th>Total Revenue</th>
                    <th>Revenue %</th>
                    <th>Rev/Count Ratio</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add table rows
    for _, row in market_share.iterrows():
        ratio = row['Revenue_Pct'] / row['Clearance_Pct'] if row['Clearance_Pct'] > 0 else 0
        row_class = 'highlight' if row['Vessel_Category'] != 'Other Vessel Types' else ''
        full_html += f"""
                <tr class="{row_class}">
                    <td>{row['Vessel_Category']}</td>
                    <td>{row['Clearance_Count']:,}</td>
                    <td>{row['Clearance_Pct']:.1f}%</td>
                    <td>${row['Total_Revenue']:,.0f}</td>
                    <td>{row['Revenue_Pct']:.1f}%</td>
                    <td>{ratio:.2f}x</td>
                </tr>
"""

    # Calculate totals
    bulk_carriers = market_share[market_share['Vessel_Category'] != 'Other Vessel Types']
    total_bulk_clearance = bulk_carriers['Clearance_Count'].sum()
    total_bulk_clearance_pct = bulk_carriers['Clearance_Pct'].sum()
    total_bulk_revenue = bulk_carriers['Total_Revenue'].sum()
    total_bulk_revenue_pct = bulk_carriers['Revenue_Pct'].sum()
    bulk_ratio = total_bulk_revenue_pct / total_bulk_clearance_pct

    full_html += f"""
            </tbody>
            <tfoot style="background: #f0f0f0; font-weight: bold;">
                <tr>
                    <td>BULK CARRIERS (TOTAL)</td>
                    <td>{total_bulk_clearance:,}</td>
                    <td>{total_bulk_clearance_pct:.1f}%</td>
                    <td>${total_bulk_revenue:,.0f}</td>
                    <td>{total_bulk_revenue_pct:.1f}%</td>
                    <td>{bulk_ratio:.2f}x</td>
                </tr>
                <tr>
                    <td>OTHER VESSEL TYPES</td>
                    <td>{market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Clearance_Count'].iloc[0]:,}</td>
                    <td>{market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Clearance_Pct'].iloc[0]:.1f}%</td>
                    <td>${market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Total_Revenue'].iloc[0]:,.0f}</td>
                    <td>{market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Revenue_Pct'].iloc[0]:.1f}%</td>
                    <td>{market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Revenue_Pct'].iloc[0] / market_share[market_share['Vessel_Category'] == 'Other Vessel Types']['Clearance_Pct'].iloc[0]:.2f}x</td>
                </tr>
            </tfoot>
        </table>

        <div class="insight">
            <h3>Analysis</h3>
            <ul>
                <li><strong>Revenue Concentration:</strong> Bulk carriers generate {bulk_ratio:.2f}x more revenue per ship than their representation in the fleet would suggest.</li>
                <li><strong>High-Value Cargo:</strong> Bulk carriers handle larger volumes and higher-value commodities, resulting in higher fees per clearance.</li>
                <li><strong>Vessel Efficiency:</strong> Larger bulk carriers (Supra/Ultra, Panamax/Kamsarmax) have higher revenue per clearance due to greater cargo capacity.</li>
                <li><strong>Market Importance:</strong> Despite representing only {total_bulk_clearance_pct:.1f}% of ship counts, bulk carriers are critical to port revenue.</li>
            </ul>
        </div>

        <p style="text-align: center; color: #666; margin-top: 40px;">
            Generated: {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}
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


def create_ratio_chart(market_share: pd.DataFrame, output_file: str):
    """Create a chart showing revenue/count ratio."""
    print("\nCreating revenue ratio chart...")

    # Calculate ratio
    market_share_copy = market_share.copy()
    market_share_copy['Ratio'] = market_share_copy['Revenue_Pct'] / market_share_copy['Clearance_Pct']

    # Sort by ratio
    market_share_copy = market_share_copy.sort_values('Ratio', ascending=True)

    fig = go.Figure()

    colors = ['red' if x == 'Other Vessel Types' else 'steelblue' for x in market_share_copy['Vessel_Category']]

    fig.add_trace(go.Bar(
        y=market_share_copy['Vessel_Category'],
        x=market_share_copy['Ratio'],
        orientation='h',
        text=market_share_copy['Ratio'].apply(lambda x: f"{x:.2f}x"),
        textposition='outside',
        marker=dict(color=colors),
        hovertemplate='<b>%{y}</b><br>Revenue/Count Ratio: %{x:.2f}x<br>Revenue %: %{customdata[0]:.1f}%<br>Count %: %{customdata[1]:.1f}%<extra></extra>',
        customdata=market_share_copy[['Revenue_Pct', 'Clearance_Pct']].values
    ))

    # Add reference line at 1.0
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray",
                  annotation_text="Equal representation", annotation_position="top")

    fig.update_layout(
        title={
            'text': 'Revenue per Ship Ratio by Vessel Type<br><sub>Values > 1.0 indicate higher revenue per clearance than average</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Revenue % / Ship Count % Ratio",
        yaxis_title="Vessel Type",
        height=600,
        showlegend=False
    )

    # Save
    fig.write_html(output_file, include_plotlyjs='cdn')
    print(f"Ratio chart saved to: {output_file}")


def main():
    """Main execution function."""
    # File paths
    base_dir = Path(r"G:\My Drive\LLM\task_usace_entrance_clearance")
    data_file = base_dir / "00_DATA" / "00.02_PROCESSED" / "usace_clearances_with_grain_v4.1.1_20260206_014715.csv"
    output_dir = base_dir / "00_DATA" / "00.03_REPORTS"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "bulk_carrier_comparison.html"
    ratio_file = output_dir / "bulk_carrier_ratio.html"

    # Run analysis
    market_share = analyze_bulk_carrier_market_share(str(data_file))

    # Create charts
    create_comparison_chart(market_share, str(output_file))
    create_ratio_chart(market_share, str(ratio_file))

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nComparison chart: {output_file}")
    print(f"Ratio chart: {ratio_file}")
    print("\nOpen these files in your browser to view the interactive charts.")

    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file:///{output_file}')
        print("\nOpening comparison chart in browser...")
    except:
        pass


if __name__ == '__main__':
    main()
