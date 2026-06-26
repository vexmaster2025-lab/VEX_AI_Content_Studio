from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database.session import get_db, get_redis
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get('/health', response_model=HealthResponse, summary='Health check')
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> HealthResponse:
    checks: dict[str, str] = {}
    http_status = status.HTTP_200_OK

    try:
        await db.execute(text('SELECT 1'))
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'unavailable'
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        await redis.ping()
        checks['redis'] = 'ok'
    except Exception:
        checks['redis'] = 'unavailable'
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    if http_status == status.HTTP_200_OK:
        return HealthResponse(status='ok', detail='Service is healthy', checks=checks)
    response.status_code = http_status
    return HealthResponse(status='degraded', detail='One or more dependencies are unavailable', checks=checks)
