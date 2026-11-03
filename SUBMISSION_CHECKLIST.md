# Round 2 Submission Readiness Checklist (`SUBMISSION_CHECKLIST.md`)

**Project**: AquaNexis — Predictive Water Intelligence System
**Track**: Track 2 — Water Purifier
**Institution**: UPES Dehradun
**Participation Type**: Solo Prototype (Software-Only)
**Deadline**: 4 November 2026, 11:59 PM IST

---

## 1. Core End-to-End Scenario Verification (`DEMO_MODE=true`)

| # | Step / Scenario | Status | Verified Output |
|---|-----------------|--------|-----------------|
| 1 | Start FastAPI Backend (`http://localhost:8000`) | ✅ PASS | `/health` → `{"status":"healthy","mode":"demo","demo_mode":true}`, `/ready` → `{"status":"ok"}` |
| 2 | Start React Frontend (`http://localhost:3000`) | ✅ PASS | Vite serving on port 3000; auto-initialized demo session (`admin` / `password123`) |
| 3 | **`NORMAL`** Scenario | ✅ PASS | `Quality: GOOD`, `SIMULATED`, `AquaScore: 100`, `FSI: 20.0`, `FHI: 83%`, `RUL: 149.4d (MODEL_MISSING)`, `Risk: LOW (13.4%)` |
| 4 | **`FILTER_STRESS`** Scenario | ✅ PASS | $\Delta P \approx 280\text{ kPa}$, Flow $\approx 0.85\text{ L/min}$ → `FSI: 67.5`, `FHI: 40%`, `RUL: 72.0d (MODEL_MISSING)`, `Risk: MEDIUM (49.3%)`, `Band: REPLACE_RECOMMENDED` |
| 5 | Feature & Counterfactual Explanation | ✅ PASS | Top 5 contributors ($\Delta P$, flow deviation, volume, age, turbidity) + 2 counterfactual RUL scenarios rendered |
| 6 | Alert Trigger & Acknowledgment | ✅ PASS | `filter_stress_high` warning alert triggered (`OPEN`) → Acknowledged (`ACKNOWLEDGED`) with evidence drawer |
| 7 | Maintenance Recommendation | ✅ PASS | Stage 1 Sediment Filter (`AQX-SED-5M`) replacement recommendation generated (`HIGH` priority) |
| 8 | **`LEAK`** Scenario | ✅ PASS | Critical software alert `leak_detected` (`auto_clear: False`) + software safety audit log |
| 9 | **`SENSOR_FAULT`** Scenario | ✅ PASS | `Quality: BAD` flagged; missing sensors excluded from FSI; RUL withheld (`N/A`, `Confidence: LOW`) |
| 10 | Live WebSocket Streaming | ✅ PASS | `/ws/realtime/00000000-0000-0000-0000-000000000001` delivers real-time `telemetry` and `alert_created` events |

---

## 2. Technical Build & Test Verification

| Component | Command | Result |
|-----------|---------|--------|
| Frontend TypeScript | `npm run typecheck` | ✅ **PASS (0 errors)** |
| Frontend Unit Tests | `npm test -- --run` | ✅ **14/14 PASS** |
| Frontend Production Build | `npm run build` | ✅ **PASS (`dist/` built cleanly)** |
| Backend Unit Tests (No-DB Suite) | `pytest tests/unit/test_config.py tests/unit/test_security.py tests/unit/test_phase_d_services.py tests/unit/test_alert_state_machine.py tests/unit/test_auto_clear_integration.py tests/unit/test_notification_providers.py tests/unit/test_maintenance.py -v` | ✅ **133/133 PASS (1.23s)** |
| Backend DB-Fixture Suite | `pytest tests/unit/test_phase_f_services.py` | ⚠️ **11 fixture errors without local TimescaleDB extension (disclosed)** |

---

## 3. Mandatory Honest Disclosures Verified

- [x] **Software-Only Prototype**: Explicitly disclosed in UI, report, and video script; `firmware/esp32/` is archived out-of-scope reference code.
- [x] **Telemetry Provenance**: All simulator readings carry `SIMULATED` provenance badges.
- [x] **RUL Model Status (`MODEL_MISSING`)**: Explicitly displayed on Dashboard and Filter Health pages (`MODEL_MISSING (Deterministic Fallback v1.0)`).
- [x] **Safety Actions**: Explicitly disclosed as software alerts and audit logs only (no physical solenoid valve, relay, or pump hardware).
- [x] **Runtime Mode**: `DEMO_MODE=true` clearly reported by `/health` and displayed in the top navigation bar.

---

## 4. Submission Package Files

| Required File | Naming Convention | Constraints | Status |
|---------------|-------------------|-------------|--------|
| **Progress Report PDF** | `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf` | `.pdf`, 1–2 pages, $<10\text{ MB}$ | ✅ **GENERATED & VERIFIED (2 pages, ~8 KB)** |
| **Demonstration Video** | `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Video.mp4` | `.mp4`, $\le 90\text{ s}$, $<50\text{ MB}$ | ⏳ **Script & live app ready (`VIDEO_SCRIPT.md`, `DEMO_RUN.md`); participant to record screen** |
| **Portal Upload** | AtomQUEST 2026 Portal | By 4 Nov 2026, 11:59 PM IST | ⏳ **Participant action (never claimed by agent)** |
