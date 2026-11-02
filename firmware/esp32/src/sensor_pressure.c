/**
 * @file sensor_pressure.c
 * @brief Pressure Sensor Driver (MS5837-30BA via TCA9548A I2C Multiplexer)
 * 
 * Supports MS5837-30BA I2C pressure sensors via TCA9548A multiplexer
 * Measures: Pressure in kPa
 * MS5837 Fixed I2C Address: 0x76 (use TCA9548A channels for multiple sensors)
 * TCA9548A I2C Address: 0x70
 * Channel 0: Inlet Pressure (MS5837 @ 0x76)
 * Channel 1: Outlet Pressure (MS5837 @ 0x76)
 */

#include "sensor_interface.h"
#include "aquanexis_config.h"
#include "driver/i2c.h"
#include "esp_log.h"

static const char* TAG = "SENSOR_PRESSURE";

typedef struct {
    bool initialized;
    bool enabled;
    uint8_t tca_channel;  // TCA9548A channel (0=inlet, 1=outlet)
    sensor_calibration_t calibration;
    sensor_thresholds_t thresholds;
    sensor_reading_t last_reading;
    uint32_t last_read_time_ms;
    // MS5837 calibration coefficients
    uint16_t coeff[8];
} pressure_sensor_data_t;

static sensor_status_t pressure_init(sensor_driver_t* driver);
static sensor_status_t pressure_read(sensor_driver_t* driver, sensor_reading_t* reading);
static sensor_status_t pressure_calibrate(sensor_driver_t* driver, float reference_value);
static sensor_status_t pressure_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal);
static sensor_status_t pressure_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal);
static sensor_status_t pressure_self_test(sensor_driver_t* driver);
static sensor_status_t pressure_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds);
static sensor_status_t pressure_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds);
static sensor_status_t pressure_set_enabled(sensor_driver_t* driver, bool enabled);
static bool pressure_is_enabled(sensor_driver_t* driver);
static sensor_status_t pressure_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading);
static esp_err_t tca9548a_select_channel(uint8_t channel);
static esp_err_t pressure_read_coefficients(pressure_sensor_data_t* data);
static float pressure_convert_raw(pressure_sensor_data_t* data, uint32_t raw_pressure, uint32_t raw_temp);
static esp_err_t pressure_i2c_write(pressure_sensor_data_t* data, uint8_t reg, const uint8_t* data_buf, size_t len);
static esp_err_t pressure_i2c_read(pressure_sensor_data_t* data, uint8_t reg, uint8_t* data_buf, size_t len);

static sensor_driver_t inlet_pressure_driver = {
    .type = SENSOR_TYPE_INLET_PRESSURE,
    .name = "Inlet Pressure Sensor",
    .init = pressure_init,
    .read = pressure_read,
    .calibrate = pressure_calibrate,
    .get_calibration = pressure_get_calibration,
    .set_calibration = pressure_set_calibration,
    .self_test = pressure_self_test,
    .get_thresholds = pressure_get_thresholds,
    .set_thresholds = pressure_set_thresholds,
    .set_enabled = pressure_set_enabled,
    .is_enabled = pressure_is_enabled,
    .get_last_reading = pressure_get_last_reading,
    .private_data = NULL
};

static sensor_driver_t outlet_pressure_driver = {
    .type = SENSOR_TYPE_OUTLET_PRESSURE,
    .name = "Outlet Pressure Sensor",
    .init = pressure_init,
    .read = pressure_read,
    .calibrate = pressure_calibrate,
    .get_calibration = pressure_get_calibration,
    .set_calibration = pressure_set_calibration,
    .self_test = pressure_self_test,
    .get_thresholds = pressure_get_thresholds,
    .set_thresholds = pressure_set_thresholds,
    .set_enabled = pressure_set_enabled,
    .is_enabled = pressure_is_enabled,
    .get_last_reading = pressure_get_last_reading,
    .private_data = NULL
};

// Select TCA9548A channel
static esp_err_t tca9548a_select_channel(uint8_t channel) {
    if (channel > 7) return ESP_ERR_INVALID_ARG;
    
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (TCA9548A_ADDR << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, 1 << channel, true);  // Enable channel
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    
    if (ret == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(1));  // Allow multiplexer to switch
    }
    return ret;
}

// Write to pressure sensor (with TCA9548A channel selection)
static esp_err_t pressure_i2c_write(pressure_sensor_data_t* data, uint8_t reg, const uint8_t* data_buf, size_t len) {
    esp_err_t ret = tca9548a_select_channel(data->tca_channel);
    if (ret != ESP_OK) return ret;
    
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (MS5837_ADDR << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, reg, true);
    if (data_buf && len > 0) {
        i2c_master_write(cmd, data_buf, len, true);
    }
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    return ret;
}

// Read from pressure sensor (with TCA9548A channel selection)
static esp_err_t pressure_i2c_read(pressure_sensor_data_t* data, uint8_t reg, uint8_t* data_buf, size_t len) {
    esp_err_t ret = tca9548a_select_channel(data->tca_channel);
    if (ret != ESP_OK) return ret;
    
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (MS5837_ADDR << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, reg, true);
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    if (ret != ESP_OK) return ret;
    
    i2c_cmd_handle_t cmd_read = i2c_cmd_link_create();
    i2c_master_start(cmd_read);
    i2c_master_write_byte(cmd_read, (MS5837_ADDR << 1) | I2C_MASTER_READ, true);
    if (len > 1) {
        i2c_master_read(cmd_read, data_buf, len - 1, I2C_MASTER_ACK);
    }
    i2c_master_read_byte(cmd_read, &data_buf[len - 1], I2C_MASTER_NACK);
    i2c_master_stop(cmd_read);
    ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd_read, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd_read);
    return ret;
}

static sensor_status_t pressure_init(sensor_driver_t* driver) {
    ESP_LOGI(TAG, "Initializing Pressure sensor on TCA9548A channel...");
    
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    
    pressure_sensor_data_t* data = calloc(1, sizeof(pressure_sensor_data_t));
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    
    // Determine TCA channel based on driver type
    data->tca_channel = (driver->type == SENSOR_TYPE_INLET_PRESSURE) ? TCA9548A_CHANNEL_INLET : TCA9548A_CHANNEL_OUTLET;
    data->enabled = true;
    
    // Reset sensor via I2C (through multiplexer)
    esp_err_t ret = pressure_i2c_write(data, 0x1E, NULL, 0);  // Reset command
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to reset pressure sensor on channel %d", data->tca_channel);
    }
    
    vTaskDelay(pdMS_TO_TICKS(10));
    
    // Read calibration coefficients
    if (pressure_read_coefficients(data) != ESP_OK) {
        ESP_LOGW(TAG, "Failed to read pressure sensor coefficients on channel %d, using defaults", data->tca_channel);
        for (int i = 0; i < 8; i++) data->coeff[i] = 0;
    }
    
    data->calibration.offset = PRESSURE_CALIBRATION_OFFSET;
    data->calibration.slope = PRESSURE_CALIBRATION_SLOPE;
    data->calibration.min_value = 0.0f;
    data->calibration.max_value = PRESSURE_MAX_KPA;
    data->calibration.is_calibrated = false;
    
    data->thresholds.min_value = 0.0f;
    data->thresholds.max_value = PRESSURE_MAX_KPA;
    data->thresholds.warning_low = 50.0f;
    data->thresholds.warning_high = 500.0f;
    data->thresholds.critical_low = 0.0f;
    data->thresholds.critical_high = 600.0f;
    
    driver->private_data = data;
    data->initialized = true;
    
    ESP_LOGI(TAG, "Pressure sensor initialized on TCA9548A channel %d", data->tca_channel);
    return SENSOR_STATUS_OK;
}

static esp_err_t pressure_read_coefficients(pressure_sensor_data_t* data) {
    for (int i = 0; i < 8; i++) {
        uint8_t msb, lsb;
        esp_err_t ret = pressure_i2c_read(data, 0xA0 + i * 2, &msb, 1);
        if (ret != ESP_OK) return ret;
        ret = pressure_i2c_read(data, 0xA0 + i * 2 + 1, &lsb, 1);
        if (ret != ESP_OK) return ret;
        data->coeff[i] = (msb << 8) | lsb;
    }
    return ESP_OK;
}

static float pressure_convert_raw(pressure_sensor_data_t* data, uint32_t raw_pressure, uint32_t raw_temp) {
    // MS5837 conversion algorithm
    int64_t dT = (int64_t)raw_temp - ((int64_t)data->coeff[5] << 8);
    int64_t temp = 2000 + dT * data->coeff[6] / 8388608;
    
    int64_t off = ((int64_t)data->coeff[2] << 17) + (dT * data->coeff[4] >> 6);
    int64_t sens = ((int64_t)data->coeff[1] << 16) + (dT * data->coeff[3] >> 7);
    
    // Second order temperature compensation
    if (temp < 2000) {
        int64_t t2 = 3 * dT * dT / 8589934592;
        int64_t off2 = 61 * (temp - 2000) * (temp - 2000) / 16;
        int64_t sens2 = 29 * (temp - 2000) * (temp - 2000) / 16;
        temp -= t2;
        off -= off2;
        sens -= sens2;
    }
    
    int64_t pressure_pa = (raw_pressure * sens / 2097152 - off) / 32768;
    return pressure_pa / 1000.0f;  // Convert to kPa
}

static sensor_status_t pressure_read(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    if (!data->enabled) return SENSOR_STATUS_MISSING;
    
    // Select TCA channel
    esp_err_t ret = tca9548a_select_channel(data->tca_channel);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to select TCA channel %d", data->tca_channel);
        return SENSOR_STATUS_COMM_ERROR;
    }
    
    // Start pressure conversion (OSR=4096, cmd 0x48)
    esp_err_t ret = pressure_i2c_write(data, 0x48, NULL, 0);  // Convert D1 (pressure)
    if (ret != ESP_OK) return SENSOR_STATUS_COMM_ERROR;
    
    vTaskDelay(pdMS_TO_TICKS(10));  // Wait for conversion (OSR=4096 ≈ 9ms)
    
    // Read pressure (3 bytes)
    uint8_t pressure_bytes[3];
    ret = pressure_i2c_read(data, 0x00, pressure_bytes, 3);
    if (ret != ESP_OK) return SENSOR_STATUS_COMM_ERROR;
    uint32_t raw_pressure = (pressure_bytes[0] << 16) | (pressure_bytes[1] << 8) | pressure_bytes[2];
    
    // Read temperature (OSR=4096, cmd 0x58)
    ret = pressure_i2c_write(data, 0x58, NULL, 0);  // Convert D2 (temperature)
    if (ret != ESP_OK) return SENSOR_STATUS_COMM_ERROR;
    
    vTaskDelay(pdMS_TO_TICKS(10));
    
    uint8_t temp_bytes[3];
    ret = pressure_i2c_read(data, 0x00, temp_bytes, 3);
    if (ret != ESP_OK) return SENSOR_STATUS_COMM_ERROR;
    
    uint32_t raw_temp = (temp_bytes[0] << 16) | (temp_bytes[1] << 8) | temp_bytes[2];
    
    // Convert to kPa
    float pressure_kpa = pressure_convert_raw(data, raw_pressure, raw_temp);
    
    // Apply calibration
    float pressure = pressure_kpa * data->calibration.slope + data->calibration.offset;
    
    if (pressure < data->thresholds.min_value) pressure = data->thresholds.min_value;
    if (pressure > data->thresholds.max_value) pressure = data->thresholds.max_value;
    
    sensor_status_t status = SENSOR_STATUS_OK;
    if (pressure <= data->thresholds.critical_low || pressure >= data->thresholds.critical_high) {
        status = SENSOR_STATUS_OUT_OF_RANGE;
    } else if (pressure <= data->thresholds.warning_low || pressure >= data->thresholds.warning_high) {
        status = SENSOR_STATUS_CALIBRATION_DUE;
    }
    
    reading->value = pressure;
    reading->status = status;
    reading->provenance = PROVENANCE_MEASURED;
    reading->timestamp_ms = esp_timer_get_time() / 1000;
    reading->sequence = 0;
    
    data->last_reading = *reading;
    data->last_read_time_ms = reading->timestamp_ms;
    
    ESP_LOGD(TAG, "Pressure (ch%d): %.1f kPa", data->tca_channel, pressure);
    return SENSOR_STATUS_OK;
}

// Calibration, get/set calibration, self-test, thresholds, enable/disable functions remain the same...

static sensor_status_t pressure_calibrate(sensor_driver_t* driver, float reference_value) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    sensor_reading_t reading;
    sensor_status_t status = pressure_read(driver, &reading);
    if (status != SENSOR_STATUS_OK) return status;
    
    if (reading.value > 0.1f) {
        data->calibration.slope = reference_value / reading.value;
        data->calibration.is_calibrated = true;
        data->calibration.last_calibration_ms = esp_timer_get_time() / 1000;
        
        ESP_LOGI(TAG, "Pressure calibrated (ch%d): ref=%.1f, measured=%.1f, slope=%.4f",
                 data->tca_channel, reference_value, reading.value, data->calibration.slope);
        return SENSOR_STATUS_OK;
    }
    return SENSOR_STATUS_FAULT;
}

static sensor_status_t pressure_get_calibration(sensor_driver_t* driver, sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *cal = data->calibration;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pressure_set_calibration(sensor_driver_t* driver, const sensor_calibration_t* cal) {
    if (!driver || !cal) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->calibration = *cal;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pressure_self_test(sensor_driver_t* driver) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data || !data->initialized) return SENSOR_STATUS_NOT_INITIALIZED;
    
    // Try to read coefficients
    if (pressure_read_coefficients(data) != ESP_OK) {
        return SENSOR_STATUS_FAULT;
    }
    return SENSOR_STATUS_OK;
}

static sensor_status_t pressure_get_thresholds(sensor_driver_t* driver, sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *thresholds = data->thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pressure_set_thresholds(sensor_driver_t* driver, const sensor_thresholds_t* thresholds) {
    if (!driver || !thresholds) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->thresholds = *thresholds;
    return SENSOR_STATUS_OK;
}

static sensor_status_t pressure_set_enabled(sensor_driver_t* driver, bool enabled) {
    if (!driver) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    data->enabled = enabled;
    return SENSOR_STATUS_OK;
}

static bool pressure_is_enabled(sensor_driver_t* driver) {
    if (!driver) return false;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    return data && data->enabled;
}

static sensor_status_t pressure_get_last_reading(sensor_driver_t* driver, sensor_reading_t* reading) {
    if (!driver || !reading) return SENSOR_STATUS_COMM_ERROR;
    pressure_sensor_data_t* data = (pressure_sensor_data_t*)driver->private_data;
    if (!data) return SENSOR_STATUS_COMM_ERROR;
    *reading = data->last_reading;
    return SENSOR_STATUS_OK;
}

// Get driver instances
sensor_driver_t* sensor_inlet_pressure_get_driver(void) {
    return &inlet_pressure_driver;
}

sensor_driver_t* sensor_outlet_pressure_get_driver(void) {
    return &outlet_pressure_driver;
}