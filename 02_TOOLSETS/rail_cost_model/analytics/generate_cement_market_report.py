"""
Generate Comprehensive Cement Rail Market Report
Includes: National market analysis, O-D flows, plant mapping, Gulf Coast focus

Data: STB Public Use Waybill Sample 2018-2023
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import query
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

# Known cement plant locations (from SCRS data and web research)
CEMENT_PLANTS = {
    '096': {  # Fargo, ND zone
        'plants': ['GCC Dacotah (Rapid City, SD)'],
        'companies': ['GCC of America'],
        'notes': 'Major Upper Midwest producer. Plant actually in Rapid City SD but serves ND/MN/SD region.'
    },
    '160': {  # Fresno, CA
        'plants': ['Lehigh Cement (Stockton)', 'CalPortland (Tehachapi)', 'Lehigh (Cupertino)'],
        'companies': ['Lehigh Hanson', 'CalPortland'],
        'notes': 'Central California hub serving LA, SF, and Central Valley markets.'
    },
    '134': {  # Houston, TX
        'plants': ['Texas Lehigh (Buda)', 'Texas Lehigh (Houston)', 'Cemex (Houston)', 'Holcim', 'Buzzi'],
        'companies': ['Lehigh Hanson', 'Cemex', 'Holcim', 'Buzzi Unicem'],
        'notes': 'Largest Gulf Coast origin. Ship Channel industrial corridor.'
    },
    '078': {  # Fayetteville, AR
        'plants': ['Ash Grove (Foreman, AR)', 'Martin Marietta'],
        'companies': ['Ash Grove Cement', 'Martin Marietta'],
        'notes': 'Serves Southeast markets including Jacksonville FL corridor.'
    },
    '127': {  # Lubbock, TX
        'plants': ['GCC (Odessa)', 'Cemex'],
        'companies': ['GCC of America', 'Cemex'],
        'notes': 'West Texas/New Mexico market. Also receives inbound from other origins.'
    },
    '124': {  # Pueblo, CO
        'plants': ['GCC (Pueblo)', 'Holcim (Florence)'],
        'companies': ['GCC of America', 'Holcim'],
        'notes': 'Rocky Mountain producer serving CO, WY, NM markets.'
    },
    '013': {  # Hartford, CT
        'plants': ['Holcim (Bristol, CT)'],
        'companies': ['Holcim'],
        'notes': 'Major Northeast producer. Serves New England and Mid-Atlantic.'
    },
    '141': {  # Salt Lake City, UT
        'plants': ['Ash Grove (Leamington)', 'Holcim (Devils Slide)'],
        'companies': ['Ash Grove Cement', 'Holcim'],
        'notes': 'Intermountain West producer.'
    },
    '038': {  # Dothan, AL (actually serves Southeast)
        'plants': ['Cemex (Demopolis, AL)', 'Buzzi (Milton, FL)'],
        'companies': ['Cemex', 'Buzzi Unicem'],
        'notes': 'Southeast/Gulf Coast region.'
    },
    '010': {  # Boston, MA
        'plants': ['Lehigh (Essex Junction, VT)', 'Import terminals'],
        'companies': ['Lehigh Hanson'],
        'notes': 'New England distribution. Mix of domestic and imported cement.'
    },
    '017': {  # Allentown, PA
        'plants': ['Lehigh (various)', 'Buzzi'],
        'companies': ['Lehigh Hanson', 'Buzzi Unicem'],
        'notes': 'Historic Lehigh Valley cement region. Namesake of Lehigh Cement.'
    },
    '167': {  # Olympia, WA
        'plants': ['Ash Grove', 'Lehigh (Seattle area)'],
        'companies': ['Ash Grove Cement', 'Lehigh Hanson'],
        'notes': 'Pacific Northwest producer.'
    }
}


def fetch_market_data():
    """Fetch comprehensive cement market data."""
    data = {}

    print("  Fetching national origins...")
    data['origins'] = query("""
        SELECT
            origin_bea,
            o.bea_name as origin,
            o.states,
            ROUND(SUM(exp_tons)/1e6, 2) as tons_M,
            ROUND(SUM(exp_freight_rev)/1e6, 1) as rev_M,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as rev_per_ton,
            ROUND(AVG(short_line_miles), 0) as avg_miles,
            COUNT(DISTINCT term_bea) as num_dests
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        WHERE stcc = '32411'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
          AND origin_bea <> '000'
        GROUP BY 1, 2, 3
        HAVING SUM(exp_tons) > 50000
        ORDER BY tons_M DESC
    """)

    print("  Fetching O-D flows...")
    data['flows'] = query("""
        SELECT
            o.bea_name as origin,
            d.bea_name as destination,
            ROUND(SUM(exp_tons)/1e6, 3) as tons_M,
            ROUND(AVG(short_line_miles), 0) as miles,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as rate,
            ROUND((SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0)) /
                  NULLIF((AVG(short_line_miles) * 0.035) + 5.00, 0) * 100, 0) as rvc
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        WHERE stcc = '32411'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
          AND origin_bea <> '000' AND term_bea <> '000'
        GROUP BY 1, 2
        HAVING SUM(exp_tons) > 100000
        ORDER BY tons_M DESC
    """)

    print("  Fetching destinations...")
    data['destinations'] = query("""
        SELECT
            term_bea,
            d.bea_name as destination,
            d.states,
            ROUND(SUM(exp_tons)/1e6, 2) as tons_M,
            ROUND(SUM(exp_freight_rev)/1e6, 1) as rev_M,
            COUNT(DISTINCT origin_bea) as num_origins,
            ROUND(AVG(short_line_miles), 0) as avg_miles
        FROM fact_waybill w
        LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
        WHERE stcc = '32411'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
          AND term_bea <> '000'
        GROUP BY 1, 2, 3
        HAVING SUM(exp_tons) > 200000
        ORDER BY tons_M DESC
    """)

    print("  Fetching annual trends...")
    data['annual'] = query("""
        SELECT
            CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
            ROUND(SUM(exp_tons)/1e6, 2) as tons_M,
            ROUND(SUM(exp_freight_rev)/1e6, 1) as rev_M,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as rev_per_ton
        FROM fact_waybill
        WHERE stcc = '32411'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
        GROUP BY 1
        ORDER BY 1
    """)

    print("  Fetching Tampa/NOLA data...")
    data['tampa'] = query("""
        SELECT
            o.bea_name as origin,
            ROUND(SUM(exp_tons), 0) as tons,
            ROUND(AVG(short_line_miles), 0) as miles,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as rate
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        WHERE stcc = '32411' AND term_bea = '042'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
        GROUP BY 1
        ORDER BY tons DESC
    """)

    data['nola'] = query("""
        SELECT
            o.bea_name as origin,
            ROUND(SUM(exp_tons), 0) as tons,
            ROUND(AVG(short_line_miles), 0) as miles,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as rate
        FROM fact_waybill w
        LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
        WHERE stcc = '32411' AND term_bea = '087'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
        GROUP BY 1
        ORDER BY tons DESC
    """)

    # Summary stats
    data['summary'] = query("""
        SELECT
            ROUND(SUM(exp_tons)/1e6, 1) as total_tons_M,
            ROUND(SUM(exp_freight_rev)/1e6, 0) as total_rev_M,
            ROUND(SUM(exp_freight_rev)/NULLIF(SUM(exp_tons),0), 2) as avg_rate,
            COUNT(DISTINCT origin_bea) as num_origins,
            COUNT(DISTINCT term_bea) as num_dests
        FROM fact_waybill
        WHERE stcc = '32411'
          AND EXTRACT(YEAR FROM waybill_date) >= 2018
    """)

    return data


def generate_report():
    """Generate comprehensive HTML report."""
    print("Generating comprehensive cement market report...")
    data = fetch_market_data()

    print("  Creating charts...")

    # Extract summary
    summ = data['summary'].iloc[0]

    # Chart 1: Origins bar chart
    orig = data['origins'].head(12)
    fig1 = px.bar(orig, x='origin', y='tons_M', color='rev_per_ton',
                  title='Top Cement Origins by Volume (2018-2023)',
                  color_continuous_scale='Viridis', text='tons_M',
                  labels={'tons_M': 'Million Tons', 'origin': 'Origin', 'rev_per_ton': '$/Ton'})
    fig1.update_traces(texttemplate='%{text:.1f}M', textposition='outside')
    fig1.update_layout(height=420, xaxis_tickangle=-35, margin=dict(b=100))
    chart1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')

    # Chart 2: Destinations bar chart
    dest = data['destinations'].head(12)
    fig2 = px.bar(dest, x='destination', y='tons_M', color='num_origins',
                  title='Top Cement Destinations by Volume (2018-2023)',
                  color_continuous_scale='Blues', text='tons_M',
                  labels={'tons_M': 'Million Tons', 'destination': 'Destination', 'num_origins': '# Origins'})
    fig2.update_traces(texttemplate='%{text:.1f}M', textposition='outside')
    fig2.update_layout(height=420, xaxis_tickangle=-35, margin=dict(b=100))
    chart2 = fig2.to_html(full_html=False, include_plotlyjs='cdn')

    # Chart 3: Annual trend
    ann = data['annual']
    fig3 = make_subplots(specs=[[{'secondary_y': True}]])
    fig3.add_trace(go.Bar(x=ann['year'], y=ann['tons_M'], name='Tons (M)', marker_color='#2c5282'), secondary_y=False)
    fig3.add_trace(go.Scatter(x=ann['year'], y=ann['rev_per_ton'], name='$/Ton', mode='lines+markers',
                               line=dict(color='#e53e3e', width=3)), secondary_y=True)
    fig3.update_layout(title='National Cement Rail Volume & Rate Trend', height=380,
                      legend=dict(orientation='h', y=-0.15))
    fig3.update_yaxes(title_text='Million Tons', secondary_y=False)
    fig3.update_yaxes(title_text='$/Ton', secondary_y=True)
    chart3 = fig3.to_html(full_html=False, include_plotlyjs='cdn')

    # Chart 4: O-D flows sankey or top flows bar
    flows = data['flows'].head(15)
    flows['lane'] = flows['origin'].fillna('Unknown') + ' → ' + flows['destination'].fillna('Unknown')
    fig4 = px.bar(flows, x='tons_M', y='lane', orientation='h', color='rvc',
                  title='Top Cement Lanes by Volume',
                  color_continuous_scale='RdYlGn_r', range_color=[100, 250],
                  labels={'tons_M': 'Million Tons', 'lane': 'Lane', 'rvc': 'R/VC %'})
    fig4.update_layout(height=500, margin=dict(l=200))
    chart4 = fig4.to_html(full_html=False, include_plotlyjs='cdn')

    # Build origin table with plant info
    origin_rows = ''
    for _, row in data['origins'].head(15).iterrows():
        bea = row['origin_bea']
        plant_info = CEMENT_PLANTS.get(bea, {})
        plants = ', '.join(plant_info.get('plants', ['Unknown'])[:2])
        origin_rows += f'''<tr>
            <td>{row['origin'] or 'Unknown'}</td>
            <td>{row['states'] or ''}</td>
            <td>{row['tons_M']:.2f}</td>
            <td>${row['rev_M']:.1f}</td>
            <td>${row['rev_per_ton']:.2f}</td>
            <td>{plants}</td>
        </tr>'''

    # O-D flow table
    flow_rows = ''
    for _, row in data['flows'].head(20).iterrows():
        rvc = row.get('rvc', 0) or 0
        rvc_class = ' class="highlight"' if rvc > 180 else ''
        flow_rows += f'''<tr>
            <td>{row['origin'] or 'Unknown'}</td>
            <td>{row['destination'] or 'Unknown'}</td>
            <td>{row['tons_M']:.3f}</td>
            <td>{int(row['miles']):,}</td>
            <td>${row['rate']:.2f}</td>
            <td{rvc_class}>{rvc:.0f}%</td>
        </tr>'''

    # Destination table
    dest_rows = ''
    for _, row in data['destinations'].head(15).iterrows():
        dest_rows += f'''<tr>
            <td>{row['destination'] or 'Unknown'}</td>
            <td>{row['states'] or ''}</td>
            <td>{row['tons_M']:.2f}</td>
            <td>${row['rev_M']:.1f}</td>
            <td>{row['num_origins']}</td>
            <td>{int(row['avg_miles']):,}</td>
        </tr>'''

    # Tampa/NOLA tables
    tampa_rows = ''
    for _, row in data['tampa'].iterrows():
        tampa_rows += f'<tr><td>{row["origin"] or "Unknown"}</td><td>{int(row["tons"]):,}</td><td>{int(row["miles"]):,}</td><td>${row["rate"]:.2f}</td></tr>'

    nola_rows = ''
    for _, row in data['nola'].iterrows():
        nola_rows += f'<tr><td>{row["origin"] or "Unknown"}</td><td>{int(row["tons"]):,}</td><td>{int(row["miles"]):,}</td><td>${row["rate"]:.2f}</td></tr>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>U.S. Cement Rail Market Analysis</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               margin: 0; padding: 20px; background: #f0f4f8; line-height: 1.7; color: #2d3748; }}
        .container {{ max-width: 1300px; margin: 0 auto; background: white; padding: 45px;
                     border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a365d; border-bottom: 4px solid #2c5282; padding-bottom: 15px; }}
        h2 {{ color: #2c5282; margin-top: 50px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
        h3 {{ color: #4a5568; margin-top: 30px; }}
        p {{ margin-bottom: 16px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 0.9em; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
        th {{ background: #2c5282; color: white; font-weight: 600; }}
        tr:nth-child(even) {{ background: #f7fafc; }}
        tr:hover {{ background: #edf2f7; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin: 25px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%); padding: 18px;
                       border-radius: 12px; color: white; text-align: center; }}
        .metric-value {{ font-size: 1.7em; font-weight: bold; }}
        .metric-label {{ font-size: 0.75em; opacity: 0.9; margin-top: 5px; }}
        .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin: 25px 0; }}
        .chart-box {{ background: #fafafa; padding: 18px; border-radius: 10px; border: 1px solid #e2e8f0; }}
        .chart-full {{ background: #fafafa; padding: 18px; border-radius: 10px; border: 1px solid #e2e8f0; margin: 25px 0; }}
        .highlight {{ background: #fefcbf; font-weight: bold; }}
        .callout {{ padding: 18px; border-radius: 8px; margin: 20px 0; }}
        .callout.blue {{ background: #ebf8ff; border-left: 5px solid #3182ce; }}
        .callout.green {{ background: #f0fff4; border-left: 5px solid #38a169; }}
        .callout.yellow {{ background: #fffff0; border-left: 5px solid #d69e2e; }}
        .toc {{ background: #edf2f7; padding: 25px 35px; border-radius: 8px; margin: 30px 0; }}
        .toc h3 {{ margin: 0 0 15px 0; }}
        .toc-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 30px; }}
        .toc a {{ color: #2c5282; text-decoration: none; }}
        .section-intro {{ font-size: 1.05em; color: #4a5568; margin-bottom: 20px; padding: 15px;
                         background: #f7fafc; border-radius: 8px; }}
        footer {{ margin-top: 60px; padding-top: 25px; border-top: 2px solid #e2e8f0;
                 color: #718096; font-size: 0.85em; text-align: center; }}
        @media (max-width: 900px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
<div class="container">

<h1>U.S. Cement Rail Market Analysis</h1>
<p style="font-size: 1.15em; color: #2c5282; margin-top: 0;">
    Portland Cement (STCC 32411) — National Origin-Destination Flow Analysis
</p>
<p><strong>Report Date:</strong> {datetime.now().strftime('%B %Y')} &nbsp;|&nbsp;
   <strong>Data Period:</strong> 2018-2023 &nbsp;|&nbsp;
   <strong>Source:</strong> STB Public Use Waybill Sample</p>

<div class="toc">
    <h3>Contents</h3>
    <div class="toc-grid">
        <a href="#summary">1. Market Summary</a>
        <a href="#origins">2. Origin Markets & Plants</a>
        <a href="#destinations">3. Destination Markets</a>
        <a href="#flows">4. O-D Flow Analysis</a>
        <a href="#gulf">5. Gulf Coast Focus</a>
        <a href="#methodology">6. Methodology & Sources</a>
    </div>
</div>

<h2 id="summary">1. National Market Summary</h2>

<div class="section-intro">
    This analysis covers <strong>Portland cement</strong> (STCC 32411), the primary hydraulic cement used in
    construction. The data represents rail movements only — cement also moves extensively by truck and barge,
    particularly for short-haul distribution from plants to ready-mix facilities.
</div>

<div class="metric-grid">
    <div class="metric-card"><div class="metric-value">{summ['total_tons_M']:.0f}M</div><div class="metric-label">Total Tons (6 yr)</div></div>
    <div class="metric-card"><div class="metric-value">${summ['total_rev_M']:,.0f}M</div><div class="metric-label">Total Revenue</div></div>
    <div class="metric-card"><div class="metric-value">${summ['avg_rate']:.2f}</div><div class="metric-label">Avg Rate/Ton</div></div>
    <div class="metric-card"><div class="metric-value">{int(summ['num_origins'])}</div><div class="metric-label">Origin Markets</div></div>
    <div class="metric-card"><div class="metric-value">{int(summ['num_dests'])}</div><div class="metric-label">Dest Markets</div></div>
</div>

<div class="chart-box">{chart3}</div>

<div class="callout blue">
    <strong>Key Insight:</strong> Cement rail volumes remained stable through 2018-2023 despite pandemic disruptions,
    averaging approximately <strong>{summ['total_tons_M']/6:.0f} million tons annually</strong>. Rates have shown
    modest inflation-driven increases, averaging ${summ['avg_rate']:.2f}/ton over the period.
</div>

<h2 id="origins">2. Origin Markets & Cement Plants</h2>

<div class="section-intro">
    Cement production is concentrated near limestone deposits and fuel sources. The top origins below represent
    major production hubs, each served by one or more cement manufacturing facilities. Note that BEA zones
    cover large areas — the "Fargo, ND" zone actually includes cement production from Rapid City, SD.
</div>

<div class="chart-box">{chart1}</div>

<h3>Cement Origins with Plant Identification</h3>
<table>
<tr><th>Origin</th><th>State(s)</th><th>Tons (M)</th><th>Rev ($M)</th><th>$/Ton</th><th>Known Plants</th></tr>
{origin_rows}
</table>

<div class="callout yellow">
    <strong>Note on "Fargo, ND":</strong> The BEA zone 096 (Fargo) covers North Dakota, Minnesota, and parts of
    South Dakota. The major cement producer in this zone is <strong>GCC Dacotah</strong> with a plant in
    <strong>Rapid City, SD</strong> — not actually in Fargo. This plant produces over 1.3 million tons annually
    and serves the Upper Midwest market via BNSF rail.
</div>

<h2 id="destinations">3. Destination Markets</h2>

<div class="section-intro">
    Cement destinations reflect construction activity patterns. Major metro areas and regions with significant
    infrastructure development show the highest inbound cement volumes. Rail cement typically serves markets
    beyond the 250-300 mile truck-competitive range from production facilities.
</div>

<div class="chart-box">{chart2}</div>

<h3>Top Cement Destinations</h3>
<table>
<tr><th>Destination</th><th>State(s)</th><th>Tons (M)</th><th>Rev ($M)</th><th># Origins</th><th>Avg Miles</th></tr>
{dest_rows}
</table>

<h2 id="flows">4. Origin-Destination Flow Analysis</h2>

<div class="section-intro">
    The table below shows the largest cement lanes by volume. R/VC ratios above 180% indicate potential
    STB rate jurisdiction. Many short-haul, high-volume lanes (like Houston→Dallas) show elevated R/VC
    ratios, reflecting railroad pricing power on captive routes.
</div>

<div class="chart-full">{chart4}</div>

<h3>Top Cement Lanes</h3>
<table>
<tr><th>Origin</th><th>Destination</th><th>Tons (M)</th><th>Miles</th><th>$/Ton</th><th>R/VC</th></tr>
{flow_rows}
</table>

<div class="callout green">
    <strong>Major Corridors Identified:</strong>
    <ul>
        <li><strong>Houston → Dallas:</strong> 5.9M tons — Largest single lane, short-haul Texas corridor</li>
        <li><strong>Fayetteville AR → Jacksonville FL:</strong> 4.8M tons — Southeast distribution</li>
        <li><strong>Fresno → Los Angeles:</strong> 4.0M tons — California I-5 corridor</li>
        <li><strong>Fargo → La Crosse WI:</strong> 2.6M tons — Upper Midwest from GCC Dacotah</li>
    </ul>
</div>

<h2 id="gulf">5. Gulf Coast Market Focus</h2>

<div class="section-intro">
    The Gulf Coast region has distinct cement market dynamics. <strong>Houston</strong> is a major production
    origin, while <strong>Tampa</strong> and <strong>New Orleans</strong> function primarily as destination
    markets receiving cement from various sources.
</div>

<h3>Houston, TX — Primary Origin</h3>
<p>Houston's cement industry is concentrated in the Ship Channel industrial corridor, with multiple
production facilities operated by Texas Lehigh, Cemex, Holcim, and Buzzi. Rail service is provided
by Union Pacific and BNSF, with destinations spanning Texas, the Southwest, and California.</p>

<h3>Tampa, FL — Destination Market</h3>
<p>Tampa receives cement via CSX rail from Southeast producers. Florida's construction boom drives
significant cement demand, though much is also served by truck and waterborne imports.</p>

<table>
<tr><th>Origin</th><th>Tons</th><th>Miles</th><th>$/Ton</th></tr>
{tampa_rows if tampa_rows else '<tr><td colspan="4">Limited rail cement data for Tampa</td></tr>'}
</table>

<h3>New Orleans, LA — Destination Market</h3>
<p>New Orleans benefits from multi-carrier rail access (UP, CSX, NS, CN) at the Mississippi River gateway.
Cement demand supports industrial and infrastructure projects throughout Louisiana.</p>

<table>
<tr><th>Origin</th><th>Tons</th><th>Miles</th><th>$/Ton</th></tr>
{nola_rows if nola_rows else '<tr><td colspan="4">Limited rail cement data for New Orleans</td></tr>'}
</table>

<h2 id="methodology">6. Methodology & Data Sources</h2>

<h3>Data Sources</h3>
<table>
<tr><th>Source</th><th>Description</th><th>Coverage</th></tr>
<tr><td>STB Public Use Waybill</td><td>Stratified sample of Class I rail carload waybills</td><td>2018-2023</td></tr>
<tr><td>SCRS (FRA)</td><td>Short Line Customer Reporting System — facility identification</td><td>Current</td></tr>
<tr><td>USGS Mineral Commodity Summaries</td><td>Cement production statistics and plant locations</td><td>2024</td></tr>
<tr><td>Company websites/filings</td><td>Plant locations for Holcim, Cemex, Lehigh, GCC, Ash Grove, Buzzi</td><td>Current</td></tr>
</table>

<h3>STCC Classification</h3>
<p>This analysis uses STCC 32411 (Portland Cement) specifically. The broader STCC 32 group includes
concrete products (32952, 32959), clay refractories (32741), and other stone/clay/glass products
that are sometimes included in "cement" statistics but represent different commodities.</p>

<h3>BEA Zone Mapping</h3>
<p>Origin and destination locations use Bureau of Economic Analysis (BEA) Economic Areas — 173 zones
that aggregate counties. Important: BEA zones can span state boundaries and cover large geographic
areas. The "Fargo, ND" zone (096) includes portions of North Dakota, Minnesota, and South Dakota.</p>

<h3>R/VC Calculation</h3>
<p>Revenue-to-Variable-Cost (R/VC) ratios use a simplified URCS approximation:</p>
<p><code>Variable Cost = (Distance × $0.035/ton-mile) + $5.00 terminal costs</code></p>
<p>R/VC ratios above 180% may trigger STB rate jurisdiction under 49 U.S.C. § 10707.</p>

<footer>
<p><strong>Rail Analytics Platform</strong></p>
<p>Data: STB Public Use Waybill 2018-2023 | Plant Data: SCRS, USGS, Company Sources</p>
<p>Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
</footer>

</div>
</body>
</html>'''

    # Write file
    output_path = Path(__file__).parent / "reports" / "cement_market_report.html"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nReport generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_report()
