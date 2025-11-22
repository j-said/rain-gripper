import logging
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# SQLAlchemy
from database import SensorData, User, Device, DeviceGroup
import schemas
from config import settings

log = logging.getLogger(__name__)

ALGORITHM = "HS256"
# Використовуємо SECRET_KEY з .env
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    password_bytes = plain_password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

# --- User ---
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Функції автентифікації (для main.py) ---


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = 30):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # Переконуємось, що user_id це рядок
    if isinstance(to_encode.get("sub"), uuid.UUID):
        to_encode["sub"] = str(to_encode["sub"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
    db_group = DeviceGroup(
        display_name=group.display_name,
        local_name=group.local_name,
        owner_user_id=user_id,
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


# --- Device ---
def get_devices_by_group(
    db: Session,
    group_id: int,
    skip: int = 0,
    limit: int = 100,
):
    return (
        db.query(Device)
        .filter(Device.group_id == group_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_device(db: Session, device: schemas.DeviceCreate, group_id: int):
    db_device = Device(
        device_name=device.device_name,
        model=device.model,
        group_id=group_id,
        local_id=device.local_id,
        mac_address=device.mac_address,
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


# --- SensorData (Denormalized) ---
def get_sensor_data(
    db: Session,
    user_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
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
