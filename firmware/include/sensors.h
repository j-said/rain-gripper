#pragma once

#include <Arduino.h>

struct SensorData {
  float air_temperature;
  float air_humidity;
  float soil_temperature;
  float soil_humidity;
  float batteryVoltage;
  int batteryLevel;
  int reedCounter;
  int loraRssi;
};