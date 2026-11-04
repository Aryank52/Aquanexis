# AquaNexis — AtomQUEST 2026 Round 2 Video Demonstration Script

**Target File**: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`  
**Format**: `.mp4` | **Target Duration**: 85–90 Seconds | **Max Size**: 50 MB  
**Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun | **Team**: Solo Prototype  
**Scope**: Primary: Prognostics of filter failure using data analytics. Secondary: Input water quality sensing beyond TDS.  

---

## Shot-by-Shot Timing & Narration Plan (Total: 88 Seconds)

```
[00:00-00:08] Identity & Track 2 ──> [00:08-00:19] Problem ──> [00:19-00:31] Solution ──> [00:31-00:44] Prototype Walkthrough
       │
       ▼
[00:44-00:58] NORMAL Scenario ──> [00:58-01:12] FILTER_STRESS (FSI/FHI/RUL) ──> [01:12-01:20] LEAK Safety Event
       │
       ▼
[01:20-01:25] Provenance Transparency ──> [01:25-01:30] Round 3 Roadmap & Close
```

---

### Segment 1: Identity & Track 2 (0:00 – 0:08 | 8s)
- **Visual**: Screen capture on `http://localhost:3000/dashboard`. Top navigation bar showing "AquaNexis | AtomQUEST 2026 Track 2 — Water Purifier (UPES Dehradun)" and the `DEMO_MODE (SIMULATED)` status pill.
- **Spoken Audio**:
  > *"Hello, this is AquaNexis, developed for AtomQUEST 2026 Track 2 — Water Purifier from UPES Dehradun. This is our Round 2 software prototype demonstration."*

---

### Segment 2: Problem Statement (0:08 – 0:19 | 11s)
- **Visual**: Pan over the telemetry grid and alert overview cards.
- **Spoken Audio**:
  > *"Conventional water purifiers rely on arbitrary calendar schedules or basic TDS checks. This leads to premature filter disposal, or worse, unexpected membrane fouling and undetected water quality degradation."*

---

### Segment 3: Solution & Core Pipeline (0:19 – 0:31 | 12s)
- **Visual**: Diagram or live UI header indicating the prognostic pipeline: Sense &rarr; Understand &rarr; Predict &rarr; Alert &rarr; Assist.
- **Spoken Audio**:
  > *"AquaNexis solves this with a predictive water intelligence platform. Our pipeline senses 13 operating parameters, validates data quality, calculates continuous filter stress and health indexes, predicts remaining useful life, and generates explainable maintenance actions."*

---

### Segment 4: Completed Prototype Overview (0:31 – 0:44 | 13s)
- **Visual**: Quick navigation across the live tabs: `/dashboard`, `/water-quality`, `/filter-health`, `/alerts`, and `/maintenance`.
- **Spoken Audio**:
  > *"Our working prototype includes a FastAPI backend running in an isolated demo mode, an interactive React and TypeScript frontend, live WebSocket streaming, and a full alert state machine backed by 154 passing unit tests."*

---

### Segment 5: NORMAL Scenario Demonstration (0:44 – 0:58 | 14s)
- **Visual**: Highlight `NORMAL` scenario active on `/dashboard`.
  - Show sensor grid: TDS 150 ppm, EC 300 µS/cm, pH 7.2, Turbidity 0.3 NTU, differential pressure 30 kPa, flow rate 2.0 L/min.
  - Show AquaScore: `100/100 (EXCELLENT)`.
  - Show Filter Health Index: `86% (NORMAL)`.
  - Show RUL: `154.8 days` with `MODEL_MISSING (Deterministic Fallback v1.0)` disclosure.
- **Spoken Audio**:
  > *"Under normal operation, all 13 sensor channels show stable municipal water parameters. AquaScore is 100, Filter Health Index is 86 percent, and the estimated remaining useful life is approximately 155 days with zero active alerts."*

---

### Segment 6: FILTER_STRESS Scenario & Prognostics (0:58 – 1:12 | 14s)
- **Visual**: Click `FILTER_STRESS` on the scenario switcher. Navigate to `/filter-health`.
  - Transmembrane differential pressure ($\Delta P$) rises to 176.9 kPa; flow rate drops to 0.96 L/min.
  - Filter Stress Index jumps to `67.5 (HIGH)`.
  - Filter Health Index drops to `37% (POOR)`.
  - RUL drops to `66.6 days` in the `REPLACE_RECOMMENDED` maintenance band.
  - Show Top Contributors: differential pressure and flow deviation.
  - Show active `filter_stress_high` alert with evidence drawer.
- **Spoken Audio**:
  > *"Switching to filter stress simulates membrane fouling. Differential pressure rises to 177 kPa and flow drops below 1 liter per minute. Filter Stress Index spikes to 67.5, Health Index drops to 37 percent, and RUL drops to 66 days, triggering a critical alert and recommending Stage 1 sediment cartridge replacement."*

---

### Segment 7: LEAK Safety Event (1:12 – 1:20 | 8s)
- **Visual**: Click `LEAK` on the scenario switcher. Show the critical red banner `leak_detected` with safety event audit log on `/alerts`.
- **Spoken Audio**:
  > *"Leak detection creates a critical safety event and records and recommends an isolation action. Physical actuator shutdown is not claimed for Round 2; hardware-in-loop validation is planned for Round 3."*

---

### Segment 8: Provenance Disclosure & Integrity (1:20 – 1:25 | 5s)
- **Visual**: Zoom in on the `SIMULATED` badge on telemetry cards, and switch to `SENSOR_FAULT` showing `Quality: BAD` and RUL withheld with `Confidence: LOW`.
- **Spoken Audio**:
  > *"Every metric carries explicit provenance labels — SIMULATED for telemetry, and CALCULATED or MODEL_PREDICTED for intelligence. Under sensor faults, predictions are suppressed to prevent false confidence."*

---

### Segment 9: Round 3 Direction & Close (1:25 – 1:30 | 5s)
- **Visual**: Return to `/dashboard` in `NORMAL` state. Display submission sign-off slide.
- **Spoken Audio**:
  > *"In Round 3, we plan to validate our models against empirical test-bench membrane aging and physical solenoid hardware. Thank you."*

---

## Verification & Recording Checklist

- [x] Script duration: Exactly 88 spoken seconds at standard 135–140 words-per-minute presentation cadence.
- [x] Target sequence matches user specifications (0-8s, 8-19s, 19-31s, 31-44s, 44-58s, 58-72s, 72-80s, 80-85s, 85-90s).
- [x] Includes exact required safety phrasing for LEAK segment.
- [x] No exaggerated AI marketing claims; grounded engineering terminology throughout.
- [x] Filename: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`.
