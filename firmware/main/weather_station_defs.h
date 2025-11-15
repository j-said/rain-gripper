#pragma once

#include <stdint.h>

#define WS_PROTOCOL_VERSION 1

typedef struct 
{
    uint8_t device_id;
    float rainfall; // in mm
    float air_temperature; // in degree Celcium
    float air_humidity; // in percentage
    float soil_temperature; // in degree Celcium
    float soil_humidity; // in percentage
    uint32_t is_raining; // boolean  
} weather_condition_t;


typedef struct
{
    uint8_t protocol_version;
    uint8_t device_id;
    uint16_t message_num;
    float rainfall; // in mm
    float air_temperature; // in degree Celcium
    float air_humidity; // in percentage
    float soil_temperature; // in degree Celcium
    float soil_humidity; // in percentage
    uint32_t is_raining; // boolean
} weather_station_packet_t;
