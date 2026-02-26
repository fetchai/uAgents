

# src.uagents.resolver

Endpoint Resolver.



#### is_valid_prefix[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L56)
```python
def is_valid_prefix(prefix: str) -> bool
```

Check if the given string is a valid prefix.

**Arguments**:

- `prefix` _str_ - The prefix to be checked.
  

**Returns**:

- `bool` - True if the prefix is valid; False otherwise.



#### query_record[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L70)
```python
def query_record(agent_address: str, network: AgentNetwork) -> dict
```

Query an agent record from the Almanac contract.

**Arguments**:

- `agent_address` _str_ - The address of the agent.
- `network` _AgentNetwork_ - The network to query (mainnet or testnet).
  

**Returns**:

- `dict` - The query result.



#### get_agent_address[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L93)
```python
def get_agent_address(name: str, network: AgentNetwork) -> str | None
```

Get the agent address associated with the provided domain from the name service contract.

**Arguments**:

- `name` _str_ - The name to query.
- `network` _AgentNetwork_ - The network to query (mainnet or testnet).
  

**Returns**:

  str | None: The associated agent address if found.



#### build_identifier[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L119)
```python
def build_identifier(prefix: str | None = None,
                     name: str | None = None,
                     address: str | None = None) -> str
```

Build an agent identifier string from prefix, name, and address.

**Arguments**:

- `prefix` _str_ - The prefix to be used in the identifier.
- `name` _str_ - The name to be used in the identifier.
- `address` _str_ - The address to be used in the identifier.
  

**Returns**:

- `str` - The constructed identifier string.



## Resolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L145)

```python
class Resolver(ABC)
```



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L146)
```python
@abstractmethod
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination to an address and endpoint.

**Arguments**:

- `destination` _str_ - The destination name or address to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address (if available) and resolved endpoints.



## GlobalResolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L160)

```python
class GlobalResolver(Resolver)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L161)
```python
def __init__(max_endpoints: int | None = None,
             almanac_api_url: str | None = None)
```

Initialize the GlobalResolver.

**Arguments**:

- `max_endpoints` _int | None_ - The maximum number of endpoints to return.
- `almanac_api_url` _str | None_ - The url for almanac api



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L179)
```python
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination using the appropriate resolver.

**Arguments**:

- `destination` _str_ - The destination name or address to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address (if available) and resolved endpoints.



## AlmanacContractResolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L201)

```python
class AlmanacContractResolver(Resolver)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L202)
```python
def __init__(max_endpoints: int | None = None)
```

Initialize the AlmanacContractResolver.

**Arguments**:

- `max_endpoints` _int | None_ - The maximum number of endpoints to return.



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L211)
```python
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination using the Almanac contract.

**Arguments**:

- `destination` _str_ - The destination address to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address and resolved endpoints.



## AlmanacApiResolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L256)

```python
class AlmanacApiResolver(Resolver)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L257)
```python
def __init__(max_endpoints: int | None = None,
             almanac_api_url: str | None = None)
```

Initialize the AlmanacApiResolver.

**Arguments**:

- `max_endpoints` _int | None_ - The maximum number of endpoints to return.
- `almanac_api_url` _str | None_ - The url for almanac api



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L325)
```python
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination using the Almanac API.
If the resolution using API fails, it retries using the Almanac Contract.

**Arguments**:

- `destination` _str_ - The destination address to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address and resolved endpoints.



## NameServiceResolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L344)

```python
class NameServiceResolver(Resolver)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L345)
```python
def __init__(max_endpoints: int | None = None,
             almanac_api_url: str | None = None)
```

Initialize the NameServiceResolver.

**Arguments**:

- `max_endpoints` _int | None_ - The maximum number of endpoints to return.



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L408)
```python
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination using the NameService contract.

**Arguments**:

- `destination` _str_ - The destination name to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address (if available) and resolved endpoints.



## RulesBasedResolver Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L445)

```python
class RulesBasedResolver(Resolver)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L446)
```python
def __init__(rules: dict[str, str], max_endpoints: int | None = None)
```

Initialize the RulesBasedResolver with the provided rules.

**Arguments**:

- `rules` _dict[str, str]_ - A dictionary of rules mapping destinations to endpoints.
- `max_endpoints` _int | None_ - The maximum number of endpoints to return.



#### resolve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/resolver.py#L457)
```python
async def resolve(destination: str) -> tuple[str | None, list[str]]
```

Resolve the destination using the provided rules.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

  tuple[str | None, list[str]]: The address and resolved endpoints.

