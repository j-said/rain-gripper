import paho.mqtt.client as paho
import logging
from config import settings

log = logging.getLogger(__name__)

mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="fastapi-server")


def connect_mqtt():
    """Підключає клієнт та запускає фоновий потік"""
    try:
        log.info(f"Підключення API до MQTT брокера: {settings.MQTT_BROKER}")
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        if settings.MQTT_PORT == 8883:
            log.info("Увімкнено TLS (порт 8883).")
            mqtt_client.tls_set()

        mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
        mqtt_client.loop_start()  
        log.info("API MQTT підключено та loop запущено.")

    except Exception as e:
        log.error(f"Не вдалося підключити API до MQTT: {e}", exc_info=True)


def disconnect_mqtt():
    """Відключає MQTT клієнт"""
    log.info("Відключення API від MQTT...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    log.info("API MQTT відключено.")
