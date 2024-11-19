<a id="src.uagents.registration"></a>

# src.uagents.registration

<a id="src.uagents.registration.generate_backoff_time"></a>

#### generate`_`backoff`_`time

```python
def generate_backoff_time(retry: int) -> float
```

Generate a backoff time starting from 0.128 seconds and limited to ~131 seconds

<a id="src.uagents.registration.coerce_metadata_to_str"></a>

#### coerce`_`metadata`_`to`_`str

```python
def coerce_metadata_to_str(
    metadata: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Union[str, Dict[str, str]]]]
```

Step through the metadata and convert any non-string values to strings.

<a id="src.uagents.registration.extract_geo_metadata"></a>

#### extract`_`geo`_`metadata

```python
def extract_geo_metadata(
        metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]
```

Extract geo-location metadata from the metadata dictionary.

<a id="src.uagents.registration.LedgerBasedRegistrationPolicy"></a>

## LedgerBasedRegistrationPolicy Objects

```python
class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy)
```

<a id="src.uagents.registration.LedgerBasedRegistrationPolicy.check_contract_version"></a>

#### check`_`contract`_`version

```python
def check_contract_version()
```

Check the version of the deployed Almanac contract and log a warning
if it is different from the supported version.

<a id="src.uagents.registration.LedgerBasedRegistrationPolicy.register"></a>

#### register

```python
async def register(agent_address: str,
                   protocols: List[str],
                   endpoints: List[AgentEndpoint],
                   metadata: Optional[Dict[str, Any]] = None)
```

Register the agent on the Almanac contract if registration is about to expire or
the registration data has changed.

