#pragma once
#include <esp_err.h>

/**
 * @brief Initialize rainfall sensor
 * 
 *  @return `ESP_OK`   - Rainfall sensor is connected and ready for use
 *          `ESP_FAIL` - Rainfall sensor is NOT connected or failed
 */
esp_err_t rainfall_init(void);

esp_err_t rainfall_read_data(float *data);