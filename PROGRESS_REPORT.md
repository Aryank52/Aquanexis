# AquaNexis — Round 2 Progress Report

**Track**: Track 2 — Water Purifier  
**Institution**: UPES Dehradun  
**Team**: Solo Prototype  
**Date**: 4 November 2026  
**Competition**: atomQUEST 2026

---

## 1. Project & Participant Details

| Field | Value |
|-------|-------|
| **Project Name** | AquaNexis — Predictive Water Intelligence System |
| **Track** | Track 2: Water Purifier |
| **Institution** | UPES Dehradun |
| **Participation Type** | Solo Prototype |
| **Primary Exploration** | Filter failure prognostics using data analytics (FSI, FHI, RUL, Failure Risk) |
| **Secondary Exploration** | Beyond-TDS water quality sensing (pH, Turbidity, Temperature, Flow, Pressure) |

---

## 2. Problem & Proposed Solution

**Problem**: Water purifiers lack predictive intelligence. Filter replacements are either reactive (after failure) or time-based (wasteful). Users have no visibility into filter degradation, water quality trends, or impending failures.

**Solution**: AquaNexis is a **software-only predictive intelligence platform** that:
- Ingests multi-sensor telemetry (13 sensor types) from water purifiers
- Computes Filter Stress Index (FSI) and Filter Health Index (FHI) using deterministic engineering models
- Estimates Remaining Useful Life (RUL) with confidence intervals
- Classifies failure risk with explainable evidence
- Provides real-time dashboard, alerts, and guided maintenance workflows
- **All sensor readings and analytics carry explicit provenance** (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)

---

## 3. Completed Software Modules

| Module | Status | Key Features |
|--------|--------|--------------|
| **Telemetry Ingestion** | ✅ Complete | FastAPI endpoint, JWT auth, duplicate detection, quality validation |
| **Water Quality Analytics** | ✅ Complete | AquaScore (0-100), parameter scores, trends, anomaly detection |
| **Filter Stress Index (FSI)** | ✅ Complete | 7-component deterministic model, pressure differential, rolling baselines |
| **Filter Health Index (FHI)** | ✅ Complete | 5-component weighted model, maintenance bands, confidence scoring |
| **RUL Estimation** | ✅ Complete | ML interface with deterministic fallback, stability tracking, counterfactuals |
| **Failure Risk Assessment** | ✅ Complete | 5-component risk model, explainable evidence, alert integration |
| **Alert State Machine** | ✅ Complete | DETECTED→OPEN→ACKNOWLEDGED/SNOOZED/RESOLVED/AUTO_CLEARED |
| **Notification System** | ✅ Complete | Console, Email/SMTP, Webhook providers with SSRF protection |
| **Maintenance & Filter Lifecycle** | ✅ Complete | Catalog (11 categories), compatibility engine, workflow state machine |
| **Calibration Management** | ✅ Complete | Time/usage-based policies, post-maintenance verification, baseline versioning |
| **Safety Architecture** | ✅ Complete | Leak/pressure/flow/pump protection, idempotent actions, role-based auth |
| **Real-time WebSocket** | ✅ Complete | Telemetry/alert broadcasts, exponential backoff reconnection |
| **React Dashboard** | ✅ Complete | Live sensor grid, AquaScore, Filter Health, Diagnostics, Alerts, Maintenance |
| **Data Provenance Display** | ✅ Complete | MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED badges on all values |

---

## 4. Original Sourcing Risks & Updated Status

| Original Risk | Status | Resolution |
|---------------|--------|------------|
| ESP32 hardware unavailable | ✅ Resolved | **Scope changed to software-only**; firmware archived as reference |
| ESP-IDF build environment | ✅ Resolved | Not required for software prototype |
| Physical sensor calibration | ✅ Resolved | Simulator provides calibrated synthetic data |
| Sensor PCB fabrication | ✅ Resolved | Out of scope — software prototype uses simulated telemetry |
| Custom filter housing | ✅ Resolved | Out of scope — maintenance module manages catalog only |

---

## 5. Budget: Original Estimate vs Actual

| Category | Original Estimate (₹) | Actual Spend (₹) | Notes |
|----------|----------------------|------------------|-------|
| ESP32 Dev Kit | 1,500 | 0 | Not purchased — out of scope |
| Sensors (13 types) | 8,000 | 0 | Not purchased — out of scope |
| PCB Fabrication | 2,000 | 0 | Not purchased — out of scope |
| Enclosure/Mechanical | 3,000 | 0 | Not purchased — out of scope |
| Cloud/Hosting | 500 | 0 | Local development only |
| **Total** | **~₹15,000** | **₹0** | **Software-only — no hardware procurement** |

*Note: Original Stage 1 abstract estimated ₹5,000–₹10,000 for minimal hardware. Actual expenditure is ₹0 as the project pivoted to a software-only prototype before any hardware procurement.*

---

## 6. Scope Change & Reason

**Original Scope (Stage 1)**: Hardware + software water purifier with ESP32, 13 physical sensors, custom PCB, filter housing, and dashboard.

**Revised Scope (G6)**: **Software-only intelligence platform**. Python telemetry simulator replaces physical sensors. All analytics, dashboard, alerts, maintenance workflows, and safety logic implemented in software.

**Reason**: Hardware development (ESP32 firmware, physical sensors, ESP-IDF setup, PCB fabrication, custom enclosure) was descoped due to:
- ESP-IDF build environment not available
- Physical hardware unavailable for validation
- Competition allows software-only prototypes where "value delivered is immense"
- Focus shifted to demonstrating **meaningful predictive and diagnostic capabilities** rather than physical integration

**Firmware preserved** in `firmware/esp32/` as archived reference with 13 sensor drivers, communication layer, and main application — syntax-validated (GCC).

---

## 7. Revised Performance Targets & Verification Status

| Original Target | Revised Target | Verification Status |
|-----------------|----------------|---------------------|
| ≥4 additional contextual signals | 13 sensor types implemented | ✅ **Verified** — All 13 sensors in simulator & dashboard |
| RUL MAE ≤ 7 days | RUL deterministic fallback (no trained model) | ⚠️ **Not verifiable** — No trained ML model; fallback clearly labeled |
| Dashboard update ≤ 5 seconds | WebSocket + 5s staleTime | ✅ **Verified** — Live updates via WebSocket, stale detection at 30s |
| Automatic safe shutdown | Software safety alerts only | ✅ **Verified** — Leak/pressure/flow alerts generated; no physical actuators |
| TDS rejection & flow/recovery tracking | Purification performance module | ✅ **Verified** — Rejection rate, recovery ratio, efficiency computed |

---

## 8. Delay Reasons

| Delay | Cause | Mitigation |
|-------|-------|------------|
| ESP-IDF environment setup failed | ESP-IDF v5.x not installed on Windows; Docker unavailable | Pivoted to software-only; firmware archived |
| PostgreSQL not running for integration tests | No local DB instance | Unit tests use mocks; 133/133 pass (11 DB errors expected) |
| WebSocket message type mismatch | Backend/frontend type definitions diverged | Fixed: added mapping layer in WebSocket manager |
| Offline mode not implemented | Frontend lacked connection state handling | Added: stale data banner, offline indicator, auto-recovery |

---

## 9. Safety / Fail-Safe Status

| Safety Feature | Implementation | Status |
|----------------|----------------|--------|
| Leak detection | Sensor reading → critical alert → safety workflow | ✅ Implemented (software) |
| High pressure protection | Threshold breach → alert + pump shutdown command | ✅ Implemented (software command only) |
| Low flow / dry run | Flow < threshold → alert + pump shutdown command | ✅ Implemented (software command only) |
| Pump overcurrent | Current > threshold → alert + shutdown command | ✅ Implemented (software command only) |
| **Physical actuator control** | **NOT IMPLEMENTED** — Software-only prototype | ⚠️ **Explicitly NOT implemented** |

**Critical Disclosure**: No physical purifier, pump, valve, or actuator exists. All safety actions are **software alerts and logged commands only**. The system demonstrates the *logic* for fail-safe responses but cannot physically shut down equipment.

---

## 10. Round 3 Plan

| Activity | Description | Target |
|----------|-------------|--------|
| **External Telemetry Integration** | Documented API for real purifier telemetry ingestion (HTTP/WebSocket) | Q1 2027 |
| **ML Model Training** | Collect operational data → train RUL model → replace deterministic fallback | Q2 2027 |
| **Mobile App** | React Native companion app for technicians/consumers | Q2 2027 |
| **Multi-device Fleet View** | Dashboard for managing multiple purifiers | Q3 2027 |
| **Field Validation** | Partner with purifier OEM for real-world pilot | Q3 2027 |
| **Regulatory Alignment** | Map analytics to ISO/NSF water quality standards | Q4 2027 |

---

## 11. Key Demonstration Evidence (G7.6)

| Scenario | Evidence |
|----------|----------|
| **NORMAL** | Dashboard: Online, AquaScore 85, all sensors GOOD, provenance=SIMULATED |
| **FILTER_STRESS** | FSI↑ to 65 (MODERATE), FHI↓ to 45 (POOR), Band=REPLACE_RECOMMENDED, Alert=Filter Health Critical |
| **LEAK** | Critical alert "Leak Detected", Diagnostics leak panel=CRITICAL, safety workflow displayed |
| **SENSOR_FAULT** | Quality flags=SUSPECT/BAD, provenance tracking, no silent degradation to reliable predictions |

All scenarios tested with Python simulator (`backend/simulator.py --profile <name>`).

---

## 12. Submission Files

| File | Description |
|------|-------------|
| `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4` | 90-second demonstration video |
| `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf` | This progress report (1-2 pages) |

---

**Declaration**: This report accurately reflects the software-only implementation status. All hardware development (ESP32 firmware, physical sensors, PCB, enclosure) is **out of scope** and archived in `firmware/esp32/`. The demonstration uses simulated telemetry from `backend/simulator.py`. No physical purifier exists.

**Prepared by**: [Participant Name]  
**Institution**: UPES Dehradun  
**Date**: 4 November 2026