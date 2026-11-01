# AquaNexis — Task Checklist

## Current Sprint: Phase D — Water Intelligence + Filter Intelligence (COMPLETE)

### Slice A — Runtime Stability ✅
### Slice B — Telemetry Foundation ✅
### Phase C — Live Dashboard + Alert Lifecycle ✅

## Phase D — Water Intelligence + Filter Intelligence ✅

### Backend (FastAPI)
- [x] **D1** AquaScore algorithm (`app/services/water_quality_service.py`, `app/domain/water_quality.py`)
- [x] **D2** Purification performance (TDS rejection, Recovery) (`app/services/purification_service.py`)
- [x] **D3** Hydraulic intelligence (ΔP, flow deviation, fill-time, reject/permeate ratio) (`app/services/hydraulic_service.py`)
- [x] **D4** Filter Stress Index (deterministic first-layer) (`app/services/filter_stress_service.py`, `app/domain/filter_intelligence.py`)
- [x] **D5** Filter Health Index (0-100) (`app/services/filter_health_service.py`, `app/domain/filter_intelligence.py`)
- [x] **D6** RUL pipeline (Random Forest / XGBoost with fallback) (`app/services/rul_service.py`, `app/domain/filter_intelligence.py`)
- [x] **D7** Failure-risk classification (`app/services/failure_risk_service.py`, `app/domain/filter_intelligence.py`)
- [x] **D8** Explainability (`app/services/rul_service.py`, `app/services/filter_health_service.py`)
- [x] **D9** Data strategy (synthetic vs measured) - documented in domain models
- [x] **D10** ML model registry (`app/services/rul_service.py`, `app/domain/filter_intelligence.py`)
- [x] **D11** Acceptance criteria - tests passing

### Migrations
- [x] 0005_alerts_table.py - Alerts table with indexes

### Domain Models (`app/domain/`)
- [x] `app/domain/filter_intelligence.py` - FilterStressIndex, FilterHealthIndex, RULPrediction, FailureRiskAssessment, FilterStressConfig, FilterHealthConfig, RULConfig
- [x] `app/domain/water_quality.py` - AquaScore, ParameterScore, TrendAnalysis, AnomalyFlag
- [x] `app/domain/filter_intelligence.py` - FilterStressIndex, FilterHealthIndex, RULPrediction, FailureRiskAssessment, PurificationPerformance, HydraulicIntelligence

### Database Models (`app/models/`)
- [x] `app/models/water_quality.py` - WaterQualityScore
- [x] `app/models/filter_health.py` - FilterHealth
- [x] `app/models/purification_performance.py` - PurificationPerformance
- [x] `app/models/system_diagnostics.py` - SystemDiagnostics
- [x] `app/models/__init__.py` - Updated exports

### Services (`app/services/`)
- [x] `app/services/water_quality_service.py` - AquaScore, trends, anomalies
- [x] `app/services/purification_service.py` - Rejection rate, recovery, efficiency
- [x] `app/services/hydraulic_service.py` - Differential pressure, flow deviation, fill time, pressure stability
- [x] `app/services/filter_stress_service.py` - Filter Stress Index (deterministic)
- [x] `app/services/filter_health_service.py` - Filter Health Index
- [x] `app/services/rul_service.py` - RUL prediction with ML fallback
- [x] `app/services/failure_risk_service.py` - Failure risk classification
- [x] `app/services/derivation_service.py` - Background derivation pipeline

### API Endpoints (`app/api/v1/endpoints/`)
- [x] `water_quality.py` - GET /water-quality/current, /history, /trends, /anomalies
- [x] `filter_health.py` - GET /filter-health/{device_id}, /history, /rul, /risk
- [x] `purification_performance.py` - GET /purification-performance/{device_id}/current, /history
- [x] `diagnostics.py` - GET /diagnostics/{device_id}/current, /history, /pressure, /leak

### Schemas (`app/schemas/telemetry.py`)
- [x] AquaScoreResponse, ParameterScore, TrendAnalysis, AnomalyFlag
- [x] FilterHealthResponse, ModelMetadata, ExplanationPayload
- [x] FilterHealthResponse, ModelMetadata, ExplanationPayload

### Tests (All 36 unit tests passing)
- [x] `test_phase_d_services.py` - 13 tests for Phase D services
- [x] `test_config.py` - 14 tests
- [x] `test_security.py` - 9 tests
- [x] `test_config.py` - 14 tests
- [x] `test_security.py` - 9 tests
- Total: 36 tests passing

---

## Next Phase: Phase E — Filter Intelligence Enhancement (or Phase F — Reliability)

### Phase E Requirements (next)
- [ ] **E1** Advanced Filter Intelligence (deeper ML models)
- [ ] **E2** Cross-device learning
- [ ] **E3** Automated maintenance scheduling
- [ ] **E2** Firmware update orchestration

### Phase F Requirements (Reliability)
- [ ] **F1** Leak detection with automatic valve closure
- [ ] **F2** Pressure diagnostics with membrane fouling detection
- [ ] **F3** Pump protection (dry-run, overcurrent)
- [ ] **F3** Sensor failure detection and graceful degradation
- [ ] **F4** System Reliability Score

---

## Notes
- Update this file when tasks are completed or added
- Check off items as done
- Move items between sections as priorities shift
- Reference implementation-plan.md for detailed acceptance criteria