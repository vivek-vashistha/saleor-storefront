"""Logging settings for the application."""

from typing import Any


class LoggerSettings:
    """Logger settings for the application."""

    @staticmethod
    def get_config() -> dict[str, Any]:
        """Get the logger configuration.

        Returns:
            Dict[str, Any]: Logger configuration dictionary.
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s :: %(message)s",
                    "datefmt": "%m-%d-%Y %H:%M:%S",
                }
            },
            "handlers": {
                "standard": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["standard"],
                    "level": "WARNING",  # Set to WARNING to effectively disable most loggers
                    "propagate": False,
                },
                "uvicorn": {  # uvicorn logger
                    "handlers": ["standard"],
                    "level": "INFO",
                    "propagate": False,
                },
                "conversational_commerce": {  # conversational_commerce logger
                    "handlers": ["standard"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
