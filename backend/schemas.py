# pydantic_core._pydantic_core.PydanticOmit: Модель для .from_attributes
from pydantic import ConfigDict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class CommandRequest(BaseModel):
    """
    Схема Pydantic для тіла POST-запиту команди.
    """

    # Очікуємо "send_data" або "update_firmware"
    action: str = Field(..., description="Тип команди (напр., 'send_data')")

    # Використовуємо dict для гнучкості (напр., {"url": "..."})
    parameters: dict | None = Field(
        default=None, description="Додаткові параметри команди"
    )


class SensorDataResponse(BaseModel):
    """
    Схема Pydantic для повернення даних з API.
    (ОНОВЛЕНО, щоб відповідати моделі SensorData)
    """

    id: int
    owner_user_id: uuid.UUID
    device_id: uuid.UUID
    timestamp: datetime
    payload: dict | None

    model_config = ConfigDict(from_attributes=True)
