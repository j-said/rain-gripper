#pragma once
#include "esp_adc/adc_oneshot.h"
#include <esp_err.h>

/**
 * @brief Initialize HD38 sensor
 * 
 *  @return `ESP_OK`   - HD38 sensor is connected and ready for use
 *          `ESP_FAIL` - HD38 sensor is NOT connected or failed
 */
esp_err_t hd38_init(adc_oneshot_unit_handle_t* handle);

/**
 * @brief Read integer data from sensor
 *
 * @param[out] humidity Humidity, percents, nullable
 * @return `ESP_OK` on success
 */
esp_err_t hd38_read_data(float *humidity);
