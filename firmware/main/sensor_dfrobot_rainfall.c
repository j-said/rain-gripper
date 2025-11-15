#include <stdint.h>
#include "sensor_dfrobot_rainfall.h"
//#include "driver/gpio.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include "sdkconfig.h"

static const char *TAG = "Rainfall sensor";

#define I2C_SLAVE_ADDR	             0x1D
#define TIMEOUT_MS		             1000
#define DELAY_MS		             1000

#define I2C_REG_PID                  0x00
#define I2C_REG_VID                  0x02
#define I2C_REG_VERSION              0x0A
#define I2C_REG_TIME_RAINFALL        0x0C
#define I2C_REG_CUMULATIVE_RAINFALL  0x10
#define I2C_REG_RAW_DATA             0x14
#define I2C_REG_SYS_TIME             0x18
#define I2C_REG_RAIN_HOUR            0x26
#define I2C_REG_BASE_RAINFALL        0x28

static esp_err_t configure_i2c(void);
static esp_err_t read_register(uint8_t reg, void* pBuf, size_t size);
//static esp_err_t write_register(uint8_t reg, void* pBuf, size_t size);
//static esp_err_t read_raw_data(uint32_t *raw_data);
static esp_err_t get_sensor_working_time(uint16_t* working_time_min);
static esp_err_t get_rainfall(float* rainfall_mm);
static esp_err_t get_firmware_version(uint16_t* version);

esp_err_t rainfall_init(void)
{
    return configure_i2c();
}

esp_err_t rainfall_read_data(float *data)
{
    return get_rainfall(data);
}

static esp_err_t configure_i2c(void)
{
    i2c_config_t conf = {
		.mode = I2C_MODE_MASTER,
		.sda_io_num = 21,
		.scl_io_num = 22,
		.sda_pullup_en = GPIO_PULLUP_ENABLE,
		.scl_pullup_en = GPIO_PULLUP_ENABLE,
		.master.clk_speed = 100000,
	};

	i2c_param_config(I2C_NUM_0, &conf);
    i2c_driver_install(I2C_NUM_0, I2C_MODE_MASTER, 0, 0, 0);
    uint16_t version;
    esp_err_t err = get_firmware_version(&version);
    if (!err){
        ESP_LOGI(TAG, "Version: %d.%d.%d.%d", version >> 12, ( version >> 8 ) & 0x0F, ( version >> 4 ) & 0x0F, version & 0x0F);
        uint16_t working_time_min;
        err = get_sensor_working_time(&working_time_min);
        if (!err) {
            ESP_LOGI(TAG, "Working time: %hu min", working_time_min);
        }
        float rainfall;
        err = get_rainfall(&rainfall);
        if (!err) {
            ESP_LOGI(TAG, "Rainfall %d", (int)(rainfall * 10000.0));
        }            
    }
    return err;
}

static esp_err_t read_register(uint8_t reg, void* pBuf, size_t size)
{
    esp_err_t err = i2c_master_write_to_device(I2C_NUM_0, I2C_SLAVE_ADDR, &reg, 1, TIMEOUT_MS / portTICK_PERIOD_MS);
    if (!err) {
      err = i2c_master_read_from_device(I2C_NUM_0, I2C_SLAVE_ADDR, (uint8_t*)pBuf, size, TIMEOUT_MS/portTICK_PERIOD_MS);
    }
    return err;    
}

static esp_err_t get_sensor_working_time(uint16_t* working_time_min)
{
    uint8_t buff[2] = { 0 };
    esp_err_t err = read_register( I2C_REG_SYS_TIME, (void*)buff, sizeof(buff));
    if (!err)
    {
        *working_time_min = buff[0] | ( ( (uint32_t)buff[1] ) << 8 );
    }

  return err;
}

static esp_err_t get_rainfall(float* rainfall_mm)
{
    uint32_t rainfall = 0;
    uint8_t buff[4] = {0};
    esp_err_t err = read_register(I2C_REG_CUMULATIVE_RAINFALL, (void*)buff, 4);
    if(!err){
        rainfall = buff[0] | ( ( (uint32_t)buff[1] ) << 8 ) | ( ( (uint32_t)buff[2]) << 16 ) | ( ( (uint32_t)buff[3] ) << 24 );
        *rainfall_mm = rainfall / 10000.0;
    }
    return err;
}

static esp_err_t get_firmware_version(uint16_t* version)
{
    uint8_t buff[2] = {0};
    esp_err_t err = read_register(I2C_REG_VERSION, (void*)buff, 2);
    *version = buff[0] | ( ((uint16_t)buff[1]) << 8 );
    return err;
}

#if 0
static esp_err_t read_raw_data(uint32_t *raw_data)
{
    return read_register(I2C_REG_RAW_DATA, raw_data, sizeof(uint32_t));
}

static esp_err_t write_register(uint8_t reg, void* pBuf, size_t size)
{
    esp_err_t err = i2c_master_write_to_device(I2C_NUM_0, I2C_SLAVE_ADDR, &reg, 1, TIMEOUT_MS / portTICK_PERIOD_MS);
    if (!err) {
      err = i2c_master_write_to_device(I2C_NUM_0, I2C_SLAVE_ADDR, (uint8_t*)pBuf, size, TIMEOUT_MS/portTICK_PERIOD_MS);
    }
    return err;     
}
#endif
