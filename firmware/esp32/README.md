# AquaNexis ESP32 Firmware (ARCHIVED — OUT OF SCOPE)

> **⚠️ IMPORTANT: HARDWARE DEVELOPMENT IS OUT OF SCOPE**
> 
> This directory contains the **archived reference implementation** of the ESP32-S3 firmware for the AquaNexis project. 
> 
> As of **2026-11-03**, the AquaNexis project has officially pivoted to a **software-only** product.
> All hardware development (ESP32 firmware, sensor integration, physical hardware bring-up) is **OUT OF SCOPE**.
> 
> This directory is preserved as **archived reference material** only. It documents a complete firmware implementation 
> that was developed and syntactically validated but never built or tested on physical hardware.

---

## What's Here

This directory contains a complete, syntactically-valid ESP32-S3 firmware implementation:

```
firmware/esp32/
├── CMakeLists.txt          # ESP-IDF build configuration
├── partitions.csv          # Partition table (factory, OTA, SPIFFS)
├── config/
│   └── sdkconfig.defaults  # ESP32-S3 config (8MB flash, PSRAM, WiFi, HTTPS, OTA)
├── include/
│   ├── aquanexis_config.h  # Hardware config, pin mapping, constants
│   ├── sensor_interface.h  # Abstract sensor driver interface (13 types)
│   └── comm_interface.h    # Communication layer interface
├── src/
│   ├── main.c              # Main application (WiFi, sensor loop, telemetry, safety, health, OTA)
│   ├── sensor_registry.c   # Unified sensor management
│   ├── sensor_tds.c        # TDS/EC sensor (Gravity analog)
│   ├── sensor_ph.c         # pH sensor (Gravity analog)
│   ├── sensor_turbidity.c  # Turbidity sensor (Gravity analog)
│   ├── sensor_temperature.c # Temperature (NTC thermistor)
│   ├── sensor_flow.c       # Flow rate (Hall effect)
│   ├── sensor_pressure.c   # Pressure (MS5837 via TCA9548A I2C mux)
│   ├── sensor_tank_level.c # Tank level (ultrasonic)
│   ├── sensor_leak.c       # Leak detection (digital contact)
│   ├── sensor_pump_current.c  # Pump current (ACS712)
│   ├── sensor_pump_power.c    # Pump power (calculated V×I)
│   ├── sensor_uv_state.c      # UV lamp state
│   └── comm_manager.c       # HTTP/HTTPS + JWT communication
└── partitions.csv          # Partition table (factory, OTA, SPIFFS)
```

## Key Technical Achievements (Archived)

- **13 sensor drivers** implemented with unified interface
- **TCA9548A I²C multiplexer** for dual MS5837 pressure sensors (both at 0x76)
- **GPIO/ADC conflict resolution** - all 13 sensors on unique pins
- **Pump power calculation corrected**: DC formula `P = V_bus × I` (PF=1.0)
- **ADC voltage limits** documented with voltage divider requirements
- **Safety architecture**: Low-voltage (3.3V) control only, optocoupler isolation required
- **13 sensor types**: TDS, pH, Turbidity, Temperature, Flow, Pressure×2, Tank Level, Leak, Pump Current, Pump Power, UV State, Conductivity
- **Communication layer**: HTTP/HTTPS + JWT, telemetry batching, OTA support
- **13/13 sensor drivers** implemented with unified registry

## Build Status

```
❌ ESP-IDF v5.x NOT INSTALLED
❌ idf.py build — BLOCKED (requires ESP-IDF)
❌ Firmware ELF/binary generation — BLOCKED
```

**To build** (when ready):
```bash
# Option 1: Native ESP-IDF
idf.py set-target esp32s3
idf.py fullclean
idf.py build

# Option 2: Docker (if ESP-IDF unavailable)
docker build -t aquanexis-firmware .
docker run --rm -v $(pwd):/project aquanexis-firmware idf.py build
```

## Hardware Status: OUT OF SCOPE

> **⚠️ This firmware was never built, flashed, or tested on physical hardware.**
> 
> All development was done against the Python simulator (`backend/simulator.py`).
> No physical ESP32-S3 board, sensors, or relay boards were ever procured or tested.
> 
> The `firmware/esp32/` directory is preserved as **archived reference material only**.
> Hardware development is **OUT OF SCOPE** for the AquaNexis product.

---

## What Was Achieved (Archived Reference)

| Component | Status |
|-----------|--------|
| 13 sensor drivers | ✅ Implemented |
| Sensor registry | ✅ Complete |
| I²C multiplexer (TCA9548A) | ✅ Implemented |
| HTTP/HTTPS + JWT comms | ✅ Implemented |
| Safety architecture | ✅ Designed |
| Safety actions (4) | ✅ Designed |
| Sensor conversion formulas | ✅ Validated (syntax) |
| Pin mapping | ✅ Conflict-free |
| Pump power (DC) | ✅ Corrected |
| ADC voltage limits | ✅ Documented |
| Pin mapping conflicts | ✅ Resolved |

---

## If You Need This in the Future

If hardware development is ever revived:

1. **Install ESP-IDF v5.2**: Download `esp-idf-tools-setup.exe` from Espressif
2. **Target**: ESP32-S3 (`idf.py set-target esp32s3`)
3. **Build**: `idf.py fullclean && idf.py build`
4. **Flash**: `idf.py -p <PORT> flash`
4. **Monitor**: `idf.py -p <PORT> monitor`

---

**Last Updated**: 2026-11-03  
**Status**: 📦 **ARCHIVED — OUT OF SCOPE**  
**Preserved for reference only**