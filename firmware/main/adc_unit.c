#include "adc_unit.h"

static adc_oneshot_unit_handle_t adc_handle;

esp_err_t adc_unit_init()
{
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = (0),
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };

    return adc_oneshot_new_unit(&init_config, &adc_handle);
}

adc_oneshot_unit_handle_t* adc_unit_get_handle()
{
    return &adc_handle;
}