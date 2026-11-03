# AquaNexis — Round 2 Progress Report

**Track**: Track 2 — Water Purifier | **Institution**: UPES Dehradun | **Participation**: Solo Prototype | **Date**: 4 November 2026 | **Competition**: atomQUEST 2026

---

## 1. Project & Participant Details

| Field | Value |
|-------|-------|
| **Project Name** | AquaNexis — Predictive Water Intelligence System |
| **Track** | Track 2: Water Purifier |
| **Institution** | UPES Dehradun |
| **Participation Type** | Solo Prototype (Software-Only) |
| **Primary Exploration** | Prognostics of filter failure using data analytics (FSI, FHI, RUL, Failure Risk, Explainability) |
| **Secondary Exploration** | Input water quality sensing beyond TDS (pH, Turbidity, EC, Temperature, Flow, Inlet/Outlet Pressure) |

---

## 2. Problem & Proposed Solution

**Problem**: Conventional water purifiers rely on fixed calendar timers or simple TDS thresholds, causing either premature filter disposal or unexpected membrane failure and unmonitored water quality degradation.

**Solution**: AquaNexis is a **software-only predictive water intelligence platform** that ingests 13-parameter purifier telemetry, validates sensor quality, computes a 7-component Filter Stress Index (FSI) and 5-component Filter Health Index (FHI), estimates Remaining Useful Life (RUL) with explicit model-status disclosure (`MODEL_MISSING` deterministic fallback), classifies failure risk with feature-level evidence, and drives stateful alerts and maintenance workflows. Every metric carries explicit provenance (`SIMULATED`, `CALCULATED`, `MODEL_PREDICTED`, `MEASURED`).

---

## 3. Completed Software Modules & Verification

| Module | Status | Verified Capabilities |
|--------|--------|-----------------------|
| **Telemetry & Quality Gate** | ✅ Complete | FastAPI ingestion, JWT/API-key auth, range/rate/cross-sensor validation (`GOOD`/`SUSPECT`/`BAD`) |
| **Water Quality (Beyond TDS)** | ✅ Complete | AquaScore (0–100), TDS, EC, pH, Turbidity, Temperature sub-scores, 1h slopes, anomaly flags |
| **Filter Stress Index (FSI)** | ✅ Complete | Normalized 7-component weighted model ($\sum w_i = 1.00$); excludes missing sensors from denominator |
| **Filter Health Index (FHI)** | ✅ Complete | 5-component health score (0–100) with maintenance bands (`NORMAL`, `MONITOR`, `REPLACE_RECOMMENDED`) |
| **RUL & Risk Prognostics** | ✅ Complete | Deterministic fallback explicitly labeled `MODEL_MISSING`; withheld (`N/A`) on `SENSOR_FAULT` |
| **Explainability Engine** | ✅ Complete | Feature contribution breakdown ($\Delta P$, flow deviation, volume, age, turbidity) + counterfactuals |
| **Alert State Machine** | ✅ Complete | `DETECTED → OPEN → ACKNOWLEDGED / SNOOZED / RESOLVED / AUTO_CLEARED` with evidence drawer |
| **Maintenance Lifecycle** | ✅ Complete | 11-category filter catalog, compatibility engine, replacement/calibration/verification workflows |
| **Real-Time WebSocket & UI** | ✅ Complete | React 18 + TypeScript dashboard (`http://localhost:3000`), live WebSocket (`/ws/realtime/{id}`) |

---

## 4. Original Sourcing Risks, Scope Change & Budget

| Aspect | Stage 1 Plan | Round 2 Actual Status & Resolution |
|--------|--------------|------------------------------------|
| **Scope** | ESP32 + 13 physical sensors +软件 | **Pivoted to Software-Only Prototype (G6)**; `firmware/esp32/` archived as reference only |
| **Hardware / PCB / Rig** | ₹5,000–₹15,000 estimated | **₹0 actual spend** — no hardware procured; deterministic Python simulator (`simulator.py`) used |
| **TimescaleDB Dependency** | PostgreSQL + TimescaleDB | Local Windows PG16 lacked `timescaledb` DLL; built isolated `DEMO_MODE` runtime while preserving DB code |

---

## 5. Revised Performance Targets & Honest Disclosures

| Target | Round 2 Implementation | Verification & Honest Disclosure |
|--------|------------------------|----------------------------------|
| **Beyond-TDS Sensing** | 13 simulated sensor channels | ✅ **Verified** — TDS, EC, pH, Turbidity, Temp, Flow, Inlet/Outlet Pressure, Tank, Leak, Current, Power, UV |
| **Filter Prognostics (RUL)** | FSI + FHI + Deterministic RUL | ⚠️ **Disclosed** — No trained `.pkl` ML model yet; UI/API explicitly show `MODEL_MISSING (Deterministic Fallback v1.0)` |
| **Real-Time Dashboard** | WebSocket + 5s query freshness | ✅ **Verified** — Live WebSocket broadcasts + stale-data detection at >30s |
| **Safety / Leak Response** | Critical alert + safety audit log | ⚠️ **Disclosed** — **Software alert and audit log only**; no physical valve, relay, or pump actuator exists |
| **Bad Sensor Handling** | Quality gate + confidence guard | ✅ **Verified** — `SENSOR_FAULT` flags `Quality: BAD`, excludes missing sensors, and withholds RUL (`Confidence: LOW`) |

---

## 6. Verified Round 2 Scenario Evidence (`DEMO_MODE=true`)

| Scenario | Verified System Response |
|----------|--------------------------|
| **`NORMAL`** | `Quality=GOOD`, `Provenance=SIMULATED`, `AquaScore=100`, `FSI=20.0`, `FHI=83%`, `RUL=149.4d (MODEL_MISSING)`, `Risk=LOW (13.4%)`, `Alerts=0` |
| **`FILTER_STRESS`** | $\Delta P \approx 280\text{ kPa}$, Flow $\approx 0.85\text{ L/min}$ → `FSI=67.5`, `FHI=40%`, `RUL=72.0d`, `Band=REPLACE_RECOMMENDED`, `Risk=MEDIUM (49.3%)`, Alert `filter_stress_high` (`OPEN` → `ACKNOWLEDGED`), Stage 1 Sediment replacement recommended |
| **`LEAK`** | `leak=true` → Critical manual-only alert `leak_detected` + `SAFETY_SHUTDOWN_RECOMMENDED` software audit log |
| **`SENSOR_FAULT`** | Turbidity `>100 NTU`, TDS/EC mismatch, missing flow/outlet pressure → `Quality=BAD`, `RUL=None (N/A)`, `Confidence=LOW`, `sensor_fault_detected` alert |

---

## 7. Automated Test Results & Round 3 Plan

- **Automated Verification**: Backend unit tests: **133/133 PASS** (`pytest`); Frontend: `npm run typecheck` **PASS**, `npm test -- --run` **14/14 PASS**, `npm run build` **PASS**.
- **Round 3 Plan**: (1) Train Random Forest/XGBoost RUL model on labeled run-to-failure datasets to replace deterministic fallback; (2) Deploy containerized TimescaleDB stack for multi-device fleet persistence; (3) Integrate external purifier telemetry ingestion API with OEM test bench data.

**Declaration**: AquaNexis is submitted as a **software-only prototype**. All telemetry in the demonstration is generated by `backend/simulator.py` (`SIMULATED`), RUL uses a deterministic fallback (`MODEL_MISSING`), and safety responses are software alerts/logs only.
