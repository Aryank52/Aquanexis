/**
 * @file main.c
 * @brief AquaNexis ESP32 Main Application
 * 
 * Main entry point for ESP32 firmware. Initializes all subsystems,
 * runs sensor reading loop, handles communication with backend,
 * and executes safety actions.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_mac.h"
#include "esp_ota_ops.h"
#include "esp_sleep.h"

#include "aquanexis_config.h"
#include "sensor_interface.h"
#include "sensor_registry.c"
#include "comm_interface.h"
#include "comm_manager.c"

static const char* TAG = "AQUANEXIS_MAIN";

// WiFi configuration
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1
#define MAX_WIFI_RETRY     10

static EventGroupHandle_t s_wifi_event_group;
static int s_retry_num = 0;
static sensor_registry_t* g_sensor_registry = NULL;
static comm_manager_t* g_comm_manager = NULL;
static char g_device_id[DEVICE_ID_MAX_LEN] = {0};
static char g_jwt_token[JWT_TOKEN_MAX_LEN] = {0};
static uint32_t g_telemetry_sequence = 0;
static uint32_t g_last_telemetry_ms = 0;
static uint32_t g_last_safety_check_ms = 0;
static uint32_t g_last_health_check_ms = 0;

// WiFi event handler
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < MAX_WIFI_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "WiFi retry %d/%d", s_retry_num, MAX_WIFI_RETRY);
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
        ESP_LOGI(TAG, "WiFi disconnected");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

static esp_err_t wifi_init_sta(void) {
    s_wifi_event_group = xEventGroupCreate();
    
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_got_ip));
    
    // Get WiFi credentials from NVS or config
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = CONFIG_WIFI_SSID,
            .password = CONFIG_WIFI_PASSWORD,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
            .pmf_cfg = {
                .capable = true,
                .required = false
            },
        },
    };
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    ESP_LOGI(TAG, "WiFi initialization complete");
    
    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
            WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
            pdFALSE,
            pdFALSE,
            portMAX_DELAY);
    
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "Connected to WiFi");
        return ESP_OK;
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGE(TAG, "Failed to connect to WiFi");
        return ESP_FAIL;
    }
    
    return ESP_FAIL;
}

// Generate device ID from MAC address
static void generate_device_id(char* device_id, size_t max_len) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    snprintf(device_id, max_len, "AQX-%02X%02X%02X%02X%02X%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

// Load device credentials from NVS
static esp_err_t load_credentials(void) {
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open("aquanexis", NVS_READONLY, &nvs_handle);
    if (err != ESP_OK) return err;
    
    size_t len = DEVICE_ID_MAX_LEN;
    err = nvs_get_str(nvs_handle, "device_id", g_device_id, &len);
    if (err != ESP_OK) {
        // Generate new device ID
        generate_device_id(g_device_id, DEVICE_ID_MAX_LEN);
        nvs_close(nvs_handle);
        return save_credentials();
    }
    
    len = JWT_TOKEN_MAX_LEN;
    err = nvs_get_str(nvs_handle, "jwt_token", g_jwt_token, &len);
    if (err != ESP_OK) {
        g_jwt_token[0] = '\0';
    }
    
    nvs_close(nvs_handle);
    return ESP_OK;
}

static esp_err_t save_credentials(void) {
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open("aquanexis", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) return err;
    
    err = nvs_set_str(nvs_handle, "device_id", g_device_id);
    if (err != ESP_OK) goto fail;
    
    err = nvs_set_str(nvs_handle, "jwt_token", g_jwt_token);
    if (err != ESP_OK) goto fail;
    
    err = nvs_commit(nvs_handle);
    
fail:
    nvs_close(nvs_handle);
    return err;
}

// Initialize all sensors
static esp_err_t init_sensors(void) {
    ESP_LOGI(TAG, "Initializing sensors...");
    
    g_sensor_registry = sensor_registry_create_default();
    if (!g_sensor_registry) {
        ESP_LOGE(TAG, "Failed to create sensor registry");
        return ESP_FAIL;
    }
    
    sensor_status_t status = sensor_registry_init_all(g_sensor_registry);
    if (status != SENSOR_STATUS_OK) {
        ESP_LOGW(TAG, "Some sensors failed to initialize (status %d)", status);
        // Continue anyway - some sensors may work
    }
    
    uint8_t enabled_count = sensor_registry_get_enabled_count(g_sensor_registry);
    ESP_LOGI(TAG, "Sensors initialized: %d enabled", enabled_count);
    
    return ESP_OK;
}

// Initialize communication
static esp_err_t init_communication(void) {
    ESP_LOGI(TAG, "Initializing communication...");
    
    g_comm_manager = comm_manager_create();
    if (!g_comm_manager) {
        ESP_LOGE(TAG, "Failed to create comm manager");
        return ESP_FAIL;
    }
    
    comm_config_t config;
    comm_config_default(&config);
    strncpy(config.backend_url, "https://api.aquanexis.local", BACKEND_URL_MAX_LEN - 1);
    strncpy(config.device_id, g_device_id, DEVICE_ID_MAX_LEN - 1);
    strncpy(config.jwt_token, g_jwt_token, JWT_TOKEN_MAX_LEN - 1);
    strncpy(config.firmware_version, AQUANEXIS_FIRMWARE_VERSION, FIRMWARE_VERSION_MAX_LEN - 1);
    
    comm_status_t status = g_comm_manager->init(g_comm_manager, &config);
    if (status != COMM_STATUS_OK) {
        ESP_LOGE(TAG, "Failed to init comm manager: %d", status);
        return ESP_FAIL;
    }
    
    status = g_comm_manager->connect(g_comm_manager);
    if (status != COMM_STATUS_OK) {
        ESP_LOGW(TAG, "Could not connect to backend (will retry): %d", status);
    }
    
    // Authenticate if we have a token
    if (g_jwt_token[0] != '\0') {
        status = g_comm_manager->authenticate(g_comm_manager, g_jwt_token);
        if (status != COMM_STATUS_OK) {
            ESP_LOGW(TAG, "Authentication failed, will retry: %d", status);
        }
    }
    
    return ESP_OK;
}

// Read all sensors and send telemetry
static void telemetry_task(void* pvParameters) {
    sensor_reading_t readings[SENSOR_TYPE_COUNT];
    telemetry_response_t response;
    
    while (1) {
        uint32_t now = esp_timer_get_time() / 1000;
        
        // Check if it's time to send telemetry
        if (now - g_last_telemetry_ms >= SENSOR_REPORT_INTERVAL_MS) {
            // Read all sensors
            memset(readings, 0, sizeof(readings));
            sensor_status_t status = sensor_registry_read_all(g_sensor_registry, readings);
            
            if (status == SENSOR_STATUS_OK) {
                // Send telemetry
                if (g_comm_manager && g_comm_manager->is_authenticated(g_comm_manager)) {
                    comm_status_t comm_status = g_comm_manager->send_telemetry(
                        g_comm_manager, readings, g_telemetry_sequence++, &response);
                    
                    if (comm_status == COMM_STATUS_OK && response.success) {
                        ESP_LOGI(TAG, "Telemetry sent: seq=%d, accepted=%d", 
                                 g_telemetry_sequence - 1, response.accepted);
                    } else if (comm_status == COMM_STATUS_AUTH_FAILED) {
                        // Try to refresh token
                        ESP_LOGW(TAG, "Auth failed, attempting token refresh...");
                        token_refresh_response_t token_resp;
                        if (g_comm_manager->refresh_token(g_comm_manager, &token_resp) == COMM_STATUS_OK 
                            && token_resp.success) {
                            strncpy(g_jwt_token, token_resp.new_jwt_token, JWT_TOKEN_MAX_LEN - 1);
                            save_credentials();
                            ESP_LOGI(TAG, "Token refreshed successfully");
                        } else {
                            ESP_LOGE(TAG, "Token refresh failed");
                        }
                    }
                } else {
                    ESP_LOGW(TAG, "Comm not ready, skipping telemetry send");
                }
            } else {
                ESP_LOGW(TAG, "Sensor read failed: %d", status);
            }
            
            g_last_telemetry_ms = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));  // Check every second
    }
}

// Safety monitoring task
static void safety_task(void* pvParameters) {
    while (1) {
        uint32_t now = esp_timer_get_time() / 1000;
        
        if (now - g_last_safety_check_ms >= 5000) {  // Check every 5 seconds
            // Read critical safety sensors
            sensor_reading_t readings[SENSOR_TYPE_COUNT];
            sensor_registry_read_all(g_sensor_registry, readings);
            
            // Check leak
            if (readings[SENSOR_TYPE_LEAK].value > 0.5f) {
                ESP_LOGE(TAG, "SAFETY: LEAK DETECTED!");
                // Trigger safety action
                // In production, this would activate valves/pumps
            }
            
            // Check pressure
            float inlet_pressure = readings[SENSOR_TYPE_INLET_PRESSURE].value;
            if (inlet_pressure > SAFETY_PRESSURE_MAX_KPA) {
                ESP_LOGE(TAG, "SAFETY: OVERPRESSURE: %.1f kPa", inlet_pressure);
            }
            
            // Check flow
            float flow = readings[SENSOR_TYPE_FLOW].value;
            if (flow < SAFETY_FLOW_MIN_LPM) {
                ESP_LOGE(TAG, "SAFETY: LOW FLOW: %.2f L/min", flow);
            }
            
            // Check pump current
            float current = readings[SENSOR_TYPE_PUMP_CURRENT].value;
            if (current > SAFETY_PUMP_CURRENT_MAX_A) {
                ESP_LOGE(TAG, "SAFETY: OVERCURRENT: %.2f A", current);
            }
            
            g_last_safety_check_ms = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// Health monitoring task
static void health_task(void* pvParameters) {
    while (1) {
        uint32_t now = esp_timer_get_time() / 1000;
        
        if (now - g_last_health_check_ms >= HEALTH_CHECK_INTERVAL_MS) {
            // Self-test all sensors
            sensor_status_t results[SENSOR_TYPE_COUNT];
            sensor_registry_self_test_all(g_sensor_registry, results);
            
            int failed = 0;
            for (int i = 0; i < SENSOR_TYPE_COUNT; i++) {
                if (results[i] != SENSOR_STATUS_OK) {
                    ESP_LOGW(TAG, "Sensor %d self-test failed: %d", i, results[i]);
                    failed++;
                }
            }
            
            // Check communication
            if (g_comm_manager) {
                bool connected = g_comm_manager->is_connected(g_comm_manager);
                bool authenticated = g_comm_manager->is_authenticated(g_comm_manager);
                
                if (!connected) {
                    ESP_LOGW(TAG, "Communication disconnected, attempting reconnect...");
                    g_comm_manager->connect(g_comm_manager);
                }
                
                if (!authenticated && g_jwt_token[0] != '\0') {
                    g_comm_manager->authenticate(g_comm_manager, g_jwt_token);
                }
            }
            
            // Log heap info
            ESP_LOGI(TAG, "Health check: sensors failed=%d, free heap=%d bytes", 
                     failed, esp_get_free_heap_size());
            
            g_last_health_check_ms = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}

// OTA update task
static void ota_task(void* pvParameters) {
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(3600000));  // Check every hour
        
        if (g_comm_manager && g_comm_manager->is_authenticated(g_comm_manager)) {
            char ota_url[256] = {0};
            char version[64] = {0};
            
            comm_status_t status = g_comm_manager->check_ota_update(g_comm_manager, ota_url, version);
            if (status == COMM_STATUS_OK && ota_url[0] != '\0') {
                ESP_LOGI(TAG, "OTA update available: %s", version);
                // In production, implement OTA update here
            }
        }
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "Starting AquaNexis ESP32 Firmware v%s", AQUANEXIS_FIRMWARE_VERSION);
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize WiFi
    ESP_ERROR_CHECK(wifi_init_sta());
    
    // Generate/load device ID
    generate_device_id(g_device_id, DEVICE_ID_MAX_LEN);
    load_credentials();
    ESP_LOGI(TAG, "Device ID: %s", g_device_id);
    
    // Initialize sensors
    ESP_ERROR_CHECK(init_sensors());
    
    // Initialize communication
    ESP_ERROR_CHECK(init_communication());
    
    // Create tasks
    xTaskCreate(telemetry_task, "telemetry_task", 8192, NULL, 5, NULL);
    xTaskCreate(safety_task, "safety_task", 4096, NULL, 10, NULL);
    xTaskCreate(health_task, "health_task", 4096, NULL, 3, NULL);
    xTaskCreate(ota_task, "ota_task", 4096, NULL, 2, NULL);
    
    ESP_LOGI(TAG, "All tasks started. System running.");
    
    // Main loop - just monitor
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        
        // Print status
        ESP_LOGI(TAG, "Status: heap=%d, sensors=%d, comm=%s, auth=%s",
                 esp_get_free_heap_size(),
                 sensor_registry_get_enabled_count(g_sensor_registry),
                 g_comm_manager && g_comm_manager->is_connected(g_comm_manager) ? "connected" : "disconnected",
                 g_comm_manager && g_comm_manager->is_authenticated(g_comm_manager) ? "yes" : "no");
    }
}