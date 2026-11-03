"""
Telemetry Simulator - generates realistic sensor data for testing.
Supports multiple profiles: NORMAL, HIGH_TURBIDITY, FILTER_STRESS, LOW_FLOW, 
HIGH_PRESSURE_DROP, LEAK, SENSOR_FAULT, DEVICE_OFFLINE
"""
import asyncio
import os
import random
import signal
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel

from app.schemas.telemetry import (
    TelemetryPayload,
    SensorReadingInput,
    DeviceCreate,
    DeviceSensorConfig,
    SafetyConfig,
    SensorConfig,
)


class SimulationProfile(str, Enum):
    NORMAL = "normal"
    HIGH_TURBIDITY = "high_turbidity"
    FILTER_STRESS = "filter_stress"
    LOW_FLOW = "low_flow"
    HIGH_PRESSURE_DROP = "high_pressure_drop"
    LEAK = "leak"
    SENSOR_FAULT = "sensor_fault"
    DEVICE_OFFLINE = "device_offline"


class SimulatorConfig(BaseModel):
    """Simulator configuration."""
    backend_url: str = "http://localhost:8000"
    device_id: UUID
    device_jwt: str
    interval_seconds: int = 10
    profile: SimulationProfile = SimulationProfile.NORMAL
    seed: Optional[int] = None
    simulate_duration_seconds: Optional[int] = None  # None = infinite


class SimulatorState:
    """Internal state for generating correlated sensor data."""
    
    def __init__(self, profile: SimulationProfile, seed: Optional[int] = None):
        self.profile = profile
        self.random = random.Random(seed)
        self.sequence = 0
        self.start_time = datetime.utcnow()
        
        # Base values for NORMAL profile
        self.base_tds = 185.0
        self.base_conductivity = 330.0
        self.base_ph = 7.2
        self.base_turbidity = 0.35
        self.base_temperature = 24.5
        self.base_flow = 2.0
        self.base_inlet_pressure = 310.0
        self.base_outlet_pressure = 285.0
        self.base_tank = 78.0
        self.base_pump_current = 1.05
        self.base_pump_power = 240.0
        
        # Drift accumulators
        self.filter_age_hours = 120.0
        self.turbidity_exposure = 4.0
        self.pressure_drift = 0.0
        self.flow_drift = 0.0
        
        # Profile-specific state
        self._init_profile_state()
    
    def _init_profile_state(self):
        """Initialize profile-specific state."""
        if self.profile == SimulationProfile.FILTER_STRESS:
            self.filter_age_hours = 1850.0  # Aged filter under fouling stress
            self.turbidity_exposure = 75.0
            self.pressure_drift = 95.0      # High inlet pressure buildup
            self.flow_drift = -1.05         # Flow restricted from 2.0 -> ~0.95 L/min
            self.base_turbidity = 2.4
            self.base_tds = 340.0
            self.base_conductivity = 610.0
            self.base_pump_current = 1.65
        elif self.profile == SimulationProfile.HIGH_TURBIDITY:
            self.turbidity_exposure = 100.0
            self.base_turbidity = 12.5
            self.base_tds = 420.0
            self.base_conductivity = 740.0
        elif self.profile == SimulationProfile.LOW_FLOW:
            self.flow_drift = -1.45
        elif self.profile == SimulationProfile.HIGH_PRESSURE_DROP:
            self.pressure_drift = 120.0
            self.flow_drift = -0.6
        elif self.profile == SimulationProfile.LEAK:
            self.flow_drift = 0.65          # Uncontrolled flow surge through leak
            self.pressure_drift = -85.0     # Line pressure drop during leak
            self.base_tank = 42.0
        elif self.profile == SimulationProfile.SENSOR_FAULT:
            pass  # Injects deterministic sensor faults in _apply_profile_effects
    
    def generate_reading(self) -> SensorReadingInput:
        """Generate a single sensor reading based on current state."""
        self.sequence += 1
        elapsed_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        
        # Apply profile-specific evolution
        self._evolve_state(elapsed_hours)
        
        # Generate correlated values with noise
        reading = SensorReadingInput(
            tds=self._clamp(self.base_tds + self.random.gauss(0, 5), 0, 2000),
            conductivity=self._clamp(self.base_conductivity + self.random.gauss(0, 10), 0, 10000),
            ph=self._clamp(self.base_ph + self.random.gauss(0, 0.05), 0, 14),
            turbidity=self._clamp(self.base_turbidity + self.random.gauss(0, 0.1), 0, 1000),
            temperature=self._clamp(self.base_temperature + self.random.gauss(0, 0.2), -10, 60),
            flow_rate=self._clamp(self.base_flow + self.flow_drift + self.random.gauss(0, 0.02), 0, 50),
            inlet_pressure=self._clamp(self.base_inlet_pressure + self.pressure_drift + self.random.gauss(0, 2), 0, 1000),
            outlet_pressure=self._clamp(
                self.base_outlet_pressure
                - (self.pressure_drift * 0.65 if self.pressure_drift > 0 else abs(self.pressure_drift) * 0.9)
                + self.random.gauss(0, 2),
                0,
                1000,
            ),
            tank_level=self._clamp(self.base_tank + self.random.gauss(0, 0.5), 0, 100),
            leak=False,
            pump_current=self._clamp(self.base_pump_current + self.random.gauss(0, 0.01), 0, 10),
            pump_power=self._clamp(self.base_pump_power + self.random.gauss(0, 2), 0, 5000),
            uv_state=True,
        )
        
        # Profile-specific modifications
        self._apply_profile_effects(reading)
        
        return reading
    
    def _evolve_state(self, elapsed_hours: float):
        """Evolve base state over time."""
        # Slow daily temperature cycle
        hour_of_day = (elapsed_hours % 24)
        temp_cycle = 3 * (0.5 - abs((hour_of_day - 12) / 12))  # ±1.5°C daily variation
        self.base_temperature = 25 + temp_cycle + self.random.gauss(0, 0.1)
        
        # Tank level slowly drains and refills
        if self.base_tank > 90:
            self.base_tank -= self.random.uniform(0.01, 0.05)
        elif self.base_tank < 30:
            self.base_tank += self.random.uniform(0.01, 0.05)
        else:
            self.base_tank += self.random.uniform(-0.02, 0.02)
        self.base_tank = self._clamp(self.base_tank, 10, 95)
        
        if self.profile == SimulationProfile.FILTER_STRESS:
            # Filter ages - pressure increases, flow decreases
            self.filter_age_hours += 1/3600  # per reading at 1Hz equivalent
            self.pressure_drift += 0.001  # kPa per reading
            self.flow_drift -= 0.00001    # L/min per reading
            self.turbidity_exposure += 0.0001
            
            # Turbidity breakthrough as filter ages
            if self.filter_age_hours > 3000:
                self.base_turbidity += 0.00005
        
        elif self.profile == SimulationProfile.HIGH_TURBIDITY:
            # Gradual turbidity increase
            self.turbidity_exposure += 0.001
            self.base_turbidity = 0.5 + self.turbidity_exposure * 0.1
            
        elif self.profile == SimulationProfile.LEAK:
            # Slow leak progression
            if self.random.random() < 0.001:  # 0.1% chance per reading
                self.base_tank -= self.random.uniform(0.5, 2.0)
                self.flow_drift -= 0.001
        
        elif self.profile == SimulationProfile.SENSOR_FAULT:
            # Random sensor faults
            pass
    
    def _apply_profile_effects(self, reading: SensorReadingInput):
        """Apply profile-specific modifications to reading."""
        if self.profile == SimulationProfile.LEAK:
            reading.leak = True
            reading.flow_rate = round(self._clamp(self.base_flow + 0.65 + self.random.uniform(0.0, 0.25), 0.1, 50), 2)
            reading.inlet_pressure = round(self._clamp(215.0 + self.random.gauss(0, 3), 50, 1000), 1)
            reading.outlet_pressure = round(self._clamp(145.0 + self.random.gauss(0, 3), 20, 1000), 1)
            self.base_tank = self._clamp(self.base_tank - 0.8, 5, 100)
            reading.tank_level = round(self.base_tank, 1)
        
        elif self.profile == SimulationProfile.SENSOR_FAULT:
            # Deterministic multi-sensor fault injection for reliable demonstration:
            # 1. Out-of-range turbidity spike (>100 NTU max range)
            reading.turbidity = round(142.5 + self.random.uniform(-5.0, 8.0), 2)
            # 2. Cross-sensor TDS vs Conductivity ratio violation (ratio > 0.7)
            reading.tds = 890.0
            reading.conductivity = 410.0
            # 3. Missing flow_rate and outlet_pressure readings (sensor dropout)
            reading.flow_rate = None
            reading.outlet_pressure = None
        
        elif self.profile == SimulationProfile.DEVICE_OFFLINE:
            # This is handled at the simulator loop level
            pass
    
    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))


async def create_device(backend_url: str, api_key: str, device_id: UUID) -> bool:
    """Create device via admin API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{backend_url}/api/v1/telemetry/devices",
                json={
                    "serial_number": f"SIM-{str(device_id)[:8]}",
                    "display_name": f"Simulator Device {str(device_id)[:8]}",
                    "model": "AquaNexis-SIM",
                    "firmware_version": "1.0.0-sim",
                    "sensor_config": DeviceSensorConfig().model_dump(),
                    "safety_config": SafetyConfig().model_dump(),
                    "capabilities": {"simulator": True}
                },
                headers={"X-API-Key": api_key},
                timeout=10.0
            )
            if response.status_code == 201:
                print(f"Created device: {device_id}")
                return True
            elif response.status_code == 409:
                print(f"Device already exists: {device_id}")
                return True
            else:
                print(f"Failed to create device: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error creating device: {e}")
            return False


async def run_simulator(config: SimulatorConfig):
    """Run the simulator loop."""
    state = SimulatorState(config.profile, config.seed)
    
    # Create device if needed and notify demo scenario state if backend is in DEMO_MODE
    api_key = os.getenv("SIMULATOR_API_KEY", "dev-api-key-change-in-production")
    await create_device(config.backend_url, api_key, config.device_id)
    async with httpx.AsyncClient() as setup_client:
        try:
            await setup_client.post(
                f"{config.backend_url}/api/v1/demo/scenario",
                json={"profile": config.profile.value, "device_id": str(config.device_id)},
                headers={"X-API-Key": api_key, "Authorization": f"Bearer {config.device_jwt}"},
                timeout=5.0,
            )
        except Exception:
            pass
    
    headers = {
        "Authorization": f"Bearer {config.device_jwt}",
        "Content-Type": "application/json"
    }
    
    start_time = datetime.utcnow()
    total_readings = 0
    failed_readings = 0
    
    print(f"Starting simulator: device={config.device_id}, profile={config.profile}, interval={config.interval_seconds}s")
    print(f"Profile: {config.profile.value}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            # Check duration limit
            if config.simulate_duration_seconds:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= config.simulate_duration_seconds:
                    print(f"Simulation duration reached ({config.simulate_duration_seconds}s)")
                    break
            
            # Check for device offline profile
            if config.profile == SimulationProfile.DEVICE_OFFLINE:
                if state.sequence > 0:
                    print("DEVICE_OFFLINE profile: stopping telemetry")
                    break
            
            # Generate reading
            reading = state.generate_reading()
            
            payload = TelemetryPayload(
                device_id=config.device_id,
                timestamp=datetime.utcnow(),
                sequence=state.sequence,
                firmware_version="1.0.0-sim",
                readings=reading,
            )
            
            # Send to backend
            try:
                response = await client.post(
                    f"{config.backend_url}/api/v1/telemetry",
                    json=payload.model_dump(mode="json"),
                    headers=headers
                )
                
                if response.status_code == 200:
                    total_readings += 1
                    if total_readings % 10 == 0:
                        print(f"Sent {total_readings} readings (last: TDS={reading.tds:.1f}, pH={reading.ph:.2f}, Flow={reading.flow_rate:.2f})")
                else:
                    failed_readings += 1
                    print(f"Failed to send: {response.status_code} - {response.text}")
                    
            except Exception as e:
                failed_readings += 1
                print(f"Error sending telemetry: {e}")
            
            # Wait for next interval
            await asyncio.sleep(config.interval_seconds)
    
    print(f"Simulator stopped. Total: {total_readings}, Failed: {failed_readings}")


def parse_args():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AquaNexis Telemetry Simulator")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument(
        "--device-id",
        default=os.getenv("SIMULATOR_DEVICE_ID", "00000000-0000-0000-0000-000000000001"),
    )
    parser.add_argument("--device-jwt", default=os.getenv("SIMULATOR_DEVICE_JWT"))
    parser.add_argument("--interval", type=int, default=int(os.getenv("SENSOR_INTERVAL_SECONDS", "10")))
    parser.add_argument("--profile", choices=[p.value for p in SimulationProfile], 
                       default=os.getenv("SIMULATION_PROFILE", "normal"))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--duration", type=int, default=None)
    
    args = parser.parse_args()
    
    if not args.device_id:
        # Generate deterministic ID from hostname or use fixed
        args.device_id = str(uuid4())
    
    if not args.device_jwt:
        # In development, create a token
        from app.infrastructure.security import create_device_token
        device_uuid = UUID(args.device_id)
        args.device_jwt = create_device_token(device_uuid)
        print(f"Generated device JWT: {args.device_jwt[:20]}...")
    
    return args


async def main():
    """Main entry point."""
    # Setup signal handling (Windows compatible)
    loop = asyncio.get_event_loop()
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass
    
    args = parse_args()
    
    simulator_config = SimulatorConfig(
        backend_url=args.backend_url,
        device_id=UUID(args.device_id),
        device_jwt=args.device_jwt,
        interval_seconds=args.interval,
        profile=SimulationProfile(args.profile),
        seed=args.seed,
        simulate_duration_seconds=args.duration,
    )
    
    try:
        await run_simulator(simulator_config)
    except asyncio.CancelledError:
        pass


async def shutdown():
    print("Shutting down...")
    asyncio.get_event_loop().stop()


if __name__ == "__main__":
    # Add app to path for imports
    import sys
    sys.path.insert(0, "/app")
    
    asyncio.run(main())