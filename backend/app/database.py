from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis

from .config import get_settings

settings = get_settings()
# Ensure we pass plain strings to libraries that expect string URLs
engine = create_async_engine(str(settings.database_url), echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
redis_client = Redis.from_url(str(settings.redis_url), decode_responses=True)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    yield redis_client
