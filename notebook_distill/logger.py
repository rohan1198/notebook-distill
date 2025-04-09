import json
import logging
import os
import traceback
from typing import Optional

class Logger:
    """A custom logger class that logs messages to the console.

    Attributes:
        module (str): The name of the module creating the log messages.
        log_level (int): The logging level, determines the importance of the messages that are logged.
    """
    def __init__(self, module: Optional[str] = None):
        """Initializes the Logger with a specific module name and log level.

        Args:
            module (Optional[str]): The name of the module using the logger. Defaults to None.
        """
        self.module = module
        log_level = os.environ.get("LOG_LEVEL", str(logging.INFO))

        try:
            self.log_level = int(log_level)
        except ValueError as e:
            self.log_level = logging.INFO
            self.dump_log(
                f"Exception while parsing $LOG_LEVEL. "
                f"Expected int but got {log_level} ({str(e)}). "
                "Setting app log level to INFO."
            )
        self.configure_logger()

    def configure_logger(self):
        """Configures the logger to write to a file or stdout with a specified format."""
        logging.basicConfig(
            level=self.log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def dump_log(self, message: str):
        """Writes a log message to the configured logger.

        Args:
            message (str): The message to log.
        """
        logger = logging.getLogger(self.module if self.module else __name__)
        logger.log(self.log_level, message)

    def info(self, message):
        """
        Logs info.

        Args:
            message (str): Info message to log
        """
        if self.log_level <= logging.INFO:
            self.dump_log(f"{message}")

    def debug(self, message):
        """
        Writes a info message.

        Args:
            message (str): Debug message to log
        """
        if self.log_level <= logging.DEBUG:
            self.dump_log(f"🕷️ {message}")

    def warning(self, message):
        """
        Writes a warning message.

        Args:
            message (str): Warning message to log
        """
        if self.log_level <= logging.WARNING:
            self.dump_log(f"⚠️ {message}")

    def error(self, message):
        """
        Writes a error message.

        Args:
            message (str): Error message to log
        """
        if self.log_level <= logging.ERROR:
            self.dump_log(f"🔴 {message}")
            traceback.print_exc()

    def critical(self, message):
        """
        Writes a critical message.

        Args:
            message (str): Critical message to log
        """
        if self.log_level <= logging.CRITICAL:
            self.dump_log(f"💥 {message}")
            traceback.print_exc()
