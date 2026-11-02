/**
 * @file sensor_leak.c
 * @brief Leak Detection Sensor Driver
 * 
 * Simple digital leak detection sensor (water contact sensor)
 * Active LOW when leak detected (water bridges contacts)
 * GPIO: Digital input with pull-up
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_LEAK";

typedef struct {
    bool initialized;
    bool enabled;
    gpio_num_t leak_gpio;
    bool last_state;
    uint32_t leak_start_time_ms;
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    bool initialized;
    bool enabled;
} leak_sensor_data_t;

static sensor_status_t leak_init(sensor_driver_t* driver);
static sensor_status_t leak_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t leak_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t leak_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t leak_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t leak_self_test(sensor_driver_t* driver);
static sensor_status_t leak_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t leak_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t leak_set_enabled(sensor_driver_t* driver, bool enabled);
static bool leak_is_enabled(sensor_driver_t* driver);
static sensor_status_t leak_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t leak_driver = {
    .type = SENSOR_TYPE_LEAK,
    .name = "Leak Detection Sensor",
    .init = leak_init,
    .read = leak_read,
    .calibrate = leak_calibrate,
    .get_calibration = leak_get_calibration,
    .set_calibration = leak_set_calibration,
    .self_test = leak_self_test,
    .get_thresholds = leak_get_thresholds,
    .set_thresholds = leak_set_thresholds,
    .set_enabled = leak_set_enabled,
    .is_enabled = leak_is_enabled,
    .get_last_reading = leak_get_last_reading,
    .private_data = NULL
};

static sensor_status_t leak_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Leak sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    leak_sensor_data_t* data = calloc(1, sizeof(leak_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->leak_gpio = GPIO_LEAK_DETECT;
    
    // Configure GPIO with pull-up (active low when leak)
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << data->leak_gpio),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = 1.0f;
    data->calibration.is_calibrated = true;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = 1.0f;
    data->thresholds.warning_low = 0.0f;
    data->thresholds.warning_high = 1.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 1.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Leak sensor initialized on GPIO%d", data->leak_gpio);
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    // Read GPIO (active LOW = leak detected)
    int level = gpio_get_level(data->leak_gpio);
    bool leak_detected = (level == 0);  // Active low
    
    // Track leak start time
    if (leak_detected && !data->last_state) {
        data->leak_start_time_ms = esp_timer_get_time() / 1000;
        ESP_LOGW(TAG, "LEAK DETECTED!");
    } else if (!leak_detected && data->last_state) {
        ESP_LOGI(TAG, "Leak cleared");
    }
    data->last_state = leak_detected;
    
    reading->value = leak_detected ? 1.0f : 0.0f;
    reading->status = leak_detected ? SENSOR_STATUS_OUT_OF_RANGE : SENSOR_STATUS_OK;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Leak: %s", leak_detected ? "DETECTED" : "OK");
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_calibrate(sensor_driver_t* driver, float reference_value) {
    // Leak sensor is binary - no calibration needed
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t leak_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool leak_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t leak_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    leak_sensor_data_t* data = (leak_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_leak_get_driver(void) {
    return &leak_driver;
}