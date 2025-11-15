#include "esp_log.h"
#include "sensor_ds18b20.h"
#include "ds18b20.h"
#include "onewire_bus_impl_rmt.h"


static const char *TAG = "DS18B20";

static onewire_bus_handle_t bus = NULL;

static  onewire_bus_config_t bus_config = {
    .bus_gpio_num = CONFIG_DS18B20_GPIO,
};

static onewire_bus_rmt_config_t rmt_config = {
    .max_rx_bytes = 10, // 1byte ROM command + 8byte ROM number + 1byte device command
};

static int ds18b20_device_num = 0;
static  ds18b20_device_handle_t ds18b20s;

esp_err_t ds18b20_init(void)
{   
    esp_err_t err = ESP_OK;
    onewire_device_iter_handle_t iter = NULL;
    onewire_device_t next_onewire_device;
    esp_err_t search_result = ESP_OK;
    do
    {
        err = onewire_new_bus_rmt(&bus_config, &rmt_config, &bus);
        if (err) break;

        // create 1-wire device iterator, which is used for device search
        err = onewire_new_device_iter(bus, &iter);
        if (err) break;
        ESP_LOGI(TAG, "Device iterator created, start searching...");
        do {
            search_result = onewire_device_iter_get_next(iter, &next_onewire_device);
            if (search_result == ESP_OK) { // found a new device, let's check if we can upgrade it to a DS18B20
                ds18b20_config_t ds_cfg = {};
                // check if the device is a DS18B20, if so, return the ds18b20 handle
                if (ds18b20_new_device(&next_onewire_device, &ds_cfg, &ds18b20s) == ESP_OK)                 {
                    ESP_LOGI(TAG, "Found a DS18B20[%d], address: %016llX", ds18b20_device_num, next_onewire_device.address);
                    ds18b20_device_num++;
                    break;
                } else {
                    ESP_LOGI(TAG, "Found an unknown device, address: %016llX", next_onewire_device.address);
                }
            }
        } while (search_result != ESP_ERR_NOT_FOUND);
        onewire_del_device_iter(iter);
        ESP_LOGI(TAG, "Searching done, %d DS18B20 device(s) found", ds18b20_device_num);
    } while (0);
    
    return ds18b20_device_num == 1? ESP_OK : ESP_FAIL;
}

esp_err_t ds18b20_read_data(float *temperature)
{
    esp_err_t err = ds18b20_trigger_temperature_conversion(ds18b20s);
    if (!err) {
        err = ds18b20_get_temperature(ds18b20s, temperature);
    }
    return err;
}