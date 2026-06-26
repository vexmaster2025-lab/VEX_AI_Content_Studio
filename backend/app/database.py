from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis

from .config import get_settings

settings = get_settings()
# Ensure we pass plain strings to libraries that expect string URLs
# Normalize DATABASE_URL to use asyncpg driver when a sync URL is provided by the environment
raw_db_url = str(settings.database_url)
# Common Render/Postgres URLs may start with 'postgres://' or 'postgresql://'
# Ensure the URL uses the 'postgresql+asyncpg://' dialect for SQLAlchemy async engine
if raw_db_url.startswith('postgres://'):
    async_db_url = raw_db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
elif raw_db_url.startswith('postgresql+asyncpg://'):
    async_db_url = raw_db_url
elif raw_db_url.startswith('postgresql://'):
    async_db_url = raw_db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
else:
    async_db_url = raw_db_url

engine = create_async_engine(async_db_url, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
redis_client = Redis.from_url(str(settings.redis_url), decode_responses=True)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    yield redis_client
