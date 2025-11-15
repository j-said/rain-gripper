#include "sensor_dht22.h"
#include "dht.h"

esp_err_t dht22_init()
{
    float humidity;
    float temperature;
    return dht22_read_data(&humidity, &temperature);
}

esp_err_t dht22_read_data(float *humidity, float *temperature)
{
    return dht_read_float_data(DHT_TYPE_AM2301, CONFIG_DHT22_GPIO, humidity, temperature);
}