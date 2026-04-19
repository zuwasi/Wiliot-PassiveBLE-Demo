(* ::Package:: *)
(* PassiveBLE.wl — Reusable RF/BLE backscatter simulation package *)
(* Based on: "PassiveBLE: Towards Fully Commodity-Compatible BLE Backscatter" *)
(* Authors: Dong et al., MobiCom 2025 (arXiv 2503.11490) *)

BeginPackage["PassiveBLE`"]

(* === Public API === *)

FriisPathLoss::usage = "FriisPathLoss[d, f] returns free-space path loss in dB at distance d (m) and frequency f (Hz)."
ReceivedPower::usage = "ReceivedPower[pTx, gTx, gRx, d, f] returns received power in dBm."
WakeUpProbability::usage = "WakeUpProbability[pRx] returns tag wake-up probability given received power pRx (dBm). Fitted to paper data."
GoodputLoS::usage = "GoodputLoS[d, phyMode] returns goodput (kbps) at distance d (m) for LoS. phyMode: \"LE1M\" or \"LE2M\"."
GoodputNLoS::usage = "GoodputNLoS[d, phyMode] returns goodput (kbps) at distance d (m) for NLoS."
BERModel::usage = "BERModel[d, phyMode] returns bit error rate at distance d (m)."
ConnectionSuccessRate::usage = "ConnectionSuccessRate[d] returns BLE connection establishment success rate at distance d (m)."
ConnectionMaintenanceRate::usage = "ConnectionMaintenanceRate[d] returns BLE connection maintenance success rate at distance d (m)."
MultiTagGoodput::usage = "MultiTagGoodput[d, nTags, phyMode] returns per-tag goodput (kbps) with nTags sharing one excitation source via TDD."
PowerBudget::usage = "PowerBudget[variant] returns power consumption in uW. variant: \"COTS\" or \"ASIC\"."
PowerBreakdown::usage = "PowerBreakdown[variant] returns Association of power components in uW."
DockDoorSimulation::usage = "DockDoorSimulation[nTags, speed, aperture, phyMode, variant] simulates pallet passing dock door. Returns Association with read results."
TagReadTime::usage = "TagReadTime[payloadBytes, phyMode] returns time (ms) to read one tag's payload."
EnergyHarvestFeasibility::usage = "EnergyHarvestFeasibility[pTx, gTx, gRx, d, f, variant] returns Association with harvesting analysis."
SystemParameters::usage = "SystemParameters[] returns Association of all key system parameters from the paper."

Begin["`Private`"]

(* === Constants === *)
c0 = 2.998*^8;                   (* speed of light, m/s *)
fBLE = 2.44*^9;                  (* BLE center frequency, Hz *)
kBoltzmann = 1.381*^-23;         (* Boltzmann constant, J/K *)
tempAmbient = 300;               (* ambient temperature, K *)
noiseFigure = 6;                 (* receiver noise figure, dB *)
bleBandwidth = 2*^6;             (* BLE channel bandwidth, Hz *)

(* === Paper-reported parameters === *)
powerCOTS = 491.0;               (* uW, off-the-shelf prototype *)
powerASIC = 9.9;                 (* uW, ASIC design *)
powerSyncAmp = 162.4;            (* uW, synchronization amplifier *)
powerSyncComp = 27.9;            (* uW, synchronization comparator *)
powerSyncTotal = 190.3;          (* uW, total sync circuit *)
powerASICStatic = 0.9;           (* uW, ASIC static *)
powerASICDynamic = 9.9;          (* uW, ASIC dynamic uplink *)

maxGoodputLE2M = 974.0;          (* kbps, LE 2M PHY *)
maxGoodputLE1M = 532.0;          (* kbps, LE 1M PHY *)
wakeUpSensitivity = -30.0;       (* dBm *)
syncAccuracy = 93.0;             (* ns *)
connectionSuccessMax = 0.999;    (* >99.9% *)
maxCommDistance = 17.0;           (* meters *)
defaultTxToTag = 0.5;            (* meters, paper default *)

(* Paper wake-up data points: {power dBm, success rate} *)
wakeUpData = {{-25, 1.0}, {-26, 1.0}, {-27, 0.999}, {-28, 0.995},
              {-29, 0.97}, {-30, 0.91}, {-31, 0.24}, {-32, 0.05},
              {-33, 0.01}, {-35, 0.0}};

(* Paper wake-up distance data: {distance m, success rate} at EIRP 20 dBm *)
wakeUpDistanceData = {{0.25, 1.0}, {0.5, 0.999}, {0.75, 0.995},
                      {1.0, 0.98}, {1.25, 0.965}, {1.5, 0.951},
                      {1.75, 0.92}, {2.0, 0.88}, {2.25, 0.84},
                      {2.5, 0.80}, {2.75, 0.72}, {3.0, 0.60},
                      {3.5, 0.35}, {4.0, 0.15}, {4.5, 0.05}, {5.0, 0.01}};

(* === RF Link Budget === *)

FriisPathLoss[d_?NumericQ, f_?NumericQ] /; d > 0 :=
  N[20 Log10[4 Pi d f / c0]]

ReceivedPower[pTx_?NumericQ, gTx_?NumericQ, gRx_?NumericQ,
              d_?NumericQ, f_?NumericQ] /; d > 0 :=
  N[pTx + gTx + gRx - FriisPathLoss[d, f]]

(* === Wake-Up Model === *)
(* Logistic fit to paper data: steep transition around -30 dBm *)

wakeUpLogisticK = 3.5;   (* steepness *)
wakeUpLogisticX0 = -30.5; (* midpoint dBm *)

WakeUpProbability[pRx_?NumericQ] :=
  N[1.0 / (1.0 + Exp[-wakeUpLogisticK (pRx - wakeUpLogisticX0)])]

(* === Goodput Models === *)
(* Exponential decay fit to paper results *)
(* LoS: goodput decays more slowly than NLoS *)

goodputDecayLoS = 0.12;   (* decay rate, per meter *)
goodputDecayNLoS = 0.18;  (* faster decay for NLoS *)

maxGoodput[phyMode_String] := Switch[phyMode,
  "LE2M", maxGoodputLE2M,
  "LE1M", maxGoodputLE1M,
  _, maxGoodputLE1M
]

GoodputLoS[d_?NumericQ, phyMode_String:"LE2M"] /; d >= 0 :=
  Module[{gMax, effectiveD},
    gMax = maxGoodput[phyMode];
    effectiveD = Max[d - defaultTxToTag, 0];
    N[gMax * Exp[-goodputDecayLoS * effectiveD]]
  ]

GoodputNLoS[d_?NumericQ, phyMode_String:"LE2M"] /; d >= 0 :=
  Module[{gMax, effectiveD},
    gMax = maxGoodput[phyMode];
    effectiveD = Max[d - defaultTxToTag, 0];
    N[gMax * 0.85 * Exp[-goodputDecayNLoS * effectiveD]]
  ]

(* === BER Model === *)
(* BER increases with distance; near zero at short range *)

BERModel[d_?NumericQ, phyMode_String:"LE2M"] /; d >= 0 :=
  Module[{baseRate, distFactor},
    baseRate = Switch[phyMode, "LE2M", 1.0*^-6, "LE1M", 5.0*^-7, _, 1.0*^-6];
    distFactor = Exp[0.35 * d];
    N[Min[baseRate * distFactor, 0.5]]
  ]

(* === Connection Performance === *)

ConnectionSuccessRate[d_?NumericQ] /; d >= 0 :=
  Module[{rate},
    rate = connectionSuccessMax * Exp[-0.005 * d^2];
    N[Max[rate, 0.0]]
  ]

ConnectionMaintenanceRate[d_?NumericQ] /; d >= 0 :=
  Module[{rate},
    (* Maintenance rate is lower than establishment, per paper Section 5.3 *)
    rate = 0.995 * Exp[-0.012 * d^2];
    N[Max[rate, 0.0]]
  ]

(* === Multi-Tag Scheduling === *)
(* TDD: tags share time slots; per-tag throughput scales as ~1/N *)

MultiTagGoodput[d_?NumericQ, nTags_Integer, phyMode_String:"LE2M"] /; nTags > 0 :=
  Module[{singleGoodput, schedulingOverhead, effectiveGoodput},
    singleGoodput = GoodputLoS[d, phyMode];
    (* Scheduling overhead: 5% per additional tag due to connection switching *)
    schedulingOverhead = 1.0 - 0.05 * Min[nTags - 1, 10];
    effectiveGoodput = singleGoodput * Max[schedulingOverhead, 0.5] / nTags;
    N[effectiveGoodput]
  ]

(* === Power Budget === *)

PowerBudget[variant_String] := Switch[variant,
  "COTS", powerCOTS,
  "ASIC", powerASIC,
  _, powerASIC
]

PowerBreakdown[variant_String] := Switch[variant,
  "COTS", <|
    "Total" -> powerCOTS,
    "Baseband" -> 300.7,
    "SyncCircuit" -> powerSyncTotal,
    "Unit" -> "uW"
  |>,
  "ASIC", <|
    "Total" -> powerASIC + powerSyncTotal,
    "BasebandStatic" -> powerASICStatic,
    "BasebandDynamic" -> powerASICDynamic,
    "SyncAmplifier" -> powerSyncAmp,
    "SyncComparator" -> powerSyncComp,
    "Unit" -> "uW"
  |>,
  _, <|"Error" -> "Unknown variant"|>
]

(* === Tag Read Time === *)

TagReadTime[payloadBytes_Integer, phyMode_String:"LE2M"] :=
  Module[{bitRate, overheadBits, totalBits},
    bitRate = Switch[phyMode, "LE2M", 2000.0, "LE1M", 1000.0, _, 1000.0]; (* kbps *)
    overheadBits = 80;  (* BLE packet header + CRC, bits *)
    totalBits = payloadBytes * 8 + overheadBits;
    N[totalBits / bitRate]  (* ms *)
  ]

(* === Dock Door Simulation === *)

DockDoorSimulation[nTags_Integer, speed_?NumericQ, aperture_?NumericQ,
                   phyMode_String:"LE2M", variant_String:"ASIC"] :=
  Module[{dwellTime, readTimePerTag, maxReads, readProbPerTag,
          expectedReads, avgDistance, connRate, payloadBytes,
          totalReadTime, readFraction},
    SeedRandom[42];
    payloadBytes = 32;  (* typical IoT sensor payload *)
    dwellTime = aperture / speed * 1000;  (* ms *)
    readTimePerTag = TagReadTime[payloadBytes, phyMode];
    avgDistance = aperture / 2;  (* average distance while in aperture *)
    connRate = ConnectionSuccessRate[avgDistance];

    (* Time available per tag in TDD *)
    totalReadTime = readTimePerTag * 1.2;  (* 20% overhead for connection setup *)
    maxReads = Floor[dwellTime / totalReadTime];

    (* Each tag needs at least one successful read *)
    readProbPerTag = If[nTags <= maxReads,
      connRate * (1 - BERModel[avgDistance, phyMode])^(payloadBytes * 8),
      connRate * (1 - BERModel[avgDistance, phyMode])^(payloadBytes * 8) *
        Min[maxReads / nTags, 1.0]
    ];

    expectedReads = N[nTags * readProbPerTag];
    readFraction = N[readProbPerTag];

    <|
      "NumTags" -> nTags,
      "Speed_mps" -> speed,
      "Aperture_m" -> aperture,
      "DwellTime_ms" -> N[dwellTime],
      "ReadTimePerTag_ms" -> N[totalReadTime],
      "MaxReadsInDwell" -> maxReads,
      "AvgDistance_m" -> N[avgDistance],
      "ConnectionRate" -> N[connRate],
      "ReadProbPerTag" -> readFraction,
      "ExpectedTagsRead" -> expectedReads,
      "ReadPercentage" -> N[readFraction * 100],
      "PHY" -> phyMode,
      "TagPower_uW" -> PowerBudget[variant],
      "Variant" -> variant
    |>
  ]

(* === Energy Harvesting Feasibility === *)

EnergyHarvestFeasibility[pTx_?NumericQ, gTx_?NumericQ, gRx_?NumericQ,
                         d_?NumericQ, f_?NumericQ, variant_String:"ASIC"] :=
  Module[{pRxDBm, pRxWatts, pTag, harvestEff, pHarvested, surplus, feasible},
    pRxDBm = ReceivedPower[pTx, gTx, gRx, d, f];
    pRxWatts = 10^((pRxDBm - 30) / 10);  (* convert dBm to Watts *)
    harvestEff = 0.35;  (* RF-to-DC conversion efficiency *)
    pHarvested = pRxWatts * harvestEff * 1.0*^6;  (* convert to uW *)
    pTag = PowerBudget[variant];
    surplus = pHarvested - pTag;
    feasible = surplus > 0;

    <|
      "ReceivedPower_dBm" -> N[pRxDBm],
      "ReceivedPower_uW" -> N[pRxWatts * 1.0*^6],
      "HarvestEfficiency" -> harvestEff,
      "HarvestedPower_uW" -> N[pHarvested],
      "TagPower_uW" -> pTag,
      "Surplus_uW" -> N[surplus],
      "Feasible" -> feasible,
      "Distance_m" -> d,
      "Variant" -> variant
    |>
  ]

(* === System Parameters Summary === *)

SystemParameters[] := <|
  "Paper" -> "PassiveBLE: Towards Fully Commodity-Compatible BLE Backscatter",
  "Venue" -> "ACM MobiCom 2025",
  "ArXiv" -> "2503.11490",
  "Frequency_Hz" -> fBLE,
  "MaxGoodput_LE2M_kbps" -> maxGoodputLE2M,
  "MaxGoodput_LE1M_kbps" -> maxGoodputLE1M,
  "PowerCOTS_uW" -> powerCOTS,
  "PowerASIC_uW" -> powerASIC,
  "PowerSync_uW" -> powerSyncTotal,
  "WakeUpSensitivity_dBm" -> wakeUpSensitivity,
  "SyncAccuracy_ns" -> syncAccuracy,
  "ConnectionSuccessRate" -> connectionSuccessMax,
  "MaxCommDistance_m" -> maxCommDistance,
  "DefaultTxToTag_m" -> defaultTxToTag,
  "WakeUpData" -> wakeUpData,
  "WakeUpDistanceData" -> wakeUpDistanceData
|>

End[]
EndPackage[]
