<a id="src.uagents.config"></a>

# src.uagents.config

<a id="src.uagents.config.parse_endpoint_config"></a>

#### parse`_`endpoint`_`config

```python
def parse_endpoint_config(
    endpoint: Optional[Union[str, List[str], Dict[str, dict]]]
) -> List[AgentEndpoint]
```

Parse the user-provided endpoint configuration.

**Returns**:

  Optional[List[Dict[str, Any]]]: The parsed endpoint configuration.

<a id="src.uagents.config.parse_agentverse_config"></a>

#### parse`_`agentverse`_`config

```python
def parse_agentverse_config(
    config: Optional[Union[str, Dict[str, str]]] = None
) -> Dict[str, Union[str, bool, None]]
```

Parse the user-provided agentverse configuration.

**Returns**:

  Dict[str, Union[str, bool, None]]: The parsed agentverse configuration.

