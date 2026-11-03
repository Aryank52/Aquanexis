# AquaNexis Round 2 Submission — 90-Second Video Script

**Target File**: `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`
**Format**: `.mp4` | **Max Duration**: 90 seconds | **Max Size**: 50 MB
**Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun | **Team**: Solo Prototype

---

## Video Sequence (Total: 90 Seconds)

### 0:00–0:10 — Title, Scope & Core Problem (10s)
- **Screen**: Open `http://localhost:3000/dashboard` showing the live AquaNexis interface and the **`DEMO_MODE (SIMULATED)`** header bar.
- **Narration**: *"Hi, this is AquaNexis from UPES Dehradun for AtomQUEST 2026 Track 2 — Water Purifier. AquaNexis is a software-only Predictive Water Intelligence System focused on filter-failure prognostics and multi-parameter water quality sensing beyond TDS."*

---

### 0:10–0:25 — `NORMAL` Operation & Provenance Transparency (15s)
- **Screen**: Highlight the `NORMAL` scenario active on the Dashboard (`/dashboard`) and Water Quality (`/water-quality`) pages.
  - Point to **`SIMULATED`** provenance badge and **`Quality: GOOD`** on the live sensor telemetry grid (`TDS ~150 ppm`, `EC ~300 µS/cm`, `pH ~7.2`, `Turbidity ~0.3 NTU`, `Inlet Pressure ~300 kPa`, `Outlet Pressure ~270 kPa`, `Flow ~2.0 L/min`).
  - Point to **AquaScore `100/100` (`CALCULATED`)**, **Filter Health `83%` (`FSI 20.0`)**, and **RUL `~149 days`** with the explicit **`MODEL_MISSING (Deterministic Fallback v1.0)`** badge.
- **Narration**: *"Under normal operating conditions, the simulator streams 13 sensor parameters over WebSocket. Every metric carries explicit provenance — SIMULATED for telemetry, CALCULATED for AquaScore, and MODEL_PREDICTED with an explicit MODEL_MISSING disclosure for our deterministic RUL fallback."*

---

### 0:25–0:55 — `FILTER_STRESS` → Prognostics → Explanation → Alert → Maintenance (30s)
- **Screen**:
  1. Click **`FILTER_STRESS`** in the top header bar (or run `python simulator.py --profile filter_stress --interval 2`).
  2. Navigate to **Filter Health** (`/filter-health`):
     - Show $\Delta P$ rising to `~280 kPa` and flow dropping to `~0.85 L/min`.
     - Show **FSI** jumping to **`67.5`**, **FHI** dropping to **`40%`**, **RUL** dropping to **`72.0 days`**, and **Failure Risk** rising to **`MEDIUM (49.3%)`** (`REPLACE_RECOMMENDED`).
     - Scroll to **Feature Contributions & Counterfactuals**: show `Differential Pressure (ΔP)` and `Flow Rate vs Baseline` as top drivers, and the counterfactual showing **`+85 days`** RUL recovery from replacing the Stage 1 Sediment Cartridge.
  3. Navigate to **Alerts** (`/alerts`):
     - Click the active `filter_stress_high` warning alert to show the **Evidence Drawer**, then click **Acknowledge** (`OPEN` → `ACKNOWLEDGED`).
  4. Navigate to **Maintenance** (`/maintenance`):
     - Show the automatically generated **Stage 1 Sediment Filter (`AQX-SED-5M`)** replacement recommendation (`HIGH` priority).
- **Narration**: *"When we switch to FILTER_STRESS, transmembrane pressure differential climbs to 280 kPa and flow drops to 0.85 L/min. Filter Stress Index jumps to 67.5, Filter Health drops to 40%, and RUL falls to 72 days. The explainability engine highlights differential pressure and flow deviation as primary contributors. An explainable alert fires, which we acknowledge, and the maintenance engine recommends replacing the Stage 1 sediment cartridge."*

---

### 0:55–1:15 — `LEAK` Safety Alert & `SENSOR_FAULT` Integrity Guard (20s)
- **Screen**:
  1. Click **`LEAK`** in the top header bar → show the critical red **`CRITICAL: Water Leak Detected (Software Alert)`** banner on `/alerts` and `/diagnostics`.
  2. Click **`SENSOR_FAULT`** in the top header bar → show **`Quality: BAD`** on `/dashboard` and `/filter-health`, where missing pressure/flow sensors are excluded from FSI and RUL displays **`N/A` (`Confidence: LOW`, `MODEL_MISSING — Degraded Confidence`)**.
- **Narration**: *"In the LEAK scenario, AquaNexis raises a manual-only critical software alert and logs a safety shutdown recommendation — disclosed honestly as software-only without physical relay hardware. Finally, under SENSOR_FAULT, bad or missing sensor readings are flagged Quality BAD and RUL is withheld with LOW confidence so corrupt data never becomes a false prediction."*

---

### 1:15–1:30 — Closing & Round 3 Roadmap (15s)
- **Screen**: Return to `/dashboard` and click **`NORMAL`**.
- **Narration**: *"With 133 passing backend unit tests, strict TypeScript build verification, and end-to-end prognostic explainability, AquaNexis is ready for Round 2 evaluation and Round 3 field telemetry training. Thank you."*

---

## Recording & Export Checklist
- [ ] Start backend (`uvicorn app.main:app --port 8000`) and frontend (`npm run dev` on `http://localhost:3000`).
- [ ] Record at `1920x1080` (30 fps), duration **$\le 90$ seconds**, file size **$< 50\text{ MB}$**.
- [ ] Save as `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4`.
