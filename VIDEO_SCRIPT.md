# AquaNexis Round 2 Submission — 90-Second Video Script

**File**: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`
**Duration**: Maximum 90 seconds
**Size**: Maximum 50 MB

---

## Video Sequence (Total: 90 seconds)

### 0:00-0:08 — Title & Problem Statement (8s)
- **Visual**: AquaNexis logo + "Predictive Water Intelligence System"
- **Text**: "Track 2: Water Purifier | UPES Dehradun | Solo Prototype"
- **Narration**: "AquaNexis is a predictive water intelligence platform that transforms raw purifier telemetry into actionable filter health insights and failure predictions."

### 0:08-0:18 — Architecture Overview (10s)
- **Visual**: Animated diagram — Python Simulator → FastAPI Backend → PostgreSQL → React Dashboard
- **Text**: "Software-only prototype | 13 sensor types | Real-time WebSocket"
- **Narration**: "Our software-only architecture ingests telemetry from 13 sensor types through a Python simulator, processes it through FastAPI with PostgreSQL persistence, and delivers real-time insights via WebSocket to a React dashboard."

### 0:18-0:35 — NORMAL Operation (17s)
- **Visual**: Dashboard page — Green "Online" badge, AquaScore 85, sensor grid with live values
- **Action**: Hover over AquaScore → shows "CALCULATED" provenance badge
- **Action**: Hover over sensor cards → shows "SIMULATED" provenance badge
- **Text**: "Normal operation | AquaScore: 85 | All sensors GOOD"
- **Narration**: "In normal operation, the dashboard shows live telemetry with full provenance tracking — every value labeled as SIMULATED from our simulator, AquaScore as CALCULATED from measured inputs."

### 0:35-0:55 — FILTER_STRESS Scenario (20s)
- **Visual**: Terminal — `python simulator.py --profile filter_stress`
- **Visual**: Dashboard updates — FSI rises to 65 (MODERATE), FHI drops to 45 (POOR)
- **Action**: Click Filter Health card → shows maintenance band "REPLACE_RECOMMENDED"
- **Action**: Click "Explain" → shows top contributors: flow deviation, cumulative volume, filter age
- **Visual**: Alert banner appears — "Filter Health Critical" with "Acknowledge" button
- **Action**: Click Acknowledge → opens Maintenance workflow with filter catalog
- **Text**: "FILTER_STRESS | FSI: 65 | FHI: 45 | RUL: Model fallback | Alert: Filter Health Critical"
- **Narration**: "Switching to FILTER_STRESS profile: Filter Stress Index rises, Filter Health Index drops to poor, maintenance band recommends replacement. The explainability panel shows exactly why — flow deviation, cumulative volume, and filter age. An alert is generated and can be acknowledged, triggering the maintenance workflow with compatible filter recommendations."

### 0:55-1:10 — LEAK Safety Scenario (15s)
- **Visual**: Terminal — `python simulator.py --profile leak`
- **Visual**: Dashboard — Critical red alert "Leak Detected", sensor card shows leak=true
- **Visual**: Diagnostics page — Leak panel shows CRITICAL status
- **Text**: "LEAK profile | Critical alert | Safety workflow (software-only)"
- **Narration**: "The LEAK profile triggers a critical safety alert. The system identifies the leak sensor activation and presents the safety workflow — note: this is software-only, no physical actuator shutdown."

### 1:10-1:20 — Analytics Credibility (10s)
- **Visual**: Filter Health page — RUL shows "Model fallback (deterministic)", provenance = MODEL_PREDICTED
- **Visual**: Provenance legend — MEASURED, SIMULATED, CALCULATED, MODEL_PREDICTED
- **Text**: "RUL: Deterministic fallback | No trained ML model | Provenance transparency"
- **Narration**: "Critical for credibility: RUL uses a deterministic fallback since no trained ML model exists. Every value shows its provenance — measured, simulated, calculated, or model predicted."

### 1:20-1:30 — Closing (10s)
- **Visual**: Project summary screen
- **Text**: "AquaNexis | UPES Dehradun | Track 2 | atomQUEST 2026"
- **Narration**: "AquaNexis — predictive water intelligence for smarter filter management. Thank you."

---

## Recording Checklist

- [ ] Record at 1920x1080, 30fps
- [ ] Use OBS Studio or similar
- [ ] Record in segments, edit together
- [ ] Add captions for key metrics
- [ ] Compress to <50 MB (H.264, ~2 Mbps)
- [ ] Verify audio clarity
- [ ] Test playback on multiple devices
- [ ] Final filename: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`

---

## Simulator Commands for Recording

```bash
# Terminal 1: Backend (if running with DB)
# Terminal 2: Frontend dev server
# Terminal 3: Simulator

# Normal
python backend/simulator.py --profile normal --interval 5

# Filter Stress
python backend/simulator.py --profile filter_stress --interval 3

# Leak
python backend/simulator.py --profile leak --interval 2
```