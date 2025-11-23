#include <string.h>
#include <math.h>
#include "main_station.h"
#include <driver/gpio.h>
#include <driver/spi_common.h>
#include <driver/spi_master.h>
#include <esp_intr_alloc.h>
#include <esp_log.h>
#include <sx127x.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/event_groups.h"
#include "esp_event.h"
#include "sdkconfig.h"
#include "esp_system.h"
#include "spi_flash_mmap.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include "sdkconfig.h"
#include "adc_unit.h"
#include "weather_station_defs.h"
#include "sensor_dht22.h"
#include "sensor_ds18b20.h"
#include "sensor_hd38.h"
#include "sensor_dfrobot_rainfall.h"
#include "sensor_raindrop.h"
#include "esp_modem_api.h"
#include "esp_netif.h"
#include "esp_netif_ppp.h"
#include "mqtt_client.h"

#if defined(CONFIG_EXAMPLE_FLOW_CONTROL_NONE)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_NONE
#elif defined(CONFIG_EXAMPLE_FLOW_CONTROL_SW)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_SW
#elif defined(CONFIG_EXAMPLE_FLOW_CONTROL_HW)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_HW
#endif

#define SCK              CONFIG_LORA_SCK
#define MISO             CONFIG_LORA_MISO
#define MOSI             CONFIG_LORA_MOSI
#define SS               CONFIG_LORA_SS
#define RST              CONFIG_LORA_RST
#define DIO0             CONFIG_LORA_DIO0

#define RAINFALL_SENSOR  BIT0
#define DHT22_SENSOR     BIT1
#define DS18B20_SENSOR   BIT2
#define HD38_SENSOR      BIT3
#define RAINDROP_SENSOR  BIT4

#define NaN              (0.0 / 0.0)

static const char *TAG = "Main station";

static sx127x device;
static TaskHandle_t handle_interrupt;
static uint32_t total_packets_received = 0;
static uint32_t sensors;
static EventGroupHandle_t event_group = NULL;

static const int CONNECT_BIT = BIT0;
static const int DISCONNECT_BIT = BIT1;
static const int MQTT_CONNECTED = BIT2;
static const int MQTT_DISCONNECTED = BIT3;
static char json_buffer[1024];

SemaphoreHandle_t   station_mutex; // Mutex for protecting access to weater data 
weather_condition_t main_station_data = {
                                            .device_id = 0,
                                            .rainfall= NaN,
                                            .air_temperature = NaN,
                                            .air_humidity = NaN,
                                            .soil_temperature = NaN,
                                            .soil_humidity = NaN
                                        };
weather_condition_t edge_station_data = {
                                            .device_id = 1,
                                            .rainfall = NaN,
                                            .air_temperature = NaN,
                                            .air_humidity = NaN,
                                            .soil_temperature = NaN,
                                            .soil_humidity = NaN                                            
                                        };


static void get_station_data(weather_condition_t* data)
{
    if (data) {

        xSemaphoreTake(station_mutex, portMAX_DELAY);

        if (data->device_id == main_station_data.device_id) {
            *data = main_station_data;
        } 
        else
        if (data->device_id == edge_station_data.device_id) {
            *data = edge_station_data;
        }

        xSemaphoreGive(station_mutex);
    }
}

static void set_station_data(weather_condition_t* data)
{
    if (data) {
        xSemaphoreTake(station_mutex, portMAX_DELAY);

        if (data->device_id == main_station_data.device_id) {
            main_station_data = *data;
        } 
        else
        if (data->device_id == edge_station_data.device_id) {
            edge_station_data = *data;
        }

        xSemaphoreGive(station_mutex);        
    }
}


static void IRAM_ATTR handle_interrupt_fromisr(void *arg) 
{
    xTaskResumeFromISR(handle_interrupt);
}

void handle_interrupt_task(void *arg) 
{
    while (1) {
        vTaskSuspend(NULL);
        sx127x_handle_interrupt((sx127x *)arg);
    }
}

static void rx_callback(sx127x *device, uint8_t *data, uint16_t data_length) 
{
    int16_t rssi;
    float snr;
    int32_t frequency_error;

    ESP_ERROR_CHECK(sx127x_rx_get_packet_rssi(device, &rssi));
    ESP_ERROR_CHECK(sx127x_lora_rx_get_packet_snr(device, &snr));
    ESP_ERROR_CHECK(sx127x_rx_get_frequency_error(device, &frequency_error));

    total_packets_received++;
    
    ESP_LOGI(TAG, "received: %hd bytes rssi: %hd snr: %f freq_error: %" PRId32, data_length, rssi, snr, frequency_error);
    weather_station_packet_t* packet = (weather_station_packet_t*)data;
    if (data_length == sizeof(weather_station_packet_t) && packet->protocol_version == WS_PROTOCOL_VERSION)
    {
        weather_condition_t edge;
        edge.device_id = 1;
        edge.rainfall = packet->rainfall;
        edge.air_temperature = packet->air_temperature;
        edge.air_humidity = packet->air_humidity;
        edge.soil_temperature = packet->soil_temperature;
        edge.soil_humidity = packet->soil_humidity;
        edge.is_raining = packet->is_raining;

        ESP_LOGI(TAG, "Edge device ID: %hhu", packet->device_id);
        ESP_LOGI(TAG, "Message number: %hd", packet->message_num);
        ESP_LOGI(TAG, "Rainfall: %f mm", packet->rainfall);
        ESP_LOGI(TAG, "Rain: %s", packet->is_raining? "yes" : "no");
        ESP_LOGI(TAG, "Air temperature: %f", packet->air_temperature);
        ESP_LOGI(TAG, "Air humidity: %f", packet->air_humidity);
        ESP_LOGI(TAG, "Soil temperature: %f", packet->soil_temperature);
        ESP_LOGI(TAG, "Soil humidity: %f\n", packet->soil_humidity);
        set_station_data(&edge);
    }
}

static void cad_callback(sx127x *device, int cad_detected) 
{
    if (cad_detected == 0) {
        ESP_LOGI(TAG, "cad not detected");
        ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_CAD, SX127x_MODULATION_LORA, device));
        return;
    }
    // put into RX mode first to handle interrupt as soon as possible
    ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_RX_CONT, SX127x_MODULATION_LORA, device));
    ESP_LOGI(TAG, "cad detected\n");
}

static void setup_gpio_interrupts(gpio_num_t gpio, sx127x *device) 
{
    gpio_set_direction(gpio, GPIO_MODE_INPUT);
    gpio_pulldown_en(gpio);
    gpio_pullup_dis(gpio);
    gpio_set_intr_type(gpio, GPIO_INTR_POSEDGE);
    gpio_isr_handler_add(gpio, handle_interrupt_fromisr, (void *)device);
}

static void on_ppp_changed(void *arg, esp_event_base_t event_base,
                           int32_t event_id, void *event_data)
{
    ESP_LOGI(TAG, "PPP state changed event %" PRIu32, event_id);
    if (event_id == NETIF_PPP_ERRORUSER) {
        /* User interrupted event from esp-netif */
        esp_netif_t **p_netif = event_data;
        ESP_LOGI(TAG, "User interrupted event from netif:%p", *p_netif);
    }
}


static void on_ip_event(void *arg, esp_event_base_t event_base,
                        int32_t event_id, void *event_data)
{
    ESP_LOGD(TAG, "IP event! %" PRIu32, event_id);
    if (event_id == IP_EVENT_PPP_GOT_IP) {
        esp_netif_dns_info_t dns_info;

        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        esp_netif_t *netif = event->esp_netif;

        ESP_LOGI(TAG, "Modem Connect to PPP Server");
        ESP_LOGI(TAG, "~~~~~~~~~~~~~~");
        ESP_LOGI(TAG, "IP          : " IPSTR, IP2STR(&event->ip_info.ip));
        ESP_LOGI(TAG, "Netmask     : " IPSTR, IP2STR(&event->ip_info.netmask));
        ESP_LOGI(TAG, "Gateway     : " IPSTR, IP2STR(&event->ip_info.gw));
        esp_netif_get_dns_info(netif, 0, &dns_info);
        ESP_LOGI(TAG, "Name Server1: " IPSTR, IP2STR(&dns_info.ip.u_addr.ip4));
        esp_netif_get_dns_info(netif, 1, &dns_info);
        ESP_LOGI(TAG, "Name Server2: " IPSTR, IP2STR(&dns_info.ip.u_addr.ip4));
        ESP_LOGI(TAG, "~~~~~~~~~~~~~~");
        xEventGroupSetBits(event_group, CONNECT_BIT);

        ESP_LOGI(TAG, "GOT ip event!!!");
    } else if (event_id == IP_EVENT_PPP_LOST_IP) {
        ESP_LOGI(TAG, "Modem Disconnect from PPP Server");
        xEventGroupSetBits(event_group, DISCONNECT_BIT);
    } else if (event_id == IP_EVENT_GOT_IP6) {
        ESP_LOGI(TAG, "GOT IPv6 event!");

        ip_event_got_ip6_t *event = (ip_event_got_ip6_t *)event_data;
        ESP_LOGI(TAG, "Got IPv6 address " IPV6STR, IPV62STR(event->ip6_info.ip));
    }
}

esp_err_t urc_handler(uint8_t *data, size_t len)
{
    ESP_LOGI(TAG, "Got URC: %s", data);
    return ESP_OK;
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGD(TAG, "Event dispatched from event loop base=%s, event_id=%" PRIu32, base, event_id);
    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
        xEventGroupSetBits(event_group, MQTT_CONNECTED);
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
        xEventGroupSetBits(event_group, MQTT_DISCONNECTED);
        break;
    default:
        //ESP_LOGI(TAG, "MQTT other event id: %d", event_id);
        break;
    }
}

void main_station(void)
{
    ESP_LOGI(TAG, "Say hello to the \"Main\" weather station");    
    ESP_LOGI(TAG, "Starting up");

    /* Init and register system/core components */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, ESP_EVENT_ANY_ID, &on_ip_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(NETIF_PPP_STATUS, ESP_EVENT_ANY_ID, &on_ppp_changed, NULL));

    //esp_err_t esp_err;
    esp_modem_dce_config_t dce_config = ESP_MODEM_DCE_DEFAULT_CONFIG("Internet");
    esp_netif_config_t netif_ppp_config = ESP_NETIF_DEFAULT_PPP();
    esp_netif_t *esp_netif = esp_netif_new(&netif_ppp_config);
    assert(esp_netif);

    event_group = xEventGroupCreate();

    esp_modem_dte_config_t dte_config = ESP_MODEM_DTE_DEFAULT_CONFIG();
    /* setup UART specific configuration based on kconfig options */
    dte_config.uart_config.tx_io_num = CONFIG_EXAMPLE_MODEM_UART_TX_PIN;
    dte_config.uart_config.rx_io_num = CONFIG_EXAMPLE_MODEM_UART_RX_PIN;
    dte_config.uart_config.rts_io_num = CONFIG_EXAMPLE_MODEM_UART_RTS_PIN;
    dte_config.uart_config.cts_io_num = CONFIG_EXAMPLE_MODEM_UART_CTS_PIN;
    dte_config.uart_config.flow_control = EXAMPLE_FLOW_CONTROL;
    dte_config.uart_config.rx_buffer_size = CONFIG_EXAMPLE_MODEM_UART_RX_BUFFER_SIZE;
    dte_config.uart_config.tx_buffer_size = CONFIG_EXAMPLE_MODEM_UART_TX_BUFFER_SIZE;
    dte_config.uart_config.event_queue_size = CONFIG_EXAMPLE_MODEM_UART_EVENT_QUEUE_SIZE;
    dte_config.task_stack_size = CONFIG_EXAMPLE_MODEM_UART_EVENT_TASK_STACK_SIZE;
    dte_config.task_priority = CONFIG_EXAMPLE_MODEM_UART_EVENT_TASK_PRIORITY;
    dte_config.dte_buffer_size = CONFIG_EXAMPLE_MODEM_UART_RX_BUFFER_SIZE / 2;
    esp_modem_dce_t *dce = esp_modem_new_dev(ESP_MODEM_DCE_SIM800, &dte_config, &dce_config, esp_netif);

    assert(dce);
    esp_err_t esp_err;
    if (dte_config.uart_config.flow_control == ESP_MODEM_FLOW_CONTROL_HW) {
        esp_err = esp_modem_set_flow_control(dce, 2, 2);  //2/2 means HW Flow Control.
        if (esp_err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to set the set_flow_control mode");
            return;
        }
        ESP_LOGI(TAG, "HW set_flow_control OK");
    }

    int rssi, ber;
    esp_err = esp_modem_get_signal_quality(dce, &rssi, &ber);
    if (esp_err != ESP_OK) {
        ESP_LOGE(TAG, "esp_modem_get_signal_quality failed with %d %s", esp_err, esp_err_to_name(esp_err));
        return;
    }
    ESP_LOGI(TAG, "Signal quality: rssi=%d, ber=%d", rssi, ber);

    esp_err = esp_modem_set_urc(dce, urc_handler);
    if (esp_err != ESP_OK) {
        ESP_LOGE(TAG, "esp_modem_set_urc() failed with %d", esp_err);
        //return;
    }
    
    vTaskDelay(1000);

    esp_err = esp_modem_set_mode(dce, ESP_MODEM_MODE_DATA);
    if (esp_err != ESP_OK) {
        ESP_LOGE(TAG, "esp_modem_set_mode(ESP_MODEM_MODE_DATA) failed with %d", esp_err);
        return;
    }
    /* Wait for IP address */
    ESP_LOGI(TAG, "Waiting for IP address");
    xEventGroupWaitBits(event_group, CONNECT_BIT | DISCONNECT_BIT, pdFALSE, pdFALSE,
                        pdMS_TO_TICKS(60000));
    
    /* Config MQTT */
    esp_mqtt_client_config_t mqtt_config = {
        .broker.address.uri = "mqtt://34.116.171.85:1883",
        .credentials.username = "admin",
        .credentials.authentication.password = "oleh",

    };

    esp_mqtt_client_handle_t mqtt_client = esp_mqtt_client_init(&mqtt_config);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);

    xEventGroupWaitBits(event_group, MQTT_CONNECTED, pdFALSE, pdFALSE,
                        pdMS_TO_TICKS(60000));

    station_mutex =  xSemaphoreCreateMutex();

     esp_err = adc_unit_init();
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
        .clock_speed_hz = 8E6,
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
    ESP_ERROR_CHECK(sx127x_rx_set_lna_boost_hf(true, &device));
    ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_STANDBY, SX127x_MODULATION_LORA, &device));
    ESP_ERROR_CHECK(sx127x_rx_set_lna_gain(SX127x_LNA_GAIN_G4, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_bandwidth(SX127x_BW_125000, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_implicit_header(NULL, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_modem_config_2(SX127x_SF_12, &device));
    ESP_ERROR_CHECK(sx127x_lora_set_syncword(18, &device));
    ESP_ERROR_CHECK(sx127x_set_preamble_length(8, &device));
    sx127x_rx_set_callback(rx_callback, &device);
    sx127x_lora_cad_set_callback(cad_callback, &device);

    BaseType_t task_code = xTaskCreatePinnedToCore(handle_interrupt_task, "handle interrupt", 8196, &device, 2, &handle_interrupt, xPortGetCoreID());
    if (task_code != pdPASS) {
        ESP_LOGE(TAG, "can't create task %d", task_code);
        return;
    }

    gpio_install_isr_service(0);
    setup_gpio_interrupts((gpio_num_t)DIO0, &device);

    ESP_ERROR_CHECK(sx127x_set_opmod(SX127x_MODE_RX_CONT, SX127x_MODULATION_LORA, &device));
    weather_condition_t main;
    weather_condition_t edge_station_data;
    edge_station_data.device_id = 1;

    while (1) {
        main.device_id = 0;
        main.rainfall = NaN;
        main.air_temperature = NaN;
        main.air_humidity = NaN;
        main.soil_temperature = NaN;
        main.soil_humidity = NaN;
        main.is_raining = 0; 

        if (sensors & RAINFALL_SENSOR) {
            rainfall_read_data(&main.rainfall);
        }
        if (sensors & DHT22_SENSOR) {
            dht22_read_data(&main.air_humidity, &main.air_temperature);
        }
        if (sensors & DS18B20_SENSOR) {
            ds18b20_read_data(&main.soil_temperature);
        }
        if (sensors & HD38_SENSOR) {
            hd38_read_data(&main.soil_humidity);
        }
        if (sensors & RAINDROP_SENSOR) {
            raindrop_read_data(&main.is_raining);
        }
        
        ESP_LOGI(TAG, "*Rainfall: %f mm", main.rainfall);
        ESP_LOGI(TAG, "*Raining: %s", main.is_raining ? "yes" : "no");
        ESP_LOGI(TAG, "*Air temperature: %f", main.air_temperature);
        ESP_LOGI(TAG, "*Air humidity: %f", main.air_humidity);
        ESP_LOGI(TAG, "*Soil temperature: %f", main.soil_temperature);
        ESP_LOGI(TAG, "*Soil humidity: %f\n", main.soil_humidity);       
        
        if (isnan(main.rainfall)) {
            main.rainfall = 0.0;
        }
        if (isnan(main.air_humidity)) {
            main.air_humidity = 0.0;
        }
        if (isnan(main.air_temperature)) {
            main.air_temperature = 0.0;
        }
        if (isnan(main.soil_humidity)) {
            main.soil_humidity = 0.0;
        }
        if (isnan(main.soil_temperature)) {
            main.soil_temperature = 0.0;
        }

        set_station_data(&main); 
        get_station_data(&edge_station_data);


        if (isnan(edge_station_data.rainfall)) {
            edge_station_data.rainfall = 0.0;
        }
        if (isnan(edge_station_data.air_humidity)) {
            edge_station_data.air_humidity = 0.0;
        }
        if (isnan(edge_station_data.air_temperature)) {
            edge_station_data.air_temperature = 0.0;
        }
        if (isnan(edge_station_data.soil_humidity)) {
            edge_station_data.soil_humidity = 0.0;
        }
        if (isnan(edge_station_data.soil_temperature)) {
            edge_station_data.soil_temperature = 0.0;
        }


        
        snprintf(json_buffer, sizeof(json_buffer), "{\"1\": {\"soil humidity\": %.1f, \"soil temperature\": %.1f, \"water_level\": %.5f, \"air tempriture\": %.1f, \"air humidity\": %.1f}, "
                                                    "\"2\": {\"soil humidity\": %.1f, \"soil temperature\": %.1f, \"water_level\": %.5f, \"air tempriture\": %.1f, \"air humidity\": %.1f}}", 
                main.soil_humidity, main.soil_temperature, main.rainfall, main.air_temperature, main.air_humidity,
                edge_station_data.soil_humidity, edge_station_data.soil_temperature, edge_station_data.rainfall, edge_station_data.air_temperature, edge_station_data.air_humidity);
        
        esp_mqtt_client_publish(mqtt_client, "b7fa8001-52c3-4d5e-a8cb-50ce3637d27e/a/data", 
                                           json_buffer , 0, 1, 0);
        ESP_LOGI(TAG,"%s", json_buffer); 
        vTaskDelay(5000/portTICK_PERIOD_MS);
    }      
}
