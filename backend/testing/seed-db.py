import logging
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, Base, engine, create_all_tables
from database import User, DeviceGroup, Device, SensorData
from crud import get_password_hash  # Використовуємо той самий хешер, що й у crud

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Статичні ID для тестових даних ---
TEST_USER_ID = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASS = "password123"

# MAC-адреси для пристроїв
MAC_1 = "00:1A:2B:3C:4D:5E"
MAC_2 = "00:1A:2B:3C:4D:5F"


def seed_data():
    """
    Заповнює базу даних актуальними даними (User, Group, Device, SensorData).
    """
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == TEST_USER_EMAIL).first()

        if existing_user:
            log.warning(f"Користувач {TEST_USER_EMAIL} вже існує. Пропуск заповнення.")
            db_user = existing_user
        else:
            log.info(f"Створення тестового користувача: {TEST_USER_EMAIL}")
            hashed_password = get_password_hash(TEST_USER_PASS)  # Хешуємо пароль
            db_user = User(
                user_id=TEST_USER_ID,
                username="testuser",
                name="Test User",
                email=TEST_USER_EMAIL,
                hashed_password=hashed_password,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            log.info(f"Створено користувача. UUID: {db_user.user_id}")
            log.info(f"Пароль для входу: {TEST_USER_PASS}")

        # --- Створення Групи 1 ('a') ---
        group_a = (
            db.query(DeviceGroup)
            .filter(
                DeviceGroup.owner_user_id == db_user.user_id,
                DeviceGroup.local_name == "a",
            )
            .first()
        )

        if not group_a:
            log.info("Створення групи 'a' (Сад)")
            group_a = DeviceGroup(
                owner_user_id=db_user.user_id,
                local_name="a",
                display_name="Мій Головний Сад",
            )
            db.add(group_a)
            db.commit()
            db.refresh(group_a)

        # --- Створення Пристрою 1 (local_id 1) ---
        dev_1 = db.query(Device).filter(Device.mac_address == MAC_1).first()
        if not dev_1:
            log.info("Створення пристрою 1 (local_id 1) у групі 'a'")
            dev_1 = Device(
                group_id=group_a.group_id,
                mac_address=MAC_1,
                local_id=1,
                device_name="Датчик Вологості (Сад)",
                model="RG-v2-hum",
            )
            db.add(dev_1)
            db.commit()
            db.refresh(dev_1)

        # --- Створення Пристрою 2 (local_id 2) ---
        dev_2 = db.query(Device).filter(Device.mac_address == MAC_2).first()
        if not dev_2:
            log.info("Створення пристрою 2 (local_id 2) у групі 'a'")
            dev_2 = Device(
                group_id=group_a.group_id,
                mac_address=MAC_2,
                local_id=2,
                device_name="Датчик Температури (Сад)",
                model="RG-v2-temp",
            )
            db.add(dev_2)
            db.commit()
            db.refresh(dev_2)

        # --- Генерація даних лише якщо їх немає ---
        count = db.query(SensorData).count()
        if count == 0:
            log.info("Генерація 20 тестових записів SensorData...")
            sensor_data_list = []
            base_time = datetime.now(timezone.utc)

            for i in range(10):  # 10 записів для пристрою 1
                record_time = base_time - timedelta(minutes=i * 10)
                payload = {"humidity": 45.0 + (i * 1.5)}
                data_record = SensorData(
                    timestamp=record_time,
                    device_id=dev_1.device_id,
                    owner_user_id=db_user.user_id,
                    payload=payload,
                )
                sensor_data_list.append(data_record)

            for i in range(10):  # 10 записів для пристрою 2
                record_time = base_time - timedelta(minutes=i * 10)
                payload = {"temperature": 21.5 - (i * 0.1)}
                data_record = SensorData(
                    timestamp=record_time,
                    device_id=dev_2.device_id,
                    owner_user_id=db_user.user_id,
                    payload=payload,
                )
                sensor_data_list.append(data_record)

            db.add_all(sensor_data_list)
            db.commit()
            log.info("Тестові дані сенсорів додано.")
        else:
            log.info("Дані сенсорів вже існують. Пропуск генерації.")

        log.info("Заповнення БД (seeding) успішно завершено.")

    except IntegrityError as e:
        log.warning(f"Помилка цілісності (можливо, дані вже існують): {e}")
        db.rollback()
    except Exception as e:
        log.error(f"Помилка під час заповнення БД: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    log.info("Запуск скрипта заповнення БД (seeding)...")
    # Переконуємось, що таблиці існують
    create_all_tables()
    seed_data()
