import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

# SQLAlchemy
from database import SensorData, User, Device, DeviceGroup
import schemas

log = logging.getLogger(__name__)


# --- User ---
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    # УВАГА: Тут має бути реальне хешування паролю!
    # Зараз просто імітація:
    fake_hashed_password = user.password + "_hashed"

    db_user = User(
        username=user.username,
        email=user.email,
        name=user.name,
        hashed_password=fake_hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- DeviceGroup ---
def get_device_groups_by_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
):
    return (
        db.query(DeviceGroup)
        .filter(DeviceGroup.owner_user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_device_group(
    db: Session, group: schemas.DeviceGroupCreate, user_id: uuid.UUID
):
    db_group = DeviceGroup(group_name=group.group_name, owner_user_id=user_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


# --- Device ---
def get_devices_by_group(
    db: Session, group_id: uuid.UUID, skip: int = 0, limit: int = 100
):
    return (
        db.query(Device)
        .filter(Device.group_id == group_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_device(db: Session, device: schemas.DeviceCreate, group_id: uuid.UUID):
    db_device = Device(
        device_name=device.device_name, model=device.model, group_id=group_id
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


# --- SensorData (Denormalized) ---
def get_sensor_data(
    db: Session, user_id: str, start_date: datetime, end_date: datetime
):
    """
    Отримує дані, використовуючи швидку денормалізовану схему.
    """
    log.info(f"Запит даних для {user_id} з {start_date} по {end_date}")

    try:
        query = (
            db.query(SensorData)
            .filter(
                SensorData.owner_user_id == user_id,
                SensorData.timestamp >= start_date,
                SensorData.timestamp <= end_date,
            )
            .order_by(SensorData.timestamp.asc())
        )
        return query.all()

    except Exception as e:
        log.error(f"Помилка запиту до БД: {e}")
        return []
