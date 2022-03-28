import logging.config
from sys import stdout

# Configuring logging
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "breif": {
                "format": "[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "precise": {
                "format": "[%(asctime)s] %(levelname)-8s %(name)-22s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S %z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "breif",
                "stream": stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "precise",
                "filename": "log.log",
                "mode": "a",
                "encoding": "utf-8",
                "maxBytes": 1024,
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "Propagate": True, "level": "DEBUG"},
        },
    }
)
