import logging
import time


class Formatter(logging.Formatter):
    """
    A formatter that adjusts its format based on
    the log type and optionally adds ANSI colours.
    """

    def __init__(self, colored: bool = False):
        self.colored = colored
        self.user_fmt = (
            "%(asctime)s - %(levelname)s - [TX: %(transaction_id)s]"
            " - [Service: %(service)s] - [Caller: %(caller)s] - "
            "[User: %(user_id)s] - [URI: %(request_uri)s] - %(message)s"
        )
        self.data_fmt = (
            "%(asctime)s - %(levelname)s - [Data: %(data_id)s] - "
            "[Service: %(service)s] - [Caller: %(caller)s] - "
            "[URI: %(request_uri)s] - %(message)s"
        )
        self.default_fmt = "%(asctime)s - %(levelname)s - %(message)s"
        super().__init__(fmt=self.default_fmt, datefmt="%Y-%m-%dT%H:%M:%SZ", style="%")
        logging.Formatter.converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "log_type"):
            fmt = self.user_fmt if record.log_type == "user" else self.data_fmt
        else:
            fmt = self.default_fmt
        if getattr(record, "api_response_code", None) is not None:
            fmt += " - [Response: %(api_response_code)s]"
        self._style._fmt = fmt
        if self.colored:
            color = ""
            if record.levelname == "DEBUG":
                color = "\033[34m"
            elif record.levelname == "INFO":
                color = "\033[32m"
            elif record.levelname == "WARNING":
                color = "\033[33m"
            elif record.levelname == "ERROR":
                color = "\033[31m"
            elif record.levelname == "CRITICAL":
                color = "\033[1;31m"
            if color:
                record.levelname = f"{color}{record.levelname}\033[0m"
        return super().format(record)
