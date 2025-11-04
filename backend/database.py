from contextlib import contextmanager
from datetime import datetime

from sqlalchemy.dialects.postgresql import (
    UUID,
    JSONB,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
)
from sqlalchemy.sql import func
from sqlalchemy import Identity
from sqlalchemy import (
    create_engine,
    Column,
    String,
    ForeignKey,
    TIMESTAMP,
    BigInteger,
    Index,
)

# Local imports
from config import settings
import logging

log = logging.getLogger(__name__)

try:
    engine = create_engine(settings.DATABASE_URL)
    log.info("Створено рушій (engine) SQLAlchemy.")
except Exception as e:
    log.error(f"Помилка створення рушія (engine) SQLAlchemy: {e}")
    log.error(f"Перевірте ваш DATABASE_URL. Поточне: {settings.DATABASE_URL}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db_session():
    """
    Безпечний менеджер контексту для отримання сесії БД.
    Використовується у mqtt_listener.py
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_all_tables():
    """
    Функція для створення всіх таблиць (визначених у Base) у базі даних.
    """
    try:
        log.info("Спроба створення таблиць (якщо не існують)...")
        Base.metadata.create_all(bind=engine)
        log.info("Таблиці успішно створено (або вже існували).")
    except Exception as e:
        log.error(f"ПОМИЛКА: Не вдалося підключитися або створити таблиці.")
        log.error(f"Деталі: {e}")
        log.error("Переконайтесь, що PostgreSQL запущено і дані в .env правильні.")


# == SQLAlchemy Models ==
class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    username = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    email = Column(
        String(255), nullable=False, unique=True, index=True
    )  # index=True створює idx_users_email
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # ORM Зв'язок: "Я володію багатьма групами"
    device_groups = relationship(
        "DeviceGroup", back_populates="owner", cascade="all, delete"
    )


class DeviceGroup(Base):
    __tablename__ = "device_groups"

    group_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    owner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_name = Column(String(100), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # ORM Зв'язки
    owner = relationship("User", back_populates="device_groups")
    devices = relationship("Device", back_populates="group", cascade="all, delete")

    __table_args__ = (Index("idx_device_groups_owner", owner_user_id),)


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("device_groups.group_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_name = Column(String(100), nullable=False)
    model = Column(String(100))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # ORM Зв'язки
    group = relationship("DeviceGroup", back_populates="devices")
    sensor_data = relationship(
        "SensorData", back_populates="device", cascade="all, delete"
    )

    __table_args__ = (Index("idx_devices_group", group_id),)


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(BigInteger, Identity(), primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- ДЕНОРМАЛІЗОВАНА КОЛОНКА ---
    # Ми дублюємо owner_user_id тут при записі даних
    owner_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True
    )

    payload = Column(JSONB, nullable=False)

    device = relationship("Device", back_populates="sensor_data")

    __table_args__ = (
        # Індекс для запиту по користувачу та часу
        Index("idx_sensor_data_user_time", owner_user_id, timestamp.desc()),
        # Індекс  для запитів по конкретному пристрою та часу
        Index("idx_sensor_data_device_time", device_id, timestamp.desc()),
        # GIN індекс для JSONB
        Index("idx_sensor_data_payload", payload, postgresql_using="gin"),
    )


if __name__ == "__main__":
    create_all_tables()
