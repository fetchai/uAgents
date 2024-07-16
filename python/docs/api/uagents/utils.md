<a id="src.uagents.utils"></a>

# src.uagents.utils

<a id="src.uagents.utils.get_logger"></a>

#### get`_`logger

```python
def get_logger(logger_name: str, level: Union[int, str] = logging.INFO)
```

Get a logger with the given name using uvicorn's default formatter.

<a id="src.uagents.utils.log"></a>

#### log

```python
def log(logger: Optional[logging.Logger], level: int, message: str)
```

Log a message with the given logger and level.

**Arguments**:

- `logger` _Optional[logging.Logger]_ - The logger to use.
- `level` _int_ - The logging level.
- `message` _str_ - The message to log.

