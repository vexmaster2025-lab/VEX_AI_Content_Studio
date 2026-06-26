from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

raw_database_url = settings.database_url
if raw_database_url.startswith('postgres://'):
    raw_database_url = raw_database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
elif raw_database_url.startswith('postgresql://'):
    raw_database_url = raw_database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

engine = create_async_engine(raw_database_url, future=True, echo=False)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
redis_client = Redis.from_url(str(settings.redis_url), decode_responses=True)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    yield redis_client
