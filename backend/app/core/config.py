from pathlib import Path
from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    app_name: str = 'VEX Backend'
    app_version: str = '1.0.0'
    database_url: str
    redis_url: str
    cors_allowed_origins: Any = ['*']
    log_level: str = 'INFO'
    env: str = 'development'
    backend_url: str = 'http://localhost:8000'
    jwt_secret: str = Field(default='dev_only_change_this_secret_32_chars_minimum')
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 60
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @field_validator('cors_allowed_origins', mode='before')
    @classmethod
    def _normalize_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        if isinstance(value, list):
            return value
        return ['*']


def get_settings() -> Settings:
    return Settings()
