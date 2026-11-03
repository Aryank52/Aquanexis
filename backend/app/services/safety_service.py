"""
Safety service - orchestrates all safety validations and executes protective actions.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, List
from uuid import UUID

from app.domain.safety import (
    SafetyConfig,
    SafetyValidationContext,
    SafetyValidationResult,
    SafetyEventType,
    SafetyActionType,
    SafetyAction,
    SafetyEvent,
    SafetyActionCommand,
    SafetyActionResponse,
    SafetyConfig,
    SafetyActionCommand,
    SafetyActionResponse,
    SafetyAuditEvent,
    SafetyConfig,
    SafetyActionCommand,
    SafetyActionResponse,
    SafetyAuditEvent,
)
from app.infrastructure.logging import get_logger

from app.services.leak_protection import LeakProtectionService
from app.services.pressure_protection import PressureProtectionService
from app.services.flow_protection import FlowProtectionService
from app.services.energy_protection import EnergyProtectionService

logger = get_logger(__name__)


class SafetyService:
    """Orchestrates all safety validations and executes protective actions."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()
        self.leak_service = LeakProtectionService(SafetyConfig())
        self.pressure_service = PressureProtectionService(SafetyConfig())
        self.flow_service = FlowProtectionService(SafetyConfig())
        self.energy_service = EnergyProtectionService(SafetyConfig())
        self.leak_service = LeakProtectionService(SafetyConfig())
        self.pressure_service = PressureProtectionService(SafetyConfig())
        self.flow_service = FlowProtectionService(SafetyConfig())
        self.energy_service = EnergyProtectionService(SafetyConfig())
        
        # Track cooldowns per device and alert code
        self._cooldowns: Dict[str, datetime] = {}

    async def validate_and_protect(
        self,
        device_id: UUID,
        reading: dict,
        previous_readings: list,
        device_config: dict,
        db_session=None,
    ) -> List[dict]:
        """
        Run all safety validations and execute protective actions if needed.
        
        Returns list of triggered alerts/actions.
        """
        device_id_str = str(device_id)
        results = []

        # Get device safety config
        safety_config = device_config.get('safety_config', {}) if device_config else {}
        safety_config = {**SafetyConfig().__dict__, **safety_config}
        
        # Merge with device safety config
        merged_config = {**SafetyConfig().__dict__, **safety_config}

        device_config = {
            'safety_config': safety_config,
            'sensor_config': device_config.get('sensor_config', {}) if device_config else {},
        }

        # Run all safety validations
        validations = [
            ("leak", self.leak_service.validate_leak),
            ("pressure", self.pressure_service.validate_pressure),
            ("flow", self.flow_service.validate_flow),
            ("energy", self.energy_service.validate_energy),
        ]

        for check_name, validator in validations:
            try:
                is_valid, evidence = validator(
                    device_id=device_id,
                    current_reading=reading,
                    previous_readings=previous_readings,
                    device_config=device_config,
                    safety_config=merged_config,
                )
                
                if is_valid:
                    # Trigger alert and potentially safety action
                    alert_result = await self._handle_alert(
                        device_id=device_id,
                        check_name=check_name,
                        evidence=evidence,
                        safety_config=merged_config,
                    )
                    results.append({
                        "check": check_name,
                        "triggered": True,
                        "evidence": evidence,
                        "alert": alert_result,
                    })
                else:
                    results.append({
                        "check": check_name,
                        "triggered": False,
                        "evidence": evidence,
                    })
            except Exception as e:
                logger.error(f"Safety check {check_name} failed", device_id=device_id, error=str(e))
                results.append({
                    "check": check_name,
                    "triggered": False,
                    "evidence": {"error": str(e)},
                })

        return results

    async def _handle_alert(
        self,
        device_id: UUID,
        check_name: str,
        evidence: dict,
        safety_config: dict,
    ) -> dict:
        """Handle alert creation and safety action execution."""
        # Map check name to alert code and severity
        alert_mapping = {
            "leak": ("leak_detected", "CRITICAL"),
            "pressure": ("pressure_high", "CRITICAL"),
            "flow": ("flow_low", "WARNING"),
            "energy": ("pump_overcurrent", "CRITICAL"),
        }
        
        alert_code, severity = alert_mapping.get(check_name, ("unknown", "WARNING"))
        
        # Check cooldown
        cooldown_key = f"{device_id}:{check_name}"
        if cooldown_key in self._cooldowns:
            cooldown_end = self._cooldowns[cooldown_key]
            if datetime.utcnow() < cooldown_end:
                return {"action": "skipped", "reason": "cooldown_active"}

        # Get cooldown duration
        cooldown_map = {
            "leak": 300,
            "pressure_high": 60,
            "flow_low": 30,
            "energy": 180,
        }
        cooldown_sec = cooldown_map.get(check_name, 300)

        # Set cooldown
        self._cooldowns[cooldown_key] = datetime.utcnow() + timedelta(seconds=cooldown_sec)

        # Determine action
        action_map = {
            "leak": "close_inlet_valve",
            "pressure_high": "open_relief_valve",
            "flow_low": "stop_pump",
            "energy": "stop_pump",
        }
        
        action = action_map.get(check_name, "stop_pump")
        
        # Execute safety action via firmware command
        action_result = await self._execute_safety_action(
            device_id=device_id,
            action=action,
            trigger_value=evidence.get('trigger_value', 0),
            threshold_value=evidence.get('threshold_value', 0),
        )

        return {
            "alert_code": check_name,
            "severity": severity,
            "action": action,
            "action_result": action_result,
        }

    async def _execute_safety_action(
        self,
        device_id: UUID,
        action: str,
        trigger_value: float,
        threshold_value: float,
    ) -> dict:
        """Execute safety action via firmware command."""
        # In production, this would send a command to the firmware
        # For now, we log and return a simulated response
        
        logger.warning(
            "SAFETY_ACTION_TRIGGERED",
            device_id=str(device_id),
            action=action,
            trigger_value=trigger_value,
            threshold_value=threshold_value,
        )

        # Simulate firmware command
        # In production: await self._send_firmware_command(device_id, action)
        
        return {
            "action": action,
            "status": "executed",
            "executed_at": datetime.utcnow().isoformat(),
            "simulated": True,
        }

    def check_cooldown(self, device_id: UUID, alert_code: str) -> bool:
        """Check if alert is in cooldown."""
        cooldown_key = f"{device_id}:{alert_code}"
        if cooldown_key in self._cooldowns:
            return datetime.utcnow() < self._cooldowns[cooldown_key]
        return False
