import paho.mqtt.client as paho
import logging
import sys
import json

# Importing configuration and database modules
from config import settings
from database import get_db_session, SensorData

SUBSCRIBE_TOPIC = "clients/#"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
log = logging.getLogger(__name__)


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback for when the client connects (API v2)."""
    if reason_code == 0:
        log.info(f"Успішно підключено до: {settings.MQTT_BROKER}")
        client.subscribe(SUBSCRIBE_TOPIC)
        log.info(f"Підписано на топік: {SUBSCRIBE_TOPIC}")
    else:
        log.error(f"Помилка підключення! Код: {reason_code}")


def on_message(client, userdata, msg):
    """
    Callback: Парсинг повідомлення та запис у PostgreSQL.
    """
    try:
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")

        # Очікувана структура: clients/{cust_id}/{sub_device_id}/{data_type}
        parts = topic.split("/")
        if len(parts) != 4 or parts[0] != "clients":
            log.warning(f"Невідомий формат топіка: {topic}")
            return

        customer_id = parts[1]
        sub_device_id = parts[2]
        data_type = parts[3]

        # Парсинг payload
        try:
            payload_json = json.loads(payload_str)
        except json.JSONDecodeError:
            log.error(f"Не вдалося розпарсити JSON з: {payload_str}")
            return

        # Використовуємо context manager для безпечної сесії
        with get_db_session() as db:

            db_record = SensorData(
                customer_id=customer_id,
                sub_device_id=sub_device_id,
                data_type=data_type,
                payload=payload_json,  # Зберігаємо payload як JSONB
            )

            db.add(db_record)
            db.commit()

            log.info(
                f"Збережено: {customer_id}/{data_type}"
            )  # (Опціонально, для debug)

    except Exception as e:
        log.error(f"Помилка в on_message: {e}. Топік: {msg.topic}")


if __name__ == "__main__":
    log.info("Запуск MQTT-лісенера...")

    mqtt_client = paho.Client(
        paho.CallbackAPIVersion.VERSION2,
        client_id="raingripper-server-listener",
        protocol=paho.MQTTv5,
    )

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        log.info("Використання логіну/паролю.")
        mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    else:
        log.info("Підключення без логіну/паролю.")

    if settings.MQTT_PORT == 8883:
        log.info("Увімкнено TLS (порт 8883).")
        mqtt_client.tls_set()

    try:
        mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
    except Exception as e:
        log.error(f"Не вдалося підключитися до брокера: {e}")
        sys.exit(1)

    log.info("Запуск мережевого циклу... CTRL+C для виходу.")
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        log.info("Скрипт зупинено. Відключення.")
        mqtt_client.disconnect()
        log.info("Відключено.")
