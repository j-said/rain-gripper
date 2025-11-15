#pragma once
#include <esp_err.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef int (*get_sms_cb)(char *buf, size_t buf_len);

esp_err_t gsm_modem_init(get_sms_cb get_sms);

#ifdef __cplusplus
}
#endif


