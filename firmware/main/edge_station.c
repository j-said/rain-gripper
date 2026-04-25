#include <driver/gpio.h>
#include <driver/spi_common.h>
#include <driver/spi_master.h>
#include <esp_intr_alloc.h>
#include <esp_log.h>
#include <sx127x.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "adc_unit.h"
#include "edge_station.h"
#include "sensor_dht22.h"
#include "sensor_ds18b20.h"
#include "sensor_hd38.h"
#include "sensor_dfrobot_rainfall.h"
#include "sensor_raindrop.h"
#include "sdkconfig.h"
#include "weather_station_defs.h"

#define SCK     CONFIG_LORA_SCK
#define MISO    CONFIG_LORA_MISO
#define MOSI    CONFIG_LORA_MOSI
#define SS      CONFIG_LORA_SS
#define RST     CONFIG_LORA_RST
#define DIO0    CONFIG_LORA_DIO0

#define NaN     (0.0 / 0.0)

#define RAINFALL_SENSOR            BIT0
#define DHT22_SENSOR               BIT1
#define DS18B20_SENSOR             BIT2
#define HD38_SENSOR                BIT3
#define RAINDROP_SENSOR            BIT4

#define EDGE_DEVICE_ID   1 

static const char *TAG = "Edge station";

static sx127x device;
static TaskHandle_t handle_interrupt;
static uint16_t messages_sent = 0;
//static int supported_power_levels[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20};
//static int supported_power_levels_count = sizeof(supported_power_levels) / sizeof(int);
static uint32_t sensors;
static void IRAM_ATTR handle_interrupt_fromisr(void *arg) 
{
    xTaskResumeFromISR(handle_interrupt);
}

static void handle_interrupt_task(void *arg) 
{
    while (1) {
        vTaskSuspend(NULL);
        sx127x_handle_interrupt((sx127x *)arg);
    }
}

static void tx_callback(sx127x *device) 
{
    ESP_LOGI(TAG, "Transmitted message %d", messages_sent);
}

void setup_gpio_interrupts(gpio_num_t gpio, sx127x *device) 
{
    gpio_set_direction(gpio, GPIO_MODE_INPUT);
    gpio_pulldown_en(gpio);
    gpio_pullup_dis(gpio);
    gpio_set_intr_type(gpio, GPIO_INTR_POSEDGE);
    gpio_isr_handler_add(gpio, handle_interrupt_fromisr, (void *)device);
}

void edge_station(void)
{
    ESP_LOGI(TAG, "Say hello to the \"Edge\" weather station");
    ESP_LOGI(TAG, "Starting up");

    esp_err_t esp_err = adc_unit_init();
    ESP_LOGI(TAG, "ADC init: %d", esp_err);   

    esp_err = dht22_init();
    ESP_LOGI(TAG, "DHT22 init: %d", esp_err);
    if (!esp_err) {
        sensors |= DHT22_SENSOR;
    } 

    esp_err = ds18b20_init();
    ESP_LOGI(TAG, "DS18B20 init: %d", esp_err);
    if (!esp_err) {
        sensors |= DS18B20_SENSOR;
    } 

    esp_err = hd38_init(adc_unit_get_handle());
    ESP_LOGI(TAG, "HD38 init: %d", esp_err);
    if (!esp_err) {
        sensors |= HD38_SENSOR;
    } 

    esp_err = rainfall_init();
    ESP_LOGI(TAG, "Rainfall init: %d", esp_err);
    if (!esp_err) {
        sensors |= RAINFALL_SENSOR;
    }

    esp_err = raindrop_init(adc_unit_get_handle());
    ESP_LOGI(TAG, "Raindrop init: %d", esp_err);
    if (!esp_err) {
        sensors |= RAINDROP_SENSOR;
    }       

    spi_bus_config_t config = {
        .mosi_io_num = MOSI,
        .miso_io_num = MISO,
        .sclk_io_num = SCK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 0,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &config, 1));

    spi_device_interface_config_t dev_cfg = {
        .clock_speed_hz = 4E6,
        .spics_io_num = SS,
        .queue_size = 16,
        .command_bits = 0,
        .address_bits = 8,
        .dummy_bits = 0,
        .mode = 0};

    spi_device_handle_t spi_device;

    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &dev_cfg, &spi_device));
    ESP_ERROR_CHECK(sx127x_create(spi_device, &device));
    ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_SLEEP, SX127x_MODULATION_LORA, &device));
    ESP_ERROR_CHECK(sx127x_set_frequency(433000000, &device));
    ESP_ERROR_CHECK(sx127x_lora_reset_fifo(&device));
    ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_STANDBY, SX127x_MODULATION_LORA, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_bandwidth(SX127x_BW_125000, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_implicit_header(NULL, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_modem_config_2(SX127x_SF_12, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_syncword(18, &device));
    ESP_ERROR_CHECK(sx127x_set_preamble_length(8, &device));
    sx127x_tx_set_callback(tx_callback, &device);

    BaseType_t task_code = xTaskCreatePinnedToCore(handle_interrupt_task, "handle interrupt", 8196, &device, 2, &handle_interrupt, xPortGetCoreID());
    if (task_code != pdPASS) {
        ESP_LOGE(TAG, "can't create task %d", task_code);
        return;
    }

    gpio_install_isr_service(0);
    setup_gpio_interrupts((gpio_num_t)DIO0, &device);

    ESP_ERROR_CHECK(sx127x_tx_set_pa_config(SX127x_PA_PIN_BOOST, 20, &device));
    sx127x_tx_header_t header = {
        .enable_crc = true,
        .coding_rate = SX127x_CR_4_5};
    ESP_ERROR_CHECK(sx127x_lora_tx_set_explicit_header(&header, &device));

    //tx_callback(&device);
    while (1) {
        weather_station_packet_t packet = {
            .protocol_version = WS_PROTOCOL_VERSION,
            .device_id = EDGE_DEVICE_ID,
            .message_num = messages_sent++,
            .rainfall = NaN,
            .air_temperature = NaN,
            .air_humidity = NaN,
            .soil_temperature = NaN,
            .soil_humidity = NaN,
            .is_raining = 0  
        };

        if (sensors & RAINFALL_SENSOR) {
            rainfall_read_data(&packet.rainfall);
        }
        if (sensors & DHT22_SENSOR) {
            dht22_read_data(&packet.air_humidity, &packet.air_temperature);
        }
        if (sensors & DS18B20_SENSOR) {
            ds18b20_read_data(&packet.soil_temperature);
        }
        if (sensors & HD38_SENSOR) {
            hd38_read_data(&packet.soil_humidity);
        }
        if (sensors & RAINDROP_SENSOR) {
            raindrop_read_data(&packet.is_raining);
        }
        
        ESP_ERROR_CHECK(sx127x_lora_tx_set_for_transmission((uint8_t*)&packet, sizeof(packet), &device));
        ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_TX, SX127x_MODULATION_LORA, &device));
        ESP_LOGI(TAG, "Transmitting %d bytes", sizeof(packet));

        ESP_LOGI(TAG, "Message number: %hd", packet.message_num);
        ESP_LOGI(TAG, "Rainfall: %f mm", packet.rainfall);
        ESP_LOGI(TAG, "Rain: %s", packet.is_raining? "yes" : "no");
        ESP_LOGI(TAG, "Air temperature: %f", packet.air_temperature);
        ESP_LOGI(TAG, "Air humidity: %f", packet.air_humidity);
        ESP_LOGI(TAG, "Soil temperature: %f", packet.soil_temperature);
        ESP_LOGI(TAG, "Soil humidity: %f\n", packet.soil_humidity);
        vTaskDelay(1000/portTICK_PERIOD_MS);
    }
}
