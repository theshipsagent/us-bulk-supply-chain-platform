"""
Cargo Flow Analysis — Streamlit Interface

Analyse commodity movements, identify bottlenecks, and export report material
from BTS inland-waterway tonnage data.

Run:  streamlit run cargo_flow_tool/app.py --server.port 8503
"""

import sys
from pathlib import Path

# Project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from cargo_flow_tool.cargo_flow_analyzer import (
    CargoFlowAnalyzer,
    COMMODITY_COLORS,
    COMMODITY_NAMES,
    COMMODITY_COLS,
    VALUE_PER_TON,
)
from cargo_flow_tool.report_export import (
    df_to_csv_bytes,
    fig_to_png_bytes,
    generate_executive_summary,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cargo Flow Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load analyser (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def load_analyzer():
    a = CargoFlowAnalyzer()
    status = a.load_data()
    return a, status


analyzer, load_status = load_analyzer()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.title("Filters")

all_rivers = sorted(analyzer.links["RIVERNAME"].dropna().unique())
selected_rivers = st.sidebar.multiselect("Rivers", all_rivers, default=[])

all_commodities = list(COMMODITY_NAMES.keys())
commodity_labels = {k: COMMODITY_NAMES[k] for k in all_commodities}
selected_commodities = st.sidebar.multiselect(
    "Commodities",
    all_commodities,
    format_func=lambda x: commodity_labels.get(x, x),
    default=[],
)

top_n = st.sidebar.slider("Top N (charts / tables)", 5, 50, 20)

unit_mode = st.sidebar.radio("Units", ["Tons", "M Tons", "$ Value"], index=0)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Links: {load_status['joined_records']:,} | "
    f"Locks: {load_status['lock_records']:,} | "
    f"Nodes: {load_status['node_records']:,}"
)


def _scale(val: float | pd.Series, commodity: str | None = None) -> float | pd.Series:
    """Convert raw tons according to the selected unit mode."""
    if unit_mode == "M Tons":
        return val / 1_000_000
    if unit_mode == "$ Value" and commodity:
        vpt = VALUE_PER_TON.get(commodity, 0)
        return val * vpt
    return val


def _unit_label() -> str:
    if unit_mode == "M Tons":
        return "Million Tons"
    if unit_mode == "$ Value":
        return "USD"
    return "Tons"


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered = analyzer.filter_links(
    rivers=selected_rivers or None,
    commodities=selected_commodities or None,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Inland Waterway Cargo Flow Analysis")

# Key metrics row
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Tonnage", f"{filtered['total'].sum():,.0f}")
c2.metric("Links", f"{len(filtered):,}")
c3.metric("Rivers", f"{filtered['RIVERNAME'].nunique():,}")
c4.metric("States", f"{filtered['STATE'].nunique():,}")
c5.metric("Est. Value", f"${filtered['total_value'].sum():,.0f}")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "River Corridors",
    "Commodity Analysis",
    "Geographic View",
    "Bottleneck Analysis",
    "Directional Flows",
    "Report Export",
])

# ============================== TAB 1 ======================================
with tab1:
    st.subheader("Top River Corridors by Tonnage")

    rivers_df = analyzer.get_tonnage_by_river(top_n=top_n)
    if selected_rivers:
        rivers_df = rivers_df[rivers_df["RIVERNAME"].isin(selected_rivers)]

    if rivers_df.empty:
        st.info("No data for the selected filters.")
    else:
        # Stacked horizontal bar (upstream / downstream)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=rivers_df["RIVERNAME"],
            x=rivers_df["total_up"],
            name="Upstream",
            orientation="h",
            marker_color="#2196F3",
        ))
        fig.add_trace(go.Bar(
            y=rivers_df["RIVERNAME"],
            x=rivers_df["total_down"],
            name="Downstream",
            orientation="h",
            marker_color="#FF9800",
        ))
        fig.update_layout(
            barmode="stack",
            yaxis=dict(autorange="reversed"),
            height=max(400, len(rivers_df) * 28),
            margin=dict(l=220),
            xaxis_title="Tons",
            legend=dict(orientation="h", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True, key="rivers_bar")

        # Data table
        with st.expander("River detail table"):
            display_cols = ["RIVERNAME", "total_up", "total_down", "total", "net_flow", "link_count", "total_value"]
            st.dataframe(
                rivers_df[display_cols].style.format({
                    "total_up": "{:,.0f}",
                    "total_down": "{:,.0f}",
                    "total": "{:,.0f}",
                    "net_flow": "{:+,.0f}",
                    "total_value": "${:,.0f}",
                }),
                use_container_width=True,
            )

# ============================== TAB 2 ======================================
with tab2:
    st.subheader("National Commodity Mix")

    mix_df = analyzer.get_national_commodity_mix()

    col_left, col_right = st.columns(2)

    with col_left:
        # Donut chart
        fig_donut = go.Figure(go.Pie(
            labels=mix_df["display_name"],
            values=mix_df["total_tons"],
            hole=0.45,
            marker=dict(colors=[COMMODITY_COLORS.get(c, "#999") for c in mix_df["commodity"]]),
            textinfo="label+percent",
        ))
        fig_donut.update_layout(
            title="System-Wide Commodity Share",
            height=450,
            showlegend=False,
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="donut")

    with col_right:
        # Grouped bar upstream vs downstream
        fig_dir = go.Figure()
        fig_dir.add_trace(go.Bar(
            x=mix_df["display_name"],
            y=mix_df["upstream"],
            name="Upstream",
            marker_color="#2196F3",
        ))
        fig_dir.add_trace(go.Bar(
            x=mix_df["display_name"],
            y=mix_df["downstream"],
            name="Downstream",
            marker_color="#FF9800",
        ))
        fig_dir.update_layout(
            barmode="group",
            title="Upstream vs Downstream by Commodity",
            yaxis_title="Tons",
            height=450,
        )
        st.plotly_chart(fig_dir, use_container_width=True, key="commodity_dir")

    # Treemap: commodity x river (top rivers only)
    st.markdown("#### Commodity x River Treemap")
    tree_data = []
    top_river_names = analyzer.get_tonnage_by_river(top_n=min(top_n, 15))["RIVERNAME"].tolist()
    for key in COMMODITY_COLS:
        col_name = f"{key}_total"
        river_agg = (
            filtered[filtered["RIVERNAME"].isin(top_river_names)]
            .groupby("RIVERNAME")[col_name]
            .sum()
            .reset_index()
        )
        river_agg.columns = ["river", "tons"]
        river_agg["commodity"] = COMMODITY_NAMES[key]
        river_agg["color_key"] = key
        tree_data.append(river_agg[river_agg["tons"] > 0])

    if tree_data:
        tree_df = pd.concat(tree_data, ignore_index=True)
        if not tree_df.empty:
            fig_tree = px.treemap(
                tree_df,
                path=["commodity", "river"],
                values="tons",
                color="commodity",
                color_discrete_map={COMMODITY_NAMES[k]: COMMODITY_COLORS[k] for k in COMMODITY_COLORS},
                height=500,
            )
            fig_tree.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_tree, use_container_width=True, key="treemap")

    # Value estimates
    st.markdown("#### Estimated Cargo Value")
    val_df = analyzer.estimate_cargo_value()
    st.dataframe(
        val_df.style.format({
            "total_tons": "{:,.0f}",
            "value_per_ton": "${:,.0f}",
            "estimated_value": "${:,.0f}",
        }),
        use_container_width=True,
    )

# ============================== TAB 3 ======================================
with tab3:
    st.subheader("Geographic View")

    geo = analyzer.get_link_geometries()
    # Apply same filters
    if selected_rivers:
        geo = geo[geo["RIVERNAME"].isin(selected_rivers)]
    if selected_commodities:
        geo = geo[geo["primary_commodity"].isin(selected_commodities)]

    geo_valid = geo.dropna(subset=["anode_x", "anode_y", "bnode_x", "bnode_y"])

    if geo_valid.empty:
        st.info("No geolocated links for the selected filters.")
    else:
        # Build line layer data
        lines = []
        for _, row in geo_valid.iterrows():
            commodity = row["primary_commodity"]
            color_hex = COMMODITY_COLORS.get(commodity, "#BDBDBD")
            # Convert hex to RGB
            r_c = int(color_hex[1:3], 16)
            g_c = int(color_hex[3:5], 16)
            b_c = int(color_hex[5:7], 16)
            lines.append({
                "from_lon": row["anode_x"],
                "from_lat": row["anode_y"],
                "to_lon": row["bnode_x"],
                "to_lat": row["bnode_y"],
                "tonnage": row["total"],
                "river": row["RIVERNAME"],
                "commodity": commodity,
                "color_r": r_c,
                "color_g": g_c,
                "color_b": b_c,
            })
        lines_df = pd.DataFrame(lines)

        import pydeck as pdk

        # Width proportional to log tonnage
        max_ton = lines_df["tonnage"].max()
        if max_ton > 0:
            lines_df["width"] = np.clip(np.log1p(lines_df["tonnage"]) / np.log1p(max_ton) * 8, 1, 10)
        else:
            lines_df["width"] = 1

        line_layer = pdk.Layer(
            "LineLayer",
            data=lines_df,
            get_source_position=["from_lon", "from_lat"],
            get_target_position=["to_lon", "to_lat"],
            get_color=["color_r", "color_g", "color_b", 180],
            get_width="width",
            width_min_pixels=1,
            pickable=True,
        )

        # Lock markers
        lock_layers = []
        lock_overlay = analyzer.get_lock_traffic_overlay()
        if not lock_overlay.empty:
            lock_pts = lock_overlay.dropna(subset=["lock_x", "lock_y"]).copy()
            if not lock_pts.empty:
                max_score = lock_pts["bottleneck_score"].max()
                lock_pts["radius"] = np.clip(
                    lock_pts["bottleneck_score"] / (max_score if max_score else 1) * 8000,
                    1500,
                    10000,
                )
                lock_pts["color_r"] = lock_pts["is_600ft"].apply(lambda x: 244 if x else 33)
                lock_pts["color_g"] = lock_pts["is_600ft"].apply(lambda x: 67 if x else 150)
                lock_pts["color_b"] = lock_pts["is_600ft"].apply(lambda x: 54 if x else 243)

                lock_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=lock_pts,
                    get_position=["lock_x", "lock_y"],
                    get_radius="radius",
                    get_fill_color=["color_r", "color_g", "color_b", 160],
                    pickable=True,
                )
                lock_layers.append(lock_layer)

        # Centre on CONUS
        view = pdk.ViewState(latitude=38.5, longitude=-90, zoom=4, pitch=0)

        deck = pdk.Deck(
            layers=[line_layer] + lock_layers,
            initial_view_state=view,
            tooltip={
                "text": "River: {river}\nTonnage: {tonnage}\nCommodity: {commodity}",
            },
        )
        st.pydeck_chart(deck)

        # Legend
        st.markdown("**Legend — Link colour by primary commodity**")
        legend_cols = st.columns(len(COMMODITY_COLORS))
        for col, (key, hex_color) in zip(legend_cols, COMMODITY_COLORS.items()):
            col.markdown(
                f'<span style="color:{hex_color}; font-size:20px;">&#9632;</span> {COMMODITY_NAMES[key]}',
                unsafe_allow_html=True,
            )
        if lock_layers:
            st.markdown(
                "Lock markers: <span style='color:#F44336;'>&#9679;</span> 600-ft chamber &nbsp; "
                "<span style='color:#2196F3;'>&#9679;</span> Standard chamber &nbsp; (size = bottleneck score)",
                unsafe_allow_html=True,
            )

# ============================== TAB 4 ======================================
with tab4:
    st.subheader("Lock Bottleneck Analysis")

    lock_df = analyzer.get_lock_traffic_overlay()

    if lock_df.empty:
        st.info("No lock overlay data available.")
    else:
        col_l, col_r = st.columns(2)

        with col_l:
            # Scatter: chamber area vs tonnage
            lock_df["chamber_area"] = lock_df["chamber_length"] * lock_df["chamber_width"]
            fig_scatter = px.scatter(
                lock_df,
                x="chamber_area",
                y="adjacent_tonnage",
                color="is_600ft",
                color_discrete_map={True: "#F44336", False: "#2196F3"},
                hover_name="lock_name",
                hover_data=["river", "chamber_length", "chamber_width"],
                labels={
                    "chamber_area": "Chamber Area (sq ft)",
                    "adjacent_tonnage": "Adjacent Link Tonnage",
                    "is_600ft": "600-ft Chamber",
                },
                title="Chamber Size vs Adjacent Tonnage",
                height=450,
            )
            st.plotly_chart(fig_scatter, use_container_width=True, key="lock_scatter")

        with col_r:
            # Top constrained locks bar
            top_locks = lock_df.head(top_n)
            fig_lock_bar = go.Figure(go.Bar(
                y=top_locks["lock_name"],
                x=top_locks["bottleneck_score"],
                orientation="h",
                marker_color=[
                    "#F44336" if is600 else "#2196F3"
                    for is600 in top_locks["is_600ft"]
                ],
                text=top_locks["river"],
                textposition="inside",
            ))
            fig_lock_bar.update_layout(
                title="Most Constrained Locks",
                xaxis_title="Bottleneck Score (tonnage / chamber area)",
                yaxis=dict(autorange="reversed"),
                height=max(400, len(top_locks) * 28),
                margin=dict(l=250),
            )
            st.plotly_chart(fig_lock_bar, use_container_width=True, key="lock_bar")

        # 600-ft chamber flag table
        small_chambers = lock_df[lock_df["is_600ft"]]
        if not small_chambers.empty:
            st.markdown(
                f"#### 600-ft (or smaller) Chambers — {len(small_chambers)} locks"
            )
            st.caption(
                "These locks require double lockage for a standard 15-barge tow (1,200 ft), "
                "roughly doubling transit delay."
            )
            display = small_chambers[
                ["lock_name", "river", "river_mile", "state", "chamber_length",
                 "chamber_width", "adjacent_tonnage", "bottleneck_score"]
            ]
            st.dataframe(
                display.style.format({
                    "adjacent_tonnage": "{:,.0f}",
                    "bottleneck_score": "{:,.1f}",
                }),
                use_container_width=True,
            )

# ============================== TAB 5 ======================================
with tab5:
    st.subheader("Directional Flow Analysis")

    col_l5, col_r5 = st.columns(2)

    with col_l5:
        # Diverging bar chart — net flow by river
        dir_river = analyzer.get_directional_flow_by_river(top_n=top_n)
        if selected_rivers:
            dir_river = dir_river[dir_river["RIVERNAME"].isin(selected_rivers)]

        if not dir_river.empty:
            colors = [
                "#FF9800" if nf > 0 else "#2196F3"
                for nf in dir_river["net_flow"]
            ]
            fig_div = go.Figure(go.Bar(
                y=dir_river["RIVERNAME"],
                x=dir_river["net_flow"],
                orientation="h",
                marker_color=colors,
            ))
            fig_div.update_layout(
                title="Net Flow by River (+ = downstream dominant)",
                xaxis_title="Net Flow (tons)",
                yaxis=dict(autorange="reversed"),
                height=max(400, len(dir_river) * 28),
                margin=dict(l=220),
            )
            st.plotly_chart(fig_div, use_container_width=True, key="div_bar")
        else:
            st.info("No directional data for selected filters.")

    with col_r5:
        # Commodity direction patterns
        dir_comm = analyzer.get_directional_flow_by_commodity()

        fig_comm_dir = go.Figure()
        fig_comm_dir.add_trace(go.Bar(
            x=dir_comm["display_name"],
            y=dir_comm["upstream"],
            name="Upstream",
            marker_color="#2196F3",
        ))
        fig_comm_dir.add_trace(go.Bar(
            x=dir_comm["display_name"],
            y=[-d for d in dir_comm["downstream"]],
            name="Downstream",
            marker_color="#FF9800",
        ))
        fig_comm_dir.update_layout(
            barmode="relative",
            title="Commodity Direction Patterns",
            yaxis_title="Tons (upstream +, downstream -)",
            height=450,
        )
        st.plotly_chart(fig_comm_dir, use_container_width=True, key="comm_dir")

    # Upstream / downstream analysis table
    st.markdown("#### Upstream vs Downstream Detail")
    dir_comm_display = dir_comm[["display_name", "upstream", "downstream", "net_flow", "direction"]]
    st.dataframe(
        dir_comm_display.style.format({
            "upstream": "{:,.0f}",
            "downstream": "{:,.0f}",
            "net_flow": "{:+,.0f}",
        }),
        use_container_width=True,
    )

# ============================== TAB 6 ======================================
with tab6:
    st.subheader("Report Export")

    # Generate executive summary
    rivers_all = analyzer.get_tonnage_by_river(top_n=10)
    mix_all = analyzer.get_national_commodity_mix()
    corridors_all = analyzer.get_top_corridors(top_n=10)
    lock_all = analyzer.get_lock_traffic_overlay()
    value_all = analyzer.estimate_cargo_value()

    summary_md = generate_executive_summary(
        total_tonnage=analyzer.links["total"].sum(),
        joined_records=load_status["joined_records"],
        top_rivers=rivers_all,
        commodity_mix=mix_all,
        top_corridors=corridors_all,
        lock_overlay=lock_all,
        cargo_value=value_all,
    )

    st.markdown("#### Executive Summary Preview")
    st.markdown(summary_md)

    st.markdown("---")
    st.markdown("#### Downloads")

    dl1, dl2, dl3, dl4 = st.columns(4)

    with dl1:
        st.download_button(
            "Executive Summary (.md)",
            data=summary_md,
            file_name="cargo_flow_executive_summary.md",
            mime="text/markdown",
        )

    with dl2:
        st.download_button(
            "River Tonnage (.csv)",
            data=df_to_csv_bytes(analyzer.get_tonnage_by_river(top_n=None)),
            file_name="river_tonnage.csv",
            mime="text/csv",
        )

    with dl3:
        st.download_button(
            "Commodity Mix (.csv)",
            data=df_to_csv_bytes(mix_all),
            file_name="commodity_mix.csv",
            mime="text/csv",
        )

    with dl4:
        st.download_button(
            "Lock Bottlenecks (.csv)",
            data=df_to_csv_bytes(lock_all) if not lock_all.empty else b"No data",
            file_name="lock_bottlenecks.csv",
            mime="text/csv",
        )

    dl5, dl6, dl7, dl8 = st.columns(4)

    with dl5:
        st.download_button(
            "Top Corridors (.csv)",
            data=df_to_csv_bytes(corridors_all),
            file_name="top_corridors.csv",
            mime="text/csv",
        )

    with dl6:
        st.download_button(
            "Cargo Value (.csv)",
            data=df_to_csv_bytes(value_all),
            file_name="cargo_value_estimates.csv",
            mime="text/csv",
        )

    with dl7:
        st.download_button(
            "Directional by River (.csv)",
            data=df_to_csv_bytes(analyzer.get_directional_flow_by_river(top_n=None)),
            file_name="directional_flow_rivers.csv",
            mime="text/csv",
        )

    with dl8:
        st.download_button(
            "State Tonnage (.csv)",
            data=df_to_csv_bytes(analyzer.get_tonnage_by_state()),
            file_name="tonnage_by_state.csv",
            mime="text/csv",
        )
