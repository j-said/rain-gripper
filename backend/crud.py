import logging
from datetime import datetime
from sqlalchemy.orm import Session

# SQLAlchemy
from database import SensorData, User, Device, DeviceGroup

log = logging.getLogger(__name__)


# Denormalized
def get_sensor_data(
    db: Session, user_id: str, start_date: datetime, end_date: datetime
):
    """
    Отримує дані, використовуючи швидку денормалізовану схему.
    """
    log.info(f"Запит даних для {user_id} з {start_date} по {end_date}")

    try:
        query = (
            db.query(SensorData)
            .filter(
                SensorData.owner_user_id == user_id,
                SensorData.timestamp >= start_date,
                SensorData.timestamp <= end_date,
            )
            .order_by(SensorData.timestamp.asc())
        )
        # TODO: check if DB uses proper indexes for this query
        # log.info(query)
        return query.all()

    except Exception as e:
        log.error(f"Помилка запиту до БД: {e}")
        return []
