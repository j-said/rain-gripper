RainGripper IoT Backend

Це backend-сервіс для проєкту RainGripper, який виконує дві основні задачі:

Прийом даних (Ingestion): Слухає MQTT топіки, парсить дані з пристроїв та зберігає їх у базу даних PostgreSQL.

Надання API (API Serving): Надає REST API для веб-порталу, щоб отримувати зрізи даних та надсилати команди пристроям.

Архітектура

Проєкт складається з двох головних сервісів, які працюють одночасно:

MQTT Listener (mqtt_listener.py):

Підключається до MQTT брокера (налаштування у config.py).

Підписується на топік clients/#.

При отриманні повідомлення, парсить топік (clients/{cust_id}/{dev_id}/{type}) та payload (JSON).

Записує дані у таблицю sensor_data в PostgreSQL.

FastAPI Server (main.py):

Запускає веб-сервер (Uvicorn).

Надає API ендпоінти для взаємодії з даними.

Підключається до PostgreSQL для виконання запитів (crud.py).

Використовує Pydantic (schemas.py) для валідації даних.

Структура Проєкту

/
├── main.py             # FastAPI сервер (API ендпоінти)
├── mqtt_listener.py    # MQTT сервіс (збереження даних у БД)
├── crud.py             # Логіка запитів до БД (SELECT, NSERT...)
├── database.py         # Моделі SQLAlchemy та підключення до БД
├── schemas.py          # Моделі Pydantic (для валідації API)
├── config.py           # Завантаження налаштувань з .env
├── requirements.txt    # Залежності Python
└── .env.example        # Приклад файлу налаштувань


Налаштування та Запуск

1. Вимоги

Python 3.10+

PostgreSQL сервер

Ubuntu (для apt команд)

2. Встановлення (Ubuntu)

# 1. Встановіть клієнт PostgreSQL та бібліотеки
sudo apt update
sudo apt install postgresql-client libpq-dev

# 2. Створіть віртуальне оточення
python3 -m venv venv
source venv/bin/activate

# 3. Встановіть залежності
pip install -r requirements.txt


3. Налаштування Бази Даних

# 1. Увійдіть у psql як суперкористувач
sudo -u postgres psql

# 2. Створіть користувача та БД (замініть на ваші дані)
CREATE USER my_user WITH PASSWORD 'my_password';
CREATE DATABASE raingripper_db;
GRANT ALL PRIVILEGES ON DATABASE raingripper_db TO my_user;

# 3. Надайте права на схему (ВАЖЛИВО)
\c raingripper_db
GRANT USAGE ON SCHEMA public TO my_user;
GRANT CREATE ON SCHEMA public TO my_user;
\q


4. Налаштування Проєкту

# 1. Створіть .env файл
cp .env.example .env

# 2. Відредагуйте .env (введіть ваші дані)
nano .env


Приклад .env:

DB_USER=my_user
DB_PASSWORD=my_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=raingripper_db

MQTT_BROKER=your.broker-address.com
MQTT_PORT=8883
MQTT_USERNAME=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password


5. Створення Таблиць

Виконайте database.py один раз, щоб створити таблицю sensor_data у вашій БД.

python database.py
# Очікуваний результат: ... Таблиці успішно створено ...


6. Запуск Сервісів

Вам потрібно запустити два процеси у двох окремих терміналах (або через supervisor).

Термінал 1: MQTT Listener

python mqtt_listener.py


Термінал 2: FastAPI Server

uvicorn main:app --host 0.0.0.0 --port 8000 --reload


API Ендпоінти

Після запуску main.py, API документація буде доступна за адресою:
http://127.0.0.1:8000/docs

GET /api/v1/data/{customer_id}

Отримує зріз даних для клієнта.

Query Параметри:

start_date (datetime, опціонально): Початок періоду.

end_date (datetime, опціонально): Кінець періоду.
(Якщо не вказано, береться остання 1 доба)

Успішна Відповідь (200):

[
  {
    "id": 1,
    "created_at": "2025-10-30T10:00:00Z",
    "customer_id": "cust_123",
    "sub_device_id": "gateway_A",
    "data_type": "logs",
    "payload": { "temp": 21.5, "humidity": 45.1 }
  }
]


POST /api/v1/command/{customer_id}/{sub_device_id}

Надсилає команду на пристрій через MQTT.

URL Параметри:

customer_id (str): ID клієнта.

sub_device_id (str): ID пристрою (або 'all').

Тіло Запиту (JSON):

{
  "action": "send_data",
  "parameters": {
    "force": true
  }
}


(Відповідно до schemas.py:CommandRequest)

Успішна Відповідь (202 - Accepted):

{
  "status": "accepted",
  "message": "Команду 'send_data' надіслано у топік."
}


(Цей ендпоінт публікує повідомлення у топік: clients/{customer_id}/{sub_device_id}/command)