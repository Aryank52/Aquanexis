/**
 * @file sensor_tds.c
 * @brief TDS/EC Sensor Driver (Gravity Analog TDS Sensor)
 * 
 * Supports DFRobot Gravity Analog TDS Sensor / EC Sensor
 * I2C Address: 0x63 (Gravity sensor hub)
 * Measures: Total Dissolved Solids (ppm) and Electrical Conductivity (µS/cm)
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/i2c.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"
#include <math.h>
#include <string.h>

static const char* TAG = "SENSOR_TDS";

// TDS Sensor Private Data
typedef struct {
    bool initialized;
    bool enabled;
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    float temperature_compensation;  // For temperature compensation
} tds_sensor_data_t;

// Forward declarations
static sensor_status_t tds_init(sensor_driver_t* driver);
static sensor_status_t tds_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t tds_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t tds_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t tds_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t tds_self_test(sensor_driver_t* driver);
static sensor_status_t tds_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t tds_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t tds_set_enabled(sensor_driver_t* driver, bool enabled);
static bool tds_is_enabled(sensor_driver_t* driver);
static sensor_status_t tds_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

// TDS Sensor Driver Instance
static sensor_driver_t tds_driver = {
    .type = SENSOR_TYPE_TDS,
    .name = "TDS/EC Sensor",
    .init = tds_init,
    .read = tds_read,
    .calibrate = tds_calibrate,
    .get_calibration = tds_get_calibration,
    .set_calibration = tds_set_calibration,
    .self_test = tds_self_test,
    .get_thresholds = tds_get_thresholds,
    .set_thresholds = tds_set_thresholds,
    .set_enabled = tds_set_enabled,
    .is_enabled = tds_is_enabled,
    .get_last_reading = tds_get_last_reading,
    .private_data = NULL
};

// Temperature compensation coefficient for TDS (2% per °C from 25°C)
#define TDS_TEMP_COEFFICIENT 0.02f
#define TDS_REF_TEMPERATURE 25.0f

static sensor_status_t tds_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing TDS sensor...");
    
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = calloc(1, sizeof(tds_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->adc_channel = ADC_CHANNEL_TDS;
    
    // Initialize ADC calibration
    esp_adc_cal_characterize(ADC_UNIT, ADC_ATTEN, ADC_WIDTH, 0, &data->adc_chars);
    
    // Configure ADC channel
    adc1_config_width(ADC_WIDTH);
    adc1_config_channel_atten(data->adc_channel, ADC_ATTEN);
    
    // Default calibration
    data->calibration.offset = TDS_CALIBRATION_OFFSET;
    data->calibration.slope = TDS_CALIBRATION_SLOPE;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = TDS_MAX_PPM;
    data->calibration.is_calibrated = false;
    
    // Default thresholds
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = TDS_MAX_PPM;
    data->thresholds.warning_low = 50.0f;
    data->thresholds.warning_high = 500.0f;
    data->thresholds.critical_low = 10.0f;
    data->thresholds.critical_high = 1000.0f;
    
    data->temperature_compensation = TDS_TEMP_COEFFICIENT;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "TDS sensor initialized successfully");
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    // Read ADC value
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) {
        ESP_LOGE(TAG, "ADC read failed");
        return SENSOR_STATUS_COMM_ERROR;
    }
    
    // Convert to voltage
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    
    // Convert voltage to TDS (Gravity TDS sensor formula)
    // TDS (ppm) = (Voltage / 3.3) * Slope * 1000 + Offset
    // For Gravity TDS: ~0-2.3V corresponds to 0-1000ppm
    float raw_tds = (voltage / 3.3f) * 1000.0f * data->calibration.slope + data->calibration.offset;
    
    // Apply temperature compensation if temperature sensor available
    // TDS_compensated = TDS_raw / (1 + coeff * (temp - 25))
    float compensated_tds = raw_tds;
    if (data->temperature_compensation > 0) {
        // In real implementation, get temperature from temperature sensor
        // For now, assume 25°C reference
        float temp = 25.0f;  // Would come from temperature sensor
        compensated_tds = raw_tds / (1.0f + data->temperature_compensation * (temp - TDS_REF_TEMPERATURE));
    }
    
    // Apply calibration
    float tds_value = compensated_tds * data->calibration.slope + data->calibration.offset;
    
    // Clamp to valid range
    if (tds_value < data->thresholds.min_value) tds_value = data->thresholds.min_value;
    if (tds_value > data->thresholds.max_value) tds_value = data->thresholds.max_value;
    
    // Calculate conductivity from TDS (approximate: EC µS/cm ≈ TDS ppm * 2)
    float conductivity = tds_value * 2.0f;
    
    // Determine status
    sensor_status_t status = SENSOR_STATUS_OK;
    if (tds_value <= data->thresholds.critical_low || tds_value >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (tds_value <= data->thresholds.warning_low || tds_value >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;  // Using as "suspect"
    }
    
    // Fill reading
    reading->value = tds_value;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;  // Set by caller
    
    // Update last reading
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "TDS: %.1f ppm, Conductivity: %.1f µS/cm, Voltage: %.3fV", 
             tds_value, conductivity, voltage);
    
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Read current raw value
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    float voltage = voltage_mv / 1000.0f;
    float raw_tds = (voltage / 3.3f) * 1000.0f;
    
    // Calculate new slope
    if (raw_tds > 0.1f) {
        data->calibration.slope = reference_value / raw_tds;
        data->calibration.is_calibrated = true;
        data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
        
        ESP_LOGI(TAG, "TDS calibrated: reference=%.1f, raw=%.1f, slope=%.4f", 
                 reference_value, raw_tds, data->calibration.slope);
        return SENSOR_STATUS_OK;
    }
    
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t tds_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->calibration = *cal;
    ESP_LOGI(TAG, "TDS calibration set: offset=%.2f, slope=%.4f", cal->offset, cal->slope);
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Read ADC to verify communication
    int adc_raw = adc1_get_raw(data->adc_channel);
    if (adc_raw < 0) return SENSOR_STATUS_COMM_ERROR;
    
    // Check if value is reasonable (not rail-to-rail)
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_raw, &data->adc_chars);
    if (voltage_mv < 50 || voltage_mv > 3300) {
        ESP_LOGW(TAG, "TDS self-test: voltage out of expected range: %dmV", voltage_mv);
        return SENSOR_STATUS_FAULT;
    }
    
    ESP_LOGI(TAG, "TDS self-test passed: voltage=%dmV", voltage_mv);
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->thresholds = *thresholds;
    ESP_LOGI(TAG, "TDS thresholds updated");
    return SENSOR_STATUS_OK;
}

static sensor_status_t tds_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = enabled;
    ESP_LOGI(TAG, "TDS sensor %s", enabled ? "enabled" : "disabled");
    return SENSOR_STATUS_OK;
}

static bool tds_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t tds_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    
    tds_sensor_data_t* data = (tds_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

// Export driver instance
sensor_driver_t* sensor_tds_get_driver(void) {
    return &tds_driver;
}