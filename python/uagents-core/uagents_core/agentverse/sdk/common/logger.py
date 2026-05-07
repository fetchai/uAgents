import logging

SDK_WARN = 99

logger = logging.getLogger("agentverse-sdk")
logger.setLevel(logging.CRITICAL)


class _AlignedFormatter(logging.Formatter):
    def format(self, record):
        record.levelprefix = f"{record.levelname}:".ljust(10)
        return super().format(record)


class _SDKWarnFilter(logging.Filter):
    def filter(self, record):
        if record.levelno == SDK_WARN:
            record.levelname = "WARNING"
        return True


logger.addFilter(_SDKWarnFilter())


_FMT = "%(levelprefix)s [sdk] %(message)s"


def _make_formatter():
    try:
        from uvicorn.logging import DefaultFormatter

        fmt = DefaultFormatter(_FMT)
        fmt.level_name_colors[SDK_WARN] = fmt.level_name_colors[logging.WARNING]
        return fmt
    except (ImportError, AttributeError):
        return _AlignedFormatter(_FMT)


def _has_structlog():
    try:
        import structlog.stdlib

        return any(
            isinstance(h.formatter, structlog.stdlib.ProcessorFormatter)
            for h in logging.getLogger().handlers
        )
    except ImportError:
        return False


def configure(level: int):
    logger.setLevel(level)
    if not logger.handlers and not _has_structlog():
        handler = logging.StreamHandler()
        handler.setLevel(0)
        handler.setFormatter(_make_formatter())
        logger.addHandler(handler)
        logger.propagate = False


def log_sdk(msg: str, *args):
    logger.log(SDK_WARN, msg, *args)
