# RainGripper IoT Backend

Це backend-сервіс для проєкту RainGripper. Побудований на асинхронній архітектурі, що розділяє прийом даних (MQTT) та обслуговування API (FastAPI).

## Архітектура — коротко

- Прийом даних (Data ingestion): `mqtt_connect.py` слухає MQTT-топіки, парсить JSON-пейлоди від пристроїв і записує дані в PostgreSQL.
- Надання API: `main.py` запускає FastAPI REST API для веб-порталу (отримання даних, керування користувачами/пристроями) і надсилання команд пристроям через MQTT.

## Сервіси

1. MQTT Listener (`mqtt_connect.py`)
  - Окремий процес Python.
  - Підключається до MQTT-брокера з постійним з'єднанням.
  - Підписується на топіки даних (наприклад `+/+/data`).
  - Парсить JSON повідомлення й записує дані в таблицю SensorData через `database.py` і `get_db_session`.
  - Використовує масові вставки (`add_all` / `commit`) для продуктивності.

2. FastAPI Server (`main.py`)
  - Запускає вебсервер (Uvicorn).
  - REST ендпоінти для CRUD: Users, DeviceGroups, Devices, та отримання даних сенсорів.
  - Валідaція через Pydantic (`schemas.py`).
  - Стійкий MQTT-клієнт для публікації команд (`mqtt_publisher.py`) керується через lifespan FastAPI.
  - API-ендпоінти використовують `mqtt_publisher.publish()` для миттєвого надсилання команд.

## Структура проєкту

```
/
├── main.py             # FastAPI сервер (ендпоінти, lifespan)
├── mqtt_connect.py     # MQTT Listener (сервіс прийому даних)
├── mqtt_client.py      # MQTT Client (для FastAPI паблішера)
├── mqtt_publisher.py   # Логіка публікації команд
├── crud.py             # Логіка запитів до БД (SELECT, INSERT...)
├── database.py         # Моделі SQLAlchemy та підключення до БД
├── schemas.py          # Моделі Pydantic (валідація API)
├── config.py           # Завантаження налаштувань з .env
├── requirements.txt    # Залежності Python
├── seed_db.py          # (Опціонально) Скрипт для заповнення БД
└── .env.example        # Приклад файлу налаштувань
```

## Вимоги

- Python 3.10+
- PostgreSQL сервер
- Ubuntu (для прикладів apt)

## Встановлення (Ubuntu)

```bash
# Оновити і встановити клієнт PostgreSQL
sudo apt update
sudo apt install postgresql-client libpq-dev

# Створити віртуальне оточення
python3 -m venv venv
source venv/bin/activate

# Встановити залежності
pip install -r requirements.txt


3) Налаштування бази даних

(Використовуйте psql або інший клієнт)

CREATE USER my_user WITH PASSWORD 'my_password';
CREATE DATABASE raingripper_db;
GRANT ALL PRIVILEGES ON DATABASE raingripper_db TO my_user;
\c raingripper_db
GRANT USAGE ON SCHEMA public TO my_user;
GRANT CREATE ON SCHEMA public TO my_user;
\q


4) Налаштування проєкту

# Створіть .env з прикладу
cp .env.example .env

# Відредагуйте .env
nano .env


(DB_USER, DB_PASSWORD, MQTT_BROKER тощо)

5) Створення таблиць

Запустіть database.py один раз, щоб створити таблиці.

python database.py
# Очікуваний результат: Таблиці успішно створено...


6) (Опціонально) Заповнення БД

Запустіть seed_db.py для додавання тестових даних.

python seed_db.py


7) Запуск сервісів

Запустіть два процеси в окремих терміналах.

Термінал 1 — MQTT Listener:

python mqtt_connect.py


Термінал 2 — FastAPI Server:

uvicorn main:app --host 0.0.0.0 --port 8000 --reload


API Документація

Після запуску FastAPI, інтерактивна документація (Swagger) доступна:
http://127.0.0.1:8000/docs

Керування користувачами

POST /api/v1/users/ - Створити нового користувача.

GET /api/v1/users/ - Отримати список користувачів.

GET /api/v1/users/{user_id} - Отримати конкретного користувача.

Керування групами (DeviceGroups)

POST /api/v1/users/{user_id}/groups/ - Створити групу для користувача.

GET /api/v1/users/{user_id}/groups/ - Отримати групи користувача.

Керування пристроями (Devices)

POST /api/v1/groups/{group_id}/devices/ - Створити пристрій у групі.

GET /api/v1/groups/{group_id}/devices/ - Отримати пристрої групи.

GET /api/v1/users/{user_id}/devices/ - Отримати всі пристрої користувача одним запитом.

Отримання даних сенсорів (Sensor Logs)

GET /api/v1/data/{user_id}

Отримує зріз даних (логів) для конкретного користувача.

Query-параметри:

start_date (datetime, опціонально) — початок періоду (UTC).

end_date (datetime, опціонально) — кінець періоду (UTC).
(Якщо не вказано — береться останні 24 години.)

Успішна відповідь (200 OK):

[
  {
    "id": 1,
    "owner_user_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "device_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33",
    "timestamp": "2025-11-04T12:00:00Z",
    "payload": {
      "humidity": 45.1,
      "water_level": 88.0
    }
  }
]

Надсилання команд

POST /api/v1/command/{user_id}/{device_group}

Надсилає команду на групу пристроїв через MQTT.

Тіло запиту (JSON):

{
  "action": "send_data",
  "parameters": { "force": true }
}


Успішна відповідь (202 Accepted):

{
  "status": "accepted",
  "message": "Команду 'send_data' надіслано у топік."
}


Цей ендпоінт публікує повідомлення у топік: {user_id}/{device_group}/command