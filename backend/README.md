# RainGripper IoT Backend

This is a backend service for the RainGripper project. Built on an asynchronous architecture that separates data ingestion (MQTT) from API serving (FastAPI).

## Architecture Overview

- Data ingestion: `mqtt_connect.py` listens to MQTT topics, parses JSON payloads from devices and writes data to PostgreSQL.
- API serving: `main.py` runs FastAPI REST API for the web portal (data retrieval, user/device management) and sends commands to devices via MQTT.

## Services

1. MQTT Listener (`mqtt_connect.py`)
  - Separate Python process
  - Connects to MQTT broker with persistent connection
  - Subscribes to data topics (e.g., `+/+/data`)
  - Parses JSON messages and writes data to SensorData table via `database.py` and `get_db_session`
  - Uses bulk inserts (`add_all` / `commit`) for performance

2. FastAPI Server (`main.py`)
  - Runs webserver (Uvicorn)
  - REST endpoints for CRUD: Users, DeviceGroups, Devices, and sensor data retrieval
  - Validation through Pydantic (`schemas.py`)
  - Resilient MQTT client for command publishing (`mqtt_publisher.py`) managed via FastAPI lifespan
  - API endpoints use `mqtt_publisher.publish()` for immediate command sending

## Project Structure

```
/
├── main.py             # FastAPI server (endpoints, lifespan)
├── mqtt_connect.py     # MQTT Listener (data ingestion service)
├── mqtt_client.py      # MQTT Client (for FastAPI publisher)
├── mqtt_publisher.py   # Command publishing logic
├── crud.py            # Database query logic (SELECT, INSERT...)
├── database.py        # SQLAlchemy models and DB connection
├── schemas.py         # Pydantic models (API validation)
├── config.py          # Load settings from .env
├── requirements.txt   # Python dependencies
├── seed_db.py         # (Optional) Database seeding script
└── .env.example       # Example settings file
```

## Requirements

- Python 3.10+
- PostgreSQL server
- Ubuntu (for apt examples)

## Installation (Ubuntu)

1. Install dependencies:
```bash
# Update and install PostgreSQL client
sudo apt update
sudo apt install postgresql-client libpq-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

2. Configure database:
```sql
CREATE USER my_user WITH PASSWORD 'my_password';
CREATE DATABASE raingripper_db;
GRANT ALL PRIVILEGES ON DATABASE raingripper_db TO my_user;
\c raingripper_db
GRANT USAGE ON SCHEMA public TO my_user;
GRANT CREATE ON SCHEMA public TO my_user;
```

3. Setup project:
```bash
# Create .env from example
cp .env.example .env

# Edit .env
nano .env
```

4. Create tables:
```bash
python database.py
```

5. (Optional) Seed database:
```bash
python seed_db.py
```

6. Run services:
```bash
# Terminal 1 - MQTT Listener
python mqtt_connect.py

# Terminal 2 - FastAPI Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Interactive API documentation (Swagger) available at:
http://127.0.0.1:8000/docs

### User Management
- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{user_id}` - Get specific user

### Device Group Management
- `POST /api/v1/users/{user_id}/groups/` - Create group for user
- `GET /api/v1/users/{user_id}/groups/` - Get user's groups

### Device Management
- `POST /api/v1/groups/{group_id}/devices/` - Create device in group
- `GET /api/v1/groups/{group_id}/devices/` - Get group's devices
- `GET /api/v1/users/{user_id}/devices/` - Get all user's devices

### Sensor Data Retrieval
- `GET /api/v1/data/{user_id}` - Get sensor logs with optional date range filters

### Command Sending
- `POST /api/v1/command/{user_id}/{device_group}` - Send command to device group via MQTT
