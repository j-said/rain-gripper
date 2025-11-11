# RainGripper IoT Backend (v0.2.0)

Це бекенд-сервіс для проекту RainGripper, побудований на асинхронній архітектурі, яка розділяє прийом даних (MQTT) та обслуговування API (FastAPI) з автентифікацією.

## Архітектура (Оновлено)

- **Прийом даних**: `mqtt_listener.py` слухає MQTT-топіки (#), використовує кеш в пам'яті (LOOKUP_CACHE) для миттєвого мапінгу (user_id, group_name, local_id) у device_pk і записує дані в PostgreSQL.

- **API**: `main.py` запускає FastAPI REST API. Усі ендпоінти (окрім `/token` та `/users/`) захищені за допомогою JWT-токенів.

- **Інвалідaція кешу**: API (`main.py`) публікує повідомлення в `system/cache/invalidate/{user_id}`, коли дані (групи, пристрої) змінюються, змушуючи `mqtt_listener` оновити свій кеш.

## Сервіси

### MQTT Listener (`mqtt_listener.py`)

- Підписується на `#`.
- Обробляє `system/cache/invalidate` для оновлення `LOOKUP_CACHE`.
- Обробляє `{user_id}/{local_group}/data` для запису даних.
- Використовує `LOOKUP_CACHE` для уникнення запитів до БД при прийомі повідомлень.

### FastAPI Server (`main.py`)

- Захищені ендпоінти (JWT).
- Ендпоінт `/token` для отримання токенів.
- Публікує команди в `{user_id}/{local_group}/command`.

## Структура проекту

```
/
├── main.py             # FastAPI (захищені ендпоінти, JWT)
├── mqtt_listener.py    # MQTT Listener (прийом даних + кешування)
├── mqtt_publisher.py   # Логіка публікації команд
├── crud.py             # Логіка запитів до БД (з хешуванням паролів)
├── database.py         # Моделі SQLAlchemy (BigInteger ID, MAC)
├── schemas.py          # Моделі Pydantic (з local_id, mac_address)
├── config.py           # Завантаження .env (включно з SECRET_KEY)
├── requirements.txt    # Залежності (включно з passlib, python-jose)
├── seed-db.py          # Оновлений скрипт заповнення БД
└── .env.example        # Приклад налаштувань (з SECRET_KEY)
```

## Встановлення

(Кроки 1-3 залишаються ті ж самі...)

1. Створіть `.env` (додайте `SECRET_KEY`):
  ```bash
  # Згенеруйте ключ
  openssl rand -hex 32
  ```

2. Скопіюйте ключ у ваш `.env` файл:
  ```
  DB_USER=...
  DB_PASSWORD=...
  ...
  MQTT_BROKER=...
  SECRET_KEY=e8b28f... (ваш ключ)
  ```

3. Створіть таблиці:
  ```bash
  python database.py
  ```

4. (Опційно) Заповніть БД тестовими даними:
  ```bash
  python seed-db.py
  ```
  Це створить юзера: `test@example.com`
  Пароль: `password123`

5. Запустіть сервіси:
  ```bash
  # Термінал 1 - MQTT Listener
  python mqtt_listener.py

  # Термінал 2 - FastAPI Server
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```

## API (Оновлено)

Документація (Swagger) доступна тут: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Автентифікація

- **POST /token** - (Public) Отримати JWT токен. Надішліть `username` (це ваш email) та `password` у `application/x-www-form-urlencoded`.

### Користувачі

- **POST /api/v1/users/** - (Public) Створити нового користувача.
- **GET /api/v1/users/me** - (Protected) Отримати дані поточного користувача.

### Групи пристроїв

- **POST /api/v1/groups/** - (Protected) Створити нову групу.
- **GET /api/v1/groups/** - (Protected) Отримати список груп.

### Пристрої

- **POST /api/v1/groups/{group_id}/devices/** - (Protected) Створити пристрій у групі.
- **GET /api/v1/groups/{group_id}/devices/** - (Protected) Отримати список пристроїв у групі.

### Дані та Команди

- **GET /api/v1/data/** - (Protected) Отримати дані сенсорів.
- **POST /api/v1/command/{device_group_local_name}** - (Protected) Надіслати команду.
