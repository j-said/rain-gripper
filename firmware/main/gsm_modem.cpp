#include "gsm_modem.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <esp_log.h>
#include "esp_modem_config.h"
#include "cxx_include/esp_modem_dte.hpp"
#include "esp_modem_config.h"
#include "cxx_include/esp_modem_api.hpp"
#include "cxx_include/esp_modem_command_library.hpp"
#include "esp_event.h"
#include "esp_event_base.h"
#include "sdkconfig.h"

using namespace esp_modem;

#if defined(CONFIG_EXAMPLE_FLOW_CONTROL_NONE)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_NONE
#elif defined(CONFIG_EXAMPLE_FLOW_CONTROL_SW)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_SW
#elif defined(CONFIG_EXAMPLE_FLOW_CONTROL_HW)
#define EXAMPLE_FLOW_CONTROL ESP_MODEM_FLOW_CONTROL_HW
#endif

extern "C" {

ESP_EVENT_DECLARE_BASE(MODEM_EVENTS);

enum {
    RING_EVENT                    
};

ESP_EVENT_DEFINE_BASE(MODEM_EVENTS);

}

namespace
{
    const char *TAG = "GSM modem";
    std::shared_ptr<DTE> uart_dte;
    get_sms_cb sms_cb;
    std::string phone_number;
    // Event loops
    esp_event_loop_handle_t evt_loop;

    extern "C" void ring_event_handler(void* event_handler_arg,
                                    esp_event_base_t event_base,
                                    int32_t event_id,
                                    void* event_data)
    {
        ESP_LOGI(TAG, "Hanging up");
        dce_commands::hang_up(&*uart_dte);

        if(sms_cb != NULL) {
            char buffer[256];
            sms_cb(buffer, sizeof(buffer));
            ESP_LOGI(TAG, "Sending SMS %s", buffer);
            dce_commands::send_sms(&*uart_dte, phone_number, buffer);
            phone_number = "";
        }    
    }
 
    command_result urc_cb(uint8_t *data, size_t len)
    {
        std::string_view urc_line((char*)data, len);
        constexpr std::string_view ring = "RING";
        constexpr std::string_view pattern = "+CLIP: ";
   
        if (urc_line.find(ring) != std::string::npos &&
            urc_line.find(pattern) != std::string::npos)
        {
            // Extract the phone number
            auto start = urc_line.find('\"');
            if (start != std::string::npos) {
                auto end = urc_line.find('\"', start + 1);
                if (end != std::string::npos) {
                    auto sv = urc_line.substr(start + 1, end - start - 1);
                    if (!phone_number.length())
                    {
                        phone_number = {sv.begin(), sv.end()};
                        ESP_LOGI(TAG, "Received a phone call from %s", phone_number.c_str());
                        esp_event_post_to(evt_loop, MODEM_EVENTS, RING_EVENT, NULL, 0, portMAX_DELAY);
                    }
                }
            }
        }
        return command_result::OK;
    }
}

extern "C" esp_err_t gsm_modem_init(get_sms_cb get_sms)
{
    sms_cb = get_sms;

    esp_event_loop_args_t loop_args = {
        .queue_size = 5,
        .task_name = "loop_task", // task will be created
        .task_priority = 4,
        .task_stack_size = 4096,
        .task_core_id = tskNO_AFFINITY
    };

    ESP_ERROR_CHECK(esp_event_loop_create(&loop_args, &evt_loop));
    ESP_ERROR_CHECK(esp_event_handler_instance_register_with(evt_loop, MODEM_EVENTS, RING_EVENT, ring_event_handler, evt_loop, NULL));

    esp_modem_dte_config_t dte_config = ESP_MODEM_DTE_DEFAULT_CONFIG();
    dte_config.uart_config.baud_rate = 9600;
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

    uart_dte = create_uart_dte(&dte_config);
    uart_dte->set_urc_cb(urc_cb);
    std::string module_name;
    command_result result = dce_commands::get_module_name(&*uart_dte, module_name);
    if (command_result::OK == result) {
        ESP_LOGI(TAG, "module name: %s", module_name.c_str());

    //     dce_commands::sms_txt_mode(&*uart_dte, true);
    //     dce_commands::sms_character_set(&*uart_dte);
            dce_commands::set_data_mode(&*uart_dte);    
    }


    return command_result::OK == result? ESP_OK : ESP_FAIL;
}

