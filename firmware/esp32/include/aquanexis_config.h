/**
 * @file aquanexis_config.h
 * @brief AquaNexis ESP32 Firmware Configuration
 * 
 * Hardware revision and pin mapping for AquaNexis water monitoring system.
 * Supports ESP32-S3 with integrated WiFi/BLE.
 */

#ifndef AQUANEXIS_CONFIG_H
#define AQUANEXIS_CONFIG_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Firmware Version
// ============================================================================
#define AQUANEXIS_FIRMWARE_VERSION "1.0.0"
#define AQUANEXIS_HARDWARE_REVISION "A"
#define AQUANEXIS_DEVICE_MODEL "AquaNexis-S3"

// ============================================================================
// Hardware Pin Mapping (ESP32-S3)
// ============================================================================

// I2C Bus (Pressure Sensors - using I2C multiplexer TCA9548A on 0x70)
// MS5837 has fixed address 0x76 - use TCA9548A channels 0 (inlet) and 1 (outlet)
#define I2C_MASTER_SCL_IO           7   // GPIO7  - I2C SCL
#define I2C_MASTER_SDA_IO           6   // GPIO6  - I2C SDA
#define I2C_MASTER_NUM              I2C_NUM_0
#define I2C_MASTER_FREQ_HZ          100000
#define I2C_MASTER_TX_BUF_DISABLE   0
#define I2C_MASTER_RX_BUF_DISABLE   0

// I2C Multiplexer (TCA9548A)
#define TCA9548A_ADDR               0x70
#define TCA9548A_CHANNEL_INLET      0   // Channel 0: Inlet MS5837 @ 0x76
#define TCA9548A_CHANNEL_OUTLET     1   // Channel 1: Outlet MS5837 @ 0x76
#define MS5837_ADDR                 0x76  // Fixed address for MS5837

// SPI Bus (Display, SD Card if present)
#define SPI_MASTER_HOST             SPI2_HOST
#define SPI_MASTER_MISO_IO          13  // GPIO13
#define SPI_MASTER_MOSI_IO          11  // GPIO11
#define SPI_MASTER_SCLK_IO          12  // GPIO12
#define SPI_MASTER_CS_IO            10  // GPIO10

// UART (Debug, Modbus if needed)
#define UART_NUM                    UART_NUM_0
#define UART_TXD                    43  // GPIO43
#define UART_RXD                    44  // GPIO44
#define UART_BAUD_RATE              115200

// ADC Channels (Analog Sensors) - ESP32-S3 ADC1 channels 0-9 on GPIO1-10
// NOTE: ADC2 cannot be used when WiFi is active
#define ADC_UNIT                    ADC_UNIT_1
#define ADC_ATTEN                   ADC_ATTEN_DB_12
#define ADC_WIDTH                   ADC_WIDTH_BIT_12

// Sensor ADC Channels - NO CONFLICTS with I2C/GPIO
#define ADC_CHANNEL_TDS             ADC_CHANNEL_0   // GPIO1 - TDS/EC
#define ADC_CHANNEL_PH              ADC_CHANNEL_1   // GPIO2 - pH
#define ADC_CHANNEL_TURBIDITY       ADC_CHANNEL_2   // GPIO3 - Turbidity
#define ADC_CHANNEL_TEMPERATURE     ADC_CHANNEL_3   // GPIO4 - Temperature (NTC)
#define ADC_CHANNEL_PUMP_CURRENT    ADC_CHANNEL_4   // GPIO5 - Pump Current (ACS712)
#define ADC_CHANNEL_TANK_LEVEL      ADC_CHANNEL_5   // GPIO6 - Tank Level (capacitive backup)
// NOTE: GPIO6-7 reserved for I2C, so tank level ADC is alternative only
// GPIO8-9 available for future use

// Digital Inputs
#define GPIO_LEAK_DETECT            15  // GPIO15 - Leak detection (active low)
#define GPIO_FLOW_METER             16  // GPIO16 - Flow meter pulse
#define GPIO_UV_STATE               17  // GPIO17 - UV lamp state feedback
#define GPIO_ULTRASONIC_TRIG        5   // GPIO5 - Ultrasonic Trig
#define GPIO_ULTRASONIC_ECHO        4   // GPIO4 - Ultrasonic Echo (with voltage divider!)

// Digital Outputs (Relays/Valves - LOW VOLTAGE CONTROL ONLY)
#define GPIO_INLET_VALVE            18  // GPIO18 - Inlet valve control (3.3V logic)
#define GPIO_OUTLET_VALVE           19  // GPIO19 - Outlet valve control (3.3V logic)
#define GPIO_PUMP_RELAY             20  // GPIO20 - Pump relay control (3.3V logic)
#define GPIO_UV_LAMP                21  // GPIO21 - UV lamp control (3.3V logic)

// LED Indicators
#define GPIO_LED_STATUS             48  // GPIO48 - Status LED (built-in on ESP32-S3)
#define GPIO_LED_ERROR              47  // GPIO47 - Error LED
#define GPIO_LED_COMM               2   // GPIO2  - Communication LED

// I2C Addresses (via TCA9548A multiplexer)
#define MS5837_ADDR                 0x76  // Fixed address for MS5837 (both sensors)
// TCA9548A channels: 0=Inlet, 1=Outlet, both at 0x76
#define I2C_ADDR_TEMPERATURE        0x48    // ADS1115 for NTC temperature (optional)
// Tank level sensor (capacitive) - optional
#define I2C_ADDR_TANK_LEVEL         0x40

// ============================================================================
// Sensor Configuration
// ============================================================================

// Sampling Intervals (milliseconds)
#define SENSOR_SAMPLE_INTERVAL_MS       1000    // 1 Hz base sampling
#define SENSOR_REPORT_INTERVAL_MS       10000   // 10s reporting interval
#define SENSOR_CALIBRATION_INTERVAL_MS  3600000 // 1 hour calibration check

// Sensor Thresholds
#define TDS_MAX_PPM                     5000
#define PH_MIN                          0.0
#define PH_MAX                          14.0
#define TURBIDITY_MAX_NTU               1000
#define TEMPERATURE_MIN_C               -20.0
#define TEMPERATURE_MAX_C               80.0
#define FLOW_RATE_MAX_LPM               100.0
#define PRESSURE_MAX_KPA                2000.0
#define TANK_LEVEL_MAX_PCT              100.0
#define PUMP_CURRENT_MAX_A              20.0
#define PUMP_POWER_MAX_W                10000.0

// Pump Power Calculation - DC Pump on 12V/24V bus
#define PUMP_SUPPLY_VOLTAGE_V           24.0f   // DC bus voltage (adjust per installation)
#define PUMP_POWER_FACTOR               1.0f    // DC power factor = 1.0

// Calibration Defaults
#define TDS_CALIBRATION_OFFSET          0.0
#define TDS_CALIBRATION_SLOPE           1.0
#define PH_CALIBRATION_OFFSET           0.0
#define PH_CALIBRATION_SLOPE            1.0
#define TURBIDITY_CALIBRATION_OFFSET    0.0
#define TURBIDITY_CALIBRATION_SLOPE     1.0
#define PRESSURE_CALIBRATION_OFFSET     0.0
#define PRESSURE_CALIBRATION_SLOPE      1.0

// Flow Meter
#define FLOW_METER_PULSES_PER_LITER     450  // Adjust based on sensor

// Ultrasonic Tank Level
#define ULTRASONIC_TIMEOUT_US           30000
#define SPEED_OF_SOUND_CM_PER_US        0.0343f

// ============================================================================
// Communication Configuration
// ============================================================================

// WiFi
#define WIFI_SSID_MAX_LEN               32
#define WIFI_PASSWORD_MAX_LEN           64
#define WIFI_CONNECT_TIMEOUT_MS         15000
#define WIFI_RECONNECT_INTERVAL_MS      30000

// MQTT / HTTP
#define BACKEND_URL_MAX_LEN             128
#define DEVICE_ID_MAX_LEN               36
#define JWT_TOKEN_MAX_LEN               512
#define FIRMWARE_VERSION_MAX_LEN        32

// Telemetry
#define TELEMETRY_SEQUENCE_MAX          0xFFFFFFFF
#define TELEMETRY_BUFFER_SIZE           100     // Buffered readings for batch send
#define TELEMETRY_BATCH_MAX             50

// Timeouts
#define HTTP_TIMEOUT_MS                 10000
#define MQTT_KEEPALIVE_S                60
#define MQTT_RECONNECT_MS               5000

// OTA
#define OTA_URL_MAX_LEN                 256
#define OTA_BUFFER_SIZE                 8192

// ============================================================================
// Safety Configuration (Low Voltage Control Only)
// ============================================================================

// These are 3.3V logic signals ONLY - DO NOT connect mains directly
// All high-voltage switching MUST be done through external relays/contactors

#define SAFETY_LEAK_ACTION_CLOSE_INLET  true
#define SAFETY_LEAK_ACTION_STOP_PUMP    true
#define SAFETY_LEAK_COOLDOWN_SEC        300

#define SAFETY_PRESSURE_MAX_KPA         600.0
#define SAFETY_PRESSURE_ACTION_OPEN_RELIEF true
#define SAFETY_PRESSURE_COOLDOWN_SEC    60

#define SAFETY_FLOW_MIN_LPM             0.1
#define SAFETY_DRY_RUN_ACTION_STOP_PUMP true
#define SAFETY_DRY_RUN_COOLDOWN_SEC     120

#define SAFETY_PUMP_CURRENT_MAX_A       2.5
#define SAFETY_OVERCURRENT_ACTION_STOP_PUMP true
#define SAFETY_OVERCURRENT_COOLDOWN_SEC 180

// ============================================================================
// Watchdog and Health
// ============================================================================

#define WATCHDOG_TIMEOUT_SEC            30
#define HEARTBEAT_INTERVAL_MS           5000
#define HEALTH_CHECK_INTERVAL_MS        60000

// ============================================================================
// Feature Flags
// ============================================================================

#define FEATURE_WIFI_ENABLED            1
#define FEATURE_MQTT_ENABLED            1
#define FEATURE_HTTP_ENABLED            1
#define FEATURE_OTA_ENABLED             1
#define FEATURE_SIMULATOR_MODE          0  // Set to 1 for testing without hardware
#define FEATURE_DEBUG_LOGGING           1

// Sensor Availability (0 = not installed, 1 = installed)
#define SENSOR_TDS_AVAILABLE            1
#define SENSOR_CONDUCTIVITY_AVAILABLE   1
#define SENSOR_PH_AVAILABLE             1
#define SENSOR_TURBIDITY_AVAILABLE      1
#define SENSOR_TEMPERATURE_AVAILABLE    1
#define SENSOR_FLOW_AVAILABLE           1
#define SENSOR_INLET_PRESSURE_AVAILABLE 1
#define SENSOR_OUTLET_PRESSURE_AVAILABLE 1
#define SENSOR_TANK_LEVEL_AVAILABLE     1
#define SENSOR_LEAK_AVAILABLE           1
#define SENSOR_PUMP_CURRENT_AVAILABLE   1
#define SENSOR_PUMP_POWER_AVAILABLE     1
#define SENSOR_UV_STATE_AVAILABLE       1

#ifdef __cplusplus
}
#endif

#endif // AQUANEXIS_CONFIG_H