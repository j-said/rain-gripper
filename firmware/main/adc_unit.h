#pragma once

#include "esp_adc/adc_oneshot.h"
#include <esp_err.h>

/**
 * @brief Initialize oneshot ADC
 * 
 *  @return `ESP_OK`
 *          `ESP_FAIL`
 */
esp_err_t adc_unit_init(void);

/**
 * @brief Return ADC unit handle
 * 
 */
adc_oneshot_unit_handle_t* adc_unit_get_handle();