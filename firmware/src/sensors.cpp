#include <DHT.h>

#include "sensors.h"
#include "config.h"


DHT dht(DHT22_PIN, DHT22);
SensorData currentSensorData;

void setupSensors() {
    dht.begin();
}

void readSensors() {
    currentSensorData.air_temperature = dht.readTemperature();
    currentSensorData.air_humidity = dht.readHumidity();
    currentSensorData.soil_humidity = analogRead(SOIL_MOISTURE_PIN);
}