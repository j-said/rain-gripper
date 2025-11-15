#pragma once
#include <esp_err.h>

/**
 * @brief Initialize DS18B20 sensor
 * 
 *  @return `ESP_OK`   - DS18B20 sensor is connected and ready for use
 *          `ESP_FAIL` - DS18B20 sensor is NOT connected or failed
 */
esp_err_t ds18b20_init(void);

esp_err_t ds18b20_read_data(float *temperature);