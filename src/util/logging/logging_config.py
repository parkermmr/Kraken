import logging

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "()": "src.util.logging.formatter.Formatter",
            "colored": False,
        },
        "colored": {
            "()": "src.util.logging.formatter.Formatter",
            "colored": True,
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "fastapi": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
    },
    "loggers": {
        "uvicorn.error": {
            "handlers": ["fastapi"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["fastapi"],
            "level": "WARNING",
            "propagate": False,
        }
    }
}


def setup_logging() -> None:
    """Applies the dictionary-based logging config."""
    logging.config.dictConfig(LOGGING_CONFIG)
