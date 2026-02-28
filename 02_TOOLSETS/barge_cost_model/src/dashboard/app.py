"""
Interactive Barge Dashboard - Main Application
A comprehensive tool for inland waterway routing and cost analysis.
"""

import streamlit as st
import requests
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="Interactive Barge Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://127.0.0.1:8000"


def check_api_health():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #0066CC;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-card {
        background-color: #F0F2F6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #0066CC;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0066CC;
    }
    .stat-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/0066CC/FFFFFF?text=Barge+Dashboard", use_container_width=True)

    st.markdown("## Navigation")
    st.markdown("Use the pages in the sidebar to navigate the dashboard.")

    st.markdown("---")

    # API Status
    api_status = check_api_health()
    if api_status:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Offline")
        st.warning("Start the API with: `uvicorn src.api.main:app`")

    st.markdown("---")

    st.markdown("### Quick Stats")
    if api_status:
        try:
            response = requests.get(f"{API_BASE_URL}/api/info/stats")
            if response.status_code == 200:
                stats = response.json()
                st.metric("Total Records", f"{stats['total_records']:,}")
                st.metric("Waterway Links", f"{stats['tables']['waterway_links']:,}")
                st.metric("Docks", f"{stats['tables']['docks']:,}")
                st.metric("Vessels", f"{stats['tables']['vessels']:,}")
        except:
            pass

# Main content
st.markdown('<div class="main-header">🚢 Interactive Barge Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Inland Waterway Routing & Cost Analysis System</div>', unsafe_allow_html=True)

# Welcome section
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🗺️ Route Planning")
    st.markdown("""
    Find optimal routes through the inland waterway network with:
    - Dijkstra & A* pathfinding algorithms
    - Vessel constraint checking
    - Lock and channel clearance validation
    """)
    if st.button("Go to Route Planning", use_container_width=True):
        st.switch_page("pages/1_🗺️_Route_Planning.py")

with col2:
    st.markdown("### 💰 Cost Analysis")
    st.markdown("""
    Calculate and compare transportation costs:
    - Fuel consumption estimates
    - Crew wages and lock fees
    - Terminal handling costs
    - Route comparison tools
    """)
    if st.button("Go to Cost Analysis", use_container_width=True):
        st.switch_page("pages/2_💰_Cost_Analysis.py")

with col3:
    st.markdown("### 🔍 Search & Explore")
    st.markdown("""
    Search the comprehensive database:
    - 20,000+ navigation facilities
    - 50,000+ vessel specifications
    - 6,800+ waterway segments
    - Lock and river information
    """)
    if st.button("Go to Search", use_container_width=True):
        st.switch_page("pages/3_🔍_Search_Explore.py")

st.markdown("---")

# System Overview
if api_status:
    st.markdown("## 📊 System Overview")

    try:
        response = requests.get(f"{API_BASE_URL}/api/info/stats")
        if response.status_code == 200:
            stats = response.json()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-value">{stats["tables"]["waterway_links"]:,}</div>', unsafe_allow_html=True)
                st.markdown('<div class="stat-label">Waterway Links</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-value">{stats["tables"]["locks"]:,}</div>', unsafe_allow_html=True)
                st.markdown('<div class="stat-label">Lock Facilities</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col3:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-value">{stats["tables"]["docks"]:,}</div>', unsafe_allow_html=True)
                st.markdown('<div class="stat-label">Navigation Facilities</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col4:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-value">{stats["tables"]["vessels"]:,}</div>', unsafe_allow_html=True)
                st.markdown('<div class="stat-label">Vessel Records</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # Tonnage Overview
        st.markdown("### 📦 Cargo Tonnage Overview")
        response = requests.get(f"{API_BASE_URL}/api/info/tonnage")
        if response.status_code == 200:
            tonnage = response.json()

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Upstream", f"{tonnage['total_upstream_tons']:,} tons")
                st.metric("Total Downstream", f"{tonnage['total_downstream_tons']:,} tons")

            with col2:
                commodities = tonnage['by_commodity']
                st.metric("Coal", f"{commodities['coal_tons']:,} tons")
                st.metric("Farm Products", f"{commodities['farm_products_tons']:,} tons")

    except Exception as e:
        st.error(f"Error loading overview data: {e}")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Interactive Barge Dashboard v1.0.0</p>
    <p>Built with Streamlit • FastAPI • PostgreSQL • NetworkX</p>
</div>
""", unsafe_allow_html=True)
