

# src.uagents.registration



#### coerce_metadata_to_str[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L49)
```python
def coerce_metadata_to_str(
        metadata: dict[str, Any] | None
) -> dict[str, str | dict[str, str]] | None
```

Step through the metadata and convert any non-string values to strings.



#### extract_geo_metadata[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L66)
```python
def extract_geo_metadata(
        metadata: dict[str, Any] | None) -> dict[str, Any] | None
```

Extract geo-location metadata from the metadata dictionary.



#### almanac_api_post[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L75)
```python
async def almanac_api_post(url: str,
                           data: BaseModel,
                           *,
                           max_retries: int | None = None,
                           retry_delay: RetryDelayFunc | None = None) -> bool
```

Send a POST request to the Almanac API.



## LedgerBasedRegistrationPolicy Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L234)

```python
class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy)
```



#### check_contract_version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L292)
```python
def check_contract_version() -> None
```

Check the version of the deployed Almanac contract and log a warning
if it is different from the supported version.



#### register[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L306)
```python
async def register(agent_identifier: str,
                   identity: Identity,
                   protocols: list[str],
                   endpoints: list[AgentEndpoint],
                   metadata: dict[str, Any] | None = None) -> None
```

Register the agent on the Almanac contract if registration is about to expire or
the registration data has changed.

