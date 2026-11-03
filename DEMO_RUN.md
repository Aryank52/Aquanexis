# AquaNexis — Round 2 Reproducible Demo Runbook (`DEMO_RUN.md`)

**Event**: AtomQUEST 2026 Round 2 | **Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun
**Primary Exploration**: Prognostics of filter failure using data analytics
**Secondary Exploration**: Input water quality sensing beyond TDS
**Runtime Mode**: `DEMO_MODE=true` (Software-Only Simulator-Backed Prototype — No Physical Hardware or TimescaleDB Required)

---

## Core Demonstration Pipeline

$$\text{Condition Changes} \rightarrow \text{Detection} \rightarrow \text{Filter-Health Intelligence (FSI/FHI)} \rightarrow \text{RUL \& Risk Prediction} \rightarrow \text{Explanation} \rightarrow \text{Alert} \rightarrow \text{Maintenance Action}$$

---

## Step-by-Step 12-Step Demonstration Sequence

### 1. Start Backend (`http://localhost:8000`)
In Terminal 1 (`e:\PROJECTS\Aquanexis\backend`):
```powershell
cd e:\PROJECTS\Aquanexis\backend
# Ensure DEMO_MODE=true in backend/.env (already configured by default)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Verify backend health and readiness:
- Health: `http://localhost:8000/health` → `{"status":"healthy","mode":"demo","demo_mode":true}`
- Readiness: `http://localhost:8000/ready` → `{"status":"ok","checks":{"database":"demo_mode_active (in_memory_simulator)"}}`

---

### 2. Start Frontend (`http://localhost:3000`)
In Terminal 2 (`e:\PROJECTS\Aquanexis\frontend`):
```powershell
cd e:\PROJECTS\Aquanexis\frontend
npm run dev
```
Open **`http://localhost:3000`** in your browser.
- Default demo login credentials (auto-initialized or available at `/login`):
  - **Username**: `admin`
  - **Password**: `password123`

---

### 3. Start Simulator in `NORMAL` Mode
You can drive scenarios either via the **top-bar `DEMO_MODE (SIMULATED)` Scenario Switcher** in the web UI **or** via the CLI simulator in Terminal 3 (`e:\PROJECTS\Aquanexis\backend`):
```powershell
cd e:\PROJECTS\Aquanexis\backend
.\.venv\Scripts\python.exe simulator.py --profile normal --interval 2
```
*(Or click **`NORMAL`** in the top navigation bar).*

---

### 4. Open Dashboard (`http://localhost:3000/dashboard`)
Observe baseline operating conditions:
- **Telemetry Provenance**: `SIMULATED` badge clearly displayed on telemetry cards.
- **Data Quality**: `Quality: GOOD` badge.
- **Water Quality (Beyond TDS)**: AquaScore `~100/100` combining multi-parameter sensing (`TDS ~150 ppm`, `EC ~300 µS/cm`, `pH ~7.2`, `Turbidity ~0.3 NTU`, `Temperature ~22°C`).
- **Filter Health**:
  - **FHI (Filter Health Index)**: `83%` (`GOOD` / `NORMAL` band)
  - **FSI (Filter Stress Index)**: `20.0` (normalized 7-component weighted stress index)
  - **RUL Estimate**: `~149 days` with explicit **`MODEL_MISSING (Deterministic Fallback v1.0)`** disclosure badge
  - **Failure Risk**: `LOW` (`13.4%`)
  - **Active Alerts**: `0`

---

### 5. Switch to `FILTER_STRESS` Scenario
Trigger progressive membrane fouling and sediment clogging:
- **Option A (UI)**: Click **`FILTER_STRESS`** in the top header bar (`DEMO_MODE (SIMULATED)`).
- **Option B (CLI)**:
  ```powershell
  .\.venv\Scripts\python.exe simulator.py --profile filter_stress --interval 2
  ```

---

### 6. Show FSI / FHI / RUL / Failure Risk Response
Navigate to **Filter Health** (`http://localhost:3000/filter-health`) and **Dashboard**:
- **Operational Telemetry Changes**:
  - Differential pressure ($\Delta P = P_{\text{inlet}} - P_{\text{outlet}}$) rises to `~280 kPa` (`inlet ~480 kPa`, `outlet ~200 kPa`).
  - Flow rate drops from `2.0 L/min` baseline to `~0.85 L/min`.
  - Feed turbidity increases (`~2.8 NTU`) and TDS creeps upward (`~285 ppm`).
- **Prognostic Intelligence Response**:
  - **FSI (Filter Stress Index)** jumps from `20.0` to **`67.5`**.
  - **FHI (Filter Health Index)** drops from `83%` to **`40%`**.
  - **RUL (Remaining Useful Life)** drops to **`72.0 days`** (`Confidence: MEDIUM`, `MODEL_MISSING (Deterministic Fallback v1.0)`).
  - **Maintenance Band** shifts to **`REPLACE_RECOMMENDED`**.
  - **Failure Risk** increases to **`MEDIUM (49.3%)`** with 4 structured evidence factors.

---

### 7. Open Feature / Counterfactual Explanation
On **Filter Health** (`http://localhost:3000/filter-health`):
- Inspect **Top Feature Contributors**:
  1. `Differential Pressure (ΔP: ~280.0 kPa)` — primary driver decreasing filter health
  2. `Flow Rate vs 2.0 L/min Baseline (~0.85 L/min)` — flow degradation driver
  3. `Cumulative Volume Processed (8,250 L / 10,000 L rated)`
  4. `Installed Filter Service Age (285 days)`
  5. `Feed Turbidity Load (~2.80 NTU)`
- Inspect **Counterfactual Action Scenarios**:
  - *"Replace Stage 1 Sediment Cartridge (reduces ΔP by ~95 kPa)"* → **`+85 days`** RUL impact
  - *"Flush RO Membrane & restore 2.0 L/min baseline flow"* → **`+42 days`** RUL impact

---

### 8. Show Triggered Alert & Evidence
Navigate to **Alerts** (`http://localhost:3000/alerts`):
- Observe active warning alert: **`High Filter Stress & Membrane Fouling Detected`** (`code: filter_stress_high`, status: `OPEN`, severity: `warning`).
- Click the alert row to open the **Alert Evidence Drawer**, displaying:
  - Trigger value (`FSI = 67.5` vs threshold `60.0`)
  - Structured evidence metrics (`FSI`, `FHI`, `Differential Pressure kPa`)
  - Recommended action and state transition audit history.

---

### 9. Acknowledge Alert
In **Alerts** (`http://localhost:3000/alerts`):
- Click **Acknowledge** on the active `filter_stress_high` alert.
- Verify the alert transitions deterministically from **`OPEN` → `ACKNOWLEDGED`** and records the acknowledgment timestamp and operator note.

---

### 10. Show Maintenance Recommendation
Navigate to **Maintenance** (`http://localhost:3000/maintenance`):
- Observe the dynamically generated **Replacement Recommendation** for **Stage 1 Sediment Filter (`AQX-SED-5M`)** and **RO Membrane (`AQX-RO-75G`)**:
  - **Priority**: `HIGH`
  - **Reason**: Elevated FSI (`67.5`), FHI dropped to `40%` (`REPLACE_RECOMMENDED` band), and $\Delta P > 150\text{ kPa}$.
- You can also inspect the **Filter Catalog** (`/maintenance/filters`), **Calibration** (`/maintenance/calibration`), and **Verification** (`/maintenance/verification`) workflows.

---

### 11. Switch to `LEAK` Scenario
Trigger a simulated hydraulic leak event:
- **Option A (UI)**: Click **`LEAK`** in the top header bar.
- **Option B (CLI)**:
  ```powershell
  .\.venv\Scripts\python.exe simulator.py --profile leak --interval 2
  ```

---

### 12. Show Critical Software Alert & `SENSOR_FAULT` Integrity Guard
1. **`LEAK` Verification**:
   - Navigate to **Alerts** (`/alerts`) and **Diagnostics** (`/diagnostics`).
   - Observe **CRITICAL** software alert: **`CRITICAL: Water Leak Detected (Software Alert)`** (`code: leak_detected`, manual-only resolution — `auto_clear: False`).
   - **Honest Disclosure**: This is a **software alert and safety audit log** (`SAFETY_SHUTDOWN_RECOMMENDED`); there is no physical solenoid valve or relay hardware connected.
2. **`SENSOR_FAULT` Verification (Bonus Step)**:
   - Click **`SENSOR_FAULT`** in the top header bar (or run `python simulator.py --profile sensor_fault --interval 2`).
   - Observe on **Dashboard** (`/dashboard`) and **Filter Health** (`/filter-health`):
     - Telemetry quality changes to **`Quality: BAD`** (turbidity spike `>150 NTU` out of range, TDS/EC cross-sensor ratio mismatch, missing `flow_rate` and `outlet_pressure`).
     - Missing sensors (`differential_pressure`, `flow_deviation`) are **excluded** from FSI weight normalization rather than scored as a false zero.
     - RUL prediction is **withheld (`N/A` / `rul_days: null`)** with **`Confidence: LOW`** and **`MODEL_MISSING (SENSOR_FAULT — Degraded Confidence)`**, ensuring bad sensor data never silently produces a confident prediction.

