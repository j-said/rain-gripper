#include "sensor_raindrop.h"
#include "soc/soc_caps.h"
#include "esp_log.h"
#include "esp_check.h"
#include "driver/gpio.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "Raindrop";

#define ADC_ATTEN           ADC_ATTEN_DB_12

static adc_oneshot_unit_handle_t* adc_handle;

esp_err_t raindrop_init(adc_oneshot_unit_handle_t* handle)
{
    adc_oneshot_chan_cfg_t config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN,
    };

    adc_handle = handle;
    esp_err_t err = adc_oneshot_config_channel(*adc_handle, CONFIG_RAINDROP_ADC_CHANNEL, &config);
    ESP_RETURN_ON_ERROR(err, TAG, "adc_oneshot    vTaskDelay(pdMS_TO_TICKS(100));_config_channel failed");

    gpio_set_direction(CONFIG_RAINDROP_GPIO, GPIO_MODE_INPUT);
    gpio_pulldown_dis(CONFIG_RAINDROP_GPIO);
    gpio_pullup_en(CONFIG_RAINDROP_GPIO);

    ESP_RETURN_ON_ERROR(err, TAG, "Sensor is not connected or fallen off");
    return ESP_OK;
}

esp_err_t raindrop_read_data(uint32_t *rain)
{
#if 0    
    int adc_raw;
    esp_err_t err = adc_oneshot_read(*adc_handle, CONFIG_HD38_ADC_CHANNEL, &adc_raw);
    ESP_RETURN_ON_ERROR(err, TAG, "adc_oneshot_read failed with error %d", err);

    *rain = adc_raw < 2000 ? 1 : 0;
#endif
    *rain = gpio_get_level(CONFIG_RAINDROP_GPIO) ? 0 : 1;
    return ESP_OK;
}
