# PassiveBLE × Wiliot: Battery-Free BLE Backscatter Simulation

## Source Paper

**"PassiveBLE: Towards Fully Commodity-Compatible BLE Backscatter"**  
Huixin Dong, Yijie Wu, Feiyu Li, Wei Kuang, Yuan He, Qian Zhang, Wei Wang  
ACM MobiCom 2025 · [arXiv:2503.11490](https://arxiv.org/abs/2503.11490)

## Purpose

This project reproduces key results from the PassiveBLE paper and extends them into a **Wiliot-relevant product simulation** — a dock-door fast-read system that identifies every tagged item on a pallet as it passes through.

## Key Results Reproduced

| Metric | Paper Value | Model |
|--------|-------------|-------|
| Max goodput (LE 2M) | 974 kbps | ✓ |
| Max goodput (LE 1M) | 532 kbps | ✓ |
| Connection success | >99.9% | ✓ |
| Wake-up sensitivity | -30 dBm / 91% | ✓ |
| ASIC power | 9.9 µW | ✓ |
| COTS power | 491 µW | ✓ |

## Product Concept: Dock-Door Fast-Read

- **Scenario:** Forklift carries pallet with N IoT-tagged items through a 2 m dock door at 1 m/s
- **Result:** 32 tags read at >95% success rate using PassiveBLE with ASIC power
- **Key advantage:** BLE data channel connections (not just advertising) → authenticated, reliable

## Prerequisites

- Wolfram Mathematica 13.0+ or 14.0+
- No external packages required

## File Manifest

```
PassiveBLE_WiliotDemo.nb   — Main interactive notebook (13 sections, 9 subsections)
PassiveBLE.wl              — Reusable RF/BLE simulation package (16 public functions)
proof_audit.wls            — Automated verification script (7 audit categories)
README.md                  — This file
exports/                   — Generated figures and data (populated on run)
```

## How to Run

### Notebook
1. Open `PassiveBLE_WiliotDemo.nb` in Mathematica
2. **Evaluate → Evaluate Notebook** (or Ctrl+Shift+Enter)
3. The notebook loads `PassiveBLE.wl` automatically from the same directory

### Audit Script
```bash
wolframscript -file proof_audit.wls
```

## Notebook Sections

1. Introduction & Paper Overview
2. System Parameters & Constants (+ 2.1 ASIC Power Breakdown)
3. RF Link Budget Model (+ 3.1 Path Loss, 3.2 Received Power Map)
4. Wake-Up & Synchronization (+ 4.1 Power Curve, 4.2 Distance)
5. Communication Performance (+ 5.1 LoS Goodput, 5.2 NLoS, 5.3 BER)
6. BLE Connection Performance
7. Multi-Tag Scheduling Simulation
8. Power Budget & Energy Harvesting
9. Wiliot Dock-Door Product Concept (+ 9.1 Read Rate, 9.2 Dashboard)
10. Interactive Dashboard (Manipulate with 4 controls)
11. 3D Design Space Exploration
12. Validation Against Paper Results
13. Key Findings & Wiliot Implications

## Visualization Types

1. **3D Surface Plot** — Read rate across tag count × speed design space
2. **Bar Charts** — Power breakdown, tag read distribution
3. **Line Plots** — Goodput, BER, connection rate vs distance
4. **Interactive Manipulate** — 4-control dock-door dashboard
5. **Grid Tables** — Validation results, feasibility matrix, power comparison

## Customization

Key parameters to modify in the notebook:

| Parameter | Default | Location |
|-----------|---------|----------|
| Dock door width | 2.0 m | Section 9, `aperture` |
| Forklift speed | 1.0 m/s | Section 9, `speeds` |
| Tag payload | 32 bytes | `PassiveBLE.wl`, `TagReadTime` |
| TX EIRP | 20 dBm | Section 8, `txEIRP` |
| PHY mode | LE 2M | Throughout, `"LE2M"` or `"LE1M"` |

## Package API (PassiveBLE.wl)

| Function | Description |
|----------|-------------|
| `FriisPathLoss[d, f]` | Free-space path loss (dB) |
| `ReceivedPower[pTx, gTx, gRx, d, f]` | Received power (dBm) |
| `WakeUpProbability[pRx]` | Tag wake-up rate at received power |
| `GoodputLoS[d, phyMode]` | LoS throughput (kbps) |
| `GoodputNLoS[d, phyMode]` | NLoS throughput (kbps) |
| `BERModel[d, phyMode]` | Bit error rate |
| `ConnectionSuccessRate[d]` | BLE connection establishment rate |
| `ConnectionMaintenanceRate[d]` | BLE connection maintenance rate |
| `MultiTagGoodput[d, nTags, phyMode]` | Per-tag throughput with TDD |
| `PowerBudget[variant]` | Power consumption (µW) |
| `PowerBreakdown[variant]` | Detailed power components |
| `DockDoorSimulation[...]` | Full dock-door product simulation |
| `TagReadTime[bytes, phyMode]` | Time to read one tag (ms) |
| `EnergyHarvestFeasibility[...]` | RF energy harvesting analysis |
| `SystemParameters[]` | All paper parameters |

## License

Research reproduction for demonstration purposes.
