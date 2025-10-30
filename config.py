import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Клас для завантаження налаштувань з .env файлу.
    """

    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "raingripper_db"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Генерує рядок підключення SQLAlchemy
        """
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    MQTT_BROKER: str = ""
    MQTT_PORT: int = 8883
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


try:
    settings = Settings()
    log.info(f"Завантажено налаштування. Брокер: {settings.MQTT_BROKER}")
    # log.info(
    #     f"Rядок підключення до БД: {settings.DATABASE_URL}"
    # )  # (Можна увімкнути для дебагу, але не для production!)
except Exception as e:
    log.error(f"Помилка завантаження .env файлу: {e}. Переконайтесь, що .env існує.")
    settings = Settings()
