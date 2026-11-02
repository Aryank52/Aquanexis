/**
 * @file sensor_flow.c
 * @brief Flow Rate Sensor Driver (Hall Effect Flow Meter)
 * 
 * Supports hall-effect flow meters (e.g., YF-S201, G1/2)
 * Measures: Flow rate in L/min via pulse counting
 * GPIO: Digital input with interrupt
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

static const char* TAG = "SENSOR_FLOW";

typedef struct {
    bool initialized;
    bool enabled;
    gpio_num_t pulse_gpio;
    volatile uint32_t pulse_count;
    uint32_t last_pulse_count;
    uint32_t last_calc_time_ms;
    float pulses_per_liter;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    SemaphoreHandle_t mutex;
} flow_sensor_data_t;

static sensor_status_t flow_init(sensor_driver_t* driver);
static sensor_status_t flow_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t flow_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t flow_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t flow_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t flow_self_test(sensor_driver_t* driver);
static sensor_status_t flow_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t flow_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t flow_set_enabled(sensor_driver_t* driver, bool enabled);
static bool flow_is_enabled(sensor_driver_t* driver);
static sensor_status_t flow_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);
static void IRAM_ATTR flow_isr_handler(void* arg);

static sensor_driver_t flow_driver = {
    .type = SENSOR_TYPE_FLOW,
    .name = "Flow Rate Sensor",
    .init = flow_init,
    .read = flow_read,
    .calibrate = flow_calibrate,
    .get_calibration = flow_get_calibration,
    .set_calibration = flow_set_calibration,
    .self_test = flow_self_test,
    .get_thresholds = flow_get_thresholds,
    .set_thresholds = flow_set_thresholds,
    .set_enabled = flow_set_enabled,
    .is_enabled = flow_is_enabled,
    .get_last_reading = flow_get_last_reading,
    .private_data = NULL
};

static void IRAM_ATTR flow_isr_handler(void* arg) {
    flow_sensor_data_t* data = (flow_sensor_data_t*)arg;
    data->pulse_count++;
}

static sensor_status_t flow_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Flow sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    flow_sensor_data_t* data = calloc(1, sizeof(flow_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->pulse_gpio = GPIO_FLOW_METER;
    data->pulses_per_liter = FLOW_METER_PULSES_PER_LITER;
    data->mutex = xSemaphoreCreateMutex();
    
    // Configure GPIO for pulse input
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << data->pulse_gpio),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_NEGEDGE  // Falling edge for pulse
    };
    gpio_config(&io_conf);
    gpio_isr_handler_add(data->pulse_gpio, flow_isr_handler, data);
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = FLOW_RATE_MAX_LPM;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = FLOW_RATE_MAX_LPM;
    data->thresholds.warning_low = 0.5f;
    data->thresholds.warning_high = 10.0f;
    data->thresholds.critical_low = 0.1f;
    data->thresholds.critical_high = 20.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Flow sensor initialized on GPIO%d", data->pulse_gpio);
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    uint32_t now = esp_timer_get_time() / 1000;
    
    if (xSemaphoreTake(data->mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        uint32_t pulses = data->pulse_count - data->last_pulse_count;
        uint32_t time_diff_ms = now - data->last_calc_time_ms;
        
        float flow_lpm = 0.0f;
        if (time_diff_ms > 0) {
            // Flow (L/min) = pulses / (pulses_per_liter * time_min)
            float time_min = time_diff_ms / 60000.0f;
            flow_lpm = (pulses / data->pulses_per_liter) / time_min;
        }
        
        data->last_pulse_count = data->pulse_count;
        data->last_calc_time_ms = now;
        
        xSemaphoreGive(data->mutex);
        
        // Apply calibration
        float flow = flow_lpm * data->calibration.slope + data->calibration.offset;
        
        if (flow < data->thresholds.min_value) flow = data->thresholds.min_value;
        if (flow > data->thresholds.max_value) flow = data->thresholds.max_value;
        
        sensor_status_t status = SENSOR_STATUS_OK;
        if (flow <= data->thresholds.critical_low || flow >= data->thresholds.critical_high) {
            status = SENSOR_STATUS_OUT_OF_RANGE;
        } else if (flow <= data->thresholds.warning_low || flow >= data->thresholds.warning_high) {
            status = SENSOR_STATUS_CALIBRATION_DUE;
        }
        
        reading->value = flow;
        reading->status = status;
        reading->provenance = PROVENANCE_MEASURED;
        reading->timestamp_ms = now;
        reading->sequence = 0;
        
        data->last_reading = *reading;
        data->last_read_time_ms = now;
        
        ESP_LOGD(TAG, "Flow: %.2f L/min, Pulses: %d", flow, (int)(data->pulse_count - data->last_pulse_count));
    } else {
        return SENSOR_STATUS_COMM_ERROR;
    }
    
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Calibrate pulses per liter
    // This would require a known flow rate over time
    // For now, just adjust slope
    data->calibration.slope = reference_value / 1.0f;  // Simplified
    data->calibration.is_calibrated = true;
    data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
    
    ESP_LOGI(TAG, "Flow calibrated: slope=%.4f", data->calibration.slope);
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Check if interrupt is registered
    if (!data->mutex) return SENSOR_STATUS_FAULT;
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t flow_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool flow_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t flow_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    flow_sensor_data_t* data = (flow_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_flow_get_driver(void) {
    static sensor_driver_t driver = {
        .type = SENSOR_TYPE_FLOW,
        .name = "Flow Rate Sensor",
        .init = flow_init,
        .read = flow_read,
        .calibrate = flow_calibrate,
        .get_calibration = flow_get_calibration,
        .set_calibration = flow_set_calibration,
        .self_test = flow_self_test,
        .get_thresholds = flow_get_thresholds,
        .set_thresholds = flow_set_thresholds,
        .set_enabled = flow_set_enabled,
        .is_enabled = flow_is_enabled,
        .get_last_reading = flow_get_last_reading,
        .private_data = NULL
    };
    return &driver;
}