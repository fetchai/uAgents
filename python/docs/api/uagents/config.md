<a id="src.uagents.config"></a>

# src.uagents.config

<a id="src.uagents.config.parse_endpoint_config"></a>

#### parse`_`endpoint`_`config

```python
def parse_endpoint_config(
    endpoint: Optional[Union[str, List[str], Dict[str, dict]]]
) -> List[Dict[str, Any]]
```

Parse the user-provided endpoint configuration.

**Returns**:

  List[Dict[str, Any]]: The parsed endpoint configuration.

<a id="src.uagents.config.parse_agentverse_config"></a>

#### parse`_`agentverse`_`config

```python
def parse_agentverse_config(
        config: Optional[Union[str, Dict[str, str]]] = None) -> Dict[str, str]
```

Parse the user-provided agentverse configutation.

**Returns**:

  Dict[str, str]: The parsed agentverse configuration.

<a id="src.uagents.config.get_logger"></a>

#### get`_`logger

```python
def get_logger(logger_name)
```

Get a logger with the given name using uvicorn's default formatter.

