import logging
import sys

from uvicorn.logging import DefaultFormatter

logging.basicConfig(level=logging.INFO)


def get_logger(logger_name: str, level: int | str = logging.INFO):
    """Get a logger with the given name using uvicorn's default formatter."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(
        DefaultFormatter(fmt="%(levelprefix)s [%(name)5s]: %(message)s")
    )
    logger.addHandler(log_handler)
    logger.propagate = False
    return logger


def log(logger: logging.Logger | None, level: int, message: str):
    """
    Log a message with the given logger and level.

    Args:
        logger (logging.Logger | None): The logger to use.
        level (int): The logging level.
        message (str): The message to log.
    """
    if logger:
        logger.log(level, message)
    else:
        BACKUP_LOGGER.log(level, message)


def set_global_log_level(level: int | str):
    """
    Set the log level for all modules globally. Can still be overruled manually.

    Args:
        level (int | str): The logging level as defined in _logging_.
    """
    logging.basicConfig(level=level)
    for name in logging.Logger.manager.loggerDict:
        logging.getLogger(name).setLevel(level)


BACKUP_LOGGER: logging.Logger = get_logger("uagents", logging.INFO)
