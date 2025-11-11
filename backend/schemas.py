import uuid
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional  # Додано

# --- Схеми Автентифікації ---


class UserLogin(BaseModel):
    """Схема для входу (email + пароль)."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Схема для повернення JWT токена."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Внутрішня схема для даних токена."""

    user_id: str | None = None


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
    group_id: int  # ЗМІНЕНО
    owner_user_id: uuid.UUID
    local_name: str  # ДОДАНО
    display_name: str  # ЗМІНЕНО
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Device(BaseModel):
    device_id: int  # ЗМІНЕНО
    group_id: int  # ЗМІНЕНО
    local_id: int  # ДОДАНО
    mac_address: str  # ДОДАНО
    device_name: str
    model: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Create Models ---
class UserCreate(BaseModel):
    username: str
    name: str
    email: EmailStr
    password: str


class DeviceGroupCreate(BaseModel):
    local_name: str = Field(..., description="Ідентифікатор для MQTT ('a', 'b', 'c')")
    display_name: str = Field(..., min_length=3, description="Назва для UI ('Мій сад')")


class DeviceCreate(BaseModel):
    local_id: int = Field(..., gt=0, le=255, description="ID пристрою в групі (1-255)")
    mac_address: str = Field(..., description="Фізична MAC-адреса")
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
    device_id: int  # ЗМІНЕНО
    timestamp: datetime
    payload: dict | None

    model_config = ConfigDict(from_attributes=True)
