import logging
import logging.config
from functools import wraps
from typing import Any, Optional

from src.util.logging.formatter import Formatter


class Logger(logging.Logger):
    """
    A logger subclass that provides methods
    for user-initiated and data-initiated logs.
    """

    def __init__(
        self,
        name: str,
        level: int = logging.NOTSET,
        logfile: Optional[str] = None,
        colored: bool = False,
    ):
        super().__init__(name, level)
        self.handlers.clear()
        formatter = Formatter(colored=colored)
        handler = logging.FileHandler(logfile) if logfile else logging.StreamHandler()
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def log_user(
        self,
        level: int,
        transaction_id: str,
        service: str,
        caller: str,
        user_id: str,
        request_uri: str,
        message: str,
        data_id: Optional[str] = None,
        api_response_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        extra = {
            "log_type": "user",
            "transaction_id": transaction_id,
            "service": service,
            "caller": caller,
            "user_id": user_id,
            "request_uri": request_uri,
            "data_id": data_id,
            "api_response_code": api_response_code,
        }
        self.log(level, message, extra=extra, **kwargs)

    def log_data(
        self,
        level: int,
        data_id: str,
        service: str,
        caller: str,
        request_uri: str,
        message: str,
        api_response_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        extra = {
            "log_type": "data",
            "data_id": data_id,
            "service": service,
            "caller": caller,
            "request_uri": request_uri,
            "api_response_code": api_response_code,
        }
        self.log(level, message, extra=extra, **kwargs)


def log_exceptions(logger: Logger):
    """Decorator to log exceptions from the decorated function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                caller = f"{func.__module__}.{func.__qualname__}"
                logger.error(f"Exception in {caller}: {e}", extra={"caller": caller})
                raise

        return wrapper

    return decorator
