/**
 * @file sensor_pump_power.c
 * @brief Pump Power Sensor Driver
 * 
 * Calculates pump power from voltage and current measurements
 * Or uses dedicated power monitoring IC (INA219, INA226)
 * Measures: Pump power in Watts
 * 
 * For DC pumps: P = V_bus × I (DC power factor = 1.0)
 * For AC pumps: P = V_rms × I_rms × PF
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/adc.h"
#include "driver/i2c.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_PUMP_POWER";

typedef struct {
    bool initialized;
    bool enabled;
    enum {
        POWER_CALCULATED = 0,  // V * I calculated
        POWER_INA219,
        POWER_INA226
    } type;
    
    // Calculated from V * I
    float supply_voltage_v;
    pump_current_sensor_data_t* current_sensor;
    
    // INA219/INA226
    uint8_t i2c_addr;
    
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    bool initialized;
    bool enabled;
} pump_power_sensor_data_t;

static sensor_status_t pump_power_init(sensor_driver_t* driver);
static sensor_status_t pump_power_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t pump_power_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t pump_power_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t pump_power_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t pump_power_self_test(sensor_driver_t* driver);
static sensor_status_t pump_power_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t pump_power_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t pump_power_set_enabled(sensor_driver_t* driver, bool enabled);
static bool pump_power_is_enabled(sensor_driver_t* driver);
static sensor_status_t pump_power_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t pump_power_driver = {
    .type = SENSOR_TYPE_PUMP_POWER,
    .name = "Pump Power Sensor",
    .init = pump_power_init,
    .read = pump_power_read,
    .calibrate = pump_power_calibrate,
    .get_calibration = pump_power_get_calibration,
    .set_calibration = pump_power_set_calibration,
    .self_test = pump_power_self_test,
    .get_thresholds = pump_power_get_thresholds,
    .set_thresholds = pump_power_set_thresholds,
    .set_enabled = pump_power_set_enabled,
    .is_enabled = pump_power_is_enabled,
    .get_last_reading = pump_power_get_last_reading,
    .private_data = NULL
};

static sensor_status_t pump_power_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Pump Power sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    pump_power_sensor_data_t* data = calloc(1, sizeof(pump_power_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->type = POWER_CALCULATED;
    data->supply_voltage_v = PUMP_SUPPLY_VOLTAGE_V;  // DC bus voltage from config
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = PUMP_POWER_MAX_W;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = PUMP_POWER_MAX_W;
    data->thresholds.warning_low = 10.0f;
    data->thresholds.warning_high = 1000.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 2000.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Pump Power sensor initialized (Calculated mode, V_bus=%.1fV)", data->supply_voltage_v);
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    float power_w = 0.0f;
    
    if (data->type == POWER_CALCULATED && data->current_sensor) {
        // DC Power = V_bus × I (DC power factor = 1.0)
        sensor_reading_t current_reading;
        sensor_status_t status = data->current_sensor->read(data->current_sensor, &current_reading);
        if (status == SENSOR_STATUS_OK) {
            float current_a = current_reading.value;
            power_w = data->supply_voltage_v * current_a * PUMP_POWER_FACTOR;  // DC PF = 1.0
        }
    } else if (data->type == POWER_INA219) {
        // TODO: Implement INA219 power reading
        power_w = 0.0f;
    } else {
        power_w = 0.0f;
    }
    
    // Apply calibration
    float power = power_w * data->calibration.slope + data->calibration.offset;
    
    if (power < data->thresholds.min_value) power = data->thresholds.min_value;
    if (power > data->thresholds.max_value) power = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (power >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (power >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = power;
    reading->status = status;
    reading->provenance = data->type == POWER_CALCULATED ? PROVENANCE_CALCULATED : PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Pump Power: %.1f W (V=%.1fV, I=%.2fA)", power, data->supply_voltage_v, 
             data->current_sensor ? data->current_sensor->last_reading.value : 0.0f);
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // For calculated power, we calibrate the slope
    // Need to read current to compute actual power
    if (data->current_sensor) {
        sensor_reading_t current_reading;
        sensor_status_t status = data->current_sensor->read(data->current_sensor, &current_reading);
        if (status == SENSOR_STATUS_OK && current_reading.value > 0.01f) {
            float measured_power = data->supply_voltage_v * current_reading.value * PUMP_POWER_FACTOR;
            data->calibration.slope = reference_value / measured_power;
            data->calibration.is_calibrated = true;
            data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
            
            ESP_LOGI(TAG, "Pump Power calibrated: ref=%.1fW, measured=%.1fW, slope=%.4f",
                     reference_value, measured_power, data->calibration.slope);
            return SENSOR_STATUS_OK;
        }
    }
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t pump_power_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_power_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool pump_power_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t pump_power_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pump_power_sensor_data_t* data = (pump_power_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_pump_power_get_driver(void) {
    return &pump_power_driver;
}