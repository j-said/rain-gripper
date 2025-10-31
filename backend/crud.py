import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Імпортуємо наші моделі SQLAlchemy
from database import SensorData

log = logging.getLogger(__name__)


def get_sensor_data(
    db: Session, customer_id: str, start_date: datetime, end_date: datetime
):
    """
    Отримує зріз даних з БД для конкретного клієнта
    та часового діапазону.
    """
    log.info(f"Запит даних для {customer_id} з {start_date} по {end_date}")

    try:
        query = (
            db.query(SensorData)
            .filter(
                SensorData.customer_id == customer_id,
                SensorData.created_at >= start_date,
                SensorData.created_at <= end_date,
            )
            .order_by(SensorData.created_at.asc())
        )

        return query.all()

    except Exception as e:
        log.error(f"Помилка запиту до БД: {e}")
        return []
