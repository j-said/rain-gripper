from pydantic import BaseModel, Field
from datetime import datetime

# pydantic_core._pydantic_core.PydanticOmit: Модель для .from_attributes
from pydantic import ConfigDict


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
    """

    id: int
    created_at: datetime
    customer_id: str
    sub_device_id: str
    data_type: str

    # Очікуємо, що payload буде JSON (dict у Python)
    payload: dict | None

    # Дозволяє Pydantic читати дані
    # з атрибутів об'єкта SQLAlchemy (model.id)
    model_config = ConfigDict(from_attributes=True)
