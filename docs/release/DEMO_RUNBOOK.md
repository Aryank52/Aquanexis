# AquaNexis — Demonstration Runbook

This guide describes how to run and demonstrate the AquaNexis Predictive Water Intelligence System.

---

## Prerequisites & Architecture

- **Operating System**: Windows / Linux / macOS
- **Backend**: Python 3.12 (FastAPI)
- **Frontend**: Node.js 20+ (React + Vite + TypeScript)
- **Runtime Environment**: `DEMO_MODE=true` (Zero external database or hardware dependencies required)

---

## Quick Start (2 Terminals)

### Terminal 1: Backend Server
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*Health Check*: Navigate to `http://localhost:8000/health` → `{"status": "healthy", "mode": "demo"}`.

### Terminal 2: Frontend Server
```powershell
cd frontend
npm run dev
```
*Access UI*: Open **`http://localhost:3000`** in your browser.

---

## Standard Demonstration Scenarios

Use the **Scenario Switcher** in the top navigation bar or trigger via API:

### 1. NORMAL Operation
- **Condition**: Standard municipal water purification.
- **Indicators**:
  - TDS ~150 ppm, EC ~300 µS/cm, pH ~7.2, Turbidity ~0.3 NTU.
  - AquaScore ~95-100 (EXCELLENT).
  - Filter Health Index ~83% (NORMAL band).
  - Remaining Useful Life ~149 days.
  - Active Alerts: 0.

### 2. FILTER_STRESS Scenario
- **Condition**: Severe membrane fouling and particulate load.
- **Observed System Reaction**:
  - Differential pressure ($\Delta P$) rises to ~180-280 kPa.
  - Product flow rate drops to ~0.85 L/min.
  - Filter Stress Index (FSI) spikes to ~67.5 (HIGH).
  - Filter Health Index (FHI) degrades to ~40% (REPLACE_RECOMMENDED).
  - Automated Alert generated: `filter_stress_high`.
  - Transparent explainability surfaces top 5 contributing factors.

### 3. LEAK Scenario
- **Condition**: High moisture detected at purifier base.
- **Observed System Reaction**:
  - Critical safety alert: `leak_detected_critical`.
  - Fail-safe state triggered: Inlet valve closure command dispatched and logged.
  - Data quality and safety response displayed with audible/visual banner.

### 4. SENSOR_FAULT Scenario
- **Condition**: pH sensor out-of-range / disconnected, erratic electrical conductivity.
- **Observed System Reaction**:
  - Provenance flagged: `Quality: SUSPECT / BAD`.
  - System does NOT generate a falsely confident prediction.
  - Dynamic denominator drops missing sensors from scoring rather than guessing.
  - Maintenance recommendation: Sensor recalibration and inspection.

