# AquaNexis Hardware Documentation

## Overview
This document describes the hardware architecture, sensor specifications, wiring, and integration details for the AquaNexis ESP32-based water monitoring system.

## Hardware Platform

### Microcontroller
- **MCU**: ESP32-S3 (Xtensa LX7 dual-core, 240 MHz)
- **Flash**: 8 MB QSPI
- **PSRAM**: 8 MB Octal SPI
- **Wireless**: WiFi 802.11 b/g/n, Bluetooth 5.0 LE
- **Package**: 7mm x 7mm QFN56

### Power Supply
- **Input**: 12V DC (from purifier power supply)
- **Regulation**: 3.3V LDO (ESP32) + 5V DC-DC (sensors)
- **Current**: ~500mA peak (WiFi active), ~50mA average
- **Backup**: Coin cell for RTC (optional)

## Sensor Specifications

### 1. TDS/EC Sensor (Gravity Analog)
- **Model**: DFRobot Gravity Analog TDS Sensor
- **Interface**: Analog (0-2.3V) -> ADC
- **Range**: 0-1000 ppm TDS, 0-2000 µS/cm EC
- **Accuracy**: ±10% F.S.
- **Power**: 3.3V, <20mA
- **Calibration**: Single-point (known TDS solution)

### 2. pH Sensor (Gravity Analog)
- **Model**: DFRobot Gravity Analog pH Sensor v2
- **Interface**: Analog (0-3V) -> ADC
- **Range**: 0-14 pH
- **Accuracy**: ±0.1 pH (after calibration)
- **Power**: 3.3V, <15mA
- **Calibration**: Two-point (pH 4.0, 7.0, 10.0 buffers)

### 3. Turbidity Sensor (Gravity Analog)
- **Model**: DFRobot Gravity Analog Turbidity Sensor
- **Interface**: Analog (0-3.3V) -> ADC
- **Range**: 0-1000 NTU
- **Accuracy**: ±5% F.S.
- **Power**: 3.3V, <20mA
- **Note**: Voltage inversely proportional to turbidity

### 4. Temperature Sensor (NTC Thermistor)
- **Type**: 10K NTC Thermistor (B=3950)
- **Interface**: Voltage divider -> ADC
- **Range**: -20°C to 80°C
- **Accuracy**: ±0.5°C (after calibration)
- **Alternative**: DS18B20 (1-Wire) for higher accuracy

### 5. Flow Rate Sensor (Hall Effect)
- **Model**: YF-S201 / G1/2" Water Flow Sensor
- **Interface**: Digital pulse (Hall effect) -> GPIO interrupt
- **Range**: 1-30 L/min
- **Accuracy**: ±3%
- **Pulses**: 450 pulses/L (YF-S201)
- **Power**: 5V, <15mA

### 6. Pressure Sensors (MS5837-30BA via TCA9548A)
- **Model**: TE Connectivity MS5837-30BA
- **Interface**: I2C via TCA9548A multiplexer (0x70)
- **MS5837 Address**: 0x76 (fixed, both sensors)
- **Multiplexer**: TCA9548A @ 0x70
- **Channel 0**: Inlet Pressure (MS5837 @ 0x76)
- **Channel 1**: Outlet Pressure (MS5837 @ 0x76)
- **Range**: 0-30 bar (0-3000 kPa)
- **Accuracy**: ±0.5% F.S.
- **Resolution**: 0.2 mbar
- **Power**: 3.3V, <1mA

### 7. Tank Level Sensor (Ultrasonic)
- **Model**: JSN-SR04T (Waterproof Ultrasonic)
- **Interface**: GPIO (Trigger/Echo)
- **Range**: 20cm - 600cm
- **Accuracy**: ±2mm
- **Beam Angle**: ~75°
- **Power**: 5V, <15mA
- **Note**: Echo pin requires voltage divider (5V -> 3.3V)

### 8. Leak Detection Sensor
- **Type**: Water Contact Sensor (Two exposed electrodes)
- **Interface**: GPIO with pull-up (Active LOW)
- **Detection**: Water bridges electrodes
- **Response Time**: <1 second
- **Power**: 3.3V, <1mA (pull-up)

### 9. Pump Current Sensor (ACS712)
- **Model**: Allegro ACS712ELCTR-05B-T
- **Interface**: Analog (VCC/2 offset) -> ADC
- **Range**: ±5A
- **Sensitivity**: 185 mV/A
- **Accuracy**: ±1.5% F.S.
- **Isolation**: 2.1 kV RMS
- **Power**: 5V, <10mA
- **Note**: Output 0-5V, requires voltage divider for ESP32 ADC (3.3V max)

### 10. Pump Power (Calculated)
- **Method**: V_bus × I (DC power factor = 1.0)
- **Voltage**: DC bus voltage (configurable, default 24V)
- **Current**: From ACS712 sensor
- **Accuracy**: ±5% (estimated)
- **Note**: For DC pumps on 12V/24V bus, P = V_bus × I (PF = 1.0)

### 11. UV Lamp State
- **Method**: Digital feedback from ballast (GPIO)
- **Alternative**: Current monitoring on ballast input
- **Power**: 3.3V logic

## Pin Mapping (ESP32-S3)

| Function | GPIO | Peripheral | Notes |
|----------|------|------------|-------|
| I2C SCL | 7 | I2C0 | Sensors: Pressure (via TCA9548A), Temp (optional) |
| I2C SDA | 6 | I2C0 | |
| TDS ADC | 1 | ADC1_CH0 | Gravity TDS |
| pH ADC | 2 | ADC1_CH1 | Gravity pH |
| Turbidity ADC | 3 | ADC1_CH2 | Gravity Turbidity |
| Temp ADC | 4 | ADC1_CH3 | NTC Thermistor |
| Pump Current ADC | 5 | ADC1_CH4 | ACS712 (with voltage divider) |
| Tank Level ADC | 6 | ADC1_CH5 | Capacitive backup (optional) |
| Pump Power ADC | 7 | ADC1_CH6 | Shunt option (future) |
| Leak Digital | 15 | GPIO | Active LOW |
| Flow Meter | 16 | GPIO | Pulse input |
| UV State | 17 | GPIO | Ballast feedback |
| Inlet Valve | 18 | GPIO | 3.3V logic |
| Outlet Valve | 19 | GPIO | 3.3V logic |
| Pump Relay | 20 | GPIO | 3.3V logic |
| UV Lamp | 21 | GPIO | 3.3V logic |
| Ultrasonic Trig | 5 | GPIO | Tank level |
| Ultrasonic Echo | 4 | GPIO | Tank level (with voltage divider) |
| Status LED | 48 | GPIO | Built-in |
| Error LED | 47 | GPIO | |
| Comm LED | 2 | GPIO | |

## I2C Sensor Architecture

```
I2C0 (GPIO6=SDA, GPIO7=SCL) 
    └── TCA9548A Multiplexer @ 0x70
          ├── Channel 0: Inlet Pressure (MS5837 @ 0x76)
          ├── Channel 1: Outlet Pressure (MS5837 @ 0x76)
          └── Channel 2: ADS1115 @ 0x48 (Temperature, optional)
```

### Analog Sensors (TDS, pH, Turbidity, Temp, Current)
```
Sensor VCC -> 3.3V
Sensor GND -> GND
Signal -> ADC_CHx (with 100nF decoupling cap)
ACS712: 5V supply, output 0-5V -> voltage divider -> ADC (3.3V max)
```

### Digital Sensors (Flow, Leak, UV State)
```
Sensor VCC -> 3.3V/5V
Sensor GND -> GND
Signal -> GPIOx (with pull-up/down as needed)
Flow meter: 5V, open collector -> GPIO with pull-up
```

### I2C Sensors (Pressure via Multiplexer, Temp optional)
```
Sensor VCC -> 3.3V
Sensor GND -> GND
SDA -> GPIO6 (pull-up 4.7k to 3.3V)
SCL -> GPIO7 (pull-up 4.7k to 3.3V)
TCA9548A @ 0x70: Channel 0=Inlet Pressure, Channel 1=Outlet Pressure
```

### Ultrasonic Tank Level
```
VCC -> 5V
GND -> GND
Trig -> GPIO5 (output)
Echo -> GPIO4 (input, 5V tolerant with voltage divider: 2.2k/3.3k)
```

### Output Controls (LOW VOLTAGE ONLY!)
```
ESP32 GPIO -> 3.3V Logic -> Optocoupler/Relay Driver -> External Relay -> Mains Load
```
⚠️ **CRITICAL**: ESP32 GPIOs are 3.3V logic ONLY. Never connect mains voltage directly. Use optocouplers and external relays for all high-voltage switching.

## Safety Architecture

### Low Voltage Control Only
All ESP32 outputs are 3.3V logic signals. High-voltage switching MUST use:
- Optocouplers (e.g., PC817) for isolation
- External relays/contactors rated for load
- Proper snubber circuits for inductive loads

### Safety Actions (Validated)
1. **Leak Detection** → Close inlet valve (3.3V signal → relay)
2. **Overpressure** → Open relief valve (3.3V signal → relay)
3. **Dry Run** → Stop pump (3.3V signal → relay)
4. **Overcurrent** → Stop pump (3.3V signal → relay)

### Prohibited Actions
- ❌ Direct mains switching from GPIO
- ❌ Unverified AI decisions on safety outputs
- ❌ Bypassing hardware interlocks

## Calibration Procedures

### TDS/EC Calibration
1. Prepare standard solution (e.g., 342 ppm NaCl)
2. Immerse sensor, wait for stabilization
3. Send calibration command with reference value
4. Firmware calculates slope, stores in NVS

### pH Calibration (Two-Point)
1. Immerse in pH 7.0 buffer, send calibrate(7.0)
2. Immerse in pH 4.0 buffer, send calibrate(4.0)
3. Firmware calculates slope and offset

### Pressure Calibration
1. Apply known pressure (reference gauge)
2. Send calibrate(reference_kPa)
4. Repeat at multiple points for linearity

### Flow Calibration
1. Measure known volume over time
2. Calculate actual flow rate
3. Send calibrate(actual_lpm)

### Tank Level Calibration
1. Fill tank to known level (e.g., 100%)
2. Send calibrate(100)
3. Drain to known level (e.g., 0%)
4. Send calibrate(0)

## Communication Protocol

### Telemetry Payload (JSON)
```json
{
  "device_id": "AQX-1234567890AB",
  "timestamp": 1699999999,
  "sequence": 12345,
  "firmware_version": "1.0.0",
  "readings": {
    "tds": {"value": 342.5, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "ph": {"value": 7.21, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "turbidity": {"value": 0.5, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "temperature": {"value": 24.5, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "flow_rate": {"value": 2.1, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "inlet_pressure": {"value": 300.2, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "outlet_pressure": {"value": 280.1, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "tank_level": {"value": 75.3, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "leak": {"value": 0, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "pump_current": {"value": 1.23, "status": 0, "provenance": 0, "timestamp_ms": 1234567890},
    "pump_power": {"value": 224.5, "status": 0, "provenance": 1, "timestamp_ms": 1234567890},
    "uv_state": {"value": 1, "status": 0, "provenance": 0, "timestamp_ms": 1234567890}
  }
}
```

### Data Provenance Values
- 0 = MEASURED (direct sensor reading)
- 1 = SIMULATED (test/simulator data)
- 2 = CALCULATED (derived from other measurements)
- 3 = MODEL_PREDICTED (ML model output)

### Status Codes
- 0 = OK
- 1 = NOT_INITIALIZED
- 2 = COMM_ERROR
- 3 = OUT_OF_RANGE
- 4 = CALIBRATION_DUE
- 5 = FAULT
- 6 = MISSING

## Hardware Bring-up Checklist

### Phase 1: Power & Communication
- [ ] 12V input present
- [ ] 3.3V LDO output stable
- [ ] 5V DC-DC output stable
- [ ] ESP32 boots, serial console accessible
- [ ] WiFi connects to AP
- [ ] Backend API reachable
- [ ] Device registers successfully
- [ ] JWT token obtained and stored

### Phase 2: Sensor Bring-up
- [ ] TDS sensor reads ~0 in air, ~300-400 in tap water
- [ ] pH sensor reads ~7.0 in neutral buffer
- [ ] Turbidity reads low in clear water
- [ ] Temperature reads ambient ±2°C
- [ ] Flow meter pulses visible on scope
- [ ] Pressure sensors read atmospheric (~101 kPa)
- [ ] Tank level changes with water level
- [ ] Leak sensor triggers when wet
- [ ] Pump current reads ~0A when off
- [ ] UV state changes with lamp

### Phase 3: Calibration
- [ ] TDS calibrated with standard solution
- [ ] pH calibrated with 2-point buffers
- [ ] Pressure calibrated at 2+ points
- [ ] Flow calibrated with measured volume
- [ ] Tank level calibrated at empty/full

### Phase 4: Safety Validation
- [ ] Leak detection triggers valve close
- [ ] Overpressure triggers relief valve
- [ ] Low flow triggers pump stop
- [ ] Overcurrent triggers pump stop
- [ ] All actions are low-voltage only

### Phase 5: Integration
- [ ] Telemetry received at backend
- [ ] Dashboard displays real data
- [ ] Alerts generate correctly
- [ ] Safety actions logged
- [ ] OTA update works

## Troubleshooting

### Common Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| All ADC readings 0 | ADC not initialized | Check `adc1_config_width/atten` calls |
| I2C sensors not found | Wrong address/wiring | Scan I2C bus, check pull-ups |
| Flow reads 0 | Interrupt not firing | Check GPIO config, pull-up |
| WiFi won't connect | Wrong credentials | Check NVS, SSID/password |
| Auth fails | Expired token | Refresh token, check time sync |
| Pressure reads 0 | I2C address wrong | Scan bus, check MS5837 addr |
| Tank level erratic | Echo noise | Add filtering, check wiring |

### Debug Commands
```bash
# Monitor serial output
idf.py monitor

# Flash firmware
idf.py flash

# Erase flash (clean)
idf.py erase-flash

# Partition table
idf.py partition-table

# OTA update
idf.py ota
```

## Hardware Revision History

| Rev | Date | Changes |
|-----|------|---------|
| A | 2026-11-02 | Initial prototype |

## Pending Hardware Items
- [ ] Physical ESP32-S3 board fabrication
- [ ] Sensor procurement and validation
- [ ] Relay board design for safety outputs
- [ ] Enclosure design (IP65 for wet environment)
- [ ] Power supply qualification
- [ ] EMC/EMI testing
- [ ] Long-term reliability testing

## ESP-IDF Environment Setup

### Current Blocker
**ESP-IDF v5.x build environment is NOT configured on this machine.**

### Required Setup Steps (Exact)

1. **Install ESP-IDF Tools** (Windows):
   - Download installer: `https://github.com/espressif/esp-idf-tools/releases/latest/download/esp-idf-tools-setup.exe`
   - Run installer, select:
     - ESP-IDF version: `v5.2` (or latest stable v5.x)
     - Target: `ESP32-S3`
     - Install Python 3.11+ (if not present)
     - Add to PATH: Yes
     - Desktop shortcut: Optional

2. **Verify Installation**:
   ```cmd
   idf.py --version
   # Should output: ESP-IDF v5.x.x
   ```

3. **Configure Project**:
   ```cmd
   cd E:\PROJECTS\Aquanexis\firmware\esp32
   idf.py set-target esp32s3
   idf.py menuconfig
   ```

4. **Build**:
   ```cmd
   idf.py build
   ```

### Current Blocker
**ESP-IDF v5.x is NOT installed on this machine.** The Python-based installer download URLs have changed and automated download failed. Manual download required.

**Required Manual Step**: 
1. Visit: https://github.com/espressif/esp-idf-tools/releases/latest
2. Download: `esp-idf-tools-setup.exe` (Windows x64)
3. Run installer with ESP-IDF v5.2, target ESP32-S3
4. Restart terminal/shell
5. Run `idf.py --version` to verify

### Alternative: Docker-based Build (if ESP-IDF unavailable)
```dockerfile
FROM espressif/idf:v5.2
WORKDIR /project
COPY . .
RUN idf.py build
```
```bash
docker build -t aquanexis-firmware .
docker run --rm -v E:/PROJECTS/Aquanexis/firmware/esp32:/project aquanexis-firmware idf.py build
```

## References
- ESP-IDF Programming Guide: https://docs.espressif.com/projects/esp-idf/
- MS5837 Datasheet: TE Connectivity
- ACS712 Datasheet: Allegro MicroSystems
- YF-S201 Datasheet: Various manufacturers
- DFRobot Gravity Sensors: DFRobot Wiki