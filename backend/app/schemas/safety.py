"""
Safety Pydantic schemas for API requests/responses.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


# Safety configuration
class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]


class SafetyConfigUpdate(BaseModel):
    leak_action: Optional[str] = None
    leak_validate_with: Optional[List[str]] = None
    leak_cooldown_sec: Optional[int] = None
    leak_persistence_readings: Optional[int] = None
    pressure_max_kpa: Optional[float] = None
    pressure_action: Optional[str] = None
    pressure_cooldown_sec: Optional[int] = None
    pressure_min_kpa: Optional[float] = None
    pressure_action_low: Optional[str] = None
    flow_min_lpm: Optional[float] = None
    dry_run_action: Optional[str] = None
    dry_run_cooldown_sec: Optional[int] = None
    flow_unstable_threshold_pct: Optional[float] = None
    pump_current_max_a: Optional[float] = None
    overcurrent_action: Optional[str] = None
    overcurrent_cooldown_sec: Optional[int] = None
    pump_power_max_w: Optional[float] = None
    persistence_required_readings: Optional[int] = None
    cooldown_enabled: Optional[bool] = None
    cooldown_by_code: Optional[Dict[str, int]] = None


class SafetyTestRequest(BaseModel):
    device_id: UUID
    test_type: Literal["leak", "pressure_high", "pressure_low", "flow_low", "pump_overcurrent", "dry_run"]
    custom_reading: Optional[Dict[str, Any]] = None


class SafetyTestResponse(BaseModel):
    test_type: str
    passed: bool
    details: Dict[str, Any]
    simulated_action: Optional[str] = None


class SafetyActionCommand(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    event_type: str
    trigger_value: float
    threshold_value: float
    timestamp: datetime
    timeout_sec: int = 5
    signature: Optional[str] = None


class SafetyActionResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    action_type: Literal["close_inlet_valve", "stop_pump", "open_relief_valve", "both_valve_and_pump"]
    status: Literal["pending", "executing", "completed", "failed", "validation_failed", "cooldown_active"]
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_response: Optional[Dict[str, Any]] = None


class SafetyConfigResponse(BaseModel):
    device_id: UUID
    leak_action: str
    leak_validate_with: List[str]
    leak_cooldown_sec: int
    leak_persistence_readings: int
    pressure_max_kpa: float
    pressure_action: str
    pressure_cooldown_sec: int
    pressure_min_kpa: float
    pressure_action_low: str
    flow_min_lpm: float
    dry_run_action: str
    dry_run_cooldown_sec: int
    flow_unstable_threshold_pct: float
    pump_current_max_a: float
    overcurrent_action: str
    overcurrent_cooldown_sec: int
    pump_power_max_w: float
    persistence_required_readings: int
    cooldown_enabled: bool
    cooldown_by_code: Dict[str, int]