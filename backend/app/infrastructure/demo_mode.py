"""
Isolated DEMO_MODE runtime engine for Round 2 software prototype demonstration.
Uses the real SimulatorState, QualityValidator, WaterQualityService, FilterStressService,
FilterHealthService, RULService, FailureRiskService, HydraulicService, PurificationService,
SafetyService, CompatibilityEngine, and Alert state transition rules without requiring TimescaleDB.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.domain.alerts import ALERT_CODES, ALERT_TRANSITIONS, AlertStatus
from app.domain.devices import Device, DeviceSensorConfig, DeviceStatus, SafetyConfig
from app.domain.quality import QualityState, quality_validator
from app.domain.readings import SensorReading, SensorReadingInput
from app.infrastructure.logging import get_logger
from app.infrastructure.websocket import ws_manager
from app.services.compatibility_engine import CompatibilityEngine
from app.services.failure_risk_service import FailureRiskService
from app.services.filter_health_service import FilterHealthService
from app.services.filter_stress_service import FilterStressService
from app.services.hydraulic_service import HydraulicService
from app.services.purification_service import PurificationService
from app.services.rul_service import RULService
from app.services.safety_service import SafetyService
from app.services.water_quality_service import WaterQualityService
from simulator import SimulationProfile, SimulatorState

logger = get_logger(__name__)

DEFAULT_DEMO_DEVICE_ID = UUID("00000000-0000-0000-0000-000000000001")
MANUAL_ONLY_CODES = {k for k, v in ALERT_CODES.items() if not v.get("auto_clear", True)}
AUTO_CLEAR_CODES = {k for k, v in ALERT_CODES.items() if v.get("auto_clear", True)}


class _AnalyticsReadingAdapter:
    """Adapts a SensorReadingInput into the attribute interface expected by analytics services."""

    def __init__(self, device_id: UUID, timestamp: datetime, reading: SensorReadingInput):
        self.device_id = device_id
        self.timestamp = timestamp
        self.tds = reading.tds
        self.conductivity = reading.conductivity
        self.ec = reading.conductivity
        self.ph = reading.ph
        self.turbidity = reading.turbidity
        self.temperature = reading.temperature
        self.flow_rate = reading.flow_rate
        self.flow = reading.flow_rate
        self.inlet_pressure = reading.inlet_pressure
        self.pressure = reading.inlet_pressure
        self.outlet_pressure = reading.outlet_pressure
        self.tank_level = reading.tank_level
        self.leak = reading.leak
        self.leak_detected = reading.leak
        self.pump_current = reading.pump_current
        self.pump_power = reading.pump_power
        self.uv_state = reading.uv_state
        # Derived permeate / reject approximations for RO purification performance
        if reading.tds is not None:
            self.feed_tds = reading.tds
            self.permeate_tds = round(max(8.0, reading.tds * 0.045), 1)
        else:
            self.feed_tds = None
            self.permeate_tds = None
        if reading.conductivity is not None:
            self.feed_conductivity = reading.conductivity
            self.permeate_conductivity = round(max(16.0, reading.conductivity * 0.045), 1)
        else:
            self.feed_conductivity = None
            self.permeate_conductivity = None
        if reading.flow_rate is not None and reading.flow_rate > 0:
            self.permeate_flow = round(reading.flow_rate * 0.72, 2)
            self.reject_flow = round(reading.flow_rate * 0.28, 2)
        else:
            self.permeate_flow = None
            self.reject_flow = None


class _PayloadWrapper:
    def __init__(self, timestamp: datetime, readings: SensorReadingInput):
        self.timestamp = timestamp
        self.readings = readings


class DemoModeEngine:
    """In-memory simulator-backed repository and real-time analytics orchestrator for DEMO_MODE."""

    def __init__(self) -> None:
        self.water_quality_service = WaterQualityService()
        self.filter_stress_service = FilterStressService()
        self.filter_health_service = FilterHealthService()
        self.rul_service = RULService()
        self.failure_risk_service = FailureRiskService()
        self.hydraulic_service = HydraulicService()
        self.purification_service = PurificationService()
        self.safety_service = SafetyService()
        self.compatibility_engine = CompatibilityEngine()

        self.current_profile: SimulationProfile = SimulationProfile.NORMAL
        self.simulator_state: SimulatorState = SimulatorState(SimulationProfile.NORMAL, seed=42)
        self.domain_device = Device(
            id=DEFAULT_DEMO_DEVICE_ID,
            serial_number="AQX-SIM-0001",
            display_name="Kitchen RO System (Simulator)",
            model="AQUANEXIS_PRO_2",
            firmware_version="1.0.0-sim (DEMO_MODE)",
            status=DeviceStatus.ACTIVE,
            sensor_config=DeviceSensorConfig(),
            safety_config=SafetyConfig(),
            capabilities={"simulator": True, "demo_mode": True, "sensors": 13},
        )

        self.devices: Dict[str, Dict[str, Any]] = {}
        self.telemetry_history: List[Dict[str, Any]] = []
        self.adapter_history: List[_AnalyticsReadingAdapter] = []
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        self.latest_water_quality: Optional[Dict[str, Any]] = None
        self.latest_filter_health: Optional[Dict[str, Any]] = None
        self.latest_failure_risk: Optional[Dict[str, Any]] = None
        self.latest_diagnostics_summary: Optional[Dict[str, Any]] = None
        self.latest_diagnostics_detail: Optional[Dict[str, Any]] = None
        self.latest_purification: Optional[Dict[str, Any]] = None
        self.purification_history: List[Dict[str, Any]] = []
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.safety_events: List[Dict[str, Any]] = []
        self.safety_audit: List[Dict[str, Any]] = []

        # Maintenance, Catalog, Calibration, Verification, Notifications
        self.filter_catalog: Dict[str, Dict[str, Any]] = {}
        self.installed_filters: Dict[str, Dict[str, Any]] = {}
        self.maintenance_events: List[Dict[str, Any]] = []
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.calibrations: List[Dict[str, Any]] = []
        self.verifications: Dict[str, Dict[str, Any]] = {}
        self.recommendations: List[Dict[str, Any]] = []
        self.notifications: List[Dict[str, Any]] = []
        self.notification_providers: Dict[str, Dict[str, Any]] = {}
        self.notification_templates: Dict[str, Dict[str, Any]] = {}

        self._bg_task: Optional[asyncio.Task] = None
        self._external_simulator_until: Optional[datetime] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Seed initial catalog, installed filters, baseline history, and run initial NORMAL cycle."""
        if self._initialized:
            return

        now = datetime.now(timezone.utc)
        dev_id_str = str(DEFAULT_DEMO_DEVICE_ID)

        self.devices[dev_id_str] = {
            "id": dev_id_str,
            "serial_number": "AQX-SIM-0001",
            "name": "Kitchen RO System (Simulator)",
            "display_name": "Kitchen RO System (Simulator)",
            "model": "AQUANEXIS_PRO_2",
            "firmware_version": "1.0.0-sim",
            "sensor_config": self.domain_device.sensor_config.__dict__,
            "calibration": {"tds_slope": 1.0, "ph_offset": 0.0, "turbidity_offset": 0.0},
            "safety_config": self.domain_device.safety_config.__dict__,
            "capabilities": {"simulator": True, "demo_mode": True},
            "status": "online",
            "last_seen": now.isoformat(),
            "last_seen_at": now.isoformat(),
            "created_at": (now - timedelta(days=45)).isoformat(),
            "updated_at": now.isoformat(),
        }

        self._seed_maintenance_and_notifications(now)

        # Generate 18 historical readings over the past 3 hours so trends and sparklines work immediately
        self.simulator_state = SimulatorState(SimulationProfile.NORMAL, seed=42)
        for idx in range(18):
            ts = now - timedelta(minutes=(18 - idx) * 10)
            reading_input = self.simulator_state.generate_reading()
            await self.ingest_reading(
                device_id=DEFAULT_DEMO_DEVICE_ID,
                reading_input=reading_input,
                timestamp=ts,
                broadcast=False,
            )

        self._initialized = True
        logger.info(
            "demo_mode_initialized", device_id=dev_id_str, profile=self.current_profile.value
        )

    def start_background_loop(self) -> None:
        if self._bg_task is None or self._bg_task.done():
            self._bg_task = asyncio.create_task(self._background_ticker())

    async def stop_background_loop(self) -> None:
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass

    async def _background_ticker(self) -> None:
        """Continuously generates simulated readings every 4 seconds unless an external simulator is posting."""
        while True:
            try:
                await asyncio.sleep(4.0)
                now = datetime.now(timezone.utc)
                if self._external_simulator_until and now < self._external_simulator_until:
                    continue
                if self.current_profile == SimulationProfile.DEVICE_OFFLINE:
                    self.devices[str(DEFAULT_DEMO_DEVICE_ID)]["status"] = "offline"
                    continue
                reading_input = self.simulator_state.generate_reading()
                await self.ingest_reading(
                    device_id=DEFAULT_DEMO_DEVICE_ID,
                    reading_input=reading_input,
                    timestamp=now,
                    broadcast=True,
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("demo_background_ticker_error", error=str(e))

    async def set_scenario(
        self, profile_name: str, device_id: UUID = DEFAULT_DEMO_DEVICE_ID
    ) -> Dict[str, Any]:
        """Switch active simulator profile and immediately compute new telemetry, analytics, and alerts."""
        profile = SimulationProfile(profile_name.lower())
        self.current_profile = profile
        self.simulator_state = SimulatorState(profile, seed=101)

        now = datetime.now(timezone.utc)
        dev_id_str = str(device_id)

        if profile == SimulationProfile.DEVICE_OFFLINE:
            if dev_id_str in self.devices:
                self.devices[dev_id_str]["status"] = "offline"
            await ws_manager.broadcast_device_status(device_id, "offline", now)
            return {
                "profile": profile.value,
                "device_id": dev_id_str,
                "status": "offline",
                "timestamp": now.isoformat(),
            }

        # Clear prior scenario history and alerts on scenario switch to isolate demonstration states
        self.alerts.clear()
        self.adapter_history.clear()

        # Seed a short burst of profile readings so trend/exposure/persistence rules respond immediately
        burst_count = 6 if profile == SimulationProfile.FILTER_STRESS else 3
        for i in range(burst_count):
            step_ts = (
                now - timedelta(minutes=(burst_count - 1 - i) * 30)
                if profile == SimulationProfile.FILTER_STRESS
                else now - timedelta(minutes=(burst_count - 1 - i) * 2)
            )
            r_in = self.simulator_state.generate_reading()
            await self.ingest_reading(
                device_id=device_id,
                reading_input=r_in,
                timestamp=step_ts,
                broadcast=(i == burst_count - 1),
            )

        return {
            "profile": profile.value,
            "device_id": dev_id_str,
            "status": self.devices.get(dev_id_str, {}).get("status", "online"),
            "latest_telemetry": self.latest_telemetry,
            "water_quality": self.latest_water_quality,
            "filter_health": self.latest_filter_health,
            "failure_risk": self.latest_failure_risk,
            "active_alerts": [
                a for a in self.alerts.values() if a["status"] in ("OPEN", "ACKNOWLEDGED")
            ],
            "timestamp": now.isoformat(),
        }

    def _detect_profile_from_reading(
        self, reading_input: SensorReadingInput
    ) -> Optional[SimulationProfile]:
        """Detect if an external simulator reading clearly matches LEAK, SENSOR_FAULT, or FILTER_STRESS."""
        if reading_input.leak is True:
            return SimulationProfile.LEAK
        if (
            reading_input.flow_rate is None
            or reading_input.outlet_pressure is None
            or (reading_input.turbidity and reading_input.turbidity > 100)
        ):
            return SimulationProfile.SENSOR_FAULT
        if (
            reading_input.inlet_pressure is not None
            and reading_input.outlet_pressure is not None
            and (reading_input.inlet_pressure - reading_input.outlet_pressure) >= 120
        ):
            return SimulationProfile.FILTER_STRESS
        return None

    async def ingest_reading(
        self,
        device_id: UUID,
        reading_input: SensorReadingInput,
        timestamp: Optional[datetime] = None,
        broadcast: bool = True,
        from_external: bool = False,
    ) -> Dict[str, Any]:
        """Validate, compute all analytics, evaluate alerts/safety, and update in-memory state."""
        now = timestamp or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now_naive = now.replace(tzinfo=None)

        if from_external:
            self._external_simulator_until = datetime.now(timezone.utc) + timedelta(seconds=15)
            inferred = self._detect_profile_from_reading(reading_input)
            if inferred and inferred != self.current_profile:
                self.current_profile = inferred

        # 1. Validate quality using real QualityValidator
        prev_domain_reading = None
        if self.adapter_history and self.current_profile == SimulationProfile.SENSOR_FAULT:
            last_a = self.adapter_history[-1]
            prev_domain_reading = SensorReading(
                id=len(self.adapter_history),
                device_id=device_id,
                timestamp=last_a.timestamp,
                ingestion_timestamp=last_a.timestamp,
                sequence=len(self.adapter_history),
                tds=last_a.tds,
                conductivity=last_a.conductivity,
                ph=last_a.ph,
                turbidity=last_a.turbidity,
                temperature=last_a.temperature,
                flow_rate=last_a.flow_rate,
                inlet_pressure=last_a.inlet_pressure,
                outlet_pressure=last_a.outlet_pressure,
                tank_level=last_a.tank_level,
                leak=bool(last_a.leak),
                pump_current=last_a.pump_current,
                pump_power=last_a.pump_power,
                uv_state=bool(last_a.uv_state),
            )

        q_flags = quality_validator.validate(
            self.domain_device,
            _PayloadWrapper(now_naive, reading_input),
            prev_domain_reading,
        )

        # Map domain QualityFlags to frontend QualityAssessment
        def _map_qstate(qs: QualityState) -> str:
            if qs == QualityState.VALID:
                return "OK"
            if qs == QualityState.SUSPECT:
                return "SUSPECT"
            return "BAD"

        sensor_flag_map: Dict[str, Dict[str, str]] = {}
        has_bad = False
        has_suspect = False
        for s_name, ui_key in [
            ("tds", "tds"),
            ("conductivity", "ec"),
            ("ph", "ph"),
            ("turbidity", "turbidity"),
            ("temperature", "temperature"),
            ("flow_rate", "flow"),
            ("inlet_pressure", "pressure"),
            ("outlet_pressure", "outlet_pressure"),
            ("tank_level", "tank_level"),
            ("pump_current", "pump_current"),
            ("pump_power", "pump_power"),
        ]:
            f_obj = getattr(q_flags, s_name)
            st = _map_qstate(f_obj.state)
            if st == "BAD":
                has_bad = True
            elif st == "SUSPECT":
                has_suspect = True
            msg = (f_obj.message or "").lower()
            sensor_flag_map[ui_key] = {
                "range": st if ("range" in msg or "not provided" in msg or st == "OK") else "OK",
                "rate": st if "rate" in msg else "OK",
                "cross_sensor": st if "ratio" in msg else "OK",
            }

        overall_quality = "BAD" if has_bad else ("SUSPECT" if has_suspect else "GOOD")

        # 2. Build adapter and append to history
        adapter = _AnalyticsReadingAdapter(device_id, now_naive, reading_input)
        self.adapter_history.append(adapter)
        if len(self.adapter_history) > 100:
            self.adapter_history = self.adapter_history[-100:]

        # Build TelemetryReading matching frontend schema
        reading_id = str(uuid4())
        telemetry_obj: Dict[str, Any] = {
            "id": reading_id,
            "device_id": str(device_id),
            "timestamp": now.isoformat(),
            "received_at": now.isoformat(),
            "provenance": "SIMULATED",
            "readings": {
                "tds": round(reading_input.tds, 1) if reading_input.tds is not None else None,
                "ec": round(reading_input.conductivity, 1)
                if reading_input.conductivity is not None
                else None,
                "ph": round(reading_input.ph, 2) if reading_input.ph is not None else None,
                "turbidity": round(reading_input.turbidity, 2)
                if reading_input.turbidity is not None
                else None,
                "temperature": round(reading_input.temperature, 1)
                if reading_input.temperature is not None
                else None,
                "flow": round(reading_input.flow_rate, 2)
                if reading_input.flow_rate is not None
                else None,
                "pressure": round(reading_input.inlet_pressure, 1)
                if reading_input.inlet_pressure is not None
                else None,
                "inlet_pressure": round(reading_input.inlet_pressure, 1)
                if reading_input.inlet_pressure is not None
                else None,
                "outlet_pressure": round(reading_input.outlet_pressure, 1)
                if reading_input.outlet_pressure is not None
                else None,
                "tank_level": round(reading_input.tank_level, 1)
                if reading_input.tank_level is not None
                else None,
                "leak_detected": bool(reading_input.leak),
                "pump_current": round(reading_input.pump_current, 2)
                if reading_input.pump_current is not None
                else None,
                "pump_power": round(reading_input.pump_power, 1)
                if reading_input.pump_power is not None
                else None,
                "permeate_flow": adapter.permeate_flow,
                "reject_flow": adapter.reject_flow,
                "uv_state": bool(reading_input.uv_state),
                "vibration": 0.12,
            },
            "quality": {
                "overall": overall_quality,
                "flags": sensor_flag_map,
            },
        }
        self.latest_telemetry = telemetry_obj
        self.telemetry_history.append(telemetry_obj)
        if len(self.telemetry_history) > 100:
            self.telemetry_history = self.telemetry_history[-100:]

        # Update device status
        dev_str = str(device_id)
        if dev_str in self.devices:
            self.devices[dev_str]["last_seen"] = now.isoformat()
            self.devices[dev_str]["last_seen_at"] = now.isoformat()
            self.devices[dev_str]["status"] = "degraded" if overall_quality != "GOOD" else "online"

        # 3. Compute Water Quality (AquaScore, parameter scores, trends, anomalies)
        aquascore_domain = self.water_quality_service.compute_aquascore(adapter)
        param_units = {
            "tds": "ppm",
            "ph": "pH",
            "turbidity": "NTU",
            "temperature": "°C",
            "conductivity": "µS/cm",
        }
        param_scores = [
            {
                "parameter": ps.parameter,
                "score": int(round(ps.score)),
                "value": round(ps.value, 2) if ps.value is not None else 0.0,
                "unit": param_units.get(ps.parameter, ""),
                "status": ps.status,
            }
            for ps in aquascore_domain.parameter_scores
        ]
        trends_dict: Dict[str, Any] = {}
        for param in ["tds", "ph", "turbidity", "temperature", "conductivity"]:
            pts = [
                {
                    "timestamp": h["timestamp"],
                    "value": h["readings"].get("ec" if param == "conductivity" else param) or 0.0,
                }
                for h in self.telemetry_history[-15:]
                if h["readings"].get("ec" if param == "conductivity" else param) is not None
            ]
            slope = 0.0
            direction = "stable"
            if len(pts) >= 2:
                delta = pts[-1]["value"] - pts[0]["value"]
                slope = round(delta, 2)
                if abs(delta) > (15 if param in ("tds", "conductivity") else 0.3):
                    direction = "degrading" if delta > 0 else "improving"
            trends_dict[param] = {
                "parameter": param,
                "window": "1h",
                "direction": direction,
                "magnitude": abs(slope),
                "points": pts,
                "slope_per_hour": slope,
            }

        anomaly_flags_map: Dict[str, float] = {}
        if overall_quality != "GOOD":
            if reading_input.turbidity and reading_input.turbidity > 10:
                anomaly_flags_map["turbidity"] = round(reading_input.turbidity / 10.0, 2)
            if reading_input.tds and reading_input.tds > 500:
                anomaly_flags_map["tds"] = round((reading_input.tds - 200) / 100.0, 2)

        self.latest_water_quality = {
            "device_id": dev_str,
            "timestamp": now.isoformat(),
            "aquascore": aquascore_domain.overall_score,
            "parameter_scores": param_scores,
            "trends": trends_dict,
            "anomaly_score": max(anomaly_flags_map.values()) if anomaly_flags_map else 0.05,
            "anomaly_flags": anomaly_flags_map,
            "provenance": "CALCULATED",
        }

        # 4. Compute Hydraulic Intelligence & Purification Performance
        hydraulic = self.hydraulic_service.compute_hydraulic_intelligence(
            reading=adapter,
            previous_readings=self.adapter_history[:-1],
            device_baselines={"flow_rate": 2.0, "pressure": 310.0},
        )
        purif_domain = self.purification_service.compute_purification_performance(
            reading=adapter,
            previous_reading=self.adapter_history[-2] if len(self.adapter_history) >= 2 else None,
        )
        rej_frac = (
            (purif_domain.rejection_rate / 100.0)
            if purif_domain and purif_domain.rejection_rate is not None
            else 0.955
        )
        rec_frac = (
            (purif_domain.recovery_ratio / 100.0)
            if purif_domain and purif_domain.recovery_ratio is not None
            else 0.720
        )
        eff_frac = (
            (purif_domain.efficiency / 100.0)
            if purif_domain and purif_domain.efficiency is not None
            else round(rej_frac * rec_frac, 3)
        )
        self.latest_purification = {
            "device_id": dev_str,
            "timestamp": now.isoformat(),
            "rejection_rate": round(rej_frac, 3),
            "recovery_ratio": round(rec_frac, 3),
            "permeate_quality": round(purif_domain.permeate_quality, 1)
            if purif_domain and purif_domain.permeate_quality is not None
            else 12.0,
            "feed_quality": round(purif_domain.feed_quality, 1)
            if purif_domain and purif_domain.feed_quality is not None
            else float(reading_input.tds or 160.0),
            "efficiency": round(eff_frac, 3),
        }
        self.purification_history.append(self.latest_purification)
        if len(self.purification_history) > 50:
            self.purification_history = self.purification_history[-50:]

        # 5. Compute Filter Stress (FSI), Filter Health (FHI), RUL, and Failure Risk
        is_stressed = self.current_profile in (
            SimulationProfile.FILTER_STRESS,
            SimulationProfile.HIGH_PRESSURE_DROP,
            SimulationProfile.LOW_FLOW,
            SimulationProfile.HIGH_TURBIDITY,
        )
        install_date = now_naive - timedelta(days=285 if is_stressed else 42)
        cum_volume = 8250.0 if is_stressed else 820.0
        op_hours = 1850.0 if is_stressed else 210.0

        fsi_domain = await self.filter_stress_service.compute_filter_stress(
            reading=adapter,
            previous_readings=self.adapter_history[:-1],
            filter_install_date=install_date,
            cumulative_volume=cum_volume,
            operating_hours=op_hours,
        )
        fhi_domain = self.filter_health_service.compute_filter_health(
            filter_stress=fsi_domain,
            filter_install_date=install_date,
            cumulative_volume=cum_volume,
            operating_hours=op_hours,
            hydraulic_intelligence=hydraulic,
        )
        rul_domain = self.rul_service.predict_rul(
            filter_stress=fsi_domain,
            filter_health=fhi_domain,
            hydraulic_intelligence=hydraulic,
            purification_performance=purif_domain,
        )
        risk_domain = self.failure_risk_service.assess_risk(
            filter_stress=fsi_domain,
            filter_health=fhi_domain,
            rul_prediction=rul_domain,
            recent_anomalies=[],
            alert_history=list(self.alerts.values()),
        )

        # Build Explainable Contributors
        dp_val = fsi_domain.pressure_differential_kpa
        flow_val = reading_input.flow_rate
        top_contributors = [
            {
                "feature": "differential_pressure_kpa",
                "contribution": round((fsi_domain.differential_pressure_score or 0.0) / 100.0, 2),
                "direction": "decreases"
                if (fsi_domain.differential_pressure_score or 0) > 25
                else "increases",
                "label": f"Differential Pressure (ΔP: {dp_val:.1f} kPa)"
                if dp_val is not None
                else "Differential Pressure (SENSOR MISSING — excluded)",
            },
            {
                "feature": "flow_deviation_pct",
                "contribution": round((fsi_domain.flow_deviation_score or 0.0) / 100.0, 2),
                "direction": "decreases"
                if (fsi_domain.flow_deviation_score or 0) > 25
                else "increases",
                "label": f"Flow Rate vs 2.0 L/min Baseline ({flow_val:.2f} L/min)"
                if flow_val is not None
                else "Flow Rate (SENSOR MISSING — excluded)",
            },
            {
                "feature": "cumulative_volume_liters",
                "contribution": round((fsi_domain.cumulative_volume_score or 0.0) / 100.0, 2),
                "direction": "decreases" if cum_volume > 3000 else "increases",
                "label": f"Cumulative Volume Processed ({cum_volume:,.0f} L / 10,000 L rated)",
            },
            {
                "feature": "filter_age_days",
                "contribution": round((fsi_domain.filter_age_score or 0.0) / 100.0, 2),
                "direction": "decreases" if is_stressed else "increases",
                "label": f"Installed Filter Service Age ({(now_naive - install_date).days} days)",
            },
            {
                "feature": "turbidity_ntu",
                "contribution": round(min(1.0, (reading_input.turbidity or 0.0) / 10.0), 2),
                "direction": "decreases" if (reading_input.turbidity or 0) > 1.5 else "increases",
                "label": f"Feed Turbidity Load ({reading_input.turbidity:.2f} NTU)"
                if reading_input.turbidity is not None
                else "Feed Turbidity Load",
            },
        ]

        # Enforce SENSOR_FAULT rule: bad/missing sensor data NEVER becomes a confident prediction
        if overall_quality != "GOOD" or self.current_profile == SimulationProfile.SENSOR_FAULT:
            pred_confidence = "LOW"
            model_display_name = "MODEL_MISSING (SENSOR_FAULT — Degraded Confidence)"
            maint_band = "MONITOR"
            deterministic_rul_days = None
            rul_lower = None
            rul_upper = None
        else:
            pred_confidence = "MEDIUM" if is_stressed else "HIGH"
            # RULService returns status=MODEL_MISSING (no trained .pkl model artifact);
            # We expose both the explicit MODEL_MISSING status in model_name and the deterministic engineering estimate
            model_display_name = (
                f"MODEL_MISSING (Deterministic Fallback v{rul_domain.model_version})"
            )
            maint_band = (
                "NORMAL"
                if fhi_domain.health_score >= 75
                else (fhi_domain.maintenance_band or "normal").upper()
            )
            # Deterministic engineering fallback estimate from FHI & lifecycle
            deterministic_rul_days = round(max(5.0, (fhi_domain.health_score / 100.0) * 180.0), 1)
            rul_lower = round(max(1.0, deterministic_rul_days * 0.75), 1)
            rul_upper = round(deterministic_rul_days * 1.25, 1)

        self.latest_filter_health = {
            "device_id": dev_str,
            "timestamp": now.isoformat(),
            "fsi": fsi_domain.score,
            "fhi": fhi_domain.health_score,
            "rul_days": deterministic_rul_days,
            "rul_status": rul_domain.status.value.upper(),
            "rul_confidence_lower": rul_lower,
            "rul_confidence_upper": rul_upper,
            "model_name": model_display_name,
            "model_version": rul_domain.model_version,
            "dataset_version": "deterministic-engineering-v1 (no trained ML artifact)",
            "input_features": {
                "fsi_score": fsi_domain.score,
                "differential_pressure_kpa": dp_val or 0.0,
                "flow_rate_lpm": flow_val or 0.0,
                "cumulative_volume_liters": cum_volume,
                "operating_hours": op_hours,
                "turbidity_ntu": reading_input.turbidity or 0.0,
            },
            "explanation": {
                "top_contributors": top_contributors,
                "model_info": {
                    "name": model_display_name,
                    "version": rul_domain.model_version,
                },
                "counterfactual": {
                    "scenarios": [
                        {
                            "description": "Replace Stage 1 Sediment Cartridge (reduces ΔP by ~95 kPa)",
                            "rul_change_days": 85,
                            "confidence": "MEDIUM",
                        },
                        {
                            "description": "Flush RO Membrane & restore 2.0 L/min baseline flow",
                            "rul_change_days": 42,
                            "confidence": "MEDIUM",
                        },
                    ]
                },
            },
            "maintenance_band": maint_band,
            "confidence_level": pred_confidence,
            "provenance": "MODEL_PREDICTED",
        }

        # Failure risk assessment
        risk_evidence_list = [
            {
                "factor": "Filter Stress Index (FSI)",
                "value": round(fsi_domain.score, 1),
                "threshold": 70.0,
                "severity": "high"
                if fsi_domain.score >= 70
                else ("medium" if fsi_domain.score >= 40 else "low"),
                "description": f"7-component weighted stress index ({fsi_domain.state.value.upper()})",
            },
            {
                "factor": "Filter Health Index (FHI)",
                "value": float(fhi_domain.health_score),
                "threshold": 50.0,
                "severity": "high"
                if fhi_domain.health_score < 40
                else ("medium" if fhi_domain.health_score < 70 else "low"),
                "description": f"Composite health score ({fhi_domain.state.value.upper()})",
            },
            {
                "factor": "Differential Pressure (ΔP)",
                "value": round(dp_val, 1) if dp_val is not None else 0.0,
                "threshold": 150.0,
                "severity": "high"
                if (dp_val or 0) >= 150
                else ("medium" if (dp_val or 0) >= 80 else "low"),
                "description": "Trans-filter pressure drop across sediment/RO stages (kPa)"
                if dp_val is not None
                else "Missing outlet pressure sensor — ΔP unavailable",
            },
            {
                "factor": "Data Quality & Sensor Integrity",
                "value": 100.0 if overall_quality == "GOOD" else 25.0,
                "threshold": 80.0,
                "severity": "low" if overall_quality == "GOOD" else "high",
                "description": f"Overall telemetry quality state: {overall_quality}",
            },
        ]
        self.latest_failure_risk = {
            "device_id": dev_str,
            "risk_level": risk_domain.risk_level.value.upper(),
            "risk_score": round(risk_domain.risk_score, 1),
            "evidence": risk_evidence_list,
            "maintenance_band": maint_band,
        }

        # 6. Compute Diagnostics (summary for Dashboard + detailed for DiagnosticsPage)
        inlet_p = reading_input.inlet_pressure or 0.0
        flow_lpm = reading_input.flow_rate or 0.0
        leak_flag = bool(reading_input.leak)
        tank_pct = reading_input.tank_level or 75.0
        pump_curr = reading_input.pump_current or 1.0
        pump_pwr = reading_input.pump_power or 240.0

        self.latest_diagnostics_summary = {
            "device_id": dev_str,
            "timestamp": now.isoformat(),
            "pressure": round(inlet_p, 1) if reading_input.inlet_pressure is not None else None,
            "flow": round(flow_lpm, 2) if reading_input.flow_rate is not None else None,
            "leak": leak_flag,
            "tank": round(tank_pct, 1),
            "pump": round(pump_curr, 2),
        }

        fouling_idx = round(min(1.0, max(0.0, ((dp_val or 20.0) - 25.0) / 175.0)), 2)
        self.latest_diagnostics_detail = {
            "device_id": dev_str,
            "timestamp": now.isoformat(),
            "pressure": {
                "current_kpa": round(inlet_p, 1),
                "trend_1h": 14.5 if is_stressed else (-42.0 if leak_flag else 0.4),
                "trend_24h": 68.0 if is_stressed else 1.2,
                "fouling_indicator": fouling_idx,
                "status": "critical"
                if (inlet_p > 550 or (dp_val or 0) > 160 or leak_flag)
                else ("elevated" if is_stressed else "normal"),
            },
            "flow": {
                "current_lpm": round(flow_lpm, 2),
                "recovery_ratio": self.latest_purification["recovery_ratio"] or 0.72,
                "permeate_lpm": adapter.permeate_flow or 0.0,
                "reject_lpm": adapter.reject_flow or 0.0,
                "trend_1h": -0.35 if is_stressed else 0.02,
                "status": "critical"
                if reading_input.flow_rate is None
                else ("low" if flow_lpm < 1.2 else "normal"),
            },
            "leak": {
                "detected": leak_flag,
                "probability": 0.96 if leak_flag else 0.01,
                "sensor_status": "FAULT" if overall_quality == "BAD" else "OK",
                "flow_delta_lpm": 0.72 if leak_flag else 0.0,
                "pressure_drop_kpa": 95.0 if leak_flag else 0.0,
                "status": "confirmed" if leak_flag else "dry",
            },
            "tank": {
                "level_percent": round(tank_pct, 1),
                "fill_rate_lpm": round((adapter.permeate_flow or 1.4), 2),
                "empty_rate_lpm": 0.85 if leak_flag else 0.25,
                "stagnation_hours": 0.0,
                "status": "low" if tank_pct < 25 else "normal",
            },
            "pump": {
                "current_a": round(pump_curr, 2),
                "power_w": round(pump_pwr, 1),
                "efficiency_trend_7d": -6.4 if is_stressed else -0.5,
                "runtime_hours": op_hours,
                "start_count": int(op_hours * 1.8),
                "status": "degraded" if is_stressed else "normal",
            },
        }

        # 7. Evaluate Alerts & Safety Protection
        await self._evaluate_alerts_and_safety(
            device_id=device_id,
            now=now,
            reading_input=reading_input,
            fsi_score=fsi_domain.score,
            fhi_score=fhi_domain.health_score,
            dp_val=dp_val,
            overall_quality=overall_quality,
            broadcast=broadcast,
        )

        # 8. Broadcast live telemetry over WebSocket
        if broadcast:
            await ws_manager.broadcast(
                device_id,
                {
                    "type": "telemetry",
                    "device_id": dev_str,
                    "timestamp": now.isoformat(),
                    "data": telemetry_obj,
                },
            )

        return {
            "accepted": True,
            "reading_id": len(self.telemetry_history),
            "quality": overall_quality.lower(),
            "derived": {
                "aquascore": aquascore_domain.overall_score,
                "fsi": fsi_domain.score,
                "fhi": fhi_domain.health_score,
                "maintenance_band": maint_band,
            },
        }

    async def _evaluate_alerts_and_safety(
        self,
        device_id: UUID,
        now: datetime,
        reading_input: SensorReadingInput,
        fsi_score: float,
        fhi_score: int,
        dp_val: Optional[float],
        overall_quality: str,
        broadcast: bool,
    ) -> None:
        dev_str = str(device_id)

        # Helper to upsert an active alert by code
        async def _trigger_alert(
            code: str,
            severity: str,
            title: str,
            message: str,
            trigger_source: str,
            trigger_val: float,
            threshold_val: float,
            evidence: Dict[str, Any],
        ) -> None:
            for existing in self.alerts.values():
                if existing["alert_code"] == code and existing["status"] in (
                    "OPEN",
                    "ACKNOWLEDGED",
                    "SNOOZED",
                ):
                    existing["trigger_value"] = trigger_val
                    existing["evidence"] = evidence
                    return

            alert_id = str(uuid4())
            alert_obj = {
                "id": alert_id,
                "device_id": dev_str,
                "alert_code": code,
                "severity": severity,
                "status": "OPEN",
                "title": title,
                "message": message,
                "trigger_source": trigger_source,
                "trigger_value": trigger_val,
                "threshold_value": threshold_val,
                "evidence": evidence,
                "created_at": now.isoformat(),
                "acknowledged_at": None,
                "acknowledged_by": None,
                "resolved_at": None,
                "resolved_by": None,
                "resolved_reason": None,
                "snoozed_until": None,
                "auto_cleared_at": None,
                "created_by": "analytics_engine",
            }
            self.alerts[alert_id] = alert_obj

            # Add corresponding notification to outbox
            self.notifications.insert(
                0,
                {
                    "id": str(uuid4()),
                    "alert_id": alert_id,
                    "device_id": dev_str,
                    "channel": "email",
                    "provider": "console",
                    "recipient": "operator@aquanexis.local",
                    "subject": f"[{severity}] {title}",
                    "body": message,
                    "template_name": "default_alert",
                    "template_data": {"code": code, "severity": severity},
                    "dedupe_key": f"{dev_str}:{code}:{alert_id[:8]}",
                    "status": "sent",
                    "error_category": None,
                    "last_error": None,
                    "attempt_count": 1,
                    "max_attempts": 3,
                    "next_attempt_at": None,
                    "created_at": now.isoformat(),
                    "sent_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                },
            )

            if broadcast:
                await ws_manager.broadcast_alert(device_id, alert_obj, event_type="alert.created")

        # Helper to auto-clear self-clearing alerts when condition resolves
        async def _auto_clear(code: str) -> None:
            if code in MANUAL_ONLY_CODES:
                return
            for existing in self.alerts.values():
                if existing["alert_code"] == code and existing["status"] in (
                    "OPEN",
                    "ACKNOWLEDGED",
                    "SNOOZED",
                ):
                    existing["status"] = "AUTO_CLEARED"
                    existing["auto_cleared_at"] = now.isoformat()
                    existing["resolved_at"] = now.isoformat()
                    existing["resolved_reason"] = (
                        "Condition returned to normal thresholds (auto-cleared)"
                    )
                    if broadcast:
                        await ws_manager.broadcast_alert(
                            device_id, existing, event_type="alert.auto_cleared"
                        )

        # Condition 1: LEAK (Critical safety event — manual-only resolution)
        if reading_input.leak:
            leak_ev = {
                "leak_sensor_contact": True,
                "inlet_pressure_kpa": reading_input.inlet_pressure,
                "pressure_drop_kpa": 95.0,
                "flow_surge_lpm": reading_input.flow_rate,
                "software_protection_action": "close_inlet_valve (SIMULATED command logged — no physical actuator)",
                "provenance": "SIMULATED",
            }
            await _trigger_alert(
                code="leak_detected",
                severity="CRITICAL",
                title="CRITICAL SAFETY ALERT: Confirmed Water Leak Detected",
                message=(
                    "Contact leak sensor triggered with correlated line pressure drop (-95 kPa) "
                    "and abnormal flow rate. Software safety action 'close_inlet_valve' logged "
                    "(software-only prototype — no physical valve actuator connected)."
                ),
                trigger_source="SafetyService / LeakProtectionService",
                trigger_val=1.0,
                threshold_val=0.0,
                evidence=leak_ev,
            )
            self.safety_events.insert(
                0,
                {
                    "id": str(uuid4()),
                    "device_id": dev_str,
                    "event_type": "leak_detected",
                    "action_taken": "close_inlet_valve",
                    "simulated": True,
                    "disclosure": "Software command logged only; no physical relay or valve exists.",
                    "evidence": leak_ev,
                    "timestamp": now.isoformat(),
                },
            )
        else:
            # Note: leak_detected is in MANUAL_ONLY_CODES, so _auto_clear will intentionally not clear it!
            await _auto_clear("leak_detected")

        # Condition 2: FILTER_STRESS / Fouling
        if fsi_score >= 55.0 or fhi_score <= 45:
            stress_ev = {
                "fsi_score": fsi_score,
                "fhi_score": fhi_score,
                "differential_pressure_kpa": dp_val,
                "flow_rate_lpm": reading_input.flow_rate,
                "maintenance_band": "REPLACE_RECOMMENDED",
                "recommended_filter": "AQX-SED-01 (Stage 1 Sediment) & AQX-RO-75G (Stage 3 RO Membrane)",
                "provenance": "MODEL_PREDICTED",
            }
            await _trigger_alert(
                code="filter_stress_high",
                severity="WARNING" if fhi_score >= 30 else "CRITICAL",
                title="Filter Fouling & High Stress Detected — Replacement Recommended",
                message=(
                    f"Filter Stress Index rose to {fsi_score:.1f} (HIGH) and Filter Health Index dropped "
                    f"to {fhi_score} (REPLACE_RECOMMENDED). Differential pressure is {dp_val or 0:.1f} kPa "
                    f"with flow restricted to {reading_input.flow_rate or 0:.2f} L/min."
                ),
                trigger_source="FilterStressService / FilterHealthService",
                trigger_val=round(fsi_score, 1),
                threshold_val=55.0,
                evidence=stress_ev,
            )
            # Ensure a maintenance recommendation exists
            if not any(
                r["trigger"] == "FILTER_STRESS_HIGH" and r["acknowledged_at"] is None
                for r in self.recommendations
            ):
                self.recommendations.insert(
                    0,
                    {
                        "id": str(uuid4()),
                        "device_id": dev_str,
                        "filter_instance_id": next(iter(self.installed_filters.keys()), None),
                        "trigger": "FILTER_STRESS_HIGH",
                        "severity": "HIGH",
                        "evidence": stress_ev,
                        "urgency_days": 7,
                        "recommended_action": (
                            "Replace Stage 1 Polypropylene Sediment Filter (AQX-SED-01) and inspect Stage 3 "
                            "RO Membrane (AQX-RO-75G). Differential pressure exceeded 160 kPa with >50% flow loss."
                        ),
                        "acknowledged_at": None,
                        "dismissed_at": None,
                        "created_at": now.isoformat(),
                    },
                )
        else:
            await _auto_clear("filter_stress_high")

        # Condition 3: SENSOR_FAULT / Bad data quality
        if overall_quality != "GOOD":
            fault_ev = {
                "overall_quality": overall_quality,
                "turbidity_ntu": reading_input.turbidity,
                "tds_ppm": reading_input.tds,
                "conductivity_us_cm": reading_input.conductivity,
                "missing_sensors": [
                    k
                    for k, v in [
                        ("flow_rate", reading_input.flow_rate),
                        ("outlet_pressure", reading_input.outlet_pressure),
                    ]
                    if v is None
                ],
                "prediction_impact": "Confidence downgraded to LOW; RUL prediction suppressed to prevent false confidence.",
                "provenance": "SIMULATED",
            }
            await _trigger_alert(
                code="sensor_fault_detected",
                severity="WARNING",
                title="Sensor Data Quality Fault — Prediction Confidence Degraded",
                message=(
                    "QualityValidator flagged BAD/SUSPECT telemetry: Turbidity out-of-range (>100 NTU), "
                    "TDS/Conductivity cross-sensor ratio mismatch, and missing Flow/Outlet Pressure channels. "
                    "Prognostic confidence downgraded to LOW."
                ),
                trigger_source="QualityValidator",
                trigger_val=round(reading_input.turbidity or 142.5, 1),
                threshold_val=100.0,
                evidence=fault_ev,
            )
        else:
            await _auto_clear("sensor_fault_detected")

    def transition_alert(
        self,
        alert_id: str,
        target_status: str,
        actor: str,
        reason: Optional[str] = None,
        snooze_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Enforce AlertStateMachine transitions on in-memory alerts."""
        alert = self.alerts.get(alert_id)
        if not alert:
            raise KeyError(f"Alert {alert_id} not found")

        current_enum = AlertStatus(alert["status"].lower())
        target_enum = AlertStatus(target_status.lower())
        allowed = ALERT_TRANSITIONS.get(current_enum, [])
        if target_enum not in allowed and current_enum != target_enum:
            raise ValueError(f"Invalid transition from {current_enum.value} to {target_enum.value}")

        now = datetime.now(timezone.utc)
        alert["status"] = target_enum.value.upper()
        if target_enum == AlertStatus.ACKNOWLEDGED:
            alert["acknowledged_at"] = now.isoformat()
            alert["acknowledged_by"] = actor
        elif target_enum == AlertStatus.RESOLVED:
            alert["resolved_at"] = now.isoformat()
            alert["resolved_by"] = actor
            alert["resolved_reason"] = reason or "Resolved by operator"
        elif target_enum == AlertStatus.SNOOZED:
            mins = snooze_minutes or 30
            alert["snoozed_until"] = (now + timedelta(minutes=mins)).isoformat()

        return alert

    def _seed_maintenance_and_notifications(self, now: datetime) -> None:
        dev_str = str(DEFAULT_DEMO_DEVICE_ID)
        catalog_entries = [
            {
                "id": "cat-sed-001",
                "filter_identifier": "AQX-SED-01",
                "manufacturer": "AquaNexis Filtration",
                "product_name": "Stage 1 — 5µm Spun Polypropylene Sediment Cartridge",
                "category": "SEDIMENT",
                "purifier_compatibility": [
                    "AQUANEXIS_HOME_1",
                    "AQUANEXIS_PRO_2",
                    "AQUANEXIS_UV_3",
                    "AquaNexis-SIM",
                ],
                "stage_position": 1,
                "specifications": {"micron_rating": 5.0, "max_pressure_kpa": 600},
                "connector_details": "1/4 inch Quick-Connect",
                "dimensions_mm": {"length": 254, "diameter": 63},
                "rated_service_interval_days": 180,
                "rated_usage_volume_liters": 6000,
                "installation_requirements": "Flush for 5 minutes prior to connecting Stage 2.",
                "maintenance_instructions": "Replace when ΔP exceeds 120 kPa or every 6 months.",
                "datasheet_reference": "AQX-DS-SED01",
                "is_active": True,
                "created_at": (now - timedelta(days=90)).isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": "cat-pre-002",
                "filter_identifier": "AQX-CB-02",
                "manufacturer": "AquaNexis Filtration",
                "product_name": "Stage 2 — Activated Coconut Shell Carbon Block",
                "category": "CARBON",
                "purifier_compatibility": [
                    "AQUANEXIS_HOME_1",
                    "AQUANEXIS_PRO_2",
                    "AQUANEXIS_UV_3",
                    "AquaNexis-SIM",
                ],
                "stage_position": 2,
                "specifications": {"chlorine_reduction_pct": 99.0, "micron_rating": 1.0},
                "connector_details": "1/4 inch Quick-Connect",
                "dimensions_mm": {"length": 254, "diameter": 63},
                "rated_service_interval_days": 270,
                "rated_usage_volume_liters": 8000,
                "installation_requirements": "Flush carbon fines until effluent runs clear.",
                "maintenance_instructions": "Replace every 9 months or 8,000 L.",
                "datasheet_reference": "AQX-DS-CB02",
                "is_active": True,
                "created_at": (now - timedelta(days=90)).isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": "cat-ro-003",
                "filter_identifier": "AQX-RO-75G",
                "manufacturer": "AquaNexis Membrane Tech",
                "product_name": "Stage 3 — High-Rejection Thin-Film Composite RO Membrane (75 GPD)",
                "category": "RO_MEMBRANE",
                "purifier_compatibility": ["AQUANEXIS_HOME_1", "AQUANEXIS_PRO_2", "AquaNexis-SIM"],
                "stage_position": 3,
                "specifications": {"rated_rejection_pct": 96.5, "capacity_gpd": 75},
                "connector_details": "1812 RO Housing Standard",
                "dimensions_mm": {"length": 298, "diameter": 45},
                "rated_service_interval_days": 365,
                "rated_usage_volume_liters": 10000,
                "installation_requirements": "Discard first 2 tank fills after membrane installation.",
                "maintenance_instructions": "Replace when TDS rejection drops below 88% or FHI < 35.",
                "datasheet_reference": "AQX-DS-RO75",
                "is_active": True,
                "created_at": (now - timedelta(days=90)).isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": "cat-post-004",
                "filter_identifier": "AQX-MIN-04",
                "manufacturer": "AquaNexis Filtration",
                "product_name": "Stage 4 — Post-Carbon & Remineralization Polishing Cartridge",
                "category": "POST_CARBON",
                "purifier_compatibility": ["AQUANEXIS_PRO_2", "AquaNexis-SIM"],
                "stage_position": 4,
                "specifications": {"ph_boost": 0.4},
                "connector_details": "1/4 inch Inline Quick-Connect",
                "dimensions_mm": {"length": 254, "diameter": 50},
                "rated_service_interval_days": 365,
                "rated_usage_volume_liters": 10000,
                "installation_requirements": "Install downstream of storage tank.",
                "maintenance_instructions": "Replace annually.",
                "datasheet_reference": "AQX-DS-MIN04",
                "is_active": True,
                "created_at": (now - timedelta(days=90)).isoformat(),
                "updated_at": now.isoformat(),
            },
        ]
        for c in catalog_entries:
            self.filter_catalog[c["id"]] = c

        for idx, c in enumerate(catalog_entries, start=1):
            inst_id = f"inst-stage-{idx}"
            self.installed_filters[inst_id] = {
                "id": inst_id,
                "device_id": dev_str,
                "catalog_id": c["id"],
                "stage_position": idx,
                "installer": "UPES Lab Commissioning",
                "serial_number": f"SN-AQX-2026-0{idx}",
                "batch_identifier": "BATCH-2026-Q3",
                "lifecycle_state": "ACTIVE",
                "cumulative_volume_liters": 820.0,
                "operating_hours": 210.0,
                "previous_installation_id": None,
                "removal_date": None,
                "replacement_reason": None,
                "created_at": (now - timedelta(days=42)).isoformat(),
                "updated_at": now.isoformat(),
            }

        event_id = "maint-evt-001"
        self.maintenance_events.append(
            {
                "id": event_id,
                "device_id": dev_str,
                "event_type": "FILTER_REPLACEMENT",
                "description": "Initial 4-stage filter commissioning and baseline verification",
                "initiated_by": "operator@aquanexis.local",
                "performed_by": "operator@aquanexis.local",
                "performed_at": (now - timedelta(days=42)).isoformat(),
                "timestamp": (now - timedelta(days=42)).isoformat(),
                "filter_instance_id": "inst-stage-1",
                "evidence": {"dp_before_kpa": 145.0, "dp_after_kpa": 24.0},
                "pre_maintenance_state": {"fsi": 68.0, "fhi": 38, "dp_kpa": 145.0},
                "post_maintenance_state": {"fsi": 8.0, "fhi": 96, "dp_kpa": 24.0},
                "pre_metrics": {"fsi": 68.0, "fhi": 38, "dp_kpa": 145.0},
                "post_metrics": {"fsi": 8.0, "fhi": 96, "dp_kpa": 24.0},
                "notes": "Baseline established post-replacement.",
                "verified": True,
                "verification_status": "PASSED",
                "verification_data": {"flow_lpm": 2.0, "rejection_pct": 95.8},
                "correlation_id": "corr-init-001",
                "created_at": (now - timedelta(days=42)).isoformat(),
            }
        )

        ver_id = "ver-run-001"
        self.verifications[ver_id] = {
            "id": ver_id,
            "maintenance_event_id": event_id,
            "device_id": dev_str,
            "state": "PASSED",
            "started_at": (now - timedelta(days=42)).isoformat(),
            "completed_at": (now - timedelta(days=42, minutes=-10)).isoformat(),
            "checks": [
                {
                    "name": "Differential Pressure Reset",
                    "passed": True,
                    "value": 24.0,
                    "threshold": 50.0,
                },
                {"name": "Permeate Flow Recovery", "passed": True, "value": 2.0, "threshold": 1.5},
                {
                    "name": "TDS Rejection Efficiency",
                    "passed": True,
                    "value": 95.8,
                    "threshold": 90.0,
                },
                {"name": "Leak Sensor Dry Check", "passed": True, "value": 0, "threshold": 0},
            ],
            "overall_result": True,
            "failure_reasons": [],
            "baseline_before": {"dp_kpa": 145.0, "flow_lpm": 0.92},
            "baseline_after": {"dp_kpa": 24.0, "flow_lpm": 2.01},
            "created_at": (now - timedelta(days=42)).isoformat(),
            "updated_at": (now - timedelta(days=42)).isoformat(),
        }

        self.calibrations.append(
            {
                "id": "cal-rec-001",
                "device_id": dev_str,
                "sensor_id": "SEN-TDS-01",
                "sensor_type": "tds",
                "calibration_method": "2-point standard KCl solution",
                "reference_standard": "NIST 300 ppm KCl",
                "reference_value": 300.0,
                "measured_value": 301.2,
                "tolerance": 5.0,
                "technician": "UPES Lab Operator",
                "notes": "Within ±0.4% tolerance",
                "calibration_date": (now - timedelta(days=20)).isoformat(),
                "correction_offset": -1.2,
                "result": "PASS",
                "next_calibration_due": (now + timedelta(days=70)).isoformat(),
                "calibration_state": "VALID",
                "created_at": (now - timedelta(days=20)).isoformat(),
                "updated_at": (now - timedelta(days=20)).isoformat(),
            }
        )

        self.recommendations.append(
            {
                "id": "rec-init-001",
                "device_id": dev_str,
                "filter_instance_id": "inst-stage-1",
                "trigger": "SCHEDULED_MONITORING",
                "severity": "LOW",
                "evidence": {"stage": 1, "filter_identifier": "AQX-SED-01", "current_fhi": 90},
                "urgency_days": 138,
                "recommended_action": "Continue routine monitoring of Stage 1 Sediment Filter; next scheduled replacement in ~138 days.",
                "acknowledged_at": None,
                "dismissed_at": None,
                "created_at": now.isoformat(),
            }
        )

        prov_id = "prov-console-001"
        self.notification_providers[prov_id] = {
            "id": prov_id,
            "device_id": dev_str,
            "channel": "email",
            "provider": "console",
            "enabled": True,
            "config": {"target": "stdout", "simulated": True},
            "min_severity": "WARNING",
            "alert_codes": None,
            "rate_limit_per_hour": 60,
            "created_at": (now - timedelta(days=30)).isoformat(),
            "updated_at": now.isoformat(),
        }

        tpl_id = "tpl-default-001"
        self.notification_templates[tpl_id] = {
            "id": tpl_id,
            "name": "default_alert",
            "channel": "email",
            "subject_template": "[AquaNexis {{ severity }}] {{ title }}",
            "body_template": "Device {{ device_id }} reported {{ alert_code }}: {{ message }}",
            "description": "Default alert notification template",
            "is_default": True,
            "created_at": (now - timedelta(days=30)).isoformat(),
            "updated_at": now.isoformat(),
        }


demo_engine = DemoModeEngine()
