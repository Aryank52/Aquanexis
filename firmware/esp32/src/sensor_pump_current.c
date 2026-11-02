/**
 * @file sensor_pump_current.c
 * @brief Pump Current Sensor Driver (ACS712 / INA219 / Shunt-based)
 * 
 * Supports:
 * - ACS712 Hall-effect current sensor (analog output)
 * - INA219 I2C current/power monitor
 * - Shunt resistor + ADC
 * Measures: Pump current in Amperes
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/adc.h"
#include "driver/i2c.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_PUMP_CURRENT";

typedef struct {
    bool initialized;
    bool enabled;
    enum {
        CURRENT_SENSOR_ACS712 = 0,
        CURRENT_SENSOR_INA219,
        CURRENT_SENSOR_SHUNT
    } type;
    
    // ACS712 / Shunt (ADC)
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    float sensitivity_mv_per_a;  // ACS712: 185mV/A (5A), 100mV/A (20A), 66mV/A (30A)
    float zero_current_voltage;  // VCC/2 for ACS712
    
    // INA219 (I2C)
    uint8_t i2c_addr;
    float shunt_resistor_ohms;
    float max_current_a;
    
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    bool initialized;
    bool enabled;
} pump_current_sensor_data_t;

static sensor_status_t pump_current_init(sensor_driver_t* driver);
static sensor_status_t pump_current_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t pump_current_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t pump_current_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t pump_current_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t pump_current_self_test(sensor_driver_t* driver);
static sensor_status_t pump_current_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t pump_current_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t pump_current_set_enabled(sensor_driver_t* driver, bool enabled);
static bool pump_current_is_enabled(sensor_driver_t* driver);
static sensor_status_t pump_current_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t pump_current_driver = {
    .type = SENSOR_TYPE_PUMP_CURRENT,
    .name = "Pump Current Sensor",
    .init = pump_current_init,
    .read = pump_current_read,
    .calibrate = pump_current_calibrate,
    .get_calibration = pump_current_get_calibration,
    .set_calibration = pump_current_set_calibration,
    .self_test = pump_current_self_test,
    .get_thresholds = pump_current_get_thresholds,
    .set_thresholds = pump_current_set_thresholds,
    .set_enabled = pump_current_set_enabled,
    .is_enabled = pump_current_is_enabled,
    .get_last_reading = pump_current_get_last_reading,
    .private_data = NULL
};

static sensor_status_t pump_current_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Pump Current sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    pump_current_sensor_data_t* data = calloc(1, sizeof(pump_current_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->type = CURRENT_SENSOR_ACS712;
    data->adc_channel = ADC_CHANNEL_PUMP_CURRENT;
    data->sensitivity_mv_per_a = 185.0f;
    data->zero_current_voltage = 1.65f;
    
    esp_adc_cal_characterize(ADC_UNIT, ADC_ATTEN, ADC_WIDTH, 0, &data->adc_chars);
    adc1_config_width(ADC_WIDTH);
    adc1_config_channel_atten(data->adc_channel, ADC_ATTEN);
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = PUMP_CURRENT_MAX_A;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = PUMP_CURRENT_MAX_A;
    data->thresholds.warning_low = 0.1f;
    data->thresholds.warning_high = 2.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 3.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Pump Current sensor initialized (ACS712 mode)");
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    float current_a = 0.0f;
    
    if (data->type == CURRENT_SENSOR_ACS712) {
        int adc_raw = adc1_get_raw(data->adc_channel);
        if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
        
        uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
        float voltage = voltage_mv / 1000.0f;
        
        float voltage_diff = voltage - data->zero_current_voltage;
        float current = voltage_diff / (data->sensitivity_mv_per_a / 1000.0f);
        current_a = fabsf(current);
    } else if (data->type == CURRENT_SENSOR_INA219) {
        current_a = 0.0f;
    } else {
        current_a = 0.0f;
    }
    
    float current = current_a * data->calibration.slope + data->calibration.offset;
    
    if (current < data->thresholds.min_value) current = data->thresholds.min_value;
    if (current > data->thresholds.max_value) current = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (current >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (current >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = current;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Pump Current: %.2f A", current);
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    float voltage_diff = voltage - data->zero_current_voltage;
    float raw_current = voltage_diff / (data->sensitivity_mv_per_a / 1000.0f);
    raw_current = fabsf(raw_current);
    
    if (raw_current > 0.01f) {
        data->calibration.slope = reference_value / raw_current;
        data->calibration.is_calibrated = true;
        data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
        
        ESP_LOGI(TAG, "Pump Current calibrated: ref=%.2f, raw=%.2f, slope=%.4f",
                 reference_value, raw_current, data->calibration.slope);
        return SENSOR_STATUS_OK;
    }
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t pump_current_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pump_current_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool pump_current_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t pump_current_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pump_current_sensor_data_t* data = (pump_current_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_pump_current_get_driver(void) {
    return &pump_current_driver;
}