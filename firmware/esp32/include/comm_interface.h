/**
 * @file comm_interface.h
 * @brief Communication Interface for ESP32 Backend Connectivity
 * 
 * Handles WiFi, HTTP/HTTPS, MQTT communication with AquaNexis backend
 */

#ifndef COMM_INTERFACE_H
#define COMM_INTERFACE_H

#include <stdint.h>
#include <stdbool.h>
#include "aquanexis_config.h"
#include "sensor_interface.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Communication Types
// ============================================================================

typedef enum {
    COMM_STATUS_OK = 0,
    COMM_STATUS_ERROR,
    COMM_STATUS_NOT_CONNECTED,
    COMM_STATUS_AUTH_FAILED,
    COMM_STATUS_TIMEOUT,
    COMM_STATUS_SERVER_ERROR,
    COMM_STATUS_INVALID_RESPONSE
} comm_status_t;

typedef enum {
    COMM_PROTOCOL_HTTP = 0,
    COMM_PROTOCOL_MQTT,
    COMM_PROTOCOL_WEBSOCKET
} comm_protocol_t;

typedef struct {
    char backend_url[BACKEND_URL_MAX_LEN];
    char device_id[DEVICE_ID_MAX_LEN];
    char jwt_token[JWT_TOKEN_MAX_LEN];
    char firmware_version[FIRMWARE_VERSION_MAX_LEN];
    comm_protocol_t protocol;
    uint32_t http_timeout_ms;
    uint32_t mqtt_keepalive_s;
} comm_config_t;

typedef struct {
    char serial_number[64];
    char display_name[128];
    char model[64];
    char firmware_version[32];
    char sensor_config_json[1024];
    char safety_config_json[1024];
} device_registration_t;

typedef struct {
    bool success;
    char device_id[DEVICE_ID_MAX_LEN];
    char jwt_token[JWT_TOKEN_MAX_LEN];
    int32_t expires_in;
    char error_message[256];
} registration_response_t;

typedef struct {
    bool success;
    char new_jwt_token[JWT_TOKEN_MAX_LEN];
    int32_t expires_in;
    char error_message[256];
} token_refresh_response_t;

typedef struct {
    uint32_t sequence;
    uint32_t timestamp_ms;
    sensor_reading_t readings[SENSOR_TYPE_COUNT];
    bool has_quality_flags;
    // Quality flags would go here
} telemetry_batch_t;

typedef struct {
    bool success;
    uint32_t accepted;
    uint32_t rejected;
    char error_message[256];
} telemetry_response_t;

// ============================================================================
// Communication Manager Interface
// ============================================================================

typedef struct comm_manager_t comm_manager_t;

struct comm_manager_t {
    comm_config_t config;
    bool initialized;
    bool connected;
    bool authenticated;
    
    // Initialize communication manager
    comm_status_t (*init)(comm_manager_t* manager, const comm_config_t* config);
    
    // Connect to backend
    comm_status_t (*connect)(comm_manager_t* manager);
    
    // Disconnect
    comm_status_t (*disconnect)(comm_manager_t* manager);
    
    // Register device with backend
    comm_status_t (*register_device)(comm_manager_t* manager, 
                                      const device_registration_t* reg,
                                      registration_response_t* response);
    
    // Authenticate with JWT
    comm_status_t (*authenticate)(comm_manager_t* manager, 
                                   const char* jwt_token);
    
    // Refresh JWT token
    comm_status_t (*refresh_token)(comm_manager_t* manager,
                                    token_refresh_response_t* response);
    
    // Send single telemetry reading
    comm_status_t (*send_telemetry)(comm_manager_t* manager,
                                     const sensor_reading_t* readings,
                                     uint32_t sequence,
                                     telemetry_response_t* response);
    
    // Send batch telemetry
    comm_status_t (*send_telemetry_batch)(comm_manager_t* manager,
                                           const telemetry_batch_t* batch,
                                           telemetry_response_t* response);
    
    // Send safety action response
    comm_status_t (*send_safety_response)(comm_manager_t* manager,
                                           const char* action_id,
                                           bool success,
                                           const char* message);
    
    // Request configuration update
    comm_status_t (*request_config_update)(comm_manager_t* manager);
    
    // OTA update check
    comm_status_t (*check_ota_update)(comm_manager_t* manager,
                                       char* ota_url,
                                       char* version);
    
    // Get connection status
    bool (*is_connected)(comm_manager_t* manager);
    bool (*is_authenticated)(comm_manager_t* manager);
    
    // Private data
    void* private_data;
};

// ============================================================================
// Global Functions
// ============================================================================

// Create and initialize communication manager
comm_manager_t* comm_manager_create(void);

// Destroy communication manager
void comm_manager_destroy(comm_manager_t* manager);

// Default configuration
void comm_config_default(comm_config_t* config);

#ifdef __cplusplus
}
#endif

#endif // COMM_INTERFACE_H