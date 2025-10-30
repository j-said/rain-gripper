import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB  # Специфічно для PostgreSQL

# Local imports
from config import settings

log = logging.getLogger(__name__)

try:
    engine = create_engine(settings.DATABASE_URL)
    log.info("Створено рушій (engine) SQLAlchemy.")
except Exception as e:
    log.error(f"Помилка створення рушія (engine) SQLAlchemy: {e}")
    log.error(f"Перевірте ваш DATABASE_URL. Поточне: {settings.DATABASE_URL}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class SensorData(Base):
    """
    Модель для зберігання всіх вхідних даних з сенсорів.
    """

    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)

    # Додаємо час створення запису, з default=now() на рівні БД
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer_id = Column(String, index=True, nullable=False)
    sub_device_id = Column(String, index=True, nullable=False)
    data_type = Column(String, index=True, nullable=False)

    payload = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<SensorData(id={self.id}, topic='{self.customer_id}/{self.sub_device_id}/{self.data_type}')>"


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


if __name__ == "__main__":
    # Цей код виконається, якщо ви запустите: python database.py
    create_all_tables()
