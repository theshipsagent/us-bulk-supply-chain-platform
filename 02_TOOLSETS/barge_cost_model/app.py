"""
Barge Route Cost Calculator - Streamlit Interface

Select origin and destination by river + mile marker.
Get route details, locks, transit time, rate forecast, cost breakdown, and rail comparison.
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from costing_tool.barge_cost_calculator import (
    BargeCostCalculator,
    USDA_SEGMENT_DEFINITIONS,
    KNOWN_JUNCTIONS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Barge Route Cost Calculator",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Initialize calculator (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def load_calculator():
    calc = BargeCostCalculator()
    status = calc.load_data()
    return calc, status


calc, load_status = load_calculator()


# ---------------------------------------------------------------------------
# Sidebar: Inputs
# ---------------------------------------------------------------------------

st.sidebar.title("Route Parameters")

# River selections
major_rivers = [
    "MISSISSIPPI RIVER",
    "OHIO RIVER",
    "ILLINOIS RIVER",
    "MISSOURI RIVER",
    "TENNESSEE RIVER",
    "ARKANSAS RIVER",
    "CUMBERLAND RIVER",
    "MONONGAHELA RIVER",
    "ALLEGHENY RIVER",
]
available_rivers = [r for r in major_rivers if r in calc.rivers_available]

# --- ORIGIN ---
st.sidebar.subheader("Origin")
origin_river = st.sidebar.selectbox(
    "Origin River",
    available_rivers,
    index=available_rivers.index("ILLINOIS RIVER") if "ILLINOIS RIVER" in available_rivers else 0,
    key="origin_river",
)
origin_range = calc.get_mile_range(origin_river)
origin_locks = calc.get_locks_on_river(origin_river)

# Show lock reference for this river
if origin_locks:
    lock_ref = ", ".join([f"M{l.mile:.0f}" for l in origin_locks[:5]])
    if len(origin_locks) > 5:
        lock_ref += f"... ({len(origin_locks)} locks)"
    st.sidebar.caption(f"Locks: {lock_ref}")

origin_mile = st.sidebar.number_input(
    f"Origin Mile Marker ({origin_range[0]:.0f}-{origin_range[1]:.0f})",
    min_value=float(origin_range[0]),
    max_value=float(origin_range[1]),
    value=min(231.0, float(origin_range[1])),
    step=1.0,
    key="origin_mile",
)

# --- DESTINATION ---
st.sidebar.subheader("Destination")
dest_river = st.sidebar.selectbox(
    "Destination River",
    available_rivers,
    index=available_rivers.index("MISSISSIPPI RIVER") if "MISSISSIPPI RIVER" in available_rivers else 0,
    key="dest_river",
)
dest_range = calc.get_mile_range(dest_river)
dest_locks = calc.get_locks_on_river(dest_river)

if dest_locks:
    lock_ref = ", ".join([f"M{l.mile:.0f}" for l in dest_locks[:5]])
    if len(dest_locks) > 5:
        lock_ref += f"... ({len(dest_locks)} locks)"
    st.sidebar.caption(f"Locks: {lock_ref}")

dest_mile = st.sidebar.number_input(
    f"Dest Mile Marker ({dest_range[0]:.0f}-{dest_range[1]:.0f})",
    min_value=float(dest_range[0]),
    max_value=float(dest_range[1]),
    value=min(100.0, float(dest_range[1])),
    step=1.0,
    key="dest_mile",
)

# --- CONFIGURATION ---
st.sidebar.subheader("Configuration")

tow_config = st.sidebar.selectbox(
    "Tow Configuration",
    ["15-barge (22,500 tons)", "6-barge (9,000 tons)", "Custom"],
    index=0,
)

if tow_config == "Custom":
    cargo_tons = st.sidebar.number_input("Cargo Tons", value=22500, step=500)
else:
    cargo_tons = 22500 if "15" in tow_config else 9000

speed_mph = st.sidebar.slider(
    "Avg Speed (mph)",
    min_value=3.0,
    max_value=10.0,
    value=6.0,
    step=0.5,
    help="Typical: 5 upstream, 8 downstream, 6 average"
)

markup = st.sidebar.number_input(
    "Rate Markup ($/ton)",
    value=2.00,
    step=0.50,
    help="Added to USDA base rate (overhead, margin)"
)

rail_rate = st.sidebar.number_input(
    "Rail Rate ($/ton-mile)",
    value=0.04,
    step=0.01,
    format="%.3f",
    help="For comparison. Typical: $0.04-$0.08"
)

# Calculate button
calculate = st.sidebar.button("Calculate Route Cost", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("Barge Route Cost Calculator")
st.caption("Select origin and destination by river + mile marker. "
           "Calculates route, locks, transit time, USDA tariff rate, and rail comparison.")

if calculate:
    try:
        tow_str = "15-barge" if "15" in tow_config else ("6-barge" if "6" in tow_config else "15-barge")
        result = calc.calculate_route_cost(
            origin_river=origin_river,
            origin_mile=origin_mile,
            dest_river=dest_river,
            dest_mile=dest_mile,
            cargo_tons=cargo_tons,
            tow_config=tow_str,
            speed_mph=speed_mph,
            rail_rate=rail_rate,
            markup_per_ton=markup,
        )

        # ============================================================
        # ROW 1: Key metrics
        # ============================================================
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Distance", f"{result.total_distance_miles:,.0f} mi")
        with col2:
            st.metric("Locks", f"{len(result.locks_encountered)}")
        with col3:
            st.metric("Transit Time", f"{result.total_time_days:.1f} days")
        with col4:
            st.metric("Barge $/ton", f"${result.total_cost_per_ton:.2f}")
        with col5:
            delta_color = "normal" if result.barge_savings_per_ton > 0 else "inverse"
            st.metric(
                "vs Rail Savings",
                f"${result.barge_savings_per_ton:.2f}/ton",
                delta=f"{result.barge_savings_pct:.1f}%",
                delta_color=delta_color,
            )

        # ============================================================
        # ROW 2: Route detail + Cost comparison
        # ============================================================
        st.markdown("---")
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("Route Detail")

            for i, seg in enumerate(result.segments):
                direction_icon = "⬇️" if seg["direction"] == "downstream" else "⬆️"
                st.markdown(
                    f"**Leg {i+1}: {seg['river']}** {direction_icon}\n"
                    f"- Mile {seg['from_mile']:.0f} → Mile {seg['to_mile']:.0f}\n"
                    f"- Distance: **{seg['distance']:.1f} miles**\n"
                    f"- Locks: **{seg['num_locks']}**"
                )

                if seg['locks']:
                    lock_data = []
                    for lock in seg['locks']:
                        chamber = "1200ft" if lock['length_ft'] >= 1200 else f"{lock['length_ft']:.0f}ft"
                        lockage = "Single" if lock['length_ft'] >= 1200 else "Double"
                        lock_data.append({
                            "Lock": lock['name'],
                            "Mile": f"{lock['mile']:.1f}",
                            "Chamber": chamber,
                            "Lockage": lockage,
                            "Est. Delay": f"{lock['delay_hrs']:.1f} hrs",
                        })
                    st.dataframe(
                        pd.DataFrame(lock_data),
                        use_container_width=True,
                        hide_index=True,
                    )

        with col_right:
            st.subheader("Barge vs Rail Comparison")

            # Comparison chart
            fig_compare = go.Figure()

            categories = ['Cost/Ton-Mile', 'Cost/Ton']
            barge_vals = [result.cost_per_ton_mile, result.total_cost_per_ton]
            rail_vals = [result.rail_cost_per_ton_mile, result.rail_cost_per_ton]

            fig_compare.add_trace(go.Bar(
                name='Barge',
                x=['$/Ton-Mile', '$/Ton'],
                y=barge_vals,
                marker_color='#2196F3',
                text=[f"${v:.4f}" if i == 0 else f"${v:.2f}" for i, v in enumerate(barge_vals)],
                textposition='outside',
            ))
            fig_compare.add_trace(go.Bar(
                name='Rail',
                x=['$/Ton-Mile', '$/Ton'],
                y=rail_vals,
                marker_color='#FF5722',
                text=[f"${v:.4f}" if i == 0 else f"${v:.2f}" for i, v in enumerate(rail_vals)],
                textposition='outside',
            ))

            fig_compare.update_layout(
                barmode='group',
                height=350,
                margin=dict(t=30, b=30),
                yaxis_title="USD",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_compare, use_container_width=True)

            # Savings callout
            if result.barge_savings_per_ton > 0:
                st.success(
                    f"**Barge saves ${result.barge_savings_per_ton:.2f}/ton** "
                    f"({result.barge_savings_pct:.1f}% cheaper than rail)\n\n"
                    f"On {cargo_tons:,} tons: **${result.barge_savings_per_ton * cargo_tons:,.0f} total savings**"
                )
            else:
                st.warning(
                    f"Rail is ${abs(result.barge_savings_per_ton):.2f}/ton cheaper for this route.\n\n"
                    f"Barge becomes competitive on longer hauls (500+ miles)."
                )

        # ============================================================
        # ROW 3: Transit time breakdown + Rate details
        # ============================================================
        st.markdown("---")
        col_time, col_rate = st.columns(2)

        with col_time:
            st.subheader("Transit Time Breakdown")

            # Pie chart of time
            fig_time = go.Figure(data=[go.Pie(
                labels=['Moving', 'Lock Delays'],
                values=[result.transit_time_hours, result.lock_delay_hours],
                marker_colors=['#4CAF50', '#FFC107'],
                hole=0.4,
                textinfo='label+value',
                texttemplate='%{label}<br>%{value:.1f} hrs',
            )])
            fig_time.update_layout(
                height=300,
                margin=dict(t=10, b=10),
                annotations=[dict(
                    text=f"{result.total_time_hours:.0f}h",
                    x=0.5, y=0.5, font_size=20, showarrow=False
                )],
            )
            st.plotly_chart(fig_time, use_container_width=True)

            st.markdown(
                f"| Metric | Value |\n"
                f"|--------|-------|\n"
                f"| Transit (moving) | {result.transit_time_hours:.1f} hours |\n"
                f"| Lock delays | {result.lock_delay_hours:.1f} hours |\n"
                f"| **Total** | **{result.total_time_hours:.1f} hours ({result.total_time_days:.1f} days)** |\n"
                f"| Avg speed | {speed_mph:.1f} mph |\n"
                f"| Locks (600ft / double) | {sum(1 for l in result.locks_encountered if l.is_600ft)} |\n"
                f"| Locks (1200ft / single) | {sum(1 for l in result.locks_encountered if not l.is_600ft)} |"
            )

        with col_rate:
            st.subheader("USDA Tariff Rate Detail")

            seg_names = []
            seg_rates = []
            for seg_id in result.usda_segments_used:
                seg_def = USDA_SEGMENT_DEFINITIONS.get(seg_id, {})
                seg_names.append(seg_def.get('name', f'Segment {seg_id}'))
                # Get rate for this segment
                col_name = f"segment_{seg_id}_rate"
                if calc.rate_data is not None and col_name in calc.rate_data.columns:
                    rate = calc.rate_data[col_name].tail(4).mean()
                    seg_rates.append(rate)
                else:
                    seg_rates.append(0)

            if seg_names:
                fig_rates = go.Figure(data=[go.Bar(
                    x=seg_names,
                    y=seg_rates,
                    marker_color='#2196F3',
                    text=[f"${r:.2f}" for r in seg_rates],
                    textposition='outside',
                )])
                fig_rates.update_layout(
                    height=300,
                    margin=dict(t=10, b=60),
                    yaxis_title="$/ton",
                    xaxis_tickangle=-30,
                )
                st.plotly_chart(fig_rates, use_container_width=True)

            st.markdown(
                f"| Component | Value |\n"
                f"|-----------|-------|\n"
                f"| USDA Base Rate (avg) | ${result.forecasted_rate_per_ton:.2f}/ton |\n"
                f"| + Markup | ${markup:.2f}/ton |\n"
                f"| **Total Rate** | **${result.rate_plus_markup:.2f}/ton** |\n"
                f"| Per ton-mile | ${result.cost_per_ton_mile:.4f} |\n"
                f"| Rate zones used | {len(result.usda_segments_used)} |"
            )

        # ============================================================
        # ROW 4: Operational costs
        # ============================================================
        st.markdown("---")
        st.subheader("Operational Cost Breakdown (Full Tow)")

        col_ops1, col_ops2 = st.columns(2)

        with col_ops1:
            fig_ops = go.Figure(data=[go.Pie(
                labels=['Fuel', 'Crew', 'Lock Fees'],
                values=[result.fuel_cost, result.crew_cost, result.lock_fees],
                marker_colors=['#F44336', '#2196F3', '#FFC107'],
                hole=0.4,
                textinfo='label+percent',
            )])
            fig_ops.update_layout(
                height=300,
                margin=dict(t=10, b=10),
                annotations=[dict(
                    text=f"${result.total_operational_cost:,.0f}",
                    x=0.5, y=0.5, font_size=16, showarrow=False
                )],
            )
            st.plotly_chart(fig_ops, use_container_width=True)

        with col_ops2:
            st.markdown(
                f"| Cost Category | Amount | Per Ton |\n"
                f"|---------------|--------|--------|\n"
                f"| Fuel ({calc.FUEL_GALLONS_PER_DAY:,} gal/day @ ${calc.FUEL_PRICE_PER_GALLON:.2f}) | ${result.fuel_cost:,.2f} | ${result.fuel_cost/cargo_tons:.2f} |\n"
                f"| Crew ({calc.CREW_SIZE} x ${calc.CREW_COST_PER_DAY:,}/day) | ${result.crew_cost:,.2f} | ${result.crew_cost/cargo_tons:.2f} |\n"
                f"| Lock Fees ({len(result.locks_encountered)} x ${calc.LOCK_FEE_PER_PASSAGE}) | ${result.lock_fees:,.2f} | ${result.lock_fees/cargo_tons:.4f} |\n"
                f"| **TOTAL** | **${result.total_operational_cost:,.2f}** | **${result.cost_per_ton_operational:.2f}** |"
            )

            st.markdown(
                f"\n**Tow:** {tow_config} | "
                f"**Cargo:** {cargo_tons:,} tons | "
                f"**Distance:** {result.total_distance_miles:,.0f} mi"
            )

        # ============================================================
        # ROW 5: Quick reference examples
        # ============================================================
        st.markdown("---")
        st.subheader("Quick Cost Examples")

        tonnages = [1500, 5000, 10000, 22500, 50000, 100000]
        examples = []
        for tons in tonnages:
            barge_cost = result.rate_plus_markup * tons
            rail_cost = result.rail_cost_per_ton * tons
            savings = rail_cost - barge_cost
            examples.append({
                "Cargo (tons)": f"{tons:,}",
                "Barge Cost": f"${barge_cost:,.0f}",
                "Rail Cost": f"${rail_cost:,.0f}",
                "Savings": f"${savings:,.0f}" if savings > 0 else f"-${abs(savings):,.0f}",
                "Barge Advantage": f"{savings/rail_cost*100:.1f}%" if rail_cost > 0 else "N/A",
            })

        st.dataframe(pd.DataFrame(examples), use_container_width=True, hide_index=True)

        # ============================================================
        # ROW 6: Rate forecast
        # ============================================================
        st.markdown("---")
        st.subheader("Rate History & Forecast")

        if calc.rate_data is not None and len(calc.rate_data) > 0:
            # Show last 52 weeks of rates for relevant segments
            recent_rates = calc.rate_data.tail(52).copy()

            fig_hist = go.Figure()
            colors = ['#2196F3', '#FF5722', '#4CAF50', '#FFC107', '#9C27B0', '#00BCD4', '#795548']

            for i, seg_id in enumerate(result.usda_segments_used):
                col_name = f"segment_{seg_id}_rate"
                seg_name = USDA_SEGMENT_DEFINITIONS.get(seg_id, {}).get('name', f'Segment {seg_id}')
                if col_name in recent_rates.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=recent_rates['date'],
                        y=recent_rates[col_name],
                        name=seg_name,
                        line=dict(color=colors[i % len(colors)]),
                    ))

            fig_hist.update_layout(
                height=350,
                margin=dict(t=30, b=30),
                yaxis_title="Rate ($/ton)",
                xaxis_title="Date",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    except ValueError as e:
        st.error(f"Route Error: {e}")
    except Exception as e:
        st.error(f"Calculation Error: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    # Landing page
    st.info("Configure origin and destination in the sidebar, then click **Calculate Route Cost**.")

    st.markdown("### How It Works")
    st.markdown("""
1. **Select Origin** - Pick a river and mile marker (e.g., Illinois River, Mile 231)
2. **Select Destination** - Pick a river and mile marker (e.g., Mississippi River, Mile 100)
3. **The tool calculates:**
   - Route through river network (via junctions if crossing rivers)
   - Every lock along the route and its delay time
   - Total transit time at standard barge/tug speeds
   - Forecasted barge rate using USDA tariff zones
   - Cost per ton and cost per ton-mile
   - Rail comparison

### Pricing Method (USDA Tariff)
- Take USDA barge rate zone tariff ($/ton)
- Add markup ($2/ton default)
- Convert to ton-mile: rate / distance
- Compare to rail at $0.04-$0.08/ton-mile

### Example
- $0.02/ton-mile x 500 miles = **$10/ton barge**
- $0.04/ton-mile x 500 miles = **$20/ton rail**
- Barge saves **$10/ton (50%)**
""")

    # Show loaded data status
    st.markdown("### System Status")
    for key, value in load_status.items():
        icon = "✅" if "FAILED" not in str(value) else "❌"
        st.markdown(f"- {icon} **{key}:** {value}")

    # Show available rivers
    st.markdown("### Available Rivers & Locks")
    for river in major_rivers:
        if river in calc.rivers_available:
            locks = calc.get_locks_on_river(river)
            mile_range = calc.get_mile_range(river)
            st.markdown(
                f"- **{river}**: Miles {mile_range[0]:.0f}-{mile_range[1]:.0f}, "
                f"{len(locks)} locks"
            )
