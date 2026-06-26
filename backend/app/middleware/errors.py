import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning('AppException: %s', exc.detail)
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning('HTTPException: %s', exc.detail)
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning('Validation error: %s', exc.errors())
        return JSONResponse(status_code=422, content={'detail': exc.errors()})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception('Unexpected exception occurred')
        return JSONResponse(status_code=500, content={'detail': 'Internal server error'})
