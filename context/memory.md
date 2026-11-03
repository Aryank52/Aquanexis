# AquaNexis Project Memory

## Durable Project Facts (Updated 2026-11-04)

### 1. Product Identity & Scope
- **Project**: AquaNexis — Predictive Water Intelligence System
- **Competition**: AtomQUEST 2026 Round 2 | **Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun | **Type**: Solo Prototype
- **Primary Exploration**: Prognostics of filter failure using data analytics (FSI, FHI, RUL, Failure Risk, Explainability)
- **Secondary Exploration**: Input water quality sensing beyond TDS (TDS, EC, pH, Turbidity, Temperature, Flow, Inlet/Outlet Pressure)
- **Strict Scope**: **Software-only prototype**. Physical purifier hardware, ESP32, sensors, relays, and hydraulic test rigs are **OUT OF SCOPE** (`firmware/esp32/` is archived reference material only).

### 2. Architecture & Runtime Modes
- **Backend**: FastAPI (`http://localhost:8000`) with two clean runtime modes:
  1. **`DEMO_MODE=true` (Default for Round 2 local demo)**: Uses `DemoModeEngine` (`backend/app/infrastructure/demo_mode.py`) backed by the deterministic `SimulatorState` (`backend/simulator.py`) and the real domain analytics/alert services (`QualityValidator`, `WaterQualityService`, `FilterStressService`, `FilterHealthService`, `RULService`, `FailureRiskService`, `HydraulicService`, `PurificationService`, `CompatibilityEngine`).
  2. **PostgreSQL + TimescaleDB Mode (`DEMO_MODE=false`)**: Full SQLAlchemy async persistence with Alembic migrations `0001`–`0008` (requires `timescaledb` extension in PostgreSQL).
- **Frontend**: React 18 + TypeScript + Vite (`http://localhost:3000`) with TanStack Query, live WebSocket updates (`/ws/realtime/{device_id}`), and a top-bar `DEMO_MODE (SIMULATED)` scenario switcher (`NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`).

### 3. Key Technical & Credibility Guarantees
- **FSI Weights**: Normalized to sum to `1.00` (`differential_pressure: 0.25`, `flow_deviation: 0.20`, `turbidity_exposure: 0.15`, `tds_anomaly: 0.10`, `cumulative_volume: 0.10`, `operating_hours: 0.10`, `filter_age: 0.10`). Missing primary sensors (`differential_pressure`, `flow_deviation`) are excluded from `total_weight` rather than scored as a false zero.
- **RUL Honesty (`MODEL_MISSING`)**: No trained `.pkl` ML artifact exists yet. `RULService` reports `status=MODEL_MISSING`, and the UI/API explicitly display `MODEL_MISSING (Deterministic Fallback v1.0)` alongside the deterministic engineering estimate.
- **`SENSOR_FAULT` Guard**: Bad or missing sensor data (`Quality: BAD`) is flagged by `QualityValidator` and withholds RUL prediction (`rul_days = None`, `Confidence: LOW`) so bad telemetry never becomes a confident prediction.
- **Safety Honesty**: `LEAK` triggers a critical software alert (`leak_detected`) and logs `SAFETY_SHUTDOWN_RECOMMENDED` in software; no physical valve or relay actuation is claimed.
