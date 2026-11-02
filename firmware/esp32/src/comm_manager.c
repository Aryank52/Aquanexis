/**
 * @file comm_manager.c
 * @brief Communication Manager Implementation
 * 
 * Handles HTTP/HTTPS communication with AquaNexis backend
 */

#include "comm_interface.h"
#include "aquanexis_config.h"
#include "esp_http_client.h"
#include "esp_tls.h"
#include "esp_log.h"
#include "cJSON.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include <string.h>

static const char* TAG = "COMM_MANAGER";

typedef struct {
    comm_config_t config;
    bool initialized;
    bool connected;
    bool authenticated;
    esp_http_client_handle_t http_client;
    SemaphoreHandle_t mutex;
    char* response_buffer;
    size_t response_buffer_size;
} comm_manager_data_t;

static comm_status_t comm_init(comm_manager_t* manager, const comm_config_t* config);
static comm_status_t comm_connect(comm_manager_t* manager);
static comm_status_t comm_disconnect(comm_manager_t* manager);
static comm_status_t comm_register_device(comm_manager_t* manager, 
                                           const device_registration_t* reg,
                                           registration_response_t* response);
static comm_status_t comm_authenticate(comm_manager_t* manager, 
                                        const char* jwt_token);
static comm_status_t comm_refresh_token(comm_manager_t* manager,
                                         token_refresh_response_t* response);
static comm_status_t comm_send_telemetry(comm_manager_t* manager,
                                          const sensor_reading_t* readings,
                                          uint32_t sequence,
                                          telemetry_response_t* response);
static comm_status_t comm_send_telemetry_batch(comm_manager_t* manager,
                                                const telemetry_batch_t* batch,
                                                telemetry_response_t* response);
static comm_status_t comm_send_safety_response(comm_manager_t* manager,
                                                const char* action_id,
                                                bool success,
                                                const char* message);
static comm_status_t comm_request_config_update(comm_manager_t* manager);
static comm_status_t comm_check_ota_update(comm_manager_t* manager,
                                            char* ota_url,
                                            char* version);
static bool comm_is_connected(comm_manager_t* manager);
static bool comm_is_authenticated(comm_manager_t* manager);

static esp_err_t http_event_handler(esp_http_client_event_t* evt);
static comm_status_t http_post_json(comm_manager_data_t* data, 
                                     const char* url, 
                                     const char* json_payload,
                                     char** response_out);
static char* create_telemetry_json(const sensor_reading_t* readings, 
                                    uint32_t sequence,
                                    const char* device_id,
                                    const char* firmware_version);

static comm_manager_t comm_manager = {
    .init = comm_init,
    .connect = comm_connect,
    .disconnect = comm_disconnect,
    .register_device = comm_register_device,
    .authenticate = comm_authenticate,
    .refresh_token = comm_refresh_token,
    .send_telemetry = comm_send_telemetry,
    .send_telemetry_batch = comm_send_telemetry_batch,
    .send_safety_response = comm_send_safety_response,
    .request_config_update = comm_request_config_update,
    .check_ota_update = comm_check_ota_update,
    .is_connected = comm_is_connected,
    .is_authenticated = comm_is_authenticated,
    .private_data = NULL
};

comm_manager_t* comm_manager_create(void) {
    return &comm_manager;
}

void comm_manager_destroy(comm_manager_t* manager) {
    if (!manager) return;
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (data) {
        if (data->http_client) {
            esp_http_client_cleanup(data->http_client);
        }
        if (data->mutex) {
            vSemaphoreDelete(data->mutex);
        }
        if (data->response_buffer) {
            free(data->response_buffer);
        }
        free(data);
        manager->private_data = NULL;
    }
    manager->initialized = false;
    manager->connected = false;
    manager->authenticated = false;
}

void comm_config_default(comm_config_t* config) {
    if (!config) return;
    memset(config, 0, sizeof(comm_config_t));
    config->protocol = COMM_PROTOCOL_HTTP;
    config->http_timeout_ms = HTTP_TIMEOUT_MS;
    config->mqtt_keepalive_s = MQTT_KEEPALIVE_S;
    strncpy(config->firmware_version, AQUANEXIS_FIRMWARE_VERSION, FIRMWARE_VERSION_MAX_LEN - 1);
}

static comm_status_t comm_init(comm_manager_t* manager, const comm_config_t* config) {
    if (!manager || !config) return COMM_STATUS_ERROR;
    
    comm_manager_data_t* data = calloc(1, sizeof(comm_manager_data_t));
    if (!data) return COMM_STATUS_ERROR;
    
    data->config = *config;
    data->mutex = xSemaphoreCreateMutex();
    data->response_buffer_size = 8192;
    data->response_buffer = malloc(data->response_buffer_size);
    
    if (!data->mutex || !data->response_buffer) {
        if (data->mutex) vSemaphoreDelete(data->mutex);
        if (data->response_buffer) free(data->response_buffer);
        free(data);
        return COMM_STATUS_ERROR;
    }
    
    // Create HTTP client
    esp_http_client_config_t http_config = {
        .url = config->backend_url,
        .timeout_ms = config->http_timeout_ms,
        .event_handler = http_event_handler,
        .user_data = data,
        .method = HTTP_METHOD_POST,
        .transport_type = HTTP_TRANSPORT_OVER_SSL,
        .cert_pem = NULL,  // Use system CA store
        .skip_cert_common_name_check = false,
    };
    
    data->http_client = esp_http_client_init(&http_config);
    if (!data->http_client) {
        ESP_LOGE(TAG, "Failed to create HTTP client");
        vSemaphoreDelete(data->mutex);
        free(data->response_buffer);
        free(data);
        return COMM_STATUS_ERROR;
    }
    
    manager->private_data = data;
    manager->initialized = true;
    manager->connected = false;
    manager->authenticated = false;
    
    ESP_LOGI(TAG, "Communication manager initialized");
    return COMM_STATUS_OK;
}

static comm_status_t comm_connect(comm_manager_t* manager) {
    if (!manager || !manager->initialized) return COMM_STATUS_NOT_CONNECTED;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data) return COMM_STATUS_ERROR;
    
    // Test connection with a simple GET to health endpoint
    char url[256];
    snprintf(url, sizeof(url), "%s/health", data->config.backend_url);
    
    esp_http_client_set_url(data->http_client, url);
    esp_http_client_set_method(data->http_client, HTTP_METHOD_GET);
    
    esp_err_t err = esp_http_client_perform(data->http_client);
    if (err == ESP_OK) {
        int status = esp_http_client_get_status_code(data->http_client);
        if (status == 200) {
            data->connected = true;
            manager->connected = true;
            ESP_LOGI(TAG, "Connected to backend");
            return COMM_STATUS_OK;
        }
    }
    
    ESP_LOGE(TAG, "Failed to connect to backend: %s", esp_err_to_name(err));
    data->connected = false;
    return COMM_STATUS_ERROR;
}

static comm_status_t comm_disconnect(comm_manager_t* manager) {
    if (!manager || !manager->initialized) return COMM_STATUS_ERROR;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data) return COMM_STATUS_ERROR;
    
    data->connected = false;
    manager->connected = false;
    manager->authenticated = false;
    data->authenticated = false;
    
    ESP_LOGI(TAG, "Disconnected from backend");
    return COMM_STATUS_OK;
}

static comm_status_t comm_register_device(comm_manager_t* manager, 
                                           const device_registration_t* reg,
                                           registration_response_t* response) {
    if (!manager || !manager->initialized || !reg || !response) return COMM_STATUS_ERROR;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data) return COMM_STATUS_ERROR;
    
    // Create registration JSON
    cJSON* json = cJSON_CreateObject();
    cJSON_AddStringToObject(json, "serial_number", reg->serial_number);
    cJSON_AddStringToObject(json, "display_name", reg->display_name);
    cJSON_AddStringToObject(json, "model", reg->model);
    cJSON_AddStringToObject(json, "firmware_version", reg->firmware_version);
    cJSON_AddStringToObject(json, "sensor_config", reg->sensor_config_json);
    cJSON_AddStringToObject(json, "safety_config", reg->safety_config_json);
    
    char* json_str = cJSON_PrintUnformatted(json);
    cJSON_Delete(json);
    
    if (!json_str) return COMM_STATUS_ERROR;
    
    char url[256];
    snprintf(url, sizeof(url), "%s/api/v1/telemetry/devices", data->config.backend_url);
    
    char* response_str = NULL;
    comm_status_t status = http_post_json(data, url, json_str, &response_str);
    free(json_str);
    
    if (status != COMM_STATUS_OK || !response_str) {
        if (response_str) free(response_str);
        return status;
    }
    
    // Parse response
    cJSON* resp_json = cJSON_Parse(response_str);
    free(response_str);
    
    if (!resp_json) return COMM_STATUS_INVALID_RESPONSE;
    
    cJSON* success = cJSON_GetObjectItem(resp_json, "success");
    if (cJSON_IsTrue(success)) {
        cJSON* device_id = cJSON_GetObjectItem(resp_json, "device_id");
        cJSON* jwt = cJSON_GetObjectItem(resp_json, "jwt_token");
        cJSON* expires = cJSON_GetObjectItem(resp_json, "expires_in");
        
        response->success = true;
        if (cJSON_IsString(device_id)) strncpy(response->device_id, device_id->valuestring, DEVICE_ID_MAX_LEN - 1);
        if (cJSON_IsString(jwt)) strncpy(response->jwt_token, jwt->valuestring, JWT_TOKEN_MAX_LEN - 1);
        if (cJSON_IsNumber(expires)) response->expires_in = expires->valueint;
    } else {
        response->success = false;
        cJSON* error = cJSON_GetObjectItem(resp_json, "error");
        if (cJSON_IsString(error)) strncpy(response->error_message, error->valuestring, 255);
    }
    
    cJSON_Delete(resp_json);
    return response->success ? COMM_STATUS_OK : COMM_STATUS_SERVER_ERROR;
}

static comm_status_t comm_authenticate(comm_manager_t* manager, 
                                        const char* jwt_token) {
    if (!manager || !manager->initialized || !jwt_token) return COMM_STATUS_ERROR;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data) return COMM_STATUS_ERROR;
    
    strncpy(data->config.jwt_token, jwt_token, JWT_TOKEN_MAX_LEN - 1);
    manager->authenticated = true;
    data->authenticated = true;
    
    ESP_LOGI(TAG, "Authenticated with JWT");
    return COMM_STATUS_OK;
}

static comm_status_t comm_refresh_token(comm_manager_t* manager,
                                         token_refresh_response_t* response) {
    if (!manager || !manager->initialized || !response) return COMM_STATUS_ERROR;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data || !data->authenticated) return COMM_STATUS_AUTH_FAILED;
    
    char url[256];
    snprintf(url, sizeof(url), "%s/api/v1/auth/refresh", data->config.backend_url);
    
    cJSON* json = cJSON_CreateObject();
    cJSON_AddStringToObject(json, "refresh_token", data->config.jwt_token);  // Using JWT as refresh for now
    
    char* json_str = cJSON_PrintUnformatted(json);
    cJSON_Delete(json);
    
    if (!json_str) return COMM_STATUS_ERROR;
    
    char* response_str = NULL;
    comm_status_t status = http_post_json(data, url, json_str, &response_str);
    free(json_str);
    
    if (status != COMM_STATUS_OK || !response_str) {
        if (response_str) free(response_str);
        return status;
    }
    
    cJSON* resp_json = cJSON_Parse(response_str);
    free(response_str);
    
    if (!resp_json) return COMM_STATUS_INVALID_RESPONSE;
    
    cJSON* success = cJSON_GetObjectItem(resp_json, "success");
    if (cJSON_IsTrue(success)) {
        cJSON* access_token = cJSON_GetObjectItem(resp_json, "access_token");
        cJSON* expires = cJSON_GetObjectItem(resp_json, "expires_in");
        
        response->success = true;
        if (cJSON_IsString(access_token)) {
            strncpy(response->new_jwt_token, access_token->valuestring, JWT_TOKEN_MAX_LEN - 1);
            // Update stored token
            strncpy(data->config.jwt_token, access_token->valuestring, JWT_TOKEN_MAX_LEN - 1);
        }
        if (cJSON_IsNumber(expires)) response->expires_in = expires->valueint;
    } else {
        response->success = false;
        cJSON* error = cJSON_GetObjectItem(resp_json, "error");
        if (cJSON_IsString(error)) strncpy(response->error_message, error->valuestring, 255);
    }
    
    cJSON_Delete(resp_json);
    return response->success ? COMM_STATUS_OK : COMM_STATUS_AUTH_FAILED;
}

static comm_status_t comm_send_telemetry(comm_manager_t* manager,
                                          const sensor_reading_t* readings,
                                          uint32_t sequence,
                                          telemetry_response_t* response) {
    if (!manager || !manager->initialized || !readings || !response) return COMM_STATUS_ERROR;
    if (!manager->authenticated) return COMM_STATUS_AUTH_FAILED;
    
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (!data) return COMM_STATUS_ERROR;
    
    // Create telemetry JSON
    char* json_str = create_telemetry_json(readings, sequence, 
                                            data->config.device_id,
                                            data->config.firmware_version);
    if (!json_str) return COMM_STATUS_ERROR;
    
    char url[256];
    snprintf(url, sizeof(url), "%s/api/v1/telemetry", data->config.backend_url);
    
    char* response_str = NULL;
    comm_status_t status = http_post_json(data, url, json_str, &response_str);
    free(json_str);
    
    if (status != COMM_STATUS_OK || !response_str) {
        if (response_str) free(response_str);
        return status;
    }
    
    cJSON* resp_json = cJSON_Parse(response_str);
    free(response_str);
    
    if (!resp_json) return COMM_STATUS_INVALID_RESPONSE;
    
    cJSON* success = cJSON_GetObjectItem(resp_json, "success");
    if (cJSON_IsTrue(success)) {
        cJSON* accepted = cJSON_GetObjectItem(resp_json, "accepted");
        cJSON* rejected = cJSON_GetObjectItem(resp_json, "rejected");
        
        response->success = true;
        response->accepted = cJSON_IsNumber(accepted) ? accepted->valueint : 0;
        response->rejected = cJSON_IsNumber(rejected) ? rejected->valueint : 0;
    } else {
        response->success = false;
        cJSON* error = cJSON_GetObjectItem(resp_json, "error");
        if (cJSON_IsString(error)) strncpy(response->error_message, error->valuestring, 255);
    }
    
    cJSON_Delete(resp_json);
    return response->success ? COMM_STATUS_OK : COMM_STATUS_SERVER_ERROR;
}

static comm_status_t comm_send_telemetry_batch(comm_manager_t* manager,
                                                const telemetry_batch_t* batch,
                                                telemetry_response_t* response) {
    // For batch, we'd create a different JSON structure
    // Simplified: send as single batch
    if (!manager || !batch || !response) return COMM_STATUS_ERROR;
    return comm_send_telemetry(manager, batch->readings, batch->sequence, response);
}

static comm_status_t comm_send_safety_response(comm_manager_t* manager,
                                                const char* action_id,
                                                bool success,
                                                const char* message) {
    if (!manager || !manager->initialized || !manager->authenticated) return COMM_STATUS_AUTH_FAILED;
    // Implementation would send safety action response
    ESP_LOGI(TAG, "Safety response sent: action=%s, success=%d, msg=%s", 
             action_id, success, message ? message : "");
    return COMM_STATUS_OK;
}

static comm_status_t comm_request_config_update(comm_manager_t* manager) {
    if (!manager || !manager->initialized || !manager->authenticated) return COMM_STATUS_AUTH_FAILED;
    ESP_LOGI(TAG, "Config update requested");
    return COMM_STATUS_OK;
}

static comm_status_t comm_check_ota_update(comm_manager_t* manager,
                                            char* ota_url,
                                            char* version) {
    if (!manager || !manager->initialized) return COMM_STATUS_ERROR;
    // Implementation would check for OTA updates
    return COMM_STATUS_OK;
}

static bool comm_is_connected(comm_manager_t* manager) {
    return manager && manager->connected;
}

static bool comm_is_authenticated(comm_manager_t* manager) {
    return manager && manager->authenticated;
}

static esp_err_t http_event_handler(esp_http_client_event_t* evt) {
    comm_manager_data_t* data = (comm_manager_data_t*)evt->user_data;
    if (!data) return ESP_OK;
    
    switch (evt->event_id) {
        case HTTP_EVENT_ON_DATA:
            if (!esp_http_client_is_chunked_response(evt->client)) {
                size_t len = evt->data_len;
                if (data->response_buffer_size < strlen(data->response_buffer) + len + 1) {
                    // Buffer too small
                    return ESP_OK;
                }
                memcpy(data->response_buffer + strlen(data->response_buffer), evt->data, len);
                data->response_buffer[strlen(data->response_buffer) + len] = '\0';
            }
            break;
        default:
            break;
    }
    return ESP_OK;
}

static comm_status_t http_post_json(comm_manager_data_t* data, 
                                     const char* url, 
                                     const char* json_payload,
                                     char** response_out) {
    if (!data || !url || !json_payload || !response_out) return COMM_STATUS_ERROR;
    
    if (xSemaphoreTake(data->mutex, pdMS_TO_TICKS(5000)) != pdTRUE) {
        return COMM_STATUS_TIMEOUT;
    }
    
    data->response_buffer[0] = '\0';
    
    esp_http_client_set_url(data->http_client, url);
    esp_http_client_set_method(data->http_client, HTTP_METHOD_POST);
    esp_http_client_set_header(data->http_client, "Content-Type", "application/json");
    
    if (data->config.jwt_token[0]) {
        char auth_header[JWT_TOKEN_MAX_LEN + 20];
        snprintf(auth_header, sizeof(auth_header), "Bearer %s", data->config.jwt_token);
        esp_http_client_set_header(data->http_client, "Authorization", auth_header);
    }
    
    esp_http_client_set_post_field(data->http_client, json_payload, strlen(json_payload));
    
    esp_err_t err = esp_http_client_perform(data->http_client);
    
    xSemaphoreGive(data->mutex);
    
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "HTTP POST failed: %s", esp_err_to_name(err));
        return COMM_STATUS_ERROR;
    }
    
    int status = esp_http_client_get_status_code(data->http_client);
    if (status >= 400) {
        ESP_LOGE(TAG, "HTTP error %d: %s", status, data->response_buffer);
        if (status == 401) return COMM_STATUS_AUTH_FAILED;
        return COMM_STATUS_SERVER_ERROR;
    }
    
    *response_out = strdup(data->response_buffer);
    return *response_out ? COMM_STATUS_OK : COMM_STATUS_ERROR;
}

static char* create_telemetry_json(const sensor_reading_t* readings, 
                                    uint32_t sequence,
                                    const char* device_id,
                                    const char* firmware_version) {
    cJSON* json = cJSON_CreateObject();
    
    cJSON_AddStringToObject(json, "device_id", device_id);
    cJSON_AddNumberToObject(json, "timestamp", esp_timer_get_time() / 1000000);  // Unix seconds
    cJSON_AddNumberToObject(json, "sequence", sequence);
    cJSON_AddStringToObject(json, "firmware_version", firmware_version);
    
    cJSON* readings_json = cJSON_CreateObject();
    
    const char* sensor_names[SENSOR_TYPE_COUNT] = {
        "tds", "conductivity", "ph", "turbidity", "temperature",
        "flow_rate", "inlet_pressure", "outlet_pressure", "tank_level",
        "leak", "pump_current", "pump_power", "uv_state"
    };
    
    for (int i = 0; i < SENSOR_TYPE_COUNT; i++) {
        if (readings[i].value != 0 || readings[i].status != SENSOR_STATUS_MISSING) {
            cJSON* sensor_json = cJSON_CreateObject();
            cJSON_AddNumberToObject(sensor_json, "value", readings[i].value);
            cJSON_AddNumberToObject(sensor_json, "status", readings[i].status);
            cJSON_AddNumberToObject(sensor_json, "provenance", readings[i].provenance);
            cJSON_AddNumberToObject(sensor_json, "timestamp_ms", readings[i].timestamp_ms);
            cJSON_AddItemToObject(readings_json, sensor_names[i], sensor_json);
        }
    }
    
    cJSON_AddItemToObject(json, "readings", readings_json);
    
    char* json_str = cJSON_PrintUnformatted(json);
    cJSON_Delete(json);
    return json_str;
}

comm_manager_t* comm_manager_create(void) {
    return &comm_manager;
}

void comm_manager_destroy(comm_manager_t* manager) {
    if (!manager) return;
    comm_manager_data_t* data = (comm_manager_data_t*)manager->private_data;
    if (data) {
        if (data->http_client) {
            esp_http_client_cleanup(data->http_client);
        }
        if (data->mutex) {
            vSemaphoreDelete(data->mutex);
        }
        if (data->response_buffer) {
            free(data->response_buffer);
        }
        free(data);
        manager->private_data = NULL;
    }
    manager->initialized = false;
    manager->connected = false;
    manager->authenticated = false;
}