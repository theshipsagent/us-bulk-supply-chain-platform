"""Generate URCS Rate Benchmarking Report."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import get_connection, query
from urcs_model import init_urcs_tables, create_urcs_views, get_stb_jurisdiction_threshold
import json

# Initialize
conn = get_connection()
init_urcs_tables(conn)
create_urcs_views(conn)

print("Generating URCS Rate Benchmarking Report...")

# Gather data
summary = query("""
    SELECT
        COUNT(*) as total_shipments,
        ROUND(AVG(rvc_ratio), 1) as avg_rvc,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold,
        ROUND(SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above,
        ROUND(SUM(revenue), 0) as total_revenue,
        ROUND(SUM(est_variable_cost), 0) as total_var_cost
    FROM v_rvc_analysis
    WHERE rvc_ratio > 0 AND rvc_ratio < 1000
""").iloc[0]

by_commodity = query("""
    SELECT
        stcc_2digit,
        COALESCE(commodity, 'Unknown') as commodity,
        shipments,
        avg_rvc,
        median_rvc,
        above_threshold,
        pct_above_threshold
    FROM v_rvc_by_commodity
    WHERE shipments > 500
    ORDER BY avg_rvc DESC
    LIMIT 20
""")

by_distance = query("""
    SELECT * FROM v_rvc_by_distance
    ORDER BY distance_band
""")

cement_analysis = query("""
    SELECT
        CASE
            WHEN miles < 250 THEN 'Short (<250 mi)'
            WHEN miles < 500 THEN 'Medium (250-500 mi)'
            WHEN miles < 1000 THEN 'Long (500-1000 mi)'
            ELSE 'Very Long (>1000 mi)'
        END as distance_band,
        COUNT(*) as shipments,
        ROUND(AVG(rvc_ratio), 1) as avg_rvc,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rvc_ratio), 1) as median_rvc,
        ROUND(AVG(revenue), 2) as avg_revenue,
        ROUND(AVG(est_variable_cost), 2) as avg_cost,
        SUM(CASE WHEN rvc_ratio > 180 THEN 1 ELSE 0 END) as above_threshold
    FROM v_rvc_analysis
    WHERE stcc LIKE '324%'
      AND rvc_ratio > 0 AND rvc_ratio < 1000
    GROUP BY 1
    ORDER BY 1
""")

# R/VC distribution data for histogram
rvc_distribution = query("""
    SELECT
        CASE
            WHEN rvc_ratio < 100 THEN '< 100%'
            WHEN rvc_ratio < 120 THEN '100-120%'
            WHEN rvc_ratio < 140 THEN '120-140%'
            WHEN rvc_ratio < 160 THEN '140-160%'
            WHEN rvc_ratio < 180 THEN '160-180%'
            WHEN rvc_ratio < 200 THEN '180-200%'
            WHEN rvc_ratio < 250 THEN '200-250%'
            WHEN rvc_ratio < 300 THEN '250-300%'
            WHEN rvc_ratio < 400 THEN '300-400%'
            ELSE '> 400%'
        END as rvc_band,
        COUNT(*) as count
    FROM v_rvc_analysis
    WHERE rvc_ratio > 0 AND rvc_ratio < 1000
    GROUP BY 1
    ORDER BY 1
""")

# Generate HTML report
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>URCS Rate Benchmarking Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #1a365d; border-bottom: 3px solid #2b6cb0; padding-bottom: 10px; }}
        h2 {{ color: #2c5282; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2b6cb0; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .chart-container {{ background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #2b6cb0; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f0f7ff; }}
        .highlight {{ background: #fff3cd; }}
        .above-threshold {{ color: #c53030; font-weight: bold; }}
        .below-threshold {{ color: #2f855a; }}
        .info-box {{ background: #e6f3ff; border-left: 4px solid #2b6cb0; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .warning-box {{ background: #fff3cd; border-left: 4px solid #d69e2e; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>URCS Rate Benchmarking Analysis</h1>
        <p>Revenue-to-Variable-Cost (R/VC) analysis using STB URCS methodology</p>

        <div class="info-box">
            <strong>What is R/VC?</strong> The Revenue-to-Variable-Cost ratio compares actual freight revenue
            to the URCS-estimated variable cost of providing service. An R/VC ratio of 180% is the STB's
            threshold for rate reasonableness jurisdiction - rates above this level may be subject to regulatory review.
        </div>

        <h2>Summary Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{summary['total_shipments']:,.0f}</div>
                <div class="metric-label">Shipments Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['avg_rvc']:.1f}%</div>
                <div class="metric-label">Average R/VC</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['median_rvc']:.1f}%</div>
                <div class="metric-label">Median R/VC</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['pct_above']:.1f}%</div>
                <div class="metric-label">Above 180% Threshold</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${summary['total_revenue']/1e9:.1f}B</div>
                <div class="metric-label">Total Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${summary['total_var_cost']/1e9:.1f}B</div>
                <div class="metric-label">Total Variable Cost</div>
            </div>
        </div>

        <h2>R/VC Distribution</h2>
        <div class="chart-container" id="rvc-histogram"></div>

        <h2>R/VC by Commodity</h2>
        <div class="chart-container" id="commodity-chart"></div>

        <table>
            <tr>
                <th>STCC</th>
                <th>Commodity</th>
                <th>Shipments</th>
                <th>Avg R/VC</th>
                <th>Median R/VC</th>
                <th>Above 180%</th>
                <th>% Above</th>
            </tr>
"""

for _, row in by_commodity.iterrows():
    rvc_class = 'above-threshold' if row['avg_rvc'] > 180 else 'below-threshold'
    html += f"""
            <tr>
                <td>{row['stcc_2digit']}</td>
                <td>{row['commodity'][:40]}</td>
                <td>{row['shipments']:,.0f}</td>
                <td class="{rvc_class}">{row['avg_rvc']:.1f}%</td>
                <td>{row['median_rvc']:.1f}%</td>
                <td>{row['above_threshold']:,.0f}</td>
                <td>{row['pct_above_threshold']:.1f}%</td>
            </tr>
"""

html += """
        </table>

        <h2>R/VC by Distance</h2>
        <div class="chart-container" id="distance-chart"></div>

        <div class="warning-box">
            <strong>Key Insight:</strong> Short-haul movements show significantly higher R/VC ratios,
            indicating stronger rail pricing power where truck competition is less effective.
            Long-haul movements show lower R/VC ratios, suggesting more competitive pricing.
        </div>

        <table>
            <tr>
                <th>Distance Band</th>
                <th>Shipments</th>
                <th>Avg R/VC</th>
                <th>Median R/VC</th>
                <th>Above 180%</th>
            </tr>
"""

for _, row in by_distance.iterrows():
    rvc_class = 'above-threshold' if row['avg_rvc'] > 180 else 'below-threshold'
    html += f"""
            <tr>
                <td>{row['distance_band']}</td>
                <td>{row['shipments']:,.0f}</td>
                <td class="{rvc_class}">{row['avg_rvc']:.1f}%</td>
                <td>{row['median_rvc']:.1f}%</td>
                <td>{row['above_threshold']:,.0f}</td>
            </tr>
"""

html += """
        </table>

        <h2>Cement (STCC 324xx) Analysis</h2>
        <div class="chart-container" id="cement-chart"></div>

        <table>
            <tr>
                <th>Distance Band</th>
                <th>Shipments</th>
                <th>Avg R/VC</th>
                <th>Median R/VC</th>
                <th>Avg Revenue</th>
                <th>Avg Cost</th>
                <th>Above 180%</th>
            </tr>
"""

for _, row in cement_analysis.iterrows():
    rvc_class = 'above-threshold' if row['avg_rvc'] > 180 else 'below-threshold'
    html += f"""
            <tr>
                <td>{row['distance_band']}</td>
                <td>{row['shipments']:,.0f}</td>
                <td class="{rvc_class}">{row['avg_rvc']:.1f}%</td>
                <td>{row['median_rvc']:.1f}%</td>
                <td>${row['avg_revenue']:,.0f}</td>
                <td>${row['avg_cost']:,.0f}</td>
                <td>{row['above_threshold']:,.0f}</td>
            </tr>
"""

# Prepare chart data
rvc_bands = rvc_distribution['rvc_band'].tolist()
rvc_counts = rvc_distribution['count'].tolist()

commodity_names = [f"{row['stcc_2digit']}: {row['commodity'][:20]}" for _, row in by_commodity.head(10).iterrows()]
commodity_rvc = by_commodity.head(10)['avg_rvc'].tolist()

distance_names = by_distance['distance_band'].tolist()
distance_rvc = by_distance['avg_rvc'].tolist()

cement_dist = cement_analysis['distance_band'].tolist()
cement_rvc = cement_analysis['avg_rvc'].tolist()

html += f"""
        </table>

        <h2>Methodology</h2>
        <div class="info-box">
            <p><strong>URCS Variable Cost Components:</strong></p>
            <ul>
                <li><strong>Car-mile costs:</strong> $0.42 per car-mile (loaded + empty return)</li>
                <li><strong>Train-mile costs:</strong> $48.50 per train-mile (locomotive + crew)</li>
                <li><strong>Gross ton-mile costs:</strong> $0.0085 per GTM (track, fuel)</li>
                <li><strong>Terminal costs:</strong> $42.00 per switch movement</li>
                <li><strong>Car ownership:</strong> $52.00 per car-day</li>
                <li><strong>Administrative:</strong> $150.00 per carload (origin + termination)</li>
            </ul>
            <p>Distance estimated from BEA zone centroids with 1.25x circuity factor for rail routing.</p>
        </div>

        <p style="color: #666; margin-top: 40px; text-align: center;">
            Generated by Rail Analytics Platform | URCS 2023 Unit Costs | STB Threshold: 180%
        </p>
    </div>

    <script>
        // R/VC Distribution Histogram
        Plotly.newPlot('rvc-histogram', [{{
            x: {json.dumps(rvc_bands)},
            y: {json.dumps(rvc_counts)},
            type: 'bar',
            marker: {{
                color: {json.dumps(rvc_bands)}.map(b => b.includes('180') || b.includes('200') || b.includes('250') || b.includes('300') || b.includes('400') ? '#c53030' : '#2b6cb0')
            }}
        }}], {{
            title: 'Distribution of R/VC Ratios',
            xaxis: {{ title: 'R/VC Ratio Band' }},
            yaxis: {{ title: 'Number of Shipments' }},
            shapes: [{{
                type: 'line',
                x0: 4.5, x1: 4.5,
                y0: 0, y1: Math.max(...{json.dumps(rvc_counts)}),
                line: {{ color: 'red', width: 2, dash: 'dash' }}
            }}],
            annotations: [{{
                x: 4.5, y: Math.max(...{json.dumps(rvc_counts)}) * 0.9,
                text: '180% Threshold',
                showarrow: false,
                font: {{ color: 'red' }}
            }}]
        }});

        // Commodity Chart
        Plotly.newPlot('commodity-chart', [{{
            y: {json.dumps(commodity_names)},
            x: {json.dumps(commodity_rvc)},
            type: 'bar',
            orientation: 'h',
            marker: {{
                color: {json.dumps(commodity_rvc)}.map(v => v > 180 ? '#c53030' : '#2b6cb0')
            }}
        }}], {{
            title: 'Average R/VC by Commodity (Top 10)',
            xaxis: {{ title: 'Average R/VC Ratio (%)' }},
            margin: {{ l: 200 }},
            shapes: [{{
                type: 'line',
                x0: 180, x1: 180,
                y0: -0.5, y1: 9.5,
                line: {{ color: 'red', width: 2, dash: 'dash' }}
            }}]
        }});

        // Distance Chart
        Plotly.newPlot('distance-chart', [{{
            x: {json.dumps(distance_names)},
            y: {json.dumps(distance_rvc)},
            type: 'bar',
            marker: {{
                color: {json.dumps(distance_rvc)}.map(v => v > 180 ? '#c53030' : '#2b6cb0')
            }}
        }}], {{
            title: 'Average R/VC by Distance Band',
            yaxis: {{ title: 'Average R/VC Ratio (%)' }},
            shapes: [{{
                type: 'line',
                x0: -0.5, x1: 3.5,
                y0: 180, y1: 180,
                line: {{ color: 'red', width: 2, dash: 'dash' }}
            }}]
        }});

        // Cement Chart
        Plotly.newPlot('cement-chart', [{{
            x: {json.dumps(cement_dist)},
            y: {json.dumps(cement_rvc)},
            type: 'bar',
            marker: {{
                color: {json.dumps(cement_rvc)}.map(v => v > 180 ? '#c53030' : '#2b6cb0')
            }}
        }}], {{
            title: 'Cement R/VC by Distance',
            yaxis: {{ title: 'Average R/VC Ratio (%)' }},
            shapes: [{{
                type: 'line',
                x0: -0.5, x1: 3.5,
                y0: 180, y1: 180,
                line: {{ color: 'red', width: 2, dash: 'dash' }}
            }}]
        }});
    </script>
</body>
</html>
"""

# Write report
output_dir = Path(__file__).parent / "reports"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "urcs_rate_benchmarking_report.html"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Report generated: {output_file}")
