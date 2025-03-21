import logging
import sys

logging.basicConfig(level=logging.INFO)


formatter = logging.Formatter(
    fmt="%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(
    logger_name: str | None = None,
    level: int | str = logging.INFO,
    log_file: str | None = "uagents_core.log",
) -> logging.Logger:
    """
    Get a logger with the given name.

    If no name is specified, the root logger is returned.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    if log_file:
        log_handler = logging.FileHandler(log_file)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)

    logger.propagate = False
    return logger
