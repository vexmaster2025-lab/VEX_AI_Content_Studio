from fastapi import APIRouter
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.billing import router as billing_router
from app.api.v1.routers.billing import webhook_router as stripe_webhook_router
from app.api.v1.routers.content import router as content_router
from app.api.v1.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(billing_router)
api_router.include_router(stripe_webhook_router)
api_router.include_router(content_router)
api_router.include_router(health_router, tags=['Health'])
