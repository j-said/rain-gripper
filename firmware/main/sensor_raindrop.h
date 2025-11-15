#pragma once
#include <stdint.h>
#include "esp_adc/adc_oneshot.h"
#include <esp_err.h>

/**
 * @brief Initialize raindrop sensor
 * 
 *  @return `ESP_OK`   - raindrop sensor is connected and ready for use
 *          `ESP_FAIL` - raindrop sensor is NOT connected or failed
 */
esp_err_t raindrop_init(adc_oneshot_unit_handle_t* adc_handle);

/**
 * @brief Read data from sensor
 *
 * @param[out] data 0 - no rain, 1 - rain
 * @return `ESP_OK` on success
 */
esp_err_t raindrop_read_data(uint32_t *rain);