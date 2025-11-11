import paho.mqtt.client as paho
import datetime
import logging
import json
import sys
import uuid

# Importing configuration and database modules
from config import settings
from database import get_db_session, SensorData, User, DeviceGroup, Device
from sqlalchemy.orm import joinedload

# --- Налаштування кешу ---
# { user_uuid: { group_local_name: { local_id: device_pk } } }
LOOKUP_CACHE = {}
# {
#     "uuid-user-123": {
#         "a": {
#             1: 1001,
#             2: 1002
#         }
#     }
# }

# Підписуємось на ВСІ топіки
SUBSCRIBE_TOPIC = "#"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
log = logging.getLogger(__name__)


def load_full_cache():
    """
    Завантажує повну "карту відповідності" з БД в пам'ять.
    Виконує 3-table JOIN.
    """
    global LOOKUP_CACHE
    log.info("Завантаження повного кешу (Lookup Map)...")

    new_cache = {}

    try:
        with get_db_session() as db:
            # JOIN User -> DeviceGroup -> Device
            # Використовуємо joinedload для уникнення N+1 запитів
            all_devices = (
                db.query(Device)
                .options(joinedload(Device.group).joinedload(DeviceGroup.owner))
                .all()
            )

            for device in all_devices:
                user_id_str = str(device.group.owner.user_id)
                group_local_name = device.group.local_name
                local_id = device.local_id
                device_pk = device.device_id

                # Створюємо вкладені dict, якщо вони не існують
                if user_id_str not in new_cache:
                    new_cache[user_id_str] = {}
                if group_local_name not in new_cache[user_id_str]:
                    new_cache[user_id_str][group_local_name] = {}

                new_cache[user_id_str][group_local_name][local_id] = device_pk

            LOOKUP_CACHE = new_cache
            log.info(f"Кеш успішно завантажено. {len(all_devices)} пристроїв.")
            # log.debug(f"Вміст кешу: {json.dumps(LOOKUP_CACHE, indent=2)}")

    except Exception as e:
        log.error(f"КРИТИЧНА ПОМИЛКА під час завантаження кешу: {e}", exc_info=True)


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback for when the client connects (API v2)."""
    if reason_code == 0:
        log.info(f"Успішно підключено до: {settings.MQTT_BROKER}")
        # Підписуємось на всі топіки
        client.subscribe(SUBSCRIBE_TOPIC)
        log.info(f"Підписано на топік: {SUBSCRIBE_TOPIC}")
    else:
        log.error(f"Помилка підключення! Код: {reason_code}")


def on_message(client, userdata, msg):
    log.info(f'{msg.payload.decode("utf-8")}')
    """
    Callback: Маршрутизація повідомлення та запис у PostgreSQL.
    """
    try:
        topic = msg.topic

        # --- РОУТИНГ ПОВІДОМЛЕНЬ ---

        # 1. Якщо це команда оновлення кешу
        if topic.startswith("system/cache/invalidate"):
            log.info(f"Отримано сигнал інвалідації кешу. Перезавантаження...")
            # TODO: Зробити розумну інвалідацію (тільки для 1 юзера)
            load_full_cache()
            return

        # 2. Якщо це дані (новий формат: {user_id}/{local_group}/data)
        if topic.endswith("/data"):
            process_sensor_data(topic, msg.payload)
            return

        # 3. Якщо це команда (ми їх ігноруємо, але знаємо про них)
        if topic.endswith("/command"):
            log.debug(f"Ігнорування топіка команди: {topic}")
            return

        # 4. Все інше
        log.warning(f"Отримано, але не оброблено. Невідомий формат топіка: {topic}")

    except Exception as e:
        log.error(
            f"Критична помилка в on_message: {e}. Топік: {msg.topic}", exc_info=True
        )


def process_sensor_data(topic: str, payload: bytes):
    """
    Обробляє повідомлення з даними, використовуючи кеш.
    """
    global LOOKUP_CACHE

    try:
        # Очікувана структура: {user_id}/{local_group}/data
        parts = topic.split("/")

        # Перевірка: 3 частини (uuid, group, data)
        if len(parts) != 3:
            log.warning(f"Некоректний формат топіка даних: {topic}")
            return

        user_id = parts[0]
        group_local_name = parts[1]

        unwraped_message = payload.decode("utf-8")
        try:
            data = json.loads(unwraped_message)
        except json.JSONDecodeError:
            log.error(f"Не вдалося розпарсити JSON з топіка {topic}")
            return

        with get_db_session() as db:
            records_to_add = []

            # data = {'1': {'temp': 20}, '2': {'temp': 21}}
            for local_id_str, payload_json in data.items():
                try:
                    local_id = int(local_id_str)

                    # --- ПОШУК В КЕШІ ---
                    device_pk = (
                        LOOKUP_CACHE.get(user_id, {})
                        .get(group_local_name, {})
                        .get(local_id)
                    )

                    if device_pk is None:
                        log.warning(
                            f"КЕШ-ПРОМАХ: Не знайдено пристрій для {user_id}/{group_local_name}/{local_id}"
                        )
                        continue

                    # --- Запис в БД ---
                    db_record = SensorData(
                        owner_user_id=uuid.UUID(user_id), 
                        device_id=device_pk,  # Знайдений PK
                        payload=payload_json,
                        timestamp=datetime.datetime.now(datetime.UTC),
                    )
                    records_to_add.append(db_record)

                except (ValueError, TypeError):
                    log.warning(
                        f"Некоректний local_id '{local_id_str}' в payload з топіка {topic}"
                    )
                except Exception as e:
                    log.error(f"Помилка обробки sub-payload: {e}", exc_info=True)

            if records_to_add:
                db.add_all(records_to_add)
                db.commit()
                log.info(f"Збережено {len(records_to_add)} записів з топіка {topic}")
            elif not data:
                log.warning(f"Отримано порожнє повідомлення з {topic}")

    except Exception as e:
        log.error(f"Критична помилка в process_sensor_data: {e}", exc_info=True)


if __name__ == "__main__":
    log.info("Запуск MQTT-лісенера...")

    # Завантажуємо кеш ПЕРЕД підключенням
    load_full_cache()

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
