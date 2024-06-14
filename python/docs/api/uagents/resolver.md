<a id="src.uagents.resolver"></a>

# src.uagents.resolver

Endpoint Resolver.

<a id="src.uagents.resolver.weighted_random_sample"></a>

#### weighted`_`random`_`sample

```python
def weighted_random_sample(items: List[Any],
                           weights: Optional[List[float]] = None,
                           k: int = 1,
                           rng=random) -> List[Any]
```

Weighted random sample from a list of items without replacement.

Ref: Efraimidis, Pavlos S. "Weighted random sampling over data streams."

**Arguments**:

- `items` _List[Any]_ - The list of items to sample from.
- `weights` _Optional[List[float]]_ - The optional list of weights for each item.
- `k` _int_ - The number of items to sample.
- `rng` _random_ - The random number generator.
  

**Returns**:

- `List[Any]` - The sampled items.

<a id="src.uagents.resolver.is_valid_address"></a>

#### is`_`valid`_`address

```python
def is_valid_address(address: str) -> bool
```

Check if the given string is a valid address.

**Arguments**:

- `address` _str_ - The address to be checked.
  

**Returns**:

- `bool` - True if the address is valid; False otherwise.

<a id="src.uagents.resolver.is_valid_prefix"></a>

#### is`_`valid`_`prefix

```python
def is_valid_prefix(prefix: str) -> bool
```

Check if the given string is a valid prefix.

**Arguments**:

- `prefix` _str_ - The prefix to be checked.
  

**Returns**:

- `bool` - True if the prefix is valid; False otherwise.

<a id="src.uagents.resolver.parse_identifier"></a>

#### parse`_`identifier

```python
def parse_identifier(identifier: str) -> Tuple[str, str, str]
```

Parse an agent identifier string into prefix, name, and address.

**Arguments**:

- `identifier` _str_ - The identifier string to be parsed.
  

**Returns**:

  Tuple[str, str, str]: A tuple containing the prefix, name, and address as strings.

<a id="src.uagents.resolver.query_record"></a>

#### query`_`record

```python
def query_record(agent_address: str, service: str, test: bool) -> dict
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
def get_agent_address(name: str, test: bool) -> Optional[str]
```

Get the agent address associated with the provided name from the name service contract.

**Arguments**:

- `name` _str_ - The name to query.
- `test` _bool_ - Whether to use the testnet or mainnet contract.
  

**Returns**:

- `Optional[str]` - The associated agent address if found.

<a id="src.uagents.resolver.Resolver"></a>

## Resolver Objects

```python
class Resolver(ABC)
```

<a id="src.uagents.resolver.Resolver.resolve"></a>

#### resolve

```python
@abstractmethod
async def resolve(destination: str) -> Tuple[Optional[str], List[str]]
```

Resolve the destination to an address and endpoint.

**Arguments**:

- `destination` _str_ - The destination name or address to resolve.
  

**Returns**:

  Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.

<a id="src.uagents.resolver.GlobalResolver"></a>

## GlobalResolver Objects

```python
class GlobalResolver(Resolver)
```

<a id="src.uagents.resolver.GlobalResolver.__init__"></a>

#### `__`init`__`

```python
def __init__(max_endpoints: Optional[int] = None)
```

Initialize the GlobalResolver.

**Arguments**:

- `max_endpoints` _Optional[int]_ - The maximum number of endpoints to return.

<a id="src.uagents.resolver.GlobalResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Tuple[Optional[str], List[str]]
```

Resolve the destination using the appropriate resolver.

**Arguments**:

- `destination` _str_ - The destination name or address to resolve.
  

**Returns**:

  Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.

<a id="src.uagents.resolver.AlmanacResolver"></a>

## AlmanacResolver Objects

```python
class AlmanacResolver(Resolver)
```

<a id="src.uagents.resolver.AlmanacResolver.__init__"></a>

#### `__`init`__`

```python
def __init__(max_endpoints: Optional[int] = None)
```

Initialize the AlmanacResolver.

**Arguments**:

- `max_endpoints` _Optional[int]_ - The maximum number of endpoints to return.

<a id="src.uagents.resolver.AlmanacResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Tuple[Optional[str], List[str]]
```

Resolve the destination using the Almanac contract.

**Arguments**:

- `destination` _str_ - The destination address to resolve.
  

**Returns**:

  Tuple[str, List[str]]: The address and resolved endpoints.

<a id="src.uagents.resolver.NameServiceResolver"></a>

## NameServiceResolver Objects

```python
class NameServiceResolver(Resolver)
```

<a id="src.uagents.resolver.NameServiceResolver.__init__"></a>

#### `__`init`__`

```python
def __init__(max_endpoints: Optional[int] = None)
```

Initialize the NameServiceResolver.

**Arguments**:

- `max_endpoints` _Optional[int]_ - The maximum number of endpoints to return.

<a id="src.uagents.resolver.NameServiceResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Tuple[Optional[str], List[str]]
```

Resolve the destination using the NameService contract.

**Arguments**:

- `destination` _str_ - The destination name to resolve.
  

**Returns**:

  Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.

<a id="src.uagents.resolver.RulesBasedResolver"></a>

## RulesBasedResolver Objects

```python
class RulesBasedResolver(Resolver)
```

<a id="src.uagents.resolver.RulesBasedResolver.__init__"></a>

#### `__`init`__`

```python
def __init__(rules: Dict[str, str], max_endpoints: Optional[int] = None)
```

Initialize the RulesBasedResolver with the provided rules.

**Arguments**:

- `rules` _Dict[str, str]_ - A dictionary of rules mapping destinations to endpoints.
- `max_endpoints` _Optional[int]_ - The maximum number of endpoints to return.

<a id="src.uagents.resolver.RulesBasedResolver.resolve"></a>

#### resolve

```python
async def resolve(destination: str) -> Tuple[Optional[str], List[str]]
```

Resolve the destination using the provided rules.

**Arguments**:

- `destination` _str_ - The destination to resolve.
  

**Returns**:

  Tuple[str, List[str]]: The address and resolved endpoints.

