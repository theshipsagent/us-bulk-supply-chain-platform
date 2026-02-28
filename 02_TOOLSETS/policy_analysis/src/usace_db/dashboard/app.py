"""
USACE Vessel Characteristics Dashboard
Streamlit application for interactive vessel analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from usace_db.database.connection import DatabaseConnection
from usace_db.dashboard import queries
from usace_db.dashboard import historical_queries

# Page configuration
st.set_page_config(
    page_title="USACE Vessel Analytics",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database connection
@st.cache_resource
def get_database():
    """Get cached database connection."""
    db = DatabaseConnection()
    db.connect()
    return db

# Title
st.title("🚢 USACE Vessel Characteristics Dashboard")

# Sidebar filters
st.sidebar.header("Filters")

# Get filter options
db = get_database()

# Operator filter
operators_list = queries.get_operator_list(db)
selected_operators = st.sidebar.multiselect(
    "Operators",
    options=[op[0] for op in operators_list],
    default=[]
)

# Vessel type filter
vessel_types = queries.get_vessel_types(db)
selected_types = st.sidebar.multiselect(
    "Vessel Types",
    options=[vt[0] for vt in vessel_types if vt[0]],
    default=[]
)

# District filter
districts = queries.get_districts(db)
selected_districts = st.sidebar.multiselect(
    "Districts",
    options=[d[0] for d in districts if d[0]],
    default=[]
)

# Series/Region filter
series_list = queries.get_series(db)
selected_series = st.sidebar.multiselect(
    "Region/Series",
    options=[s[0] for s in series_list if s[0]],
    default=[]
)

# Fleet Year filter (NEW - defaults to 2023)
st.sidebar.markdown("---")
st.sidebar.subheader("Data Year Filter")
available_years_query = db.conn.execute("""
    SELECT DISTINCT fleet_year
    FROM vessels
    WHERE fleet_year IS NOT NULL
    ORDER BY fleet_year DESC
""").fetchall()
available_years_list = [y[0] for y in available_years_query]

fleet_year = st.sidebar.selectbox(
    "Fleet Year",
    options=available_years_list,
    index=0,  # Default to most recent year (2023)
    help="Select which year's fleet data to analyze"
)

st.sidebar.markdown("---")

# Year range filter (for vessel age/build year)
year_range = st.sidebar.slider(
    "Vessel Built Year Range",
    min_value=1900,
    max_value=2025,
    value=(1950, 2025),
    help="Filter vessels by their build year"
)

# Build filter dict
filters = {
    'operators': selected_operators,
    'vessel_types': selected_types,
    'districts': selected_districts,
    'series': selected_series,
    'fleet_year': fleet_year,  # NEW
    'year_range': year_range
}

# Display selected fleet year prominently
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"### 📅 Analyzing Fleet Year: **{fleet_year}**")
with col2:
    total_years = len(available_years_list)
    st.metric("Historical Years", total_years)

st.markdown("---")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Fleet Overview",
    "🏢 Operators",
    "⚓ Vessel Types",
    "🗺️ Geography",
    "🔧 Equipment",
    "🔍 Search & Export",
    "📈 Historical Trends"
])

# ============================================================
# TAB 1: FLEET OVERVIEW
# ============================================================
with tab1:
    st.header("Fleet Overview")

    # Get fleet summary
    summary = queries.get_fleet_summary(db, filters)

    if summary:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vessels", f"{summary['total_vessels']:,}")
        col2.metric("Operators", f"{summary['total_operators']:,}")
        col3.metric("Avg Vessel Age", f"{summary['avg_age']:.1f} years")
        col4.metric("Total NRT", f"{summary['total_nrt']:,.0f}")

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Vessel Types Distribution")
            type_dist = queries.get_vessel_type_distribution(db, filters)
            if not type_dist.empty:
                fig = px.pie(
                    type_dist,
                    values='count',
                    names='vtcc_vessel_type',
                    title="Vessels by Type"
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Fleet Age Distribution")
            age_dist = queries.get_age_distribution(db, filters)
            if not age_dist.empty:
                fig = px.bar(
                    age_dist,
                    x='age_category',
                    y='count',
                    title="Vessels by Age Category",
                    color='age_category',
                    color_discrete_map={
                        'Modern': '#2ecc71',
                        'Mature': '#f39c12',
                        'Legacy': '#e74c3c'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

        # Top operators
        st.subheader("Top 15 Operators by Fleet Size")
        top_operators = queries.get_top_operators(db, filters, limit=15)
        if not top_operators.empty:
            fig = px.bar(
                top_operators,
                x='vessel_count',
                y='operator_name',
                orientation='h',
                title="Largest Vessel Operators"
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 2: OPERATOR ANALYSIS
# ============================================================
with tab2:
    st.header("Operator Analysis")

    # Operator search
    operator_search = st.text_input("Search for operator by name:")

    if operator_search:
        # Get operator details
        operator_details = queries.get_operator_details(db, operator_search)

        if not operator_details.empty:
            op = operator_details.iloc[0]

            # Display operator info
            col1, col2, col3 = st.columns(3)
            col1.metric("Operator Name", op['operator_name'])
            col2.metric("Location", f"{op['operator_city']}, {op['operator_state']}")
            col3.metric("Total Vessels", f"{op['vessel_count']:,}")

            st.write(f"**Phone:** {op['phone']}")
            st.write(f"**District:** {op['district_name']}")
            st.write(f"**Service Type:** {op['service_name']}")
            st.write(f"**Principal Commodity:** {op['principal_commodity']}")

            st.markdown("---")

            # Fleet composition
            st.subheader("Fleet Composition")
            fleet_comp = queries.get_operator_fleet_composition(db, op['ts_oper'])
            if not fleet_comp.empty:
                fig = px.bar(
                    fleet_comp,
                    x='count',
                    y='characteristic_desc',
                    orientation='h',
                    title="Vessel Types Operated"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Vessel list
            st.subheader("Vessels")
            vessels = queries.get_operator_vessels(db, op['ts_oper'])
            if not vessels.empty:
                st.dataframe(vessels[['vessel_name', 'characteristic_desc', 'nrt', 'year_vessel', 'vessel_state']])
        else:
            st.warning("Operator not found. Try another search term.")
    else:
        st.info("Enter an operator name to view details")

# ============================================================
# TAB 3: VESSEL TYPE ANALYSIS
# ============================================================
with tab3:
    st.header("Vessel Type Analysis")

    # Get vessel type stats
    type_stats = queries.get_vessel_type_stats(db, filters)

    if not type_stats.empty:
        st.subheader("Vessel Types Summary")
        st.dataframe(type_stats)

        # Tonnage by type
        st.subheader("Average NRT by Vessel Type")
        fig = px.bar(
            type_stats,
            x='vtcc_vessel_type',
            y='avg_nrt',
            title="Average Net Registered Tonnage"
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 4: GEOGRAPHIC ANALYSIS
# ============================================================
with tab4:
    st.header("Geographic Distribution")

    # District distribution
    st.subheader("Vessels by Corps District")
    district_dist = queries.get_district_distribution(db, filters)

    if not district_dist.empty:
        fig = px.bar(
            district_dist.head(20),
            x='vessel_count',
            y='district_name',
            orientation='h',
            title="Top 20 Districts by Vessel Count"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # Series distribution
    st.subheader("Vessels by Region/Series")
    series_dist = queries.get_series_distribution(db, filters)
    if not series_dist.empty:
        fig = px.pie(
            series_dist,
            values='vessel_count',
            names='series_name',
            title="Regional Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 5: EQUIPMENT ANALYSIS
# ============================================================
with tab5:
    st.header("Equipment Inventory")

    # Equipment summary
    equipment_summary = queries.get_equipment_summary(db, filters)
    if not equipment_summary.empty:
        st.subheader("Equipment by Category")
        st.dataframe(equipment_summary)

# ============================================================
# TAB 6: SEARCH & EXPORT
# ============================================================
with tab6:
    st.header("Search & Export")

    st.subheader("Advanced Search")

    # Search form
    vessel_name_search = st.text_input("Vessel Name (partial match):")
    cg_number_search = st.text_input("Coast Guard Number:")

    if st.button("Search"):
        results = queries.search_vessels(db, vessel_name_search, cg_number_search, filters)

        if not results.empty:
            st.success(f"Found {len(results)} vessels")
            st.dataframe(results)

            # Export button
            csv = results.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="usace_vessel_search_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("No vessels found matching search criteria")

# ============================================================
# TAB 7: HISTORICAL TRENDS
# ============================================================
with tab7:
    st.header("Historical Trends & Comparisons")

    # Check if historical data is available
    try:
        available_years = historical_queries.get_available_years(db)

        if len(available_years) < 2:
            st.warning("""
            ⚠️ **Historical data not yet loaded.**

            Currently only {year_count} year(s) of data in database.

            To enable historical comparisons:
            1. Download historical data files (see scripts/usace/download_historical_data.md)
            2. Organize by year in data/raw/usace/YYYY/ folders
            3. Run: `python scripts/usace/load_historical_data.py --years 2020,2021,2022`

            Once loaded, this tab will show:
            - Year-over-year fleet growth trends
            - Operator expansion/contraction analysis
            - Vessel type trends over time
            - District-level changes
            - Equipment adoption trends
            """.format(year_count=len(available_years)))

            # Show what data is available
            st.subheader("Available Data:")
            st.dataframe(available_years)

        else:
            st.success(f"✓ Historical data available for {len(available_years)} years")

            # Fleet size trend
            st.subheader("Fleet Size Trend")
            fleet_trend = historical_queries.get_fleet_size_trend(db)
            if not fleet_trend.empty:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.line(
                        fleet_trend,
                        x='fleet_year',
                        y='vessel_count',
                        title="Total Vessels Over Time",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.line(
                        fleet_trend,
                        x='fleet_year',
                        y='operator_count',
                        title="Total Operators Over Time",
                        markers=True,
                        color_discrete_sequence=['#e74c3c']
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Year comparison
            st.markdown("---")
            st.subheader("Compare Two Years")
            col1, col2 = st.columns(2)
            years_list = available_years['fleet_year'].tolist()
            with col1:
                year1 = st.selectbox("Year 1", years_list, index=len(years_list)-2 if len(years_list) > 1 else 0)
            with col2:
                year2 = st.selectbox("Year 2", years_list, index=len(years_list)-1)

            if year1 and year2 and year1 != year2:
                comparison = historical_queries.compare_two_years(db, year1, year2)
                if not comparison.empty:
                    st.dataframe(comparison)

            # Fleet age trends
            st.markdown("---")
            st.subheader("Fleet Age Distribution Over Time")
            age_trends = historical_queries.get_fleet_age_trends(db)
            if not age_trends.empty:
                fig = px.area(
                    age_trends,
                    x='fleet_year',
                    y='vessel_count',
                    color='age_bracket',
                    title="Fleet Age Composition",
                    color_discrete_map={
                        'Modern (0-10 yrs)': '#2ecc71',
                        'Mature (11-20 yrs)': '#3498db',
                        'Aging (21-30 yrs)': '#f39c12',
                        'Legacy (30+ yrs)': '#e74c3c'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

            # Top growing operators
            st.markdown("---")
            st.subheader(f"Top Growing Operators ({year2})")
            latest_year = max(years_list)
            growing = historical_queries.get_top_growing_operators(db, latest_year, limit=15)
            if not growing.empty:
                fig = px.bar(
                    growing,
                    x='percent_change',
                    y='operator_name',
                    orientation='h',
                    title=f"Highest Growth Rates ({latest_year})",
                    color='percent_change',
                    color_continuous_scale='greens'
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

            # Vessel type trends
            st.markdown("---")
            st.subheader("Vessel Type Trends")
            type_trends = historical_queries.get_vessel_type_trends(db)
            if not type_trends.empty:
                # Get unique vessel types
                vessel_types_list = type_trends['vessel_type'].unique().tolist()
                selected_type = st.selectbox("Select Vessel Type", vessel_types_list)

                if selected_type:
                    type_data = type_trends[type_trends['vessel_type'] == selected_type]
                    fig = px.line(
                        type_data,
                        x='fleet_year',
                        y='vessel_count',
                        title=f"{selected_type} - Trend Over Time",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        st.info("Make sure historical schema extensions are applied: `python scripts/usace/init_database.py`")

# Footer
st.markdown("---")
st.caption("USACE Vessel Characteristics Database | Data from Waterborne Commerce Statistics Center")
