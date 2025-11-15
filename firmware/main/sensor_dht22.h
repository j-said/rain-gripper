#pragma once
#include <esp_err.h>

/**
 * @brief Initialize DHT22 sensor
 * 
 *  @return `ESP_OK`   - DHT22 sensor is connected and ready for use
 *          `ESP_FAIL` - DHT22 sensor is NOT connected or failed
 */
esp_err_t dht22_init(void);

/**
 * @brief Read integer data from sensor
 *
 * @param[out] humidity Humidity, percents, nullable
 * @param[out] temperature Temperature, degrees Celsius, nullable
 * @return `ESP_OK` on success
 */
esp_err_t dht22_read_data(float *humidity, float *temperature);

