"""
Rail Analytics Dashboard
Main Streamlit application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import (
    get_connection,
    query,
    get_commodity_flows,
    get_top_od_pairs,
    get_commodity_summary,
    DB_PATH
)
from rcaf_data import get_rcaf_data, get_latest_rcaf, adjust_rate_by_rcaf

# Page config
st.set_page_config(
    page_title="Rail Analytics",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)


def check_database():
    """Check if database exists and has data"""
    if not DB_PATH.exists():
        return False, "Database not initialized"
    try:
        con = get_connection()
        count = con.execute("SELECT COUNT(*) FROM fact_waybill").fetchone()[0]
        con.close()
        return count > 0, f"{count:,} records"
    except Exception as e:
        return False, str(e)


def main():
    # Header
    st.markdown('<p class="main-header">🚂 Rail Analytics Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Commodity Flow Analysis | STB Waybill Data</p>', unsafe_allow_html=True)

    # Check database
    db_ready, db_msg = check_database()

    if not db_ready:
        st.error(f"Database not ready: {db_msg}")
        st.info("Run `python rail_analytics/src/database.py` to initialize the database.")
        st.stop()

    st.success(f"Database connected: {db_msg}")
    st.divider()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Get available commodity groups
        try:
            commodity_options = query("""
                SELECT DISTINCT stcc_2digit, commodity_group
                FROM v_commodity_summary
                WHERE commodity_group IS NOT NULL
                ORDER BY commodity_group
            """)

            selected_commodity = st.selectbox(
                "Commodity Group",
                options=["All"] + commodity_options['commodity_group'].tolist(),
                index=0
            )

            years = query("SELECT DISTINCT year FROM v_commodity_flows ORDER BY year")
            selected_year = st.selectbox(
                "Year",
                options=["All"] + years['year'].tolist(),
                index=0
            )

        except Exception as e:
            st.error(f"Error loading filters: {e}")
            selected_commodity = "All"
            selected_year = "All"

        st.divider()
        st.caption("Data Source: STB Public Use Waybill Sample 2018-2023")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🗺️ Flow Analysis",
        "🏗️ Cement",
        "💰 Cost Index (RCAF)",
        "⚖️ URCS Rate Analysis",
        "📈 Multi-Year Trends",
        "🔍 Data Explorer"
    ])

    # Tab 1: Overview
    with tab1:
        render_overview(selected_commodity, selected_year)

    # Tab 2: Flow Analysis
    with tab2:
        render_flow_analysis(selected_commodity, selected_year)

    # Tab 3: Cement Analysis
    with tab3:
        render_cement_dashboard()

    # Tab 4: RCAF Cost Index
    with tab4:
        render_rcaf_dashboard()

    # Tab 5: URCS Rate Benchmarking
    with tab5:
        render_urcs_dashboard()

    # Tab 6: Multi-Year Trends
    with tab6:
        render_trends(selected_commodity)

    # Tab 7: Data Explorer
    with tab7:
        render_data_explorer()


def render_overview(commodity_filter, year_filter):
    """Render overview dashboard"""
    st.subheader("📊 Overview")

    # Build query filters
    where_clauses = []
    if commodity_filter != "All":
        where_clauses.append(f"commodity_group = '{commodity_filter}'")
    if year_filter != "All":
        where_clauses.append(f"year = {year_filter}")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Key metrics
    try:
        metrics = query(f"""
            SELECT
                SUM(total_carloads) as carloads,
                SUM(total_tons) as tons,
                SUM(total_revenue) as revenue,
                COUNT(DISTINCT origin_bea || '-' || term_bea) as od_pairs,
                AVG(avg_rev_per_car) as avg_rev_car
            FROM v_commodity_flows
            {where_sql}
        """)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Carloads", f"{metrics['carloads'].iloc[0]:,.0f}")
        with col2:
            st.metric("Total Tons", f"{metrics['tons'].iloc[0]:,.0f}")
        with col3:
            st.metric("Total Revenue", f"${metrics['revenue'].iloc[0]:,.0f}")
        with col4:
            st.metric("O-D Pairs", f"{metrics['od_pairs'].iloc[0]:,}")
        with col5:
            st.metric("Avg Rev/Car", f"${metrics['avg_rev_car'].iloc[0]:,.0f}")

    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return

    st.divider()

    # Commodity breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Commodities by Carloads")
        try:
            commodity_data = query(f"""
                SELECT
                    commodity_group,
                    SUM(total_carloads) as carloads,
                    SUM(total_revenue) as revenue
                FROM v_commodity_flows
                {where_sql}
                GROUP BY commodity_group
                ORDER BY carloads DESC
                LIMIT 15
            """)

            fig = px.bar(
                commodity_data,
                x='carloads',
                y='commodity_group',
                orientation='h',
                color='revenue',
                color_continuous_scale='Blues',
                labels={'carloads': 'Carloads', 'commodity_group': 'Commodity', 'revenue': 'Revenue ($)'}
            )
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading commodity chart: {e}")

    with col2:
        st.subheader("Revenue by Region")
        try:
            region_data = query(f"""
                SELECT
                    origin_region as region,
                    SUM(total_revenue) as revenue,
                    SUM(total_carloads) as carloads
                FROM v_commodity_flows
                {where_sql}
                GROUP BY origin_region
                ORDER BY revenue DESC
            """)

            fig = px.pie(
                region_data,
                values='revenue',
                names='region',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading region chart: {e}")


def render_flow_analysis(commodity_filter, year_filter):
    """Render O-D flow analysis"""
    st.subheader("🗺️ Origin-Destination Flow Analysis")

    # Filters for flow analysis
    col1, col2 = st.columns(2)

    with col1:
        top_n = st.slider("Number of O-D pairs to show", 10, 100, 25)

    with col2:
        metric_choice = st.selectbox("Size flows by", ["Carloads", "Tons", "Revenue"])

    metric_col = {
        "Carloads": "total_carloads",
        "Tons": "total_tons",
        "Revenue": "total_revenue"
    }[metric_choice]

    # Get top O-D pairs with coordinates
    try:
        where_clauses = []
        if commodity_filter != "All":
            where_clauses.append(f"commodity_group = '{commodity_filter}'")
        if year_filter != "All":
            where_clauses.append(f"year = {year_filter}")
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        od_data = query(f"""
            SELECT
                cf.origin_bea,
                cf.origin_name,
                o.lat as origin_lat,
                o.lon as origin_lon,
                cf.term_bea,
                cf.dest_name,
                d.lat as dest_lat,
                d.lon as dest_lon,
                cf.commodity_group,
                SUM(cf.total_carloads) as total_carloads,
                SUM(cf.total_tons) as total_tons,
                SUM(cf.total_revenue) as total_revenue
            FROM v_commodity_flows cf
            LEFT JOIN dim_bea o ON cf.origin_bea = o.bea_code
            LEFT JOIN dim_bea d ON cf.term_bea = d.bea_code
            {where_sql}
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
            HAVING o.lat IS NOT NULL AND d.lat IS NOT NULL
            ORDER BY {metric_col} DESC
            LIMIT {top_n}
        """)

        if len(od_data) > 0:
            # Display top pairs table
            st.subheader("Top O-D Pairs")
            display_cols = ['origin_name', 'dest_name', 'commodity_group', 'total_carloads', 'total_tons', 'total_revenue']
            st.dataframe(
                od_data[display_cols].rename(columns={
                    'origin_name': 'Origin',
                    'dest_name': 'Destination',
                    'commodity_group': 'Commodity',
                    'total_carloads': 'Carloads',
                    'total_tons': 'Tons',
                    'total_revenue': 'Revenue ($)'
                }),
                use_container_width=True,
                hide_index=True
            )

            # Flow map using scatter lines
            st.subheader("Flow Map")

            fig = go.Figure()

            # Add lines for each O-D pair
            max_val = od_data[metric_col].max()
            for _, row in od_data.iterrows():
                width = 1 + (row[metric_col] / max_val) * 8

                fig.add_trace(go.Scattergeo(
                    lon=[row['origin_lon'], row['dest_lon']],
                    lat=[row['origin_lat'], row['dest_lat']],
                    mode='lines',
                    line=dict(width=width, color='rgba(30, 58, 95, 0.5)'),
                    hoverinfo='text',
                    text=f"{row['origin_name']} → {row['dest_name']}<br>{row['commodity_group']}<br>Carloads: {row['total_carloads']:,.0f}",
                    showlegend=False
                ))

            # Add origin points
            origins = od_data[['origin_name', 'origin_lat', 'origin_lon']].drop_duplicates()
            fig.add_trace(go.Scattergeo(
                lon=origins['origin_lon'],
                lat=origins['origin_lat'],
                mode='markers',
                marker=dict(size=8, color='green', symbol='circle'),
                name='Origins',
                hoverinfo='text',
                text=origins['origin_name']
            ))

            # Add destination points
            dests = od_data[['dest_name', 'dest_lat', 'dest_lon']].drop_duplicates()
            fig.add_trace(go.Scattergeo(
                lon=dests['dest_lon'],
                lat=dests['dest_lat'],
                mode='markers',
                marker=dict(size=8, color='red', symbol='circle'),
                name='Destinations',
                hoverinfo='text',
                text=dests['dest_name']
            ))

            fig.update_layout(
                geo=dict(
                    scope='usa',
                    projection_type='albers usa',
                    showland=True,
                    landcolor='rgb(243, 243, 243)',
                    countrycolor='rgb(204, 204, 204)',
                    showlakes=True,
                    lakecolor='rgb(255, 255, 255)'
                ),
                height=600,
                margin=dict(l=0, r=0, t=30, b=0)
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No data available for the selected filters")

    except Exception as e:
        st.error(f"Error loading flow data: {e}")


def render_cement_dashboard():
    """Render Cement-specific analysis dashboard"""
    st.subheader("�ite Cement Market Analysis")
    st.markdown("**STCC 32411 - Hydraulic Cement (Portland Cement)**")

    try:
        # Overall cement stats
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
        """)

        if len(metrics) > 0:
            m = metrics.iloc[0]

            # Key metrics row
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.metric("Total Carloads", f"{m['total_carloads']:,}")
            with col2:
                st.metric("Total Tons", f"{m['total_tons']/1e6:.1f}M")
            with col3:
                st.metric("Total Revenue", f"${m['total_revenue']/1e6:.0f}M")
            with col4:
                st.metric("Avg Rev/Car", f"${m['avg_rev_per_car']:,.0f}")
            with col5:
                st.metric("Avg Rev/Ton", f"${m['avg_rev_per_ton']:.2f}")
            with col6:
                st.metric("Avg Distance", f"{m['avg_miles']:.0f} mi")

            st.divider()

            # Two column layout for charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Price Distribution ($/Ton)")

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

                fig = px.bar(
                    price_dist,
                    x='price_range',
                    y='carloads',
                    color='avg_miles',
                    color_continuous_scale='Viridis',
                    labels={'carloads': 'Carloads', 'price_range': 'Price per Ton', 'avg_miles': 'Avg Miles'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Seasonality (by Quarter)")

                seasonality = query("""
                    SELECT
                        EXTRACT(QUARTER FROM waybill_date) as quarter,
                        CAST(SUM(exp_carloads) AS BIGINT) as carloads,
                        ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as avg_rev_ton
                    FROM fact_waybill
                    WHERE stcc = '32411'
                    GROUP BY 1
                    ORDER BY 1
                """)
                seasonality['quarter'] = seasonality['quarter'].apply(lambda x: f'Q{int(x)}')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=seasonality['quarter'],
                    y=seasonality['carloads'],
                    name='Carloads',
                    marker_color='#1E3A5F'
                ))
                fig.add_trace(go.Scatter(
                    x=seasonality['quarter'],
                    y=seasonality['avg_rev_ton'],
                    name='$/Ton',
                    yaxis='y2',
                    line=dict(color='#E74C3C', width=3),
                    mode='lines+markers'
                ))
                fig.update_layout(
                    height=350,
                    yaxis=dict(title='Carloads'),
                    yaxis2=dict(title='$/Ton', overlaying='y', side='right'),
                    legend=dict(orientation='h', y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Distance-based pricing
            st.subheader("Distance-Based Pricing Analysis")

            distance_pricing = query("""
                SELECT
                    CASE
                        WHEN short_line_miles < 200 THEN '1. < 200 mi'
                        WHEN short_line_miles < 400 THEN '2. 200-400 mi'
                        WHEN short_line_miles < 600 THEN '3. 400-600 mi'
                        WHEN short_line_miles < 800 THEN '4. 600-800 mi'
                        ELSE '5. > 800 mi'
                    END as distance_band,
                    CAST(SUM(exp_carloads) AS BIGINT) as carloads,
                    ROUND(SUM(exp_freight_rev) / SUM(exp_carloads), 0) as rev_per_car,
                    ROUND(SUM(exp_freight_rev) / SUM(exp_tons), 2) as rev_per_ton,
                    ROUND(SUM(exp_freight_rev) / SUM(exp_carloads) / AVG(short_line_miles), 2) as rev_per_car_mile
                FROM fact_waybill
                WHERE stcc = '32411' AND short_line_miles > 0
                GROUP BY 1
                ORDER BY 1
            """)

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    distance_pricing,
                    x='distance_band',
                    y='rev_per_ton',
                    color='carloads',
                    color_continuous_scale='Blues',
                    labels={'rev_per_ton': '$/Ton', 'distance_band': 'Distance Band', 'carloads': 'Carloads'}
                )
                fig.update_layout(height=300, title='Revenue per Ton by Distance')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    distance_pricing,
                    x='distance_band',
                    y='rev_per_car_mile',
                    color='carloads',
                    color_continuous_scale='Greens',
                    labels={'rev_per_car_mile': '$/Car-Mile', 'distance_band': 'Distance Band'}
                )
                fig.update_layout(height=300, title='Revenue per Car-Mile by Distance')
                st.plotly_chart(fig, use_container_width=True)

            # Pricing table
            st.dataframe(
                distance_pricing.rename(columns={
                    'distance_band': 'Distance',
                    'carloads': 'Carloads',
                    'rev_per_car': '$/Car',
                    'rev_per_ton': '$/Ton',
                    'rev_per_car_mile': '$/Car-Mile'
                }),
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # Top Routes
            st.subheader("Top Cement Routes")

            top_routes = query("""
                SELECT
                    COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
                    COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
                    o.lat as origin_lat,
                    o.lon as origin_lon,
                    d.lat as dest_lat,
                    d.lon as dest_lon,
                    CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
                    CAST(SUM(w.exp_tons) AS BIGINT) as tons,
                    ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as rev_per_car,
                    ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_tons), 2) as rev_per_ton,
                    ROUND(AVG(w.short_line_miles), 0) as avg_miles
                FROM fact_waybill w
                LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
                LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
                WHERE w.stcc = '32411'
                  AND w.origin_bea != '000' AND w.term_bea != '000'
                GROUP BY 1, 2, 3, 4, 5, 6
                ORDER BY carloads DESC
                LIMIT 15
            """)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.dataframe(
                    top_routes[['origin', 'destination', 'carloads', 'tons', 'rev_per_car', 'rev_per_ton', 'avg_miles']].rename(columns={
                        'origin': 'Origin',
                        'destination': 'Destination',
                        'carloads': 'Carloads',
                        'tons': 'Tons',
                        'rev_per_car': '$/Car',
                        'rev_per_ton': '$/Ton',
                        'avg_miles': 'Miles'
                    }),
                    use_container_width=True,
                    hide_index=True
                )

            with col2:
                # Flow map for cement
                map_data = top_routes[top_routes['origin_lat'].notna() & top_routes['dest_lat'].notna()]

                if len(map_data) > 0:
                    fig = go.Figure()

                    max_carloads = map_data['carloads'].max()
                    for _, row in map_data.iterrows():
                        width = 1 + (row['carloads'] / max_carloads) * 6

                        fig.add_trace(go.Scattergeo(
                            lon=[row['origin_lon'], row['dest_lon']],
                            lat=[row['origin_lat'], row['dest_lat']],
                            mode='lines',
                            line=dict(width=width, color='rgba(139, 69, 19, 0.6)'),
                            hoverinfo='text',
                            text=f"{row['origin']} → {row['destination']}<br>Carloads: {row['carloads']:,}<br>${row['rev_per_ton']}/ton",
                            showlegend=False
                        ))

                    fig.update_layout(
                        geo=dict(
                            scope='usa',
                            projection_type='albers usa',
                            showland=True,
                            landcolor='rgb(243, 243, 243)',
                        ),
                        height=400,
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Origin and Destination Analysis
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Top Origin Regions")
                origins = query("""
                    SELECT
                        COALESCE(o.bea_name, 'BEA ' || w.origin_bea) as origin,
                        COALESCE(o.region, 'Unknown') as region,
                        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
                        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
                    FROM fact_waybill w
                    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
                    WHERE w.stcc = '32411' AND w.origin_bea != '000'
                    GROUP BY 1, 2
                    ORDER BY carloads DESC
                    LIMIT 10
                """)

                fig = px.bar(
                    origins,
                    y='origin',
                    x='carloads',
                    orientation='h',
                    color='avg_rev_car',
                    color_continuous_scale='Oranges',
                    labels={'carloads': 'Carloads', 'origin': 'Origin', 'avg_rev_car': '$/Car'}
                )
                fig.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Top Destination Markets")
                destinations = query("""
                    SELECT
                        COALESCE(d.bea_name, 'BEA ' || w.term_bea) as destination,
                        COALESCE(d.region, 'Unknown') as region,
                        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
                        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_carloads), 0) as avg_rev_car
                    FROM fact_waybill w
                    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
                    WHERE w.stcc = '32411' AND w.term_bea != '000'
                    GROUP BY 1, 2
                    ORDER BY carloads DESC
                    LIMIT 10
                """)

                fig = px.bar(
                    destinations,
                    y='destination',
                    x='carloads',
                    orientation='h',
                    color='avg_rev_car',
                    color_continuous_scale='Blues',
                    labels={'carloads': 'Carloads', 'destination': 'Destination', 'avg_rev_car': '$/Car'}
                )
                fig.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Rate Benchmarking Tool
            st.subheader("🔧 Cement Rate Estimator")
            st.markdown("Estimate cement freight rates based on distance.")

            col1, col2, col3 = st.columns(3)

            with col1:
                est_miles = st.number_input("Estimated Distance (miles)", min_value=50, max_value=2000, value=400, step=50)

            with col2:
                # Get rate estimates based on distance
                if est_miles < 200:
                    est_rev_ton = 26
                    est_rev_car = 2700
                elif est_miles < 400:
                    est_rev_ton = 38
                    est_rev_car = 4060
                elif est_miles < 600:
                    est_rev_ton = 44
                    est_rev_car = 4640
                elif est_miles < 800:
                    est_rev_ton = 45
                    est_rev_car = 4825
                else:
                    est_rev_ton = 62
                    est_rev_car = 6200

                st.metric("Est. Revenue/Ton", f"${est_rev_ton:.2f}")
                st.metric("Est. Revenue/Car", f"${est_rev_car:,}")

            with col3:
                tons_per_car = 105  # typical cement hopper car
                st.metric("Typical Tons/Car", f"{tons_per_car}")
                st.metric("Est. Total (per car)", f"${est_rev_ton * tons_per_car:,.0f}")

            st.caption("*Estimates based on 2023 STB Waybill Sample averages. Actual rates vary by contract, carrier, and market conditions.*")

        else:
            st.warning("No cement data found in the waybill sample.")

    except Exception as e:
        st.error(f"Error loading cement data: {e}")


def render_rcaf_dashboard():
    """Render RCAF Cost Index dashboard"""
    st.subheader("💰 Rail Cost Adjustment Factor (RCAF)")

    st.markdown("""
    The RCAF is an index that tracks changes in railroad costs over time. The STB publishes three versions:
    - **RCAF-U (Unadjusted)**: Raw cost changes
    - **RCAF-A (Adjusted)**: Includes productivity adjustment (5-year moving average)
    - **RCAF-5**: Alternative productivity adjustment methodology
    """)

    try:
        # Get latest RCAF values
        latest = get_latest_rcaf()
        rcaf_data = get_rcaf_data()

        if len(latest) > 0:
            st.subheader("Current RCAF Values")
            current = latest.iloc[0]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    f"RCAF-U ({current['period']})",
                    f"{current['rcaf_u']:.3f}",
                    f"{current['yoy_change_u']:.1f}% YoY" if pd.notna(current['yoy_change_u']) else None
                )
            with col2:
                st.metric(
                    f"RCAF-A ({current['period']})",
                    f"{current['rcaf_a']:.3f}",
                    f"{current['yoy_change_a']:.1f}% YoY" if pd.notna(current['yoy_change_a']) else None
                )
            with col3:
                st.metric(
                    f"RCAF-5 ({current['period']})",
                    f"{current['rcaf_5']:.3f}" if pd.notna(current['rcaf_5']) else "N/A"
                )
            with col4:
                # Calculate cumulative change from base
                base_rcaf = rcaf_data[rcaf_data['year'] == 2000].iloc[0]['rcaf_u']
                cum_change = ((current['rcaf_u'] / base_rcaf) - 1) * 100
                st.metric("Cumulative Change (since 2000)", f"{cum_change:.1f}%")

            st.divider()

            # Historical chart
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("RCAF Historical Trend")

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=rcaf_data['period'],
                    y=rcaf_data['rcaf_u'],
                    name='RCAF-U (Unadjusted)',
                    line=dict(color='#1E3A5F', width=2)
                ))

                fig.add_trace(go.Scatter(
                    x=rcaf_data['period'],
                    y=rcaf_data['rcaf_a'],
                    name='RCAF-A (Adjusted)',
                    line=dict(color='#E74C3C', width=2)
                ))

                if rcaf_data['rcaf_5'].notna().any():
                    fig.add_trace(go.Scatter(
                        x=rcaf_data['period'],
                        y=rcaf_data['rcaf_5'],
                        name='RCAF-5',
                        line=dict(color='#27AE60', width=2, dash='dash')
                    ))

                fig.update_layout(
                    height=400,
                    xaxis_title="Quarter",
                    yaxis_title="Index Value",
                    legend=dict(orientation='h', y=-0.2),
                    hovermode='x unified'
                )

                # Add annotation for base year changes
                fig.add_annotation(
                    x='2024Q4',
                    y=0.961,
                    text="Base Year Reset",
                    showarrow=True,
                    arrowhead=2
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Year-over-Year Change")

                yoy_data = rcaf_data[rcaf_data['yoy_change_u'].notna()].copy()

                fig = px.bar(
                    yoy_data,
                    x='period',
                    y='yoy_change_u',
                    color='yoy_change_u',
                    color_continuous_scale='RdYlGn_r',
                    labels={'yoy_change_u': 'YoY Change (%)', 'period': 'Quarter'}
                )

                fig.update_layout(
                    height=400,
                    showlegend=False,
                    coloraxis_showscale=False
                )

                fig.add_hline(y=0, line_dash="dash", line_color="gray")

                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Rate Adjustment Calculator
            st.subheader("📊 Rate Adjustment Calculator")
            st.markdown("Adjust historical rail rates to current dollars using RCAF indices.")

            col1, col2, col3 = st.columns(3)

            with col1:
                base_rate = st.number_input("Original Rate ($)", min_value=0.0, value=5000.0, step=100.0)

                years = sorted(rcaf_data['year'].unique())
                base_year = st.selectbox("Original Year", years, index=len(years) - 5)
                base_qtr = st.selectbox("Original Quarter", [1, 2, 3, 4], index=0)

            with col2:
                target_year = st.selectbox("Target Year", years, index=len(years) - 1)
                target_qtr = st.selectbox("Target Quarter", [1, 2, 3, 4], index=2, key="target_qtr")

                use_adjusted = st.checkbox("Use RCAF-A (productivity adjusted)", value=True)

            with col3:
                if st.button("Calculate Adjustment", type="primary"):
                    try:
                        adjusted_rate = adjust_rate_by_rcaf(
                            base_rate, base_year, base_qtr,
                            target_year, target_qtr, use_adjusted
                        )

                        pct_change = ((adjusted_rate / base_rate) - 1) * 100

                        st.success("**Adjusted Rate**")
                        st.metric(
                            f"Rate in {target_year}Q{target_qtr}",
                            f"${adjusted_rate:,.2f}",
                            f"{pct_change:+.1f}%"
                        )

                        # Show calculation details
                        rcaf_type = "RCAF-A" if use_adjusted else "RCAF-U"
                        st.caption(f"Adjustment using {rcaf_type}")

                    except Exception as e:
                        st.error(f"Error: {e}")

            st.divider()

            # RCAF Data Table
            with st.expander("📋 View All RCAF Data"):
                st.dataframe(
                    rcaf_data[['period', 'rcaf_u', 'rcaf_a', 'rcaf_5', 'yoy_change_u']].rename(columns={
                        'period': 'Period',
                        'rcaf_u': 'RCAF-U',
                        'rcaf_a': 'RCAF-A',
                        'rcaf_5': 'RCAF-5',
                        'yoy_change_u': 'YoY Change (%)'
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                csv = rcaf_data.to_csv(index=False)
                st.download_button("Download RCAF Data (CSV)", csv, "rcaf_historical.csv", "text/csv")

        else:
            st.warning("No RCAF data available. Run `python rail_analytics/src/rcaf_data.py` to load data.")

    except Exception as e:
        st.error(f"Error loading RCAF data: {e}")
        st.info("Run `python rail_analytics/src/rcaf_data.py` to initialize RCAF data.")


def render_urcs_dashboard():
    """Render URCS Rate Benchmarking dashboard"""
    st.subheader("⚖️ URCS Rate Benchmarking")

    st.markdown("""
    The **Uniform Rail Costing System (URCS)** is the STB's methodology for calculating rail variable costs.
    The **R/VC Ratio** (Revenue-to-Variable-Cost) is a key regulatory metric - shipments above 180% R/VC
    may be subject to STB rate jurisdiction.
    """)

    try:
        # Check if URCS view exists
        try:
            test = query("SELECT COUNT(*) as cnt FROM v_waybill_with_distance LIMIT 1")
        except:
            st.warning("URCS views not initialized. Run `python rail_analytics/src/urcs_model.py` to create them.")
            return

        # Overall R/VC metrics
        metrics = query("""
            SELECT
                COUNT(*) as shipments,
                ROUND(AVG(exp_freight_rev / NULLIF(
                    GREATEST(50, est_miles) * 0.05 * exp_tons +
                    GREATEST(50, est_miles) * 0.15 * exp_carloads +
                    exp_carloads * 8.50
                , 0)) * 100, 1) as avg_rvc,
                ROUND(SUM(CASE WHEN (exp_freight_rev / NULLIF(
                    GREATEST(50, est_miles) * 0.05 * exp_tons +
                    GREATEST(50, est_miles) * 0.15 * exp_carloads +
                    exp_carloads * 8.50
                , 0)) > 1.8 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above_180
            FROM v_waybill_with_distance
            WHERE waybill_date IS NOT NULL
              AND exp_tons > 0 AND exp_freight_rev > 0
              AND est_miles > 0
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Shipments Analyzed", f"{metrics['shipments'].iloc[0]:,}")
        with col2:
            st.metric("Average R/VC Ratio", f"{metrics['avg_rvc'].iloc[0]:.1f}%")
        with col3:
            st.metric("Above 180% Threshold", f"{metrics['pct_above_180'].iloc[0]:.1f}%")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("R/VC Ratio by Year")
            rvc_by_year = query("""
                SELECT
                    CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                    ROUND(AVG(exp_freight_rev / NULLIF(
                        GREATEST(50, est_miles) * 0.05 * exp_tons +
                        GREATEST(50, est_miles) * 0.15 * exp_carloads +
                        exp_carloads * 8.50
                    , 0)) * 100, 1) as avg_rvc,
                    ROUND(SUM(CASE WHEN (exp_freight_rev / NULLIF(
                        GREATEST(50, est_miles) * 0.05 * exp_tons +
                        GREATEST(50, est_miles) * 0.15 * exp_carloads +
                        exp_carloads * 8.50
                    , 0)) > 1.8 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above_180
                FROM v_waybill_with_distance
                WHERE waybill_date IS NOT NULL
                  AND EXTRACT(YEAR FROM waybill_date) >= 2018
                  AND exp_tons > 0 AND exp_freight_rev > 0
                  AND est_miles > 0
                GROUP BY 1
                ORDER BY 1
            """)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=rvc_by_year['year'],
                y=rvc_by_year['avg_rvc'],
                name='Avg R/VC %',
                marker_color='#1E3A5F'
            ))
            fig.add_hline(y=180, line_dash="dash", line_color="red",
                         annotation_text="180% STB Threshold")
            fig.update_layout(height=350, yaxis_title='R/VC Ratio (%)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("R/VC by Distance Band")
            rvc_by_distance = query("""
                SELECT
                    CASE
                        WHEN est_miles < 300 THEN '1. Short (<300 mi)'
                        WHEN est_miles < 700 THEN '2. Medium (300-700 mi)'
                        WHEN est_miles < 1200 THEN '3. Long (700-1200 mi)'
                        ELSE '4. Very Long (>1200 mi)'
                    END as distance_band,
                    COUNT(*) as shipments,
                    ROUND(AVG(exp_freight_rev / NULLIF(
                        GREATEST(50, est_miles) * 0.05 * exp_tons +
                        GREATEST(50, est_miles) * 0.15 * exp_carloads +
                        exp_carloads * 8.50
                    , 0)) * 100, 1) as avg_rvc
                FROM v_waybill_with_distance
                WHERE waybill_date IS NOT NULL
                  AND exp_tons > 0 AND exp_freight_rev > 0
                  AND est_miles > 0
                GROUP BY 1
                ORDER BY 1
            """)

            fig = px.bar(
                rvc_by_distance,
                x='distance_band',
                y='avg_rvc',
                color='shipments',
                color_continuous_scale='Blues',
                labels={'avg_rvc': 'Avg R/VC (%)', 'distance_band': 'Distance Band'}
            )
            fig.add_hline(y=180, line_dash="dash", line_color="red")
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Top commodities by R/VC
        st.subheader("R/VC Ratio by Commodity")
        rvc_by_commodity = query("""
            SELECT
                w.stcc_2digit,
                COALESCE(s.stcc_group, 'Unknown') as commodity,
                COUNT(*) as shipments,
                ROUND(AVG(w.exp_freight_rev / NULLIF(
                    GREATEST(50, est_miles) * 0.05 * w.exp_tons +
                    GREATEST(50, est_miles) * 0.15 * w.exp_carloads +
                    w.exp_carloads * 8.50
                , 0)) * 100, 1) as avg_rvc,
                ROUND(SUM(CASE WHEN (w.exp_freight_rev / NULLIF(
                    GREATEST(50, est_miles) * 0.05 * w.exp_tons +
                    GREATEST(50, est_miles) * 0.15 * w.exp_carloads +
                    w.exp_carloads * 8.50
                , 0)) > 1.8 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_above_180
            FROM v_waybill_with_distance w
            LEFT JOIN dim_stcc s ON w.stcc = s.stcc_code
            WHERE w.waybill_date IS NOT NULL
              AND w.exp_tons > 0 AND w.exp_freight_rev > 0
              AND est_miles > 0
            GROUP BY 1, 2
            HAVING COUNT(*) > 1000
            ORDER BY avg_rvc DESC
            LIMIT 15
        """)

        fig = px.bar(
            rvc_by_commodity,
            x='avg_rvc',
            y='commodity',
            orientation='h',
            color='pct_above_180',
            color_continuous_scale='RdYlGn_r',
            labels={'avg_rvc': 'Avg R/VC (%)', 'commodity': 'Commodity', 'pct_above_180': '% Above 180%'}
        )
        fig.add_vline(x=180, line_dash="dash", line_color="red")
        fig.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

        st.caption("R/VC > 180% indicates potential STB rate jurisdiction. Short-haul shipments typically have higher R/VC due to terminal costs.")

    except Exception as e:
        st.error(f"Error loading URCS data: {e}")


def render_trends(commodity_filter):
    """Render multi-year trend analysis"""
    st.subheader("📈 Multi-Year Trend Analysis (2018-2023)")

    try:
        # Year range info
        year_info = query("""
            SELECT
                MIN(EXTRACT(YEAR FROM waybill_date)) as min_year,
                MAX(EXTRACT(YEAR FROM waybill_date)) as max_year,
                COUNT(DISTINCT EXTRACT(YEAR FROM waybill_date)) as num_years
            FROM fact_waybill
            WHERE waybill_date IS NOT NULL
              AND EXTRACT(YEAR FROM waybill_date) >= 2017
        """)

        if len(year_info) > 0:
            st.success(f"Data available: {int(year_info['min_year'].iloc[0])}-{int(year_info['max_year'].iloc[0])} ({int(year_info['num_years'].iloc[0])} years)")

        # Overall volume trends
        st.subheader("Volume & Revenue Trends")

        annual_trends = query("""
            SELECT
                CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                CAST(SUM(exp_carloads) AS BIGINT) as carloads,
                ROUND(SUM(exp_tons) / 1e9, 2) as tons_billions,
                ROUND(SUM(exp_freight_rev) / 1e9, 1) as revenue_billions,
                ROUND(SUM(exp_freight_rev) / NULLIF(SUM(exp_tons), 0), 2) as rev_per_ton
            FROM fact_waybill
            WHERE waybill_date IS NOT NULL
              AND EXTRACT(YEAR FROM waybill_date) >= 2018
            GROUP BY 1
            ORDER BY 1
        """)

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=annual_trends['year'],
                y=annual_trends['carloads'] / 1e6,
                name='Carloads (M)',
                marker_color='#1E3A5F'
            ))
            fig.add_trace(go.Scatter(
                x=annual_trends['year'],
                y=annual_trends['revenue_billions'],
                name='Revenue ($B)',
                yaxis='y2',
                line=dict(color='#E74C3C', width=3),
                mode='lines+markers'
            ))
            fig.update_layout(
                height=350,
                title='Annual Carloads & Revenue',
                yaxis=dict(title='Carloads (Millions)'),
                yaxis2=dict(title='Revenue ($Billions)', overlaying='y', side='right'),
                legend=dict(orientation='h', y=-0.2)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                annual_trends,
                x='year',
                y='rev_per_ton',
                markers=True,
                title='Revenue per Ton Trend'
            )
            fig.update_layout(height=350, yaxis_title='$/Ton')
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Commodity-specific trends
        st.subheader("Commodity Volume Trends")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Coal (STCC 11) - Declining Industry**")
            coal_trends = query("""
                SELECT
                    CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                    ROUND(SUM(exp_tons) / 1e6, 1) as tons_millions,
                    ROUND(SUM(exp_freight_rev) / 1e9, 2) as revenue_billions
                FROM fact_waybill
                WHERE stcc_2digit = '11'
                  AND waybill_date IS NOT NULL
                  AND EXTRACT(YEAR FROM waybill_date) >= 2018
                GROUP BY 1
                ORDER BY 1
            """)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=coal_trends['year'],
                y=coal_trends['tons_millions'],
                name='Tons (M)',
                marker_color='#2C3E50'
            ))
            fig.add_trace(go.Scatter(
                x=coal_trends['year'],
                y=coal_trends['revenue_billions'],
                name='Revenue ($B)',
                yaxis='y2',
                line=dict(color='orange', width=2),
                mode='lines+markers'
            ))
            fig.update_layout(
                height=300,
                yaxis=dict(title='Tons (Millions)'),
                yaxis2=dict(title='Revenue ($B)', overlaying='y', side='right'),
                legend=dict(orientation='h', y=-0.25)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Calculate CAGR
            if len(coal_trends) > 1:
                start_tons = coal_trends['tons_millions'].iloc[0]
                end_tons = coal_trends['tons_millions'].iloc[-1]
                years = len(coal_trends) - 1
                cagr = ((end_tons / start_tons) ** (1/years) - 1) * 100
                st.metric("Coal Volume CAGR", f"{cagr:.1f}%", delta=f"{end_tons - start_tons:.1f}M tons")

        with col2:
            st.markdown("**Cement (STCC 32) - Construction Materials**")
            cement_trends = query("""
                SELECT
                    CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                    ROUND(SUM(exp_tons) / 1e6, 1) as tons_millions,
                    ROUND(SUM(exp_freight_rev) / 1e9, 2) as revenue_billions
                FROM fact_waybill
                WHERE stcc_2digit = '32'
                  AND waybill_date IS NOT NULL
                  AND EXTRACT(YEAR FROM waybill_date) >= 2018
                GROUP BY 1
                ORDER BY 1
            """)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=cement_trends['year'],
                y=cement_trends['tons_millions'],
                name='Tons (M)',
                marker_color='#8B4513'
            ))
            fig.add_trace(go.Scatter(
                x=cement_trends['year'],
                y=cement_trends['revenue_billions'],
                name='Revenue ($B)',
                yaxis='y2',
                line=dict(color='green', width=2),
                mode='lines+markers'
            ))
            fig.update_layout(
                height=300,
                yaxis=dict(title='Tons (Millions)'),
                yaxis2=dict(title='Revenue ($B)', overlaying='y', side='right'),
                legend=dict(orientation='h', y=-0.25)
            )
            st.plotly_chart(fig, use_container_width=True)

            if len(cement_trends) > 1:
                start_rev = cement_trends['revenue_billions'].iloc[0]
                end_rev = cement_trends['revenue_billions'].iloc[-1]
                years = len(cement_trends) - 1
                cagr = ((end_rev / start_rev) ** (1/years) - 1) * 100
                st.metric("Cement Revenue CAGR", f"{cagr:.1f}%", delta=f"${end_rev - start_rev:.2f}B")

        st.divider()

        # Year-over-year comparison
        st.subheader("Year-over-Year Comparison")

        yoy_data = query("""
            WITH annual AS (
                SELECT
                    CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                    stcc_2digit,
                    SUM(exp_carloads) as carloads,
                    SUM(exp_tons) as tons,
                    SUM(exp_freight_rev) as revenue
                FROM fact_waybill
                WHERE waybill_date IS NOT NULL
                  AND EXTRACT(YEAR FROM waybill_date) >= 2018
                GROUP BY 1, 2
            )
            SELECT
                a.year,
                a.stcc_2digit,
                COALESCE(s.stcc_group, 'Unknown') as commodity,
                a.carloads,
                a.tons,
                a.revenue,
                ROUND((a.carloads - LAG(a.carloads) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year))
                    / NULLIF(LAG(a.carloads) OVER (PARTITION BY a.stcc_2digit ORDER BY a.year), 0) * 100, 1) as yoy_pct
            FROM annual a
            LEFT JOIN dim_stcc s ON a.stcc_2digit = LEFT(s.stcc_code, 2)
            WHERE a.year = (SELECT MAX(EXTRACT(YEAR FROM waybill_date)) FROM fact_waybill)
            ORDER BY a.carloads DESC
            LIMIT 12
        """)

        if len(yoy_data) > 0:
            fig = px.bar(
                yoy_data,
                x='commodity',
                y='yoy_pct',
                color='yoy_pct',
                color_continuous_scale='RdYlGn',
                range_color=[-30, 30],
                title=f'YoY Carload Change ({int(yoy_data["year"].iloc[0])} vs Prior Year)'
            )
            fig.add_hline(y=0, line_dash="solid", line_color="black")
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Summary table
        st.subheader("Annual Summary Table")
        summary = query("""
            SELECT
                CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as Year,
                COUNT(*) as Records,
                CAST(SUM(exp_carloads) AS BIGINT) as Carloads,
                ROUND(SUM(exp_tons) / 1e6, 1) as "Tons (M)",
                ROUND(SUM(exp_freight_rev) / 1e9, 1) as "Revenue ($B)",
                ROUND(SUM(exp_freight_rev) / NULLIF(SUM(exp_tons), 0), 2) as "$/Ton"
            FROM fact_waybill
            WHERE waybill_date IS NOT NULL
              AND EXTRACT(YEAR FROM waybill_date) >= 2018
            GROUP BY 1
            ORDER BY 1
        """)
        st.dataframe(summary, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading trends: {e}")


def render_data_explorer():
    """Render data exploration interface"""
    st.subheader("🔍 Data Explorer")

    st.write("Run custom SQL queries against the waybill database.")

    # Predefined queries
    sample_queries = {
        "Annual volume by year (2018-2023)": """
            SELECT
                CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                COUNT(*) as records,
                CAST(SUM(exp_carloads) AS BIGINT) as carloads,
                ROUND(SUM(exp_tons) / 1e6, 1) as tons_millions,
                ROUND(SUM(exp_freight_rev) / 1e9, 1) as revenue_billions
            FROM fact_waybill
            WHERE waybill_date IS NOT NULL AND EXTRACT(YEAR FROM waybill_date) >= 2018
            GROUP BY 1
            ORDER BY 1
        """,
        "Top 20 commodities by carloads": """
            SELECT stcc_2digit, commodity_group, SUM(total_carloads) as carloads
            FROM v_commodity_flows
            GROUP BY 1, 2
            ORDER BY carloads DESC
            LIMIT 20
        """,
        "Coal volume decline (2018-2023)": """
            SELECT
                CAST(EXTRACT(YEAR FROM waybill_date) AS INTEGER) as year,
                CAST(SUM(exp_carloads) AS BIGINT) as carloads,
                ROUND(SUM(exp_tons) / 1e6, 1) as tons_millions,
                ROUND(SUM(exp_freight_rev) / 1e9, 2) as revenue_billions
            FROM fact_waybill
            WHERE stcc_2digit = '11' AND waybill_date IS NOT NULL
              AND EXTRACT(YEAR FROM waybill_date) >= 2018
            GROUP BY 1
            ORDER BY 1
        """,
        "R/VC Ratio by commodity": """
            SELECT
                stcc_2digit,
                COUNT(*) as shipments,
                ROUND(AVG(exp_freight_rev / NULLIF(
                    GREATEST(50, est_miles) * 0.05 * exp_tons +
                    GREATEST(50, est_miles) * 0.15 * exp_carloads +
                    exp_carloads * 8.50
                , 0)) * 100, 1) as avg_rvc_ratio
            FROM v_waybill_with_distance
            WHERE waybill_date IS NOT NULL AND exp_tons > 0 AND est_miles > 0
            GROUP BY 1
            HAVING COUNT(*) > 1000
            ORDER BY avg_rvc_ratio DESC
        """,
        "Top O-D pairs for Cement (32)": """
            SELECT
                COALESCE(o.bea_name, 'Unknown') as origin,
                COALESCE(d.bea_name, 'Unknown') as destination,
                CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
                ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_tons), 2) as rev_per_ton
            FROM fact_waybill w
            LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
            LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
            WHERE w.stcc_2digit = '32' AND w.origin_bea != '000'
            GROUP BY 1, 2
            ORDER BY carloads DESC
            LIMIT 20
        """,
        "RCAF cost index history": """
            SELECT year, quarter, period, rcaf_u, rcaf_a,
                   ROUND(yoy_change_u, 2) as yoy_pct
            FROM fact_rcaf
            WHERE year >= 2020
            ORDER BY year DESC, quarter DESC
        """,
        "Show available tables and views": """
            SELECT table_name, table_type FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_type, table_name
        """
    }

    selected_query = st.selectbox("Sample Queries", list(sample_queries.keys()))

    sql = st.text_area(
        "SQL Query",
        value=sample_queries[selected_query],
        height=150
    )

    if st.button("Run Query", type="primary"):
        try:
            result = query(sql)
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.caption(f"{len(result)} rows returned")

            # Download button
            csv = result.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "query_results.csv",
                "text/csv"
            )
        except Exception as e:
            st.error(f"Query error: {e}")

    # Schema reference
    with st.expander("📚 Schema Reference"):
        st.markdown("""
        **Fact Table: fact_waybill** (2018-2023 data)
        - waybill_id, waybill_date, accounting_period
        - num_carloads, car_ownership, car_type, stb_car_type
        - stcc, stcc_2digit (commodity codes)
        - billed_weight, actual_weight
        - freight_revenue, transit_charges, misc_charges
        - origin_bea, term_bea (BEA economic areas)
        - short_line_miles, num_interchanges
        - exp_carloads, exp_tons, exp_freight_rev (expanded estimates)

        **Fact Table: fact_rcaf**
        - year, quarter, period, period_date
        - rcaf_u (unadjusted), rcaf_a (adjusted), rcaf_5
        - yoy_change_u, yoy_change_a (year-over-year changes)

        **Dimension Tables:**
        - dim_stcc: STCC commodity codes with descriptions
        - dim_bea: BEA economic areas with lat/lon coordinates
        - dim_car_type: Rail car types
        - dim_time: Date dimension

        **Views - Commodity Flows:**
        - v_commodity_flows: Aggregated flows by commodity, O-D, time
        - v_commodity_summary: Summary by commodity group
        - v_top_od_pairs: Top O-D pairs by volume

        **Views - URCS Rate Benchmarking:**
        - v_waybill_with_distance: Waybills with estimated distance (Haversine)
        - v_urcs_analysis: R/VC ratio analysis by shipment

        **Views - Trend Analysis:**
        - v_annual_commodity_trends: Year-over-year commodity volumes
        - v_quarterly_trends: Quarterly volume and revenue
        - v_yoy_commodity_growth: YoY growth rates by commodity
        - v_pricing_trends: Revenue per ton/car trends
        - v_coal_trends: Coal-specific trend analysis
        - v_cement_trends: Cement-specific trend analysis

        **Views - Cost Index:**
        - v_rcaf_summary: Annual RCAF averages
        - v_rcaf_latest: Most recent RCAF values
        """)


if __name__ == "__main__":
    main()
