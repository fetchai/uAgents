import logging
from typing import Optional


def log(logger: Optional[logging.Logger], level: str, message: str):
    if logger:
        logger.log(level, message)
