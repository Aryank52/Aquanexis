# AquaNexis ESP32 Hardware — Bill of Materials (BOM)

**Document Version**: 1.0  
**Date**: 2026-11-02  
**Status**: **PLANNING — NOT PROCURED**  
**Phase**: H1-Physical (BLOCKED — HARDWARE UNAVAILABLE)

---

## 1. Microcontroller & Core Components

| Item | Specification | Qty | Interface | Voltage | Status | Notes |
|------|---------------|-----|-----------|---------|--------|-------|
| ESP32-S3 Dev Board | ESP32-S3-WROOM-1-N8R8 (8MB Flash, 8MB PSRAM) | 1 | USB/UART/JTAG | 3.3V | **NOT PROCURED** | Must support 45 GPIOs; ESP32-S3-WROOM-1-N8R8 recommended |
| TCA9548A I²C Multiplexer | 8-channel I²C Mux, 0x70 default | 1 | I²C (GPIO6/7) | 3.3V | **NOT PROCURED** | Required for dual MS5837 (both 0x76); 0x70 default addr |
| 4.7kΩ Pull-up Resistors | 0603 SMD, 4.7kΩ ±1% | 4 | I²C Pull-up | 3.3V | **NOT PROCURED** | 2 for I²C bus, 2 for TCA9548A addr pins if needed |

---

## 2. Analog Sensors (ADC1, 3.3V max input)

| # | Sensor | Model / Specification | Qty | GPIO / ADC | Supply | Signal Range | Voltage Divider Needed? | Status | Notes |
|---|--------|----------------------|-----|------------|--------|--------------|------------------------|--------|-------|
| 1 | TDS/EC | DFRobot Gravity Analog TDS (SEN0244) | 1 | ADC1_CH0 (GPIO1) | 3.3V | 0–2.3V | No | **NOT PROCURED** | DFRobot SKU: SEN0244; 0–2.3V output |
| 2 | pH | DFRobot Gravity Analog pH v2 (SEN0161-V2) | 1 | ADC1_CH1 (GPIO2) | 3.3V | 0–3V | No | **NOT PROCURED** | DFRobot SKU: SEN0161-V2; 0-3V output |
| 3 | Turbidity | DFRobot Gravity Analog Turbidity (SEN0189) | 1 | ADC1_CH2 (GPIO3) | 3.3V | 0–3.3V | No | **NOT PROCURED** | DFRobot SKU: SEN0189; inverse voltage |
| 4 | Temperature (NTC) | 10kΩ NTC, B=3950, 1% | 1 | ADC1_CH3 (GPIO4) | 3.3V | Voltage divider | No | **NOT PROCURED** | 10kΩ series resistor (10kΩ 1%); B=3950 |
| 5 | Pump Current (ACS712) | Allegro ACS712ELCTR-05B-T | 1 | ADC1_CH4 (GPIO5) | 5V | 0–5V → div to 0–3.3V | **YES (2:3 divider)** | **NOT PROCURED** | ACS712ELCTR-05B-T; 185mV/A sensitivity; VCC/2 = 1.65V offset |

---

## 2b. ADC Channel Assignment Summary (No Conflicts)

| ADC1_CH | GPIO | Sensor | Notes |
|---------|------|--------|-------|
| CH0 | GPIO1 | TDS/EC | DFRobot Gravity |
| CH1 | GPIO2 | pH | DFRobot Gravity |
| CH2 | GPIO3 | Turbidity | DFRobot Gravity |
| CH3 | GPIO4 | Temperature (NTC) | 10k NTC + 10kΩ series |
| CH4 | GPIO5 | Pump Current (ACS712) | With 2:3 voltage divider |
| CH5 | GPIO6 | Tank Level (capacitive backup) | Optional backup |
| CH6 | GPIO7 | Pump Power ADC (future) | Reserved |
| CH7 | GPIO8 | — | Available |
| CH8 | GPIO9 | — | Available |
| CH9 | GPIO10 | — | Available |

---

## 3. Digital Sensors (GPIO)

| # | Sensor | Model / Spec | Qty | GPIO | Supply | Signal Type | Status | Notes |
|---|--------|-------------|-----|------|--------|-------------|--------|-------|
| 1 | Flow Meter | YF-S201 (G1/2") | 1 | GPIO16 | 5V | Pulse (Hall) | **NOT PROCURED** | 450 pulses/L; open collector; pull-up 10kΩ |
| 2 | Leak Detection | Water contact (2-wire) | 1 | GPIO15 | 3.3V | Active LOW | **NOT PROCURED** | Pull-up 10kΩ; active LOW when wet |
| 3 | UV State Feedback | Digital from ballast | 1 | GPIO17 | 3.3V | Active HIGH | **NOT PROCURED** | Ballast must provide 3.3V logic feedback |
| 4 | Ultrasonic Trig | JSN-SR04T | 1 | GPIO5 | 5V | Output | **NOT PROCURED** | 10µs trigger pulse |
| 5 | Ultrasonic Echo | JSN-SR04T | 1 | GPIO4 | 5V | Input | **NOT PROCURED** | **Needs 5V→3.3V divider (2.2k/3.3k)** |

---

## 4. I²C Sensors (via TCA9548A @ 0x70)

| Channel | Sensor | Model | Address | Qty | Notes |
|---------|--------|-------|---------|-----|-------|
| 0 | Inlet Pressure | MS5837-30BA | 0x76 | 1 | TCA9548A Ch 0 |
| 1 | Outlet Pressure | MS5837-30BA | 0x76 | 1 | TCA9548A Ch 1 |
| 2 | Temperature (optional) | ADS1115 | 0x48 | 0–1 | Optional backup |

- **TCA9548A**: 8-ch I²C Mux, addr 0x70, channels 0–7
- **MS5837-30BA**: Fixed I²C address 0x76 (cannot change) — **requires mux**
- **Pull-ups**: 4.7kΩ on SDA (GPIO6) and SCL (GPIO7) to 3.3V

---

## 5. Output Controls (3.3V Logic Only — Optocoupler Required)

| # | Output | GPIO | Function | Isolation Required | Load Type |
|---|--------|------|----------|-------------------|-----------|
| 1 | Inlet Valve | GPIO18 | Open/Close | PC817 + Relay | Solenoid valve |
| 2 | Outlet Valve | GPIO19 | Open/Close | PC817 + Relay | Solenoid valve |
| 3 | Pump Relay | GPIO20 | On/Off | PC817 + Relay | Pump motor |
| 3 | UV Lamp | GPIO21 | On/Off | PC817 + Relay | UV ballast |

⚠️ **All outputs are 3.3V logic ONLY. Must use optocouplers (e.g., PC817) + external relays. Never connect mains directly.**

---

## 6. Power Supply Components

| Component | Specification | Qty | Notes |
|-----------|---------------|-----|-------|
| 12V DC Input | From purifier PSU | 1 | Main input |
| 5V DC-DC Converter | 12V→5V, ≥2A | 1 | For 5V sensors (flow, ultrasonic, ACS712) |
| 3.3V LDO | 5V→3.3V, ≥500mA | 1 | ESP32 + logic sensors; AMS1117-3.3 or similar |
| Decoupling Capacitors | 100nF + 10µF per sensor | — | Near each sensor VCC |
| Coin Cell (optional) | CR2032 + holder | 1 | RTC backup |

---

## 7. Protection & Passive Components

| Component | Specification | Qty | Location |
|-----------|---------------|-----|----------|
| TVS Diode | 5.0V (e.g., SMAJ5.0A) | 1 | 12V input protection |
| TVS Diode | 3.3V (e.g., SMAJ3.3A) | 2 | 3.3V rail + 5V rail |
| Schottky Diode | 1N5819 (40V/1A) | 2 | Relay flyback |
| Ferrite Bead | 120Ω @ 100MHz | 4 | Power rails |
| 100nF Ceramic Cap | 0603, 50V | 15+ | Per sensor VCC |
| 10µF Electrolytic | 10V/16V | 4 | Power rail bulk |
| 4.7kΩ Resistor | 0603, 1% | 4 | I²C pull-ups |
| 10kΩ Resistor | 0603, 1% | 4 | GPIO pull-ups |
| 2.2kΩ / 3.3kΩ Resistor | 0603, 1% | 2 | Ultrasonic echo divider (5V→3.3V) |
| 2kΩ / 3kΩ Resistor | 0603, 1% | 2 | ACS712 divider (5V→3.3V) |
| 10kΩ NTC Thermistor | B=3950, 1% | 1 | Temperature sensor |
| 10kΩ Resistor | 0603, 1% | 1 | NTC series resistor |

---

## 8. Calibration Equipment & Reference Solutions

| Item | Specification | Qty | Purpose |
|------|---------------|-----|---------|
| TDS Standard Solution | 342 ppm NaCl (or 1413 µS/cm KCl) | 1 | TDS/EC single-point cal |
| pH Buffer 4.00 | NIST traceable, ±0.01 | 1 | pH low-point cal |
| pH Buffer 7.00 | NIST traceable, ±0.01 | 1 | pH mid-point cal |
| pH Buffer 10.01 | NIST traceable, ±0.01 | 1 | pH high-point cal |
| Pressure Reference Gauge | 0–500 kPa, ±0.25% | 1 | Pressure sensor cal |
| Certified Flow Meter | 0.1–10 L/min, ±1% | 1 | Flow sensor cal |
| Digital Multimeter | 6.5 digit, ±0.005% | 1 | Voltage/current verification |
| Precision Resistor | 0.1Ω, 0.1%, 5W | 1 | Shunt calibration (future) |

---

## 9. Power Supply & Wiring

| Item | Specification | Qty | Notes |
|------|---------------|-----|-------|
| 12V DC Power Supply | 12V, ≥3A | 1 | From purifier PSU |
| DC Barrel Jack | 5.5×2.1mm | 1 | Panel mount |
| Terminal Blocks | 2-pin, 5.08mm | 6 | Power distribution |
| JST-SH Connectors | 4-pin, 1.0mm | 10 | Sensor cables |
| JST-PH Connectors | 2-pin, 2.0mm | 4 | Power leads |
| Silicone Wire | 22 AWG, 300V | 5m | Sensor leads |
| Heat Shrink Tubing | 2:1, assorted | 1 kit | Insulation |
| Cable Glands | M12, IP68 | 6 | Enclosure entry |

---

## 10. Enclosure & Mechanical

| Item | Specification | Qty | Notes |
|------|---------------|-----|-------|
| Enclosure | IP65, 200×150×100mm | 1 | Polycarbonate or ABS |
| Cable Glands | M12, IP68 | 6 | Sensor cable entry |
| DIN Rail Mount | 35mm | 1 | Panel mounting |
| DIN Rail Clips | 2-pack | 1 | Secure mounting |

---

## 10. Summary — Procurement Status

| Category | Total Items | Procured | Pending |
|----------|-------------|----------|---------|
| Core MCU | 2 | 0 | 2 |
| Analog Sensors | 5 | 0 | 5 |
| Digital Sensors | 5 | 0 | 5 |
| I²C Sensors (Pressure) | 3 | 0 | 3 |
| Output Controls | 4 | 0 | 4 |
| Power Supply | 5 | 0 | 5 |
| Protection/Passive | 20+ | 0 | 20+ |
| Calibration Equipment | 8 | 0 | 8 |
| Wiring/Connectors | 8 | 0 | 8 |
| Enclosure/Mechanical | 5 | 0 | 5 |
| **TOTAL** | **~55** | **0** | **55** |

---

## 11. Dependencies & Notes

| Dependency | Description |
|------------|-------------|
| TCA9548A | **Required before** MS5837 sensors (both 0x76) |
| Voltage Dividers | **Required before** ACS712, ultrasonic echo, any 5V→3.3V |
| I²C Pull-ups | **Required before** any I²C sensor init |
| ACS712 Divider | 2kΩ/3kΩ (5V→3.3V) — **must be installed** |
| Ultrasonic Echo Divider | 2.2kΩ/3.3kΩ (5V→3.3V) — **must be installed** |
| ESP-IDF v5.x | **Required** for build; not yet installed |
| Physical Hardware | **0% procured** — all items pending |

---

## 12. Procurement Priority

| Priority | Items | Reason |
|----------|-------|--------|
| **P0 (Blocker)** | ESP32-S3 Dev Board, ESP-IDF Setup | Cannot proceed without MCU + toolchain |
| **P0 (Blocker)** | TCA9548A, 2× MS5837 | I²C address conflict resolution |
| **P0 (Blocker)** | Voltage divider parts (resistors) | ADC protection |
| **P1 (Sensors)** | TDS, pH, Turbidity, NTC, Flow, Ultrasonic, Leak, ACS712 | Core sensing |
| **P1 (I²C)** | TCA9548A, 2× MS5837 | Pressure sensing |
| **P1 (Power)** | 12V→5V DC-DC, 5V→3.3V LDO, TVS, caps | Power distribution |
| **P1 (Outputs)** | Optocouplers (PC817), relays, terminal blocks | Safety actions |
| **P2 (Calibration)** | Buffers, gauges, reference meter | Validation |
| **P2 (Enclosure)** | IP65 box, glands, DIN rail | Environmental |

---

**Document Status**: **DRAFT — NOT PROCURED**  
**All items pending procurement.** No components have been purchased or received.  
**Next Step**: Resolve ESP-IDF environment blocker, then begin procurement.