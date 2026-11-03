# AquaNexis — Known Limitations & Honest Engineering Disclosures

**Document Version**: 1.0  
**Status**: Active Post-Round 2 Staging  
**Track**: Track 2 — Water Purifier  

AquaNexis operates with high technical integrity. This document transparently lists all boundaries between the currently implemented software system and planned physical deployments.

---

## 1. Physical Edge Hardware Integration

- **Current Status**: 
  - The software architecture, unified telemetry contracts (`backend/app/domain/canonical_telemetry.py`), API ingestion pipelines (`POST /api/v1/telemetry/canonical`), and device security protocols (replay defense, token claims verification) are fully implemented and verified.
  - The actual physical ESP32 microcontroller firmware and physical sensor bench wiring remain in laboratory progress.
  - In demonstration mode, all telemetry is supplied by the deterministic Python simulator or in-memory state engine and is prominently labeled with the **`SIMULATED`** provenance badge.
  - Only physical edge packets bearing verified cryptographic device tokens will be assigned the **`MEASURED`** badge.

## 2. RUL Prognostic Dataset & Model Training

- **Current Status**:
  - The versioned training dataset (`controlled-membrane-deg-v1.0`) is generated using physics-informed degradation equations modeling thin-film composite (TFC) reverse osmosis membranes with non-linear late-life fouling.
  - The candidate multivariate regularized regression model achieves a cross-validated test MAE of 4.85 days with an $R^2$ of 0.9962 against the synthetic controlled experiment dataset.
  - Calibrated uncertainty bounds are set to $\pm 1.96 \times \text{MAE} = \pm 9.5\text{ days}$ for 95% confidence coverage.
  - **Disclosure**: This model has not yet undergone 12-month long-term validation against physical commercial membranes under fluctuating municipal tap water chemistry. Until multi-month empirical run-to-failure field trials complete, predictions retain the deterministic safety boundary and fallback capabilities.

## 3. Actuator Control & Safety Fallback

- **Current Status**:
  - Actuator command endpoints (`close_inlet_valve`, `cut_pump_power`, `flush_membrane`) enforce authorization, idempotency, sequence checks, and audit logging.
  - In the current software demonstration, actuator actions trigger software state transitions and alerts. Physical relay actuation is deferred until complete hardware-in-the-loop (HIL) safety certification is accomplished.
  - Safe default state (normally closed inlet solenoid) is specified in hardware documentation to prevent flooding during power loss.

## 4. Local Database Persistence & TimescaleDB

- **Current Status**:
  - The production database architecture requires PostgreSQL with the TimescaleDB extension for hypertables, compression, and retention policies.
  - In local development environments lacking TimescaleDB, the system operates seamlessly via `DEMO_MODE=true` using an in-memory simulation repository.
  - Continuous Integration (`.github/workflows/integration-e2e.yml`) validates the full Alembic migration chain and TimescaleDB hypertables against a live `timescale/timescaledb:latest-pg16` Docker container.

