/**
 * @file sensor_registry.c
 * @brief Sensor Registry Implementation
 * 
 * Manages all sensor drivers and provides unified interface
 */

#include "sensor_interface.h"
#include "sensor_tds.c"
#include "sensor_ph.c"
#include "sensor_turbidity.c"
#include "sensor_temperature.c"
#include "sensor_flow.c"
#include "sensor_pressure.c"
#include "sensor_tank_level.c"
#include "sensor_leak.c"
#include "sensor_pump_current.c"
#include "sensor_pump_power.c"
#include "sensor_uv_state.c"
#include "esp_log.h"

static const char* TAG = "SENSOR_REGISTRY";

void sensor_registry_init(sensor_registry_t* registry) {
    if (!registry) return;
    memset(registry, 0, sizeof(sensor_registry_t));
    ESP_LOGI(TAG, "Sensor registry initialized");
}

sensor_status_t sensor_registry_register(sensor_registry_t* registry, sensor_driver_t* driver) {
    if (!registry || !driver) return SENSOR_STATUS_COMM_ERROR;
    
    if (registry->count >= MAX_SENSORS) {
        ESP_LOGE(TAG, "Sensor registry full");
        return SENSOR_STATUS_FAULT;
    }
    
    registry->drivers[registry->count++] = driver;
    ESP_LOGI(TAG, "Registered sensor: %s (type %d)", driver->name, driver->type);
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_registry_get(sensor_registry_t* registry, sensor_type_t type) {
    if (!registry) return NULL;
    
    for (uint8_t i = 0; i < registry->count; i++) {
        if (registry->drivers[i]->type == type) {
            return registry->drivers[i];
        }
    }
    return NULL;
}

sensor_status_t sensor_registry_init_all(sensor_registry_t* registry) {
    if (!registry) return SENSOR_STATUS_COMM_ERROR;
    
    sensor_status_t overall_status = SENSOR_STATUS_OK;
    
    for (uint8_t i = 0; i < registry->count; i++) {
        sensor_driver_t* driver = registry->drivers[i];
        if (driver && driver->init) {
            sensor_status_t status = driver->init(driver);
            if (status != SENSOR_STATUS_OK) {
                ESP_LOGW(TAG, "Failed to initialize sensor: %s (status %d)", 
                         driver->name, status);
                overall_status = status;
            }
        }
    }
    
    return overall_status;
}

sensor_status_t sensor_registry_read_all(sensor_registry_t* registry, sensor_reading_t* readings) {
    if (!registry || !readings) return SENSOR_STATUS_COMM_ERROR;
    
    sensor_status_t overall_status = SENSOR_STATUS_OK;
    
    for (uint8_t i = 0; i < registry->count; i++) {
        sensor_driver_t* driver = registry->drivers[i];
        if (driver && driver->is_enabled && driver->is_enabled(driver)) {
            sensor_status_t status = driver->read(driver, &readings[driver->type]);
            if (status != SENSOR_STATUS_OK) {
                ESP_LOGW(TAG, "Failed to read sensor: %s (status %d)", 
                         driver->name, status);
                overall_status = status;
            }
        }
    }
    
    return overall_status;
}

sensor_status_t sensor_registry_self_test_all(sensor_registry_t* registry, sensor_status_t* results) {
    if (!registry || !results) return SENSOR_STATUS_COMM_ERROR;
    
    sensor_status_t overall_status = SENSOR_STATUS_OK;
    
    for (uint8_t i = 0; i < registry->count; i++) {
        sensor_driver_t* driver = registry->drivers[i];
        if (driver && driver->self_test) {
            results[i] = driver->self_test(driver);
            if (results[i] != SENSOR_STATUS_OK) {
                overall_status = results[i];
            }
        } else {
            results[i] = SENSOR_STATUS_NOT_INITIALIZED;
        }
    }
    
    return overall_status;
}

uint8_t sensor_registry_get_enabled_count(sensor_registry_t* registry) {
    if (!registry) return 0;
    
    uint8_t count = 0;
    for (uint8_t i = 0; i < registry->count; i++) {
        sensor_driver_t* driver = registry->drivers[i];
        if (driver && driver->is_enabled && driver->is_enabled(driver)) {
            count++;
        }
    }
    return count;
}

// Convenience function to create and populate registry with all available sensors
sensor_registry_t* sensor_registry_create_default(void) {
    sensor_registry_t* registry = malloc(sizeof(sensor_registry_t));
    if (!registry) return NULL;
    
    sensor_registry_init(registry);
    
    // Register all available sensors
    #if SENSOR_TDS_AVAILABLE
    sensor_registry_register(registry, sensor_tds_get_driver());
    #endif
    
    #if SENSOR_CONDUCTIVITY_AVAILABLE
    sensor_registry_register(registry, sensor_tds_get_driver());  // Uses same driver
    #endif
    
    #if SENSOR_PH_AVAILABLE
    sensor_registry_register(registry, sensor_ph_get_driver());
    #endif
    
    #if SENSOR_TURBIDITY_AVAILABLE
    sensor_registry_register(registry, sensor_turbidity_get_driver());
    #endif
    
    #if SENSOR_TEMPERATURE_AVAILABLE
    sensor_registry_register(registry, sensor_temperature_get_driver());
    #endif
    
    #if SENSOR_FLOW_AVAILABLE
    sensor_registry_register(registry, sensor_flow_get_driver());
    #endif
    
    #if SENSOR_INLET_PRESSURE_AVAILABLE
    sensor_registry_register(registry, sensor_inlet_pressure_get_driver());
    #endif
    
    #if SENSOR_OUTLET_PRESSURE_AVAILABLE
    sensor_registry_register(registry, sensor_outlet_pressure_get_driver());
    #endif
    
    #if SENSOR_TANK_LEVEL_AVAILABLE
    sensor_registry_register(registry, sensor_tank_level_get_driver());
    #endif
    
    #if SENSOR_LEAK_AVAILABLE
    sensor_registry_register(registry, sensor_leak_get_driver());
    #endif
    
    #if SENSOR_PUMP_CURRENT_AVAILABLE
    sensor_registry_register(registry, sensor_pump_current_get_driver());
    #endif
    
    #if SENSOR_PUMP_POWER_AVAILABLE
    sensor_registry_register(registry, sensor_pump_power_get_driver());
    #endif
    
    #if SENSOR_UV_STATE_AVAILABLE
    sensor_registry_register(registry, sensor_uv_state_get_driver());
    #endif
    
    return registry;
}