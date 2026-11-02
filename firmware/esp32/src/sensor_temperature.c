/**
 * @file sensor_temperature.c
 * @brief Temperature Sensor Driver (NTC Thermistor via ADC or DS18B20 via 1-Wire)
 * 
 * Supports both NTC thermistor (ADC) and DS18B20 (1-Wire) sensors
 * Measures: Water temperature in °C
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"
#include <math.h>

static const char* TAG = "SENSOR_TEMP";

typedef struct {
    bool initialized;
    bool enabled;
    bool use_1wire;  // true for DS18B20, false for NTC
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    // NTC parameters
    float ntc_beta;
    float ntc_r25;
    float series_resistor;
    // 1-Wire (if used)
    gpio_num_t one_wire_gpio;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
} temp_sensor_data_t;

static sensor_status_t temp_init(sensor_driver_t* driver);
static sensor_status_t temp_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t temp_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t temp_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t temp_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t temp_self_test(sensor_driver_t* driver);
static sensor_status_t temp_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t temp_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t temp_set_enabled(sensor_driver_t* driver, bool enabled);
static bool temp_is_enabled(sensor_driver_t* driver);
static sensor_status_t temp_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t temp_driver = {
    .type = SENSOR_TYPE_TEMPERATURE,
    .name = "Temperature Sensor",
    .init = temp_init,
    .read = temp_read,
    .calibrate = temp_calibrate,
    .get_calibration = temp_get_calibration,
    .set_calibration = temp_set_calibration,
    .self_test = temp_self_test,
    .get_thresholds = temp_get_thresholds,
    .set_thresholds = temp_set_thresholds,
    .set_enabled = temp_set_enabled,
    .is_enabled = temp_is_enabled,
    .get_last_reading = temp_get_last_reading,
    .private_data = NULL
};

static sensor_status_t temp_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Temperature sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    temp_sensor_data_t* data = calloc(1, sizeof(temp_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->use_1wire = false;  // Default to NTC thermistor
    data->adc_channel = ADC_CHANNEL_TEMPERATURE;
    
    esp_adc_cal_characterize(ADC_UNIT, ADC_ATTEN, ADC_WIDTH, 0, &data->adc_chars);
    adc1_config_width(ADC_WIDTH);
    adc1_config_channel_atten(data->adc_channel, ADC_ATTEN);
    
    // NTC 10K thermistor defaults
    data->ntc_beta = 3950.0f;
    data->ntc_r25 = 10000.0f;
    data->series_resistor = 10000.0f;
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = TEMPERATURE_MIN_C;
    data->calibration.max_value = TEMPERATURE_MAX_C;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = TEMPERATURE_MIN_C;
    data->thresholds.max_value = TEMPERATURE_MAX_C;
    data->thresholds.warning_low = 5.0f;
    data->thresholds.warning_high = 40.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 50.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Temperature sensor initialized (NTC mode)");
    return SENSOR_STATUS_OK;
}

static float ntc_to_celsius(temp_sensor_data_t* data, uint32_t adc_voltage_mv) {
    // Convert ADC voltage to resistance
    float voltage = adc_voltage_mv / 1000.0f;
    float vcc = 3.3f;
    float r_ntc = data->series_resistor * voltage / (vcc - voltage);
    
    // Steinhart-Hart equation (simplified Beta parameter equation)
    float temp_k = 1.0f / (1.0f / 298.15f + logf(r_ntc / data->ntc_r25) / data->ntc_beta);
    return temp_k - 273.15f;
}

static sensor_status_t temp_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    if (data->use_1wire) {
        // TODO: Implement DS18B20 1-Wire reading
        reading->value = 25.0f;
        reading->status = SENSOR_STATUS_FAULT;
        reading->provenance = PROVENANCE_SIMULATED;
    } else {
        int adc_raw = adc1_get_raw(data->adc_channel);
        if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
        
        uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
        float temp_c = ntc_to_celsius(data, voltage_mv);
        
        // Apply calibration
        float temp = temp_c * data->calibration.slope + data->calibration.offset;
        
        if (temp < data->thresholds.min_value) temp = data->thresholds.min_value;
        if (temp > data->thresholds.max_value) temp = data->thresholds.max_value;
        
        sensor_status_t status = SENSOR_STATUS_OK;
        if (temp <= data->thresholds.critical_low || temp >= data->thresholds.critical_high) {
            status = SENSOR_STATUS_OUT_OF_RANGE;
        } else if (temp <= data->thresholds.warning_low || temp >= data->thresholds.warning_high) {
            status = SENSOR_STATUS_CALIBRATION_DUE;
        }
        
        reading->value = temp;
        reading->status = status;
        reading->provenance = PROVENANCE_MEASURED;
        reading->timestamp_ms = esp_timer_get_time() / 1000;
        reading->sequence = 0;
        
        data->last_reading = *reading;
        data->last_read_time_ms = reading->timestamp_ms;
        
        ESP_LOGD(TAG, "Temperature: %.1f°C, Voltage: %dmV", temp, esp_adc_cal_raw_to_voltage(adc1_get_raw(data->adc_channel), &data->adc_chars));
    }
    
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // For NTC, calibration adjusts offset
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float measured = ntc_to_celsius(data, voltage_mv);
    
    data->calibration.offset = reference_value - measured;
    data->calibration.is_calibrated = true;
    data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
    
    ESP_LOGI(TAG, "Temperature calibrated: ref=%.1f, measured=%.1f, offset=%.2f", 
             reference_value, measured, data->calibration.offset);
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t temp_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool temp_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t temp_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    temp_sensor_data_t* data = (temp_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_temperature_get_driver(void) {
    static sensor_driver_t driver = {
        .type = SENSOR_TYPE_TEMPERATURE,
        .name = "Temperature Sensor",
        .init = temp_init,
        .read = temp_read,
        .calibrate = temp_calibrate,
        .get_calibration = temp_get_calibration,
        .set_calibration = temp_set_calibration,
        .self_test = temp_self_test,
        .get_thresholds = temp_get_thresholds,
        .set_thresholds = temp_set_thresholds,
        .set_enabled = temp_set_enabled,
        .is_enabled = temp_is_enabled,
        .get_last_reading = temp_get_last_reading,
        .private_data = NULL
    };
    return &driver;
}