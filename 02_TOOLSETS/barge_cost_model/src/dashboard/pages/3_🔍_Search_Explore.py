"""
Search & Explore Page - Search database for docks, locks, vessels, and waterways
"""

import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Search & Explore", page_icon="🔍", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("🔍 Search & Explore")
st.markdown("Search the comprehensive inland waterway database")

# Search type selector
search_type = st.radio(
    "Search Category",
    ["🏭 Docks & Facilities", "🔒 Locks", "🚢 Vessels", "🌊 Waterways"],
    horizontal=True
)

st.markdown("---")

# ====================
# DOCKS SEARCH
# ====================
if search_type == "🏭 Docks & Facilities":
    st.markdown("## 🏭 Navigation Facilities Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        dock_name = st.text_input("Facility Name", placeholder="e.g., New Orleans")

    with col2:
        dock_state = st.text_input("State Code", placeholder="e.g., LA", max_chars=2)

    with col3:
        dock_port = st.text_input("Port Name", placeholder="e.g., Port of Houston")

    col1, col2, col3 = st.columns(3)

    with col1:
        fac_type = st.selectbox("Facility Type", ["All", "Dock", "Terminal", "Fleeting_Area", "Anchorage", "Lock"])

    with col2:
        min_depth = st.number_input("Min Depth (feet)", min_value=0.0, value=0.0, step=1.0)

    with col3:
        limit = st.number_input("Max Results", min_value=1, max_value=500, value=50)

    if st.button("🔍 Search Docks", use_container_width=True, type="primary"):
        with st.spinner("Searching..."):
            try:
                params = {"limit": limit}
                if dock_name:
                    params["name"] = dock_name
                if dock_state:
                    params["state"] = dock_state
                if dock_port:
                    params["port"] = dock_port
                if fac_type != "All":
                    params["fac_type"] = fac_type
                if min_depth > 0:
                    params["min_depth"] = min_depth

                response = requests.get(f"{API_BASE_URL}/api/search/docks", params=params)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['dock_results'] = data['results']
                    st.success(f"Found {data['count']} facilities")
                else:
                    st.error("Search failed")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'dock_results' in st.session_state and st.session_state['dock_results']:
        results = st.session_state['dock_results']

        # Display results
        st.markdown(f"### Results ({len(results)} facilities)")

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Map visualization
        if st.checkbox("Show on Map"):
            m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

            for dock in results:
                if dock['latitude'] and dock['longitude']:
                    folium.Marker(
                        location=[dock['latitude'], dock['longitude']],
                        popup=f"{dock['name']}<br>{dock['city']}, {dock['state']}",
                        tooltip=dock['name']
                    ).add_to(m)

            st_folium(m, width=700, height=500)

# ====================
# LOCKS SEARCH
# ====================
elif search_type == "🔒 Locks":
    st.markdown("## 🔒 Lock Facilities Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        lock_name = st.text_input("Lock Name", placeholder="e.g., Lock 27")

    with col2:
        lock_river = st.text_input("River Name", placeholder="e.g., Mississippi")

    with col3:
        lock_state = st.text_input("State Code", placeholder="e.g., IL", max_chars=2)

    col1, col2, col3 = st.columns(3)

    with col1:
        min_width = st.number_input("Min Chamber Width (feet)", min_value=0.0, value=0.0)

    with col2:
        min_length = st.number_input("Min Chamber Length (feet)", min_value=0.0, value=0.0)

    with col3:
        limit = st.number_input("Max Results", min_value=1, max_value=200, value=50, key="lock_limit")

    if st.button("🔍 Search Locks", use_container_width=True, type="primary"):
        with st.spinner("Searching..."):
            try:
                params = {"limit": limit}
                if lock_name:
                    params["name"] = lock_name
                if lock_river:
                    params["river"] = lock_river
                if lock_state:
                    params["state"] = lock_state
                if min_width > 0:
                    params["min_width"] = min_width
                if min_length > 0:
                    params["min_length"] = min_length

                response = requests.get(f"{API_BASE_URL}/api/search/locks", params=params)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['lock_results'] = data['results']
                    st.success(f"Found {data['count']} locks")
                else:
                    st.error("Search failed")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'lock_results' in st.session_state and st.session_state['lock_results']:
        results = st.session_state['lock_results']

        st.markdown(f"### Results ({len(results)} locks)")

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Map visualization
        if st.checkbox("Show on Map", key="lock_map"):
            m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

            for lock in results:
                if lock['latitude'] and lock['longitude']:
                    folium.Marker(
                        location=[lock['latitude'], lock['longitude']],
                        popup=f"{lock['name']}<br>{lock['river']}<br>Width: {lock['width_ft']}ft",
                        tooltip=lock['name'],
                        icon=folium.Icon(color='red', icon='lock')
                    ).add_to(m)

            st_folium(m, width=700, height=500)

# ====================
# VESSELS SEARCH
# ====================
elif search_type == "🚢 Vessels":
    st.markdown("## 🚢 Vessel Registry Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        vessel_name = st.text_input("Vessel Name", placeholder="e.g., Atlantic")

    with col2:
        vessel_imo = st.text_input("IMO Number", placeholder="e.g., 9123456")

    with col3:
        vessel_type = st.text_input("Vessel Type", placeholder="e.g., Tanker")

    col1, col2, col3 = st.columns(3)

    with col1:
        max_beam = st.number_input("Max Beam (meters)", min_value=0.0, value=0.0)

    with col2:
        max_draft = st.number_input("Max Draft (meters)", min_value=0.0, value=0.0)

    with col3:
        limit = st.number_input("Max Results", min_value=1, max_value=500, value=50, key="vessel_limit")

    if st.button("🔍 Search Vessels", use_container_width=True, type="primary"):
        with st.spinner("Searching..."):
            try:
                params = {"limit": limit}
                if vessel_name:
                    params["name"] = vessel_name
                if vessel_imo:
                    params["imo"] = vessel_imo
                if vessel_type:
                    params["vessel_type"] = vessel_type
                if max_beam > 0:
                    params["max_beam"] = max_beam
                if max_draft > 0:
                    params["max_draft"] = max_draft

                response = requests.get(f"{API_BASE_URL}/api/search/vessels", params=params)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['vessel_results'] = data['results']
                    st.success(f"Found {data['count']} vessels")
                else:
                    st.error("Search failed")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'vessel_results' in st.session_state and st.session_state['vessel_results']:
        results = st.session_state['vessel_results']

        st.markdown(f"### Results ({len(results)} vessels)")

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Statistics
        if len(results) > 1:
            st.markdown("### 📊 Fleet Statistics")
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_dwt = sum(v['dwt'] for v in results if v['dwt']) / len([v for v in results if v['dwt']])
                st.metric("Average DWT", f"{avg_dwt:,.0f} tons")

            with col2:
                avg_beam = sum(v['beam_m'] for v in results if v['beam_m']) / len([v for v in results if v['beam_m']])
                st.metric("Average Beam", f"{avg_beam:.1f} m")

            with col3:
                avg_draft = sum(v['draft_m'] for v in results if v['draft_m']) / len([v for v in results if v['draft_m']])
                st.metric("Average Draft", f"{avg_draft:.1f} m")

# ====================
# WATERWAYS SEARCH
# ====================
elif search_type == "🌊 Waterways":
    st.markdown("## 🌊 Waterway Links Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        river_name = st.text_input("River Name", placeholder="e.g., Ohio River")

    with col2:
        state = st.text_input("State Code", placeholder="e.g., OH", max_chars=2)

    with col3:
        waterway_code = st.text_input("Waterway Code", placeholder="e.g., 6101")

    limit = st.number_input("Max Results", min_value=1, max_value=500, value=100, key="waterway_limit")

    if st.button("🔍 Search Waterways", use_container_width=True, type="primary"):
        with st.spinner("Searching..."):
            try:
                params = {"limit": limit}
                if river_name:
                    params["river_name"] = river_name
                if state:
                    params["state"] = state
                if waterway_code:
                    params["waterway_code"] = waterway_code

                response = requests.get(f"{API_BASE_URL}/api/search/waterways", params=params)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['waterway_results'] = data['results']
                    st.success(f"Found {data['count']} waterway links")
                else:
                    st.error("Search failed")

            except Exception as e:
                st.error(f"Error: {e}")

    if 'waterway_results' in st.session_state and st.session_state['waterway_results']:
        results = st.session_state['waterway_results']

        st.markdown(f"### Results ({len(results)} links)")

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Statistics
        if len(results) > 1:
            st.markdown("### 📊 Network Statistics")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_miles = sum(link['length_miles'] for link in results if link['length_miles'])
                st.metric("Total Length", f"{total_miles:,.1f} miles")

            with col2:
                unique_rivers = len(set(link['river_name'] for link in results if link['river_name']))
                st.metric("Unique Rivers", unique_rivers)

            with col3:
                unique_states = len(set(link['state'] for link in results if link['state']))
                st.metric("States Covered", unique_states)
