import logging
from pythonjsonlogger import jsonlogger
from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    log_level = settings.log_level.upper()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'levelname': 'level',
            'message': 'message',
        },
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)

    for logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
        logger = logging.getLogger(logger_name)
        logger.handlers = [handler]
        logger.setLevel(log_level)
