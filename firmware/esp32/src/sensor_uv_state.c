/**
 * @file sensor_uv_state.c
 * @brief UV Lamp State Sensor Driver
 * 
 * Monitors UV lamp state via:
 * - Digital input (lamp driver feedback)
 * - Current monitoring (lamp ballast current)
 * - Optical sensor (UV intensity)
 * Measures: UV lamp ON/OFF state
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/gpio.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_UV_STATE";

typedef struct {
    bool initialized;
    bool enabled;
    enum {
        UV_MONITOR_GPIO = 0,      // Digital feedback from ballast
        UV_MONITOR_CURRENT,       // Current sensor on ballast input
        UV_MONITOR_OPTICAL        // UV photodiode sensor
    } method;
    
    // GPIO method
    gpio_num_t feedback_gpio;
    
    // Current method
    pump_current_sensor_data_t* current_sensor;
    float current_threshold_a;  // Current above this = lamp ON
    
    // Optical method
    adc_channel_t adc_channel;
    esp_adc_cal_characteristics_t adc_chars;
    float uv_threshold_v;  // Voltage above this = UV detected
    
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    bool initialized;
    bool enabled;
} uv_state_sensor_data_t;

static sensor_status_t uv_state_init(sensor_driver_t* driver);
static sensor_status_t uv_state_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t uv_state_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t uv_state_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t uv_state_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t uv_state_self_test(sensor_driver_t* driver);
static sensor_status_t uv_state_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t uv_state_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t uv_state_set_enabled(sensor_driver_t* driver, bool enabled);
static bool uv_state_is_enabled(sensor_driver_t* driver);
static sensor_status_t uv_state_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t uv_state_driver = {
    .type = SENSOR_TYPE_UV_STATE,
    .name = "UV Lamp State Sensor",
    .init = uv_state_init,
    .read = uv_state_read,
    .calibrate = uv_state_calibrate,
    .get_calibration = uv_state_get_calibration,
    .set_calibration = uv_state_set_calibration,
    .self_test = uv_state_self_test,
    .get_thresholds = uv_state_get_thresholds,
    .set_thresholds = uv_state_set_thresholds,
    .set_enabled = uv_state_set_enabled,
    .is_enabled = uv_state_is_enabled,
    .get_last_reading = uv_state_get_last_reading,
    .private_data = NULL
};

static sensor_status_t uv_state_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing UV State sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    uv_state_sensor_data_t* data = calloc(1, sizeof(uv_state_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->method = UV_MONITOR_GPIO;
    data->feedback_gpio = GPIO_UV_STATE;
    
    // Configure GPIO input with pull-up
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << data->feedback_gpio),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    
    data->current_threshold_a = 0.1f;  // 100mA threshold
    data->uv_threshold_v = 1.0f;  // 1V threshold for optical
    
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
    
    ESP_LOGI(TAG, "UV State sensor initialized (GPIO feedback mode)");
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    bool uv_on = false;
    
    if (data->method == UV_MONITOR_GPIO) {
        // Read digital feedback (active HIGH = lamp ON)
        int level = gpio_get_level(data->feedback_gpio);
        uv_on = (level == 1);
    } else if (data->method == UV_MONITOR_CURRENT && data->current_sensor) {
        // Read current from ballast
        sensor_reading_t current_reading;
        sensor_status_t status = data->current_sensor->read(data->current_sensor, &current_reading);
        if (status == SENSOR_STATUS_OK) {
            uv_on = (current_reading.value >= data->current_threshold_a);
        }
    } else if (data->method == UV_MONITOR_OPTICAL) {
        // Read UV photodiode
        // TODO: Implement ADC reading
        uv_on = false;
    }
    
    reading->value = uv_on ? 1.0f : 0.0f;
    reading->status = uv_on ? SENSOR_STATUS_OK : SENSOR_STATUS_OK;  // Not an error if OFF
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "UV State: %s", uv_on ? "ON" : "OFF");
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_calibrate(sensor_driver_t* driver, float reference_value) {
    // UV state is binary - no analog calibration
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t uv_state_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool uv_state_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t uv_state_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    uv_state_sensor_data_t* data = (uv_state_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_uv_state_get_driver(void) {
    return &uv_state_driver;
}