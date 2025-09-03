import logging
import sys
import structlog
from app.config import settings


def setup_logging():
    """
    Set up structured logging using structlog.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        stream=sys.stdout,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    Get a logger with the specified name.
    """
    return structlog.get_logger(name)
