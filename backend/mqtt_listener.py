import paho.mqtt.client as paho
import datetime
import logging
import json
import sys
import ssl 

# Importing configuration and database modules
from config import settings
from database import get_db_session, SensorData

SUBSCRIBE_TOPIC = "#"

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

        # Очікувана структура: {user_id}/{device_group}/{data_type}
        # (e.g. c123/groupA/sensor_data/{"{device_id: UUID}": {"humidity": 45.6 etc., }, ...})
        parts = topic.split("/")
        if (
            len(parts) != 3
            or parts[2]
            == "command"  # костиль, щоб не заносило команди в БД з поламаного POST api, далі замінити на матч кейс
        ):
            log.warning(f"Невідомий формат топіка: {topic}")
            return

        user_id = parts[0]
        device_group = parts[1]
        data_type = parts[2]

        unwraped_message = msg.payload.decode("utf-8")
        try:
            data = json.loads(unwraped_message)
        except json.JSONDecodeError:
            log.error(f"Не вдалося розпарсити JSON з топіка {topic}")
            return

        with get_db_session() as db:
            records_to_add = []

            for key, value in data.items():
                device_id = key
                payload_json = value

                db_record = SensorData(
                    owner_user_id=user_id,
                    device_id=device_id,
                    payload=payload_json,
                    timestamp=datetime.datetime.now(datetime.UTC), # current UTC timestamp
                )
                records_to_add.append(db_record)

            if records_to_add:
                db.add_all(records_to_add)
                db.commit()
                log.info(f"Збережено {len(records_to_add)} записів з топіка {topic}")
            else:
                log.warning(f"Отримано порожнє повідомлення з {topic}")

    except Exception as e:
        log.error(
            f"Критична помилка в on_message: {e}. Топік: {msg.topic}", exc_info=True
        )


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
            log.info("Увімкнено TLS (порт 8883) - ІГНОРУЄМО ПЕРЕВІРКУ СЕРТИФІКАТА.")
            # Вказуємо, що ми не перевіряємо сертифікат
            mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT, cert_reqs=ssl.CERT_NONE)
            # Дозволяємо "небезпечне" з'єднання
            mqtt_client.tls_insecure_set(True)

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
