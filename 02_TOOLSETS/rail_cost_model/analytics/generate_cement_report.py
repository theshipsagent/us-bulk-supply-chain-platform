"""Generate standalone HTML report for Cement Analysis"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import query
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

OUTPUT_PATH = Path(__file__).parent / "reports" / "cement_analysis_report.html"
OUTPUT_PATH.parent.mkdir(exist_ok=True)

print("Generating Cement Analysis Report...")

# Collect all data
print("  Fetching overall metrics...")
metrics = query("""
    SELECT
        COUNT(*) as sample_records,
        CAST(SUM(exp_carloads) AS BIGINT) as total_carloads,
        CAST(SUM(exp_tons) AS BIGINT) as total_tons,
        CAST(SUM(exp_freight_rev) AS BIGINT) as total_revenue,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 2) as avg_rev_per_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as avg_rev_per_ton,
        ROUND(AVG(short_line_miles), 0) as avg_miles
    FROM fact_waybill
    WHERE stcc = '32411'
""").iloc[0]

print("  Fetching price distribution...")
price_dist = query("""
    WITH priced AS (
        SELECT *,
            exp_freight_rev/NULLIF(exp_tons,0) as rev_per_ton
        FROM fact_waybill
        WHERE stcc = '32411' AND exp_tons > 0
    )
    SELECT
        CASE
            WHEN rev_per_ton < 20 THEN 'Under $20'
            WHEN rev_per_ton < 30 THEN '$20-30'
            WHEN rev_per_ton < 40 THEN '$30-40'
            WHEN rev_per_ton < 50 THEN '$40-50'
            WHEN rev_per_ton < 75 THEN '$50-75'
            ELSE 'Over $75'
        END as price_range,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        ROUND(AVG(short_line_miles), 0) as avg_miles,
        MIN(CASE
            WHEN rev_per_ton < 20 THEN 1
            WHEN rev_per_ton < 30 THEN 2
            WHEN rev_per_ton < 40 THEN 3
            WHEN rev_per_ton < 50 THEN 4
            WHEN rev_per_ton < 75 THEN 5
            ELSE 6
        END) as sort_order
    FROM priced
    GROUP BY 1
    ORDER BY sort_order
""")

print("  Fetching seasonality...")
seasonality = query("""
    SELECT
        EXTRACT(QUARTER FROM waybill_date) as quarter,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(exp_tons) AS BIGINT) as tons,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 0) as avg_rev_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as avg_rev_ton
    FROM fact_waybill
    WHERE stcc = '32411'
    GROUP BY 1
    ORDER BY 1
""")

print("  Fetching distance pricing...")
distance_pricing = query("""
    SELECT
        CASE
            WHEN short_line_miles < 200 THEN '< 200 mi'
            WHEN short_line_miles < 400 THEN '200-400 mi'
            WHEN short_line_miles < 600 THEN '400-600 mi'
            WHEN short_line_miles < 800 THEN '600-800 mi'
            ELSE '> 800 mi'
        END as distance_band,
        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 0) as rev_per_car,
        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as rev_per_ton,
        ROUND(SUM(exp_freight_rev) / SUM(exp_carloads) / AVG(short_line_miles), 2) as rev_per_car_mile,
        MIN(CASE
            WHEN short_line_miles < 200 THEN 1
            WHEN short_line_miles < 400 THEN 2
            WHEN short_line_miles < 600 THEN 3
            WHEN short_line_miles < 800 THEN 4
            ELSE 5
        END) as sort_order
    FROM fact_waybill
    WHERE stcc = '32411' AND short_line_miles > 0
    GROUP BY 1
    ORDER BY sort_order
""")

print("  Fetching top routes...")
top_routes = query("""
    SELECT
        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        CAST(SUM(w.exp_freight_rev) AS BIGINT) as revenue,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as rev_per_car,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_tons), 2) as rev_per_ton,
        ROUND(AVG(w.short_line_miles), 0) as avg_miles
    FROM fact_waybill w
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 20
""")

print("  Fetching origins...")
origins = query("""
    SELECT
        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
        COALESCE(o.region, 'Unknown') as region,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
    FROM fact_waybill w
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 15
""")

print("  Fetching destinations...")
destinations = query("""
    SELECT
        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
        COALESCE(d.region, 'Unknown') as region,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        CAST(SUM(w.exp_tons) AS BIGINT) as tons,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
    FROM fact_waybill w
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    WHERE w.stcc = '32411'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 15
""")

# Generate charts
print("  Generating charts...")

# Price distribution chart
fig_price = px.bar(
    price_dist,
    x='price_range',
    y='carloads',
    color='avg_miles',
    color_continuous_scale='Viridis',
    labels={'carloads': 'Carloads', 'price_range': 'Price per Ton', 'avg_miles': 'Avg Miles'},
    title='Price Distribution (Revenue per Ton)'
)
fig_price.update_layout(height=400)
chart_price = fig_price.to_html(full_html=False, include_plotlyjs=False)

# Seasonality chart
fig_season = go.Figure()
fig_season.add_trace(go.Bar(
    x=[f'Q{int(q)}' for q in seasonality['quarter']],
    y=seasonality['carloads'],
    name='Carloads',
    marker_color='#1E3A5F'
))
fig_season.add_trace(go.Scatter(
    x=[f'Q{int(q)}' for q in seasonality['quarter']],
    y=seasonality['avg_rev_ton'],
    name='$/Ton',
    yaxis='y2',
    line=dict(color='#E74C3C', width=3),
    mode='lines+markers'
))
fig_season.update_layout(
    title='Cement Seasonality by Quarter',
    height=400,
    yaxis=dict(title='Carloads'),
    yaxis2=dict(title='$/Ton', overlaying='y', side='right'),
    legend=dict(orientation='h', y=-0.15)
)
chart_season = fig_season.to_html(full_html=False, include_plotlyjs=False)

# Distance pricing chart
fig_dist = px.bar(
    distance_pricing,
    x='distance_band',
    y='rev_per_ton',
    color='carloads',
    color_continuous_scale='Blues',
    labels={'rev_per_ton': '$/Ton', 'distance_band': 'Distance Band', 'carloads': 'Carloads'},
    title='Revenue per Ton by Distance'
)
fig_dist.update_layout(height=400)
chart_dist = fig_dist.to_html(full_html=False, include_plotlyjs=False)

# Car-mile chart
fig_carmile = px.bar(
    distance_pricing,
    x='distance_band',
    y='rev_per_car_mile',
    color='carloads',
    color_continuous_scale='Greens',
    labels={'rev_per_car_mile': '$/Car-Mile', 'distance_band': 'Distance Band'},
    title='Revenue per Car-Mile by Distance (Economies of Scale)'
)
fig_carmile.update_layout(height=400)
chart_carmile = fig_carmile.to_html(full_html=False, include_plotlyjs=False)

# Origins chart
fig_origins = px.bar(
    origins.head(10),
    y='origin',
    x='carloads',
    orientation='h',
    color='avg_rev_car',
    color_continuous_scale='Oranges',
    labels={'carloads': 'Carloads', 'origin': 'Origin', 'avg_rev_car': '$/Car'},
    title='Top Cement Origin Regions'
)
fig_origins.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
chart_origins = fig_origins.to_html(full_html=False, include_plotlyjs=False)

# Destinations chart
fig_dests = px.bar(
    destinations.head(10),
    y='destination',
    x='carloads',
    orientation='h',
    color='avg_rev_car',
    color_continuous_scale='Blues',
    labels={'carloads': 'Carloads', 'destination': 'Destination', 'avg_rev_car': '$/Car'},
    title='Top Cement Destination Markets'
)
fig_dests.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
chart_dests = fig_dests.to_html(full_html=False, include_plotlyjs=False)

# Build HTML
print("  Building HTML report...")

html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cement Rail Freight Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #1E3A5F 0%, #2C5282 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-card .value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #1E3A5F;
        }}
        .metric-card .label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #1E3A5F;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }}
        .chart-container {{
            min-height: 400px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #1E3A5F;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        @media (max-width: 900px) {{
            .two-col, .chart-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .footer {{
            text-align: center;
            color: #666;
            padding: 20px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚂 Cement Rail Freight Analysis</h1>
        <p>STCC 32411 - Hydraulic Cement (Portland Cement) | STB Waybill Sample 2023</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="value">{metrics['total_carloads']:,}</div>
            <div class="label">Total Carloads</div>
        </div>
        <div class="metric-card">
            <div class="value">{metrics['total_tons']/1e6:.1f}M</div>
            <div class="label">Total Tons</div>
        </div>
        <div class="metric-card">
            <div class="value">${metrics['total_revenue']/1e6:.0f}M</div>
            <div class="label">Total Revenue</div>
        </div>
        <div class="metric-card">
            <div class="value">${metrics['avg_rev_per_car']:,.0f}</div>
            <div class="label">Avg Revenue/Car</div>
        </div>
        <div class="metric-card">
            <div class="value">${metrics['avg_rev_per_ton']:.2f}</div>
            <div class="label">Avg Revenue/Ton</div>
        </div>
        <div class="metric-card">
            <div class="value">{metrics['avg_miles']:.0f} mi</div>
            <div class="label">Avg Distance</div>
        </div>
    </div>

    <div class="section">
        <h2>Price Distribution & Seasonality</h2>
        <div class="chart-grid">
            <div class="chart-container">{chart_price}</div>
            <div class="chart-container">{chart_season}</div>
        </div>
        <div class="highlight">
            <strong>Key Finding:</strong> Cement shows strong seasonality with Q3 (summer) peak at ~70,000 carloads vs Q1 low of ~50,000.
            Price per ton also increases in peak season ($39.70 vs $37.61).
        </div>
    </div>

    <div class="section">
        <h2>Distance-Based Pricing Analysis</h2>
        <div class="chart-grid">
            <div class="chart-container">{chart_dist}</div>
            <div class="chart-container">{chart_carmile}</div>
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 15px;">Rate Benchmarks by Distance</h3>
        <table>
            <thead>
                <tr>
                    <th>Distance Band</th>
                    <th>Carloads</th>
                    <th>$/Car</th>
                    <th>$/Ton</th>
                    <th>$/Car-Mile</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{row['distance_band']}</td><td>{row['carloads']:,}</td><td>${row['rev_per_car']:,.0f}</td><td>${row['rev_per_ton']:.2f}</td><td>${row['rev_per_car_mile']:.2f}</td></tr>" for _, row in distance_pricing.iterrows())}
            </tbody>
        </table>

        <div class="highlight">
            <strong>Key Finding:</strong> Revenue per car-mile <em>decreases</em> with distance (from $18.43 for short haul to $5.48 for 800+ miles),
            demonstrating economies of scale in linehaul. Short-haul cement is most expensive per mile due to terminal costs.
        </div>
    </div>

    <div class="section">
        <h2>Top Cement Routes</h2>
        <table>
            <thead>
                <tr>
                    <th>Origin</th>
                    <th>Destination</th>
                    <th>Carloads</th>
                    <th>Tons</th>
                    <th>$/Car</th>
                    <th>$/Ton</th>
                    <th>Miles</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{row['origin']}</td><td>{row['destination']}</td><td>{row['carloads']:,}</td><td>{row['tons']:,}</td><td>${row['rev_per_car']:,.0f}</td><td>${row['rev_per_ton']:.2f}</td><td>{row['avg_miles']:.0f}</td></tr>" for _, row in top_routes.iterrows())}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Origin & Destination Analysis</h2>
        <div class="chart-grid">
            <div class="chart-container">{chart_origins}</div>
            <div class="chart-container">{chart_dests}</div>
        </div>

        <div class="two-col" style="margin-top: 30px;">
            <div>
                <h3>Top Origin Regions</h3>
                <table>
                    <thead>
                        <tr><th>Origin</th><th>Region</th><th>Carloads</th><th>$/Car</th></tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td>{row['origin']}</td><td>{row['region']}</td><td>{row['carloads']:,}</td><td>${row['avg_rev_car']:,.0f}</td></tr>" for _, row in origins.head(10).iterrows())}
                    </tbody>
                </table>
            </div>
            <div>
                <h3>Top Destination Markets</h3>
                <table>
                    <thead>
                        <tr><th>Destination</th><th>Region</th><th>Carloads</th><th>$/Car</th></tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td>{row['destination']}</td><td>{row['region']}</td><td>{row['carloads']:,}</td><td>${row['avg_rev_car']:,.0f}</td></tr>" for _, row in destinations.head(10).iterrows())}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Quick Reference: Cement Rate Benchmarks</h2>
        <table>
            <thead>
                <tr>
                    <th>Distance</th>
                    <th>Expected $/Ton</th>
                    <th>Expected $/Car</th>
                    <th>$/Car-Mile</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>&lt; 200 miles</td><td>$25-26</td><td>$2,700</td><td>$18.43</td><td>Short haul, high terminal cost impact</td></tr>
                <tr><td>200-400 miles</td><td>$38-40</td><td>$4,060</td><td>$14.45</td><td>Most common distance band</td></tr>
                <tr><td>400-600 miles</td><td>$43-45</td><td>$4,640</td><td>$10.04</td><td>Medium haul</td></tr>
                <tr><td>600-800 miles</td><td>$45-47</td><td>$4,825</td><td>$7.17</td><td>Long haul efficiency gains</td></tr>
                <tr><td>&gt; 800 miles</td><td>$60-65</td><td>$6,200</td><td>$5.48</td><td>Cross-country, lowest per-mile cost</td></tr>
            </tbody>
        </table>
        <p style="margin-top: 15px; color: #666; font-size: 0.9rem;">
            <em>* Based on 2023 STB Waybill Sample. Actual rates vary by contract, carrier, origin-destination pair, and market conditions.</em>
        </p>
    </div>

    <div class="footer">
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data Source: STB Public Use Waybill Sample 2023</p>
        <p>Rail Analytics Platform | Project Rail</p>
    </div>
</body>
</html>
"""

# Write the file
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Report generated: {OUTPUT_PATH}")
print(f"   Open in browser to view.")
