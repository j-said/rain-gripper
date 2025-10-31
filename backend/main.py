import logging
import json
from datetime import datetime, timedelta
from typing import List

import uvicorn
import paho.mqtt.client as paho
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# Локальні імпорти
import crud
import schemas
from database import SessionLocal, engine, Base
from config import settings

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

try:
    Base.metadata.create_all(bind=engine)
    log.info("Перевірено/Створено таблиці БД.")
except Exception as e:
    log.error(f"Помилка під час create_all: {e}")

app = FastAPI(
    title="RainGripper IoT API",
    description="API для отримання даних з IoT пристроїв.",
    version="0.1.0",
)


def get_db():
    """
    Залежність FastAPI: надає сесію БД для API ендпоінту
    та гарантовано закриває її після завершення.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def publish_mqtt_command(
    customer_id: str, sub_device_id: str, command: schemas.CommandRequest
):
    """
    Підключається до MQTT, публікує команду та відключається.
    Це простий, хоч і не найефективніший, спосіб для MVP.
    """
    try:
        payload_dict = {
            "command": command.action,
            **(command.parameters or {}),
        }
        payload_str = json.dumps(payload_dict)

        # топік для команд 'clients/{cust_id}/{sub_device_id}/command'
        topic = f"clients/{customer_id}/{sub_device_id}/command"

        # Налаштовуємо клієнт
        mqtt_client = paho.Client(
            paho.CallbackAPIVersion.VERSION2, client_id="fastapi-publisher"
        )
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        if settings.MQTT_PORT == 8883:
            mqtt_client.tls_set()

        # Підключаємось
        mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)

        # Публікуємо
        log.info(f"Публікація у MQTT: Топік={topic}, Payload={payload_str}")
        result = mqtt_client.publish(topic, payload_str, qos=1)

        # Чекаємо підтвердження публікації
        result.wait_for_publish(timeout=5)

        if not result.is_published():
            log.error("Не вдалося опублікувати MQTT команду (timeout)")
            raise HTTPException(
                status_code=504, detail="Помилка публікації MQTT (Timeout)"
            )

        mqtt_client.disconnect()
        log.info("Команду успішно надіслано.")

    except Exception as e:
        log.error(f"Критична помилка при публікації MQTT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутрішня помилка MQTT: {e}")


@app.get("/")
def read_root():
    """Корінцевий ендпоінт для перевірки працездатності."""
    return {"status": "ok", "message": "Welcome to RainGripper API"}


@app.get("/api/v1/data/{customer_id}", response_model=List[schemas.SensorDataResponse])
def get_data_slice(
    customer_id: str,
    db: Session = Depends(get_db),
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
):
    """
    Отримує зріз даних для клієнта за вказаний період.
    """
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=1)

    try:
        data = crud.get_sensor_data(
            db=db, customer_id=customer_id, start_date=start_date, end_date=end_date
        )
        return data
    except Exception as e:
        log.error(f"Помилка в ендпоінті get_data_slice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутрішня помилка сервера")


@app.post("/api/v1/command/{customer_id}/{sub_device_id}", status_code=202)  # Accepted
def send_command_to_device(
    customer_id: str,
    sub_device_id: str,  # (напр. 'gateway_A' або 'all')
    command: schemas.CommandRequest,
):
    """
    Надсилає команду на конкретний пристрій (або групу)
    через MQTT.
    """
    log.info(f"Отримано API запит на команду для {customer_id}/{sub_device_id}")

    # Передаємо роботу MQTT-паблішеру
    # (Ця функція викличе HTTPException у разі помилки)
    publish_mqtt_command(customer_id, sub_device_id, command)

    return {
        "status": "accepted",
        "message": f"Команду '{command.action}' надіслано у топік.",
    }


if __name__ == "__main__":
    log.info("Запуск FastAPI сервера (для розробки)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
