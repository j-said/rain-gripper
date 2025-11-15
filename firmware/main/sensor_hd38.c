#include "sensor_hd38.h"
//#include "soc/soc_caps.h"
#include "esp_log.h"
#include "esp_check.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "DH38";

#define ADC_ATTEN   ADC_ATTEN_DB_12

static adc_oneshot_unit_handle_t* adc_handle;

esp_err_t hd38_init(adc_oneshot_unit_handle_t* handle)
{
    adc_handle = handle;

    adc_oneshot_chan_cfg_t config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN,
    };

    esp_err_t err = adc_oneshot_config_channel(*adc_handle, CONFIG_HD38_ADC_CHANNEL, &config);
    ESP_RETURN_ON_ERROR(err, TAG, "adc_oneshot_config_channel failed");

#if 0
    vTaskDelay(pdMS_TO_TICKS(100));

    float humidity;
    hd38_read_data(&humidity);
    ESP_RETURN_ON_ERROR(err, TAG, "hd38_read_data failed");
    ESP_LOGI(TAG, "Humidity: %f", humidity);

    // if the sensor is not connected or fallen off the humidity will be around 100 %
    if (humidity > 97.0) {
        err = ESP_FAIL;
    }
    ESP_RETURN_ON_ERROR(err, TAG, "Sensor is not connected or fallen off");
#endif    
    return ESP_OK;
}

esp_err_t hd38_read_data(float *humidity)
{
    int adc_raw;

    esp_err_t err = adc_oneshot_read(*adc_handle, CONFIG_HD38_ADC_CHANNEL, &adc_raw);
    ESP_RETURN_ON_ERROR(err, TAG, "adc_oneshot_read failed with error %d", err);

    *humidity = 100.0 - (float)(adc_raw) / 4095 * 100;
    return ESP_OK;
}
