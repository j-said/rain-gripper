#include "driver/gpio.h"
#include "edge_station.h"
#include "main_station.h"
#include "nvs_flash.h"

typedef enum {
    EDGE_STATION,
    MAIN_STATION
} StationType_t;

void app_main(void)
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    gpio_set_direction(CONFIG_MODE_STRAPPING_GPIO, GPIO_MODE_INPUT);
    StationType_t station_type = (StationType_t)gpio_get_level(CONFIG_MODE_STRAPPING_GPIO);
    switch(station_type)
    {
        case EDGE_STATION:
            edge_station();
            break;
        case MAIN_STATION:
            main_station();
            break;
    } 
}
