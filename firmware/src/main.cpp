#include <Arduino.h>

#include "sensors.h"

void setup() {
    Serial.begin(115200);
    setupSensors();
}

void loop() {
    readSensors();
    Serial.print("Air Temperature: ");
    Serial.print(currentSensorData.air_temperature);
    Serial.print(" °C, Air Humidity: ");
    Serial.print(currentSensorData.air_humidity);
    Serial.println(" %");
    Serial.print(currentSensorData.soil_humidity);
    Serial.println("");
    delay(2000);
}