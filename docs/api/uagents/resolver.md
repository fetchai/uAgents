<a id="src.uagents.resolver"></a>

# src.uagents.resolver

Endpoint Resolver.

<a id="src.uagents.resolver.query_record"></a>

#### query`_`record

```python
def query_record(agent_address: str, service: str) -> dict
```

Query a record from the Almanac contract.

**Arguments**:

- `agent_address` _str_ - The address of the agent.
- `service` _str_ - The type of service to query.
  

**Returns**:

- `dict` - The query result.

<a id="src.uagents.resolver.get_agent_address"></a>

#### get`_`agent`_`address

```python
def get_agent_address(name: str) -> str
```

Get the agent address associated with the provided name from the name service contract.

**Arguments**:

- `name` _str_ - The name to query.
  

**Returns**:

- `str` - The associated agent address.

<a id="src.uagents.resolver.is_agent_address"></a>

#### is`_`agent`_`address

```python
def is_agent_address(address)
```

Check if the provided address is a valid agent address.

**Arguments**:

- `address` - The address to check.
  

**Returns**:

- `bool` - True if the address is a valid agent address, False otherwise.

<a id="src.uagents.resolver.Resolver"></a>

## Resolver Objects

```python
class Resolver(ABC)
```

<a id="src.uagents.resolver.Resolver.resolve"></a>

#### resolve

```python
@abstractmethod
async def resolve(destination: str) -> Optional[str]
```

Resolve the destination to an endpoint.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

- `Optional[str]` - The resolved endpoint or None.

<a id="src.uagents.resolver.GlobalResolver"></a>

## GlobalResolver Objects

```python
class GlobalResolver(Resolver)
```

<a id="src.uagents.resolver.GlobalResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Optional[str]
```

Resolve the destination using a combination of Almanac and NameService resolvers.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

- `Optional[str]` - The resolved endpoint or None.

<a id="src.uagents.resolver.AlmanacResolver"></a>

## AlmanacResolver Objects

```python
class AlmanacResolver(Resolver)
```

<a id="src.uagents.resolver.AlmanacResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Optional[str]
```

Resolve the destination using the Almanac contract.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

- `Optional[str]` - The resolved endpoint or None.

<a id="src.uagents.resolver.NameServiceResolver"></a>

## NameServiceResolver Objects

```python
class NameServiceResolver(Resolver)
```

<a id="src.uagents.resolver.NameServiceResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Optional[str]
```

Resolve the destination using the NameService contract.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

- `Optional[str]` - The resolved endpoint or None.

<a id="src.uagents.resolver.RulesBasedResolver"></a>

## RulesBasedResolver Objects

```python
class RulesBasedResolver(Resolver)
```

<a id="src.uagents.resolver.RulesBasedResolver.__init__"></a>

#### `__`init`__`

```python
def __init__(rules: Dict[str, str])
```

Initialize the RulesBasedResolver with the provided rules.

**Arguments**:

- `rules` _Dict[str, str]_ - A dictionary of rules mapping destinations to endpoints.

<a id="src.uagents.resolver.RulesBasedResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Optional[str]
```

Resolve the destination using the provided rules.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

- `Optional[str]` - The resolved endpoint or None.

