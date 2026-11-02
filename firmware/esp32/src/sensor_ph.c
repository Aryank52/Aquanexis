/**
 * @file sensor_ph.c
 * @brief pH Sensor Driver (Gravity Analog pH Sensor)
 * 
 * Supports DFRobot Gravity Analog pH Sensor
 * I2C Address: 0x63 (shared with TDS on Gravity hub)
 * Measures: pH (0-14)
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_PH";

typedef struct {
    bool initialized;
    bool enabled;
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    float temperature_compensation;  // pH temperature compensation
} ph_sensor_data_t;

static sensor_status_t ph_init(sensor_driver_t* driver);
static sensor_status_t ph_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t ph_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t ph_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t ph_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t ph_self_test(sensor_driver_t* driver);
static sensor_status_t ph_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t ph_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t ph_set_enabled(sensor_driver_t* driver, bool enabled);
static bool ph_is_enabled(sensor_driver_t* driver);
static sensor_status_t ph_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t ph_driver = {
    .type = SENSOR_TYPE_PH,
    .name = "pH Sensor",
    .init = ph_init,
    .read = ph_read,
    .calibrate = ph_calibrate,
    .get_calibration = ph_get_calibration,
    .set_calibration = ph_set_calibration,
    .self_test = ph_self_test,
    .get_thresholds = ph_get_thresholds,
    .set_thresholds = ph_set_thresholds,
    .set_enabled = ph_set_enabled,
    .is_enabled = ph_is_enabled,
    .get_last_reading = ph_get_last_reading,
    .private_data = NULL
};

// pH temperature compensation: -0.003 pH/°C from 25°C (typical for glass electrode)
#define PH_TEMP_COEFFICIENT -0.003f
#define PH_REF_TEMPERATURE 25.0f
#define PH_NEUTRAL_VOLTAGE 1.5f  // Voltage at pH 7.0
#define PH_SLOPE -5.7f  // mV/pH (theoretical -59.16mV/pH at 25°C, but sensor dependent)

static sensor_status_t ph_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing pH sensor...");
    
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    ph_sensor_data_t* data = calloc(1, sizeof(ph_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->adc_channel = ADC_CHANNEL_PH;
    
    esp_adc_cal_characterize(ADC_UNIT, ADC_ATTEN, ADC_WIDTH, 0, &data->adc_chars);
    adc1_config_width(ADC_WIDTH);
    adc1_config_channel_atten(data->adc_channel, ADC_ATTEN);
    
    // Default calibration (will need two-point calibration for accuracy)
    data->calibration.offset = PH_CALIBRATION_OFFSET;
    data->calibration.slope = PH_CALIBRATION_SLOPE;
    data->calibration.min_value = PH_MIN;
    data->calibration.max_value = PH_MAX;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = PH_MIN;
    data->thresholds.max_value = PH_MAX;
    data->thresholds.warning_low = 6.0f;
    data->thresholds.warning_high = 8.5f;
    data->thresholds.critical_low = 4.0f;
    data->thresholds.critical_high = 10.0f;
    
    data->temperature_compensation = PH_TEMP_COEFFICIENT;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "pH sensor initialized successfully");
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) {
        ESP_LOGE(TAG, "ADC read failed");
        return SENSOR_STATUS_COMM_ERROR;
    }
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    
    // pH = 7.0 + (V_neutral - V_measured) / Slope
    // For Gravity pH sensor: slope ~ -5.7V/pH unit
    float raw_ph = 7.0f + (PH_NEUTRAL_VOLTAGE - voltage) / (PH_SLOPE / 1000.0f);
    
    // Apply calibration
    float ph_value = raw_ph * data->calibration.slope + data->calibration.offset;
    
    // Apply temperature compensation
    // pH_compensated = pH_raw + coeff * (temp - 25)
    float temp = 25.0f;  // Would come from temperature sensor
    ph_value += data->temperature_compensation * (temp - PH_REF_TEMPERATURE);
    
    // Clamp
    if (ph_value < data->thresholds.min_value) ph_value = data->thresholds.min_value;
    if (ph_value > data->thresholds.max_value) ph_value = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (ph_value <= data->thresholds.critical_low || ph_value >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (ph_value <= data->thresholds.warning_low || ph_value >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = ph_value;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "pH: %.2f, Voltage: %.3fV", ph_value, voltage);
    
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // For two-point calibration, we'd need two reference values
    // This is simplified single-point calibration
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    float raw_ph = 7.0f + (PH_NEUTRAL_VOLTAGE - voltage) / (PH_SLOPE / 1000.0f);
    
    if (fabsf(raw_ph - reference_value) > 0.1f) {
        data->calibration.offset = reference_value - raw_ph;
        data->calibration.is_calibrated = true;
        data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
        
        ESP_LOGI(TAG, "pH calibrated: reference=%.2f, raw=%.2f, offset=%.4f", 
                 reference_value, raw_ph, data->calibration.offset);
        return SENSOR_STATUS_OK;
    }
    
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t ph_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    ESP_LOGI(TAG, "pH calibration set: offset=%.2f, slope=%.4f", cal->offset, cal->slope);
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    if (voltage_mv < 100 || voltage_mv > 3000) {
        ESP_LOGW(TAG, "pH self-test: voltage out of range: %dmV", voltage_mv);
        return SENSOR_STATUS_FAULT;
    }
    
    ESP_LOGI(TAG, "pH self-test passed: voltage=%dmV", voltage_mv);
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    ESP_LOGI(TAG, "pH thresholds updated");
    return SENSOR_STATUS_OK;
}

static sensor_status_t ph_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    ESP_LOGI(TAG, "pH sensor %s", enabled ? "enabled" : "disabled");
    return SENSOR_STATUS_OK;
}

static bool ph_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t ph_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    ph_sensor_data_t* data = (ph_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_ph_get_driver(void) {
    return &ph_driver;
}