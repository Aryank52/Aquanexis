/**
 * @file sensor_interface.h
 * @brief Sensor Driver Interface for AquaNexis ESP32
 * 
 * Abstract interface for all sensor drivers. Each sensor implements
 * this interface for consistent initialization, reading, and calibration.
 */

#ifndef SENSOR_INTERFACE_H
#define SENSOR_INTERFACE_H

#include <stdint.h>
#include <stdbool.h>
#include "aquanexis_config.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Sensor Types and Data Structures
// ============================================================================

typedef enum {
    SENSOR_TYPE_TDS = 0,
    SENSOR_TYPE_CONDUCTIVITY,
    SENSOR_TYPE_PH,
    SENSOR_TYPE_TURBIDITY,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_FLOW,
    SENSOR_TYPE_INLET_PRESSURE,
    SENSOR_TYPE_OUTLET_PRESSURE,
    SENSOR_TYPE_TANK_LEVEL,
    SENSOR_TYPE_LEAK,
    SENSOR_TYPE_PUMP_CURRENT,
    SENSOR_TYPE_PUMP_POWER,
    SENSOR_TYPE_UV_STATE,
    SENSOR_TYPE_COUNT
} sensor_type_t;

typedef enum {
    SENSOR_STATUS_OK = 0,
    SENSOR_STATUS_NOT_INITIALIZED,
    SENSOR_STATUS_COMM_ERROR,
    SENSOR_STATUS_OUT_OF_RANGE,
    SENSOR_STATUS_CALIBRATION_DUE,
    SENSOR_STATUS_FAULT,
    SENSOR_STATUS_MISSING
} sensor_status_t;

typedef enum {
    PROVENANCE_MEASURED = 0,
    PROVENANCE_SIMULATED,
    PROVENANCE_CALCULATED,
    PROVENANCE_MODEL_PREDICTED
} data_provenance_t;

typedef struct {
    float value;
    sensor_status_t status;
    data_provenance_t provenance;
    uint32_t timestamp_ms;
    uint32_t sequence;
} sensor_reading_t;

typedef struct {
    float offset;
    float slope;
    float min_value;
    float max_value;
    uint32_t last_calibration_ms;
    bool is_calibrated;
} sensor_calibration_t;

typedef struct {
    float min_value;
    float max_value;
    float warning_low;
    float warning_high;
    float critical_low;
    float critical_high;
} sensor_thresholds_t;

// ============================================================================
// Sensor Driver Interface
// ============================================================================

typedef struct sensor_driver_t sensor_driver_t;

struct sensor_driver_t {
    sensor_type_t type;
    const char* name;
    
    // Initialize sensor hardware
    // Returns SENSOR_STATUS_OK on success
    sensor_status_t (*init)(sensor_driver_t* driver);
    
    // Read sensor value
    // Returns SENSOR_STATUS_OK on success, fills reading struct
    sensor_status_t (*read)(sensor_driver_t* driver, sensor_reading_t* reading);
    
    // Calibrate sensor with known reference value
    // Returns SENSOR_STATUS_OK on success
    sensor_status_t (*calibrate)(sensor_driver_t* driver, float reference_value);
    
    // Get current calibration
    sensor_status_t (*get_calibration)(sensor_driver_t* driver, sensor_calibration_t* cal);
    
    // Set calibration parameters
    sensor_status_t (*set_calibration)(sensor_driver_t* driver, const sensor_calibration_t* cal);
    
    // Perform self-test
    // Returns SENSOR_STATUS_OK if healthy
    sensor_status_t (*self_test)(sensor_driver_t* driver);
    
    // Get sensor thresholds
    sensor_status_t (*get_thresholds)(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
    
    // Set sensor thresholds
    sensor_status_t (*set_thresholds)(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
    
    // Enable/disable sensor
    sensor_status_t (*set_enabled)(sensor_driver_t* driver, bool enabled);
    
    // Check if sensor is enabled
    bool (*is_enabled)(sensor_driver_t* driver);
    
    // Get last reading without triggering new measurement
    sensor_status_t (*get_last_reading)(sensor_driver_t* driver, sensor_reading_t* reading);
    
    // Private data pointer
    void* private_data;
};

// ============================================================================
// Sensor Registry
// ============================================================================

#define MAX_SENSORS SENSOR_TYPE_COUNT

typedef struct {
    sensor_driver_t* drivers[MAX_SENSORS];
    uint8_t count;
} sensor_registry_t;

// Initialize sensor registry
void sensor_registry_init(sensor_registry_t* registry);

// Register a sensor driver
sensor_status_t sensor_registry_register(sensor_registry_t* registry, sensor_driver_t* driver);

// Get driver by type
sensor_driver_t* sensor_registry_get(sensor_registry_t* registry, sensor_type_t type);

// Initialize all registered sensors
sensor_status_t sensor_registry_init_all(sensor_registry_t* registry);

// Read all enabled sensors
sensor_status_t sensor_registry_read_all(sensor_registry_t* registry, sensor_reading_t* readings);

// Self-test all sensors
sensor_status_t sensor_registry_self_test_all(sensor_registry_t* registry, sensor_status_t* results);

// Get count of enabled sensors
uint8_t sensor_registry_get_enabled_count(sensor_registry_t* registry);

#ifdef __cplusplus
}
#endif

#endif // SENSOR_INTERFACE_H