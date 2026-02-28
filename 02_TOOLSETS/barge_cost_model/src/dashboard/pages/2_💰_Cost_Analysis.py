"""
Cost Analysis Page - Calculate and compare transportation costs
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Cost Analysis", page_icon="💰", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("💰 Cost Analysis")
st.markdown("Calculate and compare inland waterway transportation costs")

# Get current pricing rates
try:
    fuel_response = requests.get(f"{API_BASE_URL}/api/costs/fuel-rate")
    crew_response = requests.get(f"{API_BASE_URL}/api/costs/crew-rate")
    lock_response = requests.get(f"{API_BASE_URL}/api/costs/lock-fee")

    if all(r.status_code == 200 for r in [fuel_response, crew_response, lock_response]):
        fuel_rate = fuel_response.json()
        crew_rate = crew_response.json()
        lock_fee = lock_response.json()

        with st.expander("💵 Current Pricing Rates"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fuel Price", f"${fuel_rate['fuel_price_usd_per_gallon']:.2f}/gal")
            with col2:
                st.metric("Crew Rate", f"${crew_rate['crew_hourly_rate_usd']:.2f}/hr")
            with col3:
                st.metric("Lock Fee", f"${lock_fee['lock_fee_usd']:.2f}")
except:
    pass

# Sidebar for cost calculation inputs
with st.sidebar:
    st.markdown("## Cost Calculation")

    st.markdown("### Route Selection")

    # Use session route if available
    use_session_route = st.checkbox("Use route from Route Planning page",
                                      value='current_route' in st.session_state)

    if not use_session_route:
        # Manual node entry
        origin_node = st.number_input("Origin Node ID", min_value=1, value=450)
        dest_node = st.number_input("Destination Node ID", min_value=1, value=460)

        vessel_beam = st.number_input("Vessel Beam (m)", min_value=1.0, value=10.0, step=0.5)
        vessel_draft = st.number_input("Vessel Draft (m)", min_value=0.5, value=3.0, step=0.5)

    st.markdown("### Vessel Specifications")
    vessel_dwt = st.number_input("Vessel DWT (tons)", min_value=100, max_value=200000, value=5000, step=100)
    crew_size = st.number_input("Crew Size", min_value=1, max_value=50, value=5)

    include_terminals = st.checkbox("Include Terminal Costs", value=True)

    st.markdown("---")

    if st.button("💰 Calculate Costs", use_container_width=True, type="primary"):
        with st.spinner("Calculating costs..."):
            try:
                if use_session_route and 'current_route' in st.session_state:
                    route = st.session_state['current_route']
                    origin_node = route.get('origin_node')
                    dest_node = route.get('destination_node')
                    vessel_beam = None
                    vessel_draft = None
                else:
                    pass  # Use manual inputs

                payload = {
                    "origin_node": origin_node,
                    "destination_node": dest_node,
                    "vessel_dwt": vessel_dwt,
                    "crew_size": crew_size,
                    "include_terminals": include_terminals
                }

                if vessel_beam and vessel_draft:
                    payload["vessel_beam_m"] = vessel_beam
                    payload["vessel_draft_m"] = vessel_draft

                response = requests.post(f"{API_BASE_URL}/api/costs/calculate", json=payload)

                if response.status_code == 200:
                    st.session_state['cost_result'] = response.json()
                    st.success("✅ Costs calculated!")
                elif response.status_code == 404:
                    st.error("❌ No route found")
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ Error: {e}")

# Main content
if 'cost_result' in st.session_state:
    cost = st.session_state['cost_result']

    # Cost summary
    st.markdown("## 📊 Cost Breakdown")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Cost", f"${cost['total_cost_usd']:,.2f}")

    with col2:
        st.metric("Fuel Cost", f"${cost['fuel_cost_usd']:,.2f}")

    with col3:
        st.metric("Crew Cost", f"${cost['crew_cost_usd']:,.2f}")

    with col4:
        st.metric("Lock Fees", f"${cost['lock_cost_usd']:,.2f}")

    with col5:
        if include_terminals:
            st.metric("Terminal Costs", f"${cost.get('terminal_cost_usd', 0):,.2f}")
        else:
            st.metric("Delay Cost", f"${cost.get('delay_cost_usd', 0):,.2f}")

    st.markdown("---")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💵 Cost Distribution")

        # Pie chart of costs
        cost_breakdown = {
            'Fuel': cost['fuel_cost_usd'],
            'Crew': cost['crew_cost_usd'],
            'Locks': cost['lock_cost_usd']
        }

        if include_terminals and cost.get('terminal_cost_usd', 0) > 0:
            cost_breakdown['Terminals'] = cost['terminal_cost_usd']

        if cost.get('delay_cost_usd', 0) > 0:
            cost_breakdown['Delays'] = cost['delay_cost_usd']

        fig = px.pie(
            values=list(cost_breakdown.values()),
            names=list(cost_breakdown.keys()),
            title="Cost Distribution by Category"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📊 Cost Breakdown")

        # Bar chart
        fig = go.Figure([go.Bar(
            x=list(cost_breakdown.keys()),
            y=list(cost_breakdown.values()),
            text=[f"${v:,.0f}" for v in cost_breakdown.values()],
            textposition='auto',
        )])

        fig.update_layout(
            title="Cost Components",
            yaxis_title="Cost (USD)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    # Detailed breakdown
    st.markdown("---")
    st.markdown("### 📝 Detailed Cost Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Fuel Consumption")
        st.write(f"**Fuel Used:** {cost['fuel_gallons']:,.1f} gallons")
        st.write(f"**Fuel Cost:** ${cost['fuel_cost_usd']:,.2f}")
        st.write(f"**DWT Factor:** {vessel_dwt:,} tons")

    with col2:
        st.markdown("#### Labor Costs")
        st.write(f"**Crew Size:** {crew_size} members")
        st.write(f"**Transit Time:** {cost.get('transit_hours', 0):.1f} hours")
        st.write(f"**Crew Cost:** ${cost['crew_cost_usd']:,.2f}")

    # Cost per mile and per ton metrics
    st.markdown("---")
    st.markdown("### 📈 Efficiency Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Assuming we have distance from route
        st.metric("Cost per Mile", f"${cost['total_cost_usd'] / max(cost.get('distance_mi', 1), 1):,.2f}/mi")

    with col2:
        st.metric("Cost per DWT", f"${cost['total_cost_usd'] / vessel_dwt:,.2f}/ton")

    with col3:
        st.metric("Cost per Hour", f"${cost['total_cost_usd'] / max(cost.get('transit_hours', 1), 1):,.2f}/hr")

else:
    # Welcome message
    st.info("""
    ## 💡 Cost Analysis Guide

    ### How to Use This Tool:

    1. **Select a Route**
       - Use a route from the Route Planning page, OR
       - Enter origin and destination nodes manually

    2. **Specify Vessel Details**
       - Enter vessel deadweight tonnage (DWT)
       - Set crew size (typically 5-10 for barges)
       - Toggle terminal costs if needed

    3. **Calculate Costs**
       - Click the "Calculate Costs" button
       - View comprehensive cost breakdown
       - Analyze efficiency metrics

    ### Cost Components:

    - **Fuel Costs**: Based on distance and vessel size
    - **Crew Costs**: Wages for transit time including delays
    - **Lock Fees**: Standard fee per lock passage
    - **Terminal Costs**: Loading/unloading at origin and destination
    - **Delay Costs**: Additional costs from lock wait times
    """)

    # Sample calculation example
    with st.expander("📊 Sample Cost Calculation"):
        st.markdown("""
        **Example Route: 100 miles**
        - Vessel: 5,000 DWT
        - Crew: 5 members
        - Locks: 2 passages

        **Estimated Costs:**
        - Fuel: ~$2,500
        - Crew: ~$1,200
        - Locks: ~$600
        - **Total: ~$4,300**

        *Actual costs vary based on route specifics and current rates*
        """)
