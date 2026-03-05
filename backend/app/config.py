from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str
    FERNET_KEY: str

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    HEALTH_CHECK_INTERVAL_SECONDS: int = 300
    UPSTREAM_TIMEOUT_SECONDS: int = 30
    CONNECTION_IDLE_TIMEOUT_SECONDS: int = 600

    LOG_LEVEL: str = "INFO"


settings = Settings()  # type: ignore[call-arg]
