# AquaNexis ESP32 Firmware CMake Configuration
# Build system for ESP32-S3 firmware

cmake_minimum_required(VERSION 3.16)

# Project definition
project(aquanexis_firmware VERSION 1.0.0 LANGUAGES C)

# Set ESP-IDF path (can be overridden by environment variable)
if(NOT DEFINED ENV{IDF_PATH})
    set(IDF_PATH $ENV{HOME}/esp/esp-idf CACHE PATH "ESP-IDF path")
endif()

# Include ESP-IDF build system
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# Project configuration
set(COMPONENT_NAME "aquanexis_firmware")

# Source files
set(SRCS
    src/main.c
    src/sensor_registry.c
    src/sensor_tds.c
    src/sensor_ph.c
    src/sensor_turbidity.c
    src/sensor_temperature.c
    src/sensor_flow.c
    src/sensor_pressure.c
    src/sensor_tank_level.c
    src/sensor_leak.c
    src/sensor_pump_current.c
    src/sensor_pump_power.c
    src/sensor_uv_state.c
    src/comm_manager.c
)

# Include directories
set(INCLUDE_DIRS
    include
    ${IDF_PATH}/components/esp_system/include
    ${IDF_PATH}/components/esp_wifi/include
    ${IDF_PATH}/components/esp_event/include
    ${IDF_PATH}/components/esp_netif/include
    ${IDF_PATH}/components/nvs_flash/include
    ${IDF_PATH}/components/freertos/include
    ${IDF_PATH}/components/driver/include
    ${IDF_PATH}/components/esp_adc_cal/include
    ${IDF_PATH}/components/esp_timer/include
    ${IDF_PATH}/components/esp_ota_ops/include
    ${IDF_PATH}/components/esp_http_client/include
    ${IDF_PATH}/components/mbedtls/include
    ${IDF_PATH}/components/cJSON/include
)

# Component registration
idf_component_register(SRCS ${SRCS}
    INCLUDE_DIRS ${INCLUDE_DIRS}
    REQUIRES 
        esp_system
        esp_wifi
        esp_event
        esp_netif
        nvs_flash
        freertos
        driver
        esp_adc_cal
        esp_timer
        esp_ota_ops
        esp_http_client
        mbedtls
        cJSON
        esp_netif
        esp_wifi
        esp_event
        spi_flash
)

# Compiler options
target_compile_options(${COMPONENT_NAME} PRIVATE
    -Wall
    -Wextra
    -Werror=implicit-function-declaration
    -Werror=pointer-sign
    -Wno-unused-parameter
    -Wno-unused-variable
    -std=gnu11
)

# Linker options
target_link_libraries(${COMPONENT_NAME} PRIVATE
    m
)

# Partition table
set(PARTITION_TABLE_FILE partitions.csv CACHE FILEPATH "Partition table CSV file")

# SDK configuration
set(SDKCONFIG_DEFAULTS config/sdkconfig.defaults CACHE FILEPATH "SDK config defaults")

# Build type specific flags
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(${COMPONENT_NAME} PRIVATE -O0 -g3)
else()
    target_compile_options(${COMPONENT_NAME} PRIVATE -Os -g)
endif()

# Partition table embedding
if(EXISTS ${PARTITION_TABLE_FILE})
    set(PARTITION_TABLE_BIN ${CMAKE_BINARY_DIR}/partition_table/partition-table.bin)
    add_custom_command(
        OUTPUT ${PARTITION_TABLE_BIN}
        COMMAND ${IDF_PATH}/components/partition_table/gen_esp32part.py ${PARTITION_TABLE_FILE} ${PARTITION_TABLE_BIN}
        DEPENDS ${PARTITION_TABLE_FILE}
        COMMENT "Generating partition table binary"
    )
    add_custom_target(partition_table_bin DEPENDS ${PARTITION_TABLE_BIN})
    add_dependencies(${COMPONENT_NAME} partition_table_bin)
endif()

# Flash target
add_custom_target(flash
    COMMAND ${IDF_PATH}/components/esptool_py/esptool/esptool.py --chip esp32s3 --port ${ESPPORT} --baud 921600 write_flash -z 0x1000 ${CMAKE_BINARY_DIR}/bootloader/bootloader.bin 0x8000 ${PARTITION_TABLE_BIN} 0x10000 ${CMAKE_BINARY_DIR}/${COMPONENT_NAME}.bin
    DEPENDS ${COMPONENT_NAME}
    COMMENT "Flashing firmware to ESP32"
)

# Monitor target
add_custom_target(monitor
    COMMAND ${IDF_PATH}/tools/idf_monitor.py --port ${ESPPORT} --baud 115200
    COMMENT "Starting serial monitor"
)

# Print configuration
message(STATUS "AquaNexis ESP32 Firmware Build Configuration")
message(STATUS "  IDF_PATH: ${IDF_PATH}")
message(STATUS "  Source files: ${SRCS}")
message(STATUS "  Include dirs: ${INCLUDE_DIRS}")
message(STATUS "  Partition table: ${PARTITION_TABLE_FILE}")
message(STATUS "  SDK config: ${SDKCONFIG_DEFAULTS}")