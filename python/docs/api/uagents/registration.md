

# src.uagents.registration



#### coerce_metadata_to_str[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L52)
```python
def coerce_metadata_to_str(
    metadata: dict[str, Any] | None
) -> dict[str, str | list[str] | dict[str, str]] | None
```

Step through the metadata and convert any non-string values to strings.



#### extract_geo_metadata[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L69)
```python
def extract_geo_metadata(
        metadata: dict[str, Any] | None) -> dict[str, Any] | None
```

Extract geo-location metadata from the metadata dictionary.



#### almanac_api_post[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L76)
```python
async def almanac_api_post(url: str,
                           data: BaseModel,
                           *,
                           timeout: float | None = None,
                           max_retries: int | None = None,
                           retry_delay: RetryDelayFunc | None = None) -> bool
```

Send a POST request to the Almanac API.



## LedgerBasedRegistrationPolicy Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L220)

```python
class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy)
```



#### register[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L282)
```python
async def register(agent_identifier: str,
                   identity: Identity,
                   protocols: list[str],
                   endpoints: list[AgentEndpoint],
                   metadata: dict[str, Any] | None = None) -> None
```

Register the agent on the Almanac contract if registration is about to expire or
the registration data has changed.

