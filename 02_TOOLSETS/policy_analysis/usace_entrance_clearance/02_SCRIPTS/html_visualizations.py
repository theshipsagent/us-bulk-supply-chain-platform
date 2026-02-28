"""
USACE Market Study - HTML Visualization Module
Creates interactive plotly charts for HTML report
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List


def create_market_overview_charts(results: Dict[str, Any]) -> Dict[str, str]:
    """Create market overview interactive charts."""
    print("Creating market overview charts...")

    figures = {}
    market = results['market']

    # 1. Key metrics cards (using indicators)
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=('Total Revenue', 'Total Clearances', 'Vessel Types',
                       'Average Fee', 'Cargo Classes', 'Regions'),
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]]
    )

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['total_revenue'] / 1e6,
        number={'suffix': "M", 'prefix': "$"},
        title={'text': "Total Revenue"},
    ), row=1, col=1)

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['total_clearances'],
        number={'valueformat': ","},
        title={'text': "Total Clearances"},
    ), row=1, col=2)

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['total_vessel_types'],
        title={'text': "Vessel Types"},
    ), row=1, col=3)

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['avg_fee'],
        number={'prefix': "$", 'valueformat': ",.0f"},
        title={'text': "Average Fee"},
    ), row=2, col=1)

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['total_cargo_classes'],
        title={'text': "Cargo Classes"},
    ), row=2, col=2)

    fig.add_trace(go.Indicator(
        mode="number",
        value=market['total_regions'],
        title={'text': "Regions"},
    ), row=2, col=3)

    fig.update_layout(height=400, title_text="Market Overview - Key Metrics")
    figures['metrics_overview'] = fig.to_html(include_plotlyjs='cdn', div_id='metrics_overview')

    print(f"  Created market overview charts")
    return figures


def create_vessel_type_charts(results: Dict[str, Any]) -> Dict[str, str]:
    """Create vessel type analysis interactive charts."""
    print("Creating vessel type charts...")

    figures = {}
    vessel_types = results['vessel_types']

    # 1. Top 15 vessel types by revenue - Interactive bar chart
    top_15 = vessel_types['type_stats_df'].head(15).copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=top_15['Ships_Type'],
        x=top_15['Total_Revenue'] / 1e6,
        orientation='h',
        text=top_15['Revenue_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(
            color=top_15['Total_Revenue'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Revenue")
        ),
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:.1f}M<br>Clearances: %{customdata[0]:,}<br>Avg Fee: $%{customdata[1]:,.0f}<extra></extra>',
        customdata=top_15[['Clearances', 'Avg_Fee']].values
    ))

    fig.update_layout(
        title="Top 15 Vessel Types by Revenue",
        xaxis_title="Revenue ($ Million)",
        yaxis_title="Vessel Type",
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )

    figures['vessel_type_revenue'] = fig.to_html(include_plotlyjs='cdn', div_id='vessel_type_revenue')

    # 2. Cargo class distribution - Treemap
    cargo = vessel_types['cargo_revenue_df'].head(15).copy()
    fig = px.treemap(
        cargo,
        path=['ICST_DESC'],
        values='Total_Revenue',
        color='Total_Revenue',
        hover_data={'Clearances': True, 'Total_Tons': ':,.0f'},
        color_continuous_scale='RdYlGn',
        title="Cargo Class Revenue Distribution (Treemap)"
    )
    fig.update_traces(textinfo="label+value+percent parent")
    fig.update_layout(height=500)

    figures['cargo_treemap'] = fig.to_html(include_plotlyjs='cdn', div_id='cargo_treemap')

    # 3. Vessel type clearances vs revenue - Scatter
    top_20 = vessel_types['type_stats_df'].head(20).copy()
    top_20['Revenue_M'] = top_20['Total_Revenue'] / 1e6
    fig = px.scatter(
        top_20,
        x='Clearances',
        y='Revenue_M',
        size='Total_Tons',
        color='Avg_Fee',
        hover_name='Ships_Type',
        labels={'Revenue_M': 'Revenue ($M)', 'Clearances': 'Number of Clearances'},
        title="Vessel Types: Clearances vs Revenue (Top 20)",
        color_continuous_scale='Plasma'
    )
    fig.update_layout(height=500)

    figures['type_scatter'] = fig.to_html(include_plotlyjs='cdn', div_id='type_scatter')

    print(f"  Created {len(figures)} vessel type charts")
    return figures


def create_regional_charts(results: Dict[str, Any]) -> Dict[str, str]:
    """Create regional trade pattern interactive charts."""
    print("Creating regional charts...")

    figures = {}
    regional = results['regional_trade']

    # 1. Revenue by region - Interactive bar with coast breakdown
    region_df = regional['region_stats_df'].copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=region_df['Port_Region'],
        y=region_df['Total_Revenue'] / 1e6,
        text=region_df['Revenue_Pct'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(
            color=region_df['Total_Revenue'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Revenue")
        ),
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:.1f}M<br>Clearances: %{customdata[0]:,}<br>Avg Fee: $%{customdata[1]:,.0f}<br>Total Tons: %{customdata[2]:,.0f}<extra></extra>',
        customdata=region_df[['Clearances', 'Avg_Fee', 'Total_Tons']].values
    ))

    fig.update_layout(
        title="Revenue by Port Region",
        xaxis_title="Region",
        yaxis_title="Revenue ($ Million)",
        height=500,
        xaxis={'tickangle': -45}
    )

    figures['region_revenue'] = fig.to_html(include_plotlyjs='cdn', div_id='region_revenue')

    # 2. Coast distribution - Sunburst chart
    coast_df = regional['coast_stats_df'].copy()
    fig = px.sunburst(
        coast_df,
        path=['Port_Coast'],
        values='Total_Revenue',
        color='Total_Revenue',
        hover_data={'Clearances': True, 'Total_Tons': ':,.0f'},
        color_continuous_scale='Teal',
        title="Revenue Distribution by Coast"
    )
    fig.update_layout(height=500)

    figures['coast_sunburst'] = fig.to_html(include_plotlyjs='cdn', div_id='coast_sunburst')

    # 3. Region comparison - Radar chart
    region_df_top10 = region_df.head(10).copy()

    # Normalize metrics for radar chart
    metrics = ['Revenue_Pct', 'Clearance_Pct']
    fig = go.Figure()

    for idx, row in region_df_top10.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row['Revenue_Pct'], row['Clearance_Pct']],
            theta=['Revenue %', 'Clearance %'],
            fill='toself',
            name=row['Port_Region']
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(region_df_top10['Revenue_Pct'].max(),
                                                                  region_df_top10['Clearance_Pct'].max())])),
        showlegend=True,
        title="Regional Market Share Comparison (Top 10)",
        height=600
    )

    figures['region_radar'] = fig.to_html(include_plotlyjs='cdn', div_id='region_radar')

    print(f"  Created {len(figures)} regional charts")
    return figures


def create_vessel_type_region_heatmap(results: Dict[str, Any]) -> Dict[str, str]:
    """Create vessel type by region heatmap."""
    print("Creating vessel type x region heatmap...")

    figures = {}
    regional = results['regional_trade']
    vessel_types = results['vessel_types']

    # Get top 10 vessel types and top 10 regions
    top_types = vessel_types['type_stats_df'].head(10)['Ships_Type'].tolist()
    top_regions = regional['region_stats_df'].head(10)['Port_Region'].tolist()

    # Filter the matrix
    matrix = regional['region_type_matrix']
    matrix_filtered = matrix.loc[top_regions, top_types] / 1e6  # Convert to millions

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix_filtered.values,
        x=matrix_filtered.columns,
        y=matrix_filtered.index,
        colorscale='YlOrRd',
        text=matrix_filtered.values,
        texttemplate='$%{text:.1f}M',
        textfont={"size": 9},
        hovertemplate='Region: %{y}<br>Vessel Type: %{x}<br>Revenue: $%{z:.1f}M<extra></extra>',
        colorbar=dict(title="Revenue ($M)")
    ))

    fig.update_layout(
        title="Revenue Heatmap: Top 10 Vessel Types × Top 10 Regions",
        xaxis_title="Vessel Type",
        yaxis_title="Region",
        height=600,
        xaxis={'tickangle': -45}
    )

    figures['type_region_heatmap'] = fig.to_html(include_plotlyjs='cdn', div_id='type_region_heatmap')

    print(f"  Created heatmap")
    return figures


def create_cargo_flow_charts(results: Dict[str, Any]) -> Dict[str, str]:
    """Create cargo flow and trade pattern charts."""
    print("Creating cargo flow charts...")

    figures = {}
    flows = results['cargo_flows']

    # 1. Top origin countries - Horizontal bar
    if len(flows['origin_stats_df']) > 0:
        origin_df = flows['origin_stats_df'].head(15).copy()
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=origin_df['Origin_Country'],
            x=origin_df['Clearances'],
            orientation='h',
            marker=dict(color='lightseagreen'),
            hovertemplate='<b>%{y}</b><br>Clearances: %{x:,}<br>Tonnage: %{customdata:,.0f}<extra></extra>',
            customdata=origin_df['Total_Tons'].values
        ))

        fig.update_layout(
            title="Top 15 Origin Countries",
            xaxis_title="Number of Clearances",
            yaxis_title="Country",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )

        figures['origin_countries'] = fig.to_html(include_plotlyjs='cdn', div_id='origin_countries')

    # 2. Top destination countries - Horizontal bar
    if len(flows['dest_stats_df']) > 0:
        dest_df = flows['dest_stats_df'].head(15).copy()
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=dest_df['Destination_Country'],
            x=dest_df['Clearances'],
            orientation='h',
            marker=dict(color='coral'),
            hovertemplate='<b>%{y}</b><br>Clearances: %{x:,}<br>Tonnage: %{customdata:,.0f}<extra></extra>',
            customdata=dest_df['Total_Tons'].values
        ))

        fig.update_layout(
            title="Top 15 Destination Countries",
            xaxis_title="Number of Clearances",
            yaxis_title="Country",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )

        figures['dest_countries'] = fig.to_html(include_plotlyjs='cdn', div_id='dest_countries')

    # 3. Trade lanes - Sankey diagram
    if len(flows['trade_lanes_df']) > 0:
        trade_lanes = flows['trade_lanes_df'].head(30).copy()

        # Create node list
        origins = trade_lanes['Origin'].unique().tolist()
        regions = trade_lanes['Region'].unique().tolist()
        destinations = trade_lanes['Destination'].unique().tolist()

        all_nodes = origins + regions + destinations
        node_dict = {node: idx for idx, node in enumerate(all_nodes)}

        # Create links
        sources = []
        targets = []
        values = []
        colors = []

        for _, row in trade_lanes.iterrows():
            # Origin -> Region
            sources.append(node_dict[row['Origin']])
            targets.append(node_dict[row['Region']])
            values.append(row['Clearances'])
            colors.append('rgba(0,128,128,0.4)')

            # Region -> Destination
            sources.append(node_dict[row['Region']])
            targets.append(node_dict[row['Destination']])
            values.append(row['Clearances'])
            colors.append('rgba(255,127,80,0.4)')

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color="lightblue"
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colors
            )
        )])

        fig.update_layout(
            title="Trade Lanes: Origin → Region → Destination (Top 30)",
            height=700,
            font=dict(size=10)
        )

        figures['trade_sankey'] = fig.to_html(include_plotlyjs='cdn', div_id='trade_sankey')

    print(f"  Created {len(figures)} cargo flow charts")
    return figures


def create_grain_analysis_charts(results: Dict[str, Any]) -> Dict[str, str]:
    """Create grain shipment analysis charts."""
    print("Creating grain analysis charts...")

    figures = {}
    grain = results['grain']

    if grain['grain_clearances'] == 0:
        print("  No grain data to visualize")
        return figures

    # 1. Grain by region - Stacked bar
    if len(grain['grain_by_region_df']) > 0:
        grain_region = grain['grain_by_region_df'].copy()
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=grain_region['Port_Region'],
            y=grain_region['Clearances'],
            name='Clearances',
            marker=dict(color='gold'),
            hovertemplate='<b>%{x}</b><br>Clearances: %{y}<br>Tonnage: %{customdata:,.0f} MT<extra></extra>',
            customdata=grain_region['Tonnage'].values
        ))

        fig.update_layout(
            title="Grain Shipments by Region",
            xaxis_title="Region",
            yaxis_title="Number of Clearances",
            height=500,
            xaxis={'tickangle': -45}
        )

        figures['grain_by_region'] = fig.to_html(include_plotlyjs='cdn', div_id='grain_by_region')

    # 2. Grain destinations - Pie chart
    if len(grain['grain_dest_df']) > 0:
        grain_dest = grain['grain_dest_df'].head(10).copy()
        fig = px.pie(
            grain_dest,
            values='Tonnage',
            names='Destination_Country',
            title="Grain Export Tonnage by Destination (Top 10)",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500)

        figures['grain_dest_pie'] = fig.to_html(include_plotlyjs='cdn', div_id='grain_dest_pie')

    # 3. Grain vessel types
    if len(grain['grain_types_df']) > 0:
        grain_types = grain['grain_types_df'].head(10).copy()
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=grain_types['Ships_Type'],
            y=grain_types['Clearances'],
            marker=dict(color='wheat'),
            hovertemplate='<b>%{x}</b><br>Clearances: %{y}<br>Revenue: $%{customdata:,.0f}<extra></extra>',
            customdata=grain_types['Revenue'].values
        ))

        fig.update_layout(
            title="Grain Shipments by Vessel Type",
            xaxis_title="Vessel Type",
            yaxis_title="Number of Clearances",
            height=500,
            xaxis={'tickangle': -45}
        )

        figures['grain_vessel_types'] = fig.to_html(include_plotlyjs='cdn', div_id='grain_vessel_types')

    print(f"  Created {len(figures)} grain charts")
    return figures


def create_all_visualizations(results: Dict[str, Any]) -> Dict[str, str]:
    """Create all interactive HTML visualizations."""
    print("\n" + "="*60)
    print("Creating Interactive HTML Visualizations")
    print("="*60 + "\n")

    all_figures = {}

    all_figures.update(create_market_overview_charts(results))
    all_figures.update(create_vessel_type_charts(results))
    all_figures.update(create_regional_charts(results))
    all_figures.update(create_vessel_type_region_heatmap(results))
    all_figures.update(create_cargo_flow_charts(results))
    all_figures.update(create_grain_analysis_charts(results))

    print("\n" + "="*60)
    print(f"Visualization Complete - {len(all_figures)} interactive charts created")
    print("="*60 + "\n")

    return all_figures


if __name__ == '__main__':
    print("HTML Visualization module loaded successfully")
    print("Run from main orchestrator to generate charts")
