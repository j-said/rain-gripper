import logging
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from database import User, DeviceGroup, Device, SensorData

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Статичні ID для тестових даних ---
TEST_USER_ID = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TEST_GROUP_ID = uuid.UUID("f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22")
TEST_DEVICE_ID = uuid.UUID("b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33")


def seed_data():
    """
    Заповнює базу даних початковими даними (User, Group, Device, SensorData).
    """
    db: Session = SessionLocal()

    try:
        existing_user = db.get(User, TEST_USER_ID)

        if existing_user:
            log.warning(f"Користувач {TEST_USER_ID} вже існує. Пропуск заповнення.")
            return

        log.info(f"Створення тестового користувача: {TEST_USER_ID}")
        test_user = User(
            user_id=TEST_USER_ID,
            username="testuser",
            name="Test User",
            email="test@example.com",
            hashed_password="fake_hash_for_testing", 
        )
        db.add(test_user)

        log.info(f"Створення тестової групи пристроїв: {TEST_GROUP_ID}")
        test_group = DeviceGroup(
            group_id=TEST_GROUP_ID,
            owner_user_id=TEST_USER_ID,
            group_name="Main Garden",
        )
        db.add(test_group)

        log.info(f"Створення тестового пристрою: {TEST_DEVICE_ID}")
        test_device = Device(
            device_id=TEST_DEVICE_ID,
            group_id=TEST_GROUP_ID,
            device_name="Sensor Rig 1",
            model="RG-v2",
        )
        db.add(test_device)

        log.info("Генерація 10 тестових записів SensorData...")
        sensor_data_list = []
        base_time = datetime.now(timezone.utc)

        for i in range(10):
            record_time = base_time - timedelta(minutes=i * 10)

            # Створюємо тестовий payload
            payload = {
                "humidity": 45.0 + (i * 1.5),
                "temperature": 21.5 - (i * 0.1),
                "water_level": 88.0 - (i * 2),
            }

            data_record = SensorData(
                timestamp=record_time,
                device_id=TEST_DEVICE_ID,
                owner_user_id=TEST_USER_ID,  # Денормалізована колонка
                payload=payload,
            )
            sensor_data_list.append(data_record)

        db.add_all(sensor_data_list)

        # Фіксуємо всі зміни однією транзакцією
        db.commit()
        log.info("Дані успішно додано до бази даних.")

    except Exception as e:
        log.error(f"Помилка під час заповнення БД: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    log.info("Запуск скрипта заповнення БД (seeding)...")
    Base.metadata.create_all(bind=engine)
    seed_data()
