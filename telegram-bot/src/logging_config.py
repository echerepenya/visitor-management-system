import logging.config


def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True
            },
            "aiogram": {"level": "WARNING"},
            "httpx": {"level": "WARNING"},
            "uvicorn": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO"},
        }
    }

    logging.config.dictConfig(logging_config)
