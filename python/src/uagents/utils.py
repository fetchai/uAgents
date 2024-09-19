import logging
import sys
from typing import Optional, Union

from uvicorn.logging import DefaultFormatter

logging.basicConfig(level=logging.INFO)
formatter = DefaultFormatter(fmt="%(levelprefix)s [%(name)5s]: %(message)s")
file_formatter = DefaultFormatter(fmt="%(asctime)s [%(name)5s]: %(message)s")


def get_logger(logger_name: str, level: Union[int, str] = logging.INFO):
    """Get a logger with the given name using uvicorn's default formatter."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(formatter)
    file_handler = logging.FileHandler("agent.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def log(logger: Optional[logging.Logger], level: int, message: str):
    """
    Log a message with the given logger and level.

    Args:
        logger (Optional[logging.Logger]): The logger to use.
        level (int): The logging level.
        message (str): The message to log.
    """
    if logger:
        logger.log(level, message)
    else:
        BACKUP_LOGGER.log(level, message)


BACKUP_LOGGER = get_logger("uagents", logging.INFO)
