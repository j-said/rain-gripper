# RainGripper IoT Backend

Це backend-сервіс для проєкту RainGripper. Виконує дві основні задачі:

- Прийом даних (Ingestion): слухає MQTT-топіки, парсить payload від пристроїв і зберігає в PostgreSQL.
- Надання API (API Serving): REST API для веб-порталу — отримання даних і надсилання команд пристроям.

## Архітектура

Проєкт складається з двох сервісів, що працюють одночасно:

### MQTT Listener (mqtt_listener.py)
- Підключається до MQTT-брокера (налаштування у `config.py`).
- Підписується на топіки `clients/#`.
- При отриманні повідомлення парсить топік `clients/{cust_id}/{dev_id}/{type}` і JSON payload.
- Записує записи у таблицю `sensor_data` в PostgreSQL.

### FastAPI Server (main.py)
- Запускає веб-сервер (Uvicorn).
- Надає REST ендпоінти для взаємодії з даними.
- Виконує запити до БД через `crud.py`.
- Використовує Pydantic (`schemas.py`) для валідації вхідних даних.

## Структура проєкту
```
/
├── main.py             # FastAPI сервер (API ендпоінти)
├── mqtt_listener.py    # MQTT сервіс (збереження даних у БД)
├── crud.py             # Логіка запитів до БД (SELECT, INSERT...)
├── database.py         # Моделі SQLAlchemy та підключення до БД
├── schemas.py          # Моделі Pydantic (валидація API)
├── config.py           # Завантаження налаштувань з .env
├── requirements.txt    # Залежності Python
└── .env.example        # Приклад файлу налаштувань
```

## Налаштування та запуск

### 1) Вимоги
- Python 3.10+
- PostgreSQL сервер
- Ubuntu (для apt-команд, за потреби)

### 2) Встановлення (Ubuntu)
```bash
# Оновити і встановити клієнт PostgreSQL
sudo apt update
sudo apt install postgresql-client libpq-dev

# Створити віртуальне оточення
python3 -m venv venv
source venv/bin/activate

# Встановити залежності
pip install -r requirements.txt
```

### 3) Налаштування бази даних
```sql
-- Увійдіть у psql як postgres
sudo -u postgres psql

-- Створіть користувача та БД (замініть на свої дані)
CREATE USER my_user WITH PASSWORD 'my_password';
CREATE DATABASE raingripper_db;
GRANT ALL PRIVILEGES ON DATABASE raingripper_db TO my_user;

-- Надайте права на схему
\c raingripper_db
GRANT USAGE ON SCHEMA public TO my_user;
GRANT CREATE ON SCHEMA public TO my_user;
\q
```

### 4) Налаштування проєкту
```bash
# Створіть .env з прикладу
cp .env.example .env

# Відредагуйте .env
nano .env
```

Приклад `.env`:
```
DB_USER=my_user
DB_PASSWORD=my_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=raingripper_db

MQTT_BROKER=your.broker-address.com
MQTT_PORT=8883
MQTT_USERNAME=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password
```

### 5) Створення таблиць
Запустіть `database.py` один раз, щоб створити таблицю `sensor_data`:
```bash
python database.py
# Очікуваний результат: таблиці успішно створено
```

### 6) Запуск сервісів
Запустіть два процеси в окремих терміналах або використайте supervisor/systemd:

Термінал 1 — MQTT Listener:
```bash
python mqtt_listener.py
```

Термінал 2 — FastAPI Server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API документація
Після запуску FastAPI документація доступна:
http://127.0.0.1:8000/docs

### GET /api/v1/data/{customer_id}
Отримує зріз даних для клієнта.

Query-параметри:
- `start_date` (datetime, опціонально) — початок періоду.
- `end_date` (datetime, опціонально) — кінець періоду.
(Якщо не вказано — береться останні 24 години.)

Успішна відповідь (200):
```json
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
```

### POST /api/v1/command/{customer_id}/{sub_device_id}
Надсилає команду на пристрій через MQTT.

URL-параметри:
- `customer_id` (string) — ID клієнта.
- `sub_device_id` (string) — ID пристрою або `all`.

Тіло запиту (JSON) — приклад:
```json
{
  "action": "send_data",
  "parameters": { "force": true }
}
```

Успішна відповідь (202 Accepted):
```json
{
  "status": "accepted",
  "message": "Команду 'send_data' надіслано у топік."
}
```

Цей ендпоінт публікує повідомлення у топік:
`clients/{customer_id}/{sub_device_id}/command`

-- Короткі поради
- Переконайтесь, що `MQTT_PORT`, сертифікати та доступи коректні для TLS (якщо використовується).
- Логи MQTT listener і FastAPI допоможуть діагностувати проблеми з підключенням або серіалізацією повідомлень.
- Використовуйте supervisor або systemd для автозапуску обох сервісів у продакшені.
