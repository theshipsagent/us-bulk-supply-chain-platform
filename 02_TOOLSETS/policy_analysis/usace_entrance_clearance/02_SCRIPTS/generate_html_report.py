"""
USACE Market Study - HTML Report Generator
Assembles analysis and interactive visualizations into HTML report
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USACE Port Clearance Market Study 2023</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .metadata {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}

        .metadata-item {{
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #2a5298;
            border-radius: 4px;
        }}

        .metadata-item strong {{
            display: block;
            color: #1e3c72;
            margin-bottom: 5px;
        }}

        nav {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        nav ul {{
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}

        nav a {{
            text-decoration: none;
            color: #1e3c72;
            padding: 10px 20px;
            border-radius: 5px;
            background: #e3f2fd;
            transition: all 0.3s;
            font-weight: 500;
        }}

        nav a:hover {{
            background: #2a5298;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            color: #1e3c72;
            font-size: 2em;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 3px solid #2a5298;
        }}

        .section h3 {{
            color: #2a5298;
            font-size: 1.5em;
            margin: 25px 0 15px 0;
        }}

        .section p {{
            margin-bottom: 15px;
            line-height: 1.8;
        }}

        .chart-container {{
            margin: 30px 0;
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}

        .key-findings {{
            background: #e8f5e9;
            padding: 20px;
            border-left: 5px solid #4caf50;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .key-findings h3 {{
            color: #2e7d32;
            margin-bottom: 15px;
        }}

        .key-findings ul {{
            list-style-position: inside;
            padding-left: 10px;
        }}

        .key-findings li {{
            margin-bottom: 10px;
            padding-left: 10px;
        }}

        .insight-box {{
            background: #fff3e0;
            padding: 20px;
            border-left: 5px solid #ff9800;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .insight-box h4 {{
            color: #e65100;
            margin-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }}

        table th {{
            background: #2a5298;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        table tr:hover {{
            background: #f5f5f5;
        }}

        table tr:nth-child(even) {{
            background: #fafafa;
        }}

        footer {{
            background: #1e3c72;
            color: white;
            text-align: center;
            padding: 20px;
            margin-top: 40px;
            border-radius: 8px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
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
            margin-bottom: 10px;
            color: white;
        }}

        .stat-card p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8em;
            }}

            nav ul {{
                flex-direction: column;
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>🚢 USACE Port Clearance Market Study</h1>
        <p>Vessel Type &amp; Trade Pattern Analysis - 2023</p>
        <p style="font-size: 0.9em; margin-top: 10px;">Generated: {report_date}</p>
    </header>

    <div class="container">
        <!-- Metadata -->
        <div class="metadata">
            <div class="metadata-item">
                <strong>Total Revenue</strong>
                <span>${total_revenue_m:.1f}M</span>
            </div>
            <div class="metadata-item">
                <strong>Total Clearances</strong>
                <span>{total_clearances:,}</span>
            </div>
            <div class="metadata-item">
                <strong>Vessel Types</strong>
                <span>{total_vessel_types}</span>
            </div>
            <div class="metadata-item">
                <strong>Regions</strong>
                <span>{total_regions}</span>
            </div>
            <div class="metadata-item">
                <strong>Average Fee</strong>
                <span>${avg_fee:,.0f}</span>
            </div>
            <div class="metadata-item">
                <strong>Grain Shipments</strong>
                <span>{grain_clearances:,}</span>
            </div>
        </div>

        <!-- Navigation -->
        <nav>
            <ul>
                <li><a href="#executive-summary">Executive Summary</a></li>
                <li><a href="#market-overview">Market Overview</a></li>
                <li><a href="#vessel-types">Vessel Types</a></li>
                <li><a href="#regional-trade">Regional Trade</a></li>
                <li><a href="#type-region">Type × Region</a></li>
                <li><a href="#cargo-flows">Cargo Flows</a></li>
                <li><a href="#grain-analysis">Grain Analysis</a></li>
                <li><a href="#conclusions">Conclusions</a></li>
            </ul>
        </nav>

        {content}

        <footer>
            <p><strong>USACE Port Clearance Market Study 2023</strong></p>
            <p>Analysis of {total_clearances:,} clearances across {total_regions} port regions</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Report generated: {report_date}</p>
        </footer>
    </div>
</body>
</html>
"""


def generate_executive_summary(results: Dict[str, Any]) -> str:
    """Generate executive summary section."""
    market = results['market']
    vessel_types = results['vessel_types']
    regional = results['regional_trade']
    grain = results['grain']

    return f"""
    <section id="executive-summary" class="section">
        <h2>1. Executive Summary</h2>

        <div class="key-findings">
            <h3>Key Findings</h3>
            <ul>
                <li><strong>Market Size:</strong> ${market['total_revenue']/1e6:.1f}M in revenue from {market['total_clearances']:,} clearances</li>
                <li><strong>Vessel Diversity:</strong> {vessel_types['total_types']} distinct vessel types operating across {regional['region_stats_df'].shape[0]} regions</li>
                <li><strong>Top Vessel Type:</strong> {vessel_types['type_stats_df'].iloc[0]['Ships_Type']} generated ${vessel_types['type_stats_df'].iloc[0]['Total_Revenue']/1e6:.1f}M ({vessel_types['type_stats_df'].iloc[0]['Revenue_Pct']:.1f}% of market)</li>
                <li><strong>Regional Leader:</strong> {regional['region_stats_df'].iloc[0]['Port_Region']} leads with ${regional['region_stats_df'].iloc[0]['Total_Revenue']/1e6:.1f}M ({regional['region_stats_df'].iloc[0]['Revenue_Pct']:.1f}% of market)</li>
                <li><strong>Average Fee:</strong> ${market['avg_fee']:,.0f} per clearance</li>
                <li><strong>Grain Exports:</strong> {grain['grain_clearances']:,} shipments ({grain['grain_pct']:.1f}% of total) carrying {grain['grain_tonnage']:,.0f} MT</li>
            </ul>
        </div>

        <div class="insight-box">
            <h4>Market Characteristics</h4>
            <p>The US port clearance market demonstrates significant diversity in vessel types and regional trade patterns.
            The top vessel types account for the majority of revenue, while regional distribution shows clear geographic
            specialization based on trade routes and cargo types. Grain exports represent a small but strategically
            important segment of the market.</p>
        </div>
    </section>
    """


def generate_market_overview_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate market overview section."""
    return f"""
    <section id="market-overview" class="section">
        <h2>2. Market Overview</h2>

        <p>The USACE port clearance market in 2023 processed {results['market']['total_clearances']:,} clearances
        generating ${results['market']['total_revenue']/1e6:.1f}M in total revenue. The market encompasses
        {results['market']['total_vessel_types']} distinct vessel types operating across {results['market']['total_regions']}
        port regions.</p>

        <div class="chart-container">
            {figures.get('metrics_overview', '<p>Chart not available</p>')}
        </div>

        <h3>Market Composition</h3>
        <p>The market serves diverse cargo classes with varying vessel requirements, from bulk carriers to specialized
        container ships. Average clearance fees reflect vessel size, cargo type, and port region characteristics.</p>
    </section>
    """


def generate_vessel_type_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate vessel type analysis section."""
    top_type = results['vessel_types']['type_stats_df'].iloc[0]

    return f"""
    <section id="vessel-types" class="section">
        <h2>3. Vessel Type Analysis</h2>

        <p>Analysis of {results['vessel_types']['total_types']} distinct vessel types reveals significant variation
        in revenue contribution and operational patterns. The market is dominated by bulk carriers and container ships,
        reflecting major US trade flows.</p>

        <div class="insight-box">
            <h4>Top Vessel Type</h4>
            <p><strong>{top_type['Ships_Type']}</strong> leads the market with ${top_type['Total_Revenue']/1e6:.1f}M
            in revenue ({top_type['Revenue_Pct']:.1f}% of total) across {top_type['Clearances']:,} clearances.</p>
        </div>

        <div class="chart-container">
            <h3>Revenue by Vessel Type</h3>
            {figures.get('vessel_type_revenue', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Cargo Class Distribution</h3>
            {figures.get('cargo_treemap', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Vessel Type Performance Matrix</h3>
            {figures.get('type_scatter', '<p>Chart not available</p>')}
        </div>
    </section>
    """


def generate_regional_trade_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate regional trade pattern section."""
    top_region = results['regional_trade']['region_stats_df'].iloc[0]

    return f"""
    <section id="regional-trade" class="section">
        <h2>4. Regional Trade Patterns</h2>

        <p>Port clearances are distributed across {results['regional_trade']['region_stats_df'].shape[0]} distinct
        regions, each with unique vessel type preferences and trade characteristics. Regional specialization reflects
        geographic advantages, infrastructure, and trade route positioning.</p>

        <div class="insight-box">
            <h4>Leading Region</h4>
            <p><strong>{top_region['Port_Region']}</strong> dominates with ${top_region['Total_Revenue']/1e6:.1f}M
            in revenue ({top_region['Revenue_Pct']:.1f}% of market) from {top_region['Clearances']:,} clearances.</p>
        </div>

        <div class="chart-container">
            <h3>Revenue by Port Region</h3>
            {figures.get('region_revenue', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Coast Distribution</h3>
            {figures.get('coast_sunburst', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Regional Market Share Comparison</h3>
            {figures.get('region_radar', '<p>Chart not available</p>')}
        </div>
    </section>
    """


def generate_type_region_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate vessel type × region analysis section."""
    return f"""
    <section id="type-region" class="section">
        <h2>5. Vessel Type × Region Analysis</h2>

        <p>The intersection of vessel types and port regions reveals clear patterns of specialization.
        Certain regions show strong preferences for specific vessel types based on cargo handling
        capabilities, depth restrictions, and trade route optimization.</p>

        <div class="chart-container">
            <h3>Revenue Heatmap: Vessel Types × Regions</h3>
            {figures.get('type_region_heatmap', '<p>Chart not available</p>')}
        </div>

        <div class="key-findings">
            <h3>Regional Specialization Insights</h3>
            <ul>
                <li>Different regions show distinct vessel type preferences</li>
                <li>Infrastructure and depth limitations influence vessel type distribution</li>
                <li>Trade routes and cargo types drive regional vessel specialization</li>
                <li>Some vessel types operate nationally while others concentrate in specific regions</li>
            </ul>
        </div>
    </section>
    """


def generate_cargo_flows_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate cargo flows and trade patterns section."""
    return f"""
    <section id="cargo-flows" class="section">
        <h2>6. Cargo Flows & Trade Patterns</h2>

        <p>Analysis of origin-destination patterns reveals the major trade lanes flowing through US ports.
        These patterns reflect global supply chains, bilateral trade relationships, and US import/export strengths.</p>

        <div class="chart-container">
            <h3>Top Origin Countries</h3>
            {figures.get('origin_countries', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Top Destination Countries</h3>
            {figures.get('dest_countries', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Trade Lane Flows: Origin → Region → Destination</h3>
            {figures.get('trade_sankey', '<p>Chart not available</p>')}
        </div>

        <div class="insight-box">
            <h4>Trade Pattern Insights</h4>
            <p>Major trade flows show concentration in specific origin-destination pairs, with US port regions
            serving as critical nodes in global supply chains. Container traffic dominates certain routes while
            bulk commodities flow through specialized ports.</p>
        </div>
    </section>
    """


def generate_grain_analysis_section(results: Dict[str, Any], figures: Dict[str, str]) -> str:
    """Generate grain shipment analysis section."""
    grain = results['grain']

    return f"""
    <section id="grain-analysis" class="section">
        <h2>7. Grain Export Analysis</h2>

        <p>Grain exports represent a strategically important segment, with {grain['grain_clearances']:,}
        shipments ({grain['grain_pct']:.1f}% of total clearances) carrying {grain['grain_tonnage']:,.0f} MT
        and generating ${grain['grain_revenue']/1e6:.1f}M in revenue.</p>

        <div class="chart-container">
            <h3>Grain Shipments by Region</h3>
            {figures.get('grain_by_region', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Grain Export Destinations</h3>
            {figures.get('grain_dest_pie', '<p>Chart not available</p>')}
        </div>

        <div class="chart-container">
            <h3>Grain Vessel Types</h3>
            {figures.get('grain_vessel_types', '<p>Chart not available</p>')}
        </div>

        <div class="key-findings">
            <h3>Grain Export Insights</h3>
            <ul>
                <li>Grain shipments concentrated in specific export regions with deep-water facilities</li>
                <li>Bulk carriers dominate grain transportation</li>
                <li>Major destinations reflect US agricultural export markets</li>
                <li>Seasonal patterns influence grain shipment volumes</li>
            </ul>
        </div>
    </section>
    """


def generate_conclusions_section(results: Dict[str, Any]) -> str:
    """Generate conclusions and insights section."""
    market = results['market']
    vessel_types = results['vessel_types']
    regional = results['regional_trade']

    return f"""
    <section id="conclusions" class="section">
        <h2>8. Conclusions & Strategic Insights</h2>

        <div class="key-findings">
            <h3>Key Market Insights</h3>
            <ul>
                <li><strong>Vessel Type Diversity:</strong> {vessel_types['total_types']} vessel types reflect
                specialized cargo requirements and trade patterns</li>

                <li><strong>Regional Specialization:</strong> Clear geographic concentration with top region
                accounting for {regional['region_stats_df'].iloc[0]['Revenue_Pct']:.1f}% of market revenue</li>

                <li><strong>Trade Pattern Concentration:</strong> Major trade lanes show established
                origin-destination relationships driving consistent vessel flows</li>

                <li><strong>Infrastructure Impact:</strong> Port capabilities and depth restrictions influence
                vessel type distribution across regions</li>

                <li><strong>Grain Export Importance:</strong> Strategic agricultural exports require dedicated
                infrastructure and vessel types</li>

                <li><strong>Market Opportunities:</strong> Underserved vessel types and regions present
                potential growth opportunities</li>
            </ul>
        </div>

        <div class="insight-box">
            <h4>Strategic Considerations</h4>
            <p>The USACE port clearance market demonstrates mature infrastructure supporting diverse vessel
            types and trade patterns. Future growth will likely come from increased container traffic, expanded
            bulk commodity exports, and infrastructure investments enabling larger vessel access.</p>

            <p>Regional specialization creates competitive advantages but also concentration risk. Diversification
            of vessel types and trade lanes can enhance resilience while maintaining operational efficiency.</p>
        </div>

        <div class="stats-grid" style="margin-top: 30px;">
            <div class="stat-card">
                <h3>${market['total_revenue']/1e6:.1f}M</h3>
                <p>Total Market Revenue</p>
            </div>
            <div class="stat-card">
                <h3>{market['total_clearances']:,}</h3>
                <p>Total Clearances</p>
            </div>
            <div class="stat-card">
                <h3>{vessel_types['total_types']}</h3>
                <p>Vessel Types</p>
            </div>
            <div class="stat-card">
                <h3>{regional['region_stats_df'].shape[0]}</h3>
                <p>Port Regions</p>
            </div>
        </div>
    </section>
    """


def create_html_report(results: Dict[str, Any], figures: Dict[str, str], output_path: str) -> str:
    """Create comprehensive HTML report."""
    print("\n" + "="*60)
    print("Generating HTML Report")
    print("="*60 + "\n")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output file: {output_path}")

    # Generate sections
    print("Generating sections...")
    sections = [
        generate_executive_summary(results),
        generate_market_overview_section(results, figures),
        generate_vessel_type_section(results, figures),
        generate_regional_trade_section(results, figures),
        generate_type_region_section(results, figures),
        generate_cargo_flows_section(results, figures),
        generate_grain_analysis_section(results, figures),
        generate_conclusions_section(results)
    ]

    content = '\n'.join(sections)

    # Format template
    market = results['market']
    grain = results['grain']

    html = HTML_TEMPLATE.format(
        report_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        total_revenue_m=market['total_revenue'] / 1e6,
        total_clearances=market['total_clearances'],
        total_vessel_types=market['total_vessel_types'],
        total_regions=market['total_regions'],
        avg_fee=market['avg_fee'],
        grain_clearances=grain['grain_clearances'],
        content=content
    )

    # Write HTML file
    print("Writing HTML file...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = Path(output_path).stat().st_size / 1024  # KB
    print(f"\nHTML report generated successfully!")
    print(f"File size: {file_size:.2f} KB")
    print("="*60 + "\n")

    return output_path


if __name__ == '__main__':
    print("HTML Report Generator module loaded successfully")
    print("Run from main orchestrator to generate report")
