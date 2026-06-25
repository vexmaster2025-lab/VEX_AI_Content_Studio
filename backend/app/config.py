from functools import lru_cache
from pathlib import Path
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: AnyUrl
    redis_url: AnyUrl
    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 60
    stripe_secret_key: str
    stripe_webhook_secret: str
    backend_url: AnyUrl

    class Config:
        env_file = Path(__file__).resolve().parents[1] / '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> Settings:
    return Settings()
