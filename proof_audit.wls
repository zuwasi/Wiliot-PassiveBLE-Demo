#!/usr/bin/env wolframscript
(* === PROOF AUDIT SCRIPT — PassiveBLE Wiliot Demo === *)
(* Verifies model correctness against paper-reported values *)
(* Usage: wolframscript -file proof_audit.wls *)

Print["======================================"];
Print["   PROOF AUDIT — PassiveBLE Demo    "];
Print["======================================\n"];

passed = 0; failed = 0; warnings = 0;

auditResult[name_, test_, detail_] := If[test,
  Print["  PASS: ", name]; passed++,
  Print["  FAIL: ", name, " -- ", detail]; failed++
];
auditWarn[name_, test_, detail_] := If[!test,
  Print["  WARN: ", name, " -- ", detail]; warnings++
];

(* Load the package *)
Get[FileNameJoin[{DirectoryName[$InputFileName], "PassiveBLE.wl"}]];

(* ---------------------------------------- *)
(* AUDIT 1: Paper Value Spot-Check          *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 1: Paper Value Spot-Check ==="];

(* Check power values match paper Table 1 *)
auditResult["ASIC power = 9.9 uW",
  PassiveBLE`PowerBudget["ASIC"] == 9.9,
  StringForm["Got `1` instead of 9.9", PassiveBLE`PowerBudget["ASIC"]]
];

auditResult["COTS power = 491 uW",
  PassiveBLE`PowerBudget["COTS"] == 491.0,
  StringForm["Got `1` instead of 491", PassiveBLE`PowerBudget["COTS"]]
];

(* Check max goodput values *)
auditResult["LE 2M max goodput = 974 kbps at 0.5m",
  Abs[PassiveBLE`GoodputLoS[0.5, "LE2M"] - 974.0] < 1.0,
  StringForm["Got `1`", PassiveBLE`GoodputLoS[0.5, "LE2M"]]
];

auditResult["LE 1M max goodput = 532 kbps at 0.5m",
  Abs[PassiveBLE`GoodputLoS[0.5, "LE1M"] - 532.0] < 1.0,
  StringForm["Got `1`", PassiveBLE`GoodputLoS[0.5, "LE1M"]]
];

(* ---------------------------------------- *)
(* AUDIT 2: Physics Consistency             *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 2: Physics Consistency ==="];

(* Path loss must increase with distance *)
pl1 = PassiveBLE`FriisPathLoss[1.0, 2.44*^9];
pl5 = PassiveBLE`FriisPathLoss[5.0, 2.44*^9];
pl10 = PassiveBLE`FriisPathLoss[10.0, 2.44*^9];
auditResult["Path loss increases with distance",
  pl1 < pl5 < pl10,
  StringForm["PL(1m)=`1`, PL(5m)=`2`, PL(10m)=`3`", pl1, pl5, pl10]
];

(* Goodput must decrease with distance *)
g1 = PassiveBLE`GoodputLoS[1.0, "LE2M"];
g5 = PassiveBLE`GoodputLoS[5.0, "LE2M"];
g10 = PassiveBLE`GoodputLoS[10.0, "LE2M"];
auditResult["Goodput decreases with distance (LoS)",
  g1 > g5 > g10,
  StringForm["G(1m)=`1`, G(5m)=`2`, G(10m)=`3`", g1, g5, g10]
];

(* NLoS goodput < LoS goodput at same distance *)
gNLoS5 = PassiveBLE`GoodputNLoS[5.0, "LE2M"];
auditResult["NLoS goodput < LoS goodput at 5m",
  gNLoS5 < g5,
  StringForm["NLoS=`1`, LoS=`2`", gNLoS5, g5]
];

(* BER must increase with distance *)
ber1 = PassiveBLE`BERModel[1.0, "LE2M"];
ber10 = PassiveBLE`BERModel[10.0, "LE2M"];
auditResult["BER increases with distance",
  ber1 < ber10,
  StringForm["BER(1m)=`1`, BER(10m)=`2`", ber1, ber10]
];

(* Connection rate must decrease with distance *)
cr1 = PassiveBLE`ConnectionSuccessRate[1.0];
cr10 = PassiveBLE`ConnectionSuccessRate[10.0];
auditResult["Connection success rate decreases with distance",
  cr1 > cr10,
  StringForm["CR(1m)=`1`, CR(10m)=`2`", cr1, cr10]
];

(* Connection maintenance < establishment *)
ce5 = PassiveBLE`ConnectionSuccessRate[5.0];
cm5 = PassiveBLE`ConnectionMaintenanceRate[5.0];
auditResult["Maintenance rate < establishment rate (per paper Section 5.3)",
  cm5 < ce5,
  StringForm["Maint=`1`, Estab=`2`", cm5, ce5]
];

(* ---------------------------------------- *)
(* AUDIT 3: Wake-Up Model Consistency       *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 3: Wake-Up Model ==="];

(* Wake-up probability at -30 dBm should be close to 91% *)
wp30 = PassiveBLE`WakeUpProbability[-30];
auditResult["Wake-up at -30 dBm ~91% (within 10%)",
  Abs[wp30 - 0.91] < 0.10,
  StringForm["Got `1`, expected ~0.91", wp30]
];

(* Monotonicity: higher power -> higher wake-up probability *)
wp25 = PassiveBLE`WakeUpProbability[-25];
wp35 = PassiveBLE`WakeUpProbability[-35];
auditResult["Wake-up probability is monotonically increasing with power",
  wp35 < wp30 < wp25,
  StringForm["WP(-35)=`1`, WP(-30)=`2`, WP(-25)=`3`", wp35, wp30, wp25]
];

(* ---------------------------------------- *)
(* AUDIT 4: Multi-Tag Scaling               *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 4: Multi-Tag Scaling ==="];

(* More tags -> less per-tag throughput *)
mt1 = PassiveBLE`MultiTagGoodput[2.0, 1, "LE2M"];
mt8 = PassiveBLE`MultiTagGoodput[2.0, 8, "LE2M"];
mt32 = PassiveBLE`MultiTagGoodput[2.0, 32, "LE2M"];
auditResult["Per-tag goodput decreases with tag count",
  mt1 > mt8 > mt32,
  StringForm["1tag=`1`, 8tag=`2`, 32tag=`3`", mt1, mt8, mt32]
];

(* Total throughput should not exceed single-tag *)
auditResult["Total multi-tag throughput <= single-tag throughput",
  32 * mt32 <= mt1 * 1.01,  (* allow 1% numerical tolerance *)
  StringForm["32*perTag=`1`, singleTag=`2`", 32 * mt32, mt1]
];

(* ---------------------------------------- *)
(* AUDIT 5: Energy Harvesting               *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 5: Energy Harvesting ==="];

(* At very close range, harvesting should be feasible *)
ehClose = PassiveBLE`EnergyHarvestFeasibility[20, 2, 2, 0.5, 2.44*^9, "ASIC"];
auditResult["Energy harvesting feasible at 0.5m (ASIC)",
  ehClose["Feasible"],
  StringForm["Harvested=`1` uW, needed=`2` uW", ehClose["HarvestedPower_uW"], ehClose["TagPower_uW"]]
];

(* Harvested power must decrease with distance *)
eh1 = PassiveBLE`EnergyHarvestFeasibility[20, 2, 2, 1.0, 2.44*^9, "ASIC"];
eh3 = PassiveBLE`EnergyHarvestFeasibility[20, 2, 2, 3.0, 2.44*^9, "ASIC"];
auditResult["Harvested power decreases with distance",
  eh1["HarvestedPower_uW"] > eh3["HarvestedPower_uW"],
  StringForm["1m=`1` uW, 3m=`2` uW", eh1["HarvestedPower_uW"], eh3["HarvestedPower_uW"]]
];

(* ---------------------------------------- *)
(* AUDIT 6: Dock Door Simulation            *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 6: Dock Door Simulation ==="];

SeedRandom[42];
sim1 = PassiveBLE`DockDoorSimulation[16, 1.0, 2.0, "LE2M", "ASIC"];
auditResult["Dock simulation returns valid read percentage",
  0 <= sim1["ReadPercentage"] <= 100,
  StringForm["Got `1`%", sim1["ReadPercentage"]]
];

(* Slower speed -> more dwell time -> better read rate *)
SeedRandom[42];
simSlow = PassiveBLE`DockDoorSimulation[32, 0.5, 2.0, "LE2M", "ASIC"];
simFast = PassiveBLE`DockDoorSimulation[32, 2.0, 2.0, "LE2M", "ASIC"];
auditResult["Slower speed gives higher read rate",
  simSlow["ReadPercentage"] >= simFast["ReadPercentage"],
  StringForm["Slow=`1`%, Fast=`2`%", simSlow["ReadPercentage"], simFast["ReadPercentage"]]
];

(* Wider door -> more dwell time *)
SeedRandom[42];
simNarrow = PassiveBLE`DockDoorSimulation[32, 1.0, 1.0, "LE2M", "ASIC"];
simWide = PassiveBLE`DockDoorSimulation[32, 1.0, 3.0, "LE2M", "ASIC"];
auditResult["Wider door gives more dwell time",
  simWide["DwellTime_ms"] > simNarrow["DwellTime_ms"],
  StringForm["Wide=`1` ms, Narrow=`2` ms", simWide["DwellTime_ms"], simNarrow["DwellTime_ms"]]
];

(* ---------------------------------------- *)
(* AUDIT 7: Reproducibility (SeedRandom)    *)
(* ---------------------------------------- *)
Print["\n=== AUDIT 7: Reproducibility ==="];

SeedRandom[42];
run1 = PassiveBLE`DockDoorSimulation[32, 1.0, 2.0, "LE2M", "ASIC"];
SeedRandom[42];
run2 = PassiveBLE`DockDoorSimulation[32, 1.0, 2.0, "LE2M", "ASIC"];
auditResult["Deterministic with SeedRandom[42]",
  run1["ReadPercentage"] == run2["ReadPercentage"],
  StringForm["Run1=`1`%, Run2=`2`%", run1["ReadPercentage"], run2["ReadPercentage"]]
];

(* ---------------------------------------- *)
(* FINAL REPORT                             *)
(* ---------------------------------------- *)
Print["\n======================================"];
Print["       AUDIT REPORT SUMMARY         "];
Print["======================================"];
Print["  Passed:   ", passed];
Print["  Failed:   ", failed];
Print["  Warnings: ", warnings];
Print["--------------------------------------"];
If[failed == 0,
  Print["  OVERALL:  ALL AUDITS PASSED"],
  Print["  OVERALL:  AUDIT FAILURES DETECTED"]
];
Print["======================================"];

Exit[If[failed > 0, 1, 0]]
