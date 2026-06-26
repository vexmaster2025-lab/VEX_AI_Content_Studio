from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database import redis_client
from app.middleware.errors import register_exception_handlers

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url='/docs',
    redoc_url='/redoc',
)

configure_logging(settings)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix='/api/v1')


@app.on_event('startup')
async def on_startup() -> None:
    # Startup hooks can be extended for database readiness checks or telemetry initialization.
    pass


@app.on_event('shutdown')
async def on_shutdown() -> None:
    try:
        await redis_client.close()
        await redis_client.wait_closed()
    except Exception:
        pass
