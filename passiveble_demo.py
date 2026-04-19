"""
PassiveBLE × Wiliot: Battery-Free BLE Backscatter Simulation (Python)

Reproducing and extending results from Dong et al., MobiCom 2025 (arXiv 2503.11490).
Generates all figures to exports/ and prints validation report.

Usage:
    python passiveble_demo.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

import passiveble as pb

# === Setup ===
np.random.seed(42)
EXPORTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
os.makedirs(EXPORTS, exist_ok=True)

# Plot style
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.alpha": 0.6,
    "legend.facecolor": "#161b22",
    "legend.edgecolor": "#30363d",
    "legend.labelcolor": "#c9d1d9",
    "font.family": "sans-serif",
    "font.size": 11,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": "#0d1117",
})

BLUE = "#58a6ff"
GREEN = "#3fb950"
RED = "#f85149"
ORANGE = "#d29922"
PURPLE = "#bc8cff"
CYAN = "#39d2c0"


def save(fig, name):
    fig.savefig(os.path.join(EXPORTS, name))
    plt.close(fig)
    print(f"  [OK] Saved {name}")


# ================================================================
# FIGURE 1: Free-Space Path Loss
# ================================================================
def fig_path_loss():
    distances = np.arange(0.5, 20.5, 0.5)
    losses = [pb.friis_path_loss(d) for d in distances]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(distances, losses, color=BLUE, linewidth=2.5)
    ax.axvline(17, color=RED, linestyle="--", alpha=0.7, label="Paper max: 17 m")
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Path Loss (dB)")
    ax.set_title("Free-Space Path Loss at 2.44 GHz", fontweight="bold", fontsize=14)
    ax.legend()
    ax.grid(True)
    save(fig, "01_path_loss.png")


# ================================================================
# FIGURE 2: Received Power vs Distance
# ================================================================
def fig_received_power():
    distances = np.arange(0.5, 20.5, 0.5)
    tx_powers = [0, 5, 10, 15, 20]
    colors = [BLUE, CYAN, GREEN, ORANGE, RED]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for ptx, c in zip(tx_powers, colors):
        rx = [pb.received_power(ptx, 2, 2, d) for d in distances]
        ax.plot(distances, rx, color=c, linewidth=2, label=f"{ptx} dBm EIRP")
    ax.axhline(-30, color=RED, linestyle="--", alpha=0.7, linewidth=1.5)
    ax.text(14, -28, "Wake-up threshold: -30 dBm", color=RED, fontsize=10)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Received Power (dBm)")
    ax.set_title("Received Power vs Distance", fontweight="bold", fontsize=14)
    ax.set_ylim(-80, 10)
    ax.legend(loc="upper right")
    ax.grid(True)
    save(fig, "02_received_power.png")


# ================================================================
# FIGURE 3: Wake-Up Probability
# ================================================================
def fig_wakeup():
    power_range = np.arange(-40, -19.5, 0.5)
    model = [pb.wakeup_probability(p) for p in power_range]
    data_x = [d[0] for d in pb.WAKEUP_DATA]
    data_y = [d[1] for d in pb.WAKEUP_DATA]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(power_range, model, color=BLUE, linewidth=2.5, label="Logistic model")
    ax.scatter(data_x, data_y, color=RED, s=60, zorder=5, label="Paper data")
    ax.axvline(-30, color="#8b949e", linestyle="--", alpha=0.5)
    ax.text(-29.5, 0.5, "-30 dBm\n91%", color="#8b949e", fontsize=10)
    ax.set_xlabel("Received Power (dBm)")
    ax.set_ylabel("Wake-Up Rate")
    ax.set_title("Tag Wake-Up Probability vs Received Power", fontweight="bold", fontsize=14)
    ax.legend()
    ax.grid(True)
    save(fig, "03_wakeup_probability.png")


# ================================================================
# FIGURE 4: Wake-Up Distance
# ================================================================
def fig_wakeup_distance():
    data_x = [d[0] for d in pb.WAKEUP_DISTANCE_DATA]
    data_y = [d[1] for d in pb.WAKEUP_DISTANCE_DATA]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(data_x, data_y, color=GREEN, linewidth=2.5, marker="o", markersize=5)
    ax.fill_between(data_x, data_y, alpha=0.12, color=GREEN)
    ax.axhline(0.80, color=RED, linestyle="--", alpha=0.6)
    ax.text(4.2, 0.82, "80% threshold", color=RED, fontsize=9)
    ax.axhline(0.95, color=BLUE, linestyle="--", alpha=0.6)
    ax.text(4.2, 0.96, "95% threshold", color=BLUE, fontsize=9)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Success Rate")
    ax.set_title("Wake-Up Success Rate vs Distance (EIRP = 20 dBm)", fontweight="bold", fontsize=14)
    ax.set_xlim(0, 5.5)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True)
    save(fig, "04_wakeup_distance.png")


# ================================================================
# FIGURE 5: Goodput LoS vs NLoS
# ================================================================
def fig_goodput():
    distances = np.arange(0.5, 18.5, 0.5)
    g_le2m_los = [pb.goodput_los(d, "LE2M") for d in distances]
    g_le2m_nlos = [pb.goodput_nlos(d, "LE2M") for d in distances]
    g_le1m_los = [pb.goodput_los(d, "LE1M") for d in distances]
    g_le1m_nlos = [pb.goodput_nlos(d, "LE1M") for d in distances]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(distances, g_le2m_los, color=BLUE, linewidth=2.5, label="LE 2M LoS")
    ax.plot(distances, g_le2m_nlos, color=BLUE, linewidth=2, linestyle="--", label="LE 2M NLoS")
    ax.plot(distances, g_le1m_los, color=RED, linewidth=2.5, label="LE 1M LoS")
    ax.plot(distances, g_le1m_nlos, color=RED, linewidth=2, linestyle="--", label="LE 1M NLoS")
    ax.axhline(974, color=BLUE, linestyle=":", alpha=0.4)
    ax.text(14, 990, "974 kbps peak", color=BLUE, fontsize=9)
    ax.axhline(532, color=RED, linestyle=":", alpha=0.4)
    ax.text(14, 548, "532 kbps peak", color=RED, fontsize=9)
    ax.set_xlabel("Tag-to-RX Distance (m)")
    ax.set_ylabel("Goodput (kbps)")
    ax.set_title("Goodput: LoS vs NLoS Comparison", fontweight="bold", fontsize=14)
    ax.set_ylim(0, 1050)
    ax.legend(loc="upper right")
    ax.grid(True)
    save(fig, "05_goodput_comparison.png")


# ================================================================
# FIGURE 6: BER vs Distance
# ================================================================
def fig_ber():
    distances = np.arange(0.5, 18.5, 0.5)
    ber_2m = [pb.ber_model(d, "LE2M") for d in distances]
    ber_1m = [pb.ber_model(d, "LE1M") for d in distances]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.semilogy(distances, ber_2m, color=BLUE, linewidth=2.5, label="LE 2M PHY")
    ax.semilogy(distances, ber_1m, color=RED, linewidth=2.5, label="LE 1M PHY")
    ax.set_xlabel("Tag-to-RX Distance (m)")
    ax.set_ylabel("Bit Error Rate")
    ax.set_title("Bit Error Rate vs Distance", fontweight="bold", fontsize=14)
    ax.legend()
    ax.grid(True, which="both", alpha=0.4)
    save(fig, "06_ber.png")


# ================================================================
# FIGURE 7: Connection Performance
# ================================================================
def fig_connection():
    distances = np.arange(0.5, 17.5, 0.5)
    estab = [pb.connection_success_rate(d) for d in distances]
    maint = [pb.connection_maintenance_rate(d) for d in distances]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(distances, estab, color=GREEN, linewidth=2.5, label="Establishment")
    ax.fill_between(distances, estab, alpha=0.08, color=GREEN)
    ax.plot(distances, maint, color=ORANGE, linewidth=2.5, label="Maintenance")
    ax.fill_between(distances, maint, alpha=0.08, color=ORANGE)
    ax.axhline(0.999, color=RED, linestyle="--", alpha=0.6)
    ax.text(12, 0.996, "99.9% paper claim", color=RED, fontsize=9)
    ax.set_xlabel("Tag-to-RX Distance (m)")
    ax.set_ylabel("Success Rate")
    ax.set_title("BLE Connection Success Rate vs Distance", fontweight="bold", fontsize=14)
    ax.set_ylim(0.5, 1.01)
    ax.legend()
    ax.grid(True)
    save(fig, "07_connection_performance.png")


# ================================================================
# FIGURE 8: Multi-Tag Scheduling
# ================================================================
def fig_multi_tag():
    tag_counts = [1, 2, 4, 8, 16, 32]
    test_distances = [2, 5, 10]
    colors = [BLUE, ORANGE, RED]

    fig, ax = plt.subplots(figsize=(9, 5))
    for dist, c in zip(test_distances, colors):
        goodputs = [pb.multi_tag_goodput(dist, n, "LE2M") for n in tag_counts]
        ax.semilogy(tag_counts, goodputs, color=c, linewidth=2.5,
                    marker="o", markersize=6, label=f"{dist} m")
    ax.set_xlabel("Number of Tags")
    ax.set_ylabel("Per-Tag Goodput (kbps)")
    ax.set_title("Per-Tag Goodput vs Number of Tags (LE 2M)", fontweight="bold", fontsize=14)
    ax.legend()
    ax.grid(True, which="both", alpha=0.4)
    save(fig, "08_multi_tag.png")


# ================================================================
# FIGURE 9: Energy Harvesting
# ================================================================
def fig_energy_harvest():
    distances = np.arange(0.5, 5.25, 0.25)
    harvested = [pb.energy_harvest_feasibility(20, 2, 2, d).harvested_power_uw for d in distances]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(distances, harvested, color=GREEN, linewidth=2.5)
    ax.fill_between(distances, harvested, alpha=0.12, color=GREEN)
    ax.axhline(491, color=RED, linestyle="--", linewidth=1.5)
    ax.text(4, 510, "COTS: 491 µW", color=RED, fontsize=10)
    ax.axhline(9.9, color=ORANGE, linestyle="--", linewidth=1.5)
    ax.text(4, 30, "ASIC: 9.9 µW", color=ORANGE, fontsize=10)
    ax.set_xlabel("Distance from Excitation Source (m)")
    ax.set_ylabel("Power (µW)")
    ax.set_title("Energy Harvesting Feasibility (EIRP = 20 dBm)", fontweight="bold", fontsize=14)
    ax.set_ylim(0, 2000)
    ax.grid(True)
    save(fig, "09_energy_harvesting.png")


# ================================================================
# FIGURE 10: ASIC Power Breakdown
# ================================================================
def fig_power_breakdown():
    bd = pb.power_breakdown("ASIC")
    labels = ["Static\n0.9 µW", "Dynamic\n9.9 µW", "Sync Amp\n162.4 µW", "Sync Comp\n27.9 µW"]
    values = [bd["baseband_static"], bd["baseband_dynamic"],
              bd["sync_amplifier"], bd["sync_comparator"]]
    colors_bar = [BLUE, CYAN, ORANGE, PURPLE]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors_bar, width=0.6, edgecolor="#30363d")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                f"{val:.1f}", ha="center", va="bottom", color="#c9d1d9", fontweight="bold")
    ax.set_ylabel("Power (µW)")
    ax.set_title("PassiveBLE ASIC Power Breakdown", fontweight="bold", fontsize=14)
    ax.grid(True, axis="y")
    save(fig, "10_power_breakdown.png")


# ================================================================
# FIGURE 11: Dock-Door Read Rate
# ================================================================
def fig_dock_door():
    speeds = [0.5, 1.0, 1.5, 2.0]
    tag_range = [4, 8, 16, 24, 32, 48, 64]
    colors = [BLUE, GREEN, ORANGE, RED]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for spd, c in zip(speeds, colors):
        read_pcts = [pb.dock_door_simulation(n, spd, 2.0, "LE2M", "ASIC").read_percentage
                     for n in tag_range]
        ax.plot(tag_range, read_pcts, color=c, linewidth=2.5,
                marker="o", markersize=6, label=f"{spd} m/s")
    ax.axhline(95, color=GREEN, linestyle="--", alpha=0.5)
    ax.text(58, 96, "95% target", color=GREEN, fontsize=9)
    ax.set_xlabel("Number of Tags on Pallet")
    ax.set_ylabel("Read Success (%)")
    ax.set_title("Dock-Door Tag Read Rate vs Number of Tags", fontweight="bold", fontsize=14)
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True)
    save(fig, "11_dock_door_read_rate.png")


# ================================================================
# FIGURE 12: 3D Design Space
# ================================================================
def fig_3d_surface():
    tag_range = np.arange(4, 68, 4)
    speed_range = np.arange(0.3, 3.3, 0.3)
    T, S = np.meshgrid(tag_range, speed_range)
    R = np.zeros_like(T, dtype=float)

    for i in range(T.shape[0]):
        for j in range(T.shape[1]):
            sim = pb.dock_door_simulation(int(T[i, j]), S[i, j], 2.0, "LE2M", "ASIC")
            R[i, j] = sim.read_percentage

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0d1117")
    fig.patch.set_facecolor("#0d1117")

    cmap = LinearSegmentedColormap.from_list("custom",
        [(0, "#f85149"), (0.5, "#d29922"), (0.8, "#3fb950"), (1, "#3fb950")])
    surf = ax.plot_surface(T, S, R, cmap=cmap, alpha=0.85, edgecolor="#30363d", linewidth=0.3)
    ax.set_xlabel("Tags", color="#c9d1d9", labelpad=10)
    ax.set_ylabel("Speed (m/s)", color="#c9d1d9", labelpad=10)
    ax.set_zlabel("Read %", color="#c9d1d9", labelpad=10)
    ax.set_title("Dock-Door Read Rate Design Space", fontweight="bold", fontsize=14,
                 color="#c9d1d9", pad=15)
    ax.tick_params(colors="#8b949e")
    ax.set_zlim(0, 100)
    ax.view_init(elev=25, azim=-50)
    fig.colorbar(surf, ax=ax, shrink=0.5, label="Read %", pad=0.1)
    save(fig, "12_3d_design_space.png")


# ================================================================
# FIGURE 13: Prior Systems Comparison
# ================================================================
def fig_prior_comparison():
    systems = list(pb.PRIOR_SYSTEMS.keys())
    throughputs = [v["throughput_kbps"] for v in pb.PRIOR_SYSTEMS.values()]
    powers = [v["power_uw"] for v in pb.PRIOR_SYSTEMS.values()]
    bar_colors = ["#8b949e", "#8b949e", "#8b949e", BLUE, GREEN]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    short_names = ["FreeRide\n2017", "X-Tandem\n2020", "BLE-BS\n2021",
                   "PassiveBLE\nCOTS", "PassiveBLE\nASIC"]

    bars1 = ax1.bar(short_names, throughputs, color=bar_colors, edgecolor="#30363d")
    ax1.set_ylabel("Goodput (kbps)")
    ax1.set_title("Throughput Comparison", fontweight="bold", fontsize=13)
    ax1.set_yscale("log")
    ax1.grid(True, axis="y", alpha=0.4)
    for bar, val in zip(bars1, throughputs):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.3,
                 f"{val:.1f}", ha="center", va="bottom", color="#c9d1d9", fontsize=9)

    bars2 = ax2.bar(short_names, powers, color=bar_colors, edgecolor="#30363d")
    ax2.set_ylabel("Power (µW)")
    ax2.set_title("Power Consumption", fontweight="bold", fontsize=13)
    ax2.grid(True, axis="y", alpha=0.4)
    for bar, val in zip(bars2, powers):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 8,
                 f"{val:.1f}", ha="center", va="bottom", color="#c9d1d9", fontsize=9)

    fig.suptitle("PassiveBLE vs Prior BLE Backscatter Systems", fontweight="bold",
                 fontsize=15, color="#c9d1d9")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, "13_prior_comparison.png")


# ================================================================
# FIGURE 14: Dock-Door Dashboard Summary
# ================================================================
def fig_dashboard():
    sim = pb.dock_door_simulation(32, 1.0, 2.0, "LE2M", "ASIC")
    harvest = pb.energy_harvest_feasibility(20, 2, 2, 1.0, pb.F_BLE, "ASIC")

    fig = plt.figure(figsize=(14, 6))
    gs = gridspec.GridSpec(2, 4, hspace=0.5, wspace=0.4)

    # Big read rate
    ax0 = fig.add_subplot(gs[:, 0])
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)
    ax0.axis("off")
    color = GREEN if sim.read_percentage > 95 else ORANGE if sim.read_percentage > 80 else RED
    ax0.text(0.5, 0.65, f"{sim.read_percentage:.1f}%", ha="center", va="center",
             fontsize=48, fontweight="bold", color=color)
    ax0.text(0.5, 0.4, "Read Rate", ha="center", va="center", fontsize=14, color="#8b949e")
    ax0.text(0.5, 0.25, f"{sim.expected_tags_read:.0f} of {sim.num_tags} tags",
             ha="center", va="center", fontsize=11, color="#8b949e")

    # Metrics
    metrics = [
        ("Dwell Time", f"{sim.dwell_time_ms:.0f} ms"),
        ("Read/Tag", f"{sim.read_time_per_tag_ms:.2f} ms"),
        ("Max Reads", f"{sim.max_reads_in_dwell}"),
        ("Conn Rate", f"{sim.connection_rate * 100:.2f}%"),
    ]
    for i, (label, value) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i + 1] if i < 3 else gs[1, 1])
        ax.axis("off")
        ax.text(0.5, 0.65, value, ha="center", va="center",
                fontsize=20, fontweight="bold", color=CYAN)
        ax.text(0.5, 0.3, label, ha="center", va="center", fontsize=11, color="#8b949e")

    # Power info
    ax_pwr = fig.add_subplot(gs[1, 2])
    ax_pwr.axis("off")
    pwr_color = GREEN if harvest.feasible else RED
    pwr_text = "Self-Powered ✓" if harvest.feasible else "Needs Battery"
    ax_pwr.text(0.5, 0.65, pwr_text, ha="center", va="center",
                fontsize=16, fontweight="bold", color=pwr_color)
    ax_pwr.text(0.5, 0.3, f"{harvest.harvested_power_uw:.1f} µW harvested",
                ha="center", va="center", fontsize=10, color="#8b949e")

    # Config
    ax_cfg = fig.add_subplot(gs[1, 3])
    ax_cfg.axis("off")
    cfg_text = f"32 tags · 1 m/s\n2 m door · LE 2M\nASIC · {sim.tag_power_uw} µW"
    ax_cfg.text(0.5, 0.5, cfg_text, ha="center", va="center",
                fontsize=11, color="#8b949e", linespacing=1.6)

    fig.suptitle("Dock-Door Simulation Dashboard: 32 Tags @ 1 m/s",
                 fontweight="bold", fontsize=15, color="#c9d1d9")
    save(fig, "14_dashboard.png")


# ================================================================
# VALIDATION
# ================================================================
def run_validation():
    print("\n" + "=" * 50)
    print("  VALIDATION AGAINST PAPER RESULTS")
    print("=" * 50)

    checks = [
        ("Max Goodput LE 2M", 974.0, pb.goodput_los(0.5, "LE2M"), 0.05),
        ("Max Goodput LE 1M", 532.0, pb.goodput_los(0.5, "LE1M"), 0.05),
        ("Connection Success", 0.999, pb.connection_success_rate(0.5), 0.01),
        ("Wake-Up @ -30 dBm", 0.91, pb.wakeup_probability(-30), 0.10),
        ("ASIC Power", 9.9, pb.power_budget("ASIC"), 0.01),
        ("COTS Power", 491.0, pb.power_budget("COTS"), 0.01),
    ]

    all_pass = True
    for name, paper, model, tol in checks:
        rel_err = abs(model - paper) / paper if paper != 0 else abs(model - paper)
        status = "PASS" if rel_err <= tol else "FAIL"
        if rel_err > tol:
            all_pass = False
        print(f"  [{status}]  {name:<25s}  Paper={paper:<10.3f}  Model={model:<10.3f}  Err={rel_err * 100:.1f}%")

    print("-" * 50)
    print(f"  OVERALL: {'ALL PASSED' if all_pass else 'FAILURES DETECTED'}")
    print("=" * 50)
    return all_pass


# ================================================================
# PHYSICS CONSISTENCY CHECKS
# ================================================================
def run_physics_checks():
    print("\n" + "=" * 50)
    print("  PHYSICS CONSISTENCY CHECKS")
    print("=" * 50)

    checks = []

    # Path loss increases with distance
    pl1 = pb.friis_path_loss(1.0)
    pl5 = pb.friis_path_loss(5.0)
    pl10 = pb.friis_path_loss(10.0)
    checks.append(("Path loss increases with distance", pl1 < pl5 < pl10))

    # Goodput decreases with distance
    g1 = pb.goodput_los(1.0, "LE2M")
    g10 = pb.goodput_los(10.0, "LE2M")
    checks.append(("Goodput decreases with distance", g1 > g10))

    # NLoS < LoS
    checks.append(("NLoS goodput < LoS", pb.goodput_nlos(5.0) < pb.goodput_los(5.0)))

    # BER increases
    checks.append(("BER increases with distance", pb.ber_model(1.0) < pb.ber_model(10.0)))

    # Connection decreases
    checks.append(("Connection rate decreases with distance",
                   pb.connection_success_rate(1.0) > pb.connection_success_rate(10.0)))

    # Maintenance < establishment
    checks.append(("Maintenance < establishment",
                   pb.connection_maintenance_rate(5.0) < pb.connection_success_rate(5.0)))

    # Multi-tag scaling
    mt1 = pb.multi_tag_goodput(2.0, 1, "LE2M")
    mt32 = pb.multi_tag_goodput(2.0, 32, "LE2M")
    checks.append(("Per-tag goodput decreases with tag count", mt1 > mt32))

    # Energy harvesting at close range
    eh = pb.energy_harvest_feasibility(20, 2, 2, 0.5)
    checks.append(("Energy harvesting feasible at 0.5 m (ASIC)", eh.feasible))

    # Slower speed -> better read rate
    sim_slow = pb.dock_door_simulation(32, 0.5, 2.0)
    sim_fast = pb.dock_door_simulation(32, 2.0, 2.0)
    checks.append(("Slower speed -> higher read rate",
                   sim_slow.read_percentage >= sim_fast.read_percentage))

    all_pass = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}]  {name}")

    print("-" * 50)
    print(f"  OVERALL: {'ALL PASSED' if all_pass else 'FAILURES DETECTED'}")
    print("=" * 50)
    return all_pass


# ================================================================
# MAIN
# ================================================================
def main():
    print("=" * 50)
    print("  PassiveBLE × Wiliot: Python Simulation Demo")
    print("  Based on arXiv 2503.11490 (MobiCom 2025)")
    print("=" * 50)
    print(f"\n  Generating figures to: {EXPORTS}\n")

    fig_path_loss()
    fig_received_power()
    fig_wakeup()
    fig_wakeup_distance()
    fig_goodput()
    fig_ber()
    fig_connection()
    fig_multi_tag()
    fig_energy_harvest()
    fig_power_breakdown()
    fig_dock_door()
    fig_3d_surface()
    fig_prior_comparison()
    fig_dashboard()

    print(f"\n  All 14 figures saved to {EXPORTS}")

    run_validation()
    run_physics_checks()

    # Print key finding
    sim = pb.dock_door_simulation(32, 1.0, 2.0, "LE2M", "ASIC")
    print("\n" + "=" * 50)
    print("  KEY FINDINGS")
    print("=" * 50)
    print(f"  1. PassiveBLE achieves 974 kbps -- 63.3x faster than prior BLE backscatter")
    print(f"  2. ASIC power 9.9 uW enables RF energy harvesting within ~1.5 m")
    print(f"  3. Dock-door: 32 tags @ 1 m/s -> {sim.read_percentage:.1f}% read rate")
    print(f"  4. BLE data channels provide authenticated, reliable connections")
    print(f"  5. Multi-tag TDD supports up to 32 tags per excitation source")
    print("=" * 50)


if __name__ == "__main__":
    main()
