"""
Route Planning Page - Find optimal routes through inland waterways
"""

import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Route Planning", page_icon="🗺️", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("🗺️ Route Planning")
st.markdown("Find optimal routes through the inland waterway network")

# Sidebar for route inputs
with st.sidebar:
    st.markdown("## Route Parameters")

    # Node selection
    st.markdown("### Origin & Destination")

    # River filter for node search
    river_filter = st.text_input("Filter by River", placeholder="e.g., Mississippi")

    if st.button("Search Nodes"):
        try:
            params = {"limit": 100}
            if river_filter:
                params["river_name"] = river_filter

            response = requests.get(f"{API_BASE_URL}/api/routes/nodes", params=params)
            if response.status_code == 200:
                nodes_data = response.json()
                st.session_state['available_nodes'] = nodes_data['nodes']
                st.success(f"Found {nodes_data['count']} nodes")
            else:
                st.error("Failed to fetch nodes")
        except Exception as e:
            st.error(f"Error: {e}")

    # Node selection dropdowns
    if 'available_nodes' in st.session_state and st.session_state['available_nodes']:
        nodes = st.session_state['available_nodes']

        # Create node display strings
        node_options = {
            f"{node['node_id']} - {node['river_name']} ({node['state']})": node['node_id']
            for node in nodes
        }

        origin_display = st.selectbox("Origin Node", options=list(node_options.keys()))
        dest_display = st.selectbox("Destination Node", options=list(node_options.keys()))

        origin_node = node_options[origin_display]
        dest_node = node_options[dest_display]

        st.markdown("### Vessel Constraints")
        use_constraints = st.checkbox("Apply vessel constraints")

        vessel_beam = None
        vessel_draft = None

        if use_constraints:
            vessel_beam = st.number_input("Vessel Beam (meters)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)
            vessel_draft = st.number_input("Vessel Draft (meters)", min_value=0.5, max_value=20.0, value=3.0, step=0.5)

        st.markdown("### Algorithm")
        algorithm = st.radio("Routing Algorithm", ["dijkstra", "astar"])

        st.markdown("---")

        # Calculate route button
        if st.button("🔍 Calculate Route", use_container_width=True, type="primary"):
            with st.spinner("Calculating optimal route..."):
                try:
                    payload = {
                        "origin_node": origin_node,
                        "destination_node": dest_node,
                        "algorithm": algorithm
                    }

                    if use_constraints:
                        payload["vessel_beam_m"] = vessel_beam
                        payload["vessel_draft_m"] = vessel_draft

                    response = requests.post(f"{API_BASE_URL}/api/routes/calculate", json=payload)

                    if response.status_code == 200:
                        st.session_state['current_route'] = response.json()
                        st.success("✅ Route calculated successfully!")
                    elif response.status_code == 404:
                        st.error("❌ No route found between selected nodes")
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

                except Exception as e:
                    st.error(f"❌ Error calculating route: {e}")
    else:
        st.info("👆 Search for nodes to begin route planning")

# Main content area
if 'current_route' in st.session_state:
    route = st.session_state['current_route']

    # Route summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Distance", f"{route['total_distance_mi']:.1f} mi")

    with col2:
        st.metric("Transit Time", f"{route['transit_time_hours']:.1f} hrs")

    with col3:
        st.metric("Number of Links", route['num_links'])

    with col4:
        st.metric("Locks Encountered", route['num_locks'])

    st.markdown("---")

    # Route details tabs
    tab1, tab2, tab3 = st.tabs(["📋 Route Details", "🗺️ Map View", "⚠️ Constraints"])

    with tab1:
        st.markdown("### Route Segments")

        if route['segments']:
            segments_data = []
            for seg in route['segments']:
                segments_data.append({
                    "Link": seg['link_num'],
                    "River": seg.get('river_name', 'N/A'),
                    "Distance (mi)": f"{seg['distance_mi']:.2f}",
                    "From Node": seg['from_node'],
                    "To Node": seg['to_node']
                })

            df = pd.DataFrame(segments_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### Lock Passages")
        if route['lock_ids']:
            st.info(f"This route requires passage through {len(route['lock_ids'])} lock(s): {', '.join(map(str, route['lock_ids']))}")
        else:
            st.success("No locks required for this route")

    with tab2:
        st.markdown("### Route Map")

        # Create a simple map centered on US
        m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

        # Note: Without actual coordinates, we show a placeholder
        st.info("Map visualization requires coordinate data. This will be enhanced with actual route geometry.")

        st_folium(m, width=700, height=500)

    with tab3:
        st.markdown("### Constraint Violations")

        if route.get('feasible', True):
            st.success("✅ Route is feasible for the specified vessel")
        else:
            st.warning("⚠️ Some constraints may be violated on this route")

        if route.get('violations'):
            for violation in route['violations']:
                st.error(f"❌ {violation}")
        else:
            st.success("No constraint violations detected")

else:
    # Welcome message
    st.info("""
    ## Getting Started with Route Planning

    1. **Search for Nodes**: Use the sidebar to search for waterway nodes by river name
    2. **Select Origin & Destination**: Choose your starting and ending points
    3. **Set Constraints** (optional): Specify vessel beam and draft requirements
    4. **Choose Algorithm**: Select Dijkstra or A* pathfinding
    5. **Calculate Route**: Click the button to find the optimal path

    The system will find the shortest route while respecting lock and channel constraints.
    """)

    # Example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        **Mississippi River Route:**
        - Search for "Mississippi" to find nodes along the Mississippi River
        - Select nodes at different river miles for routing

        **Ohio River Route:**
        - Search for "Ohio" to find Ohio River nodes
        - Consider lock passages when planning routes

        **Vessel Constraints:**
        - Standard barge beam: ~10.7 meters (35 feet)
        - Typical draft: 2.7-3.7 meters (9-12 feet)
        """)
