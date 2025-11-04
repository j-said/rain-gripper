import uuid
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from datetime import datetime


# --- Base Models ---
# Використовуються для повернення даних з API (включаючи ID)
class User(BaseModel):
    user_id: uuid.UUID
    username: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceGroup(BaseModel):
    group_id: uuid.UUID
    owner_user_id: uuid.UUID
    group_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Device(BaseModel):
    device_id: uuid.UUID
    group_id: uuid.UUID
    device_name: str
    model: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Create Models ---
class UserCreate(BaseModel):
    username: str
    name: str
    email: EmailStr
    password: str  # Очікуємо пароль, щоб хешувати його в crud


class DeviceGroupCreate(BaseModel):
    group_name: str = Field(..., min_length=3)


class DeviceCreate(BaseModel):
    device_name: str = Field(..., min_length=3)
    model: str | None = None


# --- API Payloads & Responses ---
class CommandRequest(BaseModel):
    """
    Схема Pydantic для тіла POST-запиту команди.
    """

    action: str = Field(..., description="Тип команди (напр., 'send_data')")
    parameters: dict | None = Field(
        default=None, description="Додаткові параметри команди"
    )


class SensorDataResponse(BaseModel):
    """
    Схема Pydantic для повернення даних з API.
    """

    id: int
    owner_user_id: uuid.UUID
    device_id: uuid.UUID
    timestamp: datetime
    payload: dict | None

    model_config = ConfigDict(from_attributes=True)
