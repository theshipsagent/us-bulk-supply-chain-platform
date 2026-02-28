"""
Comprehensive Vessel Type Market Share Analysis
Compares ship count vs revenue for ALL vessel types
Uses Ships_Type with fallback to ICST_DESC when not available
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path


def analyze_all_vessel_types(data_file: str):
    """Analyze all vessel types: ship count vs revenue."""
    print("\n" + "="*70)
    print("COMPREHENSIVE VESSEL TYPE MARKET SHARE ANALYSIS")
    print("Ship Count vs Revenue - All Vessel Types")
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
            return f"[{row['ICST_DESC']}]"  # Brackets indicate fallback to ICST_DESC

    df['Vessel_Type_Unified'] = df.apply(get_vessel_type, axis=1)

    total_clearances = len(df)
    total_revenue = df['Fee_Adj'].sum()

    print(f"Total clearances: {total_clearances:,}")
    print(f"Total revenue: ${total_revenue:,.0f}")
    print(f"Unique vessel types: {df['Vessel_Type_Unified'].nunique()}")

    # Count how many use fallback
    fallback_count = df['Vessel_Type_Unified'].str.startswith('[').sum()
    print(f"Records using ICST_DESC fallback: {fallback_count:,} ({fallback_count/total_clearances*100:.1f}%)")

    # Calculate market share by clearances
    clearance_share = df.groupby('Vessel_Type_Unified').size().reset_index(name='Clearance_Count')
    clearance_share['Clearance_Pct'] = (clearance_share['Clearance_Count'] / total_clearances) * 100

    # Calculate market share by revenue
    revenue_share = df.groupby('Vessel_Type_Unified')['Fee_Adj'].sum().reset_index()
    revenue_share.columns = ['Vessel_Type_Unified', 'Total_Revenue']
    revenue_share['Revenue_Pct'] = (revenue_share['Total_Revenue'] / total_revenue) * 100

    # Merge
    market_share = pd.merge(clearance_share, revenue_share, on='Vessel_Type_Unified')

    # Calculate ratio
    market_share['Ratio'] = market_share['Revenue_Pct'] / market_share['Clearance_Pct']

    # Sort by revenue descending
    market_share = market_share.sort_values('Revenue_Pct', ascending=False)

    # Print summary (top 30)
    print("\n" + "="*70)
    print("MARKET SHARE SUMMARY - TOP 30 VESSEL TYPES")
    print("="*70)
    print(f"{'Vessel Type':<45} {'Ship %':>10} {'Rev %':>10} {'Ratio':>8}")
    print("-" * 70)

    for idx, row in market_share.head(30).iterrows():
        vessel_name = row['Vessel_Type_Unified']
        if len(vessel_name) > 44:
            vessel_name = vessel_name[:41] + "..."
        print(f"{vessel_name:<45} {row['Clearance_Pct']:>9.1f}% {row['Revenue_Pct']:>9.1f}% {row['Ratio']:>7.2f}x")

    print("-" * 70)
    print(f"Top 30 represent: {market_share.head(30)['Clearance_Pct'].sum():>25.1f}% {market_share.head(30)['Revenue_Pct'].sum():>9.1f}%")
    print(f"Remaining {len(market_share)-30} types: {market_share.tail(len(market_share)-30)['Clearance_Pct'].sum():>19.1f}% {market_share.tail(len(market_share)-30)['Revenue_Pct'].sum():>9.1f}%")

    # Identify high-ratio vessels (revenue generators)
    high_ratio = market_share[market_share['Ratio'] > 1.5].copy()
    print(f"\n{len(high_ratio)} vessel types with ratio > 1.5x (high revenue per clearance)")

    low_ratio = market_share[market_share['Ratio'] < 0.8].copy()
    print(f"{len(low_ratio)} vessel types with ratio < 0.8x (low revenue per clearance)")

    return market_share


def create_comprehensive_comparison_chart(market_share: pd.DataFrame, output_file: str):
    """Create interactive comparison chart for all vessel types."""
    print("\nCreating comprehensive comparison chart...")

    # Show top 25 by revenue
    top_25 = market_share.head(25).copy()

    fig = go.Figure()

    # Ship count bars
    fig.add_trace(go.Bar(
        name='Ship Count %',
        x=top_25['Vessel_Type_Unified'],
        y=top_25['Clearance_Pct'],
        text=top_25['Clearance_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(color='lightblue'),
        hovertemplate='<b>%{x}</b><br>Ship Count: %{y:.1f}%<br>Clearances: %{customdata:,}<extra></extra>',
        customdata=top_25['Clearance_Count']
    ))

    # Revenue bars
    fig.add_trace(go.Bar(
        name='Revenue %',
        x=top_25['Vessel_Type_Unified'],
        y=top_25['Revenue_Pct'],
        text=top_25['Revenue_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(color='darkgreen'),
        hovertemplate='<b>%{x}</b><br>Revenue: %{y:.1f}%<br>Amount: $%{customdata:,.0f}<extra></extra>',
        customdata=top_25['Total_Revenue']
    ))

    fig.update_layout(
        title={
            'text': 'All Vessel Types: Ship Count vs Revenue Market Share<br><sub>Top 25 by Revenue - Showing disparity between vessel numbers and revenue generation</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Vessel Type",
        yaxis_title="Market Share (%)",
        barmode='group',
        height=700,
        xaxis={'tickangle': -45, 'tickfont': {'size': 9}},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )

    # Create full HTML
    html_content = fig.to_html(include_plotlyjs='cdn', div_id='all_vessel_comparison')

    # Calculate summary stats
    top_10 = market_share.head(10)
    top_10_clearance = top_10['Clearance_Pct'].sum()
    top_10_revenue = top_10['Revenue_Pct'].sum()

    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>All Vessel Types Market Share Analysis</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1600px;
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
        .warning {{
            background: #fff3e0;
            padding: 15px;
            border-left: 5px solid #ff9800;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-box h3 {{
            font-size: 2em;
            margin: 0 0 10px 0;
        }}
        .stat-box p {{
            margin: 0;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        th {{
            background: #2a5298;
            color: white;
            padding: 12px 8px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{
            background: #f5f5f5;
        }}
        tr:hover {{
            background: #e3f2fd;
        }}
        .high-ratio {{
            background: #c8e6c9 !important;
        }}
        .low-ratio {{
            background: #ffccbc !important;
        }}
        .fallback {{
            color: #666;
            font-style: italic;
        }}
        .filter-section {{
            background: #f8f9fa;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        button {{
            background: #2a5298;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background: #1e3c72;
        }}
        button.active {{
            background: #4caf50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚢 Comprehensive Vessel Type Market Share Analysis</h1>
        <h2 style="text-align: center; color: #666;">All Vessel Types: Ship Count vs Revenue</h2>

        <div class="stats-grid">
            <div class="stat-box">
                <h3>{len(market_share)}</h3>
                <p>Vessel Types</p>
            </div>
            <div class="stat-box">
                <h3>{top_10_clearance:.1f}%</h3>
                <p>Top 10 Ship Count</p>
            </div>
            <div class="stat-box">
                <h3>{top_10_revenue:.1f}%</h3>
                <p>Top 10 Revenue</p>
            </div>
            <div class="stat-box">
                <h3>{top_10_revenue/top_10_clearance:.2f}x</h3>
                <p>Top 10 Ratio</p>
            </div>
        </div>

        <div class="insight">
            <h3>Key Insight</h3>
            <p><strong>Market concentration:</strong> The top 10 vessel types represent <strong>{top_10_clearance:.1f}%</strong>
            of ship count but generate <strong>{top_10_revenue:.1f}%</strong> of revenue.</p>
            <p>The ratio of {top_10_revenue/top_10_clearance:.2f}x indicates that top vessel types generate significantly more revenue per clearance.</p>
        </div>

        <div class="warning">
            <strong>Note:</strong> Vessel types shown in <span class="fallback">[brackets]</span> use ICST_DESC classification
            as fallback when Ships_Type is not available. This ensures complete market coverage.
        </div>

        {html_content}

        <h2 style="margin-top: 40px;">Complete Market Share Data (All {len(market_share)} Vessel Types)</h2>

        <div class="filter-section">
            <strong>Quick Filters:</strong>
            <button onclick="showAll()">Show All</button>
            <button onclick="filterHighRatio()">High Ratio (>1.5x)</button>
            <button onclick="filterLowRatio()">Low Ratio (<0.8x)</button>
            <button onclick="filterBulkCarriers()">Bulk Carriers Only</button>
            <button onclick="filterContainers()">Containers Only</button>
        </div>

        <div style="overflow-x: auto;">
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Vessel Type</th>
                        <th>Clearances</th>
                        <th>Ship Count %</th>
                        <th>Total Revenue</th>
                        <th>Revenue %</th>
                        <th>Rev/Count Ratio</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add table rows for ALL vessel types
    for idx, (_, row) in enumerate(market_share.iterrows(), 1):
        ratio = row['Ratio']
        row_class = ''
        if ratio > 1.5:
            row_class = 'high-ratio'
        elif ratio < 0.8:
            row_class = 'low-ratio'

        vessel_name = row['Vessel_Type_Unified']
        vessel_class = 'fallback' if vessel_name.startswith('[') else ''

        full_html += f"""
                    <tr class="{row_class}" data-ratio="{ratio:.2f}" data-type="{vessel_name}">
                        <td>{idx}</td>
                        <td class="{vessel_class}">{vessel_name}</td>
                        <td>{row['Clearance_Count']:,}</td>
                        <td>{row['Clearance_Pct']:.2f}%</td>
                        <td>${row['Total_Revenue']:,.0f}</td>
                        <td>{row['Revenue_Pct']:.2f}%</td>
                        <td><strong>{ratio:.2f}x</strong></td>
                    </tr>
"""

    full_html += """
                </tbody>
            </table>
        </div>

        <div class="insight" style="margin-top: 30px;">
            <h3>Understanding the Ratio</h3>
            <ul>
                <li><strong>Ratio > 1.0:</strong> Vessel type generates MORE revenue per clearance than average (highlighted in green)</li>
                <li><strong>Ratio = 1.0:</strong> Vessel type generates revenue proportional to its ship count</li>
                <li><strong>Ratio < 1.0:</strong> Vessel type generates LESS revenue per clearance than average (highlighted in orange)</li>
            </ul>
            <p><strong>Example:</strong> Bulk carriers with ratio 2.8x generate almost 3 times more revenue per clearance than their representation in the fleet would suggest.</p>
        </div>

        <script>
            const table = document.getElementById('dataTable');
            const rows = Array.from(table.getElementsByTagName('tbody')[0].getElementsByTagName('tr'));

            function showAll() {
                rows.forEach(row => row.style.display = '');
                document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
            }

            function filterHighRatio() {
                rows.forEach(row => {
                    const ratio = parseFloat(row.dataset.ratio);
                    row.style.display = ratio > 1.5 ? '' : 'none';
                });
                document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
            }

            function filterLowRatio() {
                rows.forEach(row => {
                    const ratio = parseFloat(row.dataset.ratio);
                    row.style.display = ratio < 0.8 ? '' : 'none';
                });
                document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
            }

            function filterBulkCarriers() {
                rows.forEach(row => {
                    const type = row.dataset.type.toLowerCase();
                    row.style.display = type.includes('bulk') ? '' : 'none';
                });
                document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
            }

            function filterContainers() {
                rows.forEach(row => {
                    const type = row.dataset.type.toLowerCase();
                    row.style.display = type.includes('container') ? '' : 'none';
                });
                document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
            }
        </script>

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
    print(f"Comprehensive chart saved to: {output_file}")
    print(f"File size: {file_size:.2f} KB")


def create_ratio_scatter_chart(market_share: pd.DataFrame, output_file: str):
    """Create scatter plot showing ship count vs revenue with ratio indicators."""
    print("\nCreating scatter plot...")

    # Add size for bubble chart (log scale of clearance count for better visualization)
    market_share_copy = market_share.copy()
    market_share_copy['Bubble_Size'] = market_share_copy['Clearance_Count'].apply(lambda x: max(5, x/50))

    fig = px.scatter(
        market_share_copy,
        x='Clearance_Pct',
        y='Revenue_Pct',
        size='Bubble_Size',
        color='Ratio',
        hover_name='Vessel_Type_Unified',
        hover_data={
            'Clearance_Count': ':,',
            'Total_Revenue': ':$,.0f',
            'Ratio': ':.2f',
            'Bubble_Size': False,
            'Clearance_Pct': ':.2f',
            'Revenue_Pct': ':.2f'
        },
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=1.0,
        title='Vessel Type Efficiency: Ship Count vs Revenue<br><sub>Bubble size = number of clearances | Color = revenue ratio</sub>',
        labels={
            'Clearance_Pct': 'Ship Count Market Share (%)',
            'Revenue_Pct': 'Revenue Market Share (%)',
            'Ratio': 'Revenue/Count Ratio'
        }
    )

    # Add diagonal line (equal representation)
    max_val = max(market_share_copy['Clearance_Pct'].max(), market_share_copy['Revenue_Pct'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Equal Representation',
        showlegend=True
    ))

    fig.update_layout(
        height=700,
        xaxis_title="Ship Count Market Share (%)",
        yaxis_title="Revenue Market Share (%)"
    )

    fig.write_html(output_file, include_plotlyjs='cdn')
    print(f"Scatter plot saved to: {output_file}")


def main():
    """Main execution function."""
    # File paths
    base_dir = Path(r"G:\My Drive\LLM\task_usace_entrance_clearance")
    data_file = base_dir / "00_DATA" / "00.02_PROCESSED" / "usace_clearances_with_grain_v4.1.1_20260206_014715.csv"
    output_dir = base_dir / "00_DATA" / "00.03_REPORTS"
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_file = output_dir / "all_vessel_types_comparison.html"
    scatter_file = output_dir / "vessel_efficiency_scatter.html"

    # Run analysis
    market_share = analyze_all_vessel_types(str(data_file))

    # Create charts
    create_comprehensive_comparison_chart(market_share, str(comparison_file))
    create_ratio_scatter_chart(market_share, str(scatter_file))

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nComparison chart: {comparison_file}")
    print(f"Scatter plot: {scatter_file}")
    print(f"\nTotal vessel types analyzed: {len(market_share)}")
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
