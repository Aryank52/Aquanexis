# AquaNexis — AtomQUEST 2026 Round 2 Video Script & Screen Plan
## Hybrid Presentation: Presenter On-Camera + Working Prototype Screen

**Target File**: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`  
**Total Target Duration**: 85–90 Seconds (218 spoken words at ~145 words/minute)  
**Maximum File Size**: 50 MB | **Format**: `.mp4` (1080p, 30 fps)  
**Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun | **Team**: Solo Prototype  
**Scope**: Primary: Prognostics of filter failure using data analytics. Secondary: Input water quality sensing beyond TDS.  

---

## Shot-by-Shot Hybrid Execution Plan

| Timestamp | Visual Display (What the Viewer Sees) | Spoken Audio (What the Presenter Says) |
| :---: | :--- | :--- |
| **0:00 – 0:08**<br>(8s) | **Presenter on Camera (Full View)**<br>Presenter speaking directly to lens. Clean lower-third title graphic overlay:<br>• *AquaNexis — Predictive Water Intelligence*<br>• *AtomQUEST 2026 Track 2 — Water Purifier*<br>• *UPES Dehradun \| Solo Prototype* | *"Hello, I am [Your Name] from UPES Dehradun, presenting AquaNexis for AtomQUEST Track 2 — Water Purifier."* |
| **0:08 – 0:21**<br>(13s) | **Problem Graphic / Split Screen**<br>Graphic illustrating traditional purifier limitations: blind calendar replacement timer and single TDS sensor failing to detect membrane fouling, pressure drop, or sediment clogging. | *"Conventional purifiers rely on fixed calendar timers or simple TDS checks. But TDS alone misses membrane fouling, pressure drop, and particulate load — causing premature filter waste or unmonitored degradation."* |
| **0:21 – 0:35**<br>(14s) | **Architecture & Pipeline Diagram**<br>Decision-flow diagram showing the 5-stage intelligence pipeline:<br>`Sense (13 Params) &rarr; Understand (Quality Gate) &rarr; Predict (FSI/RUL) &rarr; Alert (State Machine) &rarr; Assist (Maintenance)`. | *"AquaNexis delivers a predictive intelligence pipeline: Sense, Understand, Predict, Alert, and Assist. We evaluate thirteen parameters, including pH, turbidity, flow rate, and transmembrane differential pressure to track true filter health."* |
| **0:35 – 0:50**<br>(15s) | **Live Prototype: NORMAL &rarr; FILTER_STRESS**<br>Screen capture of live working dashboard (`localhost:3000`).<br>1. Shows `NORMAL` baseline: AquaScore 100, FHI 86%, RUL ~155d, 0 alerts.<br>2. Clicks `FILTER_STRESS`: Differential pressure rises to 177 kPa, flow drops to 0.96 L/min, FSI spikes to 67.5, FHI drops to 37%, and active `filter_stress_high` alert appears with replacement recommendation. | *"In our live prototype, normal conditions show stable baseline telemetry. Simulating membrane stress spikes differential pressure to 177 kilopascals, drops flow, elevates the Filter Stress Index to 67.5, and triggers an explainable filter replacement alert."* |
| **0:50 – 0:62**<br>(12s) | **Verified Project Statistics Overlay**<br>Graphic overlay over UI:<br>• 154 Passing Automated Unit Tests (100% pass)<br>• Controlled ML Dataset: 600 Run-to-Failure Cycles (480 train / 120 test, 15 features)<br>• Candidate Test MAE: 4.85 days ($R^2 = 0.9962$) | *"Our platform is verified by 154 automated unit tests. On a controlled dataset of 600 degradation cycles across 15 features, our candidate prognostic model achieved a test MAE of 4.85 days."* |
| **0:62 – 0:74**<br>(12s) | **Live Prototype: LEAK & Safety State**<br>Screen displays `/alerts` with critical red `leak_detected` banner and safety event audit log. Sensor fault graceful degradation highlighted on `/filter-health`. | *"Deterministic rule logic takes priority over predictive output. Leak conditions create a critical safety event and isolation recommendation. Physical automatic shutdown is not claimed until hardware-in-loop validation is complete."* |
| **0:74 – 0:83**<br>(9s) | **Completed vs. Pending Summary Card**<br>Split card on screen:<br>• *Completed (Round 2)*: Software Intelligence Stack, 13-Channel Ingestion, FSI/FHI Prognostics, React Dashboard, Tested DEMO_MODE.<br>• *Pending (Round 3)*: Physical ESP32 Hardware Bench, Multi-Month Empirical Membrane Aging. | *"Round 2 proves the complete software intelligence stack using controlled telemetry, while physical edge sensing and reference probe calibration are scheduled for Round 3."* |
| **0:83 – 0:90**<br>(7s) | **Presenter on Camera (Full View)**<br>Presenter on camera delivering confident technical conclusion. Final slide overlay with repository link and AtomQUEST Round 2 sign-off. | *"In Round 3, we will collect empirical membrane aging data and validate physical valve shut-off on a test rig. Thank you."* |

---

## Technical Pacing & Word Count Summary

- **Total Spoken Words**: **218 words**
- **Presenter Pacing**: **145–147 words per minute** (clear, articulate, natural presentation cadence)
- **Target Video Duration**: **88.5 seconds** (comfortably within the 85–90 second window)
- **Visual Delivery Ratio**: ~15 seconds on camera (Intro & Outro), ~75 seconds on live prototype screen and clean technical schematics.
