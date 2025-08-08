

# src.uagents.utils



#### get_logger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/utils.py#L9)
```python
def get_logger(logger_name: str, level: int | str = logging.INFO)
```

Get a logger with the given name using uvicorn's default formatter.



#### log[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/utils.py#L22)
```python
def log(logger: logging.Logger | None, level: int, message: str)
```

Log a message with the given logger and level.

**Arguments**:

- `logger` _logging.Logger | None_ - The logger to use.
- `level` _int_ - The logging level.
- `message` _str_ - The message to log.



#### set_global_log_level[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/utils.py#L37)
```python
def set_global_log_level(level: int | str)
```

Set the log level for all modules globally. Can still be overruled manually.

**Arguments**:

- `level` _int | str_ - The logging level as defined in _logging_.

