import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Локальні імпорти
import crud
import schemas
import mqtt_publisher
from database import SessionLocal, engine, Base, User, DeviceGroup, Device
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
    log.info("FastAPI запуск...")
    mqtt_publisher.connect_mqtt()
    yield
    log.info("FastAPI зупинка...")
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


# --- Users ---


@app.post(
    "/api/v1/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED
)  # Create User (FUTURE)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/api/v1/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/v1/users/{user_id}", response_model=schemas.User)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# --- Device Groups ---


@app.post(
    "/api/v1/users/{user_id}/groups/",
    response_model=schemas.DeviceGroup,
    status_code=status.HTTP_201_CREATED,
)
def create_device_group_for_user(
    user_id: uuid.UUID, group: schemas.DeviceGroupCreate, db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_device_group(db=db, group=group, user_id=user_id)


# GET user devices groups SASHA DO IT
@app.get("/api/v1/users/{user_id}/groups/", response_model=List[schemas.DeviceGroup])
def read_user_device_groups(
    user_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    groups = crud.get_device_groups_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return groups


# --- Devices ---


@app.post(
    "/api/v1/groups/{group_id}/devices/",
    response_model=schemas.Device,
    status_code=status.HTTP_201_CREATED,
)
def create_device_for_group(
    group_id: uuid.UUID, device: schemas.DeviceCreate, db: Session = Depends(get_db)
):
    # TODO: Додати перевірку, чи group_id існує
    return crud.create_device(db=db, device=device, group_id=group_id)


# GET rquest of devices in grops SASHA DO IT
@app.get("/api/v1/groups/{group_id}/devices/", response_model=List[schemas.Device])
def read_group_devices(
    group_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    # TODO: Додати перевірку, чи group_id існує
    devices = crud.get_devices_by_group(db, group_id=group_id, skip=skip, limit=limit)
    return devices


# --- Sensor Data ---


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
        end_date = datetime.now(timezone.utc)
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


# --- Commands (MQTT) ---


@app.post(
    "/api/v1/command/{user_id}/{device_group}", status_code=status.HTTP_202_ACCEPTED
)
def send_command_to_device(
    user_id: str,
    device_group: str,  # (напр. 'Main Garden' або 'all')
    command: schemas.CommandRequest,
):
    """
    Надсилає команду на конкретну групу пристроїв
    через MQTT.
    """
    log.info(f"Отримано API запит на команду для {user_id}/{device_group}")

    # Передаємо роботу MQTT-паблішеру
    # (Ця функція викличе HTTPException у разі помилки)
    publish_mqtt_command(user_id, device_group, command)

    return {
        "status": "accepted",
        "message": f"Команду '{command.action}' надіслано у топік.",
    }


if __name__ == "__main__":
    log.info("Запуск FastAPI сервера (для розробки)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
