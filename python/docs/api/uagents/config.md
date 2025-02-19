

# src.uagents.config



#### parse_endpoint_config[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/config.py#L62)
```python
def parse_endpoint_config(
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]],
        agentverse: AgentverseConfig,
        mailbox: bool = False,
        proxy: bool = False,
        logger: Optional[logging.Logger] = None) -> List[AgentEndpoint]
```

Parse the user-provided endpoint configuration.

**Arguments**:

- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - The endpoint configuration.
- `agentverse` _AgentverseConfig_ - The agentverse configuration.
- `mailbox` _bool_ - Whether to use the mailbox endpoint.
- `proxy` _bool_ - Whether to use the proxy endpoint.
- `logger` _Optional[logging.Logger]_ - The logger to use.
  

**Returns**:

- `Optional[List[AgentEndpoint]` - The parsed endpoint configuration.



#### parse_agentverse_config[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/config.py#L117)
```python
def parse_agentverse_config(
        config: Optional[Union[str, Dict[str,
                                         str]]] = None) -> AgentverseConfig
```

Parse the user-provided agentverse configuration.

**Returns**:

- `AgentverseConfig` - The parsed agentverse configuration.

