"""
PassiveBLE — Reusable RF/BLE backscatter simulation package (Python).

Based on: "PassiveBLE: Towards Fully Commodity-Compatible BLE Backscatter"
Authors: Dong et al., MobiCom 2025 (arXiv 2503.11490)

Mirror of PassiveBLE.wl for Python workflows.
"""

import math
from dataclasses import dataclass, field

# === Constants ===
C0 = 2.998e8          # speed of light, m/s
F_BLE = 2.44e9        # BLE center frequency, Hz

# === Paper-reported parameters ===
POWER_COTS = 491.0    # µW, off-the-shelf prototype
POWER_ASIC = 9.9      # µW, ASIC design
POWER_SYNC_AMP = 162.4
POWER_SYNC_COMP = 27.9
POWER_SYNC_TOTAL = 190.3
POWER_ASIC_STATIC = 0.9
POWER_ASIC_DYNAMIC = 9.9

MAX_GOODPUT_LE2M = 974.0   # kbps
MAX_GOODPUT_LE1M = 532.0   # kbps
WAKE_UP_SENSITIVITY = -30.0  # dBm
SYNC_ACCURACY = 93.0        # ns
CONN_SUCCESS_MAX = 0.999
MAX_COMM_DISTANCE = 17.0    # m
DEFAULT_TX_TO_TAG = 0.5     # m

# Logistic fit parameters for wake-up model
_WAKEUP_K = 3.5
_WAKEUP_X0 = -30.5

# Decay rates for goodput models
_DECAY_LOS = 0.12
_DECAY_NLOS = 0.18

# Paper wake-up data points: (power_dBm, success_rate)
WAKEUP_DATA = [
    (-25, 1.0), (-26, 1.0), (-27, 0.999), (-28, 0.995),
    (-29, 0.97), (-30, 0.91), (-31, 0.24), (-32, 0.05),
    (-33, 0.01), (-35, 0.0),
]

# Paper wake-up distance data: (distance_m, success_rate) at EIRP 20 dBm
WAKEUP_DISTANCE_DATA = [
    (0.25, 1.0), (0.5, 0.999), (0.75, 0.995), (1.0, 0.98),
    (1.25, 0.965), (1.5, 0.951), (1.75, 0.92), (2.0, 0.88),
    (2.25, 0.84), (2.5, 0.80), (2.75, 0.72), (3.0, 0.60),
    (3.5, 0.35), (4.0, 0.15), (4.5, 0.05), (5.0, 0.01),
]

# Prior systems comparison (Table 1)
PRIOR_SYSTEMS = {
    "FreeRide (2017)":         {"power_uw": 18.0,  "throughput_kbps": 0.27,  "compatible": "Partial"},
    "X-Tandem (2020)":         {"power_uw": 22.3,  "throughput_kbps": 2.0,   "compatible": "Partial"},
    "BLE-Backscatter (2021)":  {"power_uw": 15.4,  "throughput_kbps": 15.4,  "compatible": "Full (Adv)"},
    "PassiveBLE COTS":         {"power_uw": 491.0, "throughput_kbps": 974.0, "compatible": "Full (Data)"},
    "PassiveBLE ASIC":         {"power_uw": 9.9,   "throughput_kbps": 974.0, "compatible": "Full (Data)"},
}


# === RF Link Budget ===

def friis_path_loss(d: float, f: float = F_BLE) -> float:
    """Free-space path loss in dB at distance d (m) and frequency f (Hz)."""
    if d <= 0:
        raise ValueError("Distance must be positive")
    return 20 * math.log10(4 * math.pi * d * f / C0)


def received_power(p_tx: float, g_tx: float, g_rx: float,
                   d: float, f: float = F_BLE) -> float:
    """Received power in dBm."""
    return p_tx + g_tx + g_rx - friis_path_loss(d, f)


# === Wake-Up Model ===

def wakeup_probability(p_rx: float) -> float:
    """Tag wake-up probability given received power p_rx (dBm).
    Logistic fit to paper data."""
    return 1.0 / (1.0 + math.exp(-_WAKEUP_K * (p_rx - _WAKEUP_X0)))


# === Goodput Models ===

def _max_goodput(phy_mode: str) -> float:
    return MAX_GOODPUT_LE2M if phy_mode == "LE2M" else MAX_GOODPUT_LE1M


def goodput_los(d: float, phy_mode: str = "LE2M") -> float:
    """Goodput (kbps) at distance d (m) for line-of-sight."""
    g_max = _max_goodput(phy_mode)
    effective_d = max(d - DEFAULT_TX_TO_TAG, 0)
    return g_max * math.exp(-_DECAY_LOS * effective_d)


def goodput_nlos(d: float, phy_mode: str = "LE2M") -> float:
    """Goodput (kbps) at distance d (m) for non-line-of-sight."""
    g_max = _max_goodput(phy_mode)
    effective_d = max(d - DEFAULT_TX_TO_TAG, 0)
    return g_max * 0.85 * math.exp(-_DECAY_NLOS * effective_d)


# === BER Model ===

def ber_model(d: float, phy_mode: str = "LE2M") -> float:
    """Bit error rate at distance d (m)."""
    base_rate = 1.0e-6 if phy_mode == "LE2M" else 5.0e-7
    dist_factor = math.exp(0.35 * d)
    return min(base_rate * dist_factor, 0.5)


# === Connection Performance ===

def connection_success_rate(d: float) -> float:
    """BLE connection establishment success rate at distance d (m)."""
    return max(CONN_SUCCESS_MAX * math.exp(-0.005 * d ** 2), 0.0)


def connection_maintenance_rate(d: float) -> float:
    """BLE connection maintenance success rate at distance d (m)."""
    return max(0.995 * math.exp(-0.012 * d ** 2), 0.0)


# === Multi-Tag Scheduling ===

def multi_tag_goodput(d: float, n_tags: int, phy_mode: str = "LE2M") -> float:
    """Per-tag goodput (kbps) with n_tags sharing one excitation source via TDD."""
    single = goodput_los(d, phy_mode)
    overhead = 1.0 - 0.05 * min(n_tags - 1, 10)
    return single * max(overhead, 0.5) / n_tags


# === Power Budget ===

def power_budget(variant: str) -> float:
    """Power consumption in µW. variant: 'COTS' or 'ASIC'."""
    return POWER_COTS if variant == "COTS" else POWER_ASIC


def power_breakdown(variant: str) -> dict:
    """Detailed power components in µW."""
    if variant == "COTS":
        return {
            "total": POWER_COTS,
            "baseband": 300.7,
            "sync_circuit": POWER_SYNC_TOTAL,
            "unit": "µW",
        }
    return {
        "total": POWER_ASIC + POWER_SYNC_TOTAL,
        "baseband_static": POWER_ASIC_STATIC,
        "baseband_dynamic": POWER_ASIC_DYNAMIC,
        "sync_amplifier": POWER_SYNC_AMP,
        "sync_comparator": POWER_SYNC_COMP,
        "unit": "µW",
    }


# === Tag Read Time ===

def tag_read_time(payload_bytes: int = 32, phy_mode: str = "LE2M") -> float:
    """Time (ms) to read one tag's payload."""
    bit_rate = 2000.0 if phy_mode == "LE2M" else 1000.0  # kbps
    overhead_bits = 80  # BLE header + CRC
    total_bits = payload_bytes * 8 + overhead_bits
    return total_bits / bit_rate


# === Dock Door Simulation ===

@dataclass
class DockDoorResult:
    num_tags: int
    speed_mps: float
    aperture_m: float
    dwell_time_ms: float
    read_time_per_tag_ms: float
    max_reads_in_dwell: int
    avg_distance_m: float
    connection_rate: float
    read_prob_per_tag: float
    expected_tags_read: float
    read_percentage: float
    phy: str
    tag_power_uw: float
    variant: str


def dock_door_simulation(n_tags: int, speed: float, aperture: float,
                         phy_mode: str = "LE2M",
                         variant: str = "ASIC") -> DockDoorResult:
    """Simulate pallet passing dock door. Returns DockDoorResult."""
    payload_bytes = 32
    dwell_time = aperture / speed * 1000  # ms
    read_time = tag_read_time(payload_bytes, phy_mode)
    avg_distance = aperture / 2
    conn_rate = connection_success_rate(avg_distance)

    total_read_time = read_time * 1.2  # 20% overhead
    max_reads = int(dwell_time / total_read_time)

    ber = ber_model(avg_distance, phy_mode)
    packet_success = (1 - ber) ** (payload_bytes * 8)

    if n_tags <= max_reads:
        read_prob = conn_rate * packet_success
    else:
        read_prob = conn_rate * packet_success * min(max_reads / n_tags, 1.0)

    expected = n_tags * read_prob

    return DockDoorResult(
        num_tags=n_tags,
        speed_mps=speed,
        aperture_m=aperture,
        dwell_time_ms=dwell_time,
        read_time_per_tag_ms=total_read_time,
        max_reads_in_dwell=max_reads,
        avg_distance_m=avg_distance,
        connection_rate=conn_rate,
        read_prob_per_tag=read_prob,
        expected_tags_read=expected,
        read_percentage=read_prob * 100,
        phy=phy_mode,
        tag_power_uw=power_budget(variant),
        variant=variant,
    )


# === Energy Harvesting Feasibility ===

@dataclass
class HarvestResult:
    received_power_dbm: float
    received_power_uw: float
    harvest_efficiency: float
    harvested_power_uw: float
    tag_power_uw: float
    surplus_uw: float
    feasible: bool
    distance_m: float
    variant: str


def energy_harvest_feasibility(p_tx: float, g_tx: float, g_rx: float,
                               d: float, f: float = F_BLE,
                               variant: str = "ASIC") -> HarvestResult:
    """RF energy harvesting feasibility analysis."""
    p_rx_dbm = received_power(p_tx, g_tx, g_rx, d, f)
    p_rx_watts = 10 ** ((p_rx_dbm - 30) / 10)
    harvest_eff = 0.35
    p_harvested = p_rx_watts * harvest_eff * 1e6  # µW
    p_tag = power_budget(variant)
    surplus = p_harvested - p_tag

    return HarvestResult(
        received_power_dbm=p_rx_dbm,
        received_power_uw=p_rx_watts * 1e6,
        harvest_efficiency=harvest_eff,
        harvested_power_uw=p_harvested,
        tag_power_uw=p_tag,
        surplus_uw=surplus,
        feasible=surplus > 0,
        distance_m=d,
        variant=variant,
    )


# === System Parameters ===

def system_parameters() -> dict:
    """All key system parameters from the paper."""
    return {
        "paper": "PassiveBLE: Towards Fully Commodity-Compatible BLE Backscatter",
        "venue": "ACM MobiCom 2025",
        "arxiv": "2503.11490",
        "frequency_hz": F_BLE,
        "max_goodput_le2m_kbps": MAX_GOODPUT_LE2M,
        "max_goodput_le1m_kbps": MAX_GOODPUT_LE1M,
        "power_cots_uw": POWER_COTS,
        "power_asic_uw": POWER_ASIC,
        "power_sync_uw": POWER_SYNC_TOTAL,
        "wakeup_sensitivity_dbm": WAKE_UP_SENSITIVITY,
        "sync_accuracy_ns": SYNC_ACCURACY,
        "connection_success_rate": CONN_SUCCESS_MAX,
        "max_comm_distance_m": MAX_COMM_DISTANCE,
        "default_tx_to_tag_m": DEFAULT_TX_TO_TAG,
    }
