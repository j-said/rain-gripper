import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List

import uvicorn
import paho.mqtt.client as paho
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# Локальні імпорти
import crud
import schemas
import mqtt_publisher
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код при старті
    mqtt_publisher.connect_mqtt()
    yield
    # Код при зупинці
    mqtt_publisher.disconnect_mqtt()


app = FastAPI(
    title="RainGripper IoT API",
    description="API для отримання даних з IoT пристроїв.",
    version="0.1.0",
    lifespan=lifespan,
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
    user_id: str, device_group: str, command: schemas.CommandRequest
):
    """
    Публікує команду, використовуючи існуюче з'єднання.
    """
    try:
        payload_dict = {
            "command": command.action,
            **(command.parameters or {}),
        }
        payload_str = json.dumps(payload_dict)
        topic = f"{user_id}/{device_group}/command"

        log.info(f"Публікація у MQTT: Топік={topic}")

        result = mqtt_publisher.mqtt_client.publish(topic, payload_str, qos=1)

        if result.rc != 0:
            log.error(f"Помилка при постановці в чергу MQTT: {result}")
            raise HTTPException(status_code=500, detail="Помилка при відправці MQTT")

        log.info("Команду успішно надіслано в чергу paho.")

    except Exception as e:
        log.error(f"Критична помилка при публікації MQTT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутрішня помилка MQTT: {e}")


@app.get("/")
def read_root():
    """Корінцевий ендпоінт для перевірки працездатності."""
    return {"status": "ok", "message": "Welcome to RainGripper API"}


# TODO GET rquest to update sensor logs for the frontend from DB   MUST TAKE: humidity: float, water_level: float, (? coordinates: str)
# TODO GET request to send list of devices from DB to frontend !!


@app.get("/api/v1/data/{user_id}", response_model=List[schemas.SensorDataResponse])
def get_data_slice(
    user_id: str,
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
            db=db, user_id=user_id, start_date=start_date, end_date=end_date
        )
        return data
    except Exception as e:
        log.error(f"Помилка в ендпоінті get_data_slice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутрішня помилка сервера")


# @app.post("/api/v1/command/{user_id}/{sub_device_id}", status_code=202)  # Accepted
# def send_command_to_device(
#     user_id: str,
#     sub_device_id: str,  # (напр. 'gateway_A' або 'all')
#     command: schemas.CommandRequest,
# ):
#     """
#     Надсилає команду на конкретний пристрій (або групу)
#     через MQTT.
#     """
#     log.info(f"Отримано API запит на команду для {user_id}/{sub_device_id}")

#     # Передаємо роботу MQTT-паблішеру
#     # (Ця функція викличе HTTPException у разі помилки)
# publish_mqtt_command(user_id, sub_device_id, command)

#     return {
#         "status": "accepted",
#         "message": f"Команду '{command.action}' надіслано у топік.",
#     }


if __name__ == "__main__":
    log.info("Запуск FastAPI сервера (для розробки)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
