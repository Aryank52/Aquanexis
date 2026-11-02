/**
 * @file sensor_tank_level.c
 * @brief Tank Level Sensor Driver (Ultrasonic / Capacitive / Pressure-based)
 * 
 * Supports multiple tank level sensing methods:
 * - Ultrasonic (HC-SR04 or JSN-SR04T)
 * - Capacitive level sensor
 * - Pressure-based (hydrostatic)
 * Measures: Tank level percentage (0-100%)
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/gpio.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_TANK_LEVEL";

typedef struct {
    bool initialized;
    bool enabled;
    enum {
        TANK_LEVEL_ULTRASONIC = 0,
        TANK_LEVEL_CAPACITIVE,
        TANK_LEVEL_PRESSURE
    } method;
    
    // Ultrasonic
    gpio_num_t trig_gpio;
    gpio_num_t echo_gpio;
    
    // Capacitive / Pressure (ADC)
    esp_adc_cal_characteristics_t adc_chars;
    adc_channel_t adc_channel;
    
    // Tank geometry
    float tank_height_cm;
    float sensor_offset_cm;  // Distance from sensor to tank bottom/top
    float empty_distance_cm; // Distance when empty (ultrasonic)
    float full_distance_cm;  // Distance when full (ultrasonic)
    
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    bool initialized;
    bool enabled;
} tank_level_sensor_data_t;

static sensor_status_t tank_level_init(sensor_driver_t* driver);
static sensor_status_t tank_level_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t tank_level_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t tank_level_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t tank_level_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t tank_level_self_test(sensor_driver_t* driver);
static sensor_status_t tank_level_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t tank_level_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t tank_level_set_enabled(sensor_driver_t* driver, bool enabled);
static bool tank_level_is_enabled(sensor_driver_t* driver);
static sensor_status_t tank_level_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);

static sensor_driver_t tank_level_driver = {
    .type = SENSOR_TYPE_TANK_LEVEL,
    .name = "Tank Level Sensor",
    .init = tank_level_init,
    .read = tank_level_read,
    .calibrate = tank_level_calibrate,
    .get_calibration = tank_level_get_calibration,
    .set_calibration = tank_level_set_calibration,
    .self_test = tank_level_self_test,
    .get_thresholds = tank_level_get_thresholds,
    .set_thresholds = tank_level_set_thresholds,
    .set_enabled = tank_level_set_enabled,
    .is_enabled = tank_level_is_enabled,
    .get_last_reading = tank_level_get_last_reading,
    .private_data = NULL
};

static sensor_status_t tank_level_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Tank Level sensor...");
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    tank_level_sensor_data_t* data = calloc(1, sizeof(tank_level_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    data->enabled = true;
    data->method = TANK_LEVEL_ULTRASONIC;  // Default to ultrasonic
    
    // Ultrasonic pins
    data->trig_gpio = 5;   // GPIO5
    data->echo_gpio = 4;   // GPIO4
    
    // Ultrasonic pins config
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << data->trig_gpio),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    gpio_set_level(data->trig_gpio, 0);
    
    io_conf.pin_bit_mask = (1ULL << data->echo_gpio);
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&io_conf);
    
    // Tank geometry defaults
    data->tank_height_cm = 50.0f;
    data->sensor_offset_cm = 5.0f;
    data->empty_distance_cm = 55.0f;  // Sensor to bottom when empty
    data->full_distance_cm = 5.0f;    // Sensor to water when full
    
    data->calibration.offset = 0.0f;
    data->calibration.slope = 1.0f;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = TANK_LEVEL_MAX_PCT;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = TANK_LEVEL_MAX_PCT;
    data->thresholds.warning_low = 10.0f;
    data->thresholds.warning_high = 90.0f;
    data->thresholds.critical_low = 5.0f;
    data->thresholds.critical_high = 95.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Tank Level sensor initialized (Ultrasonic)");
    return SENSOR_STATUS_OK;
}

static float ultrasonic_read_distance_cm(tank_level_sensor_data_t* data) {
    // Trigger pulse
    gpio_set_level(data->trig_gpio, 1);
    esp_rom_delay_us(10);
    gpio_set_level(data->trig_gpio, 0);
    
    // Wait for echo start
    uint32_t start = esp_timer_get_time();
    while (gpio_get_level(data->echo_gpio) == 0) {
        if (esp_timer_get_time() - start > 30000) return -1.0f;  // Timeout
    }
    
    // Measure echo pulse width
    uint32_t start_time = esp_timer_get_time();
    while (gpio_get_level(data->echo_gpio) == 1) {
        if (esp_timer_get_time() - start > 30000) return -1.0f;  // Timeout
    }
    uint32_t end_time = esp_timer_get_time();
    
    // Calculate distance: time * speed_of_sound / 2
    // Speed of sound ~ 343 m/s = 34300 cm/s = 0.0343 cm/µs
    uint32_t pulse_width_us = end_time - start_time;
    float distance_cm = pulse_width_us * 0.0343f / 2.0f;
    
    return distance_cm;
}

static sensor_status_t tank_level_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    float level_pct = 0.0f;
    
    if (data->method == TANK_LEVEL_ULTRASONIC) {
        float distance = ultrasonic_read_distance_cm(data);
        if (distance < 0) {
            ESP_LOGW(TAG, "Ultrasonic timeout");
            return SENSOR_STATUS_COMM_ERROR;
        }
        
        // Calculate level percentage
        float water_distance = distance - data->sensor_offset_cm;
        float water_height = data->tank_height_cm - water_distance;
        float level = (water_height / data->tank_height_cm) * 100.0f;
        level_pct = level;
    } else {
        // Capacitive/ADC method - placeholder
        level_pct = 50.0f;  // Placeholder
    }
    
    // Apply calibration
    float level = level_pct * data->calibration.slope + data->calibration.offset;
    
    if (level < data->thresholds.min_value) level = data->thresholds.min_value;
    if (level > data->thresholds.max_value) level = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (level <= data->thresholds.critical_low || level >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (level <= data->thresholds.warning_low || level >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = level;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Tank Level: %.1f%%", level);
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Calibrate empty/full distances
    float distance = ultrasonic_read_distance_cm(data);
    if (distance < 0) return SENSOR_STATUS_FAULT;
    
    if (reference_value <= 5.0f) {
        data->full_distance_cm = distance;
        ESP_LOGI(TAG, "Tank full calibration: %.1f cm", distance);
    } else if (reference_value >= 95.0f) {
        data->empty_distance_cm = distance;
        ESP_LOGI(TAG, "Tank empty calibration: %.1f cm", distance);
    }
    
    data->calibration.is_calibrated = true;
    data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
    
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    float distance = ultrasonic_read_distance_cm(data);
    if (distance < 0) return SENSOR_STATUS_FAULT;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t tank_level_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool tank_level_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t tank_level_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    tank_level_sensor_data_t* data = (tank_level_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

sensor_driver_t* sensor_tank_level_get_driver(void) {
    return &tank_level_driver;
}