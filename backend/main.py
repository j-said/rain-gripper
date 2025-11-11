import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # ДОДАНО
from jose import JWTError, jwt

# Локальні імпорти
import crud
import schemas
import mqtt_publisher
from database import SessionLocal, engine, Base, User, DeviceGroup, Device
from config import settings

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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
    version="0.2.0",
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
    user_id: uuid.UUID,
    device_group_local_name: str,
    command: schemas.CommandRequest,
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
        # ОНОВЛЕНО: Топік відповідає mqtt_listener
        topic = f"{user_id}/{device_group_local_name}/command"

        log.info(f"Публікація у MQTT: Топік={topic}")
        result = mqtt_publisher.mqtt_client.publish(topic, payload_str, qos=1)

        if result.rc != 0:
            log.error(f"Помилка при постановці в чергу MQTT: {result}")
            raise HTTPException(status_code=500, detail="Помилка при відправці MQTT")

        log.info("Команду успішно надіслано в чергу paho.")

    except Exception as e:
        log.error(f"Критична помилка при публікації MQTT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутрішня помилка MQTT: {e}")


# --- Логіка Автентифікації ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Отримує токен, валідує його та повертає об'єкт User з БД.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[crud.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(token_data.user_id)
    except ValueError:
        raise credentials_exception

    user = crud.get_user(db, user_id=user_uuid)
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to RainGripper API"}


# --- Ендпоінти Автентифікації ---


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=crud.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/users/me", response_model=schemas.User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- Users ---


@app.post(
    "/api/v1/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # ДОДАНО: Обробка помилки унікальності
    try:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        return crud.create_user(db=db, user=user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email or username already exists")


# --- Device Groups (ЗАХИЩЕНО) ---


@app.post(
    "/api/v1/groups/",  # ОНОВЛЕНО: Ендпоінт
    response_model=schemas.DeviceGroup,
    status_code=status.HTTP_201_CREATED,
)
def create_device_group_for_user(
    group: schemas.DeviceGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.user_id
    try:
        # ПУБЛІКАЦІЯ В MQTT ДЛЯ ОНОВЛЕННЯ КЕШУ
        mqtt_publisher.mqtt_client.publish(f"system/cache/invalidate/{user_id}", "")

        return crud.create_device_group(db=db, group=group, user_id=user_id)
    except IntegrityError:  # ДОДАНО: Обробка помилки
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Group with local_name '{group.local_name}' already exists for this user.",
        )


@app.get(
    "/api/v1/groups/", response_model=List[schemas.DeviceGroup]
)  # ОНОВЛЕНО: Ендпоінт
def read_user_device_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.user_id
    groups = crud.get_device_groups_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return groups


# --- Devices (ЗАХИЩЕНО) ---


@app.post(
    "/api/v1/groups/{group_id}/devices/",
    response_model=schemas.Device,
    status_code=status.HTTP_201_CREATED,
)
def create_device_for_group(
    group_id: int,
    device: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Перевірка, чи належить група поточному юзеру
    db_group = (
        db.query(DeviceGroup)
        .filter(
            DeviceGroup.group_id == group_id,
            DeviceGroup.owner_user_id == current_user.user_id,
        )
        .first()
    )

    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found or access denied")

    try:
        # ПУБЛІКАЦІЯ В MQTT ДЛЯ ОНОВЛЕННЯ КЕШУ
        mqtt_publisher.mqtt_client.publish(
            f"system/cache/invalidate/{current_user.user_id}", ""
        )
        return crud.create_device(db=db, device=device, group_id=group_id)

    except IntegrityError as e:  # ДОДАНО: Обробка помилки
        db.rollback()
        detail = "Unknown integrity error"
        if "uq_group_local_id" in str(e):
            detail = (
                f"Device with local_id {device.local_id} already exists in this group."
            )
        elif "uq_mac_address" in str(e):
            detail = f"Device with MAC address {device.mac_address} already exists."
        raise HTTPException(status_code=409, detail=detail)


@app.get("/api/v1/groups/{group_id}/devices/", response_model=List[schemas.Device])
def read_group_devices(
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Перевірка, чи належить група поточному юзеру
    db_group = (
        db.query(DeviceGroup)
        .filter(
            DeviceGroup.group_id == group_id,
            DeviceGroup.owner_user_id == current_user.user_id,
        )
        .first()
    )

    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found or access denied")

    devices = crud.get_devices_by_group(db, group_id=group_id, skip=skip, limit=limit)
    return devices


# --- Sensor Data (ЗАХИЩЕНО) ---


@app.get("/api/v1/data/", response_model=List[schemas.SensorDataResponse])
def get_data_slice(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: datetime = Query(default=None, description="ISO 8601 format"),
    end_date: datetime = Query(default=None, description="ISO 8601 format"),
):
    user_id = current_user.user_id
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


# --- Commands (MQTT) (ЗАХИЩЕНО) ---


@app.post(
    "/api/v1/command/{device_group_local_name}", status_code=status.HTTP_202_ACCEPTED
)
def send_command_to_device(
    device_group_local_name: str,  # 'a', 'b', 'c'
    command: schemas.CommandRequest,
    current_user: User = Depends(get_current_user),  # ЗАХИЩЕНО
    db: Session = Depends(get_db),
):
    """
    Надсилає команду на конкретну групу пристроїв ('local_name')
    """
    db_found = (
        db.query(DeviceGroup)
        .filter(
            DeviceGroup.local_name == device_group_local_name,
            DeviceGroup.owner_user_id == current_user.user_id,
        )
        .first()
    )

    if not db_found:
        raise HTTPException(status_code=404, detail="Group not found or access denied")

    log.info(
        f"Отримано API запит на команду для {db_found.user_id}/{device_group_local_name}"
    )
    publish_mqtt_command(db_found.user_id, device_group_local_name, command)
    return {
        "status": "accepted",
        "message": f"Команду '{command.action}' надіслано у топік.",
    }


if __name__ == "__main__":
    log.info("Запуск FastAPI сервера (для розробки)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
