/**
 * @file sensor_turbidity.c
 * @brief Turbidity Sensor Driver (DFRobot Gravity Analog Turbidity Sensor)
 * 
 * Measures: Turbidity in NTU
 * I2C or Analog interface
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_TURBIDITY";

typedef struct {
    bool initialized;
    bool enabled;
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
} turbidity_sensor_data_t;

static sensor_status_t turbidity_init(sensor_driver_t* driver);
static sensor_status_t turbidity_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t turbidity_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t turbidity_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t turbidity_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t turbidity_self_test(sensor_driver_t* driver);
static sensor_status_t turbidity_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t turbidity_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t turbidity_set_enabled(sensor_driver_t* driver, bool enabled);
static bool turbidity_is_enabled(sensor_driver_t* driver);
static sensor_status_t turbidity_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t turbidity_driver = {
    .type = SENSOR_TYPE_TURBIDITY,
    .name = "Turbidity Sensor",
    .init = turbidity_init,
    .read = turbidity_read,
    .calibrate = turbidity_calibrate,
    .get_calibration = turbidity_get_calibration,
    .set_calibration = turbidity_set_calibration,
    .self_test = turbidity_self_test,
    .get_thresholds = turbidity_get_thresholds,
    .set_thresholds = turbidity_set_thresholds,
    .set_enabled = turbidity_set_enabled,
    .is_enabled = turbidity_is_enabled,
    .get_last_reading = turbidity_get_last_reading,
    .private_data = NULL
};

static sensor_status_t turbidity_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Turbidity sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    turbidity_sensor_data_t* data = calloc(1, sizeof(turbidity_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->adc_channel = ADC_CHANNEL_TURBIDITY;
    
    esp_adc_cal_characterize(ADC_UNIT, ADC_ATTEN, ADC_WIDTH, 0, &data->adc_chars);
    adc1_config_width(ADC_WIDTH);
    adc1_config_channel_atten(data->adc_channel, ADC_ATTEN);
    
    data->calibration.offset = TURBIDITY_CALIBRATION_OFFSET;
    data->calibration.slope = TURBIDITY_CALIBRATION_SLOPE;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = TURBIDITY_MAX_NTU;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = TURBIDITY_MAX_NTU;
    data->thresholds.warning_low = 0.1f;
    data->thresholds.warning_high = 4.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 10.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Turbidity sensor initialized");
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    
    // Turbidity: voltage inversely proportional to turbidity
    // Clear water ~2.5V, turbid water ~0.5V (depends on sensor)
    float raw_ntu = (3.3f - voltage) * 1000.0f;  // Simplified conversion
    
    float ntu = raw_ntu * data->calibration.slope + data->calibration.offset;
    
    if (ntu < data->thresholds.min_value) ntu = data->thresholds.min_value;
    if (ntu > data->thresholds.max_value) ntu = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (ntu <= data->thresholds.critical_low || ntu >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (ntu <= data->thresholds.warning_low || ntu >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = ntu;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Turbidity: %.1f NTU, Voltage: %.3fV", ntu, voltage_mv / 1000.0f);
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    float raw_ntu = (3.3f - voltage) * 1000.0f;
    
    if (raw_ntu > 0.1f) {
        data->calibration.slope = reference_value / raw_ntu;
        data->calibration.is_calibrated = true;
        data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
        ESP_LOGI(TAG, "Turbidity calibrated: ref=%.1f, raw=%.1f, slope=%.4f", 
                 reference_value, raw_ntu, data->calibration.slope);
        return SENSOR_STATUS_OK;
    }
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t turbidity_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    ESP_LOGI(TAG, "Turbidity calibration set");
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    ESP_LOGI(TAG, "Turbidity thresholds updated");
    return SENSOR_STATUS_OK;
}

static sensor_status_t turbidity_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool turbidity_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t turbidity_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    turbidity_sensor_data_t* data = (turbidity_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_turbidity_get_driver(void) {
    static sensor_driver_t driver = {
        .type = SENSOR_TYPE_TURBIDITY,
        .name = "Turbidity Sensor",
        .init = turbidity_init,
        .read = turbidity_read,
        .calibrate = turbidity_calibrate,
        .get_calibration = turbidity_get_calibration,
        .set_calibration = turbidity_set_calibration,
        .self_test = turbidity_self_test,
        .get_thresholds = turbidity_get_thresholds,
        .set_thresholds = turbidity_set_thresholds,
        .set_enabled = turbidity_set_enabled,
        .is_enabled = turbidity_is_enabled,
        .get_last_reading = turbidity_get_last_reading,
        .private_data = NULL
    };
    return &driver;
}