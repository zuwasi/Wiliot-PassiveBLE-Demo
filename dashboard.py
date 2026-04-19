"""
PassiveBLE x Wiliot — Interactive Dashboard

Run:  streamlit run dashboard.py
"""

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import passiveble as pb

# === Page Config ===
st.set_page_config(
    page_title="PassiveBLE x Wiliot Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Dark theme CSS ===
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e, #0d1117);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 13px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    .pass-badge { color: #3fb950; }
    .fail-badge { color: #f85149; }
</style>
""", unsafe_allow_html=True)

# Plotly dark template
PLOT_TEMPLATE = "plotly_dark"
COLORS = {"blue": "#58a6ff", "green": "#3fb950", "red": "#f85149",
           "orange": "#d29922", "purple": "#bc8cff", "cyan": "#39d2c0"}


# =============================================================
# SIDEBAR
# =============================================================
with st.sidebar:
    st.markdown("## 📡 PassiveBLE x Wiliot")
    st.markdown("---")
    st.markdown("### Dock-Door Configuration")
    num_tags = st.select_slider("Tags on pallet", [4, 8, 16, 24, 32, 48, 64], value=32)
    speed = st.slider("Forklift speed (m/s)", 0.3, 3.0, 1.0, 0.1)
    aperture = st.slider("Door width (m)", 1.0, 4.0, 2.0, 0.5)
    phy = st.radio("PHY Mode", ["LE2M", "LE1M"], horizontal=True)
    variant = st.radio("Tag Variant", ["ASIC", "COTS"], horizontal=True)

    st.markdown("---")
    st.markdown("### RF Configuration")
    tx_eirp = st.slider("TX EIRP (dBm)", 0, 20, 20)
    g_ant = st.slider("Antenna gain (dBi)", 0, 6, 2)

    st.markdown("---")
    st.markdown(
        "<small>Based on: Dong et al., MobiCom 2025<br>"
        "<a href='https://arxiv.org/abs/2503.11490'>arXiv 2503.11490</a></small>",
        unsafe_allow_html=True,
    )

# =============================================================
# CORE SIMULATION
# =============================================================
sim = pb.dock_door_simulation(num_tags, speed, aperture, phy, variant)
harvest = pb.energy_harvest_feasibility(tx_eirp, g_ant, g_ant, aperture / 2, pb.F_BLE, variant)

# =============================================================
# HEADER
# =============================================================
st.markdown("# Dock-Door Fast-Read Simulator")
st.markdown(f"**{num_tags} tags** on pallet at **{speed} m/s** through **{aperture} m** door "
            f"({phy} PHY, {variant})")

# =============================================================
# TOP METRICS ROW
# =============================================================
col1, col2, col3, col4 = st.columns(4)

read_color = "#3fb950" if sim.read_percentage > 95 else "#d29922" if sim.read_percentage > 80 else "#f85149"
with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{read_color}">{sim.read_percentage:.1f}%</div>
        <div class="metric-label">Read Rate</div>
        <div style="color:#8b949e; font-size:12px; margin-top:4px;">{sim.expected_tags_read:.0f} of {num_tags} tags</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:#39d2c0">{sim.dwell_time_ms:.0f}</div>
        <div class="metric-label">Dwell Time (ms)</div>
        <div style="color:#8b949e; font-size:12px; margin-top:4px;">time in aperture</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:#bc8cff">{sim.connection_rate*100:.1f}%</div>
        <div class="metric-label">Connection Rate</div>
        <div style="color:#8b949e; font-size:12px; margin-top:4px;">BLE establishment</div>
    </div>""", unsafe_allow_html=True)

pwr_color = "#3fb950" if harvest.feasible else "#f85149"
pwr_text = "Self-Powered" if harvest.feasible else "Needs Battery"
with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{pwr_color}; font-size:28px;">{pwr_text}</div>
        <div class="metric-label">Power Status</div>
        <div style="color:#8b949e; font-size:12px; margin-top:4px;">{harvest.harvested_power_uw:.1f} uW harvested</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================
# TAB LAYOUT
# =============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Dock-Door Analysis", "RF & Wake-Up", "Throughput & BER",
    "3D Design Space", "Validation"
])

# === TAB 1: DOCK DOOR ===
with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        # Read rate vs tags at different speeds
        speeds_plot = [0.5, 1.0, 1.5, 2.0, 2.5]
        tag_range = [4, 8, 16, 24, 32, 48, 64]
        fig = go.Figure()
        for spd in speeds_plot:
            reads = [pb.dock_door_simulation(n, spd, aperture, phy, variant).read_percentage
                     for n in tag_range]
            fig.add_trace(go.Scatter(x=tag_range, y=reads, mode="lines+markers",
                                     name=f"{spd} m/s", line=dict(width=2.5)))
        fig.add_hline(y=95, line_dash="dash", line_color="#3fb950", opacity=0.5,
                      annotation_text="95% target")
        fig.update_layout(title="Read Rate vs Number of Tags",
                          xaxis_title="Tags on Pallet", yaxis_title="Read Success (%)",
                          yaxis_range=[0, 105], template=PLOT_TEMPLATE, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Read rate vs speed at different tag counts
        speed_range = np.arange(0.3, 3.1, 0.1)
        tag_counts_plot = [8, 16, 32, 48, 64]
        fig2 = go.Figure()
        for nt in tag_counts_plot:
            reads = [pb.dock_door_simulation(nt, s, aperture, phy, variant).read_percentage
                     for s in speed_range]
            fig2.add_trace(go.Scatter(x=speed_range, y=reads, mode="lines",
                                      name=f"{nt} tags", line=dict(width=2.5)))
        fig2.add_hline(y=95, line_dash="dash", line_color="#3fb950", opacity=0.5)
        fig2.update_layout(title="Read Rate vs Forklift Speed",
                           xaxis_title="Speed (m/s)", yaxis_title="Read Success (%)",
                           yaxis_range=[0, 105], template=PLOT_TEMPLATE, height=400)
        st.plotly_chart(fig2, use_container_width=True)

    # Detailed simulation breakdown
    st.markdown("### Simulation Breakdown")
    breakdown_cols = st.columns(5)
    labels = ["Read/Tag (ms)", "Max Reads", "Avg Distance (m)", "Tag Power (uW)", "PHY Mode"]
    values = [f"{sim.read_time_per_tag_ms:.2f}", str(sim.max_reads_in_dwell),
              f"{sim.avg_distance_m:.1f}", f"{sim.tag_power_uw}", sim.phy]
    for col, label, val in zip(breakdown_cols, labels, values):
        col.metric(label, val)


# === TAB 2: RF & WAKE-UP ===
with tab2:
    col_left, col_right = st.columns(2)

    with col_left:
        # Received power vs distance
        distances = np.arange(0.5, 20.5, 0.5)
        fig_rx = go.Figure()
        for ptx in [0, 5, 10, 15, 20]:
            rx = [pb.received_power(ptx, g_ant, g_ant, d) for d in distances]
            fig_rx.add_trace(go.Scatter(x=distances, y=rx, mode="lines",
                                        name=f"{ptx} dBm", line=dict(width=2)))
        fig_rx.add_hline(y=-30, line_dash="dash", line_color="#f85149",
                         annotation_text="Wake-up threshold: -30 dBm")
        fig_rx.update_layout(title="Received Power vs Distance",
                             xaxis_title="Distance (m)", yaxis_title="Received Power (dBm)",
                             yaxis_range=[-80, 10], template=PLOT_TEMPLATE, height=400)
        st.plotly_chart(fig_rx, use_container_width=True)

    with col_right:
        # Wake-up probability
        power_range = np.arange(-40, -19.5, 0.5)
        model_y = [pb.wakeup_probability(p) for p in power_range]
        paper_x = [d[0] for d in pb.WAKEUP_DATA]
        paper_y = [d[1] for d in pb.WAKEUP_DATA]

        fig_wu = go.Figure()
        fig_wu.add_trace(go.Scatter(x=power_range, y=model_y, mode="lines",
                                     name="Model", line=dict(color=COLORS["blue"], width=2.5)))
        fig_wu.add_trace(go.Scatter(x=paper_x, y=paper_y, mode="markers",
                                     name="Paper data", marker=dict(color=COLORS["red"], size=8)))
        fig_wu.add_vline(x=-30, line_dash="dash", line_color="#8b949e", opacity=0.5)
        fig_wu.update_layout(title="Wake-Up Probability vs Received Power",
                             xaxis_title="Received Power (dBm)", yaxis_title="Wake-Up Rate",
                             template=PLOT_TEMPLATE, height=400)
        st.plotly_chart(fig_wu, use_container_width=True)

    # Energy harvesting
    st.markdown("### Energy Harvesting Feasibility")
    harv_distances = np.arange(0.5, 5.25, 0.25)
    harv_powers = [pb.energy_harvest_feasibility(tx_eirp, g_ant, g_ant, d, pb.F_BLE, variant).harvested_power_uw
                   for d in harv_distances]

    fig_eh = go.Figure()
    fig_eh.add_trace(go.Scatter(x=harv_distances, y=harv_powers, mode="lines",
                                 fill="tozeroy", fillcolor="rgba(63,185,80,0.1)",
                                 line=dict(color=COLORS["green"], width=2.5), name="Harvested"))
    tag_pwr = pb.power_budget(variant)
    fig_eh.add_hline(y=tag_pwr, line_dash="dash", line_color=COLORS["orange"],
                     annotation_text=f"{variant}: {tag_pwr} uW")
    if variant == "ASIC":
        fig_eh.add_hline(y=491, line_dash="dash", line_color=COLORS["red"],
                         annotation_text="COTS: 491 uW")
    fig_eh.update_layout(title=f"Harvested Power vs Distance (EIRP={tx_eirp} dBm)",
                         xaxis_title="Distance (m)", yaxis_title="Power (uW)",
                         yaxis_range=[0, max(harv_powers) * 1.2],
                         template=PLOT_TEMPLATE, height=350)
    st.plotly_chart(fig_eh, use_container_width=True)


# === TAB 3: THROUGHPUT & BER ===
with tab3:
    col_left, col_right = st.columns(2)

    with col_left:
        distances_tp = np.arange(0.5, 18.5, 0.5)
        fig_tp = go.Figure()
        for mode, dash in [("LE2M", "solid"), ("LE1M", "solid")]:
            color = COLORS["blue"] if mode == "LE2M" else COLORS["red"]
            los = [pb.goodput_los(d, mode) for d in distances_tp]
            nlos = [pb.goodput_nlos(d, mode) for d in distances_tp]
            fig_tp.add_trace(go.Scatter(x=distances_tp, y=los, mode="lines",
                                         name=f"{mode} LoS", line=dict(color=color, width=2.5)))
            fig_tp.add_trace(go.Scatter(x=distances_tp, y=nlos, mode="lines",
                                         name=f"{mode} NLoS", line=dict(color=color, width=2, dash="dash")))
        fig_tp.update_layout(title="Goodput vs Distance (LoS & NLoS)",
                             xaxis_title="Tag-to-RX Distance (m)", yaxis_title="Goodput (kbps)",
                             yaxis_range=[0, 1050], template=PLOT_TEMPLATE, height=420)
        st.plotly_chart(fig_tp, use_container_width=True)

    with col_right:
        # BER
        ber_2m = [pb.ber_model(d, "LE2M") for d in distances_tp]
        ber_1m = [pb.ber_model(d, "LE1M") for d in distances_tp]
        fig_ber = go.Figure()
        fig_ber.add_trace(go.Scatter(x=distances_tp, y=ber_2m, mode="lines",
                                      name="LE 2M", line=dict(color=COLORS["blue"], width=2.5)))
        fig_ber.add_trace(go.Scatter(x=distances_tp, y=ber_1m, mode="lines",
                                      name="LE 1M", line=dict(color=COLORS["red"], width=2.5)))
        fig_ber.update_layout(title="Bit Error Rate vs Distance",
                              xaxis_title="Distance (m)", yaxis_title="BER",
                              yaxis_type="log", template=PLOT_TEMPLATE, height=420)
        st.plotly_chart(fig_ber, use_container_width=True)

    # Connection performance
    conn_d = np.arange(0.5, 17.5, 0.5)
    estab = [pb.connection_success_rate(d) for d in conn_d]
    maint = [pb.connection_maintenance_rate(d) for d in conn_d]
    fig_conn = go.Figure()
    fig_conn.add_trace(go.Scatter(x=conn_d, y=estab, mode="lines", fill="tozeroy",
                                   fillcolor="rgba(63,185,80,0.08)",
                                   name="Establishment", line=dict(color=COLORS["green"], width=2.5)))
    fig_conn.add_trace(go.Scatter(x=conn_d, y=maint, mode="lines", fill="tozeroy",
                                   fillcolor="rgba(210,153,34,0.08)",
                                   name="Maintenance", line=dict(color=COLORS["orange"], width=2.5)))
    fig_conn.add_hline(y=0.999, line_dash="dash", line_color=COLORS["red"],
                       annotation_text="99.9% paper claim")
    fig_conn.update_layout(title="BLE Connection Success Rate vs Distance",
                           xaxis_title="Distance (m)", yaxis_title="Success Rate",
                           yaxis_range=[0.5, 1.01], template=PLOT_TEMPLATE, height=350)
    st.plotly_chart(fig_conn, use_container_width=True)


# === TAB 4: 3D DESIGN SPACE ===
with tab4:
    st.markdown("### Read Rate Across Full Design Space")
    st.markdown("Explore how tag count and forklift speed jointly affect read performance.")

    tag_3d = np.arange(4, 68, 4)
    speed_3d = np.arange(0.3, 3.1, 0.2)
    T, S = np.meshgrid(tag_3d, speed_3d)
    R = np.zeros_like(T, dtype=float)
    for i in range(T.shape[0]):
        for j in range(T.shape[1]):
            r = pb.dock_door_simulation(int(T[i, j]), float(S[i, j]), aperture, phy, variant)
            R[i, j] = r.read_percentage

    fig_3d = go.Figure(data=[go.Surface(
        x=tag_3d, y=speed_3d, z=R,
        colorscale=[[0, "#f85149"], [0.5, "#d29922"], [0.8, "#3fb950"], [1, "#3fb950"]],
        colorbar=dict(title="Read %"),
        contours=dict(
            z=dict(show=True, usecolormap=True, highlightcolor="white",
                   project_z=True, start=80, end=95, size=15)
        ),
    )])
    fig_3d.update_layout(
        scene=dict(
            xaxis_title="Tags",
            yaxis_title="Speed (m/s)",
            zaxis_title="Read %",
            zaxis_range=[0, 100],
        ),
        title=f"Dock-Door Read Rate Design Space ({aperture}m door, {phy}, {variant})",
        template=PLOT_TEMPLATE, height=600,
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    # Multi-tag scaling
    st.markdown("### Multi-Tag Throughput Scaling")
    tag_counts_mt = [1, 2, 4, 8, 16, 32]
    test_dists = [2, 5, 10]
    fig_mt = go.Figure()
    for dist in test_dists:
        gps = [pb.multi_tag_goodput(dist, n, phy) for n in tag_counts_mt]
        fig_mt.add_trace(go.Scatter(x=tag_counts_mt, y=gps, mode="lines+markers",
                                     name=f"{dist} m", line=dict(width=2.5)))
    fig_mt.update_layout(title=f"Per-Tag Goodput vs Number of Tags ({phy})",
                         xaxis_title="Number of Tags", yaxis_title="Per-Tag Goodput (kbps)",
                         yaxis_type="log", template=PLOT_TEMPLATE, height=380)
    st.plotly_chart(fig_mt, use_container_width=True)


# === TAB 5: VALIDATION ===
with tab5:
    st.markdown("### Validation Against Paper Results")

    checks = [
        ("Max Goodput LE 2M", "974 kbps", 974.0, pb.goodput_los(0.5, "LE2M"), 0.05),
        ("Max Goodput LE 1M", "532 kbps", 532.0, pb.goodput_los(0.5, "LE1M"), 0.05),
        ("Connection Success", ">99.9%", 0.999, pb.connection_success_rate(0.5), 0.01),
        ("Wake-Up @ -30 dBm", "91%", 0.91, pb.wakeup_probability(-30), 0.10),
        ("ASIC Power", "9.9 uW", 9.9, pb.power_budget("ASIC"), 0.01),
        ("COTS Power", "491 uW", 491.0, pb.power_budget("COTS"), 0.01),
    ]

    all_pass = True
    rows = []
    for name, paper_str, paper_val, model_val, tol in checks:
        rel_err = abs(model_val - paper_val) / paper_val if paper_val != 0 else abs(model_val - paper_val)
        passed = rel_err <= tol
        if not passed:
            all_pass = False
        rows.append({
            "Metric": name,
            "Paper": paper_str,
            "Model": f"{model_val:.3f}",
            "Error": f"{rel_err*100:.1f}%",
            "Status": "PASS" if passed else "FAIL",
        })

    for row in rows:
        cols = st.columns([3, 2, 2, 1, 1])
        cols[0].write(row["Metric"])
        cols[1].write(row["Paper"])
        cols[2].write(row["Model"])
        cols[3].write(row["Error"])
        if row["Status"] == "PASS":
            cols[4].markdown(f'<span class="pass-badge">PASS</span>', unsafe_allow_html=True)
        else:
            cols[4].markdown(f'<span class="fail-badge">FAIL</span>', unsafe_allow_html=True)

    st.markdown("---")
    if all_pass:
        st.success("All 6 validation checks passed")
    else:
        st.error("Validation failures detected")

    # Physics checks
    st.markdown("### Physics Consistency Checks")
    physics = [
        ("Path loss increases with distance", pb.friis_path_loss(1) < pb.friis_path_loss(10)),
        ("Goodput decreases with distance", pb.goodput_los(1) > pb.goodput_los(10)),
        ("NLoS goodput < LoS", pb.goodput_nlos(5) < pb.goodput_los(5)),
        ("BER increases with distance", pb.ber_model(1) < pb.ber_model(10)),
        ("Connection rate decreases with distance",
         pb.connection_success_rate(1) > pb.connection_success_rate(10)),
        ("Maintenance < Establishment",
         pb.connection_maintenance_rate(5) < pb.connection_success_rate(5)),
        ("Per-tag goodput decreases with tags",
         pb.multi_tag_goodput(2, 1) > pb.multi_tag_goodput(2, 32)),
        ("Energy harvesting feasible at 0.5m",
         pb.energy_harvest_feasibility(20, 2, 2, 0.5).feasible),
    ]

    all_phys = True
    for name, passed in physics:
        if passed:
            st.markdown(f"**PASS** &nbsp; {name}")
        else:
            st.markdown(f"**FAIL** &nbsp; {name}")
            all_phys = False

    if all_phys:
        st.success("All 8 physics checks passed")

    # Prior systems comparison
    st.markdown("### Prior Systems Comparison")
    systems = list(pb.PRIOR_SYSTEMS.keys())
    throughputs = [v["throughput_kbps"] for v in pb.PRIOR_SYSTEMS.values()]
    compat = [v["compatible"] for v in pb.PRIOR_SYSTEMS.values()]
    bar_colors = ["#8b949e", "#8b949e", "#8b949e", COLORS["blue"], COLORS["green"]]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(x=systems, y=throughputs, marker_color=bar_colors,
                              text=[f"{t:.1f}" for t in throughputs], textposition="outside"))
    fig_cmp.update_layout(title="Throughput Comparison (kbps)",
                          yaxis_type="log", yaxis_title="Goodput (kbps)",
                          template=PLOT_TEMPLATE, height=380)
    st.plotly_chart(fig_cmp, use_container_width=True)
