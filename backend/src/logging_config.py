import logging.config
import os


def setup_logging():
    if getattr(setup_logging, "_has_run", False):
        return
    setup_logging._has_run = True
    os.makedirs("logs", exist_ok=True)

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
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": "logs/app.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "INFO",
            },
            "src": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "aiogram": {"level": "INFO"},
            "apscheduler.executors.default": {"level": "WARNING"},
            "uvicorn": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO"},
        }
    }

    logging.config.dictConfig(logging_config)
